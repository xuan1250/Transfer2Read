'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import { Job } from '@/types/job';
import { fetchJobs, fetchJob, getDownloadUrl, deleteJob } from '@/lib/api-client';
import { useToast } from '@/hooks/use-toast';
import { Toaster } from '@/components/ui/toaster';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Download, Trash2, Upload, Loader2 } from 'lucide-react';
import { format } from 'date-fns';

// Status badge component
function JobStatusBadge({ status }: { status: string }) {
  const variants: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; className: string }> = {
    COMPLETED: { variant: 'default', className: 'bg-green-100 text-green-800 border-green-300 hover:bg-green-100' },
    PROCESSING: { variant: 'default', className: 'bg-blue-100 text-blue-800 border-blue-300 hover:bg-blue-100' },
    ANALYZING: { variant: 'default', className: 'bg-blue-100 text-blue-800 border-blue-300 hover:bg-blue-100' },
    QUEUED: { variant: 'secondary', className: 'bg-gray-100 text-gray-800 border-gray-300' },
    UPLOADED: { variant: 'secondary', className: 'bg-gray-100 text-gray-800 border-gray-300' },
    FAILED: { variant: 'destructive', className: 'bg-red-100 text-red-800 border-red-300 hover:bg-red-100' },
  };

  const config = variants[status] || variants.UPLOADED;

  return (
    <Badge variant={config.variant} className={config.className}>
      {status}
    </Badge>
  );
}

// Empty state component
function EmptyHistoryState() {
  const router = useRouter();

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="rounded-full bg-blue-50 p-6 mb-6">
        <Upload className="h-12 w-12 text-blue-600" />
      </div>
      <h2 className="text-2xl font-semibold text-slate-900 mb-2">No conversions yet</h2>
      <p className="text-slate-600 mb-6 text-center max-w-md">
        Upload your first PDF to get started with AI-powered conversion
      </p>
      <Button
        onClick={() => router.push('/')}
        className="bg-blue-600 hover:bg-blue-700 text-white"
      >
        Upload PDF
      </Button>
    </div>
  );
}

// Loading skeleton component
function LoadingSkeleton() {
  return (
    <div className="space-y-4">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="flex items-center space-x-4 p-4 border rounded-lg">
          <Skeleton className="h-12 w-12 rounded" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-[250px]" />
            <Skeleton className="h-4 w-[200px]" />
          </div>
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-8 w-8" />
          <Skeleton className="h-8 w-8" />
        </div>
      ))}
    </div>
  );
}

export default function HistoryPage() {
  const router = useRouter();
  const supabase = createClient();
  const { toast } = useToast();

  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [jobToDelete, setJobToDelete] = useState<string | null>(null);
  const [downloadingJobId, setDownloadingJobId] = useState<string | null>(null);
  const [pollingJobIds, setPollingJobIds] = useState<Set<string>>(new Set());

  const LIMIT = 20;

  // Load jobs function - using useCallback to fix ReferenceError
  const loadJobs = useCallback(async (token: string, currentOffset: number = 0, append: boolean = false) => {
    try {
      if (append) {
        setIsLoadingMore(true);
      } else {
        setIsLoading(true);
      }

      const response = await fetchJobs(token, LIMIT, currentOffset);

      if (append) {
        setJobs(prevJobs => [...prevJobs, ...response.jobs]);
      } else {
        setJobs(response.jobs);
      }

      setTotal(response.total);
      setOffset(currentOffset);

      // Start polling for processing jobs
      const processingJobs = response.jobs.filter(job =>
        job.status === 'PROCESSING' || job.status === 'ANALYZING' || job.status === 'QUEUED'
      );
      if (processingJobs.length > 0) {
        setPollingJobIds(prev => {
          const newSet = new Set(prev);
          processingJobs.forEach(job => newSet.add(job.id));
          return newSet;
        });
      }
    } catch (error) {
      const err = error as Error;
      if (err.message === 'UNAUTHORIZED') {
        router.push('/login');
        return;
      }
      toast({
        title: 'Error',
        description: err.message || 'Failed to load conversion history',
        variant: 'destructive',
        action: (
          <Button
            variant="outline"
            size="sm"
            onClick={async () => {
              const { data: { session } } = await supabase.auth.getSession();
              if (session) {
                loadJobs(session.access_token, currentOffset, append);
              }
            }}
          >
            Retry
          </Button>
        ),
      });
    } finally {
      setIsLoading(false);
      setIsLoadingMore(false);
    }
  }, [router, supabase, toast]);

  // Check authentication
  useEffect(() => {
    const checkAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        router.push('/login');
        return;
      }

      setIsAuthenticated(true);
      loadJobs(session.access_token);
    };

    checkAuth();
  }, [router, supabase, loadJobs]);

  // Polling for processing jobs
  useEffect(() => {
    if (pollingJobIds.size === 0) return;

    const pollJobs = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      for (const jobId of pollingJobIds) {
        try {
          const updatedJob = await fetchJob(session.access_token, jobId);

          // Update job in state
          setJobs(prevJobs =>
            prevJobs.map(job =>
              job.id === updatedJob.id ? updatedJob : job
            )
          );

          // Stop polling if status changed from PROCESSING/ANALYZING/QUEUED
          if (updatedJob.status !== 'PROCESSING' && updatedJob.status !== 'ANALYZING' && updatedJob.status !== 'QUEUED') {
            setPollingJobIds(prev => {
              const newSet = new Set(prev);
              newSet.delete(jobId);
              return newSet;
            });

            // Show completion toast
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
          console.error(`Failed to poll job ${jobId}:`, error);
        }
      }
    };

    const interval = setInterval(pollJobs, 5000); // Poll every 5 seconds

    return () => clearInterval(interval);
  }, [pollingJobIds, supabase, toast]);

  // Extract filename from input_path
  const getFilename = (inputPath: string | null | undefined): string => {
    if (!inputPath) return 'Untitled';
    const parts = inputPath.split('/');
    return parts[parts.length - 1] || inputPath;
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
  const handleDownload = async (jobId: string) => {
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
            onClick={() => handleDownload(jobId)}
          >
            Retry
          </Button>
        ),
      });
    } finally {
      setDownloadingJobId(null);
    }
  };

  // Handle delete
  const handleDelete = async () => {
    if (!jobToDelete) return;

    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      router.push('/login');
      return;
    }

    const jobToDeleteId = jobToDelete;
    const jobToRestore = jobs.find(j => j.id === jobToDeleteId);

    try {
      // Optimistic update
      setJobs(prevJobs => prevJobs.filter(job => job.id !== jobToDeleteId));
      setTotal(prev => prev - 1);
      setDeleteDialogOpen(false);
      setJobToDelete(null);

      await deleteJob(session.access_token, jobToDeleteId);

      toast({
        title: 'Conversion Deleted',
        description: 'The conversion job has been permanently deleted.',
      });
    } catch (error) {
      const err = error as Error;
      // Rollback on error
      if (jobToRestore) {
        setJobs(prevJobs => [...prevJobs, jobToRestore].sort(
          (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        ));
        setTotal(prev => prev + 1);
      }

      toast({
        title: 'Delete Failed',
        description: err.message || 'Failed to delete conversion',
        variant: 'destructive',
        action: (
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setJobToDelete(jobToDeleteId);
              setDeleteDialogOpen(true);
            }}
          >
            Retry
          </Button>
        ),
      });
    }
  };

  // Handle load more
  const handleLoadMore = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      router.push('/login');
      return;
    }

    const newOffset = offset + LIMIT;
    await loadJobs(session.access_token, newOffset, true);
  };

  if (!isAuthenticated) {
    return null; // Will redirect
  }

  const hasMore = jobs.length < total;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">Conversion History</h1>
          <p className="mt-2 text-slate-600">
            View and manage your past PDF to EPUB conversions
          </p>
          {total > 0 && (
            <p className="mt-1 text-sm text-slate-500">
              Showing {jobs.length} of {total} conversions
            </p>
          )}
        </div>

        {isLoading ? (
          <LoadingSkeleton />
        ) : jobs.length === 0 ? (
          <EmptyHistoryState />
        ) : (
          <>
            {/* Desktop Table View */}
            <div className="hidden md:block bg-white rounded-lg shadow">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Filename</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jobs.map((job) => (
                    <TableRow key={job.id}>
                      <TableCell className="font-medium">
                        {getFilename(job.input_path)}
                      </TableCell>
                      <TableCell>{formatDate(job.created_at)}</TableCell>
                      <TableCell>
                        <JobStatusBadge status={job.status} />
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          {job.status === 'COMPLETED' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDownload(job.id)}
                              disabled={downloadingJobId === job.id}
                            >
                              {downloadingJobId === job.id ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Download className="h-4 w-4" />
                              )}
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setJobToDelete(job.id);
                              setDeleteDialogOpen(true);
                            }}
                          >
                            <Trash2 className="h-4 w-4 text-red-600" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Load More Button - Desktop */}
              {hasMore && (
                <div className="p-4 border-t flex justify-center">
                  <Button
                    variant="outline"
                    onClick={handleLoadMore}
                    disabled={isLoadingMore}
                  >
                    {isLoadingMore ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Loading...
                      </>
                    ) : (
                      `Load More (${total - jobs.length} remaining)`
                    )}
                  </Button>
                </div>
              )}
            </div>

            {/* Mobile Card View */}
            <div className="md:hidden space-y-4">
              {jobs.map((job) => (
                <Card key={job.id}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <p className="font-semibold text-slate-900">
                          {getFilename(job.input_path)}
                        </p>
                        <p className="text-sm text-slate-600 mt-1">
                          {formatDate(job.created_at)}
                        </p>
                      </div>
                      <JobStatusBadge status={job.status} />
                    </div>
                    <div className="flex items-center gap-2 mt-4">
                      {job.status === 'COMPLETED' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDownload(job.id)}
                          disabled={downloadingJobId === job.id}
                          className="flex-1"
                        >
                          {downloadingJobId === job.id ? (
                            <>
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              Downloading...
                            </>
                          ) : (
                            <>
                              <Download className="h-4 w-4 mr-2" />
                              Download
                            </>
                          )}
                        </Button>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setJobToDelete(job.id);
                          setDeleteDialogOpen(true);
                        }}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {/* Load More Button - Mobile */}
              {hasMore && (
                <div className="pt-4">
                  <Button
                    variant="outline"
                    onClick={handleLoadMore}
                    disabled={isLoadingMore}
                    className="w-full"
                  >
                    {isLoadingMore ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Loading...
                      </>
                    ) : (
                      `Load More (${total - jobs.length} remaining)`
                    )}
                  </Button>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Conversion?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the conversion job and associated files.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <Toaster />
    </div>
  );
}
