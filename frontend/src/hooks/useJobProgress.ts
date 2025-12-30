'use client';

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useRef, useEffect } from 'react';
import { createClient } from '@/lib/supabase/client';

/**
 * Progress update data structure from backend
 */
export interface ProgressUpdate {
  job_id: string;
  status: string;
  progress_percentage: number;
  current_stage: string;
  stage_description: string;
  elements_detected: {
    tables: number;
    images: number;
    equations: number;
    chapters: number;
  };
  estimated_time_remaining?: number;
  estimated_cost?: number;
  quality_confidence?: number;
  timestamp: string;
}

/**
 * Custom hook for polling job progress updates
 *
 * Automatically polls the backend every 2 seconds while the job is QUEUED, ANALYZING, EXTRACTING,
 * STRUCTURING, GENERATING, or PROCESSING. Continues polling for 5 seconds after COMPLETED
 * to ensure final metadata is loaded. Stops polling when the job is FAILED or CANCELLED.
 * Includes automatic retry logic with exponential backoff.
 *
 * @param jobId - The UUID of the job to track
 * @returns Object containing progress data, loading state, and error
 *
 * @example
 * ```tsx
 * const { progress, isLoading, error } = useJobProgress(jobId);
 *
 * if (isLoading) return <Skeleton />;
 * if (error) return <ErrorMessage error={error} />;
 * if (!progress) return null;
 *
 * return <ProgressBar percentage={progress.progress_percentage} />;
 * ```
 */
export function useJobProgress(jobId: string) {
  const supabase = createClient();
  const queryClient = useQueryClient();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const completedAtRef = useRef<number | null>(null);

  const { data: progress, isLoading, error, refetch } = useQuery<ProgressUpdate>({
    queryKey: ['job-progress', jobId],
    queryFn: async () => {
      // Get Supabase session for authentication
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        throw new Error('Not authenticated');
      }

      // Fetch progress from backend API
      const response = await fetch(`${apiUrl}/api/v1/jobs/${jobId}/progress`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Job not found');
        }
        if (response.status === 403) {
          throw new Error('Unauthorized to access this job');
        }
        throw new Error('Failed to fetch progress');
      }

      const data = await response.json();

      // Track when job completes for grace period polling
      if (data.status === 'COMPLETED' && !completedAtRef.current) {
        completedAtRef.current = Date.now();
      }

      return data;
    },
    // Poll every 2 seconds while job is active, with grace period after completion
    refetchInterval: (query) => {
      const data = query.state.data;
      const activeStatuses = ['PROCESSING', 'QUEUED', 'ANALYZING', 'EXTRACTING', 'STRUCTURING', 'GENERATING'];

      if (data?.status && activeStatuses.includes(data.status)) {
        return 2000; // 2 seconds - job is actively processing
      }

      // Grace period: Continue polling for 5 seconds after completion to ensure final data is loaded
      if (data?.status === 'COMPLETED' && completedAtRef.current) {
        const timeSinceCompletion = Date.now() - completedAtRef.current;
        if (timeSinceCompletion < 5000) {
          return 2000; // Continue polling for 5 seconds after completion
        }
      }

      return false; // Stop polling when failed, cancelled, or 5s after completion
    },
    // Retry failed requests with exponential backoff
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000), // 1s, 2s, 4s, max 10s
    // Always fetch fresh data (no stale time)
    staleTime: 0,
    // Keep failed queries in cache for error display
    gcTime: 5 * 60 * 1000, // 5 minutes
  });

  // Invalidate parent useJob query when job completes or fails
  // This ensures the job status page updates to show download button
  useEffect(() => {
    if (progress?.status === 'COMPLETED' || progress?.status === 'FAILED') {
      // Invalidate the job query to trigger refetch with final job data
      queryClient.invalidateQueries({ queryKey: ['job', jobId] });
    }
  }, [progress?.status, jobId, queryClient]);

  return {
    progress,
    isLoading,
    error,
    refetch,
  };
}
