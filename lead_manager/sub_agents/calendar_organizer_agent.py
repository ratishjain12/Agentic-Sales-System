"""
Calendar Organizer Agent for Lead Manager.
Schedules meetings with hot leads based on calendar availability.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from crewai import Agent, Task, Crew
from leads_finder.llm_config import get_crewai_llm
from lead_manager.prompts import CALENDAR_ORGANIZER_PROMPT
from lead_manager.tools.calendar_tools import (
    CheckAvailabilityTool,
    CreateMeetingTool,
    CalendarConflictTool
)

logger = logging.getLogger(__name__)


class CalendarOrganizerAgent:
    """Agent responsible for scheduling meetings with hot leads."""
    
    def __init__(self):
        self.check_availability_tool = CheckAvailabilityTool()
        self.create_meeting_tool = CreateMeetingTool()
        self.calendar_conflict_tool = CalendarConflictTool()
        self.logger = logging.getLogger(__name__)
    
    def create_agent(self):
        """Create the Calendar Organizer Agent."""
        return Agent(
            role="Calendar Organizer",
            goal="Schedule meetings with hot leads efficiently within business hours",
            backstory="""
            You are a professional calendar management specialist responsible for scheduling 
            meetings with qualified leads. You understand business etiquette, optimal meeting 
            times, and ensure all meetings are scheduled within appropriate business hours. 
            You create professional meeting invitations with Google Meet links and clear agendas.
            """,
            verbose=True,
            allow_delegation=False,
            tools=[
                self.check_availability_tool,
                self.create_meeting_tool,
                self.calendar_conflict_tool
            ],
            llm=get_crewai_llm(model="cerebras/llama3.1-8b", temperature=0.2),
        )
    
    def schedule_meeting(self, lead_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Schedule a meeting based on lead data and analysis results.
        
        Args:
            lead_data: Dictionary containing email and sender information
            analysis_result: Analysis results from Email Analyzer
            
        Returns:
            Meeting scheduling results
        """
        try:
            sender_email = lead_data.get("sender_email", "")
            sender_name = lead_data.get("sender_name", "")
            subject = lead_data.get("subject", "")
            body = lead_data.get("body", "")
            
            self.logger.info(f"Scheduling meeting for hot lead: {sender_email}")
            
            # Check calendar availability
            availability_result = self.check_availability_tool._run(days_ahead=7)
            
            if not availability_result.get("success", False) or not availability_result.get("available_slots"):
                return {
                    "success": False,
                    "error": "No available meeting slots found",
                    "meeting_scheduled": False
                }
            
            # Get optimal meeting time
            optimal_slot = self._select_optimal_meeting_time(
                availability_result["available_slots"],
                analysis_result
            )
            
            if not optimal_slot:
                return {
                    "success": False,
                    "error": "Could not determine optimal meeting time",
                    "meeting_scheduled": False
                }
            
            # Create meeting title
            meeting_title = self._generate_meeting_title(sender_name, subject, body)
            
            # Create the meeting
            meeting_result = self.create_meeting_tool._run(
                title=meeting_title,
                attendee_email=sender_email,
                start_datetime=optimal_slot["start_datetime"],
                duration_minutes=60
            )
            
            if meeting_result.get("success", False):
                # Send UI notification about scheduled meeting
                self._send_meeting_notification(lead_data, meeting_result)
                
                return {
                    "success": True,
                    "meeting_scheduled": True,
                    "meeting_data": meeting_result.get("meeting_data", {}),
                    "meeting_id": meeting_result.get("meeting_id", ""),
                    "availability_checked": availability_result["total_slots"]
                }
            else:
                return {
                    "success": False,
                    "error": meeting_result.get("error", "Meeting creation failed"),
                    "meeting_scheduled": False
                }
                
        except Exception as e:
            self.logger.error(f"Error scheduling meeting: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "meeting_scheduled": False
            }
    
    def _select_optimal_meeting_time(self, available_slots: List[Dict], analysis_result: Dict) -> Optional[Dict]:
        """Select the optimal meeting time based on analysis and availability."""
        try:
            if not available_slots:
                return None
            
            # Prefer slots for the next business days
            urgency = analysis_result.get("meeting_request_analysis", {}).get("urgency", "normal")
            
            # Sort slots by date (earlier first for urgent requests, later first for normal)
            sorted_slots = sorted(
                available_slots, 
                key=lambda x: datetime.fromisoformat(x["start_datetime"]),
                reverse=(urgency != "urgent")
            )
            
            # Select the first suitable slot
            optimal_slot = sorted_slots[0]
            
            self.logger.info(f"Selected optimal meeting time: {optimal_slot['start_datetime']}")
            return optimal_slot
            
        except Exception as e:
            self.logger.error(f"Error selecting optimal meeting time: {str(e)}")
            return available_slots[0] if available_slots else None
    
    def _generate_meeting_title(self, sender_name: str, subject: str, body: str) -> str:
        """Generate an appropriate meeting title."""
        try:
            # Extract company or name from sender
            name_or_company = sender_name
            
            # Create title based on subject content
            if any(keyword in subject.lower() for keyword in ["meeting", "call", "demo"]):
                return f"Business Discussion - {name_or_company}"
            elif any(keyword in subject.lower() for keyword in ["partnership", "collaboration"]):
                return f"Partnership Discussion - {name_or_company}"
            elif any(keyword in subject.lower() for keyword in ["service", "consultation"]):
                return f"Services Consultation - {name_or_company}"
            else:
                return f"Sales Meeting - {name_or_company}"
                
        except Exception as e:
            self.logger.warning(f"Error generating meeting title: {str(e)}")
            return f"Sales Meeting - {sender_name}"
    
    def _send_meeting_notification(self, lead_data: Dict[str, Any], meeting_result: Dict[str, Any]) -> None:
        """Send UI notification about scheduled meeting."""
        try:
            import requests
            import os
            from datetime import datetime
            
            ui_url = os.getenv("UI_CLIENT_SERVICE_URL", "http://localhost:8000")
            meeting_data = meeting_result.get("meeting_data", {})
            
            notification_data = {
                "agent_type": "calendar",
                "business_id": f"meeting_{meeting_result.get('meeting_id', 'unknown')}",
                "status": "meeting_scheduled",
                "message": f"Meeting scheduled with {lead_data.get('sender_name', 'Lead')}",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "meeting_id": meeting_result.get("meeting_id", ""),
                    "title": meeting_data.get("title", ""),
                    "start_datetime": meeting_data.get("start_datetime", ""),
                    "end_datetime": meeting_data.get("end_datetime", ""),
                    "attendees": [
                        lead_data.get("sender_email", ""),
                        os.getenv("SALES_EMAIL", "sales@zemzen.org")
                    ],
                    "google_meet_link": meeting_data.get("google_meet_link", ""),
                    "description": meeting_data.get("description", ""),
                    "sender_email": lead_data.get("sender_email", ""),
                    "sender_name": lead_data.get("sender_name", "")
                }
            }
            
            # Send notification (for now, just log it)
            self.logger.info(f"📅 MEETING SCHEDULED NOTIFICATION: {notification_data}")
            
            # In production, this would make an HTTP request:
            # requests.post(f"{ui_url}/notifications", json=notification_data)
            
        except Exception as e:
            self.logger.error(f"Error sending meeting notification: {str(e)}")


def run_calendar_organizer(lead_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """Run calendar organizer agent."""
    agent = CalendarOrganizerAgent()
    return agent.schedule_meeting(lead_data, analysis_result)