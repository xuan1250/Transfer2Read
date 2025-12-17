'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import { useJob } from '@/hooks/useJob';
import SplitScreenComparison from '@/components/business/SplitScreenComparison';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { AlertCircle, ArrowLeft } from 'lucide-react';

/**
 * Split-Screen PDF/EPUB Preview Page
 *
 * Route: /jobs/[id]/preview
 *
 * Authentication: Required (redirects to /login if unauthenticated)
 * Authorization: Job ownership validated (403 if not user's job)
 * Access: Only accessible when job status is COMPLETED
 *
 * Displays side-by-side comparison of original PDF and converted EPUB
 * with synchronized scrolling and quality verification features.
 */
export default function PreviewPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;
  const supabase = createClient();

  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);

  // Check authentication
  useEffect(() => {
    const checkAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        // Redirect to login with return URL
        router.push(`/login?returnUrl=${encodeURIComponent(`/jobs/${jobId}/preview`)}`);
        return;
      }

      setIsAuthenticated(true);
      setAuthLoading(false);
    };

    checkAuth();
  }, [supabase, router, jobId]);

  // Fetch job details
  const { data: job, isLoading: jobLoading, error: jobError } = useJob(jobId);

  // Show auth loading state
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-4">
          <Skeleton className="h-8 w-64 mx-auto" />
          <Skeleton className="h-4 w-48 mx-auto" />
        </div>
      </div>
    );
  }

  // Only render if authenticated
  if (!isAuthenticated) {
    return null;
  }

  // Show job loading state
  if (jobLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-4">
          <Skeleton className="h-96 w-full max-w-6xl mx-auto" />
          <p className="text-sm text-gray-500">Loading preview...</p>
        </div>
      </div>
    );
  }

  // Handle job errors (404, 403, etc.)
  if (jobError) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
        <div className="max-w-md w-full space-y-6">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="mt-2">
              {jobError.message === 'Not Found'
                ? 'Job not found. The conversion job you\'re looking for doesn\'t exist or has been deleted.'
                : jobError.message === 'Forbidden'
                ? 'You do not have permission to view this job.'
                : 'Unable to load job details. Please try again later.'}
            </AlertDescription>
          </Alert>

          <Button
            variant="outline"
            className="w-full"
            onClick={() => router.push('/jobs')}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Jobs
          </Button>
        </div>
      </div>
    );
  }

  // Validate job exists and is completed
  if (!job) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
        <div className="max-w-md w-full space-y-6">
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="mt-2">
              Job not found or not accessible.
            </AlertDescription>
          </Alert>

          <Button
            variant="outline"
            className="w-full"
            onClick={() => router.push('/jobs')}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Jobs
          </Button>
        </div>
      </div>
    );
  }

  // Check if job is completed
  if (job.status !== 'COMPLETED') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
        <div className="max-w-md w-full space-y-6">
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="mt-2">
              Preview is only available for completed conversions.
              Current status: {job.status}
            </AlertDescription>
          </Alert>

          <Button
            variant="outline"
            className="w-full"
            onClick={() => router.push(`/jobs/${jobId}`)}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Job Status
          </Button>
        </div>
      </div>
    );
  }

  // Render split-screen comparison
  return (
    <SplitScreenComparison job={job} />
  );
}
