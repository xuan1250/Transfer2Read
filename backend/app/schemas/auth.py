"""
Authentication Schemas

Pydantic models for authentication and authorization.
"""
from enum import Enum
from pydantic import BaseModel


class SubscriptionTier(str, Enum):
    """User subscription tier levels."""
    FREE = "FREE"
    PRO = "PRO"
    PREMIUM = "PREMIUM"


class AuthenticatedUser(BaseModel):
    """
    Authenticated user information extracted from Supabase JWT.
    
    Attributes:
        user_id: Unique user identifier (UUID string from Supabase Auth)
        email: User's email address
        tier: User's subscription tier (FREE, PRO, or PREMIUM)
    """
    user_id: str
    email: str
    tier: SubscriptionTier = SubscriptionTier.FREE


class TestProtectedResponse(BaseModel):
    """Response model for the /auth/test-protected endpoint."""
    user_id: str
    email: str
    tier: str
