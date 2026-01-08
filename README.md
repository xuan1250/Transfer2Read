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
**Task Queue:** Celery + Redis 8.4
**Deployment:** Docker Compose (self-hosted)

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker:** 20.10+ with Docker Compose 2.0+ ([download](https://www.docker.com/products/docker-desktop/))
- **Supabase Account:** Free tier for database, auth, and storage ([sign up](https://supabase.com/))
- **AI API Keys:** OpenAI API (GPT-4o) + Anthropic API (Claude 3 Haiku)
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

### 3. Docker Deployment

Transfer2Read uses Docker Compose for easy deployment with all services containerized.

**Clone and Configure:**
```bash
# Clone the repository
git clone https://github.com/youruser/transfer2read.git
cd transfer2read

# Copy environment template
cp .env.example .env

# Edit .env with your actual credentials
nano .env
```

**Start All Services:**
```bash
# Build and start all containers (frontend, backend-api, backend-worker, redis)
docker-compose up -d --build

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

**Access the Application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Health Check: http://localhost:8000/api/health

**Docker Commands:**
```bash
# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# View logs for specific service
docker-compose logs -f backend-api
docker-compose logs -f frontend
docker-compose logs -f backend-worker

# Restart a service
docker-compose restart backend-api

# Scale worker processes (for high load)
docker-compose up -d --scale backend-worker=3
```

### 4. Local Development Setup (Without Docker)

For development purposes, you can run services locally without Docker:

**Backend Setup:**
```bash
cd backend
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend Setup:**
```bash
cd frontend
npm install
npm run dev  # Starts on http://localhost:3000
```

**Redis (Required):**
```bash
# Using Docker for Redis only
docker run -d -p 6379:6379 redis:8.4.0-alpine
```

### 5. Production Deployment Considerations

**Hardware Requirements:**
- CPU: 4+ cores (AI processing intensive)
- RAM: 8GB minimum, 16GB recommended
- Storage: 50GB+ for Docker images and temp files

**Security Checklist:**
- ✅ `.env` file excluded from version control (.gitignore)
- ✅ Use production Supabase project (separate from development)
- ✅ Configure firewall to expose only ports 3000/8000 if needed
- ✅ Enable HTTPS via reverse proxy (nginx/Caddy) for production
- ✅ Set `ENVIRONMENT=production` in `.env`
- ✅ Regular Docker image updates: `docker-compose pull && docker-compose up -d`

**Monitoring:**
```bash
# Container health
docker-compose ps

# Resource usage
docker stats

# Application logs
docker-compose logs --tail=100 -f

# Redis connection test
docker exec transfer2read-redis redis-cli ping
```

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

## Troubleshooting

### Common Docker Issues

**Port conflicts:**
```bash
# Check if ports are already in use
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :6379  # Redis

# Solution: Stop conflicting processes or change ports in docker-compose.yml
```

**Service startup order issues:**
```bash
# If worker fails because backend-api isn't ready:
docker-compose restart backend-worker

# Or add healthcheck wait in docker-compose.yml (already configured)
```

**Environment variable errors:**
```bash
# Verify .env file exists and has all required variables
cat .env

# Check if containers can read environment variables
docker-compose exec backend-api printenv | grep SUPABASE
```

**Build failures:**
```bash
# Clean Docker cache and rebuild
docker-compose down
docker system prune -f
docker-compose up -d --build
```

**Frontend not loading:**
- Check if `NEXT_PUBLIC_BACKEND_URL` is set correctly in `.env`
- Verify backend-api is running: `curl http://localhost:8000/api/health`
- Check browser console for errors

**Worker not processing tasks:**
- Check worker logs: `docker-compose logs backend-worker`
- Verify Redis connection: `docker exec transfer2read-redis redis-cli ping`
- Restart worker: `docker-compose restart backend-worker`

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Follow coding standards in `docs/architecture.md`
4. Add tests for new functionality
5. Submit pull request

## License

MIT License - see LICENSE file for details

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
