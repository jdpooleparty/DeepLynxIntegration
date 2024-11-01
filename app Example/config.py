from pydantic_settings import BaseSettings
from typing import Optional
import logging

class Settings(BaseSettings):
    """Application settings"""
    deep_lynx_url: str
    deep_lynx_api_key: str
    deep_lynx_secret: str
    deep_lynx_container_id: str
    log_level: Optional[str] = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False  # This allows for case-insensitive env var matching

def get_settings() -> Settings:
    """Get cached settings"""
    return Settings()

# Configure logging based on the settings
def configure_logging():
    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ) 