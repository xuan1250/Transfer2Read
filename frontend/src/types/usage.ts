/**
 * Usage Tracking and Tier Limit Types
 *
 * Type definitions for usage statistics, tier limits, and error responses
 * from the backend limit enforcement system.
 */

/**
 * Subscription tier types
 */
export type SubscriptionTier = 'FREE' | 'PRO' | 'PREMIUM';

/**
 * Error codes for limit violations
 */
export type LimitErrorCode =
  | 'FILE_SIZE_LIMIT_EXCEEDED'
  | 'CONVERSION_LIMIT_EXCEEDED';

/**
 * Error response from backend when tier limits are exceeded.
 * Returns HTTP 403 Forbidden with structured error information.
 *
 * @see backend/app/schemas/errors.py:10-84
 */
export interface LimitExceededError {
  /** Human-readable error message */
  detail: string;

  /** Machine-readable error code */
  code: LimitErrorCode;

  /** User's current subscription tier */
  tier: SubscriptionTier;

  /** URL to upgrade/pricing page */
  upgrade_url: string;

  // File size specific fields
  /** Current file size in MB (for FILE_SIZE_LIMIT_EXCEEDED) */
  current_size_mb?: number;

  /** Maximum allowed file size in MB (for FILE_SIZE_LIMIT_EXCEEDED) */
  max_size_mb?: number;

  // Conversion limit specific fields
  /** Current conversion count this month (for CONVERSION_LIMIT_EXCEEDED) */
  current_count?: number;

  /** Maximum conversions allowed per month (for CONVERSION_LIMIT_EXCEEDED) */
  limit?: number;

  /** Date when conversion limit resets (YYYY-MM-DD format) */
  reset_date?: string;
}

/**
 * Usage statistics for a user's monthly conversions
 */
export interface UsageStats {
  /** Month in YYYY-MM format */
  month: string;

  /** Number of conversions used this month */
  conversion_count: number;

  /** User's current subscription tier */
  tier: SubscriptionTier;

  /** Maximum conversions allowed per month (null = unlimited) */
  tier_limit: number | null;

  /** Remaining conversions (null = unlimited) */
  remaining: number | null;
}

/**
 * Tier feature information for display
 */
export interface TierFeatures {
  /** Tier name */
  tier: SubscriptionTier;

  /** Display name */
  name: string;

  /** Monthly price (null = free) */
  price: number | null;

  /** Conversions per month (null = unlimited) */
  conversions_per_month: number | null;

  /** Max file size in MB (null = unlimited) */
  max_file_size_mb: number | null;

  /** Support level description */
  support: string;

  /** List of features */
  features: string[];

  /** Is this tier recommended? */
  recommended?: boolean;
}
