import deep_lynx
from deep_lynx.rest import ApiException
from pprint import pprint
import os
from dotenv import load_dotenv
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import json
from prometheus_client import Counter, Histogram, start_http_server

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics setup
OPERATION_COUNTER = Counter('deep_lynx_operations_total', 'Total operations by type', ['operation_type'])
OPERATION_DURATION = Histogram('deep_lynx_operation_duration_seconds', 'Operation duration in seconds', ['operation_type'])
ERROR_COUNTER = Counter('deep_lynx_errors_total', 'Total errors by type', ['error_type'])

@dataclass
class OperationMetrics:
    """Metrics for an operation"""
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    error: Optional[str] = None

class DeepLynxTransaction:
    """Transaction-like context manager for related operations"""
    def __init__(self, tester, description: str):
        self.tester = tester
        self.description = description
        self.operations: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        self.metrics: List[OperationMetrics] = []
        
    def __enter__(self):
        logger.info(f"Starting transaction: {self.description}")
        # Perform health check before transaction
        if not self.tester.check_health():
            raise SystemError("System health check failed before transaction")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        if exc_type:
            logger.error(f"Transaction failed: {exc_val}")
            # Attempt rollback
            self._rollback()
            ERROR_COUNTER.labels(error_type=exc_type.__name__).inc()
        else:
            logger.info(f"Transaction completed successfully in {duration:.2f}s")
            
        # Record metrics
        self._record_metrics(end_time, bool(exc_type))
        return False  # Don't suppress exceptions

    def _rollback(self):
        """Rollback all operations in reverse order"""
        logger.warning("Starting transaction rollback")
        for operation in reversed(self.operations):
            try:
                if operation['type'] == 'create_data_source':
                    self.tester.delete_data_source(operation['result'].id)
                    logger.info(f"Rolled back data source creation: {operation['result'].id}")
                # Add other operation types as needed
            except Exception as e:
                logger.error(f"Rollback failed for operation {operation['type']}: {e}")

    def _record_metrics(self, end_time: datetime, had_error: bool):
        """Record metrics for the transaction"""
        duration = (end_time - self.start_time).total_seconds()
        OPERATION_DURATION.labels(operation_type='transaction').observe(duration)
        if had_error:
            ERROR_COUNTER.labels(error_type='transaction_error').inc()

class DeepLynxTester:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize configuration
        self.configuration = deep_lynx.Configuration()
        self.configuration.host = os.getenv('DEEP_LYNX_URL')
        self.api_client = deep_lynx.ApiClient(self.configuration)
        
        # Initialize API instances
        self.auth_api = deep_lynx.AuthenticationApi(self.api_client)
        self.containers_api = deep_lynx.ContainersApi(self.api_client)
        self.datasources_api = deep_lynx.DataSourcesApi(self.api_client)
        self.metatypes_api = deep_lynx.MetatypesApi(self.api_client)
        
        # Authentication credentials
        self.api_key = os.getenv('DEEP_LYNX_API_KEY')
        self.api_secret = os.getenv('DEEP_LYNX_API_SECRET')
        
        # Get container ID from env with proper error handling
        container_id_str = os.getenv('DEEP_LYNX_CONTAINER_ID')
        if not container_id_str:
            raise ValueError("DEEP_LYNX_CONTAINER_ID not set in environment")
        try:
            self.container_id = int(container_id_str)
        except ValueError:
            raise ValueError(f"Invalid DEEP_LYNX_CONTAINER_ID: {container_id_str}")

        # Debug info with environment variable value
        logger.info(f"Initialized with host: {self.configuration.host}")
        logger.info(f"Using container ID from env: {self.container_id}")

        # Initialize metrics server if enabled
        if os.getenv('DEEP_LYNX_METRICS_ENABLED', 'false').lower() == 'true':
            metrics_port = int(os.getenv('DEEP_LYNX_METRICS_PORT', '8000'))
            start_http_server(metrics_port)
            logger.info(f"Metrics server started on port {metrics_port}")

    @contextmanager
    def transaction(self, description: str):
        """Create a new transaction context"""
        transaction = DeepLynxTransaction(self, description)
        try:
            with transaction:
                yield transaction
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            raise

    def check_health(self) -> bool:
        """Check system health before operations"""
        try:
            # Check Deep Lynx API health
            if not self._check_api_health():
                return False
                
            # Check container accessibility
            if not self.validate_container():
                return False
                
            # Check authentication
            if 'Authorization' not in self.api_client.default_headers:
                self.authenticate()
                
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def _check_api_health(self) -> bool:
        """Check Deep Lynx API health"""
        try:
            response = requests.get(f"{self.configuration.host}/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"API health check failed: {e}")
            return False

    @OPERATION_DURATION.labels(operation_type='create_data_source').time()
    def create_data_source(self, name: str, transaction: Optional[DeepLynxTransaction] = None) -> Any:
        """Create a data source with metrics and transaction support"""
        try:
            # Health check before operation
            if not self.check_health():
                raise SystemError("System health check failed")
                
            result = super().create_data_source(name)
            OPERATION_COUNTER.labels(operation_type='create_data_source').inc()
            
            if transaction:
                transaction.operations.append({
                    'type': 'create_data_source',
                    'result': result,
                    'timestamp': datetime.now()
                })
            
            return result
            
        except Exception as e:
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            raise

    def authenticate(self):
        """Authenticate with Deep Lynx"""
        try:
            # Debug logging for authentication attempt
            logger.info("Attempting authentication with Deep Lynx...")
            logger.info(f"Host: {self.configuration.host}")
            
            # Debug the actual values
            logger.info(f"API Key: {self.api_key}")
            logger.info(f"API Secret: {self.api_secret}")
            
            if not self.api_key or not self.api_secret:
                raise ValueError("API key or secret is missing from environment variables")

            # Make request using requests library directly
            headers = {
                'x-api-key': self.api_key,
                'x-api-secret': self.api_secret
            }
            
            url = f"{self.configuration.host}/oauth/token"
            logger.info(f"Making request to: {url}")
            logger.info(f"With headers: {headers}")
            
            session = requests.Session()
            retries = Retry(total=3, backoff_factor=0.5)
            session.mount('http://', HTTPAdapter(max_retries=retries))
            
            response = session.get(url, headers=headers)
            
            if response.status_code == 200:
                # Extract token and update API client headers
                token = response.text.strip('"')  # Remove quotes from token
                self.api_client.default_headers['Authorization'] = f'Bearer {token}'
                
                logger.info("Successfully authenticated with Deep Lynx")
                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response text: {response.text[:100]}...")
                return response.text
            else:
                logger.error(f"Authentication failed with status {response.status_code}")
                logger.error(f"Response text: {response.text}")
                raise ApiException(http_resp=response)
            
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {str(e)}")
            raise

    def list_data_sources(self):
        """List all data sources in container"""
        try:
            # Revalidate container before operation
            if not self.validate_container():
                raise ValueError(f"Container {self.container_id} validation failed")
                
            logger.debug(f"Listing data sources for container {self.container_id}")
            
            try:
                # Try to list data sources
                sources = self.datasources_api.list_data_sources(
                    container_id=self.container_id,
                    timeseries=False,
                    archived=False
                )
                
                if sources and hasattr(sources, 'value'):
                    logger.info(f"Found {len(sources.value)} data sources")
                    return sources.value
                return []
                
            except ApiException as e:
                if e.status == 404:
                    # This is expected when no data sources exist yet
                    logger.info("No data sources found - this is normal for a new container")
                    return []
                else:
                    logger.error(f"Failed to list data sources: {e}")
                    raise
                
        except Exception as e:
            logger.error(f"Unexpected error listing data sources: {e}")
            raise

    def create_data_source(self, name="test_source", transaction=None):
        """Create a data source in container with verification and rollback"""
        retry_count = int(os.getenv('DEEP_LYNX_RETRY_COUNT', '3'))
        created_id = None
        
        try:
            logger.debug(f"Creating data source '{name}' in container {self.container_id}")
            
            # Pre-creation verification
            existing_sources = self.list_data_sources()
            initial_count = len(existing_sources)
            logger.debug(f"Initial data source count: {initial_count}")
            
            request = deep_lynx.CreateDataSourceRequest(
                name=name,
                adapter_type="standard",
                active=True,
                config={
                    "data_format": "json",
                    "type": "manual",
                    "options": {},
                    "unique_identifier_key": "id",
                    "chunk_size": 1000,
                    "polling_interval": 60000
                }
            )
            
            # Retry loop for transient failures
            for attempt in range(retry_count):
                try:
                    logger.debug(f"Create attempt {attempt + 1}/{retry_count}")
                    datasource = self.datasources_api.create_data_source(
                        container_id=self.container_id,
                        body=request
                    )
                    
                    if datasource and hasattr(datasource, 'value'):
                        created_id = datasource.value.id
                        logger.info(f"Created data source: {datasource.value.name} (ID: {created_id})")
                        
                        # Verify creation with multiple checks
                        verification_success = self._verify_data_source_creation(
                            created_id, name, initial_count
                        )
                        
                        if verification_success:
                            # Add to transaction if provided
                            if transaction:
                                transaction.operations.append({
                                    'type': 'create_data_source',
                                    'result': datasource.value,
                                    'timestamp': datetime.now()
                                })
                            return datasource.value
                        else:
                            raise ValueError("Data source creation verification failed")
                            
                    break  # Success, exit retry loop
                    
                except ApiException as e:
                    if e.status in [408, 429, 500, 502, 503, 504]:  # Retryable errors
                        if attempt < retry_count - 1:
                            wait_time = (attempt + 1) * 2  # Exponential backoff
                            logger.warning(f"Retryable error: {e}. Retrying in {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                    raise  # Last attempt failed or non-retryable error
                    
        except Exception as e:
            logger.error(f"Failed to create data source: {e}")
            if created_id:
                self._rollback_data_source_creation(created_id)
            raise

    def _verify_data_source_creation(self, source_id, name, initial_count):
        """Comprehensive verification of data source creation"""
        try:
            # 1. Verify retrievable
            retrieved = self.datasources_api.retrieve_data_source(
                container_id=self.container_id,
                data_source_id=source_id
            )
            if not retrieved or not hasattr(retrieved, 'value'):
                logger.error("Failed to retrieve created data source")
                return False
                
            # 2. Verify attributes
            if retrieved.value.name != name:
                logger.error(f"Name mismatch: {retrieved.value.name} != {name}")
                return False
                
            # 3. Verify count increased
            current_sources = self.list_data_sources()
            if len(current_sources) != initial_count + 1:
                logger.error(f"Source count mismatch: {len(current_sources)} != {initial_count + 1}")
                return False
                
            # 4. Verify status
            if not retrieved.value.active:
                logger.error("Data source is not active")
                return False
                
            logger.debug("All verification checks passed")
            return True
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False

    def _rollback_data_source_creation(self, source_id):
        """Rollback a failed data source creation"""
        try:
            logger.warning(f"Rolling back data source creation for ID: {source_id}")
            
            # First deactivate
            try:
                self.datasources_api.set_data_source_inactive(
                    container_id=self.container_id,
                    data_source_id=source_id
                )
                logger.debug("Data source deactivated")
            except Exception as e:
                logger.error(f"Failed to deactivate during rollback: {e}")
            
            # Then archive/delete
            try:
                self.datasources_api.archive_data_source(
                    container_id=self.container_id,
                    data_source_id=source_id,
                    archive="true",
                    force_delete="true",
                    remove_data="true"
                )
                logger.info(f"Successfully rolled back data source {source_id}")
            except Exception as e:
                logger.error(f"Failed to archive during rollback: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            logger.error("Manual cleanup may be required")
            raise

    def create_manual_import(self, source_id, data):
        """Create a manual import with data"""
        try:
            logger.debug(f"Creating manual import for source {source_id}")
            logger.debug(f"Import data: {data}")
            
            response = self.datasources_api.create_manual_import(
                container_id=self.container_id,
                data_source_id=source_id,
                body=data
            )
            
            if response and hasattr(response, 'value'):
                logger.info(f"Created import: {response.value.id}")
                return response.value
            raise ValueError("Invalid response from create_manual_import")
                
        except Exception as e:
            logger.error(f"Failed to create import: {e}")
            raise

    def list_metatypes(self):
        """List all metatypes in container 1"""
        try:
            metatypes = self.metatypes_api.list_metatypes(self.container_id)
            logger.info(f"Found {len(metatypes.value)} metatypes")
            for metatype in metatypes.value:
                logger.info(f"Metatype: {metatype.name} (ID: {metatype.id})")
            return metatypes.value
        except ApiException as e:
            logger.error(f"Failed to list metatypes: {e}")
            raise

    def check_server_health(self):
        """Check if Deep Lynx server is accessible"""
        try:
            response = requests.get(f"{self.configuration.host}/health")
            return response.status_code == 200
        except:
            return False

    def test_data_source_operations(self):
        """Test comprehensive data source operations"""
        # Add update operation
        updated_source = self.update_data_source(
            datasource_id=self.test_source_id,
            name="updated_test_source"
        )
        
        # Add delete operation
        self.delete_data_source(self.test_source_id)
        
        # Add validation tests
        self.validate_data_source_config(self.test_source_id)

    def test_metatype_operations(self):
        """Test metatype CRUD operations"""
        # Create metatype
        new_metatype = self.create_metatype({
            "name": "TestMetatype",
            "description": "Test metatype for integration testing"
        })
        
        # Update metatype
        self.update_metatype(new_metatype.id, {"description": "Updated description"})
        
        # Delete metatype
        self.delete_metatype(new_metatype.id)

    def test_error_handling(self):
        """Test error handling scenarios"""
        # Test invalid authentication
        with self.assertRaises(ApiException):
            self.authenticate_with_invalid_credentials()
        
        # Test invalid data source operations
        with self.assertRaises(ApiException):
            self.create_data_source(invalid_config={})

    def test_relationships(self):
        """Test metatype relationships"""
        # Create relationship between metatypes
        relationship = self.create_metatype_relationship(
            source_id=self.source_metatype_id,
            destination_id=self.dest_metatype_id
        )
        
        # Validate relationship
        self.validate_relationship(relationship.id)

    def test_data_operations(self):
        """Test data import/export operations"""
        # Test batch import
        self.test_batch_import(self.test_source_id)
        
        # Test data export
        exported_data = self.export_data(self.test_source_id)
        self.validate_exported_data(exported_data)

    def update_data_source(self, source_id, name):
        """Update a data source"""
        try:
            logger.debug(f"Updating data source {source_id} with name {name}")
            
            request = deep_lynx.UpdateDataSourceRequest(
                name=name,
                adapter_type="standard",
                active=True,
                config={
                    "data_format": "json",
                    "type": "manual",
                    "options": {}
                }
            )
            
            response = self.datasources_api.update_data_source(
                container_id=self.container_id,
                data_source_id=source_id,
                body=request
            )
            
            if response and hasattr(response, 'value'):
                logger.info(f"Updated data source: {response.value.name}")
                return response.value
            raise ValueError("Invalid response from update_data_source")
                
        except Exception as e:
            logger.error(f"Failed to update data source: {e}")
            raise

    def delete_data_source(self, source_id):
        """Delete a data source with safety checks"""
        try:
            logger.debug(f"Deleting data source {source_id}")
            
            # First deactivate the source
            self.datasources_api.set_data_source_inactive(
                container_id=self.container_id,
                data_source_id=source_id
            )
            
            # Then archive it
            response = self.datasources_api.archive_data_source(
                container_id=self.container_id,
                data_source_id=source_id,
                archive="true",
                force_delete="true",
                remove_data="true"
            )
            
            # Verify deletion
            try:
                self.datasources_api.retrieve_data_source(
                    container_id=self.container_id,
                    data_source_id=source_id
                )
                logger.error(f"Data source {source_id} still exists after deletion")
                raise ValueError("Deletion verification failed")
            except ApiException as e:
                if e.status == 404:
                    logger.info(f"Successfully deleted data source {source_id}")
                    return True
                raise
                
        except Exception as e:
            logger.error(f"Failed to delete data source: {e}")
            raise

    def create_metatype(self, config: dict):
        """Create a new metatype"""
        try:
            metatype = self.metatypes_api.create_metatype(
                container_id=self.container_id,
                body=deep_lynx.CreateMetatypeRequest(
                    name=config["name"],
                    description=config["description"]
                )
            )
            logger.info(f"Created metatype: {metatype.value.name} (ID: {metatype.value.id})")
            return metatype.value
        except ApiException as e:
            logger.error(f"Failed to create metatype: {e}")
            raise

    def update_metatype(self, metatype_id: int, updates: dict):
        """Update an existing metatype"""
        try:
            updated = self.metatypes_api.update_metatype(
                container_id=self.container_id,
                metatype_id=metatype_id,
                body=deep_lynx.UpdateMetatypeRequest(**updates)
            )
            logger.info(f"Updated metatype {metatype_id}")
            return updated.value
        except ApiException as e:
            logger.error(f"Failed to update metatype: {e}")
            raise

    def delete_metatype(self, metatype_id: int):
        """Delete a metatype"""
        try:
            self.metatypes_api.delete_metatype(
                container_id=self.container_id,
                metatype_id=metatype_id
            )
            logger.info(f"Deleted metatype {metatype_id}")
        except ApiException as e:
            logger.error(f"Failed to delete metatype: {e}")
            raise

    def create_metatype_relationship(self, source_id: int, destination_id: int):
        """Create a relationship between metatypes"""
        try:
            relationship = self.relationships_api.create_metatype_relationship(
                container_id=self.container_id,
                body=deep_lynx.CreateMetatypeRelationshipRequest(
                    name=f"test_relationship_{os.urandom(4).hex()}",
                    description="Test relationship",
                    origin_metatype_id=source_id,
                    destination_metatype_id=destination_id
                )
            )
            logger.info(f"Created relationship between metatypes {source_id} and {destination_id}")
            return relationship.value
        except ApiException as e:
            logger.error(f"Failed to create metatype relationship: {e}")
            raise

    def test_batch_import(self, datasource_id: int):
        """Test batch data import"""
        try:
            batch_data = [
                {"key1": "value1", "timestamp": "2024-01-01T00:00:00Z"},
                {"key2": "value2", "timestamp": "2024-01-01T00:00:00Z"}
            ]
            result = self.datasources_api.create_manual_import(
                body=batch_data,
                container_id=self.container_id,
                data_source_id=datasource_id
            )
            logger.info(f"Completed batch import for data source {datasource_id}")
            return result
        except ApiException as e:
            logger.error(f"Failed to perform batch import: {e}")
            raise

    def export_data(self, datasource_id: int):
        """Export data from a data source"""
        try:
            result = self.datasources_api.retrieve_data_source_data(
                container_id=self.container_id,
                data_source_id=datasource_id
            )
            logger.info(f"Exported data from data source {datasource_id}")
            return result.value
        except ApiException as e:
            logger.error(f"Failed to export data: {e}")
            raise

    def validate_container(self):
        """Validate container exists and is accessible"""
        try:
            # First authenticate if needed
            if 'Authorization' not in self.api_client.default_headers:
                self.authenticate()
                
            container = self.containers_api.retrieve_container(self.container_id)
            if not container or not container.value:
                logger.error("Container validation failed: Empty response")
                return False
                
            # Debug log the actual container structure
            logger.debug(f"Container structure: {dir(container.value)}")
            logger.debug(f"Container value: {container.value}")
            
            # Basic validation - just check if container exists and is accessible
            if hasattr(container.value, 'id'):
                logger.info(f"Successfully validated container {container.value.id}")
                return True
                
            logger.error("Container validation failed: Invalid container structure")
            return False
                
        except ApiException as e:
            if e.status == 401:
                logger.error("Authentication required for container validation")
                try:
                    self.authenticate()
                    return self.validate_container()
                except Exception as auth_e:
                    logger.error(f"Re-authentication failed: {auth_e}")
                    return False
            else:
                logger.error(f"Container validation failed: {e.body}")
                return False

def main():
    """Enhanced main function with transactions and metrics"""
    tester = DeepLynxTester()
    
    try:
        with tester.transaction("Data Source Creation Test") as transaction:
            # Validate container first
            if not tester.validate_container():
                raise ValueError("Container validation failed")

            # List existing sources
            initial_sources = tester.list_data_sources()
            logger.info(f"Found {len(initial_sources)} existing data sources")
            
            # Create new source within transaction
            new_source = tester.create_data_source(
                name=f"test_source_{os.urandom(4).hex()}",
                transaction=transaction
            )
            
            # Verify creation
            current_sources = tester.list_data_sources()
            if len(current_sources) != len(initial_sources) + 1:
                raise ValueError("Data source count mismatch after creation")
                
            logger.info("All operations completed successfully")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    main() 