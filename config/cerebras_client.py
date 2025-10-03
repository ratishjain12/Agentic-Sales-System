from dotenv import load_dotenv; load_dotenv()
# src/config/cerebras_client.py
from cerebras.cloud.sdk import Cerebras
from crewai import LLM
import os
from typing import Optional

class CerebrasConfig:
    """Configuration for Cerebras SDK."""

    _client: Optional[Cerebras] = None
    _llm: Optional[LLM] = None
    
    # Cerebras API endpoint (OpenAI-compatible). Defaults to public endpoint
    BASE_URL = os.getenv("CEREBRAS_BASE_URL", "https://api.cerebras.ai/v1")
    
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
    def get_crewai_llm(
        cls,
        model: str = "cerebras/llama3.1-70b",
        temperature: float = 0.5,
        **kwargs,
    ) -> LLM:
        """
        Get CrewAI's LLM configured for Cerebras via LiteLLM.
        Mirrors the snippet:
            LLM(model="cerebras/llama3.1-70b", api_key=..., base_url="https://api.cerebras.ai/v1", ...)
        """
        api_key = os.getenv("CEREBRAS_API_KEY")
        if not api_key:
            raise ValueError("CEREBRAS_API_KEY environment variable not set")

        return LLM(
            model=model,
            api_key=api_key,
            base_url=cls.BASE_URL,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
            **kwargs,
        )

    @classmethod
    def reset(cls):
        """Reset instances (useful for testing)."""
        cls._client = None
        cls._llm = None


# Convenience functions
def get_cerebras_client() -> Cerebras:
    """
    Get the Cerebras SDK client.

    Returns:
        Cerebras: Cerebras SDK client instance
    """
    return CerebrasConfig.get_client()

def get_crewai_llm(model: str = "cerebras/llama3.1-70b", **kwargs) -> LLM:
    """Get CrewAI LLM configured for Cerebras."""
    return CerebrasConfig.get_crewai_llm(model=model, **kwargs)