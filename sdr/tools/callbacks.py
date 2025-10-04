"""
Callbacks for phone call tool validation and duplicate prevention.
"""
import logging
from typing import Dict, Any, Optional
from crewai.tools import BaseTool

logger = logging.getLogger(__name__)


def validate_phone_number_callback(tool: BaseTool, args: Dict[str, Any]) -> Optional[Dict]:
    """
    Before-tool callback to validate phone number format.
    
    Args:
        tool: The tool being called
        args: Arguments passed to the tool
        
    Returns:
        None if validation passes, dict with error if validation fails
    """
    # Only apply to phone call tool
    if tool.name != "phone_call_tool":
        return None
    
    # Extract phone number from business_data
    business_data = args.get("business_data", {})
    phone = business_data.get("phone_number") or business_data.get("phone")
    
    if not phone:
        logger.error("No phone number found in business_data")
        return {
            "status": "error",
            "error": "Phone number not found in business_data",
            "transcript": [],
            "conversation_id": None
        }
    
    # Use the tool's validation method
    is_valid, normalized, error_msg = tool._validate_phone_number(phone)
    
    if not is_valid:
        logger.error(f"Phone validation failed: {error_msg}")
        return {
            "status": "error",
            "error": error_msg,
            "transcript": [],
            "conversation_id": None
        }
    
    # Update the phone number in business_data with normalized version
    if normalized != phone:
        logger.info(f"Phone number normalized: {phone} -> {normalized}")
        if "phone_number" in business_data:
            business_data["phone_number"] = normalized
        if "phone" in business_data:
            business_data["phone"] = normalized
    
    return None  # Proceed with tool execution


def prevent_duplicate_call_callback(tool: BaseTool, args: Dict[str, Any]) -> Optional[Dict]:
    """
    Before-tool callback to prevent duplicate calls.
    
    Args:
        tool: The tool being called
        args: Arguments passed to the tool
        
    Returns:
        None if no duplicate found, dict with cached result if duplicate exists
    """
    # Only apply to phone call tool
    if tool.name != "phone_call_tool":
        return None
    
    # Check if we have a cached result (this would need to be implemented
    # with a proper caching mechanism in a real implementation)
    # For now, this is a placeholder for the callback structure
    
    logger.info("Checking for duplicate calls...")
    return None  # Proceed with tool execution
