"""
MongoDB Connection and Database Management for Lead Finder.
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
from dotenv import load_dotenv

load_dotenv()


class MongoDBClient:
    """
    MongoDB client wrapper with connection management and business leads operations.
    
    Follows singleton pattern for efficient connection reuse.
    """
    
    _instance: Optional['MongoDBClient'] = None
    _client: Optional[MongoClient] = None
    _database: Optional[Database] = None
    
    # Collection names
    BUSINESS_LEADS_COLLECTION = "business_leads"
    LEAD_SESSIONS_COLLECTION = "lead_sessions"
    
    def __new__(cls) -> 'MongoDBClient':
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize MongoDB connection."""
        if self._client is None:
            self._connect()
    
    def _connect(self) -> None:
        """
        Establish MongoDB connection using environment variables.
        
        Environment Variables:
            MONGODB_URI: Full MongoDB connection string
            MONGODB_DATABASE_NAME: Database name (default: sales_leads_db)
            
        Fallback to local MongoDB if no URI provided.
        """
        # Get connection details from environment
        mongodb_uri = os.getenv("MONGODB_URI")
        database_name = os.getenv("MONGODB_DATABASE_NAME", "sales_leads_db")
        
        # Default local connection if no URI provided
        if not mongodb_uri:
            mongodb_uri = "mongodb://localhost:27017"
            print("⚠️  No MONGODB_URI found, using local MongoDB: mongodb://localhost:27017")
        
        try:
            # Create MongoDB client with timeout settings
            self._client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=20000,        # 20 second connection timeout
                socketTimeoutMS=20000           # 20 second socket timeout
            )
            
            # Test connection
            self._client.admin.command('ping')
            
            # Set database
            self._database = self._client[database_name]
            
            print(f"✅ Connected to MongoDB database: {database_name}")
            
            # Initialize collections and indexes
            self._initialize_collections()
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            raise ConnectionFailure(f"Failed to connect to MongoDB: {e}")
    
    def _initialize_collections(self) -> None:
        """Initialize collections with proper indexes."""
        # Business leads collection with indexes
        business_collection = self._database[self.BUSINESS_LEADS_COLLECTION]
        
        # Indexes for efficient querying
        business_collection.create_index([("business_id", ASCENDING)], unique=True)
        business_collection.create_index([("name", ASCENDING)])
        business_collection.create_index([("city", ASCENDING)])
        business_collection.create_index([("source", ASCENDING)])
        business_collection.create_index([("created_at", ASCENDING)])
        
        # Lead sessions collection for tracking search sessions
        sessions_collection = self._database[self.LEAD_SESSIONS_COLLECTION]
        sessions_collection.create_index([("session_id", ASCENDING)], unique=True)
        sessions_collection.create_index([("created_at", ASCENDING)])
    
    @property
    def database(self) -> Database:
        """Get the MongoDB database instance."""
        if self._database is None:
            raise ConnectionFailure("Database not connected. Call connect() first.")
        return self._database
    
    @property
    def business_leads_collection(self) -> Collection:
        """Get the business leads collection."""
        return self.database[self.BUSINESS_LEADS_COLLECTION]
    
    @property
    def sessions_collection(self) -> Collection:
        """Get the lead sessions collection."""
        return self.database[self.LEAD_SESSIONS_COLLECTION]
    
    def ping(self) -> bool:
        """Test MongoDB connection."""
        try:
            self._client.admin.command('ping')
            return True
        except:
            return False
    
    def close(self) -> None:
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            print("🔌 MongoDB connection closed")
    
    def __del__(self):
        """Ensure connections are closed on cleanup."""
        self.close()


# Convenience functions for accessing MongoDB
def get_mongodb_client() -> MongoDBClient:
    """Get the singleton MongoDB client instance."""
    return MongoDBClient()


def get_business_leads_collection() -> Collection:
    """Get the business leads collection directly."""
    client = get_mongodb_client()
    return client.business_leads_collection


def get_sessions_collection() -> Collection:
    """Get the sessions collection directly."""
    client = get_mongodb_client()
    return client.sessions_collection


# Configuration validator
def validate_mongodb_config() -> Dict[str, Any]:
    """
    Validate MongoDB configuration and return status.
    
    Returns:
        Dict containing configuration status and details
    """
    status = {
        "connected": False,
        "database_name": None,
        "uri_provided": False,
        "local_fallback": False,
        "collections_ready": False,
        "error": None
    }
    
    try:
        # Check environment variables
        mongodb_uri = os.getenv("MONGODB_URI")
        database_name = os.getenv("MONGODB_DATABASE_NAME", "sales_leads_db")
        
        status["database_name"] = database_name
        status["uri_provided"] = bool(mongodb_uri)
        
        if not mongodb_uri:
            status["local_fallback"] = True
        
        # Test connection
        client = get_mongodb_client()
        status["connected"] = client.ping()
        
        # Check collections exist
        status["collections_ready"] = (
            MongoDBClient.BUSINESS_LEADS_COLLECTION in client.database.list_collection_names()
        )
        
    except Exception as e:
        status["error"] = str(e)
    
    return status


if __name__ == "__main__":
    # Test MongoDB connection
    print("🔍 Testing MongoDB Connection...")
    
    try:
        client = get_mongodb_client()
        status = validate_mongodb_config()
        
        print("📊 MongoDB Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        # Test collection access
        collection = get_business_leads_collection()
        doc_count = collection.count_documents({})
        print(f"📄 Current business leads count: {doc_count}")
        
        print("✅ MongoDB setup successful!")
        
    except Exception as e:
        print(f"❌ MongoDB setup failed: {e}")
