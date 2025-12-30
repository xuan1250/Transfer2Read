# Rollback Procedures

**Document Owner:** Xavier (Product Manager)
**Created:** 2025-12-30
**Last Updated:** 2025-12-30
**Purpose:** Emergency rollback and disaster recovery procedures for Transfer2Read production

---

## Overview

This document covers procedures for rolling back deployments and recovering from incidents in production.

**When to Use This Guide:**

- Production deployment introduces critical bugs
- Database migration fails or corrupts data
- API keys compromised or revoked
- Service outage affecting user experience
- Security vulnerability discovered in deployed code

**Rollback SLA:**

- **Critical (Service Down):** Rollback within 15 minutes
- **Major (Functionality Broken):** Rollback within 1 hour
- **Minor (Non-critical issues):** Fix forward or schedule rollback during maintenance window

---

## Table of Contents

1. [Vercel Frontend Rollback](#vercel-frontend-rollback)
2. [Railway Backend Rollback](#railway-backend-rollback)
3. [Railway Worker Rollback](#railway-worker-rollback)
4. [Supabase Database Rollback](#supabase-database-rollback)
5. [Environment Variable Rollback](#environment-variable-rollback)
6. [API Key Compromise Response](#api-key-compromise-response)
7. [Incident Response Checklist](#incident-response-checklist)
8. [Post-Incident Review](#post-incident-review)

---

## Vercel Frontend Rollback

### Severity: Critical (User-facing)
### Estimated Time: 5 minutes

### Symptoms Requiring Rollback

- Frontend not loading (white screen, 500 errors)
- JavaScript errors breaking core functionality (cannot register, upload, or download)
- Visual regressions breaking user experience (layout broken, buttons unclickable)
- Security vulnerability introduced in frontend code

### Rollback Procedure

#### Option 1: Via Vercel Dashboard (Recommended)

1. **Log in to Vercel Dashboard:**
   - Navigate to https://vercel.com/dashboard
   - Select "Transfer2Read" project

2. **View Deployments:**
   - Click "Deployments" tab
   - Identify current production deployment (marked with "Production" badge)
   - Identify last known good deployment (previous deployment before current)

3. **Promote Previous Deployment:**
   - Click "..." menu on last known good deployment
   - Select "Promote to Production"
   - Confirm promotion

4. **Verify Rollback:**
   ```bash
   # Clear browser cache and test frontend
   curl -I https://transfer2read.com
   # Expected: 200 OK, deployment ID in x-vercel-id header matches promoted deployment
   ```

5. **Notify Team:**
   - Post in team Slack/Discord: "Vercel frontend rolled back to [DEPLOYMENT_ID] due to [REASON]"

**Time to Complete:** 2-3 minutes

---

#### Option 2: Via Vercel CLI

**Prerequisites:**
- Vercel CLI installed: `npm install -g vercel`
- Authenticated: `vercel login`

1. **List Recent Deployments:**
   ```bash
   vercel list
   # Identify last known good deployment URL
   ```

2. **Promote Deployment:**
   ```bash
   vercel promote [DEPLOYMENT_URL]
   # Example: vercel promote https://transfer2read-abc123.vercel.app
   ```

3. **Verify:**
   ```bash
   vercel inspect [DEPLOYMENT_URL]
   # Check "Production" status shows true
   ```

**Time to Complete:** 3-5 minutes

---

### Rollback Verification

After rollback, verify:

- [ ] Frontend loads at https://transfer2read.com (200 OK)
- [ ] User registration works (create test account)
- [ ] File upload works (upload small PDF)
- [ ] API calls succeed (check browser Network tab for 200 OK responses)
- [ ] No console errors in browser DevTools

---

### When NOT to Rollback

- Minor visual bugs (non-blocking, can fix forward)
- Non-critical features broken (e.g., analytics, optional settings)
- Performance slightly slower (not breaking functionality)

**Alternative:** Deploy hotfix to main branch (Vercel auto-deploys on push to main)

---

## Railway Backend Rollback

### Severity: Critical (Core functionality)
### Estimated Time: 5-10 minutes

### Symptoms Requiring Rollback

- `/api/health` endpoint returns 503 Service Unavailable
- API errors on all requests (500 Internal Server Error)
- Database connection failures
- Redis connection failures
- Conversion pipeline broken (tasks not processing)

### Rollback Procedure

#### Option 1: Via Railway Dashboard (Recommended)

1. **Log in to Railway Dashboard:**
   - Navigate to https://railway.app/dashboard
   - Select "Transfer2Read" project
   - Select "backend-api" service

2. **View Deployments:**
   - Click "Deployments" tab
   - Identify current deployment (green "Active" badge)
   - Identify last known good deployment (previous deployment before current)

3. **Redeploy Previous Deployment:**
   - Click "..." menu on last known good deployment
   - Select "Redeploy"
   - Confirm redeployment

4. **Monitor Deployment:**
   - Wait for "Deployed" status (2-5 minutes)
   - Check logs for startup messages:
     ```
     INFO:     Uvicorn running on http://0.0.0.0:8000
     INFO:     Application startup complete.
     ```

5. **Verify Rollback:**
   ```bash
   curl https://api.transfer2read.com/api/health
   # Expected: {"status":"healthy","database":"connected","redis":"connected",...}
   ```

**Time to Complete:** 5-7 minutes

---

#### Option 2: Via Railway CLI

**Prerequisites:**
- Railway CLI installed: `npm install -g @railway/cli`
- Authenticated: `railway login`

1. **Link to Project:**
   ```bash
   cd /Users/dominhxuan/Desktop/Transfer2Read/backend
   railway link
   # Select "Transfer2Read" project → "backend-api" service
   ```

2. **View Deployments:**
   ```bash
   railway status
   # Identify last known good deployment ID
   ```

3. **Rollback:**
   ```bash
   railway rollback [DEPLOYMENT_ID]
   # Railway redeploys specified deployment
   ```

4. **Monitor Logs:**
   ```bash
   railway logs
   # Watch for startup messages
   ```

**Time to Complete:** 7-10 minutes

---

### Rollback Verification

After rollback, verify:

- [ ] `/api/health` returns `{"status":"healthy"}` (200 OK)
- [ ] Supabase connection working (database: "connected")
- [ ] Redis connection working (redis: "connected")
- [ ] Test API endpoint: `curl -X POST https://api.transfer2read.com/api/conversions` (requires auth token)
- [ ] Check Railway logs for errors (should be clean)

---

## Railway Worker Rollback

### Severity: Major (Background tasks)
### Estimated Time: 5-10 minutes

### Symptoms Requiring Rollback

- PDF conversions not starting (uploads succeed but conversions stuck in "UPLOADED" status)
- Worker logs show errors or exceptions
- Celery task queue backing up (Redis task count increasing)

### Rollback Procedure

**Follow same steps as Backend Rollback (Option 1 or 2), but select "celery-worker" service instead of "backend-api".**

1. Railway Dashboard → Transfer2Read → celery-worker service → Deployments
2. Redeploy last known good deployment
3. Monitor logs for Celery startup:
   ```
   [INFO/MainProcess] Connected to redis://...
   [INFO/MainProcess] celery@celery-worker ready.
   ```

### Rollback Verification

- [ ] Worker logs show "celery@celery-worker ready"
- [ ] Test conversion: Upload PDF → verify conversion starts within 10 seconds
- [ ] Check Railway worker logs for task execution messages
- [ ] Redis queue count decreasing (tasks being processed)

---

## Supabase Database Rollback

### Severity: CRITICAL (Data integrity)
### Estimated Time: 10-30 minutes

### Symptoms Requiring Rollback

- Database migration fails and corrupts data
- RLS policies broken (users can see other users' data)
- Tables missing or schema incorrect
- Critical data deleted accidentally

**WARNING:** Database rollbacks restore ALL data to backup point, losing any data created after backup. Coordinate with team before proceeding.

### Rollback Procedure

#### Option 1: Restore from Daily Backup

1. **Log in to Supabase Dashboard:**
   - Navigate to https://supabase.com/dashboard
   - Select "Transfer2Read Production" project

2. **View Backups:**
   - Navigate to Database → Backups
   - Supabase creates automatic daily backups (7-day retention on free tier, 30-day on Pro)

3. **Select Backup:**
   - Identify last known good backup (before incident)
   - Click "Restore" button

4. **Confirm Restore:**
   - **WARNING:** This will DELETE all current data and restore backup
   - Type project name to confirm
   - Click "Restore Database"

5. **Wait for Restore:**
   - Restoration takes 5-15 minutes depending on database size
   - Monitor progress in Supabase Dashboard

6. **Verify Restore:**
   ```bash
   # Check table exists
   curl -H "apikey: $SUPABASE_SERVICE_KEY" \
        https://xxxxx.supabase.co/rest/v1/conversion_jobs?limit=1
   # Expected: 200 OK with data

   # Verify data integrity
   # - Check row counts match expected values
   # - Verify RLS policies work (test with non-admin user)
   ```

**Time to Complete:** 10-20 minutes

---

#### Option 2: Manual Backup/Restore (If Auto-Backup Unavailable)

**Prerequisites:**
- `pg_dump` and `psql` installed locally
- Supabase database connection string from Dashboard → Settings → Database

1. **Dump Current Database (Before Restore):**
   ```bash
   # Get connection string from Supabase Dashboard → Settings → Database → Connection string
   pg_dump "postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres" \
     > backup-before-restore-$(date +%Y%m%d-%H%M%S).sql
   ```

2. **Restore from Previous Backup:**
   ```bash
   # If you have a previous backup file
   psql "postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres" \
     < backup-known-good.sql
   ```

**Time to Complete:** 20-30 minutes

---

### Rollback Verification

After database rollback, verify:

- [ ] All tables present: `conversion_jobs`, `user_usage`
- [ ] Row counts match expected values (check Supabase Table Editor)
- [ ] RLS policies work (test with test user account)
- [ ] API health check returns `{"database":"connected"}`
- [ ] Test user registration, login, and file upload
- [ ] **Data Loss Assessment:** Document what data was lost (created between backup and rollback)

---

### When NOT to Rollback Database

- Minor schema changes (can apply fix migration instead)
- Single row corrupted (can fix with UPDATE query)
- RLS policy bug (can fix policy without full restore)

**Alternative:** Apply fix migration or manual SQL query to repair issue

---

## Environment Variable Rollback

### Severity: Major to Critical (depending on variable)
### Estimated Time: 5 minutes

### Symptoms Requiring Rollback

- API keys invalid or revoked (401 Unauthorized errors)
- CORS errors after changing `ALLOWED_ORIGINS`
- Redis connection failed after changing `REDIS_URL`
- Supabase connection failed after changing `SUPABASE_URL`

### Rollback Procedure

#### Vercel (Frontend)

1. **Backup Current Variables:**
   ```bash
   # Via Vercel CLI
   vercel env pull .env.vercel.backup
   # Saves current production env vars to file
   ```

2. **Restore Previous Variables:**
   - Vercel Dashboard → Transfer2Read → Settings → Environment Variables
   - Edit variable with incorrect value
   - Paste correct value from password manager or backup file
   - Save

3. **Trigger Redeployment:**
   ```bash
   # Vercel doesn't auto-redeploy on env var changes
   git commit --allow-empty -m "chore: trigger redeploy after env var fix"
   git push origin main
   ```

**Time to Complete:** 5 minutes

---

#### Railway (Backend + Worker)

1. **Backup Current Variables:**
   ```bash
   # Via Railway CLI
   railway vars --json > railway-vars-backup-$(date +%Y%m%d-%H%M%S).json
   ```

2. **Restore Previous Variables:**
   - Railway Dashboard → Transfer2Read → backend-api service → Variables
   - Edit variable with incorrect value
   - Paste correct value from password manager or backup file
   - Railway auto-redeploys on env var save

3. **Verify Deployment:**
   ```bash
   # Monitor Railway logs for errors
   railway logs --tail 100
   ```

4. **Repeat for Worker Service:**
   - Railway Dashboard → celery-worker service → Variables
   - Restore same variable

**Time to Complete:** 5-7 minutes

---

### Rollback Verification

- [ ] Health endpoint returns 200 OK (API keys, database, Redis valid)
- [ ] No CORS errors in browser console (ALLOWED_ORIGINS correct)
- [ ] Frontend can call backend API (test user registration)
- [ ] Worker can process tasks (test PDF conversion)

---

## API Key Compromise Response

### Severity: CRITICAL (Security incident)
### Estimated Time: 15-30 minutes

### Symptoms of Compromise

- Unexpected API usage spikes (OpenAI/Anthropic billing alerts)
- API key found in public GitHub repo, logs, or error messages
- Unauthorized access to production systems

### Response Procedure

**IMMEDIATE ACTIONS (within 5 minutes):**

1. **Revoke Compromised Keys:**

   **OpenAI:**
   ```bash
   # Log in to OpenAI Dashboard: https://platform.openai.com/api-keys
   # Click "..." menu on compromised key → "Revoke"
   # Confirm revocation (service will FAIL until new key added)
   ```

   **Anthropic:**
   ```bash
   # Log in to Anthropic Console: https://console.anthropic.com/settings/keys
   # Click "Delete" on compromised key
   # Confirm deletion
   ```

2. **Generate New Keys:**
   - Follow `docs/operations/api-key-rotation-guide.md` Steps 1-2
   - Create new production keys with different names (e.g., "Transfer2Read Production v2")

3. **Update Production Environment Variables:**
   ```bash
   # Railway Dashboard → backend-api service → Variables
   # Update OPENAI_API_KEY and/or ANTHROPIC_API_KEY
   # Railway auto-redeploys (2-5 minutes downtime)

   # Railway Dashboard → celery-worker service → Variables
   # Update same keys (keep API and worker in sync)
   ```

4. **Verify New Keys Work:**
   ```bash
   # Test OpenAI key
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer sk-proj-NEW_KEY"

   # Test Anthropic key
   curl https://api.anthropic.com/v1/messages \
     -H "x-api-key: sk-ant-NEW_KEY" \
     -H "anthropic-version: 2023-06-01" \
     -H "content-type: application/json" \
     -d '{"model":"claude-3-haiku-20240307","max_tokens":50,"messages":[{"role":"user","content":"test"}]}'
   ```

**FOLLOW-UP ACTIONS (within 1 hour):**

5. **Audit API Usage:**
   - OpenAI Dashboard → Usage → Check for unauthorized usage spikes
   - Anthropic Console → Usage → Review recent API calls
   - Document anomalies (dates, request counts, costs)

6. **Check Billing:**
   - OpenAI Dashboard → Billing → Review recent charges
   - If unauthorized usage detected, contact OpenAI support for refund request
   - Same for Anthropic

7. **Investigate Leak Source:**
   - Search GitHub for leaked keys: `https://github.com/search?q=sk-proj-OLD_KEY`
   - Check Railway/Vercel logs for key exposure in error messages
   - Review recent commits for accidental commits to git

8. **Document Incident:**
   - Create file: `docs/operations/incident-log.md` (if not exists)
   - Log incident:
     ```markdown
     ## Incident: API Key Compromise - [DATE]
     **Severity:** Critical
     **Duration:** [TIME] to [TIME]
     **Affected Services:** OpenAI API, Anthropic API
     **Root Cause:** [e.g., Key accidentally committed to public GitHub repo]
     **Impact:** $XXX unauthorized API usage
     **Resolution:** Keys revoked and rotated, new keys deployed to production
     **Lessons Learned:** [e.g., Add pre-commit hook to scan for secrets]
     ```

9. **Prevent Future Leaks:**
   - Install `git-secrets` or `truffleHog` to scan commits for secrets
   - Add pre-commit hook:
     ```bash
     # .git/hooks/pre-commit
     #!/bin/bash
     if git diff --cached | grep -E 'sk-proj-|sk-ant-'; then
       echo "ERROR: Potential API key found in commit!"
       exit 1
     fi
     ```
   - Review `.gitignore` to ensure `.env*` files excluded (except `.env.example`)

---

## Incident Response Checklist

**Use this checklist during active incidents to ensure all steps are followed.**

### Step 1: Assess Severity

- [ ] Determine severity level:
  - **Critical:** Service down, data loss, security breach
  - **Major:** Core functionality broken, affecting all users
  - **Minor:** Non-critical feature broken, affecting subset of users

### Step 2: Communicate

- [ ] Post in team chat: "Incident detected - [BRIEF_DESCRIPTION] - Severity: [CRITICAL/MAJOR/MINOR]"
- [ ] Update status page (if using Statuspage.io): "Investigating service issues"
- [ ] Assign incident lead (person coordinating response)

### Step 3: Triage

- [ ] Identify affected services (Frontend, Backend, Worker, Database)
- [ ] Collect evidence:
  - [ ] Error messages from Vercel/Railway/Supabase logs
  - [ ] Affected deployment IDs
  - [ ] Time incident started (first user report or monitoring alert)
- [ ] Determine rollback candidate (last known good deployment)

### Step 4: Rollback

- [ ] Execute rollback procedure (Frontend, Backend, Worker, or Database)
- [ ] Monitor rollback progress
- [ ] Verify rollback success (health checks, user testing)

### Step 5: Verify Recovery

- [ ] Test critical user flows:
  - [ ] User registration
  - [ ] PDF upload
  - [ ] Conversion processing
  - [ ] EPUB download
- [ ] Check error rates (Railway/Vercel logs)
- [ ] Update status page: "Service restored"

### Step 6: Post-Incident

- [ ] Post in team chat: "Incident resolved - [SUMMARY]"
- [ ] Schedule post-incident review meeting (within 24 hours)
- [ ] Document incident in `docs/operations/incident-log.md`

---

## Post-Incident Review

**Schedule within 24 hours of incident resolution.**

### Review Template

```markdown
## Post-Incident Review: [INCIDENT_NAME] - [DATE]

**Incident Summary:**
- Severity: [Critical/Major/Minor]
- Duration: [START_TIME] to [END_TIME]
- Affected Users: [Number or percentage]
- Services Affected: [Frontend, Backend, Worker, Database]

**Timeline:**
- [TIME] - Incident started (first detection)
- [TIME] - Incident acknowledged by team
- [TIME] - Rollback initiated
- [TIME] - Service restored
- [TIME] - Incident closed

**Root Cause:**
- [Description of what caused the incident]
- [Why did monitoring not catch this earlier?]

**Impact:**
- [Number of affected users]
- [Revenue impact, if applicable]
- [Data loss, if any]

**What Went Well:**
- [e.g., Rollback completed in 10 minutes (target: 15 minutes)]
- [e.g., Team communication was clear and timely]

**What Could Be Improved:**
- [e.g., Need better monitoring for database connection failures]
- [e.g., Rollback procedure unclear for new team members]

**Action Items:**
- [ ] [ACTION_ITEM_1] - Assigned to: [NAME] - Due: [DATE]
- [ ] [ACTION_ITEM_2] - Assigned to: [NAME] - Due: [DATE]

**Lessons Learned:**
- [Key takeaway 1]
- [Key takeaway 2]
```

### Example Action Items

- Add pre-commit hook to prevent API key leaks
- Improve monitoring alerting (add Sentry alerts for database errors)
- Document rollback procedures with screenshots
- Run quarterly disaster recovery drills
- Add canary deployments (deploy to 5% of users first, then 100%)

---

## Disaster Recovery Scenarios

### Scenario 1: Complete Vercel Outage

**Situation:** Vercel platform down, frontend inaccessible

**Response:**
1. Check Vercel status page: https://www.vercel-status.com/
2. If prolonged outage (>1 hour), deploy frontend to backup platform:
   - Option A: Netlify (similar to Vercel)
   - Option B: Railway (can host Next.js static export)
3. Update DNS to point to backup deployment

**Prevention:**
- Maintain multi-cloud deployment plan (document Netlify deployment steps)

---

### Scenario 2: Complete Railway Outage

**Situation:** Railway platform down, backend + worker inaccessible

**Response:**
1. Check Railway status page: https://railway.app/status
2. If prolonged outage (>1 hour), deploy backend to backup platform:
   - Option A: Render.com (similar to Railway)
   - Option B: Fly.io (Docker-based deployment)
3. Update Vercel env vars to point to backup backend URL

**Prevention:**
- Maintain Docker images tagged with deployment IDs
- Document Render.com / Fly.io deployment steps

---

### Scenario 3: Supabase Data Loss

**Situation:** Supabase database corrupted beyond recovery

**Response:**
1. Restore from most recent daily backup (see Database Rollback procedure)
2. If backups insufficient, contact Supabase support for Point-in-Time Recovery (PITR) - available on Pro tier
3. If PITR unavailable, assess data loss:
   - User accounts lost: Ask users to re-register
   - Conversion history lost: Notify users via email
   - Files lost: Request users re-upload PDFs

**Prevention:**
- Upgrade to Supabase Pro tier for longer backup retention (30 days + PITR)
- Implement external backup strategy:
  ```bash
  # Daily cron job to dump database
  0 2 * * * pg_dump $DATABASE_URL | gzip > /backups/supabase-$(date +\%Y\%m\%d).sql.gz
  ```

---

## Emergency Contacts

**Primary Contact:** Xavier (Product Manager)
- Email: [your-email@example.com]
- Phone: [+1-XXX-XXX-XXXX]

**Backup Contact:** [DevOps Lead]
- Email: [devops@example.com]
- Phone: [+1-XXX-XXX-XXXX]

**Platform Support:**
- Vercel: https://vercel.com/support (Priority Support if on Pro plan)
- Railway: https://railway.app/help (Discord: https://discord.gg/railway)
- Supabase: https://supabase.com/support (Discord: https://discord.supabase.com)
- OpenAI: https://help.openai.com/en/ (support@openai.com)
- Anthropic: support@anthropic.com

**Escalation Path:**
1. Attempt rollback using this guide (15 minutes)
2. Contact primary contact (Xavier)
3. Contact backup contact (DevOps Lead)
4. Contact platform support (Vercel/Railway/Supabase)

---

## Related Documentation

- **[Production Deployment Guide](production-deployment-guide.md)** - Initial deployment steps
- **[API Key Rotation Guide](api-key-rotation-guide.md)** - Rotate compromised keys
- **[Production Secrets Template](production-secrets-template.md)** - Backup of environment variables
- **[Quick Wins Plan](../sprint-artifacts/quick-wins-plan-2025-12-26.md)** - Pre-launch checklist

---

**Document Status:** ✅ Complete
**Last Reviewed:** 2025-12-30
**Next Review:** After first production incident (update with lessons learned)
**Practice Drill:** Schedule quarterly disaster recovery drill to test rollback procedures
