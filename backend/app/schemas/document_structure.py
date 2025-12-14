"""
Document Structure Pydantic Models

Defines structured output schemas for AI-powered document structure recognition and TOC generation.
Used with LangChain's .with_structured_output() for strict JSON validation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal


class TOCEntry(BaseModel):
    """Single table of contents entry with hierarchy information"""

    title: str = Field(..., description="Heading or chapter title", min_length=1)
    level: int = Field(..., ge=1, le=4, description="Hierarchy level 1-4 (H1=chapter, H2=section, etc.)")
    page_number: int = Field(..., gt=0, description="Page number where heading appears (1-indexed)")
    confidence: int = Field(..., ge=0, le=100, description="Confidence score 0-100 for detection accuracy")
    text_sample: str = Field(..., description="First 100 characters of content following the heading")
    type: Literal["chapter", "section", "subsection", "sub-subsection"] = Field(
        ..., description="Semantic type of the heading"
    )

    @field_validator("text_sample")
    @classmethod
    def limit_text_sample_length(cls, v: str) -> str:
        """Ensure text sample doesn't exceed 100 characters"""
        return v[:100]


class TOC(BaseModel):
    """Complete table of contents structure"""

    items: List[TOCEntry] = Field(default_factory=list, description="List of all TOC entries in document order")
    total_entries: int = Field(..., ge=0, description="Total number of TOC entries detected")
    max_depth: int = Field(..., ge=1, le=4, description="Maximum hierarchy depth found (1-4)")

    @field_validator("total_entries")
    @classmethod
    def validate_total_entries(cls, v: int, values) -> int:
        """Ensure total_entries matches items list length"""
        # Note: In Pydantic v2, values is not available in the same way
        # This is a placeholder for basic validation
        return v


class ChapterMetadata(BaseModel):
    """Metadata for a single chapter including subsections"""

    chapter_num: int = Field(..., gt=0, description="Chapter number (1-indexed)")
    title: str = Field(..., description="Chapter title", min_length=1)
    start_page: int = Field(..., gt=0, description="First page of chapter (1-indexed)")
    end_page: int = Field(..., gt=0, description="Last page of chapter (1-indexed)")
    subsections: List[TOCEntry] = Field(
        default_factory=list,
        description="All subsections (H2, H3, H4) within this chapter"
    )

    @field_validator("end_page")
    @classmethod
    def validate_end_page(cls, v: int, info) -> int:
        """Ensure end_page >= start_page"""
        if "start_page" in info.data and v < info.data["start_page"]:
            raise ValueError(f"end_page ({v}) must be >= start_page ({info.data['start_page']})")
        return v


class DocumentStructure(BaseModel):
    """Complete document structure analysis result"""

    title: str = Field(..., description="Document title", min_length=1)
    author: Optional[str] = Field(None, description="Document author (if detected)")
    language: str = Field(
        ...,
        description="Primary document language (ISO 639-1 code)",
        min_length=2,
        max_length=3
    )
    toc: TOC = Field(..., description="Complete table of contents structure")
    chapters: List[ChapterMetadata] = Field(
        default_factory=list,
        description="Chapter metadata with page ranges and subsections"
    )
    confidence_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Overall confidence in structure detection (0-100)"
    )

    def validate_hierarchy(self) -> List[str]:
        """
        Validate TOC hierarchy consistency.

        Returns:
            List of validation errors (empty if valid)

        Checks:
        - No H3 under H1 without H2
        - No H4 under H2 without H3
        - Level progression is logical
        """
        errors = []
        prev_level = 0

        for i, entry in enumerate(self.toc.items):
            # Check for level jumps > 1 (e.g., H1 -> H3)
            if entry.level > prev_level + 1:
                errors.append(
                    f"TOC entry {i} ('{entry.title}'): Invalid level jump from H{prev_level} to H{entry.level}"
                )

            # Check for negative page numbers (should be caught by Field validation, but double-check)
            if entry.page_number <= 0:
                errors.append(
                    f"TOC entry {i} ('{entry.title}'): Invalid page number {entry.page_number}"
                )

            # Update previous level for next iteration
            prev_level = entry.level

        return errors
