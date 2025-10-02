"""
Test Foursquare API with correct format
"""

import requests
import os

def test_foursquare_api():
    """Test the Foursquare API with the correct format."""
    
    # Your API key
    api_key = "EPSMWD4RIUS0PDEPHYXZ1IIM0MN3O2IOI5XKCBH4KTYCDLBW"
    
    # Test coordinates (Ahmedabad, Gujarat)
    lat, lng = 23.0225, 72.5714
    
    url = f"https://places-api.foursquare.com/places/search?query=IT services&ll={lat},{lng}&radius=5000"
    
    headers = {
        "accept": "application/json",
        "X-Places-Api-Version": "2025-06-17",
        "authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            print(f"\nFound {len(results)} IT services:")
            
            for i, place in enumerate(results[:3], 1):
                print(f"{i}. {place.get('name', 'N/A')}")
                print(f"   Address: {place.get('location', {}).get('address', 'N/A')}")
                print(f"   Rating: {place.get('rating', 'N/A')}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_foursquare_api()
