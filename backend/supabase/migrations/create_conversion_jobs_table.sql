-- Migration: Create conversion_jobs table with RLS policies
-- Story: 3-4-conversion-history-backend-supabase
-- Date: 2025-12-12

-- Create conversion_jobs table
CREATE TABLE IF NOT EXISTS conversion_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  status TEXT NOT NULL CHECK (status IN ('UPLOADED', 'PROCESSING', 'COMPLETED', 'FAILED')),
  input_path TEXT NOT NULL,
  output_path TEXT,
  quality_report JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ,
  deleted_at TIMESTAMPTZ
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversion_jobs_user_id ON conversion_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_conversion_jobs_created_at ON conversion_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversion_jobs_status ON conversion_jobs(status);

-- Enable Row Level Security
ALTER TABLE conversion_jobs ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can view only their own non-deleted jobs
CREATE POLICY "Users can view own jobs" ON conversion_jobs
  FOR SELECT
  USING (auth.uid() = user_id AND deleted_at IS NULL);

-- RLS Policy: Users can insert jobs with their own user_id
CREATE POLICY "Users can insert own jobs" ON conversion_jobs
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can update their own jobs
CREATE POLICY "Users can update own jobs" ON conversion_jobs
  FOR UPDATE
  USING (auth.uid() = user_id);

-- RLS Policy: Users can delete their own jobs (soft delete)
CREATE POLICY "Users can delete own jobs" ON conversion_jobs
  FOR DELETE
  USING (auth.uid() = user_id);

-- Comment on table
COMMENT ON TABLE conversion_jobs IS 'Stores conversion job records with user isolation via RLS';
COMMENT ON COLUMN conversion_jobs.status IS 'Job status: UPLOADED, PROCESSING, COMPLETED, or FAILED';
COMMENT ON COLUMN conversion_jobs.quality_report IS 'JSONB field storing AI quality metrics and confidence scores';
COMMENT ON COLUMN conversion_jobs.deleted_at IS 'Soft delete timestamp - non-null means job is deleted';
