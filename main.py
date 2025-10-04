"""
Agentic Sales Agent - Main Entry Point
A sophisticated AI-powered sales lead generation system using CrewAI and multiple LLM providers.
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv('.env')

from leads_finder.clients.map_search_service import search_leads, analyze_leads
from leads_finder.sub_agents.cluster_search_agent import run_cluster_search
from sdr.agents.sdr_main_agent import execute_sdr_main_workflow
from sdr.tools.phone_call_tool import phone_call_tool


def main():
    """Main entry point for the Agentic Sales Agent."""
    print("Agentic Sales Agent")
    print("=" * 50)
    print("AI-powered lead generation system")
    print("=" * 50)
    
    # Check if required API keys are set
    required_keys = ["FOURSQUARE_API_KEY", "OPENAI_API_KEY", "CEREBRAS_API_KEY"]
    # Add ElevenLabs keys for calling functionality
    elevenlabs_keys = ["ELEVENLABS_API_KEY", "ELEVENLABS_AGENT_ID", "ELEVENLABS_PHONE_NUMBER_ID"]
    missing_keys = [key for key in required_keys if not os.getenv(key) or os.getenv(key) == f"your_{key.lower()}_here"]
    
    if missing_keys:
        print(f"Missing required API keys: {', '.join(missing_keys)}")
        print("Please update your .env file with valid API keys.")
        return
    
    # Check ElevenLabs keys for calling functionality
    elevenlabs_set = all([os.getenv(key) and os.getenv(key) != f"your_{key.lower()}_here" for key in elevenlabs_keys])
    
    print("API keys configured successfully!")
    if elevenlabs_set:
        print("✅ ElevenLabs calling functionality available!")
    else:
        print("⚠️  ElevenLabs calling not available (missing API keys)")
    
    # Interactive menu
    while True:
        print("\n" + "=" * 50)
        print("Select an option:")
        print("1. Search leads using Foursquare API")
        print("2. Search leads using Cluster Search (OSM)")
        print("3. Run comprehensive lead analysis")
        print("4. Run complete SDR workflow (Research → Proposal → Call)")
        print("5. Test phone calling agent only")
        print("6. Run system tests")
        print("7. Exit")
        
        try:
            choice = input("\nEnter your choice (1-7): ").strip()
            
            if choice == '1':
                run_foursquare_search()
            elif choice == '2':
                run_cluster_search_demo()
            elif choice == '3':
                run_comprehensive_analysis()
            elif choice == '4':
                if elevenlabs_set:
                    run_complete_sdr_workflow()
                else:
                    print("\n⚠️  Calling functionality requires ElevenLabs API keys:")
                    print("   - ELEVENLABS_API_KEY")
                    print("   - ELEVENLABS_AGENT_ID") 
                    print("   - ELEVENLABS_PHONE_NUMBER_ID")
            elif choice == '5':
                if elevenlabs_set:
                    run_calling_test()
                else:
                    print("\n⚠️  Calling functionality requires ElevenLabs API keys:")
                    print("   - ELEVENLABS_API_KEY")
                    print("   - ELEVENLABS_AGENT_ID") 
                    print("   - ELEVENLABS_PHONE_NUMBER_ID")
            elif choice == '6':
                run_system_tests()
            elif choice == '7':
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please select 1-7.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Unexpected error: {str(e)}")


def run_foursquare_search():
    """Run Foursquare-based lead search."""
    print("\nFoursquare Lead Search")
    print("-" * 30)
    
    # Get search parameters
    query = input("Enter business type (e.g., 'restaurants', 'IT services'): ").strip()
    location = input("Enter location (e.g., 'New York', 'Ahmedabad'): ").strip()
    
    if not query or not location:
        print("Both query and location are required.")
        return
    
    try:
        radius = int(input("Enter search radius in meters (default: 2000): ").strip() or "2000")
        limit = int(input("Enter max results (default: 10): ").strip() or "10")
    except ValueError:
        print("Invalid radius or limit. Using defaults.")
        radius, limit = 2000, 10
    
    print(f"\nSearching for {query} in {location}...")
    print("This may take a few moments...")
    
    try:
        result = search_leads(query, location, radius=radius, limit=limit, use_cost_effective=False)
        
        print("\n" + "=" * 50)
        print("SEARCH RESULTS")
        print("=" * 50)
        print(result)
        
        # Ask if user wants to analyze the results
        analyze = input("\nWould you like to analyze these results? (y/n): ").strip().lower()
        if analyze == 'y':
            print("\nAnalyzing results...")
            analysis_result = analyze_leads(str(result), use_cost_effective=False)
            
            print("\n" + "=" * 50)
            print("ANALYSIS RESULTS")
            print("=" * 50)
            print(analysis_result)
            
    except Exception as e:
        print(f"Error during search: {str(e)}")
        print("This might be due to API rate limits or network issues.")


def run_cluster_search_demo():
    """Run cluster search demo."""
    print("\nCluster Search Demo")
    print("-" * 30)
    
    city = input("Enter city name (e.g., 'New York', 'Ahmedabad'): ").strip()
    
    if not city:
        print("City name is required.")
        return
    
    print(f"\nSearching for businesses in {city} using OSM data...")
    print("This may take a few moments...")
    
    try:
        result = run_cluster_search(city)
        
        print("\n" + "=" * 50)
        print("CLUSTER SEARCH RESULTS")
        print("=" * 50)
        print(result)
        
    except Exception as e:
        print(f"Error during cluster search: {str(e)}")


def run_comprehensive_analysis():
    """Run comprehensive lead analysis."""
    print("\nComprehensive Lead Analysis")
    print("-" * 30)
    
    # Use Cerebras for analysis
    
    # Demo parameters
    demo_queries = [
        ("restaurants", "New York"),
        ("coffee shops", "San Francisco"),
        ("IT services", "Ahmedabad"),
        ("hotels", "Chicago"),
        ("pharmacies", "Bangalore")
    ]
    
    print("Available demo searches:")
    for i, (query, location) in enumerate(demo_queries, 1):
        print(f"{i}. {query} in {location}")
    
    try:
        choice = int(input("\nSelect a demo (1-5): ").strip()) - 1
        
        if 0 <= choice < len(demo_queries):
            query, location = demo_queries[choice]
            
            print(f"\nSearching for {query} in {location}...")
            search_result = search_leads(query, location, radius=2000, limit=10, use_cost_effective=False)
            
            print("\nAnalyzing search results...")
            analysis_result = analyze_leads(str(search_result), use_cost_effective=False)
            
            print("\n" + "=" * 50)
            print("COMPREHENSIVE ANALYSIS")
            print("=" * 50)
            print("SEARCH RESULTS:")
            print(search_result)
            print("\nANALYSIS RESULTS:")
            print(analysis_result)
            
        else:
            print("Invalid choice.")
            
    except ValueError:
        print("Invalid input.")
    except Exception as e:
        print(f"Error during analysis: {str(e)}")


def run_complete_sdr_workflow():
    """Run the complete SDR workflow (Research → Proposal → Call → Analysis)."""
    print("\nComplete SDR Workflow")
    print("-" * 30)
    print("This will run the full pipeline: Research → Proposal → Call → Classification")
    
    # Get business data
    print("\nEnter business information:")
    name = input("Business name: ").strip()
    phone = input("Phone number: ").strip()
    email = input("Email (optional): ").strip()
    address = input("Address: ").strip()
    business_type = input("Business type (optional): ").strip()
    
    if not name or not phone:
        print("Business name and phone number are required.")
        return
    
    business_data = {
        "name": name,
        "phone": phone,
        "email": email or "",
        "address": address or "",
        "business_type": business_type or "Local Business"
    }
    
    print(f"\nRunning SDR workflow for: {name}")
    print("This will take several minutes...")
    
    try:
        results = execute_sdr_main_workflow(business_data)
        
        print("\n" + "=" * 70)
        print("SDR WORKFLOW RESULTS")
        print("=" * 70)
        
        if results.get("status") == "completed":
            print(f"✅ Status: {results['status']}")
            print(f"\n📊 Research Result:")
            print(results.get('research_result', 'N/A'))
            print(f"\n📝 Proposal:")
            print(results.get('proposal', 'N/A'))
            print(f"\n📞 Call Result:")
            call_result = results.get('call_result', '{}')
            print(call_result)
            print(f"\n🤖 Classification:")
            print(results.get('classification', 'N/A'))
        else:
            print(f"❌ Status: {results.get('status', 'unknown')}")
            print(f"Error: {results.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error running SDR workflow: {str(e)}")


def run_calling_test():
    """Test the phone calling agent only."""
    print("\nPhone Calling Agent Test")
    print("-" * 30)
    print("This will test only the phone calling functionality")
    
    # Get test data
    print("\nEnter test information:")
    phone = input("Phone number to call: ").strip()
    name = input("Business name (optional): ").strip() or "Test Business"
    
    if not phone:
        print("Phone number is required.")
        return
    
    business_data = {
        "name": name,
        "phone": phone,
        "address": "Test Address"
    }
    
    proposal = """
    Hello! This is a test call from ZemZen Web Solutions. We're testing our 
    AI calling system to help businesses get professional websites. This is 
    just a quick test to verify our system is working correctly. Thank you 
    for your time!
    """
    
    print(f"\nCalling: {phone}")
    print("This will make a real phone call...")
    
    try:
        result = phone_call_tool._run(business_data, proposal)
        
        print("\n" + "=" * 50)
        print("CALL RESULT")
        print("=" * 50)
        print(f"Status: {result.get('status')}")
        print(f"Conversation ID: {result.get('conversation_id')}")
        
        if result.get('transcript'):
            print(f"\nTranscript ({len(result.get('transcript', []))} messages):")
            print("-" * 40)
            for i, msg in enumerate(result.get('transcript', []), 1):
                role = msg.get('role', 'unknown').upper()
                message = msg.get('message', '')
                print(f"{i}. [{role}] {message}")
        
        if result.get('error'):
            print(f"\nError: {result.get('error')}")
            
        print(f"\n📁 Debug file created: phone_call_debug_detailed.json")
            
    except Exception as e:
        print(f"Error during call: {str(e)}")


def run_system_tests():
    """Run system tests."""
    print("\nSystem Tests")
    print("-" * 30)
    
    try:
        # Import and run the test configuration
        from test_configuration import test_configuration
        
        success = test_configuration()
        
        if success:
            print("\nAll system tests passed!")
        else:
            print("\nSome tests failed. Check the output above.")
            
    except ImportError:
        print("Test configuration module not found.")
        print("Make sure test_configuration.py exists in the project root.")
    except Exception as e:
        print(f"Error running tests: {str(e)}")


if __name__ == "__main__":
    main()
