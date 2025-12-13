/**
 * Tier Utility Functions
 * Shared utilities for subscription tier display and benefits
 */

import { SubscriptionTier, TierBenefits } from '@/types/auth';

/**
 * Get CSS classes for tier badge styling based on Professional Blue theme
 */
export function getTierBadgeClass(tier: SubscriptionTier): string {
  switch (tier) {
    case 'FREE':
      return 'bg-gray-200 text-gray-800 hover:bg-gray-200';
    case 'PRO':
      return 'bg-blue-100 text-blue-800 hover:bg-blue-100';
    case 'PREMIUM':
      return 'bg-amber-100 text-amber-800 hover:bg-amber-100';
    default:
      return 'bg-gray-200 text-gray-800 hover:bg-gray-200';
  }
}

/**
 * Get tier benefits configuration
 */
export function getTierBenefits(tier: SubscriptionTier): TierBenefits {
  switch (tier) {
    case 'FREE':
      return {
        features: [
          '5 conversions per month',
          'Up to 50MB per file',
          'Basic email support',
          'All conversion features'
        ],
        conversionsPerMonth: 5,
        maxFileSize: 50,
        support: 'Basic email support'
      };
    case 'PRO':
      return {
        features: [
          'Unlimited conversions',
          'No file size limit',
          'All conversion features',
          'Priority email support'
        ],
        conversionsPerMonth: 'unlimited',
        maxFileSize: 'unlimited',
        support: 'Priority email support'
      };
    case 'PREMIUM':
      return {
        features: [
          'Unlimited conversions',
          'No file size limit',
          'All conversion features',
          'Dedicated support manager',
          'Advanced features (coming soon)'
        ],
        conversionsPerMonth: 'unlimited',
        maxFileSize: 'unlimited',
        support: 'Dedicated support manager'
      };
    default:
      return {
        features: [],
        conversionsPerMonth: 0,
        maxFileSize: 0,
        support: ''
      };
  }
}
