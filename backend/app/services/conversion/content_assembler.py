"""
Content Assembler Service

Converts AI-detected layout elements (tables, images, equations) into EPUB XHTML format.
Handles content transformation from layout analysis to reflowable EPUB structure.

Key Features:
- Table conversion to HTML <table> with responsive CSS
- Image embedding with proper positioning and captions
- Equation handling (MathML with PNG fallback)
- Multi-column content reflow to single-column
- Semantic HTML5 tags (section, article, aside)

Story 4.4: EPUB Generation from AI-Analyzed Content (AC: #2)
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import base64
from io import BytesIO
from bs4 import BeautifulSoup
import re

from app.schemas.layout_analysis import (
    PageAnalysis,
    TableItem,
    ImageItem,
    EquationItem,
    TextBlock
)
from app.schemas.document_structure import ChapterMetadata


@dataclass
class XHTMLElement:
    """Represents an XHTML element with content and metadata."""
    tag: str  # HTML tag (table, img, p, etc.)
    content: str  # HTML content
    attributes: Dict[str, str]  # HTML attributes (class, id, etc.)
    bbox: Optional[List[float]] = None  # Bounding box for positioning


class ContentAssembler:
    """
    Assembles EPUB XHTML content from AI-analyzed layout elements.

    Converts detected elements (tables, images, equations, text) from layout analysis
    into properly formatted XHTML suitable for EPUB embedding.
    """

    def __init__(self):
        """Initialize content assembler."""
        self.image_counter = 0
        self.table_counter = 0
        self.equation_counter = 0

    def extract_chapters(
        self,
        chapter_metadata: List[ChapterMetadata],
        layout_analysis: List[PageAnalysis]
    ) -> List[Dict[str, Any]]:
        """
        Extract chapter data from document structure (Legacy/Vision approach).

        Args:
            chapter_metadata: List of chapters from Story 4.3
            layout_analysis: Page-by-page layout data from Story 4.2

        Returns:
            List of dicts with chapter info: {title, pages, elements}
        """
        chapters = []

        for chapter in chapter_metadata:
            chapter_data = {
                'title': chapter.title,
                'level': 1,  # Chapters are always level 1 (top-level)
                'start_page': chapter.start_page,
                'end_page': chapter.end_page if chapter.end_page else len(layout_analysis),
                'elements': []
            }

            # Extract layout elements for pages in this chapter
            for page_num in range(chapter.start_page, chapter_data['end_page'] + 1):
                if page_num <= len(layout_analysis):
                    page = layout_analysis[page_num - 1]  # 0-indexed
                    chapter_data['elements'].extend(
                        self._extract_page_elements(page, page_num)
                    )

            chapters.append(chapter_data)

        return chapters

    def extract_chapters_from_html(
        self,
        chapter_metadata: List[ChapterMetadata],
        html_content: str
    ) -> List[Dict[str, Any]]:
        """
        Extract chapter data from HTML content (Stirling-PDF approach).
        
        Splits the full HTML into chapters based on page markers (if present)
        and document structure.
        
        Args:
            chapter_metadata: List of chapters from structure analysis
            html_content: Full HTML string from Stirling-PDF
            
        Returns:
            List of dicts with chapter info: {title, elements}
            (Note: elements will be raw HTML strings wrapped in XHTMLElement)
        """
        chapters = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Try to find page containers
        # Strategy: Look for common Stirling/pdf2htmlEX classes or IDs
        # Common patterns: class="page", id="page-container-X", data-page-no="X"
        page_elements = []
        
        # Heuristic 1: class="page" or "pf" (pdf2htmlEX)
        candidates = soup.find_all('div', class_=re.compile(r'\b(page|pf)\b'))
        if not candidates:
            # Heuristic 2: direct children of body if they look like pages
            candidates = [child for child in soup.body.find_all('div', recursive=False)]
        
        if candidates and len(candidates) > 1:
            page_elements = candidates
        else:
            # Fallback: Treat body content as one page/blob
            page_elements = [soup.body]
            
        total_pages = len(page_elements)
        
        if not chapter_metadata:
             # Create single chapter if no structure
            return [{
                'title': 'Document Content',
                'elements': [XHTMLElement(
                    tag='div',
                    content=str(soup.body) if soup.body else html_content,
                    attributes={'class': 'chapter-content'}
                )]
            }]

        for chapter in chapter_metadata:
            chapter_data = {
                'title': chapter.title,
                'level': 1,
                'elements': []
            }
            
            # Identify page range
            start = chapter.start_page
            end = chapter.end_page if chapter.end_page else total_pages
            
            # Collect HTML for these pages
            chapter_html = []
            
            # Handle 1-based indexing
            # If we found pages, map them. If we have 1 big blob, just put it in first chapter.
            if len(page_elements) > 1:
                for i in range(start, end + 1):
                    if 1 <= i <= len(page_elements):
                        # Get the page element (0-indexed)
                        page_elem = page_elements[i-1]
                        chapter_html.append(str(page_elem))
            else:
                # Single blob case: Only valid for first chapter or full doc
                if chapter.chapter_num == 1:
                    chapter_html.append(str(soup.body) if soup.body else html_content)

            # Create a wrapper element for this chapter's content
            if chapter_html:
                full_chapter_html = "\n<hr class='page-break'/>\n".join(chapter_html)
                chapter_data['elements'].append(XHTMLElement(
                    tag='div',
                    content=full_chapter_html,
                    attributes={'class': 'chapter-content'}
                ))
            
            chapters.append(chapter_data)
            
        return chapters

    def _extract_page_elements(
        self,
        page_analysis: PageAnalysis,
        page_number: int
    ) -> List[XHTMLElement]:
        """
        Extract all elements from a single page.

        Args:
            page_analysis: Layout analysis for one page
            page_number: Page number for reference

        Returns:
            List of XHTML elements in reading order
        """
        elements = []

        # Extract tables
        if page_analysis.tables and page_analysis.tables.items:
            for table in page_analysis.tables.items:
                elements.append(self._convert_table_to_element(table, page_number))

        # Extract images
        if page_analysis.images and page_analysis.images.items:
            for image in page_analysis.images.items:
                elements.append(self._convert_image_to_element(image, page_number))

        # Extract equations
        if page_analysis.equations and page_analysis.equations.items:
            for equation in page_analysis.equations.items:
                elements.append(self._convert_equation_to_element(equation, page_number))

        # Extract text blocks
        if page_analysis.text_blocks and page_analysis.text_blocks.items:
            for text_block in page_analysis.text_blocks.items:
                elements.append(self._convert_text_to_element(text_block))

        # Sort by vertical position (top to bottom reading order)
        elements.sort(key=lambda e: e.bbox[1] if e.bbox else 0)

        return elements

    def _convert_table_to_element(
        self,
        table: TableItem,
        page_number: int
    ) -> XHTMLElement:
        """
        Convert table data to XHTML element.

        Args:
            table: Table item from layout analysis
            page_number: Page number for reference

        Returns:
            XHTMLElement with HTML table structure
        """
        self.table_counter += 1
        table_id = f"table-{page_number}-{self.table_counter}"

        # Build HTML table
        html_parts = [f'<table class="ai-table" id="{table_id}">']

        # Detect header row (first row with different formatting or all bold)
        has_header = len(table.rows) > 0
        if has_header:
            html_parts.append('  <thead>')
            html_parts.append('    <tr>')
            for cell in table.rows[0]:
                html_parts.append(f'      <th>{self._escape_html(cell)}</th>')
            html_parts.append('    </tr>')
            html_parts.append('  </thead>')

        # Body rows
        if len(table.rows) > 1:
            html_parts.append('  <tbody>')
            for row in table.rows[1:]:
                html_parts.append('    <tr>')
                for cell in row:
                    html_parts.append(f'      <td>{self._escape_html(cell)}</td>')
                html_parts.append('    </tr>')
            html_parts.append('  </tbody>')

        html_parts.append('</table>')
        content = '\n'.join(html_parts)

        return XHTMLElement(
            tag='table',
            content=content,
            attributes={'class': 'ai-table', 'id': table_id},
            bbox=table.bbox
        )

    def convert_table_to_html(self, table: TableItem, page_number: int) -> str:
        """
        Public API: Convert table to HTML string.

        Args:
            table: Table item from layout analysis
            page_number: Page number for reference

        Returns:
            HTML table string
        """
        element = self._convert_table_to_element(table, page_number)
        return element.content

    def _convert_image_to_element(
        self,
        image: ImageItem,
        page_number: int
    ) -> XHTMLElement:
        """
        Convert image data to XHTML element.

        Args:
            image: Image item from layout analysis
            page_number: Page number for reference

        Returns:
            XHTMLElement with <figure> and <img> tag
        """
        self.image_counter += 1
        image_id = f"image-{page_number}-{self.image_counter}"
        image_filename = f"images/page-{page_number}-img-{self.image_counter}.png"

        # Build figure with image and optional caption
        html_parts = [f'<figure id="{image_id}">']
        html_parts.append(f'  <img src="../{image_filename}" alt="{self._escape_html(image.alt_text or "Image")}" />')

        if image.alt_text:
            html_parts.append(f'  <figcaption>{self._escape_html(image.alt_text)}</figcaption>')

        html_parts.append('</figure>')
        content = '\n'.join(html_parts)

        return XHTMLElement(
            tag='figure',
            content=content,
            attributes={'id': image_id, 'class': 'ai-image'},
            bbox=image.bbox
        )

    def embed_image(
        self,
        image: ImageItem,
        page_number: int
    ) -> Tuple[str, str, bytes]:
        """
        Public API: Embed image and return HTML + image data.

        Args:
            image: Image item from layout analysis
            page_number: Page number for reference

        Returns:
            Tuple of (html_string, image_filename, image_bytes)
        """
        element = self._convert_image_to_element(image, page_number)
        image_filename = f"images/page-{page_number}-img-{self.image_counter}.png"

        # image.image_bytes should contain the actual image data
        image_bytes = image.image_bytes if image.image_bytes else b''

        return (element.content, image_filename, image_bytes)

    def _convert_equation_to_element(
        self,
        equation: EquationItem,
        page_number: int
    ) -> XHTMLElement:
        """
        Convert equation to XHTML element with MathML + PNG fallback.

        Args:
            equation: Equation item from layout analysis
            page_number: Page number for reference

        Returns:
            XHTMLElement with MathML and fallback image
        """
        self.equation_counter += 1
        equation_id = f"equation-{page_number}-{self.equation_counter}"
        fallback_filename = f"images/equation-{page_number}-{self.equation_counter}.png"

        # Build MathML with PNG fallback
        html_parts = [f'<div class="equation" id="{equation_id}">']

        # MathML content (if available)
        if equation.mathml:
            html_parts.append(f'  <math xmlns="http://www.w3.org/1998/Math/MathML">')
            html_parts.append(f'    {equation.mathml}')
            html_parts.append('  </math>')

        # PNG fallback
        if equation.latex:
            alt_text = equation.latex
        else:
            alt_text = "Equation"

        html_parts.append(f'  <img src="../{fallback_filename}" alt="{self._escape_html(alt_text)}" class="math-fallback" />')
        html_parts.append('</div>')

        content = '\n'.join(html_parts)

        return XHTMLElement(
            tag='div',
            content=content,
            attributes={'class': 'equation', 'id': equation_id},
            bbox=equation.bbox
        )

    def convert_equation_to_mathml(
        self,
        equation: EquationItem,
        page_number: int
    ) -> Tuple[str, Optional[bytes]]:
        """
        Public API: Convert equation to MathML with PNG fallback.

        Args:
            equation: Equation item from layout analysis
            page_number: Page number for reference

        Returns:
            Tuple of (html_string, png_bytes)
        """
        element = self._convert_equation_to_element(equation, page_number)
        png_bytes = equation.png_fallback if hasattr(equation, 'png_fallback') else None

        return (element.content, png_bytes)

    def _convert_text_to_element(self, text_block: TextBlock) -> XHTMLElement:
        """
        Convert text block to XHTML paragraph.

        Args:
            text_block: Text block from layout analysis

        Returns:
            XHTMLElement with <p> tag
        """
        # Determine tag based on text properties
        tag = 'p'
        css_class = 'text-block'

        # Check if this looks like a heading (future enhancement)
        # For now, treat all text as paragraphs

        content = f'<{tag} class="{css_class}">{self._escape_html(text_block.text)}</{tag}>'

        return XHTMLElement(
            tag=tag,
            content=content,
            attributes={'class': css_class},
            bbox=text_block.bbox
        )

    def reflow_multicolumn_content(self, text_blocks: List[TextBlock]) -> str:
        """
        Convert multi-column layout to single-column XHTML.

        Reorders text blocks from left-to-right, top-to-bottom reading order.

        Args:
            text_blocks: List of text blocks from layout analysis

        Returns:
            XHTML string with reflowed content
        """
        # Sort by vertical position (top to bottom), then horizontal (left to right)
        sorted_blocks = sorted(
            text_blocks,
            key=lambda b: (b.bbox[1], b.bbox[0]) if b.bbox else (0, 0)
        )

        # Convert to XHTML paragraphs
        html_parts = []
        for block in sorted_blocks:
            element = self._convert_text_to_element(block)
            html_parts.append(element.content)

        return '\n'.join(html_parts)

    def build_xhtml_chapter(
        self,
        chapter_title: str,
        elements: List[XHTMLElement],
        language: str = 'en'
    ) -> str:
        """
        Assemble complete XHTML chapter from elements.

        Args:
            chapter_title: Chapter title for <h1>
            elements: List of XHTML elements (tables, images, text)
            language: Document language code

        Returns:
            Complete XHTML string for chapter
        """
        html_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<!DOCTYPE html>',
            f'<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{language}" lang="{language}">',
            '<head>',
            '  <meta charset="UTF-8"/>',
            f'  <title>{self._escape_html(chapter_title)}</title>',
            '  <link rel="stylesheet" type="text/css" href="../styles.css"/>',
            '</head>',
            '<body>',
            f'  <section class="chapter">',
            f'    <h1>{self._escape_html(chapter_title)}</h1>',
        ]

        # Add all elements
        if elements:
            for element in elements:
                html_parts.append(f'    {element.content}')
        else:
            # Add placeholder content to prevent empty document errors
            html_parts.append('    <p class="empty-chapter">This chapter contains no extractable content.</p>')

        html_parts.extend([
            '  </section>',
            '</body>',
            '</html>'
        ])

        return '\n'.join(html_parts)

    def _escape_html(self, text: str) -> str:
        """
        Escape HTML special characters.

        Args:
            text: Raw text string

        Returns:
            HTML-escaped string
        """
        if not text:
            return ''

        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
