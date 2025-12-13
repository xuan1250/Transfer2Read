"""
Celery Tasks for Background Job Processing

Handles asynchronous operations like file cleanup.
"""
from celery import shared_task
import logging

from app.core.supabase import get_supabase_client
from app.services.storage.supabase_storage import SupabaseStorageService
from app.services.job_service import JobService

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # Retry after 1 minute
    autoretry_for=(Exception,)
)
def cleanup_job_files_task(self, job_id: str, input_path: str = None, output_path: str = None):
    """
    Clean up files associated with a deleted job (asynchronous).

    This task is scheduled when a job is deleted to remove associated files
    from Supabase Storage without blocking the DELETE request.

    Args:
        job_id: Job UUID (for logging and tracking)
        input_path: Path to input file in uploads bucket (optional)
        output_path: Path to output file in downloads bucket (optional)

    Retry Policy:
        - Max retries: 3
        - Retry delay: 60 seconds (exponential backoff)
        - Auto-retry on any Exception

    Example:
        >>> cleanup_job_files_task.delay(
        ...     job_id="550e8400-e29b-41d4-a716-446655440000",
        ...     input_path="uploads/user-id/job-id/input.pdf",
        ...     output_path="downloads/user-id/job-id/output.epub"
        ... )
    """
    logger.info(f"[Celery] Starting file cleanup for job {job_id}")

    try:
        # Initialize services
        supabase = get_supabase_client()
        storage_service = SupabaseStorageService(supabase)
        job_service = JobService(supabase, storage_service)

        # Perform cleanup
        job_service.cleanup_job_files(input_path, output_path, job_id)

        logger.info(f"[Celery] File cleanup completed for job {job_id}")
        return {"status": "success", "job_id": job_id}

    except Exception as e:
        logger.error(f"[Celery] File cleanup failed for job {job_id}: {str(e)}")
        # Celery will automatically retry due to autoretry_for
        raise
