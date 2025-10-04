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
        JSON string containing business information for MongoDB upload
    """
    results = _foursquare_search_safe(query, location, radius, limit)
    print(f"Search results type: {type(results)}")
    
    # Convert results to MongoDB-compatible format
    mongodb_results = []
    for business in results:
        mongodb_business = {
            "name": business.get('name', ''),
            "address": business.get('address', ''),
            "phone": business.get('phone'),
            "website": business.get('website'),
            "category": ', '.join(business.get('categories', [])) if business.get('categories') else None,
            "rating": business.get('rating'),
            "source": "map_search"
        }
        mongodb_results.append(mongodb_business)
    
    # Return JSON string for MongoDB upload tool
    import json
    return json.dumps(mongodb_results)


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
    """Get coordinates for any location using Nominatim API (dynamic geocoding only)."""
    geo_result = _geocode_city_dynamic(location)
    if geo_result:
        return (geo_result["lat"], geo_result["lon"])
    
    print(f"Could not find coordinates for location: {location}")
    return None


def _geocode_city_dynamic(city: str) -> Optional[Dict[str, float]]:
    """
    Get coordinates for any city using Nominatim OpenStreetMap API.
    This is the same approach used in cluster_search.py for dynamic geocoding.
    """
    USER_AGENT = "sales-agent/1.0 (contact: you@example.com)"
    
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city, "format": "json", "limit": 1, "addressdetails": 0},
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        return {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"])}
    except Exception as e:
        print(f"Dynamic geocoding failed for '{city}': {e}")
        return None


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
