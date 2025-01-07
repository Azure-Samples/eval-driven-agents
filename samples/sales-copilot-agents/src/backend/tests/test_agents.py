import pytest
from typing import Dict
from api.agents.crm_info_agent import process_crm_info
from api.agents.customer_story_agent import process_customer_story
from api.agents.engineer_feedback_agent import process_engineer_feedback

def test_crm_info_agent_valid_id(sample_input_data):
    result = process_crm_info(sample_input_data["crmId"])
    assert isinstance(result, dict)
    # Check for key information from the stubbed data
    assert result["name"] == "John Doe"
    assert result["title"] == "Senior Software Engineer"
    assert result["department"] == "Azure Cloud Services"
    assert result["tenure"] == "5 years"
    assert "cloud security" in result["expertise"]
    assert isinstance(result["summary"], str)
    assert len(result["summary"]) > 0

def test_crm_info_agent_invalid_id():
    result = process_crm_info("99999")
    assert isinstance(result, dict)
    assert "error" in result
    assert "no data is available" in result["error"].lower()

def test_crm_info_agent_malformed_id():
    result = process_crm_info("")  # Empty CRM ID
    assert isinstance(result, dict)
    assert "error" in result
    assert "invalid crm id" in result["error"].lower()

    result = process_crm_info("abc123")  # Invalid format
    assert isinstance(result, dict)
    assert "error" in result
    assert "invalid crm id" in result["error"].lower()

@pytest.mark.asyncio
async def test_customer_story_agent(mock_project_client, sample_input_data):
    result = await process_customer_story(
        mock_project_client,
        sample_input_data["transcript"],
        sample_input_data.get("notes", ""),
        sample_input_data.get("crmId", "")
    )
    assert isinstance(result, dict)
    assert "customer_background" in result
    assert "key_points" in result
    assert "sentiment" in result
    assert "action_items" in result
    assert "summary" in result
    assert isinstance(result["key_points"], list)
    assert isinstance(result["action_items"], list)
    assert result["sentiment"] in ["positive", "neutral", "negative"]
    print("\nCustomer Story Key Points:", result["key_points"])
    assert any("API rate limits" in point for point in result["key_points"])
    assert any("documentation" in point for point in result["key_points"])

@pytest.mark.asyncio
async def test_customer_story_agent_base64(mock_project_client, sample_base64_data):
    result = await process_customer_story(
        mock_project_client,
        sample_base64_data["transcript"],
        sample_base64_data.get("notes", ""),
        sample_base64_data.get("crmId", "")
    )
    assert isinstance(result, dict)
    assert all(key in result for key in ["customer_background", "key_points", "sentiment", "action_items", "summary"])
    assert isinstance(result["key_points"], list)
    assert isinstance(result["action_items"], list)
    assert result["sentiment"] in ["positive", "neutral", "negative"]
    assert len(result["summary"]) > 0

@pytest.mark.asyncio
async def test_engineer_feedback_agent(mock_project_client, sample_input_data):
    result = await process_engineer_feedback(
        mock_project_client,
        sample_input_data["transcript"],
        sample_input_data.get("notes", ""),
        sample_input_data.get("crmId", "")
    )
    assert isinstance(result, dict)
    assert "technical_issues" in result
    assert "engineering_insights" in result
    assert "recommendations" in result
    assert "systemic_patterns" in result
    assert "best_practices" in result
    
    # Validate structure
    assert isinstance(result["technical_issues"], list)
    assert all(isinstance(issue, dict) for issue in result["technical_issues"])
    assert all("severity" in issue and "impact" in issue for issue in result["technical_issues"])
    
    assert isinstance(result["engineering_insights"], list)
    assert isinstance(result["recommendations"], list)
    assert all(isinstance(rec, dict) for rec in result["recommendations"])
    assert all("action" in rec and "priority" in rec and "rationale" in rec for rec in result["recommendations"])
    
    # Check content
    assert any("API" in issue["issue"] for issue in result["technical_issues"])
    assert any("rate limit" in rec["action"].lower() for rec in result["recommendations"])

@pytest.mark.asyncio
async def test_engineer_feedback_missing_notes(mock_project_client, sample_missing_fields):
    result = await process_engineer_feedback(
        mock_project_client,
        sample_missing_fields["transcript"],
        sample_missing_fields.get("notes", ""),
        sample_missing_fields.get("crmId", "")
    )
    assert isinstance(result, dict)
    assert all(key in result for key in ["technical_issues", "engineering_insights", "recommendations", "systemic_patterns", "best_practices"])
    assert len(result["technical_issues"]) > 0
    assert len(result["recommendations"]) > 0
