import pytest
from fastapi.testclient import TestClient
import logging
import sys
from pathlib import Path
from typing import AsyncGenerator, Dict

# Add src directory to Python path
src_path = Path(__file__).parent.parent
sys.path.append(str(src_path))

from src.main import app

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Enable async test support
pytest_plugins = ["pytest_asyncio"]

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def client() -> TestClient:
    """Test client fixture"""
    logger.debug("Creating test client")
    client = TestClient(app)
    return client

@pytest.fixture
async def auth_headers() -> Dict[str, str]:
    """Auth headers for test requests"""
    logger.debug("Creating auth headers with test token")
    return {
        "Authorization": "Bearer test_token",
        "Content-Type": "application/json"
    }

@pytest.fixture
def test_settings():
    """Return test settings"""
    return Settings(
        deep_lynx_url="http://localhost:8090",
        deep_lynx_api_key="test-key",
        deep_lynx_api_secret="test-secret",
        deep_lynx_container_id="1",
        deep_lynx_integration_test="1",
        database_url="postgresql://test:test@localhost:5432/test_db",
        debug=True,
        log_level="INFO"
    )

@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings for tests"""
    test_settings = Settings(
        deep_lynx_url="http://localhost:8090",
        deep_lynx_api_key="test-key",
        deep_lynx_api_secret="test-secret",
        deep_lynx_container_id="1",
        deep_lynx_integration_test="1",
        database_url="postgresql://test:test@localhost:5432/test_db",
        debug=True,
        log_level="INFO"
    )
    
    def mock_get_settings():
        return test_settings
    
    monkeypatch.setattr("src.core.config.get_settings", mock_get_settings)
    return test_settings

@pytest.fixture
def test_data_source():
    """Test data source fixture"""
    logger.debug("Creating test data source")
    return {
        "name": "test-source",
        "adapter_type": "standard",
        "config": {
            "type": "test",
            "description": "Test data source for integration tests"
        }
    } 