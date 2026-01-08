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
    convert_to_html,
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


class TestConvertToHtml:
    """Test the convert_to_html task."""

    @patch('app.tasks.conversion_pipeline.check_cancellation')
    @patch('app.tasks.conversion_pipeline.update_job_status')
    @patch('app.tasks.conversion_pipeline.StirlingPDFClient')
    @patch('app.tasks.conversion_pipeline.SupabaseStorageService')
    @patch('app.tasks.conversion_pipeline.get_supabase_client')
    def test_convert_to_html_success(self, mock_get_supabase, mock_storage_cls, mock_stirling_cls, mock_update_status, mock_check_cancel):
        """Test convert_to_html success flow."""
        # Setup mocks
        mock_check_cancel.return_value = False
        
        # Mock Stirling Client
        mock_stirling = MagicMock()
        mock_stirling_cls.return_value = mock_stirling
        mock_stirling.convert_pdf_to_html.return_value = "<html>Content</html>"
        mock_stirling.get_version.return_value = {"version": "1.0.0"}
        
        # Mock Storage
        mock_storage = MagicMock()
        mock_storage_cls.return_value = mock_storage
        mock_storage.download_file.return_value = b"%PDF..."

        # Call task
        from app.tasks.conversion_pipeline import convert_to_html
        result = convert_to_html("test-job-id")

        # Verify status update was called
        mock_update_status.assert_called()
        call_args = mock_update_status.call_args_list[0]
        assert call_args[1]["status"] == "CONVERTING"
        # assert call_args[1]["progress"] == 20 # Initial progress

        # Verify result structure
        assert "job_id" in result
        assert result["job_id"] == "test-job-id"
        assert "html_content" in result
        assert result["html_content"] == "<html>Content</html>"
        assert "stirling_metadata" in result


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


class TestRetryBehavior:
    """Test retry configuration for transient vs permanent errors (AC #4)."""

    @patch('app.tasks.conversion_pipeline.check_cancellation')
    @patch('app.tasks.conversion_pipeline.update_job_status')
    @patch('app.tasks.conversion_pipeline.StirlingPDFClient')
    @patch('app.tasks.conversion_pipeline.SupabaseStorageService')
    @patch('app.tasks.conversion_pipeline.get_supabase_client')
    def test_transient_error_triggers_retry_httpx_timeout(
        self, mock_get_supabase, mock_storage_cls, mock_stirling_cls,
        mock_update_status, mock_check_cancel
    ):
        """Test that httpx.TimeoutException triggers automatic retry."""
        import httpx

        # Setup mocks
        mock_check_cancel.return_value = False

        # Mock Supabase
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        mock_supabase.table().select().eq().execute.return_value.data = [
            {
                "id": "test-job-id",
                "user_id": "user-123",
                "original_filename": "test.pdf"
            }
        ]

        # Mock Storage to succeed
        mock_storage = MagicMock()
        mock_storage_cls.return_value = mock_storage
        mock_storage.download_file.return_value = b"%PDF-1.4 test content"

        # Mock Stirling Client to raise TimeoutException (transient error)
        mock_stirling = MagicMock()
        mock_stirling_cls.return_value = mock_stirling
        mock_stirling.convert_pdf_to_html.side_effect = httpx.TimeoutException("Request timeout")

        # Verify the task is configured to retry TimeoutException
        task = convert_to_html
        assert httpx.TimeoutException in task.autoretry_for
        assert task.max_retries == 3
        assert task.retry_backoff is True

    @patch('app.tasks.conversion_pipeline.check_cancellation')
    @patch('app.tasks.conversion_pipeline.update_job_status')
    @patch('app.tasks.conversion_pipeline.StirlingPDFClient')
    @patch('app.tasks.conversion_pipeline.SupabaseStorageService')
    @patch('app.tasks.conversion_pipeline.get_supabase_client')
    def test_transient_error_triggers_retry_httpx_network_error(
        self, mock_get_supabase, mock_storage_cls, mock_stirling_cls,
        mock_update_status, mock_check_cancel
    ):
        """Test that httpx.NetworkError triggers automatic retry."""
        import httpx

        # Verify the task is configured to retry NetworkError
        task = convert_to_html
        assert httpx.NetworkError in task.autoretry_for
        assert httpx.HTTPError in task.autoretry_for

    @patch('app.tasks.conversion_pipeline.check_cancellation')
    @patch('app.tasks.conversion_pipeline.update_job_status')
    @patch('app.tasks.conversion_pipeline.get_supabase_client')
    def test_transient_error_triggers_retry_redis_connection_error(
        self, mock_get_supabase, mock_update_status, mock_check_cancel
    ):
        """Test that redis.exceptions.ConnectionError triggers automatic retry."""
        import redis

        # Verify the task is configured to retry Redis connection errors
        task = convert_to_html
        assert redis.exceptions.ConnectionError in task.autoretry_for

    def test_permanent_error_does_not_retry_value_error(self):
        """Test that ValueError (permanent error) does NOT trigger retry."""
        # Verify ValueError is NOT in autoretry_for
        task = convert_to_html
        assert ValueError not in task.autoretry_for
        assert Exception not in task.autoretry_for  # Ensure we're not catching all exceptions

    def test_permanent_error_does_not_retry_key_error(self):
        """Test that KeyError (permanent error) does NOT trigger retry."""
        # Verify KeyError is NOT in autoretry_for
        task = convert_to_html
        assert KeyError not in task.autoretry_for

    def test_max_retries_limit_enforced(self):
        """Test that max_retries=3 limit is configured correctly."""
        # Verify all tasks have max_retries=3
        from app.tasks.conversion_pipeline import (
            convert_to_html,
            extract_content,
            identify_structure,
            generate_epub,
            calculate_quality_score
        )

        tasks = [
            convert_to_html,
            extract_content,
            identify_structure,
            generate_epub,
            calculate_quality_score
        ]

        for task in tasks:
            assert task.max_retries == 3, f"Task {task.name} should have max_retries=3"
            assert task.retry_backoff is True, f"Task {task.name} should have retry_backoff=True"

    def test_timeout_configuration_matches_ac3(self):
        """Test that timeout configuration matches AC #3 specification (300s soft / 360s hard)."""
        from app.tasks.conversion_pipeline import (
            convert_to_html,
            extract_content,
            identify_structure,
            generate_epub,
            calculate_quality_score
        )

        tasks = [
            convert_to_html,
            extract_content,
            identify_structure,
            generate_epub,
            calculate_quality_score
        ]

        for task in tasks:
            assert task.soft_time_limit == 300, f"Task {task.name} should have soft_time_limit=300"
            assert task.time_limit == 360, f"Task {task.name} should have time_limit=360"
