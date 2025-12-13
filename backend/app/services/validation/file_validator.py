"""
File Validation Service

Validates uploaded files for type (PDF via magic bytes) and size (tier-based limits).
"""
import magic
from app.schemas.auth import SubscriptionTier


# Custom Exceptions
class ValidationError(Exception):
    """Base exception for validation errors."""
    pass


class InvalidFileTypeError(ValidationError):
    """Raised when uploaded file is not a PDF (verified by magic bytes)."""
    pass


class FileTooLargeError(ValidationError):
    """Raised when file exceeds tier-based size limit."""
    pass


class FileValidationService:
    """
    Service for validating file uploads.

    Validates:
    - File type using magic bytes (not just extension)
    - File size based on user's subscription tier

    Tier Limits:
    - FREE: 50MB (52,428,800 bytes)
    - PRO/PREMIUM: Unlimited (or 500MB for safety)

    Example:
        >>> validator = FileValidationService()
        >>> validator.validate_pdf(pdf_bytes)  # Raises InvalidFileTypeError if not PDF
        >>> validator.validate_file_size(file_size, "FREE")  # Raises FileTooLargeError if > 50MB
    """

    # File size limits by tier (in bytes)
    FREE_TIER_LIMIT = 50 * 1024 * 1024  # 50MB
    PRO_TIER_LIMIT = 500 * 1024 * 1024  # 500MB (safety limit)
    PREMIUM_TIER_LIMIT = 500 * 1024 * 1024  # 500MB (safety limit)

    def validate_pdf(self, file_data: bytes) -> bool:
        """
        Validate file is a PDF using magic bytes detection.

        Uses python-magic library to detect MIME type from file content,
        not just the file extension. This prevents users from renaming
        non-PDF files to .pdf and uploading them.

        Args:
            file_data: Binary file content to validate

        Returns:
            True if file is a valid PDF

        Raises:
            InvalidFileTypeError: If file is not a PDF (magic bytes mismatch)

        Example:
            >>> with open("document.pdf", "rb") as f:
            ...     data = f.read()
            >>> validator.validate_pdf(data)  # Returns True
            >>>
            >>> with open("image.jpg", "rb") as f:  # Renamed to .pdf
            ...     data = f.read()
            >>> validator.validate_pdf(data)  # Raises InvalidFileTypeError
        """
        # Detect MIME type from file content using magic bytes
        mime_type = magic.from_buffer(file_data, mime=True)

        if mime_type != "application/pdf":
            raise InvalidFileTypeError(
                f"Invalid file type: {mime_type}. Only PDF files are allowed."
            )

        return True

    def validate_file_size(self, file_size: int, user_tier: str | SubscriptionTier) -> bool:
        """
        Validate file size based on user's subscription tier.

        Tier Limits:
        - FREE: 50MB (52,428,800 bytes)
        - PRO: 500MB (524,288,000 bytes)
        - PREMIUM: 500MB (524,288,000 bytes)

        Args:
            file_size: File size in bytes
            user_tier: User's subscription tier (FREE, PRO, or PREMIUM)

        Returns:
            True if file size is within tier limit

        Raises:
            FileTooLargeError: If file exceeds tier limit

        Example:
            >>> # FREE tier user uploads 40MB file
            >>> validator.validate_file_size(40 * 1024 * 1024, "FREE")  # Returns True
            >>>
            >>> # FREE tier user uploads 60MB file
            >>> validator.validate_file_size(60 * 1024 * 1024, "FREE")  # Raises FileTooLargeError
            >>>
            >>> # PRO tier user uploads 60MB file
            >>> validator.validate_file_size(60 * 1024 * 1024, "PRO")  # Returns True
        """
        # Convert tier to string if it's an enum
        if isinstance(user_tier, SubscriptionTier):
            tier_str = user_tier.value
        else:
            tier_str = user_tier.upper()

        # Determine size limit based on tier
        if tier_str == "FREE":
            size_limit = self.FREE_TIER_LIMIT
            limit_mb = 50
        elif tier_str == "PRO":
            size_limit = self.PRO_TIER_LIMIT
            limit_mb = 500
        elif tier_str == "PREMIUM":
            size_limit = self.PREMIUM_TIER_LIMIT
            limit_mb = 500
        else:
            # Unknown tier - default to FREE tier limit (safest)
            size_limit = self.FREE_TIER_LIMIT
            limit_mb = 50

        # Check if file exceeds limit
        if file_size > size_limit:
            file_size_mb = file_size / (1024 * 1024)
            raise FileTooLargeError(
                f"File size ({file_size_mb:.1f}MB) exceeds {tier_str} tier limit ({limit_mb}MB)"
            )

        return True
