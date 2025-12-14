"""
Unit Tests for Heuristic Structure Detector

Tests rule-based fallback structure detection when AI fails.
"""

import pytest
from app.services.conversion.heuristic_structure import HeuristicStructureDetector


# ============================================================================
# Initialization Tests
# ============================================================================

def test_heuristic_detector_initialization():
    """Test HeuristicStructureDetector initializes correctly"""
    detector = HeuristicStructureDetector(language="en")
    assert detector.language == "en"


# ============================================================================
# Pattern Detection Tests
# ============================================================================

def test_detect_by_patterns_chapter():
    """Test pattern-based chapter detection"""
    detector = HeuristicStructureDetector(language="en")

    lines = [
        "CHAPTER 1: INTRODUCTION",
        "",
        "This is the introduction text...",
        "",
        "Chapter 2: Background",
        "",
        "Background information here..."
    ]

    detected = detector._detect_by_patterns(lines, chars_per_page=1000)

    # Should detect both chapters
    chapter_headings = [h for h in detected if h["level"] == 1]
    assert len(chapter_headings) >= 2


def test_detect_by_patterns_numbered_sections():
    """Test detection of numbered sections (1.1, 1.2, etc.)"""
    detector = HeuristicStructureDetector(language="en")

    lines = [
        "1.1 Introduction",
        "This is section 1.1",
        "",
        "1.2 Methods",
        "This is section 1.2",
        "",
        "1.2.1 Data Collection",
        "This is subsection 1.2.1"
    ]

    detected = detector._detect_by_patterns(lines, chars_per_page=100)

    # Should detect sections (level 2)
    sections = [h for h in detected if h["level"] == 2]
    assert len(sections) >= 2

    # Should detect subsections (level 3)
    subsections = [h for h in detected if h["level"] == 3]
    assert len(subsections) >= 1


def test_detect_by_formatting_all_caps():
    """Test detection of all-caps headings"""
    detector = HeuristicStructureDetector(language="en")

    lines = [
        "INTRODUCTION",
        "This is normal text.",
        "",
        "METHODS AND MATERIALS",
        "More text here."
    ]

    detected = detector._detect_by_formatting(lines, chars_per_page=100)

    # Should detect all-caps lines as headings
    all_caps_headings = [h for h in detected if h["source"] == "format:all_caps"]
    assert len(all_caps_headings) >= 2


def test_detect_by_formatting_short_lines():
    """Test detection of short standalone lines as potential headings"""
    detector = HeuristicStructureDetector(language="en")

    lines = [
        "Introduction",  # Short, capitalized, no punctuation
        "This is a longer sentence with proper punctuation.",
        "",
        "Background Information",  # Another potential heading
        "More content follows."
    ]

    detected = detector._detect_by_formatting(lines, chars_per_page=100)

    # Should detect short lines as potential headings
    short_line_headings = [h for h in detected if h["source"] == "format:short_line"]
    assert len(short_line_headings) >= 1


# ============================================================================
# Title Detection Tests
# ============================================================================

def test_detect_title_all_caps():
    """Test title detection from all-caps line"""
    detector = HeuristicStructureDetector(language="en")

    lines = [
        "",
        "INTRODUCTION TO MACHINE LEARNING",
        "",
        "By Dr. Jane Smith",
        "",
        "Chapter 1: Getting Started"
    ]

    title = detector._detect_title(lines)
    assert title == "INTRODUCTION TO MACHINE LEARNING"


def test_detect_title_no_all_caps():
    """Test title detection fallback to first prominent line"""
    detector = HeuristicStructureDetector(language="en")

    lines = [
        "",
        "Introduction to Machine Learning",  # No all-caps, but prominent
        "",
        "By Dr. Jane Smith"
    ]

    title = detector._detect_title(lines)
    assert title == "Introduction to Machine Learning"


def test_detect_title_none_found():
    """Test title detection returns None if no title found"""
    detector = HeuristicStructureDetector(language="en")

    lines = [
        "Short",
        "A",
        "Very short lines only"
    ]

    title = detector._detect_title(lines)
    # Should return None or one of the lines
    assert title is None or len(title) > 5


# ============================================================================
# Full Structure Detection Tests
# ============================================================================

def test_detect_structure_comprehensive():
    """Test full structure detection on sample document"""
    detector = HeuristicStructureDetector(language="en")

    text = """INTRODUCTION TO MACHINE LEARNING

By Dr. Jane Smith

CHAPTER 1: FOUNDATIONS

This chapter covers the basics.

1.1 What is Machine Learning?

Machine learning is a subset of AI.

1.2 Applications

ML is used in many domains.

CHAPTER 2: ALGORITHMS

This chapter covers algorithms.

2.1 Supervised Learning

Supervised learning uses labeled data.
"""

    result = detector.detect_structure(
        text=text,
        page_count=10,
        layout_hints=None
    )

    # Should detect title
    assert result["title"] == "INTRODUCTION TO MACHINE LEARNING"

    # Should detect chapters
    assert result["toc"]["total_entries"] > 0

    # Should have reasonable confidence (heuristic = 65%)
    assert result["confidence_score"] == 65

    # Should have language set
    assert result["language"] == "en"


def test_detect_structure_with_layout_hints():
    """Test structure detection using font-size hints from layout analysis"""
    detector = HeuristicStructureDetector(language="en")

    text = "Sample document text"

    layout_hints = {
        "text_blocks": [
            {"text": "Chapter 1: Introduction", "font_size_hint": 20, "page_number": 1},
            {"text": "This is body text", "font_size_hint": 10, "page_number": 1},
            {"text": "1.1 Background", "font_size_hint": 14, "page_number": 2}
        ]
    }

    result = detector.detect_structure(
        text=text,
        page_count=5,
        layout_hints=layout_hints
    )

    # Should use font-size hints to detect headings
    assert result["toc"]["total_entries"] >= 2  # At least 2 headings detected


def test_detect_structure_empty_document():
    """Test heuristic detection on empty document"""
    detector = HeuristicStructureDetector(language="en")

    result = detector.detect_structure(
        text="",
        page_count=0,
        layout_hints=None
    )

    # Should return valid structure with empty TOC
    assert result["toc"]["total_entries"] == 0
    assert len(result["chapters"]) == 0


# ============================================================================
# Deduplication Tests
# ============================================================================

def test_deduplicate_headings():
    """Test deduplication keeps highest confidence detection"""
    detector = HeuristicStructureDetector(language="en")

    headings = [
        {"title": "Chapter 1", "confidence": 80, "level": 1, "page_number": 5},
        {"title": "Chapter 1", "confidence": 90, "level": 1, "page_number": 5},  # Duplicate, higher confidence
        {"title": "Chapter 2", "confidence": 85, "level": 1, "page_number": 20}
    ]

    deduplicated = detector._deduplicate_headings(headings)

    # Should keep 2 unique headings
    assert len(deduplicated) == 2

    # Should keep higher confidence duplicate
    chapter1 = [h for h in deduplicated if h["title"] == "Chapter 1"][0]
    assert chapter1["confidence"] == 90


# ============================================================================
# Build TOC Entries Tests
# ============================================================================

def test_build_toc_entries():
    """Test conversion of detected headings to TOC format"""
    detector = HeuristicStructureDetector(language="en")

    detected_headings = [
        {"title": "Chapter 1", "level": 1, "page_number": 5, "confidence": 90, "source": "pattern"},
        {"title": "Section 1.1", "level": 2, "page_number": 6, "confidence": 85, "source": "pattern"}
    ]

    toc_entries = detector._build_toc_entries(detected_headings)

    assert len(toc_entries) == 2
    assert toc_entries[0]["type"] == "chapter"
    assert toc_entries[1]["type"] == "section"


# ============================================================================
# Build Chapters Tests
# ============================================================================

def test_build_chapters():
    """Test chapter construction from TOC entries"""
    detector = HeuristicStructureDetector(language="en")

    toc_entries = [
        {"title": "Chapter 1", "level": 1, "page_number": 5, "type": "chapter"},
        {"title": "1.1 Intro", "level": 2, "page_number": 6, "type": "section"},
        {"title": "Chapter 2", "level": 1, "page_number": 20, "type": "chapter"}
    ]

    chapters = detector._build_chapters(toc_entries)

    assert len(chapters) == 2
    assert chapters[0]["chapter_num"] == 1
    assert chapters[0]["title"] == "Chapter 1"
    assert len(chapters[0]["subsections"]) == 1
