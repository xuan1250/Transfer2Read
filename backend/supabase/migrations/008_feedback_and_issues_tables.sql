-- Migration: Create feedback and issues tables for Story 5.4
-- Description: Creates job_feedback, job_issues, and conversion_events tables with RLS policies
-- Date: 2025-12-15
-- Story: 5.4 - Download & Feedback Flow

-- ========================================
-- 1. Create job_feedback table
-- ========================================
CREATE TABLE IF NOT EXISTS public.job_feedback (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES public.conversion_jobs(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  rating VARCHAR(10) NOT NULL CHECK (rating IN ('positive', 'negative')),
  comment TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX idx_job_feedback_job_id ON public.job_feedback(job_id);
CREATE INDEX idx_job_feedback_user_id ON public.job_feedback(user_id);
CREATE INDEX idx_job_feedback_created_at ON public.job_feedback(created_at DESC);

-- Enable RLS on job_feedback
ALTER TABLE public.job_feedback ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only insert their own feedback
CREATE POLICY "Users can insert own feedback"
  ON public.job_feedback
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can only read their own feedback
CREATE POLICY "Users can read own feedback"
  ON public.job_feedback
  FOR SELECT
  USING (auth.uid() = user_id);

-- ========================================
-- 2. Create job_issues table
-- ========================================
CREATE TABLE IF NOT EXISTS public.job_issues (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES public.conversion_jobs(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  issue_type VARCHAR(50) NOT NULL,
  page_number INT,
  description TEXT NOT NULL,
  screenshot_url VARCHAR(500),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX idx_job_issues_job_id ON public.job_issues(job_id);
CREATE INDEX idx_job_issues_user_id ON public.job_issues(user_id);
CREATE INDEX idx_job_issues_issue_type ON public.job_issues(issue_type);
CREATE INDEX idx_job_issues_created_at ON public.job_issues(created_at DESC);

-- Enable RLS on job_issues
ALTER TABLE public.job_issues ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only insert their own issues
CREATE POLICY "Users can insert own issues"
  ON public.job_issues
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can only read their own issues
CREATE POLICY "Users can read own issues"
  ON public.job_issues
  FOR SELECT
  USING (auth.uid() = user_id);

-- ========================================
-- 3. Create conversion_events table for analytics
-- ========================================
CREATE TABLE IF NOT EXISTS public.conversion_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES public.conversion_jobs(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  event_type VARCHAR(50) NOT NULL,
  event_data JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for analytics queries
CREATE INDEX idx_conversion_events_job_id ON public.conversion_events(job_id);
CREATE INDEX idx_conversion_events_user_id ON public.conversion_events(user_id);
CREATE INDEX idx_conversion_events_event_type ON public.conversion_events(event_type);
CREATE INDEX idx_conversion_events_created_at ON public.conversion_events(created_at DESC);

-- Enable RLS on conversion_events
ALTER TABLE public.conversion_events ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only insert their own events
CREATE POLICY "Users can insert own events"
  ON public.conversion_events
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can only read their own events (admins would need separate policy)
CREATE POLICY "Users can read own events"
  ON public.conversion_events
  FOR SELECT
  USING (auth.uid() = user_id);

-- ========================================
-- 4. Add comments for documentation
-- ========================================
COMMENT ON TABLE public.job_feedback IS 'User feedback (thumbs up/down) for conversion quality';
COMMENT ON COLUMN public.job_feedback.rating IS 'User rating: positive or negative';
COMMENT ON COLUMN public.job_feedback.comment IS 'Optional comment explaining the rating';

COMMENT ON TABLE public.job_issues IS 'Reported issues with conversion output';
COMMENT ON COLUMN public.job_issues.issue_type IS 'Category of issue (e.g., Table formatting, Missing images)';
COMMENT ON COLUMN public.job_issues.page_number IS 'Optional page number where issue occurs';
COMMENT ON COLUMN public.job_issues.description IS 'Required detailed description of the issue';
COMMENT ON COLUMN public.job_issues.screenshot_url IS 'Optional URL to uploaded screenshot showing the issue';

COMMENT ON TABLE public.conversion_events IS 'Analytics events for download, feedback, and issue tracking';
COMMENT ON COLUMN public.conversion_events.event_type IS 'Event type: download, feedback_positive, feedback_negative, issue_reported';
COMMENT ON COLUMN public.conversion_events.event_data IS 'Optional JSON data with event-specific details';
