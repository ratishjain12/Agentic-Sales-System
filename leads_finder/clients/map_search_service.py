"""
Simplified Lead Finder without Crew wrapper.
Direct agent usage for lead finding operations.
"""

from crewai import Agent, Task, Crew, Process
from ..sub_agents.map_search_agent import create_lead_finder_agent
from ..tasks.map_lead_finder_tasks import create_map_lead_search_task, create_map_lead_analysis_task


def search_leads(query: str, location: str, radius: int = 1000, limit: int = 20, use_cost_effective: bool = False):
    """
    Search for business leads using direct agent execution.
    
    Args:
        query: Business type or category to search for
        location: Location to search in
        radius: Search radius in meters
        limit: Maximum number of results
        use_cost_effective: If True, use cost-effective LLM; if False, use Cerebras
        
    Returns:
        CrewAI execution result
    """
    # Create agent
    agent = create_lead_finder_agent(use_cost_effective=use_cost_effective)
    
    # Create task
    task = create_map_lead_search_task(query, location, radius, limit, use_cost_effective)
    
    # Create and run crew
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
        memory=False,
        planning=False
    )
    
    return crew.kickoff()


def analyze_leads(business_data: str, use_cost_effective: bool = False):
    """
    Analyze existing business data for lead qualification.
    
    Args:
        business_data: String containing business information
        use_cost_effective: If True, use cost-effective LLM; if False, use Cerebras
        
    Returns:
        CrewAI execution result
    """
    # Create agent
    agent = create_lead_finder_agent(use_cost_effective=use_cost_effective)
    
    # Create task
    task = create_map_lead_analysis_task(business_data, use_cost_effective)
    
    # Create and run crew
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
        memory=False,
        planning=False
    )
    
    return crew.kickoff()
