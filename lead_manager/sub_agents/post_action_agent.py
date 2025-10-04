"""
Post Action Agent for Lead Manager.
Finalizes the booking process and cleans up after meeting scheduling.
"""

import logging
from typing import Any, Dict
from crewai import Agent, Task, Crew
from leads_finder.llm_config import get_crewai_llm
from lead_manager.prompts import POST_ACTION_PROMPT
from lead_manager.tools.mongodb_lead_tools import (
    MarkEmailReadTool,
    SaveMeetingTool,
    UINotificationTool
)

logger = logging.getLogger(__name__)


class PostActionAgent:
    """Agent responsible for finalizing the Lead Manager workflow."""
    
    def __init__(self):
        self.mark_email_read_tool = MarkEmailReadTool()
        self.save_meeting_tool = SaveMeetingTool()
        self.ui_notification_tool = UINotificationTool()
        self.logger = logging.getLogger(__name__)
    
    def create_agent(self):
        """Create the Post Action Agent."""
        return Agent(
            role="Post Action Manager",
            goal="Finalize the lead management process and ensure proper cleanup",
            backstory="""
            You are a meticulous process finalization specialist responsible for completing 
            the lead management workflow. You ensure all data is properly saved, emails are 
            marked as read, and appropriate notifications are sent. You maintain clean audit 
            trails and verify that all actions are completed successfully.
            """,
            verbose=True,
            allow_delegation=False,
            tools=[
                self.mark_email_read_tool,
                self.save_meeting_tool,
                self.ui_notification_tool
            ],
            llm=get_crewai_llm(model="cerebras/llama3.1-8b", temperature=0.1),
        )
    
    def finalize_workflow(self, email_data: Dict[str, Any], analysis_result: Dict[str, Any], meeting_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Finalize the complete Lead Manager workflow.
        
        Args:
            email_data: Dictionary containing email information
            analysis_result: Analysis results from Email Analyzer
            meeting_result: Meeting scheduling results from Calendar Organizer
            
        Returns:
            Finalization results
        """
        try:
            self.logger.info("Finalizing Lead Manager workflow")
            
            results = {
                "success": True,
                "activities_completed": [],
                "meeting_saved": False,
                "email_marked_read": False,
                "notifications_sent": False
            }
            
            # Save meeting data if meeting was scheduled
            meeting_scheduled = meeting_result.get("meeting_scheduled", False)
            if meeting_scheduled and meeting_result.get("meeting_data"):
                save_result = self._save_meeting_data(email_data, analysis_result, meeting_result)
                results["meeting_saved"] = save_result["success"]
                results["activities_completed"].append("meeting_data_saved")
                
                if save_result["success"]:
                    self.logger.info("Meeting data saved successfully")
            
            # Mark email as read
            mark_read_result = self._mark_email_as_read(email_data)
            results["email_marked_read"] = mark_read_result["success"]
            if mark_read_result["success"]:
                results["activities_completed"].append("email_marked_read")
                self.logger.info("Email marked as read")
            
            # Send completion notification
            notification_result = self._send_completion_notification(email_data, analysis_result, meeting_result)
            results["notifications_sent"] = notification_result["success"]
            if notification_result["success"]:
                results["activities_completed"].append("completion_notification_sent")
                self.logger.info("Completion notification sent")
            
            # Generate workflow summary
            results["workflow_summary"] = self._generate_workflow_summary(
                email_data, analysis_result, meeting_result, results
            )
            
            self.logger.info(f"Workflow finalized: {len(results['activities_completed'])} activities completed")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error finalizing workflow: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "activities_completed": [],
                "meeting_saved": False,
                "email_marked_read": False,
                "notifications_sent": False
            }
    
    def _save_meeting_data(self, email_data: Dict[str, Any], analysis_result: Dict[str, Any], meeting_result: Dict[str, Any]) -> Dict[str, Any]:
        """Save complete meeting data to database."""
        try:
            meeting_data = {
                "email_context": {
                    "sender_email": email_data.get("sender_email", ""),
                    "sender_name": email_data.get("sender_name", ""),
                    "subject": email_data.get("subject", ""),
                    "date_received": email_data.get("date_received", ""),
                    "message_id": email_data.get("message_id", ""),
                    "thread_id": email_data.get("thread_id", "")
                },
                "analysis_context": {
                    "hot_lead_detected": analysis_result.get("hot_lead_detected", False),
                    "meeting_request_detected": analysis_result.get("meeting_request_detected", False),
                    "hot_lead_score": analysis_result.get("result", {}).get("hot_lead_analysis", {}).get("lead_score", 0),
                    "confidence": analysis_result.get("result", {}).get("hot_lead_analysis", {}).get("confidence", 0.0)
                },
                "meeting_details": meeting_result.get("meeting_data", {}),
                "workflow_status": "completed"
            }
            
            save_result = self.save_meeting_tool._run(meeting_data)
            return save_result
            
        except Exception as e:
            self.logger.error(f"Error saving meeting data: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _mark_email_as_read(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mark the processed email as read in Gmail."""
        try:
            message_id = email_data.get("message_id", "")
            if not message_id:
                return {"success": False, "error": "No message ID provided"}
            
            mark_result = self.mark_email_read_tool._run([message_id])
            return mark_result
            
        except Exception as e:
            self.logger.error(f"Error marking email as read: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _send_completion_notification(self, email_data: Dict[str, Any], analysis_result: Dict[str, Any], meeting_result: Dict[str, Any]) -> Dict[str, Any]:
        """Send completion notification to UI."""
        try:
            import os
            from datetime import datetime
            
            notification_data = {
                "workflow_status": "completed",
                "timestamp": datetime.utcnow().isoformat(),
                "email_summary": {
                    "sender": email_data.get("sender_email", ""),
                    "subject": email_data.get("subject", ""),
                    "date_processed": datetime.utcnow().isoformat()
                },
                "analysis_results": {
                    "hot_lead_detected": analysis_result.get("hot_lead_detected", False),
                    "meeting_request_detected": analysis_result.get("meeting_request_detected", False)
                },
                "meeting_results": {
                    "meeting_scheduled": meeting_result.get("meeting_scheduled", False),
                    "meeting_id": meeting_result.get("meeting_id", "")
                }
            }
            
            notify_result = self.ui_notification_tool._run(notification_data)
            return notify_result
            
        except Exception as e:
            self.logger.error(f"Error sending completion notification: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _generate_workflow_summary(self, email_data: Dict[str, Any], analysis_result: Dict[str, Any], meeting_result: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive workflow summary."""
        try:
            summary = {
                "processed_email": {
                    "sender": email_data.get("sender_email", ""),
                    "subject": email_data.get("subject", ""),
                    "message_id": email_data.get("message_id", "")
                },
                "lead_analysis": {
                    "is_hot_lead": analysis_result.get("hot_lead_detected", False),
                    "is_meeting_request": analysis_result.get("meeting_request_detected", False),
                    "confidence_score": analysis_result.get("result", {}).get("hot_lead_analysis", {}).get("confidence", 0.0),
                    "lead_score": analysis_result.get("result", {}).get("hot_lead_analysis", {}).get("lead_score", 0)
                },
                "meeting_scheduling": {
                    "meeting_scheduled": meeting_result.get("meeting_scheduled", False),
                    "meeting_id": meeting_result.get("meeting_id", ""),
                    "availability_checked": meeting_result.get("availability_checked", 0)
                },
                "workflow_completion": {
                    "total_activities": len(results.get("activities_completed", [])),
                    "activities_completed": results.get("activities_completed", []),
                    "success_rate": len(results.get("activities_completed", [])) / 3.0 * 100  # 3 main activities
                }
            }
            
            # Add recommendation for next_action
            if summary["lead_analysis"]["is_hot_lead"] and summary["meeting_scheduling"]["meeting_scheduled"]:
                summary["next_action_recommendation"] = "Follow up with attendee 1 hour before meeting"
            elif summary["lead_analysis"]["is_hot_lead"]:
                summary["next_action_recommendation"] = "Send personalized follow-up email within 2 hours"
            else:
                summary["next_action_recommendation"] = "Monitor for additional interest signals"
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating workflow summary: {str(e)}")
            return {"error": str(e)}


def run_post_action(email_data: Dict[str, Any], analysis_result: Dict[str, Any], meeting_result: Dict[str, Any]) -> Dict[str, Any]:
    """Run post action agent."""
    agent = PostActionAgent()
    return agent.finalize_workflow(email_data, analysis_result, meeting_result)