# src/config/cerebras_client.py
"""
Pure Cerebras SDK configuration - NO OpenAI dependencies!
"""
from cerebras.cloud.sdk import Cerebras
import os
from typing import Optional


class CerebrasConfig:
    """Configuration for Cerebras SDK."""

    _client: Optional[Cerebras] = None

    # Cerebras API settings
    BASE_URL = os.getenv("CEREBRAS_BASE_URL", "https://api.cerebras.net/v1")
    API_KEY = os.getenv("CEREBRAS_API_KEY")

    # Available models
    LLAMA_3_1_8B = "llama3.1-8b"
    LLAMA_3_1_70B = "llama3.1-70b"
    LLAMA_3_3_70B = "llama3.3-70b"

    @classmethod
    def get_client(cls) -> Cerebras:
        """
        Get or create the Cerebras SDK client instance.

        Returns:
            Cerebras: Cerebras SDK client

        Raises:
            ValueError: If CEREBRAS_API_KEY is not set
        """
        if cls._client is None:
            if not cls.API_KEY:
                raise ValueError("CEREBRAS_API_KEY environment variable not set")
            cls._client = Cerebras(api_key=cls.API_KEY)
        return cls._client

    @classmethod
    def chat_completion(
        cls,
        messages: list,
        model: str = "llama3.3-70b",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ):
        """
        Create a chat completion using Cerebras SDK.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (llama3.1-8b, llama3.1-70b, llama3.3-70b)
            temperature: Temperature for sampling (0.0-1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional arguments for Cerebras API

        Returns:
            Cerebras chat completion response
        """
        client = cls.get_client()
        return client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    @classmethod
    def reset(cls):
        """Reset client instance (useful for testing)."""
        cls._client = None


# Convenience functions
def get_cerebras_client() -> Cerebras:
    """
    Get the Cerebras SDK client.

    Returns:
        Cerebras: Cerebras SDK client instance
    """
    return CerebrasConfig.get_client()


def cerebras_chat(
    messages: list,
    model: str = "llama3.3-70b",
    temperature: float = 0.7,
    **kwargs
):
    """
    Create a chat completion using Cerebras SDK.

    Args:
        messages: List of message dicts
        model: Model name
        temperature: Temperature setting
        **kwargs: Additional arguments

    Returns:
        Chat completion response
    """
    return CerebrasConfig.chat_completion(
        messages=messages,
        model=model,
        temperature=temperature,
        **kwargs
    )