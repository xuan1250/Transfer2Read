'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useUser } from '@/hooks/useUser';

interface AuthGuardProps {
  children: React.ReactNode;
}

/**
 * AuthGuard Higher-Order Component
 * Protects routes by ensuring user is authenticated before rendering children
 * Redirects to /login if user is not authenticated
 *
 * @param {React.ReactNode} children - The protected content to render
 *
 * @example
 * ```tsx
 * export default function DashboardPage() {
 *   return (
 *     <AuthGuard>
 *       <div>Protected Dashboard Content</div>
 *     </AuthGuard>
 *   );
 * }
 * ```
 */
export function AuthGuard({ children }: AuthGuardProps) {
  const { user, loading } = useUser();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      // User is not authenticated, redirect to login
      router.push('/login');
    }
  }, [user, loading, router]);

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-4">
          {/* Loading Spinner */}
          <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]"></div>
          <p className="text-gray-600 font-medium">Loading...</p>
        </div>
      </div>
    );
  }

  // If not authenticated, don't render children (will redirect)
  if (!user) {
    return null;
  }

  // User is authenticated, render protected content
  return <>{children}</>;
}
