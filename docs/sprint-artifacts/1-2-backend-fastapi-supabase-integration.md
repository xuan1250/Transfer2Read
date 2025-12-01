# Story 1.2: Backend FastAPI & Supabase Integration

Status: ready-for-dev

## Story

As a **Developer**,
I want **to set up FastAPI with Supabase Python client**,
So that **the backend can authenticate users and access managed PostgreSQL.**

## Acceptance Criteria

1. **FastAPI 0.122.0** installed with `uvicorn[standard]`
2. **Supabase Python Client 2.24.0** installed and configured
3. **Redis 8.4.0** container running via `docker-compose.yml` (for Celery only)
4. Backend `.env` file with Supabase credentials:
   - `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
   - `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` (placeholders for now)
   - `REDIS_URL=redis://localhost:6379`
5. **Supabase client initialized** in `backend/app/core/supabase.py`
6. Health check endpoint `GET /api/health` returns:
   - `200 OK` with Supabase connection status
   - Redis connection status
7. **SQLAlchemy 2.0.36** installed for local models (if needed)

## Tasks / Subtasks

- [ ] Task 1: Set up FastAPI backend structure (AC: #1, #7)
  - [ ] 1.1: Create `backend/` directory with proper Python package structure
  - [ ] 1.2: Install FastAPI 0.122.0 and uvicorn[standard] via pip
  - [ ] 1.3: Create `backend/app/main.py` with FastAPI app initialization
  - [ ] 1.4: Install SQLAlchemy 2.0.36 for ORM support
  - [ ] 1.5: Create `backend/requirements.txt` with all core dependencies

- [ ] Task 2: Configure Supabase Python client (AC: #2, #5)
  - [ ] 2.1: Install Supabase Python client 2.24.0 (`supabase==2.24.0`)
  - [ ] 2.2: Create `backend/app/core/` directory for configuration modules
  - [ ] 2.3: Create `backend/app/core/supabase.py` with client initialization
  - [ ] 2.4: Implement async Supabase client getter function
  - [ ] 2.5: Add connection verification logic

- [ ] Task 3: Set up Redis container for Celery broker (AC: #3)
  - [ ] 3.1: Create `docker-compose.yml` in project root
  - [ ] 3.2: Define Redis 8.4.0-alpine service in docker-compose
  - [ ] 3.3: Configure Redis persistence (volume mapping)
  - [ ] 3.4: Expose Redis port 6379 for local access
  - [ ] 3.5: Test Redis container startup with `docker-compose up -d redis`

- [ ] Task 4: Configure environment variables and secrets (AC: #4)
  - [ ] 4.1: Create `backend/.env.example` template with all required variables
  - [ ] 4.2: Document Supabase credential retrieval (URL, anon key, service key)
  - [ ] 4.3: Add AI API key placeholders (OPENAI_API_KEY, ANTHROPIC_API_KEY)
  - [ ] 4.4: Configure Redis connection URL (redis://localhost:6379)
  - [ ] 4.5: Add `.env` to `.gitignore` to prevent secret leakage

- [ ] Task 5: Implement health check endpoint (AC: #6)
  - [ ] 5.1: Create `backend/app/api/` directory structure
  - [ ] 5.2: Create `backend/app/api/health.py` with health check route
  - [ ] 5.3: Implement Supabase connection health check
  - [ ] 5.4: Implement Redis connection health check
  - [ ] 5.5: Return JSON response with status of all services
  - [ ] 5.6: Handle connection failures gracefully (503 Service Unavailable)

- [ ] Task 6: Integration testing and verification (AC: #1-7)
  - [ ] 6.1: Start Redis container via docker-compose
  - [ ] 6.2: Start FastAPI backend with `uvicorn app.main:app --reload`
  - [ ] 6.3: Test `GET /api/health` endpoint returns 200 OK
  - [ ] 6.4: Verify Supabase connection status is "connected"
  - [ ] 6.5: Verify Redis connection status is "connected"
  - [ ] 6.6: Write integration test for health endpoint

## Dev Notes

### Architecture Context

**Technology Stack (Updated 2025-12-01):**
- **Backend Framework:** FastAPI 0.122.0 (latest stable, Nov 2025)
- **Python Runtime:** Python 3.13.0
- **Database & Auth:** Supabase (managed PostgreSQL + Auth + Storage)
- **Supabase Client:** supabase-py 2.24.0 (async support, server-side operations)
- **ORM:** SQLAlchemy 2.0.36 (async support, type hints)
- **Message Broker:** Redis 8.4.0 (for Celery task queue only)
- **Deployment:** Railway (backend containers + managed Redis)

**Critical Architectural Change:**
This story implements the **NEW architecture** (2025-12-01 update) which uses **Supabase** as the unified backend platform instead of self-managed PostgreSQL. The Vintasoftware template approach has been replaced with a **from-scratch** build for full control over Supabase integration.

**ADR Reference:**
- **ADR-002:** Supabase as Unified Backend Platform
  - Rationale: Managed auth, database, and storage reduce infrastructure complexity
  - Built-in Row Level Security (RLS) for data isolation
  - Real-time capabilities for future enhancements
  - No database administration overhead

### Project Structure Notes

**Backend Directory Structure:**
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── api/
│   │   ├── __init__.py
│   │   └── health.py          # Health check endpoint
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Environment variables
│   │   └── supabase.py        # Supabase client setup
│   ├── models/                # SQLAlchemy models (future)
│   ├── schemas/               # Pydantic schemas (future)
│   └── services/              # Business logic (future)
├── .env                       # Environment variables (gitignored)
├── .env.example              # Template for required variables
├── requirements.txt          # Python dependencies
└── pyproject.toml           # Optional: Poetry/modern tooling
```

**Docker Compose Structure:**
```yaml
version: '3.8'
services:
  redis:
    image: redis:8.4.0-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes  # Enable persistence
volumes:
  redis-data:
```

### Supabase Integration Details

**Supabase Client Initialization Pattern:**
```python
# backend/app/core/supabase.py
from supabase import create_client, Client
from app.core.config import settings

def get_supabase_client() -> Client:
    """
    Initialize Supabase client with service role key for admin operations.
    Use service_role key for backend (not anon key - that's for frontend).
    """
    return create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_SERVICE_KEY
    )

# Usage in endpoints
supabase: Client = get_supabase_client()
```

**Health Check Implementation Pattern:**
```python
# backend/app/api/health.py
from fastapi import APIRouter
from app.core.supabase import get_supabase_client
import redis

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Health check endpoint verifying Supabase and Redis connectivity.
    Returns 200 if all services healthy, 503 if any service unavailable.
    """
    status = {
        "status": "healthy",
        "database": "unknown",
        "redis": "unknown"
    }

    # Check Supabase connection
    try:
        supabase = get_supabase_client()
        # Simple query to verify connection
        result = supabase.table("_health_check_dummy").select("*").limit(1).execute()
        status["database"] = "connected"
    except Exception as e:
        status["status"] = "unhealthy"
        status["database"] = f"disconnected: {str(e)}"

    # Check Redis connection
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        status["redis"] = "connected"
    except Exception as e:
        status["status"] = "unhealthy"
        status["redis"] = f"disconnected: {str(e)}"

    return status, 200 if status["status"] == "healthy" else 503
```

### Required Environment Variables

**Backend `.env` File:**
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key  # KEEP SECRET - admin access

# AI API Keys (Placeholders for Story 1.4)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Redis Configuration (Local Development)
REDIS_URL=redis://localhost:6379

# Celery Configuration (For Story 1.4)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Application Configuration
ENVIRONMENT=development
```

**Security Notes:**
- **NEVER commit `.env`** to Git (verify `.gitignore` includes it)
- **Service Role Key:** Use for backend admin operations (bypasses RLS)
- **Anon Key:** Reserved for frontend client (respects RLS policies)
- **Credential Rotation:** Plan quarterly rotation for production keys

### Testing Strategy

**Integration Test Example:**
```python
# backend/tests/integration/test_health.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health_endpoint_success():
    """Test health endpoint returns 200 when all services available."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["redis"] == "connected"

@pytest.mark.asyncio
async def test_health_endpoint_redis_down():
    """Test health endpoint returns 503 when Redis unavailable."""
    # Mock Redis connection to fail
    # ... (use pytest monkeypatch)
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "disconnected" in data["redis"]
```

### Dependencies and Versions

**Core Python Dependencies (requirements.txt):**
```txt
# FastAPI Framework
fastapi==0.122.0
uvicorn[standard]==0.30.0
pydantic==2.8.0
pydantic-settings==2.4.0

# Supabase Client
supabase==2.24.0

# Database ORM
sqlalchemy==2.0.36
asyncpg==0.29.0

# Redis Client
redis==5.0.1

# Utilities
python-dotenv==1.0.0
```

**Version Verification:**
All versions verified 2025-12-01 for mutual compatibility:
- FastAPI 0.122.0 → Latest stable (Nov 2025)
- Python 3.13.0 → Compatible with FastAPI 0.122.0
- Supabase 2.24.0 → Latest stable (Nov 2025), async support
- SQLAlchemy 2.0.36 → Latest stable, async support
- Redis 8.4.0 → Latest stable (Nov 2025)

### References

- [Source: docs/architecture.md#Project-Initialization] - Supabase setup instructions
- [Source: docs/architecture.md#ADR-002] - Supabase as unified backend platform rationale
- [Source: docs/epics.md#Story-1.2] - Original acceptance criteria
- [Source: docs/sprint-artifacts/tech-spec-epic-1.md#System-Architecture-Alignment] - Foundation components
- [Supabase Python Docs](https://supabase.com/docs/reference/python/introduction) - Official client documentation
- [FastAPI Async](https://fastapi.tiangolo.com/async/) - Async patterns for FastAPI

### Learnings from Previous Story

**From Story 1-1-project-initialization-supabase-setup:**

*Note: Previous story file not found (still in-progress). This is the second story in Epic 1, implementing backend infrastructure on top of the Supabase project initialized in Story 1.1.*

**Expected Prerequisites from Story 1.1:**
- Supabase project created at supabase.com
- Storage buckets configured (`uploads` and `downloads`)
- Authentication enabled (Email/Password provider)
- Environment variables documented (SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY)
- Project directory structure created (`transfer_app/frontend/`, `transfer_app/backend/`)

**Key Integration Points:**
- This story **consumes** Supabase credentials from Story 1.1
- This story **produces** health check API for Story 1.3 (frontend integration)
- This story **enables** Story 1.4 (Celery worker setup using Redis)

### Known Constraints

**Development Environment:**
- Requires Docker Desktop for Redis container
- Requires active internet connection for Supabase API calls
- Supabase free tier: 500MB database, 1GB file storage (sufficient for dev)

**Performance Targets:**
- Health check endpoint: < 200ms response time
- Supabase client initialization: < 100ms
- Redis connection: < 50ms

**Security Constraints:**
- Service role key bypasses RLS - use carefully, validate user context
- Local Redis has no authentication (acceptable for dev, not production)
- CORS will need configuration in Story 1.3 for frontend access

### Change Log

- **2025-12-01:** Story drafted based on updated architecture (Supabase + API-based AI)
- **Source:** Epic 1, Story 1.2 from epics.md (enhanced with architectural context)

## Dev Agent Record

### Context Reference

- Story Context: docs/sprint-artifacts/1-2-backend-fastapi-supabase-integration.context.xml

### Agent Model Used

Claude 3.5 Sonnet (claude-sonnet-4-5-20250929)

### Debug Log References

### Completion Notes List

### File List
