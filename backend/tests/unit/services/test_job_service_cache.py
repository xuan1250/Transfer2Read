"""
Unit Tests for Redis Caching in JobService

Tests the Redis caching functionality for job status polling.
"""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime
import json

from app.services.job_service import JobService
from app.schemas.job import JobDetail


class TestRedisJobCaching:
    """Test Redis caching in JobService."""

    @pytest.fixture
    def mock_supabase(self):
        """Create mock Supabase client."""
        return MagicMock()

    @pytest.fixture
    def mock_storage(self):
        """Create mock storage service."""
        return MagicMock()

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis_mock = MagicMock()
        redis_mock.get.return_value = None  # Default: cache miss
        return redis_mock

    @pytest.fixture
    def job_service(self, mock_supabase, mock_storage, mock_redis):
        """Create JobService instance with mocked dependencies."""
        return JobService(mock_supabase, mock_storage, mock_redis)

    def test_get_job_cache_miss(self, job_service, mock_supabase, mock_redis):
        """Test get_job with cache miss - should fetch from database and cache result."""
        # Setup: Mock database response
        job_data = {
            "id": "test-job-id",
            "user_id": "test-user-id",
            "status": "ANALYZING",
            "input_path": "uploads/test.pdf",
            "output_path": None,
            "progress": 25,
            "stage_metadata": {"current_stage": "ANALYZING"},
            "quality_report": None,
            "created_at": "2025-12-13T10:00:00Z",
            "completed_at": None
        }
        mock_supabase.table().select().eq().execute.return_value.data = [job_data]

        # Execute
        result = job_service.get_job("test-job-id", "test-user-id")

        # Verify: Cache was checked
        mock_redis.get.assert_called_once_with("job_status:test-job-id")

        # Verify: Database was queried
        mock_supabase.table.assert_called_with("conversion_jobs")

        # Verify: Result was cached
        mock_redis.setex.assert_called_once()
        cache_call = mock_redis.setex.call_args
        assert cache_call[0][0] == "job_status:test-job-id"
        assert cache_call[0][1] == 300  # 5 minutes TTL

        # Verify: JobDetail returned correctly
        assert result.id == "test-job-id"
        assert result.status == "ANALYZING"
        assert result.progress == 25

    def test_get_job_cache_hit(self, job_service, mock_supabase, mock_redis):
        """Test get_job with cache hit - should return cached data without DB query."""
        # Setup: Mock cached data
        cached_data = {
            "id": "test-job-id",
            "user_id": "test-user-id",
            "status": "EXTRACTING",
            "input_path": "uploads/test.pdf",
            "output_path": None,
            "progress": 50,
            "stage_metadata": {"current_stage": "EXTRACTING"},
            "quality_report": None,
            "created_at": "2025-12-13T10:00:00Z",
            "completed_at": None
        }
        mock_redis.get.return_value = json.dumps(cached_data)

        # Execute
        result = job_service.get_job("test-job-id", "test-user-id")

        # Verify: Cache was checked
        mock_redis.get.assert_called_once_with("job_status:test-job-id")

        # Verify: Database was NOT queried (cache hit)
        mock_supabase.table.assert_not_called()

        # Verify: Result was NOT cached again
        mock_redis.setex.assert_not_called()

        # Verify: JobDetail returned from cache
        assert result.id == "test-job-id"
        assert result.status == "EXTRACTING"
        assert result.progress == 50

    def test_update_job_status_invalidates_cache(self, job_service, mock_supabase, mock_redis):
        """Test that update_job_status invalidates Redis cache."""
        # Setup: Mock successful update
        mock_supabase.table().update().eq().execute.return_value.data = [{"id": "test-job-id"}]

        # Execute
        result = job_service.update_job_status(
            job_id="test-job-id",
            status="COMPLETED",
            progress=100
        )

        # Verify: Update was executed
        mock_supabase.table.assert_called_with("conversion_jobs")
        assert result is True

        # Verify: Cache was invalidated
        mock_redis.delete.assert_called_once_with("job_status:test-job-id")

    def test_cache_graceful_failure(self, job_service, mock_supabase, mock_redis):
        """Test that cache failures don't break the application."""
        # Setup: Mock cache failure
        mock_redis.get.side_effect = Exception("Redis connection lost")
        mock_supabase.table().select().eq().execute.return_value.data = [{
            "id": "test-job-id",
            "user_id": "test-user-id",
            "status": "COMPLETED",
            "input_path": "uploads/test.pdf",
            "output_path": "downloads/test.epub",
            "progress": 100,
            "stage_metadata": {},
            "quality_report": None,
            "created_at": "2025-12-13T10:00:00Z",
            "completed_at": "2025-12-13T10:05:00Z"
        }]

        # Execute - should not raise exception
        result = job_service.get_job("test-job-id", "test-user-id")

        # Verify: Database was queried as fallback
        mock_supabase.table.assert_called_with("conversion_jobs")

        # Verify: JobDetail still returned
        assert result.id == "test-job-id"
        assert result.status == "COMPLETED"

    def test_no_redis_client(self, mock_supabase, mock_storage):
        """Test JobService works without Redis client (caching disabled)."""
        # Create service without Redis
        service = JobService(mock_supabase, mock_storage, redis_client=None)

        # Setup: Mock database response
        mock_supabase.table().select().eq().execute.return_value.data = [{
            "id": "test-job-id",
            "user_id": "test-user-id",
            "status": "ANALYZING",
            "input_path": "uploads/test.pdf",
            "output_path": None,
            "progress": 25,
            "stage_metadata": {},
            "quality_report": None,
            "created_at": "2025-12-13T10:00:00Z",
            "completed_at": None
        }]

        # Execute - should work without caching
        result = service.get_job("test-job-id", "test-user-id")

        # Verify: Database was queried
        mock_supabase.table.assert_called_with("conversion_jobs")

        # Verify: JobDetail returned
        assert result.id == "test-job-id"
        assert result.status == "ANALYZING"
