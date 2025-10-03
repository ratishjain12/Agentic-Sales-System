"""
CrewAI Crew for Lead Finding Workflow.
"""

from crewai import Crew, Process
from ..sub_agents.crewai_lead_finder_agent import lead_finder_agent
from ..tasks.lead_finder_tasks import create_lead_search_task, create_lead_analysis_task


class LeadFinderCrew:
    """
    CrewAI Crew for orchestrating lead finding workflows.
    """
    
    def __init__(self, use_cost_effective: bool = True):
        """
        Initialize the Lead Finder Crew.
        
        Args:
            use_cost_effective: If True, use GPT-5-nano; if False, use Cerebras llama3.1-8b
        """
        self.use_cost_effective = use_cost_effective
        self.crew = None
        self._setup_crew()
    
    def _setup_crew(self):
        """Set up the CrewAI crew with agents and process."""
        # Import here to avoid circular imports
        from ..sub_agents.crewai_lead_finder_agent import create_lead_finder_agent
        
        # Create agent with cost-effective option
        agent = create_lead_finder_agent(use_cost_effective=self.use_cost_effective)
        
        self.crew = Crew(
            agents=[agent],
            tasks=[],  # Tasks will be added dynamically
            process=Process.sequential,
            verbose=True,
            memory=False,  # Disable memory to avoid embedding issues
            planning=False  # Disable planning to avoid embedding issues
        )
    
    def search_leads(self, query: str, location: str, radius: int = 1000, limit: int = 20):
        """
        Search for business leads using the CrewAI workflow.
        
        Args:
            query: Business type or category to search for
            location: Location to search in
            radius: Search radius in meters
            limit: Maximum number of results
            
        Returns:
            CrewAI execution result
        """
        # Create the search task
        search_task = create_lead_search_task(query, location, radius, limit, self.use_cost_effective)
        
        # Update crew with the new task
        self.crew.tasks = [search_task]
        
        # Execute the crew
        result = self.crew.kickoff()
        return result
    
    def analyze_leads(self, business_data: str):
        """
        Analyze existing business data for lead qualification.
        
        Args:
            business_data: String containing business information
            
        Returns:
            CrewAI execution result
        """
        # Create the analysis task
        analysis_task = create_lead_analysis_task(business_data, self.use_cost_effective)
        
        # Update crew with the new task
        self.crew.tasks = [analysis_task]
        
        # Execute the crew
        result = self.crew.kickoff()
        return result
    
    def multi_step_lead_generation(self, query: str, location: str, radius: int = 1000, limit: int = 20):
        """
        Perform a multi-step lead generation process:
        1. Search for leads
        2. Analyze the results
        
        Args:
            query: Business type or category to search for
            location: Location to search in
            radius: Search radius in meters
            limit: Maximum number of results
            
        Returns:
            Tuple of (search_result, analysis_result)
        """
        # Step 1: Search for leads
        print(f"🔍 Searching for {query} businesses in {location}...")
        search_result = self.search_leads(query, location, radius, limit)
        
        # Step 2: Analyze the results
        print("📊 Analyzing search results...")
        analysis_result = self.analyze_leads(str(search_result))
        
        return search_result, analysis_result


# Create a global instance for easy access (default to cost-effective)
lead_finder_crew = LeadFinderCrew(use_cost_effective=True)


def get_lead_finder_crew(use_cost_effective: bool = True) -> LeadFinderCrew:
    """
    Get the Lead Finder Crew instance.
    
    Args:
        use_cost_effective: If True, use GPT-5-nano; if False, use Cerebras llama3.1-8b
    
    Returns:
        LeadFinderCrew instance
    """
    return LeadFinderCrew(use_cost_effective=use_cost_effective)
