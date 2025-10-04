"""
MongoDB Upload Tool for Lead Finder Merger Agent.
"""

import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from crewai.tools import BaseTool
from pydantic import Field, BaseModel
from leads_finder.database import get_business_leads_collection, get_sessions_collection


class BusinessLead(BaseModel):
    """Business lead data model for validation."""
    name: str
    address: str
    phone: Optional[str] = None
    website: Optional[str] = None
    category: Optional[str] = None
    rating: Optional[float] = None
    source: str  # "map_search" or "cluster_search"
    business_id: Optional[str] = None  # For deduplication


class MongoDBUploadTool(BaseTool):
    """
    MongoDB Upload Tool for uploading merged business leads.
    
    This tool processes business leads data, validates it, deduplicates entries,
    and uploads them to MongoDB with proper metadata.
    """
    
    name: str = "mongodb_upload_tool"
    description: str = """
    Upload merged business leads to MongoDB database.
    
    Input should be a JSON string containing an array of business objects.
    Each business should have: name, address, phone, website, category, rating, source.
    
    The tool will:
    1. Validate business data format
    2. Generate unique business IDs for deduplication
    3. Remove duplicate entries
    4. Upload to MongoDB with timestamps
    5. Return upload summary
    
    Example input:
    '[
        {
            "name": "Local Pizza Place",
            "address": "123 Main St, City, State",
            "phone": "555-123-4567",
            "website": null,
            "category": "Restaurant",
            "rating": 4.2,
            "source": "map_search"
        }
    ]'
    """
    
    def _run(self, business_data: str, session_id: Optional[str] = None) -> str:
        """
        Upload business leads to MongoDB.
        
        Args:
            business_data: JSON string containing array of business objects
            session_id: Optional session ID for tracking
            
        Returns:
            Upload summary as string
        """
        try:
            # Parse JSON input
            businesses = json.loads(business_data)
            
            if not isinstance(businesses, list):
                return "❌ Error: Input must be a JSON array of business objects"
            
            # Validate and process businesses
            processed_leads = []
            validation_errors = []
            
            for idx, business in enumerate(businesses):
                try:
                    # Validate business data
                    validated_business = self._validate_business(business, idx)
                    
                    # Generate business ID for deduplication
                    business_id = self._generate_business_id(validated_business)
                    validated_business.business_id = business_id
                    
                    # Convert to dict and add metadata
                    lead_doc = validated_business.model_dump()
                    lead_doc.update({
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc),
                        "session_id": session_id or str(uuid.uuid4()),
                        "lead_status": "new"
                    })
                    
                    processed_leads.append(lead_doc)
                    
                except Exception as e:
                    validation_errors.append(f"Business {idx}: {str(e)}")
            
            if validation_errors:
                return f"❌ Validation errors:\n" + "\n".join(validation_errors)
            
            # Deduplicate leads
            deduplicated_leads = self._deduplicate_leads(processed_leads)
            
            # Upload to MongoDB
            upload_result = self._upload_to_mongodb(deduplicated_leads)
            
            return upload_result
            
        except json.JSONDecodeError as e:
            return f"❌ JSON parsing error: {str(e)}"
        except Exception as e:
            return f"❌ Upload error: {str(e)}"
    
    def _validate_business(self, business: Dict[str, Any], index: int) -> BusinessLead:
        """Validate business data and return BusinessLead object."""
        required_fields = ["name", "address", "source"]
        
        for field in required_fields:
            if field not in business or not business[field]:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate source
        if business["source"] not in ["map_search", "cluster_search"]:
            raise ValueError(f"Invalid source: {business['source']}. Must be 'map_search' or 'cluster_search'")
        
        # Validate rating if provided
        if "rating" in business and business["rating"] is not None:
            try:
                rating = float(business["rating"])
                if not (0 <= rating <= 5):
                    raise ValueError("Rating must be between 0 and 5")
                business["rating"] = rating
            except (ValueError, TypeError):
                raise ValueError("Invalid rating format")
        
        return BusinessLead(**business)
    
    def _generate_business_id(self, business: BusinessLead) -> str:
        """Generate unique business ID for deduplication."""
        # Use name + address for deduplication
        identifier = f"{business.name.lower().strip()}_{business.address.lower().strip()}"
        
        # Create hash for uniqueness
        import hashlib
        return hashlib.md5(identifier.encode()).hexdigest()
    
    def _deduplicate_leads(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate leads based on business_id."""
        seen_ids = set()
        deduplicated = []
        
        for lead in leads:
            business_id = lead["business_id"]
            if business_id not in seen_ids:
                seen_ids.add(business_id)
                deduplicated.append(lead)
        
        return deduplicated
    
    def _upload_to_mongodb(self, leads: List[Dict[str, Any]]) -> str:
        """Upload leads to MongoDB with upsert logic."""
        if not leads:
            return "⚠️ No leads to upload"
        
        try:
            collection = get_business_leads_collection()
            
            # Use upsert to handle duplicates
            upsert_count = 0
            insert_count = 0
            
            for lead in leads:
                # Check if business already exists
                existing = collection.find_one({"business_id": lead["business_id"]})
                
                if existing:
                    # Update existing record
                    lead["updated_at"] = datetime.now(timezone.utc)
                    collection.update_one(
                        {"business_id": lead["business_id"]},
                        {"$set": lead}
                    )
                    upsert_count += 1
                else:
                    # Insert new record
                    collection.insert_one(lead)
                    insert_count += 1
            
            # Create session record
            if leads:
                session_id = leads[0]["session_id"]
                session_doc = {
                    "session_id": session_id,
                    "created_at": datetime.now(timezone.utc),
                    "leads_count": len(leads),
                    "insert_count": insert_count,
                    "upsert_count": upsert_count,
                    "status": "completed"
                }
                
                sessions_collection = get_sessions_collection()
                sessions_collection.update_one(
                    {"session_id": session_id},
                    {"$set": session_doc},
                    upsert=True
                )
            
            return f"""✅ Upload successful!
📊 Summary:
  • Total leads processed: {len(leads)}
  • New leads inserted: {insert_count}
  • Existing leads updated: {upsert_count}
  • Session ID: {session_id}
  • Database: sales_leads_db
  • Collection: business_leads"""
            
        except Exception as e:
            return f"❌ MongoDB upload failed: {str(e)}"


# Create tool instance for use in agents
mongodb_upload_tool_instance = MongoDBUploadTool()


def upload_business_leads(business_data: str, session_id: Optional[str] = None) -> str:
    """
    Convenience function for uploading business leads.
    
    Args:
        business_data: JSON string containing business leads
        session_id: Optional session ID
        
    Returns:
        Upload result summary
    """
    tool = MongoDBUploadTool()
    return tool._run(business_data, session_id)


if __name__ == "__main__":
    # Test the tool with sample data
    sample_data = '''[
        {
            "name": "Test Restaurant",
            "address": "123 Test St, Test City, TC 12345",
            "phone": "555-123-4567",
            "website": null,
            "category": "Restaurant",
            "rating": 4.2,
            "source": "map_search"
        },
        {
            "name": "Test Shop",
            "address": "456 Test Ave, Test City, TC 12345",
            "phone": "555-987-6543",
            "website": "https://testshop.com",
            "category": "Retail",
            "rating": 3.8,
            "source": "cluster_search"
        }
    ]'''
    
    print("🧪 Testing MongoDB Upload Tool...")
    result = upload_business_leads(sample_data, "test_session_001")
    print(result)
