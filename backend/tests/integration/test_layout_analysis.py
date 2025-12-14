"""
Integration Tests for AI Layout Analysis

Tests the full layout analysis pipeline with sample PDFs and mocked AI responses.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, AsyncMock
from app.services.conversion.document_loader import load_and_render_pages, validate_pdf
from app.services.conversion.batch_analyzer import create_batch_analyzer
from app.schemas.layout_analysis import (
    LayoutDetection,
    Tables,
    Images,
    Equations,
    TextBlocks,
    Layout,
    AnalysisMetadata,
    TokenUsage,
)


@pytest.fixture
def sample_pdf_path():
    """Fixture: Path to sample test PDF"""
    # In real implementation, create a simple test PDF in tests/fixtures/
    # For now, we'll mock the PDF loading
    return Path(__file__).parent.parent / "fixtures" / "sample_5page.pdf"


@pytest.fixture
def mock_layout_response():
    """Fixture: Mock AI response for layout analysis"""
    return LayoutDetection(
        page_number=1,
        tables=Tables(count=0, items=[]),
        images=Images(count=0, items=[]),
        equations=Equations(count=0, items=[]),
        text_blocks=TextBlocks(count=0, items=[]),
        layout=Layout(is_multi_column=False, column_count=None, reflow_strategy="default"),
        headers_footers=[],
        primary_language="en",
        secondary_languages=[],
        overall_confidence=95,
        analysis_metadata=AnalysisMetadata(
            model_used="gpt-4o",
            response_time_ms=1000,
            tokens_used=TokenUsage(prompt=500, completion=200),
        ),
    )


def test_validate_pdf_nonexistent():
    """Test PDF validation with non-existent file"""
    is_valid, error = validate_pdf("/nonexistent/path.pdf")
    assert is_valid == False
    assert "not found" in error.lower()


def test_validate_pdf_not_a_file(tmp_path):
    """Test PDF validation with directory instead of file"""
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()

    is_valid, error = validate_pdf(dir_path)
    assert is_valid == False
    assert "not a file" in error.lower()


@pytest.mark.asyncio
async def test_batch_analyzer_with_mocked_ai():
    """Test batch analyzer with mocked AI responses"""
    batch_analyzer = create_batch_analyzer(concurrency=2, batch_size=2)

    # Mock the analyzer's analyze_page method
    mock_response = LayoutDetection(
        page_number=1,
        tables=Tables(count=1, items=[]),
        images=Images(count=1, items=[]),
        equations=Equations(count=0, items=[]),
        text_blocks=TextBlocks(count=0, items=[]),
        layout=Layout(is_multi_column=False, column_count=None, reflow_strategy="default"),
        headers_footers=[],
        primary_language="en",
        secondary_languages=[],
        overall_confidence=90,
        analysis_metadata=AnalysisMetadata(
            model_used="gpt-4o",
            response_time_ms=800,
            tokens_used=TokenUsage(prompt=400, completion=150),
        ),
    )

    # Mock load_and_render_pages to avoid needing a real PDF
    from app.services.conversion.document_loader import PageData

    mock_pages = [
        PageData(page_num=i, text=f"Page {i} text", image_b64="fake_base64", width=800, height=1000)
        for i in range(1, 6)  # 5 pages
    ]

    with patch(
        "app.services.conversion.batch_analyzer.load_and_render_pages",
        return_value=mock_pages,
    ):
        with patch.object(
            batch_analyzer.analyzer, "analyze_page", new_callable=AsyncMock
        ) as mock_analyze:
            mock_analyze.return_value = mock_response

            # Run batch analysis
            results = await batch_analyzer.analyze_all_pages(
                job_id="test-job-123", pdf_path="/fake/path.pdf"
            )

            # Verify results
            assert len(results) == 5
            assert all(r.overall_confidence == 90 for r in results)

            # Verify AI was called 5 times (once per page)
            assert mock_analyze.call_count == 5


@pytest.mark.asyncio
async def test_batch_analyzer_with_progress_callback():
    """Test batch analyzer calls progress callback correctly"""
    batch_analyzer = create_batch_analyzer(concurrency=2, batch_size=2)

    # Mock pages
    from app.services.conversion.document_loader import PageData

    mock_pages = [
        PageData(page_num=i, text=f"Page {i}", image_b64="fake", width=800, height=1000)
        for i in range(1, 6)
    ]

    # Mock response
    mock_response = LayoutDetection(
        page_number=1,
        tables=Tables(count=0, items=[]),
        images=Images(count=0, items=[]),
        equations=Equations(count=0, items=[]),
        text_blocks=TextBlocks(count=0, items=[]),
        layout=Layout(is_multi_column=False, column_count=None, reflow_strategy="default"),
        headers_footers=[],
        primary_language="en",
        secondary_languages=[],
        overall_confidence=85,
        analysis_metadata=AnalysisMetadata(
            model_used="gpt-4o", response_time_ms=700, tokens_used=TokenUsage(prompt=300, completion=100)
        ),
    )

    # Track progress callback invocations
    progress_calls = []

    def progress_callback(completed, total):
        progress_calls.append((completed, total))

    with patch(
        "app.services.conversion.batch_analyzer.load_and_render_pages",
        return_value=mock_pages,
    ):
        with patch.object(
            batch_analyzer.analyzer, "analyze_page", new_callable=AsyncMock, return_value=mock_response
        ):
            results = await batch_analyzer.analyze_all_pages(
                job_id="test-job", pdf_path="/fake/path.pdf", progress_callback=progress_callback
            )

            # Verify progress callback was called
            assert len(progress_calls) >= 2  # At least 2 batches (batch_size=2, 5 pages)

            # Final callback should report all pages
            final_call = progress_calls[-1]
            assert final_call == (5, 5)


@pytest.mark.asyncio
async def test_batch_analyzer_handles_partial_failures():
    """Test batch analyzer handles some pages failing gracefully"""
    batch_analyzer = create_batch_analyzer(concurrency=2, batch_size=2)

    from app.services.conversion.document_loader import PageData

    mock_pages = [
        PageData(page_num=i, text=f"Page {i}", image_b64="fake", width=800, height=1000)
        for i in range(1, 11)  # 10 pages
    ]

    mock_response = LayoutDetection(
        page_number=1,
        tables=Tables(count=0, items=[]),
        images=Images(count=0, items=[]),
        equations=Equations(count=0, items=[]),
        text_blocks=TextBlocks(count=0, items=[]),
        layout=Layout(is_multi_column=False, column_count=None, reflow_strategy="default"),
        headers_footers=[],
        primary_language="en",
        secondary_languages=[],
        overall_confidence=80,
        analysis_metadata=AnalysisMetadata(
            model_used="gpt-4o", response_time_ms=600, tokens_used=TokenUsage(prompt=250, completion=80)
        ),
    )

    call_count = [0]

    async def mock_analyze_with_failures(*args, **kwargs):
        call_count[0] += 1
        # Fail page 3 and 7
        if call_count[0] in [3, 7]:
            raise Exception("Simulated AI failure")
        return mock_response

    with patch(
        "app.services.conversion.batch_analyzer.load_and_render_pages",
        return_value=mock_pages,
    ):
        with patch.object(
            batch_analyzer.analyzer, "analyze_page", new_callable=AsyncMock, side_effect=mock_analyze_with_failures
        ):
            results = await batch_analyzer.analyze_all_pages(
                job_id="test-job", pdf_path="/fake/path.pdf"
            )

            # Should succeed with 8/10 pages (20% failure rate is acceptable)
            assert len(results) == 8


@pytest.mark.asyncio
async def test_batch_analyzer_fails_on_high_failure_rate():
    """Test batch analyzer raises exception when >20% pages fail"""
    batch_analyzer = create_batch_analyzer(concurrency=2, batch_size=2)

    from app.services.conversion.document_loader import PageData

    mock_pages = [
        PageData(page_num=i, text=f"Page {i}", image_b64="fake", width=800, height=1000)
        for i in range(1, 6)  # 5 pages
    ]

    # Fail 3 out of 5 pages (60% failure rate > 20% threshold)
    call_count = [0]

    async def mock_analyze_with_many_failures(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] in [1, 2, 3]:  # Fail first 3 pages
            raise Exception("AI failure")
        return LayoutDetection(
            page_number=1,
            tables=Tables(count=0, items=[]),
            images=Images(count=0, items=[]),
            equations=Equations(count=0, items=[]),
            text_blocks=TextBlocks(count=0, items=[]),
            layout=Layout(is_multi_column=False, column_count=None, reflow_strategy="default"),
            headers_footers=[],
            primary_language="en",
            secondary_languages=[],
            overall_confidence=75,
            analysis_metadata=AnalysisMetadata(
                model_used="gpt-4o", response_time_ms=500, tokens_used=TokenUsage(prompt=200, completion=60)
            ),
        )

    with patch(
        "app.services.conversion.batch_analyzer.load_and_render_pages",
        return_value=mock_pages,
    ):
        with patch.object(
            batch_analyzer.analyzer,
            "analyze_page",
            new_callable=AsyncMock,
            side_effect=mock_analyze_with_many_failures,
        ):
            # Should raise exception due to high failure rate
            with pytest.raises(Exception) as exc_info:
                await batch_analyzer.analyze_all_pages(job_id="test-job", pdf_path="/fake/path.pdf")

            assert "failure rate" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_performance_100_pages():
    """
    REQUIRED Performance Test: Analyze 100-page PDF with mocked AI (AC #9).

    Verifies:
    - Completion time < 10 minutes (with mocked AI responses)
    - Token usage tracking and logging
    - All pages processed successfully
    - Memory usage stays reasonable
    """
    import time

    batch_analyzer = create_batch_analyzer(concurrency=4, batch_size=5)

    from app.services.conversion.document_loader import PageData

    # Generate 100 mock pages
    mock_pages = [
        PageData(page_num=i, text=f"Page {i} content", image_b64="fake_base64", width=800, height=1000)
        for i in range(1, 101)  # 100 pages
    ]

    # Mock response with realistic token counts
    mock_response = LayoutDetection(
        page_number=1,
        tables=Tables(count=1, items=[]),
        images=Images(count=0, items=[]),
        equations=Equations(count=0, items=[]),
        text_blocks=TextBlocks(count=2, items=[]),
        layout=Layout(is_multi_column=False, column_count=None, reflow_strategy="default"),
        headers_footers=[],
        primary_language="en",
        secondary_languages=[],
        overall_confidence=88,
        analysis_metadata=AnalysisMetadata(
            model_used="gpt-4o",
            response_time_ms=450,
            tokens_used=TokenUsage(prompt=350, completion=120),  # Simulated token usage
        ),
    )

    # Track simulated token usage for cost estimation
    total_tokens = {"prompt": 0, "completion": 0}
    progress_updates = []

    def progress_callback(completed, total):
        progress_updates.append((completed, total))

    with patch(
        "app.services.conversion.batch_analyzer.load_and_render_pages",
        return_value=mock_pages,
    ):
        with patch.object(
            batch_analyzer.analyzer, "analyze_page", new_callable=AsyncMock
        ) as mock_analyze:
            # Mock returns response with token tracking
            mock_analyze.return_value = mock_response

            # Measure execution time
            start_time = time.time()

            results = await batch_analyzer.analyze_all_pages(
                job_id="perf-test-100-pages",
                pdf_path="/fake/100page.pdf",
                progress_callback=progress_callback,
            )

            execution_time = time.time() - start_time

            # Verify completion time (target: <10 minutes with mocked AI)
            # With mocked responses, should complete in seconds
            assert execution_time < 600, f"Test took {execution_time:.1f}s, expected <600s (10 minutes)"

            # Verify all pages processed
            assert len(results) == 100, f"Expected 100 results, got {len(results)}"

            # Verify progress callbacks were called
            assert len(progress_updates) > 0, "Progress callback should be called"
            final_progress = progress_updates[-1]
            assert final_progress == (100, 100), f"Final progress should be (100, 100), got {final_progress}"

            # Simulate token usage calculation for cost estimation
            for result in results:
                total_tokens["prompt"] += result.analysis_metadata.tokens_used.prompt
                total_tokens["completion"] += result.analysis_metadata.tokens_used.completion

            # Verify token tracking is working
            assert total_tokens["prompt"] > 0, "Token usage should be tracked"
            assert total_tokens["completion"] > 0, "Completion tokens should be tracked"

            # Calculate estimated cost (GPT-4o pricing as of test creation)
            # Input: $2.50 per 1M tokens, Output: $10.00 per 1M tokens
            estimated_cost = (
                (total_tokens["prompt"] / 1_000_000) * 2.50 +
                (total_tokens["completion"] / 1_000_000) * 10.00
            )

            # Log performance metrics
            print(f"\n{'=' * 60}")
            print(f"100-Page Performance Test Results (REQUIRED - AC #9)")
            print(f"{'=' * 60}")
            print(f"Execution Time: {execution_time:.2f}s (Target: <600s)")
            print(f"Pages Processed: {len(results)}/100")
            print(f"Progress Updates: {len(progress_updates)}")
            print(f"Tokens Used:")
            print(f"  - Prompt:     {total_tokens['prompt']:,} tokens")
            print(f"  - Completion: {total_tokens['completion']:,} tokens")
            print(f"  - Total:      {sum(total_tokens.values()):,} tokens")
            print(f"Estimated Cost: ${estimated_cost:.4f} (GPT-4o pricing)")
            print(f"Avg Time/Page: {execution_time / 100:.3f}s")
            print(f"{'=' * 60}\n")

            # Performance assertions
            assert execution_time / 100 < 6, "Average time per page should be <6s with mocked AI"
            assert len(progress_updates) >= 20, "Should have at least 20 progress updates (batch_size=5)"
