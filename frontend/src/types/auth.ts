/**
 * Authentication and User Types
 */

export type SubscriptionTier = 'FREE' | 'PRO' | 'PREMIUM';

export interface UserProfile {
  id: string;
  email: string;
  tier: SubscriptionTier;
  createdAt: string;
  provider?: 'email' | 'google' | 'github';
}

export interface TierBenefits {
  conversionsPerMonth: number | 'unlimited';
  maxFileSize: number | 'unlimited'; // in MB
  support: string;
  features: string[];
}

/**
 * Tier Benefits Configuration
 */
export const tierBenefits: Record<SubscriptionTier, TierBenefits> = {
  FREE: {
    conversionsPerMonth: 5,
    maxFileSize: 50, // MB
    support: 'Basic email support',
    features: [
      '5 conversions per month',
      'Up to 50MB per file',
      'All conversion features',
      'Basic email support',
    ],
  },
  PRO: {
    conversionsPerMonth: 'unlimited',
    maxFileSize: 'unlimited',
    support: 'Priority email support',
    features: [
      'Unlimited conversions',
      'No file size limit',
      'All conversion features',
      'Priority email support',
    ],
  },
  PREMIUM: {
    conversionsPerMonth: 'unlimited',
    maxFileSize: 'unlimited',
    support: 'Dedicated support manager',
    features: [
      'Unlimited conversions',
      'No file size limit',
      'All conversion features',
      'Dedicated support manager',
      'Advanced features (coming soon)',
    ],
  },
};
