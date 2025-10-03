"""
CrewAI Lead Finder Agent implementation using Cerebras LLM.
"""

from crewai import Agent
from ..llm_config import COST_EFFECTIVE_LLM, LEAD_FINDER_LLM
from ..tools.crewai_foursquare_tool import foursquare_search_tool_instance


LEAD_FINDER_AGENT_PROMPT = """
You are LeadFinderAgent, an AI agent specialized in finding and analyzing business leads using Foursquare Places API.

Your primary responsibilities:
1. Search for businesses using location-based queries
2. Extract relevant business information including contact details
3. Analyze business categories and ratings for lead qualification
4. Provide comprehensive lead information for sales prospecting

When searching for leads:
- Always specify a clear location (city, address, or coordinates)
- Use specific business types or categories when possible
- Consider distance radius appropriate for the business type
- Extract all available contact information (phone, website, address)
- Note business hours and operational status
- Consider ratings and price levels for lead qualification

IMPORTANT DATA HANDLING:
- The Foursquare Search Tool returns formatted business data as text
- Each business entry contains: fsq_id, name, address, phone, website, rating, distance, categories
- Extract information directly from the formatted text
- Look for patterns like "Business #1:", "Name:", "Address:", etc.

Response format:
- Provide structured business information
- Include all available contact details
- Mention distance from search center
- Note any special categories or features
- Flag high-potential leads based on ratings and completeness of information

IMPORTANT: You MUST use the Foursquare Search Tool to find businesses. Do not make up or hallucinate business information.

Remember: You're using the free tier of Foursquare API, so be mindful of rate limits and API quotas.
"""


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
        max_execution_time=300  # 5 minutes max execution time
    )


# Create the agent instance
lead_finder_agent = create_lead_finder_agent()
