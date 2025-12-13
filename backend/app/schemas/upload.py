"""
Upload API Schemas

Pydantic models for PDF upload request/response validation.
"""
from pydantic import BaseModel
from datetime import datetime


class UploadResponse(BaseModel):
    """
    Response returned after successful PDF upload.

    Attributes:
        job_id: Unique identifier for the conversion job (UUID)
        status: Initial job status (always "UPLOADED")
        input_file: Original filename of uploaded PDF
        created_at: Timestamp when job was created
    """
    job_id: str
    status: str
    input_file: str
    created_at: datetime


class ErrorResponse(BaseModel):
    """
    Standard error response format.

    Attributes:
        detail: Human-readable error message
        code: Machine-readable error code (e.g., "INVALID_FILE_TYPE")
    """
    detail: str
    code: str
