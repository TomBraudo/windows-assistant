"""
LiteLLM wrapper for unified API handling across multiple providers.
Handles connection logic and provides a consistent interface.
"""

import os
from dotenv import load_dotenv
from litellm import completion

# Load environment variables
load_dotenv()


class LLMClient:
    """
    Wrapper for LiteLLM that provides a unified interface for multiple LLM providers.
    Handles API key management and provider selection.
    """
    
    def __init__(self, model: str = "groq/llama-3.3-70b-versatile"):
        """
        Initialize the LLM client.
        
        Args:
            model: Model identifier in LiteLLM format (e.g., "groq/llama-3.3-70b-versatile")
        """
        self.model = model
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify that the API key is configured for the selected model."""
        # Extract provider from model name
        provider = self.model.split("/")[0] if "/" in self.model else "unknown"

        # Check for required API keys
        if provider == "groq":
            if not os.getenv("GROQ_API_KEY"):
                raise ValueError("GROQ_API_KEY not found in environment variables")
        elif provider == "gemini":
            if not os.getenv("GOOGLE_API_KEY"):
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
        elif provider == "deepseek":
            if not os.getenv("DEEPSEEK_API_KEY"):
                raise ValueError("DEEPSEEK_API_KEY not found in environment variables")
        elif provider == "openrouter":
            # LiteLLM expects OPENROUTER_API_KEY; allow mapping from X_AI_GROK_API_KEY
            if not os.getenv("OPENROUTER_API_KEY"):
                grok_key = os.getenv("X_AI_GROK_API_KEY")
                if grok_key:
                    os.environ["OPENROUTER_API_KEY"] = grok_key
                else:
                    raise ValueError(
                        "OPENROUTER_API_KEY or X_AI_GROK_API_KEY not found in environment variables"
                    )
    
    def complete(self, messages: list, **kwargs):
        """
        Send a completion request to the LLM.
        
        Args:
            messages: List of message dictionaries with "role" and "content"
            **kwargs: Additional arguments to pass to LiteLLM completion
        
        Returns:
            The completion response from LiteLLM
        """
        try:
            response = completion(
                model=self.model,
                messages=messages,
                **kwargs
            )
            return response
        except Exception as e:
            raise ConnectionError(f"LLM API call failed: {e}")
    
    def get_response_text(self, messages: list, **kwargs) -> str:
        """
        Convenience method to get just the text content from a completion.
        
        Args:
            messages: List of message dictionaries
            **kwargs: Additional arguments for completion
        
        Returns:
            The text content of the response
        """
        response = self.complete(messages, **kwargs)
        return response.choices[0].message.content

