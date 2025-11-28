# Transfer2Read - PDF to EPUB Conversion Platform

A full-stack web application for converting PDF documents to EPUB format with AI-powered layout analysis and structure recognition.

## Tech Stack

**Foundation:** Vintasoftware Next.js FastAPI Template v0.0.6

**Frontend:**
- Next.js 15.0.3 + React 19 + TypeScript 5.x
- Tailwind CSS + shadcn/ui components
- Node.js 24.12.0 LTS

**Backend:**
- FastAPI 0.122.0 + Python 3.12+ (3.13 recommended)
- SQLAlchemy 2.0.36 (Async ORM)
- fastapi-users (JWT authentication)

**Infrastructure:**
- PostgreSQL 17 (Docker)
- MailHog (Local email testing)
- Docker Compose for local development

## Prerequisites

- **Docker Desktop** 4.x+ (required for all services)
- **Node.js** 24.12.0 LTS or higher ([Download](https://nodejs.org/))
- **Python** 3.12+ (3.13 recommended) ([Download](https://www.python.org/))
- **UV** (Python package installer) - Optional but recommended ([Install](https://astral.sh/uv))
- **Git** ([Download](https://git-scm.com/))

## Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd Transfer2Read
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

**Important:** Update the following values in `.env` before deploying to production:
- `POSTGRES_PASSWORD` - Use a strong, unique password
- `ACCESS_SECRET_KEY` - Generate with: `openssl rand -hex 32`
- `RESET_PASSWORD_SECRET_KEY` - Generate with: `openssl rand -hex 32`
- `VERIFICATION_SECRET_KEY` - Generate with: `openssl rand -hex 32`

### 3. Install Dependencies

**Frontend:**
```bash
cd frontend
npm install
```

**Backend (Option 1 - UV recommended):**
```bash
cd backend
uv sync
```

**Backend (Option 2 - pip):**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Start Services with Docker Compose

```bash
docker-compose up -d
```

Wait ~30-60 seconds for services to initialize, then access:

- **Frontend:** http://localhost:3000
- **Backend API Docs:** http://localhost:8000/docs
- **MailHog UI:** http://localhost:8025

### 5. Verify Setup

Check all services are running:

```bash
docker-compose ps
```

Expected output: All services show status "Up"

## Project Structure

```
Transfer2Read/
├── frontend/              # Next.js 15 Application
│   ├── app/               # App Router (Pages & Layouts)
│   ├── components/        # React Components
│   │   ├── ui/            # shadcn/ui primitives
│   │   └── actions/       # Server actions
│   ├── lib/               # Utilities & API clients
│   └── package.json
├── backend/               # FastAPI Application
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── models.py      # SQLAlchemy models
│   │   ├── schemas.py     # Pydantic schemas
│   │   └── users.py       # Authentication logic
│   ├── tests/             # Pytest test suite
│   ├── requirements.txt   # Python dependencies
│   └── pyproject.toml     # UV/pip configuration
├── docker-compose.yml     # Development orchestration
├── .env                   # Environment variables (not committed)
├── .env.example           # Template for .env
└── README.md              # This file
```

## Development Notes

### Deviations from Standard Template

1. **Directory Naming:** Template uses `fastapi_backend/` and `nextjs-frontend/`. We renamed to `backend/` and `frontend/` to match architecture spec.

2. **Docker Compose Environment Variables:** Added comprehensive environment variables for backend service (ACCESS_SECRET_KEY, RESET_PASSWORD_SECRET_KEY, VERIFICATION_SECRET_KEY, CORS_ORIGINS, etc.) to fix startup validation errors.

3. **Python Version:** Architecture specifies Python 3.13, but template was tested with Python 3.12.9. Both versions work correctly.

4. **Redis:** Template does not include Redis by default. Redis will be added in Story 1.4 (Async Worker Infrastructure).

5. **Docker Ignore Files:** Created `.dockerignore` files for frontend and backend to exclude `node_modules` and `.venv` from Docker builds.

6. **Security Fixes:** Ran `npm audit fix` to resolve 5 vulnerabilities (1 critical, 2 high, 1 moderate, 1 low) in frontend dependencies.

### Common Issues

**Issue:** Docker containers fail to start
**Solution:** Ensure Docker Desktop is running, then run `docker-compose up -d --build`

**Issue:** Backend validation errors on startup
**Solution:** Verify all required environment variables are set in docker-compose.yml

**Issue:** Port conflicts (3000, 8000, 5432, 8025)
**Solution:** Stop conflicting services or modify ports in docker-compose.yml

**Issue:** Permission denied errors on macOS/Linux
**Solution:** Run `chown -R $USER:$USER .` to fix ownership

## Testing

**Frontend:**
```bash
cd frontend
npm test
```

**Backend:**
```bash
cd backend
source venv/bin/activate  # or .venv/bin/activate if using UV
pytest
```

## What's Included (From Template)

✅ **Authentication System:** JWT-based auth with fastapi-users, password hashing, email recovery
✅ **Database Setup:** Async PostgreSQL with SQLAlchemy, migrations via Alembic
✅ **Type Safety:** OpenAPI schema generation, frontend type definitions
✅ **Protected Routes:** Frontend and backend route guards
✅ **Dev Environment:** Docker Compose with hot reload

## What Requires Custom Implementation (Future Epics)

❌ **Celery Workers** (Epic 1, Story 1.4)
❌ **S3 Storage** (Epic 3, Story 3.1)
❌ **PDF Processing Pipeline** (Epic 4)
❌ **AI Layout Analysis** (Epic 4)
❌ **Background Job Queue** (Epic 4)

## Documentation

- [Architecture](docs/architecture.md)
- [Product Requirements](docs/prd.md)
- [UX Design Specification](docs/ux-design-specification.md)
- [Epic Tech Specs](docs/sprint-artifacts/)

## License

[Add license information]

## Contributing

[Add contribution guidelines]
