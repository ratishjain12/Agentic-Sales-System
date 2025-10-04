"""
Email Sender Agent - Handles email sending operations
"""
from crewai import Agent
from sdr.config.sdr_config import get_sdr_llm
from sdr.tools.email_sender_tool import email_sender_tool
from sdr.prompts.email_prompts import EMAIL_SENDER_PROMPT


def create_email_sender_agent() -> Agent:
    """
    Create an Email Sender Agent for handling email sending operations.
    
    This agent is responsible for sending emails using the email sender tool.
    It validates email content, formats it properly, and handles the technical
    aspects of email delivery through Gmail Service Account.
    
    Returns:
        Agent: CrewAI Agent configured for email sending
    """
    return Agent(
        role="Email Delivery Specialist",
        goal="Successfully send personalized outreach emails to business leads using Gmail Service Account",
        backstory="""You are a technical email delivery specialist with expertise in:
        - Email deliverability and best practices
        - Gmail Service Account integration
        - Email formatting and validation
        - Error handling and troubleshooting
        - Email tracking and delivery confirmation
        
        You ensure that every email is properly formatted, sent to the correct recipient,
        and delivered successfully. You handle technical issues gracefully and provide
        clear feedback on delivery status. You understand email compliance requirements
        and ensure all emails follow best practices for deliverability.""",
        verbose=True,
        allow_delegation=False,
        tools=[email_sender_tool],
        llm=get_sdr_llm(temperature=0.3),  # Lower temperature for technical tasks
        max_iter=3,
    )


# Create singleton instance for easy import
email_sender_agent = create_email_sender_agent()