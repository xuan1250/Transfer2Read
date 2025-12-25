"""
Admin Authorization Dependencies

FastAPI dependencies for admin-only route protection.
Validates superuser status from Supabase JWT user_metadata.
"""
from fastapi import Depends, HTTPException, status
from app.core.auth import get_current_user
from app.schemas.auth import AuthenticatedUser
from app.core.supabase import get_supabase_client


async def require_superuser(
    user: AuthenticatedUser = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
) -> AuthenticatedUser:
    """
    Dependency to enforce superuser access.

    Checks user_metadata.is_superuser flag from Supabase Auth.
    This flag must be set manually in Supabase for admin users:

    UPDATE auth.users
    SET raw_user_meta_data = jsonb_set(
        COALESCE(raw_user_meta_data, '{}'::jsonb),
        '{is_superuser}',
        'true'::jsonb
    )
    WHERE email = 'admin@example.com';

    Args:
        user: Authenticated user from JWT token (provided by get_current_user dependency)
        supabase: Supabase client (provided by get_supabase_client dependency)

    Returns:
        AuthenticatedUser: The authenticated user if they are a superuser

    Raises:
        HTTPException(403): If user does not have is_superuser=true flag

    Security:
        - Backend enforcement ONLY - frontend checks are UX-only
        - All admin endpoints MUST use this dependency
        - Non-superusers receive 403 Forbidden

    Example:
        @router.get("/admin/stats")
        async def get_stats(user: AuthenticatedUser = Depends(require_superuser)):
            return {"total_users": 150}
    """
    # Fetch user metadata from Supabase to check is_superuser flag
    # Note: JWT may not have is_superuser in payload, so we fetch from Supabase Auth
    try:
        response = supabase.auth.admin.get_user_by_id(user.user_id)

        if not response or not response.user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )

        user_metadata = response.user.user_metadata or {}
        is_superuser = user_metadata.get('is_superuser', False)

        if not is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        # If we can't verify superuser status, deny access
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
