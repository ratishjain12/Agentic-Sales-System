"""
CrewAI Lead Finder Agent implementation using Cerebras LLM.
"""

from crewai import Agent
from ..llm_config import COST_EFFECTIVE_LLM, LEAD_FINDER_LLM
from ..tools.crewai_foursquare_tool import foursquare_search_tool_instance
from ..prompts import LEAD_FINDER_AGENT_PROMPT


def create_lead_finder_agent(use_cost_effective: bool = True) -> Agent:
    """
    Create a CrewAI Lead Finder Agent with cost-effective LLM.
    
    Args:
        use_cost_effective: If True, use GPT-5-nano; if False, use Cerebras llama3.1-8b
    
    Returns:
        Configured CrewAI Agent instance
    """
    llm_to_use = COST_EFFECTIVE_LLM if use_cost_effective else LEAD_FINDER_LLM
    
    return Agent(
        role='Lead Finder Specialist',
        goal='Find and analyze high-quality business leads using Foursquare Places API',
        backstory=(
            "You are an experienced sales development specialist with deep knowledge "
            "of business lead generation. You excel at identifying potential customers "
            "and extracting valuable contact information for sales teams. Your expertise "
            "lies in understanding business categories, analyzing customer ratings, and "
            "qualifying leads based on multiple criteria."
        ),
        tools=[foursquare_search_tool_instance],
        llm=llm_to_use,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        max_execution_time=300,  # 5 minutes max execution time
        memory=False,  # Disable memory to avoid embedding issues
        planning=False  # Disable planning to avoid embedding issues
    )


# Agent instances are created on-demand to avoid initialization issues
