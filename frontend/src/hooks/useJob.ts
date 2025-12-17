/**
 * useJob Hook
 *
 * Custom React hook for fetching a single job's details (non-polling version).
 * Based on useJobProgress pattern but for one-time fetch.
 */

import { useQuery } from '@tanstack/react-query';
import { createClient } from '@/lib/supabase/client';
import type { Job } from '@/types/job';

/**
 * Hook for fetching job details
 *
 * @param jobId - UUID of the job to fetch
 * @returns Query result with job data, loading, and error states
 */
export function useJob(jobId: string) {
  const supabase = createClient();

  return useQuery<Job, Error>({
    queryKey: ['job', jobId],
    queryFn: async () => {
      // Get auth session
      const { data: { session }, error: sessionError } = await supabase.auth.getSession();

      if (sessionError || !session) {
        throw new Error('UNAUTHENTICATED');
      }

      // Fetch job details from backend
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/jobs/${jobId}?include_quality_details=true`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('404');
        }
        if (response.status === 403) {
          throw new Error('403');
        }
        throw new Error('Failed to fetch job details');
      }

      const data = await response.json();
      return data as Job;
    },
    retry: 1,
    staleTime: 5000, // Consider data fresh for 5 seconds
    refetchOnWindowFocus: false, // Don't refetch on window focus
  });
}
