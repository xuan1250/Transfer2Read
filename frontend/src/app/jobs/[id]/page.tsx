/**
 * Job Status Page
 *
 * Displays job details, quality report, and action buttons for a conversion job
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import { useJob } from '@/hooks/useJob';
import { JobProgress } from '@/components/business/JobProgress';
import { QualityReportSummary } from '@/components/business/QualityReportSummary';
import { FailedJobState } from '@/components/business/FailedJobState';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import { Download, ArrowLeft, Flag } from 'lucide-react';
import { triggerConfettiOnce } from '@/lib/confetti-utils';
import { FeedbackWidget } from '@/components/business/FeedbackWidget';
import { IssueReportModal } from '@/components/business/IssueReportModal';

export default function JobStatusPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;
  const supabase = createClient();
  const { toast } = useToast();

  const { data: job, isLoading, error } = useJob(jobId);
  const [isDownloading, setIsDownloading] = useState(false);
  const [isAuthChecking, setIsAuthChecking] = useState(true);
  const [isIssueModalOpen, setIsIssueModalOpen] = useState(false);

  // Check authentication
  useEffect(() => {
    const checkAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        // Redirect to login with return URL
        router.push(`/login?returnUrl=/jobs/${jobId}`);
      } else {
        setIsAuthChecking(false);
      }
    };

    checkAuth();
  }, [jobId, router, supabase]);

  // Handle download
  const handleDownload = async () => {
    setIsDownloading(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        throw new Error('Not authenticated');
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/jobs/${jobId}/download`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Download failed');
      }

      const data = await response.json();
      // Open download URL in new tab
      window.open(data.download_url, '_blank');

      // Trigger confetti animation (only once per job)
      triggerConfettiOnce(jobId);

      // Log download event for analytics (AC #7)
      try {
        await fetch(`${apiUrl}/api/v1/jobs/${jobId}/events/download`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
        });
      } catch (analyticsError) {
        // Don't block download for analytics failures
        console.error('Analytics tracking error:', analyticsError);
      }

      toast({
        title: 'Download started!',
        description: 'Your EPUB file is ready',
        variant: 'default',
      });
    } catch (err) {
      console.error('Download error:', err);
      toast({
        title: 'Download failed',
        description: 'Please try again later',
        variant: 'destructive',
      });
    } finally {
      setIsDownloading(false);
    }
  };

  // Loading state - auth check or data fetch
  if (isAuthChecking || (isLoading && !job)) {
    return <LoadingSkeleton />;
  }

  // Error state
  if (error) {
    const errorMessage = error.message;
    return (
      <div className="container mx-auto p-6 max-w-4xl">
        <Alert variant="destructive">
          <AlertDescription>
            {errorMessage === '404'
              ? 'Job not found'
              : errorMessage === '403'
              ? 'You do not have permission to view this job'
              : 'Unable to load job details'}
          </AlertDescription>
        </Alert>
        <Button onClick={() => router.push('/history')} className="mt-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to History
        </Button>
      </div>
    );
  }

  if (!job) return null;

  const isProcessing = ['PROCESSING', 'QUEUED', 'ANALYZING', 'EXTRACTING', 'STRUCTURING', 'GENERATING'].includes(
    job.status
  );
  const isCompleted = job.status === 'COMPLETED';
  const isFailed = job.status === 'FAILED';

  return (
    <div className="container mx-auto p-6 max-w-4xl space-y-6">
      {/* Back Button */}
      <Button variant="ghost" onClick={() => router.push('/history')}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to History
      </Button>

      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground">Conversion Job Status</h1>
        {job.original_filename && (
          <p className="text-sm text-muted-foreground mt-1">File: {job.original_filename}</p>
        )}
      </div>

      {/* Processing State */}
      {isProcessing && <JobProgress jobId={jobId} />}

      {/* Completed State */}
      {isCompleted && job.quality_report && (
        <>
          <QualityReportSummary qualityReport={job.quality_report} />

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4">
            <Button
              size="lg"
              onClick={handleDownload}
              disabled={isDownloading}
              className="flex-1 gap-2"
            >
              <Download className="h-4 w-4" />
              {isDownloading ? 'Downloading...' : 'Download EPUB'}
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => setIsIssueModalOpen(true)}
              className="sm:w-auto gap-2"
            >
              <Flag className="h-4 w-4" />
              Report Issue
            </Button>
          </div>

          {/* Feedback Widget */}
          <FeedbackWidget jobId={jobId} />

          {/* Issue Report Modal */}
          <IssueReportModal
            jobId={jobId}
            isOpen={isIssueModalOpen}
            onClose={() => setIsIssueModalOpen(false)}
          />
        </>
      )}

      {/* Failed State */}
      {isFailed && <FailedJobState errorMessage={job.error_message} />}
    </div>
  );
}

/**
 * Loading Skeleton Component
 */
function LoadingSkeleton() {
  return (
    <div className="container mx-auto p-6 max-w-4xl space-y-6">
      <Skeleton className="h-10 w-64" />
      <Skeleton className="h-64 w-full" />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <Skeleton key={i} className="h-32" />
        ))}
      </div>
      <div className="flex gap-4">
        <Skeleton className="h-12 flex-1" />
        <Skeleton className="h-12 flex-1" />
      </div>
    </div>
  );
}
