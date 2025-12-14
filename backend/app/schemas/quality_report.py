"""
Quality Report Pydantic Models

Defines structured schemas for quality assurance and confidence scoring.
Used to track conversion fidelity metrics and provide transparency to users.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Any


class ElementQuality(BaseModel):
    """Quality metrics for a specific element type"""

    count: int = Field(ge=0, description="Number of elements detected")
    avg_confidence: float = Field(ge=0, le=100, description="Average confidence score (0-100)")
    low_confidence_items: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Items with confidence <80% threshold"
    )


class FidelityTarget(BaseModel):
    """Fidelity target validation result"""

    target: float = Field(ge=0, le=100, description="Target fidelity percentage")
    actual: float = Field(ge=0, le=100, description="Actual achieved fidelity")
    met: bool = Field(description="Whether target was met")


class WarningItem(BaseModel):
    """Single quality warning with context"""

    severity: str = Field(description="Severity level: WARNING or CRITICAL")
    element: str = Field(description="Element type: table, equation, multi_column")
    page: int = Field(gt=0, description="Page number where issue occurs")
    confidence: float = Field(ge=0, le=100, description="Confidence score that triggered warning")
    message: str = Field(description="User-facing warning message with context")


class QualityReport(BaseModel):
    """Complete quality assurance report for conversion job"""

    overall_confidence: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Overall document confidence score (null if unavailable)"
    )
    elements: Dict[str, Any] = Field(
        default_factory=dict,
        description="Quality metrics per element type"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="User-facing warnings for low confidence elements"
    )
    fidelity_targets: Dict[str, Any] = Field(
        default_factory=dict,
        description="Fidelity target validation results"
    )

    @field_validator('overall_confidence')
    @classmethod
    def validate_overall_confidence(cls, v: Optional[float]) -> Optional[float]:
        """Ensure overall confidence is within 0-100 range"""
        if v is not None and not (0 <= v <= 100):
            raise ValueError(f"overall_confidence must be between 0 and 100, got {v}")
        return v

    @field_validator('elements')
    @classmethod
    def validate_element_confidence(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all element confidence values are within 0-100"""
        for element_type, metrics in v.items():
            if isinstance(metrics, dict) and 'avg_confidence' in metrics:
                confidence = metrics['avg_confidence']
                if not (0 <= confidence <= 100):
                    raise ValueError(
                        f"Invalid confidence for {element_type}: {confidence}. Must be 0-100."
                    )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "overall_confidence": 95.2,
                "elements": {
                    "tables": {
                        "count": 12,
                        "avg_confidence": 93.5,
                        "low_confidence_items": []
                    },
                    "images": {
                        "count": 8,
                        "avg_confidence": 100.0,
                        "low_confidence_items": []
                    },
                    "equations": {
                        "count": 5,
                        "avg_confidence": 97.0,
                        "low_confidence_items": []
                    },
                    "chapters": {
                        "count": 15,
                        "detected_toc": True
                    },
                    "multi_column_pages": {
                        "count": 3,
                        "pages": [5, 12, 18]
                    }
                },
                "warnings": [
                    "Page 45: Table detected but low confidence (72%) - complex structure may not be fully preserved. Manual review recommended."
                ],
                "fidelity_targets": {
                    "complex_elements": {
                        "target": 95,
                        "actual": 93.5,
                        "met": False
                    },
                    "text_based": {
                        "target": 99,
                        "actual": 99.1,
                        "met": True
                    }
                }
            }
        }
    )
