-- Migration: Add quality_report column to conversion_jobs table
-- Story: 4-5-ai-based-quality-assurance-confidence-scoring
-- Date: 2025-12-13

-- Add quality_report column to store QA metrics
ALTER TABLE conversion_jobs
ADD COLUMN IF NOT EXISTS quality_report JSONB DEFAULT '{}'::jsonb;

-- Add GIN index for efficient JSONB queries (optional, for analytics)
CREATE INDEX IF NOT EXISTS idx_conversion_jobs_quality_report
ON conversion_jobs USING GIN (quality_report);

-- Add comment for documentation
COMMENT ON COLUMN conversion_jobs.quality_report IS
'Quality assurance metrics including confidence scores, element counts, warnings, and fidelity validation. Populated progressively during conversion pipeline.';

-- RLS policies: Existing policies already cover this column
-- Users can read/update their own jobs, so quality_report is automatically protected
-- No additional RLS policy needed
