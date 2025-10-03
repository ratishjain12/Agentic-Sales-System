"""
CrewAI-compatible tools for Foursquare search.
"""

from typing import Dict, List, Any, Optional
import os
import requests
from crewai.tools import BaseTool


class FoursquareSearchTool(BaseTool):
    """Tool for searching businesses using Foursquare Places API."""
    
    name: str = "Foursquare Search Tool"
    description: str = (
        "Search for businesses using Foursquare Places API. "
        "Use this tool to find business leads in specific locations. "
        "Parameters: query (business type), location (city/address), radius (meters), limit (max results)"
    )

    def _run(self, query: str, location: str, radius: int = 1000, limit: int = 20) -> str:
        """Search for businesses using Foursquare Places API."""
        return foursquare_search_tool(query, location, radius, limit)


def foursquare_search_tool(
    query: str, 
    location: str, 
    radius: int = 1000, 
    limit: int = 20
) -> str:
    """
    Search for businesses using Foursquare Places API.
    
    Args:
        query: Search query (business type, name, etc.)
        location: Location to search near (address, city, coordinates)
        radius: Search radius in meters (max 100000)
        limit: Maximum number of results (max 50)
        
    Returns:
        Formatted string containing business information
    """
    results = _foursquare_search_safe(query, location, radius, limit)
    print(f"Search results type: {type(results)}")
    
    # Return formatted text instead of JSON for better CrewAI agent processing
    return _format_results(results)


def _foursquare_search(
    query: str,
    location: str,
    radius: int = 1000,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Internal method to perform Foursquare search."""
    api_key = os.getenv("FOURSQUARE_API_KEY")
    if not api_key:
        print("FOURSQUARE_API_KEY environment variable not set")
        return []
    
    # Get coordinates for the location
    coordinates = _get_coordinates(location)
    if not coordinates:
        print(f"Could not find coordinates for location: {location}")
        return []
    
    lat, lng = coordinates
    
    url = f"https://places-api.foursquare.com/places/search"
    params = {
        "query": query,
        "ll": f"{lat},{lng}",
        "radius": min(radius, 100000),
        "limit": min(limit, 50)
    }
    
    headers = {
        "accept": "application/json",
        "X-Places-Api-Version": "2025-06-17",
        "authorization": f"Bearer {api_key}"
    }
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    # Debug: Print response content
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.text[:200]}...")
    
    try:
        data = response.json()
    except Exception as e:
        print(f"JSON parsing error: {e}")
        return []  # Return empty list instead of error string
    
    # Check if data is a dictionary
    if not isinstance(data, dict):
        print(f"Unexpected data type: {type(data)}")
        return []  # Return empty list instead of error string
    
    results = []
    
    for place in data.get("results", []):
        result = {
            "fsq_id": place.get("fsq_place_id", ""),  # Fixed: use fsq_place_id instead of fsq_id
            "name": place.get("name", ""),
            "address": _format_address(place.get("location", {})),
            "phone": place.get("contact", {}).get("phone"),
            "website": place.get("contact", {}).get("website"),
            "rating": place.get("rating"),
            "distance": place.get("distance"),
            "categories": [cat.get("name", "") for cat in place.get("categories", [])]
        }
        results.append(result)
    
    return results


def _foursquare_search_safe(
    query: str,
    location: str,
    radius: int = 1000,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Safe wrapper for Foursquare search that always returns a list."""
    try:
        return _foursquare_search(query, location, radius, limit)
    except Exception as e:
        print(f"Foursquare search error: {str(e)}")
        return []


def _get_coordinates(location: str) -> Optional[tuple]:
    """Get coordinates for common locations."""
    coordinates_map = {
        "new york": (40.7128, -74.0060),
        "new york, ny": (40.7128, -74.0060),
        "nyc": (40.7128, -74.0060),
        "san francisco": (37.7749, -122.4194),
        "san francisco, ca": (37.7749, -122.4194),
        "chicago": (41.8781, -87.6298),
        "chicago, il": (41.8781, -87.6298),
        "ahmedabad": (23.0225, 72.5714),
        "ahmedabad, gujarat": (23.0225, 72.5714),
        "bangalore": (12.9716, 77.5946),
        "bangalore, karnataka": (12.9716, 77.5946),
        "mumbai": (19.0760, 72.8777),
        "mumbai, maharashtra": (19.0760, 72.8777),
        "delhi": (28.7041, 77.1025),
        "delhi, india": (28.7041, 77.1025)
    }
    
    location_lower = location.lower().strip()
    return coordinates_map.get(location_lower)


def _format_address(location_data: Dict[str, Any]) -> str:
    """Format location data into a readable address string."""
    address_parts = []
    
    if location_data.get("address"):
        address_parts.append(location_data.get("address"))
    
    if location_data.get("locality"):
        address_parts.append(location_data.get("locality"))
    
    if location_data.get("region"):
        address_parts.append(location_data.get("region"))
    
    if location_data.get("country"):
        address_parts.append(location_data.get("country"))
    
    return ", ".join(address_parts)


def _format_results(results: List[Dict[str, Any]]) -> str:
    """Format search results for CrewAI agent consumption."""
    # Safety check for unexpected input types
    if not isinstance(results, list):
        print(f"Unexpected search results format: {type(results)}")
        return f"Unexpected search results format: {type(results)}"
    
    if not results:
        return "No businesses found for the given search criteria."
    
    formatted_results = []
    for i, business in enumerate(results, 1):
        # Debug: Check if business is a dict
        if not isinstance(business, dict):
            print(f"Business #{i} is not a dict: {type(business)} = {business}")
            continue
            
        formatted_business = f"""
Business #{i}:
- Name: {business.get('name', 'Not available')}
- Address: {business.get('address', 'Not available')}
- Phone: {business.get('phone') or 'Not available'}
- Website: {business.get('website') or 'Not available'}
- Rating: {business.get('rating') or 'Not available'}
- Distance: {business.get('distance', 'Not available')}m
- Categories: {', '.join(business.get('categories', [])) if business.get('categories') else 'Not specified'}
- Foursquare ID: {business.get('fsq_id', 'Not available')}
"""
        formatted_results.append(formatted_business)
    
    return "\n".join(formatted_results)


# Create tool instance
foursquare_search_tool_instance = FoursquareSearchTool()
