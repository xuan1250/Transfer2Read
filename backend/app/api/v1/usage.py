"""
Usage Tracking API Endpoints

Provides endpoints for querying user conversion usage statistics.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_user
from app.core.supabase import get_supabase_client
from app.core.redis_client import get_cached_redis_client
from app.schemas.auth import AuthenticatedUser
from app.schemas.usage import UsageResponse
from app.services.usage_tracker import UsageTracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("", response_model=UsageResponse)
async def get_current_usage(
    user: AuthenticatedUser = Depends(get_current_user)
) -> UsageResponse:
    """
    Get current month's conversion usage for authenticated user.

    Returns the user's conversion count, tier limit, and remaining conversions
    for the current month. Supports caching via Redis for performance.

    **Authentication Required:** Bearer token in Authorization header

    **Response:**
    - `month`: Current month in YYYY-MM-01 format
    - `conversion_count`: Number of conversions started this month
    - `tier`: User's subscription tier (FREE, PRO, PREMIUM)
    - `tier_limit`: Max conversions allowed per month (null = unlimited)
    - `remaining`: Conversions remaining this month (null = unlimited)

    **Error Responses:**
    - 401 Unauthorized: Missing or invalid authentication token
    - 500 Internal Server Error: Database or service failure

    **Example:**
    ```bash
    curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/usage
    ```

    Returns:
    ```json
    {
      "month": "2025-12-01",
      "conversion_count": 3,
      "tier": "FREE",
      "tier_limit": 5,
      "remaining": 2
    }
    ```
    """
    try:
        # Initialize clients
        supabase = get_supabase_client()
        redis = get_cached_redis_client()  # May be None if Redis unavailable

        # Create UsageTracker service
        tracker = UsageTracker(supabase, redis)

        # Query usage stats for authenticated user
        usage_data = tracker.get_usage(user.user_id)

        return UsageResponse(**usage_data)

    except Exception as e:
        logger.error(f"Failed to get usage for user {user.user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve usage data. Please try again later."
        )
