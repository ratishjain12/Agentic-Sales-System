"""
Research Lead Agent - Gathers comprehensive business insights using Exa search.
"""
from crewai import Agent
from ..config.sdr_config import get_sdr_llm
from ..tools.exa_search_tool import exa_search_tool
from ..prompts.research_prompts import RESEARCH_LEAD_PROMPT


def create_research_lead_agent() -> Agent:
    """
    Create a Research Lead Agent for gathering business insights.

    This agent uses Exa search to research businesses without websites,
    gathering information about their services, customer reviews, online presence,
    competitors, and opportunities for website development.

    Returns:
        Agent: CrewAI Agent configured for business research
    """
    return Agent(
        role="Business Research Specialist",
        goal="Research businesses without websites to understand their services, customer feedback, online presence, competitors, and identify specific opportunities where a website would help them grow",
        backstory="""You are an expert business researcher specializing in small to medium businesses
        that don't have their own websites. You excel at using web search to gather comprehensive
        insights from various sources including review sites (Google, Yelp, Facebook), social media,
        industry publications, and competitor analysis. You have a keen eye for identifying customer
        pain points and understanding how digital presence (or lack thereof) impacts business growth.

        Your research is thorough yet concise, always focusing on actionable insights that can be
        used to create personalized sales proposals. You know how to dig deep into customer reviews
        to find real pain points, assess competitive landscape, and identify specific website features
        that would benefit each unique business.""",
        verbose=True,
        allow_delegation=False,
        tools=[exa_search_tool],
        llm=get_sdr_llm(temperature=0.3),  # Lower temperature for factual research
        max_iter=15,  # Allow multiple search iterations for thorough research
    )


# Create singleton instance for easy import
research_lead_agent = create_research_lead_agent()
