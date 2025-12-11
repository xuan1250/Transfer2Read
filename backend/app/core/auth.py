"""
Authentication Middleware

JWT validation for Supabase Auth tokens.
Extracts user information from Bearer tokens and provides FastAPI dependency.
"""
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.core.config import settings
from app.schemas.auth import AuthenticatedUser, SubscriptionTier

# HTTP Bearer scheme for Authorization header
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> AuthenticatedUser:
    """
    Validate Supabase JWT and extract user information.
    
    This is a FastAPI dependency that:
    1. Extracts the Bearer token from the Authorization header
    2. Validates the JWT using Supabase's JWT secret
    3. Extracts user_id, email, and tier from the token payload
    
    Args:
        credentials: HTTP Authorization credentials containing Bearer token
        
    Returns:
        AuthenticatedUser: User information from the JWT payload
        
    Raises:
        HTTPException(401): If token is missing, invalid, or expired
        
    Example:
        @app.get("/protected")
        async def protected_route(user: AuthenticatedUser = Depends(get_current_user)):
            return {"user_id": user.user_id}
    """
    token = credentials.credentials
    
    try:
        # Supabase JWT uses HS256 algorithm with the JWT secret
        # Get JWT secret from Supabase project settings → API → JWT Secret
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
        
        # Extract user information from JWT payload
        user_id = payload.get("sub")
        email = payload.get("email")
        user_metadata = payload.get("user_metadata", {})
        tier_value = user_metadata.get("tier", "FREE")
        
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token payload: missing user ID"
            )
        
        # Validate and convert tier to enum
        try:
            tier = SubscriptionTier(tier_value)
        except ValueError:
            tier = SubscriptionTier.FREE
            
        return AuthenticatedUser(
            user_id=user_id,
            email=email or "",
            tier=tier
        )
        
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
