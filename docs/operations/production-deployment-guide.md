# Production Deployment Guide

**Document Owner:** Xavier (Product Manager)
**Created:** 2025-12-30
**Last Updated:** 2025-12-30
**Purpose:** Step-by-step guide for deploying Transfer2Read to production

---

## Overview

This guide covers deploying Transfer2Read to production using:

- **Frontend:** Vercel (Next.js)
- **Backend API + Worker:** Railway (FastAPI + Celery)
- **Database + Auth + Storage:** Supabase
- **Domain:** Custom domain (transfer2read.com, api.transfer2read.com)

**Prerequisites:**

- [ ] Completed Quick Wins QW-1, QW-2, QW-3 (domain, Supabase, API keys)
- [ ] GitHub repository with all code committed
- [ ] Accounts created: Vercel, Railway, Supabase
- [ ] Production secrets documented in password manager (see `docs/operations/production-secrets-template.md`)

**Time Required:** 2-3 hours (first time), 30 minutes (subsequent deployments)

---

## Table of Contents

1. [Step 1: Supabase Production Setup](#step-1-supabase-production-setup)
2. [Step 2: Vercel Frontend Deployment](#step-2-vercel-frontend-deployment)
3. [Step 3: Railway Backend Deployment](#step-3-railway-backend-deployment)
4. [Step 4: Railway Worker Deployment](#step-4-railway-worker-deployment)
5. [Step 5: Domain Configuration](#step-5-domain-configuration)
6. [Step 6: End-to-End Verification](#step-6-end-to-end-verification)
7. [Troubleshooting](#troubleshooting)
8. [Rollback Procedures](#rollback-procedures)

---

## Step 1: Supabase Production Setup

**Note:** This should already be completed in Quick Win QW-2. If not, follow these steps.

### 1.1 Create Production Project

1. **Log in to Supabase:**
   - Navigate to https://supabase.com/dashboard
   - Click "New Project"

2. **Configure Project:**
   ```
   Name: Transfer2Read Production
   Database Password: [Strong password from password manager]
   Region: [Closest to Railway deployment - US East or EU West]
   ```

3. **Wait for Provisioning:**
   - Project creation takes 2-3 minutes
   - Copy Project URL: `https://xxxxx.supabase.co`

### 1.2 Configure Authentication

1. **Enable Email/Password Provider:**
   - Dashboard → Authentication → Providers → Email
   - Toggle **ON**
   - Confirm email required: **Enabled**

2. **Optional: Enable OAuth Providers:**
   - **Google OAuth:** Follow Quick Win QW-2 steps
   - **GitHub OAuth:** Follow Quick Win QW-2 steps

### 1.3 Create Database Tables

1. **Navigate to SQL Editor:**
   - Dashboard → SQL Editor → New query

2. **Run Table Creation Script:**

```sql
-- Conversion Jobs Table
CREATE TABLE public.conversion_jobs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  status TEXT NOT NULL CHECK (status IN ('UPLOADED', 'ANALYZING', 'CONVERTING', 'COMPLETED', 'FAILED')),
  input_path TEXT NOT NULL,
  output_path TEXT,
  quality_report JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

-- User Usage Tracking Table
CREATE TABLE public.user_usage (
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  month DATE NOT NULL,
  conversion_count INT DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_conversion_jobs_user_id ON public.conversion_jobs(user_id);
CREATE INDEX idx_conversion_jobs_created_at ON public.conversion_jobs(created_at);
CREATE INDEX idx_user_usage_user_id_month ON public.user_usage(user_id, month);
```

3. **Verify Tables Created:**
   - Dashboard → Table Editor → Check `conversion_jobs` and `user_usage` appear

### 1.4 Configure Row Level Security (RLS)

1. **Enable RLS on Tables:**
   - Table Editor → `conversion_jobs` → RLS tab → **Enable RLS**
   - Repeat for `user_usage` table

2. **Add RLS Policies:**

```sql
-- Conversion Jobs Policies
CREATE POLICY "Users can view their own jobs"
ON public.conversion_jobs
FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own jobs"
ON public.conversion_jobs
FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own jobs"
ON public.conversion_jobs
FOR UPDATE
USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own jobs"
ON public.conversion_jobs
FOR DELETE
USING (auth.uid() = user_id);

-- User Usage Policies
CREATE POLICY "Users can view their own usage"
ON public.user_usage
FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own usage"
ON public.user_usage
FOR UPDATE
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own usage"
ON public.user_usage
FOR INSERT
WITH CHECK (auth.uid() = user_id);
```

### 1.5 Create Storage Buckets

1. **Navigate to Storage:**
   - Dashboard → Storage → Create bucket

2. **Create `uploads` Bucket:**
   ```
   Name: uploads
   Public: No (Private)
   Allowed MIME types: application/pdf
   Max file size: 52428800 bytes (50MB)
   ```

3. **Create `downloads` Bucket:**
   ```
   Name: downloads
   Public: No (Private)
   Allowed MIME types: application/epub+zip
   Max file size: 104857600 bytes (100MB)
   ```

4. **Configure Storage RLS Policies:**

```sql
-- Allow users to upload PDFs to their own folder
CREATE POLICY "Users can upload PDFs to their folder"
ON storage.objects
FOR INSERT
WITH CHECK (
  bucket_id = 'uploads' AND
  auth.uid()::text = (storage.foldername(name))[1]
);

-- Allow users to read from their own folder
CREATE POLICY "Users can read their own files"
ON storage.objects
FOR SELECT
USING (
  bucket_id IN ('uploads', 'downloads') AND
  auth.uid()::text = (storage.foldername(name))[1]
);

-- Allow users to delete their own files
CREATE POLICY "Users can delete their own files"
ON storage.objects
FOR DELETE
USING (
  bucket_id IN ('uploads', 'downloads') AND
  auth.uid()::text = (storage.foldername(name))[1]
);
```

### 1.6 Collect API Credentials

1. **Navigate to Settings → API:**
   - Copy **Project URL:** `https://xxxxx.supabase.co`
   - Copy **anon/public key:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
   - Copy **service_role key:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

2. **Store in Password Manager:**
   - Update "Transfer2Read Production Secrets" secure note
   - Reference: `docs/operations/production-secrets-template.md`

---

## Step 2: Vercel Frontend Deployment

### 2.1 Connect GitHub Repository

1. **Log in to Vercel:**
   - Navigate to https://vercel.com/dashboard
   - Click "Add New Project"

2. **Import Git Repository:**
   - Click "Import Git Repository"
   - Select your GitHub organization/user
   - Find "Transfer2Read" repository
   - Click "Import"

3. **Configure Project:**
   ```
   Framework Preset: Next.js (auto-detected)
   Root Directory: frontend/
   Build Command: npm run build (auto-detected)
   Output Directory: .next (auto-detected)
   Install Command: npm install (auto-detected)
   ```

### 2.2 Configure Environment Variables

1. **Add Environment Variables:**
   - Click "Environment Variables" section
   - Add the following for **Production** environment:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
NEXT_PUBLIC_API_URL=https://api.transfer2read.com
NEXT_PUBLIC_ENVIRONMENT=production
```

**Note:** Replace `xxxxx.supabase.co` with your actual Supabase production project URL (from Step 1.6).

2. **Deploy:**
   - Click "Deploy"
   - Wait for build to complete (2-5 minutes)
   - Note the generated Vercel URL: `https://transfer2read.vercel.app`

### 2.3 Add Custom Domain

**Note:** Complete QW-1 (Domain Purchase & DNS Setup) before this step.

1. **Navigate to Project Settings:**
   - Vercel Dashboard → Transfer2Read project → Settings → Domains

2. **Add Custom Domain:**
   - Click "Add Domain"
   - Enter: `transfer2read.com`
   - Click "Add"

3. **Configure DNS:**
   - Vercel provides DNS records to add:
     - **A Record:** `@` → `76.76.21.21` (or Vercel's current IP)
     - **OR CNAME:** `@` → `cname.vercel-dns.com`
   - Add these records to your domain registrar's DNS settings

4. **Add WWW Redirect (Optional):**
   - Click "Add Domain" again
   - Enter: `www.transfer2read.com`
   - Vercel auto-redirects `www` → `transfer2read.com` (301 permanent)

5. **Wait for DNS Propagation:**
   - DNS changes take 5-60 minutes (usually <10 minutes)
   - Vercel auto-provisions SSL certificate via Let's Encrypt
   - Once ready, status shows "Valid Configuration" with padlock icon

6. **Verify:**
   ```bash
   curl -I https://transfer2read.com
   # Expected: 200 OK, SSL certificate valid
   ```

---

## Step 3: Railway Backend Deployment

### 3.1 Create Railway Project

1. **Log in to Railway:**
   - Navigate to https://railway.app/dashboard
   - Click "New Project"

2. **Choose Template:**
   - Click "Deploy from GitHub repo"
   - Authorize Railway to access GitHub
   - Select "Transfer2Read" repository

3. **Configure Service:**
   ```
   Service Name: backend-api
   Root Directory: backend/
   Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

### 3.2 Configure Environment Variables

1. **Navigate to Service Variables:**
   - Railway Dashboard → Transfer2Read project → backend-api service → Variables

2. **Add Environment Variables:**

```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
REDIS_URL=redis://default:password@redis.railway.internal:6379
CELERY_BROKER_URL=${REDIS_URL}/0
CELERY_RESULT_BACKEND=${REDIS_URL}/0
ENVIRONMENT=production
FRONTEND_URL=https://transfer2read.com
ALLOWED_ORIGINS=https://transfer2read.com,https://www.transfer2read.com
```

**Note:** Replace placeholder values with actual production secrets from password manager.

**Important:** `REDIS_URL` will be auto-populated after adding Redis plugin in Step 3.3.

### 3.3 Add Redis Plugin

1. **Add Redis Service:**
   - Railway Dashboard → Transfer2Read project → New Service
   - Click "Database" → "Redis"
   - Railway provisions Redis and auto-sets `REDIS_URL`

2. **Verify Redis URL:**
   - Check Variables tab → `REDIS_URL` should appear automatically
   - Format: `redis://default:password@redis.railway.internal:6379`

### 3.4 Deploy Backend API

1. **Trigger Deployment:**
   - Railway auto-deploys when environment variables are set
   - Monitor deployment in Railway Dashboard → Deployments tab
   - Wait for "Deployed" status (2-5 minutes)

2. **Note Railway URL:**
   - Railway generates temporary URL: `https://backend-api-production-xxxxx.up.railway.app`
   - We'll replace this with custom domain in Step 5

### 3.5 Add Custom Domain

1. **Navigate to Service Settings:**
   - Railway Dashboard → backend-api service → Settings → Domains

2. **Add Custom Domain:**
   - Click "Add Domain"
   - Enter: `api.transfer2read.com`
   - Railway provides CNAME record:
     - **CNAME:** `api` → `backend-api-production-xxxxx.up.railway.app`

3. **Configure DNS:**
   - Add CNAME record to domain registrar DNS settings
   - Wait for DNS propagation (5-60 minutes)
   - Railway auto-provisions SSL certificate

4. **Verify:**
   ```bash
   curl https://api.transfer2read.com/api/health
   # Expected: {"status":"healthy","database":"connected","redis":"connected","timestamp":"2025-12-30T..."}
   ```

---

## Step 4: Railway Worker Deployment

### 4.1 Create Worker Service

1. **Add New Service:**
   - Railway Dashboard → Transfer2Read project → New Service
   - Click "GitHub Repo" → Select "Transfer2Read"

2. **Configure Worker Service:**
   ```
   Service Name: celery-worker
   Root Directory: backend/
   Start Command: celery -A app.worker worker --loglevel=info
   ```

### 4.2 Configure Environment Variables

**Copy ALL environment variables from backend-api service:**

```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
REDIS_URL=redis://default:password@redis.railway.internal:6379
CELERY_BROKER_URL=${REDIS_URL}/0
CELERY_RESULT_BACKEND=${REDIS_URL}/0
ENVIRONMENT=production
```

**Note:** Worker and API must share same `REDIS_URL` to communicate via Celery task queue.

### 4.3 Deploy Worker

1. **Trigger Deployment:**
   - Railway auto-deploys worker service
   - Monitor logs for Celery startup messages:
     ```
     [INFO/MainProcess] celery@celery-worker ready.
     ```

2. **Verify Worker Connectivity:**
   - Check Railway logs for "Connected to redis://..." message
   - Test by uploading PDF via frontend → verify conversion starts

---

## Step 5: Domain Configuration

**Note:** This should already be completed in Quick Win QW-1. If not, follow these steps.

### 5.1 DNS Records Summary

Add the following DNS records to your domain registrar (Namecheap, Google Domains, Cloudflare):

| Type  | Name | Value                                      | TTL  |
|-------|------|--------------------------------------------|------|
| A     | @    | 76.76.21.21 (Vercel IP, check Vercel docs) | 3600 |
| CNAME | www  | cname.vercel-dns.com                       | 3600 |
| CNAME | api  | backend-api-production-xxxxx.up.railway.app | 3600 |

**Alternative: Use Cloudflare for DNS:**
- Benefit: Faster propagation, DDoS protection, analytics
- Add Cloudflare nameservers to domain registrar
- Configure DNS records in Cloudflare dashboard
- **Important:** Set "Proxy status" to "DNS only" (grey cloud) initially to avoid SSL issues

### 5.2 Verify DNS Propagation

```bash
# Check frontend domain
dig transfer2read.com +short
# Expected: Vercel IP or CNAME

# Check backend domain
dig api.transfer2read.com +short
# Expected: Railway CNAME

# Check from external DNS server (Google)
dig @8.8.8.8 transfer2read.com +short
```

---

## Step 6: End-to-End Verification

### 6.1 Smoke Test Procedure

1. **Test Frontend Loading:**
   ```bash
   curl -I https://transfer2read.com
   # Expected: 200 OK, content-type: text/html
   ```

2. **Test Backend API Health:**
   ```bash
   curl https://api.transfer2read.com/api/health
   # Expected: {"status":"healthy","database":"connected","redis":"connected",...}
   ```

3. **Test User Registration:**
   - Visit https://transfer2read.com
   - Click "Sign Up"
   - Register with test email: `test@example.com`
   - Verify email confirmation sent (check Supabase Dashboard → Authentication → Users)

4. **Test PDF Upload & Conversion:**
   - Log in with test account
   - Upload sample PDF (use simple text PDF for first test)
   - Verify upload progress shown
   - Wait for conversion to complete (check Railway worker logs)
   - Download EPUB
   - Open EPUB in Apple Books / Calibre → verify content

5. **Test Error Handling:**
   - Upload invalid file (e.g., .txt file)
   - Expected: Error message shown, no crash

### 6.2 Monitoring & Logs

**Railway Logs:**
```bash
# View backend API logs
Railway Dashboard → backend-api service → Logs → Real-time

# View worker logs
Railway Dashboard → celery-worker service → Logs → Real-time

# Search for errors:
Filter: "error" OR "exception" OR "failed"
```

**Vercel Logs:**
```bash
# View frontend logs
Vercel Dashboard → Transfer2Read project → Logs

# Filter by function invocations, build logs, edge network logs
```

**Supabase Logs:**
```bash
# View database queries
Supabase Dashboard → Logs → Database → Query performance

# View auth events
Supabase Dashboard → Logs → Auth → Login attempts, sign-ups
```

### 6.3 Performance Check

**Test API Response Times:**
```bash
# Health endpoint (should be <200ms)
time curl https://api.transfer2read.com/api/health

# Frontend load time (should be <2s for initial load)
time curl https://transfer2read.com | wc -l
```

**Expected Performance:**
- Frontend initial load: <2 seconds (with CDN)
- API health check: <200ms
- PDF upload (10MB): <5 seconds
- Conversion (simple PDF): 20-60 seconds
- Conversion (complex PDF): 60-180 seconds

---

## Troubleshooting

### Issue: Frontend shows "API not reachable"

**Symptoms:**
- Frontend loads, but API calls fail with CORS errors or network errors

**Diagnosis:**
```bash
# Check CORS configuration
curl -H "Origin: https://transfer2read.com" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS https://api.transfer2read.com/api/conversions

# Expected: Access-Control-Allow-Origin: https://transfer2read.com
```

**Fix:**
1. Verify `ALLOWED_ORIGINS` in Railway backend-api service includes frontend domain
2. Check FastAPI CORS middleware in `backend/app/main.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=settings.ALLOWED_ORIGINS.split(","),
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```
3. Redeploy backend service after fixing

---

### Issue: Backend API returns 503 Service Unavailable

**Symptoms:**
- `/api/health` endpoint returns `{"status":"unhealthy","database":"disconnected: ..."}`

**Diagnosis:**
```bash
# Check health endpoint
curl https://api.transfer2read.com/api/health

# Expected error message shows which service failed (database or redis)
```

**Fix (Supabase Connection Failed):**
1. Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in Railway env vars
2. Test Supabase connection manually:
   ```bash
   curl -H "apikey: YOUR_SUPABASE_SERVICE_KEY" \
        https://xxxxx.supabase.co/rest/v1/conversion_jobs?limit=1
   # Expected: 200 OK with empty array []
   ```
3. Check Supabase project status (ensure not paused due to inactivity)

**Fix (Redis Connection Failed):**
1. Verify Railway Redis service is running (Dashboard → Redis service → Status)
2. Check `REDIS_URL` env var matches Redis service internal URL
3. Restart Redis service if stuck

---

### Issue: Celery worker not processing tasks

**Symptoms:**
- PDF uploads succeed, but conversions never start
- Worker logs show no activity

**Diagnosis:**
```bash
# Check Railway worker logs
Railway Dashboard → celery-worker service → Logs

# Look for "Connected to redis://..." message
# Look for "[INFO/MainProcess] celery@celery-worker ready."
```

**Fix:**
1. Verify worker service has same `REDIS_URL` as backend-api service
2. Check worker start command: `celery -A app.worker worker --loglevel=info`
3. Restart worker service
4. Test task submission manually:
   ```bash
   # SSH into Railway backend service (if Railway CLI installed)
   railway run bash

   # Inside container:
   python3 << 'EOF'
   from app.worker import test_celery_task
   result = test_celery_task.delay()
   print(f"Task ID: {result.id}")
   EOF

   # Check worker logs for task execution
   ```

---

### Issue: Custom domain not working (DNS not resolving)

**Symptoms:**
- `curl https://transfer2read.com` returns "Could not resolve host"

**Diagnosis:**
```bash
# Check DNS propagation
dig transfer2read.com +short
# Expected: Vercel IP or CNAME (not empty)

# Check from multiple locations
# Use online tool: https://dnschecker.org/#A/transfer2read.com
```

**Fix:**
1. Verify DNS records added correctly to domain registrar
2. Wait 5-60 minutes for DNS propagation (can take up to 48 hours in rare cases)
3. Clear local DNS cache:
   ```bash
   # macOS
   sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder

   # Linux
   sudo systemd-resolve --flush-caches

   # Windows
   ipconfig /flushdns
   ```
4. Try accessing via mobile data (bypasses local DNS cache)

---

### Issue: SSL certificate not provisioning

**Symptoms:**
- `curl https://transfer2read.com` returns SSL certificate error

**Diagnosis:**
```bash
# Check SSL certificate
curl -vI https://transfer2read.com 2>&1 | grep -A 5 "SSL certificate"

# Expected: Certificate issued by Let's Encrypt
```

**Fix (Vercel):**
1. Vercel auto-provisions SSL via Let's Encrypt (usually takes 5-10 minutes)
2. Verify DNS is pointing correctly (A record or CNAME)
3. Remove and re-add domain in Vercel dashboard
4. Contact Vercel support if SSL fails after 1 hour

**Fix (Railway):**
1. Railway auto-provisions SSL for custom domains
2. Verify CNAME record is correct
3. Check Railway service logs for SSL provisioning errors
4. Contact Railway support if SSL fails

---

## Rollback Procedures

**See detailed rollback procedures in:** `docs/operations/rollback-procedures.md`

### Quick Rollback Steps

**Rollback Frontend (Vercel):**
```bash
# Option 1: Via Vercel Dashboard
Vercel Dashboard → Transfer2Read → Deployments → Previous deployment → "Promote to Production"

# Option 2: Via Vercel CLI
vercel rollback
```

**Rollback Backend (Railway):**
```bash
# Option 1: Via Railway Dashboard
Railway Dashboard → backend-api → Deployments → Previous deployment → Redeploy

# Option 2: Via Railway CLI
railway rollback
```

**Rollback Database (Supabase):**
```bash
# Restore from backup
Supabase Dashboard → Database → Backups → Select backup → Restore
```

---

## Post-Deployment Checklist

**After successful deployment, verify:**

- [ ] Frontend loads at https://transfer2read.com (200 OK, SSL valid)
- [ ] Backend API health check returns `{"status":"healthy"}` at https://api.transfer2read.com/api/health
- [ ] User registration works (test account created in Supabase)
- [ ] PDF upload works (file appears in Supabase Storage uploads bucket)
- [ ] Conversion completes (EPUB downloadable, renders correctly in e-reader)
- [ ] Worker logs show Celery tasks executing
- [ ] Monitoring enabled (defer to Story 7.1: Sentry error tracking, UptimeRobot)
- [ ] Production secrets stored in password manager (all team members have access)
- [ ] Rollback procedures tested (verify you can rollback Vercel + Railway deployments)
- [ ] Documentation updated (README.md production section accurate)

---

## Next Steps

**After deployment:**

1. **Complete Epic 7 Story 7.1:** Add monitoring (Sentry, UptimeRobot, PostHog)
2. **Soft Launch:** Invite beta users (see `docs/operations/beta-users.csv`)
3. **Monitor Production Metrics:**
   - Supabase Dashboard → Database size, active users
   - Railway Dashboard → CPU, memory, network usage
   - Vercel Analytics → Page views, performance
4. **Set up Alerts:**
   - Railway: Email alerts for high CPU/memory usage
   - Supabase: Email alerts for database size approaching limit
   - OpenAI/Anthropic: Billing alerts for 80% and 100% of monthly budget
5. **Schedule API Key Rotation:**
   - Add calendar reminder for 90 days from now (OpenAI + Anthropic)
   - Follow `docs/operations/api-key-rotation-guide.md`

---

## Related Documentation

- **[Rollback Procedures](rollback-procedures.md)** - Emergency rollback and disaster recovery
- **[API Key Rotation Guide](api-key-rotation-guide.md)** - Rotate OpenAI/Anthropic keys quarterly
- **[Production Secrets Template](production-secrets-template.md)** - Master template for storing secrets
- **[Quick Wins Plan](../sprint-artifacts/quick-wins-plan-2025-12-26.md)** - Pre-launch preparation checklist
- **[Architecture Document](../architecture.md)** - System design and technology stack

---

## Support Contacts

**Primary Contact:** Xavier (Product Manager)
- Email: [your-email@example.com]
- Phone: [+1-XXX-XXX-XXXX]

**Platform Support:**
- Vercel: https://vercel.com/support
- Railway: https://railway.app/help
- Supabase: https://supabase.com/support (Discord: https://discord.supabase.com)
- OpenAI: https://help.openai.com/en/
- Anthropic: support@anthropic.com

---

**Document Status:** ✅ Complete
**Last Reviewed:** 2025-12-30
**Next Review:** After first production deployment (update with actual lessons learned)
