"""
Enhanced Prompt Refiner with intelligent element filtering and step-by-step planning.
"""

import json
from typing import List, Dict
from .llm import LLMClient
from app.tools.tool_catalog import get_refiner_tools_text


class PromptRefiner:
    """
    Refines vague user requests into detailed, step-by-step execution plans.
    Uses Groq for fast, intelligent refinement with element filtering.
    """
    
    def __init__(self, model: str = "groq/llama-3.3-70b-versatile"):
        """Initialize with Groq for speed."""
        self.llm = LLMClient(model)
        tools_text = get_refiner_tools_text()
        
        self.system_prompt = (
            "You are an expert at transforming vague requests into detailed, step-by-step execution plans.\n\n"
            f"{tools_text}\n\n"
            "CRITICAL: BREAK COMPLEX REQUESTS INTO ATOMIC STEPS\n\n"
            "Example: 'open daily dose of internet'\n"
            "→ Step 1: Click 'Google Chrome' icon on taskbar\n"
            "→ Step 2: Use Ctrl+L hotkey to focus URL bar\n"
            "→ Step 3: Type 'youtube.com'\n"
            "→ Step 4: Press Enter\n"
            "→ Step 5: Click YouTube search bar\n"
            "→ Step 6: Type 'daily dose of internet'\n"
            "→ Step 7: Press Enter\n\n"
            "RULES FOR COMPUTER CONTROL:\n"
            "1. ONE action per step (click OR type OR hotkey, not multiple)\n"
            "2. Be SPECIFIC about UI elements:\n"
            "   - Taskbar: 'Chrome icon' or 'File Explorer icon'\n"
            "   - URL bar: Use Ctrl+L (more reliable than clicking)\n"
            "   - Buttons: Use exact text, e.g., 'Submit button'\n"
            "3. For empty/invisible URL bars, ALWAYS use Ctrl+L hotkey\n"
            "4. Include element_filter when clicking:\n"
            "   - Taskbar icons: position_filter={'y_min': 0.9}, keyword_filter=['chrome']\n"
            "   - URL bars: position_filter={'y_max': 0.15}, size_filter={'min_aspect_ratio': 10}\n"
            "   - Search bars: type_filter=['text'], keyword_filter=['search']\n\n"
            "RESPONSE FORMAT (JSON only, no markdown):\n"
            "{\n"
            '  "instruction": "Clear summary of the goal",\n'
            '  "execution_plan": [\n'
            "    {\n"
            '      "step": 1,\n'
            '      "tool": "click_element",\n'
            '      "element_description": "Google Chrome",\n'
            '      "element_filter": {\n'
            '        "position_filter": {"y_min": 0.9},\n'
            '        "type_filter": ["icon"],\n'
            '        "keyword_filter": ["chrome", "browser"]\n'
            "      },\n"
            '      "description": "Open browser from taskbar"\n'
            "    },\n"
            "    {\n"
            '      "step": 2,\n'
            '      "tool": "hotkey",\n'
            '      "keys": "ctrl+l",\n'
            '      "description": "Focus URL bar"\n'
            "    },\n"
            "    {\n"
            '      "step": 3,\n'
            '      "tool": "type_text",\n'
            '      "text": "youtube.com",\n'
            '      "description": "Type URL"\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "BE ATOMIC. BE SPECIFIC. ONE ACTION PER STEP.\n"
            "Return ONLY JSON, no extra text."
        )
    
    def refine(self, user_input: str) -> Dict[str, object]:
        """
        Refine user input into a detailed execution plan.
        
        Returns:
            {
                "instruction": str,
                "execution_plan": [
                    {
                        "step": int,
                        "tool": str,
                        "element_description": str (for click_element),
                        "element_filter": dict (for click_element),
                        "description": str,
                        ...tool-specific params
                    }
                ]
            }
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        raw = self.llm.get_response_text(messages, temperature=0.1)
        
        try:
            # Clean up markdown if present
            raw = raw.strip().replace("```json", "").replace("```", "")
            data = json.loads(raw)
            
            if not isinstance(data, dict):
                raise ValueError("Response is not a JSON object")
            
            instruction = data.get("instruction") or user_input
            execution_plan = data.get("execution_plan") or []
            
            if not isinstance(execution_plan, list):
                execution_plan = []
            
            return {
                "instruction": instruction,
                "execution_plan": execution_plan
            }
        
        except Exception as e:
            # Fallback: use original input
            return {
                "instruction": user_input,
                "execution_plan": []
            }
