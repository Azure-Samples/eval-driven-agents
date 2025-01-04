import pytest
from fastapi.testclient import TestClient
import base64

def test_process_valid_input(test_client: TestClient, sample_input_data):
    response = test_client.post("/analyze", json=sample_input_data)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    assert "data" in response_data
    data = response_data["data"]
    
    # Verify engineering feedback content
    assert "engineering_feedback" in data
    eng_feedback = data["engineering_feedback"]
    print("\nFull Engineering Feedback:", eng_feedback)
    print("\nEngineering Insights:", eng_feedback.get("engineering_insights", []))
    print("\nTechnical Issues:", [issue["issue"] for issue in eng_feedback["technical_issues"]])
    assert any("api rate limits" == issue["issue"].lower() for issue in eng_feedback["technical_issues"])
    assert any("documentation" in insight.lower() for insight in eng_feedback["engineering_insights"])
    
    # Verify customer story content
    assert "customer_story" in data
    story = data["customer_story"]
    # Check for API-related issues in summary or key points
    assert any("api" in point.lower() for point in story["key_points"])
    assert "api" in story["summary"].lower()
    # Check for rate limits mention in summary or key points
    assert any("rate limit" in point.lower() for point in story["key_points"]) or "rate limit" in story["summary"].lower()
    
    # Verify CRM info content
    assert "crm_info" in data
    crm_info = data["crm_info"]
    assert crm_info.get("name") == "John Doe"
    assert crm_info.get("role", "") == "Senior Software Engineer" or crm_info.get("title", "") == "Senior Software Engineer"
    
    assert "timestamp" in response_data

def test_process_base64_input(test_client: TestClient, sample_base64_data):
    response = test_client.post("/analyze", json=sample_base64_data)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    assert "data" in response_data
    data = response_data["data"]
    assert "engineering_feedback" in data
    assert "customer_story" in data
    assert "crm_info" in data
    assert "timestamp" in response_data

def test_process_missing_fields(test_client: TestClient, sample_missing_fields):
    response = test_client.post("/analyze", json=sample_missing_fields)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    assert "data" in response_data
    data = response_data["data"]
    assert "engineering_feedback" in data
    assert "customer_story" in data
    assert "crm_info" in data
    response_data = response.json()
    assert response_data["status"] == "success"
    assert "data" in response_data
    data = response_data["data"]
    assert "engineering_feedback" in data
    assert "customer_story" in data
    assert "crm_info" in data
    assert "timestamp" in response_data

def test_process_invalid_input(test_client: TestClient):
    # Test empty payload
    response = test_client.post("/analyze", json={})
    assert response.status_code == 422
    
    # Test malformed JSON
    response = test_client.post("/analyze", data="invalid json")
    assert response.status_code == 422
    
    # Test empty string fields
    response = test_client.post("/analyze", json={"transcript": "", "notes": "", "crmId": ""})
    assert response.status_code == 400
    assert "Missing required field" in response.json()["detail"]
    
    # Test very long input
    long_text = "x" * 1000000  # 1MB of text
    response = test_client.post("/analyze", json={"transcript": long_text, "notes": "test", "crmId": "12345"})
    assert response.status_code == 400
    assert "Input too large" in response.json()["detail"]
    
    # Test special characters (should be treated as invalid base64)
    special_chars = "!@#$%^&*()_+-=[]{}|;:'\",.<>?/~`"
    response = test_client.post("/analyze", json={"transcript": special_chars, "notes": special_chars, "crmId": "12345"})
    assert response.status_code == 400
    assert "Invalid base64" in response.json()["detail"]

def test_process_invalid_base64(test_client: TestClient):
    # Test invalid base64 in transcript
    invalid_data = {
        "transcript": "not-base64!@#$",
        "notes": "UHJpb3JpdHk6IEhpZ2g=",  # valid base64
        "crmId": "12345"
    }
    response = test_client.post("/analyze", json=invalid_data)
    assert response.status_code == 400  # Invalid base64 should return 400 Bad Request
    assert "Invalid base64" in response.json()["detail"]
    
    # Test invalid base64 in notes
    invalid_notes_data = {
        "transcript": "Valid plain text",
        "notes": "invalid-base64+/=",  # invalid base64 with base64 chars
        "crmId": "12345"
    }
    response = test_client.post("/analyze", json=invalid_notes_data)
    assert response.status_code == 400
    assert "Invalid base64" in response.json()["detail"]

def test_health_check(test_client: TestClient):
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
