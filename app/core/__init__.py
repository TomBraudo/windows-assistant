"""
Core module containing the agent's brain and LLM connection logic.
"""

from .llm import LLMClient
from .agent import Agent

__all__ = ["LLMClient", "Agent"]

