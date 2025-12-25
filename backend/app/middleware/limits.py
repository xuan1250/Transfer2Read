"""
Limit Enforcement Middleware

FastAPI dependency for checking subscription tier limits before processing uploads.
Enforces file size and monthly conversion limits based on user tier.
"""
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Request
import logging

from app.core.auth import get_current_user
from app.core.limits import get_file_size_limit, get_conversion_limit
from app.core.supabase import get_supabase_client
from app.core.redis_client import get_cached_redis_client
from app.schemas.auth import AuthenticatedUser, SubscriptionTier
from app.services.usage_tracker import UsageTracker

logger = logging.getLogger(__name__)


async def check_tier_limits(
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> None:
    """
    FastAPI dependency that checks tier limits before upload processing.
    
    This dependency:
    1. Checks user's subscription tier (FREE, PRO, PREMIUM)
    2. Bypasses all checks for PRO/PREMIUM users (unlimited access)
    3. For FREE users:
       - Checks file size against 50MB limit
       - Checks monthly conversion count against 5/month limit
    4. Raises HTTPException(403) if any limit is exceeded
    
    Args:
        request: FastAPI Request object (for accessing Content-Length header)
        current_user: Authenticated user from JWT (injected by get_current_user)
        
    Returns:
        None (successful validation)
        
    Raises:
        HTTPException(403): If file size or conversion limit exceeded
        
    Security:
        - Uses user_id from authenticated session only
        - Never trusts client-provided tier data
        - Defaults to FREE tier if tier metadata missing
        
    Example:
        @router.post("/upload")
        async def upload(
            file: UploadFile,
            user: AuthenticatedUser = Depends(get_current_user),
            _: None = Depends(check_tier_limits)  # Limit check runs automatically
        ):
            # Upload logic here
            pass
    """
    user_id = current_user.user_id
    tier = current_user.tier.value if current_user.tier else "FREE"
    tier = tier.upper()
    
    # Bypass all checks for PRO/PREMIUM users
    if tier in ("PRO", "PREMIUM"):
        logger.info(f"User {user_id} bypassed limit checks (tier: {tier})")
        return None
    
    # Default to FREE tier if unrecognized
    if tier not in ("FREE", "PRO", "PREMIUM"):
        logger.warning(f"Unrecognized tier '{tier}' for user {user_id}, defaulting to FREE")
        tier = "FREE"
    
    # Check 1: File Size Limit
    content_length = request.headers.get("content-length")
    if content_length:
        file_size = int(content_length)
        max_size = get_file_size_limit(tier)
        
        if max_size and file_size > max_size:
            max_size_mb = max_size // (1024 * 1024)
            current_size_mb = round(file_size / (1024 * 1024), 2)
            
            logger.warning(
                f"User {user_id} exceeded file size limit: "
                f"{current_size_mb}MB > {max_size_mb}MB (tier: {tier})"
            )
            
            raise HTTPException(
                status_code=403,
                detail={
                    "detail": f"File size exceeds your tier limit. Maximum allowed: {max_size_mb}MB for {tier} tier.",
                    "code": "FILE_SIZE_LIMIT_EXCEEDED",
                    "current_size_mb": current_size_mb,
                    "max_size_mb": max_size_mb,
                    "tier": tier,
                    "upgrade_url": "/pricing"
                }
            )
    
    # Check 2: Monthly Conversion Limit
    supabase = get_supabase_client()
    redis = get_cached_redis_client()  # May be None if Redis unavailable
    
    tracker = UsageTracker(supabase, redis)
    
    try:
        usage = tracker.get_usage(user_id)
    except Exception as e:
        logger.error(f"Failed to get usage for user {user_id}: {e}", exc_info=True)
        # CRITICAL DECISION: Fail open or fail closed?
        # Failing open (allow upload) risks abuse but maintains availability
        # Failing closed (block upload) is more secure but impacts UX
        # For now, fail open with warning
        logger.warning(f"Usage check failed for user {user_id}, allowing upload (fail-open policy)")
        return None
    
    current_count = usage.get("conversion_count", 0)
    limit = usage.get("tier_limit")
    
    # Check if user has exceeded their conversion limit
    if limit is not None and current_count >= limit:
        # Calculate next month reset date
        now = datetime.now(timezone.utc)
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            next_month = now.replace(month=now.month + 1, day=1)
        reset_date = next_month.strftime('%Y-%m-%d')
        
        logger.warning(
            f"User {user_id} exceeded conversion limit: "
            f"{current_count}/{limit} (tier: {tier})"
        )
        
        raise HTTPException(
            status_code=403,
            detail={
                "detail": f"Monthly conversion limit reached. You have used {current_count}/{limit} conversions this month.",
                "code": "CONVERSION_LIMIT_EXCEEDED",
                "current_count": current_count,
                "limit": limit,
                "tier": tier,
                "reset_date": reset_date,
                "upgrade_url": "/pricing"
            }
        )
    
    logger.info(f"User {user_id} passed limit checks: {current_count}/{limit or '∞'} conversions, tier: {tier}")
    return None
