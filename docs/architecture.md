# Architecture

## Executive Summary

Transfer2Read is a high-fidelity PDF to EPUB converter designed to solve the "complex PDF" problem for technical and academic documents. The system employs a **Hybrid Intelligence Architecture**, utilizing a **Next.js** frontend for a responsive, modern user experience and a **FastAPI** backend powered by **PyTorch** for local, privacy-focused AI layout analysis. To ensure scalability and performance, long-running conversion tasks are offloaded to **Celery** workers backed by **Redis**, while file storage is managed via **S3-compatible** object storage. This architecture balances the need for heavy computational processing (AI models) with the requirement for a snappy, accessible web interface.

## Project Initialization

The project is initialized using the **Vintasoftware Next.js FastAPI Starter** to provide a production-ready foundation with built-in type safety and authentication.

### Setup Commands

```bash
# Initialize project using the starter template
git clone https://github.com/vintasoftware/nextjs-fastapi-starter.git transfer_app
cd transfer_app

# Install Frontend Dependencies
cd frontend
npm install

# Install Backend Dependencies
cd ../backend
pip install -r requirements.txt

# Start Development Environment (using Docker Compose is recommended)
docker-compose up -d
```

## Decision Summary

| Category | Decision | Version | Affects Epics | Rationale |
| -------- | -------- | ------- | ------------- | --------- |
| **Foundation** | **Vintasoftware Starter** | Latest | All | Provides end-to-end type safety, auth, and production structure out of the box. |
| **Frontend** | **Next.js** | 14 (App Router) | UI, Account | React ecosystem, SSR for performance, excellent Vercel integration. |
| **Backend** | **FastAPI** | 0.100+ | API, Conversion | High performance Python framework, native async support, perfect for AI integration. |
| **Async Processing** | **Celery + Redis** | 5.x / 7.x | Conversion | Robust, mature solution for handling long-running CPU-intensive tasks (PDF conversion). |
| **AI Inference** | **PyTorch Native** | 2.x | Conversion | Flexible, industry standard for running layout analysis models locally. |
| **File Storage** | **S3-Compatible** | AWS SDK v3 | Upload, Download | Scalable, secure storage for user files; decouples storage from compute. |
| **Database** | **PostgreSQL** | 15+ | Account, History | Reliable relational data for users, subscriptions, and job history. |
| **Deployment** | **Vercel + Railway** | N/A | DevOps | Best-of-breed: Vercel for frontend speed, Railway for backend/worker container orchestration. |

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
- **Language:** TypeScript (Frontend), Python 3.11+ (Backend)
- **Styling:** Tailwind CSS
- **UI Library:** shadcn/ui (Radix UI based)
- **ORM:** SQLAlchemy (Async)
- **Schema Validation:** Pydantic v2
- **Task Queue:** Celery

### Integration Points
- **Frontend <-> Backend:** REST API via generated Axios/Fetch client. Types shared via OpenAPI generation.
- **Backend <-> Worker:** Redis Message Broker.
- **Backend <-> Storage:** S3 API (boto3).
- **Backend <-> Database:** AsyncPG driver.

## Novel Pattern Designs

### PDF Conversion Pipeline (Async)

The core value proposition relies on a robust conversion pipeline that doesn't block the web server.

**Components:**
1.  **API:** Receives upload -> Saves to S3 -> Creates DB Record (PENDING) -> Pushes ID to Redis Queue.
2.  **Worker:** Pops ID -> Downloads PDF -> Runs Pipeline -> Uploads EPUB -> Updates DB Record (COMPLETED).
3.  **Client:** Polls `GET /jobs/{id}` for progress/status.

**Pipeline Steps:**
1.  **Ingest:** Load PDF with PyMuPDF.
2.  **Analyze (AI):** Pass page images to PyTorch Layout Model -> Get bounding boxes (Table, Image, Text).
3.  **Structure:** Build logical document tree (Chapters > Sections).
4.  **Reflow:** Extract text/objects based on layout analysis.
5.  **Generate:** Build EPUB container structure.

## Implementation Patterns

### Naming Conventions
- **Python/Backend:** `snake_case` for variables, functions, file names. `PascalCase` for Classes.
- **TypeScript/Frontend:** `camelCase` for variables, functions. `PascalCase` for Components and Types.
- **Database:** `snake_case` for table names (`user_accounts`) and columns (`created_at`).

### Code Organization
- **Service Pattern:** Business logic MUST exist in `backend/app/services/`, NOT in API routes. Routes should only handle request parsing and response formatting.
- **Component Colocation:** Frontend components should be organized by domain in `components/business/` if they are specific to a feature.

### Error Handling
- **Backend:** Use custom exceptions inheriting from `HTTPException`. Global exception handler in `main.py` converts these to standard JSON error responses: `{ "detail": "Error message", "code": "ERROR_CODE" }`.
- **Frontend:** Use React Error Boundaries for UI crashes. Use `try/catch` or React Query `onError` for API failures.

### Logging Strategy
- **Backend:** Structured JSON logging using `structlog`. Include `request_id` in all logs for tracing.
- **Levels:** INFO for general flow, ERROR for exceptions (with stack trace), DEBUG for local dev only.

## Data Architecture

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

### Prerequisites
- Docker & Docker Compose
- Node.js 20+
- Python 3.11+
- Poetry (optional, but recommended for Python deps)

### Setup Commands
```bash
# Start all services (DB, Redis, API, Worker, Frontend)
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
