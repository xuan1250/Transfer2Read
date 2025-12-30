# Transfer2Read

![Status](https://img.shields.io/badge/status-MVP%20Complete-green)
![Launch](https://img.shields.io/badge/launch-preparing-yellow)

AI-powered PDF to EPUB converter with intelligent layout analysis and structure recognition.

## Overview

Transfer2Read converts PDF documents into clean, readable EPUB files using advanced AI to analyze document structure, preserve formatting, and generate accurate tables of contents. Built with Next.js, FastAPI, and LangChain, powered by Supabase for authentication and storage.

## Architecture

**Frontend:** Next.js 15 (App Router) + shadcn/ui + Tailwind CSS  
**Backend:** FastAPI (Python 3.13) + LangChain AI integration  
**Database & Auth:** Supabase (PostgreSQL + Auth + Storage)  
**AI Models:** GPT-4o (layout analysis) + Claude 3 Haiku (text extraction)  
**Task Queue:** Celery + Redis  
**Deployment:** Vercel (frontend) + Railway (backend)

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js:** 24.12.0 LTS ([download](https://nodejs.org/))
- **Python:** 3.13.0 ([download](https://www.python.org/downloads/))
- **Docker Desktop:** Latest version ([download](https://www.docker.com/products/docker-desktop/))
- **Supabase Account:** Free tier ([sign up](https://supabase.com/))
- **Git:** For version control

## Setup Instructions

### 1. Supabase Project Setup

1. **Create Supabase Project:**
   - Go to [supabase.com](https://supabase.com/) and sign in/create account
   - Click "New Project"
   - Name your project: `transfer2read` or `transfer_app`
   - Select region closest to your target users
   - Wait for project provisioning (1-2 minutes)

2. **Configure Authentication:**
   - Navigate to **Authentication → Providers** in Supabase dashboard
   - Enable **Email/Password** provider (toggle ON)
   - Email confirmation is enabled by default

3. **Configure Social Authentication (Optional):**

   **Google OAuth:**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create new project or select existing one
   - Navigate to **APIs & Services → Credentials**
   - Click **Create Credentials → OAuth 2.0 Client ID**
   - Configure OAuth consent screen if prompted
   - Application type: **Web application**
   - Add Authorized redirect URI: `https://your-project.supabase.co/auth/v1/callback`
   - Copy **Client ID** and **Client Secret**
   - In Supabase dashboard: **Authentication → Providers → Google**
     - Toggle **Enable Google provider** to ON
     - Paste **Client ID** and **Client Secret**
     - Click **Save**

   **GitHub OAuth:**
   - Go to [GitHub Developer Settings](https://github.com/settings/developers)
   - Click **New OAuth App**
   - Application name: `Transfer2Read` (or your app name)
   - Homepage URL: `http://localhost:3000` (dev) or your production URL
   - Authorization callback URL: `https://your-project.supabase.co/auth/v1/callback`
   - Click **Register application**
   - Copy **Client ID**, then generate and copy **Client Secret**
   - In Supabase dashboard: **Authentication → Providers → GitHub**
     - Toggle **Enable GitHub provider** to ON
     - Paste **Client ID** and **Client Secret**
     - Click **Save**

   **Important Notes:**
   - OAuth redirect URI must match your Supabase project URL exactly
   - For production deployment, add production URL to authorized redirect URIs
   - Test OAuth flows after configuration using the Supabase Auth UI test feature

4. **Create Storage Buckets:**
   - Navigate to **Storage** section
   - Create bucket: `uploads` (set to **Private**)
   - Create bucket: `downloads` (set to **Private**)
   - These store user PDFs and generated EPUBs respectively

4. **Collect API Credentials:**
   - Go to **Settings → API**
   - Copy the following (you'll need these for `.env` files):
     - **Project URL** (`SUPABASE_URL`)
     - **anon/public key** (`SUPABASE_ANON_KEY`) - safe for frontend
     - **service_role key** (`SUPABASE_SERVICE_KEY`) - **KEEP SECRET**, backend only

**Note:** OAuth redirect URI format: `https://[PROJECT_REF].supabase.co/auth/v1/callback`
Find your PROJECT_REF in Supabase Settings → API → Project URL

### 2. Environment Configuration

**Root Directory:**
```bash
# Copy the example file
cp .env.example .env

# Edit .env and fill in your Supabase credentials + AI API keys
nano .env
```

**Frontend (Next.js):**
```bash
cd frontend
cp .env.local.example .env.local

# Edit and add your Supabase URL and Anon Key
nano .env.local
cd ..
```

**Backend (FastAPI):**
```bash
cd backend
cp .env.example .env

# Edit and add Supabase Service Role Key + AI API keys
nano .env
cd ..
```

⚠️ **Security Note:** NEVER commit `.env` files to Git! They're already in `.gitignore`.

### 3. Local Development Setup

**Backend Setup** (in `backend/` directory):
```bash
# Story 1.2 will create the FastAPI application
# For now, the directory exists but is empty
```

**Frontend Setup** (in `frontend/` directory):
```bash
# Story 1.3 will initialize the Next.js application
# For now, the directory exists but is empty
```

**Redis (Docker):**
```bash
# Story 1.2 will create docker-compose.yml for Redis
```

### 4. Running the Application

Full instructions will be available after Stories 1.2 (Backend), 1.3 (Frontend), and 1.4 (Workers) are complete.

## Project Structure

```
transfer_app/
├── .git/                      # Git repository
├── .gitignore                 # Git ignore patterns
├── .env.example               # Environment variable template
├── README.md                  # This file
├── docs/                      # Documentation files
│   ├── architecture.md        # System architecture
│   ├── prd.md                # Product requirements
│   ├── epics/                # Epic documentation
│   └── sprint-artifacts/     # Story files and tracking
├── frontend/                  # Next.js application (Story 1.3)
│   └── .env.local.example    # Frontend env template
├── backend/                   # FastAPI application (Story 1.2)
│   └── .env.example          # Backend env template
└── docker-compose.yml        # Redis container (Story 1.2)
```

## Documentation

- **[Architecture](docs/architecture.md):** System design, technology stack, ADRs
- **[Product Requirements](docs/prd.md):** Product vision and requirements
- **[UX Design](docs/ux-spec.md):** User experience specification
- **[Sprint Status](docs/sprint-artifacts/sprint-status.yaml):** Current sprint progress

## Development Workflow

1. **Story Development:** Work on stories in sprint order (see `sprint-status.yaml`)
2. **Code Standards:** Follow architecture patterns and coding standards in `docs/architecture.md`
3. **Testing:** All stories require tests (pytest for backend, Vitest for frontend)
4. **Review:** Code review required before marking stories complete

## Production Deployment

Transfer2Read is deployed using modern cloud platforms for automatic scaling and zero-downtime updates.

### Deployment Architecture

- **Frontend:** Vercel (Edge Network with global CDN)
- **Backend API:** Railway (Containerized FastAPI)
- **Worker:** Railway (Containerized Celery)
- **Redis:** Railway (Managed Redis for task queue)
- **Database + Auth + Storage:** Supabase (Managed PostgreSQL + Auth + Storage)

### Production URLs

**Live Application:**
```bash
# Frontend (Custom Domain)
https://transfer2read.com

# Backend API (Custom Domain)
https://api.transfer2read.com

# API Health Check
https://api.transfer2read.com/api/health

# API Documentation (Swagger)
https://api.transfer2read.com/docs
```

**Note:** Replace URLs above with actual production URLs after completing Quick Win QW-1 (Domain Purchase & DNS Setup). See `docs/sprint-artifacts/quick-wins-plan-2025-12-26.md` for domain configuration steps.

### Deployment Guide

**📖 For detailed deployment instructions, see:**

- **[Production Deployment Guide](docs/operations/production-deployment-guide.md)** - Step-by-step Vercel/Railway/Supabase setup
- **[Rollback Procedures](docs/operations/rollback-procedures.md)** - Emergency rollback and disaster recovery
- **[API Key Rotation Guide](docs/operations/api-key-rotation-guide.md)** - Rotate OpenAI/Anthropic keys quarterly
- **[Quick Wins Plan](docs/sprint-artifacts/quick-wins-plan-2025-12-26.md)** - Pre-launch preparation checklist

### Quick Deployment Checklist

**Pre-Launch Quick Wins (see `docs/sprint-artifacts/quick-wins-plan-2025-12-26.md`):**
- [ ] **QW-1:** Purchase domain and configure DNS (transfer2read.com, api.transfer2read.com)
- [ ] **QW-2:** Create production Supabase project (database + auth + storage)
- [ ] **QW-3:** Rotate API keys for production (OpenAI, Anthropic)
- [ ] **QW-4:** Update documentation (this README, deployment guides)
- [ ] **QW-5:** Compile beta user list (5-10 testers)

**Production Deployment:**
- [ ] Deploy frontend to Vercel with custom domain
- [ ] Deploy backend + worker to Railway
- [ ] Configure environment variables on all platforms (.env.production.example)
- [ ] Verify health endpoints (curl https://api.transfer2read.com/api/health)
- [ ] Test end-to-end functionality (register → upload → convert → download)
- [ ] Confirm CI/CD pipeline works (auto-deploy on push to main)

### Environment Variables

**Frontend (Vercel):**
```bash
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

**Backend (Railway - API and Worker services):**
```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGc...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
REDIS_URL=redis://railway-redis:6379  # Auto-provided by Railway
CELERY_BROKER_URL=redis://railway-redis:6379/0
CELERY_RESULT_BACKEND=redis://railway-redis:6379/0
ENVIRONMENT=production
```

### CI/CD Pipeline

GitHub Actions automatically runs tests on every pull request:
- **Backend Tests:** pytest with coverage
- **Frontend Build:** Next.js production build
- **Linting:** Code quality checks

Deployments are automatic:
- **Push to main → Auto-deploy** to Vercel (frontend) and Railway (backend)
- **Pull requests → Preview deployments** on Vercel

### Troubleshooting Deployment

**Frontend not loading:**
1. Check Vercel deployment logs
2. Verify environment variables are set
3. Test API endpoint directly

**Backend 500 errors:**
1. Check Railway logs for errors
2. Verify Supabase credentials
3. Test health endpoint: `/api/health`

**Worker not processing:**
1. Check Railway worker logs
2. Verify Redis connection
3. Ensure environment variables match API service

For detailed troubleshooting, see [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md#troubleshooting)



## Technology Stack Details

**Frontend:**
- Next.js 15 (App Router)
- React 19
- TypeScript
- shadcn/ui components
- Tailwind CSS
- Supabase JS Client

**Backend:**
- FastAPI (async Python web framework)
- Supabase Python Client
- LangChain (AI orchestration)
- OpenAI SDK (GPT-4o)
- Anthropic SDK (Claude 3 Haiku)
- Celery (task queue)
- Redis (message broker)

**Database & Services:**
- Supabase PostgreSQL
- Supabase Authentication
- Supabase Storage
- Row Level Security (RLS) policies

## Contributing

Development follows the BMAD sprint methodology:
1. Epics are broken into user stories
2. Stories are developed sequentially by priority
3. Each story requires acceptance criteria completion
4. Code review before story marked complete

## License

(License information TBD)

## Support

For questions or issues:
- Check `docs/architecture.md` for technical guidance
- Review story files in `docs/sprint-artifacts/` for implementation details
- Consult [Supabase documentation](https://supabase.com/docs) for platform questions

---

**Current Status:** Story 1.1 Complete - Project foundation established with Supabase configuration and directory structure.

**Next Steps:** Story 1.2 (Backend FastAPI setup) → Story 1.3 (Frontend Next.js setup)
# CI/CD Test
