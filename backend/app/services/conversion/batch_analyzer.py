"""
Batch Analyzer Service

Processes multiple PDF pages concurrently using asyncio for performance optimization.
Manages job progress updates, provides caching, and optimizes token usage by routing
simple pages to cheaper models.
"""

import logging
import asyncio
import hashlib
from typing import List, Callable, Optional, Dict
from pathlib import Path
from app.services.ai.layout_analyzer import LayoutAnalyzer
from app.services.ai.claude import ClaudeProvider
from app.services.conversion.document_loader import load_and_render_pages, PageData
from app.schemas.layout_analysis import PageAnalysis, TextBlocks
from app.core.config import settings

logger = logging.getLogger(__name__)


class BatchAnalyzer:
    """
    Analyzes all pages of a PDF concurrently with configurable concurrency limit.

    Uses asyncio.Semaphore to control concurrent AI API calls and prevent
    rate limiting. Provides progress callbacks for job status updates.
    Includes caching for repeated page patterns and token optimization.
    """

    def __init__(
        self,
        concurrency: int = 4,
        batch_size: int = 5,
        max_image_size: int = 2048,
        timeout_per_page: int = 30,
        max_retries: int = 3,
        fallback_enabled: bool = True,
        cache_enabled: bool = True,
    ):
        """
        Initialize batch analyzer.

        Args:
            concurrency: Number of pages to analyze concurrently (asyncio semaphore limit)
            batch_size: Report progress every N pages
            max_image_size: Max pixel dimension for page images
            timeout_per_page: Timeout per page analysis in seconds
            max_retries: Max retry attempts before fallback
            fallback_enabled: Enable Claude fallback on GPT-4o failure
            cache_enabled: Enable caching for repeated page patterns

        Raises:
            ValueError: If any configuration parameter is invalid
        """
        # Validate configuration parameters
        if concurrency <= 0:
            raise ValueError(f"concurrency must be > 0, got {concurrency}")
        if batch_size <= 0:
            raise ValueError(f"batch_size must be > 0, got {batch_size}")
        if max_image_size <= 0:
            raise ValueError(f"max_image_size must be > 0, got {max_image_size}")
        if timeout_per_page <= 0:
            raise ValueError(f"timeout_per_page must be > 0, got {timeout_per_page}")
        if max_retries < 0:
            raise ValueError(f"max_retries must be >= 0, got {max_retries}")

        self.concurrency = concurrency
        self.batch_size = batch_size
        self.max_image_size = max_image_size
        self.cache_enabled = cache_enabled

        # In-memory cache for page analyses (content hash -> LayoutDetection)
        self._cache: Dict[str, PageAnalysis] = {}

        # Initialize layout analyzer
        self.analyzer = LayoutAnalyzer(
            timeout_per_page=timeout_per_page,
            max_retries=max_retries,
            fallback_enabled=fallback_enabled,
        )

        # Initialize simple page provider (Claude for cost optimization)
        self.simple_page_provider = ClaudeProvider(
            api_key=settings.ANTHROPIC_API_KEY,
            temperature=0.0,
            timeout=timeout_per_page,
        )

        logger.info(
            f"BatchAnalyzer initialized: concurrency={concurrency}, "
            f"batch_size={batch_size}, max_image_size={max_image_size}, "
            f"cache_enabled={cache_enabled}"
        )

    async def analyze_all_pages(
        self,
        job_id: str,
        pdf_path: str | Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[PageAnalysis]:
        """
        Analyze all pages of a PDF concurrently.

        Args:
            job_id: Conversion job ID for logging/tracking
            pdf_path: Path to PDF file
            progress_callback: Optional callback function(pages_completed, total_pages)
                               called after every batch_size pages

        Returns:
            List of PageAnalysis results (one per page, ordered by page number)

        Raises:
            ValueError: If PDF is invalid
            Exception: If analysis fails for critical pages
        """
        logger.info(f"Starting batch analysis for job {job_id}: {pdf_path}")

        # Load and render all pages
        pages: List[PageData] = load_and_render_pages(pdf_path, self.max_image_size)
        total_pages = len(pages)

        logger.info(f"Job {job_id}: Loaded {total_pages} pages, starting concurrent analysis...")

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.concurrency)

        # Track progress
        completed_count = [0]  # Use list to allow mutation in nested function

        async def analyze_with_limit(page_data: PageData) -> PageAnalysis:
            """Analyze single page with semaphore limit, caching, and token optimization"""
            async with semaphore:
                # Check cache first (if enabled)
                if self.cache_enabled:
                    cache_key = self._generate_cache_key(page_data)
                    if cache_key in self._cache:
                        logger.info(f"Job {job_id}: Page {page_data.page_num} - using cached result")
                        completed_count[0] += 1
                        if progress_callback and completed_count[0] % self.batch_size == 0:
                            progress_callback(completed_count[0], total_pages)
                        return self._cache[cache_key]

                # Detect if page is simple (text-only, no complex elements)
                is_simple = self._is_simple_page(page_data)

                if is_simple:
                    # Use cheaper model (Claude) for simple text-only pages
                    logger.info(f"Job {job_id}: Page {page_data.page_num} - using Claude for simple page")
                    result, token_usage = await self.simple_page_provider.analyze_page(
                        image_b64=page_data.image_b64,
                        text=page_data.text,
                        page_num=page_data.page_num,
                    )
                    # Add metadata
                    from backend.app.schemas.layout_analysis import AnalysisMetadata, TokenUsage
                    import time
                    result.analysis_metadata = AnalysisMetadata(
                        model_used=self.simple_page_provider.get_model_name(),
                        response_time_ms=0,  # Not tracked for simple pages
                        tokens_used=TokenUsage(**token_usage)
                    )
                else:
                    # Use full analyzer (GPT-4o with fallback)
                    result = await self.analyzer.analyze_page(
                        image_b64=page_data.image_b64,
                        text=page_data.text,
                        page_num=page_data.page_num,
                    )

                # Store in cache if enabled
                if self.cache_enabled:
                    self._cache[cache_key] = result

                # Update progress
                completed_count[0] += 1

                # Call progress callback every batch_size pages
                if progress_callback and completed_count[0] % self.batch_size == 0:
                    progress_callback(completed_count[0], total_pages)
                    logger.info(
                        f"Job {job_id}: Progress {completed_count[0]}/{total_pages} pages analyzed"
                    )

                return result

        # Analyze all pages concurrently
        try:
            results = await asyncio.gather(
                *[analyze_with_limit(page) for page in pages],
                return_exceptions=True,
            )

            # Check for exceptions
            successful_results: List[PageAnalysis] = []
            failed_pages: List[tuple[int, Exception]] = []

            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_pages.append((pages[idx].page_num, result))
                else:
                    successful_results.append(result)

            # Log failures
            if failed_pages:
                logger.error(
                    f"Job {job_id}: {len(failed_pages)} pages failed analysis: "
                    f"{[page_num for page_num, _ in failed_pages]}"
                )

                # Raise exception if too many failures
                failure_rate = len(failed_pages) / total_pages
                if failure_rate > 0.2:  # More than 20% failed
                    raise Exception(
                        f"Analysis failed for {len(failed_pages)}/{total_pages} pages "
                        f"({failure_rate:.1%} failure rate)"
                    )

            # Final progress callback
            if progress_callback:
                progress_callback(len(successful_results), total_pages)

            logger.info(
                f"Job {job_id}: Batch analysis complete. "
                f"Success: {len(successful_results)}/{total_pages} pages"
            )

            return successful_results

        except Exception as e:
            logger.error(f"Job {job_id}: Batch analysis failed: {e}")
            raise

    def _generate_cache_key(self, page_data: PageData) -> str:
        """
        Generate cache key based on page content hash.

        Args:
            page_data: Page data including text and image

        Returns:
            Hash string for cache lookup
        """
        # Create hash from text + truncated image (for performance)
        content = f"{page_data.text}:{page_data.image_b64[:100]}"
        return hashlib.md5(content.encode()).hexdigest()

    def _is_simple_page(self, page_data: PageData) -> bool:
        """
        Detect if page is simple (text-only, likely no complex elements).

        Simple pages are routed to cheaper Claude model for cost optimization.

        Args:
            page_data: Page data with text and image

        Returns:
            True if page appears to be simple text-only
        """
        # Heuristics for simple page detection:
        # 1. Text length > 500 characters (substantial text content)
        # 2. No obvious table markers (|, -, +, grid patterns)
        # 3. No obvious math symbols (∑, ∫, ∂, etc.)
        # 4. No image markers in text (Figure, Fig., Image, etc.)

        text = page_data.text.lower()

        # Must have substantial text
        if len(page_data.text) < 500:
            return False

        # Check for table indicators
        table_markers = ["|", "─", "┌", "└", "┐", "┘", "├", "┤"]
        if any(marker in page_data.text for marker in table_markers):
            return False

        # Check for math indicators
        math_markers = ["∑", "∫", "∂", "∆", "≈", "≠", "≤", "≥", "√", "π", "α", "β", "γ"]
        if any(marker in page_data.text for marker in math_markers):
            return False

        # Check for image/figure references
        image_keywords = ["figure", "fig.", "image", "diagram", "chart", "graph"]
        if any(keyword in text for keyword in image_keywords):
            return False

        # Passed all heuristics - likely a simple text page
        return True


def create_batch_analyzer(
    concurrency: Optional[int] = None,
    batch_size: Optional[int] = None,
    max_image_size: Optional[int] = None,
    timeout_per_page: Optional[int] = None,
    max_retries: Optional[int] = None,
    fallback_enabled: Optional[bool] = None,
    cache_enabled: Optional[bool] = None,
) -> BatchAnalyzer:
    """
    Factory function to create BatchAnalyzer with settings from config.

    Args:
        All parameters optional, defaults to config settings

    Returns:
        Configured BatchAnalyzer instance
    """
    return BatchAnalyzer(
        concurrency=concurrency or settings.ANALYSIS_CONCURRENCY,
        batch_size=batch_size or settings.ANALYSIS_PAGE_BATCH_SIZE,
        max_image_size=max_image_size or settings.MAX_IMAGE_SIZE,
        timeout_per_page=timeout_per_page or settings.ANALYSIS_TIMEOUT_PER_PAGE,
        max_retries=max_retries or settings.AI_ANALYSIS_MAX_RETRIES,
        fallback_enabled=fallback_enabled
        if fallback_enabled is not None
        else settings.AI_FALLBACK_ENABLED,
        cache_enabled=cache_enabled
        if cache_enabled is not None
        else settings.AI_CACHE_ENABLED,
    )
