"""
Cerebras LLM configuration for CrewAI agents.
"""

import os
from crewai import LLM


def get_cerebras_llm(model_name: str = "cerebras/llama3.1-8b", temperature: float = 0.5):
    """
    Configure Cerebras LLM for CrewAI agents.
    
    Args:
        model_name: Cerebras model name (e.g., "cerebras/llama3.1-70b" or "cerebras/llama3.1-8b")
        temperature: Temperature for response generation
        
    Returns:
        Configured LLM instance
    """
    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        raise ValueError("CEREBRAS_API_KEY environment variable not set")
    
    return LLM(
        model=model_name,
        api_key=api_key,
        base_url="https://api.cerebras.ai/v1",
        temperature=temperature,
        # Optional parameters for better performance
        top_p=1,
        max_completion_tokens=8192,
        # response_format={"type": "json_object"}  # Uncomment if you need JSON responses
    )


# OpenAI GPT-5-nano configuration for cost-effective operations
def get_openai_gpt5_nano_llm(temperature: float = 0.5):
    """
    Configure OpenAI GPT-5-nano LLM for CrewAI agents.
    
    Args:
        temperature: Temperature for response generation
        
    Returns:
        Configured LLM instance
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    return LLM(
        model="gpt-4o-mini",
        api_key=api_key,
        base_url="https://api.openai.com/v1",
        temperature=temperature,
        # Cost-optimized parameters
        max_completion_tokens=2048,  # Limit tokens to control costs
        top_p=0.9
    )


# Lazy-loaded LLM instances (created only when accessed)
def get_lead_finder_llm():
    """Get Cerebras llama3.1-8b LLM for lead finding."""
    return get_cerebras_llm(model_name="cerebras/llama3.1-8b", temperature=0.3)

def get_analysis_llm():
    """Get Cerebras llama3.1-8b LLM for analysis."""
    return get_cerebras_llm(model_name="cerebras/llama3.1-8b", temperature=0.7)

def get_cost_effective_llm():
    """Get GPT-5-nano LLM for cost-effective operations."""
    return get_openai_gpt5_nano_llm(temperature=0.3)

# Pre-configured LLM instances (lazy loading - only created when accessed)
class LazyLLM:
    def __init__(self, factory_func):
        self._factory_func = factory_func
        self._instance = None
    
    def __getattr__(self, name):
        if self._instance is None:
            self._instance = self._factory_func()
        return getattr(self._instance, name)

LEAD_FINDER_LLM = LazyLLM(get_lead_finder_llm)
ANALYSIS_LLM = LazyLLM(get_analysis_llm)
COST_EFFECTIVE_LLM = LazyLLM(get_cost_effective_llm)
