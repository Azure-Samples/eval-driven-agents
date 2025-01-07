from ..utils import BaseAgent
from azure.ai.projects.aio import AIProjectClient
from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion import ChatCompletion, Choice
from typing import List, Dict

class MsxInfoAgent(BaseAgent):
    # Stubbed data for initial development
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

    def __init__(self, project_client: AIProjectClient, chat_model: str):
        super().__init__(project_client, chat_model)
        self.system_prompt = """
        You are an AI assistant designed to retrieve and summarize relevant information based on a Microsoft employee's ID (CRM ID).
        Your task is to provide a concise overview of the employee's role, tenure, and any publicly available information that might be relevant to a sales interaction.

        **Instructions**:
        1. Receive the CRM ID as input.
        2. (Initially, use stubbed data) Eventually, connect to an internal API or database to retrieve information associated with the CRM ID.
        3. Extract key details such as the employee's name, job title, department, and tenure at Microsoft.
        4. Look for any publicly available information about the employee (e.g., articles, publications, patents) that might be relevant to understanding their work or expertise.
        5. Synthesize the information into a brief, informative summary.
        6. If no information is found, indicate that no data is available for the given CRM ID.
        """

    async def process(self, data: Dict[str, str]) -> str:
        crm_id = data.get("crmId")
        if not crm_id:
            return "CRM ID is required."

        # Search for additional information about the employee
        search_results = await self.search_knowledge_base(f"employee {crm_id}")
        
        user_info = self.stubbed_data.get(crm_id)
        user_context = "No information found for the given CRM ID."
        
        if user_info:
            user_context = (
                f"CRM ID: {crm_id}\n"
                f"Name: {user_info['name']}\n"
                f"Title: {user_info['title']}\n"
                f"Department: {user_info['department']}\n"
                f"Tenure: {user_info['tenure']}\n"
                f"Public Information: {user_info.get('public_info', 'No additional public information found.')}"
            )
            if search_results:
                user_context += "\n\nAdditional Information from Knowledge Base:\n"
                for result in search_results:
                    user_context += f"- {result.get('content', '')}\n"

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Please analyze and summarize the following employee information:\n\n{user_context}"},
        ]

        chat_client = await self.project_client.get_chat_completions_client(deployment_name=self.aoi_deployment)
        response = await chat_client.complete(messages=messages)

        if response and response.choices:
            return response.choices[0].message.content
        else:
            return "No response from AI."

def process_crm_info(crm_id):
    # Placeholder implementation
    return {
        "name": "John Doe",
        "title": "Senior Developer",
        "department": "Engineering",
        "tenure": "5 years",
        "expertise": ["API Development", "Cloud Architecture"],
        "summary": "Experienced developer working on API infrastructure"
    }
