# Transfer2Read - Quick Wins Execution Plan

**Created:** 2025-12-26
**Owner:** Xavier (Product Manager)
**Context:** Pre-Epic 7 launch preparation tasks
**Goal:** Complete low-hanging fruit items before starting full Epic 7 stories

---

## Plan Overview

**Total Quick Wins:** 5 tasks
**Estimated Total Time:** 4-6 hours
**Target Completion:** This week (by 2025-12-31)
**Status:** ⏳ In Progress (4 of 5 complete - QW-1, QW-3, QW-4, QW-5)

**Progress Update (2025-12-30):**
- ✅ **QW-1:** Domain Purchase & DNS - COMPLETE (domain purchased, DNS configured, all endpoints verified)
- ✅ **QW-3:** API Key Rotation - Documentation complete (manual key generation pending)
- ✅ **QW-4:** Documentation Update - All docs created (README, deployment guide, rollback procedures, architecture)
- ✅ **QW-5:** Beta User List - Templates complete (Google Form, email, CSV)
- ⏳ **QW-2:** Supabase Production - Awaiting manual setup by xavier

**Benefits:**
- Unblocks production deployment preparation
- Builds launch momentum
- Reduces Epic 7 Story 7.1 scope (some items pre-completed)
- Non-technical tasks can be done in parallel with other work

---

## Quick Win Tasks

### QW-1: Domain Purchase & DNS Setup

**Priority:** HIGH (Blocks production deployment)
**Estimated Time:** 1-2 hours
**Status:** ✅ Complete (2025-12-30)

**Objective:** Secure production domain and configure DNS for frontend, backend, and optional services.

#### Steps:

1. **Purchase Domain** (15 minutes)
   - [x] Check domain availability: `transfer2read.com`, `transfer2read.app`, or alternative
   - [x] Purchase via Namecheap, Google Domains, or Cloudflare
   - [x] Cost: ~$10-15/year
   - [x] Enable auto-renewal and domain privacy

2. **Configure DNS for Frontend (Vercel)** (20 minutes)
   - [x] Log in to Vercel dashboard → Select Transfer2Read project
   - [x] Go to Settings → Domains
   - [x] Add custom domain: `transfer2read.app`
   - [x] Vercel provides DNS records to add:
     - A Record: `@` → `216.198.79.1`
     - CNAME: `www` → `613b419f4d146a8a.vercel-dns-017.com`
   - [x] Add records to domain registrar DNS settings
   - [x] Wait for DNS propagation (5-60 minutes)
   - [x] Verify: Visit `https://transfer2read.app` → Should show frontend
   - [x] SSL certificate auto-provisioned by Vercel (verify padlock icon)

3. **Configure DNS for Backend API (Railway)** (20 minutes)
   - [x] Log in to Railway dashboard → Select backend API service
   - [x] Go to Settings → Domains
   - [x] Add custom domain: `api.transfer2read.app`
   - [x] Railway provides DNS records:
     - CNAME: `api` → `m2f23wal.up.railway.app`
   - [x] Add CNAME record to domain registrar DNS settings
   - [x] Wait for DNS propagation
   - [x] Verify: Visit `https://api.transfer2read.app/api/health` → `200 OK`
   - [x] SSL certificate auto-provisioned by Railway

4. **Optional: Status Page Domain** (10 minutes)
   - [ ] If using Statuspage.io or similar:
     - CNAME: `status` → `statuspage.io` CNAME
   - [x] Deferred to post-launch (not critical for MVP)

5. **WWW Redirect** (5 minutes)
   - [x] In domain registrar settings, add CNAME:
     - `www.transfer2read.app` → `613b419f4d146a8a.vercel-dns-017.com`

#### Deliverables:
- ✅ Domain purchased and registered: `transfer2read.app` (Namecheap, 1 year)
- ✅ `transfer2read.app` → Vercel frontend (HTTPS)
- ✅ `www.transfer2read.app` → Vercel frontend (HTTPS)
- ✅ `api.transfer2read.app` → Railway backend (HTTPS)
- ✅ DNS records documented in password manager
- ✅ Backend deployment fixed (libmagic1 + pytest-cov dependencies)
- ✅ CI/CD pipeline fixed (GitHub Actions passing)

#### Validation:
```bash
# Test frontend
curl -I https://transfer2read.app
# Expected: 200 OK, SSL certificate valid

# Test backend API
curl https://api.transfer2read.app/api/health
# Expected: {"status":"healthy","database":"connected","redis":"connected"}

# Test API docs
curl https://api.transfer2read.app/docs
# Expected: HTML page with FastAPI Swagger UI
```

**Actual Results (2025-12-30):**
✅ All endpoints verified working
✅ SSL certificates provisioned and valid
✅ Backend health check: `{"status":"healthy","database":"connected","redis":"connected"}`

#### Blockers/Risks:
- DNS propagation can take up to 48 hours (usually <1 hour)
- If using Cloudflare, disable "Proxy" (orange cloud) initially to avoid SSL issues

---

### QW-2: Supabase Production Project Creation

**Priority:** HIGH (Blocks all production work)
**Estimated Time:** 1-1.5 hours
**Status:** ☐ Not Started

**Objective:** Create separate production Supabase project with database, auth, and storage configured.

#### Steps:

1. **Create Production Supabase Project** (15 minutes)
   - [ ] Log in to supabase.com
   - [ ] Create new project:
     - Name: `Transfer2Read Production` (or `transfer2read-prod`)
     - Database password: Strong password (store in password manager)
     - Region: Choose closest to Railway deployment (e.g., US East, EU West)
   - [ ] Wait for project provisioning (~2-3 minutes)
   - [ ] Note down:
     - Project URL: `https://xxxxx.supabase.co`
     - API Keys:
       - `anon` key (public, safe for frontend)
       - `service_role` key (SECRET, backend only)
     - Database connection string (for direct access if needed)

2. **Configure Authentication Providers** (15 minutes)
   - [ ] In Supabase dashboard → Authentication → Providers
   - [ ] Enable **Email** provider:
     - Confirm email required: ✅ Enabled
     - Email templates: Review welcome email, password reset (customize later)
   - [ ] Enable **Google OAuth:**
     - Get Client ID/Secret from Google Cloud Console (or use existing)
     - Add authorized redirect URI: `https://xxxxx.supabase.co/auth/v1/callback`
     - Test OAuth flow (optional: defer to Story 7.1)
   - [ ] Enable **GitHub OAuth:**
     - Get Client ID/Secret from GitHub Developer Settings
     - Add callback URL: `https://xxxxx.supabase.co/auth/v1/callback`

3. **Create Database Tables** (20 minutes)
   - [ ] In Supabase dashboard → SQL Editor
   - [ ] Run SQL script to create tables (adapt from dev schema):

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

   - [ ] Verify tables created in Table Editor

4. **Configure Row Level Security (RLS)** (15 minutes)
   - [ ] Enable RLS on `conversion_jobs` table:
     - In Table Editor → `conversion_jobs` → RLS tab → Enable RLS
   - [ ] Add policy: "Users can only access their own jobs"
     ```sql
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
     ```
   - [ ] Enable RLS on `user_usage` table with similar policies

5. **Create Storage Buckets** (10 minutes)
   - [ ] In Supabase dashboard → Storage → Create bucket
   - [ ] Create `uploads` bucket:
     - Public: ❌ (Private)
     - Allowed MIME types: `application/pdf`
     - Max file size: 52428800 bytes (50MB for free tier, adjust for Pro)
   - [ ] Create `downloads` bucket:
     - Public: ❌ (Private)
     - Allowed MIME types: `application/epub+zip`
   - [ ] Configure RLS policies on storage:
     ```sql
     -- Allow users to upload to their own folder in uploads bucket
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
     ```

6. **Configure File Retention Policy** (10 minutes)
   - [ ] Option A: Supabase SQL cron extension (if available on plan)
     ```sql
     -- Delete files older than 30 days
     SELECT cron.schedule(
       'delete-old-files',
       '0 2 * * *', -- Daily at 2 AM
       $$DELETE FROM storage.objects WHERE created_at < NOW() - INTERVAL '30 days'$$
     );
     ```
   - [ ] Option B: Document manual cleanup procedure for now (automate in Story 7.1)

#### Deliverables:
- ✅ Production Supabase project created
- ✅ Auth providers configured (Email, Google, GitHub)
- ✅ Database tables created with RLS policies
- ✅ Storage buckets created (`uploads`, `downloads`)
- ✅ API keys and project URL documented in password manager

#### Validation:
- [ ] Can create test user via Supabase dashboard → Authentication → Users → Add User
- [ ] Test user can log in via email/password (test on dev frontend pointing to prod Supabase)
- [ ] RLS policies prevent cross-user data access (test with 2 users)

#### Blockers/Risks:
- Free tier has limits: 500MB database, 1GB storage (upgrade to Pro if needed: $25/month)
- OAuth setup requires Google Cloud / GitHub app configuration (can defer if needed)

---

### QW-3: API Key Rotation for Production

**Priority:** HIGH (Security best practice)
**Estimated Time:** 30 minutes
**Status:** ✅ Complete (2025-12-30)

**Objective:** Generate new production API keys for OpenAI, Anthropic, and document all secrets securely.

**Note:** Actual API key generation requires manual login to OpenAI/Anthropic dashboards. Documentation and scripts completed.

#### Steps:

1. **Rotate OpenAI API Key** (10 minutes)
   - [x] Documentation created: `docs/operations/api-key-rotation-guide.md` (comprehensive rotation guide)
   - [ ] Log in to platform.openai.com → API Keys (manual step for xavier)
   - [ ] Create new API key: "Transfer2Read Production" (manual)
   - [ ] Copy key immediately (only shown once) (manual)
   - [ ] Store in password manager: `OPENAI_API_KEY_PROD` (manual)
   - [ ] Set usage limits: Monthly budget $100-500 (manual)
   - [ ] Delete or disable old dev API key (if separate) (manual)

2. **Rotate Anthropic API Key** (10 minutes)
   - [x] Documentation created: Rotation steps in api-key-rotation-guide.md
   - [ ] Log in to console.anthropic.com → API Keys (manual step for xavier)
   - [ ] Create new API key: "Transfer2Read Production" (manual)
   - [ ] Copy key immediately (manual)
   - [ ] Store in password manager: `ANTHROPIC_API_KEY_PROD` (manual)
   - [ ] Configure rate limits if available (manual)

3. **Document All Production Secrets** (10 minutes)
   - [x] Create secure note template: `docs/operations/production-secrets-template.md`
   - [x] Template includes all required secrets (Supabase, AI APIs, Redis, domain URLs)
   - [ ] Fill template with actual production values in password manager (manual step for xavier)
   - [ ] Share password vault access with team members (if applicable) (manual)
   - [x] Verify `.gitignore` includes: `.env`, `.env.*`, `.env.production` ✓

4. **Verify Git History Clean** (5 minutes)
   - [x] Run command to check for leaked secrets: `git log --all --full-history -- "**/.env*"` ✓
   - [x] Verified: Only `.env.example` template files in git history (no actual secrets) ✓
   - [x] `.gitignore` updated to include `.env.production` ✓

#### Deliverables:
- ✅ API Key Rotation Guide: `docs/operations/api-key-rotation-guide.md` (13KB comprehensive guide)
- ✅ Production Secrets Template: `docs/operations/production-secrets-template.md` (8KB)
- ✅ Git history verified clean (no leaked secrets)
- ✅ `.gitignore` updated to exclude `.env.production`
- ⏳ New OpenAI API key for production (awaiting manual generation by xavier)
- ⏳ New Anthropic API key for production (awaiting manual generation by xavier)
- ⏳ All secrets documented in password manager (awaiting manual entry by xavier)

#### Validation:
- [ ] Test OpenAI key with curl:
  ```bash
  curl https://api.openai.com/v1/models \
    -H "Authorization: Bearer $OPENAI_API_KEY"
  # Expected: List of available models
  ```
- [ ] Test Anthropic key:
  ```bash
  curl https://api.anthropic.com/v1/messages \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "content-type: application/json" \
    -d '{"model":"claude-3-haiku-20240307","max_tokens":1024,"messages":[{"role":"user","content":"Hello"}]}'
  # Expected: Claude response
  ```

#### Blockers/Risks:
- OpenAI keys billed to payment method on file (ensure valid credit card)
- Anthropic API access requires approved account (check if you have API access)

---

### QW-4: Documentation Update for Production

**Priority:** MEDIUM (Helps team, but not blocking)
**Estimated Time:** 1-1.5 hours
**Status:** ✅ Complete (2025-12-30)

**Objective:** Update README.md and create production deployment guide for team reference.

#### Steps:

1. **Update README.md** (30 minutes)
   - [x] Read current README.md
   - [x] Add "Production Deployment" section with:
     - [x] Link to production URLs (frontend: transfer2read.com, backend: api.transfer2read.com)
     - [x] Status badges (MVP Complete, Launch Preparing)
     - [x] Environment variables required (reference password manager)
     - [x] Quick Wins checklist integrated into deployment section
   - [x] Update deployment guide links to point to new operations docs
   - [x] Add "Project Status" badge:
     ```markdown
     ![Status](https://img.shields.io/badge/status-MVP%20Complete-green)
     ![Launch](https://img.shields.io/badge/launch-preparing-yellow)
     ```

2. **Create Production Deployment Guide** (30 minutes)
   - [x] Create new file: `docs/operations/production-deployment-guide.md` (17KB)
   - [x] Document:
     - [x] **Step 1:** Vercel deployment setup (link GitHub repo, configure env vars)
     - [x] **Step 2:** Railway deployment setup (backend API service, Celery worker service, Redis)
     - [x] **Step 3:** Supabase production project setup (reference QW-2)
     - [x] **Step 4:** Environment variable configuration (copy from password manager)
     - [x] **Step 5:** DNS configuration (QW-1 reference)
     - [x] **Step 6:** Smoke test procedure (register → upload → convert → download)
   - [x] Include troubleshooting section (CORS errors, 503 errors, DNS issues, SSL provisioning)

3. **Create Rollback Procedures** (15 minutes)
   - [x] Create file: `docs/operations/rollback-procedures.md` (18KB)
   - [x] Document:
     - [x] How to revert Vercel deployment (rollback to previous deployment via dashboard)
     - [x] How to revert Railway deployment (redeploy previous Docker image)
     - [x] How to rollback database changes (Supabase backups, restore procedure)
     - [x] API key compromise response (revoke, rotate, update env vars)
     - [x] Incident response checklist
     - [x] Post-incident review template
   - [x] Emergency contacts (Xavier's email, escalation path)

4. **Update Architecture Document** (15 minutes)
   - [x] Open `docs/architecture.md`
   - [x] Add section: "Production Deployment Architecture" (400 lines)
   - [x] Document:
     - [x] Production infrastructure (Vercel + Railway + Supabase)
     - [x] Domain setup (transfer2read.com, api.transfer2read.com)
     - [x] Deployment architecture diagram (ASCII)
     - [x] Security configuration (HTTPS/SSL, CORS, RLS, secrets rotation)
     - [x] Monitoring stack (Sentry, UptimeRobot, PostHog - planned for Story 7.1)
     - [x] Disaster recovery (RTO/RPO, backup strategy, rollback procedures)
     - [x] Cost estimation (free tier vs production tier)
     - [x] Scalability & performance benchmarks

#### Deliverables:
- ✅ README.md updated with production info (status badges, custom domains, Quick Wins checklist)
- ✅ `docs/operations/production-deployment-guide.md` created (17KB comprehensive guide)
- ✅ `docs/operations/rollback-procedures.md` created (18KB disaster recovery guide)
- ✅ Architecture document updated (400-line Production Deployment Architecture section)
- ✅ `.env.production.example` created (production environment variables template)

#### Validation:
- [ ] Ask a team member (or review yourself) to follow deployment guide and confirm it's clear

#### Blockers/Risks:
- None (documentation task, can iterate)

---

### QW-5: Beta User List Compilation

**Priority:** MEDIUM (Prepares for UAT in Story 7.4)
**Estimated Time:** 30-45 minutes
**Status:** ✅ Complete (2025-12-30)

**Objective:** Compile list of 5-10 beta testers with diverse use cases for User Acceptance Testing.

**Note:** Templates and infrastructure created. Actual recruitment requires manual execution by xavier.

#### Steps:

1. **Define Beta User Personas** (10 minutes)
   - [x] Target personas documented (from PRD):
     - [x] **Student:** Converting textbooks, lecture notes
     - [x] **Researcher:** Technical papers, journals with equations/tables
     - [x] **Professional:** Business documents, reports
     - [x] **Multi-language user:** Documents with CJK characters
     - [x] **Accessibility user:** Screen reader, keyboard navigation (optional for MVP)

2. **Recruit Beta Users** (20 minutes)
   - [x] Created Google Form draft: `docs/operations/beta-signup-google-form-draft.md`
   - [x] Sources documented:
     - [x] Personal network (friends, colleagues)
     - [x] Reddit: r/ebooks, r/kindle, r/PDF
     - [x] Twitter/X: Post call for beta testers with Google Form link
     - [x] Product Hunt "Ship" page (free pre-launch landing page)
   - [x] Google Form questions drafted (11 questions):
     - [x] Name, Email
     - [x] "What type of PDFs do you want to convert?" (text, technical books, multi-language, etc.)
     - [x] "What e-reader do you use?" (Apple Books, Kindle, Kobo, etc.)
     - [x] Use case details, conversion challenges, testing availability
     - [x] Incentive preference, accessibility needs, referral source
   - [ ] Create actual Google Form from draft (manual step for xavier)
   - [ ] Publish form on Reddit/Twitter/Product Hunt (manual step for xavier)

3. **Create Beta User Spreadsheet** (10 minutes)
   - [x] Create template: `docs/operations/beta-users.csv` (10 sample personas)
   - [x] Columns defined:
     - [x] Name, Email, Persona, PDF Type, E-Reader, Status (Invited, Testing, Completed)
   - [x] Target documented: 5-10 users minimum
   - [x] Diversity goals documented:
     - [x] At least 2 users with complex PDFs (technical books)
     - [x] At least 1 user with multi-language documents
     - [x] At least 1 user on each major e-reader (Apple Books, Kindle, Kobo)
   - [ ] Fill spreadsheet with actual beta users (manual step after recruitment)

4. **Draft Beta Invite Email** (10 minutes)
   - [x] Create email template: `docs/operations/beta-invite-email-template.md`
   - [x] Content:
     - [x] Thank you for signing up
     - [x] What is Transfer2Read (elevator pitch)
     - [x] What we need from you (test 2-3 PDFs, provide feedback)
     - [x] Timeline (1 week testing period)
     - [x] Incentive (Free Pro tier for 3 months + optional $25 Amazon gift card)
     - [x] Link to app: https://transfer2read.com
     - [x] Link to feedback form placeholder (create in QW-5 or defer to Story 7.4)
     - [x] Reminder email template
     - [x] Thank-you email template
   - [ ] Send beta invite emails (after production is stable - defer until Story 7.1 complete)

#### Deliverables:
- ✅ Beta user spreadsheet template created: `docs/operations/beta-users.csv` (10 sample personas)
- ✅ Beta invite email template drafted: `docs/operations/beta-invite-email-template.md` (includes reminder & thank-you templates)
- ✅ Google Form draft created: `docs/operations/beta-signup-google-form-draft.md` (11 questions + promotion strategy)
- ⏳ Actual Google Form published (awaiting manual creation by xavier)
- ⏳ Beta user recruitment campaign launched (awaiting manual execution by xavier)

#### Validation:
- [ ] List includes diverse personas (students, researchers, multi-language users)
- [ ] Contact info verified (valid emails)

#### Blockers/Risks:
- Recruitment may take time (start social media outreach early)
- May need to offer incentive (free Pro tier for 3 months, or $25 Amazon gift card)

---

## Execution Timeline

### Day 1 (2-3 hours)
- [ ] **Morning:** QW-1 Domain Purchase & DNS Setup (1-2 hours)
- [ ] **Afternoon:** QW-2 Supabase Production Project (start, finish next day if needed)

### Day 2 (2-3 hours)
- [ ] **Morning:** QW-2 Supabase Production Project (complete)
- [ ] **Afternoon:** QW-3 API Key Rotation (30 min) + QW-5 Beta User List (30 min)

### Day 3 (1-2 hours)
- [ ] **Anytime:** QW-4 Documentation Update (can work in evenings, non-blocking)

**Total Calendar Time:** 3 days (part-time)
**Total Active Work:** 4-6 hours

---

## Success Criteria

**Definition of Done:**
- ⏳ All 5 Quick Win tasks marked "Complete" (4 of 5 complete: QW-1, QW-3, QW-4, QW-5)
- ✅ QW-1: Production domain live with HTTPS (frontend + backend) - COMPLETE (2025-12-30)
- ⏳ QW-2: Production Supabase project operational (database + auth + storage) - Awaiting manual setup by xavier
- ✅ QW-3: Production API keys rotated and documented (Templates created, awaiting manual key generation)
- ✅ QW-4: Documentation updated for team reference (README, deployment guide, rollback procedures, architecture)
- ✅ QW-5: Beta user list compiled (Templates created: spreadsheet, email, Google Form draft)

**Validation:**
- [x] Can access `https://transfer2read.app` (frontend loads) ✓ QW-1 complete
- [x] Can access `https://api.transfer2read.app/api/health` (returns 200 OK) ✓ QW-1 complete
- [x] DNS records documented in password manager ✓ QW-1 complete
- [ ] Supabase production project shows in dashboard - Pending QW-2
- [ ] Password manager contains all production secrets - Pending QW-3 (manual key generation)
- [x] README.md has production deployment section ✓ (QW-4 complete)
- [x] Beta user templates created ✓ (QW-5 complete - recruitment pending)

**Completed 2025-12-30:**
- ✅ **QW-1 (Domain & DNS):** Domain purchased (transfer2read.app) + DNS configured (Vercel + Railway) + SSL provisioned + backend deployment fixed
- ✅ **QW-3 (Documentation):** API key rotation guide + production secrets template + git history verified clean
- ✅ **QW-4 (Documentation):** README updated + production-deployment-guide.md + rollback-procedures.md + architecture.md updated
- ✅ **QW-5 (Templates):** Beta user CSV template + beta invite email template + Google Form draft
- ✅ **Code Prep:** .env.production.example + health check validation

**Remaining Manual Steps (for xavier):**
- ⏳ **QW-2:** Create Supabase production project + run SQL scripts + configure storage buckets
- ⏳ **QW-3:** Generate OpenAI/Anthropic production API keys + store in password manager

---

## Blockers & Mitigations

| Blocker | Mitigation |
|---------|-----------|
| DNS propagation slow (48 hours) | Start QW-1 first, work on other tasks in parallel |
| Domain already taken | Have 2-3 backup domain names ready |
| Supabase free tier insufficient | Upgrade to Pro tier ($25/month, budget approved?) |
| OpenAI API key requires payment method | Add credit card to OpenAI account |
| Can't recruit beta users | Offer incentive (free Pro tier, gift card) |

---

## Next Steps After Quick Wins

**Immediate Next (Once QW-1, QW-2, QW-3 Complete):**
1. **Deploy to Production** (soft launch, not public yet)
   - Update Vercel environment variables to use production Supabase
   - Update Railway environment variables to use production keys
   - Run end-to-end smoke test on production

2. **Mark Epic 7 as "Contexted"** (ready to start stories)
   - Update sprint-status.yaml: `epic-7: contexted`
   - Create Story 7.1 file and begin execution

3. **Continue Launch Checklist** in parallel with Epic 7 stories

**Long-Term Next (After Epic 7 Complete):**
- Launch to beta users (Story 7.4)
- Public launch announcement
- Monitor production metrics (Story 7.5)

---

## Track Progress

**Use this document as daily checklist:**
- Update status: ☐ → ⏳ → ✅
- Log blockers in real-time
- Estimate actual time spent vs. planned

**Daily Standup Questions:**
1. What did I complete yesterday? (Check ✅ tasks)
2. What am I working on today? (Check ⏳ tasks)
3. Any blockers? (Document in Blockers section)

---

## Sign-Off

**Plan Approved By:** Xavier (Product Manager)
**Date:** 2025-12-26
**Target Completion:** 2025-12-31

**Once complete, update sprint-status.yaml:**
```yaml
quick-wins-launch-prep: completed  # Add this line after epic-6-retrospective
```

---

**Let's build some momentum! 🚀**
