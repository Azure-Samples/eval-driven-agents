import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from azure.ai.projects import AIProjectClient
from typing import Dict
import base64
import json

from api.main import create_app
from api.agents.crm_info_agent.crm_info_agent import process_crm_info
from api.agents.customer_story_agent.customer_story_agent import process_customer_story
from api.agents.engineer_feedback_agent.engineer_feedback_agent import process_engineer_feedback

# Stubbed CRM data for testing
CRM_STUB_DATA: Dict[str, Dict[str, str]] = {
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

@pytest.fixture(autouse=True)
def mock_openai():
    """Mock OpenAI client initialization."""
    import json
    
    def create_mock_response(messages):
        # Determine response based on message content
        system_content = messages[0]["content"].lower() if messages else ""
        user_content = messages[1]["content"].lower() if len(messages) > 1 else ""
        
        if "crm id" in system_content:
            if "12345" in user_content:
                content = {
                    "name": "John Doe",
                    "title": "Senior Software Engineer",
                    "department": "Azure Cloud Services",
                    "tenure": "5 years",
                    "expertise": ["cloud security", "Azure services"],
                    "summary": "Senior Software Engineer in Azure Cloud Services with 5 years experience and expertise in cloud security."
                }
            else:
                content = {
                    "error": "No data is available for this CRM ID."
                }
        elif "customer story" in system_content:
            content = {
                "customer_background": "Enterprise customer experiencing API integration challenges",
                "key_points": [
                    "API rate limits",
                    "Documentation quality needs improvement",
                    "Urgent resolution needed for production deployment"
                ],
                "sentiment": "negative",
                "action_items": [
                    "Review and adjust API rate limits",
                    "Update technical documentation",
                    "Schedule follow-up for deployment support"
                ],
                "summary": "Customer facing critical API rate limit issues and documentation gaps affecting production deployment."
            }
        elif "engineer feedback" in system_content:
            content = {
                "technical_issues": [
                    {
                        "issue": "api rate limits",
                        "severity": "high",
                        "impact": "Production deployments blocked"
                    }
                ],
                "engineering_insights": [
                    "Rate limiting implementation needs review",
                    "Documentation needs improvement",
                    "Documentation gaps affecting integration"
                ],
                "recommendations": [
                    {
                        "action": "Review and adjust API rate limits",
                        "priority": "high",
                        "rationale": "Current limits blocking production deployments"
                    }
                ],
                "systemic_patterns": [
                    "Recurring API limit issues",
                    "Documentation feedback pattern"
                ],
                "best_practices": [
                    "Implement rate limit monitoring",
                    "Regular documentation review process"
                ]
            }
        else:
            content = json.dumps({
                "analysis": "Mock response: Analyzed the provided information and generated insights."
            })
        
        return type('Response', (), {
            'model_dump': lambda: {
                'id': 'chatcmpl-mock',
                'object': 'chat.completion',
                'created': 1677652288,
                'model': 'gpt-4',
                'choices': [{
                    'index': 0,
                    'message': {
                        'role': 'assistant',
                        'content': content
                    },
                    'finish_reason': 'stop'
                }],
                'usage': {
                    'prompt_tokens': 9,
                    'completion_tokens': 12,
                    'total_tokens': 21
                }
            }
        })()

    with patch('openai.OpenAI') as mock_openai, \
         patch('openai.AzureOpenAI') as mock_azure_openai, \
         patch('openai.AsyncOpenAI') as mock_async_openai, \
         patch('openai.AsyncAzureOpenAI') as mock_async_azure_openai:
        
        for mock_client in [mock_openai, mock_azure_openai, mock_async_openai, mock_async_azure_openai]:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.side_effect = \
                lambda messages, **kwargs: create_mock_response(messages)
            mock_client.return_value = mock_instance
        
        yield {
            'openai': mock_openai,
            'azure_openai': mock_azure_openai,
            'async_openai': mock_async_openai,
            'async_azure_openai': mock_async_azure_openai
        }

@pytest.fixture
def test_client(mock_project_client):
    app = create_app()
    
    # Initialize Azure credentials and clients
    app.state.project_client = mock_project_client
    
    return TestClient(app)

class MockChatClient:
    async def complete(self, messages):
        import json
        user_content = messages[1]["content"].lower() if len(messages) > 1 else ""
        system_content = messages[0]["content"].lower() if messages else ""
        
        # Create mock response based on content
        if "crm id" in system_content:
            if "12345" in user_content:
                response_data = {
                    "name": "John Doe",
                    "title": "Senior Software Engineer",
                    "department": "Azure Cloud Services",
                    "tenure": "5 years",
                    "expertise": ["cloud security", "Azure services"],
                    "summary": "Senior Software Engineer in Azure Cloud Services with 5 years experience and expertise in cloud security."
                }
            else:
                response_data = {
                    "error": "No data is available for this CRM ID."
                }
        elif "customer story" in system_content:
            response_data = {
                "customer_background": "Enterprise customer experiencing API integration challenges",
                "key_points": [
                    "API rate limits",
                    "Documentation quality needs improvement",
                    "Urgent resolution needed for production deployment"
                ],
                "sentiment": "negative",
                "action_items": [
                    "Review and adjust API rate limits",
                    "Update technical documentation",
                    "Schedule follow-up for deployment support"
                ],
                "summary": "Customer facing critical API rate limit issues and documentation gaps affecting production deployment."
            }
        elif "engineer feedback" in system_content:
            response_data = {
                "technical_issues": [
                    {
                        "issue": "api rate limits",
                        "severity": "high",
                        "impact": "Production deployments blocked"
                    }
                ],
                "engineering_insights": [
                    "Rate limiting implementation needs review",
                    "Documentation needs improvement",
                    "Documentation gaps affecting integration"
                ],
                "recommendations": [
                    {
                        "action": "Review and adjust API rate limits",
                        "priority": "high",
                        "rationale": "Current limits blocking production deployments"
                    }
                ],
                "systemic_patterns": [
                    "Recurring API limit issues",
                    "Documentation feedback pattern"
                ],
                "best_practices": [
                    "Implement rate limit monitoring",
                    "Regular documentation review process"
                ]
            }
        else:
            response_data = {
                "analysis": "Mock response: Analyzed the provided information and generated insights."
            }
            
        # Create a mock response object that returns a JSON string
        class MockResponse:
            def __init__(self, data):
                self.choices = [type('Choice', (), {
                    'message': type('Message', (), {
                        'content': data
                    })
                })]
                
            async def __aiter__(self):
                yield self
                
            def model_dump(self):
                return {
                    'id': 'chatcmpl-mock',
                    'object': 'chat.completion',
                    'created': 1677652288,
                    'model': 'gpt-4',
                    'choices': [{
                        'index': 0,
                        'message': {
                            'role': 'assistant',
                            'content': response_data
                        },
                        'finish_reason': 'stop'
                    }],
                    'usage': {
                        'prompt_tokens': 9,
                        'completion_tokens': 12,
                        'total_tokens': 21
                    }
                }
                
        return MockResponse(response_data)

@pytest.fixture
def mock_project_client():
    mock_client = type('MockProjectClient', (), {
        'endpoint': 'https://mock-endpoint.openai.azure.com',
        'api_key': 'mock-api-key-12345',
        'connection_string': 'mock-connection-string',
        'credential': 'mock-credential'
    })()
    mock_chat_client = MockChatClient()
    
    async def get_chat_completions_client(deployment_name=None):
        return mock_chat_client
    
    mock_client.get_chat_completions_client = get_chat_completions_client
    
    # Add async context manager support to mock chat client
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        
    mock_chat_client.__aenter__ = __aenter__
    mock_chat_client.__aexit__ = __aexit__
    
    class MockSearchClient:
        async def search(self, query, **kwargs):
            # Return mock search results based on query
            if "crm" in query.lower():
                return [{
                    "id": "12345",
                    "content": json.dumps({
                        "name": "John Doe",
                        "title": "Senior Software Engineer",
                        "department": "Azure Cloud Services",
                        "tenure": "5 years",
                        "expertise": ["cloud security", "Azure services"],
                        "summary": "Senior engineer with cloud expertise"
                    }),
                    "score": 0.95
                }]
            elif "customer" in query.lower():
                return [{
                    "id": "67890",
                    "content": json.dumps({
                        "customer_background": "Enterprise customer experiencing API issues",
                        "key_points": ["API rate limits causing issues"],
                        "sentiment": "negative",
                        "action_items": ["Review API limits"],
                        "summary": "Customer facing API rate limit issues"
                    }),
                    "score": 0.90
                }]
            return []
        
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    async def get_search_client():
        return MockSearchClient()
    
    mock_client.get_search_client = get_search_client
    return mock_client

# CRM info agent fixture removed as it's now a standalone function

# Customer story agent fixture removed as it's now a standalone function

# Engineer feedback agent is now a standalone function, no fixture needed

@pytest.fixture
def sample_input_data():
    # Base64 encode the input strings
    transcript = base64.b64encode(
        "Customer mentioned issues with api rate limits and need for better documentation.".encode()
    ).decode()
    notes = base64.b64encode(
        "Priority: High\nCustomer needs immediate resolution for production deployment.".encode()
    ).decode()
    return {
        "transcript": transcript,
        "notes": notes,
        "crmId": "12345"
    }

@pytest.fixture
def sample_base64_data():
    return {
        "transcript": "Q3VzdG9tZXIgbWVudGlvbmVkIGlzc3VlcyB3aXRoIEFQSSByYXRlIGxpbWl0cy4=",  # base64 encoded
        "notes": "UHJpb3JpdHk6IEhpZ2gKQ3VzdG9tZXIgbmVlZHMgaW1tZWRpYXRlIHJlc29sdXRpb24u",  # base64 encoded
        "crmId": "67890"
    }

@pytest.fixture
def sample_missing_fields():
    return {
        "transcript": base64.b64encode(b"Customer mentioned issues with api rate limits.").decode(),
        "crmId": "12345"
        # notes field missing
    }
