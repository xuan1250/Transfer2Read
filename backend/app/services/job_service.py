"""
Job Service - Business Logic Layer

Handles all business logic for conversion job operations.
Separates concerns from API routes following the Service Pattern.
"""
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from supabase import Client
import logging
import json
import redis

from app.schemas.job import JobSummary, JobDetail
from app.services.storage.supabase_storage import SupabaseStorageService

logger = logging.getLogger(__name__)


class JobService:
    """
    Service class for managing conversion jobs.

    Encapsulates all business logic for job operations including:
    - Job listing with pagination and filtering
    - Job retrieval and validation
    - Job deletion with file cleanup
    - Download URL generation
    """

    def __init__(
        self,
        supabase_client: Client,
        storage_service: SupabaseStorageService,
        redis_client: Optional[redis.Redis] = None
    ):
        """
        Initialize JobService.

        Args:
            supabase_client: Supabase client for database operations
            storage_service: Storage service for file operations
            redis_client: Optional Redis client for caching (reduces DB load)
        """
        self.supabase = supabase_client
        self.storage = storage_service
        self.redis = redis_client

    def list_jobs(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None
    ) -> Tuple[List[JobSummary], int]:
        """
        List jobs for a user with pagination and filtering.

        Args:
            user_id: User's UUID
            limit: Maximum number of jobs to return (1-100)
            offset: Pagination offset
            status: Optional status filter

        Returns:
            Tuple of (list of JobSummary objects, total count)

        Raises:
            Exception: If database query fails
        """
        logger.info(f"Listing jobs for user {user_id}, limit={limit}, offset={offset}, status={status}")

        # Build query - RLS automatically filters by user_id
        query = self.supabase.table("conversion_jobs").select("*", count="exact")

        # Apply status filter if provided
        if status:
            query = query.eq("status", status)

        # Apply pagination and sorting
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

        # Execute query
        response = query.execute()

        # Extract job data and total count
        jobs_data = response.data or []
        total = response.count or 0

        # Transform to JobSummary objects
        jobs = []
        for job_data in jobs_data:
            # Extract filename from input_path
            input_path = job_data.get("input_path", "")
            input_file = input_path.split("/")[-1] if input_path else "unknown.pdf"

            # Extract overall_confidence from quality_report if present
            overall_confidence = None
            if job_data.get("quality_report"):
                quality_report_dict = job_data["quality_report"]
                overall_confidence = quality_report_dict.get("overall_confidence")

            jobs.append(JobSummary(
                id=job_data["id"],
                status=job_data["status"],
                input_file=input_file,
                created_at=job_data["created_at"],
                completed_at=job_data.get("completed_at"),
                overall_confidence=overall_confidence
            ))

        logger.info(f"Found {len(jobs)} jobs for user {user_id} (total: {total})")
        return jobs, total

    def get_job(self, job_id: str, user_id: str) -> Optional[JobDetail]:
        """
        Get details of a specific job with Redis caching.

        Implements caching strategy:
        - Cache key format: job_status:{job_id}
        - TTL: 5 minutes (300 seconds)
        - Cache invalidated on job status updates

        Args:
            job_id: Job UUID
            user_id: User's UUID (for logging)

        Returns:
            JobDetail object if found, None if not found or user doesn't own job

        Raises:
            Exception: If database query fails
        """
        logger.info(f"Getting job {job_id} for user {user_id}")

        # Try cache first if Redis is available
        cache_key = f"job_status:{job_id}"
        if self.redis:
            try:
                cached_data = self.redis.get(cache_key)
                if cached_data:
                    logger.info(f"Cache hit for job {job_id}")
                    job_dict = json.loads(cached_data)

                    # Return cached JobDetail (quality_report is already a dict)
                    return JobDetail(
                        id=job_dict["id"],
                        user_id=job_dict["user_id"],
                        status=job_dict["status"],
                        input_path=job_dict["input_path"],
                        original_filename=job_dict.get("stage_metadata", {}).get("original_filename"),
                        output_path=job_dict.get("output_path"),
                        progress=job_dict.get("progress", 0),
                        stage_metadata=job_dict.get("stage_metadata", {}),
                        quality_report=job_dict.get("quality_report"),
                        created_at=datetime.fromisoformat(job_dict["created_at"]),
                        completed_at=datetime.fromisoformat(job_dict["completed_at"]) if job_dict.get("completed_at") else None
                    )
            except Exception as e:
                # Log cache error but continue to database fallback
                logger.warning(f"Redis cache read failed for job {job_id}: {str(e)}")

        # Cache miss or Redis unavailable - fetch from database
        logger.info(f"Cache miss for job {job_id}, fetching from database")

        # Query job - RLS automatically enforces user ownership
        response = self.supabase.table("conversion_jobs").select("*").eq("id", job_id).execute()

        if not response.data or len(response.data) == 0:
            logger.warning(f"Job {job_id} not found for user {user_id}")
            return None

        job_data = response.data[0]

        # Parse quality_report if present (keep as dict for JobDetail schema)
        quality_report = job_data.get("quality_report")

        logger.info(f"Found job {job_id} with status {job_data['status']}")

        job_detail = JobDetail(
            id=job_data["id"],
            user_id=job_data["user_id"],
            status=job_data["status"],
            input_path=job_data["input_path"],
            original_filename=job_data.get("stage_metadata", {}).get("original_filename"),
            output_path=job_data.get("output_path"),
            progress=job_data.get("progress", 0),
            stage_metadata=job_data.get("stage_metadata", {}),
            quality_report=quality_report,
            created_at=job_data["created_at"],
            completed_at=job_data.get("completed_at")
        )

        # Store in cache if Redis is available
        if self.redis:
            try:
                # Serialize JobDetail for caching
                cache_data = {
                    "id": job_detail.id,
                    "user_id": job_detail.user_id,
                    "status": job_detail.status,
                    "input_path": job_detail.input_path,
                    "output_path": job_detail.output_path,
                    "progress": job_detail.progress,
                    "stage_metadata": job_detail.stage_metadata,
                    "quality_report": job_detail.quality_report,  # Already a dict
                    "created_at": job_detail.created_at.isoformat() if isinstance(job_detail.created_at, datetime) else job_detail.created_at,
                    "completed_at": job_detail.completed_at.isoformat() if job_detail.completed_at and isinstance(job_detail.completed_at, datetime) else job_detail.completed_at
                }

                # Cache for 5 minutes (300 seconds)
                self.redis.setex(cache_key, 300, json.dumps(cache_data))
                logger.info(f"Cached job {job_id} for 5 minutes")
            except Exception as e:
                # Log cache write error but don't fail the request
                logger.warning(f"Redis cache write failed for job {job_id}: {str(e)}")

        return job_detail

    def delete_job(self, job_id: str, user_id: str, async_cleanup: bool = False) -> Tuple[bool, Optional[dict]]:
        """
        Delete a job (hard delete) with optional file cleanup.

        Args:
            job_id: Job UUID
            user_id: User's UUID (for logging)
            async_cleanup: If True, schedule async cleanup via Celery

        Returns:
            Tuple of (success: bool, file_paths: dict with input_path and output_path)

        Raises:
            Exception: If database operations fail
        """
        logger.info(f"Deleting job {job_id} for user {user_id}, async={async_cleanup}")

        # First, get job details to retrieve file paths before deletion
        response = self.supabase.table("conversion_jobs").select("*").eq("id", job_id).execute()

        if not response.data or len(response.data) == 0:
            logger.warning(f"Job {job_id} not found for user {user_id}")
            return False, None

        job_data = response.data[0]
        input_path = job_data.get("input_path")
        output_path = job_data.get("output_path")

        # Hard delete: Permanently remove from database
        delete_response = self.supabase.table("conversion_jobs").delete().eq("id", job_id).execute()

        if not delete_response.data or len(delete_response.data) == 0:
            logger.warning(f"Failed to delete job {job_id}")
            return False, None

        logger.info(f"Job {job_id} permanently deleted from database")

        # Invalidate Redis cache after deletion
        if self.redis:
            try:
                cache_key = f"job_status:{job_id}"
                self.redis.delete(cache_key)
                logger.info(f"Invalidated cache for deleted job {job_id}")
            except Exception as e:
                logger.warning(f"Redis cache invalidation failed for job {job_id}: {str(e)}")

        file_paths = {
            "input_path": input_path,
            "output_path": output_path
        }

        return True, file_paths

    def cleanup_job_files(self, input_path: Optional[str], output_path: Optional[str], job_id: str) -> None:
        """
        Clean up files associated with a deleted job.

        This method can be called synchronously or via Celery task.

        Args:
            input_path: Path to input file in uploads bucket
            output_path: Path to output file in downloads bucket
            job_id: Job UUID (for logging)
        """
        logger.info(f"Cleaning up files for job {job_id}")

        try:
            if input_path:
                self.storage.delete_file("uploads", input_path)
                logger.info(f"Deleted input file: {input_path}")

            if output_path:
                self.storage.delete_file("downloads", output_path)
                logger.info(f"Deleted output file: {output_path}")

        except Exception as e:
            # Log cleanup failure but don't fail the operation
            logger.warning(f"File cleanup failed for job {job_id}: {str(e)}")

    def generate_download_url(self, job_id: str, user_id: str) -> Optional[Tuple[str, datetime]]:
        """
        Generate signed download URL for a completed job.

        Args:
            job_id: Job UUID
            user_id: User's UUID (for logging)

        Returns:
            Tuple of (signed_url, expires_at) if successful, None if job not ready

        Raises:
            Exception: If storage operations fail
        """
        logger.info(f"Generating download URL for job {job_id}, user {user_id}")

        # Query job - RLS automatically enforces user ownership
        response = self.supabase.table("conversion_jobs").select("*").eq("id", job_id).execute()

        if not response.data or len(response.data) == 0:
            logger.warning(f"Job {job_id} not found for user {user_id}")
            return None

        job_data = response.data[0]
        job_status = job_data.get("status")
        output_path = job_data.get("output_path")

        # Verify job is completed
        if job_status != "COMPLETED":
            logger.warning(f"Job {job_id} is not completed (status: {job_status})")
            return None

        # Verify output file exists
        if not output_path:
            logger.error(f"Job {job_id} has no output file")
            return None

        # Generate signed URL (1-hour expiry)
        signed_url = self.storage.generate_signed_url(
            bucket="downloads",
            path=output_path,
            expires_in=3600  # 1 hour
        )

        expires_at = datetime.utcnow() + timedelta(seconds=3600)

        logger.info(f"Generated download URL for job {job_id}, expires at {expires_at}")

        return signed_url, expires_at

    def update_job_status(
        self,
        job_id: str,
        status: str,
        progress: Optional[int] = None,
        stage_metadata: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update conversion job status and progress in database.

        This is a reusable helper for pipeline tasks to update job status atomically.
        Automatically invalidates Redis cache on update.

        Args:
            job_id: Job UUID
            status: New status value (e.g., 'ANALYZING', 'EXTRACTING', 'COMPLETED')
            progress: Progress percentage (0-100)
            stage_metadata: JSONB metadata about current stage
            error_message: Error message if failed

        Returns:
            bool: True if update successful, False otherwise

        Raises:
            Exception: If database update fails
        """
        logger.info(f"Updating job {job_id}: status={status}, progress={progress}")

        try:
            # Build update data
            update_data = {"status": status}

            if progress is not None:
                update_data["progress"] = progress

            if stage_metadata is not None:
                update_data["stage_metadata"] = stage_metadata

            if error_message is not None:
                update_data["error_message"] = error_message

            # Update completed_at when status is COMPLETED
            if status == "COMPLETED":
                update_data["completed_at"] = datetime.utcnow().isoformat()

            # Execute update
            response = self.supabase.table("conversion_jobs").update(update_data).eq("id", job_id).execute()

            if not response.data:
                logger.warning(f"No job found with id {job_id} for update")
                return False

            # Invalidate Redis cache after successful update
            if self.redis:
                try:
                    cache_key = f"job_status:{job_id}"
                    self.redis.delete(cache_key)
                    logger.info(f"Invalidated cache for job {job_id}")
                except Exception as e:
                    # Log cache invalidation error but don't fail the update
                    logger.warning(f"Redis cache invalidation failed for job {job_id}: {str(e)}")

            logger.info(f"Successfully updated job {job_id} status to {status}")
            return True

        except Exception as e:
            logger.error(f"Failed to update job {job_id} status: {str(e)}", exc_info=True)
            raise

    def check_cancellation(self, job_id: str) -> bool:
        """
        Check if job has been cancelled by checking deleted_at field.

        Args:
            job_id: Job UUID

        Returns:
            bool: True if job is cancelled, False otherwise
        """
        try:
            response = self.supabase.table("conversion_jobs").select("deleted_at").eq("id", job_id).execute()

            if not response.data:
                logger.warning(f"Job {job_id} not found during cancellation check")
                return False

            job_data = response.data[0]
            is_cancelled = job_data.get("deleted_at") is not None

            if is_cancelled:
                logger.info(f"Job {job_id} has been cancelled")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to check cancellation for job {job_id}: {str(e)}")
            return False
