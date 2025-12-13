-- Migration: Enable RLS on conversion_jobs table
-- Description: Enables Row Level Security and creates policies for user data isolation
-- Date: 2025-12-11
-- Story: 2.1 - Supabase Authentication Setup

-- Enable RLS on conversion_jobs table
ALTER TABLE public.conversion_jobs ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for user isolation
CREATE POLICY "Users can only access own jobs"
  ON public.conversion_jobs
  FOR ALL
  USING (auth.uid() = user_id);
