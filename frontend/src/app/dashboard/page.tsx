'use client';

import { useRouter } from 'next/navigation';
import { AuthGuard } from '@/components/auth/AuthGuard';
import { useUser } from '@/hooks/useUser';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { UsageProgressBar } from '@/components/business/UsageProgressBar';
import { UpgradeBanner } from '@/components/business/UpgradeBanner';

export default function DashboardPage() {
  const { user, signOut } = useUser();
  const router = useRouter();

  const handleSignOut = async () => {
    await signOut();
    router.push('/login');
    router.refresh();
  };

  return (
    <AuthGuard>
      <div className="min-h-screen bg-gray-50 py-8 px-4">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Upgrade Banner (FREE tier only) */}
          <UpgradeBanner />

          {/* Welcome Card */}
          <Card className="shadow-md">
            <CardHeader>
              <CardTitle className="text-2xl font-bold">Dashboard</CardTitle>
              <CardDescription>
                Welcome, {user?.email || 'User'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-md">
                <p className="font-medium">{"You're successfully logged in!"}</p>
                <p className="text-sm mt-1">
                  This is a protected page. Only authenticated users can access this content.
                </p>
              </div>

              {/* User Info */}
              <div className="space-y-2">
                <h3 className="font-semibold text-gray-900">Account Information</h3>
                <div className="bg-white border border-gray-200 rounded-md p-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <p className="text-sm text-gray-600">Email</p>
                      <p className="font-medium text-gray-900">{user?.email}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">User ID</p>
                      <p className="font-mono text-sm text-gray-900">{user?.id}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Sign Out Button */}
              <div className="pt-4">
                <Button
                  onClick={handleSignOut}
                  variant="destructive"
                  className="w-full md:w-auto"
                >
                  Sign Out
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Usage Progress Bar */}
          <UsageProgressBar />

          {/* Quick Actions */}
          <Card className="shadow-md">
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
              <CardDescription>Get started with your PDF conversions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                onClick={() => router.push('/upload')}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                size="lg"
              >
                📄 Upload PDF for Conversion
              </Button>
              <Button
                onClick={() => router.push('/history')}
                variant="outline"
                className="w-full"
                size="lg"
              >
                📋 View Conversion History
              </Button>
              <Button
                onClick={() => router.push('/settings')}
                variant="outline"
                className="w-full"
                size="lg"
              >
                ⚙️ Account Settings
              </Button>
              <Button
                onClick={() => router.push('/pricing')}
                variant="outline"
                className="w-full border-blue-600 text-blue-600 hover:bg-blue-50"
                size="lg"
              >
                ✨ View Pricing Plans
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </AuthGuard>
  );
}
