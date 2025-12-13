"""
Pytest configuration and fixtures for testing.

Provides shared fixtures and configuration for all tests.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from unittest.mock import Mock
from jose import jwt
from datetime import datetime, timedelta
from app.core.config import settings


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


@pytest.fixture
def valid_jwt_token():
    """
    Generate a valid Supabase JWT token for testing.

    Returns a JWT token with:
    - user_id: test-user-id
    - email: test@example.com
    - tier: FREE
    """
    payload = {
        "sub": "test-user-id-123",
        "email": "test@example.com",
        "user_metadata": {"tier": "FREE"},
        "aud": "authenticated",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")


@pytest.fixture
def pro_tier_jwt_token():
    """Generate JWT token for PRO tier user"""
    payload = {
        "sub": "pro-user-id-456",
        "email": "pro@example.com",
        "user_metadata": {"tier": "PRO"},
        "aud": "authenticated",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")


@pytest.fixture
def expired_jwt_token():
    """Generate an expired JWT token for testing"""
    payload = {
        "sub": "test-user-id",
        "email": "test@example.com",
        "user_metadata": {"tier": "FREE"},
        "aud": "authenticated",
        "exp": datetime.utcnow() - timedelta(hours=1),  # Expired
        "iat": datetime.utcnow() - timedelta(hours=2)
    }
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")


@pytest.fixture
def valid_pdf_bytes():
    """
    Generate minimal valid PDF file bytes for testing.

    Returns a simple but valid PDF file.
    """
    return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
308
%%EOF"""


@pytest.fixture
def large_pdf_bytes(valid_pdf_bytes):
    """
    Generate a large PDF file (60MB) for testing file size limits.

    Returns a PDF that exceeds FREE tier limit (50MB).
    """
    # Pad the valid PDF to 60MB
    padding = b"0" * (60 * 1024 * 1024 - len(valid_pdf_bytes))
    return valid_pdf_bytes + padding


@pytest.fixture
def jpeg_file_bytes():
    """
    Generate minimal JPEG file bytes for testing invalid file type.

    Returns a JPEG file header (not a PDF).
    """
    # JPEG magic bytes
    return b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"

