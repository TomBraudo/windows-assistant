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
import time
from typing import Dict, Any, List, Optional
from .llm import LLMClient
from .logging_utils import get_logger
from app.tools.registry import ToolRegistry
from app.tools.vision_tools import capture_screenshot, analyze_image, describe_screen
from app.tools.omniparser_helper import get_omniparser


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
        self.max_iterations = 15  # Prevent infinite loops (reduced for faster completion detection)
        
        # Import refiner for better screenshot analysis
        from .refiner_agent import PromptRefiner
        self.refiner = PromptRefiner()
        
        # System prompt for autonomous mode
        self.system_prompt = """You are an autonomous computer control agent that can see the screen and control the mouse/keyboard.

AVAILABLE COMPUTER CONTROL TOOLS:
- click_element(element_description) - Find and click UI elements using OmniParser (PIXEL-PERFECT accuracy)
- type_text(text, press_enter=True/False) - Type text (PREFERRED for input)
- press_key(key) - Press keys like 'enter', 'tab', 'esc', etc. (RELIABLE)
- hotkey(*keys) - Press keyboard shortcuts like Ctrl+C (PREFERRED over clicking menus)
- scroll(clicks, direction) - Scroll up/down (RELIABLE)
- describe_screen() - Get description of current screen (use when unsure)

OMNIPARSER UI DETECTION & ELEMENT SELECTION:
- You receive a list of AVAILABLE UI ELEMENTS with: ID, description, type, center coords, bbox
- OmniParser provides PIXEL-PERFECT coordinates - use them!
- The REFINER has already analyzed these elements and suggested which one to click
- The refiner considers: description match, position on screen, size, and type
- FOLLOW THE REFINER'S ELEMENT SELECTION - it has done geometric analysis for you
- Use the exact element description the refiner recommends

Element Selection Process:
1. Refiner reviews ALL available elements (icon 0, icon 1, icon 2, etc.)
2. Refiner considers description, position, size for the current goal step
3. Refiner selects the BEST element and explains why
4. YOU execute the action using that element's description

AVAILABLE SYSTEM TOOLS:
- launch_app(app_name) - Open applications by name (e.g., "Chrome", "Notepad")
- open_url(url) - Open URL directly in default browser

CRITICAL STRATEGY RULES:
1. **CHECK UI ELEMENTS FIRST**: Look at the AVAILABLE UI ELEMENTS list - these are detected by OmniParser
2. **USE EXACT DESCRIPTIONS**: When clicking, use the exact element description from the UI elements list
3. **CLICK WITH CONFIDENCE**: OmniParser provides pixel-perfect coordinates - clicking is now highly reliable
4. **KEYBOARD FOR NAVIGATION**: Use Ctrl+L for URL bar, Ctrl+T for new tab
5. **USE launch_app TO OPEN APPS**: Prefer launch_app("Chrome") over clicking icon when starting apps
6. **BE SPECIFIC**: Reference the exact UI element you see in the list

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
2. **FOLLOW REFINER'S ELEMENT SELECTION**: The refiner has analyzed ALL UI elements and selected the best one
   - It considered: description, position (where on screen), size (width/height), and type
   - Use the EXACT element description the refiner recommends
   - Trust the refiner's geometric analysis
3. **VERIFY PREVIOUS ACTIONS**: Always check if the expected result is visible before proceeding
4. **USE EXACT DESCRIPTIONS**: When clicking, use the exact element description from the refiner
   - Good: click_element("Google Chrome") if refiner selected that description
   - Good: click_element("URL bar") if refiner identified URL bar
   - Bad: click_element("the browser icon") - not specific enough
5. If previous action FAILED, RETRY with different element or strategy
6. After any action, set is_complete=false so we can observe the result
7. **COMPLETION DETECTION (CRITICAL)**:
   - Set is_complete=true ONLY when the user's ENTIRE goal is fully achieved
   - Ask yourself: "Is everything the user requested now done and visible?"
   - Examples:
     * Goal: "open youtube.com" → Complete when YouTube homepage is visible
     * Goal: "search for cats" → Complete when search results are visible
     * Goal: "open daily dose of internet" → Complete when on that specific channel/video
   - Do NOT continue iterating if the goal is achieved!
8. Use keyboard shortcuts for navigation when appropriate (Ctrl+L, Ctrl+T, etc.)
9. Do NOT use web_search, find_image, or other non-computer-control tools
10. **TRUST OMNIPARSER COORDINATES**: They are pixel-perfect, clicking will be accurate

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
            
            # Wait for page to load after previous action (except first iteration)
            if iteration > 1:
                print("⏳ Waiting 3 seconds for page to load...")
                time.sleep(3)
            
            # Step 1: Observe current screen
            print("👁️  Observing screen...")
            screen_description = describe_screen()
            
            if "❌" in screen_description:
                return f"Error: Failed to capture screen: {screen_description}"
            
            print(f"Screen: {screen_description[:150]}...")
            self.logger.info("Iteration %d - Screen: %s", iteration, screen_description[:200])
            
            # Step 1.25: Use OmniParser to detect available UI elements
            print("🔍 Detecting UI elements with OmniParser...")
            ui_elements_text = ""
            try:
                # Get the screenshot path from the most recent screenshot
                capture_result = capture_screenshot()
                screenshot_path = capture_result.replace("Screenshot saved to:", "").strip()
                
                omniparser = get_omniparser()
                result = omniparser.detect_elements(screenshot_path)
                elements = result.get('elements', [])
                
                if elements:
                    ui_elements_text = "\n\nAVAILABLE UI ELEMENTS (detected by OmniParser):\n"
                    ui_elements_text += omniparser.get_all_elements_text(elements)
                    print(f"   Found {len(elements)} clickable UI elements")
                    self.logger.info("OmniParser detected %d UI elements", len(elements))
                else:
                    print("   ⚠️  No UI elements detected")
                    
            except Exception as e:
                self.logger.warning("OmniParser detection failed: %s", e)
                print(f"   ⚠️  OmniParser detection failed, continuing without element detection")
                ui_elements_text = "\n(UI element detection unavailable)"
            
            # Step 1.5: Use refiner to analyze screenshot and suggest action
            print("🔍 Analyzing screenshot with refiner...")
            refiner_context = f"""GOAL: {goal}

CURRENT SCREEN DESCRIPTION:
{screen_description}

{ui_elements_text}

PREVIOUS ACTIONS:
{self._format_previous_actions(execution_history)}

YOU MUST analyze the available UI elements and decide the SINGLE NEXT ACTION.

CRITICAL INSTRUCTIONS FOR ELEMENT SELECTION:
1. Review ALL available UI elements above (icon 0, icon 1, icon 2, etc.)
2. For each element, consider:
   - Description: What is it?
   - Position: Where is it on screen (center coordinates)?
   - Size: How big is it (from bbox)?
   - Type: Is it text, icon, button?
3. Choose the BEST element for the current step
4. In your response, provide:
   - WHICH specific element ID you selected (e.g., "icon 5")
   - WHY you selected it (description, position, size match your need)
   - EXACT description to search for

EXAMPLES OF GOOD ELEMENT SELECTION:

Example 1 - Opening Chrome:
  Available: icon 103: 'Google Chrome' (type: icon) at center (407, 973), icon 98: 'Google Chrome' (type: icon) at center (267, 972)
  Selection: "icon 103" because it's labeled 'Google Chrome', type is icon (clickable), and positioned at bottom taskbar (y=973)
  Search term: "Google Chrome"

Example 2 - Clicking URL bar:
  Available: icon 4: 'runpod.net/session' (type: text) at center (605, 97)
  Selection: "icon 4" because it's wide (730px), near top (y=97), contains URL, perfect URL bar dimensions
  Search term: "URL bar" (will use geometric detection)

Example 3 - Clicking a button:
  Available: icon 15: 'Submit' (type: text) at center (850, 600)
  Selection: "icon 15" because it says 'Submit', positioned in bottom-right where buttons typically are
  Search term: "Submit"

Return JSON:
{{
  "analysis": "what you see on screen and its relevance to the goal",
  "selected_element_id": "icon X (the specific element you chose, or null if none)",
  "element_selection_reasoning": "why this element is the right choice based on description/position/size",
  "suggested_action": "the specific next action using the element's description",
  "tool_recommendation": "which tool to use (click_element, type_text, hotkey, etc.)",
  "parameters": {{"element_description": "exact text from the element's description"}},
  "reasoning": "why this action achieves the current step of the goal"
}}"""
            
            try:
                # Call refiner with proper system prompt
                refiner_response = self.refiner.llm.get_response_text(
                    [
                        {"role": "system", "content": "You are an expert at analyzing UI elements and selecting the best one for a given task. Always return valid JSON with no markdown formatting."},
                        {"role": "user", "content": refiner_context}
                    ],
                    temperature=0.1
                )
                
                # Log raw response for debugging
                self.logger.debug("Refiner raw response: %s", refiner_response[:500])
                
                # Check if response is empty
                if not refiner_response or not refiner_response.strip():
                    raise ValueError("Refiner returned empty response")
                
                # Try to parse refiner suggestion
                import json
                cleaned_response = refiner_response.strip().replace("```json", "").replace("```", "").strip()
                refiner_suggestion = json.loads(cleaned_response)
                
                print(f"💡 Refiner analysis: {refiner_suggestion.get('analysis', 'N/A')[:100]}...")
                print(f"💡 Selected element: {refiner_suggestion.get('selected_element_id', 'N/A')}")
                print(f"💡 Selection reasoning: {refiner_suggestion.get('element_selection_reasoning', 'N/A')[:150]}...")
                print(f"💡 Suggested action: {refiner_suggestion.get('suggested_action', 'N/A')[:100]}...")
                
                # Add refiner suggestion to context for decision
                screen_description += f"\n\nREFINER ANALYSIS:\n{refiner_suggestion.get('analysis', '')}\n"
                screen_description += f"SELECTED ELEMENT: {refiner_suggestion.get('selected_element_id', 'none')}\n"
                screen_description += f"SELECTION REASONING: {refiner_suggestion.get('element_selection_reasoning', '')}\n"
                screen_description += f"SUGGESTED ACTION: {refiner_suggestion.get('suggested_action', '')}\n"
                screen_description += f"RECOMMENDED TOOL: {refiner_suggestion.get('tool_recommendation', '')}"
                
            except Exception as e:
                self.logger.warning("Refiner analysis failed: %s", e)
                # Log the actual response if available for debugging
                if 'refiner_response' in locals():
                    self.logger.debug("Failed response content: %s", refiner_response[:500] if refiner_response else "None")
                print(f"⚠️  Refiner analysis failed: {str(e)[:100]}")
                print(f"   Continuing without refiner guidance...")
            
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
        print(f"\n⚠️  MAX ITERATIONS REACHED ({self.max_iterations})")
        print(f"   The agent continued iterating without explicitly completing the task")
        print(f"   This may indicate the goal was achieved but not detected")
        return f"⚠️  Reached maximum iterations ({self.max_iterations}) without explicit completion.\n\n{summary}"
    
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
            f"\n**CRITICAL COMPLETION CHECK**:",
            f"Ask yourself: Is the user's ENTIRE goal now achieved and visible on screen?",
            f"- If YES: Set is_complete=true immediately! Do NOT continue iterating!",
            f"- If NO: Proceed with next action",
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

