# Transfer2Read Deployment Guide

**Last Updated:** 2025-12-04  
**Status:** Production deployment configuration complete - Ready for manual platform setup

---

## Overview

This guide provides step-by-step instructions for deploying Transfer2Read to production using:
- **Frontend:** Vercel (automatic deployment from GitHub)
- **Backend API + Worker:** Railway (containerized deployment)
- **Database + Auth + Storage:** Supabase (managed services)
- **CI/CD:** GitHub Actions (automated testing)

## Prerequisites

Before starting, ensure you have:
- [ ] GitHub repository with all code committed to `main` branch
- [ ] [Vercel account](https://vercel.com/signup) (free tier works)
- [ ] [Railway account](https://railway.app/) (Developer plan ~$5/month)
- [ ] [Supabase account](https://supabase.com/) (free tier works)
- [ ] OpenAI API key ([get key](https://platform.openai.com/api-keys))
- [ ] Anthropic API key ([get key](https://console.anthropic.com/settings/keys))

---

## Task 1: Create Production Supabase Project

### 1.1 Create New Project

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard)
2. Click **"New Project"**
3. Configure:
   - **Organization:** Select or create
   - **Name:** `transfer2read-production` (or similar)
   - **Database Password:** Generate strong password (save to password manager)
   - **Region:** Choose closest to your users (e.g., `us-east-1`)
4. Click **"Create new project"**
5. Wait 1-2 minutes for provisioning

### 1.2 Configure Storage Buckets

1. Navigate to **Storage** in left sidebar
2. Click **"Create a new bucket"**
3. Create **uploads** bucket:
   - Name: `uploads`
   - Public: **❌ OFF** (Private)
   - Click **"Create bucket"**
4. Create **downloads** bucket:
   - Name: `downloads`
   - Public: **❌ OFF** (Private)
   - Click **"Create bucket"**

### 1.3 Enable Authentication

1. Navigate to **Authentication → Providers**
2. Find **Email** provider
3. Toggle **ON** if not already enabled
4. Configure settings:
   - **Enable email confirmations:** ✅ (recommended)
   - **Secure email change:** ✅ (recommended)
5. Click **"Save"**

### 1.4 Collect Production Credentials

1. Navigate to **Settings → API**
2. Copy and save these values (you'll need them later):

```bash
# Project URL
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co

# anon (public) key - Safe for frontend
SUPABASE_ANON_KEY=eyJhbGc...

# service_role key - NEVER expose publicly!
SUPABASE_SERVICE_KEY=eyJhbGc...
```

3. **⚠️ Security:** Store these in a secure location (password manager, not in Git!)

---

## Task 2: Deploy Frontend to Vercel

### 2.1 Connect GitHub Repository

1. Go to [vercel.com](https://vercel.com/) and sign in
2. Click **"Add New Project"**
3. Click **"Import Git Repository"**
4. Find your `transfer_app` repository
5. Click **"Import"**

### 2.2 Configure Project Settings

1. **Framework Preset:** Next.js (auto-detected)
2. **Root Directory:** `frontend/`
3. **Build Command:** `npm run build` (default)
4. **Output Directory:** `.next` (default)
5. **Install Command:** `npm ci` (default)

### 2.3 Set Environment Variables

Click **"Environment Variables"** and add:

| Name | Value | Environment |
|------|-------|-------------|
| `NEXT_PUBLIC_SUPABASE_URL` | Your production Supabase URL | Production, Preview |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Your production anon key | Production, Preview |
| `NEXT_PUBLIC_API_URL` | `https://your-backend.railway.app` (get from Task 3) | Production |
| `NEXT_PUBLIC_API_URL` | `https://your-backend-preview.railway.app` (optional) | Preview |

**Note:** Leave `NEXT_PUBLIC_API_URL` blank for now if you haven't deployed Railway yet. You'll update it after Task 3.

### 2.4 Deploy

1. Click **"Deploy"**
2. Wait 2-3 minutes for build
3. Vercel will provide a URL: `https://transfer2read.vercel.app` (or similar)
4. Visit the URL to verify deployment

### 2.5 Configure Preview Deployments

1. Navigate to **Settings → Git**
2. Verify **"Preview Deployments"** is enabled for pull requests
3. This allows testing PRs before merging to main

---

## Task 3: Deploy Backend to Railway

### 3.1 Create Railway Project

1. Go to [railway.app](https://railway.app/) and sign in
2. Click **"New Project"**
3. Click **"Deploy from GitHub repo"**
4. Select your `transfer_app` repository
5. Railway will create a project

### 3.2 Add Redis Service

1. In your Railway project, click **"+ New"**
2. Select **"Database"**
3. Choose **"Redis"**
4. Railway provisions a managed Redis instance
5. Note the **internal URL** (like `redis://redis.railway.internal:6379`)

### 3.3 Deploy Stirling-PDF Service

**⚠️ IMPORTANT:** Stirling-PDF must be deployed before the API and Worker services, as they depend on it for PDF conversion.

1. Click **"+ New"** → **"Docker Image"**
2. Image Name: `stirlingtools/stirling-pdf:latest`
3. Click **"Deploy"**
4. Wait for deployment to complete (~2-3 minutes)

5. **Service Configuration:**
   - Navigate to service **Settings** → **Networking**
   - **Public Domain:** Optional (enable only if you need to access the Stirling-PDF web UI for testing)
   - **Private Networking:** ✅ Enabled (Railway provides internal networking by default)
   - **Port:** `8080` (Railway should detect this automatically from the image)

6. **Get Internal Service URL:**
   - In Railway, go to the Stirling-PDF service
   - Navigate to **Settings** → **Service**
   - Look for the internal hostname (typically: `stirling-pdf.railway.internal`)
   - Full internal URL will be: `http://stirling-pdf.railway.internal:8080`
   - **Note this URL** - you'll need it for API and Worker environment variables

7. **Verify Stirling-PDF is Running:**
   - Check service logs for: `Started Stirling-PDF successfully`
   - Optional: If you enabled public domain, visit the URL to see the Stirling-PDF web interface

8. **Resource Configuration (Recommended):**
   - Go to **Settings** → **Resources**
   - Recommended settings for production:
     - **Memory:** 2GB (minimum) - Stirling-PDF requires significant memory for PDF processing
     - **CPU:** 1 vCPU (Railway's default)
   - These settings prevent out-of-memory errors during large PDF conversions

### 3.4 Deploy API Service

1. Click **"+ New"** → **"GitHub Repo"** → Select your repo
2. Configure the API service:
   - **Service Name:** `api` or `backend`
   - **Root Directory:** `backend/`
   - **Builder:** Dockerfile
   - **Start Command:** Leave default (uses Dockerfile CMD)

3. Set environment variables for API service:

| Variable | Value | Notes |
|----------|-------|-------|
| `SUPABASE_URL` | Production Supabase URL from Task 1 | Example: `https://xxxxx.supabase.co` |
| `SUPABASE_SERVICE_KEY` | Production service role key from Task 1 | ⚠️ Keep secret! Admin access key |
| `SUPABASE_JWT_SECRET` | JWT secret from Supabase Settings → API | Used for token validation |
| `OPENAI_API_KEY` | Your OpenAI API key | For GPT-4o structure analysis |
| `ANTHROPIC_API_KEY` | Your Anthropic API key | For Claude fallback |
| `REDIS_URL` | Railway Redis internal URL | Auto-provided by Railway |
| `CELERY_BROKER_URL` | Same as REDIS_URL | Celery message broker |
| `CELERY_RESULT_BACKEND` | Same as REDIS_URL | Celery result storage |
| `STIRLING_PDF_URL` | `http://stirling-pdf.railway.internal:8080` | From Task 3.3 - Update with actual hostname |
| `STIRLING_PDF_API_KEY` | (Leave empty or set custom key) | Optional - only if you configured API key in Stirling-PDF |
| `ENVIRONMENT` | `production` | Application environment mode |

4. Click **"Deploy"**
5. Wait for build to complete (~3-5 minutes)
6. Railway provides a public URL: `https://your-backend.railway.app`

### 3.5 Deploy Worker Service

1. Click **"+ New"** → **"GitHub Repo"** → Select your repo again
2. Configure the Worker service:
   - **Service Name:** `worker`
   - **Root Directory:** `backend/`
   - **Builder:** Dockerfile
   - **⚠️ Override Start Command:** `celery -A app.worker worker --loglevel=info`

3. Set environment variables for Worker (same as API service):
   - Copy all variables from API service
   - Use Railway's "Copy from another service" feature if available

4. Click **"Deploy"**
5. Worker doesn't get a public URL (internal service only)

### 3.6 Verify Deployments

1. **Check API service logs:**
   - Should see: `Uvicorn running on http://0.0.0.0:8000`
   - No errors about missing environment variables

2. **Check Worker service logs:**
   - Should see: `celery@worker ready`
   - Should see task registration messages

3. **Test health endpoint:**
```bash
curl https://your-backend.railway.app/api/health
```
Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2025-12-04T..."
}
```

### 3.7 Update Vercel Environment Variables

1. Go back to Vercel project
2. Navigate to **Settings → Environment Variables**
3. Update `NEXT_PUBLIC_API_URL`:
   - Value: `https://your-backend.railway.app` (from Railway API service)
4. Click **"Save"**
5. Redeploy frontend:
   - Go to **Deployments**
   - Click **"..."** on latest deployment
   - Click **"Redeploy"**

---

## Task 4: Verify CORS Configuration

### 4.1 Check Backend CORS Settings

The backend already includes production CORS configuration in `backend/app/main.py`:

```python
allow_origins=[
    "http://localhost:3000",
    "http://localhost:3001",
    "https://transfer2read.vercel.app",  # ✅ Production
],
```

**If your Vercel URL is different:**
1. Edit `backend/app/main.py`
2. Update line 24 with your actual Vercel URL
3. Commit and push to trigger Railway redeploy

### 4.2 Test CORS

1. Visit your Vercel frontend: `https://transfer2read.vercel.app`
2. Open browser DevTools → Console
3. Check for CORS errors when frontend calls backend
4. Expected: **No CORS errors** ✅

---

## Task 5: End-to-End Production Verification

### 5.1 Backend Health Check

```bash
curl https://your-backend.railway.app/api/health
```

Expected:
- **Status Code:** 200 OK
- **Response:** JSON with `{"status": "healthy", ...}`

### 5.2 Frontend Verification

1. Visit: `https://transfer2read.vercel.app`
2. Verify:
   - [ ] Page loads without errors
   - [ ] Professional Blue theme visible
   - [ ] TopBar component renders
   - [ ] No console errors in DevTools

### 5.3 Frontend-Backend Integration

1. Open DevTools → Network tab
2. Trigger any API call from frontend (if implemented)
3. Verify:
   - [ ] Request goes to Railway URL
   - [ ] Status 200 OK
   - [ ] No CORS errors

### 5.4 Worker Verification

1. Go to Railway → Worker service → Logs
2. Verify:
   - [ ] `celery@worker ready` message
   - [ ] Connected to Redis
   - [ ] No error messages

---

## Task 6: Verify CI/CD Pipeline

### 6.1 GitHub Actions Workflow

The CI/CD pipeline is configured in `.github/workflows/ci.yml` to run on:
- Every pull request to `main`
- Every push to `main`

### 6.2 Test the Pipeline

1. Create a test branch:
```bash
git checkout -b test-ci-pipeline
```

2. Make a small change (e.g., add comment to README.md):
```bash
echo "# Test CI/CD" >> README.md
git add README.md
git commit -m "test: verify CI/CD pipeline"
git push origin test-ci-pipeline
```

3. Create a Pull Request on GitHub

4. Verify GitHub Actions runs:
   - Go to PR → **Checks** tab
   - Should see: `backend-tests` and `frontend-tests` jobs
   - Wait for jobs to complete
   - Expected: **✅ All checks passed**

5. Merge the PR (or close without merging if just testing)

### 6.3 Automatic Deployment

- **Vercel:** Auto-deploys on every push to `main`
- **Railway:** Auto-deploys on every push to `main`
- No manual deployment steps needed after initial setup

---

## Task 7: Update Project Documentation

### 7.1 Production URLs

Document your production URLs for team reference:

```bash
# Frontend
https://transfer2read.vercel.app

# Backend API
https://your-backend.railway.app

# API Health Check
https://your-backend.railway.app/api/health

# API Documentation
https://your-backend.railway.app/docs
```

### 7.2 Environment Recap

**Vercel Environment Variables:**
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_API_URL`

**Railway Environment Variables (API + Worker):**
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `REDIS_URL` (auto-provided by Railway)
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `STIRLING_PDF_URL`
- `ENVIRONMENT`

---

## Troubleshooting

### Frontend Issues

**Problem:** Frontend shows 500 error  
**Solution:** Check Vercel logs → Function Logs → Look for errors

**Problem:** "Failed to fetch" errors in console  
**Solution:** 
1. Verify `NEXT_PUBLIC_API_URL` is set correctly in Vercel
2. Check CORS configuration in `backend/app/main.py`
3. Verify backend is running (test health endpoint)

### Backend Issues

**Problem:** Railway build fails  
**Solution:**
1. Check Railway build logs for errors
2. Verify `backend/Dockerfile` syntax
3. Ensure all dependencies in `requirements.txt`

**Problem:** "Connection refused" to Supabase  
**Solution:**
1. Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are correct
2. Check Supabase project is active (not paused)
3. Verify Railway has network access to Supabase (should be allowed)

**Problem:** Worker not processing tasks
**Solution:**
1. Check Railway Worker logs for startup errors
2. Verify `REDIS_URL` is correct
3. Ensure Worker has same environment variables as API
4. Check Redis service is running

**Problem:** Stirling-PDF conversion fails or times out
**Solution:**
1. Check Stirling-PDF service logs in Railway for errors
2. Verify `STIRLING_PDF_URL` environment variable is correct in API and Worker
3. Test Stirling-PDF health:
   ```bash
   curl http://stirling-pdf.railway.internal:8080/api/v1/info
   ```
4. Check Stirling-PDF resource allocation (needs minimum 2GB RAM)
5. Verify private networking is enabled between services
6. For large PDFs, may need to increase `CELERY_TASK_TIME_LIMIT` (default: 360s)

**Problem:** "Connection refused" to Stirling-PDF
**Solution:**
1. Verify Stirling-PDF service is running in Railway
2. Check internal hostname is correct (Settings → Service → Service Name)
3. Ensure all services are in the same Railway project (required for private networking)
4. Wait 1-2 minutes after deploy for internal DNS to propagate

### CI/CD Issues

**Problem:** GitHub Actions tests fail  
**Solution:**
1. Click on failed job to see error details
2. Run tests locally first: `cd backend && pytest`
3. Ensure all dependencies are in `requirements.txt`

**Problem:** Deployments not triggering  
**Solution:**
1. Verify Vercel/Railway GitHub integration is active
2. Check deployment settings in platform dashboards
3. Ensure commits are pushed to `main` branch

---

## Rollback Procedures

### Vercel Rollback

1. Go to Vercel → Deployments
2. Find the last working deployment
3. Click **"..."** → **"Promote to Production"**
4. Frontend reverts instantly

### Railway Rollback

1. Go to Railway → Service → Deployments
2. Find the last working deployment
3. Click **"..."** → **"Redeploy"**
4. Backend reverts in ~2-3 minutes

### Database Rollback

⚠️ **Supabase data changes are not easily reversible**
- Always test data migrations in development first
- Consider taking database snapshots before major changes
- Use Supabase SQL editor to manually revert schema changes if needed

---

## Security Best Practices

1. **Rotate API Keys Quarterly:**
   - OpenAI, Anthropic keys should be rotated every 3 months
   - Update in Railway environment variables

2. **Never Commit Secrets:**
   - All `.env` files are in `.gitignore`
   - Use platform secret managers (Vercel, Railway)

3. **Separate Dev/Prod Credentials:**
   - Always use different Supabase projects
   - Never use production keys in development

4. **Enable 2FA:**
   - Enable on GitHub, Vercel, Railway, Supabase accounts

5. **Monitor Logs:**
   - Regularly check Railway logs for errors
   - Set up error alerting in production

---

## Cost Estimates (Production)

| Service | Plan | Cost |
|---------|------|------|
| Vercel | Hobby (Free) | $0/month |
| Railway | Developer | ~$5/month |
| Supabase | Free Tier | $0/month* |
| OpenAI API | Pay-per-use | ~$10-50/month** |
| Anthropic API | Pay-per-use | ~$5-20/month** |

**Total: ~$20-75/month**

*Supabase Free Tier limits: 500MB database, 1GB storage, 2GB bandwidth  
**AI API costs depend on usage volume

---

## Next Steps After Deployment

1. **Monitor Performance:**
   - Set up Vercel Analytics
   - Check Railway metrics dashboard

2. **Configure Custom Domain:**
   - Add custom domain in Vercel (e.g., `transfer2read.com`)
   - Update CORS in backend with new domain

3. **Set Up Error Tracking:**
   - Consider Sentry or similar service
   - Add error reporting to backend

4. **Implement Rate Limiting:**
   - Protect AI API endpoints from abuse
   - Use Railway's rate limiting features

5. **Database Backups:**
   - Configure Supabase automated backups
   - Test restore procedures

---

**✅ Deployment Complete!**

Your Transfer2Read application is now live in production. Test all features thoroughly before announcing to users.

**Support:** Check `docs/architecture.md` for technical details or create an issue on GitHub.
