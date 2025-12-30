"""
Jobs API Endpoints

Handles conversion job listing, details, deletion, and download operations.
All business logic delegated to JobService (Service Pattern).
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime
from typing import Optional
import logging

from app.core.auth import get_current_user
from app.schemas.auth import AuthenticatedUser
from app.schemas.job import (
    JobListResponse,
    JobDetail,
    DownloadUrlResponse
)
from app.schemas.progress import ProgressUpdate, ElementsDetected
from app.schemas.feedback import FeedbackSubmitRequest, FeedbackResponse, FeedbackListResponse, FeedbackItem
from app.schemas.issue import IssueReportRequest, IssueReportResponse, IssueListResponse, IssueItem
from app.core.supabase import get_supabase_client
from app.core.redis_client import init_redis_client
from app.services.storage.supabase_storage import SupabaseStorageService
from app.services.job_service import JobService

router = APIRouter()
logger = logging.getLogger(__name__)


def get_job_service() -> JobService:
    """
    Dependency for getting initialized JobService with Redis caching.

    Returns:
        JobService: Configured job service instance with optional Redis cache
    """
    supabase = get_supabase_client()
    storage_service = SupabaseStorageService(supabase)
    redis_client = init_redis_client()
    return JobService(supabase, storage_service, redis_client)


@router.get(
    "/jobs",
    status_code=status.HTTP_200_OK,
    response_model=JobListResponse,
    summary="List conversion jobs",
    description="""
    List conversion jobs for the authenticated user with pagination and filtering.

    **Authentication Required:**
    - Requires valid Supabase JWT token in Authorization header
    - Format: `Bearer <token>`

    **Query Parameters:**
    - `limit`: Maximum number of jobs to return (default: 20, max: 100)
    - `offset`: Pagination offset (default: 0)
    - `status`: Filter by job status (UPLOADED, PROCESSING, COMPLETED, FAILED)

    **Returns:**
    - 200 OK with array of job summaries
    - Includes pagination metadata (total, limit, offset)
    - Only returns jobs owned by the authenticated user (enforced by RLS)

    **Error Codes:**
    - `UNAUTHORIZED`: Missing or invalid JWT token
    - `DATABASE_ERROR`: Failed to query jobs
    """
)
async def list_jobs(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of jobs to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
) -> JobListResponse:
    """
    List conversion jobs for authenticated user.

    Args:
        limit: Maximum number of jobs to return
        offset: Pagination offset
        status_filter: Optional status filter
        current_user: Authenticated user from JWT token
        job_service: Job service instance

    Returns:
        JobListResponse: Paginated list of jobs with metadata

    Raises:
        HTTPException(401): Authentication failure
        HTTPException(500): Database error
    """
    request_start = datetime.utcnow()
    logger.info(
        "list_jobs_request",
        extra={
            "user_id": current_user.user_id,
            "limit": limit,
            "offset": offset,
            "status_filter": status_filter
        }
    )

    try:
        jobs, total = job_service.list_jobs(
            user_id=current_user.user_id,
            limit=limit,
            offset=offset,
            status=status_filter
        )

        request_duration = (datetime.utcnow() - request_start).total_seconds() * 1000
        logger.info(
            "list_jobs_success",
            extra={
                "user_id": current_user.user_id,
                "jobs_returned": len(jobs),
                "total_jobs": total,
                "duration_ms": request_duration
            }
        )

        return JobListResponse(
            jobs=jobs,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(
            "list_jobs_error",
            extra={
                "user_id": current_user.user_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": f"Database error: {str(e)}", "code": "DATABASE_ERROR"}
        )


@router.get(
    "/jobs/{job_id}",
    status_code=status.HTTP_200_OK,
    response_model=JobDetail,
    summary="Get job details",
    description="""
    Get full details of a specific conversion job.

    **Authentication Required:**
    - Requires valid Supabase JWT token in Authorization header
    - User must own the job (enforced by RLS)

    **Returns:**
    - 200 OK with full job details including quality report
    - Includes storage paths for input/output files

    **Error Codes:**
    - `UNAUTHORIZED`: Missing or invalid JWT token
    - `NOT_FOUND`: Job not found or user doesn't own job
    - `DATABASE_ERROR`: Failed to query job
    """
)
async def get_job(
    job_id: str,
    include_quality_details: bool = Query(True, description="Include full quality report details"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
) -> JobDetail:
    """
    Get details of a specific conversion job.

    Args:
        job_id: Job identifier (UUID)
        include_quality_details: Include full quality report (default: True)
        current_user: Authenticated user from JWT token
        job_service: Job service instance

    Returns:
        JobDetail: Full job details

    Raises:
        HTTPException(401): Authentication failure
        HTTPException(404): Job not found or user doesn't own job
        HTTPException(500): Database error
    """
    request_start = datetime.utcnow()
    logger.info(
        "get_job_request",
        extra={
            "user_id": current_user.user_id,
            "job_id": job_id
        }
    )

    try:
        job = job_service.get_job(job_id, current_user.user_id)

        if not job:
            logger.warning(
                "get_job_not_found",
                extra={
                    "user_id": current_user.user_id,
                    "job_id": job_id
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": "Job not found", "code": "NOT_FOUND"}
            )

        request_duration = (datetime.utcnow() - request_start).total_seconds() * 1000
        logger.info(
            "get_job_success",
            extra={
                "user_id": current_user.user_id,
                "job_id": job_id,
                "duration_ms": request_duration,
                "include_quality_details": include_quality_details
            }
        )

        # Conditionally exclude quality report if not requested
        if not include_quality_details:
            job.quality_report = None

        return job

    except PermissionError as e:
        # Job exists but doesn't belong to user (403 Forbidden)
        logger.warning(
            "get_job_forbidden",
            extra={
                "user_id": current_user.user_id,
                "job_id": job_id,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "You do not have permission to view this job", "code": "FORBIDDEN"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_job_error",
            extra={
                "user_id": current_user.user_id,
                "job_id": job_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": f"Database error: {str(e)}", "code": "DATABASE_ERROR"}
        )


@router.get(
    "/jobs/{job_id}/progress",
    status_code=status.HTTP_200_OK,
    response_model=ProgressUpdate,
    summary="Get real-time conversion progress",
    description="""
    Get lightweight progress update for polling during conversion.

    **Authentication Required:**
    - Requires valid Supabase JWT token in Authorization header
    - User must own the job (enforced by RLS)

    **Designed for Polling:**
    - Optimized for 2-second polling interval
    - Lightweight payload (<1KB) with only progress data
    - Efficient database query (indexed job_id lookup)

    **Returns:**
    - 200 OK with current progress state
    - Includes: progress %, current stage, elements detected, cost estimate

    **Polling Behavior:**
    - Poll while status = QUEUED or PROCESSING
    - Stop polling when status = COMPLETED or FAILED
    - Updates available every 1-2 seconds during active conversion

    **Error Codes:**
    - `UNAUTHORIZED`: Missing or invalid JWT token
    - `NOT_FOUND`: Job not found or user doesn't own job
    - `DATABASE_ERROR`: Failed to query job
    """
)
async def get_job_progress(
    job_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
) -> ProgressUpdate:
    """
    Get real-time progress update for conversion job.

    Designed for efficient polling: returns only progress data, not full job object.

    Args:
        job_id: Job identifier (UUID)
        current_user: Authenticated user from JWT token
        job_service: Job service instance

    Returns:
        ProgressUpdate: Current progress state

    Raises:
        HTTPException(401): Authentication failure
        HTTPException(404): Job not found or user doesn't own job
        HTTPException(500): Database error
    """
    request_start = datetime.utcnow()
    logger.debug(
        "get_job_progress_request",
        extra={
            "user_id": current_user.user_id,
            "job_id": job_id
        }
    )

    try:
        job = job_service.get_job(job_id, current_user.user_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": "Job not found", "code": "NOT_FOUND"}
            )

        # Extract progress metadata from stage_metadata JSONB field
        progress_data = job.stage_metadata or {}

        # Extract elements detected (nested in progress metadata or quality report)
        elements = progress_data.get("elements_detected", {})
        if not elements and job.quality_report:
            # Fallback: extract from quality report if available
            quality_elements = job.quality_report.get("elements", {})
            elements = {
                "tables": quality_elements.get("tables", {}).get("count", 0),
                "images": quality_elements.get("images", {}).get("count", 0),
                "equations": quality_elements.get("equations", {}).get("count", 0),
                "chapters": quality_elements.get("chapters", {}).get("count", 0)
            }

        # Extract quality confidence from quality report
        quality_confidence = None
        if job.quality_report:
            quality_confidence = job.quality_report.get("overall_confidence")

        # Extract estimated cost (priority: stage_metadata > quality_report)
        estimated_cost = progress_data.get("estimated_cost")
        if estimated_cost is None and job.quality_report:
            estimated_cost = job.quality_report.get("estimated_cost")

        # Determine stage description based on status if not in metadata
        if progress_data.get("stage_description"):
            stage_description = progress_data["stage_description"]
        elif job.status == "COMPLETED":
            stage_description = "Conversion completed successfully!"
        elif job.status == "FAILED":
            stage_description = "Conversion failed"
        elif job.status == "ANALYZING":
            stage_description = "Analyzing document layout..."
        elif job.status == "EXTRACTING":
            stage_description = "Extracting content..."
        elif job.status == "STRUCTURING":
            stage_description = "Identifying document structure..."
        elif job.status == "GENERATING":
            stage_description = "Generating EPUB file..."
        elif job.status == "PROCESSING":
            stage_description = "Processing..."
        elif job.status == "QUEUED":
            stage_description = "Queued for processing..."
        else:
            stage_description = "Waiting to start..."

        # Build progress update response
        progress_update = ProgressUpdate(
            job_id=job.id,
            status=job.status,
            progress_percentage=job.progress,
            current_stage=progress_data.get("current_stage", job.status.lower()),
            stage_description=stage_description,
            elements_detected=ElementsDetected(**elements) if elements else ElementsDetected(),
            estimated_time_remaining=progress_data.get("estimated_time_remaining"),
            estimated_cost=estimated_cost,
            quality_confidence=int(quality_confidence) if quality_confidence else None,
            timestamp=progress_data.get("timestamp", datetime.utcnow())
        )

        request_duration = (datetime.utcnow() - request_start).total_seconds() * 1000

        # Use debug logging to avoid overwhelming logs during polling
        if request_duration > 200:
            logger.warning(
                "get_job_progress_slow",
                extra={
                    "user_id": current_user.user_id,
                    "job_id": job_id,
                    "duration_ms": request_duration,
                    "progress": job.progress
                }
            )

        return progress_update

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_job_progress_error",
            extra={
                "user_id": current_user.user_id,
                "job_id": job_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": f"Database error: {str(e)}", "code": "DATABASE_ERROR"}
        )


@router.delete(
    "/jobs/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete job",
    description="""
    Delete a conversion job (hard delete with async file cleanup).

    **Authentication Required:**
    - Requires valid Supabase JWT token in Authorization header
    - User must own the job (enforced by RLS)

    **Deletion Strategy:**
    - Hard delete: Permanently removes job record from database
    - Schedules asynchronous cleanup of associated files via Celery
    - Deleted jobs cannot be recovered

    **File Cleanup:**
    - Removes input file from uploads bucket (async)
    - Removes output file from downloads bucket (async)
    - Cleanup happens in background via Celery task

    **Returns:**
    - 204 No Content on success

    **Error Codes:**
    - `UNAUTHORIZED`: Missing or invalid JWT token
    - `NOT_FOUND`: Job not found or user doesn't own job
    - `DATABASE_ERROR`: Failed to delete job
    """
)
async def delete_job(
    job_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Delete a conversion job (hard delete with async file cleanup).

    Args:
        job_id: Job identifier (UUID)
        current_user: Authenticated user from JWT token
        job_service: Job service instance

    Raises:
        HTTPException(401): Authentication failure
        HTTPException(404): Job not found or user doesn't own job
        HTTPException(500): Database error
    """
    request_start = datetime.utcnow()
    logger.info(
        "delete_job_request",
        extra={
            "user_id": current_user.user_id,
            "job_id": job_id
        }
    )

    try:
        success, file_paths = job_service.delete_job(
            job_id=job_id,
            user_id=current_user.user_id,
            async_cleanup=True
        )

        if not success:
            logger.warning(
                "delete_job_not_found",
                extra={
                    "user_id": current_user.user_id,
                    "job_id": job_id
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": "Job not found", "code": "NOT_FOUND"}
            )

        # Schedule async file cleanup via Celery
        if file_paths:
            from app.tasks.cleanup import cleanup_job_files_task
            cleanup_job_files_task.delay(
                job_id=job_id,
                input_path=file_paths.get("input_path"),
                output_path=file_paths.get("output_path")
            )
            logger.info(
                "delete_job_cleanup_scheduled",
                extra={
                    "user_id": current_user.user_id,
                    "job_id": job_id
                }
            )

        request_duration = (datetime.utcnow() - request_start).total_seconds() * 1000
        logger.info(
            "delete_job_success",
            extra={
                "user_id": current_user.user_id,
                "job_id": job_id,
                "duration_ms": request_duration
            }
        )

        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "delete_job_error",
            extra={
                "user_id": current_user.user_id,
                "job_id": job_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": f"Database error: {str(e)}", "code": "DATABASE_ERROR"}
        )


@router.get(
    "/jobs/{job_id}/download",
    status_code=status.HTTP_200_OK,
    response_model=DownloadUrlResponse,
    summary="Get download URL for converted EPUB",
    description="""
    Get signed download URL for a completed conversion job.

    **Authentication Required:**
    - Requires valid Supabase JWT token in Authorization header
    - User must own the job (enforced by RLS)

    **Requirements:**
    - Job status must be COMPLETED
    - Output file must exist in storage

    **Returns:**
    - 200 OK with signed URL (1-hour expiry)
    - Includes expiration timestamp

    **Error Codes:**
    - `UNAUTHORIZED`: Missing or invalid JWT token
    - `NOT_FOUND`: Job not found, job not completed, or output file missing
    - `STORAGE_ERROR`: Failed to generate signed URL
    """
)
async def download_job(
    job_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
) -> DownloadUrlResponse:
    """
    Get download URL for completed conversion job.

    Args:
        job_id: Job identifier (UUID)
        current_user: Authenticated user from JWT token
        job_service: Job service instance

    Returns:
        DownloadUrlResponse: Signed download URL with expiration

    Raises:
        HTTPException(401): Authentication failure
        HTTPException(404): Job not found, not completed, or output missing
        HTTPException(500): Storage error
    """
    request_start = datetime.utcnow()
    logger.info(
        "download_job_request",
        extra={
            "user_id": current_user.user_id,
            "job_id": job_id
        }
    )

    try:
        result = job_service.generate_download_url(job_id, current_user.user_id)

        if not result:
            logger.warning(
                "download_job_not_ready",
                extra={
                    "user_id": current_user.user_id,
                    "job_id": job_id
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": "Job not found or conversion not complete", "code": "NOT_READY"}
            )

        signed_url, expires_at = result

        request_duration = (datetime.utcnow() - request_start).total_seconds() * 1000
        logger.info(
            "download_job_success",
            extra={
                "user_id": current_user.user_id,
                "job_id": job_id,
                "duration_ms": request_duration
            }
        )

        return DownloadUrlResponse(
            download_url=signed_url,
            expires_at=expires_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "download_job_error",
            extra={
                "user_id": current_user.user_id,
                "job_id": job_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": f"Storage error: {str(e)}", "code": "STORAGE_ERROR"}
        )


@router.get(
    "/jobs/{job_id}/files/input",
    status_code=status.HTTP_200_OK,
    response_model=DownloadUrlResponse,
    summary="Get signed URL for input PDF file",
    description="""
    Get signed URL for the original input PDF file (for preview comparison).

    **Authentication Required:**
    - Requires valid Supabase JWT token in Authorization header
    - User must own the job (enforced by RLS)

    **Returns:**
    - 200 OK with signed URL (1-hour expiry)
    - Includes expiration timestamp

    **Error Codes:**
    - `UNAUTHORIZED`: Missing or invalid JWT token
    - `NOT_FOUND`: Job not found or input file missing
    - `STORAGE_ERROR`: Failed to generate signed URL
    """
)
async def get_input_file(
    job_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
) -> DownloadUrlResponse:
    """
    Get signed URL for input PDF file (for split-screen preview).

    Args:
        job_id: Job identifier (UUID)
        current_user: Authenticated user from JWT token
        job_service: Job service instance

    Returns:
        DownloadUrlResponse: Signed URL with expiration

    Raises:
        HTTPException(401): Authentication failure
        HTTPException(404): Job not found or input missing
        HTTPException(500): Storage error
    """
    request_start = datetime.utcnow()
    logger.info(
        "get_input_file_request",
        extra={
            "user_id": current_user.user_id,
            "job_id": job_id
        }
    )

    try:
        result = job_service.generate_input_file_url(job_id, current_user.user_id)

        if not result:
            logger.warning(
                "get_input_file_not_found",
                extra={
                    "user_id": current_user.user_id,
                    "job_id": job_id
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": "Job not found or input file missing", "code": "NOT_FOUND"}
            )

        signed_url, expires_at = result

        request_duration = (datetime.utcnow() - request_start).total_seconds() * 1000
        logger.info(
            "get_input_file_success",
            extra={
                "user_id": current_user.user_id,
                "job_id": job_id,
                "duration_ms": request_duration
            }
        )

        return DownloadUrlResponse(
            download_url=signed_url,
            expires_at=expires_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_input_file_error",
            extra={
                "user_id": current_user.user_id,
                "job_id": job_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": f"Storage error: {str(e)}", "code": "STORAGE_ERROR"}
        )

@router.post(
    "/jobs/{job_id}/feedback",
    status_code=status.HTTP_200_OK,
    response_model=FeedbackResponse,
    summary="Submit feedback for a conversion job",
    description="""
    Submit user feedback (thumbs up/down) for a completed conversion job.

    **Authentication Required:**
    - Requires valid Supabase JWT token in Authorization header
    - Format: `Bearer <token>`

    **Request Body:**
    - `rating`: "positive" (👍) or "negative" (👎)
    - `comment`: Optional comment explaining the rating

    **Authorization:**
    - User can only submit feedback for their own jobs

    **Returns:**
    - 200 OK with feedback_id and confirmation
    - Creates record in job_feedback table
    - Logs analytics event to conversion_events table

    **Error Codes:**
    - `UNAUTHORIZED`: Missing or invalid JWT token
    - `NOT_FOUND`: Job not found or doesn't belong to user
    - `VALIDATION_ERROR`: Invalid feedback rating
    - `DATABASE_ERROR`: Failed to create feedback record
    """
)
async def submit_feedback(
    job_id: str,
    feedback: FeedbackSubmitRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
) -> FeedbackResponse:
    """
    Submit user feedback for a conversion job.

    Args:
        job_id: UUID of the conversion job
        feedback: Feedback data (rating and optional comment)
        current_user: Authenticated user from JWT token
        job_service: Job service instance

    Returns:
        FeedbackResponse: Confirmation with feedback_id

    Raises:
        HTTPException(401): Authentication failure
        HTTPException(404): Job not found
        HTTPException(500): Database error
    """
    request_start = datetime.utcnow()
    logger.info(
        "submit_feedback_request",
        extra={
            "user_id": current_user.user_id,
            "job_id": job_id,
            "rating": feedback.rating
        }
    )

    try:
        # Verify job exists and belongs to user
        job = job_service.get_job(job_id, current_user.user_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": "Job not found", "code": "NOT_FOUND"}
            )

        # Get Supabase client
        supabase = get_supabase_client()

        # Create feedback record
        feedback_data = {
            "job_id": job_id,
            "user_id": current_user.user_id,
            "rating": feedback.rating,
            "comment": feedback.comment
        }

        result = supabase.table("job_feedback").insert(feedback_data).execute()

        if not result.data:
            raise Exception("Failed to create feedback record")

        feedback_record = result.data[0]

        # Log analytics event
        event_data = {
            "job_id": job_id,
            "user_id": current_user.user_id,
            "event_type": f"feedback_{feedback.rating}",
            "event_data": {"rating": feedback.rating, "has_comment": bool(feedback.comment)}
        }
        supabase.table("conversion_events").insert(event_data).execute()

        request_duration = (datetime.utcnow() - request_start).total_seconds() * 1000
        logger.info(
            "submit_feedback_success",
            extra={
                "user_id": current_user.user_id,
                "job_id": job_id,
                "feedback_id": feedback_record["id"],
                "rating": feedback.rating,
                "duration_ms": request_duration
            }
        )

        return FeedbackResponse(
            feedback_id=feedback_record["id"],
            job_id=job_id,
            rating=feedback.rating,
            created_at=feedback_record["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "submit_feedback_error",
            extra={
                "user_id": current_user.user_id,
                "job_id": job_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": f"Failed to submit feedback: {str(e)}", "code": "DATABASE_ERROR"}
        )


@router.post(
    "/jobs/{job_id}/issues",
    status_code=status.HTTP_201_CREATED,
    response_model=IssueReportResponse,
    summary="Report an issue with a conversion job",
    description="""
    Report a specific issue with a conversion output (e.g., table formatting, missing images).

    **Authentication Required:**
    - Requires valid Supabase JWT token in Authorization header
    - Format: `Bearer <token>`

    **Request Body:**
    - `issue_type`: Category (table_formatting, missing_images, broken_chapters, incorrect_equations, font_issues, other)
    - `page_number`: Optional page number where issue occurs
    - `description`: Required detailed description (min 10 characters)
    - `screenshot_url`: Optional URL to screenshot (future enhancement)

    **Authorization:**
    - User can only report issues for their own jobs

    **Returns:**
    - 201 Created with issue_id and confirmation
    - Creates record in job_issues table
    - Logs analytics event to conversion_events table

    **Error Codes:**
    - `UNAUTHORIZED`: Missing or invalid JWT token
    - `NOT_FOUND`: Job not found or doesn't belong to user
    - `VALIDATION_ERROR`: Invalid issue data (description too short, etc.)
    - `DATABASE_ERROR`: Failed to create issue record
    """
)
async def report_issue(
    job_id: str,
    issue: IssueReportRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
) -> IssueReportResponse:
    """
    Report an issue with a conversion job.

    Args:
        job_id: UUID of the conversion job
        issue: Issue report data (type, page, description)
        current_user: Authenticated user from JWT token
        job_service: Job service instance

    Returns:
        IssueReportResponse: Confirmation with issue_id

    Raises:
        HTTPException(401): Authentication failure
        HTTPException(404): Job not found
        HTTPException(422): Validation error
        HTTPException(500): Database error
    """
    request_start = datetime.utcnow()
    logger.info(
        "report_issue_request",
        extra={
            "user_id": current_user.user_id,
            "job_id": job_id,
            "issue_type": issue.issue_type
        }
    )

    try:
        # Verify job exists and belongs to user
        job = job_service.get_job(job_id, current_user.user_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": "Job not found", "code": "NOT_FOUND"}
            )

        # Get Supabase client
        supabase = get_supabase_client()

        # Create issue record
        issue_data = {
            "job_id": job_id,
            "user_id": current_user.user_id,
            "issue_type": issue.issue_type,
            "page_number": issue.page_number,
            "description": issue.description,
            "screenshot_url": issue.screenshot_url
        }

        result = supabase.table("job_issues").insert(issue_data).execute()

        if not result.data:
            raise Exception("Failed to create issue record")

        issue_record = result.data[0]

        # Log analytics event
        event_data = {
            "job_id": job_id,
            "user_id": current_user.user_id,
            "event_type": "issue_reported",
            "event_data": {
                "issue_type": issue.issue_type,
                "has_page_number": bool(issue.page_number),
                "description_length": len(issue.description)
            }
        }
        supabase.table("conversion_events").insert(event_data).execute()

        request_duration = (datetime.utcnow() - request_start).total_seconds() * 1000
        logger.info(
            "report_issue_success",
            extra={
                "user_id": current_user.user_id,
                "job_id": job_id,
                "issue_id": issue_record["id"],
                "issue_type": issue.issue_type,
                "duration_ms": request_duration
            }
        )

        return IssueReportResponse(
            issue_id=issue_record["id"],
            job_id=job_id,
            issue_type=issue.issue_type,
            created_at=issue_record["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "report_issue_error",
            extra={
                "user_id": current_user.user_id,
                "job_id": job_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": f"Failed to report issue: {str(e)}", "code": "DATABASE_ERROR"}
        )


@router.post(
    "/{job_id}/events/download",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Download event logged successfully"},
        403: {"description": "User does not have permission to access this job"},
        404: {"description": "Job not found"},
        500: {"description": "Failed to log download event"}
    },
    tags=["jobs"]
)
async def log_download_event(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Log a download event for analytics (AC #7 - Story 5.4)

    Creates an analytics event record when a user downloads an EPUB file.

    **Authentication:** Required (JWT Bearer token)

    **Authorization:** User must own the job being downloaded

    **Analytics Event:** Logs to conversion_events table with:
    - event_type: "download"
    - event_data: {"timestamp": ISO8601}

    **Story:** 5.4 - Download & Feedback Flow
    **AC:** #7 - "Download events tracked (job_id, user_id, timestamp)"
    """
    request_start = datetime.now()

    try:
        logger.info(
            "log_download_event_start",
            extra={
                "user_id": current_user.user_id,
                "job_id": job_id,
                "timestamp": request_start.isoformat()
            }
        )

        # Verify job exists and belongs to user
        job_query = supabase.table("conversion_jobs") \
            .select("id, user_id, status") \
            .eq("id", job_id) \
            .execute()

        if not job_query.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": "Job not found", "code": "JOB_NOT_FOUND"}
            )

        job = job_query.data[0]

        if job["user_id"] != current_user.user_id:
            logger.warning(
                "log_download_event_unauthorized",
                extra={
                    "user_id": current_user.user_id,
                    "job_id": job_id,
                    "job_owner": job["user_id"]
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"detail": "Not authorized to access this job", "code": "FORBIDDEN"}
            )

        # Log download event to conversion_events table
        event_data = {
            "timestamp": datetime.now().isoformat()
        }

        event_record = supabase.table("conversion_events").insert({
            "job_id": job_id,
            "user_id": current_user.user_id,
            "event_type": "download",
            "event_data": event_data
        }).execute()

        request_duration = (datetime.now() - request_start).total_seconds() * 1000

        logger.info(
            "log_download_event_success",
            extra={
                "user_id": current_user.user_id,
                "job_id": job_id,
                "event_id": event_record.data[0]["id"],
                "duration_ms": request_duration
            }
        )

        return {"message": "Download event logged successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "log_download_event_error",
            extra={
                "user_id": current_user.user_id,
                "job_id": job_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": f"Failed to log download event: {str(e)}", "code": "DATABASE_ERROR"}
        )


@router.get(
    "/{job_id}/feedback/check",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Feedback existence check completed"},
        403: {"description": "User does not have permission to access this job"},
        404: {"description": "Job not found"}
    },
    tags=["jobs"]
)
async def check_existing_feedback(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Check if user has already submitted feedback for this job (AC #10 - Story 5.4)

    Prevents duplicate feedback submissions by checking job_feedback table.

    **Authentication:** Required (JWT Bearer token)

    **Authorization:** User must own the job

    **Returns:**
    - has_feedback: boolean indicating if feedback already exists
    - feedback_rating: "positive" | "negative" | null (if exists)

    **Story:** 5.4 - Download & Feedback Flow
    **AC:** #10 - "Duplicate feedback prevention (disable buttons after submission)"
    """
    supabase = get_supabase_client()

    try:
        # Verify job exists and belongs to user
        job_query = supabase.table("conversion_jobs") \
            .select("id, user_id") \
            .eq("id", job_id) \
            .execute()

        if not job_query.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": "Job not found", "code": "JOB_NOT_FOUND"}
            )

        job = job_query.data[0]

        if job["user_id"] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"detail": "Not authorized to access this job", "code": "FORBIDDEN"}
            )

        # Check for existing feedback
        feedback_query = supabase.table("job_feedback") \
            .select("id, rating") \
            .eq("job_id", job_id) \
            .eq("user_id", current_user.user_id) \
            .execute()

        has_feedback = len(feedback_query.data) > 0
        feedback_rating = feedback_query.data[0]["rating"] if has_feedback else None

        return {
            "has_feedback": has_feedback,
            "feedback_rating": feedback_rating
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "check_existing_feedback_error",
            extra={
                "user_id": current_user.user_id,
                "job_id": job_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": f"Failed to check feedback: {str(e)}", "code": "DATABASE_ERROR"}
        )


@router.get(
    "/jobs/{job_id}/feedback",
    status_code=status.HTTP_200_OK,
    response_model=FeedbackListResponse,
    summary="Get all feedback for a job",
    description="Retrieve all feedback submissions for a specific job"
)
async def get_job_feedback(
    job_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
) -> FeedbackListResponse:
    """
    Get all feedback for a specific job.

    Args:
        job_id: UUID of the conversion job
        current_user: Authenticated user from JWT token
        job_service: Job service instance

    Returns:
        FeedbackListResponse: List of feedback items
    """
    supabase = get_supabase_client()

    try:
        # Verify job exists and belongs to user
        job = job_service.get_job(job_id, current_user.user_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": "Job not found", "code": "NOT_FOUND"}
            )

        # Fetch feedback
        response = supabase.table("job_feedback") \
            .select("*") \
            .eq("job_id", job_id) \
            .order("created_at", desc=True) \
            .execute()

        feedback_items = [
            FeedbackItem(
                id=item["id"],
                rating=item["rating"],
                comment=item.get("comment"),
                created_at=item["created_at"]
            )
            for item in response.data
        ]

        return FeedbackListResponse(
            feedback=feedback_items,
            total=len(feedback_items)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job feedback: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": f"Failed to get feedback: {str(e)}", "code": "DATABASE_ERROR"}
        )


@router.get(
    "/jobs/{job_id}/issues",
    status_code=status.HTTP_200_OK,
    response_model=IssueListResponse,
    summary="Get all issues for a job",
    description="Retrieve all reported issues for a specific job"
)
async def get_job_issues(
    job_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
) -> IssueListResponse:
    """
    Get all issues for a specific job.

    Args:
        job_id: UUID of the conversion job
        current_user: Authenticated user from JWT token
        job_service: Job service instance

    Returns:
        IssueListResponse: List of issue items
    """
    supabase = get_supabase_client()

    try:
        # Verify job exists and belongs to user
        job = job_service.get_job(job_id, current_user.user_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": "Job not found", "code": "NOT_FOUND"}
            )

        # Fetch issues
        response = supabase.table("job_issues") \
            .select("*") \
            .eq("job_id", job_id) \
            .order("created_at", desc=True) \
            .execute()

        issue_items = [
            IssueItem(
                id=item["id"],
                issue_type=item["issue_type"],
                page_number=item.get("page_number"),
                description=item["description"],
                screenshot_url=item.get("screenshot_url"),
                created_at=item["created_at"]
            )
            for item in response.data
        ]

        return IssueListResponse(
            issues=issue_items,
            total=len(issue_items)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job issues: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": f"Failed to get issues: {str(e)}", "code": "DATABASE_ERROR"}
        )

