# Story 1.5: Vercel + Railway Deployment Configuration

Status: done

## Story

As a **DevOps Engineer**,
I want **to configure deployment to Vercel (frontend) and Railway (backend + workers)**,
So that **the application is production-ready with managed Supabase services.**

## Acceptance Criteria

1. **Vercel Project:** Frontend connected to GitHub repo
   - Production and Preview environments configured
   - Environment variables: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_URL`
2. **Railway Project:** Two services deployed:
   - **API Service:** FastAPI backend with Supabase keys, AI API keys
   - **Worker Service:** Celery worker with same environment
   - **Redis Service:** Managed Redis for Celery broker
3. **Supabase Production:** Production Supabase project (separate from dev)
4. **CORS Configuration:** Backend allows Vercel production domain
5. **Health Check:** Public URLs accessible:
   - Frontend: `https://transfer2read.vercel.app`
   - Backend: `https://transfer-api.railway.app/api/health` → `200 OK`
6. **Secrets Management:** All API keys stored in Railway secrets (not committed)
7. **CI/CD:** GitHub Actions runs tests on PR before deployment

## Tasks / Subtasks

- [x] Task 1: Create Production Supabase Project (AC: #3)
  - [x] 1.1: Create new Supabase project for production environment
  - [x] 1.2: Configure storage buckets (`uploads`, `downloads`) with RLS policies
  - [x] 1.3: Enable Email/Password authentication provider
  - [x] 1.4: Document production credentials in secure location (not in Git)
  - [x] 1.5: Update backend `.env.example` with production credential placeholders

- [x] Task 2: Set up Vercel Frontend Deployment (AC: #1)
  - [x] 2.1: Connect GitHub repository to Vercel account
  - [x] 2.2: Configure project settings:
    - Root directory: `frontend/`
    - Framework preset: Next.js
    - Build command: `npm run build`
    - Output directory: `.next`
  - [x] 2.3: Set environment variables for production:
    - `NEXT_PUBLIC_SUPABASE_URL`: Production Supabase URL
    - `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Production anon key
    - `NEXT_PUBLIC_API_URL`: Railway backend URL (TBD in Task 3)
  - [x] 2.4: Configure preview deployments for pull requests
  - [x] 2.5: Verify deployment: Visit Vercel URL and confirm frontend loads

- [x] Task 3: Set up Railway Backend Services (AC: #2, #6)
  - [x] 3.1: Create new Railway project
  - [x] 3.2: Add Redis service (managed Redis by Railway)
  - [x] 3.3: Deploy Backend API service:
    - Root directory: `backend/`
    - Dockerfile build
    - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - [x] 3.4: Set API service environment variables:
    - `SUPABASE_URL`: Production Supabase URL
    - `SUPABASE_SERVICE_KEY`: Production service role key
    - `OPENAI_API_KEY`: OpenAI API key
    - `ANTHROPIC_API_KEY`: Anthropic API key
    - `REDIS_URL`: Railway Redis internal URL (auto-provided)
    - `CELERY_BROKER_URL`: Same as REDIS_URL
    - `CELERY_RESULT_BACKEND`: Same as REDIS_URL
  - [x] 3.5: Deploy Worker service:
    - Same root directory and Dockerfile as API
    - Start command: `celery -A app.worker worker --loglevel=info`
    - Same environment variables as API service
  - [x] 3.6: Note Railway API public URL and update Vercel's `NEXT_PUBLIC_API_URL`

- [x] Task 4: Configure CORS for Production (AC: #4)
  - [x] 4.1: Update `backend/app/main.py` CORS middleware
  - [x] 4.2: Add Vercel production domain to allowed origins
  - [x] 4.3: Ensure credentials are allowed for cookie-based auth
  - [x] 4.4: Commit CORS changes and redeploy backend to Railway

- [x] Task 5: Verify Production Deployment (AC: #5)
  - [x] 5.1: Test backend health endpoint: `GET https://transfer-api.railway.app/api/health`
  - [x] 5.2: Verify response includes Supabase and Redis connection status
  - [x] 5.3: Visit frontend URL: `https://transfer2read.vercel.app`
  - [x] 5.4: Verify frontend loads correctly with Professional Blue theme
  - [x] 5.5: Test frontend-backend connectivity (check browser console for 200 OK)
  - [x] 5.6: Verify Celery worker is running (check Railway logs)

- [x] Task 6: Set up CI/CD with GitHub Actions (AC: #7)
  - [x] 6.1: Create `.github/workflows/ci.yml` workflow file
  - [x] 6.2: Configure workflow triggers: `pull_request` and `push to main`
  - [x] 6.3: Add backend test job:
    - Set up Python 3.12.9
    - Install dependencies
    - Run `pytest` with coverage
  - [x] 6.4: Add frontend test job:
    - Set up Node.js 24.x
    - Install dependencies
    - Run `npm run test:ci`
  - [x] 6.5: Configure deployment step (on push to main):
    - Vercel auto-deploys via GitHub integration
    - Railway auto-deploys via GitHub integration (verify in Railway settings)
  - [x] 6.6: Test workflow: Create PR and verify tests run successfully

- [x] Task 7: Create Deployment Documentation (AC: ALL)
  - [x] 7.1: Update README.md with deployment section
  - [x] 7.2: Document production URLs
  - [x] 7.3: Document environment variable requirements for Vercel and Railway
  - [x] 7.4: Create troubleshooting guide for common deployment issues
  - [x] 7.5: Document rollback procedure if deployment fails

## Dev Notes

### Architecture Context

**Deployment Architecture (from Architecture 2025-12-01):**
- **Frontend Deployment:** Vercel (Edge Network with automatic HTTPS and CDN)
- **Backend API + Worker:** Railway (Containers, scale independently)
  - API container: FastAPI service handling HTTP requests
  - Worker container: Celery worker processing conversion jobs
- **Redis:** Managed Redis on Railway for Celery message broker
- **Database + Auth + Storage:** Fully managed by Supabase

**Technology Stack:**
- Frontend: Next.js 15.0.3 deployed via Vercel
- Backend: FastAPI 0.122.0 + Python 3.12.9 containerized on Railway
- Message Broker: Redis 8.4.0 (Railway managed)
- Database/Auth/Storage: Supabase (managed PostgreSQL + Auth + Storage)
- AI APIs: OpenAI (GPT-4o) + Anthropic (Claude 3 Haiku)

**Zero-Downtime Deployment:**
- Railway uses blue-green deployment strategy
- Vercel uses edge network caching for instant rollbacks
- Health checks ensure services are ready before traffic switching

### Deployment Workflow Sequence

**Initial Setup Flow:**
```
1. Create Production Supabase Project
   ├── Configure storage buckets
   ├── Enable authentication
   └── Document credentials

2. Deploy to Vercel (Frontend)
   ├── Connect GitHub repo
   ├── Configure build settings
   ├── Set environment variables (partial - missing API URL)
   └── Deploy and verify

3. Deploy to Railway (Backend + Worker)
   ├── Create Railway project
   ├── Add Redis service
   ├── Deploy API service
   ├── Deploy Worker service
   ├── Configure environment variables
   └── Note public API URL

4. Update Vercel Environment Variables
   └── Set NEXT_PUBLIC_API_URL to Railway API URL

5. Configure CORS
   ├── Add Vercel domain to backend CORS
   └── Redeploy backend

6. Verify Full Integration
   ├── Test health endpoint
   ├── Test frontend-backend connectivity
   └── Verify worker is processing

7. Setup CI/CD
   └── Create GitHub Actions workflow
```

### Project Structure Notes

**Deployment Configuration Files:**
```
transfer_app/
├── .github/
│   └── workflows/
│       └── ci.yml                 # NEW: CI/CD workflow
├── frontend/
│   ├── vercel.json                # Optional: Vercel config
│   └── .env.local                 # Dev only (not deployed)
├── backend/
│   ├── Dockerfile                 # NEW: Container definition
│   ├── .env                       # Dev only (not deployed)
│   └── .env.example               # Update with prod placeholders
├── docker-compose.yml             # Dev only (not used in production)
└── README.md                      # Update with deployment docs
```

**New Files to Create:**
- `backend/Dockerfile` - Container definition for Railway deployment
- `.github/workflows/ci.yml` - CI/CD pipeline configuration
- `.dockerignore` - Exclude unnecessary files from Docker build

### Environment Variables Mapping

**Development vs. Production:**

| Variable | Dev (Local) | Production (Railway/Vercel) |
|----------|------------|----------------------------|
| `SUPABASE_URL` | Dev project URL | **Production project URL** |
| `SUPABASE_ANON_KEY` | Dev anon key | **Production anon key** |
| `SUPABASE_SERVICE_KEY` | Dev service key | **Production service key** |
| `REDIS_URL` | `redis://localhost:6379` | Railway internal URL (auto) |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Railway public API URL |

**Security Best Practices:**
- Never commit real credentials to Git
- Use `.env.example` with placeholders only
- Store production secrets in platform secret managers (Vercel/Railway)
- Rotate secrets quarterly

### Dockerfile Requirements

**Backend Dockerfile Pattern:**
```dockerfile
FROM python:3.12.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app ./app

# Railway provides $PORT environment variable
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

**Worker Variant:**
- Same Dockerfile, different start command in Railway settings
- Command: `celery -A app.worker worker --loglevel=info`

### CORS Configuration

**Current CORS (from Story 1.2):**
```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",  # Dev port variance
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production CORS (Add in This Story):**
```python
allow_origins=[
    "http://localhost:3000",
    "http://localhost:3001",
    "https://transfer2read.vercel.app",  # Production
    "https://*.vercel.app",  # Preview deployments
],
```

### CI/CD Workflow Pattern

**GitHub Actions Workflow Structure:**
```yaml
name: CI/CD Pipeline

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12.9'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '24'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run tests
        run: |
          cd frontend
          npm run test:ci
```

### Verification Checklist

**Backend Health Check Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2025-12-04T10:30:00Z"
}
```

**Frontend Verification:**
- Page loads without errors
- Professional Blue theme visible
- No console errors
- TopBar component renders

**Integration Verification:**
- Frontend can call backend health endpoint (no CORS errors)
- Backend logs show incoming requests
- Worker logs show task consumption

### References

- [Source: docs/architecture.md#Deployment-Architecture] - Vercel + Railway deployment strategy
- [Source: docs/architecture.md#ADR-002] - Supabase as unified backend platform
- [Source: docs/architecture.md#Environment-Configuration] - Environment variable setup
- [Source: docs/epics.md#Story-1.5] - Original acceptance criteria
- [Source: docs/sprint-artifacts/tech-spec-epic-1.md#Story-1.5] - Epic tech spec deployment details
- [Vercel Documentation](https://vercel.com/docs) - Next.js deployment
- [Railway Documentation](https://docs.railway.app/) - Container deployment
- [GitHub Actions Documentation](https://docs.github.com/en/actions) - CI/CD workflows

### Learnings from Previous Story

**From Story 1-4-celery-worker-ai-sdk-setup (Status: done):**

- **Celery Infrastructure Complete:**
  - Celery 5.5.3 configured with Redis backend
  - Worker entrypoint `backend/app/worker.py` running successfully
  - LangChain AI libraries (OpenAI + Anthropic) integrated
  - Test AI task created and verified working

- **Files Created for Deployment:**
  - `backend/app/core/celery_app.py` - Celery configuration
  - `backend/app/worker.py` - Worker entrypoint
  - `backend/app/tasks/ai_tasks.py` - Task definitions
  - `docker-compose.yml` - Worker service added

- **Environment Variables Established:**
  - `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
  - `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
  - `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
  - **Action for this story:** All these variables need to be configured in Railway

- **Docker Compose Pattern for Worker:**
  ```yaml
  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.worker worker --loglevel=info
    environment:
      - REDIS_URL=redis://redis:6379
      # ... other env vars
    depends_on:
      - redis
  ```
  **Note:** Railway will use similar pattern but with managed Redis

- **Backend API Structure:**
  - Health check endpoint: `GET /api/health`
  - Test AI endpoints: `POST /api/v1/test-ai`, `GET /api/v1/test-ai/{task_id}`
  - CORS configured for `localhost:3000` and `localhost:3001`
  - **Action for this story:** Add production domains to CORS

- **Technical Deviations Documented:**
  - Python 3.12.9 used (not 3.13.0 spec)
  - LangChain version adjusted for compatibility
  - **Action for this story:** Ensure Railway uses Python 3.12.9 image

- **Testing Patterns Established:**
  - Manual verification via API endpoints
  - Worker logs for debugging
  - Health check for service connectivity
  - **Action for this story:** Add these checks to CI/CD pipeline

- **Pending Integration:**
  - Worker successfully processes test AI tasks locally
  - Ready for production deployment with Railway managed Redis
  - API endpoints ready to be exposed via Railway public URL

**Key Integration Points for This Story:**

1. **Dockerfile Creation:** Need to create `backend/Dockerfile` using Python 3.12.9 base image
2. **Worker Deployment:** Use exact command from `docker-compose.yml` worker service
3. **Environment Variables:** Migrate all variables from `.env` to Railway secrets
4. **Redis Migration:** Replace `localhost` Redis with Railway managed Redis URL
5. **Health Check:** Extend to verify worker connectivity (optional enhancement)

**Files to Create/Modify:**
- NEW: `backend/Dockerfile` - Container definition
- NEW: `.github/workflows/ci.yml` - CI/CD pipeline
- MODIFY: `backend/app/main.py` - Add production CORS origins
- MODIFY: `README.md` - Deployment documentation
- MODIFY: `backend/.env.example` - Production credential placeholders

**Patterns to Follow:**
- Use Railway's automatic  `$PORT` environment variable
- Keep worker and API services in sync (same environment)
- Test locally with Docker before Railway deployment
- Document all production URLs for team reference

### Known Constraints

**Deployment Requirements:**
- GitHub repository with main branch protection
- Vercel account (free tier sufficient for MVP)
- Railway account (Developer plan ~$5/month)
- Production Supabase project (free tier sufficient for dev/staging)
- Valid API keys for OpenAI and Anthropic

**Service Dependencies:**
- Worker service depends on Redis service (Railway manages startup order)
- Backend API depends on Supabase connectivity
- Frontend depends on backend API URL (configure after Railway deployment)

**Performance Considerations:**
- Railway cold start time: ~10-30 seconds for API/Worker
- Vercel Edge Network: Instant global availability
- Redis managed by Railway: Auto-scaling enabled

**Cost Estimates (MVP):**
- Vercel: Free tier (sufficient for development)
- Railway: ~$5/month (Developer plan)
- Supabase: Free tier (500MB database, 1GB storage)
- OpenAI API: Pay-per-use (~$10-50/month for development testing)
- Anthropic API: Pay-per-use (~$5-20/month for fallback usage)

### Prerequisites

- Story 1.1: Project initialization ✓ (directory structure exists)
- Story 1.2: Backend FastAPI & Supabase integration ✓ (health check ready)
- Story 1.3: Frontend Next.js & Supabase client ✓ (deployable frontend)
- Story 1.4: Celery worker & AI SDK setup ✓ (worker ready for deployment)

### Change Log

- **2025-12-04:** Story drafted by SM agent (xavier) using create-story workflow in #yolo mode
- **Source:** Epic 1, Story 1.5 from epics.md
- **Context:** Built on completed infrastructure from Stories 1.1-1.4, integrates all previous learnings for production deployment

## Dev Agent Record

### Context Reference

- Story Context: docs/sprint-artifacts/1-5-vercel-railway-deployment-configuration.context.xml

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

**2025-12-04 - Automated Deployment Configuration Complete:**

✅ **Infrastructure Files Created:**
- `backend/Dockerfile` - Production container definition using Python 3.12.9
  - Supports both API and Worker deployments with different start commands
  - Includes PyMuPDF system dependencies for PDF processing
  - Tested with Docker build - successful ✅
- `backend/.dockerignore` - Optimized build context (excludes tests, .env, etc.)
- `.github/workflows/ci.yml` - CI/CD pipeline for automated testing
  - Backend tests: pytest with coverage on Python 3.12.9
  - Frontend tests: Next.js build validation on Node.js 24.x
  - Triggers on PR and push to main

✅ **Documentation Created:**
- `docs/DEPLOYMENT_GUIDE.md` - Comprehensive 14KB deployment guide with:
  - Step-by-step Supabase production project setup
  - Vercel frontend deployment instructions
  - Railway backend + worker deployment instructions
  - Environment variable configuration tables
  - Troubleshooting section
  - Rollback procedures
  - Security best practices
- `README.md` - Added production deployment section with:
  - Architecture overview
  - Quick deployment checklist
  - Environment variables reference
  - Troubleshooting quick reference
- `backend/.env.example` - Updated with production credential placeholders

✅ **CORS Already Configured:**
- Verified `backend/app/main.py` already includes production Vercel domain
- Line 24: `https://transfer2read.vercel.app` in allowed origins
- Task 4.1-4.3 were already complete from previous story

✅ **Docker Build Verification:**
- Successfully built image `transfer2read-test:latest`
- Build time: ~50 seconds
- Image includes all required dependencies
- No critical warnings (only JSON args recommendation for CMD)

✅ **Git Commit Complete:**
- Committed all deployment files to Git (commit 780424d)
- Files committed:
  - `.github/workflows/ci.yml` (CI/CD pipeline)
  - `backend/Dockerfile` (production container)
  - `backend/.dockerignore` (build optimization)
  - `docs/DEPLOYMENT_GUIDE.md` (deployment manual)
  - `backend/.env.example` (updated with production placeholders)
  - `README.md` (added deployment section)
  - Story file and sprint status updates
- Ready for GitHub push when user is ready to trigger CI/CD

**Manual Steps Remaining (User Action Required):**

The following tasks require manual configuration on external platforms and cannot be automated:

🔲 **Task 1** (Subtasks 1.1-1.4): Create production Supabase project
- Requires Supabase dashboard access
- Instructions in DEPLOYMENT_GUIDE.md §Task 1

🔲 **Task 2** (All subtasks): Vercel frontend deployment  
- Requires Vercel account authentication
- Requires GitHub repo connection approval
- Instructions in DEPLOYMENT_GUIDE.md §Task 2

🔲 **Task 3** (All subtasks): Railway backend deployment
- Requires Railway account authentication  
- Requires service configuration in Railway dashboard
- Instructions in DEPLOYMENT_GUIDE.md §Task 3

🔲 **Task 4.4**: Commit and redeploy (after user verifies CORS settings)

🔲 **Task 5** (All subtasks): End-to-end verification
- Requires deployed services to test
- Instructions in DEPLOYMENT_GUIDE.md §Task 5

🔲 **Task 6.6**: Test CI/CD workflow
- Create test PR to verify GitHub Actions
- Instructions in DEPLOYMENT_GUIDE.md §Task 6

**Next Steps for User:**
1. Follow `docs/DEPLOYMENT_GUIDE.md` to complete manual platform configuration
2. Start with Task 1 (Supabase), then Task 2 (Vercel), then Task 3 (Railway)
3. Verify deployments with Task 5 checks
4. Test CI/CD with Task 6.6
5. Mark remaining subtasks complete as you finish them
6. Update story status to 'review' when all tasks complete

---

**2025-12-11 - STORY COMPLETE ✅**

All tasks successfully completed and verified in production:

**✅ Deployment Accomplished:**
- Production Supabase project configured
- Vercel frontend deployed: https://transfer2-read.vercel.app
- Railway backend + worker deployed: https://api-production-9d15.up.railway.app
- End-to-end verification passed
- CI/CD pipeline tested and working

**✅ Challenges Resolved:**
- Fixed Next.js security vulnerability (15.0.3 → 15.5.7)
- Fixed React dependency conflicts with .npmrc
- Fixed Railway Worker Redis connection
- Fixed GitHub Actions PYTHONPATH for backend tests

**✅ Final Status:**
- Epic 1 (Core Infrastructure): COMPLETE
- All 5 stories (1-1 through 1-5): DONE
- Production application: LIVE and operational
- Ready for Epic 2 development

**Story marked DONE in sprint-status.yaml** ✅

### File List

**New Files Created:**
- `backend/Dockerfile` - Production container definition
- `backend/.dockerignore` - Docker build exclusions
- `.github/workflows/ci.yml` - CI/CD pipeline configuration
- `docs/DEPLOYMENT_GUIDE.md` - Comprehensive deployment manual

**Modified Files:**
- `backend/.env.example` - Added production credential placeholders
- `README.md` - Added production deployment section
- `docs/sprint-artifacts/sprint-status.yaml` - Marked story in-progress
- `docs/sprint-artifacts/1-5-vercel-railway-deployment-configuration.md` - This file (updated tasks)
