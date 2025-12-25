"""
Integration Tests for Admin API Endpoints

Tests admin routes including access control, stats retrieval,
user list fetching, and tier updates.

Uses FastAPI dependency_overrides pattern for proper dependency injection testing.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from datetime import datetime

from app.main import app
from app.schemas.auth import AuthenticatedUser, SubscriptionTier
from app.core.auth import get_current_user
from app.core.supabase import get_supabase_client


client = TestClient(app)


# Mock admin user
ADMIN_USER = AuthenticatedUser(
    user_id="admin-user-id",
    email="admin@test.com",
    tier=SubscriptionTier.FREE
)

# Mock regular user
REGULAR_USER = AuthenticatedUser(
    user_id="regular-user-id",
    email="user@test.com",
    tier=SubscriptionTier.PRO
)


def create_mock_supabase_for_superuser_check(is_superuser: bool):
    """Helper to create mock Supabase client for superuser check"""
    mock_user_obj = MagicMock()
    mock_user_obj.user_metadata = {'is_superuser': is_superuser}

    mock_response = MagicMock()
    mock_response.user = mock_user_obj

    mock_supabase = MagicMock()
    mock_supabase.auth.admin.get_user_by_id.return_value = mock_response

    return mock_supabase


def create_mock_supabase_for_stats():
    """Helper to create mock Supabase client for stats endpoint"""
    mock_supabase = MagicMock()

    # Mock count_total_users RPC
    mock_count_result = MagicMock()
    mock_count_result.data = 150
    mock_supabase.rpc.return_value.execute.return_value = mock_count_result

    # Track table query count for different queries
    table_call_count = {'count': 0}

    def table_side_effect(table_name):
        """Return different mocks based on which table is queried"""
        table_call_count['count'] += 1
        table_mock = MagicMock()

        if table_call_count['count'] == 1:  # First: user_usage for total conversions
            mock_usage_result = MagicMock()
            mock_usage_result.data = [{'conversion_count': 500}, {'conversion_count': 734}]
            table_mock.select.return_value.execute.return_value = mock_usage_result
        elif table_call_count['count'] == 2:  # Second: conversion_jobs for active jobs
            mock_jobs_result = MagicMock()
            mock_jobs_result.count = 5
            in_mock = MagicMock()
            in_mock.execute.return_value = mock_jobs_result
            table_mock.select.return_value.in_.return_value = in_mock
        else:  # Third: user_usage for monthly conversions
            mock_monthly_result = MagicMock()
            mock_monthly_result.data = [{'conversion_count': 89}]
            eq_mock = MagicMock()
            eq_mock.execute.return_value = mock_monthly_result
            table_mock.select.return_value.eq.return_value = eq_mock

        return table_mock

    mock_supabase.table.side_effect = table_side_effect

    return mock_supabase


def create_mock_supabase_for_users():
    """Helper to create mock Supabase client for users endpoint"""
    mock_supabase = MagicMock()

    # Mock user list
    mock_user1 = MagicMock()
    mock_user1.id = "user-1"
    mock_user1.email = "user1@test.com"
    mock_user1.user_metadata = {'tier': 'FREE'}
    mock_user1.created_at = "2025-01-01T00:00:00Z"
    mock_user1.last_sign_in_at = "2025-12-25T10:00:00Z"

    mock_user2 = MagicMock()
    mock_user2.id = "user-2"
    mock_user2.email = "user2@test.com"
    mock_user2.user_metadata = {'tier': 'PRO'}
    mock_user2.created_at = "2025-02-01T00:00:00Z"
    mock_user2.last_sign_in_at = "2025-12-24T09:00:00Z"

    mock_supabase.auth.admin.list_users.return_value = [mock_user1, mock_user2]

    # Mock usage data
    mock_usage_result = MagicMock()
    mock_usage_result.data = [
        {'user_id': 'user-1', 'conversion_count': 3},
        {'user_id': 'user-2', 'conversion_count': 15}
    ]
    mock_supabase.table.return_value.select.return_value.execute.return_value = mock_usage_result

    return mock_supabase


def create_mock_supabase_for_tier_update():
    """Helper to create mock Supabase client for tier update endpoint"""
    mock_supabase = MagicMock()

    # Mock user fetch (get current tier)
    mock_user_obj = MagicMock()
    mock_user_obj.user_metadata = {'tier': 'FREE'}

    mock_get_response = MagicMock()
    mock_get_response.user = mock_user_obj

    # Mock tier update
    mock_updated_user = MagicMock()
    mock_updated_user.user_metadata = {'tier': 'PRO'}

    mock_update_response = MagicMock()
    mock_update_response.user = mock_updated_user

    mock_supabase.auth.admin.get_user_by_id.return_value = mock_get_response
    mock_supabase.auth.admin.update_user_by_id.return_value = mock_update_response

    return mock_supabase


class TestAdminStatsEndpoint:
    """Tests for GET /admin/stats endpoint"""

    def setup_method(self):
        """Clear dependency overrides before each test"""
        app.dependency_overrides.clear()

    def teardown_method(self):
        """Clear dependency overrides after each test"""
        app.dependency_overrides.clear()

    def test_get_stats_as_admin(self):
        """Test that admin can fetch system stats"""
        # Override dependencies
        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER

        # Create combined mock that handles both superuser check and stats queries
        mock_supabase = create_mock_supabase_for_superuser_check(True)
        stats_supabase = create_mock_supabase_for_stats()

        # Copy stats methods to the superuser mock
        mock_supabase.rpc = stats_supabase.rpc
        mock_supabase.table = stats_supabase.table

        app.dependency_overrides[get_supabase_client] = lambda: mock_supabase

        # Make request
        response = client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": "Bearer mock-token"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['total_users'] == 150
        assert data['total_conversions'] == 1234  # 500 + 734
        assert data['active_jobs'] == 5
        assert data['monthly_conversions'] == 89

    def test_get_stats_as_non_admin(self):
        """Test that non-admin is denied access to stats"""
        # Override dependencies
        app.dependency_overrides[get_current_user] = lambda: REGULAR_USER
        app.dependency_overrides[get_supabase_client] = lambda: create_mock_supabase_for_superuser_check(False)

        # Make request
        response = client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": "Bearer mock-token"}
        )

        # Assertions
        assert response.status_code == 403
        assert "Admin access required" in response.json()['detail']


class TestAdminUsersEndpoint:
    """Tests for GET /admin/users endpoint"""

    def setup_method(self):
        """Clear dependency overrides before each test"""
        app.dependency_overrides.clear()

    def teardown_method(self):
        """Clear dependency overrides after each test"""
        app.dependency_overrides.clear()

    def test_get_users_as_admin(self):
        """Test that admin can fetch user list"""
        # Override dependencies
        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER

        # Create combined mock for superuser check + user list
        mock_supabase = create_mock_supabase_for_superuser_check(True)
        users_supabase = create_mock_supabase_for_users()

        # Copy users methods to the superuser mock
        mock_supabase.auth.admin.list_users = users_supabase.auth.admin.list_users
        mock_supabase.table = users_supabase.table

        app.dependency_overrides[get_supabase_client] = lambda: mock_supabase

        # Make request
        response = client.get(
            "/api/v1/admin/users?page=1&page_size=20",
            headers={"Authorization": "Bearer mock-token"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 2
        assert data['page'] == 1
        assert data['page_size'] == 20
        assert len(data['users']) == 2
        # Default sort is by created_at desc, so user2 (2025-02-01) comes before user1 (2025-01-01)
        assert data['users'][0]['email'] == "user2@test.com"
        assert data['users'][1]['email'] == "user1@test.com"
        assert data['users'][0]['tier'] == "PRO"
        assert data['users'][1]['tier'] == "FREE"


class TestUpdateUserTierEndpoint:
    """Tests for PATCH /admin/users/{user_id}/tier endpoint"""

    def setup_method(self):
        """Clear dependency overrides before each test"""
        app.dependency_overrides.clear()

    def teardown_method(self):
        """Clear dependency overrides after each test"""
        app.dependency_overrides.clear()

    def test_update_tier_as_admin(self):
        """Test that admin can update user tier"""
        # Override dependencies
        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER

        # Create combined mock for superuser check + tier update
        mock_supabase = create_mock_supabase_for_tier_update()

        # Also need superuser check to pass
        superuser_check = MagicMock()
        superuser_check.user_metadata = {'is_superuser': True}
        superuser_response = MagicMock()
        superuser_response.user = superuser_check

        # Make get_user_by_id return different results based on call
        call_count = {'count': 0}
        def get_user_side_effect(user_id):
            call_count['count'] += 1
            if call_count['count'] == 1:  # First call: superuser check
                return superuser_response
            else:  # Second call: get current tier
                mock_user_obj = MagicMock()
                mock_user_obj.user_metadata = {'tier': 'FREE'}
                mock_get_response = MagicMock()
                mock_get_response.user = mock_user_obj
                return mock_get_response

        mock_supabase.auth.admin.get_user_by_id.side_effect = get_user_side_effect

        # Mock tier update
        mock_updated_user = MagicMock()
        mock_updated_user.user_metadata = {'tier': 'PRO'}
        mock_update_response = MagicMock()
        mock_update_response.user = mock_updated_user
        mock_supabase.auth.admin.update_user_by_id.return_value = mock_update_response

        app.dependency_overrides[get_supabase_client] = lambda: mock_supabase

        # Make request
        response = client.patch(
            "/api/v1/admin/users/user-1/tier",
            json={"tier": "PRO"},
            headers={"Authorization": "Bearer mock-token"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['user_id'] == "user-1"
        assert data['old_tier'] == "FREE"
        assert data['new_tier'] == "PRO"

    def test_update_tier_invalid_tier(self):
        """Test that invalid tier is rejected"""
        # Override dependencies
        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        app.dependency_overrides[get_supabase_client] = lambda: create_mock_supabase_for_superuser_check(True)

        # Make request with invalid tier
        response = client.patch(
            "/api/v1/admin/users/user-1/tier",
            json={"tier": "INVALID"},
            headers={"Authorization": "Bearer mock-token"}
        )

        # Assertions
        # Pydantic Literal type now validates at request level, returns 422 (Unprocessable Entity)
        assert response.status_code == 422
        assert "tier" in response.json()['detail'][0]['loc']

    def test_update_tier_as_non_admin(self):
        """Test that non-admin cannot update tier"""
        # Override dependencies
        app.dependency_overrides[get_current_user] = lambda: REGULAR_USER
        app.dependency_overrides[get_supabase_client] = lambda: create_mock_supabase_for_superuser_check(False)

        # Make request
        response = client.patch(
            "/api/v1/admin/users/user-1/tier",
            json={"tier": "PRO"},
            headers={"Authorization": "Bearer mock-token"}
        )

        # Assertions
        assert response.status_code == 403
        assert "Admin access required" in response.json()['detail']
