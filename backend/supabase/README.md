# Supabase Database Migrations

This directory contains SQL migration scripts for the Transfer2Read backend.

## How to Apply Migrations

### Option 1: Supabase Dashboard (Recommended for Development)

1. Go to your Supabase project dashboard: https://app.supabase.com
2. Navigate to **SQL Editor** in the left sidebar
3. Click **New Query**
4. Copy the contents of the migration file (e.g., `migrations/create_conversion_jobs_table.sql`)
5. Paste into the SQL Editor
6. Click **Run** to execute the migration

### Option 2: Supabase CLI (Recommended for Production)

```bash
# Install Supabase CLI if not already installed
npm install -g supabase

# Link to your Supabase project
supabase link --project-ref your-project-ref

# Apply all migrations
supabase db push

# Or apply a specific migration
psql "your-postgres-connection-string" < migrations/create_conversion_jobs_table.sql
```

## Migration Files

### `create_conversion_jobs_table.sql`
- **Story:** 3-4-conversion-history-backend-supabase
- **Purpose:** Creates the `conversion_jobs` table with Row Level Security (RLS) policies
- **Features:**
  - Table schema with all required columns
  - Foreign key to `auth.users` with CASCADE delete
  - Indexes on `user_id`, `created_at`, and `status`
  - RLS policies for SELECT, INSERT, UPDATE, DELETE operations
  - Soft delete support via `deleted_at` column

## Verifying Migration Success

After applying the migration, verify in Supabase Dashboard:

1. **Table Editor:** Check that `conversion_jobs` table exists
2. **Table Structure:** Verify all columns are present with correct types
3. **Authentication > Policies:** Confirm 4 RLS policies are active:
   - "Users can view own jobs" (SELECT)
   - "Users can insert own jobs" (INSERT)
   - "Users can update own jobs" (UPDATE)
   - "Users can delete own jobs" (DELETE)

## Testing RLS Policies

Use the SQL Editor to test RLS policies:

```sql
-- Test SELECT policy (should only return jobs for current user)
SELECT * FROM conversion_jobs;

-- Test INSERT policy (should only allow inserting with matching user_id)
INSERT INTO conversion_jobs (user_id, status, input_path)
VALUES (auth.uid(), 'UPLOADED', 'test/path.pdf');

-- Test cross-user access (should return no rows)
SELECT * FROM conversion_jobs WHERE user_id != auth.uid();
```

## Notes

- All migrations should be idempotent (safe to run multiple times)
- Use `IF NOT EXISTS` clauses where applicable
- Always test migrations in a development environment first
- Keep migration files in version control for team collaboration
