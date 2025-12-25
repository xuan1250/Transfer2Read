"""
Error Response Schemas

Pydantic models for structured error responses.
"""
from typing import Optional
from pydantic import BaseModel, Field


class LimitExceededError(BaseModel):
    """
    Error response for tier limit violations.
    
    Used when users exceed file size limits or monthly conversion limits.
    Returns HTTP 403 Forbidden with actionable information for upgrade prompts.
    
    Error Codes:
        - FILE_SIZE_LIMIT_EXCEEDED: File too large for user's tier
        - CONVERSION_LIMIT_EXCEEDED: Monthly conversion quota exhausted
    """
    detail: str = Field(
        ...,
        description="Human-readable error message explaining the limit violation"
    )
    code: str = Field(
        ...,
        description="Machine-readable error code: FILE_SIZE_LIMIT_EXCEEDED or CONVERSION_LIMIT_EXCEEDED"
    )
    tier: str = Field(
        ...,
        description="User's current subscription tier (FREE, PRO, PREMIUM)"
    )
    upgrade_url: str = Field(
        default="/pricing",
        description="URL to upgrade page for purchasing higher tier"
    )
    
    # File size specific fields
    current_size_mb: Optional[float] = Field(
        None,
        description="Uploaded file size in MB (for FILE_SIZE_LIMIT_EXCEEDED)"
    )
    max_size_mb: Optional[int] = Field(
        None,
        description="Maximum allowed file size in MB (for FILE_SIZE_LIMIT_EXCEEDED)"
    )
    
    # Conversion limit specific fields
    current_count: Optional[int] = Field(
        None,
        description="Current conversion count this month (for CONVERSION_LIMIT_EXCEEDED)"
    )
    limit: Optional[int] = Field(
        None,
        description="Maximum conversions allowed per month (for CONVERSION_LIMIT_EXCEEDED)"
    )
    reset_date: Optional[str] = Field(
        None,
        description="Date when conversion limit resets (YYYY-MM-DD format)"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "detail": "File size exceeds your tier limit. Maximum allowed: 50MB for Free tier.",
                    "code": "FILE_SIZE_LIMIT_EXCEEDED",
                    "current_size_mb": 75.5,
                    "max_size_mb": 50,
                    "tier": "FREE",
                    "upgrade_url": "/pricing"
                },
                {
                    "detail": "Monthly conversion limit reached. You have used 5/5 conversions this month.",
                    "code": "CONVERSION_LIMIT_EXCEEDED",
                    "current_count": 5,
                    "limit": 5,
                    "tier": "FREE",
                    "reset_date": "2025-02-01",
                    "upgrade_url": "/pricing"
                }
            ]
        }
