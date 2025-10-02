"""
Simple Foursquare test - no external dependencies needed
"""

import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if we can import our modules."""
    print("Testing imports...")
    
    try:
        from leads_finder.tools.foursquare_search_tools import foursquare_search_tool
        print("✓ foursquare_search_tools imported successfully")
    except Exception as e:
        print(f"✗ foursquare_search_tools import failed: {e}")
        return False
    
    try:
        from leads_finder.sub_agents.foursquare_agent_simple import foursquare_agent
        print("✓ foursquare_agent_simple imported successfully")
    except Exception as e:
        print(f"✗ foursquare_agent_simple import failed: {e}")
        return False
    
    try:
        from leads_finder.config.foursquare_config import config
        print("✓ foursquare_config imported successfully")
    except Exception as e:
        print(f"✗ foursquare_config import failed: {e}")
        return False
    
    return True

def test_api_key():
    """Test if API key is configured."""
    print("\nTesting API key configuration...")
    
    # Load from config.env.example
    api_key = None
    try:
        with open('config.env.example', 'r') as f:
            for line in f:
                if line.startswith('FOURSQUARE_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    break
    except Exception as e:
        print(f"✗ Could not read config.env.example: {e}")
        return False
    
    if api_key and api_key != 'your_foursquare_api_key_here':
        print(f"✓ API key found: {api_key[:10]}...")
        return True
    else:
        print("✗ API key not configured properly")
        return False

def test_basic_functionality():
    """Test basic functionality without making API calls."""
    print("\nTesting basic functionality...")
    
    try:
        from leads_finder.tools.foursquare_search_tools import FoursquareSearchTool
        
        # Create tool instance
        tool = FoursquareSearchTool()
        print("✓ FoursquareSearchTool created successfully")
        
        # Test address formatting
        test_location = {
            "address": "123 Main St",
            "locality": "New York",
            "region": "NY",
            "country": "US"
        }
        
        formatted_address = tool._format_address(test_location)
        print(f"✓ Address formatting works: {formatted_address}")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Foursquare Places Agent - Basic Test ===\n")
    
    # Run tests
    imports_ok = test_imports()
    api_ok = test_api_key()
    basic_ok = test_basic_functionality()
    
    print("\n=== Test Summary ===")
    print(f"Imports: {'✓' if imports_ok else '✗'}")
    print(f"API Key: {'✓' if api_ok else '✗'}")
    print(f"Basic Functionality: {'✓' if basic_ok else '✗'}")
    
    if imports_ok and api_ok and basic_ok:
        print("\n🎉 All basic tests passed! Foursquare implementation is ready.")
        print("\nTo test with actual API calls, you'll need to:")
        print("1. Set the FOURSQUARE_API_KEY environment variable")
        print("2. Run: python leads_finder/examples/foursquare_example.py")
    else:
        print("\n⚠ Some tests failed. Check the errors above.")
