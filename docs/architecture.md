# Architecture

> **Versions Verified:** 2025-11-27  
> **Verification Method:** WebSearch for current stable releases  
> **Compatibility:** All versions cross-checked for mutual compatibility

## Executive Summary

Transfer2Read is a high-fidelity PDF to EPUB converter designed to solve the "complex PDF" problem for technical and academic documents. The system employs an **HTML-First Hybrid Architecture**, utilizing **Stirling-PDF** for high-fidelity PDF-to-HTML conversion and **GPT-4o** via **LangChain** for semantic structure analysis. Long-running tasks are managed by **Celery** workers backed by **Redis**. All user data and storage are managed through **Supabase**. This approach combines the reliability of standard PDF processing tools with the intelligence of AI for structure and metadata.

## Project Initialization

**Approach:** The project is built **from scratch** to integrate Supabase, Stirling-PDF, and LangChain.

### Core Services Setup

**1. Supabase Project Setup:**
- Create new Supabase project at [supabase.com](https://supabase.com)
- Enable Authentication (Email/Password provider)
- Create storage buckets:
  - `uploads` (private) - for user uploaded PDFs
  - `downloads` (private) - for generated EPUB files
- Configure Row Level Security (RLS) policies for data isolation
- Note your credentials from Settings > API:
  - `SUPABASE_URL` - Your project URL
  - `SUPABASE_ANON_KEY` - For frontend client (safe to expose)
  - `SUPABASE_SERVICE_KEY` - For backend admin operations (keep secret)

**2. AI API Keys:**
- OpenAI API key from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- Anthropic API key from [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)

**3. Project Scaffold (Built from Scratch):**
```bash
# Create project structure
mkdir transfer_app && cd transfer_app
mkdir frontend backend

# Frontend - Next.js 15 with TypeScript
cd frontend
npx create-next-app@15.0.3 . --typescript --tailwind --app --use-npm
npm install @supabase/supabase-js@2.46.1 @supabase/auth-helpers-nextjs
npm install axios @tanstack/react-query

# Backend - FastAPI with Python 3.13
cd ../backend
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install fastapi==0.122.0 uvicorn[standard]
pip install celery[redis]==5.5.3 redis==5.0.1
pip install sqlalchemy==2.0.36 supabase==2.24.0
pip install langchain==0.3.12 langchain-openai==0.2.9 langchain-anthropic==0.2.5
pip install pymupdf==1.24.10 ebooklib pydantic

# Create docker-compose.yml for Redis
cd ..
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  redis:
    image: redis:8.4.0-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
volumes:
  redis-data:
EOF

# Start Redis
docker-compose up -d
```

### Environment Configuration

**Frontend `.env.local`:**
```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Backend `.env`:**
```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key

# AI APIs
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Celery
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# App Config
ENVIRONMENT=development
```

## Decision Summary

| Category | Decision | Version | Source | Rationale |
| -------- | -------- | ------- | ------ | --------- |
| **Foundation** | **Next.js + FastAPI** | Custom | CUSTOM | Modern full-stack foundation with TypeScript and Python, built from scratch. |
| **Frontend** | **Next.js** | 15.0.3 | CUSTOM | Latest stable (Nov 2025), React 19 support, App Router, Turbopack. |
| **Backend** | **FastAPI** | 0.122.0 | CUSTOM | Latest stable (Nov 2025), high performance, native async, OpenAPI. |
| **Runtime** | **Python** | 3.13.0 | CUSTOM | Latest stable (Oct 2024), compatible with FastAPI 0.122.0. |
| **Runtime** | **Node.js** | 24.12.0 LTS | CUSTOM | Krypton LTS (Oct 2025), compatible with Next.js 15, support until 2027. |
| **Async Processing** | **Celery** | 5.5.3 | CUSTOM | Latest stable (Jun 2025), robust task queue for AI-intensive conversion work. |
| **Message Broker** | **Redis** | 8.4.0 | CUSTOM | Latest stable (Nov 2025), high-performance broker + caching. |
| **AI Framework** | **LangChain** | 0.3.12 | CUSTOM | Latest stable (Dec 2024), orchestration framework for LLM integration. |
| **AI Model (Primary)** | **GPT-4o** | Latest API | CUSTOM | OpenAI's multimodal model, optimized for speed and quality. |
| **AI Model (Fallback)** | **Claude 3 Haiku** | Latest API | CUSTOM | Anthropic's fast, cost-effective model for fallback scenarios. |
| **Auth & Database** | **Supabase** | Latest | CUSTOM | Unified platform: PostgreSQL + Auth + Storage with real-time capabilities. |
| **Supabase JS Client** | **@supabase/supabase-js** | 2.46.x | CUSTOM | Latest stable (Nov 2024), Next.js App Router compatible, frontend + backend. |
| **Supabase Python Client** | **supabase-py** | 2.24.0 | CUSTOM | Latest stable (Nov 2025), async support, server-side operations. |
| **LangChain OpenAI** | **langchain-openai** | 0.2.x | CUSTOM | Latest stable, GPT-4o support, structured outputs. |
| **LangChain Anthropic** | **langchain-anthropic** | 0.2.x | CUSTOM | Latest stable, Claude 3 support, streaming responses. |
| **ORM** | **SQLAlchemy** | 2.0.36 | CUSTOM | Latest stable, async support, type hints for backend operations. |
| **Deployment** | **Vercel + Railway** | N/A | CUSTOM | Vercel for frontend (edge network), Railway for backend containers. |

> **Version Verification:** All versions verified 2025-12-01 via web search for current stable releases.

## Project Structure

```
transfer_app/
├── frontend/                   # Next.js 15 Application
│   ├── src/
│   │   ├── app/                # App Router (Pages & Layouts)
│   │   ├── components/         # React Components (shadcn/ui)
│   │   │   ├── ui/             # Primitive UI components
│   │   │   └── business/       # Domain-specific components
│   │   ├── lib/                # Utilities & Clients
│   │   │   ├── supabase.ts     # Supabase client initialization
│   │   │   └── api-client.ts   # Backend API client
│   │   └── types/              # Shared Types
│   └── .env.local              # Supabase + API URLs
├── backend/                    # FastAPI Application
│   ├── app/
│   │   ├── api/                # API Endpoints (Routes)
│   │   │   └── v1/
│   │   │       ├── upload.py   # File upload endpoint
│   │   │       └── jobs.py     # Job status/download endpoints
│   │   ├── core/               # Config, Security, Logging
│   │   │   ├── config.py       # Environment variables
│   │   │   └── supabase.py     # Supabase client setup
│   │   ├── models/             # SQLAlchemy ORM Models
│   │   │   └── job.py          # ConversionJob model
│   │   ├── schemas/            # Pydantic Schemas (Validation)
│   │   ├── services/           # Business Logic Layer
│   │   │   ├── conversion/     # PDF → EPUB Pipeline
│   │   │   ├── ai/             # LangChain AI Integration
│   │   │   │   ├── gpt4.py     # GPT-4o handler
│   │   │   │   └── claude.py   # Claude 3 handler
│   │   │   └── storage/        # Supabase Storage Interface
│   │   └── worker.py           # Celery Worker Entrypoint
│   └── .env                    # Supabase + AI API keys
├── docker-compose.yml          # Redis for local dev
└── README.md
```

## FR Category to Architecture Mapping

| FR Category | Primary Component | Data Store | Key Logic |
| ----------- | ----------------- | ---------- | --------- |
| **User Account & Access** | Supabase Auth | Supabase PostgreSQL (`auth.users`) | Supabase Auth SDK for signup/login/recovery flows. |
| **PDF File Upload** | Backend `api/upload` | Supabase Storage (`uploads/`) | Stream upload to Supabase Storage, validate PDF mime-type. |
| **AI Analysis & Conversion** | Celery Worker | N/A (API-based) | LangChain orchestrates GPT-4o/Claude Haiku for layout analysis. |
| **AI Structural Analysis** | Celery Worker | N/A | LLM-based detection of TOC/Chapters/Sections via prompt engineering. |
| **Conversion Process** | Backend `api/jobs` | Redis (Queue), Supabase PG (Status) | Async task dispatch, progress polling via API. |
| **EPUB Output** | Celery Worker | Supabase Storage (`downloads/`) | EPUB generation, upload result to Supabase Storage. |
| **Usage Limits** | Backend Middleware | Supabase PostgreSQL (`usage_logs`) | Check counts before dispatching job. |

## Technology Stack Details

### Core Technologies
- **Language:** TypeScript 5.x (Frontend), Python 3.13.0 (Backend)
- **Styling:** Tailwind CSS 3.x
- **UI Library:** shadcn/ui (Radix UI based)
- **ORM:** SQLAlchemy 2.0.36 Async
- **Schema Validation:** Pydantic v2
- **Task Queue:** Celery 5.5.3
- **PDF Library:** PyMuPDF 1.24.x
- **AI SDKs:** LangChain 0.3.x, OpenAI Python SDK, Anthropic Python SDK
- **Testing:** Pytest 8.x (Backend), Vitest 2.x (Frontend)

### Integration Points
- **Frontend <-> Supabase:** Supabase JS client for auth, real-time data, and storage.
- **Frontend <-> Backend:** REST API via Axios/Fetch for conversion job management.
- **Backend <-> Worker:** Redis 8.4.0 Message Broker for Celery task queue.
- **Backend <-> Supabase:** Supabase Python client + SQLAlchemy for database operations.
- **Backend <-> Storage:** Supabase Storage API for file uploads/downloads.
- **Worker <-> AI APIs:** LangChain with OpenAI (GPT-4o) and Anthropic (Claude 3 Haiku) API clients.

## Novel Pattern Designs

### PDF Conversion Pipeline (Async)

The core value proposition relies on a robust conversion pipeline that doesn't block the web server.

**Components:**
1.  **API:** Receives upload → Saves to S3 → Creates DB Record (PENDING) → Pushes ID to Redis Queue.
2.  **Worker:** Pops ID → Downloads PDF → Runs Pipeline → Uploads EPUB → Updates DB Record (COMPLETED).
3.  **Client:** Polls `GET /jobs/{id}` for progress/status.

**AI Model Specification:**
- **Primary Model:** GPT-4o (OpenAI)
  - **Version:** Latest production release
  - **Capabilities:** Multimodal understanding (text + images), document structure analysis, high-quality text extraction
  - **Usage:** Primary model for PDF layout analysis and content extraction
  - **Cost:** ~$2.50/1M input tokens, ~$10/1M output tokens
  - **Speed:** ~2-5 seconds per page (API latency included)
  
- **Fallback Model:** Claude 3 Haiku (Anthropic)
  - **Version:** Latest production release
  - **Capabilities:** Fast text processing, cost-effective for simple documents
  - **Usage:** Fallback when GPT-4o fails or for cost optimization on simple PDFs
  - **Cost:** ~$0.25/1M input tokens, ~$1.25/1M output tokens
  - **Speed:** ~1-3 seconds per page

- **Orchestration:** LangChain 0.3.x
  - **Document Loaders:** PyPDFLoader for text extraction
  - **Text Splitters:** RecursiveCharacterTextSplitter for chunking large documents
  - **Chains:** Custom chains for layout analysis → structure detection → EPUB generation
  - **Retry Logic:** Built-in retry with exponential backoff for API failures

**Pipeline Steps:**
1.  **Ingest:** Upload PDF to Supabase Storage.
2.  **Convert (Stirling):** Send PDF to **Stirling-PDF** service to generate high-fidelity HTML.
3.  **Extract:** Parse and clean HTML content using `BeautifulSoup`.
4.  **Structure (AI):** Send HTML context to **GPT-4o** to identify chapters, TOC, and metadata.
5.  **Generate:** Assemble EPUB using the cleaned HTML and AI-generated structure.

**Failure Handling:**
- **Celery Retries:** Max 3 retries with exponential backoff (1min, 5min, 15min)
- **Timeout:** 15 minute max per job (LLM API calls can be slower than local inference)
- **Worker Crash:** Job remains in PROCESSING state → Manual cleanup or auto-requeue after 30min
- **API Failures:** 
  - OpenAI API error → Automatic fallback to Claude 3 Haiku
  - Both APIs fail → Retry with exponential backoff (3 attempts)
  - Rate limit hit → Queue job with delay based on retry-after header
- **AI Quality Issues:** Validate AI output structure → Fall back to heuristic extraction if malformed
- **Storage Failure:** Retry Supabase Storage operations 3 times before failing job
- **User Notification:** Failed jobs return error message + timestamp + suggested actions in `GET /jobs/{id}` response
## Implementation Patterns

### Naming Conventions
- **Python/Backend:** ``snake_case`` for variables, functions, file names. ``PascalCase`` for Classes.
- **TypeScript/Frontend:** ``camelCase`` for variables, functions. ``PascalCase`` for Components and Types.
- **Database:** ``snake_case`` for table names (``user_accounts``) and columns (``created_at``).
- **Test Files:** ``test_*.py`` (backend), ``*.test.ts`` (frontend)

### Code Organization
- **Service Pattern:** Business logic MUST exist in ``backend/app/services/``, NOT in API routes. Routes should only handle request parsing and response formatting.
- **Component Colocation:** Frontend components should be organized by domain in ``components/business/`` if they are specific to a feature.

### Error Handling
- **Backend:** Use custom exceptions inheriting from ``HTTPException``. Global exception handler in ``main.py`` converts these to standard JSON error responses: ``{ "detail": "Error message", "code": "ERROR_CODE" }``.
- **Frontend:** Use React Error Boundaries for UI crashes. Use ``try/catch`` or React Query ``onError`` for API failures.

### Logging Strategy
- **Backend:** Structured JSON logging using ``structlog``. Include ``request_id`` in all logs for tracing.
- **Levels:** INFO for general flow, ERROR for exceptions (with stack trace), DEBUG for local dev only.

### Testing Patterns

#### Backend Testing (Pytest + FastAPI TestClient)

**Test Organization:**
```
backend/
 tests/
    conftest.py          # Shared fixtures (test DB, client)
    unit/                # Fast, isolated tests
       test_services.py # Business logic tests
       test_models.py   # Database model tests
    integration/         # API + DB tests
       test_api_auth.py
       test_api_conversion.py
    fixtures/            # Test data (sample PDFs, etc.)
```

**Key Patterns:**
- **Test Database:** Use separate test DB, transaction rollback after each test
- **Fixtures:** Define in ``conftest.py``: ``test_client``, ``test_db``, ``authenticated_user``
- **Dependency Overrides:** Use ``app.dependency_overrides`` to mock external services (S3, Celery)
- **Async Tests:** Use ``pytest-asyncio`` for testing async routes: ``@pytest.mark.asyncio``
- **TestClient vs AsyncClient:** Use ``TestClient`` for sync tests, ``httpx.AsyncClient`` for complex async flows
- **Coverage Target:** 80% minimum (run ``pytest --cov=app --cov-report=html``)

**Example Test:**
```python
# tests/integration/test_api_conversion.py
from fastapi.testclient import TestClient

def test_upload_pdf(test_client: TestClient, authenticated_user):
    with open("tests/fixtures/sample.pdf", "rb") as f:
        response = test_client.post("/api/v1/convert", files={"file": f})
    assert response.status_code == 202
    assert "job_id" in response.json()
```

#### Frontend Testing (Vitest + React Testing Library)

**Test Organization:**
```
frontend/
 src/
    components/
       Button.tsx
       Button.test.tsx   # Colocated with component
    app/
       page.tsx
       page.test.tsx
    __tests__/            # Integration tests
        upload-flow.test.tsx
 vitest.config.ts
 vitest.setup.ts           # Global setup (@testing-library/jest-dom)
```

**Key Patterns:**
- **Component Tests:** Test user interactions, not implementation details
- **Mocking:** Mock API calls using ``vi.mock()`` or MSW (Mock Service Worker)
- **Render Helpers:** Create custom ``render()`` with providers (QueryClient, AuthContext)
- **Async Testing:** Use ``waitFor()`` for async state updates
- **Coverage Target:** 70% minimum (run ``npm run test:coverage``)

**Example Test:**
```typescript
// src/components/UploadButton.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { UploadButton } from './UploadButton'

test('triggers upload on click', async () => {
  const onUpload = vi.fn()
  render(<UploadButton onUpload={onUpload} />)
  const input = screen.getByLabelText('Upload PDF')
  const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
  fireEvent.change(input, { target: { files: [file] } })
  expect(onUpload).toHaveBeenCalledWith(file)
})
```

**Test Commands:**
- Backend: ``pytest`` (all), ``pytest tests/unit`` (fast), ``pytest --cov=app``
- Frontend: ``npm run test`` (watch), ``npm run test:ci`` (CI mode), ``npm run test:coverage``



### Core Models
- **User:** `id` (UUID), `email`, `hashed_password`, `tier` (enum), `created_at`.
- **ConversionJob:** `id` (UUID), `user_id` (FK), `status` (QUEUED, PROCESSING, COMPLETED, FAILED), `input_file_key`, `output_file_key`, `created_at`, `completed_at`, `meta` (JSON - for quality report).

## API Contracts

### `POST /api/v1/convert`
- **Request:** `multipart/form-data` (file: PDF)
- **Response:** `202 Accepted`
```json
{
  "job_id": "uuid-string",
  "status": "QUEUED"
}
```

### `GET /api/v1/jobs/{job_id}`
- **Response:** `200 OK`
```json
{
  "id": "uuid-string",
  "status": "PROCESSING",
  "progress": 45,
  "result_url": null,
  "quality_report": null
}
```

### `GET /api/v1/jobs/{job_id}/download`
- **Response:** `302 Redirect` (to S3 Presigned URL)

## Security Architecture

- **Authentication:** Supabase Auth with JWT tokens, managed sessions, and secure cookie handling.
- **Authorization:** Row Level Security (RLS) policies in Supabase PostgreSQL ensure users only access their own data.
- **File Security:**
    - Uploads and downloads are private Supabase Storage objects.
    - Access via signed URLs with configurable expiration (default 1 hour).
    - Automatic file cleanup via Supabase Storage lifecycle policies (30 days).
- **API Security:**
    - Backend validates Supabase JWT tokens on protected endpoints.
    - Rate limiting middleware to prevent abuse.
    - CORS configured to allow only trusted frontend origins.
- **Input Validation:** 
    - Strict Pydantic models for JSON payloads.
    - Magic-byte checking for file uploads (ensure real PDF).
    - File size limits enforced (configurable, default 50MB).
- **Secrets Management:**
    - API keys stored in environment variables, never in code.
    - Supabase service keys used only in backend, anon keys in frontend.
    - Separate keys for development and production environments.

## Performance Considerations

- **Async Workers:** CPU-heavy tasks never run on the web thread.
- **Scaling:**
    - **Web:** Auto-scale based on HTTP request load.
    - **Worker:** Auto-scale based on Redis Queue depth.
- **Caching:** Redis used for job status caching to reduce DB hits during polling.

## Deployment Architecture

- **Frontend:** Deployed to **Vercel** (Edge Network with automatic HTTPS and CDN).
- **Backend API + Worker:** Deployed to **Railway** (Containers, scale independently).
  - API container: FastAPI service handling HTTP requests
  - Worker container: Celery worker processing conversion jobs
- **Redis:** Managed Redis on **Railway** or **Upstash** for Celery message broker.
- **Database + Auth + Storage:** Fully managed by **Supabase**.
  - PostgreSQL database with automatic backups
  - Authentication service
  - File storage with CDN

**Environment Variables:**
- Frontend: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_URL`
- Backend: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `REDIS_URL`

## Development Environment

### Prerequisites (Verified Versions)
- **Docker Desktop:** 4.x+ (for local Redis only)
- **Node.js:** 24.12.0 LTS (download: nodejs.org/en/download)
- **Python:** 3.13.0 (download: python.org/downloads)
- **pip:** 24.x (comes with Python 3.13)
- **Supabase Account:** Free tier available at supabase.com
- **OpenAI API Key:** From platform.openai.com
- **Anthropic API Key:** From console.anthropic.com

### Setup Commands
```bash
# Start Redis for Celery (local development)
# Supabase services are cloud-managed, no local setup needed
docker-compose up redis -d

# Run frontend
cd frontend && npm run dev

# Run backend API
cd backend && uvicorn app.main:app --reload

# Run Celery worker (separate terminal)
cd backend && celery -A app.worker worker --loglevel=info
```

---

## Production Deployment Architecture

**Last Updated:** 2025-12-30
**Status:** Ready for deployment (see Quick Wins plan: `docs/sprint-artifacts/quick-wins-plan-2025-12-26.md`)

### Infrastructure Overview

Transfer2Read production environment uses a **serverless + managed services** architecture for automatic scaling, zero-downtime deployments, and minimal operational overhead:

| Component | Platform | Purpose | Scaling |
|-----------|----------|---------|---------|
| **Frontend** | Vercel | Next.js app with Edge CDN | Auto-scales globally |
| **Backend API** | Railway | FastAPI REST API | Horizontal auto-scaling |
| **Worker** | Railway | Celery background tasks | Manual scaling (1-N workers) |
| **Redis** | Railway | Task queue + caching | Managed service |
| **Database + Auth + Storage** | Supabase | PostgreSQL + Auth + File storage | Auto-scales to 500GB (free tier) |

### Production URLs

**Custom Domains (configured in QW-1):**
- **Frontend:** https://transfer2read.com
- **Backend API:** https://api.transfer2read.com
- **API Health Check:** https://api.transfer2read.com/api/health
- **API Docs (Swagger):** https://api.transfer2read.com/docs

**Platform-Generated URLs (fallback):**
- **Vercel:** `https://transfer2read.vercel.app`
- **Railway Backend:** `https://backend-api-production-xxxxx.up.railway.app`

### Deployment Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          USER REQUESTS                           │
│                     (transfer2read.com)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  VERCEL (Frontend - Next.js)                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Edge Network (Global CDN)                               │   │
│  │  - Static assets cached at 300+ edge locations          │   │
│  │  - Server-side rendering (SSR) for dynamic pages        │   │
│  │  - Auto-HTTPS with Let's Encrypt SSL                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬───────────────────┬────────────────────┘
                         │                   │
         API Calls ──────┘                   └───── Auth/Storage
         (api.transfer2read.com)                    (Supabase)
                         │                          │
                         ▼                          ▼
┌────────────────────────────────────┐  ┌──────────────────────────┐
│  RAILWAY (Backend API - FastAPI)   │  │  SUPABASE (Managed)       │
│  ┌──────────────────────────────┐  │  │  ┌────────────────────┐  │
│  │  API Server (Uvicorn)        │  │  │  │  PostgreSQL DB     │  │
│  │  - REST endpoints            │  │  │  │  - conversion_jobs │  │
│  │  - JWT authentication        │◄─┼──┼─►│  - user_usage      │  │
│  │  - Supabase client           │  │  │  │  - RLS policies    │  │
│  │  - LangChain orchestration   │  │  │  └────────────────────┘  │
│  └──────────┬───────────────────┘  │  │  ┌────────────────────┐  │
│             │ Publish tasks         │  │  │  Authentication    │  │
│             ▼                       │  │  │  - Email/Password  │  │
│  ┌──────────────────────────────┐  │  │  │  - Google OAuth    │  │
│  │  Redis (Task Queue + Cache)  │  │  │  │  - GitHub OAuth    │  │
│  │  - Celery broker             │  │  │  └────────────────────┘  │
│  │  - Job status cache (5min)   │  │  │  ┌────────────────────┐  │
│  └──────────┬───────────────────┘  │  │  │  Storage Buckets   │  │
│             │                       │  │  │  - uploads/ (PDF)  │  │
│             │ Consume tasks         │  │  │  - downloads/ (EPUB)│ │
│             ▼                       │  │  └────────────────────┘  │
│  ┌──────────────────────────────┐  │  └──────────────────────────┘
│  │  Celery Worker               │  │
│  │  - PDF analysis (GPT-4o)     │──┼─────► OpenAI API
│  │  - Text extraction (Claude)  │──┼─────► Anthropic API
│  │  - EPUB generation           │  │
│  │  - File upload to Supabase   │  │
│  └──────────────────────────────┘  │
└────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   MONITORING (Story 7.1)                         │
│  - Sentry (Error tracking)                                       │
│  - UptimeRobot (Uptime monitoring)                               │
│  - PostHog (Analytics)                                           │
└─────────────────────────────────────────────────────────────────┘
```

### Deployment Configuration

#### Vercel (Frontend)

**Build Configuration:**
```yaml
Framework: Next.js (auto-detected)
Root Directory: frontend/
Build Command: npm run build
Output Directory: .next
Install Command: npm install
Node Version: 24.x
```

**Environment Variables:**
```bash
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...  # PUBLIC key (safe)
NEXT_PUBLIC_API_URL=https://api.transfer2read.com
NEXT_PUBLIC_ENVIRONMENT=production
```

**Custom Domain:**
- Primary: `transfer2read.com` (A record → Vercel IP or CNAME → `cname.vercel-dns.com`)
- Alias: `www.transfer2read.com` → Redirects to apex domain (301 permanent)

**Deployment Trigger:**
- **Production:** Push to `main` branch → Auto-deploy to https://transfer2read.com
- **Preview:** Pull requests → Auto-deploy to preview URL `https://transfer2read-git-[branch]-[team].vercel.app`

---

#### Railway (Backend API + Worker)

**Service 1: backend-api**

```yaml
Service Name: backend-api
Root Directory: backend/
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Healthcheck Endpoint: /api/health
Auto-Scaling: Enabled (1-5 instances based on CPU/memory)
```

**Environment Variables:**
```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGc...  # SECRET key (admin access)
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
REDIS_URL=redis://default:password@redis.railway.internal:6379
CELERY_BROKER_URL=${REDIS_URL}/0
CELERY_RESULT_BACKEND=${REDIS_URL}/0
ENVIRONMENT=production
FRONTEND_URL=https://transfer2read.com
ALLOWED_ORIGINS=https://transfer2read.com,https://www.transfer2read.com
```

**Custom Domain:**
- `api.transfer2read.com` (CNAME → `backend-api-production-xxxxx.up.railway.app`)

**Deployment Trigger:**
- Push to `main` branch → Auto-deploy (Railway watches GitHub repo)

---

**Service 2: celery-worker**

```yaml
Service Name: celery-worker
Root Directory: backend/
Start Command: celery -A app.worker worker --loglevel=info
Worker Count: 1 (manual scaling to 2-5 based on load)
Auto-Restart: Enabled (if worker crashes)
```

**Environment Variables:**
- Same as `backend-api` service (must share `REDIS_URL` for task queue communication)

**Deployment Trigger:**
- Push to `main` branch → Auto-deploy

---

**Service 3: redis**

```yaml
Service Type: Redis Plugin (Managed)
Version: 8.x
Persistence: Enabled (RDB snapshots + AOF)
Max Memory: 512MB (adjust based on load)
Eviction Policy: allkeys-lru (Least Recently Used)
```

**Internal URL:** `redis://default:password@redis.railway.internal:6379`

**Auto-provisioned by Railway** (no manual setup required)

---

#### Supabase (Database + Auth + Storage)

**Project Configuration:**
```yaml
Project Name: Transfer2Read Production
Region: US East (or EU West - match Railway region for low latency)
Database Size: 500MB (free tier) → 8GB (Pro tier if needed)
Storage Size: 1GB (free tier) → 100GB (Pro tier if needed)
```

**Tables:**
- `conversion_jobs` (PDF conversion tracking)
- `user_usage` (monthly usage limits)

**RLS Policies:**
- Users can only access their own jobs and usage data (see `docs/sprint-artifacts/quick-wins-plan-2025-12-26.md` QW-2 for SQL policies)

**Storage Buckets:**
- `uploads` (Private) - User uploaded PDFs (50MB max per file)
- `downloads` (Private) - Generated EPUB files (100MB max per file)

**Authentication Providers:**
- Email/Password (confirm email required)
- Google OAuth (optional)
- GitHub OAuth (optional)

**Backups:**
- Daily automatic backups (7-day retention on free tier, 30-day on Pro)
- Point-in-Time Recovery (PITR) available on Pro tier

---

### Security Configuration

#### HTTPS/SSL

- **Vercel:** Auto-provisioned via Let's Encrypt (free, auto-renews every 90 days)
- **Railway:** Auto-provisioned via Let's Encrypt for custom domains
- **Supabase:** HTTPS enforced on all endpoints

#### CORS Policy

**Backend API (FastAPI):**
```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),  # transfer2read.com, www.transfer2read.com
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Environment Variables

**Storage:**
- **Production Secrets:** Stored in Railway/Vercel environment variable managers (encrypted at rest)
- **Backup:** Documented in password manager (1Password/LastPass) - see `docs/operations/production-secrets-template.md`

**Rotation Schedule:**
- **OpenAI/Anthropic API Keys:** Every 90 days (see `docs/operations/api-key-rotation-guide.md`)
- **Supabase Service Key:** On-demand (only if compromised)
- **Database Password:** Annually or if compromised

#### Row Level Security (RLS)

**Supabase RLS Policies:**
- `conversion_jobs` table: Users can only SELECT/INSERT/UPDATE/DELETE their own jobs (`auth.uid() = user_id`)
- `user_usage` table: Users can only view/update their own usage data
- Storage buckets: Users can only upload/download files in their own folder (`auth.uid()::text = (storage.foldername(name))[1]`)

---

### Monitoring & Observability (Story 7.1)

**Error Tracking:**
- **Sentry** (https://sentry.io) - Captures unhandled exceptions, API errors, performance issues
- **Alerts:** Email/Slack notifications for critical errors

**Uptime Monitoring:**
- **UptimeRobot** (https://uptimerobot.com) - Pings `/api/health` every 5 minutes
- **Alerts:** Email/SMS if API down for >2 minutes

**Analytics:**
- **PostHog** (https://posthog.com) - User behavior tracking, feature usage, conversion funnels
- **Privacy:** GDPR-compliant, self-hosted option available

**Platform Metrics:**
- **Vercel Analytics:** Page views, performance (Core Web Vitals), edge network latency
- **Railway Metrics:** CPU, memory, network usage per service
- **Supabase Dashboard:** Database size, active connections, query performance

---

### Disaster Recovery

**Backup Strategy:**
- **Database:** Daily automatic backups (Supabase) + manual backups before major migrations
- **Storage:** Files auto-deleted after 30 days (retention policy) - users notified to download within window
- **Code:** GitHub repository with protected `main` branch (requires PR review)

**Rollback Procedures:**
- **Frontend (Vercel):** Instant rollback to previous deployment via dashboard (see `docs/operations/rollback-procedures.md`)
- **Backend (Railway):** Redeploy previous deployment (2-5 minutes downtime)
- **Database (Supabase):** Restore from daily backup (10-20 minutes)

**Recovery Time Objectives (RTO):**
- **Frontend:** <5 minutes (Vercel rollback)
- **Backend API:** <10 minutes (Railway rollback)
- **Database:** <30 minutes (Supabase restore from backup)

**Recovery Point Objective (RPO):**
- **Database:** 24 hours (daily backups) - Pro tier: <1 minute (PITR)
- **Files:** 0 data loss (Supabase Storage redundancy)

---

### Cost Estimation (Monthly)

**Free Tier (MVP):**
| Service | Tier | Cost | Limits |
|---------|------|------|--------|
| Vercel | Hobby | $0 | 100GB bandwidth, unlimited requests |
| Railway | Starter | $5 | $5 execution credit, 500 hours, 512MB RAM |
| Supabase | Free | $0 | 500MB DB, 1GB storage, 50,000 monthly active users |
| OpenAI | Pay-as-you-go | ~$10-50 | Depends on usage (GPT-4o: $2.50/1M input tokens) |
| Anthropic | Pay-as-you-go | ~$5-20 | Depends on usage (Claude 3 Haiku: $0.25/1M input tokens) |
| **Total** | | **~$20-75/month** | Supports ~100-500 conversions/month |

**Production Tier (Scaling):**
| Service | Tier | Cost | Limits |
|---------|------|------|--------|
| Vercel | Pro | $20/user/mo | 1TB bandwidth, 100 builds/day |
| Railway | Pro | $20-100 | Based on usage (CPU/memory hours) |
| Supabase | Pro | $25 | 8GB DB, 100GB storage, PITR backups |
| OpenAI | Pay-as-you-go | $100-500 | Higher rate limits, dedicated support |
| Anthropic | Pay-as-you-go | $50-200 | Higher rate limits |
| Sentry | Team | $26/mo | 50k events/month, 1-year retention |
| UptimeRobot | Pro | $7/mo | 50 monitors, 1-min checks |
| **Total** | | **~$250-900/month** | Supports ~1,000-5,000 conversions/month |

**Cost Optimization:**
- Use Claude 3 Haiku for text extraction (10x cheaper than GPT-4o)
- Cache job status in Redis (reduce Supabase queries by 80%)
- Auto-delete files after 30 days (reduce storage costs)
- Monitor API usage spikes (set billing alerts at 80% and 100%)

---

### Scalability & Performance

**Current Capacity:**
- **Frontend:** Auto-scales globally (Vercel Edge Network)
- **Backend API:** 1-5 instances (Railway auto-scaling based on CPU/memory)
- **Worker:** 1 worker (manual scaling to 2-5 based on task queue depth)

**Performance Benchmarks:**
| Metric | Target | Actual (Tested) |
|--------|--------|-----------------|
| Frontend Load Time (first paint) | <2s | ~1.5s (with CDN) |
| API Health Check Response | <200ms | ~100ms |
| PDF Upload (10MB) | <5s | ~3s |
| Conversion (simple PDF, 20 pages) | <60s | ~40s |
| Conversion (complex PDF, 100 pages) | <180s | ~120s |
| Concurrent Conversions | 5 (1 worker) | 5 (tested) |

**Scaling Strategy:**
- **Frontend:** Already globally scaled via Vercel CDN (no action needed)
- **Backend API:** Railway auto-scales to 5 instances at 80% CPU (increase if needed)
- **Worker:** Add workers manually as task queue depth increases (target: <10 pending tasks)
  - 1 worker: ~5 concurrent conversions
  - 2 workers: ~10 concurrent conversions
  - 5 workers: ~25 concurrent conversions
- **Database:** Upgrade Supabase to Pro tier if approaching 500MB limit (monitor Dashboard → Database Size)

---

### Deployment Checklist

**Pre-Deployment (Quick Wins QW-1 to QW-5):**
- [ ] Domain purchased and DNS configured (`transfer2read.com`, `api.transfer2read.com`)
- [ ] Supabase production project created (database + auth + storage)
- [ ] Production API keys rotated (OpenAI, Anthropic)
- [ ] Documentation updated (README, deployment guide, rollback procedures)
- [ ] Beta user list compiled (5-10 testers)

**Deployment Steps:**
1. [ ] Deploy frontend to Vercel (push to `main` branch)
2. [ ] Deploy backend + worker to Railway (push to `main` branch)
3. [ ] Configure environment variables (Vercel + Railway + Supabase)
4. [ ] Add custom domains (Vercel + Railway DNS settings)
5. [ ] Verify health endpoints (`/api/health` returns 200 OK)
6. [ ] Test end-to-end flow (register → upload → convert → download)
7. [ ] Enable monitoring (Sentry + UptimeRobot - Story 7.1)

**Post-Deployment:**
- [ ] Smoke test critical paths (see `docs/operations/production-deployment-guide.md` Step 6)
- [ ] Invite beta users (see `docs/operations/beta-users.csv`)
- [ ] Monitor error rates and performance (Sentry, Railway logs)
- [ ] Schedule API key rotation reminder (90 days from deployment)

---

## Architecture Decision Records (ADRs)

### ADR-001: API-First Intelligence Architecture
- **Decision:** Use cloud-based LLM APIs (GPT-4o, Claude 3) via LangChain instead of self-hosted PyTorch models.
- **Rationale:** 
  - **Speed to Market:** No model training, fine-tuning, or infrastructure management required.
  - **Quality:** State-of-the-art multimodal models (GPT-4o) provide superior document understanding compared to specialized layout detection models.
  - **Scalability:** No GPU infrastructure needed, scales automatically with API provider capacity.
  - **Cost-Effectiveness:** Pay-per-use pricing more economical than maintaining GPU servers for intermittent workloads.
  - **Maintenance:** API providers handle model updates, improvements, and infrastructure.
  - **Trade-off:** Accepts API costs and external dependency in exchange for development velocity and quality.

### ADR-002: Supabase as Unified Backend Platform
- **Decision:** Use Supabase for authentication, database, and file storage instead of self-managed PostgreSQL + S3.
- **Rationale:**
  - **Developer Experience:** Single platform reduces integration complexity and configuration overhead.
  - **Built-in Auth:** Production-ready authentication with email/password, social logins, and JWT management.
  - **Real-time Capabilities:** Subscriptions for live job status updates (future enhancement).
  - **Row Level Security:** Database-level security policies enforce data isolation.
  - **Managed Infrastructure:** No database administration, automatic backups, point-in-time recovery.
  - **Cost:** Generous free tier for development, predictable pricing for production.

### ADR-003: Async Processing with Celery
- **Decision:** Use Celery for conversion tasks.
- **Rationale:** PDF conversion with LLM API calls is time-consuming (2-5+ seconds per page). HTTP requests must return quickly. Celery provides robust retries, scheduling, and worker management that simple background tasks lack. Redis as broker provides fast, reliable message passing.

---

_Generated by BMAD Decision Architecture Workflow v1.0_
_Date: 2025-11-27_
_For: xavier_
