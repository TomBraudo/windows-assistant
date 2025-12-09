import json
from typing import List, Dict, Any

from .llm import LLMClient


class ResponseJudge:
    """
    A second-pass LLM that reviews the agent's behavior and checks for hallucinations.

    It looks at:
      - original user input
      - refined instruction from the PromptRefiner
      - the full conversation history so far
      - the list of tools that were actually executed (names, args, results)
      - the final assistant text

    and decides whether the assistant hallucinated actions (e.g. claiming to create
    a PowerPoint without calling 'create_presentation').
    """

    def __init__(self, model: str = "openrouter/tngtech/deepseek-r1t2-chimera:free"):
        self.llm = LLMClient(model)
        self.system_prompt = (
            "You are a strict judge for a Windows automation agent that uses tools.\n\n"
            "You will be given, in JSON form:\n"
            "- original_user_input: the user's raw request\n"
            "- refined_instruction: the refiner's clarified instruction\n"
            "- history: the full conversation so far (system, user, assistant, and tool messages)\n"
            "- executed_tools: a list of tool calls that actually ran, with name, args, and result\n"
            "- final_text: the assistant's final natural language reply shown to the user\n\n"
            "Your job is to determine whether the final_text HALLUCINATES actions that did not "
            "actually happen. Examples of hallucination include:\n"
            "- Saying a PowerPoint/Word/file was created when 'create_presentation' or "
            "  'create_and_open_file' was never executed.\n"
            "- Mentioning that an app or URL was opened when 'launch_app' or 'open_url' was not executed.\n"
            "- Emitting fake function-like text such as '<function=...>' instead of using real tools.\n\n"
            "RESPONSE FORMAT (must be valid JSON, no extra text):\n"
            "{\n"
            '  \"hallucinated\": true or false,\n'
            '  \"reason\": \"short explanation\",\n'
            '  \"corrected_instruction\": \"if hallucinated, a clearer instruction that would fix it\",\n'
            '  \"recommended_tools\": [\"tool_name_1\", \"tool_name_2\", ...]\n'
            "}\n\n"
            "Guidelines:\n"
            "- If final_text clearly and only reports the actual tools that ran, set 'hallucinated' to false.\n"
            "- If final_text claims work that is not supported by executed_tools, set 'hallucinated' to true and "
            "  explain what is wrong in 'reason'.\n"
            "- When hallucinated is true, 'corrected_instruction' should restate what the agent SHOULD actually do "
            "  using tools (e.g. 'create and open a PowerPoint on the Desktop titled X with bullets Y and Z, using "
            "create_presentation and find_image').\n"
            "- 'recommended_tools' should list the tools that should be used on a retry to fix the problem.\n"
            "- Do NOT wrap your JSON in markdown. Return ONLY the JSON object.\n"
        )

    def review(
        self,
        original_user_input: str,
        refined_instruction: str,
        history: List[Dict[str, Any]],
        executed_tools: List[Dict[str, Any]],
        final_text: str,
    ) -> Dict[str, Any]:
        """
        Review the agent's behavior and return a judgment dict:
            - hallucinated: bool
            - reason: str
            - corrected_instruction: str
            - recommended_tools: List[str]
        """
        # Make history JSON-serializable (strip non-serializable Message objects)
        serializable_history: List[Dict[str, Any]] = []
        for h in history:
            if isinstance(h, dict):
                serializable_history.append(h)
            else:
                # Fallback: capture only role and content if present, otherwise string form
                entry: Dict[str, Any] = {}
                role = getattr(h, "role", None)
                content = getattr(h, "content", None)
                if role is not None:
                    entry["role"] = role
                if content is not None:
                    entry["content"] = content
                if not entry:
                    entry["repr"] = repr(h)
                serializable_history.append(entry)

        payload = {
            "original_user_input": original_user_input,
            "refined_instruction": refined_instruction,
            "history": serializable_history,
            "executed_tools": executed_tools,
            "final_text": final_text,
        }

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": json.dumps(payload)},
        ]

        raw = self.llm.get_response_text(messages)
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("Judge response is not a JSON object")
            # Ensure required keys with defaults
            hallucinated = bool(data.get("hallucinated", False))
            reason = data.get("reason") or ""
            corrected = data.get("corrected_instruction") or refined_instruction
            tools = data.get("recommended_tools") or []
            if not isinstance(tools, list):
                tools = []
            return {
                "hallucinated": hallucinated,
                "reason": reason,
                "corrected_instruction": corrected,
                "recommended_tools": tools,
            }
        except Exception:
            # If judge fails, treat as no hallucination
            return {
                "hallucinated": False,
                "reason": "Judge failed to parse response.",
                "corrected_instruction": refined_instruction,
                "recommended_tools": [],
            }


