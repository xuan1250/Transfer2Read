"""
Upload API Endpoint

Handles PDF file uploads to Supabase Storage with authentication and validation.
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from datetime import datetime
import uuid
import logging

from app.core.auth import get_current_user
from app.middleware.limits import check_tier_limits
from app.schemas.auth import AuthenticatedUser
from app.schemas.upload import UploadResponse
from app.services.validation import (
    FileValidationService,
    InvalidFileTypeError,
    FileTooLargeError
)
from app.services.storage.supabase_storage import (
    SupabaseStorageService,
    StorageUploadError
)
from app.core.supabase import get_supabase_client
from app.core.redis_client import get_cached_redis_client
from app.services.usage_tracker import UsageTracker
from celery import chain
from app.tasks.conversion_pipeline import (
    convert_to_html,
    extract_content,
    identify_structure,
    generate_epub,
    calculate_quality_score
)

logger = logging.getLogger(__name__)
router = APIRouter()


def get_storage_service() -> SupabaseStorageService:
    """
    Dependency for getting initialized SupabaseStorageService.

    Returns:
        SupabaseStorageService: Configured storage service instance
    """
    supabase = get_supabase_client()
    return SupabaseStorageService(supabase)


@router.post(
    "/upload",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=UploadResponse,
    summary="Upload PDF for conversion",
    description="""
    Upload a PDF file for conversion to EPUB format.

    **Authentication Required:**
    - Requires valid Supabase JWT token in Authorization header
    - Format: `Bearer <token>`

    **Tier Limits (Enforced BEFORE Processing):**
    - FREE tier: 
      - File size: 50MB maximum
      - Conversions: 5 per month
    - PRO/PREMIUM tier: Unlimited file size and conversions

    **File Validation:**
    - File must be valid PDF (verified by magic bytes, not extension)
    - Limits checked before file processing begins

    **Returns:**
    - 202 Accepted with job_id for tracking conversion status
    - Job initially created with status "UPLOADED"
    - Use `/jobs/{job_id}` endpoint to poll conversion progress

    **Error Codes:**
    - `FILE_SIZE_LIMIT_EXCEEDED`: File exceeds tier limit (403 Forbidden)
    - `CONVERSION_LIMIT_EXCEEDED`: Monthly conversion limit reached (403 Forbidden)
    - `INVALID_FILE_TYPE`: File is not a PDF (400 Bad Request)
    - `FILE_TOO_LARGE`: File exceeds tier limit (413 Request Entity Too Large)
    - `UNAUTHORIZED`: Missing or invalid JWT token (401 Unauthorized)
    - `STORAGE_ERROR`: Failed to upload to storage (500 Internal Server Error)
    - `DATABASE_ERROR`: Failed to create job record (500 Internal Server Error)
    """
)
async def upload_pdf(
    file: UploadFile = File(..., description="PDF file to upload"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    storage_service: SupabaseStorageService = Depends(get_storage_service),
    _: None = Depends(check_tier_limits)  # Limit check runs BEFORE file processing
) -> UploadResponse:
    """
    Upload PDF file and create conversion job.
    
    Tier limits are enforced BEFORE file processing via check_tier_limits dependency.

    Args:
        file: Uploaded PDF file (multipart/form-data)
        current_user: Authenticated user from JWT token
        storage_service: Supabase storage service
        _: Limit enforcement dependency (runs automatically)

    Returns:
        UploadResponse: Job information with job_id, status, and timestamp

    Raises:
        HTTPException(403): Tier limit exceeded (file size or conversion count)
        HTTPException(400): Invalid file type
        HTTPException(401): Authentication failure
        HTTPException(413): File too large for user's tier
        HTTPException(500): Storage or database error
    """
    # Read file content
    file_data = await file.read()
    file_size = len(file_data)
    filename = file.filename or "unknown.pdf"

    # Validate file type and size
    validator = FileValidationService()

    try:
        validator.validate_pdf(file_data)
        validator.validate_file_size(file_size, current_user.tier)
    except InvalidFileTypeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": str(e), "code": "INVALID_FILE_TYPE"}
        )
    except FileTooLargeError as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"detail": str(e), "code": "FILE_TOO_LARGE"}
        )

    # Generate job ID and storage path
    job_id = str(uuid.uuid4())
    storage_path = f"{current_user.user_id}/{job_id}/input.pdf"

    # Upload to Supabase Storage
    try:
        storage_service.upload_file(
            bucket="uploads",
            path=storage_path,
            file_data=file_data,
            content_type="application/pdf"
        )
    except StorageUploadError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": f"Storage upload failed: {str(e)}", "code": "STORAGE_ERROR"}
        )

    # Create database record
    supabase = get_supabase_client()
    created_at = datetime.utcnow()

    job_data = {
        "id": job_id,
        "user_id": current_user.user_id,
        "status": "UPLOADED",
        "input_path": storage_path,
        "stage_metadata": {"original_filename": filename},
        "created_at": created_at.isoformat()
    }

    try:
        supabase.table("conversion_jobs").insert(job_data).execute()
    except Exception as e:
        # If database insert fails, try to clean up uploaded file
        try:
            storage_service.delete_file("uploads", storage_path)
        except:
            pass  # Ignore cleanup errors

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": f"Database error: {str(e)}", "code": "DATABASE_ERROR"}
        )

    # Increment usage count (after successful job creation)
    # IMPORTANT: Increment failures should NOT block conversion
    try:
        redis_client = get_cached_redis_client()
        usage_tracker = UsageTracker(supabase, redis_client)
        new_count = usage_tracker.increment_usage(current_user.user_id)
        logger.info(f"Incremented usage for user {current_user.user_id} to {new_count}")
    except Exception as e:
        # Log error but don't fail the request - usage tracking is non-critical
        logger.error(f"Failed to increment usage for user {current_user.user_id}: {str(e)}", exc_info=True)
        # Continue with conversion even if usage tracking fails

    # Dispatch Celery pipeline for async conversion
    try:
        logger.info(f"Dispatching conversion pipeline for job {job_id}")

        # Build the conversion chain directly (avoid orchestrator task anti-pattern)
        workflow = chain(
            convert_to_html.s(job_id),
            extract_content.s(),
            identify_structure.s(),
            generate_epub.s(),
            calculate_quality_score.s()
        )

        # Execute the chain asynchronously (no .get() - fire and forget)
        workflow.apply_async()

        logger.info(f"Successfully dispatched pipeline for job {job_id}")
    except Exception as e:
        # Log error but don't fail the request - job can be retried manually
        logger.error(f"Failed to dispatch conversion pipeline for job {job_id}: {str(e)}", exc_info=True)
        # Note: We could update job status to FAILED here, but let's allow retry
        # If Celery is down, the job will remain in UPLOADED status

    # Return success response
    return UploadResponse(
        job_id=job_id,
        status="UPLOADED",
        input_file=filename,
        created_at=created_at
    )
