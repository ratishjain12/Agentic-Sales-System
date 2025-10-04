"""
SDR Main Agent with proper CrewAI Sequential Orchestration pattern.

This implements the correct pattern:
- Individual Agent instances, each with their tools
- Single Crew with Process.sequential orchestration
- Tasks with context relationships
"""

from typing import Dict, Any, List
from crewai import Crew, Task, Process, Agent
from ..prompts.research_prompts import RESEARCH_LEAD_PROMPT
from ..prompts.caller_prompts import OUTREACH_CALLER_AGENT_PROMPT
from ..prompts.classifier_prompts import CONVERSATION_CLASSIFIER_PROMPT
from ..config.sdr_config import get_sdr_llm
from ..tools.exa_search_tool import ExaSearchTool
from ..tools.phone_call_tool import phone_call_tool
from ..tools.data_storage_tool import data_storage_tool
from .outreach_email_agent.sub_agents.email_sender.email_agent import email_agent
import json


class SDRAgent:
    """
    SDR Main Agent following proper CrewAI orchestration pattern.
    
    Each agent is an individual Agent instance with tools,
    orchestrated in a single Crew with Process.sequential.
    """

    def __init__(self):
        """Initialize all SDR agents with their tools."""
        self.researcher = self._create_researcher()
        self.draft_writer = self._create_draft_writer()
        self.fact_checker = self._create_fact_checker()
        self.outreach_caller = self._create_outreach_caller()
        self.classifier = self._create_classifier()
        self.lead_clerk = self._create_lead_clerk()
        # Use the email agent system (crafter + sender)
        self.email_agent = email_agent

    def _create_researcher(self) -> Agent:
        """Create Research Lead Agent with research tools."""
        return Agent(
            role="Research Lead Specialist",
            goal="Research businesses comprehensively to gather insights for sales outreach",
            backstory="""You are an expert business researcher specializing in gathering 
            comprehensive information about potential business leads. You excel at finding 
            business details, reviews, competitive landscape, and growth opportunities.""",
            tools=[ExaSearchTool()],
            llm=get_sdr_llm(model="llama3.3-70b", temperature=0.3),
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            max_execution_time=300,
            memory=False,
            planning=False
        )

    def _create_draft_writer(self) -> Agent:
        """Create Draft Writer Agent."""
        return Agent(
            role="Proposal Draft Writer",
            goal="Create compelling initial drafts of business proposals",
            backstory="""You are a skilled proposal writer who creates persuasive, 
            customized business proposals based on research findings. You excel at 
            translating insights into compelling business opportunities.""",
            llm=get_sdr_llm(model="llama3.3-70b", temperature=0.7),
            verbose=True,
            allow_delegation=False,
            max_iter=2,
            max_execution_time=180,
            memory=False,
            planning=False
        )

    def _create_fact_checker(self) -> Agent:
        """Create Fact Checker Agent."""
        return Agent(
            role="Proposal Fact Checker and Editor",
            goal="Review, fact-check, and polish business proposals",
            backstory="""You are a meticulous editor and fact-checker who ensures 
            proposals are accurate, professional, and compelling. You verify facts, 
            improve clarity, and create the final polished version.""",
            llm=get_sdr_llm(model="llama3.3-70b", temperature=0.3),
            verbose=True,
            allow_delegation=False,
            max_iter=2,
            max_execution_time=180,
            memory=False,
            planning=False
        )

    def _create_outreach_caller(self) -> Agent:
        """Create Outreach Caller Agent with phone call tool."""
        return Agent(
            role="Outreach Caller Specialist",
            goal="Make professional phone calls to business owners with personalized proposals",
            backstory="""You are an experienced sales development representative who excels at 
            cold calling business owners. You use research insights and proposals to have 
            meaningful conversations about potential business opportunities.""",
            tools=[phone_call_tool],
            llm=get_sdr_llm(model="llama3.3-70b", temperature=0.4),
            verbose=True,
            allow_delegation=False,
            max_iter=1,
            max_execution_time=600,
            memory=False,
            planning=False
        )

    def _create_classifier(self) -> Agent:
        """Create Conversation Classifier Agent."""
        return Agent(
            role="Conversation Outcome Classifier",
            goal="Analyze phone call outcomes and classify conversation results",
            backstory="""You are a conversation analyst who excels at understanding call outcomes, 
            extracting key information, and categorizing the business owner's interest level 
            for follow-up activities.""",
            llm=get_sdr_llm(model="llama3.3-70b", temperature=0.2),
            verbose=True,
            allow_delegation=False,
            max_iter=2,
            max_execution_time=120,
            memory=False,
            planning=False
        )

    def _create_lead_clerk(self) -> Agent:
        """Create Lead Clerk Agent with data storage tool."""
        return Agent(
            role="Lead Management Clerk",
            goal="Process conversation results and determine next steps",
            backstory="""You are a lead management specialist who processes conversation outcomes, 
            determines appropriate follow-up actions, and manages lead data systematically.""",
            tools=[data_storage_tool],
            llm=get_sdr_llm(model="llama3.3-70b", temperature=0.3),
            verbose=True,
            allow_delegation=False,
            max_iter=2,
            max_execution_time=180,
            memory=False,
            planning=False
        )

    def _create_email_outreach_agent(self) -> Agent:
        """Create Email Outreach Agent that coordinates with the email agent system."""
        return Agent(
            role="Email Outreach Coordinator",
            goal="Coordinate email outreach using the email agent system (crafter + sender)",
            backstory="""You are an email outreach coordinator who determines when to send emails 
            and provides the necessary context for the email agent system. You work with the 
            email crafter and sender agents to create and send personalized follow-up communications.""",
            llm=get_sdr_llm(model="llama3.3-70b", temperature=0.5),
            verbose=True,
            allow_delegation=False,
            max_iter=2,
            max_execution_time=300,
            memory=False,
            planning=False
        )

    def create_tasks(self, business_data: Dict[str, Any]) -> List[Task]:
        """Create all tasks with proper context relationships."""
        business_info = "\n".join([f"- {k}: {v}" for k, v in business_data.items()])

        # Task 1: Research
        research_task = Task(
            description=f"""
            {RESEARCH_LEAD_PROMPT}
            
            ### BUSINESS DATA
            {business_info}
            
            Research this business thoroughly and provide comprehensive findings.
            """,
            expected_output="Comprehensive research findings about the business including online presence, reviews, competitors, and opportunities",
            agent=self.researcher
        )

        # Task 2: Draft
        draft_task = Task(
            description=f"""
            Create an initial draft of a business proposal using the research findings.
            
            ### BUSINESS DATA
            {business_info}
            
            ### RESEARCH FINDINGS
            {{task_context}}
            
            Write a compelling 2-3 paragraph proposal draft.
            """,
            expected_output="Initial proposal draft (2-3 paragraphs)",
            agent=self.draft_writer,
            context=[research_task]  # Gets research output automatically
        )

        # Task 3: Fact Check
        fact_check_task = Task(
            description=f"""
            Review and fact-check the proposal draft, then create the final polished version.
            
            ### BUSINESS DATA
            {business_info}
            
            ### RESEARCH FINDINGS + DRAFT
            {{task_context}}
            
            Validate facts, improve clarity, and create a polished final proposal.
            """,
            expected_output="Final polished business proposal (1-2 paragraphs)",
            agent=self.fact_checker,
            context=[research_task, draft_task]  # Gets both research and draft
        )

        # Task 4: Phone Call
        caller_task = Task(
            description=f"""
            {OUTREACH_CALLER_AGENT_PROMPT}
            
            ### BUSINESS DATA
            {business_info}
            
            ### PROPOSAL
            {{task_context}}
            
            Make a phone call to the business owner using the phone_call_tool.
            """,
            expected_output="Call result with status, transcript, conversation_id, and error fields",
            agent=self.outreach_caller,
            context=[fact_check_task]  # Uses the final proposal
        )

        # Task 5: Classify
        classifier_task = Task(
            description=f"""
            {CONVERSATION_CLASSIFIER_PROMPT}
            
            ### BUSINESS DATA
            {business_info}
            
            ### CALL RESULT
            {{task_context}}
            
            Analyze the call result and classify the conversation outcome. Return JSON with:
            - call_category: agreed_to_email|interested|not_interested|issue_appeared|other
            - email: extracted email address or empty string
            - note: brief summary of the conversation
            """,
            expected_output="JSON object with call_category, email, and note fields",
            agent=self.classifier,
            context=[caller_task]  # Uses call results
        )

        # Task 6: Lead Clerk
        clerk_task = Task(
            description=f"""
            Process the conversation results and determine next steps.
            
            ### BUSINESS DATA
            {business_info}
            
            ### CONVERSATION RESULTS
            {{task_context}}
            
            Analyze the conversation results and determine appropriate next steps.
            Store the data and plan follow-up actions if needed.
            """,
            expected_output="Processing result with stored data and follow-up actions",
            agent=self.lead_clerk,
            context=[classifier_task, caller_task]  # Uses classification and call results
        )

        # Task 7: Email Outreach (Using Email Agent System)
        email_task = Task(
            description=f"""
            Coordinate email outreach using the email agent system if the business owner agreed to receive emails.
            
            ### BUSINESS DATA
            {business_info}
            
            ### CONVERSATION RESULTS
            {{task_context}}
            
            If the conversation results indicate interest or agreement to receive email:
            1. Use the email agent system to craft a personalized email
            2. The email crafter will create compelling content based on research and proposal
            3. The email sender will send the email using Gmail Service Account
            4. Provide confirmation of email sending
            
            If no interest or no email agreement, skip email sending.
            """,
            expected_output="Email sent confirmation with details or skip message with reason",
            agent=self._create_email_outreach_agent(),
            context=[clerk_task, classifier_task, research_task, fact_check_task]  # Uses all relevant context
        )

        return [
            research_task,
            draft_task,
            fact_check_task,
            caller_task,
            classifier_task,
            clerk_task,
            email_task
        ]

    def _send_email_via_agent_system(self, business_data: Dict[str, Any], research_result: str, proposal: str) -> Dict[str, Any]:
        """
        Helper method to send email using the email agent system (crafter + sender).
        
        Args:
            business_data: Business information including email
            research_result: Research findings
            proposal: Generated proposal
            
        Returns:
            Email sending result from the email agent system
        """
        try:
            # Ensure business data has email field
            if 'email' not in business_data or not business_data['email']:
                return {
                    "success": False,
                    "message": "No email address available for sending",
                    "business_name": business_data.get('name', 'Unknown')
                }
            
            # Use the email agent system to send the email
            # This will use both email crafter and sender agents
            result = self.email_agent.send_outreach_email(
                business_data=business_data,
                research_result=research_result,
                proposal=proposal
            )
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error in email agent system: {str(e)}",
                "business_name": business_data.get('name', 'Unknown')
            }

    def execute_workflow(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete SDR workflow using proper CrewAI orchestration.
        
        Creates a single Crew with all agents and lets CrewAI handle sequential execution.
        """
        try:
            print(f"\n=== CREATING SDR MAIN AGENT ORCHESTRATOR ===")
            
            # Create all tasks with proper context relationships
            tasks = self.create_tasks(business_data)
            
            # Single Crew for orchestration - this is the key pattern!
            crew = Crew(
                agents=[
                    self.researcher,
                    self.draft_writer,
                    self.fact_checker,
                    self.outreach_caller,
                    self.classifier,
                    self.lead_clerk,
                    self._create_email_outreach_agent()
                ],
                tasks=tasks,
                process=Process.sequential,  # Process.SEQUENTIAL - Automatic sequential execution
                verbose=True
            )
            
            print(f"\n=== EXECUTING SEQUENTIAL WORKFLOW ===")
            print("CrewAI will automatically execute: Research → Draft → Fact Check → Call → Classify → Clerk → Email")
            
            # Kickoff the crew - CrewAI handles the orchestration
            result = crew.kickoff()
            
            print(f"\n=== SDR WORKFLOW COMPLETED ===")
            
            # Extract results from individual tasks
            results = {
                "business_data": business_data,
                "status": "completed",
                "research_result": tasks[0].output.raw if tasks[0].output else "No research output",
                "draft_result": tasks[1].output.raw if tasks[1].output else "No draft output", 
                "proposal_result": tasks[2].output.raw if tasks[2].output else "No proposal output",
                "call_result": tasks[3].output.raw if tasks[3].output else "No call output",
                "classification_result": tasks[4].output.raw if tasks[4].output else "No classification output",
                "clerk_result": tasks[5].output.raw if tasks[5].output else "No clerk output",
                "email_result": tasks[6].output.raw if tasks[6].output else "No email output",
            }
            
            # If email task completed and business has email, also try to send email using the email agent system
            if tasks[6].output and "email" in business_data:
                try:
                    email_result = self._send_email_via_agent_system(
                        business_data=business_data,
                        research_result=results["research_result"],
                        proposal=results["proposal_result"]
                    )
                    results["email_agent_system_result"] = email_result
                except Exception as e:
                    results["email_agent_system_result"] = {
                        "success": False,
                        "message": f"Error in email agent system: {str(e)}"
                    }
            
            return results
            
        except Exception as e:
            error_msg = f"Error in SDR orchestration: {str(e)}"
            print(f"\n=== ERROR: {error_msg} ===")
            return {
                "business_data": business_data,
                "status": "error",
                "error": error_msg
            }


# Create main SDR agent instance
sdr_main_agent = SDRAgent()


def execute_sdr_main_workflow(business_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to execute the SDR main agent workflow.
    
    Args:
        business_data: Dictionary containing business information
        
    Returns:
        Dictionary with unified lead finding results
        
    Example:
        >>> business_data = {
        ...     "name": "The Coffee Shop",
        ...     "phone": "+1234567890",
        ...     "email": "info@coffeeshop.com",
        ...     "address": "123 Main St, City, State"
        ... }
        >>> results = execute_sdr_main_workflow(business_data)
    """
    return sdr_main_agent.execute_workflow(business_data)