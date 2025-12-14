"""
Job API Schemas

Pydantic models for conversion job request/response validation.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any


class JobSummary(BaseModel):
    """
    Summary of a conversion job for list view.

    Attributes:
        id: Job identifier (UUID)
        status: Current job status
        input_file: Original filename (extracted from input_path)
        created_at: Job creation timestamp
        completed_at: Job completion timestamp (if completed)
        overall_confidence: Overall quality confidence score (if quality report available)
    """
    id: str
    status: str
    input_file: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    overall_confidence: Optional[float] = Field(None, ge=0, le=100, description="Overall quality confidence")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "COMPLETED",
            "input_file": "document.pdf",
            "created_at": "2025-12-12T10:30:00Z",
            "completed_at": "2025-12-12T10:32:15Z",
            "overall_confidence": 95.2
        }
    })


class JobDetail(BaseModel):
    """
    Full details of a conversion job.

    Attributes:
        id: Job identifier (UUID)
        user_id: Owner's user ID (UUID)
        status: Current job status
        input_path: Supabase Storage path to input PDF
        original_filename: Original filename of uploaded PDF
        output_path: Supabase Storage path to output EPUB (if completed)
        progress: Progress percentage (0-100)
        stage_metadata: JSONB metadata about current pipeline stage
        quality_report: Complete AI quality metrics (if completed and requested)
        created_at: Job creation timestamp
        completed_at: Job completion timestamp (if completed)
    """
    id: str
    user_id: str
    status: str
    input_path: str
    original_filename: Optional[str] = None
    output_path: Optional[str] = None
    progress: int = Field(0, ge=0, le=100, description="Progress percentage")
    stage_metadata: Dict[str, Any] = Field(default_factory=dict, description="Current stage metadata")
    quality_report: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "status": "COMPLETED",
            "input_path": "uploads/user-id/job-id/input.pdf",
            "original_filename": "my-document.pdf",
            "output_path": "downloads/user-id/job-id/output.epub",
            "progress": 100,
            "stage_metadata": {
                "current_stage": "COMPLETED",
                "progress_percent": 100,
                "quality_confidence": 95.2,
                "completed_at": "2025-12-12T10:32:15Z",
                "original_filename": "my-document.pdf"
            },
            "quality_report": {
                "overall_confidence": 95.2,
                "elements": {
                    "tables": {"count": 12, "avg_confidence": 93.5},
                    "images": {"count": 8, "avg_confidence": 100.0},
                    "equations": {"count": 5, "avg_confidence": 97.0}
                },
                "warnings": [],
                "fidelity_targets": {
                    "complex_elements": {"target": 95, "actual": 95.2, "met": True}
                }
            },
            "created_at": "2025-12-12T10:30:00Z",
            "completed_at": "2025-12-12T10:32:15Z"
        }
    })


class JobListResponse(BaseModel):
    """
    Response for listing jobs with pagination.

    Attributes:
        jobs: Array of job summaries
        total: Total count of jobs matching filter
        limit: Maximum number of jobs returned
        offset: Pagination offset
    """
    jobs: List[JobSummary]
    total: int
    limit: int
    offset: int

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "jobs": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "status": "COMPLETED",
                    "input_file": "document.pdf",
                    "created_at": "2025-12-12T10:30:00Z",
                    "completed_at": "2025-12-12T10:32:15Z"
                }
            ],
            "total": 50,
            "limit": 20,
            "offset": 0
        }
    })


class DownloadUrlResponse(BaseModel):
    """
    Response containing signed download URL.

    Attributes:
        download_url: Supabase Storage signed URL (1-hour expiry)
        expires_at: URL expiration timestamp
    """
    download_url: str
    expires_at: datetime

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "download_url": "https://supabase.co/.../output.epub?token=...",
            "expires_at": "2025-12-12T11:30:00Z"
        }
    })
