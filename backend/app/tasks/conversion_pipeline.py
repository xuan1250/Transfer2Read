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
from app.services.conversion.batch_analyzer import create_batch_analyzer
from app.services.storage.supabase_storage import SupabaseStorageService
from app.services.ai.structure_analyzer import StructureAnalyzer
from app.services.conversion import text_chunker
from app.services.conversion.heuristic_structure import HeuristicStructureDetector
from app.schemas.document_structure import DocumentStructure

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
            analyze_layout.s(job_id),
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
    Analyze PDF layout using AI (Story 4.2 Implementation).

    Uses GPT-4o (primary) and Claude 3.5 Haiku (fallback) to detect layout elements
    (tables, images, equations, multi-column layouts). Processes pages concurrently
    for performance.

    Args:
        job_id: Job UUID

    Returns:
        dict: Contains job_id, layout_analysis (full results), and page_analyses (list)
    """
    logger.info(f"[Task 1/5] Analyzing layout for job {job_id} with AI")

    try:
        # Check cancellation
        check_cancellation(job_id)

        # Update status to ANALYZING (25% progress)
        update_job_status(
            job_id=job_id,
            status="ANALYZING",
            progress=25,
            stage_metadata={
                "current_stage": "layout_analysis",
                "stage_description": "Analyzing layout...",
                "progress_percent": 25,
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

        # Create batch analyzer
        batch_analyzer = create_batch_analyzer()

        # Define progress callback
        def progress_callback(completed: int, total: int):
            """Update job progress after each batch"""
            progress_percent = 25 + int((completed / total) * 25)  # 25-50% range
            update_job_status(
                job_id=job_id,
                status="ANALYZING",
                progress=progress_percent,
                stage_metadata={
                    "current_stage": "ANALYZING",
                    "progress_percent": progress_percent,
                    "pages_analyzed": completed,
                    "total_pages": total,
                    "stage_started_at": job_data.get("stage_metadata", {}).get("stage_started_at", datetime.utcnow().isoformat())
                }
            )

        # Run async analysis in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            page_analyses = loop.run_until_complete(
                batch_analyzer.analyze_all_pages(
                    job_id=job_id,
                    pdf_path=temp_pdf_path,
                    progress_callback=progress_callback
                )
            )
        finally:
            loop.close()

        # Read PDF bytes into memory before cleanup (needed for EPUB generation)
        with open(temp_pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        # Cleanup temp file
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

        # Calculate aggregate metrics
        total_tables = sum(pa.tables.count for pa in page_analyses)
        total_images = sum(pa.images.count for pa in page_analyses)
        total_equations = sum(pa.equations.count for pa in page_analyses)
        avg_confidence = sum(pa.overall_confidence for pa in page_analyses) / len(page_analyses) if page_analyses else 0

        # Aggregate token usage and calculate cost
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_cost = 0.0

        for pa in page_analyses:
            if pa.analysis_metadata and pa.analysis_metadata.tokens_used:
                total_prompt_tokens += pa.analysis_metadata.tokens_used.prompt
                total_completion_tokens += pa.analysis_metadata.tokens_used.completion

        # Calculate cost using CostTrackerCallback's pricing
        from app.services.ai.cost_tracker import CostTrackerCallback

        # Determine predominant model for pricing
        models_used = [pa.analysis_metadata.model_used for pa in page_analyses if pa.analysis_metadata]
        predominant_model = max(set(models_used), key=models_used.count) if models_used else "gpt-4o"

        # Calculate cost
        tracker = CostTrackerCallback(model_name=predominant_model)
        total_cost = tracker._calculate_call_cost(total_prompt_tokens, total_completion_tokens)

        # Determine AI model used (check if any page used Claude)
        models_used_set = set(pa.analysis_metadata.model_used for pa in page_analyses)
        ai_model_used = "mixed" if len(models_used_set) > 1 else list(models_used_set)[0] if models_used_set else "unknown"

        # Prepare layout analysis summary
        layout_analysis = {
            "total_pages": len(page_analyses),
            "total_tables": total_tables,
            "total_images": total_images,
            "total_equations": total_equations,
            "average_confidence": round(avg_confidence, 2),
            "ai_model_used": ai_model_used,
            "token_usage": {
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "total_tokens": total_prompt_tokens + total_completion_tokens
            },
            "estimated_cost": total_cost,
            "completed_at": datetime.utcnow().isoformat()
        }

        # Store full analysis in database (requires migration 005 to be run)
        supabase.table("conversion_jobs").update({
            "layout_analysis": {
                "page_analyses": [pa.model_dump() for pa in page_analyses]
            },
            "ai_model_used": ai_model_used
        }).eq("id", job_id).execute()

        # Update status with elements detected for real-time progress
        update_job_status(
            job_id=job_id,
            status="ANALYZING",
            progress=50,
            stage_metadata={
                "current_stage": "layout_analysis",
                "stage_description": f"Detected {total_tables} tables, {total_images} images, {total_equations} equations...",
                "progress_percent": 50,
                "elements_detected": {
                    "tables": total_tables,
                    "images": total_images,
                    "equations": total_equations,
                    "chapters": 0  # Not yet detected, will be updated in identify_structure
                },
                "estimated_cost": total_cost,  # Include cost for real-time display
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info(
            f"Layout analysis completed for job {job_id}: "
            f"{len(page_analyses)} pages, {total_tables} tables, {total_images} images, "
            f"{total_equations} equations (avg confidence: {avg_confidence:.1f}%)"
        )

        return {
            "job_id": job_id,
            "user_id": user_id,
            "pdf_bytes": pdf_bytes,
            "layout_analysis": layout_analysis,
            "page_analyses": [pa.model_dump() for pa in page_analyses]
        }

    except TaskCancelled:
        raise
    except Exception as e:
        logger.error(f"Layout analysis failed for job {job_id}: {str(e)}", exc_info=True)
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
                "current_stage": "extraction",
                "stage_description": "Extracting content...",
                "progress_percent": 50,
                "timestamp": datetime.utcnow().isoformat()
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
    Identify document structure (TOC, chapters) using AI structure analysis.

    This task uses GPT-4o to detect chapter boundaries and build a table of contents.
    Implements Story 4.3: AI-Powered Structure Recognition & TOC Generation.

    Args:
        previous_result: Output from extract_content task containing:
            - job_id: Conversion job UUID
            - layout_analysis: Summary of layout analysis
            - page_analyses: Full PageAnalysis objects from Story 4.2

    Returns:
        dict: Contains job_id, layout_analysis, extracted_content, and document_structure
            - document_structure: Full DocumentStructure with TOC and chapters
            - toc: List of TOC entries for quick access
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
                "stage_description": "Generating EPUB structure...",
                "progress_percent": 75,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # Extract page analyses from previous result
        page_analyses = previous_result.get("page_analyses", [])

        if not page_analyses:
            logger.warning(f"No page analyses found for job {job_id}, skipping structure analysis")
            return {
                **previous_result,
                "document_structure": {
                    "title": "Unknown Document",
                    "author": None,
                    "language": "en",
                    "toc": {"items": [], "total_entries": 0, "max_depth": 0},
                    "chapters": [],
                    "confidence_score": 0
                }
            }

        # Extract full text from page analyses (text_blocks contain the text)
        full_text = ""
        primary_language = page_analyses[0].get("primary_language", "en") if page_analyses else "en"

        for page_analysis in page_analyses:
            text_blocks = page_analysis.get("text_blocks", {}).get("items", [])
            page_text = " ".join(block.get("text", "") for block in text_blocks)
            full_text += page_text + "\n\n"

        page_count = len(page_analyses)

        logger.info(
            f"Extracted text for structure analysis: {len(full_text)} chars, "
            f"{page_count} pages, language={primary_language}"
        )

        # Check if chunking is needed
        needs_chunking = text_chunker.detect_needs_chunking(
            page_count=page_count,
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
        analysis_method = "ai_full"

        # Scenario 1: Small document - analyze as single chunk
        if not needs_chunking:
            try:
                logger.info(f"Analyzing structure in single pass (no chunking needed)")

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    doc_struct, token_usage = loop.run_until_complete(
                        analyzer.analyze_structure(
                            text=full_text,
                            language=primary_language,
                            page_count=page_count,
                            document_title=None  # Let AI detect
                        )
                    )
                    document_structure = doc_struct.model_dump()
                    logger.info(
                        f"Structure analysis successful: {document_structure['toc']['total_entries']} entries, "
                        f"confidence={document_structure['confidence_score']}%, "
                        f"tokens={token_usage['prompt']}+{token_usage['completion']}"
                    )
                finally:
                    loop.close()

            except Exception as e:
                logger.warning(f"AI structure analysis failed: {e}, falling back to heuristics")
                analysis_method = "heuristic_fallback"

        # Scenario 2: Large document - chunk and merge
        else:
            try:
                logger.info(f"Large document detected - using chunking strategy")

                # Split into chunks
                chunks = text_chunker.split_text_into_chunks(
                    text=full_text,
                    page_count=page_count,
                    max_pages=settings.STRUCTURE_CHUNK_SIZE,
                    overlap_pages=settings.STRUCTURE_CHUNK_OVERLAP
                )

                logger.info(f"Split into {len(chunks)} chunks for analysis")

                # Analyze each chunk
                chunk_results = []
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    for i, chunk in enumerate(chunks):
                        logger.info(
                            f"Analyzing chunk {i+1}/{len(chunks)}: "
                            f"pages {chunk.start_page}-{chunk.end_page}"
                        )

                        doc_struct, token_usage = loop.run_until_complete(
                            analyzer.analyze_structure(
                                text=chunk.text,
                                language=primary_language,
                                page_count=chunk.end_page - chunk.start_page + 1,
                                document_title=None
                            )
                        )
                        chunk_results.append(doc_struct.model_dump())

                        # Update progress within chunking (75% + up to 5%)
                        chunk_progress = 75 + int((i + 1) / len(chunks) * 5)
                        update_job_status(
                            job_id=job_id,
                            status="STRUCTURING",
                            progress=chunk_progress,
                            stage_metadata={
                                "current_stage": "STRUCTURING",
                                "progress_percent": chunk_progress,
                                "chunks_analyzed": i + 1,
                                "total_chunks": len(chunks)
                            }
                        )
                finally:
                    loop.close()

                # Merge chunk results
                logger.info(f"Merging results from {len(chunks)} chunks")
                document_structure = text_chunker.merge_toc_results(chunk_results, chunks)
                analysis_method = "ai_chunked"

            except Exception as e:
                logger.warning(f"Chunked AI analysis failed: {e}, falling back to heuristics")
                analysis_method = "heuristic_fallback"

        # Scenario 3: Heuristic fallback (if AI failed or low confidence)
        if (
            document_structure is None or
            document_structure.get("confidence_score", 0) < settings.STRUCTURE_CONFIDENCE_THRESHOLD
        ):
            if document_structure:
                logger.warning(
                    f"AI confidence too low ({document_structure['confidence_score']}% < "
                    f"{settings.STRUCTURE_CONFIDENCE_THRESHOLD}%), using heuristic fallback"
                )

            logger.info(f"Running heuristic structure detection as fallback")
            detector = HeuristicStructureDetector(language=primary_language)

            # Pass layout hints from page analyses (font sizes)
            layout_hints = {
                "text_blocks": []
            }
            for i, page_analysis in enumerate(page_analyses):
                for block in page_analysis.get("text_blocks", {}).get("items", []):
                    layout_hints["text_blocks"].append({
                        "text": block.get("text", ""),
                        "font_size_hint": block.get("font_size_hint"),
                        "page_number": i + 1
                    })

            document_structure = detector.detect_structure(
                text=full_text,
                page_count=page_count,
                layout_hints=layout_hints
            )
            analysis_method = "heuristic_fallback"

        # Store document structure in database
        supabase = get_supabase_client()
        supabase.table("conversion_jobs").update({
            "document_structure": document_structure
        }).eq("id", job_id).execute()

        logger.info(
            f"Structure identification completed for job {job_id}: "
            f"{document_structure['toc']['total_entries']} TOC entries, "
            f"{len(document_structure['chapters'])} chapters, "
            f"confidence={document_structure['confidence_score']}%, "
            f"method={analysis_method}"
        )

        # Get elements detected from previous result (from layout analysis)
        layout_analysis = previous_result.get("layout_analysis", {})

        # Update progress to 80% (structure analysis complete) with all elements including chapters
        update_job_status(
            job_id=job_id,
            status="STRUCTURING",
            progress=80,
            stage_metadata={
                "current_stage": "structure",
                "stage_description": f"Detected {len(document_structure['chapters'])} chapters...",
                "progress_percent": 80,
                "elements_detected": {
                    "tables": layout_analysis.get("total_tables", 0),
                    "images": layout_analysis.get("total_images", 0),
                    "equations": layout_analysis.get("total_equations", 0),
                    "chapters": len(document_structure['chapters'])
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        return {
            **previous_result,
            "document_structure": document_structure,
            "toc": document_structure["toc"]["items"]  # Quick access to TOC
        }

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
    Generate EPUB file from structured content (Story 4.4).

    This task creates a valid EPUB 3 file using ebooklib, assembles content
    from AI analysis, and uploads to Supabase Storage.

    Args:
        previous_result: Output from identify_structure task containing:
            - job_id: str
            - document_structure: Dict from Story 4.3
            - layout_analysis: List[Dict] from Story 4.2
            - pdf_bytes: bytes (original PDF)

    Returns:
        dict: Contains job_id, output_path, and epub_metadata
    """
    from app.services.conversion.epub_generator import EpubGenerator
    from app.services.storage.supabase_storage import SupabaseStorageService
    from app.schemas.document_structure import DocumentStructure
    from app.schemas.layout_analysis import PageAnalysis
    from pydantic import ValidationError

    job_id = previous_result["job_id"]
    logger.info(f"[Task 4/5] Generating EPUB for job {job_id}")

    try:
        # Check cancellation
        check_cancellation(job_id)

        # Update status to GENERATING (85% progress)
        update_job_status(
            job_id=job_id,
            status="GENERATING",
            progress=85,
            stage_metadata={
                "current_stage": "epub_generation",
                "stage_description": "Generating EPUB file...",
                "progress_percent": 85,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # Extract data from previous result
        document_structure_dict = previous_result.get("document_structure")
        layout_analysis_list = previous_result.get("page_analyses", [])  # Get actual page analyses list
        pdf_bytes = previous_result.get("pdf_bytes")
        user_id = previous_result.get("user_id", "unknown")

        if not document_structure_dict:
            raise ValueError("Missing document_structure from previous task")

        if not pdf_bytes:
            raise ValueError("Missing pdf_bytes from previous task")

        # Parse document structure
        try:
            document_structure = DocumentStructure(**document_structure_dict)
        except ValidationError as e:
            logger.error(f"Invalid document structure: {e}")
            # Create minimal fallback structure
            document_structure = DocumentStructure(
                title=document_structure_dict.get("title", "Converted Document"),
                author=document_structure_dict.get("author"),
                language=document_structure_dict.get("language", "en"),
                toc=document_structure_dict.get("toc", {"entries": []}),
                chapters=document_structure_dict.get("chapters", []),
                confidence_score=50
            )

        # Parse layout analysis
        layout_analysis = []
        for page_dict in layout_analysis_list:
            try:
                layout_analysis.append(PageAnalysis(**page_dict))
            except (ValidationError, TypeError):
                # Skip invalid pages
                logger.warning(f"Skipping invalid page analysis: {page_dict}")

        # Create EPUB generator
        generator = EpubGenerator(job_id=job_id, user_id=user_id)

        # Generate EPUB
        logger.info(f"Generating EPUB with {len(layout_analysis)} pages")
        epub_bytes, epub_metadata = generator.generate(
            document_structure=document_structure,
            layout_analysis=layout_analysis,
            pdf_bytes=pdf_bytes
        )

        # Update progress to 95% (uploading)
        update_job_status(
            job_id=job_id,
            status="GENERATING",
            progress=95,
            stage_metadata={
                "current_stage": "epub_generation",
                "stage_description": "Uploading EPUB to storage...",
                "progress_percent": 95,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # Upload to Supabase Storage
        supabase = get_supabase_client()
        storage_service = SupabaseStorageService(supabase)
        output_path = f"downloads/{user_id}/{job_id}/output.epub"

        try:
            storage_service.upload_file(
                bucket="downloads",
                path=output_path,
                file_data=epub_bytes,
                content_type="application/epub+zip"
            )
            logger.info(f"EPUB uploaded to {output_path}")
        except Exception as upload_error:
            logger.error(f"Upload failed: {upload_error}")
            # Retry upload
            import time
            time.sleep(2)
            storage_service.upload_file(
                bucket="downloads",
                path=output_path,
                file_data=epub_bytes,
                content_type="application/epub+zip"
            )

        # Generate signed download URL (1 hour expiration)
        try:
            download_url = storage_service.generate_signed_url(
                bucket="downloads",
                path=output_path,
                expires_in=3600  # 1 hour
            )
        except Exception:
            download_url = None

        # Update job status to COMPLETED (100%) with output_path
        supabase.table("conversion_jobs").update({
            "status": "COMPLETED",
            "progress": 100,
            "output_path": output_path,  # Set output_path column directly
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

        logger.info(f"Updated job {job_id}: status=COMPLETED, progress=100, output_path={output_path}")

        # Invalidate Redis cache after successful update
        redis_client = get_redis_client()
        if redis_client:
            try:
                cache_key = f"job_status:{job_id}"
                redis_client.delete(cache_key)
                logger.info(f"Invalidated cache for job {job_id}")
            except Exception as e:
                logger.warning(f"Redis cache invalidation failed for job {job_id}: {str(e)}")

        logger.info(f"EPUB generation completed for job {job_id}: {output_path}")

        return {
            **previous_result,
            "job_id": job_id,
            "output_path": output_path,
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
