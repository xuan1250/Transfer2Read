'use client';

import React, { useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Upload, CheckCircle, XCircle, Loader2, X } from 'lucide-react';
import axios, { AxiosError } from 'axios';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { createClient } from '@/lib/supabase/client';
import { getTierBenefits } from '@/lib/tierUtils';
import { SubscriptionTier } from '@/types/auth';

/**
 * Upload state management
 */
interface UploadState {
  isDragging: boolean;
  uploadProgress: number;
  uploadError: string | null;
  uploadSuccess: boolean;
  isUploading: boolean;
}

/**
 * Component props interface
 */
interface UploadZoneProps {
  onUploadSuccess?: (jobId: string) => void;
  maxSizeMB?: number;
  className?: string;
}

/**
 * UploadZone Component
 *
 * A drag-and-drop upload zone for PDF files with comprehensive validation,
 * progress tracking, and error handling.
 *
 * Features:
 * - Drag-and-drop file upload
 * - Click-to-browse file selection
 * - Client-side file validation (type & size based on user tier)
 * - Upload progress indicator
 * - Comprehensive error handling
 * - Success state with auto-redirect
 * - Responsive design
 * - Full accessibility (keyboard navigation, ARIA labels)
 */
export default function UploadZone({
  onUploadSuccess,
  maxSizeMB,
  className = ''
}: UploadZoneProps) {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const supabase = createClient();

  // State management
  const [state, setState] = useState<UploadState>({
    isDragging: false,
    uploadProgress: 0,
    uploadError: null,
    uploadSuccess: false,
    isUploading: false
  });

  const [userTier, setUserTier] = useState<SubscriptionTier>('FREE');
  const [jobId, setJobId] = useState<string | null>(null);

  // Fetch user tier on mount
  React.useEffect(() => {
    const fetchUserTier = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.user) {
        const tier = (session.user.user_metadata?.tier as SubscriptionTier) || 'FREE';
        setUserTier(tier);
      }
    };
    fetchUserTier();
  }, [supabase.auth]);

  /**
   * Validate file before upload
   */
  const validateFile = useCallback((file: File): { valid: boolean; error?: string } => {
    // Check file type
    if (file.type !== 'application/pdf') {
      return {
        valid: false,
        error: 'Please upload a PDF file'
      };
    }

    // Get tier-based size limit
    const tierBenefits = getTierBenefits(userTier);
    const maxSize = maxSizeMB || (typeof tierBenefits.maxFileSize === 'number' ? tierBenefits.maxFileSize : 500);
    const maxSizeBytes = maxSize * 1024 * 1024; // Convert MB to bytes

    // Check file size
    if (file.size > maxSizeBytes) {
      return {
        valid: false,
        error: `File size exceeds your tier limit (${maxSize}MB for ${userTier} tier)`
      };
    }

    // Check for empty file
    if (file.size === 0) {
      return {
        valid: false,
        error: 'File is empty or corrupted'
      };
    }

    return { valid: true };
  }, [userTier, maxSizeMB]);

  /**
   * Upload PDF file to backend
   */
  const uploadPDF = useCallback(async (file: File): Promise<{ job_id: string }> => {
    const formData = new FormData();
    formData.append('file', file);

    // Get JWT token from Supabase session
    const { data: { session } } = await supabase.auth.getSession();
    if (!session?.access_token) {
      throw new Error('UNAUTHORIZED');
    }

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    try {
      const response = await axios.post(
        `${apiUrl}/api/v1/upload`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${session.access_token}`
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              setState(prev => ({ ...prev, uploadProgress: percentCompleted }));
            }
          }
        }
      );

      return { job_id: response.data.job_id };
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw error;
      }
      throw new Error('NETWORK_ERROR');
    }
  }, [supabase.auth]);

  /**
   * Handle file selection (from drag-drop or click)
   */
  const handleFileSelect = useCallback(async (file: File) => {
    // Reset state
    setState({
      isDragging: false,
      uploadProgress: 0,
      uploadError: null,
      uploadSuccess: false,
      isUploading: true
    });

    // Validate file
    const validation = validateFile(file);
    if (!validation.valid) {
      setState(prev => ({
        ...prev,
        uploadError: validation.error || 'Invalid file',
        isUploading: false
      }));

      // Auto-dismiss error after 5 seconds
      setTimeout(() => {
        setState(prev => ({ ...prev, uploadError: null }));
      }, 5000);

      return;
    }

    try {
      // Upload file
      const result = await uploadPDF(file);
      setJobId(result.job_id);

      // Show success state
      setState(prev => ({
        ...prev,
        uploadSuccess: true,
        isUploading: false,
        uploadProgress: 100
      }));

      // Call success callback if provided
      if (onUploadSuccess) {
        onUploadSuccess(result.job_id);
      }

      // Redirect after 1 second
      setTimeout(() => {
        router.push(`/jobs/${result.job_id}`);
      }, 1000);

    } catch (error) {
      let errorMessage = 'Upload failed. Please check your connection and try again.';

      if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError<{ detail: string; code: string }>;

        if (axiosError.response?.status === 401) {
          // Unauthorized - redirect to login
          router.push('/login?message=Please log in to upload files');
          return;
        } else if (axiosError.response?.status === 403) {
          // Limit exceeded (conversion or file size)
          const errorData = axiosError.response.data;
          errorMessage = errorData?.detail || 'Limit exceeded. Please upgrade to continue.';
        } else if (axiosError.response?.status === 400) {
          errorMessage = axiosError.response.data?.detail || 'Invalid file. Please upload a valid PDF.';
        } else if (axiosError.response?.status === 413) {
          errorMessage = 'File exceeds tier limit. Upgrade to Pro for unlimited uploads.';
        } else if (axiosError.response?.status === 500) {
          errorMessage = 'Server error. Please try again later.';
        }
      } else if ((error as Error).message === 'UNAUTHORIZED') {
        router.push('/login?message=Please log in to upload files');
        return;
      }

      setState(prev => ({
        ...prev,
        uploadError: errorMessage,
        isUploading: false,
        uploadProgress: 0
      }));

      // Auto-dismiss error after 5 seconds
      setTimeout(() => {
        setState(prev => ({ ...prev, uploadError: null }));
      }, 5000);
    }
  }, [validateFile, uploadPDF, onUploadSuccess, router]);

  /**
   * Drag-and-drop event handlers
   */
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!state.isUploading) {
      setState(prev => ({ ...prev, isDragging: true }));
    }
  }, [state.isUploading]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    // Only set isDragging to false if we're leaving the upload zone itself
    if (e.currentTarget === e.target) {
      setState(prev => ({ ...prev, isDragging: false }));
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (state.isUploading) return;

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      if (files.length > 1) {
        setState(prev => ({
          ...prev,
          uploadError: 'Only one file can be uploaded at a time',
          isDragging: false
        }));
        setTimeout(() => {
          setState(prev => ({ ...prev, uploadError: null }));
        }, 5000);
        return;
      }
      handleFileSelect(files[0]);
    }
  }, [state.isUploading, handleFileSelect]);

  /**
   * Click-to-browse handlers
   */
  const handleClick = useCallback(() => {
    if (!state.isUploading && fileInputRef.current) {
      fileInputRef.current.click();
    }
  }, [state.isUploading]);

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
    // Reset input value to allow re-uploading the same file
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [handleFileSelect]);

  /**
   * Keyboard accessibility
   */
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  }, [handleClick]);

  /**
   * Dismiss error manually
   */
  const dismissError = useCallback(() => {
    setState(prev => ({ ...prev, uploadError: null }));
  }, []);

  /**
   * Navigate to job immediately (before auto-redirect)
   */
  const handleViewJob = useCallback(() => {
    if (jobId) {
      router.push(`/jobs/${jobId}`);
    }
  }, [jobId, router]);

  return (
    <div className={`flex flex-col items-center gap-4 ${className}`}>
      {/* Upload Zone Card */}
      <Card
        className={`
          relative w-full md:w-[500px] lg:w-[600px]
          min-h-[300px] md:h-[350px] lg:h-[400px]
          flex flex-col items-center justify-center
          cursor-pointer transition-all duration-300
          border-2 border-dashed
          ${state.isDragging
            ? 'border-blue-600 bg-blue-50 scale-105'
            : 'border-gray-300 bg-white hover:border-gray-400'
          }
          ${state.isUploading ? 'pointer-events-none opacity-75' : ''}
          ${state.uploadSuccess ? 'border-green-500 bg-green-50' : ''}
        `}
        role="button"
        tabIndex={state.isUploading ? -1 : 0}
        aria-label="Upload PDF file. Drag and drop or press Enter to browse."
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
      >
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          className="hidden"
          onChange={handleFileInputChange}
          aria-label="Upload PDF file"
          disabled={state.isUploading}
        />

        {/* Upload Icon and Instructions */}
        {!state.isUploading && !state.uploadSuccess && (
          <div className="flex flex-col items-center gap-4 px-8 text-center">
            <Upload
              className={`w-16 h-16 ${state.isDragging ? 'text-blue-600' : 'text-gray-400'}`}
            />
            <div>
              <p className="text-lg font-medium text-gray-700 mb-2">
                Drag and drop your PDF here
              </p>
              <p className="text-sm text-gray-500">
                or click to browse
              </p>
            </div>
            <div className="text-xs text-gray-400 mt-2">
              {userTier === 'FREE' ? 'Max 50MB' : 'Unlimited file size'}
            </div>
          </div>
        )}

        {/* Uploading State */}
        {state.isUploading && !state.uploadSuccess && (
          <div className="flex flex-col items-center gap-4 px-8 w-full max-w-md">
            <Loader2 className="w-16 h-16 text-blue-600 animate-spin" />
            <div className="w-full">
              <p className="text-sm font-medium text-gray-700 mb-2 text-center">
                Uploading... {state.uploadProgress}%
              </p>
              <Progress value={state.uploadProgress} className="w-full" />
            </div>
          </div>
        )}

        {/* Success State */}
        {state.uploadSuccess && (
          <div className="flex flex-col items-center gap-4 px-8">
            <CheckCircle className="w-16 h-16 text-green-600" />
            <div className="text-center">
              <p className="text-lg font-medium text-green-700 mb-1">
                ✓ Upload successful!
              </p>
              <p className="text-sm text-gray-600">
                Redirecting to job status...
              </p>
            </div>
            <Button
              onClick={handleViewJob}
              variant="default"
              className="mt-2"
            >
              View Job Now
            </Button>
          </div>
        )}
      </Card>

      {/* Error Alert */}
      {state.uploadError && (
        <Alert
          variant="destructive"
          className="w-full md:w-[500px] lg:w-[600px]"
          role="alert"
          aria-live="polite"
        >
          <XCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span className="text-sm font-medium">{state.uploadError}</span>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 hover:bg-transparent"
              onClick={dismissError}
              aria-label="Dismiss error"
            >
              <X className="h-4 w-4" />
            </Button>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
