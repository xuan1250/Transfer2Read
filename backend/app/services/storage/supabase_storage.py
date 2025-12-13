"""
Supabase Storage Service

Provides file upload, download, and deletion operations using Supabase Storage.
"""
from typing import Optional
from supabase import Client


class StorageUploadError(Exception):
    """Raised when file upload to Supabase Storage fails."""
    pass


class StorageDeleteError(Exception):
    """Raised when file deletion from Supabase Storage fails."""
    pass


class SupabaseStorageService:
    """
    Service for managing file storage operations with Supabase Storage.

    Provides methods for uploading, downloading, and deleting files from
    Supabase Storage buckets with proper error handling and signed URL generation.

    Attributes:
        client: Supabase client instance
        storage: Supabase storage client

    Example:
        >>> from app.core.supabase import get_supabase_client
        >>> supabase = get_supabase_client()
        >>> storage_service = SupabaseStorageService(supabase)
        >>> url = storage_service.upload_file(
        ...     bucket="uploads",
        ...     path="user_id/job_id/document.pdf",
        ...     file_data=b"PDF content",
        ...     content_type="application/pdf"
        ... )
    """

    def __init__(self, supabase_client: Client):
        """
        Initialize the storage service with a Supabase client.

        Args:
            supabase_client: Configured Supabase client instance
        """
        self.client = supabase_client
        self.storage = supabase_client.storage

    def upload_file(
        self,
        bucket: str,
        path: str,
        file_data: bytes,
        content_type: str = "application/pdf"
    ) -> str:
        """
        Upload file to Supabase Storage and return a signed URL.

        Args:
            bucket: Bucket name ('uploads' or 'downloads')
            path: File path within bucket (e.g., 'user_id/job_id/filename.pdf')
            file_data: Binary file content
            content_type: MIME type (default: 'application/pdf')

        Returns:
            Signed URL for secure file access (1-hour expiry)

        Raises:
            StorageUploadError: If upload fails due to network, authentication,
                or storage errors

        Example:
            >>> url = storage_service.upload_file(
            ...     "uploads",
            ...     "550e8400/a1b2c3d4/doc.pdf",
            ...     pdf_bytes,
            ...     "application/pdf"
            ... )
            >>> print(url)  # https://...supabase.co/storage/v1/object/sign/uploads/...
        """
        try:
            # Upload file to Supabase Storage
            self.storage.from_(bucket).upload(
                path,
                file_data,
                {"content-type": content_type, "upsert": "false"}
            )

            # Generate signed URL (1-hour expiry)
            signed_url = self.generate_signed_url(bucket, path, expires_in=3600)
            return signed_url

        except Exception as e:
            raise StorageUploadError(
                f"Failed to upload file to {bucket}/{path}: {str(e)}"
            )

    def generate_signed_url(
        self,
        bucket: str,
        path: str,
        expires_in: int = 3600
    ) -> str:
        """
        Generate a temporary signed URL for secure file access.

        Signed URLs allow temporary access to private files without exposing
        permanent credentials. Default expiry is 1 hour (3600 seconds).

        Args:
            bucket: Bucket name ('uploads' or 'downloads')
            path: File path within bucket
            expires_in: URL expiration time in seconds (default: 3600 = 1 hour)

        Returns:
            Temporary signed URL string

        Example:
            >>> url = storage_service.generate_signed_url(
            ...     "downloads",
            ...     "user_id/job_id/output.epub",
            ...     expires_in=7200  # 2 hours
            ... )
        """
        response = self.storage.from_(bucket).create_signed_url(path, expires_in)
        return response.get('signedURL') or response.get('signed_url', '')

    def delete_file(self, bucket: str, path: str) -> bool:
        """
        Delete file from Supabase Storage.

        Returns True on success, False if file not found or deletion failed.
        This method is idempotent - calling it multiple times for the same
        file will not raise an error.

        Args:
            bucket: Bucket name ('uploads' or 'downloads')
            path: File path within bucket

        Returns:
            True if file was deleted successfully, False if file not found
            or deletion failed

        Example:
            >>> success = storage_service.delete_file(
            ...     "uploads",
            ...     "user_id/job_id/old_file.pdf"
            ... )
            >>> if success:
            ...     print("File deleted")
            ... else:
            ...     print("File not found or already deleted")
        """
        try:
            self.storage.from_(bucket).remove([path])
            return True
        except Exception:
            # File not found or deletion failed - return False (idempotent)
            return False

    def list_files(self, bucket: str, prefix: str = "") -> list[dict]:
        """
        List files in bucket with optional prefix filter.

        Useful for displaying user's files, cleanup operations, or
        fetching conversion history.

        Args:
            bucket: Bucket name ('uploads' or 'downloads')
            prefix: Optional path prefix to filter results
                (e.g., 'user_id/' to list all files for a user)

        Returns:
            List of file metadata dictionaries with keys:
                - name (str): File path
                - id (str): Supabase file ID
                - updated_at (str): Last modified timestamp
                - created_at (str): Creation timestamp
                - last_accessed_at (str): Last access timestamp
                - metadata (dict): Additional file metadata

        Example:
            >>> files = storage_service.list_files(
            ...     "uploads",
            ...     prefix="550e8400-e29b-41d4-a716-446655440000/"
            ... )
            >>> for file in files:
            ...     print(f"{file['name']} - {file['created_at']}")
        """
        response = self.storage.from_(bucket).list(prefix)
        return response
