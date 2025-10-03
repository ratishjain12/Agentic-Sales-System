"""
Configuration for SDR agents using Cerebras.
"""
import os
from typing import Optional
from dotenv import load_dotenv
from crewai import LLM

# Load environment variables
load_dotenv()


class SDRConfig:
    """Configuration for SDR agents."""

    # Model configuration for different agents
    # Using llama3.3-70b for better quality proposals
    DEFAULT_MODEL = "llama3.3-70b"
    FAST_MODEL = "llama3.1-8b"  # For simpler tasks

    # Temperature settings
    CREATIVE_TEMPERATURE = 0.7  # For draft writing
    PRECISE_TEMPERATURE = 0.3   # For fact checking

    # Agent-specific settings
    DRAFT_WRITER_MODEL = DEFAULT_MODEL
    DRAFT_WRITER_TEMPERATURE = CREATIVE_TEMPERATURE

    FACT_CHECKER_MODEL = DEFAULT_MODEL
    FACT_CHECKER_TEMPERATURE = PRECISE_TEMPERATURE


def get_sdr_llm(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    **kwargs
):
    """
    Get a Cerebras LLM instance for SDR agents using LiteLLM's native Cerebras support.

    Args:
        model: Model name (defaults to SDRConfig.DEFAULT_MODEL)
        temperature: Temperature setting (defaults to 0.7)
        **kwargs: Additional arguments to pass to LLM

    Returns:
        LLM instance configured for Cerebras
    """
    model_name = model or SDRConfig.DEFAULT_MODEL

    # Use LiteLLM's native Cerebras support with cerebras/ prefix
    return LLM(
        model=f"cerebras/{model_name}",
        api_key=os.getenv("CEREBRAS_API_KEY"),
        temperature=temperature if temperature is not None else 0.7,
        **kwargs
    )


def get_draft_writer_llm():
    """Get LLM configured for draft writing."""
    return get_sdr_llm(
        model=SDRConfig.DRAFT_WRITER_MODEL,
        temperature=SDRConfig.DRAFT_WRITER_TEMPERATURE
    )


def get_fact_checker_llm():
    """Get LLM configured for fact checking."""
    return get_sdr_llm(
        model=SDRConfig.FACT_CHECKER_MODEL,
        temperature=SDRConfig.FACT_CHECKER_TEMPERATURE
    )
