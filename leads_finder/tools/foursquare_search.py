"""
Foursquare search tool implementation.
"""

import os
import requests
from typing import Dict, List, Any, Optional


def foursquare_search_tool(
    query: str,
    location: str,
    radius: int = 1000,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Search for businesses using Foursquare Places API.
    
    Args:
        query: Search query (business type, name, etc.)
        location: Location to search near (address, city, coordinates)
        radius: Search radius in meters (max 100000)
        limit: Maximum number of results (max 50)
        
    Returns:
        List of dictionaries containing business information
    """
    api_key = os.getenv("FOURSQUARE_API_KEY")
    if not api_key:
        raise ValueError("FOURSQUARE_API_KEY environment variable not set")
    
    # Simple geocoding for common cities
    coordinates = _get_coordinates(location)
    if not coordinates:
        raise ValueError(f"Could not find coordinates for location: {location}")
    
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
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        for place in data.get("results", []):
            result = {
                "fsq_id": place.get("fsq_id", ""),
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
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Foursquare API request failed: {str(e)}")


def _get_coordinates(location: str) -> Optional[tuple]:
    """Get coordinates for common locations."""
    # Simple coordinate mapping for common cities
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
        address_parts.append(location_data["address"])
    
    if location_data.get("locality"):
        address_parts.append(location_data["locality"])
    
    if location_data.get("region"):
        address_parts.append(location_data["region"])
    
    if location_data.get("country"):
        address_parts.append(location_data["country"])
    
    return ", ".join(address_parts)
