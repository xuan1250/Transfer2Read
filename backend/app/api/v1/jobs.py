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
    current_user: AuthenticatedUser = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
) -> JobDetail:
    """
    Get details of a specific conversion job.

    Args:
        job_id: Job identifier (UUID)
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
                "duration_ms": request_duration
            }
        )

        return job

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


@router.delete(
    "/jobs/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete job",
    description="""
    Delete a conversion job (soft delete with async file cleanup).

    **Authentication Required:**
    - Requires valid Supabase JWT token in Authorization header
    - User must own the job (enforced by RLS)

    **Deletion Strategy:**
    - Soft delete: Sets `deleted_at` timestamp on job record
    - Schedules asynchronous cleanup of associated files via Celery
    - Deleted jobs are excluded from list queries via RLS policy

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
    Delete a conversion job (soft delete with async file cleanup).

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
