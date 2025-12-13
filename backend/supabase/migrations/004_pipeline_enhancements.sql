-- Migration: Pipeline Enhancements for Conversion Jobs
-- Description: Add new status values, progress tracking, and stage metadata for conversion pipeline
-- Date: 2025-12-12
-- Story: 4.1 - Conversion Pipeline Orchestrator

-- Add new columns for progress tracking and stage metadata
ALTER TABLE public.conversion_jobs
ADD COLUMN IF NOT EXISTS progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
ADD COLUMN IF NOT EXISTS stage_metadata JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

-- Update status check constraint to include new pipeline statuses
-- Note: In PostgreSQL, we need to drop and recreate the constraint
ALTER TABLE public.conversion_jobs
DROP CONSTRAINT IF EXISTS conversion_jobs_status_check;

ALTER TABLE public.conversion_jobs
ADD CONSTRAINT conversion_jobs_status_check
CHECK (status IN (
    'UPLOADED',
    'QUEUED',
    'PROCESSING',
    'ANALYZING',
    'EXTRACTING',
    'STRUCTURING',
    'GENERATING',
    'COMPLETED',
    'FAILED',
    'CANCELLED'
));

-- Create index on status for faster queries
CREATE INDEX IF NOT EXISTS idx_conversion_jobs_status
ON public.conversion_jobs(status)
WHERE deleted_at IS NULL;

-- Create index on deleted_at for faster cancellation checks
CREATE INDEX IF NOT EXISTS idx_conversion_jobs_deleted_at
ON public.conversion_jobs(deleted_at)
WHERE deleted_at IS NOT NULL;

-- Add comment on new columns
COMMENT ON COLUMN public.conversion_jobs.progress IS 'Progress percentage (0-100) for current conversion';
COMMENT ON COLUMN public.conversion_jobs.stage_metadata IS 'JSONB metadata about current pipeline stage';
COMMENT ON COLUMN public.conversion_jobs.deleted_at IS 'Timestamp when job was cancelled/deleted by user';
