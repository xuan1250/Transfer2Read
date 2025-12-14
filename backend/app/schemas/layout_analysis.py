"""
Layout Analysis Pydantic Models

Defines structured output schemas for AI-powered PDF layout analysis.
Used with LangChain's .with_structured_output() for strict JSON validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class TableItem(BaseModel):
    """Single table detection with bounding box and structure"""

    bbox: List[int] = Field(
        ..., description="Bounding box [x1, y1, x2, y2] in pixels", min_length=4, max_length=4
    )
    rows: int = Field(..., gt=0, description="Number of table rows")
    cols: int = Field(..., gt=0, description="Number of table columns")
    confidence: int = Field(..., ge=0, le=100, description="Confidence score 0-100")
    header_detected: bool = Field(..., description="Whether table header was detected")
    content_sample: str = Field(..., description="Sample content from table")


class Tables(BaseModel):
    """All tables detected on a page"""

    count: int = Field(..., ge=0, description="Number of tables detected")
    items: List[TableItem] = Field(default_factory=list, description="List of detected tables")


class ImageItem(BaseModel):
    """Single image/diagram detection"""

    bbox: List[int] = Field(
        ..., description="Bounding box [x1, y1, x2, y2] in pixels", min_length=4, max_length=4
    )
    format: Literal["photo", "diagram", "chart"] = Field(
        ..., description="Image format type"
    )
    alt_text: str = Field(..., description="AI-generated alt text description")


class Images(BaseModel):
    """All images detected on a page"""

    count: int = Field(..., ge=0, description="Number of images detected")
    items: List[ImageItem] = Field(default_factory=list, description="List of detected images")


class EquationItem(BaseModel):
    """Single equation detection"""

    latex: str = Field(..., description="LaTeX representation of equation")
    confidence: int = Field(..., ge=0, le=100, description="Confidence score 0-100")
    position: Literal["inline", "block"] = Field(..., description="Equation position type")


class Equations(BaseModel):
    """All equations detected on a page"""

    count: int = Field(..., ge=0, description="Number of equations detected")
    items: List[EquationItem] = Field(
        default_factory=list, description="List of detected equations"
    )


class TextBlock(BaseModel):
    """Single text block detection with paragraph-level segmentation"""

    bbox: List[int] = Field(
        ..., description="Bounding box [x1, y1, x2, y2] in pixels", min_length=4, max_length=4
    )
    text: str = Field(..., description="Text content of the block")
    font_size_hint: Optional[int] = Field(
        None, description="Estimated font size in points (if detectable)"
    )


class TextBlocks(BaseModel):
    """All text blocks detected on a page"""

    count: int = Field(..., ge=0, description="Number of text blocks detected")
    items: List[TextBlock] = Field(default_factory=list, description="List of detected text blocks")


class Layout(BaseModel):
    """Page layout structure"""

    is_multi_column: bool = Field(..., description="Whether page has multiple columns")
    column_count: Optional[int] = Field(None, description="Number of columns if multi-column")
    reflow_strategy: str = Field(..., description="Recommended reflow strategy")


class HeaderFooter(BaseModel):
    """Header or footer detection"""

    position: Literal["header", "footer"] = Field(..., description="Position type")
    text: str = Field(..., description="Header/footer text content")
    page_num: int = Field(..., gt=0, description="Page number")


class TokenUsage(BaseModel):
    """Token usage for cost tracking"""

    prompt: int = Field(..., ge=0, description="Prompt tokens used")
    completion: int = Field(..., ge=0, description="Completion tokens used")


class AnalysisMetadata(BaseModel):
    """Analysis execution metadata"""

    model_used: Literal["gpt-4o", "claude-3-5-haiku-20241022"] = Field(
        ..., description="AI model used"
    )
    response_time_ms: int = Field(..., ge=0, description="Response time in milliseconds")
    tokens_used: TokenUsage = Field(..., description="Token usage details")


class LayoutDetection(BaseModel):
    """Complete layout detection for a single PDF page"""

    page_number: int = Field(..., gt=0, description="PDF page number (1-indexed)")
    tables: Tables = Field(..., description="Detected tables with nested items")
    images: Images = Field(..., description="Detected images with nested items")
    equations: Equations = Field(..., description="Detected equations with nested items")
    text_blocks: TextBlocks = Field(..., description="Detected text blocks with paragraph segmentation")
    layout: Layout = Field(..., description="Page layout structure")
    headers_footers: List[HeaderFooter] = Field(
        default_factory=list, description="Detected headers and footers"
    )
    primary_language: str = Field(
        ..., description="Primary language (ISO 639-1 code)", min_length=2, max_length=3
    )
    secondary_languages: List[str] = Field(
        default_factory=list, description="Secondary languages detected"
    )
    overall_confidence: int = Field(
        ..., ge=0, le=100, description="Overall analysis confidence 0-100"
    )
    analysis_metadata: AnalysisMetadata = Field(..., description="Analysis execution metadata")


# Alias for clarity in batch processing
PageAnalysis = LayoutDetection
