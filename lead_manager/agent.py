"""
Main Lead Manager Agent - Orchestrates the complete email processing workflow.
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
from lead_manager.config import LeadManagerConfig
from lead_manager.prompts import LEAD_MANAGER_PROMPT, EMAIL_ANALYZER_PROMPT, CALENDAR_ORGANIZER_PROMPT, POST_ACTION_PROMPT
from lead_manager.tools.check_email_tool import CheckEmailTool

# Import sub-agents
from lead_manager.sub_agents.email_checker_agent import run_email_checker
from lead_manager.sub_agents.email_analyzer_agent import run_email_analyzer
from lead_manager.sub_agents.calendar_organizer_agent import run_calendar_organizer
from lead_manager.sub_agents.post_action_agent import run_post_action

logger = logging.getLogger(__name__)


class LeadManagerAgent:
    """Main orchestrating agent for the Lead Manager workflow."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = LeadManagerConfig()
        
    def create_agent(self):
        """Create the main Lead Manager Agent."""
        return Agent(
            role="Lead Manager Orchestrator",
            goal="Orchestrate complete email processing workflow from email monitoring to meeting scheduling",
            backstory="""
            You are the master orchestrator of an intelligent Lead Manager system that processes 
            incoming emails, identifies hot leads through AI-powered content analysis, and automatically 
            schedules meetings with qualified prospects. You coordinate four specialized sub-agents to 
            ensure seamless workflow execution from email receipt to meeting confirmation.
            """,
            verbose=True,
            allow_delegation=True,
            tools=[CheckEmailTool()],
            llm=get_crewai_llm(model="cerebras/llama3.1-8b", temperature=0.1),
        )
    
    def process_leads(self) -> Dict[str, Any]:
        """
        Execute the complete Lead Manager workflow.
        
        Returns:
            Dictionary with complete workflow results
        """
        try:
            self.logger.info("Starting Lead Manager workflow...")
            
            workflow_results = {
                "workflow_started": True,
                "emails_processed": 0,
                "hot_leads_found": 0,
                "meetings_scheduled": 0,
                "successful_processes": 0,
                "detailed_results": [],
                "workflow_summary": {}
            }
            
            # Step 1: Email Checker Agent - Retrieve unread emails
            self.logger.info("Step 1: Checking for unread emails...")
            emails_result = run_email_checker()
            
            if not emails_result.get("success", False):
                self.logger.error("Failed to retrieve emails")
                return _create_error_result("Email retrieval failed", emails_result.get("error", "Unknown error"))
            
            emails_data = emails_result.get("result", {})
            unread_emails = emails_data.get("unread_emails", [])
            
            if not unread_emails:
                self.logger.info("No unread emails found")
                return self._create_no_emails_result()
            
            workflow_results["emails_processed"] = len(unread_emails)
            self.logger.info(f"Found {len(unread_emails)} unread emails")
            
            # Process each email through the workflow according to the flowchart
            for i, email_data in enumerate(unread_emails):
                try:
                    self.logger.info(f"📧 Processing email {i+1}/{len(unread_emails)}: {email_data.get('sender_email', 'Unknown')}")
                    
                    email_result = self._process_email_according_to_flow(email_data)
                    workflow_results["detailed_results"].append(email_result)
                    
                    # Update counters
                    if email_result.get("hot_lead_detected"):
                        workflow_results["hot_leads_found"] += 1
                    if email_result.get("meeting_scheduled"):
                        workflow_results["meetings_scheduled"] += 1
                    if email_result.get("processed_successfully"):
                        workflow_results["successful_processes"] += 1
                        
                except Exception as e:
                    self.logger.error(f"❌ Error processing email {i+1}: {str(e)}")
                    workflow_results["detailed_results"].append({
                        "email": email_data.get("sender_email", "Unknown"),
                        "error": str(e),
                        "processed_successful": False
                    })
            
            # Generate comprehensive workflow summary
            workflow_results["workflow_summary"] = self._generate_workflow_summary(workflow_results)
            
            self.logger.info("Lead Manager workflow completed successfully!")
            self.logger.info(f"Summary: {workflow_results['emails_processed']} emails, {workflow_results['hot_leads_found']} hot leads, {workflow_results['meetings_scheduled']} meetings scheduled")
            
            return {
                "success": True,
                "workflow_completed": True,
                "results": workflow_results
            }
            
        except Exception as e:
            self.logger.error(f"Fatal error in Lead Manager workflow: {str(e)}")
            return _create_error_result("Workflow execution failed", str(e))
    
    def _should_process_email(self, email_data: Dict[str, Any]) -> bool:
        """Filter emails to only process business-related emails."""
        sender_email = email_data.get("sender_email", "").lower()
        subject = email_data.get("subject", "").lower()
        
        # Skip automated/system emails
        skip_domains = [
            "noreply@", "no-reply@", "notification@", "admin@",
            "cloudplatform-noreply@google.com", "analytics-noreply@google.com",
            "accounts-noreply@google.com", "support@", "bounce@", "mail-noreply@",
            "news@", "marketing@", "updates@"
        ]
        
        skip_keywords = [
            "verify your account", "account verification",
            "payment required", "billing notification", "system maintenance",
            "security alert", "password reset", "two-factor authentication",
            "spam warning", "virus detected"
        ]
        
        # Check if it's from a skip domain
        for skip_domain in skip_domains:
            if skip_domain in sender_email:
                return False
        
        # Check if it contains skip keywords
        for skip_keyword in skip_keywords:
            if skip_keyword in subject:
                return False
                
        return True

    def _process_email_according_to_flow(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single email according to the exact flowchart sequence:
        1. Email Checker Agent → Email Data (already done)
        2. Email Analyzer Agent → Hot Lead Detection
        3. Decision: Hot Lead? → Yes: UI Notification
        4. Meeting Request Analysis (using AI)
        5. Decision: Meeting Request? → Yes: Calendar Organizer Agent
        6. Calendar Organizer Agent → Check Availability + Create Meeting
        7. Post Action Agent → Mark Email Read + Save Meeting Data + Final Notifications
        """
        try:
            sender_email = email_data.get("sender_email", "")
            
            # Show email details being processed
            subject = email_data.get("subject", "No Subject")
            sender_name = email_data.get("sender_name", "Unknown")
            print(f"\n📧 PROCESSING EMAIL:")
            print(f"   👤 From: {sender_name} ({sender_email})")
            print(f"   📝 Subject: {subject}")
            print(f"   📅 Date: {email_data.get('date_received', 'Unknown')}")
            print(f"   🔗 Message ID: {email_data.get('message_id', 'Unknown')}")
            
            # Check if we should process this email
            if not self._should_process_email(email_data):
                print(f"   ⏭️ DECISION: SKIPPING - Non-business email")
                print(f"   📋 Flow: Email Checker → Filtered Out")
                self.logger.info(f"⏭️ Skipping non-business email: {sender_email}")
                return {
                    "sender_email": sender_email,
                    "processed_successful": False,
                    "skipped": True,
                    "reason": "Non-business email",
                    "hot_lead_detected": False,
                    "meeting_request_detected": False,
                    "meeting_scheduled": False,
                    "workflow_steps_completed": ["email_checker", "filtered_out"]
                }
            
            print(f"   ✅ DECISION: PROCESSING - Business email")
            print(f"   🔄 Starting Sequential Workflow...")
            
            self.logger.info(f"📧 SEQUENTIAL WORKFLOW: {sender_email}")
            
            # === STEP 1: Email Checker Agent ✅ (Already completed) ===
            self.logger.info(f"🔄 STEP 1: Email Checker Agent ✅ COMPLETED")
            
            # === STEP 2: Email Analyzer Agent (RANK NEXT) ===
            self.logger.info(f"🔍 STEP 2: Email Analyzer Agent → ANALYZING...")
            analysis_result = run_email_analyzer(email_data)
            
            if not analysis_result.get("success", False):
                return {
                    "sender_email": sender_email,
                    "processed_successful": False,
                    "error": analysis_result.get("error", "Analysis failed"),
                    "hot_lead_detected": False,
                    "meeting_request_detected": False,
                    "meeting_scheduled": False,
                    "workflow_steps_completed": ["email_checker"]
                }
            
            hot_lead_detected = analysis_result.get("hot_lead_detected", False)
            meeting_request_detected = analysis_result.get("meeting_request_detected", False)
            
            # === STEP 3: Decision Point - Hot Lead? ===
            if hot_lead_detected:
                self.logger.info(f"🔥 STEP 3: HOT LEAD DETECTED! ✅ → UI Notification sent")
            else:
                self.logger.info(f"📧 STEP 3: No hot lead detected - CONTINUING...")
            
            # === STEP 4: Meeting Request Analysis ✅ (Already completed in analyzer) ===
            self.logger.info(f"🤖 STEP 4: Meeting Request Analysis ✅ COMPLETED")
            
            # === STEP 5: Decision Point - Meeting Request + Hot Lead? ===
            meeting_result = {"meeting_scheduled": False, "reason": "No meeting request or not hot lead"}
            
            if meeting_request_detected and hot_lead_detected:
                self.logger.info(f"🚀 STEP 5: Meeting Request + Hot Lead → CALENDAR ORGANIZER")
                
                # === STEP 6: Calendar Organizer Agent (ONLY if both hot lead + meeting request) ===
                self.logger.info(f"📅 STEP 6: Calendar Organizer Agent → SCHEDULING...")
                meeting_result = run_calendar_organizer(email_data, analysis_result.get("result", {}))
                
                if meeting_result.get("success", False) and meeting_result.get("meeting_scheduled"):
                    self.logger.info(f"✅ STEP 6: Meeting scheduled successfully!")
                    workflow_steps = ["email_checker", "email_analyzer", "hot_lead_notification", "calendar_organizer"]
                else:
                    self.logger.error(f"❌ STEP 6: Meeting scheduling failed!")
                    workflow_steps = ["email_checker", "email_analyzer", "hot_lead_notification", "calendar_organizer_failed"]
            else:
                if meeting_request_detected and not hot_lead_detected:
                    self.logger.info(f"📧 STEP 5: Meeting request but NOT hot lead → NO CALENDAR ORGANIZER")
                    workflow_steps = ["email_checker", "email_analyzer", "calendar_organizer_skipped"]
                else:
                    self.logger.info(f"📧 STEP 5: No meeting request → NO CALENDAR ORGANIZER")
                    workflow_steps = ["email_checker", "email_analyzer"]
            
            # === STEP 7: Post Action Agent (ALWAYS RUNS LAST) ===
            self.logger.info(f"🔧 STEP 7: Post Action Agent → FINALIZING...")
            finalization_result = run_post_action(email_data, analysis_result, meeting_result)
            
            self.logger.info(f"✅ SEQUENTIAL WORKFLOW COMPLETED for: {sender_email}")
            
            return {
                "sender_email": sender_email,
                "processed_successful": True,
                "hot_lead_detected": hot_lead_detected,
                "meeting_request_detected": meeting_request_detected,
                "meeting_scheduled": meeting_result.get("meeting_scheduled", False),
                "analysis_result": analysis_result,
                "meeting_result": meeting_result,
                "finalization_result": finalization_result,
                "workflow_completed": finalization_result.get("success", False),
                "workflow_steps_completed": workflow_steps
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error processing email from {sender_email}: {str(e)}")
            return {
                "sender_email": sender_email,
                "processed_successful": False,
                "error": str(e),
                "hot_lead_detected": False,
                "meeting_request_detected": False,
                "meeting_scheduled": False,
                "workflow_steps_completed": ["email_checker", "error"]
            }

    def _process_single_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single email through the complete Lead Manager workflow.
        
        Args:
            email_data: Dictionary containing email information
            
        Returns:
            Processing results for the email
        """
        try:
            sender_email = email_data.get("sender_email", "")
            self.logger.info(f"Analyzing email from: {sender_email}")
            
            # Step 2: Email Analyzer Agent - Analyze for hot leads and meeting requests
            analysis_result = run_email_analyzer(email_data)
            
            if not analysis_result.get("success", False):
                return {
                    "sender_email": sender_email,
                    "processed_successful": False,
                    "error": analysis_result.get("error", "Analysis failed"),
                    "hot_lead_detected": False,
                    "meeting_request_detected": False,
                    "meeting_scheduled": False
                }
            
            hot_lead_detected = analysis_result.get("hot_lead_detected", False)
            meeting_request_detected = analysis_result.get("meeting_request_detected", False)
            
            self.logger.info(f"Analysis results: Hot lead({hot_lead_detected}), Meeting request({meeting_request_detected})")
            
            # Step 3: Calendar Organizer Agent - Schedule meeting if both hot lead AND meeting request
            meeting_result = None
            should_schedule = self._should_schedule_meeting(hot_lead_detected, meeting_request_detected)
            
            if should_schedule:
                self.logger.info(f"Scheduling meeting for hot lead: {email_data.get('sender_email', 'Unknown')}")
                meeting_result = run_calendar_organizer(email_data, analysis_result.get("result", {}))
                
                if not meeting_result.get("success", False):
                    self.logger.error(f"Failed to schedule meeting: {meeting_result.get('error', 'Unknown error')}")
            else:
                self.logger.info(f"No meeting scheduled - Hot lead: {hot_lead_detected}, Meeting request: {meeting_request_detected}")
                meeting_result = {"meeting_scheduled": False, "reason": "Conditions not met"}
            
            # Step 4: Post Action Agent - Finalize workflow
            self.logger.info(f"Finalizing workflow for: {email_data.get('sender_email', 'Unknown')}")
            finalization_result = run_post_action(email_data, analysis_result, meeting_result)
            
            return {
                "sender_email": sender_email,
                "processed_successful": True,
                "hot_lead_detected": hot_lead_detected,
                "meeting_request_detected": meeting_request_detected,
                "meeting_scheduled": meeting_result.get("meeting_scheduled", False),
                "analysis_result": analysis_result,
                "meeting_result": meeting_result,
                "finalization_result": finalization_result,
                "workflow_completed": finalization_result.get("success", False)
            }
            
        except Exception as e:
            self.logger.error(f"Error processing email from {sender_email}: {str(e)}")
            return {
                "sender_email": sender_email,
                "processed_successful": False,
                "error": str(e),
                "hot_lead_detected": False,
                "meeting_request_detected": False,
                "meeting_scheduled": False
            }
    
    def _should_schedule_meeting(self, hot_lead: bool, meeting_request: bool) -> bool:
        """Determine if a meeting should be scheduled based on analysis results."""
        # Only schedule meetings for actual hot leads who have made meeting requests
        return hot_lead and meeting_request
    
    def _create_no_emails_result(self) -> Dict[str, Any]:
        """Create result for when no emails are found."""
        return {
            "success": True,
            "workflow_completed": True,
            "results": {
                "workflow_started": True,
                "emails_processed": 0,
                "hot_leads_found": 0,
                "meetings_scheduled": 0,
                "successful_processes": 0,
                "detailed_results": [],
                "workflow_summary": {
                    "status": "No emails to process",
                    "total_emails": 0,
                    "success_rate": 100.0,
                    "recommendation": "Continue monitoring Gmail for incoming emails"
                }
            }
        }
    
    def _generate_workflow_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive workflow summary."""
        try:
            total_emails = results.get("emails_processed", 0)
            hot_leads = results.get("hot_leads_found", 0)
            meetings_scheduled = results.get("meetings_scheduled", 0)
            successful_processes = results.get("successful_processes", 0)
            
            success_rate = (successful_processes / total_emails * 100) if total_emails > 0 else 0
            hot_lead_rate = (hot_leads / total_emails * 100) if total_emails > 0 else 0
            meeting_conversion_rate = (meetings_scheduled / hot_leads * 100) if hot_leads > 0 else 0
            
            summary = {
                "workflow_status": "completed",
                "total_emails_processed": total_emails,
                "hot_leads_identified": hot_leads,
                "meetings_successfully_scheduled": meetings_scheduled,
                "successful_processes": successful_processes,
                "success_rate_percentage": round(success_rate, 2),
                "hot_lead_detection_rate": round(hot_lead_rate, 2),
                "meeting_conversion_rate": round(meeting_conversion_rate, 2),
                "recommendation": self._get_workflow_recommendation(results)
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating workflow summary: {str(e)}")
            return {"error": str(e)}
    
    def _get_workflow_recommendation(self, results: Dict[str, Any]) -> str:
        """Get recommendation based on workflow results."""
        hot_leads = results.get("hot_leads_found", 0)
        meetings_scheduled = results.get("meetings_scheduled", 0)
        
        if meetings_scheduled > 0:
            return f"Excellent! {meetings_scheduled} meetings scheduled with hot leads. Follow up with attendees and prepare presentation materials."
        elif hot_leads > 0:
            return f"Good lead identification! {hot_leads} hot leads detected. Consider manual follow-up for high-interest prospects."
        else:
            return "No hot leads detected in current batch. Continue monitoring emails for business interest signals."


def _create_error_result(message: str, error_details: str) -> Dict[str, Any]:
    """Create standardized error result."""
    return {
        "success": False,
        "workflow_completed": False,
        "error": message,
        "error_details": error_details,
        "results": None
    }


def process_leads() -> Dict[str, Any]:
    """Main entry point for Lead Manager workflow."""
    agent = LeadManagerAgent()
    return agent.process_leads()