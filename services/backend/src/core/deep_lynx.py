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
from typing import Optional

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
                token_response = self.auth_api.retrieve_o_auth_token(
                    x_api_key=self.settings.deep_lynx_api_key,
                    x_api_secret=self.settings.deep_lynx_api_secret,
                    x_api_expiry='1h'
                )
                logger.debug("Got token response")
                
                # The token response IS the token for this version of Deep Lynx
                token = str(token_response)
                logger.debug(f"Token length: {len(token)}")

                # Store auth info
                self.auth = DeepLynxAuth(
                    api_key=self.settings.deep_lynx_api_key,
                    api_secret=self.settings.deep_lynx_api_secret,
                    token=token,
                    container_id=self.container_id
                )

                # Update configuration and headers with token
                self.config.access_token = token
                self.api_client.default_headers.update({
                    'Authorization': f'Bearer {token}'
                })

                logger.debug("Successfully authenticated with Deep Lynx")
                logger.debug("Final headers: %s", 
                    {k: '***' if k in ['x-api-key', 'x-api-secret', 'Authorization'] else v 
                     for k, v in self.api_client.default_headers.items()})
                
                return DeepLynxResponse(
                    status="success",
                    message="Successfully authenticated",
                    data={"container_id": self.container_id}
                )

            except Exception as token_error:
                logger.error(f"Token retrieval failed: {str(token_error)}")
                raise Exception(f"Token retrieval failed: {str(token_error)}")

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
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

# Singleton instance
_client: Optional[DeepLynxClient] = None

def get_client() -> DeepLynxClient:
    """Get or create Deep Lynx client singleton"""
    global _client
    if _client is None:
        _client = DeepLynxClient()
    return _client