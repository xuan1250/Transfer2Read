"""
Unit Tests for Supabase Storage Service

Tests file upload, download, deletion, and signed URL generation operations.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.storage.supabase_storage import (
    SupabaseStorageService,
    StorageUploadError,
    StorageDeleteError,
)


@pytest.fixture
def mock_supabase_client():
    """
    Create a mock Supabase client for testing.

    Returns:
        Mock: Configured mock Supabase client with storage operations
    """
    client = Mock()
    client.storage = Mock()
    return client


@pytest.fixture
def storage_service(mock_supabase_client):
    """
    Create SupabaseStorageService instance with mocked client.

    Args:
        mock_supabase_client: Mocked Supabase client fixture

    Returns:
        SupabaseStorageService: Service instance for testing
    """
    return SupabaseStorageService(mock_supabase_client)


class TestUploadFile:
    """Test cases for upload_file method."""

    def test_upload_file_success(self, storage_service, mock_supabase_client):
        """Test successful file upload returns signed URL."""
        # Mock upload success
        mock_bucket = Mock()
        mock_bucket.upload.return_value = {"Key": "uploads/user/job/file.pdf"}
        mock_bucket.create_signed_url.return_value = {
            "signedURL": "https://example.com/signed-url"
        }
        mock_supabase_client.storage.from_.return_value = mock_bucket

        # Call upload_file
        result = storage_service.upload_file(
            bucket="uploads",
            path="user_id/job_id/test.pdf",
            file_data=b"PDF content",
            content_type="application/pdf"
        )

        # Verify
        assert result == "https://example.com/signed-url"
        mock_bucket.upload.assert_called_once_with(
            "user_id/job_id/test.pdf",
            b"PDF content",
            {"content-type": "application/pdf", "upsert": "false"}
        )
        mock_bucket.create_signed_url.assert_called_once_with(
            "user_id/job_id/test.pdf",
            3600
        )

    def test_upload_file_invalid_bucket(self, storage_service, mock_supabase_client):
        """Test upload to invalid bucket raises StorageUploadError."""
        # Mock upload failure
        mock_bucket = Mock()
        mock_bucket.upload.side_effect = Exception("Bucket not found")
        mock_supabase_client.storage.from_.return_value = mock_bucket

        # Expect StorageUploadError
        with pytest.raises(StorageUploadError) as exc_info:
            storage_service.upload_file(
                bucket="invalid_bucket",
                path="test.pdf",
                file_data=b"data",
                content_type="application/pdf"
            )

        assert "Failed to upload file to invalid_bucket/test.pdf" in str(exc_info.value)
        assert "Bucket not found" in str(exc_info.value)

    def test_upload_file_network_error(self, storage_service, mock_supabase_client):
        """Test network failure during upload raises StorageUploadError."""
        # Mock network error
        mock_bucket = Mock()
        mock_bucket.upload.side_effect = Exception("Network timeout")
        mock_supabase_client.storage.from_.return_value = mock_bucket

        # Expect StorageUploadError
        with pytest.raises(StorageUploadError) as exc_info:
            storage_service.upload_file(
                bucket="uploads",
                path="user/job/file.pdf",
                file_data=b"data"
            )

        assert "Network timeout" in str(exc_info.value)


class TestGenerateSignedUrl:
    """Test cases for generate_signed_url method."""

    def test_generate_signed_url_default_expiry(
        self, storage_service, mock_supabase_client
    ):
        """Test signed URL generation with default 1-hour expiry."""
        # Mock signed URL response
        mock_bucket = Mock()
        mock_bucket.create_signed_url.return_value = {
            "signedURL": "https://supabase.co/storage/signed/url"
        }
        mock_supabase_client.storage.from_.return_value = mock_bucket

        # Call generate_signed_url
        result = storage_service.generate_signed_url(
            bucket="downloads",
            path="user/job/output.epub"
        )

        # Verify
        assert result == "https://supabase.co/storage/signed/url"
        mock_bucket.create_signed_url.assert_called_once_with(
            "user/job/output.epub",
            3600  # Default 1 hour
        )

    def test_generate_signed_url_custom_expiry(
        self, storage_service, mock_supabase_client
    ):
        """Test signed URL generation with custom expiry time."""
        # Mock signed URL response
        mock_bucket = Mock()
        mock_bucket.create_signed_url.return_value = {
            "signedURL": "https://supabase.co/storage/signed/url-2h"
        }
        mock_supabase_client.storage.from_.return_value = mock_bucket

        # Call with 2-hour expiry
        result = storage_service.generate_signed_url(
            bucket="downloads",
            path="user/job/output.epub",
            expires_in=7200  # 2 hours
        )

        # Verify
        assert result == "https://supabase.co/storage/signed/url-2h"
        mock_bucket.create_signed_url.assert_called_once_with(
            "user/job/output.epub",
            7200
        )

    def test_generate_signed_url_alternative_key(
        self, storage_service, mock_supabase_client
    ):
        """Test signed URL with alternative response key format."""
        # Some Supabase versions use 'signed_url' instead of 'signedURL'
        mock_bucket = Mock()
        mock_bucket.create_signed_url.return_value = {
            "signed_url": "https://supabase.co/storage/alt-url"
        }
        mock_supabase_client.storage.from_.return_value = mock_bucket

        result = storage_service.generate_signed_url(
            bucket="uploads",
            path="file.pdf"
        )

        assert result == "https://supabase.co/storage/alt-url"


class TestDeleteFile:
    """Test cases for delete_file method."""

    def test_delete_file_success(self, storage_service, mock_supabase_client):
        """Test successful file deletion returns True."""
        # Mock successful deletion
        mock_bucket = Mock()
        mock_bucket.remove.return_value = {"message": "Success"}
        mock_supabase_client.storage.from_.return_value = mock_bucket

        # Call delete_file
        result = storage_service.delete_file(
            bucket="uploads",
            path="user/job/old_file.pdf"
        )

        # Verify
        assert result is True
        mock_bucket.remove.assert_called_once_with(["user/job/old_file.pdf"])

    def test_delete_file_not_found(self, storage_service, mock_supabase_client):
        """Test deleting non-existent file returns False (graceful handling)."""
        # Mock file not found error
        mock_bucket = Mock()
        mock_bucket.remove.side_effect = Exception("File not found")
        mock_supabase_client.storage.from_.return_value = mock_bucket

        # Call delete_file
        result = storage_service.delete_file(
            bucket="uploads",
            path="user/job/nonexistent.pdf"
        )

        # Verify - should return False, not raise exception
        assert result is False

    def test_delete_file_idempotent(self, storage_service, mock_supabase_client):
        """Test calling delete multiple times doesn't raise errors."""
        # Mock deletion failure (file already gone)
        mock_bucket = Mock()
        mock_bucket.remove.side_effect = Exception("Not found")
        mock_supabase_client.storage.from_.return_value = mock_bucket

        # Call delete twice
        result1 = storage_service.delete_file("uploads", "file.pdf")
        result2 = storage_service.delete_file("uploads", "file.pdf")

        # Both should return False without errors
        assert result1 is False
        assert result2 is False


class TestListFiles:
    """Test cases for list_files method."""

    def test_list_files_with_prefix(self, storage_service, mock_supabase_client):
        """Test listing files with user prefix filter."""
        # Mock file listing response
        mock_bucket = Mock()
        mock_bucket.list.return_value = [
            {
                "name": "user123/job1/file1.pdf",
                "id": "file-id-1",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z"
            },
            {
                "name": "user123/job2/file2.pdf",
                "id": "file-id-2",
                "created_at": "2025-01-02T00:00:00Z",
                "updated_at": "2025-01-02T00:00:00Z"
            }
        ]
        mock_supabase_client.storage.from_.return_value = mock_bucket

        # Call list_files with prefix
        result = storage_service.list_files(
            bucket="uploads",
            prefix="user123/"
        )

        # Verify
        assert len(result) == 2
        assert result[0]["name"] == "user123/job1/file1.pdf"
        assert result[1]["name"] == "user123/job2/file2.pdf"
        mock_bucket.list.assert_called_once_with("user123/")

    def test_list_files_empty_bucket(self, storage_service, mock_supabase_client):
        """Test listing files in empty bucket returns empty list."""
        # Mock empty response
        mock_bucket = Mock()
        mock_bucket.list.return_value = []
        mock_supabase_client.storage.from_.return_value = mock_bucket

        # Call list_files
        result = storage_service.list_files(
            bucket="downloads",
            prefix="user456/"
        )

        # Verify
        assert result == []
        mock_bucket.list.assert_called_once_with("user456/")

    def test_list_files_no_prefix(self, storage_service, mock_supabase_client):
        """Test listing all files without prefix filter."""
        # Mock response
        mock_bucket = Mock()
        mock_bucket.list.return_value = [
            {"name": "user1/job1/file.pdf"},
            {"name": "user2/job2/file.pdf"}
        ]
        mock_supabase_client.storage.from_.return_value = mock_bucket

        # Call without prefix
        result = storage_service.list_files(bucket="uploads")

        # Verify
        assert len(result) == 2
        mock_bucket.list.assert_called_once_with("")
