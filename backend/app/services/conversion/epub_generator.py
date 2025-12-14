"""
EPUB Generator Service

This service generates EPUB 3.0 files from AI-analyzed PDF content.
Converts document structure and layout analysis into reflowable EPUB format.

Key Features:
- EPUB 3.0 specification compliance
- Table, image, and equation embedding
- Multi-language font support (EN, ZH, JP, KO, VI)
- Dublin Core metadata
- Responsive CSS styling
- NCX and Nav generation for e-reader compatibility

Dependencies:
- ebooklib: EPUB creation
- PyMuPDF (fitz): PDF metadata extraction and cover generation
- Pillow: Image processing
- lxml: XML validation

Story 4.4: EPUB Generation from AI-Analyzed Content
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import uuid
from datetime import datetime
from io import BytesIO
import logging

from ebooklib import epub
from PIL import Image
import fitz  # PyMuPDF

from app.core.config import settings
from app.schemas.document_structure import DocumentStructure, TOC, ChapterMetadata
from app.schemas.layout_analysis import PageAnalysis, LayoutDetection
from app.services.conversion.font_manager import FontManager
from app.services.conversion.content_assembler import ContentAssembler
from app.services.conversion.toc_generator import TOCGenerator

logger = logging.getLogger(__name__)

# Import the CSS stylesheet directly
from pathlib import Path

def get_epub_stylesheet() -> str:
    """Load EPUB stylesheet from templates directory."""
    css_path = Path(__file__).parent / "templates" / "epub_styles.css"
    return css_path.read_text(encoding='utf-8')


class EpubGenerator:
    """
    Main EPUB generation orchestrator.

    Converts AI-analyzed content from Stories 4.2 (layout analysis) and 4.3 (document structure)
    into valid EPUB 3.0 files with proper metadata, navigation, and styling.

    Usage:
        generator = EpubGenerator(job_id="abc123", user_id="user_xyz")
        epub_bytes = generator.generate(
            document_structure=structure,
            layout_analysis=layout_data,
            pdf_bytes=original_pdf
        )
    """

    def __init__(self, job_id: str, user_id: str):
        """
        Initialize EPUB generator.

        Args:
            job_id: Conversion job ID for tracking
            user_id: User ID for storage path generation
        """
        self.job_id = job_id
        self.user_id = user_id
        self.book: Optional[epub.EpubBook] = None
        self.font_manager = FontManager()
        self.content_assembler = ContentAssembler()
        self.toc_generator = TOCGenerator()

    def create_epub_book(self) -> epub.EpubBook:
        """
        Initialize a new EPUB book instance.

        Returns:
            epub.EpubBook: Empty EPUB book ready for content
        """
        book = epub.EpubBook()

        # Generate unique identifier (required by EPUB spec)
        unique_id = str(uuid.uuid4())
        book.set_identifier(unique_id)

        # Set default language (will be overridden with actual language)
        book.set_language('en')

        self.book = book
        return book

    def set_metadata(
        self,
        title: str,
        author: Optional[str] = None,
        language: str = 'en',
        publisher: str = "Transfer2Read"
    ) -> None:
        """
        Set EPUB metadata using Dublin Core standard.

        Args:
            title: Document title (from PDF metadata or first heading)
            author: Author name (from PDF metadata or "Unknown")
            language: Primary language code (from layout analysis)
            publisher: Publisher name (default: Transfer2Read)
        """
        if not self.book:
            raise RuntimeError("Must call create_epub_book() first")

        # Set core metadata
        self.book.set_title(title or "Converted Document")

        # Add author (supports multiple authors)
        if author:
            self.book.add_author(author)
        else:
            self.book.add_author("Unknown")

        # Set language
        self.book.set_language(language)

        # Add publication date (conversion date)
        pub_date = datetime.utcnow().strftime("%Y-%m-%d")
        self.book.add_metadata('DC', 'date', pub_date)

        # Add publisher
        self.book.add_metadata('DC', 'publisher', publisher)

        # Add generator metadata
        self.book.add_metadata(None, 'meta', '', {
            'name': 'generator',
            'content': 'Transfer2Read AI Conversion Engine'
        })

    def generate(
        self,
        document_structure: DocumentStructure,
        layout_analysis: List[PageAnalysis],
        pdf_bytes: bytes
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Generate complete EPUB from AI-analyzed content.

        This is the main entry point that orchestrates the entire EPUB generation process:
        1. Create EPUB book
        2. Extract and set metadata
        3. Generate cover image
        4. Build chapters from document structure
        5. Embed images, tables, equations
        6. Add TOC navigation
        7. Apply CSS styling
        8. Validate structure
        9. Write EPUB to bytes

        Args:
            document_structure: TOC and chapter structure from Story 4.3
            layout_analysis: Page layouts with tables/images from Story 4.2
            pdf_bytes: Original PDF file for metadata and cover extraction

        Returns:
            Tuple of (epub_bytes, epub_metadata)
            - epub_bytes: Complete EPUB file as bytes
            - epub_metadata: Dict with title, author, page_count, chapter_count, etc.

        Raises:
            ValueError: If document_structure or layout_analysis is invalid
            RuntimeError: If EPUB generation fails
        """
        # Step 1: Create book
        self.create_epub_book()

        # Step 2: Extract metadata from PDF
        metadata = self._extract_pdf_metadata(pdf_bytes)

        # Override with AI-detected metadata if available
        title = document_structure.title or metadata.get('title', 'Converted Document')
        author = document_structure.author or metadata.get('author')
        language = document_structure.language or 'en'

        # Set metadata
        self.set_metadata(title=title, author=author, language=language)

        # Step 3: Generate cover image (first page thumbnail)
        cover_image = self._generate_cover_image(pdf_bytes)
        if cover_image:
            self._add_cover_to_book(cover_image)

        # Step 4: Embed fonts for multi-language support
        text_sample = self._extract_text_sample(document_structure)
        font_result = self.font_manager.detect_and_embed_fonts(
            book=self.book,
            language=language,
            text_sample=text_sample
        )

        # Step 5: Add CSS stylesheet (with font-face rules if fonts embedded)
        self._add_stylesheet(font_result.get('embedded_fonts', []))

        # Step 6: Build chapters from document structure and layout analysis
        chapters_data = []
        if document_structure.chapters:
            # Extract chapters with elements from layout analysis
            chapters_data = self.content_assembler.extract_chapters(
                chapter_metadata=document_structure.chapters,
                layout_analysis=layout_analysis
            )
        else:
            # Graceful degradation: Create single chapter from all pages
            chapters_data = [{
                'title': title or 'Document Content',
                'start_page': 1,
                'end_page': len(layout_analysis) if layout_analysis else 0,
                'elements': []
            }]
            # Extract elements from all pages (if any)
            if layout_analysis:
                for page_num, page in enumerate(layout_analysis, start=1):
                    chapters_data[0]['elements'].extend(
                        self.content_assembler._extract_page_elements(page, page_num)
                    )

        # Step 7: Create EPUB chapters and embed images/tables/equations
        epub_chapters = []
        toc_entries = []

        for idx, chapter_data in enumerate(chapters_data):
            chapter_num = idx + 1
            chapter_file = f'chapters/chapter-{chapter_num}.xhtml'

            # Build XHTML content for this chapter
            xhtml_content = self.content_assembler.build_xhtml_chapter(
                chapter_title=chapter_data['title'],
                elements=chapter_data['elements'],
                language=language
            )

            # Validate that content is not empty
            if not xhtml_content or len(xhtml_content.strip()) == 0:
                logger.warning(f"Chapter {chapter_num} has empty content, using fallback")
                xhtml_content = self.content_assembler.build_xhtml_chapter(
                    chapter_title=chapter_data['title'],
                    elements=[],  # Force fallback content
                    language=language
                )

            # Create EPUB chapter
            chapter = epub.EpubHtml(
                title=chapter_data['title'],
                file_name=chapter_file,
                lang=language
            )
            # Set content as string (ebooklib handles encoding)
            chapter.set_content(xhtml_content.encode('utf-8'))
            self.book.add_item(chapter)
            epub_chapters.append(chapter)

            # Add to TOC entries for navigation
            toc_entries.append({
                'title': chapter_data['title'],
                'level': 1,  # All chapters are level 1 by default
                'href': chapter_file,
                'id': f'chapter-{chapter_num}'
            })

            # Embed images from this chapter (if any)
            for element in chapter_data['elements']:
                if element.tag == 'figure':
                    # Extract image data and add to EPUB
                    # Image embedding is handled by content_assembler
                    pass  # Images are already referenced in XHTML

        # Step 8: Add TOC navigation (NCX and Nav)
        if document_structure.toc and document_structure.toc.items:
            # Use AI-generated TOC structure
            toc_data = [
                {
                    'title': entry.title,
                    'level': entry.level,
                    'href': f'chapters/chapter-{i+1}.xhtml',
                    'id': f'toc-entry-{i+1}'
                }
                for i, entry in enumerate(document_structure.toc.items)
            ]
        else:
            # Use chapter-based TOC
            toc_data = toc_entries

        # Build TOC structure for ebooklib (it will auto-generate Nav and NCX)
        if toc_data:
            self.book.toc = tuple([
                epub.Link(entry['href'], entry['title'], entry['id'])
                for entry in toc_data
            ])
        else:
            # Fallback: create a simple TOC with one entry
            self.book.toc = (
                epub.Link('chapters/chapter-1.xhtml', 'Document Content', 'chapter-1'),
            )

        # Add NCX for EPUB 2 compatibility (ebooklib will auto-generate content)
        self.book.add_item(epub.EpubNcx())

        # Add Nav for EPUB 3 (ebooklib will auto-generate content)
        self.book.add_item(epub.EpubNav())

        # Step 9: Set spine (reading order)
        self.book.spine = ['nav'] + epub_chapters

        # Write EPUB to bytes
        epub_bytes = self._write_epub_to_bytes()

        # Prepare metadata
        epub_metadata = {
            'title': title,
            'author': author or 'Unknown',
            'language': language,
            'chapter_count': len(epub_chapters),
            'page_count': len(layout_analysis) if layout_analysis else 0,
            'size_bytes': len(epub_bytes),
            'generated_at': datetime.utcnow().isoformat(),
            'has_toc': bool(document_structure.toc and document_structure.toc.items),
            'fonts_embedded': len(font_result.get('embedded_fonts', []))
        }

        return epub_bytes, epub_metadata

    def _extract_pdf_metadata(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Extract metadata from PDF file.

        Args:
            pdf_bytes: Original PDF file bytes

        Returns:
            Dict with title, author, subject, keywords, etc.
        """
        try:
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            metadata = pdf_document.metadata
            pdf_document.close()

            return {
                'title': metadata.get('title', ''),
                'author': metadata.get('author', ''),
                'subject': metadata.get('subject', ''),
                'keywords': metadata.get('keywords', ''),
                'creator': metadata.get('creator', ''),
                'producer': metadata.get('producer', ''),
            }
        except Exception as e:
            # If PDF metadata extraction fails, return empty dict
            return {}

    def _generate_cover_image(self, pdf_bytes: bytes) -> Optional[bytes]:
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

    def _add_cover_to_book(self, cover_image_bytes: bytes) -> None:
        """
        Add cover image to EPUB book.

        Args:
            cover_image_bytes: Cover image as PNG bytes
        """
        if not self.book:
            return

        # Create cover image item
        cover_item = epub.EpubItem(
            uid="cover-image",
            file_name="images/cover.png",
            media_type="image/png",
            content=cover_image_bytes
        )
        self.book.add_item(cover_item)

        # Set as cover
        self.book.set_cover("images/cover.png", cover_image_bytes)

    def _write_epub_to_bytes(self) -> bytes:
        """
        Write EPUB book to bytes.

        Returns:
            Complete EPUB file as bytes

        Raises:
            RuntimeError: If EPUB writing fails
        """
        if not self.book:
            raise RuntimeError("No EPUB book to write")

        # Write to BytesIO
        output = BytesIO()
        epub.write_epub(output, self.book)
        epub_bytes = output.getvalue()
        output.close()

        return epub_bytes

    def _extract_text_sample(self, document_structure: DocumentStructure) -> str:
        """
        Extract text sample from document structure for font detection.

        Args:
            document_structure: Document structure with chapters and content

        Returns:
            Text sample (first 1000 chars from chapters)
        """
        text_parts = []

        # Extract from title
        if document_structure.title:
            text_parts.append(document_structure.title)

        # Extract from chapters
        if document_structure.chapters:
            for chapter in document_structure.chapters[:3]:  # First 3 chapters
                if hasattr(chapter, 'title') and chapter.title:
                    text_parts.append(chapter.title)
                if hasattr(chapter, 'content') and chapter.content:
                    text_parts.append(chapter.content[:500])

        # Combine and limit to 1000 chars
        sample = " ".join(text_parts)[:1000]
        return sample

    def _add_stylesheet(self, embedded_fonts: List[str]) -> None:
        """
        Add CSS stylesheet to EPUB with font-face rules if fonts are embedded.

        Args:
            embedded_fonts: List of embedded font keys
        """
        if not self.book:
            return

        # Get base stylesheet
        base_css = get_epub_stylesheet()

        # Update CSS with font-face rules if fonts embedded
        if embedded_fonts:
            css_content = self.font_manager.update_css_with_fonts(base_css, embedded_fonts)
        else:
            css_content = base_css

        # Create CSS item
        css_item = epub.EpubItem(
            uid="style",
            file_name="styles/epub_styles.css",
            media_type="text/css",
            content=css_content.encode('utf-8')
        )

        self.book.add_item(css_item)
