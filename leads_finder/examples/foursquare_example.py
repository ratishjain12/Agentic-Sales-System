"""
Example usage of Foursquare Places Agent for lead finding.
"""

import os
from dotenv import load_dotenv
from leads_finder.sub_agents.foursquare_agent import foursquare_agent
from leads_finder.tools.foursquare_search_tools import foursquare_search_nearby, foursquare_get_place_details

# Load environment variables
load_dotenv()


def example_search_restaurants():
    """Example: Search for restaurants in New York City."""
    print("=== Searching for restaurants in New York City ===")
    
    try:
        results = foursquare_search_nearby(
            query="restaurants",
            location="New York, NY",
            radius=2000,  # 2km radius
            limit=10
        )
        
        print(f"Found {len(results)} restaurants:")
        for i, restaurant in enumerate(results, 1):
            print(f"\n{i}. {restaurant['name']}")
            print(f"   Address: {restaurant.get('address', 'N/A')}")
            print(f"   Phone: {restaurant.get('phone', 'N/A')}")
            print(f"   Website: {restaurant.get('website', 'N/A')}")
            print(f"   Rating: {restaurant.get('rating', 'N/A')}")
            print(f"   Distance: {restaurant.get('distance', 'N/A')}m")
            
    except Exception as e:
        print(f"Error searching restaurants: {e}")


def example_search_coffee_shops():
    """Example: Search for coffee shops in San Francisco."""
    print("\n=== Searching for coffee shops in San Francisco ===")
    
    try:
        results = foursquare_search_nearby(
            query="coffee shops",
            location="San Francisco, CA",
            radius=1500,  # 1.5km radius
            limit=5
        )
        
        print(f"Found {len(results)} coffee shops:")
        for i, shop in enumerate(results, 1):
            print(f"\n{i}. {shop['name']}")
            print(f"   Address: {shop.get('address', 'N/A')}")
            print(f"   Phone: {shop.get('phone', 'N/A')}")
            print(f"   Rating: {shop.get('rating', 'N/A')}")
            print(f"   Price Level: {shop.get('price', 'N/A')}")
            
    except Exception as e:
        print(f"Error searching coffee shops: {e}")


def example_get_place_details():
    """Example: Get detailed information about a specific place."""
    print("\n=== Getting detailed place information ===")
    
    # First search for a place to get its ID
    try:
        results = foursquare_search_nearby(
            query="Starbucks",
            location="Times Square, New York",
            limit=1
        )
        
        if results:
            place_id = results[0]['fsq_id']
            print(f"Getting details for: {results[0]['name']}")
            
            details = foursquare_get_place_details(place_id)
            if details:
                print(f"\nDetailed Information:")
                print(f"Name: {details['name']}")
                print(f"Address: {details.get('address', 'N/A')}")
                print(f"Phone: {details.get('phone', 'N/A')}")
                print(f"Website: {details.get('website', 'N/A')}")
                print(f"Rating: {details.get('rating', 'N/A')}")
                print(f"Categories: {[cat.get('name', '') for cat in details.get('categories', [])]}")
                
    except Exception as e:
        print(f"Error getting place details: {e}")


def example_agent_usage():
    """Example: Using the Foursquare agent for lead finding."""
    print("\n=== Using Foursquare Agent for Lead Finding ===")
    
    try:
        # Create a task for the agent
        task = foursquare_agent.create_task(
            "Find 5 high-rated restaurants in downtown Chicago that would be good prospects for a food delivery service partnership. Include their contact information and ratings."
        )
        
        # Execute the task
        result = foursquare_agent.execute_task(task)
        print(f"Agent Result: {result}")
        
    except Exception as e:
        print(f"Error using agent: {e}")


if __name__ == "__main__":
    # Check if API key is configured
    if not os.getenv("FOURSQUARE_API_KEY"):
        print("Please set FOURSQUARE_API_KEY environment variable.")
        print("Get your API key from: https://foursquare.com/developers/orgs/68de853467bf093d3e59bafa/projects/68de853567bf093d3e59bb08/settings")
        exit(1)
    
    # Run examples
    example_search_restaurants()
    example_search_coffee_shops()
    example_get_place_details()
    example_agent_usage()
