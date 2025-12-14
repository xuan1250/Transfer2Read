'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

/**
 * Provider component for TanStack Query
 * Wraps the application to enable React Query hooks
 *
 * @example
 * ```tsx
 * <QueryProvider>
 *   <YourApp />
 * </QueryProvider>
 * ```
 */
export function QueryProvider({ children }: { children: React.ReactNode }) {
  // Create a client instance per component to avoid sharing state between users
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Disable automatic refetching on window focus for better UX
            refetchOnWindowFocus: false,
            // Retry failed queries 3 times
            retry: 3,
            // Cache queries for 5 minutes
            staleTime: 5 * 60 * 1000,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
