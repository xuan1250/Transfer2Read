'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import { Job } from '@/types/job';
import { fetchJob, getDownloadUrl } from '@/lib/api-client';
import { useToast } from '@/hooks/use-toast';
import { Toaster } from '@/components/ui/toaster';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Download,
  ArrowLeft,
  Calendar,
  FileText,
  CheckCircle,
  XCircle,
  Loader2,
  AlertCircle,
  Clock
} from 'lucide-react';
import { format } from 'date-fns';

function JobStatusBadge({ status }: { status: string }) {
  const variants: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; className: string }> = {
    COMPLETED: { variant: 'default', className: 'bg-green-100 text-green-800 border-green-300 hover:bg-green-100' },
    PROCESSING: { variant: 'default', className: 'bg-blue-100 text-blue-800 border-blue-300 hover:bg-blue-100' },
    ANALYZING: { variant: 'default', className: 'bg-blue-100 text-blue-800 border-blue-300 hover:bg-blue-100' },
    EXTRACTING: { variant: 'default', className: 'bg-blue-100 text-blue-800 border-blue-300 hover:bg-blue-100' },
    STRUCTURING: { variant: 'default', className: 'bg-blue-100 text-blue-800 border-blue-300 hover:bg-blue-100' },
    GENERATING: { variant: 'default', className: 'bg-blue-100 text-blue-800 border-blue-300 hover:bg-blue-100' },
    QUEUED: { variant: 'secondary', className: 'bg-gray-100 text-gray-800 border-gray-300' },
    UPLOADED: { variant: 'secondary', className: 'bg-gray-100 text-gray-800 border-gray-300' },
    FAILED: { variant: 'destructive', className: 'bg-red-100 text-red-800 border-red-300 hover:bg-red-100' },
    CANCELLED: { variant: 'secondary', className: 'bg-gray-100 text-gray-800 border-gray-300' },
  };

  const config = variants[status] || variants.UPLOADED;

  return (
    <Badge variant={config.variant} className={config.className}>
      {status}
    </Badge>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-12 w-3/4" />
      <Skeleton className="h-6 w-1/2" />
      <div className="grid gap-6 md:grid-cols-2">
        <Skeleton className="h-48" />
        <Skeleton className="h-48" />
      </div>
      <Skeleton className="h-64" />
    </div>
  );
}

export default function JobDetailPage() {
  const router = useRouter();
  const params = useParams();
  const jobId = params.id as string;
  const supabase = createClient();
  const { toast } = useToast();

  const [job, setJob] = useState<Job | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [downloadingJobId, setDownloadingJobId] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  const getFilename = (inputPath: string | null | undefined): string => {
    if (!inputPath) return 'Untitled';
    const parts = inputPath.split('/');
    return parts[parts.length - 1] || inputPath;
  };

  const formatDate = (dateString: string): string => {
    try {
      return format(new Date(dateString), 'PPpp');
    } catch {
      return dateString;
    }
  };

  const loadJob = async (token: string) => {
    try {
      setIsLoading(true);
      const jobData = await fetchJob(token, jobId);
      setJob(jobData);

      const inProgressStatuses = ['PROCESSING', 'ANALYZING', 'EXTRACTING', 'STRUCTURING', 'GENERATING', 'QUEUED'];
      if (inProgressStatuses.includes(jobData.status)) {
        setIsPolling(true);
      }
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

  useEffect(() => {
    const checkAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        router.push('/login');
        return;
      }

      setIsAuthenticated(true);
      loadJob(session.access_token);
    };

    checkAuth();
  }, [jobId, router, supabase]);

  useEffect(() => {
    if (!isPolling) return;

    const pollJob = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      try {
        const updatedJob = await fetchJob(session.access_token, jobId);
        setJob(updatedJob);

        const inProgressStatuses = ['PROCESSING', 'ANALYZING', 'EXTRACTING', 'STRUCTURING', 'GENERATING', 'QUEUED'];
        if (!inProgressStatuses.includes(updatedJob.status)) {
          setIsPolling(false);

          if (updatedJob.status === 'COMPLETED') {
            toast({
              title: 'Conversion Complete',
              description: 'Your PDF has been successfully converted!',
            });
          } else if (updatedJob.status === 'FAILED') {
            toast({
              title: 'Conversion Failed',
              description: 'There was an error converting your PDF.',
              variant: 'destructive',
            });
          }
        }
      } catch (error) {
        console.error('Failed to poll job:', error);
      }
    };

    const interval = setInterval(pollJob, 5000);

    return () => clearInterval(interval);
  }, [isPolling, jobId, supabase, toast]);

  const handleDownload = async () => {
    if (!job) return;

    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      router.push('/login');
      return;
    }

    try {
      setDownloadingJobId(job.id);
      const { download_url } = await getDownloadUrl(session.access_token, job.id);

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
      });
    } finally {
      setDownloadingJobId(null);
    }
  };

  if (!isAuthenticated) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <LoadingSkeleton />
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Card>
            <CardContent className="p-8 text-center">
              <XCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
              <h2 className="text-2xl font-semibold text-slate-900 mb-2">Job Not Found</h2>
              <p className="text-slate-600 mb-6">
                The conversion job you are looking for does not exist or you do not have access to it.
              </p>
              <Button onClick={() => router.push('/history')}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to History
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Button
          variant="ghost"
          onClick={() => router.push('/history')}
          className="mb-6"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to History
        </Button>

        <div className="mb-8">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 mb-2">
                {getFilename(job.input_path)}
              </h1>
              <p className="text-sm text-slate-600 font-mono">Job ID: {job.id}</p>
            </div>
            <JobStatusBadge status={job.status} />
          </div>

          <div className="flex gap-3">
            {job.status === 'COMPLETED' && (
              <Button
                onClick={handleDownload}
                disabled={downloadingJobId === job.id}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                {downloadingJobId === job.id ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Downloading...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4 mr-2" />
                    Download EPUB
                  </>
                )}
              </Button>
            )}
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2 mb-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Basic Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm font-medium text-slate-600">Status</p>
                <p className="text-base text-slate-900 mt-1">
                  <JobStatusBadge status={job.status} />
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-slate-600">Original Filename</p>
                <p className="text-base text-slate-900 mt-1">{job.original_filename || getFilename(job.input_path)}</p>
              </div>
              {job.input_path && (
                <div>
                  <p className="text-sm font-medium text-slate-600">Input Path</p>
                  <p className="text-sm text-slate-700 mt-1 font-mono break-all">{job.input_path}</p>
                </div>
              )}
              {job.output_path && (
                <div>
                  <p className="text-sm font-medium text-slate-600">Output Path</p>
                  <p className="text-sm text-slate-700 mt-1 font-mono break-all">{job.output_path}</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Timeline
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm font-medium text-slate-600 flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Created
                </p>
                <p className="text-base text-slate-900 mt-1">{formatDate(job.created_at)}</p>
              </div>
              {job.completed_at && (
                <div>
                  <p className="text-sm font-medium text-slate-600 flex items-center gap-2">
                    <CheckCircle className="h-4 w-4" />
                    Completed
                  </p>
                  <p className="text-base text-slate-900 mt-1">{formatDate(job.completed_at)}</p>
                </div>
              )}
              {job.created_at && job.completed_at && (
                <div>
                  <p className="text-sm font-medium text-slate-600">Processing Time</p>
                  <p className="text-base text-slate-900 mt-1">
                    {Math.round((new Date(job.completed_at).getTime() - new Date(job.created_at).getTime()) / 1000 / 60)} minutes
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {job.error_message && (
          <Card className="mb-6 border-red-200 bg-red-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-red-800">
                <AlertCircle className="h-5 w-5" />
                Error Details
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-red-700">{job.error_message}</p>
            </CardContent>
          </Card>
        )}

        {job.quality_report && (
          <Card>
            <CardHeader>
              <CardTitle>Quality Report</CardTitle>
              <CardDescription>Detailed analysis of the conversion quality</CardDescription>
            </CardHeader>
            <CardContent>
              {job.quality_report.overall_confidence !== undefined && (
                <div className="mb-6">
                  <p className="text-sm font-medium text-slate-600 mb-2">Overall Confidence</p>
                  <div className="flex items-center gap-4">
                    <div className="flex-1 bg-gray-200 rounded-full h-3">
                      <div
                        className={`h-3 rounded-full transition-all ${'${'}
                          job.quality_report.overall_confidence >= 80
                            ? 'bg-green-600'
                            : job.quality_report.overall_confidence >= 60
                            ? 'bg-yellow-600'
                            : 'bg-red-600'
                        ${'}'}`}
                        style={{'{{'}{ width: `${'${'}job.quality_report.overall_confidence{'}'}%` {'}}'}}}
                      />
                    </div>
                    <span className="text-lg font-semibold text-slate-900">
                      {job.quality_report.overall_confidence.toFixed(1)}%
                    </span>
                  </div>
                </div>
              )}

              {job.quality_report.elements && (
                <div className="mb-6">
                  <p className="text-sm font-medium text-slate-600 mb-3">Detected Elements</p>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {Object.entries(job.quality_report.elements).map(([key, metrics]) => (
                      <div key={key} className="bg-slate-50 rounded-lg p-4">
                        <p className="text-xs text-slate-600 uppercase mb-1">{key.replace(/_/g, ' ')}</p>
                        <p className="text-2xl font-bold text-slate-900">{metrics.count}</p>
                        {metrics.avg_confidence !== undefined && (
                          <p className="text-xs text-slate-600 mt-1">
                            {metrics.avg_confidence.toFixed(0)}% confidence
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {job.quality_report.warnings && job.quality_report.warnings.length > 0 && (
                <div className="mb-6">
                  <p className="text-sm font-medium text-slate-600 mb-2">Warnings</p>
                  <ul className="list-disc list-inside space-y-1">
                    {job.quality_report.warnings.map((warning, index) => (
                      <li key={index} className="text-sm text-amber-700">{warning}</li>
                    ))}
                  </ul>
                </div>
              )}

              {job.quality_report.pages_processed && (
                <div className="mb-4">
                  <p className="text-sm font-medium text-slate-600">Pages Processed</p>
                  <p className="text-base text-slate-900 mt-1">{job.quality_report.pages_processed}</p>
                </div>
              )}

              {job.quality_report.estimated_cost !== undefined && (
                <div>
                  <p className="text-sm font-medium text-slate-600">Estimated Cost</p>
                  <p className="text-base text-slate-900 mt-1">${job.quality_report.estimated_cost.toFixed(4)}</p>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      <Toaster />
    </div>
  );
}
