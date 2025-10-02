# src/config/cerebras_client.py
from cerebras.cloud.sdk import Cerebras
from langchain_openai import ChatOpenAI
import os
from typing import Optional

class CerebrasConfig:
    _client: Optional[Cerebras] = None
    _llm: Optional[ChatOpenAI] = None
    
    # Cerebras API endpoint (OpenAI compatible)
    BASE_URL = os.getenv("CEREBRAS_BASE_URL")
    
    @classmethod
    def get_client(cls) -> Cerebras:
        """Get or create the Cerebras SDK client instance."""
        if cls._client is None:
            api_key = os.getenv("CEREBRAS_API_KEY")
            if not api_key:
                raise ValueError("CEREBRAS_API_KEY environment variable not set")
            cls._client = Cerebras(api_key=api_key)
        return cls._client
    
    @classmethod
    def get_llm(cls, model: str = "llama3.1-8b", temperature: float = 0.7, **kwargs) -> ChatOpenAI:
        """
        Get Cerebras LLM for CrewAI (OpenAI-compatible).
        
        Available models:
        - llama3.1-8b (fast, efficient)
        - llama3.1-70b (more capable)
        - llama3.3-70b (latest)
        """
        api_key = os.getenv("CEREBRAS_API_KEY")
        if not api_key:
            raise ValueError("CEREBRAS_API_KEY environment variable not set")
        
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=cls.BASE_URL,
            temperature=temperature,
            **kwargs
        )
    
    @classmethod
    def reset(cls):
        """Reset instances (useful for testing)."""
        cls._client = None
        cls._llm = None


# Convenience functions
def get_cerebras_client() -> Cerebras:
    """Get the Cerebras SDK client."""
    return CerebrasConfig.get_client()

def get_cerebras_llm(model: str = "llama3.1-8b", **kwargs) -> ChatOpenAI:
    """Get Cerebras LLM for CrewAI."""
    return CerebrasConfig.get_llm(model=model, **kwargs)