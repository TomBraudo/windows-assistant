import json
from typing import List, Dict

from .llm import LLMClient
from app.tools.tool_catalog import get_refiner_tools_text


class PromptRefiner:
    """
    A lightweight agent that refines raw user input into a clearer,
    tool-friendly instruction before passing it to the main Windows agent.

    Uses an OpenRouter-hosted Grok model for fast reasoning and rewriting.
    """

    def __init__(self, model: str = "openrouter/tngtech/deepseek-r1t2-chimera:free"):
        self.llm = LLMClient(model)
        tools_text = get_refiner_tools_text()
        # IMPORTANT: Output MUST be strict JSON so the main agent can parse it.
        self.system_prompt = (
            "You are a prompt refiner for a Windows automation agent.\n\n"
            f"{tools_text}\n\n"
            "Your job is to create an EXECUTION PLAN that breaks down the user's request into sequential steps.\n"
            "IMPORTANT: Each step should use ONLY ONE tool. The agent will execute these steps one at a time,\n"
            "passing the results from each step to the next.\n\n"
            "RESPONSE FORMAT (must be valid JSON, no extra text):\n"
            "{\n"
            '  \"instruction\": \"<overall refined natural language instruction>\",\n'
            '  \"execution_plan\": [\n'
            '    {\n'
            '      \"step\": 1,\n'
            '      \"tool\": \"tool_name\",\n'
            '      \"description\": \"what this step accomplishes\",\n'
            '      \"instruction\": \"specific instruction for this tool call\"\n'
            '    },\n'
            '    ...\n'
            '  ]\n'
            "}\n\n"
            "Guidelines:\n"
            "- Break complex requests into multiple steps (e.g., research then create document)\n"
            "- Each step must use exactly ONE tool from the list above\n"
            "- Order steps logically (e.g., web_search before create_presentation)\n"
            "- Be explicit about filenames (with extensions), app names, and desired outputs\n"
            "- The 'instruction' for each step should be clear about what data to use from previous steps\n\n"
            "**CRITICAL - IMAGE HANDLING:**\n"
            "- If you see '[User attached image: <path>]' in the user input, you MUST include analyze_image as the FIRST step\n"
            "- Step 1 must be: analyze_image with the image path and appropriate question\n"
            "- Subsequent steps should use the image analysis result as context\n"
            "- Example: If user says 'what's in this image', create 1 step with analyze_image\n"
            "- Example: If user says 'describe this screenshot and create a report', create 2 steps:\n"
            "  Step 1: analyze_image to understand what's in the image\n"
            "  Step 2: create_note using the analysis from step 1\n\n"
            "- When the user mentions an app by a friendly name, make it clear in the instruction\n"
            "- Do NOT mention tool/function names or write pseudo-calls like '<function(...)>' inside instructions\n"
            "- Do NOT explain your reasoning. Do NOT wrap the JSON in markdown\n"
            "Return ONLY the JSON object, nothing else."
        )

    def refine(self, user_input: str) -> Dict[str, object]:
        """
        Refine the original user input into an execution plan with ordered steps.

        Returns a dict with:
            - instruction: str (overall instruction)
            - execution_plan: List[Dict] (ordered list of steps, each with one tool)
        """
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input},
        ]
        raw = self.llm.get_response_text(messages)

        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("Refiner response is not a JSON object")
            instruction = data.get("instruction") or user_input
            execution_plan = data.get("execution_plan") or []
            if not isinstance(execution_plan, list):
                execution_plan = []
            return {"instruction": instruction, "execution_plan": execution_plan}
        except Exception as e:
            # Fallback: use original input, empty execution plan
            return {"instruction": user_input, "execution_plan": []}

