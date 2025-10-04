"""
Outreach Caller Agent for making phone calls to convince business owners.
"""

from crewai import Agent
from ..config.sdr_config import get_sdr_llm
from ..tools.phone_call_tool import phone_call_tool
from ..prompts.caller_prompts import OUTREACH_CALLER_AGENT_PROMPT


def create_outreach_caller_agent() -> Agent:
    """
    Create the Outreach Caller Agent for making phone calls to business owners.

    Returns:
        Agent: CrewAI Agent configured for making outreach calls
    """
    return Agent(
        role="Outreach Caller Specialist",
        goal="Make persuasive phone calls to business owners to present proposals and secure agreement to receive email follow-ups",
        backstory="""You are a professional outreach specialist with expertise in making
        persuasive phone calls to business owners. You use advanced AI voice technology to
        conduct natural, professional conversations that highlight the value of web solutions
        and secure permission to send detailed proposals via email. You understand the
        importance of being respectful, concise, and focused on the business owner's needs.""",
        tools=[phone_call_tool],
        llm=get_sdr_llm(temperature=0.5),
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        max_execution_time=600,  # 10 minutes for call completion
        memory=False,
        planning=False
    )


# Singleton instance
outreach_caller_agent = create_outreach_caller_agent()
