import deep_lynx
from deep_lynx.rest import ApiException
import os
from dotenv import load_dotenv
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class DeepLynxClient:
    """Base client for Deep Lynx operations"""
    def __init__(self, host: str = None, env_file_path: str = None):
        self.host = host  # Store the host parameter first
        self._init_from_env(env_file_path)
        self._setup_client()
        
    def _init_from_env(self, env_file_path: Optional[str] = None):
        if env_file_path:
            load_dotenv(env_file_path)
        else:
            load_dotenv()
            
        # Use self.host if provided in constructor, otherwise get from env
        self.host = self.host or os.getenv('DEEP_LYNX_URL')
        self.api_key = os.getenv('DEEP_LYNX_API_KEY')
        self.api_secret = os.getenv('DEEP_LYNX_API_SECRET')
        self.container_id = os.getenv('DEEP_LYNX_CONTAINER_ID')
        
        # Validate required environment variables
        if not all([self.host, self.api_key, self.api_secret, self.container_id]):
            missing = []
            if not self.host: missing.append('DEEP_LYNX_URL')
            if not self.api_key: missing.append('DEEP_LYNX_API_KEY')
            if not self.api_secret: missing.append('DEEP_LYNX_API_SECRET')
            if not self.container_id: missing.append('DEEP_LYNX_CONTAINER_ID')
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
    def _setup_client(self):
        """Set up the Deep Lynx API client and initialize all needed APIs"""
        self.configuration = deep_lynx.Configuration()
        self.configuration.host = self.host
        
        auth_str = f"{self.api_key}:{self.api_secret}"
        self.configuration.api_key['Authorization'] = auth_str
        self.configuration.api_key_prefix['Authorization'] = 'Basic'
        
        self.api_client = deep_lynx.ApiClient(self.configuration)
        
        # Initialize all needed APIs
        self.users_api = deep_lynx.UsersApi(self.api_client)
        self.auth_api = deep_lynx.AuthenticationApi(self.api_client)
        self.containers_api = deep_lynx.ContainersApi(self.api_client)
        
    def authenticate(self) -> bool:
        """Authenticate with Deep Lynx"""
        try:
            token_response = self.auth_api.retrieve_o_auth_token(
                x_api_key=self.api_key,
                x_api_secret=self.api_secret
            )
            
            token = token_response.value if hasattr(token_response, 'value') else token_response
            self.api_client.default_headers['Authorization'] = f"Bearer {token}"
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False 