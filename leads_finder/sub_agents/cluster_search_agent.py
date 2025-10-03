from typing import Any, Dict
from crewai import Agent, Task, Crew, Process
from leads_finder.prompts import CLUSTER_SEARCH_AGENT_PROMPT
from leads_finder.tools.cluster_search import ClusterSearchTool
from leads_finder.llm_config import get_crewai_llm

def create_cluster_search_agent(city: str) -> Crew:
    print("cluster search agent called!!")
    tool = ClusterSearchTool()

    agent = Agent(
        role="ClusterSearchAgent",
        goal="Find businesses in the requested city and return structured JSON.",
        backstory="Agent specialized in custom cluster search for local businesses.",
        tools=[tool],
        allow_delegation=False,
        verbose=True,
        llm=get_crewai_llm(model="cerebras/gpt-oss-120b", temperature=0.5),
    )

    task = Task(
        description=CLUSTER_SEARCH_AGENT_PROMPT.format(city=city),
        agent=agent,
        expected_output=(
            "JSON array of businesses with fields: name, address, phone, website, category, established."
        ),
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )
    return crew


def run_cluster_search(city: str):
    crew = create_cluster_search_agent(city)
    result = crew.kickoff()
    for attr in ("raw", "output"):
        if hasattr(result, attr):
            return getattr(result, attr)
    try:
        return result.to_dict()
    except Exception:
        return str(result)



