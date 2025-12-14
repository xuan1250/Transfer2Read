"""
Unit Tests for Text Chunker

Tests document chunking logic for large document processing.
Verifies chunking, overlap, and merge functionality.
"""

import pytest
from app.services.conversion.text_chunker import (
    detect_needs_chunking,
    split_text_into_chunks,
    merge_toc_results,
    _deduplicate_toc_entries,
    _reconstruct_chapters,
    TextChunk
)


# ============================================================================
# Chunking Detection Tests
# ============================================================================

def test_detect_needs_chunking_small_document():
    """Test small documents don't need chunking"""
    needs_chunking = detect_needs_chunking(
        page_count=50,
        text_length=100000,
        max_pages=100
    )
    assert needs_chunking is False


def test_detect_needs_chunking_large_page_count():
    """Test large page count triggers chunking"""
    needs_chunking = detect_needs_chunking(
        page_count=150,  # > 100 max
        text_length=200000,
        max_pages=100
    )
    assert needs_chunking is True


def test_detect_needs_chunking_large_text():
    """Test large text length triggers chunking"""
    needs_chunking = detect_needs_chunking(
        page_count=80,
        text_length=2500000,  # ~625K tokens
        max_pages=100,
        max_tokens=500000
    )
    assert needs_chunking is True


# ============================================================================
# Text Splitting Tests
# ============================================================================

def test_split_text_into_chunks_simple():
    """Test splitting a 200-page document into chunks"""
    # Simulate 200 pages of text (1000 chars per page)
    text = "A" * 200000  # 200,000 chars
    page_count = 200

    chunks = split_text_into_chunks(
        text=text,
        page_count=page_count,
        max_pages=50,
        overlap_pages=5
    )

    # Should create 4 chunks (50 pages each)
    assert len(chunks) == 4

    # First chunk has no overlap
    assert chunks[0].overlap_chars == 0
    assert chunks[0].chunk_num == 0

    # Subsequent chunks have overlap
    assert chunks[1].overlap_chars > 0
    assert chunks[2].overlap_chars > 0


def test_split_text_page_ranges():
    """Test chunk page ranges are correct"""
    text = "A" * 100000  # 100,000 chars
    page_count = 100

    chunks = split_text_into_chunks(
        text=text,
        page_count=page_count,
        max_pages=50,
        overlap_pages=5
    )

    # Chunk 0: pages 1-50
    assert chunks[0].start_page == 1
    assert chunks[0].end_page == 50

    # Chunk 1: pages 46-100 (5 page overlap)
    assert chunks[1].start_page <= 50  # Overlaps with chunk 0
    assert chunks[1].end_page >= 95  # Covers rest of document


def test_split_text_empty_document():
    """Test splitting empty document returns empty list"""
    chunks = split_text_into_chunks(
        text="",
        page_count=0,
        max_pages=50
    )
    assert len(chunks) == 0


def test_split_text_small_document_no_chunks():
    """Test small document creates single chunk"""
    text = "A" * 10000  # Small document
    page_count = 10

    chunks = split_text_into_chunks(
        text=text,
        page_count=page_count,
        max_pages=50
    )

    # Should create 1 chunk
    assert len(chunks) == 1
    assert chunks[0].start_page == 1
    assert chunks[0].end_page == 10


# ============================================================================
# TOC Merging Tests
# ============================================================================

def test_merge_toc_results_simple():
    """Test merging TOC results from multiple chunks"""
    chunk_results = [
        {
            "title": "Test Document",
            "author": None,
            "language": "en",
            "confidence_score": 90,
            "toc": {
                "total_entries": 2,
                "max_depth": 1,
                "items": [
                    {"title": "Chapter 1", "level": 1, "page_number": 5, "confidence": 95, "text_sample": "", "type": "chapter"},
                    {"title": "Chapter 2", "level": 1, "page_number": 25, "confidence": 93, "text_sample": "", "type": "chapter"}
                ]
            },
            "chapters": []
        },
        {
            "title": "Test Document",
            "author": None,
            "language": "en",
            "confidence_score": 88,
            "toc": {
                "total_entries": 2,
                "max_depth": 1,
                "items": [
                    {"title": "Chapter 3", "level": 1, "page_number": 75, "confidence": 91, "text_sample": "", "type": "chapter"},
                    {"title": "Chapter 4", "level": 1, "page_number": 100, "confidence": 89, "text_sample": "", "type": "chapter"}
                ]
            },
            "chapters": []
        }
    ]

    chunks = [
        TextChunk(0, "", 1, 50, 0, 50000, 0),
        TextChunk(1, "", 51, 120, 50001, 120000, 5000)
    ]

    merged = merge_toc_results(chunk_results, chunks)

    # Should have 4 entries total
    assert merged["toc"]["total_entries"] == 4
    assert len(merged["toc"]["items"]) == 4

    # Entries should be sorted by page number
    assert merged["toc"]["items"][0]["page_number"] == 5
    assert merged["toc"]["items"][1]["page_number"] == 25
    assert merged["toc"]["items"][2]["page_number"] == 75
    assert merged["toc"]["items"][3]["page_number"] == 100


def test_merge_toc_results_with_duplicates():
    """Test deduplication of overlapping entries"""
    chunk_results = [
        {
            "title": "Test Document",
            "language": "en",
            "confidence_score": 90,
            "toc": {
                "items": [
                    {"title": "Chapter 1", "level": 1, "page_number": 5, "confidence": 95, "text_sample": "", "type": "chapter"},
                    {"title": "Section 1.1", "level": 2, "page_number": 48, "confidence": 90, "text_sample": "", "type": "section"}
                ]
            },
            "chapters": []
        },
        {
            "title": "Test Document",
            "language": "en",
            "confidence_score": 92,
            "toc": {
                "items": [
                    # Duplicate from overlap region (same title, similar page)
                    {"title": "Section 1.1", "level": 2, "page_number": 48, "confidence": 92, "text_sample": "", "type": "section"},
                    {"title": "Chapter 2", "level": 1, "page_number": 75, "confidence": 91, "text_sample": "", "type": "chapter"}
                ]
            },
            "chapters": []
        }
    ]

    chunks = [
        TextChunk(0, "", 1, 50, 0, 50000, 0),
        TextChunk(1, "", 46, 100, 45000, 100000, 5000)  # 5-page overlap
    ]

    merged = merge_toc_results(chunk_results, chunks)

    # Should deduplicate "Section 1.1" (appears twice with page 48)
    # Total unique entries: 3 (Chapter 1, Section 1.1, Chapter 2)
    assert merged["toc"]["total_entries"] == 3


def test_merge_toc_results_empty():
    """Test merging empty results"""
    merged = merge_toc_results([], [])

    assert merged["toc"]["total_entries"] == 0
    assert len(merged["toc"]["items"]) == 0
    assert merged["confidence_score"] == 0


def test_merge_toc_calculates_avg_confidence():
    """Test merged result calculates average confidence"""
    chunk_results = [
        {"confidence_score": 90, "toc": {"items": []}, "language": "en", "title": "Test", "chapters": []},
        {"confidence_score": 80, "toc": {"items": []}, "language": "en", "title": "Test", "chapters": []},
        {"confidence_score": 85, "toc": {"items": []}, "language": "en", "title": "Test", "chapters": []}
    ]
    chunks = [TextChunk(i, "", 1, 10, 0, 10000, 0) for i in range(3)]

    merged = merge_toc_results(chunk_results, chunks)

    # Average: (90 + 80 + 85) / 3 = 85
    assert merged["confidence_score"] == 85


# ============================================================================
# Deduplication Tests
# ============================================================================

def test_deduplicate_toc_entries_removes_exact_duplicates():
    """Test deduplication removes exact duplicates"""
    entries = [
        {"title": "Chapter 1", "page_number": 5, "confidence": 90, "_chunk_num": 0},
        {"title": "Chapter 1", "page_number": 5, "confidence": 85, "_chunk_num": 1},  # Duplicate
        {"title": "Chapter 2", "page_number": 20, "confidence": 88, "_chunk_num": 1}
    ]

    deduplicated = _deduplicate_toc_entries(entries)

    # Should keep higher confidence duplicate
    assert len(deduplicated) == 2
    assert deduplicated[0]["title"] == "Chapter 1"
    assert deduplicated[0]["confidence"] == 90  # Higher confidence kept


def test_deduplicate_toc_entries_similar_page_numbers():
    """Test deduplication handles similar page numbers (within 2 pages)"""
    entries = [
        {"title": "Section 1.1", "page_number": 48, "confidence": 90, "_chunk_num": 0},
        {"title": "Section 1.1", "page_number": 49, "confidence": 92, "_chunk_num": 1},  # Within 2 pages
    ]

    deduplicated = _deduplicate_toc_entries(entries)

    # Should deduplicate and keep higher confidence
    assert len(deduplicated) == 1
    assert deduplicated[0]["confidence"] == 92


def test_deduplicate_keeps_distant_same_titles():
    """Test deduplication keeps same titles if pages are far apart"""
    entries = [
        {"title": "Introduction", "page_number": 5, "confidence": 90, "_chunk_num": 0},
        {"title": "Introduction", "page_number": 100, "confidence": 88, "_chunk_num": 1},  # Different section
    ]

    deduplicated = _deduplicate_toc_entries(entries)

    # Should keep both (different sections with same name)
    assert len(deduplicated) == 2


# ============================================================================
# Chapter Reconstruction Tests
# ============================================================================

def test_reconstruct_chapters_from_toc():
    """Test chapter reconstruction from TOC entries"""
    toc_entries = [
        {"title": "Chapter 1", "level": 1, "page_number": 5, "type": "chapter"},
        {"title": "Section 1.1", "level": 2, "page_number": 6, "type": "section"},
        {"title": "Section 1.2", "level": 2, "page_number": 10, "type": "section"},
        {"title": "Chapter 2", "level": 1, "page_number": 25, "type": "chapter"},
        {"title": "Section 2.1", "level": 2, "page_number": 26, "type": "section"}
    ]

    chapters = _reconstruct_chapters(toc_entries)

    # Should create 2 chapters
    assert len(chapters) == 2

    # Chapter 1
    assert chapters[0]["chapter_num"] == 1
    assert chapters[0]["title"] == "Chapter 1"
    assert chapters[0]["start_page"] == 5
    assert chapters[0]["end_page"] == 10  # Last subsection page
    assert len(chapters[0]["subsections"]) == 2

    # Chapter 2
    assert chapters[1]["chapter_num"] == 2
    assert chapters[1]["title"] == "Chapter 2"
    assert chapters[1]["start_page"] == 25
    assert chapters[1]["end_page"] == 26
    assert len(chapters[1]["subsections"]) == 1


def test_reconstruct_chapters_empty_toc():
    """Test chapter reconstruction with empty TOC"""
    chapters = _reconstruct_chapters([])
    assert len(chapters) == 0


def test_reconstruct_chapters_no_level1():
    """Test chapter reconstruction when no level 1 entries exist"""
    toc_entries = [
        {"title": "Section 1", "level": 2, "page_number": 5, "type": "section"},
        {"title": "Section 2", "level": 2, "page_number": 10, "type": "section"}
    ]

    chapters = _reconstruct_chapters(toc_entries)

    # Should create no chapters (orphaned sections)
    assert len(chapters) == 0
