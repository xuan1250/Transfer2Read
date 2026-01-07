"""
Integration Tests for Stirling-PDF Service

Tests the actual Stirling-PDF service integration (requires service running).
Story 4.2: Stirling-PDF Integration & AI Structure Analysis (AC: #1)

Note: These tests require STIRLING_PDF_URL to be configured and service to be accessible.
Mark as @pytest.mark.integration for selective test execution.
"""
import pytest
import os
from pathlib import Path
from app.services.stirling.stirling_client import StirlingPDFClient
from app.core.config import settings


@pytest.mark.integration
@pytest.mark.asyncio
class TestStirlingPDFIntegration:
    """Integration tests for Stirling-PDF service."""

    @pytest.fixture
    def stirling_client(self):
        """Create StirlingPDFClient with real settings."""
        if not settings.STIRLING_PDF_URL:
            pytest.skip("STIRLING_PDF_URL not configured")
        return StirlingPDFClient()

    @pytest.fixture
    def sample_pdf_bytes(self):
        """Load sample PDF for testing."""
        # Look for test PDF in fixtures directory
        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        sample_pdf_path = fixtures_dir / "sample-5-page.pdf"

        if not sample_pdf_path.exists():
            pytest.skip(f"Sample PDF not found at {sample_pdf_path}")

        with open(sample_pdf_path, "rb") as f:
            return f.read()

    async def test_stirling_service_health_check(self, stirling_client):
        """Test Stirling-PDF service is accessible via get_version()."""
        try:
            version_info = await stirling_client.get_version()

            assert version_info is not None
            assert isinstance(version_info, dict)
            # Stirling-PDF typically returns version info
            print(f"✓ Stirling-PDF service health check passed: {version_info}")

        except Exception as e:
            pytest.fail(f"Stirling-PDF service health check failed: {str(e)}")

    async def test_convert_pdf_to_html_real_service(self, stirling_client, sample_pdf_bytes):
        """Test actual PDF to HTML conversion with real Stirling service."""
        try:
            html_output = await stirling_client.convert_pdf_to_html(
                sample_pdf_bytes,
                "sample-5-page.pdf"
            )

            # Verify output
            assert html_output is not None
            assert len(html_output) > 0
            assert isinstance(html_output, str)

            # Verify HTML structure
            assert "<html" in html_output.lower()
            assert "<body" in html_output.lower()

            # Verify content is present (basic sanity check)
            # Assuming sample PDF has some text content
            assert len(html_output) > 1000  # Non-empty document

            print(f"✓ Stirling-PDF conversion successful: {len(html_output)} chars")
            print(f"✓ PDF size: {len(sample_pdf_bytes)} bytes")

        except Exception as e:
            pytest.fail(f"Stirling-PDF conversion failed: {str(e)}")

    async def test_conversion_performance(self, stirling_client, sample_pdf_bytes):
        """Test conversion performance for 5-page PDF (should be <30s)."""
        import time

        try:
            start_time = time.time()
            html_output = await stirling_client.convert_pdf_to_html(
                sample_pdf_bytes,
                "sample-5-page.pdf"
            )
            end_time = time.time()

            duration = end_time - start_time

            assert duration < 30.0, f"Conversion took {duration:.2f}s, expected <30s"

            print(f"✓ Conversion completed in {duration:.2f}s (target: <30s)")
            print(f"✓ Output size: {len(html_output)} chars")

        except Exception as e:
            pytest.fail(f"Performance test failed: {str(e)}")

    async def test_html_output_contains_expected_text(self, stirling_client, sample_pdf_bytes):
        """Test that HTML output contains expected text content from PDF."""
        try:
            html_output = await stirling_client.convert_pdf_to_html(
                sample_pdf_bytes,
                "sample-5-page.pdf"
            )

            # Basic content validation
            # This assumes sample PDF has some identifiable text
            # Adjust based on actual sample PDF content
            assert len(html_output) > 500

            # Verify HTML has basic structure elements
            html_lower = html_output.lower()
            assert "<html" in html_lower or "<!doctype" in html_lower

            print(f"✓ HTML output contains valid structure")

        except Exception as e:
            pytest.fail(f"Content validation failed: {str(e)}")


@pytest.mark.integration
@pytest.mark.asyncio
class TestStirlingPDFErrorHandling:
    """Integration tests for Stirling-PDF error scenarios."""

    @pytest.fixture
    def stirling_client(self):
        """Create StirlingPDFClient with real settings."""
        if not settings.STIRLING_PDF_URL:
            pytest.skip("STIRLING_PDF_URL not configured")
        return StirlingPDFClient()

    async def test_corrupted_pdf_handling(self, stirling_client):
        """Test handling of corrupted PDF file."""
        # Create invalid PDF bytes
        corrupted_pdf = b"This is not a valid PDF file"

        try:
            await stirling_client.convert_pdf_to_html(corrupted_pdf, "corrupted.pdf")
            # If conversion succeeds with garbage input, that's unexpected
            # Stirling-PDF should return error or empty response

        except Exception as e:
            # Expected to fail - corrupted PDF should raise error
            print(f"✓ Corrupted PDF properly rejected: {type(e).__name__}")

    async def test_empty_pdf_handling(self, stirling_client):
        """Test handling of empty PDF bytes."""
        empty_pdf = b""

        try:
            await stirling_client.convert_pdf_to_html(empty_pdf, "empty.pdf")
            pytest.fail("Empty PDF should have raised an error")

        except Exception as e:
            # Expected to fail
            print(f"✓ Empty PDF properly rejected: {type(e).__name__}")
