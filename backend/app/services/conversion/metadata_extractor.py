"""
Metadata Extractor Service

Extracts and processes PDF metadata for EPUB embedding.
Handles title, author, language detection, and cover image generation.

Story 4.4: EPUB Generation from AI-Analyzed Content (AC: #3)
"""

from typing import Dict, Any, Optional, Tuple
from io import BytesIO
from datetime import datetime
import fitz  # PyMuPDF
from PIL import Image

from app.core.config import settings


class MetadataExtractor:
    """
    Extracts metadata from PDF files for EPUB generation.

    Features:
    - PDF metadata extraction (title, author, subject, keywords)
    - Cover image generation from first page
    - Language detection from content
    - Dublin Core metadata formatting
    """

    def extract_pdf_metadata(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Extract metadata from PDF file.

        Args:
            pdf_bytes: Original PDF file bytes

        Returns:
            Dict with title, author, subject, keywords, creator, producer
        """
        try:
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            metadata = pdf_document.metadata or {}
            pdf_document.close()

            return {
                'title': metadata.get('title', '') or '',
                'author': metadata.get('author', '') or '',
                'subject': metadata.get('subject', '') or '',
                'keywords': metadata.get('keywords', '') or '',
                'creator': metadata.get('creator', '') or '',
                'producer': metadata.get('producer', '') or '',
            }
        except Exception as e:
            # If PDF metadata extraction fails, return empty dict
            return {
                'title': '',
                'author': '',
                'subject': '',
                'keywords': '',
                'creator': '',
                'producer': ''
            }

    def generate_cover_image(self, pdf_bytes: bytes) -> Optional[bytes]:
        """
        Generate cover image from first PDF page.

        Renders the first page as an image with configured dimensions.

        Args:
            pdf_bytes: Original PDF file bytes

        Returns:
            Cover image as PNG bytes, or None if generation fails
        """
        try:
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

            if pdf_document.page_count == 0:
                pdf_document.close()
                return None

            # Get first page
            first_page = pdf_document[0]

            # Calculate zoom to achieve target cover dimensions
            page_rect = first_page.rect
            zoom_x = settings.EPUB_COVER_WIDTH / page_rect.width
            zoom_y = settings.EPUB_COVER_HEIGHT / page_rect.height
            zoom = min(zoom_x, zoom_y)  # Maintain aspect ratio

            # Render page to pixmap
            mat = fitz.Matrix(zoom, zoom)
            pix = first_page.get_pixmap(matrix=mat)

            # Convert to PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(BytesIO(img_data))

            # Resize to exact cover dimensions (may crop)
            img = img.resize(
                (settings.EPUB_COVER_WIDTH, settings.EPUB_COVER_HEIGHT),
                Image.Resampling.LANCZOS
            )

            # Convert to bytes
            output = BytesIO()
            img.save(output, format='PNG', optimize=True)
            cover_bytes = output.getvalue()

            pdf_document.close()
            return cover_bytes

        except Exception as e:
            # Cover generation is optional - return None on failure
            return None

    def embed_metadata_in_epub(
        self,
        book,  # epub.EpubBook
        title: str,
        author: Optional[str] = None,
        language: str = 'en',
        publisher: str = "Transfer2Read",
        pdf_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Embed Dublin Core metadata in EPUB book.

        Args:
            book: epub.EpubBook instance
            title: Document title
            author: Author name (optional)
            language: Primary language code
            publisher: Publisher name
            pdf_metadata: Additional PDF metadata (keywords, subject, etc.)
        """
        # Set core metadata
        book.set_title(title or "Converted Document")

        # Add author (supports multiple authors)
        if author:
            # Split multiple authors by comma or semicolon
            authors = [a.strip() for a in author.replace(';', ',').split(',')]
            for auth in authors:
                if auth:
                    book.add_author(auth)
        else:
            book.add_author("Unknown")

        # Set language
        book.set_language(language)

        # Add publication date (conversion date)
        pub_date = datetime.utcnow().strftime("%Y-%m-%d")
        book.add_metadata('DC', 'date', pub_date)

        # Add publisher
        book.add_metadata('DC', 'publisher', publisher)

        # Add subject/keywords if available
        if pdf_metadata:
            if pdf_metadata.get('subject'):
                book.add_metadata('DC', 'subject', pdf_metadata['subject'])

            if pdf_metadata.get('keywords'):
                # Split keywords and add as separate entries
                keywords = [k.strip() for k in pdf_metadata['keywords'].split(',')]
                for keyword in keywords:
                    if keyword:
                        book.add_metadata('DC', 'subject', keyword)

        # Add generator metadata
        book.add_metadata(None, 'meta', '', {
            'name': 'generator',
            'content': 'Transfer2Read AI Conversion Engine v1.0'
        })

        # Add creation timestamp
        book.add_metadata(None, 'meta', '', {
            'property': 'dcterms:created',
            'content': datetime.utcnow().isoformat() + 'Z'
        })
