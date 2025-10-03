"""
Simple test for Foursquare Places Agent
"""

import os
from dotenv import load_dotenv
from leads_finder.tools.foursquare_search import foursquare_search_tool

# Load environment variables from .env file
load_dotenv()

def test_foursquare():
    """Test the Foursquare search tool."""
    
    print("🔍 Testing Foursquare Places API")
    print("=" * 40)
    
    try:
        # Test IT services search in Ahmedabad
        results = foursquare_search_tool(
            query="IT services",
            location="Ahmedabad, Gujarat",
            radius=5000,
            limit=5
        )
        
        print(f"✅ Found {len(results)} IT services in Ahmedabad:")
        
        for i, business in enumerate(results, 1):
            print(f"\n{i}. {business['name']}")
            print(f"   📍 Address: {business.get('address', 'N/A')}")
            print(f"   📞 Phone: {business.get('phone', 'N/A')}")
            print(f"   🌐 Website: {business.get('website', 'N/A')}")
            print(f"   ⭐ Rating: {business.get('rating', 'N/A')}")
            print(f"   📏 Distance: {business.get('distance', 'N/A')}m")
            print(f"   🏷️ Categories: {', '.join(business.get('categories', []))}")
        
        print(f"\n🎉 Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_foursquare()
