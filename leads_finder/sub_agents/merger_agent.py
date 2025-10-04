"""
MergerAgent implementation using CrewAI and Cerebras LLM.
"""

from crewai import Agent
from leads_finder.prompts import MERGER_AGENT_PROMPT
from leads_finder.tools.mongodb_upload import mongodb_upload_tool_instance
from config.cerebras_client import get_crewai_llm


# Create the Merger Agent following the reference pattern
merger_agent = Agent(
    role="MergerAgent",
    goal="Process, deduplicate, and upload merged business leads to MongoDB",
    backstory=(
        "You are a specialized data processing agent with expertise in "
        "business lead management. Your primary function is to receive "
        "raw business data from multiple sources (MapSearch and ClusterSearch agents), "
        "process and clean the data, remove duplicates, validate information, "
        "and upload the final consolidated leads to MongoDB database. "
        "You ensure data quality and maintain comprehensive audit trails."
    ),
    tools=[mongodb_upload_tool_instance],
    llm=get_crewai_llm(model="cerebras/gpt-oss-120b", temperature=0.3),
    verbose=True,
    allow_delegation=False,
    max_iter=2,
    max_execution_time=120,
    memory=False,
    planning=False
)
