"""
Main Lead Finder Agent implementation using CrewAI.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
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


def _extract_businesses_from_table(table_str: str, city: str, business_type: str) -> List[Dict[str, Any]]:
    """Extract business data from markdown table format."""
    businesses = []
    
    try:
        lines = table_str.split('\n')
        in_table = False
        
        for line in lines:
            line = line.strip()
            
            # Skip header lines
            if '| Business Name |' in line or '|---------------|' in line:
                in_table = True
                continue
            
            # Skip empty lines
            if not line or not in_table:
                continue
            
            # Parse table row
            if line.startswith('|') and line.endswith('|'):
                parts = [part.strip() for part in line.split('|')[1:-1]]  # Remove empty first/last parts
                
                if len(parts) >= 8:  # Ensure we have all columns
                    business = {
                        "name": parts[0],
                        "address": parts[1],
                        "phone": parts[2] if parts[2] != 'N/A' else None,
                        "email": parts[3] if parts[3] != 'N/A' else None,
                        "website": parts[4] if parts[4] not in ['N/A', '–'] else None,
                        "category": parts[5] if parts[5] != 'N/A' else business_type.title(),
                        "rating": float(parts[6]) if parts[6] != 'N/A' and parts[6].replace('.', '').isdigit() else None,
                        "source": parts[7] if parts[7] != 'N/A' else "unknown"
                    }
                    businesses.append(business)
        
        logger.info(f"🔍 Extracted {len(businesses)} businesses from table format")
        
    except Exception as e:
        logger.error(f"❌ Failed to extract businesses from table: {str(e)}")
    
    return businesses


def _format_business_results_as_structured_data(business_list: List[Dict[str, Any]], city: str, business_type: str) -> Dict[str, Any]:
    """Format business results as structured JSON data."""
    if not business_list:
        return {
            "businesses": [],
            "summary": {
                "total_leads": 0,
                "map_search_count": 0,
                "cluster_search_count": 0,
                "successfully_uploaded": False,
                "city": city,
                "business_type": business_type
            }
        }
    
    # Count sources
    map_search_count = 0
    cluster_search_count = 0
    
    # Clean and standardize business data
    cleaned_businesses = []
    for business in business_list:
        # Count sources
        source = business.get('source', 'unknown')
        if source == 'map_search':
            map_search_count += 1
        elif source == 'cluster_search':
            cluster_search_count += 1
        
        # Clean and standardize business data
        cleaned_business = {
            "name": business.get('name'),
            "address": business.get('address'),
            "phone": business.get('phone'),
            "email": business.get('email'),
            "website": business.get('website'),
            "category": business.get('category', business_type.title()),
            "rating": business.get('rating'),
            "source": source,
            "fsq_id": business.get('fsq_id'),
            "distance": business.get('distance'),
            "categories": business.get('categories', [])
        }
        
        # Remove None values and convert to null for JSON
        cleaned_business = {k: v for k, v in cleaned_business.items() if v is not None}
        cleaned_businesses.append(cleaned_business)
    
    # Create structured result
    result = {
        "businesses": cleaned_businesses,
        "summary": {
            "total_leads": len(business_list),
            "map_search_count": map_search_count,
            "cluster_search_count": cluster_search_count,
            "successfully_uploaded": True,
            "city": city,
            "business_type": business_type
        }
    }
    
    return result


def _format_business_results_as_table(business_list: List[Dict[str, Any]], city: str, business_type: str) -> str:
    """Format business results as a markdown table (legacy function)."""
    if not business_list:
        return f"No {business_type} businesses found in {city}."
    
    # Create table header
    table_lines = [f"**{business_type.title()} Business Leads in {city}**"]
    table_lines.append("")
    table_lines.append("| Business Name | Address | Phone | Email | Website | Category | Rating | Source |")
    table_lines.append("|---------------|---------|-------|-------|---------|----------|--------|--------|")
    
    # Count sources
    map_search_count = 0
    cluster_search_count = 0
    
    # Add table rows
    for business in business_list:
        name = business.get('name', 'N/A')
        address = business.get('address', 'N/A')
        phone = business.get('phone') or 'N/A'
        email = business.get('email') or 'N/A'  # Add email field
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
        
        table_lines.append(f"| {name} | {address} | {phone} | {email} | {website} | {category} | {rating} | {source} |")
    
    # Add summary
    table_lines.append("")
    table_lines.append("**Summary**")
    table_lines.append("")
    table_lines.append(f"- **Total leads found:** {len(business_list)}")
    table_lines.append(f"- **Map search results:** {map_search_count}")
    table_lines.append(f"- **Cluster search results:** {cluster_search_count}")
    table_lines.append(f"- **Successfully uploaded to MongoDB**")
    
    return "\n".join(table_lines)


def create_lead_finder_agent(city: str, business_type: str = "restaurants", session_id: Optional[str] = None) -> Crew:
    """
    Create the main Lead Finder Agent following the reference architecture.
    
    This agent implements the SequentialAgent pattern:
    - LeadFinderAgent (Root) → PotentialLeadFinderAgent → MergerAgent
    - Orchestrates the complete lead discovery workflow
    - Handles session management and error recovery
    
    Args:
        city: City name to search for business leads
        business_type: Type of business to search for (e.g., "restaurants", "jewellery", "cafe")
        session_id: Optional session ID for tracking
        
    Returns:
        CrewAI Crew with sequential execution workflow
    """
    
    # Initialize tools
    foursquare_tool = foursquare_search_tool_instance
    cluster_tool = ClusterSearchTool()
    
    # Create a custom MongoDB upload tool that includes session_id
    class SessionAwareMongoDBUploadTool(mongodb_upload_tool_instance.__class__):
        def __init__(self, session_id: str):
            super().__init__()
            # Store session_id as a private attribute
            self._session_id = session_id
            logger.info(f"🔍 SessionAwareMongoDBUploadTool initialized with session_id: {self._session_id}")
        
        def _run(self, business_data: str) -> str:
            """Upload business leads to MongoDB with the session_id."""
            logger.info(f"🔍 SessionAwareMongoDBUploadTool using session_id: {self._session_id}")
            
            # Handle both string and list inputs
            if isinstance(business_data, list):
                # Convert list to JSON string
                import json
                business_data = json.dumps(business_data)
                logger.info(f"🔍 Converted list to JSON string for MongoDB upload")
            elif isinstance(business_data, str):
                # Already a string, use as is
                logger.info(f"🔍 Using string input for MongoDB upload")
            else:
                # Convert other types to JSON string
                import json
                business_data = json.dumps(business_data)
                logger.info(f"🔍 Converted {type(business_data)} to JSON string for MongoDB upload")
            
            return mongodb_upload_tool_instance._run(business_data, self._session_id)
    
    mongodb_tool = SessionAwareMongoDBUploadTool(session_id or 'default_session')
    
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
        - Use the foursquare_search_tool with query="{business_type}", location="{city}", radius=5000, limit=3
        - This will return JSON data with business information
        
        Step 2: Search for additional businesses using cluster search
        - Use the cluster_search_tool with query="{city} {business_type}"
        - This will return additional business data in JSON format
        
        Step 3: Upload results to MongoDB
        - Combine the results from both searches
        - Ensure each business has a "source" field: "map_search" for Foursquare results, "cluster_search" for cluster results
        - Use the mongodb_upload_tool to store the combined results
        
        Step 4: Present results in structured JSON format
        - Return the business data as a clean JSON array
        - Include a summary object with statistics
        - Ensure all business objects have consistent field names
        
        You MUST call these tools in sequence and use their actual results. Do not just return the query parameters.
        """,
        agent=root_agent,
        expected_output=(
            f"A **JSON object** containing {business_type} business leads found in {city}. "
            "The JSON must have this structure: "
            '{"businesses": [{"name": "...", "address": "...", "phone": "...", "email": "...", "website": "...", "category": "...", "rating": "...", "source": "..."}], '
            '"summary": {"total_leads": 0, "map_search_count": 0, "cluster_search_count": 0, "successfully_uploaded": true}}. '
            "Each business object must have all fields (use null for missing data). "
            "Do NOT return markdown tables or raw tool outputs - only the structured JSON."
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


async def run_lead_finder_workflow(city: str, business_type: str = "restaurants", max_results: int = 3, search_radius: int = 25000, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the complete lead finder workflow with guaranteed MongoDB upload.
    
    Args:
        city: City name to search for business leads
        business_type: Type of business to search for (e.g., "restaurants", "jewellery", "cafe")
        max_results: Maximum number of results to return
        search_radius: Search radius in meters
        session_id: Optional session ID for tracking
        
    Returns:
        Dictionary with workflow results and statistics
    """
    try:
        logger.info(f"Starting lead finder workflow for {city} - {business_type}")
        logger.info(f"🔍 Lead finder received session_id: {session_id}")
        
        # Create lead finder crew
        crew = create_lead_finder_agent(city, business_type, session_id)
        
        # Execute the workflow asynchronously
        result = await asyncio.to_thread(crew.kickoff)
        
        # Extract and format result
        result_str = str(result)
        
        # Debug logging
        logger.info(f"🔍 Lead finder result type: {type(result)}")
        logger.info(f"🔍 Lead finder result length: {len(result_str)}")
        logger.info(f"🔍 Lead finder result preview: {result_str[:200]}...")
        
        # Try to extract business data from the result and upload directly
        leads_found = 0
        stored_count = 0
        business_list = []
        
        # Try to extract JSON data from the result
        import re
        import json
        
        # Look for structured JSON patterns (new format)
        structured_pattern = r'{"businesses":\s*\[.*?\],\s*"summary":\s*{.*?}}'
        structured_matches = re.findall(structured_pattern, result_str, re.DOTALL)
        
        if structured_matches:
            try:
                # Parse the structured JSON
                structured_data = json.loads(structured_matches[0])
                business_list = structured_data.get("businesses", [])
                leads_found = len(business_list)
                logger.info(f"🔍 Extracted {leads_found} businesses from structured JSON result")
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse structured JSON from agent result: {str(e)}")
        
        # Fallback: Look for old array JSON patterns
        if not business_list:
            json_pattern = r'\[{.*?}\]'
            json_matches = re.findall(json_pattern, result_str, re.DOTALL)
            
            if json_matches:
                try:
                    # Parse the JSON array
                    business_list = json.loads(json_matches[0])
                    leads_found = len(business_list)
                    logger.info(f"🔍 Extracted {leads_found} businesses from array JSON result")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to parse array JSON from agent result: {str(e)}")
        
        # Final fallback: Try to extract from table format
        if not business_list and "|" in result_str:
            logger.info("🔍 Attempting to extract business data from table format")
            business_list = _extract_businesses_from_table(result_str, city, business_type)
            leads_found = len(business_list)
        
        # Note: MongoDB upload is handled by the CrewAI agent's mongodb_upload_tool
        # No need for direct upload here to avoid race conditions
        if business_list:
            stored_count = len(business_list)  # Assume agent uploaded successfully
            logger.info(f"📤 Agent handled MongoDB upload for {len(business_list)} businesses")
        else:
            logger.warning(f"⚠️ No business data found to process")
            stored_count = 0
        
        # Format the result as structured data if we have business data
        structured_result = None
        if business_list:
            structured_result = _format_business_results_as_structured_data(business_list, city, business_type)
            result_str = json.dumps(structured_result, indent=2)
        
        workflow_result = {
            "success": True,
            "city": city,
            "business_type": business_type,
            "result": result_str,
            "structured_data": structured_result,
            "max_results": max_results,
            "search_radius": search_radius,
            "leads_found": leads_found,
            "stored_count": stored_count
        }
        
        logger.info(f"Lead finder workflow completed for {city} - {business_type}")
        logger.info(f"📊 Final stats: {leads_found} leads found, {stored_count} stored")
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
        **kwargs: Additional search parameters including session_id
        
    Returns:
        Dictionary with lead discovery results
    """
    max_results = kwargs.get('max_results', 3)
    search_radius = kwargs.get('search_radius', 25000)
    session_id = kwargs.get('session_id', None)
    
    return run_lead_finder_workflow(city, business_type, max_results, search_radius, session_id)


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