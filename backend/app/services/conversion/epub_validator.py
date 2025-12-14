"""
EPUB Validator Service

Validates EPUB structure, file references, XHTML well-formedness, and file size constraints.

Story 4.4: EPUB Generation from AI-Analyzed Content (AC: #6)
"""

from typing import Dict, Any, List, Tuple, Optional
from io import BytesIO
import zipfile
from lxml import etree
import logging

from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)


class EpubValidator:
    """
    Validates EPUB files for structure, content, and size requirements.

    Features:
    - EPUB structure validation (mimetype, META-INF, OEBPS)
    - File reference validation (all referenced files exist)
    - XHTML well-formedness check
    - File size constraint (≤ 120% of PDF size)
    """

    def __init__(self):
        """Initialize EPUB validator."""
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_epub_structure(self, epub_bytes: bytes) -> Tuple[bool, List[str], List[str]]:
        """
        Validate EPUB structure and file references.

        Args:
            epub_bytes: Complete EPUB file as bytes

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        try:
            # Open EPUB as ZIP
            with zipfile.ZipFile(BytesIO(epub_bytes), 'r') as epub_zip:
                # Check mimetype file
                if 'mimetype' not in epub_zip.namelist():
                    self.errors.append("Missing 'mimetype' file")
                else:
                    mimetype_content = epub_zip.read('mimetype').decode('utf-8').strip()
                    if mimetype_content != 'application/epub+zip':
                        self.errors.append(f"Invalid mimetype: {mimetype_content}")

                # Check META-INF/container.xml
                if 'META-INF/container.xml' not in epub_zip.namelist():
                    self.errors.append("Missing 'META-INF/container.xml'")

                # Check for content.opf (package document)
                has_opf = any('content.opf' in name or '.opf' in name for name in epub_zip.namelist())
                if not has_opf:
                    self.errors.append("Missing content.opf (package document)")

                # Validate file references
                self._validate_file_references(epub_zip)

                # Validate XHTML files
                self._validate_xhtml_files(epub_zip)

        except zipfile.BadZipFile:
            self.errors.append("Invalid ZIP file structure")
        except Exception as e:
            self.errors.append(f"Validation error: {str(e)}")

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings

    def _validate_file_references(self, epub_zip: zipfile.ZipFile) -> None:
        """
        Check that all referenced files exist in the EPUB.

        Args:
            epub_zip: Open zipfile.ZipFile object
        """
        file_list = set(epub_zip.namelist())

        # Check common required files
        required_dirs = ['META-INF/', 'OEBPS/']
        for req_dir in required_dirs:
            has_dir = any(name.startswith(req_dir) for name in file_list)
            if not has_dir:
                self.warnings.append(f"Missing recommended directory: {req_dir}")

    def _validate_xhtml_files(self, epub_zip: zipfile.ZipFile) -> None:
        """
        Validate that all XHTML files are well-formed XML.

        Args:
            epub_zip: Open zipfile.ZipFile object
        """
        xhtml_files = [name for name in epub_zip.namelist() if name.endswith('.xhtml') or name.endswith('.html')]

        for xhtml_file in xhtml_files:
            try:
                content = epub_zip.read(xhtml_file)
                # Parse as XML to check well-formedness
                etree.fromstring(content)
            except etree.XMLSyntaxError as e:
                self.errors.append(f"Malformed XHTML in {xhtml_file}: {str(e)}")
            except Exception as e:
                self.warnings.append(f"Could not validate {xhtml_file}: {str(e)}")

    def validate_xhtml(self, xhtml_content: str, filename: str = "unknown") -> bool:
        """
        Validate a single XHTML string for well-formedness.

        Args:
            xhtml_content: XHTML content as string
            filename: File name for error reporting

        Returns:
            True if valid, False otherwise
        """
        try:
            etree.fromstring(xhtml_content.encode('utf-8'))
            return True
        except etree.XMLSyntaxError as e:
            self.errors.append(f"Malformed XHTML in {filename}: {str(e)}")
            return False

    def check_file_size(
        self,
        epub_size_bytes: int,
        pdf_size_bytes: int,
        max_ratio: float = 1.2
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if EPUB size is within acceptable limits (≤ 120% of PDF size).

        Args:
            epub_size_bytes: EPUB file size in bytes
            pdf_size_bytes: Original PDF file size in bytes
            max_ratio: Maximum allowed ratio (default: 1.2 = 120%)

        Returns:
            Tuple of (is_within_limit, message)
        """
        if pdf_size_bytes == 0:
            return True, None

        ratio = epub_size_bytes / pdf_size_bytes

        if ratio <= max_ratio:
            return True, f"EPUB size OK: {ratio*100:.1f}% of PDF size"
        else:
            return False, f"EPUB oversized: {ratio*100:.1f}% of PDF size (max: {max_ratio*100}%)"

    def compress_images_if_oversized(
        self,
        epub_bytes: bytes,
        pdf_size_bytes: int
    ) -> Tuple[bytes, bool]:
        """
        Compress images in EPUB if file size exceeds limits.

        Extracts images from EPUB, compresses them with reduced quality,
        and rebuilds the EPUB with compressed images.

        Args:
            epub_bytes: Original EPUB bytes
            pdf_size_bytes: PDF size for comparison

        Returns:
            Tuple of (compressed_epub_bytes, was_compressed)
        """
        # Check if compression needed
        is_ok, msg = self.check_file_size(len(epub_bytes), pdf_size_bytes)

        if is_ok:
            return epub_bytes, False

        logger.info(f"EPUB oversized ({msg}), attempting image compression...")

        try:
            # Open EPUB as ZIP
            input_zip = zipfile.ZipFile(BytesIO(epub_bytes), 'r')

            # Create new ZIP for output
            output_buffer = BytesIO()
            output_zip = zipfile.ZipFile(output_buffer, 'w', zipfile.ZIP_DEFLATED)

            compressed_count = 0
            total_saved_bytes = 0

            # Process each file in EPUB
            for file_info in input_zip.filelist:
                file_name = file_info.filename
                file_data = input_zip.read(file_name)

                # Check if this is an image file
                if self._is_compressible_image(file_name):
                    try:
                        # Compress image
                        compressed_data, saved_bytes = self._compress_image(
                            file_data,
                            settings.EPUB_IMAGE_QUALITY
                        )

                        if saved_bytes > 0:
                            # Use compressed version
                            output_zip.writestr(file_info, compressed_data)
                            compressed_count += 1
                            total_saved_bytes += saved_bytes
                            logger.debug(f"Compressed {file_name}: saved {saved_bytes} bytes")
                        else:
                            # Keep original if compression didn't help
                            output_zip.writestr(file_info, file_data)
                    except Exception as e:
                        # If compression fails, keep original
                        logger.warning(f"Failed to compress {file_name}: {e}")
                        output_zip.writestr(file_info, file_data)
                else:
                    # Copy non-image files as-is
                    output_zip.writestr(file_info, file_data)

            input_zip.close()
            output_zip.close()

            compressed_epub_bytes = output_buffer.getvalue()

            # Check if compression was successful
            original_size = len(epub_bytes)
            new_size = len(compressed_epub_bytes)
            reduction_pct = ((original_size - new_size) / original_size) * 100

            logger.info(
                f"Image compression complete: {compressed_count} images compressed, "
                f"saved {total_saved_bytes} bytes ({reduction_pct:.1f}% reduction)"
            )

            # Verify new size is within limits
            is_ok_now, new_msg = self.check_file_size(new_size, pdf_size_bytes)

            if is_ok_now:
                logger.info(f"EPUB now within size limits: {new_msg}")
                return compressed_epub_bytes, True
            else:
                logger.warning(
                    f"EPUB still oversized after compression: {new_msg}. "
                    f"Returning compressed version anyway."
                )
                self.warnings.append(new_msg or "EPUB size still exceeds recommended limit after compression")
                return compressed_epub_bytes, True

        except Exception as e:
            logger.error(f"Image compression failed: {e}")
            self.warnings.append(f"Image compression failed: {str(e)}")
            return epub_bytes, False

    def _is_compressible_image(self, filename: str) -> bool:
        """
        Check if file is a compressible image format.

        Args:
            filename: File path in EPUB

        Returns:
            True if file is PNG or JPEG
        """
        lower_name = filename.lower()
        return (
            lower_name.endswith('.png') or
            lower_name.endswith('.jpg') or
            lower_name.endswith('.jpeg')
        )

    def _compress_image(
        self,
        image_data: bytes,
        quality: int = 85
    ) -> Tuple[bytes, int]:
        """
        Compress an image with reduced quality.

        Args:
            image_data: Original image bytes
            quality: JPEG quality (1-100, default: 85)

        Returns:
            Tuple of (compressed_bytes, bytes_saved)
        """
        original_size = len(image_data)

        # Load image
        img = Image.open(BytesIO(image_data))

        # Convert RGBA to RGB if necessary (for JPEG compatibility)
        if img.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
            img = background
        elif img.mode not in ['RGB', 'L']:
            # Convert other modes to RGB
            img = img.convert('RGB')

        # Compress as JPEG
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        compressed_data = output.getvalue()

        compressed_size = len(compressed_data)
        bytes_saved = original_size - compressed_size

        return compressed_data, bytes_saved
