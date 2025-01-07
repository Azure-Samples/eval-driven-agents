from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import logging
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def decode_base64(text: str) -> str:
    """Decode base64 encoded text."""
    try:
        # Add padding if necessary
        padding = 4 - (len(text) % 4)
        if padding != 4:
            text += '=' * padding

        # Try to decode as base64
        decoded = base64.b64decode(text.encode('utf-8')).decode('utf-8')
        return decoded
    except Exception as e:
        logger.error(f"Base64 decoding error: {e}")
        raise ValueError(f"Invalid base64 encoding: {str(e)}")

def validate_input(data: Dict[str, Any]) -> Optional[str]:
    """Validate input data for analysis."""
    try:
        # Check required fields
        if not data.get("transcript"):
            return "Missing required field: transcript"
        
        # Check for empty strings after trimming
        if not data.get("transcript", "").strip():
            return "Transcript cannot be empty"
        
        # Check input size limits (1MB total)
        total_size = sum(len(str(v)) for v in data.values())
        if total_size > 1000000:
            return "Input too large: maximum total size is 1MB"
        
        return None
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return f"Validation error: {str(e)}"

def format_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Format the response data for consistency."""
    try:
        return {
            "engineering_feedback": data.get("engineering_feedback", {
                "technical_issues": [],
                "engineering_insights": [],
                "recommendations": [],
                "systemic_patterns": [],
                "best_practices": []
            }),
            "customer_story": data.get("customer_story", {
                "customer_background": "",
                "key_points": [],
                "sentiment": "neutral",
                "action_items": [],
                "summary": ""
            }),
            "crm_info": data.get("crm_info", {
                "name": "",
                "title": "",
                "department": "",
                "tenure": "",
                "expertise": [],
                "summary": ""
            })
        }
    except Exception as e:
        logger.error(f"Response formatting error: {e}")
        return {
            "error": "Failed to format response",
            "details": str(e)
        }

class BaseAgent:
    """Base class for all agents with common functionality."""
    def __init__(self, project_client):
        self.project_client = project_client

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the input data. To be implemented by child classes."""
        raise NotImplementedError("Subclasses must implement process()")
