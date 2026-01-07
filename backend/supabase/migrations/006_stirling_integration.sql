-- Migration: 006_stirling_integration
-- Description: Add columns for Stirling-PDF integration (html_content, stirling_metadata)

-- Add HTML storage column
ALTER TABLE conversion_jobs 
ADD COLUMN IF NOT EXISTS html_content TEXT;

-- Add Stirling-PDF metadata
ALTER TABLE conversion_jobs 
ADD COLUMN IF NOT EXISTS stirling_metadata JSONB;

-- Comment on columns
COMMENT ON COLUMN conversion_jobs.html_content IS 'Full HTML content converted from PDF via Stirling-PDF';
COMMENT ON COLUMN conversion_jobs.stirling_metadata IS 'Metadata from Stirling-PDF conversion process (version, time, etc.)';
