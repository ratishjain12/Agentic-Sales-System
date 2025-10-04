"""
Configuration for Lead Manager Agent.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LeadManagerConfig:
    """Configuration class for Lead Manager."""
    
    # MongoDB Configuration
    MONGODB_URI = os.getenv("MONGODB_URI")
    MONGODB_DATABASE_NAME = os.getenv("LEAD_MANAGER_DATABASE_NAME", "leads_manager_db")
    
    # Gmail Configuration
    GMAIL_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE")
    SALES_EMAIL = os.getenv("SALES_EMAIL", "sales@zemzen.org")
    
    # Google Calendar Configuration
    CALENDAR_ID = os.getenv("CALENDAR_ID", "primary")
    BUSINESS_HOURS_START = int(os.getenv("BUSINESS_HOURS_START", "9"))
    BUSINESS_HOURS_END = int(os.getenv("BUSINESS_HOURS_END", "18"))
    MEETING_DURATION = int(os.getenv("MEETING_DURATION", "60"))
    AVAILABILITY_DAYS = int(os.getenv("AVAILABILITY_DAYS", "7"))
    
    # Cerebras LLM Configuration
    CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
    CEREBRAS_BASE_URL = os.getenv("CEREBRAS_BASE_URL")
    DEFAULT_MODEL = "cerebras/llama3.1-8b"
    
    # UI Notifications
    UI_CLIENT_SERVICE_URL = os.getenv("UI_CLIENT_SERVICE_URL", "http://localhost:8000")
    
    # Hot Lead Detection Configuration (Content-based)
    HOT_LEAD_KEYWORDS = [
        "interested", "partnership", "collaboration", "services", "discuss",
        "meeting", "demo", "consultation", "opportunity", "proposal",
        "quotation", "pricing", "solution", "implementation", "project",
        "contract", "business", "company", "help", "support", "assistance",
        "consulting", "development", "design", "marketing", "sales"
    ]
    
    HOT_LEAD_URGENCY_KEYWORDS = [
        "urgent", "asap", "immediately", "soon", "rapid", "quick",
        "priority", "important", "deadline", "timeline", "schedule"
    ]
    
    # Email Analysis Configuration
    MIN_CONFIDENCE_SCORE = 0.7
    HOT_LEAD_THRESHOLD = 0.6
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        required_vars = [
            "CEREBRAS_API_KEY",
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        return True