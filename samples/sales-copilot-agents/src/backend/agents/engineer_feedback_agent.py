from ..utils import BaseAgent
from azure.ai.projects.aio import AIProjectClient
from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion import ChatCompletion, Choice
from typing import List, Dict

class EngineerFeedbackAgent(BaseAgent):
    def __init__(self, project_client: AIProjectClient, chat_model: str):
        super().__init__(project_client, chat_model)
        self.system_prompt = """
        You are an AI assistant designed to analyze customer interactions and provide concise, actionable feedback for engineers.
        Focus on technical aspects, product improvement suggestions, and identifying customer pain points.
        Be direct and specific in your feedback.

        **Instructions**:
        1. Analyze the provided meeting transcript and notes.
        2. Extract key technical details, customer feedback, and potential issues.
        3. Provide specific suggestions for engineers to address these points.
        4. Prioritize feedback based on impact and feasibility.
        5. If CRM ID is available, look for related information to that user.
        6. Output should be formatted for readability, using bullet points or numbered lists where appropriate.
        """

    async def process(self, data: Dict[str, str]) -> str:
        # Search for technical context and previous similar issues
        search_results = await self.search_knowledge_base(
            f"technical feedback {data.get('transcript', '')[:100]}"
        )
        
        context = f"Meeting Transcript: {data.get('transcript', '')}\nNotes: {data.get('notes', '')}\nCRM ID: {data.get('crmId', '')}"
        
        if search_results:
            context += "\n\nRelevant Technical Context:\n"
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

async def process_engineer_feedback(project_client, transcript, notes, crm_id):
    # Placeholder implementation
    return {
        "technical_issues": [{
            "issue": "api rate limits",
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
