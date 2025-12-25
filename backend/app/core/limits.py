"""
Tier Limits Configuration

Centralized configuration for subscription tier limits.
Defines file size and conversion count limits for FREE, PRO, and PREMIUM tiers.
"""
from typing import Optional, Dict, Any


TIER_LIMITS: Dict[str, Dict[str, Any]] = {
    "FREE": {
        "max_file_size_mb": 50,
        "max_conversions_per_month": 5
    },
    "PRO": {
        "max_file_size_mb": None,  # Unlimited
        "max_conversions_per_month": None  # Unlimited
    },
    "PREMIUM": {
        "max_file_size_mb": None,  # Unlimited
        "max_conversions_per_month": None  # Unlimited
    }
}


def get_file_size_limit(tier: str) -> Optional[int]:
    """
    Get maximum file size limit in bytes for given tier.
    
    Args:
        tier: Subscription tier (FREE, PRO, PREMIUM)
        
    Returns:
        int: Maximum file size in bytes, or None if unlimited
        
    Defaults to FREE tier limits if tier is unrecognized.
    """
    tier = tier.upper() if tier else "FREE"
    if tier not in TIER_LIMITS:
        tier = "FREE"
    limit_mb = TIER_LIMITS[tier]["max_file_size_mb"]
    return limit_mb * 1024 * 1024 if limit_mb else None


def get_conversion_limit(tier: str) -> Optional[int]:
    """
    Get maximum conversions per month for given tier.
    
    Args:
        tier: Subscription tier (FREE, PRO, PREMIUM)
        
    Returns:
        int: Maximum conversions per month, or None if unlimited
        
    Defaults to FREE tier limits if tier is unrecognized.
    """
    tier = tier.upper() if tier else "FREE"
    if tier not in TIER_LIMITS:
        tier = "FREE"
    return TIER_LIMITS[tier]["max_conversions_per_month"]
