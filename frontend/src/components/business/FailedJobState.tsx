/**
 * FailedJobState Component
 *
 * Displays error message and troubleshooting guidance when a job fails
 */

'use client';

import React from 'react';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface FailedJobStateProps {
  errorMessage?: string;
}

export function FailedJobState({ errorMessage }: FailedJobStateProps) {
  const router = useRouter();

  return (
    <div className="space-y-6">
      {/* Error Alert */}
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Conversion Failed</AlertTitle>
        <AlertDescription>
          {errorMessage || 'An unexpected error occurred during conversion.'}
        </AlertDescription>
      </Alert>

      {/* Troubleshooting Guidance */}
      <div className="bg-muted/50 rounded-lg p-6 space-y-4">
        <h3 className="font-semibold text-foreground">Troubleshooting Steps:</h3>
        <ul className="list-disc list-inside space-y-2 text-sm text-muted-foreground">
          <li>Try uploading again - temporary issues may have been resolved</li>
          <li>Check file format - only PDF files are supported</li>
          <li>Ensure your PDF is not corrupted or password-protected</li>
          <li>Large or complex PDFs may take longer - try a smaller file first</li>
          <li>Contact support if the issue persists</li>
        </ul>
      </div>

      {/* Upload Another PDF Button */}
      <Button
        size="lg"
        onClick={() => router.push('/')}
        className="w-full sm:w-auto"
      >
        Upload Another PDF
      </Button>
    </div>
  );
}
