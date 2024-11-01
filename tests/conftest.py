import pytest
from pathlib import Path
from typing import Generator
import os
from unittest.mock import patch
from dotenv import load_dotenv

# Register custom markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "config: marks tests related to configuration"
    )
    config.addinivalue_line(
        "markers", "error: marks tests related to error handling"
    )

@pytest.fixture(scope="session")
def test_env_vars() -> dict:
    """Base test environment variables for unit tests."""
    return {
        'DEEP_LYNX_URL': 'http://test.com',
        'DEEP_LYNX_API_KEY': 'test_key',
        'DEEP_LYNX_API_SECRET': 'test_secret',
        'DEBUG': 'False',
        'LOG_LEVEL': 'DEBUG',
        'DEEP_LYNX_INTEGRATION_TEST': '1'
    }

@pytest.fixture
def mock_env(test_env_vars, monkeypatch) -> None:
    """Setup mock environment variables."""
    for key, value in test_env_vars.items():
        monkeypatch.setenv(key, value)

@pytest.fixture
def temp_env_file(tmp_path, test_env_vars) -> Generator[Path, None, None]:
    """Create a temporary .env file."""
    env_file = tmp_path / ".env"
    env_content = "\n".join(f"{k}={v}" for k, v in test_env_vars.items())
    env_file.write_text(env_content)
    yield env_file
    env_file.unlink(missing_ok=True)

@pytest.fixture
def mock_auth_api():
    """Mock Deep Lynx Authentication API."""
    with patch('deep_lynx.AuthenticationApi') as mock:
        yield mock

@pytest.fixture
def integration_env():
    """Environment for integration tests using real credentials."""
    # Load the real .env file
    load_dotenv()
    
    # Get real credentials from .env
    real_key = os.getenv('DEEP_LYNX_API_KEY')
    real_secret = os.getenv('DEEP_LYNX_API_SECRET')
    
    if not (real_key and real_secret):
        pytest.skip("Integration test requires DEEP_LYNX_API_KEY and DEEP_LYNX_API_SECRET in .env")
    
    # Store original env vars
    original_env = {}
    for key in ['DEEP_LYNX_URL', 'DEEP_LYNX_API_KEY', 'DEEP_LYNX_API_SECRET']:
        original_env[key] = os.environ.get(key)
    
    # Set integration test environment
    os.environ.update({
        'DEEP_LYNX_URL': 'http://localhost:8090',
        'DEEP_LYNX_API_KEY': real_key,
        'DEEP_LYNX_API_SECRET': real_secret,
        'DEEP_LYNX_INTEGRATION_TEST': '1'
    })
    
    yield
    
    # Restore original environment
    for key, value in original_env.items():
        if value is not None:
            os.environ[key] = value
        else:
            os.environ.pop(key, None)

@pytest.fixture(autouse=True)
def cleanup_api_client():
    """Cleanup API client connections after each test."""
    yield
    # Force cleanup of any remaining API clients
    import gc
    gc.collect()
    
    # Clean up any remaining pools
    from multiprocessing import pool
    for obj in gc.get_objects():
        if isinstance(obj, pool.Pool):
            obj.close()
            obj.join()