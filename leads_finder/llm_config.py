"""
Optimized LLM configuration for Agentic Sales Agent.
Consolidates Cerebras and OpenAI configurations with lazy loading.
"""

import os
from typing import Optional
from crewai import LLM


class LLMConfig:
    """Centralized LLM configuration manager."""
    
    # Cerebras API endpoint (OpenAI-compatible)
    CEREBRAS_BASE_URL = os.getenv("CEREBRAS_BASE_URL", "https://api.cerebras.ai/v1")
    OPENAI_BASE_URL = "https://api.openai.com/v1"
    
    @classmethod
    def get_cerebras_llm(
        cls,
        model: str = "cerebras/llama3.1-8b",
        temperature: float = 0.5,
        **kwargs,
    ) -> LLM:
        """
        Get CrewAI LLM configured for Cerebras.
        
        Args:
            model: Cerebras model name
            temperature: Temperature for response generation
            **kwargs: Additional LLM parameters
            
        Returns:
            Configured LLM instance
        """
        api_key = os.getenv("CEREBRAS_API_KEY")
        if not api_key:
            raise ValueError("CEREBRAS_API_KEY environment variable not set")

        return LLM(
            model=model,
            api_key=api_key,
            base_url=cls.CEREBRAS_BASE_URL,
            temperature=temperature,
            top_p=kwargs.get("top_p", 1),
            max_completion_tokens=kwargs.get("max_completion_tokens", 8192),
            **{k: v for k, v in kwargs.items() if k not in ["top_p", "max_completion_tokens"]}
        )
    
    @classmethod
    def get_openai_llm(
        cls,
        model: str = "gpt-4o-mini",
        temperature: float = 0.5,
        **kwargs,
    ) -> LLM:
        """
        Get CrewAI LLM configured for OpenAI.
        
        Args:
            model: OpenAI model name
            temperature: Temperature for response generation
            **kwargs: Additional LLM parameters
            
        Returns:
            Configured LLM instance
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        return LLM(
            model=model,
            api_key=api_key,
            base_url=cls.OPENAI_BASE_URL,
            temperature=temperature,
            top_p=kwargs.get("top_p", 0.9),
            max_completion_tokens=kwargs.get("max_completion_tokens", 2048),
            **{k: v for k, v in kwargs.items() if k not in ["top_p", "max_completion_tokens"]}
        )


# Lazy-loaded LLM instances (created only when accessed)
class LazyLLM:
    """Lazy loading wrapper for LLM instances."""
    
    def __init__(self, factory_func):
        self._factory_func = factory_func
        self._instance: Optional[LLM] = None
    
    def __getattr__(self, name):
        if self._instance is None:
            self._instance = self._factory_func()
        return getattr(self._instance, name)
    
    def reset(self):
        """Reset the cached instance."""
        self._instance = None


# Pre-configured LLM instances
def get_lead_finder_llm() -> LLM:
    """Get Cerebras llama3.1-8b LLM for lead finding."""
    return LLMConfig.get_cerebras_llm(
        model="cerebras/llama3.1-8b",
        temperature=0.3,
        max_completion_tokens=4096
    )

def get_analysis_llm() -> LLM:
    """Get Cerebras llama3.1-8b LLM for analysis."""
    return LLMConfig.get_cerebras_llm(
        model="cerebras/llama3.1-8b",
        temperature=0.7,
        max_completion_tokens=4096
    )

def get_cost_effective_llm() -> LLM:
    """Get Cerebras llama3.1-8b LLM for cost-effective operations."""
    return LLMConfig.get_cerebras_llm(
        model="cerebras/llama3.1-8b",
        temperature=0.3,
        max_completion_tokens=2048
    )

def get_high_performance_llm() -> LLM:
    """Get Cerebras llama3.1-70b LLM for high-performance tasks."""
    return LLMConfig.get_cerebras_llm(
        model="cerebras/llama3.1-70b",
        temperature=0.5,
        max_completion_tokens=8192
    )

# Lazy-loaded instances
LEAD_FINDER_LLM = LazyLLM(get_lead_finder_llm)
ANALYSIS_LLM = LazyLLM(get_analysis_llm)
COST_EFFECTIVE_LLM = LazyLLM(get_cost_effective_llm)
HIGH_PERFORMANCE_LLM = LazyLLM(get_high_performance_llm)

# Convenience functions for backward compatibility
def get_crewai_llm(model: str = "cerebras/llama3.1-8b", **kwargs) -> LLM:
    """Get CrewAI LLM configured for Cerebras (backward compatibility)."""
    return LLMConfig.get_cerebras_llm(model=model, **kwargs)
