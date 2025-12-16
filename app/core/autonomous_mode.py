"""
Autonomous Computer Control Mode - Vision-guided iterative task execution.

This mode uses a continuous feedback loop:
1. Observe screen (vision)
2. Plan next action (LLM)
3. Execute action (computer control)
4. Verify result (vision)
5. Repeat until task complete or max iterations
"""

import json
from typing import Dict, Any, List, Optional
from .llm import LLMClient
from .logging_utils import get_logger
from app.tools.registry import ToolRegistry
from app.tools.vision_tools import capture_screenshot, analyze_image, describe_screen


class AutonomousComputerAgent:
    """
    Autonomous agent that uses vision feedback to complete GUI-based tasks.
    
    Unlike the standard agent which uses pre-planned execution steps,
    this agent observes the screen after each action and decides the next
    step based on what it sees.
    """
    
    def __init__(self, registry: ToolRegistry, model: str = "groq/llama-3.1-70b-versatile"):
        self.llm = LLMClient(model)
        self.registry = registry
        self.logger = get_logger("autonomous_agent", "agent.log")
        self.max_iterations = 20  # Prevent infinite loops
        
        # Import refiner for better screenshot analysis
        from .refiner_agent import PromptRefiner
        self.refiner = PromptRefiner()
        
        # System prompt for autonomous mode
        self.system_prompt = """You are an autonomous computer control agent that can see the screen and control the mouse/keyboard.

AVAILABLE COMPUTER CONTROL TOOLS:
- click_element(element_description) - Find and click UI elements (DPI-FIXED, works reliably now)
- type_text(text, press_enter=True/False) - Type text (PREFERRED for input)
- press_key(key) - Press keys like 'enter', 'tab', 'esc', etc. (RELIABLE)
- hotkey(*keys) - Press keyboard shortcuts like Ctrl+C (PREFERRED over clicking menus)
- scroll(clicks, direction) - Scroll up/down (RELIABLE)
- describe_screen() - Get description of current screen (use when unsure)

AVAILABLE SYSTEM TOOLS:
- launch_app(app_name) - Open applications by name (e.g., "Chrome", "Notepad")
- open_url(url) - Open URL directly in default browser

CRITICAL STRATEGY RULES:
1. **UNDERSTAND THE SCREEN FIRST**: The screenshot analysis tells you what's visible - read it carefully
2. **CLICK SEARCH RESULTS**: When you see Google search results, click the first relevant link
3. **USE KEYBOARD FOR NAVIGATION**: Ctrl+L for URL bar, Ctrl+T for new tab
4. **USE launch_app TO OPEN APPS**: launch_app("Chrome") instead of clicking icon
5. **CLICK WHEN NEEDED**: DPI is fixed - clicking buttons, links, and elements works reliably now
6. **BE SPECIFIC**: When clicking, describe position: "first search result", "top-left", etc.

TASK COMPLETION PROCESS:
1. You will receive the user's goal and a description of what's currently on screen
2. Decide the SINGLE NEXT ACTION to take
3. The action will be executed
4. You'll see the new screen state
5. Repeat until goal is achieved

RESPONSE FORMAT (must be valid JSON):
{
  "thought": "what I observe on screen and my analysis of the situation",
  "verification": "did my previous action succeed? what evidence do I see?",
  "action": {
    "tool": "tool_name",
    "parameters": {
      "param1": "value1",
      "param2": "value2"
    }
  },
  "is_complete": false,
  "completion_message": "only if is_complete=true, explain what was accomplished"
}

CRITICAL RULES:
1. Return ONLY ONE action at a time
2. **READ REFINER ANALYSIS**: The refiner provides expert analysis of the screenshot - follow its suggestions
3. ALWAYS verify previous action before continuing - check if the expected result is visible
4. **CLICK SEARCH RESULTS**: When on Google search, click the first relevant result
5. **CLICK BUTTONS/LINKS**: DPI is fixed - clicking works reliably now, use it when needed
6. If previous action FAILED, RETRY with different strategy
7. After any action, set is_complete=false so we can observe the result
8. Set is_complete=true ONLY when the user's goal is fully achieved
9. Use keyboard shortcuts for navigation (Ctrl+L, Ctrl+T, etc.)
10. Do NOT use web_search, find_image, or other non-computer-control tools

WHEN TO CLICK VS KEYBOARD:
✓ CLICK: Links, buttons, search results, dropdown menus, specific UI elements
✓ KEYBOARD: URL bar focus (Ctrl+L), new tab (Ctrl+T), typing text, page navigation

UNDERSTANDING SEARCH RESULTS:
- When you see Google search results, the first blue link is usually what you want
- Click it using: click_element("first search result link at the top")
- Be specific with position: "first result", "second result", etc.

EXAMPLES:

Task: "Open Chrome and search for Python tutorials"
Screen: "Desktop with taskbar visible at bottom"
Response:
{
  "thought": "I need to open Chrome. Instead of clicking the icon (unreliable), I should use launch_app.",
  "verification": "No previous action yet, this is the first step.",
  "action": {
    "tool": "launch_app",
    "parameters": {
      "app_name": "Chrome"
    }
  },
  "is_complete": false
}

Next Screen: "Chrome window is open showing new tab page"
Response:
{
  "thought": "Chrome opened successfully! Now I need to focus the address bar. Using Ctrl+L is much more reliable than clicking.",
  "verification": "SUCCESS - launch_app worked! Chrome window is now visible.",
  "action": {
    "tool": "hotkey",
    "parameters": {
      "keys": ["ctrl", "l"]
    }
  },
  "is_complete": false
}

Next Screen: "Chrome window with address bar highlighted/focused"
Response:
{
  "thought": "Address bar is now focused (I can see it's highlighted). I can now type my search query.",
  "verification": "SUCCESS - Ctrl+L worked, address bar is focused and ready.",
  "action": {
    "tool": "type_text",
    "parameters": {
      "text": "Python tutorials",
      "press_enter": true
    }
  },
  "is_complete": false
}

Next Screen: "Google search results page showing Python tutorial links"
Response:
{
  "thought": "The search completed successfully. I can see Google results with Python tutorials.",
  "verification": "SUCCESS - The text was typed and Enter was pressed, search results are now visible.",
  "action": {
    "tool": "describe_screen",
    "parameters": {}
  },
  "is_complete": true,
  "completion_message": "Successfully opened Chrome and searched for Python tutorials. Search results are now displayed."
}

Return ONLY the JSON, no extra text."""
    
    def execute(self, goal: str) -> str:
        """
        Execute a task using autonomous computer control with vision feedback.
        
        Args:
            goal: The user's task description
        
        Returns:
            Final completion message
        """
        self.logger.info("Starting autonomous mode for goal: %s", goal)
        print(f"\n{'='*60}")
        print("🤖 AUTONOMOUS COMPUTER CONTROL MODE")
        print(f"{'='*60}")
        print(f"Goal: {goal}")
        print(f"Max iterations: {self.max_iterations}")
        print(f"{'='*60}\n")
        
        # Track execution history
        execution_history: List[Dict[str, Any]] = []
        
        for iteration in range(1, self.max_iterations + 1):
            print(f"\n{'─'*60}")
            print(f"Iteration {iteration}/{self.max_iterations}")
            print(f"{'─'*60}")
            
            # Step 1: Observe current screen
            print("👁️  Observing screen...")
            screen_description = describe_screen()
            
            if "❌" in screen_description:
                return f"Error: Failed to capture screen: {screen_description}"
            
            print(f"Screen: {screen_description[:150]}...")
            self.logger.info("Iteration %d - Screen: %s", iteration, screen_description[:200])
            
            # Step 1.5: Use refiner to analyze screenshot and suggest action
            print("🔍 Analyzing screenshot with refiner...")
            refiner_context = f"""GOAL: {goal}

CURRENT SCREEN DESCRIPTION:
{screen_description}

PREVIOUS ACTIONS:
{self._format_previous_actions(execution_history)}

Analyze the current screen and suggest the SINGLE NEXT ACTION to achieve the goal.
Be specific about what you see and what should be done next.

Return JSON:
{{
  "analysis": "what you see on screen and its relevance to the goal",
  "suggested_action": "the specific next action to take",
  "tool_recommendation": "which tool to use (click_element, type_text, hotkey, etc.)",
  "parameters": {{"param": "value"}},
  "reasoning": "why this action makes sense"
}}"""
            
            try:
                refiner_response = self.refiner.llm.get_response_text(
                    [{"role": "user", "content": refiner_context}],
                    temperature=0.1
                )
                
                # Try to parse refiner suggestion
                import json
                refiner_suggestion = json.loads(refiner_response.strip().replace("```json", "").replace("```", ""))
                print(f"💡 Refiner analysis: {refiner_suggestion.get('analysis', 'N/A')[:100]}...")
                print(f"💡 Suggested: {refiner_suggestion.get('suggested_action', 'N/A')[:100]}...")
                
                # Add refiner suggestion to context for decision
                screen_description += f"\n\nREFINER ANALYSIS:\n{refiner_suggestion.get('analysis', '')}\n"
                screen_description += f"SUGGESTED ACTION: {refiner_suggestion.get('suggested_action', '')}\n"
                screen_description += f"RECOMMENDED TOOL: {refiner_suggestion.get('tool_recommendation', '')}"
                
            except Exception as e:
                self.logger.warning("Refiner analysis failed: %s", e)
                print(f"⚠️  Refiner analysis failed, continuing without it")
            
            # Step 2: Build context for LLM
            context = self._build_context(goal, screen_description, execution_history)
            
            # Step 3: Get next action from LLM
            print("🧠 Deciding next action...")
            try:
                response = self.llm.complete(
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": context}
                    ],
                    temperature=0.1,
                )
                
                raw_response = response.choices[0].message.content
                self.logger.debug("LLM response: %s", raw_response)
                
                # Parse JSON response
                decision = self._parse_decision(raw_response)
                
            except Exception as e:
                self.logger.error("Failed to get next action: %s", e)
                return f"Error: Failed to plan next action: {str(e)}"
            
            # Check if task is complete
            if decision.get("is_complete", False):
                completion_msg = decision.get("completion_message", "Task completed")
                print(f"\n✅ TASK COMPLETE")
                print(f"   {completion_msg}")
                self.logger.info("Task completed after %d iterations", iteration)
                return completion_msg
            
            # Step 4: Execute the action
            thought = decision.get("thought", "")
            verification = decision.get("verification", "N/A")
            action = decision.get("action", {})
            
            if not action or "tool" not in action:
                self.logger.warning("No valid action in decision")
                continue
            
            print(f"💭 Thought: {thought}")
            
            # Show verification of previous action (if not first iteration)
            if iteration > 1:
                if "SUCCESS" in verification.upper() or "WORKED" in verification.upper():
                    print(f"✓ Verification: {verification}")
                elif "FAIL" in verification.upper() or "DIDN'T" in verification.upper() or "NOT" in verification.upper():
                    print(f"⚠️  Verification: {verification}")
                else:
                    print(f"ℹ️  Verification: {verification}")
            
            print(f"⚡ Action: {action['tool']}({action.get('parameters', {})})")
            
            # Execute tool
            tool_name = action["tool"]
            parameters = action.get("parameters", {})
            
            # Special handling for hotkey - needs to unpack keys parameter
            tool_failed = False
            if tool_name == "hotkey" and "keys" in parameters:
                keys_list = parameters["keys"]
                try:
                    result = self.registry.execute(tool_name, *keys_list)
                    result_str = str(result)
                except Exception as e:
                    result_str = f"Error: {str(e)}"
                    self.logger.error("Hotkey execution failed: %s", e)
                    tool_failed = True
            else:
                # Normal tool execution
                try:
                    result = self.registry.execute(tool_name, **parameters)
                    result_str = str(result)
                except Exception as e:
                    result_str = f"Error: {str(e)}"
                    self.logger.error("Tool '%s' raised error: %s", tool_name, e)
                    tool_failed = True
            
            print(f"📊 Result: {result_str[:100]}...")
            
            # Record in history
            execution_history.append({
                "iteration": iteration,
                "screen": screen_description[:200],
                "thought": thought,
                "verification": verification,
                "action": action,
                "result": result_str[:500],
                "success": not result_str.startswith("Error")
            })
            
            self.logger.info(
                "Iteration %d - Executed %s: %s",
                iteration, tool_name, result_str[:200]
            )
        
        # Max iterations reached
        summary = self._generate_summary(goal, execution_history)
        self.logger.warning("Max iterations reached without completion")
        return f"⚠️  Reached maximum iterations ({self.max_iterations}).\n\n{summary}"
    
    def _build_context(
        self,
        goal: str,
        screen_description: str,
        history: List[Dict[str, Any]]
    ) -> str:
        """Build context string for LLM decision making."""
        context_parts = [
            f"GOAL: {goal}",
            f"\nCURRENT SCREEN: {screen_description}",
        ]
        
        if history:
            context_parts.append("\nPREVIOUS ACTIONS (most recent last):")
            # Show last 3 actions for context
            for item in history[-3:]:
                verification_text = item.get('verification', 'N/A')
                context_parts.append(
                    f"  - Iteration {item['iteration']}: {item['action']['tool']} → "
                    f"{'✓' if item['success'] else '❌'} {item['result'][:100]}"
                )
            
            # Emphasize the last action's verification
            if history:
                last_item = history[-1]
                context_parts.append(
                    f"\nREMINDER: Last action was '{last_item['action']['tool']}'. "
                    f"Did it succeed? Check the current screen carefully before proceeding."
                )
        
        context_parts.append("\nWhat is the SINGLE NEXT ACTION to take? (Return JSON only)")
        
        return "\n".join(context_parts)
    
    def _parse_decision(self, raw_response: str) -> Dict[str, Any]:
        """Parse LLM's JSON decision response."""
        # Clean markdown code blocks if present
        response = raw_response.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            response = "\n".join(lines)
        
        response = response.replace("```json", "").replace("```", "").strip()
        
        # Parse JSON
        try:
            decision = json.loads(response)
            return decision
        except json.JSONDecodeError as e:
            self.logger.error("Failed to parse decision JSON: %s", e)
            self.logger.debug("Raw response was: %s", response)
            
            # Return error decision
            return {
                "thought": "Failed to parse decision",
                "action": {"tool": "describe_screen", "parameters": {}},
                "is_complete": False
            }
    
    def _generate_summary(self, goal: str, history: List[Dict[str, Any]]) -> str:
        """Generate execution summary."""
        successful = sum(1 for h in history if h.get("success", False))
        failed = len(history) - successful
        
        summary_lines = [
            f"Goal: {goal}",
            f"Total actions: {len(history)}",
            f"Successful: {successful}",
            f"Failed: {failed}",
            "\nLast few actions:",
        ]
        
        for item in history[-5:]:
            status = "✓" if item["success"] else "❌"
            summary_lines.append(
                f"  {status} Iteration {item['iteration']}: "
                f"{item['action']['tool']} - {item['result'][:80]}"
            )
        
        return "\n".join(summary_lines)
    
    def _format_previous_actions(self, history: List[Dict[str, Any]]) -> str:
        """Format previous actions for refiner context."""
        if not history:
            return "No previous actions yet."
        
        lines = []
        for item in history[-3:]:  # Last 3 actions
            status = "✓" if item.get("success") else "❌"
            lines.append(
                f"{status} Iteration {item['iteration']}: {item['action']['tool']} "
                f"→ {item['result'][:100]}"
            )
        return "\n".join(lines)

