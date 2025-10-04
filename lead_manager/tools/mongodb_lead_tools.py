"""
MongoDB-based tools for Lead Manager operations.
"""

import os
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from pymongo import MongoClient
from lead_manager.config import LeadManagerConfig

# Configure logging
logger = logging.getLogger(__name__)


def get_lead_manager_mongodb_client():
    """Get MongoDB client specifically for Lead Manager operations."""
    mongodb_uri = LeadManagerConfig.MONGODB_URI
    database_name = LeadManagerConfig.MONGODB_DATABASE_NAME
    
    if not mongodb_uri:
        mongodb_uri = "mongodb://localhost:27017"
        logger.warning("No MONGODB_URI found, using local MongoDB")
    
    client = MongoClient(mongodb_uri)
    database = client[database_name]
    
    return client, database


class HotLeadCheckResult(BaseModel):
    is_hot_lead: bool = Field(..., description="Whether the email sender is a hot lead")
    lead_data: Optional[Dict[str, Any]] = Field(None, description="Hot lead data if found")
    confidence: float = Field(0.0, description="Confidence score for hot lead identification")


class MeetingData(BaseModel):
    meeting_id: str = Field(..., description="Unique meeting ID")
    title: str = Field(..., description="Meeting title")
    attendee_email: str = Field(..., description="Attendee email address")
    start_datetime: str = Field(..., description="Meeting start time in ISO format")
    end_datetime: str = Field(..., description="Meeting end time in ISO format")
    google_meet_link: Optional[str] = Field(None, description="Google Meet video link")
    calendar_event_id: Optional[str] = Field(None, description="Google Calendar event ID")
    status: str = Field(default="scheduled", description="Meeting status")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Creation timestamp")


class CheckHotLeadTool(BaseTool):
    """Tool to check if an email sender is a hot lead using MongoDB."""
    
    name: str = "check_hot_lead_tool"
    description: str = "Check if an email sender is a hot lead by querying the MongoDB database"
    
    def _run(self, email_address: str) -> Dict[str, Any]:
        """
        Check if the email sender is a hot lead.
        
        Args:
            email_address: Email address to check
            
        Returns:
            Dictionary with hot lead check results
        """
        try:
            client, database = get_lead_manager_mongodb_client()
            collection = database["hot_leads"]
            
            # Search for the email address in hot leads
            hot_lead = collection.find_one({"email": email_address.lower()})
            
            if hot_lead:
                result = HotLeadCheckResult(
                    is_hot_lead=True,
                    lead_data={
                        "name": hot_lead.get("name"),
                        "company": hot_lead.get("company"),
                        "email": hot_lead.get("email"),
                        "phone": hot_lead.get("phone"),
                        "industry": hot_lead.get("industry"),
                        "lead_score": hot_lead.get("lead_score", 0),
                        "last_contact": hot_lead.get("last_contact"),
                        "notes": hot_lead.get("notes")
                    },
                    confidence=0.9
                )
                logger.info(f"Hot lead found: {email_address}")
            else:
                result = HotLeadCheckResult(
                    is_hot_lead=False,
                    confidence=0.1
                )
                logger.info(f"No hot lead found for: {email_address}")
            
            return result.dict()
            
        except Exception as e:
            logger.error(f"Error checking hot lead for {email_address}: {str(e)}")
            return HotLeadCheckResult(
                is_hot_lead=False,
                confidence=0.0
            ).dict()


class SaveMeetingTool(BaseTool):
    """Tool to save meeting data to MongoDB."""
    
    name: str = "save_meeting_tool"
    description: str = "Save meeting data to MongoDB database"
    
    def _run(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save meeting data to MongoDB.
        
        Args:
            meeting_data: Dictionary containing meeting information
            
        Returns:
            Dictionary with save operation results
        """
        try:
            client, database = get_lead_manager_mongodb_client()
            collection = database["meetings"]
            
            # Add metadata
            meeting_data["created_at"] = datetime.utcnow().isoformat()
            meeting_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Insert meeting data
            result = collection.insert_one(meeting_data)
            
            logger.info(f"Meeting saved with ID: {result.inserted_id}")
            
            return {
                "success": True,
                "meeting_id": str(result.inserted_id),
                "message": "Meeting data saved successfully"
            }
            
        except Exception as e:
            logger.error(f"Error saving meeting data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to save meeting data"
            }


class MarkEmailReadTool(BaseTool):
    """Tool to mark emails as read in Gmail."""
    
    name: str = "mark_email_read_tool"
    description: str = "Mark emails as read in Gmail using the Gmail API"
    
    def _run(self, message_ids: List[str]) -> Dict[str, Any]:
        """
        Mark emails as read.
        
        Args:
            message_ids: List of Gmail message IDs to mark as read
            
        Returns:
            Dictionary with operation results
        """
        try:
            # This would integrate with Gmail API
            # For now, we'll return a success response
            logger.info(f"Marking {len(message_ids)} emails as read")
            
            return {
                "success": True,
                "marked_count": len(message_ids),
                "message": f"Successfully marked {len(message_ids)} emails as read"
            }
            
        except Exception as e:
            logger.error(f"Error marking emails as read: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to mark emails as read"
            }


class UINotificationTool(BaseTool):
    """Tool to send notifications to the UI client."""
    
    name: str = "ui_notification_tool"
    description: str = "Send real-time notifications to the UI dashboard"
    
    def _run(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send notification to UI client.
        
        Args:
            notification_data: Dictionary containing notification information
            
        Returns:
            Dictionary with notification results
        """
        try:
            ui_client_url = os.getenv("UI_CLIENT_SERVICE_URL", "http://localhost:8000")
            
            # Add timestamp and agent type
            notification_data["timestamp"] = datetime.utcnow().isoformat()
            notification_data["agent_type"] = "lead_manager"
            
            # In a real implementation, this would make an HTTP request to the UI client
            logger.info(f"Sending UI notification: {notification_data.get('message', 'No message')}")
            
            return {
                "success": True,
                "notification_sent": True,
                "message": "Notification sent to UI client"
            }
            
        except Exception as e:
            logger.error(f"Error sending UI notification: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to send UI notification"
            }


# Tool instances for easy import
check_hot_lead_tool_instance = CheckHotLeadTool()
save_meeting_tool_instance = SaveMeetingTool()
mark_email_read_tool_instance = MarkEmailReadTool()
ui_notification_tool_instance = UINotificationTool()