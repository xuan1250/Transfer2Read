"""
PDF Document Loader

Extracts text and renders pages to images for AI vision analysis.
Uses PyMuPDF (fitz) for PDF processing.
"""

import logging
import base64
import io
from dataclasses import dataclass
from typing import List, BinaryIO
from pathlib import Path
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


@dataclass
class PageData:
    """Container for extracted PDF page data"""

    page_num: int  # 1-indexed page number
    text: str  # Extracted text layer
    image_b64: str  # Base64-encoded PNG image
    width: int  # Page width in pixels
    height: int  # Page height in pixels


def validate_pdf(pdf_path: str | Path) -> tuple[bool, str]:
    """
    Validate PDF file is readable and has pages.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Tuple of (is_valid, error_message)
        - (True, "") if valid
        - (False, "error message") if invalid
    """
    try:
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            return False, f"PDF file not found: {pdf_path}"

        if not pdf_path.is_file():
            return False, f"Path is not a file: {pdf_path}"

        # Try to open PDF
        with fitz.open(pdf_path) as doc:
            if doc.page_count == 0:
                return False, "PDF has no pages"

            # Check if encrypted
            if doc.is_encrypted:
                return False, "PDF is password-protected (not supported)"

        return True, ""

    except fitz.FileDataError as e:
        return False, f"Invalid PDF file: {e}"
    except Exception as e:
        return False, f"Error validating PDF: {e}"


def load_and_render_pages(
    pdf_path: str | Path, max_image_size: int = 2048
) -> List[PageData]:
    """
    Load PDF and extract text + rendered images for all pages.

    Args:
        pdf_path: Path to PDF file
        max_image_size: Maximum dimension (width or height) in pixels for rendered images

    Returns:
        List of PageData objects (one per page)

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If PDF is invalid or encrypted
        Exception: For other PDF processing errors
    """
    pdf_path = Path(pdf_path)

    # Validate PDF first
    is_valid, error_msg = validate_pdf(pdf_path)
    if not is_valid:
        raise ValueError(error_msg)

    logger.info(f"Loading PDF: {pdf_path}")

    pages: List[PageData] = []

    try:
        with fitz.open(pdf_path) as doc:
            page_count = doc.page_count
            logger.info(f"PDF has {page_count} pages")

            for page_num in range(1, page_count + 1):
                page = doc[page_num - 1]  # 0-indexed in fitz

                # Extract text layer
                text = page.get_text()

                # Calculate zoom to respect max_image_size
                zoom = _calculate_zoom(page, max_image_size)

                # Render page to image
                mat = fitz.Matrix(zoom, zoom)
                pixmap = page.get_pixmap(matrix=mat, alpha=False)

                # Convert to PNG bytes
                png_bytes = pixmap.tobytes("png")

                # Encode to base64
                image_b64 = base64.b64encode(png_bytes).decode("utf-8")

                # Create PageData
                page_data = PageData(
                    page_num=page_num,
                    text=text,
                    image_b64=image_b64,
                    width=pixmap.width,
                    height=pixmap.height,
                )

                pages.append(page_data)

                logger.debug(
                    f"Page {page_num}: {len(text)} chars, {pixmap.width}x{pixmap.height}px"
                )

    except Exception as e:
        logger.error(f"Error loading PDF {pdf_path}: {e}")
        raise

    logger.info(f"Successfully loaded {len(pages)} pages from PDF")
    return pages


def _calculate_zoom(page: fitz.Page, max_size: int) -> float:
    """
    Calculate zoom factor to fit page within max_size while preserving aspect ratio.

    Args:
        page: PyMuPDF page object
        max_size: Maximum dimension (width or height) in pixels

    Returns:
        Zoom factor (1.0 = original size)
    """
    rect = page.rect
    width = rect.width
    height = rect.height

    # Calculate current size at 72 DPI (default)
    current_max = max(width, height)

    if current_max <= max_size:
        # Already small enough, use default 2x zoom for clarity
        return 2.0

    # Scale down to fit max_size
    zoom = max_size / current_max
    return zoom
