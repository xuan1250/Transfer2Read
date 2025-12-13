# Supabase Migration Guide

## How to Apply Migrations

### Option 1: Supabase SQL Editor (Recommended for Development)

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Open the migration file (e.g., `004_pipeline_enhancements.sql`)
4. Copy the entire SQL content
5. Paste into SQL Editor and click "Run"
6. Verify the migration was successful

### Option 2: Supabase CLI

```bash
# Install Supabase CLI if not installed
npm install -g supabase

# Link your project
supabase link --project-ref your-project-ref

# Apply migration
supabase db push
```

## Migration 004: Pipeline Enhancements

**File:** `migrations/004_pipeline_enhancements.sql`
**Story:** 4.1 - Conversion Pipeline Orchestrator
**Date:** 2025-12-12

### Changes

1. **New Columns:**
   - `progress`: INTEGER (0-100) - Progress percentage for conversion
   - `stage_metadata`: JSONB - Metadata about current pipeline stage
   - `deleted_at`: TIMESTAMPTZ - Soft delete timestamp for cancellation

2. **New Status Values:**
   - `ANALYZING` - AI layout analysis in progress (25%)
   - `EXTRACTING` - Content extraction in progress (50%)
   - `STRUCTURING` - Structure recognition in progress (75%)
   - `GENERATING` - EPUB generation in progress (90%)
   - `CANCELLED` - Job cancelled by user

3. **New Indexes:**
   - `idx_conversion_jobs_status` - Faster status filtering
   - `idx_conversion_jobs_deleted_at` - Faster cancellation checks

### Verification

After applying the migration, verify with:

```sql
-- Check new columns exist
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'conversion_jobs'
AND column_name IN ('progress', 'stage_metadata', 'deleted_at');

-- Check new indexes exist
SELECT indexname FROM pg_indexes
WHERE tablename = 'conversion_jobs';

-- Test new status values
UPDATE conversion_jobs
SET status = 'ANALYZING', progress = 25
WHERE id = (SELECT id FROM conversion_jobs LIMIT 1);
```

### Rollback (if needed)

```sql
-- Remove new columns
ALTER TABLE public.conversion_jobs
DROP COLUMN IF EXISTS progress,
DROP COLUMN IF EXISTS stage_metadata,
DROP COLUMN IF EXISTS deleted_at;

-- Restore original status constraint
ALTER TABLE public.conversion_jobs
DROP CONSTRAINT IF EXISTS conversion_jobs_status_check;

ALTER TABLE public.conversion_jobs
ADD CONSTRAINT conversion_jobs_status_check
CHECK (status IN ('UPLOADED', 'QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED'));

-- Drop indexes
DROP INDEX IF EXISTS idx_conversion_jobs_status;
DROP INDEX IF EXISTS idx_conversion_jobs_deleted_at;
```

## Notes

- Migrations should be applied in order (001, 002, 003, 004, ...)
- Always test migrations in development before applying to production
- Keep migration files in version control
- Document all schema changes in this guide
