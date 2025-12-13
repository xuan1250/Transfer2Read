# Supabase Migrations

This directory contains SQL migration scripts for the Transfer2Read Supabase database schema.

## Overview

These migrations were extracted from manual Supabase dashboard operations to ensure reproducibility across environments (development, staging, production).

## Migration Files

| File | Description | Story Reference |
|------|-------------|-----------------|
| `001_user_metadata_trigger.sql` | Creates trigger to set default `tier: FREE` for new users | Story 2.1 |
| `002_conversion_jobs_table.sql` | Creates `conversion_jobs` table with proper constraints | Story 2.1 |
| `003_conversion_jobs_rls.sql` | Enables Row Level Security on `conversion_jobs` table | Story 2.1 |

## How to Apply Migrations

### Option 1: Supabase Dashboard (Current Method)

1. Open your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Copy the contents of each migration file in order (001 → 002 → 003)
4. Paste into the SQL editor and click **Run**
5. Verify execution success in the output panel

### Option 2: Supabase CLI (Future - Not Yet Configured)

```bash
# Install Supabase CLI (if not already installed)
npm install -g supabase

# Initialize Supabase locally (one-time setup)
supabase init

# Link to your project
supabase link --project-ref your-project-ref

# Apply migrations
supabase db push
```

**Note:** Supabase CLI integration is not yet configured for this project. For now, use Option 1 (Dashboard).

## Environment Setup

These migrations are designed for fresh Supabase projects. If setting up a new environment:

1. **Development/Staging:** Run all migrations in order
2. **Production:** Migrations already applied (as of 2025-12-11)

### Verification Checklist

After applying migrations, verify:

- [ ] **Trigger Test:** Create a test user in Supabase Auth and verify `raw_user_meta_data` contains `{"tier": "FREE"}`
- [ ] **Table Test:** Query `conversion_jobs` table exists with all columns
- [ ] **RLS Test:** Attempt to query `conversion_jobs` as a user - should only see own records

## Dependencies

These migrations assume:

- Supabase Auth is enabled (Email/Password provider)
- PostgreSQL extensions: `uuid-ossp` (for `gen_random_uuid()`)

## Notes

- **Idempotent Migrations:** All migrations use `CREATE OR REPLACE` or `CREATE IF NOT EXISTS` where possible to allow re-running without errors
- **Order Matters:** Always apply migrations in numerical order (001, 002, 003)
- **Manual Tracking:** Currently no automated migration tracking table. Keep track manually or via Supabase dashboard history

## Future Improvements

- [ ] Set up Supabase CLI for automated migration application
- [ ] Add migration tracking table (e.g., `schema_migrations`)
- [ ] Create rollback scripts for each migration
- [ ] Add automated verification tests

---

**Last Updated:** 2025-12-12
**Epic:** Epic 2 - Authentication & User Profile
**Action Item:** Create SQL Migration Files (Epic 2 Retrospective)
