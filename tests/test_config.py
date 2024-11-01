import pytest
from dev.config import DeepLynxConfig
import deep_lynx
from unittest.mock import patch, MagicMock
from deep_lynx.rest import ApiException
import os
from pathlib import Path

@pytest.mark.unit
@pytest.mark.config
def test_config_loads_from_env(mock_env):
    """Test that configuration loads from environment variables."""
    config = DeepLynxConfig()
    assert config.api_url == 'http://test.com'
    assert config.api_key == 'test_key'
    assert config.api_secret == 'test_secret'
    assert config.debug is False
    assert config.log_level == 'DEBUG'

@pytest.mark.unit
@pytest.mark.config
def test_config_loads_from_env_file(temp_env_file):
    """Test that configuration loads from .env file."""
    with patch.object(DeepLynxConfig, 'model_config', {
        **DeepLynxConfig.model_config,
        'env_file': temp_env_file
    }):
        config = DeepLynxConfig()
        assert config.api_url == 'http://test.com'
        assert config.api_key == 'test_key'
        assert config.api_secret == 'test_secret'

@pytest.mark.unit
@pytest.mark.config
def test_config_env_precedence(mock_env, temp_env_file):
    """Test that environment variables take precedence over .env file."""
    with patch.dict('os.environ', {
        'DEEP_LYNX_URL': 'http://override.com'
    }):
        with patch.object(DeepLynxConfig, 'model_config', {
            **DeepLynxConfig.model_config,
            'env_file': temp_env_file
        }):
            config = DeepLynxConfig()
            assert config.api_url == 'http://override.com'
            assert config.api_key == 'test_key'  # From env file

@pytest.mark.integration
@pytest.mark.config
def test_get_client_end_to_end(integration_env):
    """
    End-to-end test for client initialization.
    Only runs if DEEP_LYNX_INTEGRATION_TEST is set.
    """
    if not os.getenv('DEEP_LYNX_INTEGRATION_TEST'):
        pytest.skip("Integration test requires DEEP_LYNX_INTEGRATION_TEST=1")
    
    config = DeepLynxConfig()
    client = config.get_client()
    assert isinstance(client, deep_lynx.ApiClient)
    
    # Test actual API connection
    auth_api = deep_lynx.AuthenticationApi(client)
    token = auth_api.retrieve_o_auth_token(
        x_api_key=config.api_key,
        x_api_secret=config.api_secret,
        x_api_expiry='1h'
    )
    assert token is not None

@pytest.mark.unit
@pytest.mark.config
def test_get_client_token_handling(mock_auth_api, mock_env):
    """Test client initialization with token handling."""
    mock_token = MagicMock()
    mock_token.value = "test_token_value"
    mock_auth_api.return_value.retrieve_o_auth_token.return_value = mock_token
    
    config = DeepLynxConfig()
    client = config.get_client()
    
    # Verify token retrieval call
    mock_auth_api.return_value.retrieve_o_auth_token.assert_called_once_with(
        x_api_key=config.api_key,
        x_api_secret=config.api_secret,
        x_api_expiry='1h'
    )

@pytest.mark.unit
@pytest.mark.error
@pytest.mark.parametrize("error_status,expected_error", [
    (401, ConnectionError),
    (403, ConnectionError),
    (500, Exception)
])
def test_get_client_error_handling(mock_env, error_status, expected_error):
    """Test various error scenarios in client initialization."""
    with patch('deep_lynx.AuthenticationApi') as mock_auth_api:
        mock_auth_api.return_value.retrieve_o_auth_token.side_effect = \
            ApiException(status=error_status)
        
        config = DeepLynxConfig()
        with pytest.raises(expected_error):
            config.get_client() 

@pytest.mark.unit
@pytest.mark.config
def test_connection_pooling_config(mock_env):
    """Test connection pooling configuration."""
    with patch.dict('os.environ', {
        'POOL_CONNECTIONS': '20',
        'POOL_MAXSIZE': '30',
        'MAX_RETRIES': '5'
    }):
        config = DeepLynxConfig()
        assert config.pool_connections == 20
        assert config.pool_maxsize == 30
        assert config.max_retries == 5

@pytest.mark.unit
@pytest.mark.error
def test_retry_mechanism(mock_env):
    """Test retry mechanism for failed requests."""
    with patch('deep_lynx.AuthenticationApi') as mock_auth_api:
        # Setup mock to fail with server errors then succeed
        mock_token = MagicMock()
        mock_token.value = "test_token_value"
        mock_auth_api.return_value.retrieve_o_auth_token.side_effect = [
            ApiException(status=503),
            ApiException(status=503),
            mock_token
        ]
        
        config = DeepLynxConfig()
        with pytest.raises(Exception) as exc_info:
            config.get_client()
        
        assert "Deep Lynx server error" in str(exc_info.value)
        assert mock_auth_api.return_value.retrieve_o_auth_token.call_count == 1  # No retry in auth layer