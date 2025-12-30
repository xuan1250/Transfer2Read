"""
Feedback API Schemas

Pydantic models for user feedback submission and responses.
Story 5.4 - Download & Feedback Flow
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, Literal, List


class FeedbackSubmitRequest(BaseModel):
    """
    Request schema for submitting user feedback on conversion quality.

    Attributes:
        rating: User rating - either 'positive' (👍) or 'negative' (👎)
        comment: Optional comment explaining the rating (especially for negative feedback)
    """
    rating: Literal['positive', 'negative'] = Field(
        ...,
        description="User rating: 'positive' for good conversion, 'negative' for poor conversion"
    )
    comment: Optional[str] = Field(
        None,
        max_length=2000,
        description="Optional comment explaining the rating"
    )

    @field_validator('comment')
    @classmethod
    def validate_comment(cls, v: Optional[str]) -> Optional[str]:
        """Trim whitespace and return None for empty strings."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "rating": "positive",
            "comment": "Perfect conversion! Tables and equations look great."
        }
    })


class FeedbackResponse(BaseModel):
    """
    Response schema after successful feedback submission.

    Attributes:
        feedback_id: UUID of created feedback record
        job_id: UUID of the conversion job
        rating: The submitted rating
        created_at: Timestamp of feedback submission
    """
    feedback_id: str = Field(..., description="UUID of created feedback record")
    job_id: str = Field(..., description="UUID of the conversion job")
    rating: Literal['positive', 'negative']
    created_at: datetime

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "feedback_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "job_id": "550e8400-e29b-41d4-a716-446655440000",
            "rating": "positive",
            "created_at": "2025-12-15T10:30:00Z"
        }
    })


class FeedbackItem(BaseModel):
    """
    Single feedback item for listing.
    """
    id: str = Field(..., description="Feedback ID")
    rating: Literal['positive', 'negative']
    comment: Optional[str] = None
    created_at: datetime


class FeedbackListResponse(BaseModel):
    """
    Response schema for listing feedback.
    """
    feedback: List[FeedbackItem] = Field(default_factory=list)
    total: int = Field(default=0)


class FeedbackStats(BaseModel):
    """
    Aggregated feedback statistics for analytics.

    Attributes:
        total_feedback: Total number of feedback submissions
        positive_count: Number of positive (👍) ratings
        negative_count: Number of negative (👎) ratings
        positive_ratio: Percentage of positive feedback (0-100)
    """
    total_feedback: int = Field(..., ge=0)
    positive_count: int = Field(..., ge=0)
    negative_count: int = Field(..., ge=0)
    positive_ratio: float = Field(..., ge=0, le=100, description="Percentage of positive feedback")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "total_feedback": 150,
            "positive_count": 135,
            "negative_count": 15,
            "positive_ratio": 90.0
        }
    })

