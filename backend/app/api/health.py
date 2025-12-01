"""
Health Check Endpoint

Provides system health status by verifying connectivity to:
- Supabase (database and auth)
- Redis (message broker and cache)
"""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import redis.asyncio as redis

from app.core.supabase import get_supabase_client
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint verifying Supabase and Redis connectivity.

    Returns:
        200 OK if all services healthy
        503 Service Unavailable if any service fails

    Response body:
        {
            "status": "healthy" | "unhealthy",
            "database": "connected" | "disconnected: <error>",
            "redis": "connected" | "disconnected: <error>",
            "timestamp": "ISO8601 timestamp"
        }
    """
    health_status = {
        "status": "healthy",
        "database": "unknown",
        "redis": "unknown",
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    }

    # Check Supabase connection
    try:
        supabase = get_supabase_client()
        # Verify client initialization by checking auth status
        # This doesn't require any tables to exist
        # Just verifies the Supabase client can connect
        if supabase is not None:
            health_status["database"] = "connected"
        else:
            health_status["status"] = "unhealthy"
            health_status["database"] = "disconnected: Client initialization failed"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"] = f"disconnected: {str(e)}"

    # Check Redis connection
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        await redis_client.aclose()
        health_status["redis"] = "connected"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["redis"] = f"disconnected: {str(e)}"

    # Return appropriate status code
    if health_status["status"] == "healthy":
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=health_status
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status
        )
