"""
Usage Tracking Schemas

Pydantic models for usage tracking API requests and responses.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class UsageResponse(BaseModel):
    """
    User's monthly usage statistics response.

    Attributes:
        month: First day of current month in UTC (YYYY-MM-01 format)
        conversion_count: Number of conversions this month
        tier: User's subscription tier (FREE, PRO, PREMIUM)
        tier_limit: Max conversions allowed per month (None = unlimited)
        remaining: Conversions remaining this month (None = unlimited)
    """
    month: str = Field(..., description="Current month in YYYY-MM-01 format")
    conversion_count: int = Field(..., description="Number of conversions this month", ge=0)
    tier: str = Field(..., description="User subscription tier")
    tier_limit: Optional[int] = Field(None, description="Max conversions per month (None = unlimited)")
    remaining: Optional[int] = Field(None, description="Remaining conversions (None = unlimited)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "month": "2025-12-01",
                "conversion_count": 3,
                "tier": "FREE",
                "tier_limit": 5,
                "remaining": 2
            }
        }
    )
