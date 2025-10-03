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
load_dotenv('env.txt')

from leads_finder.crew.lead_finder_crew import get_lead_finder_crew
from leads_finder.sub_agents.cluster_search_agent import run_cluster_search


def main():
    """Main entry point for the Agentic Sales Agent."""
    print("Agentic Sales Agent")
    print("=" * 50)
    print("AI-powered lead generation system")
    print("=" * 50)
    
    # Check if required API keys are set
    required_keys = ["FOURSQUARE_API_KEY", "OPENAI_API_KEY", "CEREBRAS_API_KEY"]
    missing_keys = [key for key in required_keys if not os.getenv(key) or os.getenv(key) == f"your_{key.lower()}_here"]
    
    if missing_keys:
        print(f"Missing required API keys: {', '.join(missing_keys)}")
        print("Please update your env.txt file with valid API keys.")
        return
    
    print("API keys configured successfully!")
    
    # Interactive menu
    while True:
        print("\n" + "=" * 50)
        print("Select an option:")
        print("1. Search leads using Foursquare API")
        print("2. Search leads using Cluster Search (OSM)")
        print("3. Run comprehensive lead analysis")
        print("4. Run system tests")
        print("5. Exit")
        
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == '1':
                run_foursquare_search()
            elif choice == '2':
                run_cluster_search_demo()
            elif choice == '3':
                run_comprehensive_analysis()
            elif choice == '4':
                run_system_tests()
            elif choice == '5':
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please select 1-5.")
                
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
    
    # Get the lead finder crew
    crew = get_lead_finder_crew(use_cost_effective=True)
    
    print(f"\nSearching for {query} in {location}...")
    print("This may take a few moments...")
    
    try:
        result = crew.search_leads(query, location, radius=radius, limit=limit)
        
        print("\n" + "=" * 50)
        print("SEARCH RESULTS")
        print("=" * 50)
        print(result)
        
        # Ask if user wants to analyze the results
        analyze = input("\nWould you like to analyze these results? (y/n): ").strip().lower()
        if analyze == 'y':
            print("\nAnalyzing results...")
            analysis_result = crew.analyze_leads(str(result))
            
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
    
    # Get the lead finder crew
    crew = get_lead_finder_crew(use_cost_effective=False)  # Use Cerebras for analysis
    
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
            search_result = crew.search_leads(query, location, radius=2000, limit=10)
            
            print("\nAnalyzing search results...")
            analysis_result = crew.analyze_leads(str(search_result))
            
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
