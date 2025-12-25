'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { X, Sparkles } from 'lucide-react';
import { useUser } from '@/hooks/useUser';

export interface UpgradeBannerProps {
  /** Custom className for the banner */
  className?: string;
}

const DISMISSAL_KEY = 'upgrade-banner-dismissed';
const DISMISSAL_DURATION = 7 * 24 * 60 * 60 * 1000; // 7 days in milliseconds

/**
 * Promotional banner encouraging FREE tier users to upgrade to PRO.
 * Features:
 * - Only visible to FREE tier users
 * - Dismissible with 7-day localStorage persistence
 * - Professional Blue theme with gradient accent
 * - Mobile-responsive design
 */
export function UpgradeBanner({ className }: UpgradeBannerProps) {
  const { user } = useUser();
  const router = useRouter();
  const [isVisible, setIsVisible] = useState(false);

  // Get user tier
  const tier = user?.user_metadata?.tier || 'FREE';

  useEffect(() => {
    // Only show banner for FREE tier users
    if (tier !== 'FREE') {
      setIsVisible(false);
      return;
    }

    // Check if banner was dismissed recently
    if (typeof window !== 'undefined') {
      const dismissedAt = localStorage.getItem(DISMISSAL_KEY);
      if (dismissedAt) {
        const dismissedTime = parseInt(dismissedAt, 10);
        const now = Date.now();
        if (now - dismissedTime < DISMISSAL_DURATION) {
          // Still within dismissal period
          setIsVisible(false);
          return;
        } else {
          // Dismissal expired, clear it
          localStorage.removeItem(DISMISSAL_KEY);
        }
      }
      setIsVisible(true);
    }
  }, [tier]);

  const handleDismiss = () => {
    setIsVisible(false);
    if (typeof window !== 'undefined') {
      localStorage.setItem(DISMISSAL_KEY, Date.now().toString());
    }
  };

  const handleUpgrade = () => {
    router.push('/pricing');
  };

  if (!isVisible) {
    return null;
  }

  return (
    <Card
      className={`relative overflow-hidden bg-gradient-to-r from-blue-50 via-blue-50 to-sky-50 border-blue-200 ${className}`}
    >
      {/* Dismiss button */}
      <button
        onClick={handleDismiss}
        className="absolute top-3 right-3 p-1 rounded-md hover:bg-blue-100 transition-colors"
        aria-label="Dismiss banner"
      >
        <X className="h-4 w-4 text-gray-600" />
      </button>

      <CardContent className="p-6 pr-12">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          {/* Icon */}
          <div className="flex-shrink-0">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-600">
              <Sparkles className="h-6 w-6 text-white" />
            </div>
          </div>

          {/* Content */}
          <div className="flex-grow space-y-1">
            <h3 className="text-lg font-bold text-gray-900">
              Unlock Unlimited Conversions with Pro
            </h3>
            <p className="text-sm text-gray-700">
              No limits on file size or monthly conversions. Get priority support and faster processing.
            </p>
          </div>

          {/* CTA Button */}
          <div className="flex-shrink-0">
            <Button
              onClick={handleUpgrade}
              className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-md"
            >
              See Plans
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
