"""
CrewAI Tasks for Map-based Lead Finding Workflow.
"""

from crewai import Task
from ..sub_agents.map_search_agent import create_lead_finder_agent


def create_map_lead_search_task(query: str, location: str, radius: int = 1000, limit: int = 20, use_cost_effective: bool = True) -> Task:
    """
    Create a task for searching business leads.
    
    Args:
        query: Business type or category to search for
        location: Location to search in
        radius: Search radius in meters
        limit: Maximum number of results
        
    Returns:
        Configured CrewAI Task
    """
    return Task(
        description=f"""
        Search for {query} businesses in {location} within a {radius}m radius.
        
        Use the Foursquare Search Tool to find businesses matching the criteria:
        - Query: "{query}"
        - Location: "{location}"
        - Radius: {radius} meters
        - Limit: {limit} results
        
        IMPORTANT: The Foursquare Search Tool returns formatted business data as text. 
        Each business entry contains: fsq_id, name, address, phone, website, rating, distance, categories.
        
        For each business found, analyze and provide:
        1. Complete business information (name, address, phone, website)
        2. Business categories and ratings
        3. Distance from search center
        4. Lead qualification score (1-10) based on:
           - Completeness of contact information
           - Business rating (if available)
           - Relevance to search query
           - Distance from search location
        
        Format the results as a structured report with:
        - Executive summary of findings
        - Detailed business listings
        - Top 5 highest-qualified leads
        - Recommendations for follow-up
        """,
        expected_output=f"""
        A comprehensive lead generation report containing:
        
        1. EXECUTIVE SUMMARY:
           - Total businesses found: [number]
           - High-quality leads identified: [number]
           - Average lead score: [score]
           - Geographic distribution analysis
        
        2. DETAILED BUSINESS LISTINGS:
           For each business found, include:
           - Business Name
           - Complete Address
           - Phone Number (if available)
           - Website (if available)
           - Business Categories
           - Customer Rating (if available)
           - Distance from search center
           - Lead Qualification Score (1-10)
           - Notes and Observations
        
        3. TOP 5 HIGHEST-QUALIFIED LEADS:
           Ranked list of the best prospects with:
           - Lead score and reasoning
           - Contact information completeness
           - Recommended next steps
        
        4. RECOMMENDATIONS:
           - Suggested follow-up strategies
           - Priority order for outreach
           - Additional research suggestions
           - Geographic expansion opportunities
        """,
        agent=create_lead_finder_agent(use_cost_effective=use_cost_effective)
    )


def create_map_lead_analysis_task(business_data: str, use_cost_effective: bool = True) -> Task:
    """
    Create a task for analyzing existing business data.
    
    Args:
        business_data: String containing business information to analyze
        
    Returns:
        Configured CrewAI Task
    """
    return Task(
        description=f"""
        Analyze the following business data and provide lead qualification insights:
        
        {business_data}
        
        For each business, evaluate:
        1. Contact information completeness
        2. Business category relevance
        3. Geographic desirability
        4. Customer rating analysis
        5. Competitive positioning
        
        Provide recommendations for:
        - Lead prioritization
        - Outreach strategies
        - Follow-up timing
        - Additional research needs
        """,
        expected_output="""
        A detailed lead analysis report with:
        
        1. LEAD QUALIFICATION MATRIX:
           - Business name and lead score
           - Contact completeness rating
           - Geographic score
           - Category relevance score
           - Overall recommendation
        
        2. OUTREACH STRATEGY:
           - Recommended approach for each lead
           - Timing suggestions
           - Key talking points
           - Potential objections and responses
        
        3. PRIORITY RANKING:
           - Hot leads (immediate follow-up)
           - Warm leads (schedule follow-up)
           - Cold leads (long-term nurturing)
        
        4. NEXT STEPS:
           - Immediate actions required
           - Research gaps to fill
           - Tools and resources needed
        """,
        agent=create_lead_finder_agent(use_cost_effective=use_cost_effective)
    )