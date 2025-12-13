"""
Unit Tests for File Validation Service

Tests PDF validation and file size checking based on subscription tiers.
"""
import pytest
from app.services.validation import (
    FileValidationService,
    InvalidFileTypeError,
    FileTooLargeError
)


class TestFileValidationService:
    """Test suite for FileValidationService"""

    @pytest.fixture
    def validator(self):
        """Fixture providing FileValidationService instance"""
        return FileValidationService()

    def test_validate_pdf_with_valid_pdf(self, validator):
        """Test that valid PDF file passes validation"""
        # Create minimal valid PDF header
        pdf_data = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n"
        assert validator.validate_pdf(pdf_data) is True

    def test_validate_pdf_with_text_file(self, validator):
        """Test that text file fails PDF validation"""
        text_data = b"This is just a text file, not a PDF"
        with pytest.raises(InvalidFileTypeError) as exc_info:
            validator.validate_pdf(text_data)
        assert "Invalid file type" in str(exc_info.value)

    def test_validate_pdf_with_html_file(self, validator):
        """Test that HTML file fails PDF validation"""
        html_data = b"<html><body>Not a PDF</body></html>"
        with pytest.raises(InvalidFileTypeError) as exc_info:
            validator.validate_pdf(html_data)
        assert "text/html" in str(exc_info.value)

    def test_validate_file_size_free_tier_within_limit(self, validator):
        """Test that file under 50MB passes for FREE tier"""
        # 40MB file
        file_size = 40 * 1024 * 1024
        assert validator.validate_file_size(file_size, "FREE") is True

    def test_validate_file_size_free_tier_exactly_limit(self, validator):
        """Test that exactly 50MB file passes for FREE tier (inclusive)"""
        # Exactly 50MB
        file_size = 50 * 1024 * 1024
        assert validator.validate_file_size(file_size, "FREE") is True

    def test_validate_file_size_free_tier_exceeds_limit(self, validator):
        """Test that file over 50MB fails for FREE tier"""
        # 60MB file
        file_size = 60 * 1024 * 1024
        with pytest.raises(FileTooLargeError) as exc_info:
            validator.validate_file_size(file_size, "FREE")
        assert "60.0MB" in str(exc_info.value)
        assert "50MB" in str(exc_info.value)

    def test_validate_file_size_free_tier_one_byte_over(self, validator):
        """Test that 50MB + 1 byte fails for FREE tier"""
        # 50MB + 1 byte
        file_size = (50 * 1024 * 1024) + 1
        with pytest.raises(FileTooLargeError):
            validator.validate_file_size(file_size, "FREE")

    def test_validate_file_size_pro_tier_large_file(self, validator):
        """Test that 100MB file passes for PRO tier"""
        # 100MB file
        file_size = 100 * 1024 * 1024
        assert validator.validate_file_size(file_size, "PRO") is True

    def test_validate_file_size_pro_tier_very_large_file(self, validator):
        """Test that 200MB file passes for PRO tier"""
        # 200MB file (still under 500MB limit)
        file_size = 200 * 1024 * 1024
        assert validator.validate_file_size(file_size, "PRO") is True

    def test_validate_file_size_pro_tier_exceeds_limit(self, validator):
        """Test that file over 500MB fails even for PRO tier"""
        # 600MB file (exceeds safety limit)
        file_size = 600 * 1024 * 1024
        with pytest.raises(FileTooLargeError) as exc_info:
            validator.validate_file_size(file_size, "PRO")
        assert "600.0MB" in str(exc_info.value)

    def test_validate_file_size_premium_tier_large_file(self, validator):
        """Test that 100MB file passes for PREMIUM tier"""
        # 100MB file
        file_size = 100 * 1024 * 1024
        assert validator.validate_file_size(file_size, "PREMIUM") is True

    def test_validate_file_size_with_subscription_tier_enum(self, validator):
        """Test validation with SubscriptionTier enum instead of string"""
        from app.schemas.auth import SubscriptionTier

        # 40MB file with enum
        file_size = 40 * 1024 * 1024
        assert validator.validate_file_size(file_size, SubscriptionTier.FREE) is True

        # 60MB file with enum should fail for FREE
        file_size = 60 * 1024 * 1024
        with pytest.raises(FileTooLargeError):
            validator.validate_file_size(file_size, SubscriptionTier.FREE)

    def test_validate_file_size_unknown_tier_defaults_to_free(self, validator):
        """Test that unknown tier defaults to FREE tier limits"""
        # 60MB file with unknown tier
        file_size = 60 * 1024 * 1024
        with pytest.raises(FileTooLargeError):
            validator.validate_file_size(file_size, "UNKNOWN_TIER")

    def test_validate_file_size_case_insensitive(self, validator):
        """Test that tier names are case-insensitive"""
        # 40MB file with lowercase tier
        file_size = 40 * 1024 * 1024
        assert validator.validate_file_size(file_size, "free") is True
        assert validator.validate_file_size(file_size, "pro") is True
        assert validator.validate_file_size(file_size, "premium") is True
