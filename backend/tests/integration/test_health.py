"""
Integration Tests for Health Check Endpoint

Tests the /api/health endpoint to verify:
- API responds with proper status codes
- Supabase connection is verified
- Redis connection is verified
- Response format is correct
"""
import pytest
# Client fixture is provided by conftest.py


@pytest.mark.asyncio
async def test_health_endpoint_success(client):
    """
    Test health endpoint returns 200 when all services available.

    AC#6: Health check endpoint returns 200 OK with Supabase and Redis status
    """
    response = await client.get("/api/health")

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "status" in data
    assert "database" in data
    assert "redis" in data
    assert "timestamp" in data

    # Verify all services are connected
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["redis"] == "connected"


@pytest.mark.asyncio
async def test_health_endpoint_response_format(client):
    """
    Test health endpoint returns properly formatted JSON response.

    Verifies ISO8601 timestamp format and correct field types.
    """
    response = await client.get("/api/health")

    data = response.json()

    # Verify field types
    assert isinstance(data["status"], str)
    assert isinstance(data["database"], str)
    assert isinstance(data["redis"], str)
    assert isinstance(data["timestamp"], str)

    # Verify timestamp format (ISO8601 with Z suffix)
    assert data["timestamp"].endswith("Z")
    assert "T" in data["timestamp"]
