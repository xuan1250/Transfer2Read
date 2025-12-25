"""
Unit Tests for UsageTracker Service

Tests usage tracking logic including increment, get_usage, caching, and edge cases.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone
from app.services.usage_tracker import UsageTracker


class TestUsageTrackerIncrementUsage:
    """Test increment_usage method."""

    def test_increment_creates_new_row_for_first_conversion(self):
        """Test that increment_usage creates a new row for user's first conversion."""
        # Setup mocks
        mock_supabase = Mock()
        mock_redis = Mock()

        # Mock RPC response for new user (first conversion)
        mock_result = Mock()
        mock_result.data = 1  # New count is 1
        mock_supabase.rpc.return_value.execute.return_value = mock_result

        # Create tracker
        tracker = UsageTracker(mock_supabase, mock_redis)

        # Test increment
        count = tracker.increment_usage('user-123')

        # Assertions
        assert count == 1
        mock_supabase.rpc.assert_called_once()
        call_args = mock_supabase.rpc.call_args
        assert call_args[0][0] == 'increment_user_usage'
        assert call_args[0][1]['p_user_id'] == 'user-123'
        # Verify month format (YYYY-MM-01)
        assert call_args[0][1]['p_month'].endswith('-01')

        # Verify Redis cache was updated
        mock_redis.set.assert_called_once()
        redis_key = mock_redis.set.call_args[0][0]
        assert 'usage:user-123:' in redis_key
        assert mock_redis.set.call_args[0][1] == 1  # Count value
        assert mock_redis.set.call_args[1]['ex'] == 3600  # TTL

    def test_increment_updates_existing_row(self):
        """Test that increment_usage updates existing row for repeat conversions."""
        # Setup mocks
        mock_supabase = Mock()
        mock_redis = Mock()

        # Mock RPC response for existing user (count = 4)
        mock_result = Mock()
        mock_result.data = 4  # User has done 4 conversions
        mock_supabase.rpc.return_value.execute.return_value = mock_result

        tracker = UsageTracker(mock_supabase, mock_redis)
        count = tracker.increment_usage('user-456')

        assert count == 4
        mock_redis.set.assert_called_with(
            pytest.helpers.any_string_containing('usage:user-456:'),
            4,
            ex=3600
        )

    def test_increment_continues_when_redis_fails(self):
        """Test that increment_usage continues even if Redis cache update fails."""
        # Setup mocks
        mock_supabase = Mock()
        mock_redis = Mock()

        # Mock successful database increment
        mock_result = Mock()
        mock_result.data = 2
        mock_supabase.rpc.return_value.execute.return_value = mock_result

        # Mock Redis failure
        mock_redis.set.side_effect = Exception("Redis connection error")

        tracker = UsageTracker(mock_supabase, mock_redis)
        count = tracker.increment_usage('user-789')

        # Should still return count even though Redis failed
        assert count == 2

    def test_increment_raises_exception_on_database_failure(self):
        """Test that increment_usage raises exception if database operation fails."""
        # Setup mocks
        mock_supabase = Mock()
        mock_redis = Mock()

        # Mock database failure
        mock_supabase.rpc.return_value.execute.side_effect = Exception("Database connection error")

        tracker = UsageTracker(mock_supabase, mock_redis)

        # Should raise exception
        with pytest.raises(Exception, match="Database connection error"):
            tracker.increment_usage('user-999')

    def test_increment_works_without_redis(self):
        """Test that increment_usage works when Redis is not available (None)."""
        # Setup mocks
        mock_supabase = Mock()

        # Mock successful increment
        mock_result = Mock()
        mock_result.data = 3
        mock_supabase.rpc.return_value.execute.return_value = mock_result

        tracker = UsageTracker(mock_supabase, redis_client=None)
        count = tracker.increment_usage('user-no-redis')

        # Should work fine without Redis
        assert count == 3


class TestUsageTrackerGetUsage:
    """Test get_usage method."""

    def test_get_usage_returns_correct_data_for_free_tier(self):
        """Test get_usage calculates remaining conversions correctly for FREE tier."""
        # Setup mocks
        mock_supabase = Mock()
        mock_redis = Mock()

        # Mock Redis cache hit (count = 3)
        mock_redis.get.return_value = '3'

        # Mock Supabase auth response (FREE tier)
        mock_user = Mock()
        mock_user.user.user_metadata = {'tier': 'FREE'}
        mock_supabase.auth.admin.get_user_by_id.return_value = mock_user

        tracker = UsageTracker(mock_supabase, mock_redis)
        usage = tracker.get_usage('user-123')

        # Assertions
        assert usage['conversion_count'] == 3
        assert usage['tier'] == 'FREE'
        assert usage['tier_limit'] == 5
        assert usage['remaining'] == 2  # 5 - 3 = 2
        assert usage['month'].endswith('-01')  # Format: YYYY-MM-01

    def test_get_usage_returns_unlimited_for_pro_tier(self):
        """Test get_usage returns None for limit and remaining for PRO tier."""
        # Setup mocks
        mock_supabase = Mock()
        mock_redis = Mock()

        # Mock Redis cache hit (count = 50)
        mock_redis.get.return_value = '50'

        # Mock Supabase auth response (PRO tier)
        mock_user = Mock()
        mock_user.user.user_metadata = {'tier': 'PRO'}
        mock_supabase.auth.admin.get_user_by_id.return_value = mock_user

        tracker = UsageTracker(mock_supabase, mock_redis)
        usage = tracker.get_usage('pro-user-456')

        assert usage['conversion_count'] == 50
        assert usage['tier'] == 'PRO'
        assert usage['tier_limit'] is None  # Unlimited
        assert usage['remaining'] is None  # Unlimited

    def test_get_usage_falls_back_to_database_on_cache_miss(self):
        """Test get_usage queries database when Redis cache misses."""
        # Setup mocks
        mock_supabase = Mock()
        mock_redis = Mock()

        # Mock Redis cache miss
        mock_redis.get.return_value = None

        # Mock database query
        mock_result = Mock()
        mock_result.data = [{'conversion_count': 2}]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        # Mock user tier
        mock_user = Mock()
        mock_user.user.user_metadata = {'tier': 'FREE'}
        mock_supabase.auth.admin.get_user_by_id.return_value = mock_user

        tracker = UsageTracker(mock_supabase, mock_redis)
        usage = tracker.get_usage('user-789')

        # Should fetch from database
        assert usage['conversion_count'] == 2
        mock_supabase.table.assert_called_with('user_usage')

        # Should update cache with fetched value
        mock_redis.set.assert_called_once()

    def test_get_usage_returns_zero_for_new_user(self):
        """Test get_usage returns count=0 for new user with no usage data."""
        # Setup mocks
        mock_supabase = Mock()
        mock_redis = Mock()

        # Mock Redis cache miss
        mock_redis.get.return_value = None

        # Mock database query (no data - new user)
        mock_result = Mock()
        mock_result.data = []  # Empty result
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        # Mock user tier
        mock_user = Mock()
        mock_user.user.user_metadata = {'tier': 'FREE'}
        mock_supabase.auth.admin.get_user_by_id.return_value = mock_user

        tracker = UsageTracker(mock_supabase, mock_redis)
        usage = tracker.get_usage('new-user-999')

        assert usage['conversion_count'] == 0
        assert usage['remaining'] == 5  # Full limit remaining

    def test_get_usage_calculates_remaining_correctly_at_limit(self):
        """Test get_usage calculates remaining=0 when user reaches limit."""
        # Setup mocks
        mock_supabase = Mock()
        mock_redis = Mock()

        # Mock Redis cache hit (count = 5, at limit)
        mock_redis.get.return_value = '5'

        # Mock user tier
        mock_user = Mock()
        mock_user.user.user_metadata = {'tier': 'FREE'}
        mock_supabase.auth.admin.get_user_by_id.return_value = mock_user

        tracker = UsageTracker(mock_supabase, mock_redis)
        usage = tracker.get_usage('user-limit')

        assert usage['conversion_count'] == 5
        assert usage['remaining'] == 0  # No conversions remaining

    def test_get_usage_works_without_redis(self):
        """Test get_usage works when Redis is not available (None)."""
        # Setup mocks
        mock_supabase = Mock()

        # Mock database query
        mock_result = Mock()
        mock_result.data = [{'conversion_count': 1}]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        # Mock user tier
        mock_user = Mock()
        mock_user.user.user_metadata = {'tier': 'FREE'}
        mock_supabase.auth.admin.get_user_by_id.return_value = mock_user

        tracker = UsageTracker(mock_supabase, redis_client=None)
        usage = tracker.get_usage('user-no-redis')

        assert usage['conversion_count'] == 1
        assert usage['remaining'] == 4

    def test_get_usage_defaults_to_free_tier_on_auth_error(self):
        """Test get_usage defaults to FREE tier if user tier fetch fails."""
        # Setup mocks
        mock_supabase = Mock()
        mock_redis = Mock()

        # Mock Redis cache hit
        mock_redis.get.return_value = '2'

        # Mock auth error
        mock_supabase.auth.admin.get_user_by_id.side_effect = Exception("Auth service unavailable")

        tracker = UsageTracker(mock_supabase, mock_redis)
        usage = tracker.get_usage('user-auth-fail')

        # Should default to FREE tier
        assert usage['tier'] == 'FREE'
        assert usage['tier_limit'] == 5
        assert usage['remaining'] == 3  # 5 - 2 = 3


class TestUsageTrackerHelperMethods:
    """Test helper methods."""

    def test_get_current_month_format(self):
        """Test _get_current_month returns correct format (YYYY-MM-01)."""
        mock_supabase = Mock()
        tracker = UsageTracker(mock_supabase, None)

        month = tracker._get_current_month()

        # Format: YYYY-MM-01
        assert len(month) == 10
        assert month[4] == '-'
        assert month[7] == '-'
        assert month.endswith('-01')

    def test_get_redis_key_format(self):
        """Test _get_redis_key returns correct format (usage:{user_id}:{YYYY-MM})."""
        mock_supabase = Mock()
        tracker = UsageTracker(mock_supabase, None)

        key = tracker._get_redis_key('user-123', '2025-12-01')

        assert key == 'usage:user-123:2025-12'

    def test_get_redis_key_strips_day_from_month(self):
        """Test _get_redis_key strips day from month string."""
        mock_supabase = Mock()
        tracker = UsageTracker(mock_supabase, None)

        key = tracker._get_redis_key('user-456', '2025-11-15')

        # Should strip day and use only YYYY-MM
        assert key == 'usage:user-456:2025-11'


# Helper for pytest (if available)
if hasattr(pytest, 'helpers'):
    pytest.helpers.register(lambda s: lambda x: s in x, name='any_string_containing')
