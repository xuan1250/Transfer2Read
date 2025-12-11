"""
Unit Tests for Authentication Middleware

Tests for JWT validation and user extraction from Supabase tokens.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from app.core.auth import get_current_user
from app.schemas.auth import AuthenticatedUser, SubscriptionTier


# Test constants
TEST_JWT_SECRET = "test-jwt-secret-for-unit-tests"
TEST_USER_ID = "123e4567-e89b-12d3-a456-426614174000"
TEST_EMAIL = "test@example.com"


def create_test_token(
    user_id: str = TEST_USER_ID,
    email: str = TEST_EMAIL,
    tier: str = "FREE",
    expired: bool = False
) -> str:
    """Create a test JWT token."""
    import time
    
    payload = {
        "sub": user_id,
        "email": email,
        "user_metadata": {"tier": tier},
        "aud": "authenticated",
        "exp": int(time.time()) - 3600 if expired else int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    """Test successful user extraction from valid JWT."""
    token = create_test_token()
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    
    with patch("app.core.auth.settings") as mock_settings:
        mock_settings.SUPABASE_JWT_SECRET = TEST_JWT_SECRET
        
        user = await get_current_user(credentials)
        
        assert user.user_id == TEST_USER_ID
        assert user.email == TEST_EMAIL
        assert user.tier == SubscriptionTier.FREE


@pytest.mark.asyncio
async def test_get_current_user_with_pro_tier():
    """Test user extraction with PRO tier from JWT metadata."""
    token = create_test_token(tier="PRO")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    
    with patch("app.core.auth.settings") as mock_settings:
        mock_settings.SUPABASE_JWT_SECRET = TEST_JWT_SECRET
        
        user = await get_current_user(credentials)
        
        assert user.tier == SubscriptionTier.PRO


@pytest.mark.asyncio
async def test_get_current_user_with_premium_tier():
    """Test user extraction with PREMIUM tier from JWT metadata."""
    token = create_test_token(tier="PREMIUM")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    
    with patch("app.core.auth.settings") as mock_settings:
        mock_settings.SUPABASE_JWT_SECRET = TEST_JWT_SECRET
        
        user = await get_current_user(credentials)
        
        assert user.tier == SubscriptionTier.PREMIUM


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    """Test 401 response for invalid JWT signature."""
    token = create_test_token()
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    
    with patch("app.core.auth.settings") as mock_settings:
        # Use different secret to simulate invalid signature
        mock_settings.SUPABASE_JWT_SECRET = "wrong-secret"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_expired_token():
    """Test 401 response for expired JWT."""
    token = create_test_token(expired=True)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    
    with patch("app.core.auth.settings") as mock_settings:
        mock_settings.SUPABASE_JWT_SECRET = TEST_JWT_SECRET
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_malformed_token():
    """Test 401 response for malformed JWT."""
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", 
        credentials="not-a-valid-jwt"
    )
    
    with patch("app.core.auth.settings") as mock_settings:
        mock_settings.SUPABASE_JWT_SECRET = TEST_JWT_SECRET
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_missing_user_id():
    """Test 401 response when JWT payload has no 'sub' claim."""
    import time
    
    # Create token without 'sub' claim
    payload = {
        "email": TEST_EMAIL,
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    
    with patch("app.core.auth.settings") as mock_settings:
        mock_settings.SUPABASE_JWT_SECRET = TEST_JWT_SECRET
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert "missing user ID" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_invalid_tier_defaults_to_free():
    """Test that invalid tier value defaults to FREE."""
    token = create_test_token(tier="INVALID_TIER")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    
    with patch("app.core.auth.settings") as mock_settings:
        mock_settings.SUPABASE_JWT_SECRET = TEST_JWT_SECRET
        
        user = await get_current_user(credentials)
        
        # Invalid tier should default to FREE
        assert user.tier == SubscriptionTier.FREE


@pytest.mark.asyncio
async def test_get_current_user_missing_tier_defaults_to_free():
    """Test that missing tier in user_metadata defaults to FREE."""
    import time
    
    # Create token without tier in user_metadata
    payload = {
        "sub": TEST_USER_ID,
        "email": TEST_EMAIL,
        "user_metadata": {},
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    
    with patch("app.core.auth.settings") as mock_settings:
        mock_settings.SUPABASE_JWT_SECRET = TEST_JWT_SECRET
        
        user = await get_current_user(credentials)
        
        assert user.tier == SubscriptionTier.FREE
