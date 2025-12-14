"""
Unit Tests for Layout Analyzer

Tests AI layout analysis with mocked GPT-4o/Claude responses.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.services.ai.layout_analyzer import LayoutAnalyzer
from backend.app.schemas.layout_analysis import (
    LayoutDetection,
    Tables,
    Images,
    Equations,
    Layout,
    AnalysisMetadata,
    TokenUsage,
    TableItem,
    ImageItem,
    EquationItem,
)


@pytest.fixture
def mock_layout_detection():
    """Fixture: Mock LayoutDetection response"""
    return LayoutDetection(
        page_number=1,
        tables=Tables(
            count=2,
            items=[
                TableItem(
                    bbox=[50, 100, 500, 300],
                    rows=5,
                    cols=4,
                    confidence=95,
                    header_detected=True,
                    content_sample="Financial Summary 2024",
                ),
                TableItem(
                    bbox=[50, 350, 500, 550],
                    rows=10,
                    cols=3,
                    confidence=92,
                    header_detected=False,
                    content_sample="Q1 Revenue Data",
                ),
            ],
        ),
        images=Images(
            count=1,
            items=[
                ImageItem(
                    bbox=[50, 600, 500, 800], format="diagram", alt_text="System architecture diagram"
                )
            ],
        ),
        equations=Equations(
            count=3,
            items=[
                EquationItem(latex="E = mc^2", confidence=98, position="inline"),
                EquationItem(
                    latex="\\frac{\\partial f}{\\partial x} = 2x + 1", confidence=87, position="block"
                ),
                EquationItem(latex="\\sum_{i=1}^{n} x_i", confidence=90, position="inline"),
            ],
        ),
        layout=Layout(is_multi_column=False, column_count=None, reflow_strategy="preserve_tables"),
        headers_footers=[],
        primary_language="en",
        secondary_languages=[],
        overall_confidence=92,
        analysis_metadata=AnalysisMetadata(
            model_used="gpt-4o", response_time_ms=1250, tokens_used=TokenUsage(prompt=850, completion=320)
        ),
    )


@pytest.fixture
def analyzer():
    """Fixture: LayoutAnalyzer instance with test API keys"""
    return LayoutAnalyzer(
        openai_api_key="sk-test-openai-key",
        anthropic_api_key="sk-ant-test-anthropic-key",
        timeout_per_page=30,
        max_retries=3,
        fallback_enabled=True,
    )


@pytest.mark.asyncio
async def test_analyze_page_success(analyzer, mock_layout_detection):
    """Test successful page analysis with GPT-4o"""
    # Mock GPT-4o provider
    with patch.object(
        analyzer.primary_provider, "analyze_page", new_callable=AsyncMock
    ) as mock_analyze:
        mock_analyze.return_value = mock_layout_detection

        result = await analyzer.analyze_page(
            image_b64="fake_base64_image", text="Sample text", page_num=1
        )

        # Verify result
        assert result.page_number == 1
        assert result.tables.count == 2
        assert result.images.count == 1
        assert result.equations.count == 3
        assert result.overall_confidence == 92

        # Verify GPT-4o was called once
        mock_analyze.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_page_fallback_to_claude(analyzer, mock_layout_detection):
    """Test fallback to Claude when GPT-4o fails"""
    # Mock GPT-4o to fail
    with patch.object(
        analyzer.primary_provider, "analyze_page", new_callable=AsyncMock
    ) as mock_gpt:
        mock_gpt.side_effect = Exception("GPT-4o API error")

        # Mock Claude to succeed
        with patch.object(
            analyzer.fallback_provider, "analyze_page", new_callable=AsyncMock
        ) as mock_claude:
            mock_claude.return_value = mock_layout_detection

            result = await analyzer.analyze_page(
                image_b64="fake_base64_image", text="Sample text", page_num=1
            )

            # Verify result came from Claude
            assert result.page_number == 1
            assert result.tables.count == 2

            # Verify GPT-4o was retried max_retries times
            assert mock_gpt.call_count == 3  # max_retries

            # Verify Claude was called once
            mock_claude.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_page_both_providers_fail(analyzer):
    """Test exception when both GPT-4o and Claude fail"""
    # Mock both providers to fail
    with patch.object(
        analyzer.primary_provider, "analyze_page", new_callable=AsyncMock
    ) as mock_gpt:
        mock_gpt.side_effect = Exception("GPT-4o error")

        with patch.object(
            analyzer.fallback_provider, "analyze_page", new_callable=AsyncMock
        ) as mock_claude:
            mock_claude.side_effect = Exception("Claude error")

            # Should raise exception
            with pytest.raises(Exception) as exc_info:
                await analyzer.analyze_page(
                    image_b64="fake_base64_image", text="Sample text", page_num=1
                )

            assert "All AI providers failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_permanent_error_no_retry(analyzer):
    """Test that permanent errors (invalid API key) fail immediately without retry"""
    # Mock GPT-4o with permanent error
    with patch.object(
        analyzer.primary_provider, "analyze_page", new_callable=AsyncMock
    ) as mock_analyze:
        mock_analyze.side_effect = Exception("Invalid API key")

        with pytest.raises(Exception):
            await analyzer.analyze_page(
                image_b64="fake_base64_image", text="Sample text", page_num=1
            )

        # Should only be called once (no retries for permanent errors)
        assert mock_analyze.call_count == 1


def test_calculate_backoff(analyzer):
    """Test exponential backoff calculation"""
    assert analyzer._calculate_backoff(1) == 60  # 1 min
    assert analyzer._calculate_backoff(2) == 300  # 5 min
    assert analyzer._calculate_backoff(3) == 900  # 15 min


def test_is_permanent_error(analyzer):
    """Test permanent error detection"""
    assert analyzer._is_permanent_error(Exception("Invalid API key")) == True
    assert analyzer._is_permanent_error(Exception("Authentication failed")) == True
    assert analyzer._is_permanent_error(Exception("model_not_found")) == True
    assert analyzer._is_permanent_error(Exception("Timeout error")) == False
    assert analyzer._is_permanent_error(Exception("Rate limit exceeded")) == False
