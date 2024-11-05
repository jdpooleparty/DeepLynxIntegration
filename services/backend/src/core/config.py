from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Deep Lynx settings
    DEEP_LYNX_URL: str
    DEEP_LYNX_API_KEY: str
    DEEP_LYNX_API_SECRET: str
    DEEP_LYNX_CONTAINER_ID: int
    
    # Database settings
    DATABASE_URL: str
    
    # App settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings() 