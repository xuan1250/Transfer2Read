# Transfer2Read Production Secrets Template

**Document Type:** Secure Note Template (for Password Manager)
**Owner:** Xavier (Product Manager)
**Created:** 2025-12-30
**Purpose:** Master template for storing all production secrets securely

---

## Instructions

**How to Use This Template:**

1. **Create Secure Note in Password Manager**
   - Tool: 1Password, LastPass, Bitwarden, or similar
   - Name: "Transfer2Read Production Secrets"
   - Type: Secure Note
   - Tags: production, transfer2read, secrets

2. **Copy Template Below**
   - Replace all `XXXXX` placeholders with actual values
   - Delete sections that don't apply (e.g., optional services)
   - Add rotation dates as you create/rotate keys

3. **Share Access Securely**
   - Share password vault with team members who need production access
   - Set permissions: "Can view and edit" for DevOps team
   - Set permissions: "Can view only" for developers (read-only)

4. **Never Store in Plain Text**
   - ❌ DO NOT store in Google Docs, Notion, Slack, or email
   - ❌ DO NOT commit this file with actual values to git
   - ✅ ONLY store in encrypted password manager vault

---

## Template

```bash
# ============================================
# Transfer2Read Production Secrets
# Last Updated: YYYY-MM-DD
# Owner: Xavier
# Team Access: [List who has access]
# ============================================

# ============================================
# SUPABASE PRODUCTION
# ============================================
# Project URL: https://app.supabase.com/project/XXXXX
# Region: [e.g., US East, EU West]
# Created: YYYY-MM-DD

SUPABASE_URL=https://XXXXX.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.XXXXX  # PUBLIC (safe for frontend)
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.XXXXX  # SECRET (backend only, never expose to frontend)

# Database Connection String (optional, for direct access):
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres

# Supabase Database Password:
SUPABASE_DB_PASSWORD=XXXXX  # Set during project creation

# ============================================
# AI API KEYS
# ============================================

# OpenAI API Key
# Dashboard: https://platform.openai.com/api-keys
# Created: YYYY-MM-DD
# Rotated: YYYY-MM-DD
# Next Rotation: YYYY-MM-DD (90 days from last rotation)
# Monthly Budget: $XXX
OPENAI_API_KEY=sk-proj-XXXXX

# Anthropic API Key
# Dashboard: https://console.anthropic.com/settings/keys
# Created: YYYY-MM-DD
# Rotated: YYYY-MM-DD
# Next Rotation: YYYY-MM-DD (90 days from last rotation)
ANTHROPIC_API_KEY=sk-ant-XXXXX

# ============================================
# REDIS (Railway Auto-Generated)
# ============================================
# Service: Railway Redis Plugin
# Dashboard: https://railway.app/project/XXXXX
REDIS_URL=redis://default:XXXXX@XXXXX.railway.app:XXXXX

# Alternative Redis Provider (if using Upstash instead):
# REDIS_URL=redis://default:XXXXX@XXXXX.upstash.io:XXXXX
# REDIS_TLS_URL=rediss://default:XXXXX@XXXXX.upstash.io:XXXXX  # SSL version

# ============================================
# DOMAIN & URLS
# ============================================
# Domain Registrar: [Namecheap, Google Domains, Cloudflare, etc.]
# Purchased: YYYY-MM-DD
# Auto-Renewal: [Enabled/Disabled]

FRONTEND_URL=https://transfer2read.com
BACKEND_API_URL=https://api.transfer2read.com
WWW_REDIRECT=https://www.transfer2read.com  # Redirects to transfer2read.com

# Optional: Status Page
STATUS_PAGE_URL=https://status.transfer2read.com

# ============================================
# DEPLOYMENT PLATFORMS
# ============================================

# Vercel (Frontend)
# Dashboard: https://vercel.com/[TEAM]/transfer2read
# Project ID: proj_XXXXX
# Team: [Your Vercel Team Name]
# Git Integration: GitHub (main branch → auto-deploy to production)

# Railway (Backend + Workers)
# Dashboard: https://railway.app/project/XXXXX
# Project ID: XXXXX
# Services:
#   - Backend API (FastAPI)
#   - Celery Worker (background tasks)
#   - Redis (caching & task queue)
# Git Integration: GitHub (main branch → auto-deploy to production)

# ============================================
# MONITORING & ERROR TRACKING (Story 7.1)
# ============================================
# NOTE: Add these after completing Epic 7 Story 7.1

# Sentry (Error Tracking)
# Dashboard: https://sentry.io/organizations/XXXXX/projects/transfer2read/
# SENTRY_DSN=https://XXXXX@oXXXXX.ingest.sentry.io/XXXXX

# UptimeRobot (Uptime Monitoring)
# Dashboard: https://uptimerobot.com/dashboard
# API Key: XXXXX (read-only)
# Alert Email: [your-email@example.com]

# PostHog (Analytics)
# Dashboard: https://app.posthog.com/project/XXXXX
# POSTHOG_API_KEY=phc_XXXXX

# ============================================
# THIRD-PARTY SERVICES (Optional)
# ============================================

# SendGrid (Email Delivery, if not using Supabase Auth emails)
# SENDGRID_API_KEY=SG.XXXXX

# Stripe (Payment Processing, for Pro tier - Epic 6)
# Dashboard: https://dashboard.stripe.com/
# STRIPE_SECRET_KEY=sk_live_XXXXX  # SECRET (backend only)
# STRIPE_PUBLISHABLE_KEY=pk_live_XXXXX  # PUBLIC (safe for frontend)
# STRIPE_WEBHOOK_SECRET=whsec_XXXXX  # For webhook signature verification

# ============================================
# ENVIRONMENT-SPECIFIC NOTES
# ============================================

# PRODUCTION vs STAGING:
# - Production: Uses keys above
# - Staging: Uses separate keys (store in separate secure note: "Transfer2Read Staging Secrets")

# DEVELOPMENT:
# - Use local .env file (NOT committed to git)
# - Use separate Supabase project (free tier)
# - Use separate OpenAI/Anthropic keys with lower rate limits

# ============================================
# ACCESS CONTROL
# ============================================

# Who has access to this vault:
# - Xavier (Owner, Full Access)
# - [DevOps Team Member 1] (Full Access)
# - [Developer 1] (View Only)
# - [Developer 2] (View Only)

# Access granted: YYYY-MM-DD
# Last reviewed: YYYY-MM-DD
# Next review: YYYY-MM-DD (quarterly)

# ============================================
# EMERGENCY CONTACTS
# ============================================

# Primary Contact: Xavier
# Email: [your-email@example.com]
# Phone: [+1-XXX-XXX-XXXX]

# Backup Contact: [DevOps Lead]
# Email: [devops@example.com]
# Phone: [+1-XXX-XXX-XXXX]

# Escalation Path:
# 1. Primary contact (Xavier)
# 2. Backup contact (DevOps Lead)
# 3. Platform support (Vercel, Railway, Supabase)

# ============================================
# INCIDENT RESPONSE
# ============================================

# If API keys are compromised:
# 1. IMMEDIATELY rotate ALL keys (follow docs/operations/api-key-rotation-guide.md)
# 2. Revoke old keys in OpenAI/Anthropic dashboards
# 3. Check billing for unexpected usage spikes
# 4. Review Railway/Vercel logs for suspicious activity
# 5. Document incident in docs/operations/incident-log.md (create if needed)

# If database is compromised:
# 1. IMMEDIATELY disable Supabase service_role key (regenerate in Supabase Dashboard)
# 2. Review Supabase logs for unauthorized access
# 3. Restore from backup if data integrity compromised
# 4. Rotate database password
# 5. Audit RLS policies for vulnerabilities

# ============================================
# BACKUP & DISASTER RECOVERY
# ============================================

# Supabase Backups:
# - Automatic daily backups (7-day retention on free tier, 30-day on Pro)
# - Manual backup: Supabase Dashboard → Database → Backups → Download
# - Restore procedure: Supabase Dashboard → Database → Backups → Restore

# Code Repository:
# - GitHub: https://github.com/[USERNAME]/Transfer2Read
# - Branch strategy: main (production), develop (staging)
# - Protected branches: main (requires PR review)

# Environment Variables Backup:
# - Vercel: Export via Vercel CLI: `vercel env pull .env.production.backup`
# - Railway: Export via Railway CLI: `railway vars --json > railway-vars.json`
# - Store backups in this password vault (secure note)

# ============================================
# ROTATION SCHEDULE
# ============================================

# OpenAI API Key:
# - Last rotated: YYYY-MM-DD
# - Next rotation: YYYY-MM-DD (90 days)
# - Rotation guide: docs/operations/api-key-rotation-guide.md

# Anthropic API Key:
# - Last rotated: YYYY-MM-DD
# - Next rotation: YYYY-MM-DD (90 days)
# - Rotation guide: docs/operations/api-key-rotation-guide.md

# Supabase Service Key:
# - Rotation: On-demand (only if compromised)
# - How to rotate: Supabase Dashboard → Settings → API → Generate new key

# Database Password:
# - Rotation: Annually or if compromised
# - How to rotate: Supabase Dashboard → Settings → Database → Reset password

# Stripe Keys (if using):
# - Rotation: On-demand (only if compromised)
# - How to rotate: Stripe Dashboard → Developers → API keys → Roll key

# ============================================
# COMPLIANCE & SECURITY
# ============================================

# Data Retention:
# - Conversion jobs: 30 days (auto-delete after 30 days - see QW-2 Step 6)
# - User data: Retained until user deletes account
# - Logs: 7 days (Railway default retention)

# Encryption:
# - Data at rest: Encrypted by Supabase (AES-256)
# - Data in transit: HTTPS/TLS 1.3 (enforced by Vercel/Railway)
# - Secrets: Encrypted by password manager (AES-256)

# Compliance:
# - GDPR: User data deletion supported (Supabase RLS + account deletion)
# - CCPA: Data export supported (Supabase export feature)
# - SOC 2: Supabase is SOC 2 Type II certified

# ============================================
# NOTES
# ============================================

# Add any additional notes, tips, or gotchas here:
# - Example: "Redis URL changes every time Railway restarts the service - check Railway dashboard for latest URL"
# - Example: "Supabase anon key is safe to expose in frontend (RLS protects data)"
# - Example: "OpenAI rate limits: 10,000 tokens/min on free tier, 90,000 on paid tier"

```

---

## Validation Checklist

**After filling out template, verify:**

- [ ] All `XXXXX` placeholders replaced with actual values
- [ ] Rotation dates added for API keys
- [ ] Team access list updated with current members
- [ ] Emergency contacts verified (phone/email work)
- [ ] Password manager vault shared with team
- [ ] This template file (`.md`) does NOT contain actual secrets (only placeholder XXXXX)
- [ ] Actual secrets stored ONLY in password manager secure note

---

## Related Documents

- **API Key Rotation Guide:** `docs/operations/api-key-rotation-guide.md`
- **Production Deployment Guide:** `docs/operations/production-deployment-guide.md` (created in QW-4)
- **Rollback Procedures:** `docs/operations/rollback-procedures.md` (created in QW-4)
- **Quick Wins Plan:** `docs/sprint-artifacts/quick-wins-plan-2025-12-26.md`

---

**Document Status:** ✅ Complete
**Last Reviewed:** 2025-12-30
**Next Review:** 2025-03-30 (quarterly)
