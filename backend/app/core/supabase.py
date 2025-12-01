"""
Supabase Client Configuration

Initializes and provides access to the Supabase client for backend operations.
Uses service_role key for admin access (bypasses Row Level Security policies).
"""
from supabase import create_client, Client
from app.core.config import settings


def get_supabase_client() -> Client:
    """
    Initialize Supabase client with service role key for admin operations.

    IMPORTANT: Use service_role key for backend (not anon key - that's for frontend).
    The service_role key bypasses Row Level Security policies and has full access.

    Returns:
        Client: Configured Supabase client instance

    Example:
        >>> supabase = get_supabase_client()
        >>> result = supabase.table("users").select("*").execute()
    """
    return create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_SERVICE_KEY
    )


async def verify_supabase_connection() -> dict:
    """
    Verify Supabase connection by attempting a simple query.

    Returns:
        dict: Connection status with details
            - connected (bool): Whether connection succeeded
            - error (str, optional): Error message if connection failed

    Example:
        >>> status = await verify_supabase_connection()
        >>> if status["connected"]:
        ...     print("Supabase is ready!")
    """
    try:
        supabase = get_supabase_client()
        # Attempt a simple query to verify connection
        # Query the auth.users table metadata (lightweight operation)
        supabase.table("_health_check").select("*").limit(1).execute()
        return {"connected": True}
    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }
