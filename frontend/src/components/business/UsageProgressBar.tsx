'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, TrendingUp } from 'lucide-react';
import { UsageStats, SubscriptionTier } from '@/types/usage';
import { useUser } from '@/hooks/useUser';
import { createClient } from '@/lib/supabase/client';

export interface UsageProgressBarProps {
  /** Custom className for the wrapper */
  className?: string;

  /** Callback when usage data is loaded */
  onUsageLoaded?: (usage: UsageStats) => void;
}

/**
 * Displays user's monthly conversion usage with a visual progress bar.
 * Shows current usage, remaining conversions, and color-coded warning states.
 *
 * Color coding:
 * - Green: 0-60% used
 * - Yellow/Amber: 61-90% used (warning)
 * - Red: 91-100% used (critical)
 *
 * For PRO/PREMIUM users: Shows "Unlimited" badge instead of progress bar
 */
export function UsageProgressBar({
  className,
  onUsageLoaded,
}: UsageProgressBarProps) {
  const { user } = useUser();
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get user tier from user metadata
  const tier: SubscriptionTier = (user?.user_metadata?.tier as SubscriptionTier) || 'FREE';

  useEffect(() => {
    const fetchUsage = async () => {
      if (!user) {
        setLoading(false);
        return;
      }

      // Fetch session to get access_token
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session?.access_token) {
        setLoading(false);
        return;
      }

      try {
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${API_BASE_URL}/api/v1/usage`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });

        if (!response.ok) {
          if (response.status === 401) {
            throw new Error('Unauthorized');
          }
          throw new Error('Failed to fetch usage data');
        }

        const data: UsageStats = await response.json();
        setUsage(data);
        onUsageLoaded?.(data);
      } catch (err) {
        console.error('Error fetching usage:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchUsage();
  }, [user, onUsageLoaded]);

  // Loading state
  if (loading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-3">
          <Skeleton className="h-5 w-40" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-full" />
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card className={className}>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <AlertCircle className="h-4 w-4" />
            <span>Unable to load usage data</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // No usage data
  if (!usage) {
    return null;
  }

  // Unlimited tiers (PRO/PREMIUM)
  if (tier === 'PRO' || tier === 'PREMIUM' || usage.tier_limit === null) {
    return (
      <Card className={className}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium">Monthly Conversions</CardTitle>
            <Badge className="bg-green-600 hover:bg-green-700">Unlimited</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-green-600">
              {usage.conversion_count}
            </span>
            <span className="text-sm text-gray-600">conversions this month</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            You have unlimited conversions with {tier} tier
          </p>
        </CardContent>
      </Card>
    );
  }

  // FREE tier with limits
  const percentage = usage.tier_limit > 0
    ? Math.round((usage.conversion_count / usage.tier_limit) * 100)
    : 0;

  const remaining = usage.remaining ?? 0;

  // Determine color based on percentage
  let progressColor = 'bg-green-600'; // 0-60%
  let textColor = 'text-green-600';
  let warningState: 'normal' | 'warning' | 'critical' = 'normal';

  if (percentage >= 91) {
    progressColor = 'bg-red-600';
    textColor = 'text-red-600';
    warningState = 'critical';
  } else if (percentage >= 61) {
    progressColor = 'bg-amber-500';
    textColor = 'text-amber-600';
    warningState = 'warning';
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-medium">Monthly Conversions</CardTitle>
          {warningState === 'critical' && (
            <Badge variant="destructive" className="gap-1">
              <AlertCircle className="h-3 w-3" />
              Limit Reached
            </Badge>
          )}
          {warningState === 'warning' && (
            <Badge className="bg-amber-500 hover:bg-amber-600 gap-1">
              <TrendingUp className="h-3 w-3" />
              Almost Full
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Usage Text */}
        <div className="flex items-baseline gap-2">
          <span className={`text-2xl font-bold ${textColor}`}>
            {usage.conversion_count}
          </span>
          <span className="text-gray-600">
            / {usage.tier_limit}
          </span>
          <span className="text-sm text-gray-600">Free Conversions Used This Month</span>
        </div>

        {/* Progress Bar */}
        <Progress
          value={percentage}
          className="h-2.5"
          indicatorClassName={progressColor}
          aria-label={`${percentage}% of monthly conversions used`}
        />

        {/* Remaining Conversions */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">
            {remaining > 0 ? (
              <>
                <strong className={textColor}>{remaining}</strong> conversion{remaining === 1 ? '' : 's'} remaining
              </>
            ) : (
              <strong className="text-red-600">No conversions remaining</strong>
            )}
          </span>
          <Badge variant="outline">{tier}</Badge>
        </div>

        {/* Warning message for critical state */}
        {warningState === 'critical' && (
          <div className="rounded-md bg-red-50 border border-red-200 p-3">
            <p className="text-xs text-red-800">
              You&apos;ve reached your monthly limit. Upgrade to PRO for unlimited conversions.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
