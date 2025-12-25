"""
Unit Tests for Admin Dependency

Tests the require_superuser dependency for admin route protection.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException

from app.dependencies.admin import require_superuser
from app.schemas.auth import AuthenticatedUser, SubscriptionTier


@pytest.mark.asyncio
async def test_require_superuser_with_superuser():
    """Test that superuser can access protected routes"""
    # Mock user
    mock_user = AuthenticatedUser(
        user_id="test-user-id",
        email="admin@test.com",
        tier=SubscriptionTier.FREE
    )

    # Mock Supabase response
    mock_supabase_user = MagicMock()
    mock_supabase_user.user_metadata = {'is_superuser': True}

    mock_response = MagicMock()
    mock_response.user = mock_supabase_user

    # Create mock Supabase client
    mock_supabase = MagicMock()
    mock_supabase.auth.admin.get_user_by_id.return_value = mock_response

    # Call dependency with both parameters
    result = await require_superuser(mock_user, mock_supabase)

    # Assertions
    assert result == mock_user
    mock_supabase.auth.admin.get_user_by_id.assert_called_once_with(mock_user.user_id)


@pytest.mark.asyncio
async def test_require_superuser_without_superuser():
    """Test that non-superuser is denied access"""
    # Mock user
    mock_user = AuthenticatedUser(
        user_id="test-user-id",
        email="user@test.com",
        tier=SubscriptionTier.FREE
    )

    # Mock Supabase response (no is_superuser flag)
    mock_supabase_user = MagicMock()
    mock_supabase_user.user_metadata = {}

    mock_response = MagicMock()
    mock_response.user = mock_supabase_user

    # Create mock Supabase client
    mock_supabase = MagicMock()
    mock_supabase.auth.admin.get_user_by_id.return_value = mock_response

    # Call dependency - should raise 403
    with pytest.raises(HTTPException) as exc_info:
        await require_superuser(mock_user, mock_supabase)

    # Assertions
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Admin access required"


@pytest.mark.asyncio
async def test_require_superuser_with_false_flag():
    """Test that user with is_superuser=false is denied"""
    # Mock user
    mock_user = AuthenticatedUser(
        user_id="test-user-id",
        email="user@test.com",
        tier=SubscriptionTier.PRO
    )

    # Mock Supabase response with explicit false
    mock_supabase_user = MagicMock()
    mock_supabase_user.user_metadata = {'is_superuser': False}

    mock_response = MagicMock()
    mock_response.user = mock_supabase_user

    # Create mock Supabase client
    mock_supabase = MagicMock()
    mock_supabase.auth.admin.get_user_by_id.return_value = mock_response

    # Call dependency - should raise 403
    with pytest.raises(HTTPException) as exc_info:
        await require_superuser(mock_user, mock_supabase)

    # Assertions
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Admin access required"


@pytest.mark.asyncio
async def test_require_superuser_user_not_found():
    """Test that missing user is denied access"""
    # Mock user
    mock_user = AuthenticatedUser(
        user_id="nonexistent-id",
        email="ghost@test.com",
        tier=SubscriptionTier.FREE
    )

    # Mock Supabase response (no user)
    mock_response = MagicMock()
    mock_response.user = None

    # Create mock Supabase client
    mock_supabase = MagicMock()
    mock_supabase.auth.admin.get_user_by_id.return_value = mock_response

    # Call dependency - should raise 403
    with pytest.raises(HTTPException) as exc_info:
        await require_superuser(mock_user, mock_supabase)

    # Assertions
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Admin access required"
