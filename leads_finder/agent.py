"""
Main Lead Finder Agent implementation using CrewAI.
"""

import logging
from typing import Dict, Any, List, Optional
from crewai import Agent, Task, Crew, Process
from leads_finder.prompts import ROOT_AGENT_PROMPT
from leads_finder.sub_agents.potential_lead_finder_agent import create_potential_lead_finder_agent
from leads_finder.sub_agents.merger_agent import merger_agent
from leads_finder.tools.mongodb_upload import mongodb_upload_tool_instance
from leads_finder.tools.map_search import foursquare_search_tool_instance
from leads_finder.tools.cluster_search import ClusterSearchTool
from config.cerebras_client import get_crewai_llm

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _format_business_results_as_table(business_list: List[Dict[str, Any]], city: str, business_type: str) -> str:
    """Format business results as a markdown table."""
    if not business_list:
        return f"No {business_type} businesses found in {city}."
    
    # Create table header
    table_lines = [f"**{business_type.title()} Business Leads in {city}**"]
    table_lines.append("")
    table_lines.append("| Business Name | Address | Phone | Website | Category | Rating | Source |")
    table_lines.append("|---------------|---------|-------|---------|----------|--------|--------|")
    
    # Count sources
    map_search_count = 0
    cluster_search_count = 0
    
    # Add table rows
    for business in business_list:
        name = business.get('name', 'N/A')
        address = business.get('address', 'N/A')
        phone = business.get('phone') or 'N/A'
        website = business.get('website') or 'N/A'
        if website == 'N/A':
            website = '–'
        category = business.get('category', 'N/A')
        rating = business.get('rating') or 'N/A'
        source = business.get('source', 'N/A')
        
        # Count sources
        if source == 'map_search':
            map_search_count += 1
        elif source == 'cluster_search':
            cluster_search_count += 1
        
        # Wrap long content
        if len(address) > 30:
            address = address[:27] + "..."
        
        table_lines.append(f"| {name} | {address} | {phone} | {website} | {category} | {rating} | {source} |")
    
    # Add summary
    table_lines.append("")
    table_lines.append("**Summary**")
    table_lines.append("")
    table_lines.append(f"- **Total leads found:** {len(business_list)}")
    table_lines.append(f"- **Map search results:** {map_search_count}")
    table_lines.append(f"- **Cluster search results:** {cluster_search_count}")
    table_lines.append(f"- **Successfully uploaded to MongoDB**")
    
    return "\n".join(table_lines)


def create_lead_finder_agent(city: str, business_type: str = "restaurants") -> Crew:
    """
    Create the main Lead Finder Agent following the reference architecture.
    
    This agent implements the SequentialAgent pattern:
    - LeadFinderAgent (Root) → PotentialLeadFinderAgent → MergerAgent
    - Orchestrates the complete lead discovery workflow
    - Handles session management and error recovery
    
    Args:
        city: City name to search for business leads
        business_type: Type of business to search for (e.g., "restaurants", "jewellery", "cafe")
        
    Returns:
        CrewAI Crew with sequential execution workflow
    """
    
    # Initialize tools
    foursquare_tool = foursquare_search_tool_instance
    cluster_tool = ClusterSearchTool()
    mongodb_tool = mongodb_upload_tool_instance
    
    # Create the root Lead Finder Agent with actual tools
    root_agent = Agent(
        role="LeadFinderAgent",
        goal=f"Find and store real business leads for {city} and present results in a formatted table",
        backstory=(
            "You are a business lead discovery specialist with access to powerful tools. "
            "You MUST use the foursquare_search_tool to find businesses via Foursquare Places API, "
            "the cluster_search_tool to find additional businesses via OpenStreetMap data, "
            "and the mongodb_upload_tool to store results in the database. "
            "Your job is to execute these tools in sequence, collect real business data, "
            "upload it to MongoDB, and then present the results in a clean markdown table format "
            "with columns: Business Name, Address, Phone, Website, Category, Rating, Source. "
            "Include a summary section with total counts and source breakdown. "
            "DO NOT just return query parameters - you must actually call the tools and process their results."
        ),
        tools=[foursquare_tool, cluster_tool, mongodb_tool],
        llm=get_crewai_llm(model="cerebras/gpt-oss-120b", temperature=0.1),
        verbose=True,
        allow_delegation=False,
        max_iter=10,  # Increased iterations to allow for tool calls
        max_execution_time=600,  # 10 minutes total
        memory=False,
        planning=False
    )
    
    # Create the main lead finding task
    lead_finding_task = Task(
        description=f"""
        You are a business lead discovery specialist. Your task is to find real business leads in {city} for {business_type} and store them in MongoDB.
        
        IMPORTANT: You MUST use the available tools to perform actual searches and database operations.
        
        Step 1: Search for businesses using Foursquare
        - Use the foursquare_search_tool with query="{business_type}", location="{city}", radius=5000, limit=10
        - This will return JSON data with business information
        
        Step 2: Search for additional businesses using cluster search
        - Use the cluster_search_tool with query="{city} {business_type}"
        - This will return additional business data in JSON format
        
        Step 3: Upload results to MongoDB
        - Combine the results from both searches
        - Ensure each business has a "source" field: "map_search" for Foursquare results, "cluster_search" for cluster results
        - Use the mongodb_upload_tool to store the combined results
        
        Step 4: Present results in markdown table format
        - Create a clean table with columns: Business Name | Address | Phone | Website | Category | Rating | Source
        - Include a summary section with statistics
        
        You MUST call these tools in sequence and use their actual results. Do not just return the query parameters.
        """,
        agent=root_agent,
        expected_output=(
            f"A **markdown table** showing {business_type} business leads found in {city}. "
            "The table must have columns: Business Name | Address | Phone | Website | Category | Rating | Source. "
            "Include a **Summary** section below the table with: Total leads processed, New leads inserted, Source breakdown (map_search vs cluster_search). "
            "Do NOT return raw JSON or tool call outputs - only the formatted table and summary."
        ),
    )
    
    # Create crew with sequential execution
    crew = Crew(
        agents=[root_agent],
        tasks=[lead_finding_task],
        process=Process.sequential,
        verbose=True,
    )
    
    return crew


def run_lead_finder_workflow(city: str, business_type: str = "restaurants", max_results: int = 50, search_radius: int = 25000) -> Dict[str, Any]:
    """
    Run the complete lead finder workflow.
    
    Args:
        city: City name to search for business leads
        business_type: Type of business to search for (e.g., "restaurants", "jewellery", "cafe")
        max_results: Maximum number of results to return
        search_radius: Search radius in meters
        
    Returns:
        Dictionary with workflow results and statistics
    """
    try:
        logger.info(f"Starting lead finder workflow for {city} - {business_type}")
        
        # Create lead finder crew
        crew = create_lead_finder_agent(city, business_type)
        
        # Execute the workflow
        result = crew.kickoff()
        
        # Extract and format result
        result_str = str(result)
        
        # If the result doesn't contain a table format, try to extract meaningful data
        if "|" not in result_str and "Business Name" not in result_str:
            # Try to extract data from JSON-like content in the result
            import re
            import json
            
            # Look for JSON patterns in the result
            json_pattern = r'\[{.*?}\]'
            json_matches = re.findall(json_pattern, result_str, re.DOTALL)
            
            if json_matches:
                try:
                    # Parse the JSON and format as table
                    business_list = json.loads(json_matches[0])
                    result_str = _format_business_results_as_table(business_list, city, business_type)
                except:
                    pass  # Keep original result if parsing fails
        
        workflow_result = {
            "success": True,
            "city": city,
            "business_type": business_type,
            "result": result_str,
            "max_results": max_results,
            "search_radius": search_radius
        }
        
        logger.info(f"Lead finder workflow completed for {city} - {business_type}")
        return workflow_result
        
    except Exception as e:
        error_msg = f"Lead finder workflow failed: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "city": city,
            "business_type": business_type,
            "error": error_msg,
            "max_results": max_results,
            "search_radius": search_radius
        }


def find_leads(city: str, business_type: str = "restaurants", **kwargs) -> Dict[str, Any]:
    """
    Main function to find business leads in a specified city.
    
    Args:
        city: City name to search for business leads
        business_type: Type of business to search for (e.g., "restaurants", "jewellery", "cafe")
        **kwargs: Additional search parameters
        
    Returns:
        Dictionary with lead discovery results
    """
    max_results = kwargs.get('max_results', 50)
    search_radius = kwargs.get('search_radius', 25000)
    
    return run_lead_finder_workflow(city, business_type, max_results, search_radius)


# For compatibility with reference pattern
lead_finder_agent = create_lead_finder_agent
root_agent = create_lead_finder_agent


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python agent.py <city_name> [business_type] [max_results] [search_radius]")
        print("Example: python agent.py 'Ahmedabad' 'restaurants' 10 1000")
        print("Example: python agent.py 'Mumbai' 'jewellery' 20 5000")
        print("Example: python agent.py 'Delhi' 'cafe' 15 2000")
        sys.exit(1)
    
    city = sys.argv[1]
    business_type = sys.argv[2] if len(sys.argv) > 2 else "restaurants"
    max_results = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    search_radius = int(sys.argv[4]) if len(sys.argv) > 4 else 25000
    
    print(f"🚀 Starting Lead Finder Workflow for: {city}")
    print(f"🏢 Business Type: {business_type}")
    print(f"📊 Parameters: max_results={max_results}, search_radius={search_radius}m")
    
    result = find_leads(city, business_type=business_type, max_results=max_results, search_radius=search_radius)
    
    print("\n📋 Lead Finder Results:")
    print(f"  Success: {result['success']}")
    print(f"  City: {result['city']}")
    print(f"  Business Type: {result['business_type']}")
    if result['success']:
        print(f"  Result: {result['result'][:300]}...")
    else:
        print(f"  Error: {result['error']}")
