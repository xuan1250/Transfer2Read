# Integration Tests for RLS (Row Level Security)

This directory contains integration tests that verify Supabase Row Level Security policies work correctly with real database interactions.

## Prerequisites

### 1. Test Supabase Project

You need a separate Supabase project for integration testing. **Do NOT use your production project.**

#### Option A: Create a Test Supabase Project (Recommended)

1. Go to [supabase.com](https://supabase.com)
2. Create a new project named "transfer2read-test" or similar
3. Apply the migration from `backend/supabase/migrations/create_conversion_jobs_table.sql`
4. Note your credentials from Settings > API

#### Option B: Use Local Supabase (Advanced)

```bash
# Install Supabase CLI
npm install -g supabase

# Start local Supabase
cd backend
supabase start

# Apply migrations
supabase db push
```

### 2. Environment Variables

Create a `.env.test` file in the `backend/` directory:

```bash
# Test Supabase Project Credentials (NOT production!)
TEST_SUPABASE_URL=https://your-test-project.supabase.co
TEST_SUPABASE_ANON_KEY=your-anon-key
TEST_SUPABASE_SERVICE_KEY=your-service-role-key

# Also needed for FastAPI app
SUPABASE_URL=${TEST_SUPABASE_URL}
SUPABASE_SERVICE_KEY=${TEST_SUPABASE_SERVICE_KEY}
SUPABASE_JWT_SECRET=your-jwt-secret
```

**Security Note:** Never commit `.env.test` to version control. It's already in `.gitignore`.

## Running Integration Tests

### Run All Integration Tests

```bash
cd backend

# Load test environment variables
export $(cat .env.test | xargs)

# Run integration tests
pytest tests/integration/test_rls_jobs.py -v

# Or run with markers
pytest -m integration -v
```

### Run Specific Test Classes

```bash
# Test RLS job access controls
pytest tests/integration/test_rls_jobs.py::TestRLSJobAccess -v

# Test RLS job deletion
pytest tests/integration/test_rls_jobs.py::TestRLSJobDeletion -v

# Test RLS job download
pytest tests/integration/test_rls_jobs.py::TestRLSJobDownload -v

# Test soft delete with RLS
pytest tests/integration/test_rls_jobs.py::TestRLSSoftDelete -v
```

### Skip Integration Tests

If environment variables are not set, integration tests are automatically skipped:

```bash
# Run all tests, skip integration if env vars missing
pytest tests/ -v
```

## Test Coverage

The integration tests verify:

### ✅ AC9.1-9.2: Test User Setup
- Creates two test users (Alice and Bob) with unique emails
- Generates JWT tokens for authenticated requests
- Cleans up test data after test run

### ✅ AC9.3: Cross-User Access Blocked
- **Test:** `test_alice_can_read_own_job` - Alice can access her own job
- **Test:** `test_bob_cannot_read_alice_job` - Bob cannot access Alice's job (404)
- **Verification:** RLS policies prevent unauthorized access

### ✅ AC9.4: Job List Isolation
- **Test:** `test_alice_lists_only_own_jobs` - Alice only sees her jobs
- **Test:** `test_bob_lists_only_own_jobs` - Bob doesn't see Alice's jobs
- **Verification:** Multi-tenancy enforced at database level

### ✅ AC9.5: Job Deletion by Owner
- **Test:** `test_alice_can_delete_own_job` - Alice can delete her jobs
- **Verification:** Soft delete sets `deleted_at` timestamp

### ✅ AC9.6: Deletion Blocked for Non-Owner
- **Test:** `test_bob_cannot_delete_alice_job` - Bob cannot delete Alice's job (404)
- **Verification:** RLS DELETE policy enforces ownership

### ✅ Additional: Download Access Control
- **Test:** `test_alice_can_download_own_job` - Owner can download
- **Test:** `test_bob_cannot_download_alice_job` - Non-owner blocked

### ✅ Additional: Soft Delete Enforcement
- **Test:** `test_deleted_jobs_not_visible_in_list` - Deleted jobs excluded from lists
- **Test:** `test_deleted_jobs_not_accessible_directly` - Deleted jobs return 404

## Test Architecture

### Fixtures

**`test_supabase_client`** (module-scoped)
- Creates Supabase client with service role key
- Used for admin operations (user creation, cleanup)

**`test_users`** (module-scoped)
- Creates Alice and Bob with unique emails per test run
- Returns user_id, email, and access_token for each
- Cleans up jobs and users after all tests

**`alice_job`** (function-scoped)
- Creates a completed job for Alice
- Used by tests that need existing job data
- Automatically cleaned up after each test

### Test Isolation

- Each test run uses unique email addresses (`alice-{uuid}@test.local`)
- Module-scoped fixtures ensure users are created once per test session
- Function-scoped fixtures ensure fresh data for each test
- Cleanup happens automatically via fixture teardown

## Troubleshooting

### Tests are Skipped

**Symptom:** All integration tests show "SKIPPED"

**Solution:** Set the required environment variables:
```bash
export TEST_SUPABASE_URL=https://...
export TEST_SUPABASE_ANON_KEY=...
export TEST_SUPABASE_SERVICE_KEY=...
```

### Authentication Errors

**Symptom:** `401 Unauthorized` errors

**Solution:**
1. Verify JWT secret is correct in `.env.test`
2. Check that SUPABASE_JWT_SECRET matches your test project
3. Ensure test users were created successfully

### RLS Policy Errors

**Symptom:** Tests fail with "new row violates row-level security policy"

**Solution:**
1. Verify RLS policies are applied: Check Supabase Dashboard > Authentication > Policies
2. Re-run migration: `backend/supabase/migrations/create_conversion_jobs_table.sql`
3. Ensure policies include `deleted_at IS NULL` for SELECT

### User Creation Fails

**Symptom:** `Failed to create Alice` or `Failed to create Bob`

**Solution:**
1. Check Supabase Auth is enabled: Dashboard > Authentication > Settings
2. Verify email confirmation is disabled for test project
3. Ensure service role key has admin permissions

### Database Connection Errors

**Symptom:** `Connection refused` or `timeout`

**Solution:**
1. Verify TEST_SUPABASE_URL is correct
2. Check Supabase project is active (not paused)
3. Ensure network connectivity to Supabase

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run integration tests
        env:
          TEST_SUPABASE_URL: ${{ secrets.TEST_SUPABASE_URL }}
          TEST_SUPABASE_ANON_KEY: ${{ secrets.TEST_SUPABASE_ANON_KEY }}
          TEST_SUPABASE_SERVICE_KEY: ${{ secrets.TEST_SUPABASE_SERVICE_KEY }}
          SUPABASE_JWT_SECRET: ${{ secrets.TEST_SUPABASE_JWT_SECRET }}
        run: |
          cd backend
          pytest tests/integration/test_rls_jobs.py -v
```

### GitLab CI Example

```yaml
integration_tests:
  stage: test
  script:
    - cd backend
    - pip install -r requirements.txt
    - pytest tests/integration/test_rls_jobs.py -v
  variables:
    TEST_SUPABASE_URL: $TEST_SUPABASE_URL
    TEST_SUPABASE_ANON_KEY: $TEST_SUPABASE_ANON_KEY
    TEST_SUPABASE_SERVICE_KEY: $TEST_SUPABASE_SERVICE_KEY
    SUPABASE_JWT_SECRET: $TEST_SUPABASE_JWT_SECRET
  only:
    - main
    - merge_requests
```

## Best Practices

1. **Separate Test Project:** Always use a dedicated Supabase project for testing
2. **Regular Cleanup:** Integration tests create and cleanup data automatically
3. **Unique Identifiers:** Test emails use UUIDs to avoid conflicts
4. **Service Role Key:** Only used in fixtures for admin operations
5. **Environment Isolation:** Never use production credentials in tests

## Additional Resources

- [Supabase RLS Documentation](https://supabase.com/docs/guides/auth/row-level-security)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)
- [Pytest Fixtures Guide](https://docs.pytest.org/en/latest/fixture.html)
