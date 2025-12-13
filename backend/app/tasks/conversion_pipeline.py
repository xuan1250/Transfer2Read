"""
Conversion Pipeline Tasks

Main orchestrator for PDF to EPUB conversion pipeline using Celery.
Implements a chain of tasks: analyze → extract → structure → generate → qa
"""
import logging
import os
import shutil
from datetime import datetime
from typing import Dict, Any, Optional
from celery import chain
from supabase import create_client, Client
import redis

from app.core.celery_app import celery_app
from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions
# ============================================================================

def get_supabase_client() -> Client:
    """Get Supabase client for database operations."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


def get_redis_client() -> Optional[redis.Redis]:
    """
    Get Redis client for cache invalidation.

    Returns:
        redis.Redis: Redis client or None if connection fails
    """
    try:
        client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        client.ping()
        return client
    except Exception as e:
        logger.warning(f"Redis connection failed: {str(e)}. Cache invalidation disabled.")
        return None


def update_job_status(
    job_id: str,
    status: str,
    progress: int = None,
    stage_metadata: Dict[str, Any] = None,
    error_message: str = None
) -> None:
    """
    Update conversion job status in database and invalidate cache.

    Args:
        job_id: Job UUID
        status: New status value
        progress: Progress percentage (0-100)
        stage_metadata: JSONB metadata about current stage
        error_message: Error message if failed
    """
    try:
        supabase = get_supabase_client()

        # Build update data
        update_data = {"status": status}

        if progress is not None:
            update_data["progress"] = progress

        if stage_metadata is not None:
            # Merge with existing metadata if present
            update_data["stage_metadata"] = stage_metadata

        if error_message is not None:
            update_data["error_message"] = error_message

        # Update status to COMPLETED also sets completed_at
        if status == "COMPLETED":
            update_data["completed_at"] = datetime.utcnow().isoformat()

        # Execute update
        supabase.table("conversion_jobs").update(update_data).eq("id", job_id).execute()

        logger.info(f"Updated job {job_id}: status={status}, progress={progress}")

        # Invalidate Redis cache after successful update
        redis_client = get_redis_client()
        if redis_client:
            try:
                cache_key = f"job_status:{job_id}"
                redis_client.delete(cache_key)
                logger.info(f"Invalidated cache for job {job_id}")
            except Exception as e:
                logger.warning(f"Redis cache invalidation failed for job {job_id}: {str(e)}")

    except Exception as e:
        logger.error(f"Failed to update job {job_id} status: {str(e)}")
        raise


def check_cancellation(job_id: str) -> bool:
    """
    Check if job has been cancelled by checking deleted_at field.

    Args:
        job_id: Job UUID

    Returns:
        True if job is cancelled, False otherwise

    Raises:
        TaskCancelled: If job is cancelled
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table("conversion_jobs").select("deleted_at").eq("id", job_id).execute()

        if not response.data:
            logger.warning(f"Job {job_id} not found during cancellation check")
            return False

        job_data = response.data[0]
        is_cancelled = job_data.get("deleted_at") is not None

        if is_cancelled:
            logger.info(f"Job {job_id} has been cancelled")
            raise TaskCancelled(f"Job {job_id} was cancelled by user")

        return False

    except TaskCancelled:
        raise
    except Exception as e:
        logger.error(f"Failed to check cancellation for job {job_id}: {str(e)}")
        return False


def cleanup_temp_files(job_id: str) -> None:
    """
    Cleanup temporary files created during conversion.

    Args:
        job_id: Job UUID
    """
    temp_dir = f"/tmp/{job_id}"
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temp directory: {temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory {temp_dir}: {str(e)}")


# ============================================================================
# Custom Exceptions
# ============================================================================

class TaskCancelled(Exception):
    """Raised when task is cancelled by user."""
    pass


class InvalidPDFError(Exception):
    """Raised when PDF file is invalid or corrupted."""
    pass


class CorruptedFileError(Exception):
    """Raised when file is corrupted."""
    pass


class UnsupportedFormatError(Exception):
    """Raised when file format is not supported."""
    pass


# ============================================================================
# Pipeline Tasks
# ============================================================================

@celery_app.task(
    name='conversion_pipeline',
    bind=True,
    autoretry_for=(Exception,),
    max_retries=0,  # No retry for main orchestrator
    soft_time_limit=900,   # 15 minutes soft limit
    time_limit=1200        # 20 minutes hard limit
)
def conversion_pipeline(self, job_id: str) -> Dict[str, Any]:
    """
    Main orchestrator for PDF to EPUB conversion pipeline.

    Chains together 5 stages:
    1. analyze_layout - PDF layout analysis with AI
    2. extract_content - Content extraction from analyzed PDF
    3. identify_structure - TOC and chapter structure recognition
    4. generate_epub - EPUB file generation from structured content
    5. calculate_quality_score - Quality assurance scoring

    Args:
        job_id: UUID of the conversion job

    Returns:
        dict: Final pipeline result with EPUB path and quality report
    """
    logger.info(f"Starting conversion pipeline for job {job_id}")

    try:
        # Check if job is cancelled before starting
        check_cancellation(job_id)

        # Build the conversion chain
        workflow = chain(
            analyze_layout.s(job_id),
            extract_content.s(),
            identify_structure.s(),
            generate_epub.s(),
            calculate_quality_score.s()
        )

        # Execute the chain
        result = workflow.apply_async()

        # Wait for completion
        final_result = result.get()

        logger.info(f"Conversion pipeline completed for job {job_id}")
        return final_result

    except TaskCancelled as e:
        logger.warning(f"Pipeline cancelled for job {job_id}: {str(e)}")
        update_job_status(job_id, "CANCELLED", error_message="Job cancelled by user")
        cleanup_temp_files(job_id)
        raise

    except (InvalidPDFError, CorruptedFileError, UnsupportedFormatError) as e:
        # Permanent errors - don't retry
        logger.error(f"Permanent error in pipeline for job {job_id}: {str(e)}")
        update_job_status(job_id, "FAILED", error_message=str(e))
        cleanup_temp_files(job_id)
        raise

    except Exception as e:
        # Unexpected errors
        logger.error(f"Pipeline failed for job {job_id}: {str(e)}", exc_info=True)
        update_job_status(job_id, "FAILED", error_message=f"Conversion failed: {str(e)}")
        cleanup_temp_files(job_id)
        raise


@celery_app.task(
    name='analyze_layout',
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=900,  # 15 minutes max backoff
    soft_time_limit=900,
    time_limit=1200
)
def analyze_layout(self, job_id: str) -> Dict[str, Any]:
    """
    Analyze PDF layout using AI (Placeholder for Story 4.2).

    This task will use GPT-4o to detect layout elements (tables, images, text blocks).
    Current implementation is a placeholder that updates status to ANALYZING.

    Args:
        job_id: Job UUID

    Returns:
        dict: Contains job_id and layout_analysis results
    """
    logger.info(f"[Task 1/5] Analyzing layout for job {job_id}")

    try:
        # Check cancellation
        check_cancellation(job_id)

        # Update status to ANALYZING (25% progress)
        update_job_status(
            job_id=job_id,
            status="ANALYZING",
            progress=25,
            stage_metadata={
                "current_stage": "ANALYZING",
                "progress_percent": 25,
                "stage_started_at": datetime.utcnow().isoformat()
            }
        )

        # TODO: Implement in Story 4.2
        # - Load PDF from Supabase Storage
        # - Convert pages to images
        # - Send to GPT-4o for layout analysis
        # - Return structured layout data

        layout_analysis = {
            "placeholder": True,
            "message": "Layout analysis to be implemented in Story 4.2"
        }

        logger.info(f"Layout analysis completed for job {job_id}")
        return {"job_id": job_id, "layout_analysis": layout_analysis}

    except TaskCancelled:
        raise
    except Exception as e:
        logger.error(f"Layout analysis failed for job {job_id}: {str(e)}", exc_info=True)
        raise


@celery_app.task(
    name='extract_content',
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=900,
    soft_time_limit=900,
    time_limit=1200
)
def extract_content(self, previous_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract content from PDF based on layout analysis (Placeholder for Story 4.2).

    This task will extract text, tables, and images from the PDF.
    Current implementation is a placeholder that updates status to EXTRACTING.

    Args:
        previous_result: Output from analyze_layout task

    Returns:
        dict: Contains job_id, layout_analysis, and extracted_content
    """
    job_id = previous_result["job_id"]
    logger.info(f"[Task 2/5] Extracting content for job {job_id}")

    try:
        # Check cancellation
        check_cancellation(job_id)

        # Update status to EXTRACTING (50% progress)
        update_job_status(
            job_id=job_id,
            status="EXTRACTING",
            progress=50,
            stage_metadata={
                "current_stage": "EXTRACTING",
                "progress_percent": 50,
                "stage_started_at": datetime.utcnow().isoformat()
            }
        )

        # TODO: Implement in Story 4.2
        # - Use layout analysis to extract content
        # - Preserve reading order
        # - Extract tables as HTML
        # - Extract images with captions

        extracted_content = {
            "placeholder": True,
            "message": "Content extraction to be implemented in Story 4.2"
        }

        logger.info(f"Content extraction completed for job {job_id}")
        return {**previous_result, "extracted_content": extracted_content}

    except TaskCancelled:
        raise
    except Exception as e:
        logger.error(f"Content extraction failed for job {job_id}: {str(e)}", exc_info=True)
        raise


@celery_app.task(
    name='identify_structure',
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=900,
    soft_time_limit=900,
    time_limit=1200
)
def identify_structure(self, previous_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Identify document structure (TOC, chapters) using AI (Placeholder for Story 4.3).

    This task will use AI to detect chapter boundaries and build a table of contents.
    Current implementation is a placeholder that updates status to STRUCTURING.

    Args:
        previous_result: Output from extract_content task

    Returns:
        dict: Contains job_id, layout_analysis, extracted_content, and structure
    """
    job_id = previous_result["job_id"]
    logger.info(f"[Task 3/5] Identifying structure for job {job_id}")

    try:
        # Check cancellation
        check_cancellation(job_id)

        # Update status to STRUCTURING (75% progress)
        update_job_status(
            job_id=job_id,
            status="STRUCTURING",
            progress=75,
            stage_metadata={
                "current_stage": "STRUCTURING",
                "progress_percent": 75,
                "stage_started_at": datetime.utcnow().isoformat()
            }
        )

        # TODO: Implement in Story 4.3
        # - Analyze content for chapter markers
        # - Build hierarchical structure
        # - Generate TOC entries

        structure = {
            "placeholder": True,
            "message": "Structure identification to be implemented in Story 4.3"
        }

        logger.info(f"Structure identification completed for job {job_id}")
        return {**previous_result, "structure": structure}

    except TaskCancelled:
        raise
    except Exception as e:
        logger.error(f"Structure identification failed for job {job_id}: {str(e)}", exc_info=True)
        raise


@celery_app.task(
    name='generate_epub',
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=900,
    soft_time_limit=900,
    time_limit=1200
)
def generate_epub(self, previous_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate EPUB file from structured content (Placeholder for Story 4.4).

    This task will create a valid EPUB 3 file using ebooklib.
    Current implementation is a placeholder that updates status to GENERATING.

    Args:
        previous_result: Output from identify_structure task

    Returns:
        dict: Contains job_id and epub_path
    """
    job_id = previous_result["job_id"]
    logger.info(f"[Task 4/5] Generating EPUB for job {job_id}")

    try:
        # Check cancellation
        check_cancellation(job_id)

        # Update status to GENERATING (90% progress)
        update_job_status(
            job_id=job_id,
            status="GENERATING",
            progress=90,
            stage_metadata={
                "current_stage": "GENERATING",
                "progress_percent": 90,
                "stage_started_at": datetime.utcnow().isoformat()
            }
        )

        # TODO: Implement in Story 4.4
        # - Create EPUB container
        # - Generate chapter XHTML files
        # - Create NCX and nav files
        # - Upload to Supabase Storage

        epub_path = ""  # Will be set in Story 4.4

        logger.info(f"EPUB generation completed for job {job_id}")
        return {**previous_result, "epub_path": epub_path}

    except TaskCancelled:
        raise
    except Exception as e:
        logger.error(f"EPUB generation failed for job {job_id}: {str(e)}", exc_info=True)
        raise


@celery_app.task(
    name='calculate_quality_score',
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=900,
    soft_time_limit=900,
    time_limit=1200
)
def calculate_quality_score(self, previous_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate quality score for conversion (Placeholder for Story 4.5).

    This task will run quality checks and generate a confidence score.
    Current implementation is a placeholder that updates status to COMPLETED.

    Args:
        previous_result: Output from generate_epub task

    Returns:
        dict: Contains job_id, epub_path, and quality_report
    """
    job_id = previous_result["job_id"]
    logger.info(f"[Task 5/5] Calculating quality score for job {job_id}")

    try:
        # Check cancellation
        check_cancellation(job_id)

        # TODO: Implement in Story 4.5
        # - Validate EPUB structure
        # - Calculate fidelity score
        # - Generate quality report

        quality_report = {
            "placeholder": True,
            "message": "Quality scoring to be implemented in Story 4.5"
        }

        # Update status to COMPLETED (100% progress)
        update_job_status(
            job_id=job_id,
            status="COMPLETED",
            progress=100,
            stage_metadata={
                "current_stage": "COMPLETED",
                "progress_percent": 100,
                "stage_started_at": datetime.utcnow().isoformat()
            }
        )

        # Cleanup temp files on success
        cleanup_temp_files(job_id)

        logger.info(f"Quality scoring completed for job {job_id}")
        return {**previous_result, "quality_report": quality_report}

    except TaskCancelled:
        raise
    except Exception as e:
        logger.error(f"Quality scoring failed for job {job_id}: {str(e)}", exc_info=True)
        raise
