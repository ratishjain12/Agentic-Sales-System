"""
Map Agent implementation for lead finding using Google Maps.
"""

from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext

from ..config import MODEL
from ..prompts import MAP_AGENT_PROMPT
from ..tools.map_search import google_maps_search_tool
     

map_agent = LlmAgent(
    model=MODEL,
    name="MapAgent",
    description="Agent specialized in finding business information using Google Maps",
    instruction=MAP_AGENT_PROMPT,
    tools=[google_maps_search_tool],
)
