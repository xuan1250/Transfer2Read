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
| **Deployment** | **Docker Compose** | N/A | CUSTOM | Self-hosted Docker containers for frontend, backend, worker, and Redis. |

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

**Status:** Self-Hosted Docker Deployment

Transfer2Read runs on self-hosted infrastructure using Docker Compose. All services run as containers on the host machine.

### Docker Compose Configuration

Create `docker-compose.yml` in project root with 4 services: frontend, backend-api, backend-worker, redis.

**Key Configuration:**
- Frontend: Next.js on port 3000
- Backend API: FastAPI on port 8000  
- Worker: Celery background tasks
- Redis: Port 6379 (internal)
- All services use `.env` file for configuration
- Volumes for Redis persistence and backend uploads
- Restart policy: `unless-stopped`

### Environment Configuration

Root `.env` file contains:
- Supabase credentials (URL, service key, anon key)
- AI API keys (OpenAI, Anthropic)
- Redis URLs (internal Docker network)

### Deployment Commands

**Start:** `docker-compose up -d`
**Logs:** `docker-compose logs -f`
**Stop:** `docker-compose down`
**Rebuild:** `docker-compose up -d --build`

### Health Checks

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000/api/health`
- Redis: `docker exec transfer2read-redis redis-cli ping`

### Production Considerations

**Hardware Requirements:**
- CPU: 4+ cores (AI processing intensive)
- RAM: 8GB minimum, 16GB recommended
- Storage: 50GB+ for images and temp files

**Performance:**
- Concurrent conversions limited by CPU cores
- Vertical scaling only (upgrade host hardware)
- Local Redis provides fast queue performance

**Security:**
- API keys in `.env` (never commit)
- Firewall: Expose ports 3000/8000 only if needed
- Supabase handles auth/storage security

**Monitoring:**
- Container health: `docker-compose ps`
- Resources: `docker stats`
- Logs: `docker-compose logs`

**Scaling:**
- Vertical only (CPU/RAM upgrades)
- Scale workers: `docker-compose up -d --scale backend-worker=3`

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
