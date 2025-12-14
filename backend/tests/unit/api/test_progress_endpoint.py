"""
Unit tests for progress endpoint (GET /jobs/{job_id}/progress).

Tests the real-time progress updates endpoint for polling-based conversion status.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from app.schemas.job import JobDetail
from app.schemas.progress import ProgressUpdate, ElementsDetected
from app.schemas.quality_report import QualityReport


@pytest.mark.asyncio
async def test_get_job_progress_success(client, valid_jwt_token):
    """Test successful progress retrieval for PROCESSING job."""
    job_id = "test-job-123"

    # Mock job data with progress metadata
    mock_job = Mock(spec=JobDetail)
    mock_job.id = job_id
    mock_job.status = "PROCESSING"
    mock_job.progress = 50
    mock_job.stage_metadata = {
        "current_stage": "layout_analysis",
        "stage_description": "Analyzing layout...",
        "elements_detected": {
            "tables": 12,
            "images": 8,
            "equations": 5,
            "chapters": 0
        },
        "estimated_time_remaining": 45,
        "estimated_cost": 0.12,
        "timestamp": datetime.utcnow()
    }
    mock_job.quality_report = {
        "overall_confidence": 94,
        "estimated_cost": 0.12
    }

    with patch('app.api.v1.jobs.JobService') as MockJobService:
        mock_service = MockJobService.return_value
        mock_service.get_job.return_value = mock_job

        response = await client.get(
            f"/api/v1/jobs/{job_id}/progress",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert data["job_id"] == job_id
    assert data["status"] == "PROCESSING"
    assert data["progress_percentage"] == 50
    assert data["current_stage"] == "layout_analysis"
    assert data["stage_description"] == "Analyzing layout..."

    # Verify elements detected
    assert data["elements_detected"]["tables"] == 12
    assert data["elements_detected"]["images"] == 8
    assert data["elements_detected"]["equations"] == 5
    assert data["elements_detected"]["chapters"] == 0

    # Verify optional fields
    assert data["estimated_time_remaining"] == 45
    assert data["estimated_cost"] == 0.12
    assert data["quality_confidence"] == 94
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_get_job_progress_queued(client, valid_jwt_token):
    """Test progress for QUEUED job (minimal metadata)."""
    job_id = "queued-job-456"

    mock_job = Mock(spec=JobDetail)
    mock_job.id = job_id
    mock_job.status = "QUEUED"
    mock_job.progress = 0
    mock_job.stage_metadata = None  # No progress metadata yet
    mock_job.quality_report = None

    with patch('app.api.v1.jobs.JobService') as MockJobService:
        mock_service = MockJobService.return_value
        mock_service.get_job.return_value = mock_job

        response = await client.get(
            f"/api/v1/jobs/{job_id}/progress",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

    assert response.status_code == 200
    data = response.json()

    assert data["job_id"] == job_id
    assert data["status"] == "QUEUED"
    assert data["progress_percentage"] == 0
    assert data["current_stage"] == "queued"
    assert data["stage_description"] == "Waiting to start..."
    assert data["elements_detected"]["tables"] == 0
    assert data["elements_detected"]["images"] == 0


@pytest.mark.asyncio
async def test_get_job_progress_completed(client, valid_jwt_token):
    """Test progress for COMPLETED job with quality report."""
    job_id = "completed-job-789"

    mock_job = Mock(spec=JobDetail)
    mock_job.id = job_id
    mock_job.status = "COMPLETED"
    mock_job.progress = 100
    mock_job.stage_metadata = {
        "current_stage": "completed",
        "stage_description": "Conversion complete!",
        "timestamp": datetime.utcnow()
    }
    mock_job.quality_report = {
        "overall_confidence": 98,
        "estimated_cost": 0.25,
        "elements": {
            "tables": {"count": 15},
            "images": {"count": 10},
            "equations": {"count": 8},
            "chapters": {"count": 12}
        }
    }

    with patch('app.api.v1.jobs.JobService') as MockJobService:
        mock_service = MockJobService.return_value
        mock_service.get_job.return_value = mock_job

        response = await client.get(
            f"/api/v1/jobs/{job_id}/progress",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

    assert response.status_code == 200
    data = response.json()

    assert data["job_id"] == job_id
    assert data["status"] == "COMPLETED"
    assert data["progress_percentage"] == 100
    assert data["quality_confidence"] == 98
    assert data["estimated_cost"] == 0.25

    # Elements should fallback to quality report
    assert data["elements_detected"]["tables"] == 15
    assert data["elements_detected"]["images"] == 10
    assert data["elements_detected"]["equations"] == 8
    assert data["elements_detected"]["chapters"] == 12


@pytest.mark.asyncio
async def test_get_job_progress_not_found(client, valid_jwt_token):
    """Test 404 when job doesn't exist or user doesn't own it."""
    job_id = "nonexistent-job"

    with patch('app.api.v1.jobs.JobService') as MockJobService:
        mock_service = MockJobService.return_value
        mock_service.get_job.return_value = None  # Job not found

        response = await client.get(
            f"/api/v1/jobs/{job_id}/progress",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"]["detail"].lower()


@pytest.mark.asyncio
async def test_get_job_progress_unauthorized(client):
    """Test 401 when JWT token is missing."""
    job_id = "test-job-123"

    response = await client.get(f"/api/v1/jobs/{job_id}/progress")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_job_progress_failed_job(client, valid_jwt_token):
    """Test progress for FAILED job shows error state."""
    job_id = "failed-job-999"

    mock_job = Mock(spec=JobDetail)
    mock_job.id = job_id
    mock_job.status = "FAILED"
    mock_job.progress = 50
    mock_job.stage_metadata = {
        "current_stage": "failed",
        "stage_description": "Conversion failed",
        "timestamp": datetime.utcnow()
    }
    mock_job.quality_report = None

    with patch('app.api.v1.jobs.JobService') as MockJobService:
        mock_service = MockJobService.return_value
        mock_service.get_job.return_value = mock_job

        response = await client.get(
            f"/api/v1/jobs/{job_id}/progress",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

    assert response.status_code == 200
    data = response.json()

    assert data["job_id"] == job_id
    assert data["status"] == "FAILED"
    assert data["current_stage"] == "failed"


@pytest.mark.asyncio
async def test_get_job_progress_cost_priority(client, valid_jwt_token):
    """Test that stage_metadata cost takes priority over quality_report cost."""
    job_id = "cost-priority-job"

    mock_job = Mock(spec=JobDetail)
    mock_job.id = job_id
    mock_job.status = "PROCESSING"
    mock_job.progress = 75
    mock_job.stage_metadata = {
        "current_stage": "structure_analysis",
        "stage_description": "Generating structure...",
        "estimated_cost": 0.15,  # This should take priority
        "timestamp": datetime.utcnow()
    }
    mock_job.quality_report = {
        "estimated_cost": 0.10  # This should be overridden
    }

    with patch('app.api.v1.jobs.JobService') as MockJobService:
        mock_service = MockJobService.return_value
        mock_service.get_job.return_value = mock_job

        response = await client.get(
            f"/api/v1/jobs/{job_id}/progress",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

    assert response.status_code == 200
    data = response.json()

    # Should use stage_metadata cost, not quality_report cost
    assert data["estimated_cost"] == 0.15


@pytest.mark.asyncio
async def test_get_job_progress_minimal_data(client, valid_jwt_token):
    """Test progress endpoint with absolute minimal job data."""
    job_id = "minimal-job"

    mock_job = Mock(spec=JobDetail)
    mock_job.id = job_id
    mock_job.status = "QUEUED"  # Use valid status
    mock_job.progress = 5
    mock_job.stage_metadata = {}  # Empty metadata
    mock_job.quality_report = None

    with patch('app.api.v1.jobs.JobService') as MockJobService:
        mock_service = MockJobService.return_value
        mock_service.get_job.return_value = mock_job

        response = await client.get(
            f"/api/v1/jobs/{job_id}/progress",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

    assert response.status_code == 200
    data = response.json()

    # Should have sensible defaults
    assert data["job_id"] == job_id
    assert data["status"] == "QUEUED"
    assert data["progress_percentage"] == 5
    assert data["current_stage"] == "queued"
    assert data["elements_detected"]["tables"] == 0
    assert data["estimated_cost"] is None
    assert data["quality_confidence"] is None
