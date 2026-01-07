import logging
import httpx
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class StirlingPDFClient:
    """
    Client for Stirling-PDF API integration.
    Handles communication with the Stirling-PDF service for PDF conversions.
    """

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize the Stirling-PDF client.

        Args:
            base_url: Base URL of the Stirling-PDF service (default: settings.STIRLING_PDF_URL)
            api_key: API Key for authentication (default: settings.STIRLING_PDF_API_KEY)
        """
        url = base_url or settings.STIRLING_PDF_URL

        if not url:
            raise ValueError("Stirling-PDF URL is not configured")

        self.base_url = url.rstrip('/')
        self.api_key = api_key or settings.STIRLING_PDF_API_KEY

    async def convert_pdf_to_html(self, pdf_bytes: bytes, filename: str = "document.pdf") -> str:
        """
        Convert PDF to HTML using Stirling-PDF API.
        
        Endpoint: POST /api/v1/convert/pdf/html

        Args:
            pdf_bytes: Raw PDF file bytes
            filename: Filename to send in the multipart upload

        Returns:
            str: The converted HTML content

        Raises:
            httpx.HTTPError: If the API request fails
            ValueError: If the response is empty
        """
        endpoint = f"{self.base_url}/api/v1/convert/pdf/html"
        headers = {
            "X-API-KEY": self.api_key
        }
        
        # Stirling-PDF expects multipart/form-data with 'fileInput' field
        files = {
            "fileInput": (filename, pdf_bytes, "application/pdf")
        }

        logger.info(f"Sending PDF ({len(pdf_bytes)} bytes) to Stirling-PDF at {endpoint}")

        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 min timeout for large PDFs
            response = await client.post(
                endpoint,
                headers=headers,
                files=files
            )
            
            if response.status_code != 200:
                logger.error(f"Stirling-PDF conversion failed: {response.status_code} - {response.text}")
                response.raise_for_status()
                
            html_content = response.text
            
            if not html_content:
                raise ValueError("Stirling-PDF returned empty response")
                
            logger.info(f"Stirling-PDF conversion successful, received {len(html_content)} chars")
            return html_content

    async def get_version(self) -> dict:
        """
        Get Stirling-PDF version info to check health.
        
        Endpoint: GET /api/v1/info
        """
        endpoint = f"{self.base_url}/api/v1/info"
        headers = {
            "X-API-KEY": self.api_key
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(endpoint, headers=headers)
            response.raise_for_status()
            return response.json()
