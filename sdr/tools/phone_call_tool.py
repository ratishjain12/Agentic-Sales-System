"""
Phone Call Tool for making outreach calls to business owners using ElevenLabs + Twilio.
"""

import os
import json
import logging
import asyncio
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from crewai.tools import BaseTool
from pydantic import Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PhoneCallTool(BaseTool):
    """Tool for making phone calls to business owners using ElevenLabs Conversational AI."""

    name: str = "phone_call_tool"
    description: str = """
    Make a phone call to a business owner to present a proposal.

    Args:
        business_data (dict): Dictionary containing business information including:
            - name: Business name
            - phone_number or phone: Contact phone number
            - address: Business address
            - Any other relevant business details
        proposal (str): The proposal text to discuss with the business owner

    Returns:
        dict: Call result containing:
            - status: 'done', 'failed', or 'error'
            - transcript: List of conversation messages
            - conversation_id: ID of the conversation
            - error: Error message if applicable
    """

    elevenlabs_api_key: Optional[str] = Field(default=None, exclude=True)
    elevenlabs_agent_id: Optional[str] = Field(default=None, exclude=True)
    elevenlabs_phone_number_id: Optional[str] = Field(default=None, exclude=True)

    def __init__(self, **kwargs):
        """Initialize the phone call tool with API credentials."""
        super().__init__(**kwargs)
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.elevenlabs_agent_id = os.getenv("ELEVENLABS_AGENT_ID")
        self.elevenlabs_phone_number_id = os.getenv("ELEVENLABS_PHONE_NUMBER_ID")

    def _validate_phone_number(self, phone: str) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Validate and normalize international phone number.

        Args:
            phone: Phone number to validate (supports international formats)

        Returns:
            Tuple of (is_valid, normalized_phone, error_message)
        """
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)

        # Check for minimum length
        if len(digits) < 10:
            return False, None, f"Invalid phone number length: {len(digits)} digits. Minimum 10 digits required."

        # If already has country code (starts with valid country code digits)
        # India: 91 (12 digits total), US: 1 (11 digits total)
        if len(digits) == 12 and digits.startswith('91'):
            # India number
            normalized = f"+{digits}"
            return True, normalized, None
        elif len(digits) == 11 and digits.startswith('1'):
            # US/Canada number
            normalized = f"+{digits}"
            # Validate US area code
            area_code_first_digit = normalized[2]
            if area_code_first_digit in ['0', '1']:
                return False, None, f"Invalid US area code: {normalized[2:5]}. Area code cannot start with 0 or 1."
            return True, normalized, None
        elif len(digits) == 10:
            # Assume US number without country code
            normalized = f"+1{digits}"
            area_code_first_digit = normalized[2]
            if area_code_first_digit in ['0', '1']:
                return False, None, f"Invalid US area code: {normalized[2:5]}. Area code cannot start with 0 or 1."
            return True, normalized, None
        else:
            # Generic international number - just prepend + if valid length
            if len(digits) >= 10 and len(digits) <= 15:
                normalized = f"+{digits}"
                return True, normalized, None
            else:
                return False, None, f"Invalid phone number length: {len(digits)} digits. Expected 10-15 digits."

    def _run(self, business_data: dict, proposal: str) -> dict:
        """
        Execute the phone call tool.

        Args:
            business_data: Dictionary containing business information
            proposal: The proposal text to discuss

        Returns:
            Dictionary with call results
        """
        # Initialize minimal logging for production
        root_path = Path.cwd()
        debug_file = root_path / "phone_call_debug_detailed.json"
        
        try:
            # Check environment variables
            if not all([self.elevenlabs_api_key, self.elevenlabs_agent_id, self.elevenlabs_phone_number_id]):
                missing = []
                if not self.elevenlabs_api_key:
                    missing.append("ELEVENLABS_API_KEY")
                if not self.elevenlabs_agent_id:
                    missing.append("ELEVENLABS_AGENT_ID")
                if not self.elevenlabs_phone_number_id:
                    missing.append("ELEVENLABS_PHONE_NUMBER_ID")

                error_msg = f"Missing environment variables: {', '.join(missing)}"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "transcript": [],
                    "error": error_msg,
                    "conversation_id": None
                }

            # Extract phone number from business data
            # business_data.get("phone_number") or business_data.get("phone")
            phone = "+918320999207"
            if not phone:
                error_msg = "Phone number not found in business_data"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "transcript": [],
                    "error": error_msg,
                    "conversation_id": None
                }

            # Validate and normalize phone number
            is_valid, normalized_phone, error_msg = self._validate_phone_number(phone)
            if not is_valid:
                logger.error(f"Phone validation failed: {error_msg}")
                return {
                    "status": "error",
                    "transcript": [],
                    "error": error_msg,
                    "conversation_id": None
                }

            logger.info(f"Validated phone number: {normalized_phone}")

            logger.info(f"Initiating call to {normalized_phone}")
            start_time = time.time()
            
            # Run async call in sync context - use asyncio.run for new event loop
            try:
                result = asyncio.run(self._make_call_async(business_data, proposal, normalized_phone))
            except RuntimeError as e:
                if "cannot be called from a running event loop" in str(e):
                    # Fallback: create new thread with new event loop
                    import concurrent.futures
                    import threading
                    
                    def run_in_new_loop():
                        return asyncio.run(self._make_call_async(business_data, proposal, normalized_phone))
                    
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_in_new_loop)
                        result = future.result()
                else:
                    raise

            end_time = time.time()
            
            # Write debug file for production monitoring
            debug_info = {
                "timestamp": datetime.now().isoformat(),
                "business_data": business_data,
                "proposal": proposal,
                "extracted_phone": phone,
                "normalized_phone": normalized_phone,
                "call_result": result,
                "call_duration": end_time - start_time
            }
            
            try:
                with open(debug_file, 'w', encoding='utf-8') as f:
                    json.dump(debug_info, f, indent=2, ensure_ascii=False)
                logger.debug(f"Debug info written to: {debug_file}")
            except Exception as e:
                logger.error(f"Failed to write debug file: {e}")
            
            return result

        except Exception as e:
            error_msg = f"Unexpected error in phone call tool: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "transcript": [],
                "error": error_msg,
                "conversation_id": None
            }

    async def _make_call_async(self, business_data: dict, proposal: str, phone: str) -> dict:
        """
        Make the actual phone call using ElevenLabs API.

        Args:
            business_data: Business information
            proposal: Proposal text
            phone: Validated phone number

        Returns:
            Call result dictionary
        """
        try:
            # Import ElevenLabs SDK
            try:
                from elevenlabs.client import ElevenLabs
                from elevenlabs.conversational_ai.conversation import Conversation
            except ImportError:
                error_msg = "ElevenLabs SDK not installed. Run: pip install elevenlabs"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "transcript": [],
                    "error": error_msg,
                    "conversation_id": None
                }

            # Initialize ElevenLabs client
            client = ElevenLabs(api_key=self.elevenlabs_api_key)

            # Import caller prompt
            from ..prompts.caller_prompts import CALLER_SYSTEM_PROMPT, FIRST_MESSAGE

            # Create a more focused system prompt for the dynamic variables
            focused_prompt = f"""You are Lexi from ZemZen Web Solutions. You are calling {business_data.get('name', 'a business')} about website development opportunities.

BUSINESS INFO: {business_data.get('name', 'Unknown Business')} - {business_data.get('business_type', 'Unknown Type')} in {business_data.get('address', 'Unknown Location')}

PROPOSAL CONTENT: {proposal}

Your job:
1. Introduce yourself as Lexi from ZemZen Web Solutions
2. Mention you've researched their {business_data.get('business_type', 'business')}
3. Highlight that this is a brief call about website opportunities
4. Ask about sending them an email with details
5. Be conversational, friendly, and professional
6. Keep the call under 2 minutes
7. If they say no, thank them politely and end the call

Focus on the specific business benefits for {business_data.get('business_type', 'their industry')}."""

            logger.info(f"Created focused prompt for {business_data.get('name', 'business')}")

            logger.info(f"Initiating call to {phone}")

            # Store transcript messages for real-time capture
            transcript_messages = []

            # Initiate the call
            logger.info(f"Using focused prompt: {focused_prompt[:100]}...")
            logger.info(f"Using first message: {FIRST_MESSAGE}")
            
            # Use the exact ElevenLabs SDK structure you provided
            from elevenlabs.conversational_ai.conversation import Conversation, ConversationInitiationData
            
            conversation_override = {
                "agent": {
                    "prompt": {
                        "prompt": focused_prompt  # Override the system prompt
                    },
                    "first_message": FIRST_MESSAGE,  # Override the first message
                    "language": "en"  # Optional: override the language
                }
            }
            
            # REQUIRED: Dynamic Variables from your ElevenLabs dashboard
            # These MUST be sent or conversation will fail
            dynamic_variables = {
                "agentic": "Sales Agent System",
                "product_or_service": "Website Development Services", 
                "customer_name": business_data.get('name', 'Business Owner'),
                "agent_name": "Lexi",
                "your_company_name": "ZemZen Web Solutions"
            }
            
            config = ConversationInitiationData(
                conversation_config_override=conversation_override,
                dynamic_variables=dynamic_variables  # REQUIRED for production
            )
            
            response = client.conversational_ai.twilio.outbound_call(
                agent_id=self.elevenlabs_agent_id,
                agent_phone_number_id=self.elevenlabs_phone_number_id,
                to_number=phone,
                conversation_initiation_client_data=config
            )

            # Extract conversation ID from response
            # The response might have different attributes depending on SDK version
            conversation_id = None
            if hasattr(response, 'conversation_id'):
                conversation_id = response.conversation_id
            elif hasattr(response, 'id'):
                conversation_id = response.id
            elif hasattr(response, 'call_id'):
                conversation_id = response.call_id
            else:
                # Try to extract from response dict/object
                logger.info(f"Response type: {type(response)}, Response: {response}")
                if hasattr(response, '__dict__'):
                    logger.info(f"Response attributes: {response.__dict__}")

            logger.info(f"Call initiated. Conversation ID: {conversation_id}")

            # Poll for conversation status
            max_attempts = 60  # 1 minute with 1-second intervals (enough time for ring + answer)
            attempt = 0

            while attempt < max_attempts:
                await asyncio.sleep(1)
                attempt += 1

                try:
                    # Get conversation status
                    conversation = client.conversational_ai.conversations.get(conversation_id=conversation_id)
                    status = conversation.status

                    logger.info(f"Polling attempt {attempt}: Status = {status}")
                    
                    # Debug: Log conversation details occasionally for troubleshooting
                    if attempt == 1 or attempt % 10 == 0:  # Log every 10th attempt after first
                        logger.debug(f"Debug - Status: {status}, Attempt: {attempt}, Transcript: {len(conversation.transcript) if conversation.transcript else 0} messages")
                    
                    # Capture transcript messages in real-time
                    if hasattr(conversation, 'transcript') and conversation.transcript:
                        turns = (
                            getattr(conversation, "transcript", None)
                            or getattr(conversation, "turns", None)
                            or []
                        )
                        # Update transcript_messages with latest conversation data
                        transcript_messages = []
                        for t in turns:
                            role = getattr(t, "role", "unknown")
                            msg = (
                                t.message if hasattr(t, "message") else
                                getattr(t, "text", "unknown")
                            )
                            if hasattr(msg, "text"):
                                msg = msg.text
                            transcript_messages.append({"role": role, "message": msg})

                    if status in ["in-progress"]:
                        # Call is active, continue polling but don't timeout quickly
                        # Wait a bit longer for conversation to finish
                        if attempt > 40:  # After 40 seconds of being in-progress
                            logger.info(f"Call was active for {attempt} seconds. Returning current transcript.")
                            return {
                                "status": "done",
                                "transcript": transcript_messages,
                                "conversation_id": conversation_id,
                                "error": None,
                                "note": f"Call was in progress for {attempt} seconds. May have been cut short due to timeout."
                            }

                    if status in ["done", "completed"]:
                        logger.info(f"Call completed successfully. Transcript length: {len(transcript_messages)}")

                        return {
                            "status": "done",
                            "transcript": transcript_messages,
                            "conversation_id": conversation_id,
                            "error": None
                        }

                    elif status in ["no_answer", "busy", "rejected", "declined"]:
                        error_msg = f"Call {status}. No conversation took place."
                        logger.info(f"Call ended with status: {status}")

                        return {
                            "status": "no_answer",
                            "transcript": [],
                            "conversation_id": conversation_id,
                            "error": error_msg
                        }

                    elif status in ["failed", "error"]:
                        error_msg = f"Call failed with status: {status}"
                        logger.error(error_msg)

                        return {
                            "status": "failed",
                            "transcript": [],
                            "conversation_id": conversation_id,
                            "error": error_msg
                        }

                except Exception as poll_error:
                    logger.warning(f"Error polling conversation: {str(poll_error)}")
                    continue

            # Timeout
            error_msg = "Call status polling timeout (1 minute)"
            logger.error(error_msg)
            return {
                "status": "error",
                "transcript": [],
                "conversation_id": conversation_id,
                "error": error_msg
            }

        except Exception as e:
            error_msg = f"Error making call: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "transcript": [],
                "error": error_msg,
                "conversation_id": None
            }


# Singleton instance - can be created with custom parameters
def create_phone_call_tool(**kwargs):
    """Create a phone call tool instance with optional custom parameters."""
    return PhoneCallTool(**kwargs)

# Default singleton instance
phone_call_tool = PhoneCallTool()
