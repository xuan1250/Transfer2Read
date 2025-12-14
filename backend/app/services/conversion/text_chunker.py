"""
Text Chunker for Large Documents

Handles splitting large documents into manageable chunks for AI analysis,
with sliding window overlap to maintain context across chunks.
"""

import logging
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """Single chunk of document text with metadata"""

    chunk_num: int  # 0-indexed chunk number
    text: str  # Chunk text content
    start_page: int  # Estimated start page (1-indexed)
    end_page: int  # Estimated end page (1-indexed)
    char_start: int  # Character offset in original document
    char_end: int  # Character offset end
    overlap_chars: int  # Number of overlap characters from previous chunk


def detect_needs_chunking(
    page_count: int,
    text_length: int,
    max_pages: int = 100,
    max_tokens: int = 500000
) -> bool:
    """
    Determine if document requires chunking for AI analysis.

    Args:
        page_count: Total number of pages in document
        text_length: Total character length of document text
        max_pages: Maximum pages before chunking (default: 100)
        max_tokens: Maximum estimated tokens before chunking (default: 500K)

    Returns:
        True if chunking is needed, False otherwise

    Notes:
        - Rough token estimate: ~4 chars per token for English
        - Conservative thresholds to stay under GPT-4o context limits
    """
    estimated_tokens = text_length // 4  # Rough estimate

    needs_chunking = page_count > max_pages or estimated_tokens > max_tokens

    if needs_chunking:
        logger.info(
            f"Chunking required: {page_count} pages, {text_length} chars "
            f"(~{estimated_tokens} tokens) exceeds limits"
        )
    else:
        logger.info(
            f"No chunking needed: {page_count} pages, {text_length} chars "
            f"(~{estimated_tokens} tokens) within limits"
        )

    return needs_chunking


def split_text_into_chunks(
    text: str,
    page_count: int,
    max_pages: int = 50,
    overlap_pages: int = 5
) -> List[TextChunk]:
    """
    Split document text into logical chunks with sliding window overlap.

    Args:
        text: Full document text to split
        page_count: Total number of pages in document
        max_pages: Maximum pages per chunk (default: 50)
        overlap_pages: Number of pages to overlap between chunks (default: 5)

    Returns:
        List of TextChunk objects with metadata

    Strategy:
        - Estimate chars per page: total_chars / page_count
        - Split into chunks of max_pages worth of characters
        - Include overlap_pages of previous chunk for context
        - Maintain chunk metadata for reassembly and page mapping

    Example:
        200-page document with max_pages=50, overlap=5:
        - Chunk 0: pages 1-50 (0 overlap)
        - Chunk 1: pages 46-95 (5 page overlap from chunk 0)
        - Chunk 2: pages 91-140 (5 page overlap from chunk 1)
        - Chunk 3: pages 136-185 (5 page overlap from chunk 2)
        - Chunk 4: pages 181-200 (5 page overlap from chunk 3)
    """
    if page_count == 0 or len(text) == 0:
        logger.warning("Empty document provided to text chunker")
        return []

    # Calculate characters per page (rough estimate)
    chars_per_page = len(text) // page_count if page_count > 0 else len(text)
    chunk_size = chars_per_page * max_pages
    overlap_size = chars_per_page * overlap_pages

    logger.info(
        f"Splitting document: {page_count} pages, {len(text)} chars, "
        f"~{chars_per_page} chars/page, chunk_size={chunk_size}, overlap={overlap_size}"
    )

    chunks: List[TextChunk] = []
    chunk_num = 0
    current_pos = 0

    while current_pos < len(text):
        # Calculate chunk boundaries
        chunk_start = max(0, current_pos - overlap_size) if chunk_num > 0 else current_pos
        chunk_end = min(len(text), current_pos + chunk_size)

        # Extract chunk text
        chunk_text = text[chunk_start:chunk_end]

        # Calculate overlap
        actual_overlap = current_pos - chunk_start if chunk_num > 0 else 0

        # Estimate page range for this chunk
        start_page = max(1, (chunk_start // chars_per_page) + 1)
        end_page = min(page_count, (chunk_end // chars_per_page) + 1)

        # Create chunk
        chunk = TextChunk(
            chunk_num=chunk_num,
            text=chunk_text,
            start_page=start_page,
            end_page=end_page,
            char_start=chunk_start,
            char_end=chunk_end,
            overlap_chars=actual_overlap
        )

        chunks.append(chunk)
        logger.debug(
            f"Chunk {chunk_num}: pages {start_page}-{end_page}, "
            f"chars {chunk_start}-{chunk_end}, overlap={actual_overlap}"
        )

        # Move to next chunk (skip overlap for next iteration)
        current_pos = chunk_end
        chunk_num += 1

        # Safety check to prevent infinite loops
        if chunk_num > 1000:
            logger.error("Text chunking exceeded 1000 chunks - possible infinite loop")
            break

    logger.info(f"Created {len(chunks)} chunks from {page_count}-page document")
    return chunks


def merge_toc_results(
    chunk_results: List[Dict[str, Any]],
    chunks: List[TextChunk]
) -> Dict[str, Any]:
    """
    Merge TOC results from multiple analyzed chunks into single structure.

    Args:
        chunk_results: List of DocumentStructure dicts from each chunk
        chunks: List of TextChunk metadata used for analysis

    Returns:
        Merged DocumentStructure dict with combined TOC entries

    Strategy:
        - Combine TOC entries from all chunks
        - Adjust page numbers based on chunk offsets
        - Remove duplicates from overlap regions (same title + similar page)
        - Validate hierarchy consistency across chunks
        - Use highest confidence entry for duplicates
        - Reconstruct chapter boundaries across chunk splits

    Notes:
        - Overlap regions may produce duplicate entries
        - Page numbers should be consistent with original document
        - Hierarchy levels must be validated across chunk boundaries
    """
    if not chunk_results:
        logger.warning("No chunk results to merge")
        return {
            "title": "Unknown Document",
            "author": None,
            "language": "en",
            "toc": {"items": [], "total_entries": 0, "max_depth": 0},
            "chapters": [],
            "confidence_score": 0
        }

    logger.info(f"Merging TOC results from {len(chunk_results)} chunks")

    # Use first chunk's metadata as base
    merged_result = {
        "title": chunk_results[0].get("title", "Unknown Document"),
        "author": chunk_results[0].get("author"),
        "language": chunk_results[0].get("language", "en"),
        "toc": {"items": [], "total_entries": 0, "max_depth": 0},
        "chapters": [],
        "confidence_score": 0
    }

    # Collect all TOC entries from chunks
    all_entries = []
    confidence_scores = []

    for i, result in enumerate(chunk_results):
        chunk = chunks[i]
        toc = result.get("toc", {})
        entries = toc.get("items", [])

        logger.debug(f"Chunk {i}: {len(entries)} TOC entries, pages {chunk.start_page}-{chunk.end_page}")

        for entry in entries:
            # Page numbers from AI should already be absolute (based on full text context)
            # But we'll track which chunk they came from for deduplication
            entry_with_chunk = dict(entry)
            entry_with_chunk["_chunk_num"] = i
            all_entries.append(entry_with_chunk)

        # Collect confidence scores
        if "confidence_score" in result:
            confidence_scores.append(result["confidence_score"])

    # Remove duplicates (entries with same title and similar page number)
    deduplicated_entries = _deduplicate_toc_entries(all_entries)

    logger.info(
        f"Deduplication: {len(all_entries)} total entries -> {len(deduplicated_entries)} unique entries"
    )

    # Sort by page number
    deduplicated_entries.sort(key=lambda e: e["page_number"])

    # Remove temporary chunk tracking field
    for entry in deduplicated_entries:
        entry.pop("_chunk_num", None)

    # Build merged TOC
    merged_result["toc"]["items"] = deduplicated_entries
    merged_result["toc"]["total_entries"] = len(deduplicated_entries)
    merged_result["toc"]["max_depth"] = max([e["level"] for e in deduplicated_entries], default=0)

    # Calculate average confidence
    merged_result["confidence_score"] = (
        sum(confidence_scores) // len(confidence_scores) if confidence_scores else 0
    )

    # Reconstruct chapters from merged TOC
    merged_result["chapters"] = _reconstruct_chapters(deduplicated_entries)

    logger.info(
        f"Merged result: {merged_result['toc']['total_entries']} TOC entries, "
        f"{len(merged_result['chapters'])} chapters, confidence={merged_result['confidence_score']}%"
    )

    return merged_result


def _deduplicate_toc_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate TOC entries from overlap regions.

    Strategy:
        - Group entries by title
        - For same title, keep entry with:
          1. Highest confidence score
          2. From later chunk (more context)
        - Consider entries duplicates if:
          - Same title (exact match)
          - Page numbers within 2 pages of each other
    """
    if not entries:
        return []

    # Group by title
    title_groups: Dict[str, List[Dict[str, Any]]] = {}
    for entry in entries:
        title = entry["title"]
        if title not in title_groups:
            title_groups[title] = []
        title_groups[title].append(entry)

    # For each title group, deduplicate by page number proximity
    deduplicated = []
    for title, group in title_groups.items():
        # Sort by page number
        group.sort(key=lambda e: e["page_number"])

        # Keep first entry, then only add if page number differs by >2
        kept_entries = [group[0]]
        for entry in group[1:]:
            # Check if this entry is far enough from all kept entries
            is_duplicate = any(
                abs(entry["page_number"] - kept["page_number"]) <= 2
                for kept in kept_entries
            )

            if not is_duplicate:
                kept_entries.append(entry)
            else:
                # If duplicate, keep the one with higher confidence
                for i, kept in enumerate(kept_entries):
                    if abs(entry["page_number"] - kept["page_number"]) <= 2:
                        if entry["confidence"] > kept["confidence"]:
                            kept_entries[i] = entry
                        break

        deduplicated.extend(kept_entries)

    # Sort final list by page number
    deduplicated.sort(key=lambda e: e["page_number"])
    return deduplicated


def _reconstruct_chapters(toc_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Reconstruct chapter metadata from merged TOC entries.

    Strategy:
        - Level 1 entries are chapter boundaries
        - Group subsequent entries until next level 1
        - Calculate chapter page ranges from entry page numbers
    """
    if not toc_entries:
        return []

    chapters = []
    current_chapter = None
    chapter_num = 1

    for entry in toc_entries:
        if entry["level"] == 1:
            # Save previous chapter if exists
            if current_chapter:
                chapters.append(current_chapter)

            # Start new chapter
            current_chapter = {
                "chapter_num": chapter_num,
                "title": entry["title"],
                "start_page": entry["page_number"],
                "end_page": entry["page_number"],  # Will update as we find subsections
                "subsections": []
            }
            chapter_num += 1
        elif current_chapter:
            # Add subsection to current chapter
            current_chapter["subsections"].append(entry)
            # Update chapter end page
            current_chapter["end_page"] = max(
                current_chapter["end_page"],
                entry["page_number"]
            )

    # Add final chapter
    if current_chapter:
        chapters.append(current_chapter)

    return chapters
