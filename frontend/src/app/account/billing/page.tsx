'use client';

import { useUser } from '@/hooks/useUser';
import { AuthGuard } from '@/components/auth/AuthGuard';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

export default function BillingPage() {
  const { user } = useUser();
  const userTier = (user?.user_metadata?.tier as string) || 'FREE';

  return (
    <AuthGuard>
      <div className="min-h-screen bg-gray-50 py-8 px-4">
        <div className="max-w-3xl mx-auto space-y-6">
          {/* Page Header */}
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Billing & Subscription</h1>
            <p className="text-gray-600 mt-1">Manage your subscription and billing information</p>
          </div>

          {/* Coming Soon Card */}
          <Card>
            <CardHeader>
              <CardTitle>Subscription Management</CardTitle>
              <CardDescription>Manage your billing and payment methods</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 text-blue-800 px-6 py-4 rounded-lg">
                <div className="flex items-start gap-3">
                  <svg
                    className="h-6 w-6 flex-shrink-0 mt-0.5"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                  <div>
                    <p className="font-semibold mb-2">Coming Soon</p>
                    <p className="text-sm">
                      Subscription management features will be available in Epic 6. You&apos;ll be able to:
                    </p>
                    <ul className="mt-3 space-y-1 text-sm list-disc list-inside">
                      <li>Update payment methods</li>
                      <li>View billing history</li>
                      <li>Manage subscription plan</li>
                      <li>Download invoices</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Current Plan Info */}
              <div className="pt-4">
                <h3 className="font-semibold text-gray-900 mb-2">Current Plan</h3>
                <p className="text-sm text-gray-600">
                  You are currently on the <span className="font-semibold">{userTier}</span> plan.
                </p>
              </div>

              {/* Actions */}
              <div className="pt-4 flex gap-4">
                <Link href="/settings">
                  <Button variant="outline">Back to Settings</Button>
                </Link>
                <Link href="/pricing">
                  <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                    View Pricing
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </AuthGuard>
  );
}
