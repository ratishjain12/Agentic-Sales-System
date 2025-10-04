from typing import Any, Dict
from crewai import Agent, Task, Crew, Process
from lead_manager.prompts import EMAIL_CHECKER_PROMPT
from lead_manager.tools.check_email_tool import CheckEmailTool
from config.cerebras_client import get_crewai_llm

def create_email_checker_agent() -> Crew:
    print("email checker agent called!!")
    tool = CheckEmailTool()

    agent = Agent(
        role="EmailCheckerAgent",
        goal="Monitor and structure unread email data for sales analysis.",
        backstory="Agent specialized in retrieving and organizing unread emails from sales email accounts.",
        tools=[tool],
        allow_delegation=False,
        verbose=True,
        llm=get_crewai_llm(model="cerebras/gpt-oss-120b", temperature=0.5),
    )

    task = Task(
        description=EMAIL_CHECKER_PROMPT,
        agent=agent,
        expected_output=(
            "JSON object with 'unread_emails' key containing structured email data with fields: "
            "sender_email, message_id, thread_id, sender_name, subject, body, date_received, "
            "thread_conversation_history."
        ),
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )
    return crew


def run_email_checker():
    crew = create_email_checker_agent()
    result = crew.kickoff()
    for attr in ("raw", "output"):
        if hasattr(result, attr):
            return getattr(result, attr)
    try:
        return result.to_dict()
    except Exception:
        return str(result)