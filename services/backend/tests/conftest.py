import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
import os

# Add src directory to Python path
root_path = str(Path(__file__).parent.parent)
sys.path.append(root_path)

# Set test environment variables
os.environ["SECRET_KEY"] = "test-secret-key"

from src.main import app
from src.core.deep_lynx import get_client
import logging

logger = logging.getLogger(__name__)

@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)

@pytest.fixture
async def auth_headers(client):
    """Get authentication headers"""
    try:
        # Login to get token
        response = client.post(
            "/auth/login",
            data={"username": "test", "password": "test"}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        # Get Deep Lynx headers
        dl_client = get_client()
        headers = dl_client.api_client.default_headers.copy()
        
        # Add JWT token
        headers["Authorization"] = f"Bearer {token}"
        
        logger.debug(f"Auth headers created: {headers}")
        return headers
        
    except Exception as e:
        logger.error(f"Failed to get auth headers: {e}")
        raise

@pytest.fixture
def test_data_source():
    """Test data source fixture"""
    return {
        "name": "test-source",
        "adapter_type": "standard",
        "config": {
            "type": "test",
            "description": "Test data source for integration tests"
        }
    } 