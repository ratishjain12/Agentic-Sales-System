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
import logging

logger = logging.getLogger(__name__)


class BusinessLead(BaseModel):
    """Business lead data model for validation."""
    name: str
    address: str
    phone: Optional[str] = None
    email: Optional[str] = None  # Add email field
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
    Each business should have: name, address, phone, email, website, category, rating, source.
    
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
            "email": "info@pizzapalace.com",
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
            logger.info(f"🔍 MongoDB upload tool called with session_id: {session_id}")
            logger.info(f"🔍 Business data length: {len(business_data)}")
            
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
                    
                    # Debug logging
                    logger.info(f"🔍 Storing lead with session_id: {lead_doc['session_id']}")
                    logger.info(f"🔍 Lead email: {lead_doc.get('email', 'None')}")
                    
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
        
        # Validate email if provided
        if "email" in business and business["email"] is not None:
            email = business["email"].strip()
            if email and not self._is_valid_email(email):
                raise ValueError(f"Invalid email format: {email}")
            business["email"] = email if email else None
        
        return BusinessLead(**business)
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format using basic regex."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
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
        """Upload leads to MongoDB with synchronous verification and proper error handling."""
        if not leads:
            return "⚠️ No leads to upload"
        
        try:
            collection = get_business_leads_collection()
            sessions_collection = get_sessions_collection()
            session_id = leads[0]["session_id"]
            
            logger.info(f"🚀 Starting MongoDB upload for session {session_id} with {len(leads)} leads")
            
            # First, mark session as "uploading" to prevent race conditions
            sessions_collection.update_one(
                {"session_id": session_id},
                {"$set": {
                    "session_id": session_id,
                    "status": "uploading",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "leads_count": len(leads)
                }},
                upsert=True
            )
            logger.info(f"📝 Marked session {session_id} as 'uploading'")
            
            # Upload leads with individual verification
            upsert_count = 0
            insert_count = 0
            failed_uploads = []
            
            for i, lead in enumerate(leads):
                try:
                    # Check if business already exists
                    existing = collection.find_one({"business_id": lead["business_id"]})
                    
                    if existing:
                        # Update existing record
                        lead["updated_at"] = datetime.now(timezone.utc)
                        result = collection.update_one(
                            {"business_id": lead["business_id"]},
                            {"$set": lead}
                        )
                        if result.modified_count > 0:
                            upsert_count += 1
                            logger.info(f"✅ Updated lead {i+1}/{len(leads)}: {lead.get('name', 'Unknown')}")
                        else:
                            logger.warning(f"⚠️ No changes made to lead {i+1}: {lead.get('name', 'Unknown')}")
                    else:
                        # Insert new record
                        result = collection.insert_one(lead)
                        if result.inserted_id:
                            insert_count += 1
                            logger.info(f"✅ Inserted lead {i+1}/{len(leads)}: {lead.get('name', 'Unknown')}")
                        else:
                            failed_uploads.append(f"Lead {i+1}: Insert failed")
                            
                except Exception as e:
                    error_msg = f"Lead {i+1} ({lead.get('name', 'Unknown')}): {str(e)}"
                    failed_uploads.append(error_msg)
                    logger.error(f"❌ Upload failed for {error_msg}")
            
            # Verify upload completion by checking actual data in database
            verification_count = collection.count_documents({"session_id": session_id})
            logger.info(f"🔍 Verification: Found {verification_count} leads in database for session {session_id}")
            
            # Only mark as completed if we have successful uploads
            if verification_count > 0:
                session_doc = {
                    "session_id": session_id,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "leads_count": len(leads),
                    "verified_count": verification_count,
                    "insert_count": insert_count,
                    "upsert_count": upsert_count,
                    "failed_count": len(failed_uploads),
                    "status": "completed"
                }
                
                sessions_collection.update_one(
                    {"session_id": session_id},
                    {"$set": session_doc},
                    upsert=True
                )
                logger.info(f"✅ Session {session_id} marked as 'completed' with {verification_count} verified leads")
                
                # Final verification
                final_session_record = sessions_collection.find_one({"session_id": session_id})
                if final_session_record and final_session_record.get("status") == "completed":
                    logger.info(f"🎉 Upload process completed successfully for session {session_id}")
                else:
                    logger.error(f"❌ Session status verification failed for {session_id}")
                
                # Prepare success message
                success_msg = f"""✅ Upload successful!
📊 Summary:
  • Total leads processed: {len(leads)}
  • Verified in database: {verification_count}
  • New leads inserted: {insert_count}
  • Existing leads updated: {upsert_count}
  • Failed uploads: {len(failed_uploads)}
  • Session ID: {session_id}
  • Database: sales_leads_db
  • Collection: business_leads"""
                
                if failed_uploads:
                    success_msg += f"\n⚠️ Failed uploads:\n" + "\n".join(f"  • {fail}" for fail in failed_uploads)
                
                return success_msg
            else:
                # No leads were successfully uploaded
                sessions_collection.update_one(
                    {"session_id": session_id},
                    {"$set": {
                        "status": "failed",
                        "updated_at": datetime.now(timezone.utc),
                        "error": "No leads verified in database"
                    }},
                    upsert=True
                )
                logger.error(f"❌ Upload failed: No leads verified in database for session {session_id}")
                return f"❌ Upload failed: No leads were successfully stored in database"
            
        except Exception as e:
            # Mark session as failed
            try:
                sessions_collection = get_sessions_collection()
                sessions_collection.update_one(
                    {"session_id": session_id},
                    {"$set": {
                        "status": "failed",
                        "updated_at": datetime.now(timezone.utc),
                        "error": str(e)
                    }},
                    upsert=True
                )
            except:
                pass  # Don't fail on session update failure
            
            logger.error(f"❌ MongoDB upload failed: {str(e)}")
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
            "email": "info@testrestaurant.com",
            "website": null,
            "category": "Restaurant",
            "rating": 4.2,
            "source": "map_search"
        },
        {
            "name": "Test Shop",
            "address": "456 Test Ave, Test City, TC 12345",
            "phone": "555-987-6543",
            "email": "contact@testshop.com",
            "website": "https://testshop.com",
            "category": "Retail",
            "rating": 3.8,
            "source": "cluster_search"
        }
    ]'''
    
    print("🧪 Testing MongoDB Upload Tool...")
    result = upload_business_leads(sample_data, "test_session_001")
    print(result)
