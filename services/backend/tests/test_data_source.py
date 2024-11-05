import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
import logging

# Add the project root to the Python path
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

logger = logging.getLogger(__name__)

def test_list_data_sources(client, auth_headers):
    """Test listing all data sources"""
    response = client.get("/datasources", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # Log response for debugging
    logger.debug(f"List data sources response: {data}")
    
    # Verify data structure
    if data:
        first_source = data[0]
        assert "id" in first_source
        assert "name" in first_source
        assert "adapter_type" in first_source
        assert "config" in first_source
        assert "active" in first_source
        assert "created_at" in first_source

def test_create_data_source(client, auth_headers, test_data_source):
    """Test creating a new data source"""
    # Create data source
    response = client.post(
        "/datasources",
        headers=auth_headers,
        json=test_data_source
    )
    assert response.status_code == 200
    data = response.json()
    
    # Log response for debugging
    logger.debug(f"Create data source response: {data}")
    
    # Verify response structure
    assert data["name"] == test_data_source["name"]
    assert data["adapter_type"] == test_data_source["adapter_type"]
    
    # Verify config fields individually
    assert data["config"]["type"] == test_data_source["config"]["type"]
    assert data["config"]["description"] == test_data_source["config"]["description"]
    
    # Return created ID for other tests
    return data["id"]

def test_get_data_source(client, auth_headers, test_data_source):
    """Test getting a specific data source"""
    # First create a data source
    created_id = test_create_data_source(client, auth_headers, test_data_source)
    
    # Get the created data source
    response = client.get(f"/datasources/{created_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    
    # Log response for debugging
    logger.debug(f"Get data source response: {data}")
    
    # Verify response structure
    assert data["id"] == created_id
    assert data["name"] == test_data_source["name"]
    assert data["adapter_type"] == test_data_source["adapter_type"]
    assert data["config"] == test_data_source["config"]

def test_get_nonexistent_data_source(client, auth_headers):
    """Test getting a data source that doesn't exist"""
    response = client.get("/datasources/999999", headers=auth_headers)
    assert response.status_code == 404

def test_create_invalid_data_source(client, auth_headers):
    """Test creating a data source with invalid data"""
    invalid_data = {
        "name": "",  # Invalid: empty name
        "adapter_type": "invalid_type",
        "config": None  # Invalid: config should be a dict
    }
    
    response = client.post(
        "/datasources",
        headers=auth_headers,
        json=invalid_data
    )
    assert response.status_code in [400, 422]  # Either validation or API error

@pytest.mark.parametrize("field", ["name", "adapter_type", "config"])
def test_create_missing_required_field(client, auth_headers, test_data_source, field):
    """Test creating a data source with missing required fields"""
    invalid_data = test_data_source.copy()
    del invalid_data[field]
    
    response = client.post(
        "/datasources",
        headers=auth_headers,
        json=invalid_data
    )
    assert response.status_code == 422  # FastAPI validation error

def test_authentication_required(client):
    """Test that authentication is required for all endpoints"""
    # Try without auth headers
    endpoints = [
        ("GET", "/datasources"),
        ("POST", "/datasources"),
        ("GET", "/datasources/1")
    ]
    
    for method, endpoint in endpoints:
        if method == "GET":
            response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint, json={})
            
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden 