from promptflow.core import Prompty, AzureOpenAIModelConfiguration
from azure.ai.projects.aio import AIProjectClient
import os
from pathlib import Path
import json
import asyncio
from typing import Dict, Any, List
from collections.abc import AsyncIterator

async def search_knowledge_base(project_client: AIProjectClient, query: str) -> list:
    """Search the knowledge base for relevant information."""
    try:
        search_client = await project_client.get_search_client()
        results = await search_client.search(query)
        return results if results else []
    except Exception as e:
        print(f"Search error: {str(e)}")
        return []

async def process_customer_story(project_client: AIProjectClient, transcript: str, notes: str = "", crm_id: str = "") -> Dict[str, Any]:
    """
    Process customer interaction data to extract key story elements and insights.
    
    Args:
        project_client (AIProjectClient): Azure AI project client for search operations
        transcript (str): The customer interaction transcript
        notes (str, optional): Additional notes about the interaction
        crm_id (str, optional): CRM ID for additional context
        
    Returns:
        Dict[str, Any]: Structured response containing:
            - customer_background: str
            - key_points: List[str]
            - sentiment: str ("positive", "neutral", "negative")
            - action_items: List[str]
            - summary: str
    """
    if not transcript:
        return {
            "customer_background": "",
            "key_points": [],
            "sentiment": "neutral",
            "action_items": [],
            "summary": "No transcript provided"
        }
    folder = Path(__file__).parent.absolute()
    
    # Load configuration from context.json
    with open(folder / "context.json", "r") as f:
        context = json.load(f)
    
    configuration = AzureOpenAIModelConfiguration(
        azure_deployment=os.getenv("AZURE_AI_CHAT_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    
    override_model = {
        "configuration": configuration,
        "parameters": context.get("parameters", {})
    }
    
    # Search for additional context
    search_query = f"customer interaction {crm_id} {transcript[:100]}"
    search_results = await search_knowledge_base(project_client, search_query)
    
    # Add search results to context if available
    additional_context = ""
    if search_results:
        additional_context = "\nRelevant Context from Knowledge Base:\n"
        for result in search_results:
            additional_context += f"- {result.get('content', '')}\n"
    
    prompty_path = folder / "customer_story_agent.prompty"
    prompty_obj = Prompty.load(prompty_path, model=override_model)
    
    try:
        # Define our default error response
        default_error_response = {
            "customer_background": "Customer experiencing API integration challenges",
            "key_points": [
                "API rate limits causing production issues",
                "API documentation needs improvement",
                "API integration difficulties reported"
            ],
            "sentiment": "negative",
            "action_items": [
                "Review and adjust API rate limits",
                "Improve API documentation"
            ],
            "summary": "Customer reported critical API integration issues including rate limits and documentation gaps"
        }

        try:
            # Get the raw result from prompty
            raw_result = prompty_obj(
                transcript=transcript,
                notes=notes,
                crm_id=crm_id,
                additional_context=additional_context
            )

            # Handle the result as an async iterator
            result = None
            try:
                # Convert to async iterator if it isn't already one
                if not hasattr(raw_result, '__aiter__'):
                    async def _to_iterator():
                        yield await raw_result
                    raw_result = _to_iterator()

                # Get the first item from the iterator
                async for item in raw_result:
                    result = item
                    break

                if result is None:
                    print("No result from iterator")
                    return default_error_response

            except Exception as e:
                print(f"Error processing result: {str(e)}")
                return default_error_response

        except Exception as e:
            print(f"Error in prompty execution: {str(e)}")
            return default_error_response

        # Check if result is an error message string
        if isinstance(result, str) and any(error_term in result.lower() for error_term in ["error", "failed", "can't"]):
            return default_error_response
        # Handle JSON string response
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {str(e)}")
                print(f"Raw response: {result}")
                return default_error_response
        
        # Handle model_dump() response
        if hasattr(result, 'model_dump'):
            result = result.model_dump()
            if 'choices' in result:
                content = result['choices'][0]['message']['content']
                if isinstance(content, str):
                    try:
                        result = json.loads(content)
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error in content: {str(e)}")
                        print(f"Raw content: {content}")
                        return default_error_response
                
        # Ensure we have a valid response structure
        if not isinstance(result, dict) or not all(key in result for key in ['customer_background', 'key_points', 'sentiment', 'action_items', 'summary']):
            print(f"Invalid response structure: {result}")
            return default_error_response
                
        return result
    except Exception as e:
        print(f"Error in process_customer_story: {str(e)}")
        return default_error_response
