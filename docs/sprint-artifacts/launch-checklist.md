# Transfer2Read - Launch Checklist

**Project:** Transfer2Read
**Created:** 2025-12-26
**Purpose:** Quick verification checklist for straightforward launch preparation items
**Context:** Complements Epic 7 stories with simple go/no-go checks

---

## How to Use This Checklist

This checklist covers **straightforward verifications** that don't require full story implementation:
- DNS, SSL, and domain configuration
- Environment variable validation
- Documentation review
- Simple functional checks

For **complex launch activities** (load testing, security audit, UAT), refer to **Epic 7 Stories** in `docs/epics.md`.

**Progress:** ☐ Not Started | ⏳ In Progress | ✅ Complete

---

## 1. Domain & DNS Configuration

### Frontend Domain (Vercel)
- [ ] Custom domain configured (e.g., `transfer2read.com`, `app.transfer2read.com`)
- [ ] SSL certificate valid and auto-renewing
- [ ] DNS records propagated (A/CNAME pointing to Vercel)
- [ ] WWW redirect configured (www → non-www or vice versa)
- [ ] Preview URLs working for feature branches

### Backend API Domain (Railway)
- [ ] Custom domain configured (e.g., `api.transfer2read.com`)
- [ ] SSL certificate valid (Railway auto-provision or custom)
- [ ] DNS records propagated
- [ ] CORS allows production frontend domain only

### Additional Domains (Optional)
- [ ] Status page domain (e.g., `status.transfer2read.com`)
- [ ] Documentation/help domain (e.g., `docs.transfer2read.com`)

---

## 2. Environment Variables Verification

### Frontend (Vercel)
- [ ] `NEXT_PUBLIC_SUPABASE_URL` - Production Supabase project URL
- [ ] `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Production anon key (safe for client)
- [ ] `NEXT_PUBLIC_API_URL` - Production backend API URL (https://api.transfer2read.com)
- [ ] `NODE_ENV=production` (auto-set by Vercel)

### Backend API (Railway)
- [ ] `SUPABASE_URL` - Production Supabase project URL
- [ ] `SUPABASE_SERVICE_KEY` - Production service role key (SECRET!)
- [ ] `OPENAI_API_KEY` - Production API key (rotated from dev)
- [ ] `ANTHROPIC_API_KEY` - Production API key (rotated from dev)
- [ ] `REDIS_URL` - Railway Redis connection string
- [ ] `FASTAPI_ENV=production` - Disables debug mode
- [ ] `CORS_ORIGINS` - Production frontend domain(s) only

### Celery Worker (Railway)
- [ ] Same environment variables as Backend API (shares config)
- [ ] Worker process configured in Railway (separate service)

### Secrets Management
- [ ] All production secrets stored in password manager (1Password, LastPass, Bitwarden)
- [ ] Team members have access to password vault
- [ ] `.env` files NEVER committed to git (verified with `git log --all --full-history -- "**/.env*"`)

---

## 3. Supabase Production Configuration

### Project Setup
- [ ] Separate production Supabase project created (not using dev project)
- [ ] Production project URL different from dev
- [ ] Organization/billing configured (upgrade from free tier if needed)

### Database
- [ ] All tables created: `auth.users`, `conversion_jobs`, `user_usage`
- [ ] Indexes created for performance (on `user_id`, `created_at`, etc.)
- [ ] Row Level Security (RLS) enabled on all user-facing tables
- [ ] RLS policies tested (users can't access each other's data)

### Authentication
- [ ] Email/Password provider enabled
- [ ] Email templates configured (welcome, password reset, confirmation)
- [ ] Google OAuth configured with production Client ID/Secret
- [ ] GitHub OAuth configured with production Client ID/Secret
- [ ] Redirect URLs whitelisted for production domains

### Storage
- [ ] `uploads` bucket created (private, RLS enabled)
- [ ] `downloads` bucket created (private, RLS enabled)
- [ ] RLS policies: Users can only access their own folders (`{user_id}/*`)
- [ ] Storage quota monitored (alert at 80% capacity)
- [ ] File retention policy configured (auto-delete after 30 days)

### Scheduled Jobs
- [ ] Monthly usage reset job configured (pg_cron or Celery Beat)
- [ ] Scheduled job tested (manual trigger or wait for first run)

---

## 4. API Health & Connectivity

### Backend API
- [ ] `/api/health` endpoint returns `200 OK`
- [ ] Health check includes Supabase connection status
- [ ] Health check includes Redis connection status

### Frontend
- [ ] Landing page loads (https://transfer2read.com)
- [ ] No console errors in browser
- [ ] All static assets load (images, fonts, CSS, JS)

### Worker
- [ ] Celery worker logs show successful startup
- [ ] Worker can connect to Redis (broker)
- [ ] Worker can connect to Supabase (for job updates)
- [ ] Test job dispatched and completed successfully

### Inter-Service Communication
- [ ] Frontend can call Backend API (test `/api/health` from browser)
- [ ] Backend API can enqueue Celery tasks
- [ ] Celery worker can read from Redis queue
- [ ] All services can reach Supabase (no firewall blocks)

---

## 5. Functional Smoke Tests

### User Registration & Login
- [ ] User can register with email/password
- [ ] Email confirmation sent (check spam folder)
- [ ] User can log in with email/password
- [ ] User can log in with Google OAuth
- [ ] User can log in with GitHub OAuth
- [ ] Dashboard loads after successful login

### PDF Upload & Conversion
- [ ] User can upload a simple PDF (10 pages, text-only)
- [ ] Upload progress bar displays
- [ ] Conversion job starts automatically
- [ ] Progress updates display in real-time (or via polling)
- [ ] Conversion completes successfully (status: COMPLETED)
- [ ] Quality report displays with confidence score

### Download & History
- [ ] User can download converted EPUB
- [ ] EPUB file opens in Apple Books/Calibre/Kobo
- [ ] Conversion appears in History page
- [ ] User can re-download EPUB from History
- [ ] User can delete job from History

### Tier Limits
- [ ] Free tier user sees "3/5 conversions" usage indicator
- [ ] After 5 conversions, user sees upgrade prompt
- [ ] Upgrade button links to pricing page (or Stripe Checkout)

---

## 6. Security Quick Checks

### HTTPS Enforcement
- [ ] All HTTP requests redirect to HTTPS
- [ ] No mixed content warnings in browser console
- [ ] SSL certificate valid (not expired, not self-signed)

### Authentication
- [ ] Accessing `/dashboard` without login redirects to `/login`
- [ ] JWT token expires after 1 hour (test by waiting)
- [ ] Invalid JWT returns `401 Unauthorized`

### Authorization
- [ ] User A cannot access User B's jobs (test with 2 accounts)
- [ ] User A cannot download User B's files (try URL manipulation)
- [ ] Admin endpoints require `is_superuser` flag

### CORS
- [ ] API rejects requests from unauthorized domains (test with Postman/curl)
- [ ] API allows requests from production frontend domain

---

## 7. Documentation Review

### User-Facing Documentation
- [ ] Landing page explains what Transfer2Read does
- [ ] Pricing page lists Free vs. Pro vs. Premium tiers
- [ ] FAQ page answers common questions (file size limits, supported formats, etc.)
- [ ] Privacy policy published (legal review if needed)
- [ ] Terms of service published (legal review if needed)

### Developer Documentation
- [ ] README.md updated with production deployment instructions
- [ ] Environment variables documented in README or wiki
- [ ] Architecture diagram up-to-date (reflects Supabase + Railway + Vercel)
- [ ] API documentation available (optional: Swagger/OpenAPI at `/api/docs`)

### Operations Documentation
- [ ] Incident response runbook created (`docs/operations/incident-response-runbook.md`)
- [ ] Deployment procedures documented
- [ ] Rollback procedures documented
- [ ] API key rotation procedures documented
- [ ] Database backup/restore procedures documented

---

## 8. Monitoring & Alerting

### Basic Monitoring
- [ ] Railway metrics dashboard accessible
- [ ] Supabase dashboard accessible
- [ ] Uptime monitoring configured (UptimeRobot, Pingdom, etc.)
  - [ ] Frontend uptime check (https://transfer2read.com)
  - [ ] Backend API health check (https://api.transfer2read.com/api/health)

### Error Tracking
- [ ] Sentry (or alternative) integrated in frontend
- [ ] Sentry integrated in backend API
- [ ] Sentry integrated in Celery worker
- [ ] Test error sent to Sentry (verify alerts work)

### Alerts Configured
- [ ] Email/Slack alert on API downtime (>2 minutes)
- [ ] Email/Slack alert on high error rate (>5% of requests)
- [ ] Email/Slack alert on high AI API cost (>$50/day)

---

## 9. Performance Baseline

### Page Load Times (Desktop, Good Connection)
- [ ] Landing page: **< 2 seconds** ✅
- [ ] Dashboard: **< 3 seconds** ✅
- [ ] Split-screen preview (50-page PDF): **< 5 seconds** ✅

### Conversion Performance
- [ ] Simple PDF (10-20 pages): **< 30 seconds** end-to-end ✅
- [ ] Complex PDF (300 pages): **< 2 minutes** (FR35) ✅

*(For full load testing, see Epic 7, Story 7.2)*

---

## 10. Pre-Launch Team Readiness

### Access & Permissions
- [ ] All team members have access to:
  - [ ] GitHub repository
  - [ ] Vercel dashboard
  - [ ] Railway dashboard
  - [ ] Supabase dashboard
  - [ ] Password manager (production secrets)
  - [ ] Monitoring dashboards (Sentry, UptimeRobot)

### Communication Channels
- [ ] Support email configured (e.g., support@transfer2read.com)
- [ ] Team Slack/Discord channel for incidents
- [ ] On-call rotation defined (if applicable)

### Rollback Plan
- [ ] Previous stable version tagged in git
- [ ] Rollback procedure tested (revert deployment)
- [ ] Database rollback plan (if schema changes)

---

## 11. Legal & Compliance

### Privacy & Data Protection
- [ ] Privacy policy reviewed and published
- [ ] Terms of service reviewed and published
- [ ] Cookie consent banner (if using analytics)
- [ ] GDPR compliance (if targeting EU users):
  - [ ] Data deletion flow works (account deletion)
  - [ ] Data export feature (optional for MVP)

### Business Setup
- [ ] Business entity registered (LLC, corporation, etc.)
- [ ] Payment processing set up (Stripe account verified)
- [ ] Tax ID obtained (if applicable)

---

## 12. Marketing & Launch Preparation

### Launch Assets
- [ ] Landing page optimized for conversions
- [ ] Social media accounts created (Twitter/X, LinkedIn, etc.)
- [ ] Launch announcement drafted
- [ ] Email list set up (for beta users, early adopters)

### Analytics
- [ ] Google Analytics (or alternative) integrated
- [ ] Conversion funnel tracking configured (signup → upload → conversion → download)
- [ ] Goal tracking set up (e.g., "User completed first conversion")

### Beta User Outreach
- [ ] Beta user list compiled (5-10 testers)
- [ ] Beta invite emails drafted
- [ ] Feedback survey created (Google Forms, Typeform)

---

## 13. Final Go/No-Go Decision

### Launch Readiness Criteria

**MUST-HAVE (Blocking Issues):**
- [ ] ✅ All production services operational (Vercel, Railway, Supabase)
- [ ] ✅ End-to-end smoke test passes (register → upload → convert → download)
- [ ] ✅ Security audit complete with no critical vulnerabilities (Epic 7.3)
- [ ] ✅ Monitoring and alerting functional (Epic 7.5)
- [ ] ✅ 0 critical bugs from UAT (Epic 7.4)

**NICE-TO-HAVE (Can Launch Without):**
- [ ] Load testing complete (Epic 7.2) - can scale after launch if needed
- [ ] Full UAT with 10 beta users - can launch with fewer testers
- [ ] Public status page - can add post-launch
- [ ] Social media presence - can build after launch

### Launch Decision
- [ ] **Product Manager (Xavier) approval:** GO / NO-GO
- [ ] **Technical Lead approval:** GO / NO-GO
- [ ] **Security approval:** GO / NO-GO

**Final Decision:** ☐ APPROVED FOR LAUNCH | ☐ HOLD (issues to resolve)

---

## 14. Launch Day Checklist

### Morning of Launch
- [ ] All team members notified of launch time
- [ ] Monitoring dashboards open (Railway, Supabase, Sentry, Uptime)
- [ ] Support email inbox ready (support@transfer2read.com)
- [ ] Incident response runbook accessible

### Launch Steps
1. [ ] Final smoke test on production (register → upload → convert → download)
2. [ ] Remove "Beta" badge from UI (if present)
3. [ ] Announce launch on social media (Twitter, LinkedIn, Product Hunt)
4. [ ] Send beta user thank-you email with launch announcement
5. [ ] Post in relevant communities (Reddit, Hacker News, etc.)

### Post-Launch Monitoring (First 24 Hours)
- [ ] Monitor error rates in Sentry (target: <1% of requests)
- [ ] Monitor uptime (target: 99%+)
- [ ] Monitor AI API costs (budget: <$100/day initially)
- [ ] Monitor user feedback (support emails, social media mentions)
- [ ] Track signup rate and conversion rate (analytics dashboard)

---

## 15. Post-Launch Follow-Up

### Week 1 After Launch
- [ ] Review monitoring metrics (uptime, errors, performance)
- [ ] Address any critical bugs reported by users
- [ ] Send follow-up survey to early users (NPS score, feedback)
- [ ] Document lessons learned in retrospective

### Week 2-4 After Launch
- [ ] Analyze usage patterns (most popular PDF types, conversion times)
- [ ] Identify bottlenecks for optimization
- [ ] Plan next epic (Post-MVP Enhancements, Marketing, Technical Debt)

---

## Checklist Completion Summary

**Total Items:** 150+
**Completed:** ☐ / 150+
**Completion Rate:** ☐%

**Status:** ☐ Not Started | ⏳ In Progress | ✅ Ready for Launch

**Sign-Off:**
- Product Manager (Xavier): _________________ Date: _______
- Technical Lead: __________________________ Date: _______
- Security Reviewer: _______________________ Date: _______

---

**Next Steps After Launch:**
1. Monitor production metrics closely for first 48 hours
2. Run Epic 7 Retrospective workflow after 1 week
3. Plan Epic 8 based on user feedback and business priorities
4. Celebrate the launch! 🎉🚀

---
