from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Deep Lynx Configuration
    deep_lynx_url: str
    deep_lynx_api_key: str
    deep_lynx_api_secret: str
    deep_lynx_container_id: str = "1"
    deep_lynx_integration_test: Optional[str] = None

    # Database Configuration
    database_url: Optional[str] = None

    # Application Settings
    debug: bool = False
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_prefix = "DEEP_LYNX_"
        case_sensitive = False

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            # Check if we're running tests
            if os.getenv("TESTING", "").lower() == "true":
                return (
                    init_settings,
                    env_settings.with_prefix("DEEP_LYNX_"),
                    file_secret_settings.with_path("tests/.env.test")
                )
            return (
                init_settings,
                env_settings.with_prefix("DEEP_LYNX_"),
                file_secret_settings
            )