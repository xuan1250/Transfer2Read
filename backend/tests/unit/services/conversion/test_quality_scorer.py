"""
Unit Tests for Quality Scorer Service

Tests confidence calculation, element counting, warning generation, and fidelity validation.
"""

import pytest
from app.services.conversion.quality_scorer import QualityScorer
from app.schemas.quality_report import QualityReport


@pytest.fixture
def quality_scorer():
    """Create QualityScorer instance with default settings."""
    return QualityScorer()


@pytest.fixture
def sample_layout_analysis_simple():
    """Sample layout analysis for simple text-only document."""
    return {
        "pages": [
            {
                "page_number": 1,
                "text_blocks": {
                    "count": 10,
                    "items": [{"text": f"Block {i}"} for i in range(10)]
                },
                "tables": {"count": 0, "items": []},
                "images": {"count": 0, "items": []},
                "equations": {"count": 0, "items": []},
                "layout": {"is_multi_column": False},
                "overall_confidence": 99
            },
            {
                "page_number": 2,
                "text_blocks": {
                    "count": 8,
                    "items": [{"text": f"Block {i}"} for i in range(8)]
                },
                "tables": {"count": 0, "items": []},
                "images": {"count": 0, "items": []},
                "equations": {"count": 0, "items": []},
                "layout": {"is_multi_column": False},
                "overall_confidence": 99
            }
        ]
    }


@pytest.fixture
def sample_layout_analysis_complex():
    """Sample layout analysis for complex document with tables and equations."""
    return {
        "pages": [
            {
                "page_number": 1,
                "text_blocks": {
                    "count": 5,
                    "items": [{"text": f"Block {i}"} for i in range(5)]
                },
                "tables": {
                    "count": 2,
                    "items": [
                        {"confidence": 95, "rows": 5, "cols": 3},
                        {"confidence": 72, "rows": 8, "cols": 4}  # Low confidence
                    ]
                },
                "images": {
                    "count": 1,
                    "items": [{"format": "photo", "alt_text": "Sample image"}]
                },
                "equations": {
                    "count": 1,
                    "items": [{"confidence": 88, "latex": "E = mc^2"}]
                },
                "layout": {"is_multi_column": False},
                "overall_confidence": 90
            },
            {
                "page_number": 2,
                "text_blocks": {
                    "count": 3,
                    "items": [{"text": f"Block {i}"} for i in range(3)]
                },
                "tables": {"count": 0, "items": []},
                "images": {"count": 0, "items": []},
                "equations": {
                    "count": 1,
                    "items": [{"confidence": 65, "latex": "\\int_0^1 x^2 dx"}]  # Low confidence
                },
                "layout": {"is_multi_column": True},  # Multi-column page
                "overall_confidence": 85
            }
        ]
    }


@pytest.fixture
def sample_document_structure():
    """Sample document structure with TOC and chapters."""
    return {
        "title": "Sample Document",
        "author": "Test Author",
        "language": "en",
        "toc": {
            "items": [
                {"title": "Chapter 1", "level": 1, "page_number": 1},
                {"title": "Section 1.1", "level": 2, "page_number": 2},
                {"title": "Chapter 2", "level": 1, "page_number": 5}
            ],
            "total_entries": 3,
            "max_depth": 2
        },
        "chapters": [
            {"chapter_num": 1, "title": "Chapter 1", "start_page": 1, "end_page": 4},
            {"chapter_num": 2, "title": "Chapter 2", "start_page": 5, "end_page": 10}
        ],
        "confidence_score": 92
    }


class TestConfidenceCalculation:
    """Test overall confidence score calculation."""

    def test_simple_text_document(self, quality_scorer, sample_layout_analysis_simple):
        """Test confidence for text-only document (should be ~99%)."""
        confidence = quality_scorer.calculate_confidence(sample_layout_analysis_simple)

        assert isinstance(confidence, float)
        assert 98.0 <= confidence <= 100.0  # Should be close to 99%

    def test_complex_document_with_mixed_elements(self, quality_scorer, sample_layout_analysis_complex):
        """Test confidence for document with tables, images, equations."""
        confidence = quality_scorer.calculate_confidence(sample_layout_analysis_complex)

        assert isinstance(confidence, float)
        assert 80.0 <= confidence <= 100.0
        # Should be weighted average considering low-confidence elements

    def test_empty_document(self, quality_scorer):
        """Test confidence for empty document (no pages)."""
        layout_analysis = {"pages": []}
        confidence = quality_scorer.calculate_confidence(layout_analysis)

        assert confidence == 99.0  # Default for empty documents

    def test_confidence_range_validation(self, quality_scorer, sample_layout_analysis_complex):
        """Ensure confidence is always within 0-100 range."""
        confidence = quality_scorer.calculate_confidence(sample_layout_analysis_complex)

        assert 0 <= confidence <= 100


class TestElementCounting:
    """Test element detection and counting."""

    def test_count_tables_and_equations(self, quality_scorer, sample_layout_analysis_complex, sample_document_structure):
        """Test counting of tables and equations."""
        element_counts = quality_scorer.count_detected_elements(
            sample_layout_analysis_complex,
            sample_document_structure
        )

        assert element_counts["tables"]["count"] == 2
        assert element_counts["equations"]["count"] == 2
        assert element_counts["images"]["count"] == 1

        # Check average confidences
        # Tables: (95 + 72) / 2 = 83.5
        assert element_counts["tables"]["avg_confidence"] == 83.5
        # Equations: (88 + 65) / 2 = 76.5
        assert element_counts["equations"]["avg_confidence"] == 76.5

    def test_count_chapters_from_structure(self, quality_scorer, sample_layout_analysis_simple, sample_document_structure):
        """Test chapter counting from document structure."""
        element_counts = quality_scorer.count_detected_elements(
            sample_layout_analysis_simple,
            sample_document_structure
        )

        assert element_counts["chapters"]["count"] == 2
        assert element_counts["chapters"]["detected_toc"] is True

    def test_count_multi_column_pages(self, quality_scorer, sample_layout_analysis_complex, sample_document_structure):
        """Test multi-column page detection."""
        element_counts = quality_scorer.count_detected_elements(
            sample_layout_analysis_complex,
            sample_document_structure
        )

        assert element_counts["multi_column_pages"]["count"] == 1
        assert 2 in element_counts["multi_column_pages"]["pages"]

    def test_low_confidence_items_tracking(self, quality_scorer, sample_layout_analysis_complex, sample_document_structure):
        """Test that low-confidence items are tracked."""
        element_counts = quality_scorer.count_detected_elements(
            sample_layout_analysis_complex,
            sample_document_structure
        )

        # Table with 72% confidence should be in low_confidence_items
        assert len(element_counts["tables"]["low_confidence_items"]) == 1
        assert element_counts["tables"]["low_confidence_items"][0]["confidence"] == 72

        # Equation with 65% confidence should be in low_confidence_items
        assert len(element_counts["equations"]["low_confidence_items"]) == 1
        assert element_counts["equations"]["low_confidence_items"][0]["confidence"] == 65


class TestWarningGeneration:
    """Test quality warning generation for low confidence elements."""

    def test_warning_for_low_confidence_table(self, quality_scorer, sample_layout_analysis_complex):
        """Test warning generation for table with <80% confidence."""
        warnings = quality_scorer.generate_warnings(sample_layout_analysis_complex)

        # Should have warning for table with 72% confidence
        assert len(warnings) > 0
        assert any("Table" in warning and "72" in warning for warning in warnings)

    def test_warning_for_low_confidence_equation(self, quality_scorer, sample_layout_analysis_complex):
        """Test warning generation for equation with <80% confidence."""
        warnings = quality_scorer.generate_warnings(sample_layout_analysis_complex)

        # Should have warning for equation with 65% confidence
        assert any("Equation" in warning and "65" in warning for warning in warnings)

    def test_critical_warning_for_very_low_confidence(self, quality_scorer):
        """Test critical warning for confidence <60%."""
        layout_analysis = {
            "pages": [{
                "page_number": 1,
                "text_blocks": {"count": 0, "items": []},
                "tables": {
                    "count": 1,
                    "items": [{"confidence": 50, "rows": 3, "cols": 3}]  # Critical
                },
                "images": {"count": 0, "items": []},
                "equations": {"count": 0, "items": []},
                "layout": {"is_multi_column": False},
                "overall_confidence": 50
            }]
        }

        warnings = quality_scorer.generate_warnings(layout_analysis)

        # Should have CRITICAL warning for 50% confidence
        assert any("[CRITICAL]" in warning for warning in warnings)

    def test_no_warnings_for_high_confidence(self, quality_scorer, sample_layout_analysis_simple):
        """Test that no warnings are generated for high-confidence document."""
        warnings = quality_scorer.generate_warnings(sample_layout_analysis_simple)

        assert len(warnings) == 0

    def test_custom_warning_threshold(self, quality_scorer, sample_layout_analysis_complex):
        """Test warning generation with custom threshold."""
        # Use 90% threshold - should trigger more warnings
        warnings = quality_scorer.generate_warnings(sample_layout_analysis_complex, threshold=90)

        # Should have warnings for elements below 90%
        assert len(warnings) > 2  # More warnings with higher threshold


class TestFidelityTargetValidation:
    """Test fidelity target validation against PRD requirements."""

    def test_complex_document_target_met(self, quality_scorer):
        """Test complex document meeting 95%+ fidelity target."""
        layout_analysis = {
            "pages": [{
                "page_number": 1,
                "text_blocks": {"count": 5, "items": []},
                "tables": {
                    "count": 1,
                    "items": [{"confidence": 96, "rows": 3, "cols": 3}]
                },
                "images": {"count": 0, "items": []},
                "equations": {"count": 0, "items": []},
                "layout": {"is_multi_column": False},
                "overall_confidence": 96
            }]
        }

        fidelity_targets = quality_scorer.validate_fidelity_targets(
            overall_confidence=96.0,
            layout_analysis=layout_analysis
        )

        assert "complex_elements" in fidelity_targets
        assert fidelity_targets["complex_elements"]["target"] == 95
        assert fidelity_targets["complex_elements"]["actual"] == 96.0
        assert fidelity_targets["complex_elements"]["met"] is True

    def test_complex_document_target_not_met(self, quality_scorer):
        """Test complex document failing to meet 95% target."""
        layout_analysis = {
            "pages": [{
                "page_number": 1,
                "text_blocks": {"count": 5, "items": []},
                "tables": {
                    "count": 1,
                    "items": [{"confidence": 85, "rows": 3, "cols": 3}]
                },
                "images": {"count": 0, "items": []},
                "equations": {"count": 0, "items": []},
                "layout": {"is_multi_column": False},
                "overall_confidence": 90
            }]
        }

        fidelity_targets = quality_scorer.validate_fidelity_targets(
            overall_confidence=90.0,
            layout_analysis=layout_analysis
        )

        assert fidelity_targets["complex_elements"]["met"] is False

    def test_text_only_document_target(self, quality_scorer, sample_layout_analysis_simple):
        """Test text-only document against 99%+ target."""
        fidelity_targets = quality_scorer.validate_fidelity_targets(
            overall_confidence=99.0,
            layout_analysis=sample_layout_analysis_simple
        )

        assert "text_based" in fidelity_targets
        assert fidelity_targets["text_based"]["target"] == 99
        assert fidelity_targets["text_based"]["met"] is True

    def test_edge_case_exactly_at_target(self, quality_scorer):
        """Test document with confidence exactly at target threshold."""
        layout_analysis = {
            "pages": [{
                "page_number": 1,
                "text_blocks": {"count": 5, "items": []},
                "tables": {
                    "count": 1,
                    "items": [{"confidence": 95, "rows": 3, "cols": 3}]
                },
                "images": {"count": 0, "items": []},
                "equations": {"count": 0, "items": []},
                "layout": {"is_multi_column": False},
                "overall_confidence": 95
            }]
        }

        fidelity_targets = quality_scorer.validate_fidelity_targets(
            overall_confidence=95.0,
            layout_analysis=layout_analysis
        )

        # Exactly 95% should meet target (>=)
        assert fidelity_targets["complex_elements"]["met"] is True


class TestQualityReportGeneration:
    """Test complete quality report generation."""

    def test_generate_complete_report(self, quality_scorer, sample_layout_analysis_complex, sample_document_structure):
        """Test full quality report generation."""
        quality_report = quality_scorer.generate_quality_report(
            sample_layout_analysis_complex,
            sample_document_structure
        )

        # Verify it's a QualityReport instance
        assert isinstance(quality_report, QualityReport)

        # Verify all sections present
        assert quality_report.overall_confidence is not None
        assert isinstance(quality_report.elements, dict)
        assert isinstance(quality_report.warnings, list)
        assert isinstance(quality_report.fidelity_targets, dict)

        # Verify element counts
        assert quality_report.elements["tables"]["count"] == 2
        assert quality_report.elements["chapters"]["count"] == 2

        # Verify warnings generated for low-confidence elements
        assert len(quality_report.warnings) > 0

    def test_report_schema_validation(self, quality_scorer, sample_layout_analysis_complex, sample_document_structure):
        """Test that generated report passes Pydantic validation."""
        quality_report = quality_scorer.generate_quality_report(
            sample_layout_analysis_complex,
            sample_document_structure
        )

        # Convert to dict and back to validate schema
        report_dict = quality_report.model_dump()
        validated_report = QualityReport(**report_dict)

        assert validated_report.overall_confidence == quality_report.overall_confidence

    def test_graceful_degradation_on_error(self, quality_scorer):
        """Test that report generation handles invalid data gracefully."""
        # Pass invalid data - should handle gracefully, not crash
        invalid_layout = {"invalid": "data"}
        invalid_structure = {"invalid": "data"}

        # Should not raise exception - graceful handling
        quality_report = quality_scorer.generate_quality_report(
            invalid_layout,
            invalid_structure
        )

        # Should return a valid report even with invalid input
        # (QualityScorer handles missing keys gracefully)
        assert quality_report.overall_confidence is not None or len(quality_report.warnings) > 0


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_missing_pages_array(self, quality_scorer, sample_document_structure):
        """Test handling of layout analysis without pages array."""
        layout_analysis = {}  # Missing 'pages' key

        confidence = quality_scorer.calculate_confidence(layout_analysis)

        # Should return default confidence
        assert confidence == 99.0

    def test_missing_document_structure(self, quality_scorer, sample_layout_analysis_complex):
        """Test handling of missing document structure."""
        empty_structure = {"chapters": [], "toc": {"total_entries": 0}}

        element_counts = quality_scorer.count_detected_elements(
            sample_layout_analysis_complex,
            empty_structure
        )

        # Should handle gracefully
        assert element_counts["chapters"]["count"] == 0
        assert element_counts["chapters"]["detected_toc"] is False

    def test_confidence_bounds_validation(self, quality_scorer):
        """Test that confidence values are always bounded 0-100."""
        # Even with extreme values in input, output should be bounded
        layout_analysis = {
            "pages": [{
                "page_number": 1,
                "text_blocks": {"count": 1, "items": [{"text": "test"}]},
                "tables": {"count": 0, "items": []},
                "images": {"count": 0, "items": []},
                "equations": {"count": 0, "items": []},
                "layout": {"is_multi_column": False},
                "overall_confidence": 150  # Invalid value
            }]
        }

        confidence = quality_scorer.calculate_confidence(layout_analysis)

        assert 0 <= confidence <= 100
