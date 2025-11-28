# Story 1.1: Project Initialization & Monorepo Setup

Status: ready-for-dev

## Story

As a **Developer**,
I want **to initialize the project repository with the Vintasoftware starter template**,
So that **I have a production-ready foundation with type safety, authentication, and deployment structure.**

## Acceptance Criteria

1. Repo initialized using `vintasoftware/nextjs-fastapi-starter` template v0.0.6
2. Directory structure matches Architecture doc (`frontend/`, `backend/`, `docker-compose.yml`)
3. Frontend dependencies installed successfully (`npm install` completes without errors)
4. Backend dependencies installed successfully (`pip install -r requirements.txt` completes without errors)
5. `docker-compose up` starts all services (frontend, backend, database) without errors
6. Git repository initialized with `.gitignore` properly configured to exclude `.env`, `node_modules`, `__pycache__`

## Tasks / Subtasks

- [ ] **Task 1: Clone and initialize repository** (AC: #1, #2, #6)
  - [ ] Clone `vintasoftware/nextjs-fastapi-starter` template v0.0.6 from GitHub
  - [ ] Verify directory structure: `frontend/`, `backend/`, `docker-compose.yml`, `.gitignore`
  - [ ] Initialize Git repository if not already initialized
  - [ ] Verify `.gitignore` includes: `.env`, `.env.local`, `node_modules/`, `__pycache__/`, `.next/`, `dist/`, `*.pyc`
  - [ ] Create initial commit with message "Initialize project with Vintasoftware template v0.0.6"

- [ ] **Task 2: Install frontend dependencies** (AC: #3)
  - [ ] Navigate to `frontend/` directory
  - [ ] Run `npm install` to install all Node.js dependencies
  - [ ] Verify `node_modules/` directory created
  - [ ] Verify `package-lock.json` generated
  - [ ] Check for any peer dependency warnings and resolve if critical

- [ ] **Task 3: Install backend dependencies** (AC: #4)
  - [ ] Navigate to `backend/` directory
  - [ ] Create Python virtual environment: `python3.13 -m venv venv`
  - [ ] Activate virtual environment: `source venv/bin/activate` (Unix) or `venv\Scripts\activate` (Windows)
  - [ ] Run `pip install -r requirements.txt` to install all Python dependencies
  - [ ] Verify all packages installed without conflicts
  - [ ] Check Python version compatibility (must be Python 3.13+)

- [ ] **Task 4: Verify Docker Compose configuration** (AC: #5)
  - [ ] Review `docker-compose.yml` to understand service definitions
  - [ ] Verify services defined: `postgres`, `redis`, `backend`, `frontend` (and possibly `worker` if included)
  - [ ] Create `.env` file in project root with required environment variables (see Dev Notes for template)
  - [ ] Run `docker-compose up -d` to start all services in detached mode
  - [ ] Wait for services to initialize (~30-60 seconds)
  - [ ] Check service health: `docker-compose ps` (all services should show "Up")
  - [ ] Verify logs for each service: `docker-compose logs backend`, `docker-compose logs frontend`, etc.
  - [ ] Test connectivity: Access `http://localhost:3000` (frontend) and `http://localhost:8000` (backend)

- [ ] **Task 5: Documentation and handoff**
  - [ ] Document any deviations from standard template setup in project README
  - [ ] Create `.env.example` file with all required environment variables (values redacted)
  - [ ] Verify setup instructions work on clean machine (or document known prerequisites)
  - [ ] Commit all configuration files to repository

## Dev Notes

### Architecture Context

**Foundation Stack (from architecture.md):**
- **Template:** Vintasoftware Next.js FastAPI Template v0.0.6 (verified 2025-11-27)
- **Frontend:** Next.js 15.0.3 + React 19 + TypeScript 5.x
- **Backend:** FastAPI 0.122.0 + Python 3.13.0
- **Database:** PostgreSQL 17.7 (provided by Docker Compose)
- **Cache/Queue:** Redis 8.4.0 (provided by Docker Compose)
- **Development:** Docker Compose for local orchestration

**What the Starter Provides (No Manual Setup Needed):**
- ✅ Authentication System: JWT-based auth using `fastapi-users`, password hashing, email recovery
- ✅ Database Setup: Async PostgreSQL with SQLAlchemy, Docker Compose config
- ✅ Type Safety: OpenAPI schema generation, frontend type definitions
- ✅ Dev Environment: Docker Compose with all services (frontend, backend, DB, Redis)
- ✅ Protected Routes: Frontend and backend route guards
- ✅ User Dashboard: Basic user management UI

**What Requires Custom Implementation (Later Epics):**
- ❌ Celery Workers (Epic 1, Story 1.4)
- ❌ S3 Storage (Epic 3, Story 3.1)
- ❌ PyTorch AI Pipeline (Epic 4)
- ❌ PDF Processing (Epic 4)
- ❌ Background Jobs (Epic 4)

### Project Structure Notes

**Expected Directory Structure (from Architecture):**
```
transfer_app/
├── frontend/                   # Next.js 15 Application
│   ├── src/
│   │   ├── app/                # App Router (Pages & Layouts)
│   │   ├── components/         # React Components (shadcn/ui)
│   │   │   ├── ui/             # Primitive UI components
│   │   │   └── business/       # Domain-specific components
│   │   ├── lib/                # Utilities & API Clients
│   │   └── types/              # Shared Types (generated)
│   ├── package.json
│   └── tsconfig.json
├── backend/                    # FastAPI Application
│   ├── app/
│   │   ├── api/                # API Endpoints (Routes)
│   │   │   └── v1/
│   │   ├── core/               # Config, Security, Logging
│   │   ├── db/                 # Database connection & migrations
│   │   ├── models/             # SQLAlchemy ORM Models
│   │   ├── schemas/            # Pydantic Schemas (Data Validation)
│   │   └── services/           # Business Logic Layer (to be added in later epics)
│   ├── requirements.txt
│   └── alembic/                # Database migrations
├── docker-compose.yml          # Local dev orchestration
├── .gitignore
├── .env.example
└── README.md
```

**Key Files to Verify:**
- `frontend/package.json`: Verify Next.js 15.0.3, React 19, Tailwind CSS present
- `backend/requirements.txt`: Verify FastAPI 0.122.0, SQLAlchemy 2.0.36, asyncpg present
- `docker-compose.yml`: Verify PostgreSQL 17.7 and Redis 8.4.0 images specified
- `.gitignore`: Must exclude sensitive files and build artifacts

### Environment Variables Template

Create `.env` file in project root with the following template:

```env
# Database Configuration
POSTGRES_SERVER=localhost
POSTGRES_USER=transfer_app
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=transfer_app
DATABASE_URL=postgresql+asyncpg://transfer_app:your_secure_password_here@localhost:5432/transfer_app

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379

# Backend Configuration
SECRET_KEY=your_super_secret_key_at_least_32_characters_long
ACCESS_TOKEN_EXPIRE_MINUTES=10080
BACKEND_CORS_ORIGINS=["http://localhost:3000"]

# Frontend Configuration (frontend/.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Security Note:** Never commit the actual `.env` file to Git. Create `.env.example` with placeholder values for documentation.

### Testing Strategy

**Acceptance Criteria Validation:**

1. **AC #1 (Template Initialization):**
   - Manual: Check Git remote URL or commit history for template origin
   - Verify: `git log --oneline` shows initial template commits

2. **AC #2 (Directory Structure):**
   - Unit Test: Write script to assert directories exist
   ```python
   import os
   assert os.path.exists('frontend/src/app')
   assert os.path.exists('backend/app/api')
   assert os.path.exists('docker-compose.yml')
   ```

3. **AC #3 (Frontend Dependencies):**
   - Integration: Run `npm list next react tailwindcss` to verify key packages
   - Expected: All packages installed without errors

4. **AC #4 (Backend Dependencies):**
   - Integration: Run `pip list | grep -E "fastapi|sqlalchemy|asyncpg"`
   - Expected: All packages present with correct versions

5. **AC #5 (Docker Compose):**
   - E2E Test:
   ```bash
   docker-compose up -d
   sleep 30
   docker-compose ps | grep "Up" | wc -l  # Should be >= 4 (frontend, backend, postgres, redis)
   curl http://localhost:3000  # Should return 200
   curl http://localhost:8000/docs  # Should return 200 (FastAPI docs)
   ```

6. **AC #6 (Git Configuration):**
   - Unit Test: Assert `.gitignore` contains required patterns
   ```bash
   grep -q "\.env" .gitignore && echo "PASS" || echo "FAIL"
   grep -q "node_modules" .gitignore && echo "PASS" || echo "FAIL"
   grep -q "__pycache__" .gitignore && echo "PASS" || echo "FAIL"
   ```

### Naming Conventions (from Architecture)

- **Python/Backend:** `snake_case` for variables, functions, file names. `PascalCase` for Classes.
- **TypeScript/Frontend:** `camelCase` for variables, functions. `PascalCase` for Components and Types.
- **Database:** `snake_case` for table names and columns.

### Common Issues and Solutions

**Issue 1: Python Version Mismatch**
- **Symptom:** `pip install` fails with dependency conflicts
- **Solution:** Ensure Python 3.13+ installed: `python --version`
- **Workaround:** If Python 3.13 unavailable, try Python 3.11+ (may require adjusting some package versions)

**Issue 2: Node.js Version Mismatch**
- **Symptom:** `npm install` shows peer dependency warnings
- **Solution:** Ensure Node.js 24.12.0 LTS installed: `node --version`
- **Workaround:** Use `nvm` to switch Node versions: `nvm install 24 && nvm use 24`

**Issue 3: Docker Compose Fails to Start Services**
- **Symptom:** `docker-compose ps` shows services as "Exit 1" or "Restarting"
- **Solution:** Check logs for specific service: `docker-compose logs <service_name>`
- **Common Causes:**
  - Database initialization timeout (wait 60s, retry)
  - Port conflicts (another service using 5432, 6379, 3000, or 8000)
  - Missing `.env` file (create from template above)

**Issue 4: Permission Issues on macOS/Linux**
- **Symptom:** Cannot write to directories, Docker volume mount fails
- **Solution:** Ensure current user owns project directory: `chown -R $USER:$USER .`
- **Docker:** Add user to docker group: `sudo usermod -aG docker $USER` (logout/login required)

**Issue 5: Template Version Not Found**
- **Symptom:** GitHub shows template but v0.0.6 tag doesn't exist
- **Solution:** Clone latest stable version: `git clone --branch v0.0.6 https://github.com/vintasoftware/nextjs-fastapi-template.git`
- **Fallback:** If tag unavailable, use main branch and document version in README

### Prerequisites

- **Before Starting This Story:**
  - Docker Desktop installed and running (version 4.x+)
  - Node.js 24.12.0 LTS installed (verify: `node --version`)
  - Python 3.13.0 installed (verify: `python --version`)
  - Git installed (verify: `git --version`)
  - GitHub account with access to Vintasoftware template
  - Text editor or IDE (VS Code recommended)

- **Dependencies:**
  - None (this is the first story in the project)

### References

- [Source: docs/architecture.md#Project-Initialization]
- [Source: docs/epics.md#Story-1.1]
- [Source: docs/sprint-artifacts/tech-spec-epic-1.md#Story-1.1-Workflow]
- [Vintasoftware Template: https://github.com/vintasoftware/nextjs-fastapi-template]
- [Architecture Decision: ADR-001 Hybrid Intelligence Architecture]

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/1-1-project-initialization-monorepo-setup.context.xml

### Agent Model Used

<!-- Agent model name and version will be recorded here during implementation -->

### Debug Log References

<!-- Links to debug logs or error traces will be added here during implementation -->

### Completion Notes List

<!-- Dev agent will document:
- Setup steps completed
- Configuration decisions made
- Deviations from standard setup
- Integration verification results
- Files created or modified
-->

### File List

<!-- Dev agent will list all files created, modified, or deleted:
- NEW: <file_path> - <description>
- MODIFIED: <file_path> - <changes made>
- DELETED: <file_path> - <reason>
-->
