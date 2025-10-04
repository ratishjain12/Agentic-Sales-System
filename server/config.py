"""
Server Configuration
"""
import os
from typing import List

class Settings:
    """Server settings and configuration"""
    
    # API Settings
    API_TITLE = "Sales Agent API"
    API_VERSION = "1.0.0"
    API_DESCRIPTION = "REST API for Sales Development Representative Agent System"
    
    # Server Settings
    HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    PORT = int(os.getenv("SERVER_PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS Settings
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
    
    # Agent Settings
    MAX_WORKFLOW_RETRIES = int(os.getenv("MAX_WORKFLOW_RETRIES", "3"))
    WORKFLOW_TIMEOUT = int(os.getenv("WORKFLOW_TIMEOUT", "300"))  # seconds
    
    # Email Settings
    EMAIL_RATE_LIMIT = int(os.getenv("EMAIL_RATE_LIMIT", "10"))  # emails per minute
    EMAIL_BATCH_SIZE = int(os.getenv("EMAIL_BATCH_SIZE", "5"))
    
    # Database Settings
    MONGODB_URI = os.getenv("MONGODB_URI")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE_NAME", "sales_leads_db")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/server.log")

settings = Settings()
