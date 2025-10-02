"""
Foursquare API Configuration
Get your API key from: https://foursquare.com/developers/orgs/68de853467bf093d3e59bafa/projects/68de853567bf093d3e59bb08/settings

Environment Variables Required:
- FOURSQUARE_API_KEY: Your Foursquare Places API key

Optional Environment Variables:
- FOURSQUARE_DEFAULT_RADIUS: Default search radius in meters (default: 1000)
- FOURSQUARE_DEFAULT_LIMIT: Default number of results (default: 20)
- FOURSQUARE_RATE_LIMIT_REQUESTS_PER_MINUTE: Rate limit for requests per minute (default: 60)
- FOURSQUARE_RATE_LIMIT_REQUESTS_PER_DAY: Rate limit for requests per day (default: 1000)

Free Tier Limits:
- 1,000 requests per day
- 60 requests per minute
- Basic place information
- Search radius up to 100km
- Up to 50 results per search
"""

import os
from typing import Optional


class FoursquareConfig:
    """Configuration class for Foursquare API settings."""
    
    def __init__(self):
        self.api_key = os.getenv("FOURSQUARE_API_KEY")
        self.default_radius = int(os.getenv("FOURSQUARE_DEFAULT_RADIUS", "1000"))
        self.default_limit = int(os.getenv("FOURSQUARE_DEFAULT_LIMIT", "20"))
        self.rate_limit_per_minute = int(os.getenv("FOURSQUARE_RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))
        self.rate_limit_per_day = int(os.getenv("FOURSQUARE_RATE_LIMIT_REQUESTS_PER_DAY", "1000"))
    
    def validate(self) -> bool:
        """Validate that required configuration is present."""
        if not self.api_key:
            raise ValueError(
                "FOURSQUARE_API_KEY environment variable is required. "
                "Get your API key from: https://foursquare.com/developers/orgs/68de853467bf093d3e59bafa/projects/68de853567bf093d3e59bb08/settings"
            )
        return True


# Global configuration instance
config = FoursquareConfig()
