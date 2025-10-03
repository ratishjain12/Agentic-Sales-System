"""
Research Crew - Orchestrates business research using the Research Lead Agent.
"""
from typing import Dict, Any
from crewai import Crew, Task, Process
from .research_lead_agent import research_lead_agent
from ..prompts.research_prompts import RESEARCH_LEAD_PROMPT


class ResearchCrew:
    """
    Crew for researching businesses without websites.
    """

    def __init__(self):
        """Initialize the Research Crew."""
        self.research_agent = research_lead_agent

    def create_research_task(self, business_data: Dict[str, Any]) -> Task:
        """
        Create a research task for the Research Lead Agent.

        Args:
            business_data: Dictionary containing business information
                Expected keys: name, address/location, phone, industry (optional)

        Returns:
            Task for business research
        """
        # Format business data for the prompt
        business_info = "\n".join([f"- {k}: {v}" for k, v in business_data.items()])

        # Extract key info for search context
        business_name = business_data.get('name', 'Unknown Business')
        location = business_data.get('address') or business_data.get('location', '')
        industry = business_data.get('industry', '')

        description = f"""
{RESEARCH_LEAD_PROMPT}

### BUSINESS TO RESEARCH
{business_info}

### YOUR TASK
Research "{business_name}" {f"in {location}" if location else ""} {f"({industry})" if industry else ""}.

Use the exa_search tool to conduct thorough research following the strategy outlined above.
Perform multiple searches to gather comprehensive information from different angles.

Provide your findings in the structured format specified in the OUTPUT REQUIREMENTS section.
"""

        return Task(
            description=description,
            agent=self.research_agent,
            expected_output="""A comprehensive research summary (300-400 words) covering:
1. Business Profile - what they do and their reputation
2. Current Online Presence - their digital footprint
3. Customer Insights - reviews, ratings, pain points (3-4 bullet points)
4. Competitive Landscape - competitors with websites
5. Website Opportunities - specific benefits (3-4 bullet points)"""
        )

    def research_business(self, business_data: Dict[str, Any]) -> str:
        """
        Research a business and return comprehensive insights.

        Args:
            business_data: Dictionary containing business information
                Required: name
                Optional: address/location, phone, email, industry

        Returns:
            Research findings as a string

        Example:
            >>> crew = ResearchCrew()
            >>> business_data = {
            ...     "name": "The Coffee Shop",
            ...     "address": "123 Main St, Springfield",
            ...     "phone": "+1234567890",
            ...     "industry": "Food & Beverage"
            ... }
            >>> research = crew.research_business(business_data)
        """
        # Validate required fields
        if 'name' not in business_data:
            raise ValueError("business_data must contain 'name' field")

        # Create task
        research_task = self.create_research_task(business_data)

        # Create crew with single agent
        crew = Crew(
            agents=[self.research_agent],
            tasks=[research_task],
            process=Process.sequential,
            verbose=True
        )

        # Execute the crew
        result = crew.kickoff()

        # Return the research findings
        return str(result)


# Create singleton instance for easy import
research_crew = ResearchCrew()


def research_business(business_data: Dict[str, Any]) -> str:
    """
    Convenience function to research a business.

    Args:
        business_data: Dictionary containing business information

    Returns:
        Research findings
    """
    return research_crew.research_business(business_data)
