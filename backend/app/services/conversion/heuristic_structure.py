"""
Heuristic Structure Detection Fallback

Provides rule-based document structure detection when AI analysis fails
or returns low confidence results. Uses font-size analysis, pattern matching,
and formatting cues to generate TOC.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class HeuristicStructureDetector:
    """
    Rule-based document structure detection using heuristics.

    Fallback strategy when AI fails or returns low confidence (<70%).
    Uses font-size analysis, pattern matching, and formatting detection.
    """

    # Regex patterns for common heading structures (English-focused, extend for other languages)
    CHAPTER_PATTERNS = [
        r"^(CHAPTER|Chapter)\s+([IVXLCDM]+|\d+)[:\s]*(.*)",  # "Chapter 1: Introduction"
        r"^(PART|Part)\s+([IVXLCDM]+|\d+)[:\s]*(.*)",  # "Part I: Overview"
        r"^([IVXLCDM]+)\.\s+(.*)",  # "I. Introduction"
        r"^(\d+)\.\s+([A-Z][^.]+)",  # "1. Introduction" (capitalized)
    ]

    SECTION_PATTERNS = [
        r"^(\d+)\.(\d+)\s+(.*)",  # "1.1 Background"
        r"^(SECTION|Section)\s+(\d+)[:\s]*(.*)",  # "Section 1: Overview"
        r"^([A-Z])\.\s+(.*)",  # "A. Background"
    ]

    SUBSECTION_PATTERNS = [
        r"^(\d+)\.(\d+)\.(\d+)\s+(.*)",  # "1.1.1 Details"
        r"^([a-z])\)\s+(.*)",  # "a) First point"
    ]

    def __init__(self, language: str = "en"):
        """
        Initialize heuristic detector.

        Args:
            language: ISO 639-1 language code (currently only 'en' fully supported)
        """
        self.language = language
        logger.info(f"Initialized HeuristicStructureDetector for language: {language}")

    def detect_structure(
        self,
        text: str,
        page_count: int,
        layout_hints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Detect document structure using heuristics.

        Args:
            text: Full document text
            page_count: Total number of pages
            layout_hints: Optional layout analysis data (font sizes, formatting)

        Returns:
            DocumentStructure dict with detected TOC and chapters

        Strategy:
            1. Split text into lines
            2. Apply pattern matching for chapter/section detection
            3. Use font-size hints if available (from layout analysis)
            4. Detect formatting cues (all-caps, short lines)
            5. Estimate page numbers based on text position
            6. Build hierarchical TOC structure
        """
        logger.info(f"Running heuristic structure detection: {page_count} pages, {len(text)} chars")

        # Split text into lines for analysis
        lines = text.split("\n")
        chars_per_page = len(text) // page_count if page_count > 0 else len(text)

        # Detect headings using multiple strategies
        detected_headings = []

        # Strategy 1: Pattern matching
        detected_headings.extend(self._detect_by_patterns(lines, chars_per_page))

        # Strategy 2: Font size (if layout hints available)
        if layout_hints:
            detected_headings.extend(self._detect_by_font_size(layout_hints, chars_per_page))

        # Strategy 3: Formatting cues (all-caps, short lines)
        detected_headings.extend(self._detect_by_formatting(lines, chars_per_page))

        # Remove duplicates and sort by page number
        deduplicated = self._deduplicate_headings(detected_headings)
        deduplicated.sort(key=lambda h: h["page_number"])

        logger.info(f"Heuristic detection found {len(deduplicated)} potential headings")

        # Build TOC structure
        toc_entries = self._build_toc_entries(deduplicated)

        # Build chapters
        chapters = self._build_chapters(toc_entries)

        # Construct DocumentStructure result
        result = {
            "title": self._detect_title(lines) or "Unknown Document",
            "author": None,  # Heuristics can't reliably detect author
            "language": self.language,
            "toc": {
                "items": toc_entries,
                "total_entries": len(toc_entries),
                "max_depth": max([e["level"] for e in toc_entries], default=1)
            },
            "chapters": chapters,
            "confidence_score": 65  # Heuristic fallback = lower confidence
        }

        logger.info(
            f"Heuristic result: {len(toc_entries)} TOC entries, "
            f"{len(chapters)} chapters, confidence=65%"
        )

        return result

    def _detect_by_patterns(
        self,
        lines: List[str],
        chars_per_page: int
    ) -> List[Dict[str, Any]]:
        """
        Detect headings using regex pattern matching.

        Returns:
            List of detected heading dicts with: title, level, page, confidence
        """
        detected = []
        char_position = 0

        for line in lines:
            line_stripped = line.strip()

            if not line_stripped or len(line_stripped) < 3:
                char_position += len(line) + 1  # +1 for newline
                continue

            # Try chapter patterns (level 1)
            for pattern in self.CHAPTER_PATTERNS:
                match = re.match(pattern, line_stripped)
                if match:
                    page_num = max(1, char_position // chars_per_page + 1)
                    detected.append({
                        "title": line_stripped,
                        "level": 1,
                        "page_number": page_num,
                        "confidence": 85,
                        "source": "pattern:chapter"
                    })
                    break

            # Try section patterns (level 2)
            for pattern in self.SECTION_PATTERNS:
                match = re.match(pattern, line_stripped)
                if match:
                    page_num = max(1, char_position // chars_per_page + 1)
                    detected.append({
                        "title": line_stripped,
                        "level": 2,
                        "page_number": page_num,
                        "confidence": 80,
                        "source": "pattern:section"
                    })
                    break

            # Try subsection patterns (level 3)
            for pattern in self.SUBSECTION_PATTERNS:
                match = re.match(pattern, line_stripped)
                if match:
                    page_num = max(1, char_position // chars_per_page + 1)
                    detected.append({
                        "title": line_stripped,
                        "level": 3,
                        "page_number": page_num,
                        "confidence": 75,
                        "source": "pattern:subsection"
                    })
                    break

            char_position += len(line) + 1  # +1 for newline

        return detected

    def _detect_by_font_size(
        self,
        layout_hints: Dict[str, Any],
        chars_per_page: int
    ) -> List[Dict[str, Any]]:
        """
        Detect headings based on font size hints from layout analysis.

        Strategy:
            - Larger fonts (>18pt) → H1 (chapter)
            - Large fonts (14-18pt) → H2 (section)
            - Medium fonts (12-14pt) → H3 (subsection)
        """
        detected = []

        # Extract text blocks with font size hints from layout analysis
        # This would come from Story 4.2's layout_analysis output
        text_blocks = layout_hints.get("text_blocks", [])

        for block in text_blocks:
            font_size = block.get("font_size_hint")
            text = block.get("text", "").strip()
            page_num = block.get("page_number", 1)

            if not font_size or not text or len(text) > 150:  # Skip long blocks
                continue

            # Classify by font size
            if font_size >= 18:
                level = 1
                confidence = 90
            elif font_size >= 14:
                level = 2
                confidence = 85
            elif font_size >= 12:
                level = 3
                confidence = 75
            else:
                continue  # Not a heading

            detected.append({
                "title": text,
                "level": level,
                "page_number": page_num,
                "confidence": confidence,
                "source": f"font_size:{font_size}pt"
            })

        return detected

    def _detect_by_formatting(
        self,
        lines: List[str],
        chars_per_page: int
    ) -> List[Dict[str, Any]]:
        """
        Detect headings based on formatting cues (all-caps, short lines).

        Heuristics:
            - ALL CAPS lines <80 chars → Likely heading
            - Standalone short lines <60 chars without punctuation → Potential heading
            - Lines with no trailing period → Potential heading
        """
        detected = []
        char_position = 0

        for line in lines:
            line_stripped = line.strip()

            if not line_stripped or len(line_stripped) < 5:
                char_position += len(line) + 1
                continue

            # All-caps detection
            if line_stripped.isupper() and len(line_stripped) < 80:
                page_num = max(1, char_position // chars_per_page + 1)
                detected.append({
                    "title": line_stripped,
                    "level": 1,  # All-caps usually chapters
                    "page_number": page_num,
                    "confidence": 70,
                    "source": "format:all_caps"
                })

            # Short standalone lines without trailing punctuation
            elif (
                len(line_stripped) < 60 and
                not line_stripped.endswith((".", ",", ";", ":", ")", "]")) and
                line_stripped[0].isupper()  # Starts with capital
            ):
                page_num = max(1, char_position // chars_per_page + 1)
                detected.append({
                    "title": line_stripped,
                    "level": 2,  # Conservative level
                    "page_number": page_num,
                    "confidence": 60,
                    "source": "format:short_line"
                })

            char_position += len(line) + 1

        return detected

    def _deduplicate_headings(
        self,
        headings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate headings detected by multiple strategies.

        Strategy:
            - Group by title and page number
            - Keep highest confidence detection
        """
        if not headings:
            return []

        # Group by title
        title_groups: Dict[str, List[Dict[str, Any]]] = {}
        for heading in headings:
            title = heading["title"]
            if title not in title_groups:
                title_groups[title] = []
            title_groups[title].append(heading)

        deduplicated = []
        for title, group in title_groups.items():
            # Sort by confidence (descending) and keep first
            group.sort(key=lambda h: h["confidence"], reverse=True)
            deduplicated.append(group[0])

        return deduplicated

    def _detect_title(self, lines: List[str]) -> Optional[str]:
        """
        Attempt to detect document title from first few lines.

        Strategy:
            - Look for all-caps lines in first 50 lines
            - Look for short prominent lines
            - Return first match or None
        """
        for line in lines[:50]:
            line_stripped = line.strip()

            # All-caps line that looks like a title
            if (
                line_stripped.isupper() and
                10 < len(line_stripped) < 100 and
                not line_stripped.startswith(("PAGE", "CHAPTER", "SECTION"))
            ):
                return line_stripped

        # If no all-caps found, look for first prominent line
        for line in lines[:20]:
            line_stripped = line.strip()
            if 10 < len(line_stripped) < 100 and line_stripped[0].isupper():
                return line_stripped

        return None

    def _build_toc_entries(
        self,
        detected_headings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convert detected headings to TOCEntry format.
        """
        toc_entries = []

        for heading in detected_headings:
            # Determine type based on level
            type_map = {
                1: "chapter",
                2: "section",
                3: "subsection",
                4: "sub-subsection"
            }

            entry = {
                "title": heading["title"],
                "level": heading["level"],
                "page_number": heading["page_number"],
                "confidence": heading["confidence"],
                "text_sample": "",  # Heuristics don't have context
                "type": type_map.get(heading["level"], "section")
            }
            toc_entries.append(entry)

        return toc_entries

    def _build_chapters(
        self,
        toc_entries: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Group TOC entries into chapter structures.
        """
        if not toc_entries:
            return []

        chapters = []
        current_chapter = None
        chapter_num = 1

        for entry in toc_entries:
            if entry["level"] == 1:
                # Save previous chapter
                if current_chapter:
                    chapters.append(current_chapter)

                # Start new chapter
                current_chapter = {
                    "chapter_num": chapter_num,
                    "title": entry["title"],
                    "start_page": entry["page_number"],
                    "end_page": entry["page_number"],
                    "subsections": []
                }
                chapter_num += 1
            elif current_chapter:
                # Add subsection
                current_chapter["subsections"].append(entry)
                current_chapter["end_page"] = max(
                    current_chapter["end_page"],
                    entry["page_number"]
                )

        # Add final chapter
        if current_chapter:
            chapters.append(current_chapter)

        return chapters
