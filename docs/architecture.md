# Architecture

> **Versions Verified:** 2025-11-27  
> **Verification Method:** WebSearch for current stable releases  
> **Compatibility:** All versions cross-checked for mutual compatibility

## Executive Summary

Transfer2Read is a high-fidelity PDF to EPUB converter designed to solve the "complex PDF" problem for technical and academic documents. The system employs a **Hybrid Intelligence Architecture**, utilizing a **Next.js** frontend for a responsive, modern user experience and a **FastAPI** backend powered by **PyTorch** for local, privacy-focused AI layout analysis. To ensure scalability and performance, long-running conversion tasks are offloaded to **Celery** workers backed by **Redis**, while file storage is managed via **S3-compatible** object storage. This architecture balances the need for heavy computational processing (AI models) with the requirement for a snappy, accessible web interface.

## Project Initialization

The project is initialized using the **Vintasoftware Next.js FastAPI Template v0.0.6** (verified 2025-11-27) to provide a production-ready foundation.

### What the Starter Provides (No Manual Setup Needed)

The template comes pre-configured with:
- ✅ **Authentication System**: JWT-based auth using `fastapi-users`, password hashing, email recovery
- ✅ **Database Setup**: Async PostgreSQL with SQLAlchemy, Docker Compose config
- ✅ **Type Safety**: OpenAPI schema generation, frontend type definitions
- ✅ **Dev Environment**: Docker Compose with all services (frontend, backend, DB, Redis)
- ✅ **Protected Routes**: Frontend and backend route guards
- ✅ **User Dashboard**: Basic user management UI

### What Requires Custom Implementation

- ❌ **Celery Workers**: Need to add Celery configuration and worker process
- ❌ **S3 Storage**: Need to integrate boto3 and configure S3 bucket
- ❌ **PyTorch AI Pipeline**: Need to add layout detection model and conversion logic  
- ❌ **PDF Processing**: Need to implement PyMuPDF + AI analysis pipeline
- ❌ **Background Jobs**: Need to design job queue and progress tracking

### Setup Commands

```bash
# Clone specific template version
git clone --branch v0.0.6 https://github.com/vintasoftware/nextjs-fastapi-template.git transfer_app
cd transfer_app

# Install Frontend Dependencies
cd frontend
npm install

# Install Backend Dependencies
cd ../backend
pip install -r requirements.txt

# Start Development Environment (Docker provides DB + Redis automatically)
docker-compose up -d
```

## Decision Summary

| Category | Decision | Version | Source | Rationale |
| -------- | -------- | ------- | ------ | --------- |
| **Foundation** | **Vintasoftware Template** | 0.0.6 | PROVIDED BY STARTER | Production-ready auth, type safety, Docker setup. |
| **Frontend** | **Next.js** | 15.0.3 | CUSTOM | Latest stable (Nov 2025), React 19 support, App Router, Turbopack. |
| **Backend** | **FastAPI** | 0.122.0 | CUSTOM | Latest stable (Nov 2025), high performance, native async, OpenAPI. |
| **Runtime** | **Python** | 3.13.0 | CUSTOM | Latest stable (Oct 2024), compatible with FastAPI 0.122.0. |
| **Runtime** | **Node.js** | 24.12.0 LTS | CUSTOM | Krypton LTS (Oct 2025), compatible with Next.js 15, support until 2027. |
| **Async Processing** | **Celery** | 5.5.3 | CUSTOM | Latest stable (Jun 2025), robust task queue for CPU-intensive work. |
| **Message Broker** | **Redis** | 8.4.0 | CUSTOM | Latest stable (Nov 2025), high-performance broker + caching. |
| **AI Inference** | **PyTorch** | 2.9.1 | CUSTOM | Latest stable (Nov 2025), flexible framework for layout detection. |
| **AI Model** | **DocLayout-YOLO** | Latest | CUSTOM | Real-time layout detection (Oct 2024), YOLO-v10 based, optimized for documents. |
| **File Storage** | **S3-Compatible (boto3)** | 1.36.0 | CUSTOM | Latest boto3 SDK, works with AWS S3 or alternatives (R2, MinIO). |
| **Database** | **PostgreSQL** | 17.7 | PROVIDED BY STARTER | Latest stable (Nov 2025), advanced features, async support via AsyncPG. |
| **ORM** | **SQLAlchemy** | 2.0.36 | PROVIDED BY STARTER | Latest stable, async support, type hints. |
| **Deployment** | **Vercel + Railway** | N/A | CUSTOM | Vercel for frontend (edge network), Railway for backend containers. |

## Project Structure

```
transfer_app/
├── frontend/                   # Next.js 14 Application
│   ├── src/
│   │   ├── app/                # App Router (Pages & Layouts)
│   │   ├── components/         # React Components (shadcn/ui)
│   │   │   ├── ui/             # Primitive UI components
│   │   │   └── business/       # Domain-specific components
│   │   ├── lib/                # Utilities & API Clients
│   │   └── types/              # Shared Types (generated)
├── backend/                    # FastAPI Application
│   ├── app/
│   │   ├── api/                # API Endpoints (Routes)
│   │   │   └── v1/
│   │   ├── core/               # Config, Security, Logging
│   │   ├── db/                 # Database connection & migrations
│   │   ├── models/             # SQLAlchemy ORM Models
│   │   ├── schemas/            # Pydantic Schemas (Data Validation)
│   │   ├── services/           # Business Logic Layer
│   │   │   ├── conversion/     # PDF Processing Pipeline
│   │   │   ├── ai/             # PyTorch Model Inference
│   │   │   └── storage/        # S3 Interface
│   │   └── worker.py           # Celery Worker Entrypoint
├── docker-compose.yml          # Local dev orchestration
└── README.md
```

## FR Category to Architecture Mapping

| FR Category | Primary Component | Data Store | Key Logic |
| ----------- | ----------------- | ---------- | --------- |
| **User Account & Access** | Backend `api/auth` | PostgreSQL (`users`) | `fastapi-users` library for auth flows. |
| **PDF File Upload** | Backend `api/upload` | S3 Bucket (`uploads/`) | Stream upload to S3, validate PDF mime-type. |
| **AI Analysis & Conversion** | Celery Worker | N/A (Ephemeral) | `services.ai` runs PyTorch models; `services.conversion` handles PyMuPDF. |
| **AI Structural Analysis** | Celery Worker | N/A | Heuristic + AI detection of TOC/Chapters. |
| **Conversion Process** | Backend `api/jobs` | Redis (Queue), PG (Status) | Async task dispatch, progress polling via API. |
| **EPUB Output** | Celery Worker | S3 Bucket (`downloads/`) | EPUB generation, upload result to S3. |
| **Usage Limits** | Backend Middleware | PostgreSQL (`usage_logs`) | Check counts before dispatching job. |

## Technology Stack Details

### Core Technologies
- **Language:** TypeScript 5.x (Frontend), Python 3.13.0 (Backend)
- **Styling:** Tailwind CSS 3.x (PROVIDED BY STARTER)
- **UI Library:** shadcn/ui (Radix UI based, PROVIDED BY STARTER)
- **ORM:** SQLAlchemy 2.0.36 Async (PROVIDED BY STARTER)
- **Schema Validation:** Pydantic v2 (PROVIDED BY STARTER)
- **Task Queue:** Celery 5.5.3
- **PDF Library:** PyMuPDF 1.24.x
- **Testing:** Pytest 8.x (Backend), Vitest 2.x (Frontend)

### Integration Points
- **Frontend <-> Backend:** REST API via generated Axios/Fetch client. Types shared via OpenAPI generation (PROVIDED BY STARTER).
- **Backend <-> Worker:** Redis 8.4.0 Message Broker.
- **Backend <-> Storage:** S3 API via boto3 1.36.0.
- **Backend <-> Database:** AsyncPG driver (PROVIDED BY STARTER).
- **Worker <-> AI Model:** PyTorch 2.9.1 loading DocLayout-YOLO weights from Hugging Face.

## Novel Pattern Designs

### PDF Conversion Pipeline (Async)

The core value proposition relies on a robust conversion pipeline that doesn't block the web server.

**Components:**
1.  **API:** Receives upload → Saves to S3 → Creates DB Record (PENDING) → Pushes ID to Redis Queue.
2.  **Worker:** Pops ID → Downloads PDF → Runs Pipeline → Uploads EPUB → Updates DB Record (COMPLETED).
3.  **Client:** Polls `GET /jobs/{id}` for progress/status.

**AI Model Specification:**
- **Model:** DocLayout-YOLO (github.com/opendatalab/DocLayout-YOLO)
- **Version:** Latest release (October 2024)
- **Architecture:** YOLO-v10 based, optimized for real-time document layout detection
- **Capabilities:** Detects text blocks, tables, images, titles, headers, footers across 23 layout categories
- **Source:** Pre-trained weights from Hugging Face Model Hub
- **Loading Pattern:** Lazy load in worker on first task (cached in memory for subsequent tasks)
- **Location:** `backend/app/services/ai/models/doclayout_yolo.pt`
- **Inference:** ~28ms per page on NVIDIA GPU, ~100ms on CPU

**Pipeline Steps:**
1.  **Ingest:** Load PDF with PyMuPDF (fitz library).
2.  **Analyze (AI):** Render page to image → Pass to DocLayout-YOLO → Get bounding boxes + labels (Table, Image, Text, Title).
3.  **Structure:** Build logical document tree using detected titles/headers (Chapters > Sections).
4.  **Reflow:** Extract text/objects based on layout bounding boxes, preserve reading order.
5.  **Generate:** Build EPUB container structure (OPF, NCX, XHTML per chapter).

**Failure Handling:**
- **Celery Retries:** Max 3 retries with exponential backoff (1min, 5min, 15min)
- **Timeout:** 10 minute max per job (configurable via env var)
- **Worker Crash:** Job remains in PROCESSING state → Manual cleanup or auto-requeue after 30min
- **S3 Failure:** Retry S3 operations 3 times before failing job
- **AI Model Error:** Fall back to heuristic text extraction (no layout analysis) + log warning
- **User Notification:** Failed jobs return error message + timestamp in `GET /jobs/{id}` response
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

- **Authentication:** JWT (JSON Web Tokens) stored in HttpOnly, Secure cookies.
- **File Security:**
    - Uploads are private S3 objects.
    - Downloads via short-lived Presigned URLs.
    - Automatic expiration/deletion of files after 30 days (Lifecycle Policy).
- **Input Validation:** Strict Pydantic models for JSON; Magic-byte checking for file uploads (ensure real PDF).

## Performance Considerations

- **Async Workers:** CPU-heavy tasks never run on the web thread.
- **Scaling:**
    - **Web:** Auto-scale based on HTTP request load.
    - **Worker:** Auto-scale based on Redis Queue depth.
- **Caching:** Redis used for job status caching to reduce DB hits during polling.

## Deployment Architecture

- **Frontend:** Deployed to **Vercel** (Edge Network).
- **Backend API:** Deployed to **Railway** (Container).
- **Worker:** Deployed to **Railway** (Container, scaled independently).
- **Data:** PostgreSQL and Redis managed on **Railway**.
- **Storage:** AWS S3 (or R2/MinIO).

## Development Environment

### Prerequisites (Verified Versions)
- **Docker Desktop:** 4.x+ (includes Docker Compose)
- **Node.js:** 24.12.0 LTS (download: nodejs.org/en/download)
- **Python:** 3.13.0 (download: python.org/downloads)
- **pip:** 24.x (comes with Python 3.13)

### Setup Commands
```bash
# Start all services (DB, Redis, API, Worker, Frontend)
# Docker Compose provides PostgreSQL 17.7 and Redis 8.4 automatically via starter template
docker-compose up --build
```

## Architecture Decision Records (ADRs)

### ADR-001: Hybrid Intelligence Architecture
- **Decision:** Run AI models locally (on server) rather than using 3rd party AI APIs.
- **Rationale:** Privacy is a core value proposition. High volume of text processing would be cost-prohibitive with GPT-4/Claude APIs. PyTorch native implementation allows fine-tuned control over the layout analysis pipeline.

### ADR-002: Async Processing with Celery
- **Decision:** Use Celery for conversion tasks.
- **Rationale:** PDF conversion is time-consuming (>30s). HTTP requests must return quickly. Celery provides robust retries, scheduling, and worker management that simple background tasks lack.

---

_Generated by BMAD Decision Architecture Workflow v1.0_
_Date: 2025-11-27_
_For: xavier_
