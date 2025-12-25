"""
Integration Tests for Usage API Endpoint

Tests GET /api/v1/usage endpoint with authentication and error handling.
"""
import pytest
from unittest.mock import Mock, patch


class TestGetUsageEndpoint:
    """Test GET /api/v1/usage endpoint."""

    @pytest.mark.asyncio
    async def test_get_usage_returns_authenticated_user_data(self, client, valid_jwt_token):
        """Test GET /usage returns 200 OK with authenticated JWT token."""
        # Mock UsageTracker.get_usage
        with patch('app.api.v1.usage.UsageTracker') as MockTracker:
            mock_tracker_instance = Mock()
            mock_tracker_instance.get_usage.return_value = {
                'month': '2025-12-01',
                'conversion_count': 3,
                'tier': 'FREE',
                'tier_limit': 5,
                'remaining': 2
            }
            MockTracker.return_value = mock_tracker_instance

            # Make request with auth token
            response = await client.get(
                "/api/v1/usage",
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data['month'] == '2025-12-01'
            assert data['conversion_count'] == 3
            assert data['tier'] == 'FREE'
            assert data['tier_limit'] == 5
            assert data['remaining'] == 2

    @pytest.mark.asyncio
    async def test_get_usage_returns_401_for_unauthenticated_request(self, client):
        """Test GET /usage returns 401 Unauthorized when JWT token missing."""
        # Make request without auth token
        response = await client.get("/api/v1/usage")

        assert response.status_code == 403  # FastAPI HTTPBearer returns 403
        assert 'detail' in response.json()

    @pytest.mark.asyncio
    async def test_get_usage_returns_401_for_invalid_token(self, client):
        """Test GET /usage returns 401 Unauthorized when JWT token invalid."""
        # Make request with invalid token
        response = await client.get(
            "/api/v1/usage",
            headers={"Authorization": "Bearer invalid-token-123"}
        )

        assert response.status_code == 401
        assert 'detail' in response.json()

    @pytest.mark.asyncio
    async def test_get_usage_handles_new_user_with_no_data(self, client, valid_jwt_token):
        """Test GET /usage handles new user with no usage data (returns count=0)."""
        # Mock UsageTracker.get_usage for new user
        with patch('app.api.v1.usage.UsageTracker') as MockTracker:
            mock_tracker_instance = Mock()
            mock_tracker_instance.get_usage.return_value = {
                'month': '2025-12-01',
                'conversion_count': 0,
                'tier': 'FREE',
                'tier_limit': 5,
                'remaining': 5
            }
            MockTracker.return_value = mock_tracker_instance

            response = await client.get(
                "/api/v1/usage",
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data['conversion_count'] == 0
            assert data['remaining'] == 5

    @pytest.mark.asyncio
    async def test_get_usage_returns_unlimited_for_pro_tier(self, client, pro_tier_jwt_token):
        """Test GET /usage returns null limit/remaining for PRO tier."""
        # Mock UsageTracker.get_usage for PRO tier user
        with patch('app.api.v1.usage.UsageTracker') as MockTracker:
            mock_tracker_instance = Mock()
            mock_tracker_instance.get_usage.return_value = {
                'month': '2025-12-01',
                'conversion_count': 25,
                'tier': 'PRO',
                'tier_limit': None,
                'remaining': None
            }
            MockTracker.return_value = mock_tracker_instance

            response = await client.get(
                "/api/v1/usage",
                headers={"Authorization": f"Bearer {pro_tier_jwt_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data['tier'] == 'PRO'
            assert data['tier_limit'] is None
            assert data['remaining'] is None

    @pytest.mark.asyncio
    async def test_get_usage_returns_500_on_service_failure(self, client, valid_jwt_token):
        """Test GET /usage returns 500 Internal Server Error when service fails."""
        # Mock UsageTracker to raise exception
        with patch('app.api.v1.usage.UsageTracker') as MockTracker:
            mock_tracker_instance = Mock()
            mock_tracker_instance.get_usage.side_effect = Exception("Database connection failed")
            MockTracker.return_value = mock_tracker_instance

            response = await client.get(
                "/api/v1/usage",
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )

            assert response.status_code == 500
            assert 'detail' in response.json()
            assert 'Failed to retrieve usage data' in response.json()['detail']

    @pytest.mark.asyncio
    async def test_get_usage_expired_token(self, client, expired_jwt_token):
        """Test GET /usage returns 401 for expired JWT token."""
        response = await client.get(
            "/api/v1/usage",
            headers={"Authorization": f"Bearer {expired_jwt_token}"}
        )

        assert response.status_code == 401
        assert 'detail' in response.json()
