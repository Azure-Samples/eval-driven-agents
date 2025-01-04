from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MockChatCompletionsClient:
    """Mock chat completions client for development."""
    
    async def complete(self, messages: list, **kwargs) -> Dict[str, Any]:
        """Mock completion method."""
        logger.info("Mock chat completion called with messages: %s", messages)
        return {
            "choices": [{
                "message": {
                    "content": "This is a mock response from the development environment."
                }
            }]
        }

class MockAIProjectClient:
    """Mock client for development when Azure credentials are not available."""
    
    def __init__(self):
        self.chat_client = MockChatCompletionsClient()
        logger.info("Initialized mock AI Project client")
    
    @classmethod
    def from_connection_string(cls, credential: Any, conn_str: str) -> 'MockAIProjectClient':
        """Mock the connection string initialization method."""
        logger.info("Creating mock client from connection string: %s", conn_str)
        return cls()
        
    async def get_chat_completions_client(self, deployment_name: str) -> MockChatCompletionsClient:
        """Get a mock chat completions client."""
        logger.info("Getting mock chat completions client for deployment: %s", deployment_name)
        return self.chat_client

    async def complete(self, *args, **kwargs) -> Dict[str, Any]:
        """Direct completion method for compatibility."""
        return await self.chat_client.complete(*args, **kwargs)

    @property
    def endpoint(self) -> str:
        """Mock endpoint property."""
        return "http://localhost:8000"

    @property
    def api_key(self) -> str:
        """Mock API key property."""
        return "mock-api-key"

    @property
    def credential(self) -> Any:
        """Mock credential property."""
        return None 