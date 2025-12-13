"""
Unit Tests for Storage Utility Functions

Tests filename sanitization and storage path generation.
"""
import pytest
from app.services.storage.utils import sanitize_filename, generate_storage_path


class TestSanitizeFilename:
    """Test cases for sanitize_filename function."""

    def test_sanitize_basic_filename(self):
        """Test basic filename remains unchanged."""
        assert sanitize_filename("document.pdf") == "document.pdf"
        assert sanitize_filename("file.txt") == "file.txt"
        assert sanitize_filename("image.png") == "image.png"

    def test_sanitize_filename_with_spaces(self):
        """Test spaces are replaced with underscores."""
        assert sanitize_filename("My Document.pdf") == "My_Document.pdf"
        assert sanitize_filename("test file name.txt") == "test_file_name.txt"

    def test_sanitize_filename_with_parentheses(self):
        """Test parentheses are removed."""
        assert sanitize_filename("My Document (1).pdf") == "My_Document_1.pdf"
        assert sanitize_filename("file (copy).txt") == "file_copy.txt"

    def test_sanitize_filename_special_characters(self):
        """Test forbidden characters are removed."""
        # Test individual forbidden characters
        assert sanitize_filename("test<file.pdf") == "testfile.pdf"
        assert sanitize_filename("test>file.pdf") == "testfile.pdf"
        assert sanitize_filename('test:file.pdf') == "testfile.pdf"
        assert sanitize_filename('test"file.pdf') == "testfile.pdf"
        assert sanitize_filename("test/file.pdf") == "testfile.pdf"
        assert sanitize_filename("test\\file.pdf") == "testfile.pdf"
        assert sanitize_filename("test|file.pdf") == "testfile.pdf"
        assert sanitize_filename("test?file.pdf") == "testfile.pdf"
        assert sanitize_filename("test*file.pdf") == "testfile.pdf"

    def test_sanitize_filename_multiple_special_chars(self):
        """Test multiple special characters are removed."""
        assert sanitize_filename("test<>:file.pdf") == "testfile.pdf"
        assert sanitize_filename('test"/\\|?*file.pdf') == "testfile.pdf"

    def test_sanitize_filename_multiple_underscores(self):
        """Test multiple consecutive underscores are collapsed."""
        assert sanitize_filename("test    file.pdf") == "test_file.pdf"
        assert sanitize_filename("test  (  )  file.pdf") == "test_file.pdf"

    def test_sanitize_filename_long_name(self):
        """Test long filenames are truncated to 255 characters."""
        # Create a filename longer than 255 chars
        long_name = "a" * 300 + ".pdf"
        result = sanitize_filename(long_name)

        # Should be exactly 255 characters
        assert len(result) == 255
        # Should preserve extension
        assert result.endswith(".pdf")
        # Should truncate the name part
        assert result == ("a" * 251) + ".pdf"

    def test_sanitize_filename_long_name_no_extension(self):
        """Test long filename without extension is truncated to 255."""
        long_name = "a" * 300
        result = sanitize_filename(long_name)

        assert len(result) == 255
        assert result == "a" * 255

    def test_sanitize_filename_preserves_extension(self):
        """Test file extension is always preserved."""
        assert sanitize_filename("test.pdf") == "test.pdf"
        assert sanitize_filename("test.epub") == "test.epub"
        assert sanitize_filename("test.tar.gz") == "test.tar.gz"

    def test_sanitize_filename_edge_cases(self):
        """Test edge cases like dots, dashes, underscores."""
        # These should be preserved
        assert sanitize_filename("test-file.pdf") == "test-file.pdf"
        assert sanitize_filename("test_file.pdf") == "test_file.pdf"
        assert sanitize_filename("test.file.pdf") == "test.file.pdf"


class TestGenerateStoragePath:
    """Test cases for generate_storage_path function."""

    def test_generate_storage_path_basic(self):
        """Test basic path generation with valid UUIDs."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        job_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        filename = "document.pdf"

        result = generate_storage_path(user_id, job_id, filename)

        expected = f"{user_id}/{job_id}/document.pdf"
        assert result == expected

    def test_generate_storage_path_sanitizes_filename(self):
        """Test filename is sanitized in generated path."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        job_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        filename = "My Document (1).pdf"

        result = generate_storage_path(user_id, job_id, filename)

        expected = f"{user_id}/{job_id}/My_Document_1.pdf"
        assert result == expected

    def test_generate_storage_path_invalid_user_id(self):
        """Test ValueError raised for invalid user_id UUID."""
        with pytest.raises(ValueError) as exc_info:
            generate_storage_path(
                user_id="invalid-uuid",
                job_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                filename="test.pdf"
            )

        assert "Invalid UUID format" in str(exc_info.value)

    def test_generate_storage_path_invalid_job_id(self):
        """Test ValueError raised for invalid job_id UUID."""
        with pytest.raises(ValueError) as exc_info:
            generate_storage_path(
                user_id="550e8400-e29b-41d4-a716-446655440000",
                job_id="not-a-uuid",
                filename="test.pdf"
            )

        assert "Invalid UUID format" in str(exc_info.value)

    def test_generate_storage_path_empty_filename(self):
        """Test ValueError raised for empty filename after sanitization."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        job_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

        # Filename with only special characters becomes empty after sanitization
        with pytest.raises(ValueError) as exc_info:
            generate_storage_path(user_id, job_id, "<>:?*")

        assert "Filename cannot be empty" in str(exc_info.value)

    def test_generate_storage_path_with_special_chars(self):
        """Test path generation with filename containing special characters."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        job_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        filename = "test<file>:name.pdf"

        result = generate_storage_path(user_id, job_id, filename)

        # Special characters should be removed
        expected = f"{user_id}/{job_id}/testfilename.pdf"
        assert result == expected

    def test_generate_storage_path_preserves_structure(self):
        """Test path structure is always user_id/job_id/filename."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        job_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        filename = "test.pdf"

        result = generate_storage_path(user_id, job_id, filename)

        # Verify structure
        parts = result.split('/')
        assert len(parts) == 3
        assert parts[0] == user_id
        assert parts[1] == job_id
        assert parts[2] == "test.pdf"
