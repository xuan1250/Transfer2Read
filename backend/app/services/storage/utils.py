"""
Storage Utility Functions

Provides helper functions for file path generation and filename sanitization.
"""
import re
from uuid import UUID


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing special characters and limiting length.

    Removes or replaces characters that are invalid in file paths or could
    cause security issues (path traversal attacks). Preserves file extension.

    Rules:
    - Removes special characters: <>:"/\\|?*
    - Replaces spaces with underscores
    - Limits total length to 255 characters (filesystem limit)
    - Preserves file extension when truncating

    Args:
        filename: Original filename to sanitize

    Returns:
        Sanitized filename safe for storage

    Examples:
        >>> sanitize_filename("My Document (1).pdf")
        'My_Document_1.pdf'
        >>> sanitize_filename("test<>file:data.pdf")
        'testfiledata.pdf'
        >>> sanitize_filename("a" * 300 + ".pdf")
        'aaa...aaa.pdf'  # Truncated to 255 chars
    """
    # Remove special characters that are invalid in file paths
    # <>:"/\\|?* are forbidden in most filesystems
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)

    # Replace parentheses with nothing (cleaner than underscores)
    filename = re.sub(r'[()]', '', filename)

    # Replace spaces with underscores for URL-friendliness
    filename = filename.replace(' ', '_')

    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)

    # Limit to 255 characters (filesystem limit)
    if len(filename) > 255:
        # Try to preserve extension
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
            # Reserve space for extension + dot
            max_name_length = 255 - len(ext) - 1
            filename = name[:max_name_length] + '.' + ext
        else:
            filename = filename[:255]

    return filename


def generate_storage_path(user_id: str, job_id: str, filename: str) -> str:
    """
    Generate storage path following naming convention: {user_id}/{job_id}/{filename}

    This path structure ensures:
    - No collisions between users (user_id isolation)
    - No collisions within user (job_id uniqueness)
    - Clean organization for RLS policies
    - Easy cleanup by user or job

    Args:
        user_id: UUID string of user (from auth.uid())
        job_id: UUID string of conversion job
        filename: Original filename (will be sanitized)

    Returns:
        Full storage path in format: user_id/job_id/sanitized_filename

    Raises:
        ValueError: If user_id or job_id are not valid UUIDs, or if
            filename becomes empty after sanitization

    Examples:
        >>> generate_storage_path(
        ...     "550e8400-e29b-41d4-a716-446655440000",
        ...     "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        ...     "document.pdf"
        ... )
        '550e8400-e29b-41d4-a716-446655440000/a1b2c3d4-e5f6-7890-abcd-ef1234567890/document.pdf'

        >>> generate_storage_path(
        ...     "550e8400-e29b-41d4-a716-446655440000",
        ...     "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        ...     "My Document (1).pdf"
        ... )
        '550e8400-e29b-41d4-a716-446655440000/a1b2c3d4-e5f6-7890-abcd-ef1234567890/My_Document_1.pdf'
    """
    # Validate UUIDs (raises ValueError if invalid)
    try:
        UUID(user_id)
        UUID(job_id)
    except ValueError as e:
        raise ValueError(f"Invalid UUID format: {str(e)}")

    # Sanitize filename
    safe_filename = sanitize_filename(filename)

    if not safe_filename:
        raise ValueError(
            f"Filename cannot be empty after sanitization. Original: {filename}"
        )

    return f"{user_id}/{job_id}/{safe_filename}"
