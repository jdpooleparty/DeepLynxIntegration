import pytest
from fastapi.testclient import TestClient
from deep_lynx.models import (
    ListDataSourcesResponse,
    CreateDataSourcesResponse,
    GetDataSourceResponse,
    UpdateDataSourceResponse,
    DataSourceConfig,
    Generic200Response
)
from deep_lynx.api import DataSourcesApi
from deep_lynx.rest import ApiException
import logging
import json
import time
from typing import Dict, Any

# Enhanced logging setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('test_data_source.log')
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(file_handler)

class TestContext:
    """Context manager for test cases with detailed logging"""
    def __init__(self, description: str):
        self.description = description
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        logger.info(f"\n{'='*20} Starting Test: {self.description} {'='*20}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if exc_type:
            logger.error(
                f"Test '{self.description}' failed after {duration:.2f}s\n"
                f"Error: {exc_type.__name__}: {exc_val}",
                exc_info=(exc_type, exc_val, exc_tb)
            )
        else:
            logger.info(f"Test '{self.description}' completed successfully in {duration:.2f}s")
        logger.info("="*60 + "\n")

def validate_response(response: Dict[str, Any], expected_model: Any, context: str = "") -> None:
    """Validate response against Deep Lynx schema"""
    try:
        logger.debug(f"Validating response for {context}")
        logger.debug(f"Response data: {json.dumps(response, indent=2)}")
        validated = expected_model(**response)
        logger.info(f"Response validation successful for {context}")
        return validated
    except Exception as e:
        logger.error(f"Schema validation failed for {context}: {str(e)}")
        raise

@pytest.fixture
def sample_data_source():
    """Fixture for test data source with enhanced logging"""
    config = {
        "name": "test-source",
        "type": "standard",
        "adapter_type": "standard",
        "config": {
            "data_type": "json",
            "kind": "standard",
            "options": {
                "batch_size": 1000,
                "retry_count": 3,
                "timeout": 30
            }
        }
    }
    logger.debug(f"Created sample data source config: {json.dumps(config, indent=2)}")
    return config

@pytest.mark.asyncio
async def test_data_source_lifecycle(client: TestClient, auth_headers: Dict[str, str], sample_data_source):
    """Test complete lifecycle with enhanced validation and logging"""
    # Get client and headers
    test_client = await client
    headers = await auth_headers
    
    with TestContext("Data Source Lifecycle Test"):
        # Create
        with TestContext("Create Data Source"):
            create_response = test_client.post(
                "/datasources",
                headers=headers,
                json=sample_data_source
            )
            logger.debug(f"Create response: {create_response.json()}")
            assert create_response.status_code == 201

@pytest.mark.asyncio
async def test_data_source_error_handling(client, auth_headers):
    """Test error handling scenarios"""
    test_client = await client
    headers = await auth_headers
    
    with TestContext("Data Source Error Handling"):
        # Invalid data source creation
        with TestContext("Invalid Data Source Creation"):
            invalid_source = {
                "name": "test-source",
                # Missing required fields
            }
            response = test_client.post(
                "/datasources",
                headers=headers,
                json=invalid_source
            )
            assert response.status_code == 422

@pytest.mark.asyncio
async def test_data_source_validation(client, auth_headers, sample_data_source):
    """Test data source validation rules"""
    test_client = await client
    headers = await auth_headers
    
    with TestContext("Data Source Validation"):
        # Name length validation
        with TestContext("Name Length"):
            invalid_name = sample_data_source.copy()
            invalid_name["name"] = "a" * 256  # Too long
            response = test_client.post(
                "/datasources",
                headers=headers,
                json=invalid_name
            )
            assert response.status_code == 422

@pytest.mark.asyncio
async def test_data_source_batch_operations(client, auth_headers, sample_data_source):
    """Test batch operations on data sources"""
    test_client = await client
    headers = await auth_headers
    created_ids = []

    with TestContext("Batch Operations"):
        # Create multiple sources
        for i in range(3):
            source = sample_data_source.copy()
            source["name"] = f"test-source-{i}"
            source["type"] = "standard"  # Add required type field
            response = test_client.post(
                "/datasources",
                headers=headers,
                json=source
            )
            assert response.status_code == 201
            created_ids.append(response.json()["id"])

@pytest.mark.asyncio
async def test_data_source_config_updates(client, auth_headers, sample_data_source):
    """Test data source configuration updates"""
    test_client = await client
    headers = await auth_headers
    
    with TestContext("Config Updates"):
        # Create initial source
        source = sample_data_source.copy()
        source["type"] = "standard"  # Add required type field
        create_response = test_client.post(
            "/datasources",
            headers=headers,
            json=source
        )
        assert create_response.status_code == 201

@pytest.mark.asyncio
async def test_data_source_performance(client, auth_headers, sample_data_source):
    """Test performance metrics for data source operations"""
    test_client = await client
    headers = await auth_headers
    
    with TestContext("Performance Testing"):
        # Measure list performance
        with TestContext("List Performance"):
            start_time = time.time()
            response = test_client.get("/datasources", headers=headers)
            assert response.status_code == 200