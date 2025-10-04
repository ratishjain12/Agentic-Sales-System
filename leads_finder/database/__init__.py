"""
Database module for Lead Finder system.
"""

from .mongodb_client import (
    MongoDBClient,
    get_mongodb_client,
    get_business_leads_collection,
    get_sessions_collection,
    validate_mongodb_config
)

__all__ = [
    "MongoDBClient",
    "get_mongodb_client", 
    "get_business_leads_collection",
    "get_sessions_collection",
    "validate_mongodb_config"
]


