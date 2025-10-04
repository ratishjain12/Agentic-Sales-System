"""
Lead Clerk Agent for processing conversation results and storing data.
"""

from crewai import Agent
from ..config.sdr_config import get_sdr_llm
from ..prompts.clerk_prompts import LEAD_CLERK_PROMPT


def create_lead_clerk_agent() -> Agent:
    """
    Create the Lead Clerk Agent for processing conversation results.

    Returns:
        Agent: CrewAI Agent configured for lead processing
    """
    return Agent(
        role="Lead Clerk Specialist",
        goal="Process conversation results and decide whether to store lead data or trigger follow-up actions",
        backstory="""You are a professional lead clerk with expertise in analyzing sales conversation 
        results and determining the appropriate next steps. You understand the nuances of different 
        conversation outcomes and can make intelligent decisions about lead qualification and follow-up actions.""",
        tools=[],  # Will be added when needed
        llm=get_sdr_llm(temperature=0.3),  # Lower temperature for consistent processing
        verbose=True,
        allow_delegation=False,
        max_iter=1,
        max_execution_time=60,  # 1 minute for processing
        memory=False,
        planning=False
    )


# Singleton instance
lead_clerk_agent = create_lead_clerk_agent()
