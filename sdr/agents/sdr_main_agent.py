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
from ..prompts.email_prompts import OUTREACH_EMAIL_PROMPT
from ..config.sdr_config import get_sdr_llm
from ..tools.exa_search_tool import ExaSearchTool
from ..tools.phone_call_tool import phone_call_tool
from ..tools.data_storage_tool import data_storage_tool
from ..tools.email_sender_tool import email_sender_tool
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
        """Create Email Outreach Agent that can actually send emails using the email sender tool."""
        return Agent(
            role="Email Outreach Specialist",
            goal="Send personalized follow-up emails to businesses that agreed to receive proposals using Gmail OAuth2",
            backstory="""You are an email outreach specialist who crafts and sends personalized follow-up emails 
            to businesses after successful phone conversations. You have access to the email_sender tool which 
            uses Gmail OAuth2 to send emails. You create compelling, personalized emails based on research 
            findings and proposals, then send them using the email_sender tool. You ensure emails are 
            professional, engaging, and tailored to each specific business.""",
            tools=[email_sender_tool],
            llm=get_sdr_llm(model="llama3.3-70b", temperature=0.5),
            verbose=True,
            allow_delegation=False,
            max_iter=3,
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

        # Task 7: Email Outreach (Using Email Sender Tool)
        email_task = Task(
            description=f"""
            {OUTREACH_EMAIL_PROMPT}
            
            ### BUSINESS DATA
            {business_info}
            
            ### CONVERSATION RESULTS
            {{task_context}}
            
            Based on the conversation results and classification, determine if the business owner agreed to receive emails.
            If yes, craft and send a personalized follow-up email using the email_sender tool.
            If no, provide a clear reason for skipping email sending.
            """,
            expected_output="Email sent confirmation with message ID and details, or skip message with reason if no email agreement",
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
            
            # Email integration is now handled directly in the main workflow task
            # No need for additional email system call since the email task already handles it
            
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


if __name__ == "__main__":
    """Test the SDR main agent directly."""
    print("=== SDR Main Agent Direct Test ===")
    print("=" * 50)
    
    # Get business data from user input
    print("\n📝 Enter Business Information:")
    business_name = input("Business Name: ").strip()
    business_email = input("Business Email: ").strip()
    business_phone = input("Business Phone (with country code): ").strip()
    business_address = input("Business Address: ").strip()
    business_industry = input("Industry: ").strip()
    business_website = input("Website (optional): ").strip()
    business_description = input("Brief Description: ").strip()
    
    # Create business data dictionary
    business_data = {
        "name": business_name,
        "email": business_email,
        "phone": business_phone,
        "address": business_address,
        "industry": business_industry,
        "website": business_website if business_website else None,
        "description": business_description
    }
    
    print(f"Business: {business_data['name']}")
    print(f"Email: {business_data['email']}")
    print(f"Phone: {business_data['phone']}")
    
    try:
        print(f"\n🚀 Starting Complete SDR Workflow...")
        print("Flow: Research → Draft → Fact Check → Call → Classify → Clerk → Email")
        
        # Execute the complete SDR workflow
        results = execute_sdr_main_workflow(business_data)
        
        print(f"\n📊 Workflow Results:")
        print(f"Status: {results.get('status', 'Unknown')}")
        
        if results.get('email_result'):
            print(f"\n📧 Email Result:")
            print(f"   {results['email_result']}")
        
        if results.get('call_result'):
            print(f"\n📞 Call Result:")
            print(f"   {results['call_result']}")
        
        if results.get('research_result'):
            print(f"\n🔍 Research Result:")
            print(f"   {results['research_result'][:200]}...")
        
        print(f"\n🎉 SDR Main Agent test completed!")
        
    except Exception as e:
        print(f"❌ Error in SDR workflow: {e}")
        import traceback
        traceback.print_exc()