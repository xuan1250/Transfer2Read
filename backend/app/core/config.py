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
    SUPABASE_JWT_SECRET: str   # JWT secret for validating access tokens

    # AI API Keys
    OPENAI_API_KEY: str  # Required for GPT-4o layout analysis
    ANTHROPIC_API_KEY: str  # Required for Claude fallback

    # AI Analysis Configuration (Story 4.2)
    ANALYSIS_CONCURRENCY: int = 4  # Number of concurrent page analyses
    ANALYSIS_PAGE_BATCH_SIZE: int = 5  # Update progress every N pages
    ANALYSIS_TIMEOUT_PER_PAGE: int = 30  # Timeout per page in seconds
    MAX_IMAGE_SIZE: int = 2048  # Max pixel dimension for vision input
    AI_ANALYSIS_MAX_RETRIES: int = 3  # Max retry attempts before fallback
    AI_FALLBACK_ENABLED: bool = True  # Enable Claude fallback on OpenAI failure
    AI_CACHE_ENABLED: bool = True  # Enable caching for repeated page patterns
    AI_SIMPLE_PAGE_MODEL: str = "claude-3-5-haiku-20241022"  # Model for simple text-only pages

    # AI Structure Analysis Configuration (Story 4.3)
    STRUCTURE_CHUNK_SIZE: int = 50  # Max pages per chunk for large docs
    STRUCTURE_CHUNK_OVERLAP: int = 5  # Pages overlap between chunks
    STRUCTURE_CONFIDENCE_THRESHOLD: int = 70  # Min confidence before heuristic fallback
    STRUCTURE_MAX_DEPTH: int = 4  # Max TOC hierarchy depth (H1-H4)
    STRUCTURE_ANALYSIS_TIMEOUT: int = 60  # Timeout for structure analysis in seconds

    # EPUB Generation Configuration (Story 4.4)
    EPUB_MAX_FILE_SIZE_MB: int = 100  # Max EPUB size before compression
    EPUB_IMAGE_QUALITY: int = 85  # JPEG quality for image compression (0-100)
    EPUB_VALIDATION_ENABLED: bool = True  # Enable epubcheck validation
    EPUB_GENERATION_TIMEOUT: int = 600  # 10 minutes max for EPUB generation
    EPUB_COVER_WIDTH: int = 800  # Cover image width in pixels
    EPUB_COVER_HEIGHT: int = 1200  # Cover image height in pixels

    # Quality Scoring Configuration (Story 4.5)
    QUALITY_SCORING_ENABLED: bool = True  # Enable quality calculation
    QUALITY_WARNING_THRESHOLD: int = 80  # Flag confidence below this threshold
    QUALITY_TARGET_COMPLEX: int = 95  # FR24: Complex PDF fidelity target
    QUALITY_TARGET_TEXT: int = 99  # FR25: Text-based PDF fidelity target
    QUALITY_TEXT_BASE_CONFIDENCE: int = 99  # Base confidence for simple text blocks

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
