"""
Unit Tests for StirlingPDFClient

Tests the Stirling-PDF client with mocked httpx responses.
Story 4.2: Stirling-PDF Integration & AI Structure Analysis (AC: #1)
"""
import pytest
import httpx
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.stirling.stirling_client import StirlingPDFClient


class TestStirlingPDFClientInitialization:
    """Test StirlingPDFClient initialization."""

    def test_init_with_defaults(self):
        """Test initialization uses settings defaults."""
        with patch('app.services.stirling.stirling_client.settings') as mock_settings:
            mock_settings.STIRLING_PDF_URL = "http://stirling-pdf:8080"
            mock_settings.STIRLING_PDF_API_KEY = "test-key"

            client = StirlingPDFClient()

            assert client.base_url == "http://stirling-pdf:8080"
            assert client.api_key == "test-key"

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        client = StirlingPDFClient(
            base_url="http://custom:9000",
            api_key="custom-key"
        )

        assert client.base_url == "http://custom:9000"
        assert client.api_key == "custom-key"

    def test_init_strips_trailing_slash(self):
        """Test that trailing slashes are removed from base URL."""
        client = StirlingPDFClient(base_url="http://stirling-pdf:8080/")
        assert client.base_url == "http://stirling-pdf:8080"

    def test_init_without_url_raises_error(self):
        """Test initialization fails without URL."""
        with patch('app.services.stirling.stirling_client.settings') as mock_settings:
            mock_settings.STIRLING_PDF_URL = None
            mock_settings.STIRLING_PDF_API_KEY = None

            with pytest.raises(ValueError, match="Stirling-PDF URL is not configured"):
                StirlingPDFClient()


class TestConvertPdfToHtml:
    """Test convert_pdf_to_html method."""

    @pytest.mark.asyncio
    async def test_convert_pdf_to_html_success(self):
        """Test successful PDF to HTML conversion."""
        client = StirlingPDFClient(
            base_url="http://stirling-pdf:8080",
            api_key="test-key"
        )

        mock_html = "<html><body><h1>Test Document</h1><p>Sample content.</p></body></html>"
        pdf_bytes = b"%PDF-1.4 fake pdf content"

        # Mock httpx AsyncClient
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = mock_html
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.convert_pdf_to_html(pdf_bytes, "test.pdf")

            # Verify result
            assert result == mock_html
            assert len(result) > 0

            # Verify API call
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://stirling-pdf:8080/api/v1/convert/pdf/html"
            assert "X-API-KEY" in call_args[1]["headers"]
            assert call_args[1]["headers"]["X-API-KEY"] == "test-key"
            assert "files" in call_args[1]

    @pytest.mark.asyncio
    async def test_convert_pdf_to_html_with_custom_filename(self):
        """Test conversion with custom filename."""
        client = StirlingPDFClient(
            base_url="http://stirling-pdf:8080",
            api_key="test-key"
        )

        mock_html = "<html><body>Content</body></html>"
        pdf_bytes = b"%PDF-1.4 fake pdf"

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = mock_html
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.convert_pdf_to_html(pdf_bytes, "custom-name.pdf")

            # Verify filename was passed
            call_args = mock_client.post.call_args
            files = call_args[1]["files"]
            assert "fileInput" in files
            assert files["fileInput"][0] == "custom-name.pdf"

    @pytest.mark.asyncio
    async def test_convert_pdf_to_html_connection_failure_500(self):
        """Test conversion handles 500 server error."""
        client = StirlingPDFClient(
            base_url="http://stirling-pdf:8080",
            api_key="test-key"
        )

        pdf_bytes = b"%PDF-1.4 fake pdf"

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "500 Server Error",
                request=MagicMock(),
                response=mock_response
            )
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                await client.convert_pdf_to_html(pdf_bytes, "test.pdf")

    @pytest.mark.asyncio
    async def test_convert_pdf_to_html_timeout(self):
        """Test conversion handles timeout."""
        client = StirlingPDFClient(
            base_url="http://stirling-pdf:8080",
            api_key="test-key"
        )

        pdf_bytes = b"%PDF-1.4 fake pdf"

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.TimeoutException("Request timeout")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(httpx.TimeoutException):
                await client.convert_pdf_to_html(pdf_bytes, "test.pdf")

    @pytest.mark.asyncio
    async def test_convert_pdf_to_html_empty_response(self):
        """Test conversion handles empty response."""
        client = StirlingPDFClient(
            base_url="http://stirling-pdf:8080",
            api_key="test-key"
        )

        pdf_bytes = b"%PDF-1.4 fake pdf"

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = ""  # Empty response
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(ValueError, match="empty response"):
                await client.convert_pdf_to_html(pdf_bytes, "test.pdf")

    @pytest.mark.asyncio
    async def test_convert_pdf_to_html_network_error(self):
        """Test conversion handles network errors."""
        client = StirlingPDFClient(
            base_url="http://stirling-pdf:8080",
            api_key="test-key"
        )

        pdf_bytes = b"%PDF-1.4 fake pdf"

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.NetworkError("Connection refused")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(httpx.NetworkError):
                await client.convert_pdf_to_html(pdf_bytes, "test.pdf")

    @pytest.mark.asyncio
    async def test_convert_pdf_to_html_api_key_in_header(self):
        """Test that X-API-KEY header is sent correctly."""
        client = StirlingPDFClient(
            base_url="http://stirling-pdf:8080",
            api_key="super-secret-key"
        )

        mock_html = "<html><body>Content</body></html>"
        pdf_bytes = b"%PDF-1.4 fake pdf"

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = mock_html
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await client.convert_pdf_to_html(pdf_bytes, "test.pdf")

            # Verify X-API-KEY header was sent
            call_args = mock_client.post.call_args
            headers = call_args[1]["headers"]
            assert "X-API-KEY" in headers
            assert headers["X-API-KEY"] == "super-secret-key"

    @pytest.mark.asyncio
    async def test_convert_pdf_to_html_large_pdf(self):
        """Test conversion with large PDF bytes."""
        client = StirlingPDFClient(
            base_url="http://stirling-pdf:8080",
            api_key="test-key"
        )

        mock_html = "<html><body><h1>Large Document</h1>" + "<p>Content</p>" * 1000 + "</body></html>"
        # Simulate 5MB PDF
        pdf_bytes = b"%PDF-1.4 " + b"x" * (5 * 1024 * 1024)

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = mock_html
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.convert_pdf_to_html(pdf_bytes, "large.pdf")

            assert len(result) > 1000
            assert "Large Document" in result


class TestGetVersion:
    """Test get_version method."""

    @pytest.mark.asyncio
    async def test_get_version_success(self):
        """Test successful version info retrieval."""
        client = StirlingPDFClient(
            base_url="http://stirling-pdf:8080",
            api_key="test-key"
        )

        mock_version = {"version": "0.20.0", "name": "Stirling-PDF"}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = mock_version
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.get_version()

            assert result == mock_version
            assert "version" in result

            # Verify API call
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[0][0] == "http://stirling-pdf:8080/api/v1/info"

    @pytest.mark.asyncio
    async def test_get_version_with_api_key(self):
        """Test version info includes API key in header."""
        client = StirlingPDFClient(
            base_url="http://stirling-pdf:8080",
            api_key="version-test-key"
        )

        mock_version = {"version": "0.20.0"}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = mock_version
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await client.get_version()

            # Verify X-API-KEY header was sent
            call_args = mock_client.get.call_args
            headers = call_args[1]["headers"]
            assert "X-API-KEY" in headers
            assert headers["X-API-KEY"] == "version-test-key"

    @pytest.mark.asyncio
    async def test_get_version_failure(self):
        """Test version info handles server errors."""
        client = StirlingPDFClient(
            base_url="http://stirling-pdf:8080",
            api_key="test-key"
        )

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "503 Service Unavailable",
                request=MagicMock(),
                response=mock_response
            )
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                await client.get_version()

    @pytest.mark.asyncio
    async def test_get_version_timeout(self):
        """Test version info handles timeout (10s timeout configured)."""
        client = StirlingPDFClient(
            base_url="http://stirling-pdf:8080",
            api_key="test-key"
        )

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("Request timeout after 10s")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(httpx.TimeoutException):
                await client.get_version()
