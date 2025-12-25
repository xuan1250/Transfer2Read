'use client';

import { useRouter } from 'next/navigation';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LimitExceededError } from '@/types/usage';
import { ArrowRight, Check, X, AlertCircle } from 'lucide-react';

export interface LimitReachedModalProps {
  /** Whether the modal is open */
  isOpen: boolean;

  /** Callback when modal is closed */
  onClose: () => void;

  /** Error data from API response */
  errorData: LimitExceededError;
}

/**
 * Modal that displays when a user hits a tier limit.
 * Shows contextual message, usage stats, and upgrade CTA.
 *
 * Triggered by API 403 responses with error codes:
 * - FILE_SIZE_LIMIT_EXCEEDED
 * - CONVERSION_LIMIT_EXCEEDED
 */
export function LimitReachedModal({
  isOpen,
  onClose,
  errorData,
}: LimitReachedModalProps) {
  const router = useRouter();

  const handleUpgrade = () => {
    onClose();
    router.push('/pricing');
  };

  // Determine limit type
  const isFileSizeLimit = errorData.code === 'FILE_SIZE_LIMIT_EXCEEDED';
  const isConversionLimit = errorData.code === 'CONVERSION_LIMIT_EXCEEDED';

  // Format reset date if available
  const formatResetDate = (dateStr?: string) => {
    if (!dateStr) return null;
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100">
              <AlertCircle className="h-6 w-6 text-amber-600" />
            </div>
            <div>
              <DialogTitle className="text-xl">Limit Reached</DialogTitle>
              <DialogDescription className="mt-1">
                Upgrade to continue using the service
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {/* Error Message */}
        <div className="rounded-md bg-amber-50 border border-amber-200 p-4">
          <p className="text-sm text-amber-900 font-medium">
            {errorData.detail}
          </p>
        </div>

        {/* Usage Stats */}
        <div className="space-y-3">
          {isFileSizeLimit && errorData.current_size_mb && errorData.max_size_mb && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">File Size Limit</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-red-600">
                    {errorData.current_size_mb.toFixed(1)} MB
                  </span>
                  <span className="text-sm text-gray-600">
                    / {errorData.max_size_mb} MB allowed
                  </span>
                </div>
                <div className="text-sm text-gray-600 mt-1">
                  Your current tier: <Badge variant="outline">{errorData.tier}</Badge>
                </div>
              </CardContent>
            </Card>
          )}

          {isConversionLimit && errorData.current_count !== undefined && errorData.limit && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Monthly Conversions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-red-600">
                    {errorData.current_count} / {errorData.limit}
                  </span>
                  <span className="text-sm text-gray-600">conversions used</span>
                </div>
                {errorData.reset_date && (
                  <p className="text-sm text-gray-600 mt-1">
                    Resets on: <strong>{formatResetDate(errorData.reset_date)}</strong>
                  </p>
                )}
                <div className="text-sm text-gray-600 mt-1">
                  Your current tier: <Badge variant="outline">{errorData.tier}</Badge>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Tier Comparison */}
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-900">Upgrade to Unlock More</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* PRO Tier Card */}
            <Card className="border-blue-200 bg-blue-50/50">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-bold text-blue-900">PRO</CardTitle>
                  <Badge className="bg-blue-600 hover:bg-blue-700">Recommended</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-green-600 shrink-0" />
                  <span className="text-gray-700">Unlimited conversions</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-green-600 shrink-0" />
                  <span className="text-gray-700">Unlimited file size</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-green-600 shrink-0" />
                  <span className="text-gray-700">Priority support</span>
                </div>
              </CardContent>
            </Card>

            {/* FREE Tier Current State */}
            <Card className="border-gray-200">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-bold text-gray-900">FREE</CardTitle>
                  {errorData.tier === 'FREE' && (
                    <Badge variant="outline">Current</Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-center gap-2 text-sm">
                  <X className="h-4 w-4 text-red-500 shrink-0" />
                  <span className="text-gray-700 line-through">5 conversions/month</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <X className="h-4 w-4 text-red-500 shrink-0" />
                  <span className="text-gray-700 line-through">50 MB file size</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <X className="h-4 w-4 text-red-500 shrink-0" />
                  <span className="text-gray-700 line-through">Basic support</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Footer Actions */}
        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button
            variant="outline"
            onClick={onClose}
            className="w-full sm:w-auto order-2 sm:order-1"
          >
            Maybe Later
          </Button>
          <Button
            onClick={handleUpgrade}
            className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 text-white order-1 sm:order-2"
          >
            Upgrade to Pro
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
