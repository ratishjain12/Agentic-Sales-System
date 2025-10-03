"""
Test script for cost-effective CrewAI Lead Finder configuration.
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv('env.txt')


def test_configuration():
    """Test the cost-effective configuration."""
    print("🧪 Testing Cost-Effective CrewAI Configuration")
    print("=" * 50)
    
    # Test 1: Check API keys
    print("1. Checking API keys...")
    openai_key = os.getenv("OPENAI_API_KEY")
    foursquare_key = os.getenv("FOURSQUARE_API_KEY")
    cerebras_key = os.getenv("CEREBRAS_API_KEY")
    
    print(f"   ✅ OpenAI API Key: {'Set' if openai_key and openai_key != 'your_openai_api_key_here' else '❌ Missing'}")
    print(f"   ✅ Foursquare API Key: {'Set' if foursquare_key else '❌ Missing'}")
    print(f"   ✅ Cerebras API Key: {'Set' if cerebras_key and cerebras_key != 'your_cerebras_api_key_here' else '❌ Missing'}")
    
    # Test 2: Test LLM configurations
    print("\n2. Testing LLM configurations...")
    try:
        from leads_finder.llm_config import COST_EFFECTIVE_LLM, LEAD_FINDER_LLM
        
        print("   ✅ GPT-5-nano LLM configuration loaded")
        print("   ✅ Cerebras llama3.1-8b LLM configuration loaded")
        
        # Test model names
        print(f"   📝 GPT-5-nano model: {COST_EFFECTIVE_LLM.model}")
        print(f"   📝 Cerebras model: {LEAD_FINDER_LLM.model}")
        
    except Exception as e:
        print(f"   ❌ Error loading LLM configurations: {e}")
        return False
    
    # Test 3: Test agent creation
    print("\n3. Testing agent creation...")
    try:
        from leads_finder.sub_agents.crewai_lead_finder_agent import create_lead_finder_agent
        
        # Test cost-effective agent
        cost_effective_agent = create_lead_finder_agent(use_cost_effective=True)
        print("   ✅ Cost-effective agent (GPT-5-nano) created")
        
        # Test Cerebras agent
        cerebras_agent = create_lead_finder_agent(use_cost_effective=False)
        print("   ✅ Cerebras agent (llama3.1-8b) created")
        
    except Exception as e:
        print(f"   ❌ Error creating agents: {e}")
        return False
    
    # Test 4: Test crew creation
    print("\n4. Testing crew creation...")
    try:
        from leads_finder.crew.lead_finder_crew import get_lead_finder_crew
        
        # Test cost-effective crew
        cost_effective_crew = get_lead_finder_crew(use_cost_effective=True)
        print("   ✅ Cost-effective crew created")
        
        # Test Cerebras crew
        cerebras_crew = get_lead_finder_crew(use_cost_effective=False)
        print("   ✅ Cerebras crew created")
        
    except Exception as e:
        print(f"   ❌ Error creating crews: {e}")
        return False
    
    # Test 5: Test tool integration
    print("\n5. Testing tool integration...")
    try:
        from leads_finder.tools.crewai_foursquare_tool import foursquare_search_tool
        print("   ✅ Foursquare search tool loaded")
        
    except Exception as e:
        print(f"   ❌ Error loading tools: {e}")
        return False
    
    print("\n🎉 All tests passed! Configuration is ready.")
    print("\n💰 Cost-Effective Setup Summary:")
    print("   • Primary LLM: GPT-5-nano (OpenAI) - $0.05/$0.40 per 1M tokens")
    print("   • Backup LLM: Cerebras llama3.1-8b - Cheaper than 70B model")
    print("   • Embeddings: text-embedding-3-small (OpenAI)")
    print("   • Tools: Foursquare Places API (free tier)")
    
    return True


def show_usage_examples():
    """Show usage examples for both configurations."""
    print("\n📚 Usage Examples:")
    print("=" * 30)
    
    print("\n1. Using Cost-Effective GPT-5-nano (Default):")
    print("""
from leads_finder.crew.lead_finder_crew import get_lead_finder_crew

# Get cost-effective crew (GPT-5-nano)
crew = get_lead_finder_crew(use_cost_effective=True)

# Search for leads
result = crew.search_leads("restaurants", "New York", radius=2000, limit=10)
""")
    
    print("\n2. Using Cerebras llama3.1-8b:")
    print("""
from leads_finder.crew.lead_finder_crew import get_lead_finder_crew

# Get Cerebras crew (llama3.1-8b)
crew = get_lead_finder_crew(use_cost_effective=False)

# Search for leads
result = crew.search_leads("coffee shops", "San Francisco", radius=1000, limit=5)
""")


if __name__ == "__main__":
    success = test_configuration()
    
    if success:
        show_usage_examples()
        
        print("\n🚀 Ready to run the demo!")
        print("Run: python demo_crewai_lead_finder.py")
        print("Or quick test: python demo_crewai_lead_finder.py --quick")
    else:
        print("\n❌ Configuration issues found. Please fix them before running the demo.")
