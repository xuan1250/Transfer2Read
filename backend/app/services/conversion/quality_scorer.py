"""
Quality Scorer Service

Calculates quality confidence scores from AI analysis results.
Provides transparency metrics for conversion fidelity.
"""

import logging
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.schemas.quality_report import QualityReport

logger = logging.getLogger(__name__)


class QualityScorer:
    """
    Calculate and track conversion quality metrics.

    Aggregates AI confidence scores from layout and structure analysis
    to provide users with transparency about conversion fidelity.
    """

    def __init__(
        self,
        warning_threshold: int = None,
        target_complex: int = None,
        target_text: int = None,
        text_base_confidence: int = None
    ):
        """
        Initialize quality scorer with configurable thresholds.

        Args:
            warning_threshold: Confidence below this triggers warnings (default: 80)
            target_complex: Fidelity target for complex PDFs (default: 95)
            target_text: Fidelity target for text-based PDFs (default: 99)
            text_base_confidence: Base confidence for text blocks (default: 99)
        """
        self.warning_threshold = warning_threshold or settings.QUALITY_WARNING_THRESHOLD
        self.target_complex = target_complex or settings.QUALITY_TARGET_COMPLEX
        self.target_text = target_text or settings.QUALITY_TARGET_TEXT
        self.text_base_confidence = text_base_confidence or settings.QUALITY_TEXT_BASE_CONFIDENCE

    def calculate_confidence(self, layout_analysis: Dict[str, Any]) -> float:
        """
        Calculate overall document confidence as weighted average.

        Weights by element complexity:
        - Text blocks: 99% base confidence (high-quality OCR)
        - Tables: AI confidence (varies 50-100%)
        - Images: 100% (preserved as-is, no transformation)
        - Equations: AI confidence (varies 60-100%)
        - Multi-column: AI confidence on reflow (70-95%)

        Args:
            layout_analysis: Dict with page analysis results containing elements

        Returns:
            Overall confidence score (0-100)
        """
        total_score = 0.0
        total_weight = 0

        # Aggregate across all pages
        pages = layout_analysis.get("pages", [])

        for page in pages:
            # Text blocks (assume 99% baseline)
            text_blocks = page.get("text_blocks", {}).get("items", [])
            total_score += len(text_blocks) * self.text_base_confidence
            total_weight += len(text_blocks)

            # Tables (use AI confidence)
            tables = page.get("tables", {}).get("items", [])
            for table in tables:
                confidence = table.get("confidence", 0)
                total_score += confidence
                total_weight += 1

            # Images (100% - no analysis needed, just preservation)
            images = page.get("images", {}).get("items", [])
            total_score += len(images) * 100
            total_weight += len(images)

            # Equations (use AI confidence)
            equations = page.get("equations", {}).get("items", [])
            for equation in equations:
                confidence = equation.get("confidence", 0)
                total_score += confidence
                total_weight += 1

            # Multi-column layout (use overall page confidence)
            layout = page.get("layout", {})
            if layout.get("is_multi_column", False):
                # Use overall_confidence from page analysis as proxy
                page_confidence = page.get("overall_confidence", 85)
                total_score += page_confidence
                total_weight += 1

        # Calculate weighted average
        if total_weight == 0:
            logger.warning("No elements found for confidence calculation, returning default 99%")
            return 99.0  # Default for empty documents (pure text assumed)

        overall_confidence = total_score / total_weight
        return round(overall_confidence, 2)

    def count_detected_elements(
        self,
        layout_analysis: Dict[str, Any],
        document_structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Count all detected elements across document.

        Args:
            layout_analysis: Layout analysis results with element detections
            document_structure: Document structure with TOC and chapters

        Returns:
            Dict with element counts and metadata
        """
        element_counts = {
            "tables": {"count": 0, "avg_confidence": 0.0, "low_confidence_items": []},
            "images": {"count": 0, "avg_confidence": 100.0, "low_confidence_items": []},
            "equations": {"count": 0, "avg_confidence": 0.0, "low_confidence_items": []},
            "text_blocks": {"count": 0, "avg_confidence": self.text_base_confidence},
            "chapters": {"count": 0, "detected_toc": False},
            "multi_column_pages": {"count": 0, "pages": []}
        }

        pages = layout_analysis.get("pages", [])

        # Aggregate tables
        all_tables = []
        for page in pages:
            tables = page.get("tables", {}).get("items", [])
            for table in tables:
                all_tables.append(table.get("confidence", 0))
                if table.get("confidence", 0) < self.warning_threshold:
                    element_counts["tables"]["low_confidence_items"].append({
                        "page": page.get("page_number"),
                        "confidence": table.get("confidence", 0)
                    })

        element_counts["tables"]["count"] = len(all_tables)
        if all_tables:
            element_counts["tables"]["avg_confidence"] = round(sum(all_tables) / len(all_tables), 2)

        # Aggregate equations
        all_equations = []
        for page in pages:
            equations = page.get("equations", {}).get("items", [])
            for equation in equations:
                all_equations.append(equation.get("confidence", 0))
                if equation.get("confidence", 0) < self.warning_threshold:
                    element_counts["equations"]["low_confidence_items"].append({
                        "page": page.get("page_number"),
                        "confidence": equation.get("confidence", 0)
                    })

        element_counts["equations"]["count"] = len(all_equations)
        if all_equations:
            element_counts["equations"]["avg_confidence"] = round(sum(all_equations) / len(all_equations), 2)

        # Count images
        total_images = sum(
            page.get("images", {}).get("count", 0) for page in pages
        )
        element_counts["images"]["count"] = total_images

        # Count text blocks
        total_text_blocks = sum(
            page.get("text_blocks", {}).get("count", 0) for page in pages
        )
        element_counts["text_blocks"]["count"] = total_text_blocks

        # Count multi-column pages
        multi_column_pages = []
        for page in pages:
            layout = page.get("layout", {})
            if layout.get("is_multi_column", False):
                multi_column_pages.append(page.get("page_number"))

        element_counts["multi_column_pages"]["count"] = len(multi_column_pages)
        element_counts["multi_column_pages"]["pages"] = multi_column_pages

        # Extract chapter counts from document structure
        chapters = document_structure.get("chapters", [])
        element_counts["chapters"]["count"] = len(chapters)

        toc = document_structure.get("toc", {})
        element_counts["chapters"]["detected_toc"] = toc.get("total_entries", 0) > 0

        return element_counts

    def generate_warnings(
        self,
        layout_analysis: Dict[str, Any],
        threshold: Optional[float] = None
    ) -> List[str]:
        """
        Generate user-facing warnings for low-confidence elements.

        Thresholds:
        - Below 80%: Warning with manual review recommendation
        - Below 60%: Critical warning - strong recommendation for review

        Args:
            layout_analysis: Layout analysis results
            threshold: Confidence threshold (default: self.warning_threshold)

        Returns:
            List of warning messages
        """
        if threshold is None:
            threshold = self.warning_threshold

        warnings = []
        pages = layout_analysis.get("pages", [])

        for page in pages:
            page_num = page.get("page_number", 0)

            # Check tables
            tables = page.get("tables", {}).get("items", [])
            for table in tables:
                confidence = table.get("confidence", 0)
                if confidence < threshold:
                    severity = "CRITICAL" if confidence < 60 else "WARNING"
                    warnings.append(
                        f"[{severity}] Page {page_num}: Table detected but low confidence "
                        f"({confidence:.0f}%) - complex structure may not be fully preserved. "
                        f"Manual review recommended."
                    )

            # Check equations
            equations = page.get("equations", {}).get("items", [])
            for equation in equations:
                confidence = equation.get("confidence", 0)
                if confidence < threshold:
                    severity = "CRITICAL" if confidence < 60 else "WARNING"
                    warnings.append(
                        f"[{severity}] Equation on page {page_num}: Low confidence "
                        f"({confidence:.0f}%) - unusual notation detected. "
                        f"Verify accuracy in final EPUB."
                    )

            # Check multi-column layouts
            layout = page.get("layout", {})
            if layout.get("is_multi_column", False):
                page_confidence = page.get("overall_confidence", 100)
                if page_confidence < threshold:
                    warnings.append(
                        f"[WARNING] Page {page_num}: Multi-column layout with low confidence "
                        f"({page_confidence:.0f}%) - reading order may need verification."
                    )

        return warnings

    def validate_fidelity_targets(
        self,
        overall_confidence: float,
        layout_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate actual confidence against PRD fidelity targets.

        Targets (from PRD):
        - Complex PDFs (with tables/equations): 95%+ fidelity (FR24)
        - Text-based PDFs: 99%+ fidelity (FR25)

        Args:
            overall_confidence: Calculated overall confidence score
            layout_analysis: Layout analysis to determine document type

        Returns:
            Dict with target validation results
        """
        fidelity_targets = {}

        # Determine document complexity
        pages = layout_analysis.get("pages", [])
        has_complex_elements = False

        for page in pages:
            tables_count = page.get("tables", {}).get("count", 0)
            equations_count = page.get("equations", {}).get("count", 0)
            if tables_count > 0 or equations_count > 0:
                has_complex_elements = True
                break

        if has_complex_elements:
            # Complex document: target 95%+
            fidelity_targets["complex_elements"] = {
                "target": self.target_complex,
                "actual": overall_confidence,
                "met": overall_confidence >= self.target_complex
            }
        else:
            # Text-based document: target 99%+
            fidelity_targets["text_based"] = {
                "target": self.target_text,
                "actual": overall_confidence,
                "met": overall_confidence >= self.target_text
            }

        return fidelity_targets

    def generate_quality_report(
        self,
        layout_analysis: Dict[str, Any],
        document_structure: Dict[str, Any]
    ) -> QualityReport:
        """
        Generate complete quality report for conversion job.

        This is the main entry point that orchestrates all quality calculations.

        Args:
            layout_analysis: Layout analysis results from AI
            document_structure: Document structure from AI

        Returns:
            Complete QualityReport model
        """
        try:
            # Calculate overall confidence
            overall_confidence = self.calculate_confidence(layout_analysis)

            # Count detected elements
            element_counts = self.count_detected_elements(layout_analysis, document_structure)

            # Generate warnings
            warnings = self.generate_warnings(layout_analysis)

            # Validate fidelity targets
            fidelity_targets = self.validate_fidelity_targets(overall_confidence, layout_analysis)

            # Build quality report
            quality_report = QualityReport(
                overall_confidence=overall_confidence,
                elements=element_counts,
                warnings=warnings,
                fidelity_targets=fidelity_targets
            )

            logger.info(
                f"Quality report generated: {overall_confidence:.1f}% confidence, "
                f"{len(warnings)} warnings"
            )

            return quality_report

        except Exception as e:
            logger.error(f"Quality report generation failed: {str(e)}", exc_info=True)
            # Return degraded report
            return QualityReport(
                overall_confidence=None,
                elements={},
                warnings=["Quality scoring unavailable due to error"],
                fidelity_targets={}
            )
