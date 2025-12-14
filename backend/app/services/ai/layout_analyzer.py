"""
Layout Analyzer Service

Orchestrates AI-powered PDF layout analysis with GPT-4o/Claude fallback.
Handles retry logic, fallback mechanisms, and error handling.
"""

import logging
import time
import asyncio
from typing import Optional
from app.services.ai.gpt4 import GPT4Provider
from app.services.ai.claude import ClaudeProvider
from app.schemas.layout_analysis import LayoutDetection, AnalysisMetadata, TokenUsage
from app.core.config import settings

logger = logging.getLogger(__name__)


class LayoutAnalyzer:
    """
    Main service for analyzing PDF page layouts using AI.

    Manages GPT-4o as primary model with automatic fallback to Claude 3.5 Haiku
    on failure. Implements retry logic with exponential backoff.
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        timeout_per_page: int = 30,
        max_retries: int = 3,
        fallback_enabled: bool = True,
    ):
        """
        Initialize layout analyzer with AI providers.

        Args:
            openai_api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY)
            anthropic_api_key: Anthropic API key (defaults to settings.ANTHROPIC_API_KEY)
            timeout_per_page: Timeout in seconds for each page analysis
            max_retries: Maximum retry attempts before fallback
            fallback_enabled: Whether to enable Claude fallback on GPT-4o failure
        """
        self.timeout_per_page = timeout_per_page
        self.max_retries = max_retries
        self.fallback_enabled = fallback_enabled

        # Initialize primary provider (GPT-4o)
        self.primary_provider = GPT4Provider(
            api_key=openai_api_key or settings.OPENAI_API_KEY,
            temperature=0.0,
            timeout=timeout_per_page,
        )

        # Initialize fallback provider (Claude) if enabled
        self.fallback_provider = None
        if fallback_enabled:
            self.fallback_provider = ClaudeProvider(
                api_key=anthropic_api_key or settings.ANTHROPIC_API_KEY,
                temperature=0.0,
                timeout=timeout_per_page,
            )

        logger.info(
            f"LayoutAnalyzer initialized: "
            f"primary=GPT-4o, fallback={'Claude 3.5 Haiku' if fallback_enabled else 'disabled'}, "
            f"timeout={timeout_per_page}s, max_retries={max_retries}"
        )

    async def analyze_page(
        self, image_b64: str, text: str, page_num: int
    ) -> LayoutDetection:
        """
        Analyze a single PDF page with retry and fallback logic.

        Attempts analysis with GPT-4o first. On failure, retries with exponential
        backoff. If all retries exhausted, falls back to Claude (if enabled).

        Args:
            image_b64: Base64-encoded page image
            text: Extracted text from page
            page_num: Page number (1-indexed)

        Returns:
            LayoutDetection: Structured layout analysis result

        Raises:
            Exception: If both primary and fallback providers fail
        """
        start_time = time.time()

        # Try primary provider (GPT-4o) with retries
        try:
            result, token_usage = await self._analyze_with_retries(
                provider=self.primary_provider,
                image_b64=image_b64,
                text=text,
                page_num=page_num,
            )

            # Add metadata with actual token usage
            result.analysis_metadata = self._create_metadata(
                model_name=self.primary_provider.get_model_name(),
                start_time=start_time,
                token_usage=token_usage,
            )

            return result

        except Exception as e:
            logger.warning(
                f"GPT-4o failed on page {page_num} after {self.max_retries} retries: {e}"
            )

            # Try fallback provider if enabled
            if self.fallback_enabled and self.fallback_provider:
                logger.info(f"Attempting fallback to Claude for page {page_num}...")

                try:
                    result, token_usage = await self._analyze_with_retries(
                        provider=self.fallback_provider,
                        image_b64=image_b64,
                        text=text,
                        page_num=page_num,
                    )

                    # Add metadata with actual token usage
                    result.analysis_metadata = self._create_metadata(
                        model_name=self.fallback_provider.get_model_name(),
                        start_time=start_time,
                        token_usage=token_usage,
                    )

                    logger.info(f"Page {page_num} analyzed successfully with Claude fallback")
                    return result

                except Exception as fallback_error:
                    logger.error(
                        f"Both GPT-4o and Claude failed on page {page_num}: {fallback_error}"
                    )
                    raise Exception(
                        f"All AI providers failed for page {page_num}: "
                        f"GPT-4o: {e}, Claude: {fallback_error}"
                    ) from fallback_error

            else:
                # No fallback available
                raise Exception(
                    f"GPT-4o failed on page {page_num} and fallback is disabled"
                ) from e

    async def _analyze_with_retries(
        self, provider, image_b64: str, text: str, page_num: int
    ) -> tuple[LayoutDetection, dict]:
        """
        Attempt analysis with exponential backoff retries.

        Args:
            provider: AI provider (GPT4Provider or ClaudeProvider)
            image_b64: Base64-encoded image
            text: Text layer
            page_num: Page number

        Returns:
            tuple: (LayoutDetection result, token_usage_dict)

        Raises:
            Exception: If all retries exhausted
        """
        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            try:
                result, token_usage = await provider.analyze_page(image_b64, text, page_num)
                return result, token_usage

            except TimeoutError as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = self._calculate_backoff(attempt)
                    logger.warning(
                        f"Timeout on page {page_num} (attempt {attempt}/{self.max_retries}), "
                        f"retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"Timeout on page {page_num} after {self.max_retries} attempts"
                    )

            except Exception as e:
                last_exception = e

                # Check if transient error (retry) or permanent (fail immediately)
                if self._is_permanent_error(e):
                    logger.error(f"Permanent error on page {page_num}: {e}")
                    raise

                if attempt < self.max_retries:
                    wait_time = self._calculate_backoff(attempt)
                    logger.warning(
                        f"Transient error on page {page_num} (attempt {attempt}/{self.max_retries}): {e}, "
                        f"retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"Failed on page {page_num} after {self.max_retries} attempts: {e}"
                    )

        # All retries exhausted
        raise last_exception

    def _calculate_backoff(self, attempt: int) -> int:
        """
        Calculate exponential backoff wait time.

        Args:
            attempt: Current attempt number (1-indexed)

        Returns:
            Wait time in seconds (60, 300, 900 for attempts 1, 2, 3)
        """
        # 1 min, 5 min, 15 min
        backoff_seconds = [60, 300, 900]
        return backoff_seconds[min(attempt - 1, len(backoff_seconds) - 1)]

    def _is_permanent_error(self, error: Exception) -> bool:
        """
        Determine if error is permanent (no retry) or transient (retry).

        Args:
            error: Exception from AI provider

        Returns:
            True if permanent error (invalid API key, model not found)
            False if transient error (timeout, rate limit, network)
        """
        error_str = str(error).lower()

        # Permanent errors
        permanent_keywords = [
            "invalid api key",
            "authentication failed",
            "model not found",
            "model_not_found",
            "invalid_api_key",
            "unauthorized",
        ]

        for keyword in permanent_keywords:
            if keyword in error_str:
                return True

        return False

    def _create_metadata(
        self, model_name: str, start_time: float, token_usage: dict
    ) -> AnalysisMetadata:
        """
        Create analysis metadata with actual token usage.

        Args:
            model_name: Name of AI model used
            start_time: Start timestamp (time.time())
            token_usage: Dictionary with 'prompt' and 'completion' token counts

        Returns:
            AnalysisMetadata object
        """
        response_time_ms = int((time.time() - start_time) * 1000)

        return AnalysisMetadata(
            model_used=model_name,
            response_time_ms=response_time_ms,
            tokens_used=TokenUsage(
                prompt=token_usage.get('prompt', 0),
                completion=token_usage.get('completion', 0)
            ),
        )
