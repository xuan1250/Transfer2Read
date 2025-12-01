"""
Application Configuration

Pydantic-based configuration management for environment variables.
Loads from .env file in development and from environment in production.
"""
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str  # Use service_role key for backend (bypasses RLS)

    # AI API Keys (placeholders for future stories)
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"

    # Celery Configuration (for future async tasks)
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Application Configuration
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Global settings instance
settings = Settings()
