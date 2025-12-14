-- Migration: Add AI Layout Analysis Columns
-- Description: Add columns for AI layout analysis results, model tracking, and token usage
-- Date: 2025-12-13
-- Story: 4.2 - LangChain AI Layout Analysis Integration

-- Add AI-related columns to conversion_jobs table
ALTER TABLE public.conversion_jobs
ADD COLUMN IF NOT EXISTS layout_analysis JSONB DEFAULT NULL,
ADD COLUMN IF NOT EXISTS ai_model_used TEXT DEFAULT NULL,
ADD COLUMN IF NOT EXISTS token_usage JSONB DEFAULT NULL;

-- Create index on ai_model_used for analytics queries
CREATE INDEX IF NOT EXISTS idx_conversion_jobs_ai_model_used
ON public.conversion_jobs(ai_model_used)
WHERE ai_model_used IS NOT NULL;

-- Create GIN index on layout_analysis JSONB for efficient querying
-- Enables queries like: WHERE layout_analysis @> '{"page_analyses": [{"tables": {"count": 2}}]}'
CREATE INDEX IF NOT EXISTS idx_conversion_jobs_layout_analysis
ON public.conversion_jobs USING GIN(layout_analysis)
WHERE layout_analysis IS NOT NULL;

-- Add comments on new columns
COMMENT ON COLUMN public.conversion_jobs.layout_analysis IS 'JSONB structure containing AI-detected page elements (tables, images, equations, layout). Format matches LayoutDetection Pydantic model with page_analyses array.';
COMMENT ON COLUMN public.conversion_jobs.ai_model_used IS 'AI model used for analysis: gpt-4o, claude-3-5-haiku-20241022, or mixed (fallback scenario)';
COMMENT ON COLUMN public.conversion_jobs.token_usage IS 'JSONB tracking API token consumption: {"total_prompt_tokens": N, "total_completion_tokens": N, "per_page_average": {...}, "estimated_cost_usd": N}';
