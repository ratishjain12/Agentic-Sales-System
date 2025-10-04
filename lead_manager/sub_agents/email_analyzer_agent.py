"""
Email Analyzer Agent for Lead Manager.
Analyzes emails to identify hot leads and meeting requests using AI.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from crewai import Agent, Task, Crew
from leads_finder.llm_config import get_crewai_llm
from lead_manager.prompts import EMAIL_ANALYZER_PROMPT
from lead_manager.tools.meeting_analysis_tool import (
    MeetingAnalysisTool, 
    HotLeadAnalysisTool
)

logger = logging.getLogger(__name__)


class EmailAnalyzerAgent:
    """Agent responsible for analyzing emails for hot leads and meeting requests."""
    
    def __init__(self):
        self.meeting_analysis_tool = MeetingAnalysisTool()
        self.hot_lead_analysis_tool = HotLeadAnalysisTool()
        self.logger = logging.getLogger(__name__)
    
    def create_agent(self):
        """Create the Email Analyzer Agent."""
        return Agent(
            role="Email Analyzer",
            goal="Analyze emails to identify hot leads and meeting requests using AI",
            backstory="""
            You are an expert email analyst specializing in identifying potential sales opportunities 
            and meeting requests from business communications. You use sophisticated AI-powered analysis 
            to detect genuine interest, qualify leads, and identify scheduling requests. Your analysis 
            helps the sales team prioritize responses and maximize conversion opportunities.
            """,
            verbose=True,
            allow_delegation=False,
            tools=[
                self.meeting_analysis_tool,
                self.hot_lead_analysis_tool
            ],
            llm=get_crewai_llm(model="cerebras/llama3.1-8b", temperature=0.3),
        )
    
    def analyze_email_content(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze email content for hot leads and meeting requests.
        
        Args:
            email_data: Dictionary containing email information
            
        Returns:
            Analysis results with hot lead and meeting request information
        """
        try:
            sender_email = email_data.get("sender_email", "")
            sender_name = email_data.get("sender_name", "")
            subject = email_data.get("subject", "")
            body = email_data.get("body", "")
            
            self.logger.info(f"Analyzing email from {sender_email}: 'subject'")
            
            # Perform hot lead analysis
            hot_lead_result = self.hot_lead_analysis_tool._run(
                email_body=body,
                sender_email=sender_email,
                subject=subject
            )
            
            # Perform meeting request analysis
            meeting_result = self.meeting_analysis_tool._run(
                email_body=body,
                sender_email=sender_email,
                subject=subject
            )
            
            # Combine results
            analysis_result = {
                "email_info": {
                    "sender_email": sender_email,
                    "sender_name": sender_name,
                    "subject": subject,
                    "message_id": email_data.get("message_id", "")
                },
                "hot_lead_analysis": hot_lead_result.get("analysis", {}),
                "meeting_request_analysis": meeting_result.get("analysis", {}),
                "timestamp": email_data.get("date_received", ""),
                "analysis_summary": self._generate_analysis_summary(
                    hot_lead_result.get("analysis", {}),
                    meeting_result.get("analysis", {})
                )
            }
            
            # Send UI notification if hot lead detected
            if hot_lead_result.get("analysis", {}).get("is_hot_lead", False):
                self._send_hot_lead_notification(analysis_result)
            
            self.logger.info(f"Email analysis completed for {sender_email}")
            
            return {
                "success": True,
                "result": analysis_result,
                "hot_lead_detected": hot_lead_result.get("analysis", {}).get("is_hot_lead", False),
                "meeting_request_detected": meeting_result.get("analysis", {}).get("is_meeting_request", False)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing email content: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    def _generate_analysis_summary(self, hot_lead_analysis: Dict, meeting_analysis: Dict) -> Dict[str, Any]:
        """Generate summary of the analysis."""
        is_hot_lead = hot_lead_analysis.get("is_hot_lead", False)
        is_meeting_request = meeting_analysis.get("is_meeting_request", False)
        
        summary = {
            "overall_assessment": "normal_email",
            "action_required": False,
            "priority": "low"
        }
        
        if is_hot_lead and is_meeting_request:
            summary = {
                "overall_assessment": "high_value_hot_lead_with_meeting_request",
                "action_required": True,
                "priority": "urgent"
            }
        elif is_hot_lead:
            summary = {
                "overall_assessment": "hot_lead_interested",
                "action_required": True,
                "priority": "high"
            }
        elif is_meeting_request:
            summary = {
                "overall_assessment": "meeting_request_no_hot_lead",
                "action_required": False,
                "priority": "medium"
            }
        
        # Calculate confidence scores
        hot_lead_confidence = hot_lead_analysis.get("confidence", 0.0)
        meeting_confidence = meeting_analysis.get("confidence", 0.0)
        
        summary["confidence_scores"] = {
            "hot_lead_confidence": hot_lead_confidence,
            "meeting_request_confidence": meeting_confidence,
            "overall_confidence": (hot_lead_confidence + meeting_confidence) / 2
        }
        
        return summary
    
    def _send_hot_lead_notification(self, analysis_result: Dict[str, Any]) -> None:
        """Send UI notification for hot lead detection."""
        try:
            import requests
            import os
            from datetime import datetime
            
            ui_url = os.getenv("UI_CLIENT_SERVICE_URL", "http://localhost:8000")
            
            email_info = analysis_result["email_info"]
            hot_lead_analysis = analysis_result["hot_lead_analysis"]
            
            notification_data = {
                "agent_type": "lead_manager",
                "business_id": f"hot_lead_{hash(email_info['sender_email'])}",
                "status": "found",
                "message": f"Hot lead email from {email_info['sender_email']}",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "id": f"hot_lead_{hash(email_info['sender_email'])}",
                    "name": email_info.get("sender_name", ""),
                    "email": email_info["sender_email"],
                    "sender_email": email_info["sender_email"],
                    "sender_name": email_info["sender_name"],
                    "subject": email_info["subject"],
                    "body_preview": analysis_result.get("email_body", "")[:200] + "...",
                    "received_date": analysis_result["timestamp"],
                    "message_id": email_info.get("message_id", ""),
                    "lead_score": hot_lead_analysis.get("lead_score", 0),
                    "confidence": hot_lead_analysis.get("confidence", 0.0),
                    "interest_signals": hot_lead_analysis.get("interest_signals", []),
                    "business_context": hot_lead_analysis.get("business_context", ""),
                    "type": "hot_lead_email"
                }
            }
            
            # Send notification (for now, just log it)
            self.logger.info(f"🔥 HOT LEAD NOTIFICATION: {notification_data}")
            
            # In production, this would make an HTTP request:
            # requests.post(f"{ui_url}/notifications", json=notification_data)
            
        except Exception as e:
            self.logger.error(f"Error sending hot lead notification: {str(e)}")


def run_email_analyzer(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """Run email analyzer agent."""
    agent = EmailAnalyzerAgent()
    return agent.analyze_email_content(email_data)