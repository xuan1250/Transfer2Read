'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import { Job } from '@/types/job';
import { fetchJob, getDownloadUrl } from '@/lib/api-client';
import { useToast } from '@/hooks/use-toast';
import { Toaster } from '@/components/ui/toaster';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { JobProgress } from '@/components/business/JobProgress';
import { useJobProgress } from '@/hooks/useJobProgress';
import { Download, ArrowLeft, Loader2, FileText, Calendar, Clock } from 'lucide-react';
import { format } from 'date-fns';

// Loading skeleton component
function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <Skeleton className="h-10 w-10 rounded" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-6 w-[300px]" />
          <Skeleton className="h-4 w-[200px]" />
        </div>
      </div>
      <Skeleton className="h-48 w-full" />
      <Skeleton className="h-32 w-full" />
    </div>
  );
}

export default function JobStatusPage() {
  const router = useRouter();
  const params = useParams();
  const jobId = params?.id as string;
  const supabase = createClient();
  const { toast } = useToast();

  const [job, setJob] = useState<Job | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [downloadingJobId, setDownloadingJobId] = useState<string | null>(null);

  // Get real-time progress for active jobs
  const { progress } = useJobProgress(jobId);

  // Load job details
  useEffect(() => {
    const loadJob = async () => {
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        router.push('/login');
        return;
      }

      setIsAuthenticated(true);

      try {
        const jobData = await fetchJob(session.access_token, jobId);
        setJob(jobData);
      } catch (error) {
        const err = error as Error;
        if (err.message === 'UNAUTHORIZED') {
          router.push('/login');
          return;
        }
        toast({
          title: 'Error',
          description: err.message || 'Failed to load job details',
          variant: 'destructive',
        });
      } finally {
        setIsLoading(false);
      }
    };

    if (jobId) {
      loadJob();
    }
  }, [jobId, router, supabase, toast]);

  // Extract filename - prefer original_filename, fallback to input_path extraction
  const getFilename = (job: Job): string => {
    if (job.original_filename) return job.original_filename;
    if (!job.input_path) return 'Untitled';
    const parts = job.input_path.split('/');
    return parts[parts.length - 1] || job.input_path;
  };

  // Format date
  const formatDate = (dateString: string): string => {
    try {
      return format(new Date(dateString), 'MMM dd, yyyy HH:mm');
    } catch {
      return dateString;
    }
  };

  // Handle download
  const handleDownload = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      router.push('/login');
      return;
    }

    try {
      setDownloadingJobId(jobId);
      const { download_url } = await getDownloadUrl(session.access_token, jobId);

      // Trigger download
      window.location.href = download_url;

      toast({
        title: 'Download Started',
        description: 'Your EPUB file download has started.',
      });
    } catch (error) {
      const err = error as Error;
      toast({
        title: 'Download Failed',
        description: err.message || 'Failed to download file',
        variant: 'destructive',
        action: (
          <Button
            variant="outline"
            size="sm"
            onClick={handleDownload}
          >
            Retry
          </Button>
        ),
      });
    } finally {
      setDownloadingJobId(null);
    }
  };

  if (!isAuthenticated) {
    return null; // Will redirect
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <LoadingSkeleton />
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center py-16">
            <h2 className="text-2xl font-semibold text-slate-900 mb-2">Job Not Found</h2>
            <p className="text-slate-600 mb-6">
              The conversion job you&apos;re looking for doesn&apos;t exist or you don&apos;t have access to it.
            </p>
            <Button
              onClick={() => router.push('/history')}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to History
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const isProcessing = ['PROCESSING', 'QUEUED', 'ANALYZING', 'EXTRACTING', 'STRUCTURING', 'GENERATING'].includes(job.status);
  const isCompleted = job.status === 'COMPLETED';
  const isFailed = job.status === 'FAILED' || job.status === 'CANCELLED';

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={() => router.push('/history')}
            className="mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to History
          </Button>

          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
                {getFilename(job)}
                {isCompleted && <Badge className="bg-green-100 text-green-800">Complete</Badge>}
                {isProcessing && <Badge className="bg-blue-100 text-blue-800">Processing</Badge>}
                {isFailed && <Badge variant="destructive">Failed</Badge>}
              </h1>
              <p className="mt-2 text-slate-600">
                Conversion job details and progress
              </p>
            </div>
          </div>
        </div>

        {/* Real-Time Progress (for PROCESSING/QUEUED jobs) */}
        {isProcessing && (
          <div className="mb-6">
            <JobProgress jobId={jobId} />
          </div>
        )}

        {/* Job Details */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Job Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  Created
                </p>
                <p className="text-base font-semibold text-foreground">
                  {formatDate(job.created_at)}
                </p>
              </div>

              {job.completed_at && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    Completed
                  </p>
                  <p className="text-base font-semibold text-foreground">
                    {formatDate(job.completed_at)}
                  </p>
                </div>
              )}

              <div>
                <p className="text-sm font-medium text-muted-foreground">Job ID</p>
                <p className="text-sm font-mono text-foreground break-all">{job.id}</p>
              </div>

              <div>
                <p className="text-sm font-medium text-muted-foreground">Status</p>
                <p className="text-base font-semibold text-foreground">
                  {progress?.stage_description || job.status}
                </p>
              </div>
            </div>

            {job.error_message && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm font-medium text-red-800 mb-1">Error Message</p>
                <p className="text-sm text-red-700">{job.error_message}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Download Button (for COMPLETED jobs) */}
        {isCompleted && (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <h3 className="text-lg font-semibold text-slate-900 mb-2">
                  Your EPUB is ready!
                </h3>
                <p className="text-slate-600 mb-6">
                  Download your converted file below
                </p>
                <Button
                  onClick={handleDownload}
                  disabled={downloadingJobId === jobId}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                  size="lg"
                >
                  {downloadingJobId === jobId ? (
                    <>
                      <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                      Downloading...
                    </>
                  ) : (
                    <>
                      <Download className="h-5 w-5 mr-2" />
                      Download EPUB
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Failed State */}
        {isFailed && (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <h3 className="text-lg font-semibold text-red-800 mb-2">
                  Conversion Failed
                </h3>
                <p className="text-slate-600 mb-6">
                  There was an error converting your PDF. Please try uploading it again or contact support if the problem persists.
                </p>
                <Button
                  onClick={() => router.push('/')}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  Upload New File
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <Toaster />
    </div>
  );
}
