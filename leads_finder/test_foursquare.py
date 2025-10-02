"""
Test script for Foursquare Places Agent
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

def test_foursquare_tools():
    """Test the Foursquare search tools."""
    print("Testing Foursquare search tools...")
    
    try:
        from leads_finder.tools.foursquare_search_tools import foursquare_search_nearby
        
        # Test basic search
        results = foursquare_search_nearby(
            query="coffee",
            location="Surat, Gujarat",
            radius=1000,
            limit=3
        )
        
        print(f"✓ Search successful: Found {len(results)} results")
        
        if results:
            first_result = results[0]
            print(f"✓ First result: {first_result['name']}")
            print(f"✓ Address: {first_result.get('address', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Search failed: {e}")
        return False


def test_foursquare_agent():
    """Test the Foursquare agent."""
    print("\nTesting Foursquare agent...")
    
    try:
        from leads_finder.sub_agents.foursquare_agent import foursquare_agent
        
        print(f"✓ Agent created: {foursquare_agent.role}")
        print(f"✓ Agent goal: {foursquare_agent.goal}")
        print(f"✓ Available tools: {len(foursquare_agent.tools)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Agent creation failed: {e}")
        return False


def test_configuration():
    """Test the configuration."""
    print("\nTesting configuration...")
    
    try:
        from leads_finder.config.foursquare_config import config
        
        if config.api_key:
            print("✓ API key configured")
        else:
            print("⚠ API key not configured (set FOURSQUARE_API_KEY environment variable)")
        
        print(f"✓ Default radius: {config.default_radius}m")
        print(f"✓ Default limit: {config.default_limit}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


if __name__ == "__main__":
    print("=== Foursquare Places Agent Test Suite ===\n")
    
    # Test configuration
    config_ok = test_configuration()
    
    # Test agent creation
    agent_ok = test_foursquare_agent()
    
    # Test tools (only if API key is configured)
    if config_ok and os.getenv("FOURSQUARE_API_KEY"):
        tools_ok = test_foursquare_tools()
    else:
        print("\nSkipping tools test (no API key configured)")
        tools_ok = True
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Configuration: {'✓' if config_ok else '✗'}")
    print(f"Agent: {'✓' if agent_ok else '✗'}")
    print(f"Tools: {'✓' if tools_ok else '✗'}")
    
    if config_ok and agent_ok and tools_ok:
        print("\n🎉 All tests passed! Foursquare Places Agent is ready to use.")
    else:
        print("\n⚠ Some tests failed. Check the errors above.")
