# Production Environment Verification Checklist

**Generated:** 2025-12-30
**Project:** Transfer2Read
**Epic:** 7 - Launch Readiness
**Story:** 7.1 - Production Environment Verification

## Overview

This checklist verifies that all production services are correctly configured and operational before public launch. Complete each section in order, documenting findings and any issues encountered.

**Production URLs:**
- Frontend: https://transfer2read.com
- Backend API: https://api.transfer2read.com
- API Health: https://api.transfer2read.com/api/health
- API Docs: https://api.transfer2read.com/docs

---

## 1. Production Infrastructure Verification

### 1.1 Vercel Frontend Deployment

- [ ] **Custom Domain Configuration**
  - [ ] Visit https://transfer2read.com - site loads successfully
  - [ ] SSL certificate valid (check browser lock icon)
  - [ ] Certificate issuer: Let's Encrypt or Vercel
  - [ ] HTTP redirects to HTTPS (test http://transfer2read.com)
  - [ ] www subdomain handling verified (https://www.transfer2read.com)

  **Evidence:** _Screenshot of browser showing SSL certificate_
  **Findings:** _Document any issues_

- [ ] **Environment Variables (Vercel Dashboard)**
  - [ ] `NEXT_PUBLIC_SUPABASE_URL` = Production Supabase URL
  - [ ] `NEXT_PUBLIC_SUPABASE_ANON_KEY` = Production anon key (public safe)
  - [ ] `NEXT_PUBLIC_API_URL` = https://api.transfer2read.com
  - [ ] `NEXT_PUBLIC_ENVIRONMENT` = production

  **Verification Method:** Vercel Dashboard > Project > Settings > Environment Variables
  **Findings:** _All variables present and correct: YES / NO / ISSUES:_

- [ ] **Preview Deployments**
  - [ ] Create test branch and push to GitHub
  - [ ] Verify preview deployment URL generated
  - [ ] Preview deployment loads successfully
  - [ ] Preview uses correct environment variables

  **Test Branch:** _branch-name_
  **Preview URL:** _https://transfer2read-git-[branch].vercel.app_
  **Findings:** _Preview deployments working: YES / NO_

### 1.2 Railway Backend API

- [ ] **Health Check Endpoint**
  ```bash
  curl -v https://api.transfer2read.com/api/health
  ```
  - [ ] Returns HTTP 200 OK
  - [ ] Response includes: `{"status": "healthy", "database": "connected", "redis": "connected", "timestamp": "..."}`
  - [ ] Response time < 500ms

  **Response:**
  ```json
  (paste response here)
  ```

  **Findings:** _Health check passing: YES / NO_

- [ ] **Environment Variables (Railway Dashboard)**
  - [ ] `SUPABASE_URL` = Production Supabase URL (same as frontend)
  - [ ] `SUPABASE_SERVICE_KEY` = Service role key (SECRET, not anon key)
  - [ ] `OPENAI_API_KEY` = Production key (starts with sk-proj-)
  - [ ] `ANTHROPIC_API_KEY` = Production key (starts with sk-ant-)
  - [ ] `REDIS_URL` = Railway Redis internal URL
  - [ ] `CELERY_BROKER_URL` = ${REDIS_URL}/0
  - [ ] `CELERY_RESULT_BACKEND` = ${REDIS_URL}/0
  - [ ] `ENVIRONMENT` = production
  - [ ] `FRONTEND_URL` = https://transfer2read.com
  - [ ] `ALLOWED_ORIGINS` = https://transfer2read.com,https://www.transfer2read.com

  **Verification Method:** Railway Dashboard > backend-api > Variables
  **Findings:** _All variables present: YES / NO / MISSING:_

- [ ] **Auto-Deploy from Main Branch**
  - [ ] Make trivial commit to main branch (e.g., update comment in README)
  - [ ] Verify Railway detects commit and triggers deployment
  - [ ] Deployment completes successfully
  - [ ] Health check still passing after deployment

  **Test Commit:** _commit SHA_
  **Deploy Time:** _X minutes_
  **Findings:** _Auto-deploy working: YES / NO_

### 1.3 Railway Celery Worker

- [ ] **Worker Logs Verification**
  - [ ] Access Railway Dashboard > celery-worker > Logs
  - [ ] Search for "Celery worker started" or similar startup message
  - [ ] Search for "LangChain" or "AI SDK" initialization messages
  - [ ] No critical errors in last 100 log lines

  **Log Evidence:** _Screenshot or copy key log lines_
  **Findings:** _Worker started successfully: YES / NO_

- [ ] **Test Job Processing**
  - [ ] Manually trigger a test conversion job (via API or frontend)
  - [ ] Monitor worker logs for job pickup
  - [ ] Verify job completes successfully
  - [ ] Check EPUB file generated in Supabase storage

  **Test Job ID:** _job-uuid_
  **Processing Time:** _X seconds_
  **Findings:** _Worker processes jobs: YES / NO_

### 1.4 Railway Redis

- [ ] **Redis Connection from API**
  - [ ] Health check endpoint already verifies Redis connectivity
  - [ ] Confirm health check shows `"redis": "connected"`

  **Findings:** _Redis accessible from API: YES / NO_

- [ ] **Redis Connection from Worker**
  - [ ] Worker logs show successful connection to Redis
  - [ ] No "ConnectionError" or "RedisError" in worker logs

  **Findings:** _Redis accessible from Worker: YES / NO_

- [ ] **Redis Persistence Configuration**
  - [ ] Railway Dashboard > redis > Configuration
  - [ ] Verify persistence enabled (RDB + AOF)
  - [ ] Verify eviction policy set (allkeys-lru recommended)

  **Persistence:** _Enabled: YES / NO_
  **Eviction Policy:** _policy-name_
  **Findings:** _Redis configured correctly: YES / NO_

---

## 2. Supabase Production Configuration

### 2.1 Production Project Verification

- [ ] **Separate Production Project**
  - [ ] Supabase Dashboard shows separate "Transfer2Read Production" project
  - [ ] Production project URL different from development
  - [ ] Production project region: _region-name_

  **Production Project URL:** _https://xxxxx.supabase.co_
  **Development Project URL:** _https://yyyyy.supabase.co_
  **Findings:** _Separate projects confirmed: YES / NO_

- [ ] **Database Connectivity**
  - [ ] Backend health check shows `"database": "connected"`
  - [ ] Able to query tables via Supabase SQL Editor

  **Findings:** _Database accessible: YES / NO_

### 2.2 Row Level Security (RLS) Policies

- [ ] **Verify RLS Enabled on All Tables**
  ```sql
  SELECT schemaname, tablename, rowsecurity
  FROM pg_tables
  WHERE schemaname = 'public'
  AND tablename IN ('conversion_jobs', 'user_usage');
  ```
  - [ ] `conversion_jobs` RLS enabled: true
  - [ ] `user_usage` RLS enabled: true

  **SQL Result:**
  ```
  (paste result here)
  ```

- [ ] **Verify RLS Policies Exist**
  ```sql
  SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
  FROM pg_policies
  WHERE tablename IN ('conversion_jobs', 'user_usage');
  ```
  - [ ] `conversion_jobs` has SELECT/INSERT/UPDATE/DELETE policies
  - [ ] `user_usage` has SELECT/UPDATE policies
  - [ ] All policies enforce `auth.uid() = user_id` or equivalent

  **SQL Result:**
  ```
  (paste result here)
  ```

  **Findings:** _RLS policies protect user data: YES / NO_

### 2.3 Storage Buckets Configuration

- [ ] **Verify Storage Buckets Exist**
  - [ ] Supabase Dashboard > Storage > Buckets
  - [ ] Bucket: `uploads` exists (Private)
  - [ ] Bucket: `downloads` exists (Private)

  **Findings:** _Buckets configured: YES / NO_

- [ ] **Verify Storage RLS Policies**
  - [ ] Users can only upload to their own folder (auth.uid()/*)
  - [ ] Users can only download from their own folder
  - [ ] Test with test user: upload file to `uploads/{test-user-id}/test.pdf`
  - [ ] Verify file accessible only by that user

  **Test User ID:** _uuid_
  **Test File Path:** _uploads/{uuid}/test.pdf_
  **Findings:** _Storage RLS working: YES / NO_

### 2.4 Authentication Providers

- [ ] **Verify Auth Providers Enabled**
  - [ ] Supabase Dashboard > Authentication > Providers
  - [ ] Email/Password provider enabled
  - [ ] Email confirmation required: YES / NO
  - [ ] Google OAuth configured (Client ID, Client Secret)
  - [ ] GitHub OAuth configured (Client ID, Client Secret)

  **Enabled Providers:**
  - [ ] Email
  - [ ] Google
  - [ ] GitHub

  **Findings:** _All auth providers working: YES / NO_

### 2.5 Database Migrations Applied

- [ ] **Verify All Tables Exist**
  ```sql
  SELECT table_name
  FROM information_schema.tables
  WHERE table_schema = 'public'
  AND table_name IN ('conversion_jobs', 'user_usage');
  ```
  - [ ] Table: `conversion_jobs` exists
  - [ ] Table: `user_usage` exists

  **SQL Result:**
  ```
  (paste result here)
  ```

- [ ] **Verify Database Indexes**
  ```sql
  SELECT tablename, indexname, indexdef
  FROM pg_indexes
  WHERE schemaname = 'public'
  AND tablename IN ('conversion_jobs', 'user_usage');
  ```
  - [ ] Indexes on `user_id` columns exist
  - [ ] Indexes on frequently queried columns exist

  **SQL Result:**
  ```
  (paste result here)
  ```

  **Findings:** _All migrations applied: YES / NO_

### 2.6 Monthly Usage Reset Job

- [ ] **Verify pg_cron or Scheduled Job Configured**
  - [ ] Supabase Dashboard > Database > Cron Jobs (if available)
  - [ ] OR verify external scheduler configured (Vercel Cron, GitHub Actions)
  - [ ] Job resets `user_usage.conversion_count = 0` monthly

  **Reset Schedule:** _1st of every month at midnight UTC_
  **Implementation:** _pg_cron / Vercel Cron / GitHub Actions_
  **Findings:** _Usage reset configured: YES / NO / DEFERRED_

---

## 3. API Keys & Secrets Security

### 3.1 API Key Rotation Verification

- [ ] **OpenAI API Key**
  - [ ] Production key different from development key
  - [ ] Key created date: _YYYY-MM-DD_
  - [ ] OpenAI Dashboard > Usage > Rate Limits configured appropriately
  - [ ] Test API call successful:
    ```bash
    curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"
    ```

  **Key Last 4 Chars:** _...XXXX_
  **Rate Limits:** _RPM: XXX, TPM: XXXX_
  **Findings:** _OpenAI key valid and rotated: YES / NO_

- [ ] **Anthropic API Key**
  - [ ] Production key different from development key
  - [ ] Key created date: _YYYY-MM-DD_
  - [ ] Anthropic Console > API Keys > check key status
  - [ ] Test API call successful:
    ```bash
    curl https://api.anthropic.com/v1/messages -H "x-api-key: $ANTHROPIC_API_KEY" -H "Content-Type: application/json" -d '{"model":"claude-3-haiku-20240307","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
    ```

  **Key Last 4 Chars:** _...XXXX_
  **Findings:** _Anthropic key valid and rotated: YES / NO_

- [ ] **Supabase Service Role Key**
  - [ ] Backend uses service role key (NOT anon key)
  - [ ] Verify in Railway environment variables
  - [ ] Service key never exposed in frontend code

  **Verification:** _Backend uses service role key: YES / NO_

### 3.2 Secrets Storage Verification

- [ ] **Railway Environment Variables**
  - [ ] All secrets stored in Railway (not in code or Git)
  - [ ] Variables marked as "Encrypted" in Railway UI

  **Findings:** _Secrets stored securely in Railway: YES / NO_

- [ ] **Vercel Environment Variables**
  - [ ] All public vars stored in Vercel (not hardcoded)
  - [ ] Only `NEXT_PUBLIC_*` vars exposed to browser

  **Findings:** _Vercel env vars configured correctly: YES / NO_

### 3.3 Git History Verification

- [ ] **Verify .env Files Never Committed**
  ```bash
  git log --all --full-history -- "**/.env*"
  ```
  - [ ] No `.env` files found in git history
  - [ ] If found, verify they don't contain production secrets

  **Git Log Result:**
  ```
  (paste result - should be empty)
  ```

  **Findings:** _No secrets in Git history: YES / NO_

### 3.4 API Key Rotation Documentation

- [ ] **Create API Key Rotation Guide**
  - [ ] Document rotation schedule (90 days recommended)
  - [ ] Document rotation procedure
  - [ ] Store in `docs/operations/api-key-rotation-guide.md`

  **Rotation Schedule:** _Every 90 days_
  **Next Rotation Date:** _2025-03-30_
  **Findings:** _Documentation created: YES / NO_

---

## 4. CORS & Security Configuration

### 4.1 CORS Configuration

- [ ] **Verify CORS Allows Only Production Domains**
  - [ ] Check `backend/app/main.py` CORS configuration
  - [ ] Verify allowed origins:
    - https://transfer2read.com
    - https://www.transfer2read.com
    - https://transfer2read.vercel.app (for preview deployments)
  - [ ] NO localhost domains in production CORS

  **Current CORS Config:**
  ```python
  (paste allow_origins list from main.py)
  ```

  **Findings:** _CORS configured correctly: YES / NO_

- [ ] **Test CORS Headers**
  - [ ] Test unauthorized origin rejected:
    ```bash
    curl -v https://api.transfer2read.com/api/health -H "Origin: https://malicious-site.com"
    ```
  - [ ] Verify response does NOT include `Access-Control-Allow-Origin: https://malicious-site.com`

  - [ ] Test authorized origin accepted:
    ```bash
    curl -v https://api.transfer2read.com/api/health -H "Origin: https://transfer2read.com"
    ```
  - [ ] Verify response includes `Access-Control-Allow-Origin: https://transfer2read.com`

  **Findings:** _CORS correctly restricts access: YES / NO_

### 4.2 Rate Limiting

- [ ] **Verify Rate Limiting Enabled**
  - [ ] Check backend code for rate limiting middleware (if implemented)
  - [ ] OR verify Railway/Vercel rate limiting configured

  **Rate Limiting Implementation:** _FastAPI middleware / Railway / Vercel / NOT YET IMPLEMENTED_
  **Limits:** _X requests per minute per IP_
  **Findings:** _Rate limiting active: YES / NO / DEFERRED_

### 4.3 HTTPS Enforcement

- [ ] **Vercel Frontend HTTPS**
  - [ ] Test HTTP → HTTPS redirect:
    ```bash
    curl -I http://transfer2read.com
    ```
  - [ ] Verify response: `301 Moved Permanently` or `302 Found` to HTTPS

  **Findings:** _Frontend enforces HTTPS: YES / NO_

- [ ] **Railway Backend HTTPS**
  - [ ] Test HTTP → HTTPS redirect (if Railway exposes HTTP):
    ```bash
    curl -I http://api.transfer2read.com
    ```
  - [ ] OR verify Railway only exposes HTTPS port

  **Findings:** _Backend enforces HTTPS: YES / NO_

### 4.4 Security Headers

- [ ] **Verify Security Headers Present**
  ```bash
  curl -I https://api.transfer2read.com/api/health
  ```
  - [ ] `Strict-Transport-Security` (HSTS) header present
  - [ ] `X-Content-Type-Options: nosniff` header present
  - [ ] `X-Frame-Options: DENY` or `SAMEORIGIN` header present

  **Response Headers:**
  ```
  (paste relevant headers)
  ```

  **Findings:** _Security headers configured: YES / NO / PARTIAL_

---

## 5. End-to-End Smoke Tests

### 5.1 User Registration

- [ ] **Create Test User Account**
  - [ ] Navigate to https://transfer2read.com
  - [ ] Click Sign Up
  - [ ] Email: `test+smoke-{timestamp}@example.com`
  - [ ] Password: `Test@12345`
  - [ ] Submit registration form
  - [ ] Verify email confirmation sent (check email or Supabase Dashboard > Auth)
  - [ ] Confirm email (if required)

  **Test Email:** _test+smoke-1234567890@example.com_
  **Registration Time:** _YYYY-MM-DD HH:MM:SS UTC_
  **Screenshot:** _registration-success.png_
  **Findings:** _User registration successful: YES / NO_

### 5.2 User Login

- [ ] **Login with Test User**
  - [ ] Navigate to https://transfer2read.com/login
  - [ ] Enter test user credentials
  - [ ] Submit login form
  - [ ] Verify redirected to dashboard or home
  - [ ] Verify user session active (JWT token in browser)

  **Login Time:** _HH:MM:SS_
  **Screenshot:** _login-success.png_
  **Findings:** _User login successful: YES / NO_

### 5.3 PDF Upload

- [ ] **Upload Test PDF**
  - [ ] Prepare test PDF (10-20 pages, simple text-only document)
  - [ ] Navigate to upload page
  - [ ] Drag-and-drop or click to upload test PDF
  - [ ] Verify upload progress bar appears
  - [ ] Verify upload completes successfully
  - [ ] File uploaded to Supabase Storage: `uploads/{user-id}/...`

  **Test PDF:** _test-document.pdf_ (2.5 MB, 15 pages)
  **Upload Time:** _3 seconds_
  **Screenshot:** _upload-success.png_
  **Findings:** _PDF upload successful: YES / NO_

### 5.4 Conversion Job Monitoring

- [ ] **Monitor Conversion Job Progress**
  - [ ] Conversion job dispatched to Celery worker
  - [ ] Job status updates in real-time (WebSocket or polling)
  - [ ] Railway logs show worker picked up job
  - [ ] AI API calls successful (OpenAI GPT-4o, Anthropic Claude)
  - [ ] Conversion completes without errors

  **Job ID:** _uuid_
  **Processing Time:** _42 seconds_
  **Worker Logs:** _Screenshot or copy key log lines_
  **Findings:** _Conversion job completed: YES / NO_

### 5.5 Quality Report Verification

- [ ] **Verify Conversion Quality Report**
  - [ ] Quality report displayed to user
  - [ ] Confidence score: _99%_ (target: >95%)
  - [ ] Quality issues listed (if any)

  **Quality Score:** _99%_
  **Screenshot:** _quality-report.png_
  **Findings:** _Quality report generated: YES / NO_

### 5.6 EPUB Download

- [ ] **Download Converted EPUB**
  - [ ] Click Download button
  - [ ] EPUB file downloads successfully
  - [ ] File size: _2.8 MB_ (reasonable vs original PDF)
  - [ ] Open EPUB in reader app (Apple Books, Calibre, Adobe Digital Editions)
  - [ ] Verify EPUB opens without errors
  - [ ] Spot-check: Table of contents present, images render, formatting preserved

  **EPUB File:** _test-document.epub_
  **File Size:** _2.8 MB (112% of original PDF)_
  **Screenshot:** _epub-reader-view.png_
  **Findings:** _EPUB download and validation successful: YES / NO_

### 5.7 Usage Tracking Verification

- [ ] **Verify Usage Tracking Incremented**
  - [ ] Supabase Dashboard > Table Editor > `user_usage`
  - [ ] Find row for test user (`user_id = {test-user-uuid}`)
  - [ ] Verify `conversion_count = 1`
  - [ ] Verify `last_conversion_at` updated to recent timestamp

  **User ID:** _uuid_
  **Conversion Count:** _1_
  **Last Conversion At:** _YYYY-MM-DD HH:MM:SS_
  **Screenshot:** _usage-tracking.png_
  **Findings:** _Usage tracking working: YES / NO_

### 5.8 Logout and Re-Login

- [ ] **Logout**
  - [ ] Click Logout button
  - [ ] Verify session cleared (JWT token removed)
  - [ ] Redirected to login or home page

  **Findings:** _Logout successful: YES / NO_

- [ ] **Re-Login**
  - [ ] Login again with same test credentials
  - [ ] Verify previous conversion history visible
  - [ ] Verify usage count persisted

  **Findings:** _Re-login and data persistence successful: YES / NO_

### 5.9 Smoke Test Results Documentation

- [ ] **Document Smoke Test Results**
  - [ ] Create `docs/sprint-artifacts/production-smoke-test-results-{date}.md`
  - [ ] Include all screenshots
  - [ ] Document any errors or issues encountered
  - [ ] Overall smoke test status: PASS / FAIL

  **Results Document:** _docs/sprint-artifacts/production-smoke-test-results-2025-12-30.md_
  **Overall Status:** _PASS / FAIL_

---

## Summary and Sign-Off

### Verification Results

| Section | Status | Notes |
|---------|--------|-------|
| 1. Production Infrastructure | ☐ PASS ☐ FAIL | _notes_ |
| 2. Supabase Production | ☐ PASS ☐ FAIL | _notes_ |
| 3. API Keys & Secrets | ☐ PASS ☐ FAIL | _notes_ |
| 4. CORS & Security | ☐ PASS ☐ FAIL | _notes_ |
| 5. End-to-End Smoke Tests | ☐ PASS ☐ FAIL | _notes_ |

### Critical Issues Identified

1. _Issue description_ - **Severity:** HIGH/MED/LOW - **Status:** OPEN/RESOLVED
2. _Issue description_ - **Severity:** HIGH/MED/LOW - **Status:** OPEN/RESOLVED

### Non-Critical Issues / Improvements

1. _Issue description_ - **Action:** _Deferred to Story X.X / Fixed_
2. _Issue description_ - **Action:** _Deferred to Story X.X / Fixed_

### Final Recommendation

- [ ] **APPROVE** - Production environment ready for public launch
- [ ] **BLOCK** - Critical issues must be resolved before launch

**Verified By:** _Name / Role_
**Date:** _YYYY-MM-DD_
**Signature:** _Digital signature or approval comment_

---

## Next Steps

After verification completes:

1. If APPROVED:
   - [ ] Update sprint-status.yaml: `7-1-production-environment-verification: review → done`
   - [ ] Proceed with Story 7.2: Load and Performance Testing
   - [ ] Schedule beta user invites

2. If BLOCKED:
   - [ ] Create new stories for critical issues
   - [ ] Fix critical issues
   - [ ] Re-run verification checklist
   - [ ] Obtain approval before proceeding

---

**Document Version:** 1.0
**Last Updated:** 2025-12-30
**Related Documents:**
- `docs/architecture.md` - Production Deployment Architecture
- `docs/operations/api-key-rotation-guide.md` - API Key Rotation Procedures
- `docs/operations/rollback-procedures.md` - Rollback Procedures
- `docs/sprint-artifacts/production-smoke-test-results-{date}.md` - Smoke Test Results
