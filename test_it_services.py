"""
Comprehensive IT Services Search Test
"""

import requests
import os

def test_it_services_search():
    """Test searching for various IT services."""
    
    api_key = "EPSMWD4RIUS0PDEPHYXZ1IIM0MN3O2IOI5XKCBH4KTYCDLBW"
    
    # Test different locations
    locations = [
        ("Ahmedabad, Gujarat", 23.0225, 72.5714),
        ("Bangalore, Karnataka", 12.9716, 77.5946),
        ("Mumbai, Maharashtra", 19.0760, 72.8777)
    ]
    
    # Test different IT service queries
    queries = [
        "IT services",
        "software company", 
        "technology services",
        "computer services",
        "IT consulting"
    ]
    
    headers = {
        "accept": "application/json",
        "X-Places-Api-Version": "2025-06-17",
        "authorization": f"Bearer {api_key}"
    }
    
    for city_name, lat, lng in locations:
        print(f"\n🔍 Searching in {city_name}")
        print("=" * 50)
        
        for query in queries:
            url = f"https://places-api.foursquare.com/places/search?query={query}&ll={lat},{lng}&radius=10000"
            
            try:
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    print(f"\n📊 '{query}': Found {len(results)} results")
                    
                    # Show top 2 results
                    for i, place in enumerate(results[:2], 1):
                        name = place.get('name', 'N/A')
                        address = place.get('location', {}).get('address', 'N/A')
                        phone = place.get('contact', {}).get('phone', 'N/A')
                        website = place.get('contact', {}).get('website', 'N/A')
                        rating = place.get('rating', 'N/A')
                        
                        print(f"  {i}. {name}")
                        print(f"     📍 {address}")
                        print(f"     📞 {phone}")
                        print(f"     🌐 {website}")
                        print(f"     ⭐ {rating}")
                        print()
                        
                else:
                    print(f"❌ Error for '{query}': {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Exception for '{query}': {e}")
            
            # Small delay to respect rate limits
            import time
            time.sleep(0.5)

if __name__ == "__main__":
    test_it_services_search()
