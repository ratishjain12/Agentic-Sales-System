"""
Gmail Email Checking Tool using Service Account Authentication.
"""

import os
import base64
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, AsyncGenerator
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from email.utils import parsedate_to_datetime

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

# Gmail OAuth2 Configuration
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", ".secrets/credentials.json")
TOKEN_FILE = os.getenv("TOKEN_FILE", ".secrets/token.json")
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly'
]


class EmailMessage(BaseModel):
    sender_email: str = Field(..., description="Sender email address")
    message_id: str = Field(..., description="Unique message ID")
    thread_id: str = Field(..., description="Thread/conversation ID")
    sender_name: str = Field(..., description="Sender display name")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body content")
    date_received: str = Field(..., description="Date received in ISO 8601 format")
    thread_conversation_history: List[Dict[str, str]] = Field(
        default_factory=list, 
        description="Previous messages in the thread"
    )


def extract_message_body(message):
    """Extract clean text body from Gmail message, removing HTML and CSS"""
    body = ""
    
    def extract_text_from_part(part):
        mime_type = part.get('mimeType', '')
        
        if mime_type == 'text/plain':
            data = part.get('body', {}).get('data')
            if data:
                # Plain text doesn't need HTML cleaning, but still clean basic formatting
                return clean_plain_text(base64.urlsafe_b64decode(data).decode('utf-8'))
        
        elif mime_type == 'text/html':
            data = part.get('body', {}).get('data')
            if data:
                html_content = base64.urlsafe_b64decode(data).decode('utf-8')
                return decode_to_clean_text(html_content)
        
        return ""
    
    def clean_plain_text(text):
        """Clean plain text without aggressive HTML removal"""
        if not text:
            return ""
        
        import re
        
        # Remove email headers
        text = re.sub(r'^From:.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^To:.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^Subject:.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^Date:.*$', '', text, flags=re.MULTILINE)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def decode_to_clean_text(text):
        """Clean up the extracted text by removing HTML, CSS, and formatting noise"""
        if not text:
            return ""
        
        import re
        
        # Remove HTML tags completely
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # Remove CSS styles and rules (everything between curly braces)
        clean_text = re.sub(r'\{[^}]*\}', '', clean_text)
        
        # Remove CSS selectors and class names
        clean_text = re.sub(r'[.#][A-Za-z][A-Za-z0-9_\-]*', '', clean_text)
        
        # Remove HTML attributes (key="value" or key=value)
        clean_text = re.sub(r'\w+="[^"]*"', '', clean_text)
        clean_text = re.sub(r"\w+='[^']*'", '', clean_text)
        clean_text = re.sub(r'\w+=[^>\s]+', '', clean_text)
        
        # Remove media queries and CSS at-rules
        clean_text = re.sub(r'@media[^}]*}', '', clean_text, flags=re.DOTALL)
        clean_text = re.sub(r'@[a-zA-Z]+[^;}]*[;}][^;}]*', '', clean_text)
        
        # Remove CSS properties (property: value;)
        clean_text = re.sub(r'[a-zA-Z-]+\s*:\s*[^;]+;', '', clean_text)
        
        # Remove style attributes content
        clean_text = re.sub(r'style\s*=\s*["\'][^"\']*["\']', '', clean_text)
        
        # Remove HTML entities
        clean_text = re.sub(r'&[a-zA-Z0-9#]+;', '', clean_text)
        clean_text = re.sub(r'&nbsp;', ' ', clean_text)
        clean_text = re.sub(r'&amp;', '&', clean_text)
        clean_text = re.sub(r'&lt;', '<', clean_text)
        clean_text = re.sub(r'&gt;', '>', clean_text)
        
        # Remove JavaScript and script content
        clean_text = re.sub(r'<script[^>]*>.*?</script>', '', clean_text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove mailto links but keep the email part
        clean_text = re.sub(r'mailto:([^>\s]+)', r'\1', clean_text)
        
        # Remove absolute URLs but keep relative text
        clean_text = re.sub(r'https?://[^\s]+', '', clean_text)
        
        # Clean up whitespace and formatting
        clean_text = re.sub(r'\s+', ' ', clean_text)
        clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)
        clean_text = re.sub(r'^\s+|\s+$', '', clean_text, flags=re.MULTILINE)
        
        # Remove email footers and signatures (common patterns)
        clean_text = re.sub(r'© \d{4}.*$', '', clean_text, flags=re.MULTILINE)
        clean_text = re.sub(r'You have received this.*$', '', clean_text, flags=re.MULTILINE)
        clean_text = re.sub(r'Unsubscribe.*$', '', clean_text, flags=re.MULTILINE)
        clean_text = re.sub(r'To unsubscribe.*$', '', clean_text, flags=re.MULTILINE)
        
        return clean_text.strip()
    
    payload = message.get('payload', {})
    
    # Priority: Look for plain text first
    plain_text_found = False
    
    # Single part message
    if payload.get('body', {}).get('data'):
        mime_type = payload.get('mimeType', '')
        if mime_type == 'text/plain':
            plain_text_found = True
            body = extract_text_from_part(payload)
        elif mime_type == 'text/html':
            body = decode_to_clean_text(base64.urlsafe_b64decode(payload.get('body', {}).get('data')).decode('utf-8'))
    
    # Multi-part message
    elif payload.get('parts'):
        # First pass: look for plain text
        for part in payload['parts']:
            if part.get('parts'):  # Nested parts
                for nested_part in part['parts']:
                    if nested_part.get('mimeType') == 'text/plain':
                        text = extract_text_from_part(nested_part)
                        if text:
                            plain_text_found = True
                            body += text + "\n\n"
            elif part.get('mimeType') == 'text/plain':
                text = extract_text_from_part(part)
                if text:
                    plain_text_found = True
                    body += text + "\n\n"
        
        # Second pass: if no plain text, use HTML
        if not plain_text_found:
            for part in payload['parts']:
                if part.get('parts'):  # Nested parts
                    for nested_part in part['parts']:
                        if nested_part.get('mimeType') == 'text/html':
                            html_text = decode_to_clean_text(base64.urlsafe_b64decode(nested_part.get('body', {}).get('data')).decode('utf-8'))
                            if html_text:
                                body += html_text + "\n\n"
                elif part.get('mimeType') == 'text/html':
                    html_text = decode_to_clean_text(base64.urlsafe_b64decode(part.get('body', {}).get('data')).decode('utf-8'))
                    if html_text:
                        body += html_text + "\n\n"
    
    # Final cleanup
    body = decode_to_clean_text(body) if body else ""
    
    return body.strip() if body else ""


def extract_email_address(email_string):
    """Extract email address from 'Name <email@domain.com>' format"""
    if '<' in email_string and '>' in email_string:
        return email_string.split('<')[1].split('>')[0]
    return email_string.strip()


def get_thread_details(service, thread_id):
    """Get detailed information about an email thread"""
    try:
        thread = service.users().threads().get(
            userId='me',
            id=thread_id
        ).execute()
        
        messages = thread.get('messages', [])
        participants = set()
        
        for msg in messages:
            headers = msg['payload'].get('headers', [])
            from_header = next((h['value'] for h in headers if h['name'] == 'From'), '')
            to_header = next((h['value'] for h in headers if h['name'] == 'To'), '')
            
            # Extract email addresses
            if from_header:
                participants.add(extract_email_address(from_header))
            if to_header:
                for email in to_header.split(','):
                    participants.add(extract_email_address(email.strip()))
        
        return {
            'message_count': len(messages),
            'participants': list(participants)
        }
        
    except Exception as e:
        logger.warning(f"Error getting thread details: {e}")
        return {'message_count': 1, 'participants': ['Unknown']}


def _authenticate_gmail_service():
    """Authenticate with Gmail API using OAuth2."""
    try:
        if not GMAIL_API_AVAILABLE:
            print("❌ Gmail API dependencies not installed")
            print("💡 Run: pip install google-auth google-auth-oauthlib google-api-python-client")
            return None
        
        # Check if credentials file exists
        if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
            print(f"❌ Credentials file not found: {GOOGLE_CREDENTIALS_FILE}")
            print("📋 To set up Gmail API with OAuth2:")
            print("1. Go to Google Cloud Console")
            print("2. Enable Gmail API")
            print("3. Create OAuth 2.0 Client ID")
            print("4. Download as JSON file")
            print(f"5. Place it at: {GOOGLE_CREDENTIALS_FILE}")
            return None
        
        print(f"🔗 Authenticating with Gmail API using OAuth2...")
        print(f"📧 Credentials file: {GOOGLE_CREDENTIALS_FILE}")
        
        creds = None
        # Load token if it exists
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, GMAIL_SCOPES)
        
        # If there are no valid credentials, request authorization
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing expired credentials...")
                creds.refresh(Request())
            else:
                print("🔗 Starting OAuth2 authentication flow...")
                flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILE, GMAIL_SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        service = build('gmail', 'v1', credentials=creds)
        print("✅ Gmail API OAuth2 authentication successful")
        return service
        
    except Exception as e:
        logger.error(f"❌ Gmail OAuth2 authentication error: {e}")
        return None


def _get_unread_emails_from_gmail():
    """Get unread emails from Gmail using OAuth2 authentication."""
    try:
        logger.info("🔍 Checking unread emails...")
        
        # Authenticate
        service = _authenticate_gmail_service()
        if not service:
            return []
        
        # Get unread messages (limited to first 10)
        results = service.users().messages().list(
            userId='me',
            q='is:unread',
            maxResults=10
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            logger.info("✅ No unread emails found!")
            return []
        
        logger.info(f"📧 Found {len(messages)} unread email(s)")
        
        unread_emails = []
        
        for i, message in enumerate(messages, 1):
            message_id = message['id']
            
            # Get detailed message info
            msg = service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = msg['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            date_hdr = next((h['value'] for h in headers if h['name'] == 'Date'), 'No Date')
            thread_id = msg.get('threadId')
            
            # Get message body
            body = extract_message_body(msg)
            
            # Get thread details
            thread_info = get_thread_details(service, thread_id)
            
            # Convert header date to ISO format for JSON serialization
            try:
                dt = parsedate_to_datetime(date_hdr)
                date_received = dt.isoformat()
            except Exception:
                date_received = date_hdr
            
            # Extract sender email address
            sender_email = extract_email_address(sender)
            
            # Extract sender name
            sender_name = sender.split('<')[0].strip().strip('"') if '<' in sender else sender_email.split('@')[0]
            
            email_data = {
                'sender_email': sender_email,
                'message_id': message_id,
                'thread_id': thread_id,
                'sender_name': sender_name,
                'subject': subject,
                'body': body,
                'date_received': date_received,
                'thread_conversation_history': []
            }
            
            unread_emails.append(email_data)
            
            logger.info(f"📧 Email #{i}: {sender_email} - {subject}")
        
        return unread_emails
        
    except Exception as e:
        logger.error(f"❌ Error getting emails from Gmail: {e}")
        return []


class CheckEmailTool(BaseTool):
    """Tool to retrieve unread emails using Gmail OAuth2 API."""
    
    name: str = "check_email_tool"
    description: str = "Retrieve unread emails from Gmail using OAuth2 authentication and return structured email data."
    
    def _run(self, query: str = None) -> Any:
        print("📧 Gmail OAuth2 email checker tool called!!")
        
        try:
            # Get emails from Gmail using OAuth2
            emails = _get_unread_emails_from_gmail()
            
            # Convert to EmailMessage objects and then to dicts
            structured_emails = []
            for email_data in emails:
                try:
                    email_obj = EmailMessage(**email_data)
                    structured_emails.append(email_obj.model_dump())
                except Exception as e:
                    print(f"❌ Error structuring email: {e}")
                    continue
            
            print(f"📊 Returning {len(structured_emails)} structured emails")
            return structured_emails
            
        except Exception as e:
            print(f"❌ Error in Gmail OAuth2 check_email_tool: {e}")
            return []


# Instantiate the tool
check_email_tool = CheckEmailTool()
