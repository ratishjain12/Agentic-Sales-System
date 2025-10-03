"""
Exa Search Tool - AI-powered web search for business research.
"""
import os
from typing import Optional
from exa_py import Exa
from crewai.tools import BaseTool
from pydantic import Field


class ExaSearchTool(BaseTool):
    """
    Exa Search Tool for researching businesses, reviews, competitors, and online presence.

    Exa is an AI-powered search engine optimized for LLM applications.
    It provides semantic search capabilities and returns clean, structured data.
    """

    name: str = "exa_search"
    description: str = """Search the web for comprehensive business information including:
    - Business services, products, and offerings
    - Customer reviews and feedback (Google, Yelp, Facebook)
    - Online presence and social media
    - Competitor analysis
    - Market position and opportunities

    Use this tool to gather insights about businesses for sales research.
    Input should be a clear search query like 'Business Name reviews' or 'cafes in City with websites'."""

    api_key: Optional[str] = Field(default=None, exclude=True)
    num_results: int = Field(default=5, description="Number of search results to return")

    def __init__(self, api_key: Optional[str] = None, num_results: int = 5, **kwargs):
        """
        Initialize Exa Search Tool.

        Args:
            api_key: Exa API key (defaults to EXA_API_KEY env var)
            num_results: Number of results to return per search
        """
        super().__init__(**kwargs)
        self.api_key = api_key or os.getenv("EXA_API_KEY")
        self.num_results = num_results

        if not self.api_key:
            raise ValueError(
                "EXA_API_KEY not found. Please set it in your .env file or pass it as an argument."
            )

    def _run(self, query: str) -> str:
        """
        Execute a search query using Exa.

        Args:
            query: Search query string

        Returns:
            Formatted search results as string
        """
        try:
            # Initialize Exa client
            exa = Exa(api_key=self.api_key)

            # Perform search with content extraction
            results = exa.search_and_contents(
                query,
                num_results=self.num_results,
                text=True,  # Extract text content
                highlights=True  # Get relevant highlights
            )

            # Format results
            formatted_results = []
            formatted_results.append(f"Search Results for: '{query}'\n")
            formatted_results.append("=" * 80)

            for idx, result in enumerate(results.results, 1):
                formatted_results.append(f"\n{idx}. {result.title}")
                formatted_results.append(f"   URL: {result.url}")

                # Add highlights if available
                if hasattr(result, 'highlights') and result.highlights:
                    formatted_results.append(f"   Key Points:")
                    for highlight in result.highlights[:3]:  # Top 3 highlights
                        formatted_results.append(f"   - {highlight}")

                # Add text excerpt
                if hasattr(result, 'text') and result.text:
                    excerpt = result.text[:300] + "..." if len(result.text) > 300 else result.text
                    formatted_results.append(f"   Excerpt: {excerpt}")

                formatted_results.append("")

            return "\n".join(formatted_results)

        except Exception as e:
            return f"Error performing search: {str(e)}\nPlease check your EXA_API_KEY and query."


def create_exa_search_tool(api_key: Optional[str] = None, num_results: int = 5) -> ExaSearchTool:
    """
    Factory function to create an Exa Search Tool.

    Args:
        api_key: Exa API key (defaults to EXA_API_KEY env var)
        num_results: Number of results to return per search

    Returns:
        ExaSearchTool instance
    """
    return ExaSearchTool(api_key=api_key, num_results=num_results)


# Create singleton instance for easy import
exa_search_tool = create_exa_search_tool()
