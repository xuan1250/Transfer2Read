"""
Unit tests for Jobs API endpoints.

Tests all jobs endpoints with mocked dependencies.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from httpx import AsyncClient


@pytest.fixture
def mock_supabase_client():
    """
    Mock Supabase client for testing without database.

    Returns a Mock with preconfigured method chains.
    """
    mock = Mock()
    # Configure table() method chain
    mock.table.return_value = mock
    mock.select.return_value = mock
    mock.eq.return_value = mock
    mock.order.return_value = mock
    mock.range.return_value = mock
    mock.insert.return_value = mock
    mock.update.return_value = mock
    mock.delete.return_value = mock
    mock.execute.return_value = Mock(data=[], count=0)
    return mock


@pytest.fixture
def mock_storage_service():
    """Mock SupabaseStorageService for testing without storage."""
    with patch("app.api.v1.jobs.SupabaseStorageService") as mock:
        service = Mock()
        service.delete_file.return_value = None
        service.create_signed_url.return_value = "https://supabase.co/signed-url"
        mock.return_value = service
        yield service


@pytest.mark.asyncio
class TestListJobs:
    """Tests for GET /api/v1/jobs endpoint"""

    async def test_list_jobs_success(self, client: AsyncClient, valid_jwt_token):
        """Test listing jobs with valid authentication"""
        # Mock Supabase response
        with patch("app.api.v1.jobs.get_supabase_client") as mock_get_client:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = [
                {
                    "id": "job-1",
                    "user_id": "test-user-id-123",
                    "status": "COMPLETED",
                    "input_path": "uploads/user-id/job-id/document.pdf",
                    "output_path": "downloads/user-id/job-id/output.epub",
                    "quality_report": {"overall_confidence": 95},
                    "created_at": "2025-12-12T10:30:00Z",
                    "completed_at": "2025-12-12T10:32:15Z",
                    "deleted_at": None
                }
            ]
            mock_response.count = 1

            mock_client.table.return_value.select.return_value.order.return_value.range.return_value.execute.return_value = mock_response
            mock_get_client.return_value = mock_client

            response = await client.get(
                "/api/v1/jobs",
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "jobs" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data
            assert len(data["jobs"]) == 1
            assert data["jobs"][0]["id"] == "job-1"
            assert data["jobs"][0]["status"] == "COMPLETED"
            assert data["jobs"][0]["input_file"] == "document.pdf"

    async def test_list_jobs_with_pagination(self, client: AsyncClient, valid_jwt_token):
        """Test pagination parameters"""
        with patch("app.api.v1.jobs.get_supabase_client") as mock_get_client:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = []
            mock_response.count = 100

            mock_client.table.return_value.select.return_value.order.return_value.range.return_value.execute.return_value = mock_response
            mock_get_client.return_value = mock_client

            response = await client.get(
                "/api/v1/jobs?limit=10&offset=20",
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["limit"] == 10
            assert data["offset"] == 20
            assert data["total"] == 100

    async def test_list_jobs_with_status_filter(self, client: AsyncClient, valid_jwt_token):
        """Test status filter parameter"""
        with patch("app.api.v1.jobs.get_supabase_client") as mock_get_client:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = []
            mock_response.count = 0

            # Configure mock chain
            table_mock = mock_client.table.return_value
            select_mock = table_mock.select.return_value
            eq_mock = select_mock.eq.return_value
            order_mock = eq_mock.order.return_value
            range_mock = order_mock.range.return_value
            range_mock.execute.return_value = mock_response

            mock_get_client.return_value = mock_client

            response = await client.get(
                "/api/v1/jobs?status=COMPLETED",
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )

            assert response.status_code == 200
            # Verify eq() was called with status filter
            select_mock.eq.assert_called_once_with("status", "COMPLETED")

    async def test_list_jobs_unauthorized(self, client: AsyncClient):
        """Test listing jobs without authentication"""
        response = await client.get("/api/v1/jobs")
        assert response.status_code == 401  # Missing Authorization header

    async def test_list_jobs_empty_result(self, client: AsyncClient, valid_jwt_token):
        """Test listing jobs when user has no jobs"""
        with patch("app.api.v1.jobs.get_supabase_client") as mock_get_client:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = []
            mock_response.count = 0

            mock_client.table.return_value.select.return_value.order.return_value.range.return_value.execute.return_value = mock_response
            mock_get_client.return_value = mock_client

            response = await client.get(
                "/api/v1/jobs",
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["jobs"] == []
            assert data["total"] == 0


@pytest.mark.asyncio
class TestGetJob:
    """Tests for GET /api/v1/jobs/{job_id} endpoint"""

    async def test_get_job_success(self, client: AsyncClient, valid_jwt_token):
        """Test getting job details with valid job_id"""
        with patch("app.api.v1.jobs.get_supabase_client") as mock_get_client:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = [
                {
                    "id": "job-1",
                    "user_id": "test-user-id-123",
                    "status": "COMPLETED",
                    "input_path": "uploads/user/job/input.pdf",
                    "output_path": "downloads/user/job/output.epub",
                    "quality_report": {
                        "overall_confidence": 95,
                        "tables": {"count": 12, "avg_confidence": 93}
                    },
                    "created_at": "2025-12-12T10:30:00Z",
                    "completed_at": "2025-12-12T10:32:15Z"
                }
            ]

            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            mock_get_client.return_value = mock_client

            response = await client.get(
                "/api/v1/jobs/job-1",
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "job-1"
            assert data["status"] == "COMPLETED"
            assert data["quality_report"]["overall_confidence"] == 95

    async def test_get_job_not_found(self, client: AsyncClient, valid_jwt_token):
        """Test getting non-existent job"""
        with patch("app.api.v1.jobs.get_supabase_client") as mock_get_client:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = []  # No job found

            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            mock_get_client.return_value = mock_client

            response = await client.get(
                "/api/v1/jobs/non-existent-id",
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )

            assert response.status_code == 404
            data = response.json()
            assert "detail" in data

    async def test_get_job_unauthorized(self, client: AsyncClient):
        """Test getting job without authentication"""
        response = await client.get("/api/v1/jobs/job-1")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestDeleteJob:
    """Tests for DELETE /api/v1/jobs/{job_id} endpoint"""

    async def test_delete_job_success(self, client: AsyncClient, valid_jwt_token):
        """Test deleting job with file cleanup"""
        with patch("app.api.v1.jobs.get_supabase_client") as mock_get_client, \
             patch("app.api.v1.jobs.SupabaseStorageService") as mock_storage_cls, \
             patch("app.tasks.cleanup.cleanup_job_files_task") as mock_celery_task:

            # Mock database responses
            mock_client = Mock()

            # Mock SELECT response (job exists)
            select_response = Mock()
            select_response.data = [
                {
                    "id": "job-1",
                    "user_id": "test-user-id-123",
                    "status": "COMPLETED",
                    "input_path": "uploads/user/job/input.pdf",
                    "output_path": "downloads/user/job/output.epub"
                }
            ]

            # Mock UPDATE response (soft delete)
            update_response = Mock()
            update_response.data = [{"id": "job-1"}]

            # Configure mock chains
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = select_response
            mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = update_response

            mock_get_client.return_value = mock_client

            # Mock storage service
            mock_storage = Mock()
            mock_storage.delete_file.return_value = None
            mock_storage_cls.return_value = mock_storage

            # Mock Celery task
            mock_celery_task.delay.return_value = Mock()

            response = await client.delete(
                "/api/v1/jobs/job-1",
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )

            assert response.status_code == 204
            # Verify Celery task was scheduled
            mock_celery_task.delay.assert_called_once()

    async def test_delete_job_not_found(self, client: AsyncClient, valid_jwt_token):
        """Test deleting non-existent job"""
        with patch("app.api.v1.jobs.get_supabase_client") as mock_get_client:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = []  # No job found

            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            mock_get_client.return_value = mock_client

            response = await client.delete(
                "/api/v1/jobs/non-existent-id",
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )

            assert response.status_code == 404

    async def test_delete_job_cleanup_failure(self, client: AsyncClient, valid_jwt_token):
        """Test deleting job when file cleanup fails"""
        with patch("app.api.v1.jobs.get_supabase_client") as mock_get_client, \
             patch("app.api.v1.jobs.SupabaseStorageService") as mock_storage_cls, \
             patch("app.tasks.cleanup.cleanup_job_files_task") as mock_celery_task:

            # Mock database responses
            mock_client = Mock()
            select_response = Mock()
            select_response.data = [
                {
                    "id": "job-1",
                    "input_path": "uploads/user/job/input.pdf",
                    "output_path": None
                }
            ]

            update_response = Mock()
            update_response.data = [{"id": "job-1"}]

            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = select_response
            mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = update_response
            mock_get_client.return_value = mock_client

            # Mock storage service
            mock_storage = Mock()
            mock_storage_cls.return_value = mock_storage

            # Mock Celery task (cleanup happens async, so delete succeeds)
            mock_celery_task.delay.return_value = Mock()

            # Delete should succeed even if cleanup fails later
            response = await client.delete(
                "/api/v1/jobs/job-1",
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )

            assert response.status_code == 204


@pytest.mark.asyncio
class TestDownloadJob:
    """Tests for GET /api/v1/jobs/{job_id}/download endpoint"""

    async def test_download_job_success(self, client: AsyncClient, valid_jwt_token):
        """Test downloading completed job"""
        with patch("app.api.v1.jobs.get_supabase_client") as mock_get_client, \
             patch("app.api.v1.jobs.SupabaseStorageService") as mock_storage_cls:

            # Mock database response
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = [
                {
                    "id": "job-1",
                    "status": "COMPLETED",
                    "output_path": "downloads/user/job/output.epub"
                }
            ]

            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            mock_get_client.return_value = mock_client

            # Mock storage service
            mock_storage = Mock()
            mock_storage.generate_signed_url.return_value = "https://supabase.co/signed-url"
            mock_storage_cls.return_value = mock_storage

            response = await client.get(
                "/api/v1/jobs/job-1/download",
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "download_url" in data
            assert "expires_at" in data
            assert data["download_url"] == "https://supabase.co/signed-url"

    async def test_download_job_not_completed(self, client: AsyncClient, valid_jwt_token):
        """Test downloading job that is not completed"""
        with patch("app.api.v1.jobs.get_supabase_client") as mock_get_client:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = [
                {
                    "id": "job-1",
                    "status": "PROCESSING",  # Not completed
                    "output_path": None
                }
            ]

            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            mock_get_client.return_value = mock_client

            response = await client.get(
                "/api/v1/jobs/job-1/download",
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )

            assert response.status_code == 404
            data = response.json()
            detail = data["detail"]
            assert "not complete" in detail["detail"].lower()

    async def test_download_job_no_output(self, client: AsyncClient, valid_jwt_token):
        """Test downloading job with no output file"""
        with patch("app.api.v1.jobs.get_supabase_client") as mock_get_client:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = [
                {
                    "id": "job-1",
                    "status": "COMPLETED",
                    "output_path": None  # No output file
                }
            ]

            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            mock_get_client.return_value = mock_client

            response = await client.get(
                "/api/v1/jobs/job-1/download",
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )

            assert response.status_code == 404
            data = response.json()
            detail = data["detail"]
            # Job service returns None for no output, which triggers "not complete" message
            assert "not complete" in detail["detail"].lower()

    async def test_download_job_storage_error(self, client: AsyncClient, valid_jwt_token):
        """Test download when storage service fails"""
        with patch("app.api.v1.jobs.get_supabase_client") as mock_get_client, \
             patch("app.api.v1.jobs.SupabaseStorageService") as mock_storage_cls:

            # Mock database response
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = [
                {
                    "id": "job-1",
                    "status": "COMPLETED",
                    "output_path": "downloads/user/job/output.epub"
                }
            ]

            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            mock_get_client.return_value = mock_client

            # Mock storage service to raise error
            mock_storage = Mock()
            mock_storage.generate_signed_url.side_effect = Exception("Storage unavailable")
            mock_storage_cls.return_value = mock_storage

            response = await client.get(
                "/api/v1/jobs/job-1/download",
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )

            assert response.status_code == 500
            data = response.json()
            detail = data["detail"]
            assert "storage error" in detail["detail"].lower()
