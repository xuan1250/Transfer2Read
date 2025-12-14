"""
TOC Generator for EPUB

Generates EPUB Navigation Control Files (NCX for EPUB 2, Nav for EPUB 3)
from detected document structure. Supports hierarchical chapter organization.
"""

import logging
from typing import Dict, Any, List
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


class TOCGenerator:
    """
    Generates EPUB table of contents structures (NCX and Nav).

    Supports both EPUB 2 (NCX) and EPUB 3 (Nav) formats for maximum compatibility.
    """

    def __init__(self):
        """Initialize TOC generator."""
        logger.info("Initialized TOCGenerator")

    def build_epub_ncx(
        self,
        toc_entries: List[Dict[str, Any]],
        document_title: str,
        uid: str = "unknown"
    ) -> str:
        """
        Generate EPUB 2 Navigation Control File (NCX) XML.

        Args:
            toc_entries: List of TOCEntry dicts with title, level, page_number
            document_title: Document title for NCX metadata
            uid: Unique identifier for document (default: "unknown")

        Returns:
            NCX XML string

        Format:
            <?xml version="1.0" encoding="UTF-8"?>
            <ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
              <head>
                <meta name="dtb:uid" content="{uid}"/>
                <meta name="dtb:depth" content="{max_depth}"/>
                <meta name="dtb:totalPageCount" content="0"/>
                <meta name="dtb:maxPageNumber" content="0"/>
              </head>
              <docTitle><text>{document_title}</text></docTitle>
              <navMap>
                <navPoint id="navPoint-1" playOrder="1">
                  <navLabel><text>Chapter 1</text></navLabel>
                  <content src="chapter1.xhtml"/>
                </navPoint>
              </navMap>
            </ncx>
        """
        logger.info(f"Generating EPUB 2 NCX for '{document_title}' with {len(toc_entries)} entries")

        # Calculate max depth
        max_depth = max([e.get("level", 1) for e in toc_entries], default=1)

        # Create root NCX element
        ncx = ET.Element("ncx", {
            "xmlns": "http://www.daisy.org/z3986/2005/ncx/",
            "version": "2005-1",
            "xml:lang": "en"
        })

        # Add head metadata
        head = ET.SubElement(ncx, "head")
        ET.SubElement(head, "meta", {"name": "dtb:uid", "content": uid})
        ET.SubElement(head, "meta", {"name": "dtb:depth", "content": str(max_depth)})
        ET.SubElement(head, "meta", {"name": "dtb:totalPageCount", "content": "0"})
        ET.SubElement(head, "meta", {"name": "dtb:maxPageNumber", "content": "0"})

        # Add document title
        doc_title = ET.SubElement(ncx, "docTitle")
        ET.SubElement(doc_title, "text").text = document_title

        # Add navigation map
        nav_map = ET.SubElement(ncx, "navMap")

        # Build hierarchical navigation points
        if toc_entries:
            self._build_ncx_nav_points(nav_map, toc_entries)
        else:
            # Add placeholder navPoint to prevent empty navigation
            nav_point = ET.SubElement(nav_map, "navPoint", {
                "id": "navPoint-1",
                "playOrder": "1"
            })
            nav_label = ET.SubElement(nav_point, "navLabel")
            ET.SubElement(nav_label, "text").text = "Document Content"
            ET.SubElement(nav_point, "content", {"src": "chapters/chapter-1.xhtml"})

        # Convert to XML string
        tree = ET.ElementTree(ncx)
        xml_str = ET.tostring(ncx, encoding="unicode", method="xml")

        # Pretty print (basic)
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str

        logger.info(f"NCX generated successfully: {len(toc_entries)} entries, max_depth={max_depth}")
        return xml_str

    def _build_ncx_nav_points(
        self,
        parent: ET.Element,
        toc_entries: List[Dict[str, Any]],
        start_index: int = 0,
        current_level: int = 1
    ) -> int:
        """
        Recursively build NCX navPoint hierarchy.

        Args:
            parent: Parent XML element to append navPoints to
            toc_entries: List of TOC entries
            start_index: Index to start processing from
            current_level: Current hierarchy level (1-4)

        Returns:
            Index of last processed entry
        """
        play_order = start_index + 1
        i = start_index

        while i < len(toc_entries):
            entry = toc_entries[i]
            entry_level = entry.get("level", 1)

            # If this entry is at a higher level, return (go back up the tree)
            if entry_level < current_level:
                return i - 1

            # If this entry is at our level, create navPoint
            if entry_level == current_level:
                nav_point = ET.SubElement(parent, "navPoint", {
                    "id": f"navPoint-{i + 1}",
                    "playOrder": str(play_order)
                })

                # Add label
                nav_label = ET.SubElement(nav_point, "navLabel")
                ET.SubElement(nav_label, "text").text = entry.get("title", "Untitled")

                # Add content reference (placeholder - actual file would be determined by EPUB generator)
                content_src = f"chapter{i + 1}.xhtml"
                ET.SubElement(nav_point, "content", {"src": content_src})

                # Check if next entries are sub-levels
                if i + 1 < len(toc_entries) and toc_entries[i + 1].get("level", 1) > current_level:
                    # Recursively process sub-levels
                    last_processed = self._build_ncx_nav_points(
                        nav_point,
                        toc_entries,
                        i + 1,
                        current_level + 1
                    )
                    i = last_processed + 1
                else:
                    i += 1

                play_order += 1

            # If entry is deeper than current level, skip (will be handled by recursion)
            elif entry_level > current_level:
                i += 1

        return len(toc_entries) - 1

    def build_epub_nav(
        self,
        toc_entries: List[Dict[str, Any]],
        document_title: str
    ) -> str:
        """
        Generate EPUB 3 Navigation Document (Nav) HTML.

        Args:
            toc_entries: List of TOCEntry dicts with title, level, page_number
            document_title: Document title for nav metadata

        Returns:
            Nav HTML string

        Format:
            <?xml version="1.0" encoding="UTF-8"?>
            <html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
              <head>
                <title>{document_title}</title>
              </head>
              <body>
                <nav epub:type="toc" id="toc">
                  <h1>Table of Contents</h1>
                  <ol>
                    <li><a href="chapter1.xhtml">Chapter 1: Introduction</a>
                      <ol>
                        <li><a href="chapter1.xhtml#section1">1.1 Background</a></li>
                      </ol>
                    </li>
                  </ol>
                </nav>
              </body>
            </html>
        """
        logger.info(f"Generating EPUB 3 Nav for '{document_title}' with {len(toc_entries)} entries")

        # Create HTML root
        html = ET.Element("html", {
            "xmlns": "http://www.w3.org/1999/xhtml",
            "xmlns:epub": "http://www.idpf.org/2007/ops",
            "xml:lang": "en"
        })

        # Add head
        head = ET.SubElement(html, "head")
        ET.SubElement(head, "title").text = document_title

        # Add body
        body = ET.SubElement(html, "body")

        # Add nav element
        nav = ET.SubElement(body, "nav", {
            "epub:type": "toc",
            "id": "toc"
        })
        ET.SubElement(nav, "h1").text = "Table of Contents"

        # Build hierarchical ordered list
        if toc_entries:
            root_ol = ET.SubElement(nav, "ol")
            self._build_nav_list(root_ol, toc_entries)
        else:
            # Add placeholder entry to prevent empty navigation
            root_ol = ET.SubElement(nav, "ol")
            li = ET.SubElement(root_ol, "li")
            a = ET.SubElement(li, "a", {"href": "chapters/chapter-1.xhtml"})
            a.text = "Document Content"

        # Convert to HTML string
        html_str = ET.tostring(html, encoding="unicode", method="xml")
        html_str = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE html>\n' + html_str

        logger.info(f"Nav generated successfully: {len(toc_entries)} entries")
        return html_str

    def _build_nav_list(
        self,
        parent_ol: ET.Element,
        toc_entries: List[Dict[str, Any]],
        start_index: int = 0,
        current_level: int = 1
    ) -> int:
        """
        Recursively build nested <ol> structure for EPUB 3 Nav.

        Args:
            parent_ol: Parent <ol> element
            toc_entries: List of TOC entries
            start_index: Index to start processing from
            current_level: Current hierarchy level

        Returns:
            Index of last processed entry
        """
        i = start_index

        while i < len(toc_entries):
            entry = toc_entries[i]
            entry_level = entry.get("level", 1)

            # If entry is at higher level, return
            if entry_level < current_level:
                return i - 1

            # If entry is at our level, create <li>
            if entry_level == current_level:
                li = ET.SubElement(parent_ol, "li")

                # Add link
                link_href = f"chapter{i + 1}.xhtml"
                a = ET.SubElement(li, "a", {"href": link_href})
                a.text = entry.get("title", "Untitled")

                # Check if next entries are sub-levels
                if i + 1 < len(toc_entries) and toc_entries[i + 1].get("level", 1) > current_level:
                    # Create nested <ol> for sub-entries
                    nested_ol = ET.SubElement(li, "ol")
                    last_processed = self._build_nav_list(
                        nested_ol,
                        toc_entries,
                        i + 1,
                        current_level + 1
                    )
                    i = last_processed + 1
                else:
                    i += 1

            # If entry is deeper, skip (handled by recursion)
            elif entry_level > current_level:
                i += 1

        return len(toc_entries) - 1

    def insert_chapter_breaks(
        self,
        content: str,
        chapters: List[Dict[str, Any]]
    ) -> str:
        """
        Insert chapter break markers into HTML content.

        Args:
            content: HTML content string
            chapters: List of ChapterMetadata dicts with start_page, end_page

        Returns:
            Content with <div class="chapter" id="chapter-X"> markers inserted

        Strategy:
            - Estimate chapter positions based on page numbers
            - Insert <div class="chapter" id="chapter-{num}"> at chapter starts
            - Close previous chapter div before starting new one

        Note:
            This is a simplified implementation. Real EPUB generation
            would split content into separate XHTML files per chapter.
        """
        logger.info(f"Inserting chapter breaks for {len(chapters)} chapters")

        if not chapters:
            return content

        # For now, return content with chapter markers as comments
        # Real implementation would split content into files
        marked_content = content

        for chapter in chapters:
            chapter_num = chapter.get("chapter_num", 0)
            # Insert chapter marker (simplified - real impl would split files)
            marker = f'\n<!-- CHAPTER {chapter_num} START: {chapter.get("title", "Untitled")} -->\n'
            marked_content += marker

        logger.info(f"Chapter breaks inserted: {len(chapters)} markers")
        return marked_content

    def tag_hierarchical_headers(
        self,
        content: str,
        toc_entries: List[Dict[str, Any]]
    ) -> str:
        """
        Tag headers in content with correct hierarchy (H1, H2, H3, H4).

        Args:
            content: Plain text or HTML content
            toc_entries: List of TOCEntry dicts with title and level

        Returns:
            Content with headers tagged as <h1>, <h2>, <h3>, <h4>

        Strategy:
            - For each TOC entry, find its title in content
            - Replace with proper <hN> tag based on level
            - Preserve hierarchy consistency

        Note:
            This is a simplified implementation. Real EPUB generation
            would apply semantic HTML structure during content conversion.
        """
        logger.info(f"Tagging {len(toc_entries)} hierarchical headers")

        tagged_content = content

        for entry in toc_entries:
            title = entry.get("title", "")
            level = entry.get("level", 1)

            if not title:
                continue

            # Simple replacement (real impl would be more sophisticated)
            # This is placeholder logic for concept demonstration
            h_tag = f"<h{level}>{title}</h{level}>"

            # Replace title with tagged version (if not already tagged)
            if title in tagged_content and f"<h{level}>" not in tagged_content[:100]:
                tagged_content = tagged_content.replace(title, h_tag, 1)

        logger.info(f"Headers tagged with H1-H4 tags")
        return tagged_content

    def validate_toc_hierarchy(
        self,
        toc_entries: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Validate TOC hierarchy for proper nesting.

        Args:
            toc_entries: List of TOCEntry dicts

        Returns:
            List of validation error messages (empty if valid)

        Checks:
            - No H3 under H1 without H2
            - No H4 under H2 without H3
            - Level progression is logical (no jumps > 1)
        """
        errors = []
        prev_level = 0

        for i, entry in enumerate(toc_entries):
            level = entry.get("level", 1)
            title = entry.get("title", "Untitled")

            # Check for level jumps > 1
            if level > prev_level + 1:
                errors.append(
                    f"Entry {i} ('{title}'): Invalid level jump from H{prev_level} to H{level}"
                )

            prev_level = level

        if errors:
            logger.warning(f"TOC hierarchy validation found {len(errors)} errors")
        else:
            logger.info("TOC hierarchy validation passed")

        return errors
