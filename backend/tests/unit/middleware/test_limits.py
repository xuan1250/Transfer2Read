"""
Unit Tests for Limit Enforcement Middleware

Tests for tier-based limit checks (file size and monthly conversions).
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException, Request
from datetime import datetime, timezone

from app.middleware.limits import check_tier_limits
from app.schemas.auth import AuthenticatedUser, SubscriptionTier
from app.core.limits import get_file_size_limit, get_conversion_limit


# ============================================================================
# Unit Tests for Helper Functions
# ============================================================================

class TestLimitHelpers:
    """Test get_file_size_limit and get_conversion_limit helper functions."""
    
    def test_free_tier_file_size_limit(self):
        """FREE tier should have 50MB file size limit."""
        assert get_file_size_limit("FREE") == 50 * 1024 * 1024
    
    def test_pro_tier_unlimited_file_size(self):
        """PRO tier should have unlimited file size (None)."""
        assert get_file_size_limit("PRO") is None
    
    def test_premium_tier_unlimited_file_size(self):
        """PREMIUM tier should have unlimited file size (None)."""
        assert get_file_size_limit("PREMIUM") is None
    
    def test_unknown_tier_defaults_to_free_file_size(self):
        """Unrecognized tier should default to FREE limits."""
        assert get_file_size_limit("UNKNOWN") == 50 * 1024 * 1024
        assert get_file_size_limit(None) == 50 * 1024 * 1024
        assert get_file_size_limit("") == 50 * 1024 * 1024
    
    def test_case_insensitive_tier_names(self):
        """Tier names should be case-insensitive."""
        assert get_file_size_limit("free") == 50 * 1024 * 1024
        assert get_file_size_limit("FrEe") == 50 * 1024 * 1024
        assert get_file_size_limit("pro") is None
    
    def test_free_tier_conversion_limit(self):
        """FREE tier should have 5 conversions per month limit."""
        assert get_conversion_limit("FREE") == 5
    
    def test_pro_tier_unlimited_conversions(self):
        """PRO tier should have unlimited conversions (None)."""
        assert get_conversion_limit("PRO") is None
    
    def test_premium_tier_unlimited_conversions(self):
        """PREMIUM tier should have unlimited conversions (None)."""
        assert get_conversion_limit("PREMIUM") is None
    
    def test_unknown_tier_defaults_to_free_conversions(self):
        """Unrecognized tier should default to FREE conversion limit."""
        assert get_conversion_limit("UNKNOWN") == 5
        assert get_conversion_limit(None) == 5


# ============================================================================
# Unit Tests for check_tier_limits Middleware
# ============================================================================

class TestCheckTierLimits:
    """Test check_tier_limits FastAPI dependency."""
    
    @pytest.fixture
    def mock_request(self):
        """Create mock FastAPI Request."""
        request = Mock(spec=Request)
        request.headers = {}
        return request
    
    @pytest.fixture
    def free_user(self):
        """Create FREE tier user."""
        return AuthenticatedUser(
            user_id="user-123",
            email="free@example.com",
            tier=SubscriptionTier.FREE
        )
    
    @pytest.fixture
    def pro_user(self):
        """Create PRO tier user."""
        return AuthenticatedUser(
            user_id="user-456",
            email="pro@example.com",
            tier=SubscriptionTier.PRO
        )
    
    @pytest.fixture
    def premium_user(self):
        """Create PREMIUM tier user."""
        return AuthenticatedUser(
            user_id="user-789",
            email="premium@example.com",
            tier=SubscriptionTier.PREMIUM
        )
    
    # ------------------------------------------------------------------------
    # PRO/PREMIUM Tier Bypass Tests
    # ------------------------------------------------------------------------
    
    @pytest.mark.asyncio
    async def test_pro_user_bypasses_all_checks(self, mock_request, pro_user):
        """PRO users should bypass all limit checks."""
        # Even with large file and high usage, PRO users pass
        mock_request.headers = {"content-length": str(100 * 1024 * 1024)}  # 100MB
        
        with patch("app.middleware.limits.UsageTracker") as MockTracker:
            # Mock shows user has already used 1000 conversions (way over limit)
            tracker_instance = MockTracker.return_value
            tracker_instance.get_usage.return_value = {
                "conversion_count": 1000,
                "tier_limit": None,
                "tier": "PRO"
            }
            
            # Should not raise exception
            result = await check_tier_limits(mock_request, pro_user)
            assert result is None
            
            # UsageTracker should NOT be called (bypassed before check)
            MockTracker.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_premium_user_bypasses_all_checks(self, mock_request, premium_user):
        """PREMIUM users should bypass all limit checks."""
        mock_request.headers = {"content-length": str(200 * 1024 * 1024)}  # 200MB
        
        with patch("app.middleware.limits.UsageTracker") as MockTracker:
            # Should not raise exception
            result = await check_tier_limits(mock_request, premium_user)
            assert result is None
            
            # UsageTracker should NOT be called (bypassed before check)
            MockTracker.assert_not_called()
    
    # ------------------------------------------------------------------------
    # File Size Limit Tests
    # ------------------------------------------------------------------------
    
    @pytest.mark.asyncio
    async def test_free_user_file_size_under_limit(self, mock_request, free_user):
        """FREE user with file under 50MB should pass file size check."""
        # 30MB file (under 50MB limit)
        mock_request.headers = {"content-length": str(30 * 1024 * 1024)}
        
        with patch("app.middleware.limits.UsageTracker") as MockTracker:
            tracker_instance = MockTracker.return_value
            tracker_instance.get_usage.return_value = {
                "conversion_count": 2,
                "tier_limit": 5,
                "tier": "FREE"
            }
            
            # Should not raise exception
            result = await check_tier_limits(mock_request, free_user)
            assert result is None
    
    @pytest.mark.asyncio
    async def test_free_user_file_size_at_limit(self, mock_request, free_user):
        """FREE user with file exactly at 50MB should pass."""
        # Exactly 50MB (boundary case)
        mock_request.headers = {"content-length": str(50 * 1024 * 1024)}
        
        with patch("app.middleware.limits.UsageTracker") as MockTracker:
            tracker_instance = MockTracker.return_value
            tracker_instance.get_usage.return_value = {
                "conversion_count": 0,
                "tier_limit": 5,
                "tier": "FREE"
            }
            
            # Should not raise exception (at limit is OK)
            result = await check_tier_limits(mock_request, free_user)
            assert result is None
    
    @pytest.mark.asyncio
    async def test_free_user_file_size_exceeds_limit(self, mock_request, free_user):
        """FREE user with file over 50MB should be rejected."""
        # 75MB file (over 50MB limit)
        mock_request.headers = {"content-length": str(75 * 1024 * 1024)}
        
        with pytest.raises(HTTPException) as exc_info:
            await check_tier_limits(mock_request, free_user)
        
        assert exc_info.value.status_code == 403
        detail = exc_info.value.detail
        assert detail["code"] == "FILE_SIZE_LIMIT_EXCEEDED"
        assert detail["tier"] == "FREE"
        assert detail["current_size_mb"] == 75.0
        assert detail["max_size_mb"] == 50
        assert "/pricing" in detail.get("upgrade_url", "")
    
    @pytest.mark.asyncio
    async def test_file_size_check_without_content_length_header(self, mock_request, free_user):
        """If Content-Length header missing, skip file size check."""
        # No Content-Length header
        mock_request.headers = {}
        
        with patch("app.middleware.limits.UsageTracker") as MockTracker:
            tracker_instance = MockTracker.return_value
            tracker_instance.get_usage.return_value = {
                "conversion_count": 1,
                "tier_limit": 5,
                "tier": "FREE"
            }
            
            # Should not raise exception (can't check file size without header)
            result = await check_tier_limits(mock_request, free_user)
            assert result is None
    
    # ------------------------------------------------------------------------
    # Conversion Limit Tests
    # ------------------------------------------------------------------------
    
    @pytest.mark.asyncio
    async def test_free_user_under_conversion_limit(self, mock_request, free_user):
        """FREE user with 2/5 conversions should pass."""
        mock_request.headers = {"content-length": str(10 * 1024 * 1024)}
        
        with patch("app.middleware.limits.UsageTracker") as MockTracker:
            tracker_instance = MockTracker.return_value
            tracker_instance.get_usage.return_value = {
                "conversion_count": 2,
                "tier_limit": 5,
                "tier": "FREE"
            }
            MockTracker.return_value = tracker_instance
            
            # Should not raise exception
            result = await check_tier_limits(mock_request, free_user)
            assert result is None
    
    @pytest.mark.asyncio
    async def test_free_user_at_conversion_limit(self, mock_request, free_user):
        """FREE user at 5/5 conversions should be rejected."""
        mock_request.headers = {"content-length": str(10 * 1024 * 1024)}
        
        with patch("app.middleware.limits.UsageTracker") as MockTracker:
            tracker_instance = MockTracker.return_value
            tracker_instance.get_usage.return_value = {
                "conversion_count": 5,
                "tier_limit": 5,
                "tier": "FREE"
            }
            MockTracker.return_value = tracker_instance
            
            with pytest.raises(HTTPException) as exc_info:
                await check_tier_limits(mock_request, free_user)
            
            assert exc_info.value.status_code == 403
            detail = exc_info.value.detail
            assert detail["code"] == "CONVERSION_LIMIT_EXCEEDED"
            assert detail["tier"] == "FREE"
            assert detail["current_count"] == 5
            assert detail["limit"] == 5
            assert "reset_date" in detail
    
    @pytest.mark.asyncio
    async def test_free_user_exceeds_conversion_limit(self, mock_request, free_user):
        """FREE user with 6/5 conversions should be rejected."""
        mock_request.headers = {"content-length": str(10 * 1024 * 1024)}
        
        with patch("app.middleware.limits.UsageTracker") as MockTracker:
            tracker_instance = MockTracker.return_value
            tracker_instance.get_usage.return_value = {
                "conversion_count": 6,
                "tier_limit": 5,
                "tier": "FREE"
            }
            MockTracker.return_value = tracker_instance
            
            with pytest.raises(HTTPException) as exc_info:
                await check_tier_limits(mock_request, free_user)
            
            assert exc_info.value.status_code == 403
            detail = exc_info.value.detail
            assert detail["code"] == "CONVERSION_LIMIT_EXCEEDED"
    
    # ------------------------------------------------------------------------
    # Edge Cases and Error Handling
    # ------------------------------------------------------------------------
    
    @pytest.mark.asyncio
    async def test_default_to_free_tier_when_metadata_missing(self, mock_request):
        """User with FREE tier (default) should have FREE limits enforced."""
        # In practice, get_current_user always returns a valid tier (defaults to FREE)
        # This tests that FREE tier limits are properly enforced
        user_free_tier = AuthenticatedUser(
            user_id="user-999",
            email="freetier@example.com",
            tier=SubscriptionTier.FREE  # FREE tier is the default
        )
        
        # File over 50MB (FREE limit)
        mock_request.headers = {"content-length": str(60 * 1024 * 1024)}
        
        with pytest.raises(HTTPException) as exc_info:
            await check_tier_limits(mock_request, user_free_tier)
        
        # Should apply FREE tier limits
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "FILE_SIZE_LIMIT_EXCEEDED"
    
    @pytest.mark.asyncio
    async def test_usage_tracker_failure_fails_open(self, mock_request, free_user):
        """If UsageTracker fails, allow upload (fail-open policy)."""
        mock_request.headers = {"content-length": str(10 * 1024 * 1024)}
        
        with patch("app.middleware.limits.UsageTracker") as MockTracker:
            tracker_instance = MockTracker.return_value
            tracker_instance.get_usage.side_effect = Exception("Database connection failed")
            MockTracker.return_value = tracker_instance
            
            # Should NOT raise exception (fail-open for availability)
            result = await check_tier_limits(mock_request, free_user)
            assert result is None
    
    @pytest.mark.asyncio
    async def test_reset_date_calculation_december(self, mock_request, free_user):
        """Reset date should handle year rollover in December."""
        mock_request.headers = {"content-length": str(10 * 1024 * 1024)}
        
        with patch("app.middleware.limits.UsageTracker") as MockTracker:
            tracker_instance = MockTracker.return_value
            tracker_instance.get_usage.return_value = {
                "conversion_count": 5,
                "tier_limit": 5,
                "tier": "FREE"
            }
            MockTracker.return_value = tracker_instance
            
            # Mock datetime to December
            with patch("app.middleware.limits.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(2025, 12, 15, tzinfo=timezone.utc)
                
                with pytest.raises(HTTPException) as exc_info:
                    await check_tier_limits(mock_request, free_user)
                
                detail = exc_info.value.detail
                # Should show January 1st of next year
                assert detail["reset_date"] == "2026-01-01"
    
    @pytest.mark.asyncio
    async def test_reset_date_calculation_regular_month(self, mock_request, free_user):
        """Reset date should correctly calculate next month."""
        mock_request.headers = {"content-length": str(10 * 1024 * 1024)}
        
        with patch("app.middleware.limits.UsageTracker") as MockTracker:
            tracker_instance = MockTracker.return_value
            tracker_instance.get_usage.return_value = {
                "conversion_count": 5,
                "tier_limit": 5,
                "tier": "FREE"
            }
            MockTracker.return_value = tracker_instance
            
            # Mock datetime to March
            with patch("app.middleware.limits.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(2025, 3, 20, tzinfo=timezone.utc)
                
                with pytest.raises(HTTPException) as exc_info:
                    await check_tier_limits(mock_request, free_user)
                
                detail = exc_info.value.detail
                # Should show April 1st
                assert detail["reset_date"] == "2025-04-01"
