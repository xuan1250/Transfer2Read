-- Migration: Create conversion_jobs table
-- Description: Creates the conversion_jobs table to track file conversion tasks
-- Date: 2025-12-11
-- Story: 2.1 - Supabase Authentication Setup

CREATE TABLE IF NOT EXISTS public.conversion_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'UPLOADED' CHECK (status IN ('UPLOADED', 'QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED')),
  input_path TEXT,
  output_path TEXT,
  quality_report JSONB,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);
