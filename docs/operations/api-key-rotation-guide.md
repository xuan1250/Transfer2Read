# API Key Rotation Guide for Production

**Document Owner:** Xavier (Product Manager)
**Created:** 2025-12-30
**Purpose:** Rotate OpenAI and Anthropic API keys for production environment
**Part of:** Quick Win QW-3

---

## Overview

This guide covers rotating API keys for Transfer2Read production deployment. Follow these steps whenever:

- Deploying to production for the first time
- Keys are suspected to be compromised
- Scheduled rotation (recommended: every 90 days)
- Team member with key access leaves

**Time Required:** 30 minutes
**Prerequisites:**
- OpenAI account with billing enabled
- Anthropic API access (console.anthropic.com)
- Access to password manager (1Password, LastPass, or similar)

---

## Step 1: Rotate OpenAI API Key

### 1.1 Create New Production Key

1. **Log in to OpenAI Platform**
   - Navigate to: https://platform.openai.com/api-keys
   - Authenticate with your OpenAI account

2. **Create New API Key**
   ```bash
   # In OpenAI Dashboard:
   # 1. Click "Create new secret key"
   # 2. Name: "Transfer2Read Production"
   # 3. Permissions: Full access (or restrict to specific models if available)
   # 4. Click "Create secret key"
   ```

3. **Copy Key Immediately**
   - OpenAI shows the key ONLY ONCE
   - Format: `sk-proj-...` (starts with `sk-proj-` for project keys)
   - Store temporarily in secure note (do NOT close browser tab yet)

4. **Set Usage Limits (Recommended)**
   ```bash
   # In OpenAI Dashboard → Settings → Limits:
   # - Monthly budget: $100-500 (adjust based on expected traffic)
   # - Email alerts: 80% and 100% of budget
   # - Rate limits: Leave default initially (adjust after load testing)
   ```

5. **Store Key in Password Manager**
   ```bash
   # In password manager (1Password/LastPass):
   # - Create secure note: "Transfer2Read Production Secrets"
   # - Field: OPENAI_API_KEY_PROD
   # - Value: sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   # - Tags: production, transfer2read, openai
   ```

### 1.2 Delete or Disable Old Key (If Applicable)

1. **Identify Old Keys**
   - In OpenAI Dashboard → API Keys
   - Look for keys named "Transfer2Read Dev" or older production keys

2. **Revoke Old Keys**
   ```bash
   # Click "..." menu next to old key → "Revoke"
   # Confirm revocation
   # NOTE: Services using old key will IMMEDIATELY fail
   ```

3. **Update Deployment BEFORE Revoking**
   - If old key is currently in use, update Railway/Vercel env vars FIRST
   - Test new key in staging environment
   - Only revoke old key after confirming new key works

### 1.3 Validate New Key

```bash
# Test OpenAI key with curl:
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

# Expected output:
# {
#   "data": [
#     {"id": "gpt-4", "object": "model", ...},
#     {"id": "gpt-3.5-turbo", "object": "model", ...},
#     ...
#   ]
# }

# If you get error 401 Unauthorized:
# - Verify key was copied correctly (no extra spaces)
# - Check if key was revoked accidentally
# - Ensure billing is enabled on OpenAI account
```

---

## Step 2: Rotate Anthropic API Key

### 2.1 Create New Production Key

1. **Log in to Anthropic Console**
   - Navigate to: https://console.anthropic.com/settings/keys
   - Authenticate with your Anthropic account

2. **Create New API Key**
   ```bash
   # In Anthropic Console:
   # 1. Click "Create Key"
   # 2. Name: "Transfer2Read Production"
   # 3. Click "Create Key"
   ```

3. **Copy Key Immediately**
   - Anthropic shows the key ONLY ONCE
   - Format: `sk-ant-...` (starts with `sk-ant-`)
   - Store temporarily in secure note

4. **Set Rate Limits (If Available)**
   - Check Anthropic Console for rate limiting options
   - Set monthly budget if feature is available
   - Enable email alerts for usage

5. **Store Key in Password Manager**
   ```bash
   # In password manager:
   # - Add to same secure note: "Transfer2Read Production Secrets"
   # - Field: ANTHROPIC_API_KEY_PROD
   # - Value: sk-ant-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   # - Tags: production, transfer2read, anthropic
   ```

### 2.2 Delete Old Key (If Applicable)

1. **Identify Old Keys**
   - In Anthropic Console → Settings → API Keys
   - Look for older keys or dev keys

2. **Delete Old Keys**
   ```bash
   # Click "Delete" next to old key
   # Confirm deletion
   # NOTE: Services using old key will IMMEDIATELY fail
   ```

3. **Update Deployment BEFORE Deleting**
   - Same precaution as OpenAI: update env vars first, test, then delete old key

### 2.3 Validate New Key

```bash
# Test Anthropic key with curl:
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: sk-ant-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-3-haiku-20240307",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# Expected output:
# {
#   "id": "msg_XXXXXXXX",
#   "type": "message",
#   "role": "assistant",
#   "content": [{"type": "text", "text": "Hello! How can I help you today?"}],
#   ...
# }

# If you get error 401 Unauthorized:
# - Verify key was copied correctly
# - Check if key was deleted accidentally
# - Ensure Anthropic API access is enabled for your account
```

---

## Step 3: Document All Production Secrets

### 3.1 Create Master Secrets Document

Create secure note in password manager: **"Transfer2Read Production Secrets"**

**Template:**

```bash
# ============================================
# Transfer2Read Production Secrets
# Last Updated: 2025-12-30
# Owner: Xavier
# ============================================

# Supabase Production
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... # PUBLIC (safe for frontend)
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... # SECRET (backend only)

# AI APIs
OPENAI_API_KEY=sk-proj-... # SECRET
ANTHROPIC_API_KEY=sk-ant-... # SECRET

# Redis (Railway auto-generated)
REDIS_URL=redis://default:password@host.railway.app:port # SECRET

# Domain & URLs
FRONTEND_URL=https://transfer2read.com
BACKEND_API_URL=https://api.transfer2read.com

# Deployment Platforms
# - Vercel Project ID: proj_XXXXXXXX
# - Railway Project ID: proj_XXXXXXXX

# ============================================
# ROTATION SCHEDULE
# ============================================
# OpenAI API Key: Rotate every 90 days (next: 2025-03-30)
# Anthropic API Key: Rotate every 90 days (next: 2025-03-30)
# Supabase Service Key: On-demand (if compromised)
# ============================================
```

### 3.2 Share Access Securely

1. **Using 1Password (Recommended)**
   - Create shared vault: "Transfer2Read Production"
   - Add all team members who need access
   - Set permissions: "Can view and edit"

2. **Using LastPass**
   - Create secure note → Share → Enter team member emails
   - Set expiration (optional): None for permanent access

3. **Using Google Drive (Less Secure, NOT Recommended)**
   - If no password manager available, store in encrypted ZIP:
   ```bash
   # Create encrypted archive:
   zip -e transfer2read-secrets.zip secrets.txt
   # Enter strong password
   # Store ZIP in Google Drive with restricted access
   # Share password via separate channel (Signal, WhatsApp)
   ```

### 3.3 Never Commit Secrets to Git

**Verify .gitignore Coverage:**

```bash
cd /Users/dominhxuan/Desktop/Transfer2Read

# Check if .env files are ignored:
cat .gitignore | grep -E "\.env"

# Expected output:
# .env
# .env.*
# .env.local
# .env.*.local
# .env.production
```

**Check Git History for Leaked Secrets:**

```bash
# Search for .env files in git history:
git log --all --full-history -- "**/.env*" --oneline

# If any .env files (NOT .env.example) appear:
# - Verify they are template files (safe)
# - If actual secrets committed, consider using git filter-branch to remove
#   (CAUTION: rewrites history, coordinate with team)
```

**If Secrets Were Accidentally Committed:**

```bash
# DO NOT PANIC - follow these steps:

# 1. IMMEDIATELY ROTATE ALL EXPOSED KEYS
#    - Follow steps 1-2 above for OpenAI/Anthropic
#    - Revoke exposed keys immediately

# 2. Remove file from git (future commits only):
git rm --cached .env
git commit -m "Remove accidentally committed .env file"

# 3. (Optional) Remove from git history (advanced):
# WARNING: This rewrites history and requires force push
# Only do this if secrets were recently committed and team is small

git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/.env" \
  --prune-empty --tag-name-filter cat -- --all

git push origin --force --all
git push origin --force --tags

# 4. Inform team to re-clone repository (if history rewritten)
```

---

## Step 4: Update Production Environment Variables

### 4.1 Update Vercel (Frontend)

1. **Log in to Vercel Dashboard**
   - Navigate to: https://vercel.com/dashboard
   - Select Transfer2Read project

2. **Update Environment Variables**
   ```bash
   # In Vercel Dashboard → Settings → Environment Variables:

   # Add/Update:
   NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc... (ANON key, safe to be public)
   NEXT_PUBLIC_API_URL=https://api.transfer2read.com

   # Environment: Production
   ```

3. **Trigger Redeployment**
   ```bash
   # Option A: Via Vercel Dashboard
   # - Go to Deployments tab
   # - Click "..." menu on latest deployment → "Redeploy"

   # Option B: Via Git Push
   git commit --allow-empty -m "chore: trigger Vercel redeployment for new env vars"
   git push origin main
   ```

### 4.2 Update Railway (Backend API + Workers)

1. **Log in to Railway Dashboard**
   - Navigate to: https://railway.app/dashboard
   - Select Transfer2Read project

2. **Update Backend API Service Environment Variables**
   ```bash
   # In Railway Dashboard → Backend API Service → Variables:

   # Add/Update:
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_SERVICE_KEY=eyJhbGc... (SERVICE key, SECRET)
   OPENAI_API_KEY=sk-proj-...
   ANTHROPIC_API_KEY=sk-ant-...
   REDIS_URL=redis://... (auto-generated by Railway Redis plugin)
   FRONTEND_URL=https://transfer2read.com

   # Environment: Production
   ```

3. **Update Celery Worker Service (If Separate)**
   - Same environment variables as Backend API
   - Ensure Redis URL matches

4. **Trigger Redeployment**
   ```bash
   # Railway auto-redeploys when env vars change
   # Monitor deployment in Railway Dashboard → Deployments tab
   # Wait for "Deployed" status (usually 2-5 minutes)
   ```

---

## Step 5: Validation & Testing

### 5.1 Test OpenAI Integration

```bash
# SSH into Railway backend service (or use Railway CLI):
railway run bash

# Inside container, test OpenAI:
python3 << 'EOF'
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")
response = openai.models.list()
print("OpenAI models:", [m.id for m in response.data[:3]])
EOF

# Expected output:
# OpenAI models: ['gpt-4', 'gpt-3.5-turbo', ...]
```

### 5.2 Test Anthropic Integration

```bash
# Inside Railway container:
python3 << 'EOF'
import anthropic
import os

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
message = client.messages.create(
    model="claude-3-haiku-20240307",
    max_tokens=50,
    messages=[{"role": "user", "content": "Hello"}]
)
print("Anthropic response:", message.content[0].text)
EOF

# Expected output:
# Anthropic response: Hello! How can I help you today?
```

### 5.3 Test End-to-End Production Flow

```bash
# Test production frontend → backend → AI pipeline:

# 1. Register test user:
curl -X POST https://api.transfer2read.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "SecurePassword123!"}'

# 2. Upload PDF (requires auth token from step 1):
# - Visit https://transfer2read.com
# - Log in with test@example.com
# - Upload sample PDF
# - Verify conversion starts and completes

# 3. Check logs for API key usage:
# - Railway Dashboard → Backend Service → Logs
# - Search for "OpenAI API call" or "Anthropic API call"
# - Verify no 401 Unauthorized errors
```

---

## Step 6: Post-Rotation Checklist

**After completing rotation, verify:**

- [ ] New OpenAI API key created and stored in password manager
- [ ] New Anthropic API key created and stored in password manager
- [ ] Old keys revoked/deleted (if applicable)
- [ ] Vercel environment variables updated with new keys
- [ ] Railway environment variables updated with new keys
- [ ] Production deployment successful (no errors in logs)
- [ ] End-to-end test passed (upload → convert → download works)
- [ ] Usage limits configured on OpenAI dashboard
- [ ] Team members have access to password manager vault
- [ ] .gitignore verified to exclude .env files
- [ ] Git history checked for leaked secrets (none found)

---

## Troubleshooting

### Error: 401 Unauthorized from OpenAI

**Cause:** Invalid or revoked API key

**Fix:**
1. Verify key in password manager matches key in Railway/Vercel env vars
2. Check OpenAI Dashboard → API Keys → Verify key is active
3. Test key using curl command from Step 1.3
4. If key is invalid, create new key and repeat rotation steps

### Error: 401 Unauthorized from Anthropic

**Cause:** Invalid or deleted API key

**Fix:**
1. Verify key in password manager matches key in Railway env vars
2. Check Anthropic Console → Settings → Keys → Verify key exists
3. Test key using curl command from Step 2.3
4. If key is invalid, create new key and repeat rotation steps

### Error: Deployment Failed After Env Var Update

**Cause:** Railway/Vercel build failure due to missing dependencies or syntax errors

**Fix:**
1. Check Railway/Vercel deployment logs for specific error
2. Verify all required env vars are set (not just API keys)
3. Rollback to previous deployment if critical:
   ```bash
   # Vercel: Dashboard → Deployments → Previous deployment → Promote to Production
   # Railway: Dashboard → Deployments → Previous deployment → Redeploy
   ```
4. Fix issue and redeploy

### Usage Limits Exceeded

**Symptom:** OpenAI returns 429 Too Many Requests

**Fix:**
1. Check OpenAI Dashboard → Usage → Current month usage
2. If exceeded budget:
   - Increase monthly limit in Settings → Limits
   - Add payment method if not on file
3. If exceeded rate limit:
   - Implement exponential backoff in backend code (Story 7.1 task)
   - Reduce concurrent requests

---

## Security Best Practices

1. **Rotate Keys Regularly**
   - Schedule: Every 90 days
   - Set calendar reminder: March 30, June 30, September 30, December 30

2. **Never Share Keys in Plain Text**
   - Use password manager shared vaults
   - Never send keys via email, Slack, or SMS
   - If must share temporarily, use encrypted channel (Signal, 1Password share)

3. **Monitor API Usage**
   - Set up billing alerts on OpenAI/Anthropic dashboards
   - Review monthly usage reports
   - Investigate unexpected spikes (possible key leak)

4. **Audit Access**
   - Review password manager vault members quarterly
   - Remove access for ex-team members immediately

5. **Use Separate Keys for Dev/Staging/Production**
   - Dev: Lower rate limits, separate billing
   - Staging: Separate key for pre-production testing
   - Production: Highest security, monitored closely

---

## Next Steps

**After completing QW-3:**
1. ✅ Mark QW-3 as complete in quick-wins-plan-2025-12-26.md
2. Proceed to QW-4: Documentation Update for Production
3. Update sprint-status.yaml when all quick wins complete

**For production deployment (after QW-1, QW-2, QW-3):**
1. Deploy frontend to Vercel with production Supabase
2. Deploy backend to Railway with production API keys
3. Run end-to-end smoke test
4. Begin Epic 7 Story 7.1: Monitoring & Error Tracking

---

**Document Status:** ✅ Complete
**Last Reviewed:** 2025-12-30
**Next Review:** 2025-03-30 (90 days)
