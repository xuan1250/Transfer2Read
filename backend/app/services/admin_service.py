"""
Admin Service Layer

Business logic for admin dashboard operations.
Handles user management, system statistics, and tier updates.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from supabase import Client

from app.schemas.auth import SubscriptionTier
from app.schemas.admin import AdminUserInfo, SystemStats

logger = logging.getLogger(__name__)


class AdminService:
    """
    Service for admin dashboard operations.

    This service provides:
    - System-wide statistics (users, conversions, active jobs)
    - User list with pagination, search, and filtering
    - User tier management (upgrades/downgrades)
    """

    def __init__(self, supabase_client: Client):
        """
        Initialize AdminService.

        Args:
            supabase_client: Supabase client with service_role key for admin operations
        """
        self.supabase = supabase_client

    async def get_system_stats(self) -> SystemStats:
        """
        Get system-wide statistics for admin dashboard.

        Queries:
        - Total users from Supabase Auth
        - Total conversions from user_usage table
        - Active jobs from conversion_jobs table (status=PROCESSING/PENDING)
        - Monthly conversions from user_usage table (current month)

        Returns:
            SystemStats: System statistics

        Raises:
            Exception: If database queries fail
        """
        try:
            # Total users from Supabase Auth
            # Use admin.list_users with pagination to get count
            users_response = self.supabase.auth.admin.list_users(page=1, per_page=1)
            total_users = 0

            # Supabase Python client doesn't return total count in list_users
            # We need to count all users by paginating (expensive but accurate)
            # For MVP, we'll use a database query instead
            try:
                # Query auth.users directly via RPC function (more efficient)
                count_result = self.supabase.rpc('count_total_users').execute()
                total_users = count_result.data if count_result.data else 0
            except Exception as e:
                logger.warning(f"Failed to get user count via RPC, falling back to auth API: {e}")
                # Fallback: count via auth API (less efficient)
                page = 1
                per_page = 100
                while True:
                    page_users = self.supabase.auth.admin.list_users(page=page, per_page=per_page)
                    if not page_users or len(page_users) == 0:
                        break
                    total_users += len(page_users)
                    if len(page_users) < per_page:
                        break
                    page += 1

            # Total conversions from user_usage table
            usage_response = self.supabase.table('user_usage').select('conversion_count').execute()
            total_conversions = sum(row['conversion_count'] for row in usage_response.data) if usage_response.data else 0

            # Active jobs from conversion_jobs table
            # Note: Assuming we have conversion_jobs or similar table tracking job status
            # If not exists, return 0 for MVP
            try:
                active_jobs_response = self.supabase.table('conversion_jobs') \
                    .select('id', count='exact') \
                    .in_('status', ['PROCESSING', 'PENDING']) \
                    .execute()
                active_jobs = active_jobs_response.count if hasattr(active_jobs_response, 'count') else 0
            except Exception as e:
                logger.warning(f"Failed to query active jobs: {e}")
                active_jobs = 0

            # Monthly conversions (current month)
            current_month = datetime.now(timezone.utc).strftime('%Y-%m-01')
            monthly_response = self.supabase.table('user_usage') \
                .select('conversion_count') \
                .eq('month', current_month) \
                .execute()
            monthly_conversions = sum(row['conversion_count'] for row in monthly_response.data) if monthly_response.data else 0

            return SystemStats(
                total_users=total_users,
                total_conversions=total_conversions,
                active_jobs=active_jobs,
                monthly_conversions=monthly_conversions
            )

        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"Failed to get system stats: {type(e).__name__}: {e}")

            # Provide more specific error messages for common failure modes
            if "connection" in error_msg or "timeout" in error_msg:
                raise Exception("Database connection failed - please check Supabase connection")
            elif "auth" in error_msg or "permission" in error_msg:
                raise Exception("Authentication error - verify Supabase service key permissions")
            else:
                raise Exception(f"Failed to fetch system statistics: {type(e).__name__}")

    async def get_users(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        tier_filter: Optional[str] = None,
        sort_by: str = 'created_at',
        sort_order: str = 'desc'
    ) -> Dict[str, Any]:
        """
        Get paginated list of users with filters.

        Args:
            page: Page number (1-indexed)
            page_size: Users per page (max 100)
            search: Filter by email (case-insensitive)
            tier_filter: Filter by tier (ALL, FREE, PRO, PREMIUM)
            sort_by: Column to sort by (email, tier, conversions, last_login, created_at)
            sort_order: Sort direction (asc, desc)

        Returns:
            dict: {users: List[AdminUserInfo], total: int, page: int, page_size: int, total_pages: int}

        Raises:
            Exception: If database queries fail
        """
        try:
            # Fetch users from Supabase Auth with pagination
            # Note: Supabase Auth API has limited filtering - we'll filter in Python for MVP
            all_users = []
            page_num = 1
            per_page = 100

            # Fetch all users (for MVP - optimize later with better API usage)
            while True:
                users_response = self.supabase.auth.admin.list_users(page=page_num, per_page=per_page)
                if not users_response or len(users_response) == 0:
                    break
                all_users.extend(users_response)
                if len(users_response) < per_page:
                    break
                page_num += 1

            # Get usage data for all users
            usage_response = self.supabase.table('user_usage').select('user_id, conversion_count').execute()
            usage_by_user = {row['user_id']: row['conversion_count'] for row in usage_response.data} if usage_response.data else {}

            # Convert to AdminUserInfo and apply filters
            admin_users = []
            for user in all_users:
                user_metadata = user.user_metadata or {}
                tier = user_metadata.get('tier', 'FREE')
                email = user.email or ""

                # Apply search filter
                if search and search.lower() not in email.lower():
                    continue

                # Apply tier filter
                if tier_filter and tier_filter != 'ALL' and tier != tier_filter:
                    continue

                # Get total conversions for user
                total_conversions = sum(
                    count for uid, count in usage_by_user.items() if uid == user.id
                )

                admin_users.append(AdminUserInfo(
                    id=user.id,
                    email=email,
                    tier=tier,
                    total_conversions=total_conversions,
                    last_login=user.last_sign_in_at,
                    created_at=user.created_at
                ))

            # Sort users
            reverse = sort_order == 'desc'
            if sort_by == 'email':
                admin_users.sort(key=lambda u: u.email.lower(), reverse=reverse)
            elif sort_by == 'tier':
                admin_users.sort(key=lambda u: u.tier, reverse=reverse)
            elif sort_by == 'conversions':
                admin_users.sort(key=lambda u: u.total_conversions, reverse=reverse)
            elif sort_by == 'last_login':
                admin_users.sort(key=lambda u: u.last_login or "", reverse=reverse)
            elif sort_by == 'created_at':
                admin_users.sort(key=lambda u: u.created_at, reverse=reverse)

            # Paginate
            total = len(admin_users)
            total_pages = (total + page_size - 1) // page_size
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_users = admin_users[start_idx:end_idx]

            return {
                'users': paginated_users,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages
            }

        except Exception as e:
            logger.error(f"Failed to get user list: {e}")
            raise

    async def update_user_tier(self, user_id: str, new_tier: str) -> Dict[str, Any]:
        """
        Update a user's subscription tier.

        Uses Supabase Admin API to update user_metadata.tier.

        Args:
            user_id: UUID of user to update
            new_tier: New tier value (FREE, PRO, or PREMIUM)

        Returns:
            dict: {user_id, old_tier, new_tier, updated_at}

        Raises:
            ValueError: If new_tier is invalid
            Exception: If update fails
        """
        # Validate tier
        valid_tiers = ['FREE', 'PRO', 'PREMIUM']
        if new_tier not in valid_tiers:
            raise ValueError(f"Invalid tier: {new_tier}. Must be one of: {valid_tiers}")

        try:
            # Fetch current user to get old tier
            user_response = self.supabase.auth.admin.get_user_by_id(user_id)
            if not user_response or not user_response.user:
                raise ValueError(f"User not found: {user_id}")

            old_tier = user_response.user.user_metadata.get('tier', 'FREE')

            # Update user metadata with new tier
            update_response = self.supabase.auth.admin.update_user_by_id(
                user_id,
                {
                    'user_metadata': {
                        'tier': new_tier
                    }
                }
            )

            if not update_response or not update_response.user:
                raise Exception("Failed to update user tier")

            updated_at = datetime.now(timezone.utc).isoformat()

            logger.info(f"Admin updated user {user_id} tier: {old_tier} → {new_tier}")

            return {
                'user_id': user_id,
                'old_tier': old_tier,
                'new_tier': new_tier,
                'updated_at': updated_at
            }

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to update user tier: {e}")
            raise
