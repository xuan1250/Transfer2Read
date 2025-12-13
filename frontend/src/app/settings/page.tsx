'use client';

import { useUser } from '@/hooks/useUser';
import { AuthGuard } from '@/components/auth/AuthGuard';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { ChangePasswordForm } from '@/components/settings/ChangePasswordForm';
import { DeleteAccountDialog } from '@/components/settings/DeleteAccountDialog';
import { SubscriptionTier } from '@/types/auth';
import { getTierBadgeClass, getTierBenefits } from '@/lib/tierUtils';

export default function SettingsPage() {
  const { user } = useUser();

  // Extract user data
  const userEmail = user?.email || '';
  const userTier = (user?.user_metadata?.tier as SubscriptionTier) || 'FREE';
  const authProvider = user?.app_metadata?.provider || 'email';
  const createdAt = user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A';

  // Determine if user is using email/password authentication
  const isEmailPasswordUser = authProvider === 'email';

  return (
    <AuthGuard>
      <div className="min-h-screen bg-gray-50 py-8 px-4">
        <div className="max-w-3xl mx-auto space-y-6">
          {/* Page Header */}
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
            <p className="text-gray-600 mt-1">Manage your account settings and preferences</p>
          </div>

          {/* Account Information */}
          <Card>
            <CardHeader>
              <CardTitle>Account Information</CardTitle>
              <CardDescription>Your account details and authentication method</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Email */}
              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <Input
                  id="email"
                  type="email"
                  value={userEmail}
                  disabled
                  className="bg-gray-50"
                />
              </div>

              {/* Account Creation Date */}
              <div className="space-y-2">
                <Label htmlFor="created-at">Account Created</Label>
                <Input
                  id="created-at"
                  type="text"
                  value={createdAt}
                  disabled
                  className="bg-gray-50"
                />
              </div>

              {/* Authentication Provider */}
              <div className="space-y-2">
                <Label htmlFor="provider">Authentication Method</Label>
                <Input
                  id="provider"
                  type="text"
                  value={authProvider === 'email' ? 'Email/Password' : authProvider === 'google' ? 'Google' : authProvider === 'github' ? 'GitHub' : authProvider}
                  disabled
                  className="bg-gray-50"
                />
              </div>
            </CardContent>
          </Card>

          {/* Subscription Tier */}
          <Card>
            <CardHeader>
              <CardTitle>Subscription Tier</CardTitle>
              <CardDescription>Your current subscription plan and benefits</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Tier Badge */}
              <div className="space-y-2">
                <Label>Current Tier</Label>
                <div>
                  <Badge className={`${getTierBadgeClass(userTier)} text-sm px-3 py-1 font-semibold`}>
                    {userTier}
                  </Badge>
                </div>
              </div>

              {/* Tier Name */}
              <div className="space-y-2">
                <Label>Plan Name</Label>
                <p className="text-lg font-semibold text-gray-900">
                  {userTier === 'FREE' && 'Free Plan'}
                  {userTier === 'PRO' && 'Pro Plan'}
                  {userTier === 'PREMIUM' && 'Premium Plan'}
                </p>
              </div>

              {/* Tier Benefits List */}
              <div className="space-y-2">
                <Label>Benefits</Label>
                <ul className="space-y-2">
                  {getTierBenefits(userTier).features.map((feature, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                      <svg
                        className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5"
                        fill="none"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path d="M5 13l4 4L19 7"></path>
                      </svg>
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Usage Display (Placeholder) */}
              <div className="space-y-2">
                <Label>Current Usage</Label>
                <div className="bg-gray-50 border border-gray-200 rounded-md p-3">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-600">Conversions this month:</span>
                    <span className="font-semibold text-gray-900">
                      {/* TODO: Connect to Epic 6 usage tracking (Stories 6.1-6.3) */}
                      0 / {getTierBenefits(userTier).conversionsPerMonth === 'unlimited' ? '∞' : getTierBenefits(userTier).conversionsPerMonth}
                    </span>
                  </div>
                  <div className="mt-2 text-xs text-gray-500">
                    Full usage tracking coming in Epic 6
                  </div>
                </div>
              </div>

              {/* Upgrade Button (only for FREE tier) */}
              {userTier === 'FREE' && (
                <div className="pt-2">
                  <a
                    href="/pricing"
                    className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 py-2 rounded-md transition-colors"
                  >
                    Upgrade to Pro
                  </a>
                </div>
              )}

              {/* Manage Subscription Button (for PRO/PREMIUM) */}
              {(userTier === 'PRO' || userTier === 'PREMIUM') && (
                <div className="pt-2">
                  <a
                    href="/account/billing"
                    className="inline-block bg-gray-600 hover:bg-gray-700 text-white font-medium px-6 py-2 rounded-md transition-colors"
                  >
                    Manage Subscription
                  </a>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Security Section */}
          <Card>
            <CardHeader>
              <CardTitle>Security</CardTitle>
              <CardDescription>Manage your password and account security</CardDescription>
            </CardHeader>
            <CardContent>
              {isEmailPasswordUser ? (
                <ChangePasswordForm />
              ) : (
                <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-md text-sm">
                  You&apos;re signed in with {authProvider === 'google' ? 'Google' : 'GitHub'}. Password change is not available.
                </div>
              )}
            </CardContent>
          </Card>

          {/* Danger Zone */}
          <Card className="border-red-200">
            <CardHeader>
              <CardTitle className="text-red-600">Danger Zone</CardTitle>
              <CardDescription>Irreversible actions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <p className="text-sm text-gray-700 font-medium">Delete Account</p>
                <p className="text-sm text-gray-600">
                  Once you delete your account, there is no going back. Please be certain.
                </p>
              </div>
              <DeleteAccountDialog userEmail={userEmail} />
            </CardContent>
          </Card>
        </div>
      </div>
    </AuthGuard>
  );
}
