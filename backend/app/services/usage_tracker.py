"""
Usage Tracking Service

Tracks user conversion usage per month for tier limit enforcement.
Uses Supabase PostgreSQL for persistence and Redis for caching.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from supabase import Client
import redis

from app.schemas.auth import SubscriptionTier

logger = logging.getLogger(__name__)


class UsageTracker:
    """
    Service for tracking and querying user conversion usage.

    This service handles:
    - Incrementing usage count when users start conversions
    - Querying current usage stats with tier limits
    - Caching usage data in Redis for performance
    - Graceful fallback to database when Redis unavailable
    """

    def __init__(self, supabase_client: Client, redis_client: Optional[redis.Redis] = None):
        """
        Initialize UsageTracker service.

        Args:
            supabase_client: Supabase client for database operations
            redis_client: Redis client for caching (optional - graceful degradation if None)
        """
        self.supabase = supabase_client
        self.redis = redis_client

    def _get_current_month(self) -> str:
        """
        Get first day of current month in UTC.

        Returns:
            str: Month in YYYY-MM-01 format (e.g., "2025-12-01")
        """
        now = datetime.now(timezone.utc)
        return now.strftime('%Y-%m-01')

    def _get_redis_key(self, user_id: str, month: Optional[str] = None) -> str:
        """
        Generate Redis cache key for user usage.

        Args:
            user_id: User UUID
            month: Month string (YYYY-MM format). Uses current month if not provided.

        Returns:
            str: Redis key in format "usage:{user_id}:{YYYY-MM}"
        """
        if month is None:
            month = self._get_current_month()[:7]  # YYYY-MM only (no day)
        else:
            month = month[:7]  # Ensure YYYY-MM format
        return f"usage:{user_id}:{month}"

    def increment_usage(self, user_id: str) -> int:
        """
        Increment conversion count for user in current month.

        Uses PostgreSQL function for atomic UPSERT to prevent race conditions.
        Updates Redis cache after successful increment.

        Args:
            user_id: User UUID to increment usage for

        Returns:
            int: New conversion count for this month

        Raises:
            Exception: If database operation fails

        Security:
            CRITICAL - This method explicitly filters by user_id for defense-in-depth.
            Even though we use a PostgreSQL function, the user_id is passed as parameter
            to ensure only that user's data is modified.
        """
        month = self._get_current_month()

        try:
            # Use PostgreSQL function for atomic increment (prevents race conditions)
            # CRITICAL: Explicit user_id parameter for defense-in-depth security
            result = self.supabase.rpc(
                'increment_user_usage',
                {
                    'p_user_id': user_id,
                    'p_month': month
                }
            ).execute()

            new_count = result.data if result.data is not None else 1

            # Update Redis cache with new count
            if self.redis:
                try:
                    redis_key = self._get_redis_key(user_id, month)
                    self.redis.set(redis_key, new_count, ex=3600)  # TTL: 1 hour
                    logger.debug(f"Updated Redis cache for user {user_id}: {new_count}")
                except Exception as e:
                    logger.warning(f"Redis cache update failed: {e}. Continuing without cache.")

            logger.info(f"Incremented usage for user {user_id} to {new_count} (month: {month})")
            return new_count

        except Exception as e:
            logger.error(f"Failed to increment usage for user {user_id}: {e}")
            raise

    def get_usage(self, user_id: str) -> dict:
        """
        Get current month's usage statistics for user.

        Checks Redis cache first, falls back to Supabase database if cache miss.
        Fetches user tier from Supabase Auth metadata to calculate limits.

        Args:
            user_id: User UUID to query usage for

        Returns:
            dict: Usage statistics with keys:
                - month (str): Current month (YYYY-MM-01)
                - conversion_count (int): Number of conversions this month
                - tier (str): User's subscription tier
                - tier_limit (int|None): Max conversions allowed (None = unlimited)
                - remaining (int|None): Conversions remaining (None = unlimited)

        Raises:
            Exception: If database operation fails

        Security:
            CRITICAL - Explicitly filters by user_id in database query for defense-in-depth.
            Never rely solely on RLS policies - always filter by user_id in application code.
        """
        month = self._get_current_month()
        count = 0

        # Try Redis cache first
        if self.redis:
            try:
                redis_key = self._get_redis_key(user_id, month)
                cached_count = self.redis.get(redis_key)
                if cached_count is not None:
                    count = int(cached_count)
                    logger.debug(f"Cache hit for user {user_id}: {count}")
                else:
                    raise ValueError("Cache miss")  # Trigger fallback to database
            except Exception as e:
                logger.debug(f"Redis cache miss or error: {e}. Falling back to database.")
                count = None  # Will fetch from database

        # Fallback to database if cache miss or Redis unavailable
        if count is None:
            try:
                # CRITICAL: Explicit user_id filter for defense-in-depth security
                result = self.supabase.table('user_usage') \
                    .select('conversion_count') \
                    .eq('user_id', user_id) \
                    .eq('month', month) \
                    .execute()

                if result.data and len(result.data) > 0:
                    count = result.data[0]['conversion_count']
                else:
                    count = 0  # New user or new month (no usage yet)

                logger.debug(f"Database query for user {user_id}: {count}")

                # Update cache with fetched value
                if self.redis:
                    try:
                        redis_key = self._get_redis_key(user_id, month)
                        self.redis.set(redis_key, count, ex=3600)
                    except Exception as e:
                        logger.warning(f"Redis cache set failed: {e}")

            except Exception as e:
                logger.error(f"Failed to fetch usage from database for user {user_id}: {e}")
                raise

        # Fetch user tier from Supabase Auth metadata
        try:
            user_result = self.supabase.auth.admin.get_user_by_id(user_id)
            tier_str = user_result.user.user_metadata.get('tier', 'FREE')
        except Exception as e:
            logger.warning(f"Failed to fetch user tier for {user_id}: {e}. Defaulting to FREE.")
            tier_str = 'FREE'

        # Calculate tier limit and remaining conversions
        tier_limits = {
            'FREE': 5,
            'PRO': None,  # Unlimited
            'PREMIUM': None  # Unlimited
        }
        limit = tier_limits.get(tier_str, 5)  # Default to FREE if unknown tier

        # Calculate remaining conversions (None for unlimited)
        if limit is not None:
            remaining = max(0, limit - count)
        else:
            remaining = None  # Unlimited

        return {
            'month': month,
            'conversion_count': count,
            'tier': tier_str,
            'tier_limit': limit,
            'remaining': remaining
        }
