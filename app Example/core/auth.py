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
from app.config import get_settings
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class DeepLynxWrapper:
    """Wrapper class for Deep Lynx API clients"""
    def __init__(self, config: Configuration):
        self.api_client = ApiClient(config)
        self.auth_api = AuthenticationApi(self.api_client)
        self.containers_api = ContainersApi(self.api_client)
        self.datasources_api = DataSourcesApi(self.api_client)
        self.type_mappings_api = DataTypeMappingsApi(self.api_client)
        self.metatypes_api = MetatypesApi(self.api_client)
        self.relationships_api = MetatypeRelationshipsApi(self.api_client)

_deep_lynx_client = None

async def initialize_deep_lynx_client():
    """Initialize the Deep Lynx client with configuration"""
    global _deep_lynx_client
    try:
        settings = get_settings()
        
        # Create configuration with SSL verification disabled
        config = Configuration()
        config.host = settings.deep_lynx_url
        config.verify_ssl = False
        
        # Set container ID in configuration
        config.container_id = settings.deep_lynx_container_id
        
        # Initialize empty API key dict
        config.api_key = {}
        config.api_key['x-api-key'] = settings.deep_lynx_api_key
        config.api_key['x-api-secret'] = settings.deep_lynx_secret
        
        # Initialize client with default headers
        client = DeepLynxWrapper(config)
        client.api_client.default_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'x-api-key': settings.deep_lynx_api_key,
            'x-api-secret': settings.deep_lynx_secret
        }
        
        # Get token
        try:
            token_response = client.auth_api.retrieve_o_auth_token(
                x_api_key=settings.deep_lynx_api_key,
                x_api_secret=settings.deep_lynx_secret,
                x_api_expiry='1h'
            )
            
            if not token_response:
                logger.error("No token response received")
                raise HTTPException(status_code=401, detail="Failed to authenticate with Deep Lynx")
            
            # Store token and update configuration
            config.access_token = token_response.value if hasattr(token_response, 'value') else token_response
            
            # Create new client with updated configuration and headers
            _deep_lynx_client = DeepLynxWrapper(config)
            _deep_lynx_client.api_client.default_headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {config.access_token}',
                'x-api-key': settings.deep_lynx_api_key,
                'x-api-secret': settings.deep_lynx_secret
            }
            
            # Ensure container_id is set in the final client configuration
            _deep_lynx_client.api_client.configuration.container_id = settings.deep_lynx_container_id
            
            logger.info("Deep Lynx client initialized successfully")
            
        except Exception as auth_error:
            logger.error(f"Authentication error: {str(auth_error)}")
            raise HTTPException(status_code=401, detail="Failed to authenticate with Deep Lynx")
            
    except Exception as e:
        logger.error(f"Failed to initialize Deep Lynx client: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize Deep Lynx client: {str(e)}"
        )

async def get_deep_lynx_client() -> DeepLynxWrapper:
    """Get the initialized Deep Lynx client"""
    if _deep_lynx_client is None:
        await initialize_deep_lynx_client()
    return _deep_lynx_client