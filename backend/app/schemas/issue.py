"""
Issue Report API Schemas

Pydantic models for issue reporting and responses.
Story 5.4 - Download & Feedback Flow
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, Literal


# Define common issue types
IssueType = Literal[
    "table_formatting",
    "missing_images",
    "broken_chapters",
    "incorrect_equations",
    "font_issues",
    "other"
]


class IssueReportRequest(BaseModel):
    """
    Request schema for reporting conversion issues.

    Attributes:
        issue_type: Category of the issue
        page_number: Optional page number where issue occurs
        description: Required detailed description of the issue
        screenshot_url: Optional URL to uploaded screenshot (future enhancement)
    """
    issue_type: IssueType = Field(
        ...,
        description="Category of issue: table_formatting, missing_images, broken_chapters, incorrect_equations, font_issues, other"
    )
    page_number: Optional[int] = Field(
        None,
        ge=1,
        description="Optional page number where the issue occurs"
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Required detailed description of the issue"
    )
    screenshot_url: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional URL to screenshot showing the issue (future enhancement)"
    )

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Ensure description is not just whitespace."""
        v = v.strip()
        if len(v) < 10:
            raise ValueError('Description must be at least 10 characters long (excluding whitespace)')
        return v

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "issue_type": "table_formatting",
            "page_number": 42,
            "description": "The table on page 42 has misaligned columns. The data in the third column appears in the fourth column.",
            "screenshot_url": None
        }
    })


class IssueReportResponse(BaseModel):
    """
    Response schema after successful issue report submission.

    Attributes:
        issue_id: UUID of created issue record
        job_id: UUID of the conversion job
        issue_type: The reported issue type
        created_at: Timestamp of issue report submission
    """
    issue_id: str = Field(..., description="UUID of created issue record")
    job_id: str = Field(..., description="UUID of the conversion job")
    issue_type: IssueType
    created_at: datetime

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "issue_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
            "job_id": "550e8400-e29b-41d4-a716-446655440000",
            "issue_type": "table_formatting",
            "created_at": "2025-12-15T10:35:00Z"
        }
    })


class IssueStats(BaseModel):
    """
    Aggregated issue statistics for analytics.

    Attributes:
        total_issues: Total number of reported issues
        by_type: Count of issues by type
        most_common_type: The most frequently reported issue type
    """
    total_issues: int = Field(..., ge=0)
    by_type: dict[str, int] = Field(default_factory=dict, description="Count by issue type")
    most_common_type: Optional[str] = Field(None, description="Most frequently reported issue type")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "total_issues": 45,
            "by_type": {
                "table_formatting": 18,
                "missing_images": 12,
                "broken_chapters": 8,
                "incorrect_equations": 5,
                "font_issues": 2
            },
            "most_common_type": "table_formatting"
        }
    })
