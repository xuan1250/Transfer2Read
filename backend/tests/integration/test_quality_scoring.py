"""
Integration Tests for Quality Scoring in Conversion Pipeline

Tests end-to-end quality scoring integration with the full conversion pipeline.
"""

import pytest
from unittest.mock import Mock, patch
from app.tasks.conversion_pipeline import calculate_quality_score
from app.services.conversion.quality_scorer import QualityScorer


@pytest.fixture
def mock_job_id():
    """Mock job ID for testing."""
    return "test-job-12345"


@pytest.fixture
def sample_pipeline_result():
    """Sample result from previous pipeline stages."""
    return {
        "job_id": "test-job-12345",
        "page_analyses": [
            {
                "page_number": 1,
                "text_blocks": {
                    "count": 5,
                    "items": [{"text": f"Block {i}"} for i in range(5)]
                },
                "tables": {
                    "count": 1,
                    "items": [{"confidence": 93, "rows": 5, "cols": 3}]
                },
                "images": {
                    "count": 2,
                    "items": [
                        {"format": "photo", "alt_text": "Image 1"},
                        {"format": "chart", "alt_text": "Image 2"}
                    ]
                },
                "equations": {
                    "count": 1,
                    "items": [{"confidence": 97, "latex": "E = mc^2"}]
                },
                "layout": {"is_multi_column": False},
                "overall_confidence": 95
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
        ],
        "document_structure": {
            "title": "Test Document",
            "author": "Test Author",
            "language": "en",
            "toc": {
                "items": [
                    {"title": "Chapter 1", "level": 1, "page_number": 1, "confidence": 95},
                    {"title": "Chapter 2", "level": 1, "page_number": 2, "confidence": 98}
                ],
                "total_entries": 2,
                "max_depth": 1
            },
            "chapters": [
                {"chapter_num": 1, "title": "Chapter 1", "start_page": 1, "end_page": 1},
                {"chapter_num": 2, "title": "Chapter 2", "start_page": 2, "end_page": 2}
            ],
            "confidence_score": 96
        },
        "epub_metadata": {
            "file_size": 1024000,
            "chapters_count": 2
        }
    }


@pytest.mark.integration
class TestQualityScoringPipelineIntegration:
    """Test quality scoring integration with conversion pipeline."""

    @patch('app.tasks.conversion_pipeline.get_supabase_client')
    @patch('app.tasks.conversion_pipeline.check_cancellation')
    @patch('app.tasks.conversion_pipeline.cleanup_temp_files')
    def test_calculate_quality_score_task_success(
        self,
        mock_cleanup,
        mock_check_cancel,
        mock_supabase,
        sample_pipeline_result
    ):
        """Test successful quality score calculation in pipeline task."""
        # Setup mocks
        mock_check_cancel.return_value = False
        mock_supabase_instance = Mock()
        mock_supabase_instance.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
        mock_supabase.return_value = mock_supabase_instance

        # Execute task
        result = calculate_quality_score(None, sample_pipeline_result)

        # Verify quality report in result
        assert "quality_report" in result
        quality_report = result["quality_report"]

        # Verify quality report structure
        assert "overall_confidence" in quality_report
        assert "elements" in quality_report
        assert "warnings" in quality_report
        assert "fidelity_targets" in quality_report

        # Verify confidence is calculated
        assert quality_report["overall_confidence"] is not None
        assert 0 <= quality_report["overall_confidence"] <= 100

        # Verify database update was called
        assert mock_supabase_instance.table.called
        assert mock_supabase_instance.table.return_value.update.called

        # Verify cleanup was called
        assert mock_cleanup.called

    @patch('app.tasks.conversion_pipeline.get_supabase_client')
    @patch('app.tasks.conversion_pipeline.check_cancellation')
    def test_quality_scoring_with_missing_data(
        self,
        mock_check_cancel,
        mock_supabase,
        mock_job_id
    ):
        """Test quality scoring with missing page_analyses or document_structure."""
        # Setup mocks
        mock_check_cancel.return_value = False
        mock_supabase_instance = Mock()
        mock_supabase_instance.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
        mock_supabase.return_value = mock_supabase_instance

        # Pipeline result with missing data
        incomplete_result = {
            "job_id": mock_job_id,
            "page_analyses": [],  # Empty
            "document_structure": {}  # Empty
        }

        # Execute task
        result = calculate_quality_score(None, incomplete_result)

        # Should return degraded quality report
        quality_report = result["quality_report"]
        assert quality_report["overall_confidence"] is None
        assert "Insufficient data" in quality_report["warnings"][0]

    @patch('app.tasks.conversion_pipeline.get_supabase_client')
    @patch('app.tasks.conversion_pipeline.check_cancellation')
    @patch('app.tasks.conversion_pipeline.settings')
    def test_quality_scoring_disabled(
        self,
        mock_settings,
        mock_check_cancel,
        mock_supabase,
        sample_pipeline_result
    ):
        """Test that quality scoring can be disabled via settings."""
        # Setup mocks
        mock_check_cancel.return_value = False
        mock_settings.QUALITY_SCORING_ENABLED = False
        mock_supabase_instance = Mock()
        mock_supabase_instance.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
        mock_supabase.return_value = mock_supabase_instance

        # Execute task
        result = calculate_quality_score(None, sample_pipeline_result)

        # Should return disabled message
        quality_report = result["quality_report"]
        assert "Quality scoring disabled" in quality_report["warnings"]

    @patch('app.tasks.conversion_pipeline.get_supabase_client')
    @patch('app.tasks.conversion_pipeline.check_cancellation')
    def test_quality_scoring_error_graceful_degradation(
        self,
        mock_check_cancel,
        mock_supabase,
        sample_pipeline_result
    ):
        """Test graceful degradation when quality scoring fails."""
        # Setup mocks
        mock_check_cancel.return_value = False
        mock_supabase_instance = Mock()
        mock_supabase_instance.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
        mock_supabase.return_value = mock_supabase_instance

        # Corrupt the pipeline result to trigger error
        corrupted_result = {
            "job_id": "test-job-12345",
            "page_analyses": "invalid_data",  # Should be list
            "document_structure": "invalid_data"  # Should be dict
        }

        # Execute task - should not raise exception
        result = calculate_quality_score(None, corrupted_result)

        # Should return degraded quality report
        assert "quality_report" in result
        quality_report = result["quality_report"]

        # Graceful degradation: confidence should be None
        assert quality_report.get("overall_confidence") is None or quality_report.get("warnings")


@pytest.mark.integration
class TestQualityReportDatabaseStorage:
    """Test quality report storage in database."""

    @patch('app.tasks.conversion_pipeline.get_supabase_client')
    @patch('app.tasks.conversion_pipeline.check_cancellation')
    def test_quality_report_stored_in_database(
        self,
        mock_check_cancel,
        mock_supabase,
        sample_pipeline_result
    ):
        """Test that quality report is stored in conversion_jobs table."""
        # Setup mocks
        mock_check_cancel.return_value = False
        mock_supabase_instance = Mock()
        mock_update_call = Mock()
        mock_supabase_instance.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_call
        mock_supabase.return_value = mock_supabase_instance

        # Execute task
        calculate_quality_score(None, sample_pipeline_result)

        # Verify update was called with quality_report
        update_call_args = mock_supabase_instance.table.return_value.update.call_args
        assert update_call_args is not None

        # Verify quality_report was in the update
        update_data = update_call_args[0][0]
        assert "quality_report" in update_data

        # Verify quality report structure
        quality_report = update_data["quality_report"]
        assert "overall_confidence" in quality_report
        assert "elements" in quality_report
        assert "warnings" in quality_report
        assert "fidelity_targets" in quality_report


@pytest.mark.integration
class TestQualityMetricsAccuracy:
    """Test accuracy of quality metrics calculation."""

    def test_element_counts_match_input(self, sample_pipeline_result):
        """Test that element counts accurately reflect input data."""
        scorer = QualityScorer()
        layout_analysis = {"pages": sample_pipeline_result["page_analyses"]}
        document_structure = sample_pipeline_result["document_structure"]

        quality_report = scorer.generate_quality_report(layout_analysis, document_structure)

        # Verify element counts
        assert quality_report.elements["tables"]["count"] == 1
        assert quality_report.elements["images"]["count"] == 2
        assert quality_report.elements["equations"]["count"] == 1
        assert quality_report.elements["chapters"]["count"] == 2

    def test_confidence_calculation_weighted_correctly(self, sample_pipeline_result):
        """Test that confidence is weighted by element complexity."""
        scorer = QualityScorer()
        layout_analysis = {"pages": sample_pipeline_result["page_analyses"]}

        confidence = scorer.calculate_confidence(layout_analysis)

        # Page 1: 5 text blocks (99% each), 1 table (93%), 2 images (100%), 1 equation (97%)
        # Page 2: 8 text blocks (99% each)
        # Total weight = 5 + 1 + 2 + 1 + 8 = 17
        # Total score = (5*99) + 93 + (2*100) + 97 + (8*99) = 495 + 93 + 200 + 97 + 792 = 1677
        # Average = 1677 / 17 = 98.65

        # Allow small margin for rounding
        assert 98.0 <= confidence <= 99.0

    def test_fidelity_target_determination(self, sample_pipeline_result):
        """Test that correct fidelity target is applied based on document type."""
        scorer = QualityScorer()
        layout_analysis = {"pages": sample_pipeline_result["page_analyses"]}

        # Has tables and equations - should be classified as complex
        fidelity_targets = scorer.validate_fidelity_targets(
            overall_confidence=95.0,
            layout_analysis=layout_analysis
        )

        # Should target complex documents (95%+)
        assert "complex_elements" in fidelity_targets
        assert fidelity_targets["complex_elements"]["target"] == 95


@pytest.mark.integration
class TestQualityWarningsGeneration:
    """Test warning generation in realistic scenarios."""

    def test_no_warnings_for_high_quality_document(self, sample_pipeline_result):
        """Test that high-quality documents generate no warnings."""
        scorer = QualityScorer()
        layout_analysis = {"pages": sample_pipeline_result["page_analyses"]}

        warnings = scorer.generate_warnings(layout_analysis)

        # All elements have confidence >= 80%, should have no warnings
        assert len(warnings) == 0

    def test_warnings_for_low_confidence_elements(self):
        """Test warnings generated for low-confidence elements."""
        scorer = QualityScorer()

        layout_analysis = {
            "pages": [{
                "page_number": 1,
                "text_blocks": {"count": 0, "items": []},
                "tables": {
                    "count": 1,
                    "items": [{"confidence": 70, "rows": 5, "cols": 3}]  # Below 80%
                },
                "images": {"count": 0, "items": []},
                "equations": {
                    "count": 1,
                    "items": [{"confidence": 55, "latex": "complex_formula"}]  # Critical
                },
                "layout": {"is_multi_column": False},
                "overall_confidence": 65
            }]
        }

        warnings = scorer.generate_warnings(layout_analysis)

        # Should have 2 warnings (table + equation)
        assert len(warnings) >= 2

        # Should have at least one CRITICAL warning (equation < 60%)
        assert any("[CRITICAL]" in warning for warning in warnings)

        # Should have at least one WARNING (table 70%)
        assert any("[WARNING]" in warning and "Table" in warning for warning in warnings)
