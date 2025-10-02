"""
Simple Foursquare Places Agent Example - No CrewAI
"""

import os
from dotenv import load_dotenv
from leads_finder.sub_agents.foursquare_agent_simple import foursquare_agent

# Load environment variables
load_dotenv()


def example_search_restaurants():
    """Example: Search for restaurants in New York City."""
    print("=== Searching for restaurants in New York City ===")
    
    results = foursquare_agent.search_businesses(
        query="restaurants",
        location="New York, NY",
        radius=2000,  # 2km radius
        limit=5
    )
    
    return results


def example_search_coffee_shops():
    """Example: Search for coffee shops in San Francisco."""
    print("\n=== Searching for coffee shops in San Francisco ===")
    
    results = foursquare_agent.search_businesses(
        query="coffee shops",
        location="San Francisco, CA",
        radius=1500,  # 1.5km radius
        limit=3
    )
    
    return results


def example_find_leads():
    """Example: Find qualified leads."""
    print("\n=== Finding qualified restaurant leads ===")
    
    leads = foursquare_agent.find_leads(
        business_type="restaurants",
        location="Surat, Gujarat",
        radius=3000,
        min_rating=4.0,
        limit=5
    )
    
    return leads


if __name__ == "__main__":
    # Check if API key is configured
    if not os.getenv("FOURSQUARE_API_KEY"):
        print("Please set FOURSQUARE_API_KEY environment variable.")
        print("Get your API key from: https://foursquare.com/developers/orgs/68de853467bf093d3e59bafa/projects/68de853567bf093d3e59bb08/settings")
        exit(1)
    
    print("🚀 Foursquare Places Agent - Simple Example\n")
    
    # Run examples
    try:
        example_search_restaurants()
        example_search_coffee_shops()
        example_find_leads()
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
