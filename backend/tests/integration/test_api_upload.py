"""
Integration Tests for Upload API

Tests the complete upload flow including authentication, validation,
storage, and database operations.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO


@pytest.mark.asyncio
class TestUploadAPI:
    """Integration test suite for PDF upload endpoint"""

    @patch('app.api.v1.upload.get_supabase_client')
    @patch('app.api.v1.upload.SupabaseStorageService')
    async def test_upload_pdf_success(
        self,
        mock_storage_service_class,
        mock_supabase_client,
        client,
        valid_jwt_token,
        valid_pdf_bytes
    ):
        """Test successful PDF upload by authenticated FREE tier user"""
        # Mock storage service
        mock_storage = Mock()
        mock_storage.upload_file.return_value = "https://storage.supabase.co/signed-url"
        mock_storage_service_class.return_value = mock_storage

        # Mock Supabase client
        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value = Mock()
        mock_supabase = Mock()
        mock_supabase.table.return_value = mock_table
        mock_supabase_client.return_value = mock_supabase

        # Upload PDF
        files = {"file": ("test.pdf", BytesIO(valid_pdf_bytes), "application/pdf")}
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = await client.post("/api/v1/upload", files=files, headers=headers)

        # Assertions
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "UPLOADED"
        assert data["input_file"] == "test.pdf"
        assert "created_at" in data

        # Verify storage upload was called
        mock_storage.upload_file.assert_called_once()
        call_args = mock_storage.upload_file.call_args
        assert call_args[1]["bucket"] == "uploads"
        assert "test-user-id-123" in call_args[1]["path"]
        assert call_args[1]["content_type"] == "application/pdf"

        # Verify database insert was called
        mock_supabase.table.assert_called_with("conversion_jobs")
        mock_table.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_without_auth_token(self, client, valid_pdf_bytes):
        """Test upload without Authorization header returns 401"""
        files = {"file": ("test.pdf", BytesIO(valid_pdf_bytes), "application/pdf")}

        response = await client.post("/api/v1/upload", files=files)

        assert response.status_code == 401  # HTTPBearer returns 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_upload_with_invalid_token(self, client, valid_pdf_bytes):
        """Test upload with malformed JWT returns 401"""
        files = {"file": ("test.pdf", BytesIO(valid_pdf_bytes), "application/pdf")}
        headers = {"Authorization": "Bearer invalid.jwt.token"}

        response = await client.post("/api/v1/upload", files=files, headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_upload_with_expired_token(self, client, expired_jwt_token, valid_pdf_bytes):
        """Test upload with expired JWT returns 401"""
        files = {"file": ("test.pdf", BytesIO(valid_pdf_bytes), "application/pdf")}
        headers = {"Authorization": f"Bearer {expired_jwt_token}"}

        response = await client.post("/api/v1/upload", files=files, headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, client, valid_jwt_token, jpeg_file_bytes):
        """Test upload of non-PDF file returns 400 INVALID_FILE_TYPE"""
        files = {"file": ("image.jpg", BytesIO(jpeg_file_bytes), "image/jpeg")}
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = await client.post("/api/v1/upload", files=files, headers=headers)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        # HTTPException wraps detail in another dict
        if isinstance(data["detail"], dict):
            assert data["detail"]["code"] == "INVALID_FILE_TYPE"
            assert "Invalid file type" in data["detail"]["detail"]
        else:
            assert "Invalid file type" in data["detail"]

    @pytest.mark.asyncio
    async def test_upload_oversized_file_free_tier(
        self,
        client,
        valid_jwt_token,
        large_pdf_bytes
    ):
        """Test upload of 60MB file for FREE tier returns 413 FILE_TOO_LARGE"""
        files = {"file": ("large.pdf", BytesIO(large_pdf_bytes), "application/pdf")}
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = await client.post("/api/v1/upload", files=files, headers=headers)

        assert response.status_code == 413
        data = response.json()
        assert "detail" in data
        # HTTPException wraps detail
        if isinstance(data["detail"], dict):
            assert data["detail"]["code"] == "FILE_TOO_LARGE"
            assert "60" in data["detail"]["detail"]  # 60MB in error message
        else:
            assert "60" in data["detail"]

    @patch('app.api.v1.upload.get_supabase_client')
    @patch('app.api.v1.upload.SupabaseStorageService')
    @pytest.mark.asyncio
    async def test_upload_large_file_pro_tier(
        self,
        mock_storage_service_class,
        mock_supabase_client,
        client,
        pro_tier_jwt_token,
        large_pdf_bytes
    ):
        """Test upload of 60MB file for PRO tier succeeds"""
        # Mock storage service
        mock_storage = Mock()
        mock_storage.upload_file.return_value = "https://storage.supabase.co/signed-url"
        mock_storage_service_class.return_value = mock_storage

        # Mock Supabase client
        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value = Mock()
        mock_supabase = Mock()
        mock_supabase.table.return_value = mock_table
        mock_supabase_client.return_value = mock_supabase

        files = {"file": ("large.pdf", BytesIO(large_pdf_bytes), "application/pdf")}
        headers = {"Authorization": f"Bearer {pro_tier_jwt_token}"}

        response = await client.post("/api/v1/upload", files=files, headers=headers)

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "UPLOADED"

    @pytest.mark.asyncio
    async def test_upload_missing_file_parameter(self, client, valid_jwt_token):
        """Test upload without file parameter returns 422 validation error"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = await client.post("/api/v1/upload", headers=headers)

        assert response.status_code == 422  # FastAPI validation error
        data = response.json()
        assert "detail" in data

    @patch('app.api.v1.upload.get_supabase_client')
    @patch('app.api.v1.upload.SupabaseStorageService')
    @pytest.mark.asyncio
    async def test_upload_storage_error(
        self,
        mock_storage_service_class,
        mock_supabase_client,
        client,
        valid_jwt_token,
        valid_pdf_bytes
    ):
        """Test storage upload failure returns 500 STORAGE_ERROR"""
        from app.services.storage.supabase_storage import StorageUploadError

        # Mock storage service to raise error
        mock_storage = Mock()
        mock_storage.upload_file.side_effect = StorageUploadError("Network timeout")
        mock_storage_service_class.return_value = mock_storage

        files = {"file": ("test.pdf", BytesIO(valid_pdf_bytes), "application/pdf")}
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = await client.post("/api/v1/upload", files=files, headers=headers)

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        if isinstance(data["detail"], dict):
            assert data["detail"]["code"] == "STORAGE_ERROR"
        else:
            assert "Storage upload failed" in data["detail"]

    @patch('app.api.v1.upload.get_supabase_client')
    @patch('app.api.v1.upload.SupabaseStorageService')
    @pytest.mark.asyncio
    async def test_upload_database_error(
        self,
        mock_storage_service_class,
        mock_supabase_client,
        client,
        valid_jwt_token,
        valid_pdf_bytes
    ):
        """Test database insert failure returns 500 DATABASE_ERROR"""
        # Mock storage service (succeeds)
        mock_storage = Mock()
        mock_storage.upload_file.return_value = "https://storage.supabase.co/signed-url"
        mock_storage.delete_file.return_value = True
        mock_storage_service_class.return_value = mock_storage

        # Mock Supabase client to fail on insert
        mock_table = Mock()
        mock_table.insert.side_effect = Exception("Database connection failed")
        mock_supabase = Mock()
        mock_supabase.table.return_value = mock_table
        mock_supabase_client.return_value = mock_supabase

        files = {"file": ("test.pdf", BytesIO(valid_pdf_bytes), "application/pdf")}
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = await client.post("/api/v1/upload", files=files, headers=headers)

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        if isinstance(data["detail"], dict):
            assert data["detail"]["code"] == "DATABASE_ERROR"
        else:
            assert "Database error" in data["detail"]

        # Verify cleanup was attempted
        mock_storage.delete_file.assert_called_once()

    @patch('app.api.v1.upload.get_supabase_client')
    @patch('app.api.v1.upload.SupabaseStorageService')
    @pytest.mark.asyncio
    async def test_upload_response_format(
        self,
        mock_storage_service_class,
        mock_supabase_client,
        client,
        valid_jwt_token,
        valid_pdf_bytes
    ):
        """Test response contains all required fields in correct format"""
        # Mock storage service
        mock_storage = Mock()
        mock_storage.upload_file.return_value = "https://storage.supabase.co/signed-url"
        mock_storage_service_class.return_value = mock_storage

        # Mock Supabase client
        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value = Mock()
        mock_supabase = Mock()
        mock_supabase.table.return_value = mock_table
        mock_supabase_client.return_value = mock_supabase

        files = {"file": ("document.pdf", BytesIO(valid_pdf_bytes), "application/pdf")}
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = await client.post("/api/v1/upload", files=files, headers=headers)

        assert response.status_code == 202
        data = response.json()

        # Verify all required fields present
        assert "job_id" in data
        assert "status" in data
        assert "input_file" in data
        assert "created_at" in data

        # Verify field values
        assert isinstance(data["job_id"], str)
        assert len(data["job_id"]) == 36  # UUID format
        assert data["status"] == "UPLOADED"
        assert data["input_file"] == "document.pdf"
        assert "T" in data["created_at"]  # ISO 8601 timestamp format
