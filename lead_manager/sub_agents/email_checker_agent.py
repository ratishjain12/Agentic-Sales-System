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
    """Run email checker agent and return structured results."""
    import json
    try:
        crew = create_email_checker_agent()
        result = crew.kickoff()
        
        # Try to extract structured data from different result formats
        if hasattr(result, 'raw'):
            raw_result = result.raw
            if isinstance(raw_result, str):
                try:
                    # Try to parse JSON from string
                    parsed_result = json.loads(raw_result)
                    return {"success": True, "result": parsed_result}
                except json.JSONDecodeError:
                    return {"success": False, "error": "Failed to parse email data", "raw": raw_result}
            elif isinstance(raw_result, dict):
                return {"success": True, "result": raw_result}
            else:
                return {"success": True, "result": raw_result}
        
        elif hasattr(result, 'output'):
            output_result = result.output
            if isinstance(output_result, str):
                try:
                    parsed_result = json.loads(output_result)
                    return {"success": True, "result": parsed_result}
                except json.JSONDecodeError:
                    return {"success": False, "error": "Failed to parse email data", "raw": output_result}
            elif isinstance(output_result, dict):
                return {"success": True, "result": output_result}
            else:
                return {"success": True, "result": output_result}
        
        elif hasattr(result, 'to_dict'):
            return {"success": True, "result": result.to_dict()}
            
        # If all else fails, try to convert to string and parse
        string_result = str(result)
        try:
            parsed_result = json.loads(string_result)
            return {"success": True, "result": parsed_result}
        except json.JSONDecodeError:
            return {"success": False, "error": "Failed to parse email data", "raw": string_result}
            
    except Exception as e:
        return {"success": False, "error": str(e)}