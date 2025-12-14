'use client';

import React, { useEffect, useRef } from 'react';
import { Loader2, Check } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useJobProgress } from '@/hooks/useJobProgress';
import { toast } from '@/hooks/use-toast';

/**
 * Component props interface
 */
interface JobProgressProps {
  jobId: string;
  className?: string;
}

/**
 * Element card component for displaying detected elements
 */
interface ElementCardProps {
  icon: string;
  label: string;
  count: number;
  isComplete?: boolean; // Whether detection is complete (job finished)
}

function ElementCard({ icon, label, count, isComplete = false }: ElementCardProps) {
  const hasElements = count > 0;
  const showCheckmark = isComplete && hasElements;

  return (
    <div className="border rounded-lg p-3 text-center bg-background hover:bg-accent/50 transition-colors relative">
      {/* Checkmark icon when complete */}
      {showCheckmark && (
        <div className="absolute top-1 right-1">
          <Check className="h-4 w-4 text-green-600" />
        </div>
      )}
      <div className="text-2xl mb-1">{icon}</div>
      <div className="text-xs font-medium text-muted-foreground">{label}</div>
      <div className="text-lg font-bold text-foreground">{count}</div>
    </div>
  );
}

/**
 * JobProgress Component
 *
 * Displays real-time progress updates for a conversion job.
 * Automatically polls the backend every 2 seconds while the job is processing.
 *
 * Features:
 * - Animated progress bar with percentage
 * - Current stage description
 * - Element detection counters (tables, images, equations, chapters)
 * - Estimated time remaining
 * - Real-time AI cost estimate
 * - Quality confidence score
 * - Automatic polling management
 * - Error handling with retry logic
 * - Loading states
 *
 * @param jobId - The UUID of the job to track
 * @param className - Optional CSS classes
 *
 * @example
 * ```tsx
 * <JobProgress jobId="123e4567-e89b-12d3-a456-426614174000" />
 * ```
 */
export function JobProgress({ jobId, className }: JobProgressProps) {
  const { progress, isLoading, error } = useJobProgress(jobId);
  const previousStatusRef = useRef<string | null>(null);

  // Show toast notification when job completes
  useEffect(() => {
    if (progress && previousStatusRef.current !== 'COMPLETED' && progress.status === 'COMPLETED') {
      toast({
        title: "✓ Conversion Complete!",
        description: `Your document has been successfully converted with ${progress.quality_confidence || 0}% quality confidence.`,
        variant: "default",
      });
    }
    if (progress) {
      previousStatusRef.current = progress.status;
    }
  }, [progress]);

  // Loading state - first fetch
  if (isLoading && !progress) {
    return (
      <Card className={`p-6 space-y-6 ${className || ''}`}>
        {/* Progress Bar Skeleton */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-5 w-12" />
          </div>
          <Skeleton className="h-2 w-full" />
          <Skeleton className="h-4 w-32" />
        </div>

        {/* Element Detection Skeleton */}
        <div className="space-y-2">
          <Skeleton className="h-5 w-36" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="border rounded-lg p-3 space-y-2">
                <Skeleton className="h-8 w-8 mx-auto rounded-full" />
                <Skeleton className="h-4 w-16 mx-auto" />
                <Skeleton className="h-6 w-12 mx-auto" />
              </div>
            ))}
          </div>
        </div>

        {/* Cost and Quality Skeleton */}
        <div className="flex gap-3">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-6 w-24" />
        </div>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Alert variant="destructive" className={className}>
        <AlertDescription>
          <div className="flex items-center justify-between">
            <span>Connection lost. Reconnecting...</span>
            <Loader2 className="h-4 w-4 animate-spin ml-2" />
          </div>
        </AlertDescription>
      </Alert>
    );
  }

  // No data
  if (!progress) {
    return null;
  }

  const {
    progress_percentage,
    stage_description,
    elements_detected,
    estimated_time_remaining,
    estimated_cost,
    quality_confidence,
    status,
  } = progress;

  // Determine if job is still processing
  const isProcessing = ['PROCESSING', 'QUEUED', 'ANALYZING', 'EXTRACTING', 'STRUCTURING', 'GENERATING'].includes(status);
  const isComplete = status === 'COMPLETED';
  const isFailed = status === 'FAILED' || status === 'CANCELLED';

  return (
    <Card className={`p-6 space-y-6 ${className || ''}`}>
      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <h3 className="text-lg font-semibold text-foreground">
              {stage_description}
            </h3>
            {isProcessing && (
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
            )}
          </div>
          <span className="text-sm font-medium text-muted-foreground">
            {progress_percentage}%
          </span>
        </div>
        <Progress
          value={progress_percentage}
          className="h-2 transition-all duration-300 ease-in-out"
        />
        {estimated_time_remaining && isProcessing && (
          <p className="text-xs text-muted-foreground">
            Estimated time remaining: ~{estimated_time_remaining} seconds
          </p>
        )}
      </div>

      {/* Element Detection Counters */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium text-foreground">Detected Elements</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <ElementCard icon="📊" label="Tables" count={elements_detected.tables} isComplete={isComplete} />
          <ElementCard icon="🖼️" label="Images" count={elements_detected.images} isComplete={isComplete} />
          <ElementCard icon="🧮" label="Equations" count={elements_detected.equations} isComplete={isComplete} />
          <ElementCard
            icon="📖"
            label="Chapters"
            count={elements_detected.chapters}
            isComplete={isComplete}
          />
        </div>
      </div>

      {/* Cost and Quality Indicators */}
      <div className="flex flex-wrap gap-3">
        {/* Estimated Cost */}
        {estimated_cost !== null && estimated_cost !== undefined && (
          <Badge variant="secondary" className="text-xs">
            Estimated cost: ${estimated_cost.toFixed(4)}
          </Badge>
        )}

        {/* Quality Confidence */}
        {quality_confidence !== null && quality_confidence !== undefined && (
          <Badge
            variant={quality_confidence >= 90 ? "default" : quality_confidence >= 70 ? "secondary" : "destructive"}
            className="text-xs"
          >
            Quality: {quality_confidence}%
          </Badge>
        )}

        {/* Status Badge */}
        {isComplete && (
          <Badge variant="default" className="text-xs">
            ✓ Complete
          </Badge>
        )}
        {isFailed && (
          <Badge variant="destructive" className="text-xs">
            ✗ Failed
          </Badge>
        )}
      </div>
    </Card>
  );
}
