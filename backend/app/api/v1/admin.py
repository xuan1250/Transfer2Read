"""
Admin API Endpoints

Provides admin-only endpoints for system monitoring and user management.
All endpoints require superuser authorization via require_superuser dependency.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies.admin import require_superuser
from app.core.supabase import get_supabase_client
from app.schemas.auth import AuthenticatedUser, SubscriptionTier
from app.schemas.admin import (
    SystemStats,
    UserListResponse,
    TierUpdateRequest,
    TierUpdateResponse
)
from app.services.admin_service import AdminService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    user: AuthenticatedUser = Depends(require_superuser),
    supabase = Depends(get_supabase_client)
) -> SystemStats:
    """
    Get system-wide statistics for admin dashboard.

    Returns key metrics including total users, conversions, and active jobs.
    This endpoint is restricted to users with is_superuser=true flag.

    **Authentication Required:** Bearer token in Authorization header
    **Authorization Required:** User must have is_superuser=true in user_metadata

    **Response:**
    - `total_users`: Total number of registered users
    - `total_conversions`: All-time conversion count across all users
    - `active_jobs`: Count of jobs in processing or pending status
    - `monthly_conversions`: Conversions completed in current month

    **Error Responses:**
    - 401 Unauthorized: Missing or invalid authentication token
    - 403 Forbidden: User does not have admin privileges
    - 500 Internal Server Error: Database query failure

    **Example:**
    ```bash
    curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/admin/stats
    ```

    Returns:
    ```json
    {
        "total_users": 150,
        "total_conversions": 1234,
        "active_jobs": 5,
        "monthly_conversions": 89
    }
    ```
    """
    try:
        admin_service = AdminService(supabase)
        stats = await admin_service.get_system_stats()
        return stats

    except Exception as e:
        logger.error(f"Failed to fetch system stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch system statistics"
        )


@router.get("/users", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Users per page (max 100)"),
    search: Optional[str] = Query(None, description="Filter by email (case-insensitive)"),
    tier_filter: Optional[str] = Query(None, description="Filter by tier (ALL, FREE, PRO, PREMIUM)"),
    sort_by: str = Query("created_at", description="Column to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    user: AuthenticatedUser = Depends(require_superuser),
    supabase = Depends(get_supabase_client)
) -> UserListResponse:
    """
    Get paginated list of users with filtering and sorting.

    Returns user list with email, tier, conversions, last login, and creation date.
    Supports pagination, email search, tier filtering, and column sorting.

    **Authentication Required:** Bearer token in Authorization header
    **Authorization Required:** User must have is_superuser=true in user_metadata

    **Query Parameters:**
    - `page` (int, default 1): Page number (1-indexed)
    - `page_size` (int, default 20): Users per page (max 100)
    - `search` (string, optional): Filter by email (case-insensitive substring match)
    - `tier_filter` (string, optional): Filter by tier (ALL, FREE, PRO, PREMIUM)
    - `sort_by` (string, default "created_at"): Column to sort (email, tier, conversions, last_login, created_at)
    - `sort_order` (string, default "desc"): Sort direction (asc or desc)

    **Response:**
    - `users`: Array of user objects with id, email, tier, total_conversions, last_login, created_at
    - `total`: Total number of users matching filters
    - `page`: Current page number
    - `page_size`: Users per page
    - `total_pages`: Total number of pages

    **Error Responses:**
    - 401 Unauthorized: Missing or invalid authentication token
    - 403 Forbidden: User does not have admin privileges
    - 500 Internal Server Error: Database query failure

    **Example:**
    ```bash
    curl -H "Authorization: Bearer <token>" \
         "http://localhost:8000/api/v1/admin/users?page=1&page_size=20&tier_filter=FREE"
    ```

    Returns:
    ```json
    {
        "users": [
            {
                "id": "uuid",
                "email": "user@example.com",
                "tier": "FREE",
                "total_conversions": 3,
                "last_login": "2025-12-25T10:30:00Z",
                "created_at": "2025-01-01T00:00:00Z"
            }
        ],
        "total": 150,
        "page": 1,
        "page_size": 20,
        "total_pages": 8
    }
    ```
    """
    try:
        admin_service = AdminService(supabase)

        result = await admin_service.get_users(
            page=page,
            page_size=page_size,
            search=search,
            tier_filter=tier_filter,
            sort_by=sort_by,
            sort_order=sort_order
        )

        return UserListResponse(**result)

    except Exception as e:
        logger.error(f"Failed to fetch user list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user list"
        )


@router.patch("/users/{user_id}/tier", response_model=TierUpdateResponse)
async def update_user_tier(
    user_id: str,
    request: TierUpdateRequest,
    admin_user: AuthenticatedUser = Depends(require_superuser),
    supabase = Depends(get_supabase_client)
) -> TierUpdateResponse:
    """
    Update a user's subscription tier.

    Allows admin to manually upgrade or downgrade a user's tier.
    Useful for Private Beta support before Stripe integration.
    Updates user_metadata.tier in Supabase Auth.

    **Authentication Required:** Bearer token in Authorization header
    **Authorization Required:** User must have is_superuser=true in user_metadata

    **Path Parameters:**
    - `user_id` (string): UUID of the user to update

    **Request Body:**
    - `tier` (string): New tier value (must be FREE, PRO, or PREMIUM)

    **Response:**
    - `user_id`: UUID of the updated user
    - `old_tier`: Previous subscription tier
    - `new_tier`: New subscription tier
    - `updated_at`: Timestamp of the update (ISO 8601)

    **Error Responses:**
    - 400 Bad Request: Invalid tier value
    - 401 Unauthorized: Missing or invalid authentication token
    - 403 Forbidden: User does not have admin privileges
    - 404 Not Found: User not found
    - 500 Internal Server Error: Update operation failed

    **Example:**
    ```bash
    curl -X PATCH \
         -H "Authorization: Bearer <token>" \
         -H "Content-Type: application/json" \
         -d '{"tier": "PRO"}' \
         http://localhost:8000/api/v1/admin/users/550e8400-e29b-41d4-a716-446655440000/tier
    ```

    Returns:
    ```json
    {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "old_tier": "FREE",
        "new_tier": "PRO",
        "updated_at": "2025-12-25T10:30:00Z"
    }
    ```

    **Security Notes:**
    - Admin actions are logged for audit trail
    - Tier change takes effect immediately
    - User will bypass tier limits on next request
    """
    try:
        admin_service = AdminService(supabase)

        result = await admin_service.update_user_tier(user_id, request.tier)

        return TierUpdateResponse(**result)

    except ValueError as e:
        # Invalid tier or user not found
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    except Exception as e:
        logger.error(f"Failed to update user tier: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user tier"
        )
