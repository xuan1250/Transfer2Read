"""
Redis Client Configuration

Provides Redis client for caching and session management.
"""
import redis
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_redis_client() -> Optional[redis.Redis]:
    """
    Get Redis client for caching operations.

    Returns:
        redis.Redis: Configured Redis client, or None if connection fails

    Note:
        Gracefully handles connection failures - returns None to allow
        application to continue without caching.
    """
    try:
        client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,  # Automatically decode bytes to strings
            socket_connect_timeout=5,
            socket_timeout=5
        )

        # Test connection
        client.ping()
        logger.info(f"Redis connection established: {settings.REDIS_URL}")
        return client

    except redis.ConnectionError as e:
        logger.warning(f"Redis connection failed: {str(e)}. Caching disabled.")
        return None
    except Exception as e:
        logger.error(f"Redis client initialization error: {str(e)}")
        return None


# Global Redis client instance (initialized on import)
_redis_client: Optional[redis.Redis] = None


def init_redis_client() -> Optional[redis.Redis]:
    """
    Initialize global Redis client.

    Returns:
        redis.Redis: Redis client or None if initialization failed
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = get_redis_client()
    return _redis_client


def get_cached_redis_client() -> Optional[redis.Redis]:
    """
    Get cached Redis client instance.

    Returns:
        redis.Redis: Cached Redis client or None
    """
    global _redis_client
    return _redis_client
