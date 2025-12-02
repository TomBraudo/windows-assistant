import os
from typing import List, Dict

from .llm import LLMClient


class PromptRefiner:
    """
    A lightweight agent that refines raw user input into a clearer,
    tool-friendly instruction before passing it to the main Windows agent.

    Uses an OpenRouter-hosted Grok model for fast reasoning and rewriting.
    """

    def __init__(self, model: str = "openrouter/x-ai/grok-4.1-fast:free"):
        self.llm = LLMClient(model)
        self.system_prompt = (
            "You are a prompt refiner for a Windows automation agent that controls tools like:\n"
            "- file search and opening (including Word documents),\n"
            "- web search, image search and download,\n"
            "- application launching.\n\n"
            "Given the raw user input, rewrite it as a single, clear instruction that is easy for a "
            "tool-using agent to execute. Be explicit about filenames (with extensions), apps, and "
            "targets, but do NOT mention tools or functions by name. Do not explain anything. "
            "Return ONLY the refined instruction, nothing else."
        )

    def refine(self, user_input: str) -> str:
        """
        Refine the original user input into a clearer instruction.
        """
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input},
        ]
        return self.llm.get_response_text(messages)


