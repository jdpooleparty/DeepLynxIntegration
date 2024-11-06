from deep_lynx import (
    Configuration,
    ApiClient,
    AuthenticationApi,
    ContainersApi,
    DataSourcesApi,
    DataTypeMappingsApi,
    MetatypesApi,
    MetatypeRelationshipsApi
)
from ..models.auth import DeepLynxAuth, DeepLynxResponse
from .config import get_settings
import logging
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)

class DeepLynxClient:
    """Enhanced Deep Lynx client with authentication handling"""
    def __init__(self):
        self.settings = get_settings()
        self._init_client()
        self.auth: Optional[DeepLynxAuth] = None

    def _init_client(self):
        """Initialize the Deep Lynx API client"""
        try:
            logger.info(f"Initializing Deep Lynx client with URL: {self.settings.deep_lynx_url}")
            logger.debug(f"Using container ID: {self.settings.deep_lynx_container_id}")
            
            # Log credentials (masked)
            logger.debug(f"API Key (masked): {'*' * len(self.settings.deep_lynx_api_key)}")
            logger.debug(f"API Secret (masked): {'*' * len(self.settings.deep_lynx_api_secret)}")
            
            # Create configuration
            self.config = Configuration()
            self.config.host = self.settings.deep_lynx_url
            self.config.verify_ssl = False
            
            # Set API keys
            self.config.api_key = {}
            self.config.api_key_prefix = {}
            
            # Set up API client
            self.api_client = ApiClient(configuration=self.config)
            
            # Set headers according to Deep Lynx example
            self.api_client.default_headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'x-api-key': self.settings.deep_lynx_api_key,
                'x-api-secret': self.settings.deep_lynx_api_secret
            }
            
            logger.debug("Headers set: %s", 
                {k: '***' if k in ['x-api-key', 'x-api-secret'] else v 
                 for k, v in self.api_client.default_headers.items()})
            
            # Initialize API instances
            self.auth_api = AuthenticationApi(self.api_client)
            self.containers_api = ContainersApi(self.api_client)
            self.datasources_api = DataSourcesApi(self.api_client)
            self.type_mappings_api = DataTypeMappingsApi(self.api_client)
            self.metatypes_api = MetatypesApi(self.api_client)
            self.relationships_api = MetatypeRelationshipsApi(self.api_client)
            
            # Store container ID
            self.container_id = self.settings.deep_lynx_container_id
            logger.info("Deep Lynx client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Deep Lynx client: {str(e)}")
            raise

    def authenticate(self) -> DeepLynxResponse:
        """Authenticate with Deep Lynx"""
        try:
            logger.debug("Starting authentication process")
            
            # Log request details (safely)
            logger.debug("Authentication request details:")
            logger.debug(f"URL: {self.config.host}/oauth/token")
            logger.debug("Headers: %s", 
                {k: '***' if k in ['x-api-key', 'x-api-secret'] else v 
                 for k, v in self.api_client.default_headers.items()})
            
            # Try direct token retrieval
            try:
                logger.debug("Requesting OAuth token...")
                token_response = self.auth_api.retrieve_o_auth_token(
                    x_api_key=self.settings.deep_lynx_api_key,
                    x_api_secret=self.settings.deep_lynx_api_secret,
                    x_api_expiry='1h'
                )
                logger.debug("Got token response")
                
                # The token response IS the token for this version of Deep Lynx
                token = str(token_response)
                logger.debug(f"Token received (length: {len(token)})")

                # Update headers with token
                self.api_client.default_headers['Authorization'] = f'Bearer {token}'
                logger.debug("Updated headers with token")

                # Store auth info - only pass required fields
                self.auth = DeepLynxAuth(
                    token=token,
                    expiry='1h'  # TODO: Get actual expiry from response
                )
                
                logger.info("Authentication successful")
                return DeepLynxResponse(
                    status="success",
                    message="Authenticated successfully",
                    data={"token_length": len(token)}
                )

            except Exception as auth_error:
                logger.error(f"Token retrieval failed: {str(auth_error)}")
                if hasattr(auth_error, 'body'):
                    logger.error(f"Error response body: {auth_error.body}")
                if hasattr(auth_error, 'headers'):
                    logger.error("Error response headers: %s", 
                        {k: v for k, v in auth_error.headers.items()})
                raise

        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return DeepLynxResponse(
                status="error",
                message=f"Authentication failed: {str(e)}"
            )

    def verify_connection(self) -> DeepLynxResponse:
        """Verify connection to Deep Lynx"""
        try:
            logger.debug("Verifying connection to Deep Lynx")
            
            # Try to list containers as a test - note: this is not an async call
            response = self.containers_api.list_containers()
            
            # Verify our container exists
            container_found = False
            if response and hasattr(response, 'value'):
                for container in response.value:
                    if str(container.id) == str(self.container_id):
                        container_found = True
                        break

            if not container_found:
                raise Exception(f"Container {self.container_id} not found")

            return DeepLynxResponse(
                status="success",
                message="Connection verified",
                data={"container_id": self.container_id}
            )

        except Exception as e:
            logger.error(f"Connection verification failed: {str(e)}")
            return DeepLynxResponse(
                status="error",
                message=f"Connection failed: {str(e)}"
            )

    def ensure_authenticated(self) -> bool:
        """Ensure client is authenticated"""
        if not self.auth:
            auth_response = self.authenticate()
            return auth_response.status == "success"
        return True

    async def upload_file(
        self, 
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upload a file to Deep Lynx"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # Ensure we're authenticated
            if not self.auth:
                await self._authenticate()

            # Prepare file upload
            with open(file_path, 'rb') as file:
                file_name = os.path.basename(file_path)
                
                # Create file upload request
                response = self.datasources_api.upload_file(
                    container_id=self.settings.DEEP_LYNX_CONTAINER_ID,
                    data_source_id="standard",  # Using standard data source
                    file=file,
                    metadata=metadata or {"filename": file_name}
                )
                
                logger.info(f"Successfully uploaded file: {file_name}")
                return response

        except Exception as e:
            logger.error(f"Failed to upload file: {str(e)}")
            raise

    async def associate_file_with_node(self, file_id: str, node_id: str) -> Dict[str, Any]:
        """
        Associate an uploaded file with a node in the ontology
        """
        try:
            # Ensure we're authenticated
            if not self.auth:
                await self._authenticate()

            # Create relationship between file and node
            response = self.containers_api.create_edge(
                container_id=self.settings.DEEP_LYNX_CONTAINER_ID,
                body={
                    "from_node": file_id,
                    "to_node": node_id,
                    "relationship_type": "ATTACHED_TO"  # You can customize this
                }
            )
            
            logger.info(f"Associated file {file_id} with node {node_id}")
            return response

        except Exception as e:
            logger.error(f"Failed to associate file with node: {str(e)}")
            raise

    async def get_node_files(self, node_id: str) -> Dict[str, Any]:
        """
        Get all files associated with a specific node
        """
        try:
            # Ensure we're authenticated
            if not self.auth:
                await self._authenticate()

            logger.debug(f"Querying files for node {node_id}")
            # Query for files attached to this node
            response = self.containers_api.list_node_edges(
                container_id=self.settings.DEEP_LYNX_CONTAINER_ID,
                node_id=node_id,
                relationship_type="ATTACHED_TO"
            )
            
            logger.info(f"Retrieved files for node {node_id}")
            return response

        except Exception as e:
            logger.error(f"Failed to get node files: {str(e)}")
            raise
        finally:
            logger.debug(f"Completed get_node_files request for node {node_id}")

    async def verify_container(self) -> bool:
        """Verify container exists and is accessible"""
        try:
            if not self.auth:
                await self._authenticate()
                
            container = self.containers_api.retrieve_container(
                self.settings.deep_lynx_container_id
            )
            
            # Use proper attribute access
            if not container or not container.value:
                logger.error("Container not found or invalid response")
                return False
                
            if not hasattr(container.value, 'active') or not container.value.active:
                logger.error("Container is not active")
                return False
                
            if not hasattr(container.value, 'permissions'):
                logger.error("No permissions attribute for container")
                return False
                
            logger.info(f"Successfully verified container {self.settings.deep_lynx_container_id}")
            return True
        except ApiException as e:
            if e.status == 401:
                logger.error("Authentication required - attempting to re-authenticate")
                try:
                    await self._authenticate()
                    return await self.verify_container()
                except Exception as auth_e:
                    logger.error(f"Re-authentication failed: {auth_e}")
                    return False
            else:
                logger.error(f"Container verification failed: {e.body}")
                return False

    async def _authenticate(self):
        """Internal authentication method"""
        auth_response = self.authenticate()
        if auth_response.status != "success":
            raise Exception("Authentication failed")
            
        # Verify container access after authentication
        if not await self.verify_container():
            raise Exception(f"Could not access container {self.container_id}")

    async def list_data_sources(self) -> Dict[str, Any]:
        """List all data sources"""
        try:
            if not self.auth:
                await self._authenticate()
            
            # Add container validation
            await self.validate_container_access()
            
            response = self.datasources_api.list_data_sources(
                container_id=self.settings.deep_lynx_container_id
            )
            return response
        except Exception as e:
            logger.error(f"Failed to list data sources: {str(e)}")
            raise

    async def create_data_source(self, data_source: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new data source with validation"""
        try:
            if not self.auth:
                await self._authenticate()
            
            # Validate and sanitize input
            sanitized_config = {
                "name": str(data_source.get("name", "")),
                "adapter_type": str(data_source.get("adapter_type", "standard")),
                "active": bool(data_source.get("active", True)),
                "data_format": str(data_source.get("data_format", "json")),
                "config": data_source.get("config", {})
            }
            
            # Ensure config is valid JSON
            if not isinstance(sanitized_config["config"], dict):
                sanitized_config["config"] = {}
            
            response = self.datasources_api.create_data_source(
                container_id=self.settings.deep_lynx_container_id,
                body=deep_lynx.CreateDataSourceRequest(**sanitized_config)
            )
            
            logger.debug(f"Create data source response: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to create data source: {str(e)}")
            raise

    async def get_data_source(self, datasource_id: str) -> Dict[str, Any]:
        """Get a specific data source"""
        try:
            if not self.auth:
                await self._authenticate()
            
            response = self.datasources_api.retrieve_data_source(
                container_id=self.settings.deep_lynx_container_id,
                data_source_id=datasource_id
            )
            return response
        except Exception as e:
            logger.error(f"Failed to get data source: {str(e)}")
            raise

    async def update_data_source(self, datasource_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a data source configuration"""
        try:
            if not self.auth:
                await self._authenticate()
            
            # Ensure proper configuration structure
            config = {
                "configuration": {
                    **updates,
                    "config": updates.get("config", {}),
                    "data_format": updates.get("data_format", "json")
                }
            }
            
            response = self.datasources_api.set_data_source_configuration(
                container_id=self.settings.deep_lynx_container_id,
                data_source_id=datasource_id,
                body=config
            )
            logger.debug(f"Data source update response: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to update data source: {str(e)}")
            raise

# Singleton instance
_client: Optional[DeepLynxClient] = None

def get_client() -> DeepLynxClient:
    """Get or create Deep Lynx client singleton"""
    global _client
    if _client is None:
        _client = DeepLynxClient()
    return _client