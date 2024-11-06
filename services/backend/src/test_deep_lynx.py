import deep_lynx
from deep_lynx.rest import ApiException
from pprint import pprint
import os
from dotenv import load_dotenv
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    def create_data_source(self, name="test_source"):
        """Create a data source in container"""
        try:
            # Debug log the request
            logger.debug(f"Creating data source '{name}' in container {self.container_id}")
            
            # Create request with correct parameters - removed container_id
            request = deep_lynx.CreateDataSourceRequest(
                name=name,
                adapter_type="standard",
                active=True,
                config={
                    "data_format": "json",
                    "type": "manual",
                    "options": {}
                }
            )
            
            # Create the data source
            datasource = self.datasources_api.create_data_source(
                body=request,
                container_id=self.container_id  # container_id goes here, not in request
            )
            
            if datasource and hasattr(datasource, 'value'):
                logger.info(f"Created data source: {datasource.value.name} (ID: {datasource.value.id})")
                return datasource.value
            else:
                logger.error("Data source creation returned invalid response")
                raise ValueError("Invalid response from create_data_source")
                
        except ApiException as e:
            if e.status == 404:
                logger.error(f"Container {self.container_id} not found")
            elif e.status == 403:
                logger.error("Permission denied creating data source")
            else:
                logger.error(f"Failed to create data source: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating data source: {e}")
            raise

    def create_manual_import(self, datasource_id, data):
        """Create a manual import with test data"""
        try:
            import_result = self.datasources_api.create_manual_import(
                body=data,
                container_id=self.container_id,
                data_source_id=datasource_id
            )
            logger.info(f"Successfully created manual import for data source {datasource_id}")
            return import_result
        except ApiException as e:
            logger.error(f"Failed to create manual import: {e}")
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

    def update_data_source(self, datasource_id: int, name: str):
        """Update an existing data source"""
        try:
            # First verify data source exists
            self.datasources_api.retrieve_data_source(
                container_id=self.container_id,
                data_source_id=datasource_id
            )
            
            # Format configuration according to API spec
            config = {
                "configuration": {  # Required wrapper
                    "name": name,
                    "adapter_type": "standard",
                    "active": True,
                    "config": {},  # Required even if empty
                    "data_format": "json"  # Required field we were missing
                }
            }
            
            updated = self.datasources_api.set_data_source_configuration(
                container_id=self.container_id,
                data_source_id=datasource_id,
                body=config
            )
            logger.info(f"Updated data source {datasource_id} to name: {name}")
            return updated.value
        except ApiException as e:
            if e.status == 404:
                logger.error(f"Data source {datasource_id} not found")
            elif e.status == 400:
                logger.error(f"Invalid configuration: {e.body}")
            elif e.status == 500:
                logger.error(f"Server error: {e.body}")
            raise

    def delete_data_source(self, datasource_id: int):
        """Delete a data source"""
        try:
            self.datasources_api.delete_data_source(
                container_id=self.container_id,
                data_source_id=datasource_id
            )
            logger.info(f"Deleted data source {datasource_id}")
        except ApiException as e:
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
    """Main test function"""
    tester = DeepLynxTester()
    
    try:
        # Add comprehensive container check
        if not tester.validate_container():
            logger.error("Container validation failed - stopping tests")
            return

        # Authentication test
        logger.info("\n=== Testing Authentication ===")
        token = tester.authenticate()
        
        # Data source operations
        logger.info("\n=== Testing Data Source Operations ===")
        
        # List existing sources
        existing_sources = tester.list_data_sources()
        logger.info(f"Found {len(existing_sources)} existing data sources")
        
        # Create a new data source
        logger.info("Creating new data source...")
        new_source = tester.create_data_source(name=f"test_source_{os.urandom(4).hex()}")
        
        # Verify the new source appears in listing
        updated_sources = tester.list_data_sources()
        logger.info(f"Found {len(updated_sources)} data sources after creation")
        
        # Test updating the data source
        logger.info("\n=== Testing Data Source Updates ===")
        updated_name = f"updated_source_{os.urandom(4).hex()}"
        tester.update_data_source(new_source.id, updated_name)
        
        # Test data import
        logger.info("\n=== Testing Data Import ===")
        test_data = [
            {"key": "value1", "timestamp": "2024-01-01T00:00:00Z"},
            {"key": "value2", "timestamp": "2024-01-01T00:00:01Z"}
        ]
        tester.create_manual_import(new_source.id, test_data)
        
        # Clean up (optional)
        if os.getenv('DEEP_LYNX_CLEANUP', 'false').lower() == 'true':
            logger.info("\n=== Cleaning Up ===")
            tester.delete_data_source(new_source.id)
            
        logger.info("\n=== All Tests Completed Successfully ===")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    main() 