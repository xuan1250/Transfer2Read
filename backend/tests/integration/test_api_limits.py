"""
Integration Tests for Limit Enforcement

End-to-end tests for upload API with tier limit enforcement.
Tests via FastAPI TestClient with mocked database and Redis.
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from datetime import datetime
import io

from app.api.v1.upload import router
from app.schemas.auth import AuthenticatedUser, SubscriptionTier


@pytest.fixture
def app():
    """Create FastAPI app with upload router."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_free_user():
    """Mock FREE tier user."""
    return AuthenticatedUser(
        user_id="free-user-123",
        email="free@example.com",
        tier=SubscriptionTier.FREE
    )


@pytest.fixture
def mock_pro_user():
    """Mock PRO tier user."""
    return AuthenticatedUser(
        user_id="pro-user-456",
        email="pro@example.com",
        tier=SubscriptionTier.PRO
    )


@pytest.fixture
def mock_premium_user():
    """Mock PREMIUM tier user."""
    return AuthenticatedUser(
        user_id="premium-user-789",
        email="premium@example.com",
        tier=SubscriptionTier.PREMIUM
    )


@pytest.fixture
def valid_pdf_file():
    """Create a valid (small) PDF file for testing."""
    # PDF magic bytes header
    pdf_content = b"%PDF-1.4\n"
    pdf_content += b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    pdf_content += b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
    pdf_content += b"3 0 obj<</Type/Page/Parent 2 0 R>>endobj\n"
    pdf_content += b"xref\n0 4\n0000000000 65535 f\n"
    pdf_content += b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n109\n%%EOF\n"
    
    return io.BytesIO(pdf_content)


@pytest.fixture
def large_pdf_file():
    """Create a large PDF file (over 50MB) for testing."""
    # Create 60MB file
    pdf_content = b"%PDF-1.4\n" + (b"x" * (60 * 1024 * 1024))
    return io.BytesIO(pdf_content)


# ============================================================================
# Integration Tests for Limit Enforcement
# ============================================================================

class TestUploadLimitEnforcement:
    """Integration tests for /api/v1/upload with limit enforcement."""
    
    # ------------------------------------------------------------------------
    # FREE User: Under Limit (Should Succeed)
    # ------------------------------------------------------------------------
    
    def test_free_user_under_limit_succeeds(
        self,
        client,
        valid_pdf_file,
        mock_free_user
    ):
        """FREE user with 2/5 conversions and small file should succeed."""
        
        with patch("app.core.auth.get_current_user") as mock_get_user, \
             patch("app.middleware.limits.UsageTracker") as MockTracker, \
             patch("app.api.v1.upload.get_storage_service") as mock_storage, \
             patch("app.api.v1.upload.get_supabase_client") as mock_supabase:
            
            # Mock authentication (patch at core module level)
            mock_get_user.return_value = mock_free_user
            
            # Mock usage tracker (under limit)
            tracker_instance = MockTracker.return_value
            tracker_instance.get_usage.return_value = {
                "conversion_count": 2,
                "tier_limit": 5,
                "tier": "FREE"
            }
            tracker_instance.increment_usage.return_value = 3
            
            # Mock storage and database
            mock_storage_instance = Mock()
            mock_storage_instance.upload_file.return_value = None
            mock_storage.return_value = mock_storage_instance
            
            mock_supabase_instance = Mock()
            mock_supabase_instance.table.return_value.insert.return_value.execute.return_value = None
            mock_supabase.return_value = mock_supabase_instance
            
            # Make request
            response = client.post(
                "/api/v1/upload",
                files={"file": ("test.pdf", valid_pdf_file, "application/pdf")}
            )
            
            # Should succeed (202 Accepted)
            assert response.status_code == 202
            data = response.json()
            assert "job_id" in data
            assert data["status"] == "UPLOADED"
    
    # ------------------------------------------------------------------------
    # FREE User: At Conversion Limit (Should Fail with 403)
    # ------------------------------------------------------------------------
    
    def test_free_user_at_limit_returns_403(
        self,
        client,
        valid_pdf_file,
        mock_free_user
    ):
        """FREE user with 5/5 conversions should get 403 with CONVERSION_LIMIT_EXCEEDED."""
        
        with patch("app.core.auth.get_current_user") as mock_get_user, \
             patch("app.middleware.limits.UsageTracker") as MockTracker:
            
            # Mock authentication
            mock_get_user.return_value = mock_free_user
            
            # Mock usage tracker (at limit)
            tracker_instance = MockTracker.return_value
            tracker_instance.get_usage.return_value = {
                "conversion_count": 5,
                "tier_limit": 5,
                "tier": "FREE"
            }
            MockTracker.return_value = tracker_instance
            
            # Make request
            response = client.post(
                "/api/v1/upload",
                files={"file": ("test.pdf", valid_pdf_file, "application/pdf")}
            )
            
            # Should fail (403 Forbidden)
            assert response.status_code == 403
            data = response.json()
            assert data["detail"]["code"] == "CONVERSION_LIMIT_EXCEEDED"
            assert data["detail"]["tier"] == "FREE"
            assert data["detail"]["current_count"] == 5
            assert data["detail"]["limit"] == 5
            assert "reset_date" in data["detail"]
            assert "/pricing" in data["detail"]["upgrade_url"]
    
    # ------------------------------------------------------------------------
    # FREE User: File Too Large (Should Fail with 403)
    # ------------------------------------------------------------------------
    
    def test_free_user_large_file_returns_403(
        self,
        client,
        large_pdf_file,
        mock_free_user
    ):
        """FREE user uploading 60MB file should get 403 with FILE_SIZE_LIMIT_EXCEEDED."""
        
        with patch("app.core.auth.get_current_user") as mock_get_user:
            # Mock authentication
            mock_get_user.return_value = mock_free_user
            
            # Make request (Content-Length header set automatically by TestClient)
            response = client.post(
                "/api/v1/upload",
                files={"file": ("large.pdf", large_pdf_file, "application/pdf")}
            )
            
            # Should fail (403 Forbidden)
            assert response.status_code == 403
            data = response.json()
            assert data["detail"]["code"] == "FILE_SIZE_LIMIT_EXCEEDED"
            assert data["detail"]["tier"] == "FREE"
            assert data["detail"]["current_size_mb"] > 50
            assert data["detail"]["max_size_mb"] == 50
            assert "/pricing" in data["detail"]["upgrade_url"]
    
    # ------------------------------------------------------------------------
    # PRO User: Bypasses Limits (Should Succeed)
    # ------------------------------------------------------------------------
    
    def test_pro_user_bypasses_conversion_limit(
        self,
        client,
        valid_pdf_file,
        mock_pro_user
    ):
        """PRO user with many conversions should bypass limit and succeed."""
        
        with patch("app.core.auth.get_current_user") as mock_get_user, \
             patch("app.api.v1.upload.get_storage_service") as mock_storage, \
             patch("app.api.v1.upload.get_supabase_client") as mock_supabase, \
             patch("app.api.v1.upload.UsageTracker") as MockTracker:
            
            # Mock authentication
            mock_get_user.return_value = mock_pro_user
            
            # Mock storage and database
            mock_storage_instance = Mock()
            mock_storage_instance.upload_file.return_value = None
            mock_storage.return_value = mock_storage_instance
            
            mock_supabase_instance = Mock()
            mock_supabase_instance.table.return_value.insert.return_value.execute.return_value = None
            mock_supabase.return_value = mock_supabase_instance
            
            # Mock usage tracker
            tracker_instance = MockTracker.return_value
            tracker_instance.increment_usage.return_value = 100  # Already has 100 conversions
            
            # Make request
            response = client.post(
                "/api/v1/upload",
                files={"file": ("test.pdf", valid_pdf_file, "application/pdf")}
            )
            
            # Should succeed (202 Accepted) - PRO bypasses limit
            assert response.status_code == 202
            data = response.json()
            assert "job_id" in data
    
    def test_pro_user_bypasses_file_size_limit(
        self,
        client,
        large_pdf_file,
        mock_pro_user
    ):
        """PRO user with large file should bypass limit and succeed."""
        
        with patch("app.core.auth.get_current_user") as mock_get_user, \
             patch("app.api.v1.upload.get_storage_service") as mock_storage, \
             patch("app.api.v1.upload.get_supabase_client") as mock_supabase, \
             patch("app.api.v1.upload.UsageTracker") as MockTracker:
            
            # Mock authentication
            mock_get_user.return_value = mock_pro_user
            
            # Mock storage and database
            mock_storage_instance = Mock()
            mock_storage_instance.upload_file.return_value = None
            mock_storage.return_value = mock_storage_instance
            
            mock_supabase_instance = Mock()
            mock_supabase_instance.table.return_value.insert.return_value.execute.return_value = None
            mock_supabase.return_value = mock_supabase_instance
            
            # Mock usage tracker
            tracker_instance = MockTracker.return_value
            tracker_instance.increment_usage.return_value = 1
            
            # Make request
            response = client.post(
                "/api/v1/upload",
                files={"file": ("large.pdf", large_pdf_file, "application/pdf")}
            )
            
            # Should succeed (202 Accepted) - PRO bypasses file size limit
            assert response.status_code == 202
            data = response.json()
            assert "job_id" in data
    
    # ------------------------------------------------------------------------
    # PREMIUM User: Bypasses Limits (Should Succeed)
    # ------------------------------------------------------------------------
    
    def test_premium_user_bypasses_all_limits(
        self,
        client,
        large_pdf_file,
        mock_premium_user
    ):
        """PREMIUM user should bypass all limits."""
        
        with patch("app.core.auth.get_current_user") as mock_get_user, \
             patch("app.api.v1.upload.get_storage_service") as mock_storage, \
             patch("app.api.v1.upload.get_supabase_client") as mock_supabase, \
             patch("app.api.v1.upload.UsageTracker") as MockTracker:
            
            # Mock authentication
            mock_get_user.return_value = mock_premium_user
            
            # Mock storage and database
            mock_storage_instance = Mock()
            mock_storage_instance.upload_file.return_value = None
            mock_storage.return_value = mock_storage_instance
            
            mock_supabase_instance = Mock()
            mock_supabase_instance.table.return_value.insert.return_value.execute.return_value = None
            mock_supabase.return_value = mock_supabase_instance
            
            # Mock usage tracker
            tracker_instance = MockTracker.return_value
            tracker_instance.increment_usage.return_value = 500  # Many conversions
            
            # Make request
            response = client.post(
                "/api/v1/upload",
                files={"file": ("large.pdf", large_pdf_file, "application/pdf")}
            )
            
            # Should succeed (202 Accepted) - PREMIUM bypasses all limits
            assert response.status_code == 202
            data = response.json()
            assert "job_id" in data
    
    # ------------------------------------------------------------------------
    # Error Response Schema Validation
    # ------------------------------------------------------------------------
    
    def test_limit_exceeded_error_schema_matches_specification(
        self,
        client,
        valid_pdf_file,
        mock_free_user
    ):
        """403 error response should match LimitExceededError schema."""
        
        with patch("app.core.auth.get_current_user") as mock_get_user, \
             patch("app.middleware.limits.UsageTracker") as MockTracker:
            
            # Mock authentication
            mock_get_user.return_value = mock_free_user
            
            # Mock usage tracker (at limit)
            tracker_instance = MockTracker.return_value
            tracker_instance.get_usage.return_value = {
                "conversion_count": 5,
                "tier_limit": 5,
                "tier": "FREE"
            }
            MockTracker.return_value = tracker_instance
            
            # Make request
            response = client.post(
                "/api/v1/upload",
                files={"file": ("test.pdf", valid_pdf_file, "application/pdf")}
            )
            
            # Validate error schema
            assert response.status_code == 403
            data = response.json()
            
            # Required fields
            assert "detail" in data["detail"]
            assert "code" in data["detail"]
            assert "tier" in data["detail"]
            assert "upgrade_url" in data["detail"]
            
            # Schema-specific fields for CONVERSION_LIMIT_EXCEEDED
            assert "current_count" in data["detail"]
            assert "limit" in data["detail"]
            assert "reset_date" in data["detail"]
            
            # Verify types
            assert isinstance(data["detail"]["detail"], str)
            assert isinstance(data["detail"]["code"], str)
            assert isinstance(data["detail"]["tier"], str)
            assert isinstance(data["detail"]["current_count"], int)
            assert isinstance(data["detail"]["limit"], int)
