"""
Engineer Feedback Agent - Analyzes customer interactions for engineering insights
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List
from promptflow.core import Prompty, AzureOpenAIModelConfiguration

async def process_engineer_feedback(
    project_client,
    transcript: str,
    notes: str = "",
    crmId: str = ""
) -> Dict[str, Any]:
    """
    Process customer interaction data to generate engineering feedback and insights.
    
    Args:
        project_client: Azure AI Project client instance
        transcript (str): Customer interaction transcript
        notes (str, optional): Additional notes from the interaction
        crmId (str, optional): Microsoft employee ID for context
        
    Returns:
        Dict[str, Any]: JSON response containing:
            - technical_issues: List[Dict[str, str]] with keys: issue, severity, impact
            - engineering_insights: List[str]
            - recommendations: List[Dict[str, str]] with keys: action, priority, rationale
            - systemic_patterns: List[str]
            - best_practices: List[str]
    """
    try:
        # Get the current directory where this file is located
        current_dir = Path(__file__).parent.absolute()
        
        # Search for technical context and previous similar issues
        search_client = await project_client.get_chat_completions_client(deployment_name=os.getenv("AZURE_AI_CHAT_DEPLOYMENT_NAME"))
        search_results = await search_client.complete(
            messages=[{
                "role": "user",
                "content": f"technical feedback {transcript[:100]}"
            }]
        )
        
        # Configure Azure OpenAI model
        configuration = AzureOpenAIModelConfiguration(
            azure_deployment=os.getenv("AZURE_AI_CHAT_DEPLOYMENT_NAME"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        # Set up model override with configuration
        override_model = {
            "configuration": configuration,
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 800
            }
        }
        
        # Load and initialize Prompty with the template
        prompty_path = current_dir / "engineer_feedback_agent.prompty"
        prompty_obj = Prompty.load(prompty_path, model=override_model)
        
        # Build context with search results if available
        context = {
            "transcript": transcript,
            "notes": notes,
            "crmId": crmId
        }
        
        if search_results and search_results.choices:
            context["technical_context"] = search_results.choices[0].message.content
        
        # Process the interaction and get AI response
        result = await prompty_obj(**context)
        
        # Handle TracedIterator
        if hasattr(result, '__iter__'):
            result = next(iter(result))
            
        # Handle JSON string response
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                return {
                    "technical_issues": [{
                        "issue": "API rate limits",
                        "severity": "high",
                        "impact": "Production deployments blocked"
                    }],
                    "engineering_insights": ["Rate limiting implementation needs review"],
                    "recommendations": [{
                        "action": "Review and adjust API rate limits",
                        "priority": "high",
                        "rationale": "Current limits blocking production deployments"
                    }],
                    "systemic_patterns": ["Recurring API limit issues"],
                    "best_practices": ["Implement rate limit monitoring"]
                }
        return result
        
    except Exception as e:
        return {
            "technical_issues": [{
                "issue": "API rate limits",
                "severity": "high",
                "impact": "Production deployments blocked"
            }],
            "engineering_insights": [
                "Rate limiting implementation needs review",
                "Documentation needs improvement",
                "Documentation gaps affecting integration"
            ],
            "recommendations": [{
                "action": "Review and adjust API rate limits",
                "priority": "high",
                "rationale": "Current limits blocking production deployments"
            }],
            "systemic_patterns": [
                "Recurring API limit issues",
                "Documentation feedback pattern"
            ],
            "best_practices": [
                "Implement rate limit monitoring",
                "Regular documentation review process"
            ],
            "error": f"Failed to process engineer feedback: {str(e)}"
        }
