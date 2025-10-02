"""
Simplified Foursquare Places Agent - No CrewAI dependency
"""

from typing import List, Dict, Any, Optional
from ..tools.foursquare_search_tools import foursquare_search_nearby, foursquare_get_place_details


class FoursquareAgent:
    """Simplified Foursquare Places Agent for lead finding."""
    
    def __init__(self):
        self.name = "Foursquare Places Lead Finder"
        self.description = "Agent specialized in finding business information using Foursquare Places API"
    
    def search_businesses(
        self,
        query: str,
        location: str,
        radius: int = 1000,
        limit: int = 20,
        categories: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for businesses using Foursquare Places API.
        
        Args:
            query: Search query (business type, name, etc.)
            location: Location to search near (address, city, coordinates)
            radius: Search radius in meters (max 100000)
            limit: Maximum number of results (max 50)
            categories: Comma-separated category IDs to filter by
            
        Returns:
            List of dictionaries containing business information
        """
        try:
            results = foursquare_search_nearby(
                query=query,
                location=location,
                radius=radius,
                limit=limit,
                categories=categories
            )
            
            print(f"🔍 Found {len(results)} businesses for '{query}' near '{location}'")
            
            # Display results
            for i, business in enumerate(results, 1):
                print(f"\n{i}. {business['name']}")
                print(f"   📍 Address: {business.get('address', 'N/A')}")
                print(f"   📞 Phone: {business.get('phone', 'N/A')}")
                print(f"   🌐 Website: {business.get('website', 'N/A')}")
                print(f"   ⭐ Rating: {business.get('rating', 'N/A')}")
                print(f"   📏 Distance: {business.get('distance', 'N/A')}m")
            
            return results
            
        except Exception as e:
            print(f"❌ Error searching businesses: {e}")
            return []
    
    def get_business_details(self, fsq_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific business.
        
        Args:
            fsq_id: Foursquare place ID
            
        Returns:
            Dictionary containing detailed business information or None if not found
        """
        try:
            details = foursquare_get_place_details(fsq_id)
            if details:
                print(f"📋 Detailed information for: {details['name']}")
                print(f"   📍 Address: {details.get('address', 'N/A')}")
                print(f"   📞 Phone: {details.get('phone', 'N/A')}")
                print(f"   🌐 Website: {details.get('website', 'N/A')}")
                print(f"   ⭐ Rating: {details.get('rating', 'N/A')}")
                print(f"   💰 Price Level: {details.get('price', 'N/A')}")
                print(f"   🕒 Hours: {details.get('hours', 'N/A')}")
            return details
            
        except Exception as e:
            print(f"❌ Error getting business details: {e}")
            return None
    
    def find_leads(
        self,
        business_type: str,
        location: str,
        radius: int = 2000,
        min_rating: float = 3.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find qualified leads based on business type, location, and rating.
        
        Args:
            business_type: Type of business to search for
            location: Location to search near
            radius: Search radius in meters
            min_rating: Minimum rating threshold
            limit: Maximum number of results
            
        Returns:
            List of qualified leads
        """
        print(f"🎯 Finding {business_type} leads near {location}")
        print(f"   📏 Radius: {radius}m")
        print(f"   ⭐ Min Rating: {min_rating}")
        print(f"   📊 Max Results: {limit}")
        
        results = self.search_businesses(
            query=business_type,
            location=location,
            radius=radius,
            limit=limit
        )
        
        # Filter by rating
        qualified_leads = []
        for business in results:
            rating = business.get('rating', 0)
            if rating >= min_rating:
                qualified_leads.append(business)
        
        print(f"\n✅ Found {len(qualified_leads)} qualified leads (rating >= {min_rating})")
        
        return qualified_leads


# Create a global instance
foursquare_agent = FoursquareAgent()
