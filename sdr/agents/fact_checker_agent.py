"""
Fact Checker Agent - Reviews and improves proposal drafts.
"""
from crewai import Agent
from ..config.sdr_config import get_fact_checker_llm
from ..prompts.proposal_prompts import FACT_CHECKER_PROMPT


def create_fact_checker_agent() -> Agent:
    """
    Create a Fact Checker Agent for reviewing and improving proposals.

    Returns:
        Agent: CrewAI Agent configured for fact checking and refinement
    """
    return Agent(
        role="Fact Checker & Quality Assurance",
        goal="Review and refine business proposals to ensure accuracy, professionalism, and persuasiveness",
        backstory="""You are a meticulous quality assurance specialist with a keen eye for detail.
        Your expertise lies in reviewing business proposals to ensure they are factually accurate,
        professionally written, and highly persuasive. You cross-reference claims with research data,
        eliminate errors, and enhance clarity while maintaining the personalized touch. You never let
        over-promises or generic language slip through.""",
        verbose=True,
        allow_delegation=False,
        llm=get_fact_checker_llm(),
        max_iter=3,
    )


# Create singleton instance for easy import
fact_checker_agent = create_fact_checker_agent()
