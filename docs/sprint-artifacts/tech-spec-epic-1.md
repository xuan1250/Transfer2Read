# Epic Technical Specification: Project Foundation & Deployment Pipeline

Date: 2025-11-28
Author: xavier
Epic ID: 1
Status: Approved

---

## Overview

Epic 1 establishes the complete technical foundation for Transfer2Read, the AI-powered PDF to EPUB converter designed to achieve 95%+ fidelity for complex documents. This epic initializes the project using the **Vintasoftware Next.js FastAPI Template v0.0.6**, providing production-ready authentication, database setup, and type safety out-of-the-box. Custom implementation includes configuring **Celery** workers for asynchronous PDF conversion tasks, integrating **S3-compatible storage** for file management, and establishing a complete **CI/CD deployment pipeline** to Vercel (frontend) and Railway (backend/workers).

This foundation epic is a necessary greenfield exception - it delivers no direct user value but enables all subsequent feature development. Without this infrastructure, no conversion can occur, no files can be stored, and no deployment can happen. The five stories in this epic systematically build from monorepo initialization through deployment automation, ensuring the application can scale from development to production.

## Objectives and Scope

**In Scope:**

- Initialize project repository using Vintasoftware starter template (v0.0.6)
- Configure Next.js 15.0.3 frontend with shadcn/ui and Professional Blue theme
- Configure FastAPI 0.122.0 backend with PostgreSQL 17.7 and Redis 8.4.0
- Implement Celery 5.5.3 worker infrastructure for asynchronous task processing
- Integrate S3-compatible storage service (boto3 1.36.0) for PDF/EPUB file management
- Establish Docker Compose development environment with all services
- Configure CI/CD deployment pipelines to Vercel (frontend) and Railway (backend/workers/database)
- Deploy working "Hello World" application to production URLs
- Verify frontend-backend communication in production environment

**Out of Scope:**

- PDF conversion logic or AI model integration (Epic 4)
- Authentication UI or user management features (Epic 2)
- File upload API endpoints or validation logic (Epic 3)
- Quality preview interface or EPUB generation (Epics 4 & 5)
- Usage tier enforcement or admin dashboard (Epic 6)
- Any business logic beyond basic health checks and starter template functionality

## System Architecture Alignment

This epic implements the core architectural decisions documented in `architecture.md`:

**Foundation Components:**
- **Template Baseline:** Vintasoftware Next.js FastAPI Template v0.0.6 (Architecture: "Project Initialization" section)
- **Frontend Stack:** Next.js 15.0.3 (latest stable, Nov 2025) + React 19 + Tailwind CSS + shadcn/ui
- **Backend Stack:** FastAPI 0.122.0 (latest stable, Nov 2025) + Python 3.13.0
- **Data Layer:** PostgreSQL 17.7 (async via AsyncPG) + SQLAlchemy 2.0.36 + Redis 8.4.0
- **Task Queue:** Celery 5.5.3 with Redis broker (Architecture ADR-002: Async Processing)
- **Storage:** S3-compatible object storage via boto3 1.36.0

**Deployment Architecture:**
- Frontend → Vercel (Edge Network) for optimal global performance
- Backend API + Workers → Railway (Container Platform) for unified backend services
- Database (PostgreSQL + Redis) → Railway managed services
- Storage → AWS S3 (or R2/MinIO alternatives)

**Constraints Respected:**
- All version selections match Architecture "Decision Summary" table
- Docker Compose development environment mirrors production architecture
- No custom framework implementations - leverage starter template and standard libraries
- CORS configured for Vercel-to-Railway communication

## Detailed Design

### Services and Modules

This epic establishes the foundational services and module structure that all subsequent epics will build upon:

| Service/Module | Location | Responsibility | Owner | Inputs | Outputs |
|----------------|----------|----------------|-------|--------|---------|
| **Frontend App** | `frontend/src/app/` | Next.js 15 App Router pages, layouts, routing | Frontend Dev | User requests | Rendered HTML, API calls |
| **UI Components** | `frontend/src/components/ui/` | shadcn/ui base components (Button, Card, Input, etc.) | Frontend Dev | Props | Rendered React components |
| **API Client** | `frontend/src/lib/api/` | Type-safe API client (generated from OpenAPI) | Frontend Dev | API endpoints | HTTP requests/responses |
| **Backend API** | `backend/app/api/v1/` | FastAPI route handlers, request validation | Backend Dev | HTTP requests | JSON responses |
| **Core Config** | `backend/app/core/` | Configuration, security, logging setup | Backend Dev | Environment vars | Config objects |
| **Database Layer** | `backend/app/db/` | AsyncPG connection, session management | Backend Dev | SQL queries | DB results |
| **Celery Worker** | `backend/app/worker.py` | Async task processor entrypoint | Backend Dev | Redis queue messages | Task execution |
| **S3 Storage Service** | `backend/app/services/storage/` | S3 upload/download/delete operations | Backend Dev | File objects, keys | S3 URLs, confirmations |
| **Health Check** | `backend/app/api/v1/health.py` | System health endpoint (DB, Redis status) | Backend Dev | None | Health status JSON |

**Module Dependencies:**

```
Frontend (Next.js)
  ├── Depends on: Backend API (HTTP)
  └── Integrates: shadcn/ui, Tailwind CSS

Backend (FastAPI)
  ├── Depends on: PostgreSQL (data), Redis (cache)
  └── Exposes: REST API (OpenAPI spec)

Worker (Celery)
  ├── Depends on: Redis (broker), PostgreSQL (results)
  └── Shares: Backend codebase (models, services)

Storage Service
  ├── Depends on: S3-compatible storage (AWS/R2/MinIO)
  └── Used by: Backend API, Celery Worker
```

### Data Models and Contracts

Epic 1 uses the baseline data models provided by the Vintasoftware starter template. Custom models for conversion jobs and user usage will be added in Epic 2 and Epic 3.

**User Model** (Provided by Starter):

```python
# backend/app/models/user.py
from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    tier = Column(Enum('FREE', 'PRO', 'PREMIUM', name='user_tier'), default='FREE')
    created_at = Column(DateTime, server_default=func.now())
```

**Database Schema:**

```sql
-- PostgreSQL 17.7 schema (initialized via Alembic migrations)

CREATE TYPE user_tier AS ENUM ('FREE', 'PRO', 'PREMIUM');

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    tier user_tier DEFAULT 'FREE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
```

**Configuration Schema:**

```python
# backend/app/core/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int = 6379

    # S3 Storage
    S3_BUCKET: str
    S3_REGION: str
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str

    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    class Config:
        env_file = ".env"
```

### APIs and Interfaces

**Health Check Endpoint** (Story 1.2):

```
GET /api/health

Response 200 OK:
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2025-11-28T10:30:00Z"
}

Response 503 Service Unavailable:
{
  "status": "unhealthy",
  "database": "disconnected",
  "redis": "connected",
  "timestamp": "2025-11-28T10:30:00Z"
}
```

**Authentication Endpoints** (Provided by Starter):

```
POST /api/auth/register
Request:
{
  "email": "user@example.com",
  "password": "securepassword123"
}

Response 201 Created:
{
  "id": "uuid-string",
  "email": "user@example.com",
  "tier": "FREE"
}

POST /api/auth/login
Request:
{
  "username": "user@example.com",  // Note: fastapi-users uses 'username' field
  "password": "securepassword123"
}

Response 200 OK:
{
  "access_token": "jwt-token-string",
  "token_type": "bearer"
}
```

**Frontend-Backend Integration:**

```typescript
// frontend/src/lib/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,  // Include cookies for JWT
});

export async function checkHealth() {
  const response = await apiClient.get('/api/health');
  return response.data;
}
```

**CORS Configuration:**

```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local dev
        "https://transfer2read.vercel.app",  # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Workflows and Sequencing

**Story 1.1: Project Initialization Workflow**

```
Developer → Clone Vintasoftware Template v0.0.6
         → Initialize Git repository
         → Configure .gitignore (exclude .env, node_modules, __pycache__)
         → Install frontend dependencies (npm install)
         → Install backend dependencies (pip install -r requirements.txt)
         → Verify directory structure matches Architecture
```

**Story 1.2: Database Setup Workflow**

```
Docker Compose → Start PostgreSQL 17.7 container
              → Start Redis 8.4.0 container

Backend → Load configuration from .env
       → Initialize SQLAlchemy engine (AsyncPG driver)
       → Run Alembic migrations (create users table)
       → Verify database connection via health endpoint

Test → GET /api/health
    → Assert response.status_code == 200
    → Assert response.database == "connected"
```

**Story 1.3: Frontend Setup Workflow**

```
Developer → Initialize Next.js 14 App Router
         → Install Tailwind CSS
         → Run `npx shadcn-ui@latest init`
         → Configure tailwind.config.ts with Professional Blue tokens
         → Add color variables to CSS:
           --primary: #2563eb
           --secondary: #64748b
           --success: #10b981
         → Create layout component (TopBar + Main)
         → Verify theme renders correctly on landing page
```

**Story 1.4: Worker Infrastructure Workflow**

```
Backend → Install Celery 5.5.3
       → Configure celery_app.py (Redis broker URL)
       → Create worker.py entrypoint
       → Define test task:
         @celery_app.task
         def test_task():
             return "Worker operational"

Docker Compose → Add worker service to docker-compose.yml
              → Share backend codebase volume

Test → Dispatch test_task from API
    → Verify task executes in worker logs
    → Assert task returns "Worker operational"
```

**Story 1.5: Deployment Pipeline Workflow**

```
Vercel Setup (Frontend):
  Developer → Connect GitHub repo to Vercel
           → Configure build settings (npm run build)
           → Set environment variables (NEXT_PUBLIC_API_URL)
           → Deploy to production + preview environments

Railway Setup (Backend):
  Developer → Create Railway project
           → Add PostgreSQL service (managed)
           → Add Redis service (managed)
           → Add Backend API service (Dockerfile)
           → Add Worker service (Dockerfile, different command)
           → Set environment variables (DB_URL, REDIS_URL, S3_*)
           → Configure CORS to allow Vercel domain

GitHub Actions (CI/CD):
  Push to main → Run tests (pytest backend, vitest frontend)
              → Build Docker images
              → Deploy to Railway (backend, worker)
              → Deploy to Vercel (frontend)

Verification:
  Test → Visit Vercel URL
      → Verify frontend loads
      → Call backend health endpoint
      → Assert frontend-backend communication works
```

## Non-Functional Requirements

### Performance

**NFR3: Web Interface Responsiveness**
- Target: Frontend responds to user interactions within 200ms
- Implementation: Next.js 15 with React 19 concurrent rendering, Turbopack for fast builds
- Measurement: Lighthouse performance score ≥90

**NFR6: Concurrent User Capacity**
- Target: System handles concurrent requests for up to 100 users simultaneously
- Implementation: FastAPI async request handling, Railway auto-scaling configuration
- Load Test: Use Locust to simulate 100 concurrent users on health endpoint

**Development Environment Performance:**
- Docker Compose startup: < 30 seconds for all services
- Frontend hot reload: < 2 seconds after code change
- Backend auto-reload: < 3 seconds after code change

**Deployment Performance:**
- Vercel frontend build: < 3 minutes
- Railway backend deploy: < 5 minutes
- Zero-downtime deployments via Railway blue-green strategy

### Security

**NFR10: Data Encryption at Rest**
- Requirement: All stored data encrypted using AES-256
- Implementation:
  - PostgreSQL: Enable TLS encryption on Railway managed service
  - S3: Server-side encryption enabled by default (SSE-S3 or SSE-KMS)
- Verification: Check Railway DB connection uses SSL, verify S3 bucket encryption policy

**NFR11: Data Transmission Security**
- Requirement: All data transmission uses HTTPS/TLS 1.3 or higher
- Implementation:
  - Vercel: Automatic HTTPS for all deployments
  - Railway: TLS certificates auto-provisioned
  - Frontend-Backend: HTTPS only, CORS with credentials
- Verification: SSL Labs test on production URLs (A+ rating target)

**NFR12: Password Security**
- Requirement: User passwords hashed using bcrypt with minimum 12 rounds
- Implementation: fastapi-users library handles hashing (bcrypt default)
- Configuration: Verify BCRYPT_ROUNDS >= 12 in backend settings

**NFR13: Session Token Expiration**
- Requirement: Session tokens expire after 7 days of inactivity
- Implementation: JWT ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
- Configuration: Set in backend/app/core/config.py

**NFR15: OAuth Security**
- Requirement: OAuth 2.0 standards for social authentication
- Implementation: fastapi-users OAuth integration (Google, GitHub)
- Defer to Epic 2: Social auth implementation

**NFR17: Input Validation**
- Requirement: Validate all user inputs to prevent injection attacks
- Implementation:
  - Pydantic v2 schemas for request validation
  - SQLAlchemy parameterized queries (no raw SQL)
  - Frontend: Zod schema validation before API calls

**Environment Variable Security:**
- Store secrets in .env (local), Railway/Vercel environment variables (production)
- Never commit .env to Git (.gitignore enforced)
- Rotate secrets quarterly (documented in ops runbook)

### Reliability/Availability

**NFR8: Uptime Target**
- Requirement: Web application maintains 99.5% uptime
- Implementation:
  - Vercel: 99.99% SLA for frontend (edge network)
  - Railway: 99.9% SLA for backend services
  - Health checks: Railway restarts unhealthy containers automatically
- Monitoring: Uptime Robot or Railway built-in monitoring

**NFR31: Clear Error Messages**
- Requirement: System provides clear error messages when failures occur
- Implementation:
  - Backend: Custom exception handlers return structured JSON errors
    ```json
    {
      "detail": "Database connection failed",
      "code": "DB_CONNECTION_ERROR",
      "timestamp": "2025-11-28T10:30:00Z"
    }
    ```
  - Frontend: User-friendly error displays (no raw stack traces)
  - Health endpoint: Returns degraded status with specific failure details

**NFR32: Error Logging**
- Requirement: System logs all errors for debugging without exposing sensitive data
- Implementation:
  - Backend: Structured JSON logging via structlog
  - Log levels: ERROR with stack traces, INFO for requests
  - PII Redaction: Never log passwords, tokens, or email addresses in error messages
  - Log aggregation: Railway native logs (searchable, filterable)

**Database Reliability:**
- PostgreSQL: Railway managed service with automatic backups (daily)
- Redis: Persistence enabled (AOF + RDB) for cache durability
- Connection pooling: SQLAlchemy async pool (max 20 connections)

**Graceful Degradation:**
- If Redis fails: Backend continues (no cache, performance degraded)
- If S3 fails: File operations return 503, but health endpoint stays up
- If Worker crashes: Jobs remain in queue, retry when worker restarts

### Observability

**Logging Requirements:**

- **Structured Logging:** All backend logs in JSON format for easy parsing
  ```json
  {
    "timestamp": "2025-11-28T10:30:00Z",
    "level": "INFO",
    "service": "backend",
    "request_id": "uuid-string",
    "message": "Health check called",
    "metadata": {"db_status": "connected", "redis_status": "connected"}
  }
  ```

- **Log Levels:**
  - INFO: All HTTP requests (method, path, status, duration)
  - ERROR: Exceptions with stack traces
  - DEBUG: Detailed execution flow (development only)

- **Log Retention:** Railway native logs (7 days free tier, upgrade for longer)

**Metrics Requirements:**

- **Health Endpoint Metrics:**
  - Database connection status (boolean)
  - Redis connection status (boolean)
  - API response time (ms)
  - Timestamp of last check

- **System Metrics:**
  - HTTP request rate (requests/min)
  - Error rate (errors/min)
  - Database query duration (p50, p95, p99)
  - Celery queue depth (pending tasks)

**Tracing Requirements (Epic 1 Baseline):**

- **Request ID Propagation:**
  - Generate unique request_id for each API call
  - Include in all logs for that request
  - Return in response header: `X-Request-ID`

- **Trace Context:**
  - Track request path: Frontend → Backend → Database/Redis
  - Log entry/exit points for critical operations

**Monitoring Dashboards (Epic 1 Setup):**

- Railway built-in dashboard: CPU, memory, request metrics
- Health endpoint status page: Simple HTML page showing system status
- Future: Integrate Prometheus + Grafana (post-MVP)

## Dependencies and Integrations

**Frontend Dependencies** (package.json):

```json
{
  "dependencies": {
    "next": "15.0.3",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "axios": "^1.6.0",
    "@radix-ui/react-*": "latest",
    "tailwindcss": "^3.4.0",
    "zod": "^3.22.0",
    "@tanstack/react-query": "^5.0.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "@types/node": "^20.10.0",
    "@types/react": "^19.0.0",
    "eslint": "^8.55.0",
    "prettier": "^3.1.0",
    "vitest": "^2.0.0",
    "@testing-library/react": "^14.1.0"
  }
}
```

**Backend Dependencies** (requirements.txt):

```txt
# Core Framework
fastapi==0.122.0
uvicorn[standard]==0.30.0
pydantic==2.8.0
pydantic-settings==2.4.0

# Database
sqlalchemy==2.0.36
asyncpg==0.29.0
alembic==1.13.0

# Authentication
fastapi-users[sqlalchemy]==13.0.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Task Queue
celery==5.5.3
redis==5.0.0

# Storage
boto3==1.36.0

# Utilities
python-multipart==0.0.9
python-magic==0.4.27
structlog==24.1.0

# Testing
pytest==8.3.0
pytest-asyncio==0.23.0
httpx==0.27.0
```

**System Dependencies:**

```yaml
# Docker Compose (docker-compose.yml)
services:
  postgres:
    image: postgres:17.7
    environment:
      POSTGRES_USER: transfer_app
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: transfer_app
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:8.4.0
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  backend:
    build: ./backend
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql+asyncpg://transfer_app:${DB_PASSWORD}@postgres:5432/transfer_app
      REDIS_URL: redis://redis:6379

  worker:
    build: ./backend
    command: celery -A app.worker worker --loglevel=info
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    depends_on:
      - backend
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
```

**External Service Integrations:**

| Service | Purpose | Version/Plan | Configuration |
|---------|---------|--------------|---------------|
| **Vercel** | Frontend hosting | Free tier | Auto-deploy from GitHub main branch |
| **Railway** | Backend/DB hosting | Developer plan ($5/mo) | PostgreSQL 17.7, Redis 8.4, API + Worker containers |
| **AWS S3** | File storage | Standard pricing | Bucket: `transfer2read-{env}`, Region: `us-east-1` |
| **GitHub** | Code repository | Free | Branch protection, Actions for CI/CD |

**Version Constraints:**

- Python: `>=3.13.0` (required for FastAPI 0.122.0)
- Node.js: `>=24.12.0` (LTS, required for Next.js 15)
- PostgreSQL: `>=17.0` (supports latest async features)
- Redis: `>=8.0` (latest stable)

**Integration Points:**

1. **Frontend ↔ Backend:**
   - Protocol: REST API over HTTPS
   - Authentication: JWT in HttpOnly cookies
   - CORS: Configured for Vercel domain

2. **Backend ↔ Database:**
   - Driver: AsyncPG (PostgreSQL native async)
   - Connection pool: Max 20 connections
   - Migrations: Alembic version control

3. **Backend ↔ Redis:**
   - Use cases: Celery broker, caching (future)
   - Connection: redis-py async client

4. **Worker ↔ S3:**
   - SDK: boto3 (AWS SDK for Python)
   - Authentication: IAM credentials or access keys
   - Operations: PutObject, GetObject, DeleteObject

5. **CI/CD Pipeline:**
   - Trigger: Push to main branch
   - GitHub Actions → Vercel (frontend)
   - GitHub Actions → Railway (backend, worker)

## Acceptance Criteria (Authoritative)

These criteria are extracted directly from the Epic 1 stories in `epics.md` and must be verified before marking stories complete:

### Story 1.1: Project Initialization & Monorepo Setup

- **AC1.1.1:** Repo initialized using `vintasoftware/nextjs-fastapi-starter` template
- **AC1.1.2:** Directory structure matches Architecture doc (`frontend/`, `backend/`, `docker-compose.yml`)
- **AC1.1.3:** Frontend dependencies installed (`npm install`)
- **AC1.1.4:** Backend dependencies installed (`pip install -r requirements.txt`)
- **AC1.1.5:** `docker-compose up` starts all services (frontend, backend, db) without errors
- **AC1.1.6:** Git repository initialized with `.gitignore` properly configured

### Story 1.2: Backend Core & Database Configuration

- **AC1.2.1:** PostgreSQL 15+ container running via Docker
- **AC1.2.2:** Redis container running via Docker
- **AC1.2.3:** FastAPI configured with `asyncpg` driver and SQLAlchemy (Async)
- **AC1.2.4:** Database migration system (Alembic) initialized
- **AC1.2.5:** Basic health check endpoint `GET /api/health` returns 200 OK and DB status
- **AC1.2.6:** Environment variables configured for local development (`.env`)

### Story 1.3: Frontend Foundation & UI Library

- **AC1.3.1:** Next.js 14 App Router configured
- **AC1.3.2:** Tailwind CSS installed and configured
- **AC1.3.3:** shadcn/ui initialized (`npx shadcn-ui@latest init`)
- **AC1.3.4:** "Professional Blue" color tokens added to `tailwind.config.ts` (Primary: `#2563eb`, etc.)
- **AC1.3.5:** Font families configured (Inter/Sans, Mono) per UX spec
- **AC1.3.6:** Basic layout component created (TopBar placeholder, Main content area)
- **AC1.3.7:** Landing page renders with correct theme colors

### Story 1.4: Async Worker Infrastructure

- **AC1.4.1:** Celery configured in `backend/app/core/celery_app.py`
- **AC1.4.2:** Redis configured as Celery broker and backend
- **AC1.4.3:** Worker entrypoint `backend/app/worker.py` created
- **AC1.4.4:** Docker Compose updated to include `worker` service
- **AC1.4.5:** Test task dispatched from API and executed by worker successfully
- **AC1.4.6:** Worker logs visible in Docker output

### Story 1.5: Deployment Pipeline Configuration

- **AC1.5.1:** Frontend project connected to Vercel (Production & Preview environments)
- **AC1.5.2:** Backend/Worker/DB services configured on Railway
- **AC1.5.3:** Environment variables synced to Vercel and Railway
- **AC1.5.4:** CI/CD pipeline (GitHub Actions) runs tests on PR
- **AC1.5.5:** Successful deployment of "Hello World" app to public URL
- **AC1.5.6:** Frontend can communicate with Backend in production environment

## Traceability Mapping

This table maps each Acceptance Criterion to its implementing component/service and suggested test approach:

| AC ID | Spec Section | Component/API | Test Strategy |
|-------|--------------|---------------|---------------|
| **AC1.1.1** | Overview | Git repository | Manual: Verify .git folder, check remote URL contains starter template |
| **AC1.1.2** | Project Structure | File system | Unit: Assert directories exist using `os.path.exists()` |
| **AC1.1.3** | Frontend Dependencies | package.json | Integration: Run `npm list` and verify key packages (next, react, tailwind) |
| **AC1.1.4** | Backend Dependencies | requirements.txt | Integration: Run `pip list` and verify key packages (fastapi, sqlalchemy, celery) |
| **AC1.1.5** | Docker Setup | docker-compose.yml | E2E: `docker-compose up -d` → Wait 30s → Verify all containers healthy |
| **AC1.1.6** | Git Config | .gitignore | Unit: Assert .env, node_modules, __pycache__ in .gitignore |
| **AC1.2.1** | Data Layer | PostgreSQL service | Integration: Connect to DB, execute `SELECT version()` |
| **AC1.2.2** | Data Layer | Redis service | Integration: Connect to Redis, execute `PING` command |
| **AC1.2.3** | Data Layer | backend/app/db/ | Unit: Test async session creation, verify AsyncPG driver loaded |
| **AC1.2.4** | Data Layer | Alembic migrations | Manual: Run `alembic history`, verify initial migration exists |
| **AC1.2.5** | APIs (Health) | backend/app/api/v1/health.py | Integration: `GET /api/health` → Assert 200, "database": "connected" |
| **AC1.2.6** | Core Config | .env file | Manual: Verify .env.example template exists, check required vars documented |
| **AC1.3.1** | Frontend App | frontend/src/app/ | Unit: Verify `app/page.tsx` and `app/layout.tsx` exist |
| **AC1.3.2** | Visual Foundation | tailwind.config.ts | Unit: Assert Tailwind config contains content paths |
| **AC1.3.3** | UI Components | frontend/src/components/ui/ | Integration: Run `ls components/ui/` → Verify button.tsx exists |
| **AC1.3.4** | Visual Foundation | tailwind.config.ts | Unit: Assert `--primary: #2563eb` in theme.extend.colors |
| **AC1.3.5** | Visual Foundation | CSS config | Manual: Inspect computed styles, verify font-family matches spec |
| **AC1.3.6** | UI Components | Layout component | Integration: Render layout, assert TopBar and Main elements present |
| **AC1.3.7** | Visual Foundation | Landing page | E2E: Visit localhost:3000, screenshot, verify blue primary color used |
| **AC1.4.1** | Celery Worker | backend/app/core/celery_app.py | Unit: Import celery_app, verify broker_url configured |
| **AC1.4.2** | Celery Worker | Redis connection | Integration: Verify Celery connects to Redis (check logs for connection success) |
| **AC1.4.3** | Celery Worker | backend/app/worker.py | Unit: Verify worker.py imports celery_app |
| **AC1.4.4** | Docker Setup | docker-compose.yml | Manual: Verify `worker` service defined with correct command |
| **AC1.4.5** | Workflows (Worker) | Test task execution | Integration: Dispatch `test_task()` → Poll result → Assert "Worker operational" |
| **AC1.4.6** | Observability | Docker logs | Manual: `docker-compose logs worker` → Verify task execution logged |
| **AC1.5.1** | Deployment | Vercel project | Manual: Verify Vercel dashboard shows project, production URL accessible |
| **AC1.5.2** | Deployment | Railway project | Manual: Verify Railway dashboard shows 4 services (API, Worker, PG, Redis) |
| **AC1.5.3** | Core Config | Env vars | Manual: Check Vercel/Railway settings, verify all required vars present |
| **AC1.5.4** | CI/CD | GitHub Actions | Integration: Create PR → Verify Actions run, tests execute |
| **AC1.5.5** | Deployment | Production URLs | E2E: Visit Vercel URL, assert page loads (status 200) |
| **AC1.5.6** | Integration Points | Frontend ↔ Backend | E2E: Frontend calls /api/health → Assert response received (CORS working) |

**Test Execution Order:**

1. **Unit Tests** (AC1.1.6, AC1.2.3, AC1.3.1-4, AC1.4.1, AC1.4.3): Run locally, fast feedback
2. **Integration Tests** (AC1.1.3-4, AC1.2.1-2, AC1.2.5, AC1.3.3, AC1.4.2, AC1.4.5, AC1.5.4): Require services running
3. **E2E Tests** (AC1.1.5, AC1.3.7, AC1.5.5-6): Full system verification
4. **Manual Checks** (AC1.1.1-2, AC1.2.4, AC1.2.6, AC1.3.5, AC1.4.4, AC1.4.6, AC1.5.1-3): One-time setup validation

## Risks, Assumptions, Open Questions

### Risks

**RISK-1.1: Vintasoftware Template Version Drift**
- **Risk:** Template v0.0.6 may have bugs or breaking changes not documented
- **Impact:** Medium - Could delay Story 1.1 if template has critical issues
- **Mitigation:** Test template in isolated repo first, verify all dependencies install cleanly
- **Fallback:** Use stable v0.0.5 or manually assemble stack without template

**RISK-1.2: Railway/Vercel Service Outages During Setup**
- **Risk:** Cloud providers may have downtime during deployment configuration
- **Impact:** Low - Delays deployment but doesn't block local development
- **Mitigation:** Configure deployment in Story 1.5 last (all local dev working first)
- **Fallback:** Use alternative providers (Fly.io, Render) if Railway unavailable

**RISK-1.3: S3 Bucket Configuration Complexity**
- **Risk:** S3 permissions and lifecycle policies may require trial-and-error
- **Impact:** Low - Storage service not needed until Epic 3
- **Mitigation:** Document minimal S3 configuration for Epic 1 (basic upload/download only)
- **Fallback:** Use local filesystem storage for development, defer S3 to Story 3.1

**RISK-1.4: Next.js 15 Compatibility Issues**
- **Risk:** Next.js 15 is recent (Nov 2025), may have ecosystem compatibility issues
- **Impact:** Medium - Could break shadcn/ui integration or React Query
- **Mitigation:** Test shadcn/ui installation on Next.js 15 in isolation first
- **Fallback:** Downgrade to Next.js 14.2.x (stable LTS) if blockers found

**RISK-1.5: Celery Worker Container Sharing Code**
- **Risk:** Worker container needs to share backend codebase, volume mounting may fail
- **Impact:** Medium - Blocks Story 1.4 if worker can't import backend modules
- **Mitigation:** Use Docker Compose volumes to share `./backend` directory
- **Fallback:** Copy backend code into worker image (less elegant, but functional)

### Assumptions

**ASSUMPTION-1.1: Developer Has Local Environment Ready**
- Assumes developer has Docker Desktop, Node.js 24+, Python 3.13+ installed
- If false: Add prerequisite setup time (1-2 hours)

**ASSUMPTION-1.2: GitHub Repository Already Created**
- Assumes repo exists and developer has write access
- If false: Create repo first, configure branch protection

**ASSUMPTION-1.3: Vercel/Railway Accounts Available**
- Assumes developer has accounts or can create free tier accounts
- If false: Use alternative deployment (manual VPS setup, add 4-8 hours)

**ASSUMPTION-1.4: S3 Bucket Can Be Created**
- Assumes AWS account exists or Cloudflare R2 free tier available
- If false: Defer S3 to Epic 3, use mock storage service for Epic 1

**ASSUMPTION-1.5: No Custom Domain Required for MVP**
- Assumes default Vercel/Railway domains acceptable (e.g., transfer2read.vercel.app)
- If false: Add DNS configuration task to Story 1.5

### Open Questions

**QUESTION-1.1: Which S3-Compatible Provider?**
- Options: AWS S3 (standard), Cloudflare R2 (no egress fees), MinIO (self-hosted)
- **Recommendation:** Start with AWS S3 for simplicity, migrate to R2 if costs grow
- **Decision needed by:** Story 3.1 (not Story 1.5)

**QUESTION-1.2: Monorepo or Separate Repos?**
- Current: Monorepo (frontend/ + backend/ in one repo)
- Alternative: Separate repos for frontend and backend
- **Recommendation:** Monorepo for easier coordination, matches template structure
- **Decision: RESOLVED** - Use monorepo per Architecture doc

**QUESTION-1.3: What Testing Framework for Frontend?**
- Architecture suggests Vitest, but starter template may use Jest
- **Recommendation:** Use Vitest 2.x (faster, modern, better Vite/Next.js integration)
- **Decision needed by:** Story 1.3 (frontend setup)

**QUESTION-1.4: Staging Environment Needed?**
- Current: Production + Vercel preview environments
- Alternative: Add dedicated staging environment on Railway
- **Recommendation:** Use Vercel preview for now, add staging post-MVP if needed
- **Decision: RESOLVED** - Preview environments sufficient for Epic 1

**QUESTION-1.5: CI/CD on Every Commit or Just Main?**
- Options: Deploy on all branches, only main, or main + tagged releases
- **Recommendation:** Deploy to production on main push, preview on PR creation
- **Decision needed by:** Story 1.5 (deployment pipeline)

## Test Strategy Summary

### Test Levels

**Unit Tests** (Fast, Isolated):
- Target: Configuration loading, utility functions, module imports
- Framework: pytest (backend), Vitest (frontend)
- Coverage Goal: 70% for foundation code (configs, utils)
- Run Frequency: On every file save (watch mode), pre-commit hook

**Integration Tests** (Services Running):
- Target: Database connections, API endpoints, Celery task dispatch
- Framework: pytest + TestClient (backend), React Testing Library (frontend)
- Coverage Goal: 90% for API routes and service integrations
- Run Frequency: On PR creation, before merge

**E2E Tests** (Full System):
- Target: Docker Compose startup, frontend-backend communication, deployment verification
- Framework: Manual testing + simple bash scripts for Epic 1
- Coverage Goal: All critical user paths (health check, page load)
- Run Frequency: Before deployment to production

**Manual Testing**:
- Target: One-time setup verification (template initialization, deployment config)
- Checklist: 12 manual checks (see Traceability Mapping)
- Run Frequency: Once per story completion

### Test Frameworks

**Backend Testing:**
```python
# pytest configuration (backend/pytest.ini)
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto

# Example test (tests/integration/test_health.py)
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "redis" in data
```

**Frontend Testing:**
```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
    },
  },
})

// Example test (src/components/Layout.test.tsx)
import { render, screen } from '@testing-library/react'
import { Layout } from './Layout'

test('renders TopBar and Main area', () => {
  render(<Layout><div>Content</div></Layout>)
  expect(screen.getByRole('banner')).toBeInTheDocument() // TopBar
  expect(screen.getByRole('main')).toBeInTheDocument()   // Main
})
```

### Coverage Targets

| Component | Target Coverage | Priority |
|-----------|-----------------|----------|
| Backend API Routes | 90% | High |
| Backend Config/Utils | 70% | Medium |
| Frontend Components | 70% | Medium |
| Frontend Pages | 60% | Low (E2E covers) |
| Celery Tasks | 80% | High |

### Test Execution Strategy

**Local Development:**
```bash
# Backend tests (run in backend/)
pytest                          # All tests
pytest tests/unit               # Fast unit tests only
pytest --cov=app --cov-report=html  # With coverage

# Frontend tests (run in frontend/)
npm run test                    # Watch mode
npm run test:ci                 # CI mode (run once)
npm run test:coverage           # With coverage
```

**CI Pipeline (GitHub Actions):**
```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:17.7
      redis:
        image: redis:8.4
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '24'
      - run: npm install --prefix frontend
      - run: npm run test:ci --prefix frontend
```

### Edge Cases & Boundary Testing

**Story 1.2 (Database):**
- Edge Case: Database connection fails → Health endpoint returns 503
- Boundary: Max connection pool exhausted → New requests queue or fail gracefully

**Story 1.4 (Celery Worker):**
- Edge Case: Redis broker unavailable → Worker logs connection error, retries
- Boundary: Worker crashes mid-task → Task remains in queue, restarts on worker recovery

**Story 1.5 (Deployment):**
- Edge Case: Vercel build fails → GitHub Actions marks deployment as failed, no update to production
- Boundary: Railway service restart → Zero-downtime via health checks, traffic redirected

### Regression Prevention

- **Freeze Dependencies:** Pin exact versions in requirements.txt and package.json
- **Pre-commit Hooks:** Run linters (ESLint, Ruff) and formatters (Prettier, Black) before commit
- **Branch Protection:** Require passing tests before merge to main
- **Smoke Tests:** After deployment, automated curl/fetch to health endpoint
