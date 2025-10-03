"""
Demo script for Agentic Sales Agent Lead Finder.
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv('env.txt')

from leads_finder.clients.map_search_service import search_leads, analyze_leads


def main():
    """Main demo function."""
    print("Agentic Sales Agent - Lead Finder Demo")
    print("=" * 50)
    print("AI-powered lead generation with multiple LLM providers")
    print("=" * 50)
    
    # Check if required API keys are set
    required_keys = ["FOURSQUARE_API_KEY", "OPENAI_API_KEY"]
    missing_keys = [key for key in required_keys if not os.getenv(key) or os.getenv(key) == f"your_{key.lower()}_here"]
    
    if missing_keys:
        print(f"Missing required API keys: {', '.join(missing_keys)}")
        print("Please update your env.txt file with valid API keys.")
        return
    
    print("API keys configured successfully!")
    
    # Using Cerebras LLM by default
    
    # Demo parameters
    demo_queries = [
        ("restaurants", "New York"),
        ("coffee shops", "San Francisco"),
        ("hotels", "Chicago"),
        ("gyms", "Ahmedabad"),
        ("pharmacies", "Bangalore")
    ]
    
    print("\nAvailable demo searches:")
    for i, (query, location) in enumerate(demo_queries, 1):
        print(f"{i}. {query} in {location}")
    
    # Interactive demo
    while True:
        try:
            print("\n" + "=" * 50)
            choice = input("Select a demo (1-5) or 'q' to quit: ").strip()
            
            if choice.lower() == 'q':
                print("👋 Goodbye!")
                break
            
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(demo_queries):
                query, location = demo_queries[choice_idx]
                
                print(f"\nSearching for {query} in {location}...")
                print("This may take a few moments...")
                
                try:
                    # Execute the lead search
                    result = search_leads(query, location, radius=2000, limit=10, use_cost_effective=False)
                    
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
            
            else:
                print("Invalid choice. Please select 1-5 or 'q' to quit.")
        
        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Unexpected error: {str(e)}")


def quick_demo():
    """Quick demo without user interaction."""
    print("Quick Agentic Sales Agent Demo")
    print("=" * 40)
    
    # Check API keys
    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your_openai_api_key_here":
        print("Please set OPENAI_API_KEY in env.txt")
        return
    
    if not os.getenv("FOURSQUARE_API_KEY"):
        print("Please set FOURSQUARE_API_KEY in env.txt")
        return
    
    # Run a quick search using Cerebras LLM (default)
    print("Searching for restaurants in New York...")
    try:
        result = search_leads("restaurants", "New York", radius=1000, limit=5, use_cost_effective=False)
        print("\nRESULTS:")
        print(result)
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_demo()
    else:
        main()
