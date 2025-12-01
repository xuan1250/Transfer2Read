"""
Pytest configuration and fixtures for testing.

Provides shared fixtures and configuration for all tests.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    """
    Fixture providing an async HTTP client for testing FastAPI app.

    Usage:
        async def test_endpoint(client):
            response = await client.get("/api/health")
            assert response.status_code == 200
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
