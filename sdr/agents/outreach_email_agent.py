"""
Outreach Email Agent for sending follow-up emails after successful calls.
"""

from crewai import Agent
from ..config.sdr_config import get_sdr_llm
from ..prompts.email_prompts import OUTREACH_EMAIL_PROMPT


def create_outreach_email_agent() -> Agent:
    """
    Create the Outreach Email Agent for sending follow-up emails.

    Returns:
        Agent: CrewAI Agent configured for email outreach
    """
    return Agent(
        role="Outreach Email Specialist",
        goal="Send professional follow-up emails to businesses that agreed to receive proposals",
        backstory="""You are a professional email outreach specialist with expertise in crafting 
        compelling follow-up emails. You understand how to create personalized, professional emails 
        that maintain the momentum from successful phone conversations and drive business engagement.""",
        tools=[],  # Email tools will be added when needed
        llm=get_sdr_llm(temperature=0.5),
        verbose=True,
        allow_delegation=False,
        max_iter=2,
        max_execution_time=120,  # 2 minutes for email creation
        memory=False,
        planning=False
    )


# Singleton instance
outreach_email_agent = create_outreach_email_agent()
