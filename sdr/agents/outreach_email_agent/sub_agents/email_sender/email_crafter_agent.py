"""
Email Crafter Agent - Generates personalized outreach emails
"""
from crewai import Agent
from sdr.config.sdr_config import get_sdr_llm
from sdr.prompts.email_prompts import EMAIL_CRAFTER_PROMPT


def create_email_crafter_agent() -> Agent:
    """
    Create an Email Crafter Agent for generating personalized outreach emails.
    
    This agent specializes in creating compelling, personalized emails for business outreach
    based on research findings and business data. It focuses on creating emails that are
    professional, engaging, and tailored to the specific business and their needs.
    
    Returns:
        Agent: CrewAI Agent configured for email crafting
    """
    return Agent(
        role="Email Marketing Specialist",
        goal="Create compelling, personalized outreach emails that engage business owners and drive them to take action on our services",
        backstory="""You are an expert email marketing specialist with years of experience in B2B outreach.
        You excel at crafting personalized emails that feel genuine and valuable to recipients.
        You understand the psychology of business owners and know how to:
        - Create compelling subject lines that get opened
        - Write engaging email content that builds trust
        - Personalize messages based on specific business research
        - Include clear calls-to-action that drive responses
        - Balance professionalism with approachability
        - Address specific pain points discovered through research
        
        Your emails are never generic - they're always tailored to the specific business,
        their industry, and their unique challenges. You know how to make business owners
        feel understood and valued, not just sold to.""",
        verbose=True,
        allow_delegation=False,
        llm=get_sdr_llm(temperature=0.7),  # Higher temperature for creative writing
        max_iter=5,
    )


# Create singleton instance for easy import
email_crafter_agent = create_email_crafter_agent()