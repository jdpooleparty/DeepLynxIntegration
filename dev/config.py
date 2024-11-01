from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
import deep_lynx
from deep_lynx.rest import ApiException
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import logging
from multiprocessing.pool import Pool

logger = logging.getLogger(__name__)

class DeepLynxConfig(BaseSettings):
    """Configuration for Deep Lynx connection and authentication."""
    
    api_url: str = Field(alias='DEEP_LYNX_URL')
    api_key: str = Field(alias='DEEP_LYNX_API_KEY')
    api_secret: str = Field(alias='DEEP_LYNX_API_SECRET')
    debug: bool = Field(default=False, alias='DEBUG')
    log_level: str = Field(default='INFO', alias='LOG_LEVEL')
    max_retries: int = Field(default=3, alias='MAX_RETRIES')
    pool_connections: int = Field(default=10, alias='POOL_CONNECTIONS')
    pool_maxsize: int = Field(default=10, alias='POOL_MAXSIZE')

    def get_client(self) -> deep_lynx.ApiClient:
        """Initialize and return an authenticated Deep Lynx API client with connection pooling."""
        try:
            # Initialize configuration
            configuration = deep_lynx.Configuration()
            configuration.host = self.api_url
            api_client = deep_lynx.ApiClient(configuration)
            
            # Replace default pool with empty pool that has a no-op close method
            class NoOpPool:
                def close(self): pass
                def join(self): pass
            api_client.pool = NoOpPool()
            
            # Configure retry strategy
            retry_strategy = Retry(
                total=self.max_retries,
                backoff_factor=0.5,
                status_forcelist=[500, 502, 503, 504]
            )

            # Configure connection pooling
            adapter = HTTPAdapter(
                max_retries=retry_strategy,
                pool_connections=self.pool_connections,
                pool_maxsize=self.pool_maxsize
            )

            # Apply adapter to both HTTP and HTTPS
            api_client.rest_client.pool_manager.connection_pool_kw.update({
                'retries': retry_strategy,
                'maxsize': self.pool_maxsize
            })

            # Initialize authentication API
            auth_api = deep_lynx.AuthenticationApi(api_client)
            
            try:
                token = auth_api.retrieve_o_auth_token(
                    x_api_key=self.api_key,
                    x_api_secret=self.api_secret,
                    x_api_expiry='1h'
                )
                logger.debug("Successfully retrieved OAuth token")
                return api_client

            except ApiException as e:
                logger.error(f"Authentication failed: {str(e)}")
                if e.status in (401, 403):
                    raise ConnectionError(f"Failed to connect to Deep Lynx: {str(e)}")
                elif e.status >= 500:
                    raise Exception(f"Deep Lynx server error: {str(e)}")
                else:
                    raise e

        except ConnectionError as e:
            logger.error(f"Connection error: {str(e)}")
            raise  # Re-raise ConnectionError directly
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise Exception(f"Unexpected error connecting to Deep Lynx: {str(e)}")

    model_config = SettingsConfigDict(
        env_file='.env',
        case_sensitive=True,
        extra='ignore'
    )