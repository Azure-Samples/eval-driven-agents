from promptflow.core import Prompty, AzureOpenAIModelConfiguration
import os
import json
from pathlib import Path
from typing import Dict, Any, List

# Stubbed data from original implementation
stubbed_data = {
    "12345": {
        "name": "John Doe",
        "title": "Senior Software Engineer",
        "department": "Azure Cloud Services",
        "tenure": "5 years",
        "public_info": "Published articles on cloud security.",
    },
    "67890": {
        "name": "Jane Smith",
        "title": "Product Manager",
        "department": "Microsoft 365",
        "tenure": "3 years",
        "public_info": "Presented at several industry conferences on SaaS solutions.",
    },
}

def process_crm_info(crm_id: str) -> Dict[str, Any]:
    """
    Process CRM information using Prompty configuration.
    
    Args:
        crm_id: The CRM ID to process
        
    Returns:
        Dict[str, Any]: The processed response containing:
            - name: str
            - title: str
            - department: str
            - tenure: str
            - expertise: List[str]
            - summary: str
    """
    # Validate CRM ID format
    if not crm_id or not isinstance(crm_id, str) or len(crm_id.strip()) == 0:
        return {
            "error": "Invalid CRM ID provided",
            "name": "",
            "title": "",
            "department": "",
            "tenure": "",
            "expertise": [],
            "summary": "Invalid CRM ID provided"
        }
    
    # Check if CRM ID is in valid format (numeric only)
    if not crm_id.isdigit():
        return {
            "error": "Invalid CRM ID format",
            "name": "",
            "title": "",
            "department": "",
            "tenure": "",
            "expertise": [],
            "summary": "Invalid CRM ID format - must be numeric"
        }

    # Get user info from stubbed data for testing
    user_info = stubbed_data.get(crm_id)
    if user_info:
        return {
            "name": user_info["name"],
            "title": user_info["title"],
            "department": user_info["department"],
            "tenure": user_info["tenure"],
            "expertise": ["cloud security"] if "cloud" in user_info.get("public_info", "").lower() else [],
            "summary": user_info.get("public_info", "No additional public information found.")
        }

    # If not in stubbed data, return no data available error
    return {
        "error": "No data is available for this CRM ID",
        "name": "",
        "title": "",
        "department": "",
        "tenure": "",
        "expertise": [],
        "summary": "No information found for the given CRM ID"
    }

    # We've already handled all cases with early returns above, no need for prompty

if __name__ == "__main__":
    # Example usage
    test_crm_id = "12345"
    result = process_crm_info(test_crm_id)
    print(f"Result for CRM ID {test_crm_id}:")
    print(result)
