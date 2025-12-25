-- Migration: Create user_usage table for tracking monthly conversion counts
-- Description: Creates user_usage table with RLS policies for Story 6.1
-- Date: 2025-12-25
-- Story: 6.1 - Usage Tracking with Supabase PostgreSQL

-- ========================================
-- 1. Create user_usage table
-- ========================================
CREATE TABLE IF NOT EXISTS public.user_usage (
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  month DATE NOT NULL, -- Format: YYYY-MM-01 (first day of month)
  conversion_count INTEGER NOT NULL DEFAULT 0,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  PRIMARY KEY (user_id, month)
);

-- ========================================
-- 2. Create indexes for performance
-- ========================================
CREATE INDEX idx_user_usage_user_id ON public.user_usage(user_id);
CREATE INDEX idx_user_usage_month ON public.user_usage(month);

-- ========================================
-- 3. Enable Row Level Security
-- ========================================
ALTER TABLE public.user_usage ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only read their own usage stats
CREATE POLICY "Users can read own usage"
  ON public.user_usage
  FOR SELECT
  USING (auth.uid() = user_id);

-- Note: INSERT/UPDATE operations are performed via backend service with service role key
-- Backend uses explicit user_id filtering for defense-in-depth security

-- ========================================
-- 4. Create PostgreSQL function for atomic increment
-- ========================================
-- This function provides atomic UPSERT with increment to prevent race conditions
CREATE OR REPLACE FUNCTION increment_user_usage(p_user_id UUID, p_month DATE)
RETURNS INTEGER AS $$
DECLARE
  new_count INTEGER;
BEGIN
  INSERT INTO public.user_usage (user_id, month, conversion_count, updated_at)
  VALUES (p_user_id, p_month, 1, NOW())
  ON CONFLICT (user_id, month)
  DO UPDATE SET
    conversion_count = public.user_usage.conversion_count + 1,
    updated_at = NOW()
  RETURNING conversion_count INTO new_count;

  RETURN new_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ========================================
-- 5. Add table comments for documentation
-- ========================================
COMMENT ON TABLE public.user_usage IS 'Tracks monthly conversion usage per user for tier limit enforcement';
COMMENT ON COLUMN public.user_usage.user_id IS 'Reference to auth.users - identifies the user';
COMMENT ON COLUMN public.user_usage.month IS 'First day of month in UTC (YYYY-MM-01 format)';
COMMENT ON COLUMN public.user_usage.conversion_count IS 'Number of conversions started in this month';
COMMENT ON COLUMN public.user_usage.updated_at IS 'Last time this usage record was updated';

COMMENT ON FUNCTION increment_user_usage(UUID, DATE) IS 'Atomically increments usage count for user+month, creates row if not exists';
