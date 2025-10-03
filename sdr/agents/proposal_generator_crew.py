"""
Proposal Generator Crew - Orchestrates proposal generation using Review/Critique pattern.

This crew implements the Generator-Critic pattern where:
1. Draft Writer Agent generates an initial proposal
2. Fact Checker Agent reviews and refines it
"""
from typing import Dict, Any
from crewai import Crew, Task, Process
from .draft_writer_agent import draft_writer_agent
from .fact_checker_agent import fact_checker_agent
from ..prompts.proposal_prompts import DRAFT_WRITER_PROMPT, FACT_CHECKER_PROMPT


class ProposalGeneratorCrew:
    """
    Crew for generating business proposals using sequential Review/Critique pattern.
    """

    def __init__(self):
        """Initialize the Proposal Generator Crew."""
        self.draft_writer = draft_writer_agent
        self.fact_checker = fact_checker_agent

    def create_draft_task(self, business_data: Dict[str, Any], research_result: str) -> Task:
        """
        Create a task for the Draft Writer Agent.

        Args:
            business_data: Dictionary containing business information
            research_result: Research findings about the business

        Returns:
            Task for draft writing
        """
        # Format business data for the prompt
        business_info = "\n".join([f"- {k}: {v}" for k, v in business_data.items()])

        description = f"""
{DRAFT_WRITER_PROMPT}

### BUSINESS DATA
{business_info}

### RESEARCH FINDINGS
{research_result}

Based on the above information, write a personalized, compelling proposal for this business.
"""

        return Task(
            description=description,
            agent=self.draft_writer,
            expected_output="A personalized 1-2 paragraph business proposal for website development services"
        )

    def create_fact_check_task(self, business_data: Dict[str, Any], research_result: str) -> Task:
        """
        Create a task for the Fact Checker Agent.

        Args:
            business_data: Dictionary containing business information
            research_result: Research findings about the business

        Returns:
            Task for fact checking and refinement
        """
        # Format business data for the prompt
        business_info = "\n".join([f"- {k}: {v}" for k, v in business_data.items()])

        description = f"""
{FACT_CHECKER_PROMPT}

### BUSINESS DATA
{business_info}

### RESEARCH FINDINGS
{research_result}

### DRAFT PROPOSAL TO REVIEW
{{{{ task_context }}}}

Review the draft proposal above and provide the final, polished version that is ready to send.
"""

        return Task(
            description=description,
            agent=self.fact_checker,
            expected_output="A refined, polished 1-2 paragraph business proposal free of errors and overpromises",
            context=[]  # Will be populated with previous task output
        )

    def generate_proposal(
        self,
        business_data: Dict[str, Any],
        research_result: str
    ) -> str:
        """
        Generate a business proposal using the Review/Critique pattern.

        Args:
            business_data: Dictionary containing business information (name, phone, email, etc.)
            research_result: Research findings about the business

        Returns:
            Final polished proposal as a string

        Example:
            >>> crew = ProposalGeneratorCrew()
            >>> business_data = {
            ...     "name": "The Coffee Shop",
            ...     "phone": "+1234567890",
            ...     "industry": "Food & Beverage"
            ... }
            >>> research = "Great reviews, no website, strong local presence..."
            >>> proposal = crew.generate_proposal(business_data, research)
        """
        # Create tasks
        draft_task = self.create_draft_task(business_data, research_result)
        fact_check_task = self.create_fact_check_task(business_data, research_result)

        # Set context for fact checker (it will receive draft writer's output)
        fact_check_task.context = [draft_task]

        # Create crew with sequential process
        crew = Crew(
            agents=[self.draft_writer, self.fact_checker],
            tasks=[draft_task, fact_check_task],
            process=Process.sequential,
            verbose=True
        )

        # Execute the crew
        result = crew.kickoff()

        # Return the final proposal (output from fact checker)
        return str(result)


# Create singleton instance for easy import
proposal_generator_crew = ProposalGeneratorCrew()


def generate_proposal(business_data: Dict[str, Any], research_result: str) -> str:
    """
    Convenience function to generate a proposal.

    Args:
        business_data: Dictionary containing business information
        research_result: Research findings about the business

    Returns:
        Final polished proposal
    """
    return proposal_generator_crew.generate_proposal(business_data, research_result)
