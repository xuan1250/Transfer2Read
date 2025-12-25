"""
Admin API Schemas

Pydantic models for admin dashboard endpoints.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class SystemStats(BaseModel):
    """
    System-wide statistics for admin dashboard.

    Attributes:
        total_users: Total number of registered users
        total_conversions: All-time conversion count across all users
        active_jobs: Count of jobs currently processing or pending
        monthly_conversions: Conversions completed in current month
    """
    total_users: int = Field(..., description="Total registered users")
    total_conversions: int = Field(..., description="All-time conversion count")
    active_jobs: int = Field(..., description="Active jobs (processing/pending)")
    monthly_conversions: int = Field(..., description="Conversions this month")


class AdminUserInfo(BaseModel):
    """
    User information for admin user management table.

    Attributes:
        id: User UUID from Supabase Auth
        email: User's email address
        tier: Subscription tier (FREE, PRO, PREMIUM)
        total_conversions: Total conversions across all time
        last_login: Last sign-in timestamp (ISO 8601)
        created_at: Account creation timestamp (ISO 8601)
    """
    id: str = Field(..., description="User UUID")
    email: str = Field(..., description="User email address")
    tier: str = Field(..., description="Subscription tier")
    total_conversions: int = Field(0, description="Total conversions")
    last_login: Optional[str] = Field(None, description="Last login timestamp")
    created_at: str = Field(..., description="Account creation timestamp")


class UserListResponse(BaseModel):
    """
    Paginated user list response for admin dashboard.

    Attributes:
        users: List of users for current page
        total: Total number of users matching filters
        page: Current page number (1-indexed)
        page_size: Number of users per page
        total_pages: Total number of pages
    """
    users: List[AdminUserInfo] = Field(..., description="List of users")
    total: int = Field(..., description="Total users matching filters")
    page: int = Field(..., description="Current page (1-indexed)")
    page_size: int = Field(..., description="Users per page")
    total_pages: int = Field(..., description="Total pages")


class TierUpdateRequest(BaseModel):
    """
    Request body for updating a user's subscription tier.

    Attributes:
        tier: New subscription tier (must be FREE, PRO, or PREMIUM)
    """
    tier: Literal['FREE', 'PRO', 'PREMIUM'] = Field(..., description="New tier (FREE/PRO/PREMIUM)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tier": "PRO"
            }
        }
    )


class TierUpdateResponse(BaseModel):
    """
    Response after successfully updating a user's tier.

    Attributes:
        user_id: UUID of the user whose tier was updated
        old_tier: Previous subscription tier
        new_tier: New subscription tier
        updated_at: Timestamp of the update (ISO 8601)
    """
    user_id: str = Field(..., description="User UUID")
    old_tier: str = Field(..., description="Previous tier")
    new_tier: str = Field(..., description="New tier")
    updated_at: str = Field(..., description="Update timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "old_tier": "FREE",
                "new_tier": "PRO",
                "updated_at": "2025-12-25T10:30:00Z"
            }
        }
    )
