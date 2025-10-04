"""
Email Agent - Main orchestrator for email crafting and sending
"""
from typing import Dict, Any, Optional
from crewai import Crew, Task, Process
from .email_crafter_agent import email_crafter_agent
from .email_sender_agent import email_sender_agent
from sdr.prompts.email_prompts import EMAIL_CRAFTER_PROMPT, EMAIL_SENDER_PROMPT


class EmailAgent:
    """
    Main orchestrator for email crafting and sending workflow.
    
    This agent coordinates the email crafting and sending process:
    1. Email Crafter Agent creates personalized email content
    2. Email Sender Agent sends the email using Gmail Service Account
    """
    
    def __init__(self):
        """Initialize the Email Agent."""
        self.email_crafter = email_crafter_agent
        self.email_sender = email_sender_agent
    
    def create_email_crafting_task(self, business_data: Dict[str, Any], research_result: str, proposal: str) -> Task:
        """
        Create a task for the Email Crafter Agent.
        
        Args:
            business_data: Dictionary containing business information
            research_result: Research findings about the business
            proposal: Generated proposal for the business
            
        Returns:
            Task for email crafting
        """
        # Format business data for the prompt
        business_info = "\n".join([f"- {k}: {v}" for k, v in business_data.items()])
        
        description = f"""
{EMAIL_CRAFTER_PROMPT}

### BUSINESS DATA
{business_info}

### RESEARCH FINDINGS
{research_result}

### PROPOSAL
{proposal}

Based on the above information, craft a personalized outreach email that:
1. Engages the business owner personally
2. References specific findings from the research
3. Introduces our services naturally
4. Includes a clear call-to-action
5. Feels genuine and valuable, not salesy

The email should be professional yet approachable, and tailored specifically to this business.
"""
        
        return Task(
            description=description,
            agent=self.email_crafter,
            expected_output="A personalized outreach email with subject line and body content"
        )
    
    def create_email_sending_task(self, business_data: Dict[str, Any]) -> Task:
        """
        Create a task for the Email Sender Agent.
        
        Args:
            business_data: Dictionary containing business information
            
        Returns:
            Task for email sending
        """
        # Extract email from business data
        to_email = business_data.get('email', '')
        if not to_email:
            raise ValueError("Business data must contain 'email' field for sending")
        
        description = f"""
{EMAIL_SENDER_PROMPT}

### EMAIL TO SEND
{{{{ task_context }}}}

### RECIPIENT
Email: {to_email}

Send this email to the business owner using the email_sender tool.
Validate the email content and ensure proper delivery.
"""
        
        return Task(
            description=description,
            agent=self.email_sender,
            expected_output="Email sent successfully with delivery confirmation",
            context=[]  # Will be populated with previous task output
        )
    
    def send_outreach_email(
        self,
        business_data: Dict[str, Any],
        research_result: str,
        proposal: str
    ) -> Dict[str, Any]:
        """
        Send a personalized outreach email to a business lead.
        
        Args:
            business_data: Dictionary containing business information (must include 'email')
            research_result: Research findings about the business
            proposal: Generated proposal for the business
            
        Returns:
            Dict with email sending results and details
            
        Example:
            >>> agent = EmailAgent()
            >>> business_data = {
            ...     "name": "The Coffee Shop",
            ...     "email": "owner@coffeeshop.com",
            ...     "phone": "+1234567890",
            ...     "industry": "Food & Beverage"
            ... }
            >>> research = "Great reviews, no website..."
            >>> proposal = "We can help you build a website..."
            >>> result = agent.send_outreach_email(business_data, research, proposal)
        """
        # Validate required fields
        if 'email' not in business_data:
            raise ValueError("business_data must contain 'email' field")
        
        # Create tasks
        crafting_task = self.create_email_crafting_task(business_data, research_result, proposal)
        sending_task = self.create_email_sending_task(business_data)
        
        # Set context for sender (it will receive crafter's output)
        sending_task.context = [crafting_task]
        
        # Create crew with sequential process
        crew = Crew(
            agents=[self.email_crafter, self.email_sender],
            tasks=[crafting_task, sending_task],
            process=Process.sequential,
            verbose=True
        )
        
        # Execute the crew
        result = crew.kickoff()
        
        # Return structured result
        return {
            "success": True,
            "message": "Email sent successfully",
            "business_name": business_data.get('name', 'Unknown'),
            "email": business_data.get('email'),
            "result": str(result)
        }


# Create singleton instance for easy import
email_agent = EmailAgent()


def send_outreach_email(
    business_data: Dict[str, Any],
    research_result: str,
    proposal: str
) -> Dict[str, Any]:
    """
    Convenience function to send an outreach email.
    
    Args:
        business_data: Dictionary containing business information
        research_result: Research findings about the business
        proposal: Generated proposal for the business
        
    Returns:
        Dict with email sending results
    """
    return email_agent.send_outreach_email(business_data, research_result, proposal)