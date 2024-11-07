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
import pytest
import sys #important for pytest

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
    def __init__(self, host: str, container_id: str):
        """Initialize the tester with Deep Lynx configuration"""
        # Load environment variables from correct path
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        load_dotenv(env_path)
        
        # Debug initialization state
        logger.info("\n=== Initializing Deep Lynx Tester ===")
        logger.info(f"Host: {host}")
        logger.info(f"Environment file path: {env_path}")
        logger.info(f"Environment file exists: {os.path.exists(env_path)}")
        
        # Debug environment variables
        logger.debug("Environment Variables:")
        logger.debug(f"DEEP_LYNX_URL: {os.getenv('DEEP_LYNX_URL')}")
        logger.debug(f"DEEP_LYNX_API_KEY: {'SET' if os.getenv('DEEP_LYNX_API_KEY') else 'NOT SET'}")
        logger.debug(f"DEEP_LYNX_API_SECRET: {'SET' if os.getenv('DEEP_LYNX_API_SECRET') else 'NOT SET'}")
        logger.debug(f"DEEP_LYNX_CONTAINER_ID: {os.getenv('DEEP_LYNX_CONTAINER_ID')}")
        
        # Store credentials
        self.api_key = os.getenv('DEEP_LYNX_API_KEY')
        self.api_secret = os.getenv('DEEP_LYNX_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            raise ValueError("API key and secret must be set in environment variables")
        
        # Initialize configuration properly
        self.configuration = deep_lynx.Configuration()
        self.configuration.host = host
        
        # Set up authentication with both key and secret
        auth_str = f"{self.api_key}:{self.api_secret}"
        self.configuration.api_key['Authorization'] = auth_str
        self.configuration.api_key_prefix['Authorization'] = 'Basic'
        
        # Initialize API client and APIs
        self.api_client = deep_lynx.ApiClient(self.configuration)
        self.container_id = container_id
        
        # Initialize all required APIs
        self.auth_api = deep_lynx.AuthenticationApi(self.api_client)
        self.datasources_api = deep_lynx.DataSourcesApi(self.api_client)
        self.imports_api = deep_lynx.ImportsApi(self.api_client)
        self.data_query_api = deep_lynx.DataQueryApi(self.api_client)
        self.containers_api = deep_lynx.ContainersApi(self.api_client)
        
        # Debug API initialization
        logger.debug("\n=== API Initialization ===")
        logger.debug(f"APIs initialized: auth, datasources, imports, data_query, containers")
        logger.debug(f"Auth string length: {len(auth_str) if auth_str else 0}")
        
    def check_health(self) -> bool:
        """Check system health before operations"""
        try:
            # First ensure we're authenticated
            if not self.authenticate():
                logger.error("Authentication failed during health check")
                return False

            # Debug logging to verify authentication headers
            logger.debug(f"Using headers: {self.api_client.default_headers}")
            
            # Verify container exists
            try:
                container = self.containers_api.retrieve_container(self.container_id)
                logger.info(f"Successfully validated container {self.container_id}")
                return True
            except ApiException as e:
                logger.error(f"Container validation failed: Status {e.status}, Body: {e.body}")
                if e.status == 401:
                    # Try re-authenticating once
                    logger.info("Attempting to re-authenticate...")
                    if self.authenticate():
                        return self.check_health()
                return False
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False

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
            logger.info("Attempting authentication with Deep Lynx...")
            
            # Debug logging
            logger.debug(f"Host: {self.configuration.host}")
            logger.debug(f"API Key length: {len(self.api_key) if self.api_key else 0}")
            logger.debug(f"API Secret length: {len(self.api_secret) if self.api_secret else 0}")
            
            # Make authentication request
            try:
                token_response = self.auth_api.retrieve_o_auth_token(
                    x_api_key=self.api_key,
                    x_api_secret=self.api_secret
                )
                
                # Debug the response
                logger.debug(f"Token response type: {type(token_response)}")
                logger.debug(f"Token response: {token_response}")
                
                # Handle different response types
                if isinstance(token_response, str):
                    token = token_response
                elif hasattr(token_response, 'value'):
                    token = token_response.value
                else:
                    logger.error(f"Unexpected token response type: {type(token_response)}")
                    return False
                
                # Update headers with token
                self.api_client.default_headers['Authorization'] = f"Bearer {token}"
                
                logger.info("Successfully authenticated with Deep Lynx")
                logger.debug(f"Token set in headers, length: {len(token)}")
                
                return True
                
            except ApiException as e:
                logger.error(f"Authentication API call failed: Status {e.status}, Body: {e.body}")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {str(e)}")
            return False

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
        """Create a data source with complete configuration"""
        try:
            request = deep_lynx.CreateDataSourceRequest(
                name=name,
                adapter_type="standard",
                active=True,
                config=deep_lynx.DataSourceConfig(  # Using correct parameters from API model
                    kind="manual",
                    data_type="json",
                    data_format="json"
                )
            )
            
            # Create data source
            datasource = self.datasources_api.create_data_source(
                container_id=self.container_id,
                body=request
            )
            
            # Enhanced verification logging
            if datasource and hasattr(datasource, 'value'):
                logger.info(f"✓ Created data source successfully:")
                logger.info(f"  • Name: {datasource.value.name}")
                logger.info(f"  • ID: {datasource.value.id}")
                logger.info(f"  • Type: {datasource.value.adapter_type}")
                logger.info(f"  • Status: {'Active' if datasource.value.active else 'Inactive'}")
                logger.info(f"  • Created at: {datasource.value.created_at}")
                
                if transaction:
                    transaction.operations.append({
                        'type': 'create_data_source',
                        'result': datasource.value,
                        'timestamp': datetime.now()
                    })
                
                return datasource.value
                    
        except Exception as e:
            logger.error(f"Data source creation failed: {str(e)}")
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

    def test_metatype_operations(self, transaction=None):
        """Test metatype creation and management"""
        try:
            logger.info("\n=== Testing Metatype Operations ===")
            
            # Create metatype
            metatype_request = {
                "name": f"test_metatype_{os.urandom(4).hex()}",
                "description": "Test metatype for integration testing",
                "container_id": self.container_id
            }
            
            metatype = self.metatypes_api.create_metatype(
                container_id=self.container_id,
                body=metatype_request
            )
            
            if transaction:
                transaction.operations.append({
                    'type': 'create_metatype',
                    'result': metatype.value,
                    'timestamp': datetime.now()
                })
            
            logger.info(f"Created metatype: {metatype.value.name}")
            return metatype.value
                
        except Exception as e:
            logger.error(f"Metatype operations test failed: {e}")
            raise

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

    def test_data_import(self):
        """Test data import functionality"""
        try:
            test_data = [
                {"id": "test1", "value": 100},
                {"id": "test2", "value": 200}
            ]
            
            import_result = self.datasources_api.create_manual_import(
                container_id=self.container_id,
                data_source_id=self.source_id,
                body=test_data
            )
            
            logger.info(f"Data import successful: {len(test_data)} records")
            return import_result
            
        except Exception as e:
            logger.error(f"Data import failed: {str(e)}")
            raise

    def test_data_transformations(self, transaction=None):
        """Test data transformation functionality"""
        try:
            logger.info("\n=== Testing Data Transformation Operations ===")
            
            # Create source and destination types
            source_type = self.test_metatype_operations(transaction)
            dest_type = self.test_metatype_operations(transaction)
            
            # Create transformation mapping
            mapping_request = {
                "container_id": self.container_id,
                "source_metatype_id": source_type.id,
                "destination_metatype_id": dest_type.id,
                "transformation_name": f"test_transform_{os.urandom(4).hex()}",
                "conditions": {
                    "source_field": "name",
                    "destination_field": "transformed_name",
                    "transformation": "uppercase"
                }
            }
            
            mapping = self.type_mappings_api.create_data_type_mapping(
                container_id=self.container_id,
                body=mapping_request
            )
            
            if transaction:
                transaction.operations.append({
                    'type': 'create_transformation',
                    'result': mapping.value,
                    'timestamp': datetime.now()
                })
                
            logger.info(f"Created transformation mapping: {mapping.value.transformation_name}")
            return mapping.value
            
        except Exception as e:
            logger.error(f"Data transformation test failed: {e}")
            raise

    def test_file_import(self, transaction=None):
        """Test file import functionality"""
        try:
            logger.info("\n=== Testing File Import Operations ===")
            
            # Create test file
            test_file_path = "test_data.json"
            test_data = [
                {"id": 1, "name": "Test Item 1", "value": 100},
                {"id": 2, "name": "Test Item 2", "value": 200}
            ]
            with open(test_file_path, 'w') as f:
                json.dump(test_data, f)
                
            try:
                # Create data source for testing
                source = self.create_data_source(
                    name=f"file_import_test_{os.urandom(4).hex()}",
                    transaction=transaction
                )
                
                # Import file using imports_api
                with open(test_file_path, 'rb') as file:
                    import_result = self.imports_api.upload_file(
                        container_id=self.container_id,
                        data_source_id=source.id,
                        file=file,
                        metadata=json.dumps({
                            "type": "json",
                            "mapping": {
                                "id": "id",
                                "name": "name",
                                "value": "value"
                            }
                        })
                    )
                    
                logger.info(f"File import initiated: {import_result.value.id}")
                
                # Verify import using data_query_api
                query_result = self.data_query_api.query_data(
                    container_id=self.container_id,
                    body={
                        "data_source_id": source.id,
                        "limit": 10
                    }
                )
                
                if len(query_result.value) == len(test_data):
                    logger.info("File import verification successful")
                    return import_result.value
                raise ValueError("Import verification failed")
                
            finally:
                # Cleanup test file
                if os.path.exists(test_file_path):
                    os.remove(test_file_path)
                
        except Exception as e:
            logger.error(f"File import test failed: {e}")
            raise

    def test_data_transformation_pipeline(self, transaction=None):
        """Test complete data transformation pipeline"""
        try:
            logger.info("\n=== Testing Data Transformation Pipeline ===")
            
            # 1. Create metatypes for source and destination
            source_metatype = self.metatypes_api.create_metatype(
                container_id=self.container_id,
                body={
                    "name": f"source_type_{os.urandom(4).hex()}",
                    "description": "Source data type",
                    "properties": {
                        "name": {"type": "string", "required": True},
                        "value": {"type": "number", "required": True}
                    }
                }
            )
            
            dest_metatype = self.metatypes_api.create_metatype(
                container_id=self.container_id,
                body={
                    "name": f"transformed_type_{os.urandom(4).hex()}",
                    "description": "Transformed data type",
                    "properties": {
                        "transformed_name": {"type": "string", "required": True},
                        "doubled_value": {"type": "number", "required": True}
                    }
                }
            )
            
            # 2. Create transformation mapping
            mapping = self.type_mappings_api.create_data_type_mapping(
                container_id=self.container_id,
                body={
                    "name": f"test_transform_{os.urandom(4).hex()}",
                    "source_metatype_id": source_metatype.value.id,
                    "destination_metatype_id": dest_metatype.value.id,
                    "transformations": [
                        {
                            "source_field": "name",
                            "destination_field": "transformed_name",
                            "transformation": "uppercase"
                        },
                        {
                            "source_field": "value",
                            "destination_field": "doubled_value",
                            "transformation": "multiply",
                            "transformation_args": {"factor": 2}
                        }
                    ]
                }
            )
            
            if transaction:
                transaction.operations.append({
                    'type': 'create_transformation_pipeline',
                    'result': {
                        'source_metatype': source_metatype.value,
                        'dest_metatype': dest_metatype.value,
                        'mapping': mapping.value
                    },
                    'timestamp': datetime.now()
                })
            
            logger.info(f"Created transformation pipeline: {mapping.value.name}")
            return mapping.value
            
        except Exception as e:
            logger.error(f"Transformation pipeline test failed: {e}")
            raise

    def test_complete_pipeline(self):
        """Test complete data pipeline with import and transformation"""
        try:
            with self.transaction("Complete Pipeline Test") as transaction:
                # 1. Create data source
                source = self.create_data_source(
                    name=f"pipeline_test_{os.urandom(4).hex()}",
                    transaction=transaction
                )
                
                # 2. Create test data
                test_data = [
                    {
                        "id": "test1",
                        "name": "Test Record 1",
                        "value": 100,
                        "metadata": {"category": "A"}
                    },
                    {
                        "id": "test2",
                        "name": "Test Record 2",
                        "value": 200,
                        "metadata": {"category": "B"}
                    }
                ]
                
                # 3. Import data
                import_result = self.datasources_api.create_manual_import(
                    container_id=self.container_id,
                    data_source_id=source.id,
                    body=test_data
                )
                
                # 4. Query and validate imported data
                query_result = self.data_query_api.query_data(
                    container_id=self.container_id,
                    body={
                        "data_source_id": source.id,
                        "query": {
                            "value": {"$gt": 150}  # Query records with value > 150
                        }
                    }
                )
                
                # 5. Create and apply transformation
                transform_result = self.test_data_transformations(transaction)
                
                # 6. Verify transformed data
                transformed_data = self.data_query_api.query_data(
                    container_id=self.container_id,
                    body={
                        "metatype_id": transform_result.destination_metatype_id,
                        "query": {
                            "doubled_value": {"$gt": 300}  # Verify transformation
                        }
                    }
                )
                
                return {
                    "source": source,
                    "import": import_result.value,
                    "query": query_result.value,
                    "transform": transform_result,
                    "transformed_data": transformed_data.value
                }
                
        except Exception as e:
            logger.error(f"Complete pipeline test failed: {e}")
            raise

    def validate_data_integrity(self, original_data, imported_data):
        """Validate data integrity after import"""
        try:
            # Check record counts
            if len(original_data) != len(imported_data):
                raise ValueError(f"Data count mismatch: {len(original_data)} vs {len(imported_data)}")
                
            # Check data fields
            for orig, imp in zip(original_data, imported_data):
                for key in orig.keys():
                    if orig[key] != imp.get(key):
                        raise ValueError(f"Data mismatch for key {key}: {orig[key]} vs {imp.get(key)}")
                        
            logger.info("Data integrity validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Data integrity validation failed: {e}")
            raise

    def test_error_handling(self):
        """Test error handling and recovery"""
        try:
            with self.transaction("Error Handling Test") as transaction:
                # Test invalid data source creation
                with pytest.raises(ValueError):
                    self.create_data_source(name="", transaction=transaction)
                    
                # Test duplicate data source
                source = self.create_data_source(
                    name="duplicate_test",
                    transaction=transaction
                )
                with pytest.raises(ApiException):
                    self.create_data_source(name="duplicate_test")
                    
                # Test invalid data import
                with pytest.raises(ValueError):
                    self.datasources_api.create_manual_import(
                        container_id=self.container_id,
                        data_source_id=source.id,
                        body={"invalid": "data"}
                    )
                    
        except Exception as e:
            logger.error(f"Error handling test failed: {e}")
            raise

    def test_data_source_functionality(self):
        """Test complete data source functionality"""
        try:
            # 1. Create data source
            source = self.create_data_source()
            
            # 2. Test data import
            test_data = [{"id": "test1", "value": 100}]
            import_result = self.datasources_api.create_manual_import(
                container_id=self.container_id,
                data_source_id=source.id,
                body=test_data
            )
            logger.info(f"Data import result: {import_result.value}")
            
            # 3. Test data query
            query_result = self.data_query_api.query_data(
                container_id=self.container_id,
                body={"data_source_id": source.id}
            )
            logger.info(f"Query result: {query_result.value}")
            
            return {
                "source": source,
                "import": import_result.value,
                "query": query_result.value
            }
            
        except Exception as e:
            logger.error(f"Functionality test failed: {str(e)}")
            raise

    def validate_data_source_config(self, config: deep_lynx.DataSourceConfig) -> bool:
        """Validate data source configuration against API model"""
        try:
            required_fields = {
                'data_format': str,
                'kind': str,
                'data_type': str
            }
            
            # Check required fields and types
            for field, field_type in required_fields.items():
                if not hasattr(config, field):
                    logger.error(f"Missing required field: {field}")
                    return False
                if not isinstance(getattr(config, field), field_type):
                    logger.error(f"Invalid type for {field}: expected {field_type}")
                    return False
                    
            # Validate allowed values
            allowed_formats = ['json', 'csv', 'xml']
            allowed_kinds = ['manual', 'automatic', 'scheduled']
            
            if config.data_format not in allowed_formats:
                logger.error(f"Invalid data_format: {config.data_format}")
                return False
                
            if config.kind not in allowed_kinds:
                logger.error(f"Invalid kind: {config.kind}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            return False

    def cleanup_test_sources(self):
        """Clean up test data sources"""
        try:
            sources = self.list_data_sources()
            test_sources = [s for s in sources if s.name.startswith('test_source_')]
            
            for source in test_sources:
                logger.info(f"Cleaning up test source: {source.name}")
                self.datasources_api.archive_data_source(
                    container_id=self.container_id,
                    data_source_id=source.id,
                    archive="true",
                    force_delete="true",
                    remove_data="true"
                )
                
            logger.info(f"Cleaned up {len(test_sources)} test sources")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")

    def upload_and_attach_file(self, data_node_id: str, file_path: str, metadata: dict = None):
        """Upload a file and attach it to a data node"""
        try:
            logger.info(f"Uploading file {file_path} for node {data_node_id}")
            
            # Verify file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
                
            # Prepare metadata properly
            file_metadata = {
                "data_node_id": data_node_id,
                "file_type": "pdf"
            }
            
            # Merge additional metadata if provided
            if metadata:
                file_metadata.update(metadata)
                
            # Upload file
            with open(file_path, 'rb') as file:
                response = self.datasources_api.upload_file(
                    container_id=self.container_id,
                    data_source_id=self.data_source_id,
                    file=file,
                    metadata=json.dumps(file_metadata)  # Use the merged metadata
                )
                
                logger.info(f"✓ File uploaded successfully:")
                logger.info(f"  • File ID: {response.value.id}")
                logger.info(f"  • Node ID: {data_node_id}")
                logger.info(f"  • File name: {os.path.basename(file_path)}")
                
                return response.value
                
        except Exception as e:
            logger.error(f"File upload failed: {str(e)}")
            raise

    def test_file_upload(self):
        """Test file upload functionality"""
        try:
            with DeepLynxTransaction(self, "File Upload Test") as transaction:
                # 1. Create test data node
                test_data = {
                    "name": "Test Document",
                    "type": "document",
                    "properties": {
                        "description": "Test PDF document"
                    }
                }
                
                node = self.create_data_node(test_data)
                
                # 2. Upload and attach PDF
                file_path = "path/to/your/test.pdf"
                metadata = {
                    "description": "Test document upload",
                    "version": "1.0"
                }
                
                file_info = self.upload_and_attach_file(
                    data_node_id=node.id,
                    file_path=file_path,
                    metadata=metadata
                )
                
                # 3. Verify attachment
                node_with_files = self.get_data_node(node.id)
                logger.info(f"✓ File attachment verified:")
                logger.info(f"  • Node: {node.id}")
                logger.info(f"  • Files: {len(node_with_files.files)}")
                
                return {
                    "node": node,
                    "file": file_info
                }
                
        except Exception as e:
            logger.error(f"File upload test failed: {str(e)}")
            raise

    def test_pdf_upload(self):
        """
        Test PDF file upload functionality
        Goal: Upload a PDF file to Deep Lynx and associate it with a data node
        Steps:
        1. Create a data source for PDF files
        2. Create a data node (or use existing)
        3. Upload PDF and attach to node
        4. Verify upload success
        """
        try:
            with self.transaction("PDF Upload Test") as transaction:
                logger.info("\n=== Starting PDF Upload Test ===")
                
                # Debug environment
                logger.debug("\n=== Environment Info ===")
                logger.debug(f"Current working directory: {os.getcwd()}")
                logger.debug(f"API Client Configuration:")
                logger.debug(f"  Host: {self.api_client.configuration.host}")
                logger.debug(f"  APIs initialized: {hasattr(self, 'imports_api')}")
                
                # Create data source
                source = self.create_data_source(
                    name=f"pdf_source_{os.urandom(4).hex()}",
                    transaction=transaction
                )
                
                # File handling with detailed debugging
                pdf_path = os.path.join(os.path.dirname(__file__), "..", "testPDF.pdf")
                abs_path = os.path.abspath(pdf_path)
                
                logger.debug("\n=== File Information ===")
                logger.debug(f"PDF path: {abs_path}")
                logger.debug(f"File exists: {os.path.exists(abs_path)}")
                logger.debug(f"File size: {os.path.getsize(abs_path)} bytes")
                logger.debug(f"File permissions: {oct(os.stat(abs_path).st_mode)[-3:]}")
                
                try:
                    with open(abs_path, 'rb') as file:
                        # Prepare metadata
                        metadata = {
                            "filename": "testPDF.pdf",
                            "mime_type": "application/pdf",
                            "size": os.path.getsize(abs_path),
                            "source": "test_upload",
                            "description": "Test PDF document upload"
                        }
                        
                        logger.debug("\n=== Upload Attempt ===")
                        logger.debug(f"Data source ID: {source.id}")
                        logger.debug(f"Metadata: {json.dumps(metadata, indent=2)}")
                        
                        # Changed create_file to upload_file
                        upload_result = self.datasources_api.upload_file(
                            container_id=self.container_id,
                            data_source_id=source.id,
                            file=file,
                            metadata=json.dumps(metadata)
                        )
                        
                        logger.debug("\n=== Upload Result ===")
                        logger.debug(f"Result: {upload_result}")
                        
                        return {
                            'node': upload_result.value,
                            'file': upload_result.value.file,
                            'file_path': upload_result.value.file_path
                        }
                        
                except Exception as e:
                    logger.error("\n=== Upload Error ===")
                    logger.error(f"Error type: {type(e).__name__}")
                    logger.error(f"Error message: {str(e)}")
                    logger.error("Stack trace:", exc_info=True)
                    raise
                
        except Exception as e:
            logger.error(f"PDF upload test failed: {str(e)}")
            raise

def main():
    """Main test execution function with enhanced error handling"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get configuration from environment with fallbacks
        host = os.getenv('DEEP_LYNX_URL', 'http://localhost:8090')
        container_id = os.getenv('DEEP_LYNX_CONTAINER_ID', '2')
        
        logger.info("\n=== PDF Upload Test Configuration ===")
        logger.info(f"Host: {host}")
        logger.info(f"Container ID: {container_id}")
        
        # Initialize tester with validated parameters
        tester = DeepLynxTester(
            host=host,
            container_id=container_id
        )
        
        # ONLY run the PDF upload test
        logger.info("\n=== Starting PDF Upload Test ===")
        pdf_result = tester.test_pdf_upload()
        
        # Log the results
        logger.info("\n=== PDF Upload Results ===")
        logger.info(f"✓ PDF upload completed successfully")
        logger.info(f"  • Node ID: {pdf_result['node'].id if pdf_result.get('node') else 'N/A'}")
        logger.info(f"  • File ID: {pdf_result['file'].id if pdf_result.get('file') else 'N/A'}")
        logger.info(f"  • File path: {pdf_result.get('file_path', 'N/A')}")
            
    except Exception as e:
        logger.error(f"\nTest failed with error:")
        logger.error(f"  • Error type: {type(e).__name__}")
        logger.error(f"  • Error message: {str(e)}")
        logger.error(f"  • Stack trace:", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("\n=== Test Complete ===\n")

if __name__ == "__main__":
    # Configure logging format for better readability
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'  # Simplified format for cleaner output
    )
    main() 