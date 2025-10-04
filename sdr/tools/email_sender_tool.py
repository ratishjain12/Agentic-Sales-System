"""
Email Sender Tool - Gmail OAuth2 Integration
"""
import os
import json
import base64
from typing import Optional, Dict, Any, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from crewai.tools import BaseTool
from pydantic import Field

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class EmailSenderTool(BaseTool):
    """
    Tool for sending emails using Gmail OAuth2 (Personal Gmail).
    
    This works with your personal Gmail account and doesn't require
    service account configuration.
    
    Requires:
    - Gmail OAuth2 credentials JSON file
    - GMAIL_CREDENTIALS_FILE environment variable
    - GMAIL_SENDER_EMAIL environment variable
    """
    
    name: str = "email_sender"
    description: str = """Send emails using Gmail OAuth2 (Personal Gmail).
    
    Parameters:
    - to_email: Recipient email address
    - subject: Email subject line
    - body: Email body content (HTML or plain text)
    - is_html: Whether body is HTML (default: True)
    
    Returns:
    - Success message with message ID or error details
    """
    
    credentials_file: Optional[str] = Field(default=None, exclude=True)
    token_file: Optional[str] = Field(default=None, exclude=True)
    sender_email: Optional[str] = Field(default=None, exclude=True)
    
    def __init__(self, credentials_file: Optional[str] = None, token_file: Optional[str] = None, sender_email: Optional[str] = None, **kwargs):
        """
        Initialize OAuth2 Email Sender Tool.
        
        Args:
            credentials_file: Path to OAuth2 credentials JSON file
            token_file: Path to store/load OAuth2 token
            sender_email: Email address to send from
        """
        super().__init__(**kwargs)
        self.credentials_file = credentials_file or os.getenv("GMAIL_CREDENTIALS_FILE", "credentials/oauth2_credentials.json")
        self.token_file = token_file or os.getenv("GMAIL_TOKEN_FILE", "credentials/token.json")
        self.sender_email = sender_email or os.getenv("GMAIL_SENDER_EMAIL", "ratishjain10@gmail.com")
        
        # Validate credentials file exists
        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(f"OAuth2 credentials file not found: {self.credentials_file}")
    
    def _get_gmail_service(self):
        """Get authenticated Gmail service instance using OAuth2."""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing OAuth2 token...")
                creds.refresh(Request())
            else:
                print("🔑 Starting OAuth2 authentication flow...")
                print("   A browser window will open for authentication.")
                print("   Please complete the authentication process.")
                
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
            print(f"✅ OAuth2 token saved to: {self.token_file}")
        
        # Build Gmail service
        service = build('gmail', 'v1', credentials=creds)
        return service
    
    def _run(self, to_email: str, subject: str, body: str, is_html: bool = True) -> str:
        """
        Send an email using Gmail OAuth2.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            body: Email body content
            is_html: Whether body is HTML format
            
        Returns:
            Success message with message ID or error details
        """
        try:
            # Validate inputs
            if not to_email or not subject or not body:
                return "Error: to_email, subject, and body are required"
            
            # Get Gmail service
            service = self._get_gmail_service()
            
            # Create message
            message = MIMEMultipart('alternative')
            message['to'] = to_email
            message['from'] = self.sender_email
            message['subject'] = subject
            
            # Add body
            if is_html:
                html_part = MIMEText(body, 'html')
                message.attach(html_part)
            else:
                text_part = MIMEText(body, 'plain')
                message.attach(text_part)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send email
            send_message = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            message_id = send_message.get('id')
            return f"Email sent successfully! Message ID: {message_id}"
            
        except HttpError as e:
            error_details = e.error_details[0] if e.error_details else {}
            return f"Gmail API error: {error_details.get('message', str(e))}"
        except Exception as e:
            return f"Error sending email: {str(e)}"
    
    def send_email(self, to_email: str, subject: str, body: str, is_html: bool = True) -> Dict[str, Any]:
        """
        Send email and return structured result.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            body: Email body content
            is_html: Whether body is HTML format
            
        Returns:
            Dict with success status and details
        """
        result = self._run(to_email, subject, body, is_html)
        
        return {
            "success": "successfully" in result.lower(),
            "message": result,
            "to_email": to_email,
            "subject": subject
        }


def create_email_sender_tool(credentials_file: Optional[str] = None, token_file: Optional[str] = None, sender_email: Optional[str] = None) -> EmailSenderTool:
    """
    Factory function to create an Email Sender Tool.
    
    Args:
        credentials_file: Path to OAuth2 credentials JSON file
        token_file: Path to store/load OAuth2 token
        sender_email: Email address to send from
        
    Returns:
        EmailSenderTool instance
    """
    return EmailSenderTool(credentials_file=credentials_file, token_file=token_file, sender_email=sender_email)


# Create singleton instance for easy import
email_sender_tool = create_email_sender_tool()