"""
Unit Tests for Conversion Pipeline Tasks

Tests the conversion pipeline orchestration logic with mocked dependencies.
"""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime

from app.tasks.conversion_pipeline import (
    update_job_status,
    check_cancellation,
    cleanup_temp_files,
    analyze_layout,
    extract_content,
    identify_structure,
    generate_epub,
    calculate_quality_score,
    TaskCancelled
)


class TestUpdateJobStatus:
    """Test the update_job_status helper function."""

    @patch('app.tasks.conversion_pipeline.get_supabase_client')
    def test_update_job_status_success(self, mock_get_supabase):
        """Test successful job status update."""
        # Setup mock
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        mock_supabase.table().update().eq().execute.return_value = None

        # Call function
        job_id = "test-job-id"
        status = "ANALYZING"
        progress = 25
        stage_metadata = {"current_stage": "ANALYZING"}

        update_job_status(job_id, status, progress, stage_metadata)

        # Verify Supabase client was called correctly
        mock_supabase.table.assert_called_once_with("conversion_jobs")
        mock_supabase.table().update.assert_called_once()

    @patch('app.tasks.conversion_pipeline.get_supabase_client')
    def test_update_job_status_completed(self, mock_get_supabase):
        """Test that completed_at is set when status is COMPLETED."""
        # Setup mock
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase

        # Call function
        update_job_status("job-id", "COMPLETED", progress=100)

        # Verify update includes completed_at
        update_call = mock_supabase.table().update.call_args
        update_data = update_call[0][0]
        assert "completed_at" in update_data
        assert update_data["status"] == "COMPLETED"
        assert update_data["progress"] == 100


class TestCheckCancellation:
    """Test the check_cancellation helper function."""

    @patch('app.tasks.conversion_pipeline.get_supabase_client')
    def test_check_cancellation_not_cancelled(self, mock_get_supabase):
        """Test that job not cancelled returns False."""
        # Setup mock - job exists with deleted_at = None
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        mock_supabase.table().select().eq().execute.return_value.data = [
            {"deleted_at": None}
        ]

        # Call function
        result = check_cancellation("job-id")

        # Verify result
        assert result is False

    @patch('app.tasks.conversion_pipeline.get_supabase_client')
    def test_check_cancellation_is_cancelled(self, mock_get_supabase):
        """Test that cancelled job raises TaskCancelled exception."""
        # Setup mock - job exists with deleted_at set
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        mock_supabase.table().select().eq().execute.return_value.data = [
            {"deleted_at": "2025-12-12T10:30:00Z"}
        ]

        # Call function and expect exception
        with pytest.raises(TaskCancelled):
            check_cancellation("job-id")


class TestAnalyzeLayout:
    """Test the analyze_layout task."""

    @patch('app.tasks.conversion_pipeline.check_cancellation')
    @patch('app.tasks.conversion_pipeline.update_job_status')
    def test_analyze_layout_placeholder(self, mock_update_status, mock_check_cancel):
        """Test analyze_layout placeholder implementation."""
        # Setup mocks
        mock_check_cancel.return_value = False

        # Call task
        result = analyze_layout("test-job-id")

        # Verify status update was called
        mock_update_status.assert_called_once()
        call_args = mock_update_status.call_args
        assert call_args[1]["status"] == "ANALYZING"
        assert call_args[1]["progress"] == 25

        # Verify result structure
        assert "job_id" in result
        assert result["job_id"] == "test-job-id"
        assert "layout_analysis" in result


class TestExtractContent:
    """Test the extract_content task."""

    @patch('app.tasks.conversion_pipeline.check_cancellation')
    @patch('app.tasks.conversion_pipeline.update_job_status')
    def test_extract_content_placeholder(self, mock_update_status, mock_check_cancel):
        """Test extract_content placeholder implementation."""
        # Setup mocks
        mock_check_cancel.return_value = False
        previous_result = {
            "job_id": "test-job-id",
            "layout_analysis": {"placeholder": True}
        }

        # Call task
        result = extract_content(previous_result)

        # Verify status update was called
        mock_update_status.assert_called_once()
        call_args = mock_update_status.call_args
        assert call_args[1]["status"] == "EXTRACTING"
        assert call_args[1]["progress"] == 50

        # Verify result structure
        assert "job_id" in result
        assert "extracted_content" in result
        assert result["layout_analysis"] == previous_result["layout_analysis"]


class TestIdentifyStructure:
    """Test the identify_structure task."""

    @patch('app.tasks.conversion_pipeline.check_cancellation')
    @patch('app.tasks.conversion_pipeline.update_job_status')
    def test_identify_structure_placeholder(self, mock_update_status, mock_check_cancel):
        """Test identify_structure placeholder implementation."""
        # Setup mocks
        mock_check_cancel.return_value = False
        previous_result = {
            "job_id": "test-job-id",
            "layout_analysis": {},
            "extracted_content": {}
        }

        # Call task
        result = identify_structure(previous_result)

        # Verify status update was called
        mock_update_status.assert_called_once()
        call_args = mock_update_status.call_args
        assert call_args[1]["status"] == "STRUCTURING"
        assert call_args[1]["progress"] == 75

        # Verify result structure
        assert "structure" in result


class TestGenerateEpub:
    """Test the generate_epub task."""

    @patch('app.tasks.conversion_pipeline.check_cancellation')
    @patch('app.tasks.conversion_pipeline.update_job_status')
    def test_generate_epub_placeholder(self, mock_update_status, mock_check_cancel):
        """Test generate_epub placeholder implementation."""
        # Setup mocks
        mock_check_cancel.return_value = False
        previous_result = {
            "job_id": "test-job-id",
            "layout_analysis": {},
            "extracted_content": {},
            "structure": {}
        }

        # Call task
        result = generate_epub(previous_result)

        # Verify status update was called
        mock_update_status.assert_called_once()
        call_args = mock_update_status.call_args
        assert call_args[1]["status"] == "GENERATING"
        assert call_args[1]["progress"] == 90

        # Verify result structure
        assert "epub_path" in result


class TestCalculateQualityScore:
    """Test the calculate_quality_score task."""

    @patch('app.tasks.conversion_pipeline.cleanup_temp_files')
    @patch('app.tasks.conversion_pipeline.check_cancellation')
    @patch('app.tasks.conversion_pipeline.update_job_status')
    def test_calculate_quality_score_placeholder(self, mock_update_status, mock_check_cancel, mock_cleanup):
        """Test calculate_quality_score placeholder implementation."""
        # Setup mocks
        mock_check_cancel.return_value = False
        previous_result = {
            "job_id": "test-job-id",
            "layout_analysis": {},
            "extracted_content": {},
            "structure": {},
            "epub_path": "/tmp/test.epub"
        }

        # Call task
        result = calculate_quality_score(previous_result)

        # Verify status update was called with COMPLETED
        mock_update_status.assert_called_once()
        call_args = mock_update_status.call_args
        assert call_args[1]["status"] == "COMPLETED"
        assert call_args[1]["progress"] == 100

        # Verify cleanup was called
        mock_cleanup.assert_called_once_with("test-job-id")

        # Verify result structure
        assert "quality_report" in result
