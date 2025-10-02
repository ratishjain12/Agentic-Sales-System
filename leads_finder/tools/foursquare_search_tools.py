"""
Foursquare Places API search tools for lead finding.
"""

import os
import requests
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class FoursquareSearchResult(BaseModel):
    """Model for Foursquare search results."""
    fsq_id: str = Field(description="Foursquare place ID")
    name: str = Field(description="Business name")
    location: Dict[str, Any] = Field(description="Location information")
    categories: List[Dict[str, Any]] = Field(description="Business categories")
    distance: Optional[int] = Field(description="Distance in meters", default=None)
    geocodes: Dict[str, Any] = Field(description="Geographic coordinates")
    address: Optional[str] = Field(description="Full address", default=None)
    phone: Optional[str] = Field(description="Phone number", default=None)
    website: Optional[str] = Field(description="Website URL", default=None)
    rating: Optional[float] = Field(description="Business rating", default=None)
    price: Optional[int] = Field(description="Price level (1-4)", default=None)
    hours: Optional[Dict[str, Any]] = Field(description="Business hours", default=None)


class FoursquareSearchTool:
    """Tool for searching businesses using Foursquare Places API."""
    
    def __init__(self):
        self.api_key = os.getenv("FOURSQUARE_API_KEY")
        self.base_url = "https://places-api.foursquare.com/places"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "X-Places-Api-Version": "2025-06-17"
        }
    
    def search_nearby(
        self,
        query: str,
        location: str,
        radius: int = 1000,
        limit: int = 20,
        categories: Optional[str] = None
    ) -> List[FoursquareSearchResult]:
        """
        Search for businesses near a location using Foursquare Places API.
        
        Args:
            query: Search query (business type, name, etc.)
            location: Location to search near (address, city, coordinates)
            radius: Search radius in meters (max 100000)
            limit: Maximum number of results (max 50)
            categories: Comma-separated category IDs to filter by
            
        Returns:
            List of FoursquareSearchResult objects
        """
        if not self.api_key:
            raise ValueError("FOURSQUARE_API_KEY environment variable not set")
        
        # First, geocode the location to get coordinates
        coordinates = self._geocode_location(location)
        if not coordinates:
            raise ValueError(f"Could not geocode location: {location}")
        
        lat, lng = coordinates
        
        # Build search parameters using coordinates
        params = {
            "query": query,
            "ll": f"{lat},{lng}",
            "radius": min(radius, 100000),  # API limit
            "limit": min(limit, 50),  # API limit
            "fields": "fsq_id,name,location,categories,distance,geocodes,contact,hours,rating,price"
        }
        
        if categories:
            params["categories"] = categories
        
        try:
            response = requests.get(
                f"{self.base_url}/search",
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for place in data.get("results", []):
                result = FoursquareSearchResult(
                    fsq_id=place.get("fsq_id", ""),
                    name=place.get("name", ""),
                    location=place.get("location", {}),
                    categories=place.get("categories", []),
                    distance=place.get("distance"),
                    geocodes=place.get("geocodes", {}),
                    address=self._format_address(place.get("location", {})),
                    phone=place.get("contact", {}).get("phone"),
                    website=place.get("contact", {}).get("website"),
                    rating=place.get("rating"),
                    price=place.get("price"),
                    hours=place.get("hours", {})
                )
                results.append(result)
            
            return results
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Foursquare API request failed: {str(e)}")
    
    def get_place_details(self, fsq_id: str) -> Optional[FoursquareSearchResult]:
        """
        Get detailed information about a specific place.
        
        Args:
            fsq_id: Foursquare place ID
            
        Returns:
            FoursquareSearchResult object or None if not found
        """
        if not self.api_key:
            raise ValueError("FOURSQUARE_API_KEY environment variable not set")
        
        params = {
            "fields": "fsq_id,name,location,categories,geocodes,contact,hours,rating,price,description,features,stats"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/{fsq_id}",
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            place = response.json()
            
            return FoursquareSearchResult(
                fsq_id=place.get("fsq_id", ""),
                name=place.get("name", ""),
                location=place.get("location", {}),
                categories=place.get("categories", []),
                geocodes=place.get("geocodes", {}),
                address=self._format_address(place.get("location", {})),
                phone=place.get("contact", {}).get("phone"),
                website=place.get("contact", {}).get("website"),
                rating=place.get("rating"),
                price=place.get("price"),
                hours=place.get("hours", {})
            )
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Foursquare API request failed: {str(e)}")
    
    def _geocode_location(self, location: str) -> Optional[tuple]:
        """
        Geocode a location string to get latitude and longitude.
        
        Args:
            location: Location string (address, city, etc.)
            
        Returns:
            Tuple of (latitude, longitude) or None if geocoding fails
        """
        try:
            # Use Foursquare's autocomplete API for geocoding
            params = {
                "query": location,
                "types": "geo"
            }
            
            response = requests.get(
                f"{self.base_url}/autocomplete",
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            if results:
                # Get the first result
                first_result = results[0]
                if "geocodes" in first_result and "main" in first_result["geocodes"]:
                    geocodes = first_result["geocodes"]["main"]
                    return (geocodes["latitude"], geocodes["longitude"])
            
            return None
            
        except requests.exceptions.RequestException:
            return None
    
    def _format_address(self, location_data: Dict[str, Any]) -> str:
        """
        Format location data into a readable address string.
        
        Args:
            location_data: Location data from Foursquare API
            
        Returns:
            Formatted address string
        """
        address_parts = []
        
        if location_data.get("address"):
            address_parts.append(location_data["address"])
        
        if location_data.get("locality"):
            address_parts.append(location_data["locality"])
        
        if location_data.get("region"):
            address_parts.append(location_data["region"])
        
        if location_data.get("postcode"):
            address_parts.append(location_data["postcode"])
        
        if location_data.get("country"):
            address_parts.append(location_data["country"])
        
        return ", ".join(address_parts)


# Create a global instance
foursquare_search_tool = FoursquareSearchTool()


def foursquare_search_nearby(
    query: str,
    location: str,
    radius: int = 1000,
    limit: int = 20,
    categories: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for businesses near a location using Foursquare Places API.
    
    Args:
        query: Search query (business type, name, etc.)
        location: Location to search near (address, city, coordinates)
        radius: Search radius in meters (max 100000)
        limit: Maximum number of results (max 50)
        categories: Comma-separated category IDs to filter by
        
    Returns:
        List of dictionaries containing business information
    """
    results = foursquare_search_tool.search_nearby(
        query=query,
        location=location,
        radius=radius,
        limit=limit,
        categories=categories
    )
    
    # Convert to dictionaries for easier handling
    return [result.dict() for result in results]


def foursquare_get_place_details(fsq_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific place.
    
    Args:
        fsq_id: Foursquare place ID
        
    Returns:
        Dictionary containing detailed place information or None if not found
    """
    result = foursquare_search_tool.get_place_details(fsq_id)
    return result.dict() if result else None
