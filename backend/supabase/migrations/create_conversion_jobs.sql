-- Migration: Create conversion_jobs table with RLS policies
-- Story: 3-2-pdf-upload-api-supabase-integration
-- Date: 2025-12-12

-- Create conversion_jobs table
CREATE TABLE IF NOT EXISTS conversion_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'UPLOADED',
    input_path TEXT NOT NULL,
    output_path TEXT,
    quality_report JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversion_jobs_user_id ON conversion_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_conversion_jobs_status ON conversion_jobs(status);
CREATE INDEX IF NOT EXISTS idx_conversion_jobs_created_at ON conversion_jobs(created_at DESC);

-- Enable Row Level Security
ALTER TABLE conversion_jobs ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can insert their own jobs
CREATE POLICY users_insert_own_jobs
ON conversion_jobs
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can select their own jobs
CREATE POLICY users_select_own_jobs
ON conversion_jobs
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- RLS Policy: Users can update their own jobs
CREATE POLICY users_update_own_jobs
ON conversion_jobs
FOR UPDATE
TO authenticated
USING (auth.uid() = user_id);

-- Add comments for documentation
COMMENT ON TABLE conversion_jobs IS 'Stores PDF to EPUB conversion job metadata and status';
COMMENT ON COLUMN conversion_jobs.id IS 'Unique job identifier (UUID)';
COMMENT ON COLUMN conversion_jobs.user_id IS 'User who created the conversion job';
COMMENT ON COLUMN conversion_jobs.status IS 'Job status: UPLOADED, PROCESSING, COMPLETED, FAILED';
COMMENT ON COLUMN conversion_jobs.input_path IS 'Supabase Storage path to uploaded PDF file';
COMMENT ON COLUMN conversion_jobs.output_path IS 'Supabase Storage path to generated EPUB file (null until completed)';
COMMENT ON COLUMN conversion_jobs.quality_report IS 'AI-generated quality report (JSON)';
COMMENT ON COLUMN conversion_jobs.created_at IS 'Timestamp when job was created';
COMMENT ON COLUMN conversion_jobs.completed_at IS 'Timestamp when job finished processing (null if not completed)';
