import pytest
from src.core.deep_lynx import DeepLynxClient
from src.core.config import Settings

def test_deep_lynx_client_initialization(monkeypatch):
    """Test Deep Lynx client initialization with mocked settings"""
    # Create test settings
    test_settings = Settings(
        deep_lynx_url="http://localhost:8090",
        deep_lynx_api_key="YWIxZGQ5YmQtOGE1Yy00MTE0LTk4ZmItMDMyOThkNTc1ZjEw",
        deep_lynx_api_secret="YzA3ZWI2NWUtYzhlNC00ZTQxLTlhYzYtODM1YTNmZmFiMzc0",
        deep_lynx_container_id="1",
        deep_lynx_integration_test="1",
        database_url="postgresql://user:password@localhost:5432/dbname",
        debug=True,
        log_level="INFO"
    )
    
    def mock_get_settings():
        return test_settings
    
    # Apply the mock
    monkeypatch.setattr("src.core.config.get_settings", mock_get_settings)
    
    # Create client and verify
    client = DeepLynxClient()
    assert client is not None
    assert client.settings == test_settings
