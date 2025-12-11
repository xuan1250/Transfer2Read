"""
Auth API Routes

Test endpoints for verifying authentication functionality.
"""
from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.schemas.auth import AuthenticatedUser, TestProtectedResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/test-protected", response_model=TestProtectedResponse)
async def test_protected(
    user: AuthenticatedUser = Depends(get_current_user)
) -> TestProtectedResponse:
    """
    Test protected endpoint requiring authentication.
    
    This endpoint validates the Supabase JWT token from the Authorization header
    and returns the authenticated user's information.
    
    Requires:
        Authorization: Bearer <supabase_access_token>
    
    Returns:
        TestProtectedResponse: User ID, email, and subscription tier
        
    Raises:
        401: If token is missing, invalid, or expired
        
    Example:
        curl -X POST http://localhost:8000/api/v1/auth/test-protected \\
             -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    """
    return TestProtectedResponse(
        user_id=user.user_id,
        email=user.email,
        tier=user.tier.value
    )
