"""
Draft Writer Agent - Creates initial proposal drafts based on business research.
"""
from crewai import Agent
from ..config.sdr_config import get_draft_writer_llm
from ..prompts.proposal_prompts import DRAFT_WRITER_PROMPT


def create_draft_writer_agent() -> Agent:
    """
    Create a Draft Writer Agent for generating initial proposals.

    Returns:
        Agent: CrewAI Agent configured for draft writing
    """
    return Agent(
        role="Draft Writer",
        goal="Write personalized and compelling business proposals for website development services",
        backstory="""You are an experienced business proposal writer with expertise in
        website development services. You excel at understanding business needs from research
        and crafting personalized, persuasive proposals that resonate with business owners.
        You know how to highlight pain points and present solutions that drive action.""",
        verbose=True,
        allow_delegation=False,
        llm=get_draft_writer_llm(),
        max_iter=3,
    )


# Create singleton instance for easy import
draft_writer_agent = create_draft_writer_agent()
