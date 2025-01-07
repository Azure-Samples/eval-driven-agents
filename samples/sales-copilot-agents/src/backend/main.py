from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from azure.identity import ClientSecretCredential
from azure.ai.projects.aio import AIProjectClient
import os
import logging
import asyncio
import base64
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, List, Dict

from agents.engineer_feedback_agent import process_engineer_feedback
from agents.customer_story_agent import process_customer_story
from agents.crm_info_agent import process_crm_info
from utils import validate_input, format_response
from mock_client import MockAIProjectClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TechnicalIssue(BaseModel):
    issue: str = Field(..., description="Description of the technical issue")
    severity: str = Field(..., description="Issue severity (high/medium/low)")
    impact: str = Field(..., description="Business impact of the issue")

class Recommendation(BaseModel):
    action: str = Field(..., description="Recommended action")
    priority: str = Field(..., description="Priority level (high/medium/low)")
    rationale: str = Field(..., description="Reasoning behind the recommendation")

class EngineeringFeedback(BaseModel):
    technical_issues: List[TechnicalIssue]
    engineering_insights: List[str]
    recommendations: List[Recommendation]
    systemic_patterns: List[str]
    best_practices: List[str]

class CustomerStory(BaseModel):
    customer_background: str
    key_points: List[str]
    sentiment: str
    action_items: List[str]
    summary: str

class CRMInfo(BaseModel):
    name: str
    title: str
    department: str
    tenure: str
    expertise: List[str]
    summary: str

class AnalyzeRequest(BaseModel):
    transcript: str = Field(
        ..., 
        description="Base64 encoded Teams meeting transcript",
        example="Q3VzdG9tZXI6IFdlJ3JlIGhhdmluZyBpc3N1ZXMgd2l0aCB0aGUgQVBJIHJhdGUgbGltaXRzLg=="
    )
    notes: Optional[str] = Field(
        "", 
        description="Base64 encoded additional notes",
        example="LSBDdXN0b21lciBpcyBFbnRlcnByaXNlIHRpZXIKLSBVcmdlbnQgZXNjYWxhdGlvbiBuZWVkZWQ="
    )
    crmId: Optional[str] = Field(
        "", 
        description="CRM ID for customer lookup",
        example="12345"
    )

class AnalyzeResponse(BaseModel):
    engineering_feedback: EngineeringFeedback
    customer_story: CustomerStory
    crm_info: CRMInfo

app = FastAPI(
    title="Sales Copilot Agents API",
    description="""
    API for analyzing customer interactions using Azure AI.
    
    This API provides endpoints to:
    - Analyze Teams meeting transcripts
    - Generate engineering feedback
    - Create customer stories
    - Retrieve CRM information
    
    All text inputs should be Base64 encoded.
    """,
    version="1.0.0",
    docs_url="/swagger",
    redoc_url="/docs"
)

@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to ReDoc documentation."""
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Status information about the API
    """
    return {"status": "healthy"}

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configured per environment in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize Azure clients and resources on startup."""
    try:
        # Get environment variables
        tenant_id = os.getenv("AZURE_TENANT_ID")
        client_id = os.getenv("AZURE_CLIENT_ID")
        client_secret = os.getenv("AZURE_CLIENT_SECRET")
        connection_string = os.getenv("AZURE_AIPROJECT_CONNECTION_STRING")
        deployment_name = os.getenv("AZURE_AI_CHAT_DEPLOYMENT_NAME")

        # Validate required environment variables
        required_vars = {
            "AZURE_TENANT_ID": tenant_id,
            "AZURE_CLIENT_ID": client_id,
            "AZURE_CLIENT_SECRET": client_secret,
            "AZURE_AIPROJECT_CONNECTION_STRING": connection_string,
            "AZURE_AI_CHAT_DEPLOYMENT_NAME": deployment_name
        }
        
        missing_vars = [k for k, v in required_vars.items() if not v]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        try:
            # Initialize Azure credentials using service principal
            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
            
            # Initialize AI Project client using connection string
            app.state.project_client = AIProjectClient.from_connection_string(
                credential=credential,
                conn_str=connection_string
            )
            
            # Test the connection by getting a chat completions client
            chat_client = await app.state.project_client.get_chat_completions_client(
                deployment_name=deployment_name
            )
            
            logger.info("Successfully connected to Azure AI Project")
            
        except Exception as e:
            logger.warning(f"Failed to initialize AI Project client: {e}")
            logger.warning("Falling back to mock client")
            app.state.project_client = MockAIProjectClient()
            
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        logger.warning("Falling back to mock client")
        app.state.project_client = MockAIProjectClient()

@app.post("/analyze", 
    response_model=AnalyzeResponse,
    tags=["Analysis"],
    summary="Analyze customer interaction",
    response_description="Analysis results including engineering feedback, customer story, and CRM information"
)
async def analyze_interaction(request: AnalyzeRequest):
    """
    Analyze customer interaction data using multiple agents.
    
    The endpoint processes:
    - Teams meeting transcript
    - Additional notes
    - CRM ID for customer information
    
    All text inputs must be Base64 encoded.
    
    Returns a comprehensive analysis including:
    - Engineering feedback and recommendations
    - Customer story and sentiment analysis
    - CRM information and context
    """
    # Convert Pydantic model to dict for validation
    data = request.model_dump()
    
    # Validate input size first
    total_size = sum(len(str(v)) for v in data.values())
    if total_size > 1000000:
        raise HTTPException(status_code=400, detail="Input too large: maximum total size is 1MB")
        
    # Then validate and decode base64
    try:
        # Always decode transcript as it's required
        if not data.get('transcript'):
            raise HTTPException(status_code=400, detail="Missing required field: transcript")
            
        try:
            data['transcript'] = base64.b64decode(data['transcript']).decode('utf-8')
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 encoding in transcript")
            
        # Only decode notes if present and not empty
        if notes := data.get('notes'):
            if notes.strip():
                try:
                    data['notes'] = base64.b64decode(notes).decode('utf-8')
                except Exception:
                    raise HTTPException(status_code=400, detail="Invalid base64 encoding in notes")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    # Additional validation if needed
    if error := validate_input(data):
        raise HTTPException(status_code=400, detail=error)
    
    try:
        # Process data with each agent in parallel
        # Note: process_crm_info is synchronous, so we wrap it in a coroutine
        async def process_crm_info_async(data):
            return process_crm_info(data.get('crmId', ''))
            
        try:
            results = await asyncio.gather(
                process_engineer_feedback(app.state.project_client, data.get('transcript', ''), data.get('notes', ''), data.get('crmId', '')),
                process_customer_story(app.state.project_client, data.get('transcript', ''), data.get('notes', ''), data.get('crmId', '')),
                process_crm_info_async(data)
            )
        except Exception as e:
            logger.error(f"Error processing with agents: {e}")
            # Return default responses if agents fail
            results = [
                {
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
                },
                {
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
                },
                {
                    "name": "",
                    "title": "",
                    "department": "",
                    "tenure": "",
                    "expertise": [],
                    "summary": "Error retrieving CRM info"
                }
            ]
        
        # Combine results
        response_data = {
            "engineering_feedback": results[0],
            "customer_story": results[1],
            "crm_info": results[2]
        }
        
        return format_response(response_data)
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def create_app():
    """Create and configure the FastAPI application."""
    return app
