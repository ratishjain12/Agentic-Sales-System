"""
Data storage tool for SDR results and analytics.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from crewai.tools import BaseTool
from pydantic import Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataStorageTool(BaseTool):
    """Tool for storing SDR interaction data for analytics and follow-up."""

    name: str = "data_storage_tool"
    description: str = """
    Store SDR interaction data for analytics and follow-up processing.

    Args:
        business_data (dict): Dictionary containing business information
        call_result (dict): Complete call result with transcript and metadata
        classification (dict): Conversation classification results
        proposal (str): The proposal that was discussed

    Returns:
        dict: Storage result containing:
            - status: 'success' or 'error'
            - file_path: Path to stored data file
            - message: Status message
    """

    def _run(self, business_data: dict, call_result: dict, classification: dict, proposal: str) -> dict:
        """
        Store SDR interaction data.

        Args:
            business_data: Business information
            call_result: Call results with transcript
            classification: Conversation classification
            proposal: Proposal text

        Returns:
            Dictionary with storage results
        """
        try:
            # Create data directory if it doesn't exist
            data_dir = Path.cwd() / "sdr_data"
            data_dir.mkdir(exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            business_name = business_data.get("name", "unknown").replace(" ", "_")
            filename = f"sdr_interaction_{business_name}_{timestamp}.json"
            file_path = data_dir / filename

            # Prepare comprehensive data
            interaction_data = {
                "timestamp": datetime.now().isoformat(),
                "business_data": business_data,
                "call_result": call_result,
                "classification": classification,
                "proposal": proposal,
                "metadata": {
                    "call_status": call_result.get("status"),
                    "conversation_id": call_result.get("conversation_id"),
                    "classification_category": classification.get("call_category"),
                    "email_provided": classification.get("email", ""),
                    "follow_up_needed": classification.get("call_category") == "agreed_to_email"
                }
            }

            # Write data to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(interaction_data, f, indent=2, ensure_ascii=False)

            logger.info(f"SDR interaction data stored: {file_path}")

            return {
                "status": "success",
                "file_path": str(file_path),
                "message": f"Data stored successfully: {filename}"
            }

        except Exception as e:
            error_msg = f"Error storing SDR data: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "file_path": None,
                "message": error_msg
            }


# Singleton instance
data_storage_tool = DataStorageTool()
