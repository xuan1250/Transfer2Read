"""
Job API Schemas

Pydantic models for conversion job request/response validation.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class QualityReport(BaseModel):
    """
    Quality metrics from AI analysis.

    Attributes:
        overall_confidence: Overall conversion quality score (0-100)
        tables: Table extraction metrics
        images: Image extraction metrics
        equations: Equation rendering metrics
    """
    overall_confidence: Optional[int] = Field(None, ge=0, le=100, description="Overall quality score")
    tables: Optional[Dict[str, Any]] = Field(None, description="Table extraction metrics")
    images: Optional[Dict[str, Any]] = Field(None, description="Image extraction metrics")
    equations: Optional[Dict[str, Any]] = Field(None, description="Equation rendering metrics")

    class Config:
        json_schema_extra = {
            "example": {
                "overall_confidence": 95,
                "tables": {"count": 12, "avg_confidence": 93},
                "images": {"count": 8},
                "equations": {"count": 5, "avg_confidence": 97}
            }
        }


class JobSummary(BaseModel):
    """
    Summary of a conversion job for list view.

    Attributes:
        id: Job identifier (UUID)
        status: Current job status
        input_file: Original filename (extracted from input_path)
        created_at: Job creation timestamp
        completed_at: Job completion timestamp (if completed)
        quality_report: AI quality metrics (if completed)
    """
    id: str
    status: str
    input_file: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    quality_report: Optional[QualityReport] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "COMPLETED",
                "input_file": "document.pdf",
                "created_at": "2025-12-12T10:30:00Z",
                "completed_at": "2025-12-12T10:32:15Z",
                "quality_report": {
                    "overall_confidence": 95,
                    "tables": {"count": 12}
                }
            }
        }


class JobDetail(BaseModel):
    """
    Full details of a conversion job.

    Attributes:
        id: Job identifier (UUID)
        user_id: Owner's user ID (UUID)
        status: Current job status
        input_path: Supabase Storage path to input PDF
        output_path: Supabase Storage path to output EPUB (if completed)
        progress: Progress percentage (0-100)
        stage_metadata: JSONB metadata about current pipeline stage
        quality_report: AI quality metrics (if completed)
        created_at: Job creation timestamp
        completed_at: Job completion timestamp (if completed)
    """
    id: str
    user_id: str
    status: str
    input_path: str
    output_path: Optional[str] = None
    progress: int = Field(0, ge=0, le=100, description="Progress percentage")
    stage_metadata: Dict[str, Any] = Field(default_factory=dict, description="Current stage metadata")
    quality_report: Optional[QualityReport] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "ANALYZING",
                "input_path": "uploads/user-id/job-id/input.pdf",
                "output_path": None,
                "progress": 25,
                "stage_metadata": {
                    "current_stage": "ANALYZING",
                    "progress_percent": 25,
                    "stage_started_at": "2025-12-12T10:30:00Z"
                },
                "quality_report": None,
                "created_at": "2025-12-12T10:30:00Z",
                "completed_at": None
            }
        }


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

    class Config:
        json_schema_extra = {
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
        }


class DownloadUrlResponse(BaseModel):
    """
    Response containing signed download URL.

    Attributes:
        download_url: Supabase Storage signed URL (1-hour expiry)
        expires_at: URL expiration timestamp
    """
    download_url: str
    expires_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "download_url": "https://supabase.co/.../output.epub?token=...",
                "expires_at": "2025-12-12T11:30:00Z"
            }
        }
