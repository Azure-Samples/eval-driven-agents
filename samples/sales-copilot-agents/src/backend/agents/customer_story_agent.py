from ..utils import BaseAgent
from azure.ai.projects.aio import AIProjectClient
from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion import ChatCompletion, Choice
from typing import List, Dict

class CustomerStoryAgent(BaseAgent):
    def __init__(self, project_client: AIProjectClient, chat_model: str):
        super().__init__(project_client, chat_model)
        self.system_prompt = """
        You are an AI assistant specialized in crafting compelling customer stories from sales interactions.
        Your goal is to highlight the customer's journey, their challenges, and how our solutions address their needs.
        Use a narrative format that is engaging and easy to follow.

        **Instructions**:
        1. Analyze the provided meeting transcript, notes, and CRM ID information.
        2. Identify the customer's key challenges, needs, and goals.
        3. Describe how our product or service addresses these needs.
        4. Highlight any positive outcomes or successes mentioned.
        5. If relevant, incorporate brief information found through Bing Search about the customer (based on keywords from the interaction).
        6. Craft a concise and impactful customer story that can be used for internal training or marketing purposes.
        """
    async def process(self, data: Dict[str, str]) -> str:
        # Search for additional context about the customer interaction
        search_results = await self.search_knowledge_base(
            f"customer interaction {data.get('crmId', '')} {data.get('transcript', '')[:100]}"
        )
        
        context = f"Meeting Transcript: {data.get('transcript', '')}\nNotes: {data.get('notes', '')}\nCRM ID: {data.get('crmId', '')}"
        
        if search_results:
            context += "\n\nRelevant Context from Knowledge Base:\n"
            for result in search_results:
                context += f"- {result.get('content', '')}\n"

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": context},
        ]

        chat_client = await self.project_client.get_chat_completions_client(deployment_name=self.aoi_deployment)
        response = await chat_client.complete(messages=messages)

        if response and response.choices:
            return response.choices[0].message.content
        else:
            return "No response from AI."

async def process_customer_story(project_client, transcript, notes, crm_id):
    # Placeholder implementation
    return {
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
