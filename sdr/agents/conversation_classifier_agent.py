"""
Conversation Classifier Agent for analyzing phone call results.
"""

from crewai import Agent
from ..config.sdr_config import get_sdr_llm
from ..prompts.classifier_prompts import CONVERSATION_CLASSIFIER_PROMPT


def create_conversation_classifier_agent() -> Agent:
    """
    Create the Conversation Classifier Agent for analyzing phone call results.

    Returns:
        Agent: CrewAI Agent configured for conversation classification
    """
    return Agent(
        role="Conversation Classifier Specialist",
        goal="Analyze phone conversation transcripts and classify call outcomes into predefined categories",
        backstory="""You are a professional conversation analyst with expertise in sales call evaluation.
        You analyze phone conversation transcripts to determine the outcome and extract key information
        like email addresses and business owner responses. You understand the nuances of sales conversations
        and can accurately classify call results.""",
        tools=[],  # No tools needed - pure analysis
        llm=get_sdr_llm(temperature=0.3),  # Lower temperature for consistent classification
        verbose=True,
        allow_delegation=False,
        max_iter=1,
        max_execution_time=60,  # 1 minute for analysis
        memory=False,
        planning=False
    )


# Singleton instance
conversation_classifier_agent = create_conversation_classifier_agent()