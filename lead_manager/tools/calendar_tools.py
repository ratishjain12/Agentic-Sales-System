"""
Calendar management tools for Lead Manager.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from lead_manager.config import LeadManagerConfig

logger = logging.getLogger(__name__)


class AvailabilitySlot(BaseModel):
    start_datetime: str = Field(..., description="Available slot start time in ISO format")
    end_datetime: str = Field(..., description="Available slot end time in ISO format")
    duration_minutes: int = Field(..., description="Duration of the slot in minutes")


class MeetingData(BaseModel):
    title: str = Field(..., description="Meeting title")
    attendee_email: str = Field(..., description="Attendee email address")
    start_datetime: str = Field(..., description="Meeting start time in ISO format")
    end_datetime: str = Field(..., description="Meeting end time in ISO format")
    description: str = Field(..., description="Meeting description")
    google_meet_link: Optional[str] = Field(None, description="Google Meet video link")


class CheckAvailabilityTool(BaseTool):
    """Tool to check Google Calendar availability for meetings."""
    
    name: str = "check_availability_tool"
    description: str = "Check Google Calendar availability for scheduling meetings within business hours"
    
    def _run(self, days_ahead: int = 7) -> Dict[str, Any]:
        """
        Check calendar availability for the next specified days.
        
        Args:
            days_ahead: Number of days ahead to check (default: 7)
            
        Returns:
            Dictionary with availability information
        """
        try:
            logger.info(f"Checking calendar availability for next {days_ahead} days")
            
            # For now, return mock availability data
            # In production, this would integrate with Google Calendar API
            availability_slots = self._generate_mock_availability(days_ahead)
            
            logger.info(f"Found {len(availability_slots)} available slots")
            
            return {
                "success": True,
                "available_slots": [slot.dict() for slot in availability_slots],
                "total_slots": len(availability_slots),
                "business_hours": f"{LeadManagerConfig.BUSINESS_HOURS_START}:00 - {LeadManagerConfig.BUSINESS_HOURS_END}:00",
                "days_checked": days_ahead
            }
            
        except Exception as e:
            logger.error(f"Error checking calendar availability: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "available_slots": [],
                "total_slots": 0
            }
    
    def _generate_mock_availability(self, days_ahead: int) -> List[AvailabilitySlot]:
        """Generate mock availability slots."""
        slots = []
        today = datetime.now()
        
        for day_offset in range(days_ahead):
            current_date = today + timedelta(days=day_offset)
            
            # Skip weekends (Saturday=5, Sunday=6)
            if current_date.weekday() in [5, 6]:
                continue
                
            # Business hours
            start_hour = LeadManagerConfig.BUSINESS_HOURS_START
            end_hour = LeadManagerConfig.BUSINESS_HOURS_END
            
            # Generate time slots every hour
            for hour in range(start_hour, end_hour):
                slot_start = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                slot_end = slot_start + timedelta(minutes=LeadManagerConfig.MEETING_DURATION)
                
                slots.append(AvailabilitySlot(
                    start_datetime=slot_start.isoformat(),
                    end_datetime=slot_end.isoformat(),
                    duration_minutes=LeadManagerConfig.MEETING_DURATION
                ))
        
        return slots


class CreateMeetingTool(BaseTool):
    """Tool to create Google Calendar meetings."""
    
    name: str = "create_meeting_tool"
    description: str = "Create Google Calendar meeting with Google Meet integration"
    
    def _run(self, title: str, attendee_email: str, start_datetime: str, duration_minutes: int = 60) -> Dict[str, Any]:
        """
        Create a Google Calendar meeting.
        
        Args:
            title: Meeting title
            attendee_email: Email of the attendee
            start_datetime: Start time in ISO format
            duration_minutes: Meeting duration in minutes
            
        Returns:
            Dictionary with meeting creation results
        """
        try:
            logger.info(f"Creating meeting: {title} with {attendee_email}")
            
            # Parse start datetime
            start_time = datetime.fromisoformat(start_datetime)
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            # Generate Google Meet link (mock)
            meet_link = f"https://meet.google.com/abc-defg-hij"
            
            # Create meeting description
            description = self._generate_meeting_description(title, attendee_email)
            
            # In production, this would create actual Google Calendar event
            meeting_data = MeetingData(
                title=title,
                attendee_email=attendee_email,
                start_datetime=start_datetime,
                end_datetime=end_time.isoformat(),
                description=description,
                google_meet_link=meet_link
            )
            
            logger.info(f"Meeting created successfully: {title}")
            
            return {
                "success": True,
                "meeting_id": f"meeting_{hash(title + attendee_email + start_datetime)}",
                "meeting_data": meeting_data.dict(),
                "invitation_sent": True
            }
            
        except Exception as e:
            logger.error(f"Error creating meeting: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "meeting_id": None
            }
    
    def _generate_meeting_description(self, title: str, attendee_email: str) -> str:
        """Generate professional meeting description."""
        return f"""
Meeting: {title}

📅 Attendees:
• {LeadManagerConfig.SALES_EMAIL}
• {attendee_email}

🎯 Agenda:
• Introduction and overview
• Discussion of requirements
• Q&A session
• Next steps

📞 Meeting Link: https://meet.google.com/abc-defg-hij

Looking forward to speaking with you!

Best regards,
Sales Team
        """.strip()


class CalendarConflictTool(BaseTool):
    """Tool to detect and resolve calendar conflicts."""
    
    name: str = "calendar_conflict_tool"
    description: str = "Detect and suggest resolution for calendar conflicts"
    
    def _run(self, proposed_datetime: str, duration_minutes: int = 60) -> Dict[str, Any]:
        """
        Check for calendar conflicts.
        
        Args:
            proposed_datetime: Proposed meeting start time
            duration_minutes: Meeting duration
            
        Returns:
            Dictionary with conflict resolution info
        """
        try:
            proposed_start = datetime.fromisoformat(proposed_datetime)
            proposed_end = proposed_start + timedelta(minutes=duration_minutes)
            
            # Simple conflict checking (business hours only)
            start_hour = proposed_start.hour
          
            conflicts = []
            
            # Check against business hours
            if start_hour < LeadManagerConfig.BUSINESS_HOURS_START:
                conflicts.append({
                    "type": "outside_business_hours",
                    "message": f"Meeting time is before business hours (before {LeadManagerConfig.BUSINESS_HOURS_START}:00)"
                })
            
            if proposed_end.hour > LeadManagerConfig.BUSINESS_HOURS_END:
                conflicts.append({
                    "type": "outside_business_hours", 
                    "message": f"Meeting extends beyond business hours (after {LeadManagerConfig.BUSINESS_HOURS_END}:00)"
                })
            
            # Check weekend conflicts
            if proposed_start.weekday() in [5, 6]:
                conflicts.append({
                    "type": "weekend_conflict",
                    "message": "Meeting is scheduled for weekend"
                })
            
            return {
                "has_conflicts": len(conflicts) > 0,
                "conflicts": conflicts,
                "recommended_action": self._get_conflict_resolution(conflicts)
            }
            
        except Exception as e:
            logger.error(f"Error checking calendar conflicts: {str(e)}")
            return {
                "has_conflicts": False,
                "conflicts": [],
                "error": str(e)
            }
    
    def _get_conflict_resolution(self, conflicts: List[Dict]) -> str:
        """Suggest conflict resolution."""
        if not conflicts:
            return "No conflicts detected"
        
        if any(c["type"] == "outside_business_hours" for c in conflicts):
            return "Suggest rescheduling within business hours (9:00 AM - 6:00 PM)"
        
        if any(c["type"] == "weekend_conflict" for c in conflicts):
            return "Suggest rescheduling to weekday"
        
        return "Manual review required"


# Tool instances for easy import
check_availability_tool_instance = CheckAvailabilityTool()
create_meeting_tool_instance = CreateMeetingTool()
calendar_conflict_tool_instance = CalendarConflictTool()