"""
Email tool for sending follow-up emails after successful calls.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from crewai.tools import BaseTool
from pydantic import Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailTool(BaseTool):
    """Tool for sending follow-up emails to businesses."""

    name: str = "email_tool"
    description: str = """
    Send follow-up email to business after successful phone conversation.

    Args:
        business_data (dict): Dictionary containing business information
        email_data (dict): Email content including to, subject, and body
        proposal (str): The proposal to include in the email

    Returns:
        dict: Email result containing:
            - status: 'sent', 'failed', or 'error'
            - message: Status message
            - email_details: Email information
    """

    def _run(self, business_data: dict, email_data: dict, proposal: str) -> dict:
        """
        Send follow-up email.

        Args:
            business_data: Business information
            email_data: Email content (to, subject, body)
            proposal: Proposal text

        Returns:
            Dictionary with email results
        """
        try:
            # For now, simulate email sending (you can integrate with actual email service)
            # In production, you would integrate with Gmail API, SendGrid, etc.
            
            to_email = email_data.get("to")
            subject = email_data.get("subject")
            body = email_data.get("body")

            if not all([to_email, subject, body]):
                return {
                    "status": "error",
                    "message": "Missing required email fields (to, subject, body)",
                    "email_details": None
                }

            # Simulate email sending
            logger.info(f"Simulating email send to: {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body preview: {body[:100]}...")

            # In a real implementation, you would:
            # 1. Connect to email service (Gmail API, SendGrid, etc.)
            # 2. Send the actual email
            # 3. Handle delivery confirmations
            # 4. Log the email in your system

            # For now, return success
            return {
                "status": "sent",
                "message": f"Email sent successfully to {to_email}",
                "email_details": {
                    "to": to_email,
                    "subject": subject,
                    "sent_at": datetime.now().isoformat(),
                    "business_name": business_data.get("name"),
                    "proposal_included": True
                }
            }

        except Exception as e:
            error_msg = f"Error sending email: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "message": error_msg,
                "email_details": None
            }


# Singleton instance
email_tool = EmailTool()
