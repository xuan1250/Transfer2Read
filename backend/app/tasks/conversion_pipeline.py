"""
Conversion Pipeline Tasks

Main orchestrator for PDF to EPUB conversion pipeline using Celery.
Implements a chain of tasks: analyze → extract → structure → generate → qa
"""
import logging
import os
import shutil
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from celery import chain
from supabase import create_client, Client
import redis

from app.core.celery_app import celery_app
from app.core.config import settings
from app.services.stirling.stirling_client import StirlingPDFClient
from app.services.storage.supabase_storage import SupabaseStorageService
from app.services.ai.structure_analyzer import StructureAnalyzer
from app.services.conversion import text_chunker
from app.services.conversion.heuristic_structure import HeuristicStructureDetector
from app.schemas.document_structure import DocumentStructure
from bs4 import BeautifulSoup
import fitz  # PyMuPDF

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
    DEPRECATED: This orchestrator task is deprecated.

    The chain is now launched directly from the API endpoint to avoid
    the anti-pattern of calling .get() within a task.

    See: app/api/v1/upload.py for the new pattern

    This task remains for backwards compatibility but should not be used.
    """
    logger.warning(
        f"DEPRECATED: conversion_pipeline orchestrator called for job {job_id}. "
        "Chain should be launched directly from API endpoint."
    )

    try:
        # Check if job is cancelled before starting
        check_cancellation(job_id)

        # Build the conversion chain
        workflow = chain(
            convert_to_html.s(job_id),
            extract_content.s(),
            identify_structure.s(),
            generate_epub.s(),
            calculate_quality_score.s()
        )

        # Execute the chain asynchronously (NO .get() - fire and forget)
        result = workflow.apply_async()

        # Return the task ID instead of blocking with .get()
        logger.info(f"Conversion pipeline dispatched for job {job_id}, task_id: {result.id}")
        return {"job_id": job_id, "task_id": result.id, "status": "dispatched"}

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
    name='convert_to_html',
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=900,  # 15 minutes max backoff
    soft_time_limit=900,
    time_limit=1200
)
def convert_to_html(self, job_id: str) -> Dict[str, Any]:
    """
    Convert PDF to HTML using Stirling-PDF (Stage 1).

    Replaces AI Layout Analysis (Story 4.2) with direct PDF->HTML conversion.
    This preserves layout structure, tables, and images using Stirling-PDF's engine.

    Args:
        job_id: Job UUID

    Returns:
        dict: Contains job_id, html_content, and pdf_bytes
    """
    logger.info(f"[Task 1/5] Converting PDF to HTML for job {job_id}")

    try:
        # Check cancellation
        check_cancellation(job_id)

        # Update status to CONVERTING (20% progress)
        update_job_status(
            job_id=job_id,
            status="CONVERTING",
            progress=20,
            stage_metadata={
                "current_stage": "html_conversion",
                "stage_description": "Converting PDF to HTML via Stirling-PDF...",
                "progress_percent": 20,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # Get job details from database
        supabase = get_supabase_client()
        job_response = supabase.table("conversion_jobs").select("*").eq("id", job_id).execute()

        if not job_response.data:
            raise ValueError(f"Job {job_id} not found in database")

        job_data = job_response.data[0]
        user_id = job_data["user_id"]
        input_path = job_data["input_path"]

        # Download PDF from Supabase Storage to temp location
        storage_service = SupabaseStorageService(supabase)
        temp_pdf_path = f"/tmp/{job_id}_input.pdf"

        logger.info(f"Downloading PDF from storage: {input_path}")
        storage_service.download_file(
            bucket="uploads",
            file_path=input_path,
            local_path=temp_pdf_path
        )

        # Read PDF bytes
        with open(temp_pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        # Convert to HTML using Stirling-PDF
        s_client = StirlingPDFClient()
        logger.info(f"Sending request to Stirling-PDF...")
        
        try:
            html_content = asyncio.run(s_client.convert_pdf_to_html(
                pdf_bytes=pdf_bytes,
                filename=os.path.basename(input_path)
            ))
        except Exception as e:
            logger.error(f"Stirling-PDF conversion failed: {e}")
            raise

        # Check Stirling-PDF version for metadata
        try:
            version_info = asyncio.run(s_client.get_version())
        except Exception:
            version_info = {"version": "unknown"}

        # Store HTML content in database
        # Note: Requires migration 006_stirling_integration
        supabase.table("conversion_jobs").update({
            "html_content": html_content,
            "stirling_metadata": {
                "version_info": version_info,
                "converted_at": datetime.utcnow().isoformat(),
                "content_length": len(html_content)
            }
        }).eq("id", job_id).execute()

        # Convert status update (40% complete)
        update_job_status(
            job_id=job_id,
            status="CONVERTING",
            progress=40,
            stage_metadata={
                "current_stage": "html_conversion",
                "stage_description": "HTML conversion completed",
                "progress_percent": 40,
                "html_length": len(html_content),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # Cleanup temp file
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

        logger.info(f"PDF->HTML conversion completed for job {job_id} ({len(html_content)} chars)")

        return {
            "job_id": job_id,
            "user_id": user_id,
            "pdf_bytes": pdf_bytes,  # Keep for cover generation
            "html_content": html_content
        }

    except TaskCancelled:
        raise
    except Exception as e:
        logger.error(f"HTML conversion failed for job {job_id}: {str(e)}", exc_info=True)
        # Cleanup temp file on error
        temp_pdf_path = f"/tmp/{job_id}_input.pdf"
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
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
    Process and clean HTML content (Stage 2).
    
    Parses the HTML from Stirling-PDF, validates structure, and prepares
    content for AI structure analysis.
    
    Args:
        previous_result: Output from convert_to_html task
        
    Returns:
        dict: Updated result with cleaned_html and formatting stats
    """
    job_id = previous_result["job_id"]
    logger.info(f"[Task 2/5] Processing HTML content for job {job_id}")

    try:
        # Check cancellation
        check_cancellation(job_id)

        # Update status to EXTRACTING (50% progress)
        update_job_status(
            job_id=job_id,
            status="EXTRACTING",
            progress=50,
            stage_metadata={
                "current_stage": "extraction",
                "stage_description": "Parsing and cleaning HTML...",
                "progress_percent": 50,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        html_content = previous_result.get("html_content")
        if not html_content:
            raise ValueError("No HTML content found from previous stage")

        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Basic cleanup
        # Remove empty paragraphs
        for p in soup.find_all('p'):
            if not p.get_text(strip=True) and not p.find('img'):
                p.decompose()
        
        # Count elements for stats
        total_images = len(soup.find_all('img'))
        total_tables = len(soup.find_all('table'))
        total_paragraphs = len(soup.find_all('p'))
        
        # Extract text for Structure Analysis (Stage 3)
        # We'll pass the full HTML, but extracting text helps with size checks
        text_content = soup.get_text(separator='\n\n', strip=True)
        
        logger.info(
            f"HTML processed: {total_images} images, {total_tables} tables, "
            f"{total_paragraphs} paragraphs"
        )

        return {
            **previous_result,
            "cleaned_html": str(soup),
            "extraction_stats": {
                "images": total_images,
                "tables": total_tables,
                "paragraphs": total_paragraphs,
                "text_length": len(text_content)
            }
        }

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
    Identify document structure (TOC, chapters) using AI structure analysis (Stage 3).

    Uses GPT-4o to analyze text content extracted from HTML.
    Uses PyMuPDF to extract metadata (page count, title) from original PDF.

    Args:
        previous_result: Output from extract_content task containing:
            - job_id: Conversion job UUID
            - html_content: Converted HTML
            - cleaned_html: Cleaned HTML from Stage 2
            - pdf_bytes: Original PDF bytes

    Returns:
        dict: Updated result with document_structure
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
                "current_stage": "structure",
                "stage_description": "Analyzing document structure...",
                "progress_percent": 75,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        cleaned_html = previous_result.get("cleaned_html")
        pdf_bytes = previous_result.get("pdf_bytes")
        
        if not cleaned_html:
            raise ValueError("No HTML content available for structure analysis")

        # Extract metadata using PyMuPDF
        page_count = 0
        metadata_title = None
        metadata_author = None
        
        if pdf_bytes:
            try:
                with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                    page_count = len(doc)
                    metadata_title = doc.metadata.get("title")
                    metadata_author = doc.metadata.get("author")
                    logger.info(f"Extracted metadata: {page_count} pages, Title: {metadata_title}")
            except Exception as e:
                logger.warning(f"Failed to extract PDF metadata: {e}")
        
        # Extract plain text from HTML for AI analysis
        # We use BeautifulSoup again here to get clean text
        soup = BeautifulSoup(cleaned_html, 'html.parser')
        full_text = soup.get_text(separator='\n\n', strip=True)
        
        # Determine language (simple heuristic or default to en)
        # TODO: Use langdetect or similar if needed, for now default en
        primary_language = "en" 
        
        logger.info(
            f"Extracted text for structure analysis: {len(full_text)} chars, "
            f"Page Count: {page_count}"
        )

        # Check if chunking is needed
        needs_chunking = text_chunker.detect_needs_chunking(
            page_count=page_count or 1, # Fallback if 0
            text_length=len(full_text),
            max_pages=settings.STRUCTURE_CHUNK_SIZE
        )

        # Initialize structure analyzer
        analyzer = StructureAnalyzer(
            api_key=settings.OPENAI_API_KEY,
            temperature=0.0,
            timeout=settings.STRUCTURE_ANALYSIS_TIMEOUT
        )

        document_structure = None

        # Scenario 1: Small document - analyze as single chunk
        if not needs_chunking:
            try:
                logger.info(f"Analyzing structure in single pass")

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    doc_struct, token_usage = loop.run_until_complete(
                        analyzer.analyze_structure(
                            text=full_text,
                            language=primary_language,
                            page_count=page_count,
                            document_title=metadata_title
                        )
                    )
                    
                    document_structure = doc_struct.model_dump()
                    
                    # Add usage stats
                    document_structure["analysis_stats"] = {
                        "tokens_used": token_usage,
                        "method": "ai_full"
                    }
                    # Keep author if found
                    if metadata_author and not document_structure.get("author"):
                        document_structure["author"] = metadata_author

                finally:
                    if not loop.is_closed():
                        loop.run_until_complete(analyzer.aclose())
                        loop.close()

            except Exception as e:
                logger.error(f"AI structure analysis failed: {e}")
                # Fallback to Heuristic
                logger.info("Falling back to heuristic structure detection")
                detector = HeuristicStructureDetector()
                document_structure = detector.detect_structure(
                    text=full_text,
                    page_count=page_count,
                    title=metadata_title
                ).model_dump()
                document_structure["analysis_stats"] = {"method": "heuristic_fallback"}

        else:
            # Scenario 2: Large document - chunking
            # For now, simplistic fallback or implement chunking logic for HTML text
            # Reusing existing chunker logic which expects "pages" mapping?
            # Existing chunker might expect page-mapped text.
            # Here we have one big blob.
            # We'll try to analyze the first X chars to get TOC, which is usually at start.
            logger.info("Large document detected. Analyzing start of text for TOC.")
            
            truncated_text = full_text[:100000] # Analyze first 100k chars
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                doc_struct, token_usage = loop.run_until_complete(
                    analyzer.analyze_structure(
                        text=truncated_text,
                        language=primary_language,
                        page_count=page_count,
                        document_title=metadata_title
                    )
                )
                document_structure = doc_struct.model_dump()
                document_structure["analysis_stats"] = {
                    "tokens_used": token_usage,
                    "method": "ai_truncated"
                }
            finally:
                if not loop.is_closed():
                    loop.run_until_complete(analyzer.aclose())
                    loop.close()

        # Store result in database
        supabase = get_supabase_client()
        supabase.table("conversion_jobs").update({
            "document_structure": document_structure
        }).eq("id", job_id).execute()

        logger.info(f"Structure identified: {len(document_structure.get('chapters', []))} chapters")

        return {
            **previous_result,
            "document_structure": document_structure
        }

    except TaskCancelled:
        raise
    except Exception as e:
        logger.error(f"Structure identification failed for job {job_id}: {str(e)}", exc_info=True)
        # Fallback to empty structure to allow EPUB generation to proceed (flat structure)
        return {
            **previous_result,
            "document_structure": {
                "title": "Unknown Document",
                "chapters": [],
                "toc": {"items": []},
                "confidence_score": 0
            }
        }
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
    Generate EPUB file from analyzed content (Stage 4).

    Creates EPUB 3.0 file with:
    - AI-detected structure (TOC, chapters)
    - HTML content from Stirling-PDF
    - Proper metadata and cover image
    - Embedded fonts and styles

    Args:
        previous_result: Output from identify_structure task containing:
            - job_id: Conversion job UUID
            - html_content: Converted HTML
            - document_structure: TOC and chapters
            - pdf_bytes: Original PDF bytes

    Returns:
        dict: Updated result with epub_path and storage location
    """
    from app.services.conversion.epub_generator import EpubGenerator
    from app.services.storage.supabase_storage import SupabaseStorageService
    from app.schemas.document_structure import DocumentStructure
    from pydantic import ValidationError

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
                "current_stage": "epub_generation",
                "stage_description": "Generating EPUB file...",
                "progress_percent": 90,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        document_structure_dict = previous_result.get("document_structure")
        html_content = previous_result.get("html_content")
        pdf_bytes = previous_result.get("pdf_bytes")
        user_id = previous_result.get("user_id")

        if not document_structure_dict:
            raise ValueError("No document structure found for EPUB generation")
        
        if not html_content:
            logger.warning("No HTML content provided, attempting to retrieve from DB")
            # Retrieval logic if missing
            supabase = get_supabase_client()
            job = supabase.table("conversion_jobs").select("html_content").eq("id", job_id).single().execute()
            if job.data and job.data.get("html_content"):
                html_content = job.data["html_content"]
            else:
                 raise ValueError("No HTML content found for EPUB generation")

        # Convert dict back to Pydantic model
        try:
            document_structure = DocumentStructure(**document_structure_dict)
        except ValidationError as e:
            logger.error(f"Invalid document structure: {e}")
            # Fallback
            document_structure = DocumentStructure(
                title="Converted Document",
                chapters=[],
                toc={"items": []}
            )

        # Initialize generator
        generator = EpubGenerator(job_id=job_id, user_id=user_id)

        # Generate EPUB
        epub_bytes, epub_metadata = generator.generate(
            document_structure=document_structure,
            html_content=html_content,
            pdf_bytes=pdf_bytes
        )

        # Upload EPUB to Supabase Storage
        supabase = get_supabase_client()
        storage_service = SupabaseStorageService(supabase)
        
        filename = f"{job_id}.epub"
        # We'll store output in 'downloads' bucket (or 'output'?)
        output_path = f"downloads/{user_id}/{job_id}/output.epub"
        
        logger.info(f"Uploading EPUB to storage: {output_path}")
        
        # Retry logic for upload
        for attempt in range(3):
            try:
                storage_service.upload_file(
                    bucket="downloads",
                    path=output_path,
                    file_data=epub_bytes,
                    content_type="application/epub+zip"
                )
                break
            except Exception as e:
                if attempt == 2:
                    raise
                import time
                time.sleep(1)
        
        # Generate signed download URL
        try:
            download_url = storage_service.generate_signed_url(
                bucket="downloads",
                path=output_path,
                expires_in=3600
            )
        except Exception:
            download_url = None

        # Update job status to COMPLETED
        supabase.table("conversion_jobs").update({
            "status": "COMPLETED",
            "progress": 100,
            "output_path": output_path,
            "completed_at": datetime.utcnow().isoformat(),
            "stage_metadata": {
                "current_stage": "COMPLETED",
                "progress_percent": 100,
                "output_path": output_path,
                "epub_metadata": epub_metadata,
                "download_url": download_url,
                "completed_at": datetime.utcnow().isoformat()
            }
        }).eq("id", job_id).execute()

        logger.info(f"EPUB generation completed for job {job_id}: {output_path}")

        return {
            **previous_result,
            "epub_storage_path": output_path,
            "epub_metadata": epub_metadata,
            "download_url": download_url
        }

    except TaskCancelled:
        raise
    except Exception as e:
        logger.error(f"EPUB generation failed for job {job_id}: {str(e)}", exc_info=True)
        # Update job to FAILED
        update_job_status(
            job_id=job_id,
            status="FAILED",
            progress=0,
            stage_metadata={
                "current_stage": "FAILED",
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat()
            },
            error_message=f"EPUB generation failed: {str(e)}"
        )
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
    Calculate quality metrics and confidence scores from AI analysis (Story 4.5).

    Aggregates AI confidence scores from layout and structure analysis to provide
    transparency about conversion fidelity. Validates against PRD targets (95%+ complex, 99%+ text).

    Args:
        previous_result: Output from generate_epub task containing:
            - job_id: str
            - page_analyses: List[Dict] from layout analysis
            - document_structure: Dict from structure analysis
            - epub_metadata: Dict with EPUB generation results

    Returns:
        dict: Contains job_id, epub_path, and quality_report
    """
    from app.services.conversion.quality_scorer import QualityScorer

    job_id = previous_result["job_id"]
    logger.info(f"[Task 5/5] Calculating quality score for job {job_id}")

    try:
        # Check cancellation
        check_cancellation(job_id)

        # Check if quality scoring is enabled
        if not settings.QUALITY_SCORING_ENABLED:
            logger.info(f"Quality scoring disabled, skipping for job {job_id}")
            quality_report = {
                "overall_confidence": None,
                "elements": {},
                "warnings": ["Quality scoring disabled"],
                "fidelity_targets": {}
            }
        else:
            # Extract data from previous pipeline stages
            page_analyses = previous_result.get("page_analyses", [])
            document_structure = previous_result.get("document_structure", {})

            if not page_analyses or not document_structure:
                logger.warning(
                    f"Missing analysis data for job {job_id}, "
                    f"pages={len(page_analyses)}, structure={bool(document_structure)}"
                )
                quality_report = {
                    "overall_confidence": None,
                    "elements": {},
                    "warnings": ["Insufficient data for quality scoring"],
                    "fidelity_targets": {}
                }
            else:
                # Build layout analysis structure expected by QualityScorer
                layout_analysis = {
                    "pages": page_analyses
                }

                # Initialize quality scorer
                scorer = QualityScorer()

                # Generate complete quality report
                quality_report_obj = scorer.generate_quality_report(
                    layout_analysis=layout_analysis,
                    document_structure=document_structure
                )

                # Convert to dict for storage
                quality_report = quality_report_obj.model_dump()

                # Log quality metrics
                logger.info(
                    f"Quality report generated for job {job_id}: "
                    f"confidence={quality_report['overall_confidence']:.1f}%, "
                    f"warnings={len(quality_report['warnings'])}, "
                    f"elements={list(quality_report['elements'].keys())}"
                )

        # Store quality report in database
        supabase = get_supabase_client()
        supabase.table("conversion_jobs").update({
            "quality_report": quality_report
        }).eq("id", job_id).execute()

        # Update job status to COMPLETED with quality info in message
        confidence_msg = ""
        if quality_report.get("overall_confidence") is not None:
            confidence_msg = f" (Quality: {quality_report['overall_confidence']:.0f}%)"

        update_job_status(
            job_id=job_id,
            status="COMPLETED",
            progress=100,
            stage_metadata={
                "current_stage": "COMPLETED",
                "progress_percent": 100,
                "quality_confidence": quality_report.get("overall_confidence"),
                "quality_warnings": len(quality_report.get("warnings", [])),
                "completed_at": datetime.utcnow().isoformat()
            }
        )

        # Cleanup temp files on success
        cleanup_temp_files(job_id)

        logger.info(f"Quality scoring completed for job {job_id}{confidence_msg}")
        return {**previous_result, "quality_report": quality_report}

    except TaskCancelled:
        raise
    except Exception as e:
        logger.error(f"Quality scoring failed for job {job_id}: {str(e)}", exc_info=True)

        # Graceful degradation - save degraded quality report
        try:
            degraded_report = {
                "overall_confidence": None,
                "elements": {},
                "warnings": [f"Quality scoring error: {str(e)}"],
                "fidelity_targets": {}
            }
            supabase = get_supabase_client()
            supabase.table("conversion_jobs").update({
                "quality_report": degraded_report
            }).eq("id", job_id).execute()
            logger.info(f"Saved degraded quality report for job {job_id}")
        except Exception as db_error:
            logger.error(f"Failed to save degraded quality report: {db_error}")

        # Continue pipeline even if quality scoring fails
        return {**previous_result, "quality_report": degraded_report if 'degraded_report' in locals() else {}}
