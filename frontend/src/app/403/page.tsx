/**
 * 403 Forbidden Page
 *
 * Displayed when users try to access admin routes without superuser privileges.
 */
'use client';

import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { ShieldAlert } from 'lucide-react';

export default function ForbiddenPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full text-center">
        <div className="flex justify-center mb-6">
          <div className="p-4 bg-red-100 rounded-full">
            <ShieldAlert className="h-16 w-16 text-red-600" />
          </div>
        </div>

        <h1 className="text-4xl font-bold text-gray-900 mb-4">403 Forbidden</h1>
        <p className="text-lg text-gray-600 mb-8">
          You don't have permission to access this page. Admin privileges are required.
        </p>

        <div className="space-y-3">
          <Button
            onClick={() => router.push('/dashboard')}
            className="w-full bg-blue-600 hover:bg-blue-700"
          >
            Go to Dashboard
          </Button>
          <Button
            variant="outline"
            onClick={() => router.back()}
            className="w-full"
          >
            Go Back
          </Button>
        </div>
      </div>
    </div>
  );
}
