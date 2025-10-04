"""
Potential Lead Finder Agent implementation using CrewAI.
"""

from crewai import Agent, Task, Crew, Process
from leads_finder.sub_agents.map_search_agent import create_lead_finder_agent
from leads_finder.sub_agents.cluster_search_agent import create_cluster_search_agent
from config.cerebras_client import get_crewai_llm


def create_potential_lead_finder_agent(city: str) -> Crew:
    """
    Create Potential Lead Finder Agent that coordinates parallel searches.
    
    This agent follows the reference architecture pattern:
    - ParallelAgent equivalent using CrewAI
    - Coordinates MapSearch and ClusterSearch agents
    - Aggregates results from multiple sources
    
    Args:
        city: City name to search for business leads
        
    Returns:
        CrewAI Crew with parallel execution capabilities
    """
    
    # Create Map Search Agent (Foursquare-based)
    map_search_agent = create_lead_finder_agent(use_cost_effective=True)
    
    # Create Cluster Search Agent
    cluster_search_agent = create_cluster_search_agent(city)
    
    # Create coordination agent
    coordinator_agent = Agent(
        role="LeadFinderCoordinator",
        goal=f"Coordinate parallel business lead searches in {city}",
        backstory=(
            "You are a specialized coordinator agent responsible for managing "
            "parallel business lead searches from multiple data sources. "
            "Your role is to orchestrate searches, aggregate results, and "
            "ensure comprehensive lead discovery for the specified city."
        ),
        llm=get_crewai_llm(model="cerebras/gpt-oss-120b", temperature=0.2),
        verbose=True,
        allow_delegation=True,
        max_iter=1,
        max_execution_time=300,  # 5 minutes
        memory=False,
        planning=False
    )
    
    # Create coordination task
    coordination_task = Task(
        description=f"""
        Coordinate parallel business lead searches for {city}:
        
        1. Delegate to MapSearchAgent to find businesses using Foursquare Places API
        2. Delegate to ClusterSearchAgent to find businesses using custom cluster search
        3. Aggregate results from both sources
        4. Return combined business data with source attribution
        
        Ensure each business entry includes:
        - name: Business name
        - address: Full address
        - phone: Contact phone (if available)
        - website: Business website (if available)
        - category: Business category/type
        - rating: Business rating (if available)
        - source: "map_search" or "cluster_search"
        
        Return aggregated results as JSON array.
        """,
        agent=coordinator_agent,
        expected_output=(
            f"JSON array of business leads from {city} with fields: "
            "name, address, phone, website, category, rating, source. "
            "Each business must include source field indicating origin."
        ),
    )
    
    # Create crew with parallel execution
    crew = Crew(
        agents=[coordinator_agent],
        tasks=[coordination_task],
        process=Process.sequential,
        verbose=True,
    )
    
    return crew


def run_potential_lead_finder(city: str) -> str:
    """
    Run the potential lead finder workflow.
    
    Args:
        city: City name to search for business leads
        
    Returns:
        Combined results from all search sources
    """
    try:
        # Create potential lead finder crew
        crew = create_potential_lead_finder_agent(city)
        
        # Execute the workflow
        result = crew.kickoff()
        
        # Extract result
        for attr in ("raw", "output"):
            if hasattr(result, attr):
                return getattr(result, attr)
        
        try:
            return result.to_dict()
        except Exception:
            return str(result)
            
    except Exception as e:
        error_msg = f"Potential lead finder failed: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg


# For compatibility with reference pattern
def create_potential_lead_finder_crew(city: str) -> Crew:
    """Create potential lead finder crew (alias for compatibility)."""
    return create_potential_lead_finder_agent(city)
