"""
SDR Crew - Orchestrates the complete sales outreach process.

This crew implements a sequential pipeline:
1. Research Lead Agent - Gathers business insights
2. Proposal Generator Crew - Creates personalized proposal (Draft → Fact Check)
3. Outreach Caller Agent - Makes phone call with proposal
4. Conversation Classifier Agent - Analyzes call outcome
"""

from typing import Dict, Any
from crewai import Crew, Task, Process
from .research_lead_agent import research_lead_agent
from .proposal_generator_crew import proposal_generator_crew
from .outreach_caller_agent import outreach_caller_agent
from .conversation_classifier_agent import conversation_classifier_agent
from .lead_clerk_agent import lead_clerk_agent
from .outreach_email_agent import outreach_email_agent
from ..prompts.research_prompts import RESEARCH_LEAD_PROMPT
from ..prompts.caller_prompts import OUTREACH_CALLER_AGENT_PROMPT
from ..prompts.classifier_prompts import CONVERSATION_CLASSIFIER_PROMPT
import json


class SDRCrew:
    """
    Complete SDR workflow crew for researching, proposing, calling, and analyzing.
    """

    def __init__(self):
        """Initialize the SDR Crew with all agents."""
        self.research_agent = research_lead_agent
        self.proposal_crew = proposal_generator_crew
        self.caller_agent = outreach_caller_agent
        self.classifier_agent = conversation_classifier_agent
        self.clerk_agent = lead_clerk_agent
        self.email_agent = outreach_email_agent

    def create_research_task(self, business_data: Dict[str, Any]) -> Task:
        """
        Create a task for researching the business.

        Args:
            business_data: Dictionary containing business information

        Returns:
            Task for research
        """
        business_info = "\n".join([f"- {k}: {v}" for k, v in business_data.items()])

        description = f"""
{RESEARCH_LEAD_PROMPT}

### BUSINESS DATA
{business_info}

Research this business thoroughly and provide comprehensive findings.
"""

        return Task(
            description=description,
            agent=self.research_agent,
            expected_output="Comprehensive research findings about the business including online presence, reviews, competitors, and opportunities"
        )

    def create_proposal_task(self, business_data: Dict[str, Any]) -> Task:
        """
        Create a task for generating the proposal.

        Args:
            business_data: Dictionary containing business information

        Returns:
            Task for proposal generation
        """
        business_info = "\n".join([f"- {k}: {v}" for k, v in business_data.items()])

        description = f"""
Generate a personalized business proposal using the research findings.

### BUSINESS DATA
{business_info}

### RESEARCH FINDINGS
{{{{ task_context }}}}

Use the proposal generator crew to create a polished, compelling proposal.
The proposal will go through draft writing and fact checking.
"""

        return Task(
            description=description,
            agent=self.research_agent,  # Placeholder, actual work done by sub-crew
            expected_output="A polished 1-2 paragraph business proposal",
            context=[]  # Will receive research task output
        )

    def create_caller_task(self, business_data: Dict[str, Any]) -> Task:
        """
        Create a task for making the phone call.

        Args:
            business_data: Dictionary containing business information

        Returns:
            Task for phone call
        """
        business_info = json.dumps(business_data, indent=2)

        description = f"""
{OUTREACH_CALLER_AGENT_PROMPT}

### BUSINESS DATA
{business_info}

### PROPOSAL
{{{{ task_context }}}}

Make a phone call to the business owner using the phone_call_tool with the business data and proposal.
"""

        return Task(
            description=description,
            agent=self.caller_agent,
            expected_output="Call result dictionary with status, transcript, conversation_id, and error fields",
            context=[]  # Will receive proposal from previous task
        )

    def create_classifier_task(self, business_data: Dict[str, Any]) -> Task:
        """
        Create a task for classifying the call outcome.

        Args:
            business_data: Dictionary containing business information

        Returns:
            Task for classification
        """
        business_info = json.dumps(business_data, indent=2)

        description = f"""
{CONVERSATION_CLASSIFIER_PROMPT}

### BUSINESS DATA
{business_info}

### CALL RESULT
{{{{ task_context }}}}

Analyze the call result and classify the conversation outcome. Return a JSON object with:
- call_category: agreed_to_email|interested|not_interested|issue_appeared|other
- email: extracted email address or empty string
- note: brief summary of the conversation
"""

        return Task(
            description=description,
            agent=self.classifier_agent,
            expected_output="JSON object with call_category, email, and note fields",
            context=[]  # Will receive call result from previous task
        )

    def create_clerk_task(self, business_data: Dict[str, Any]) -> Task:
        """
        Create a task for processing conversation results.

        Args:
            business_data: Dictionary containing business information

        Returns:
            Task for lead processing
        """
        business_info = json.dumps(business_data, indent=2)

        description = f"""
        Process the conversation results and determine next steps.

        ### BUSINESS DATA
        {business_info}

        ### CONVERSATION RESULTS
        {{{{ task_context }}}}

        Analyze the conversation results and determine the appropriate next steps.
        Store the data and plan follow-up actions if needed.
        """

        return Task(
            description=description,
            agent=self.clerk_agent,
            expected_output="Processing result with stored data and follow-up actions",
            context=[]  # Will receive classification from previous task
        )

    def create_email_task(self, business_data: Dict[str, Any]) -> Task:
        """
        Create a task for sending follow-up email.

        Args:
            business_data: Dictionary containing business information

        Returns:
            Task for email sending
        """
        business_info = json.dumps(business_data, indent=2)

        description = f"""
        Send follow-up email to business that agreed to receive proposal.

        ### BUSINESS DATA
        {business_info}

        ### CONVERSATION RESULTS
        {{{{ task_context }}}}

        Create and send a professional follow-up email with the proposal.
        """

        return Task(
            description=description,
            agent=self.email_agent,
            expected_output="Email sent confirmation with details",
            context=[]  # Will receive clerk results from previous task
        )

    def execute_sdr_workflow(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete SDR workflow.

        Args:
            business_data: Dictionary containing business information (name, phone, email, address, etc.)

        Returns:
            Dictionary containing all results:
                - business_data: Original business data
                - research_result: Research findings
                - proposal: Generated proposal
                - call_result: Phone call results
                - classification: Call classification results

        Example:
            >>> sdr = SDRCrew()
            >>> business_data = {
            ...     "name": "The Coffee Shop",
            ...     "phone": "+1234567890",
            ...     "email": "info@coffeeshop.com",
            ...     "address": "123 Main St, City, State"
            ... }
            >>> results = sdr.execute_sdr_workflow(business_data)
        """
        try:
            # Step 1: Research the business
            print("\n=== STEP 1: RESEARCHING BUSINESS ===")
            research_task = self.create_research_task(business_data)
            research_crew = Crew(
                agents=[self.research_agent],
                tasks=[research_task],
                process=Process.sequential,
                verbose=True
            )
            research_result = str(research_crew.kickoff())

            # Step 2: Generate proposal using the proposal generator crew
            print("\n=== STEP 2: GENERATING PROPOSAL ===")
            proposal = self.proposal_crew.generate_proposal(business_data, research_result)

            # Step 3: Make phone call
            print("\n=== STEP 3: MAKING PHONE CALL ===")
            caller_task = self.create_caller_task(business_data)

            # Manually set the proposal in the task description
            caller_task.description = caller_task.description.replace("{{ task_context }}", proposal)

            caller_crew = Crew(
                agents=[self.caller_agent],
                tasks=[caller_task],
                process=Process.sequential,
                verbose=True
            )
            call_result = str(caller_crew.kickoff())

            # Step 4: Classify conversation
            print("\n=== STEP 4: CLASSIFYING CONVERSATION ===")
            classifier_task = self.create_classifier_task(business_data)

            # Manually set the call result in the task description
            classifier_task.description = classifier_task.description.replace("{{ task_context }}", call_result)

            classifier_crew = Crew(
                agents=[self.classifier_agent],
                tasks=[classifier_task],
                process=Process.sequential,
                verbose=True
            )
            classification_result = str(classifier_crew.kickoff())

            # Step 5: Process results (Lead Clerk)
            print("\n=== STEP 5: PROCESSING RESULTS ===")
            clerk_task = self.create_clerk_task(business_data)

            # Combine call result and classification for clerk
            combined_results = f"Call Result: {call_result}\nClassification: {classification_result}"
            clerk_task.description = clerk_task.description.replace("{{ task_context }}", combined_results)

            clerk_crew = Crew(
                agents=[self.clerk_agent],
                tasks=[clerk_task],
                process=Process.sequential,
                verbose=True
            )
            clerk_result = str(clerk_crew.kickoff())

            # Step 6: Send follow-up email (if needed)
            email_result = None
            try:
                # Parse classification to check if email is needed
                import json
                classification_data = json.loads(classification_result)
                if classification_data.get("call_category") == "agreed_to_email":
                    print("\n=== STEP 6: SENDING FOLLOW-UP EMAIL ===")
                    email_task = self.create_email_task(business_data)

                    # Combine all results for email
                    email_context = f"Business Data: {json.dumps(business_data, indent=2)}\nProposal: {proposal}\nClassification: {classification_result}"
                    email_task.description = email_task.description.replace("{{ task_context }}", email_context)

                    email_crew = Crew(
                        agents=[self.email_agent],
                        tasks=[email_task],
                        process=Process.sequential,
                        verbose=True
                    )
                    email_result = str(email_crew.kickoff())
                else:
                    print("\n=== STEP 6: NO EMAIL FOLLOW-UP NEEDED ===")
                    email_result = "No email follow-up required based on conversation classification"
            except Exception as e:
                print(f"\n=== STEP 6: EMAIL ERROR ===")
                email_result = f"Email processing error: {str(e)}"

            # Compile all results
            results = {
                "business_data": business_data,
                "research_result": research_result,
                "proposal": proposal,
                "call_result": call_result,
                "classification": classification_result,
                "clerk_result": clerk_result,
                "email_result": email_result,
                "status": "completed"
            }

            print("\n=== SDR WORKFLOW COMPLETED ===")
            return results

        except Exception as e:
            error_msg = f"Error in SDR workflow: {str(e)}"
            print(f"\n=== ERROR: {error_msg} ===")
            return {
                "business_data": business_data,
                "status": "error",
                "error": error_msg
            }


# Singleton instance
sdr_crew = SDRCrew()


def execute_sdr_workflow(business_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to execute the SDR workflow.

    Args:
        business_data: Dictionary containing business information

    Returns:
        Dictionary with workflow results
    """
    return sdr_crew.execute_sdr_workflow(business_data)
