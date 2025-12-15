import json
import os
import platform
from typing import List, Dict, Any, Optional
from .llm import LLMClient
from .refiner_agent import PromptRefiner
from .judge_agent import ResponseJudge
from .logging_utils import get_logger
from app.tools.registry import ToolRegistry
from app.tools.os_ops import get_desktop_path  # <--- Import the helper
from app.tools.tool_catalog import validate_tool_name, get_all_tool_names

class Agent:
    def __init__(self, registry: ToolRegistry, model: str = "groq/llama-3.1-8b-instant"):
        # Main tool-using LLM (Groq)
        self.llm = LLMClient(model)
        # Prompt refiner LLM (OpenRouter Grok) used before each turn
        self.refiner = PromptRefiner()
        # Judge LLM (OpenRouter Grok) used after a full pass to detect hallucinations
        self.judge = ResponseJudge()
        self.registry = registry
        self.history: List[Dict[str, Any]] = []
        self.logger = get_logger("agent", "agent.log")
        self.max_tool_rounds = 4  # allow multiple tool rounds per request
        
        # --- Context Injection ---
        user = os.getlogin()
        cwd = os.getcwd()
        # Use the robust helper to find the REAL desktop (OneDrive aware)
        desktop = get_desktop_path()
        
        # --- IMPROVED SYSTEM PROMPT ---
        self.system_prompt = f"""You are a Windows Automation Agent running on {platform.system()}.
        
        SYSTEM CONTEXT:
        - Current User: {user}
        - Working Directory: {cwd}
        - Real Desktop Path: {desktop}
        
        CRITICAL INSTRUCTIONS:
        1. **ACT, DON'T TEACH**: Do NOT explain how to perform a task with Python code. Do NOT show code snippets.
        
        2. **SINGLE TOOL PER CALL**: 
           - You will call exactly one tool per step (enforced by the system)
           - Focus on providing the correct parameters for the tool
           - Never write fake function calls like "<function(...)>" in your text response
        
        3. **IMAGE HANDLING (MANDATORY)**:
           - If you see "[User attached image: <path>]" in the context, you MUST analyze it first
           - ALWAYS call 'analyze_image' tool with the provided image path before doing anything else
           - Use the image analysis result as context for the user's request
           - If the user asks about "this image", "the screenshot", or "what you see", they are referring to the attached image
           - NEVER skip image analysis when an image is attached
        
        4. **STRICT NO-HALLUCINATION POLICY**:
           - ONLY use data from previous tool results that are marked with ✓
           - If a previous step FAILED (marked with ❌), you cannot use its results
           - NEVER invent, guess, or make up information
           - NEVER embed URLs or file paths in text - use actual downloaded file paths from tool results
           - If you lack required context from a failed step, explain what's missing
        
        5. **USE PREVIOUS RESULTS CORRECTLY**: 
           - Results from previous steps are provided in the context
           - For 'find_image': it returns "Saved image to: <path>" - extract the path for use in image_query
           - For 'web_search': it returns research content - use this content directly
           - For 'analyze_image': it returns a description - use this to answer user's questions
           - Always extract and use actual data, never invent placeholder data
        
        6. **CONFIRMATION**: After running a tool, simply state what was done (e.g., "I have created the file at [path].").
        
        7. **DEFAULT PATHS**: If the user asks for the "Desktop" or doesn't specify a folder, ALWAYS use the 'Real Desktop Path' provided above.
        """

    def process(self, user_input: str, _is_retry: bool = False) -> str:
        """Main loop: Listen -> Think -> Act -> Reply
        
        New flow: Execute one tool per API call, sequentially following the execution plan.
        """
        
        # 1. First, refine the raw user input into an execution plan
        try:
            self.logger.info("User input: %s", user_input)
            refiner_result = self.refiner.refine(user_input)
            refined_input = refiner_result.get("instruction", user_input)
            execution_plan = refiner_result.get("execution_plan", [])
            self.logger.info(
                "Refined input: %s | execution_plan=%s",
                refined_input,
                execution_plan,
            )
        except Exception:
            # If refinement fails for any reason, fall back to the original input
            self.logger.exception("Refiner failed; falling back to raw input")
            refined_input = user_input
            execution_plan = []
        
        # 2. Add (refined) User Input to History
        self.history.append({"role": "user", "content": refined_input})

        # If no execution plan, fall back to single direct call
        if not execution_plan:
            self.logger.info("No execution plan provided, falling back to direct tool call")
            return self._execute_direct_call(user_input, refined_input)
        
        # 3. Execute the plan: one tool per API call, sequentially
        executed_tools: List[Dict[str, Any]] = []
        failed_steps: List[int] = []
        
        for step_idx, step in enumerate(execution_plan):
            step_num = step.get("step", step_idx + 1)
            tool_name = step.get("tool")
            step_instruction = step.get("instruction", "")
            step_description = step.get("description", "")
            
            # Validate tool name against catalog
            if not validate_tool_name(tool_name):
                self.logger.error(
                    "Tool '%s' not in catalog. Available tools: %s",
                    tool_name, get_all_tool_names()
                )
                error_msg = f"❌ Step {step_num} failed: Tool '{tool_name}' is not in the tool catalog"
                self.history.append({"role": "assistant", "content": error_msg})
                failed_steps.append(step_num)
                continue
            
            self.logger.info(
                "Executing step %d/%d: tool=%s, description=%s",
                step_num, len(execution_plan), tool_name, step_description
            )
            print(f"📋 Step {step_num}/{len(execution_plan)}: {step_description}")
            
            # Build context for this step: include results from previous steps
            step_context = step_instruction
            
            if executed_tools:
                step_context += "\n\nResults from previous steps:\n"
                for prev_tool in executed_tools:
                    # Mark if previous step had error
                    if prev_tool['result'].startswith("Error:"):
                        step_context += f"- ❌ {prev_tool['name']} FAILED: {prev_tool['result'][:500]}\n"
                    else:
                        step_context += f"- ✓ {prev_tool['name']}: {prev_tool['result'][:500]}...\n"
            
            # Check if previous critical steps failed
            if failed_steps:
                step_context += f"\n\n⚠️ WARNING: Previous steps {failed_steps} failed. You cannot proceed if you need their results."
            
            # Add step instruction to history
            self.history.append({"role": "user", "content": step_context})
            
            # Get full tool schema (we'll use prompting to guide tool choice, not restriction)
            full_schema = self.registry.get_tool_schema()
            
            # Verify the planned tool exists
            if not self._get_single_tool_schema(tool_name):
                self.logger.error("Tool '%s' not found in registry", tool_name)
                error_msg = f"❌ Step {step_num} failed: Tool '{tool_name}' not found in registry"
                self.history.append({"role": "assistant", "content": error_msg})
                failed_steps.append(step_num)
                continue
            
            # Make API call with constrained tool choice
            # Use tool_choice to FORCE the specific tool from the plan (best practice)
            # For first step or if no failures yet, force the planned tool
            # Otherwise allow agent to decline if previous steps failed
            if step_num == 1 or not failed_steps:
                # Force the exact tool specified in the plan
                tool_choice_config = {
                    "type": "function",
                    "function": {"name": tool_name}
                }
            else:
                # Allow agent to decide (in case previous steps failed)
                tool_choice_config = "auto"
            
            try:
                response = self.llm.complete(
                    messages=[{"role": "system", "content": self.system_prompt}] + self.history,
                    tools=full_schema,
                    tool_choice=tool_choice_config,
                    temperature=0,
                )
                msg = response.choices[0].message
            except Exception as e:
                error_str = str(e)
                self.logger.error("LLM call failed for step %d: %s", step_num, error_str)
                error_msg = f"❌ Step {step_num} failed: LLM API error: {error_str[:200]}"
                self.history.append({"role": "assistant", "content": error_msg})
                failed_steps.append(step_num)
                
                # Track failed step
                executed_tools.append({
                    "name": tool_name,
                    "args": {},
                    "result": f"Error: LLM call failed - {error_str[:200]}",
                    "step": step_num,
                    "failed": True
                })
                continue
            
            # Execute the single tool call
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                self.history.append(msg)
                
                # Should only be one tool call
                tool_call = msg.tool_calls[0]
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                
                # Validate that agent called the correct tool
                if func_name != tool_name:
                    self.logger.warning(
                        "Step %d: Agent called '%s' but plan specified '%s'. "
                        "Proceeding with agent's choice but this indicates plan/execution mismatch.",
                        step_num, func_name, tool_name
                    )
                    print(f"⚠️  Warning: Expected {tool_name} but agent chose {func_name}")
                
                self.logger.info("Step %d: executing %s(%s)", step_num, func_name, args)
                print(f"🤖 Executing: {func_name}({args})")
                
                try:
                    result = self.registry.execute(func_name, **args)
                    result_str = str(result)
                    tool_failed = False
                except Exception as e:
                    result_str = f"Error: {str(e)}"
                    self.logger.error("Tool '%s' raised error: %s", func_name, e)
                    failed_steps.append(step_num)
                    tool_failed = True
                
                # Add result to history
                self.history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": result_str
                })
                
                executed_tools.append({
                    "name": func_name,
                    "args": args,
                    "result": result_str,
                    "step": step_num,
                    "failed": tool_failed
                })
            else:
                # Agent chose not to call the tool (likely because previous steps failed)
                self.logger.warning("Step %d: Agent declined to call tool (likely due to missing context)", step_num)
                text = msg.content or f"Cannot proceed with step {step_num} due to missing required context from previous steps"
                self.history.append({"role": "assistant", "content": text})
                failed_steps.append(step_num)
                
                executed_tools.append({
                    "name": tool_name,
                    "args": {},
                    "result": text,
                    "step": step_num,
                    "failed": True
                })
        
        # 4. Generate execution summary
        summary_lines = []
        summary_lines.append("\n📊 Execution Summary:")
        summary_lines.append(f"   Total steps: {len(execution_plan)}")
        summary_lines.append(f"   Successful: {len(executed_tools) - len(failed_steps)}")
        summary_lines.append(f"   Failed: {len(failed_steps)}")
        
        if failed_steps:
            summary_lines.append(f"\n❌ Failed steps: {failed_steps}")
            for tool in executed_tools:
                if tool.get('failed'):
                    summary_lines.append(f"   - Step {tool['step']}: {tool['name']} - {tool['result'][:100]}")
        
        execution_summary = "\n".join(summary_lines)
        print(execution_summary)
        self.logger.info(execution_summary)
        
        # 5. Final Call: Get summary response based on all tool results
        # Add execution summary to context
        self.history.append({"role": "user", "content": f"{execution_summary}\n\nProvide a final summary for the user."})
        
        final_response = self.llm.complete(
            messages=[{"role": "system", "content": self.system_prompt}] + self.history
        )
        final_text = final_response.choices[0].message.content
        
        # If there were failures, prepend a warning
        if failed_steps:
            warning = f"⚠️ Warning: {len(failed_steps)} step(s) failed during execution.\n\n"
            final_text = warning + final_text
        
        self.history.append({"role": "assistant", "content": final_text})
        self.logger.info("Final assistant response: %s", final_text)
        
        return final_text

    def _get_single_tool_schema(self, tool_name: str) -> Optional[List[Dict[str, Any]]]:
        """Get the schema for a single tool by name."""
        full_schema = self.registry.get_tool_schema()
        for tool in full_schema:
            if tool.get("function", {}).get("name") == tool_name:
                return [tool]
        return None
    
    def _execute_direct_call(self, user_input: str, refined_input: str) -> str:
        """Fallback: execute a single direct tool call without a plan."""
        full_schema = self.registry.get_tool_schema()
        
        try:
            response = self.llm.complete(
                messages=[{"role": "system", "content": self.system_prompt}] + self.history,
                tools=full_schema,
                tool_choice="required",
                temperature=0,
            )
            msg = response.choices[0].message
        except Exception as e:
            self.logger.error("Direct call failed: %s", e)
            error_msg = f"Error: {str(e)}"
            self.history.append({"role": "assistant", "content": error_msg})
            return error_msg
        
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            self.history.append(msg)
            
            # Execute the first tool call only
            tool_call = msg.tool_calls[0]
            func_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            self.logger.info("Direct call: executing %s(%s)", func_name, args)
            print(f"🤖 Executing: {func_name}({args})")
            
            try:
                result = self.registry.execute(func_name, **args)
                result_str = str(result)
            except Exception as e:
                result_str = f"Error: {str(e)}"
                self.logger.error("Tool '%s' raised error: %s", func_name, e)
            
            self.history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": func_name,
                "content": result_str
            })
            
            # Get final response
            final_response = self.llm.complete(
                messages=[{"role": "system", "content": self.system_prompt}] + self.history
            )
            final_text = final_response.choices[0].message.content
            self.history.append({"role": "assistant", "content": final_text})
            
            return final_text
        else:
            text = msg.content or "No tool was called."
            self.history.append({"role": "assistant", "content": text})
            return text
    
    def _make_plan(self, instruction: str) -> str:
        """Produce a short numbered plan (2-6 steps) to guide tool calls."""
        try:
            resp = self.llm.complete(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Make a concise, 2-6 step numbered plan to accomplish the user's request. "
                            "Keep steps short and specific. Do not include tool syntax."
                        ),
                    },
                    {"role": "user", "content": instruction},
                ],
                temperature=0.2,
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            return ""