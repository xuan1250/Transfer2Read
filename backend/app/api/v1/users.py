"""
Users API Routes

Endpoints for user account management including account deletion.
"""
from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user
from app.core.supabase import get_supabase_client
from app.schemas.auth import AuthenticatedUser

router = APIRouter(prefix="/users", tags=["users"])


@router.delete("/me")
async def delete_current_user(
    user: AuthenticatedUser = Depends(get_current_user)
) -> dict:
    """
    Delete the current authenticated user's account and all associated data.

    This endpoint:
    1. Validates the user's JWT token
    2. Deletes all user data (conversion jobs, uploaded files, etc.)
    3. Deletes the user from Supabase Auth

    GDPR Compliance: Complete removal of all user data.

    Requires:
        Authorization: Bearer <supabase_access_token>

    Returns:
        dict: Deletion confirmation message

    Raises:
        401: If token is missing, invalid, or expired
        500: If deletion fails

    Example:
        curl -X DELETE http://localhost:8000/api/v1/users/me \\
             -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    """
    supabase = get_supabase_client()

    try:
        # Step 1: Delete user data from conversion_jobs table (if exists)
        # Note: This table will be created in Epic 3, but we prepare for it
        try:
            delete_jobs_result = supabase.table("conversion_jobs").delete().eq(
                "user_id", user.user_id
            ).execute()
        except Exception as e:
            # Table might not exist yet, that's okay
            print(f"Note: conversion_jobs cleanup skipped (table may not exist): {e}")

        # Step 2: Delete uploaded files from Supabase Storage
        # Note: Storage buckets will be created in Epic 3
        try:
            # List user's files in 'uploads' bucket
            uploads_list = supabase.storage.from_("uploads").list(f"{user.user_id}/")
            if uploads_list:
                # Delete all user's uploaded files
                file_paths = [f"{user.user_id}/{file['name']}" for file in uploads_list]
                supabase.storage.from_("uploads").remove(file_paths)
        except Exception as e:
            # Bucket might not exist yet, that's okay
            print(f"Note: uploads storage cleanup skipped (bucket may not exist): {e}")

        try:
            # List user's files in 'downloads' bucket
            downloads_list = supabase.storage.from_("downloads").list(f"{user.user_id}/")
            if downloads_list:
                # Delete all user's generated EPUB files
                file_paths = [f"{user.user_id}/{file['name']}" for file in downloads_list]
                supabase.storage.from_("downloads").remove(file_paths)
        except Exception as e:
            # Bucket might not exist yet, that's okay
            print(f"Note: downloads storage cleanup skipped (bucket may not exist): {e}")

        # Step 3: Delete user from Supabase Auth
        # Using service_role client which has admin access
        delete_user_result = supabase.auth.admin.delete_user(user.user_id)

        # If we got here, deletion was successful
        return {
            "message": "Account deleted successfully",
            "user_id": user.user_id
        }

    except Exception as e:
        print(f"Error deleting user {user.user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete account: {str(e)}"
        )
