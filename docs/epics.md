# Transfer2Read - Epic and Story Breakdown

**Project:** Transfer2Read  
**Originally Created:** 2025-11-27  
**Last Updated:** 2025-12-01 (Architecture Enhancement)  
**Product Manager:** xavier  
**Context:** PRD + UX Design + Architecture (Supabase + API-Based AI)  

---

## Document Purpose

This document provides a comprehensive breakdown of Transfer2Read into **implementable epics and detailed user stories**. Each story includes:
- BDD-style acceptance criteria
- Technical implementation guidance
- References to UX mockups and Architecture decisions
- Prerequisites and dependencies

**Usage:** Dev agents will use this document during Phase 4 (Implementation) to build the application story-by-story.

**Version History:**
- **2025-11-27:** Initial epic breakdown with PRD + UX + Architecture (original PyTorch-based)
- **2025-12-01:** Enhanced with updated Architecture (Supabase + LangChain + GPT-4o/Claude API-based AI)

---

## Step 0: Workflow Mode Detection

🔄 **UPDATE MODE - Architecture Enhancement**

Existing epics found from 2025-11-27. Enhancing stories with NEW architecture context.

**Available Context:**
- ✅ PRD (required) - Complete functional requirements (47 FRs)
- ✅ UX Design - Complete specification (Direction 3: Preview Focused, Professional Blue theme)
- ✅ **Architecture (UPDATED 2025-12-01)** - New technical stack with Supabase + API-based AI

**Architecture Changes Incorporated:**

**Major Updates:**
1. **Authentication & Database:** Added **Supabase** for unified auth, PostgreSQL, and file storage (replaces self-managed PostgreSQL + S3)
2. **AI Processing:** Changed from local PyTorch models → **API-based AI** (GPT-4o primary, Claude 3 Haiku fallback via LangChain)
3. **Deployment:** Updated to **Vercel** (frontend) + **Railway** (backend + workers)
4. **Storage:** Migrated from generic S3 → **Supabase Storage** with built-in security policies

**Technical Stack (Current):**
- Frontend: Next.js 15.0.3 + shadcn/ui + **Supabase JS Client**
- Backend: FastAPI 0.122.0 + **Supabase Python Client** + LangChain 0.3.12
- AI: **GPT-4o** (OpenAI) + **Claude 3 Haiku** (Anthropic) via LangChain
- Queue: Celery 5.5.3 + Redis 8.4.0
- Database/Auth/Storage: **Supabase** (managed PostgreSQL + Auth + Storage)

This update enhances all stories with specific Supabase integration details and API-based AI implementation guidance.

---

## Step 1: FR Inventory from PRD

Extracting all Functional Requirements from PRD to ensure complete coverage:

### User Account & Access
- **FR1:** Users can create accounts using email/password authentication
- **FR2:** Users can create accounts using social authentication (Google, GitHub)
- **FR3:** Users can log in securely with email/password or social auth
- **FR4:** Users can reset forgotten passwords via email verification
- **FR5:** Users can view their account profile and settings
- **FR6:** Users can see their current subscription tier (Free, Pro, Premium)
- **FR7:** Users can upgrade or change their subscription tier

### PDF File Upload & Management
- **FR8:** Users can upload PDF files via drag-and-drop interface
- **FR9:** Users can upload PDF files via file browser selection
- **FR10:** Users can upload PDF files up to 50MB in Free tier
- **FR11:** Users can upload PDF files with no size limit in Pro/Premium tiers
- **FR12:** System validates uploaded files are valid PDFs before processing
- **FR13:** Users can view their conversion history (past uploads and conversions)
- **FR14:** Users can re-download previously converted EPUB files
- **FR15:** Users can delete files from their conversion history

### AI-Powered PDF Analysis & Conversion
- **FR16:** System analyzes PDF layout to detect complex elements (tables, charts, images, equations, multi-column layouts)
- **FR17:** System preserves table structures with correct alignment and cell content during conversion
- **FR18:** System preserves images and charts with original positioning and captions
- **FR19:** System renders mathematical equations correctly using MathML or high-quality image fallback
- **FR20:** System intelligently reflows multi-column layouts into single-column EPUB format
- **FR21:** System handles mixed-language documents (e.g., English + Chinese + Japanese)
- **FR22:** System embeds appropriate fonts for special characters to prevent missing glyphs
- **FR23:** System detects document type (technical vs. narrative) and adapts conversion strategy
- **FR24:** System achieves 95%+ fidelity for complex PDF elements
- **FR25:** System achieves 99%+ fidelity for text-based PDFs

### AI Structural Analysis
- **FR26:** System auto-detects document structure (chapters, sections, headings)
- **FR27:** System auto-generates Table of Contents from detected structure
- **FR28:** System identifies and tags chapter breaks in EPUB output
- **FR29:** System recognizes and properly tags headers and titles with correct hierarchy

### Conversion Process & Feedback
- **FR30:** Users can initiate PDF to EPUB conversion with one action
- **FR31:** Users can view real-time conversion progress during processing
- **FR32:** Users can see quality indicators during conversion (detected elements count)
- **FR33:** Users receive a quality report after conversion showing detected elements (tables, images, chapters)
- **FR34:** Users can preview before/after comparison of converted content
- **FR35:** System completes conversion of 300-page technical book in under 2 minutes

### EPUB Output & Download
- **FR36:** System generates reflowable EPUB files from PDF input
- **FR37:** System produces EPUB files with file size ≤ 120% of original PDF
- **FR38:** Users can download converted EPUB files
- **FR39:** Generated EPUBs are compatible with major e-readers (Apple Books, Kindle, Kobo, Google Play Books)
- **FR40:** Generated EPUBs preserve formatting when opened on target devices

### Usage Limits & Tier Management
- **FR41:** Free tier users can convert up to 5 PDFs per month
- **FR42:** Free tier users can upload files up to 50MB
- **FR43:** Pro/Premium tier users have unlimited conversions
- **FR44:** Pro/Premium tier users have no file size limits
- **FR45:** System tracks user's monthly conversion count for Free tier
- **FR46:** System notifies users when approaching tier limits
- **FR47:** System prevents conversions that exceed tier limits and prompts upgrade

**Total Functional Requirements:** 47 FRs

---

## Step 2: Proposed Epic Structure

### Epic Analysis & Grouping

After analyzing all 47 FRs, I've identified **6 natural epic groupings** that deliver incremental USER VALUE:

### ✅ Epic 1: Project Foundation & Deployment Pipeline
**Goal:** Establish technical foundation for all subsequent development  
**User Value:** Necessary infrastructure to enable the application to exist  
**Validation:** Foundation epic (acceptable as first epic for greenfield)

### ✅ Epic 2: User Identity & Account Management
**Goal:** Users can create accounts, log in, and manage their profiles  
**User Value:** Users can identify themselves and access the platform  
**What users can do:** Sign up, log in, view their account, manage subscription tiers

### ✅ Epic 3: PDF Upload & File Management
**Goal:** Users can upload PDFs and manage their conversion history  
**User Value:** Users can get their PDF files into the system and track past conversions  
**What users can do:** Upload PDFs via drag-drop or file browser, view conversion history, re-download EPUBs

### ✅ Epic 4: AI-Powered Conversion Engine (Core Value)
**Goal:** System converts complex PDFs to EPUBs with 95%+ fidelity  
**User Value:** **THE differentiator** - users get perfect conversions of complex technical documents  
**What users can do:** Convert their PDFs and **trust the output quality**

### ✅ Epic 5: Quality Preview & Download Experience
**Goal:** Users verify conversion quality before downloading  
**User Value:** Confidence through visual proof - novel UX pattern that builds trust  
**What users can do:** See before/after comparison, verify perfect formatting, download with confidence

### ✅ Epic 6: Usage Tiers & Limits Enforcement
**Goal:** System enforces tier limits and enables upgrades  
**User Value:** Free users can try the service, paying users get unlimited access  
**What users can do:** Use freemium tier, upgrade to Pro/Premium for more conversions

---

### FR Coverage Mapping

Validating that EVERY FR maps to at least one epic:

**Epic 1: Foundation (Greenfield Setup)**
- Infrastructure needs for all FRs (no specific FR, enables everything)

**Epic 2: User Identity & Account Management**
- FR1: Email/password authentication  
- FR2: Social authentication (Google, GitHub)  
- FR3: Login functionality  
- FR4: Password reset  
- FR5: View profile and settings  
- FR6: View subscription tier  
- FR7: Upgrade/change subscription tier

**Epic 3: PDF Upload & File Management**
- FR8: Drag-and-drop PDF upload  
- FR9: File browser PDF upload  
- FR10: 50MB limit for Free tier  
- FR11: No size limit for Pro/Premium  
- FR12: PDF validation before processing  
- FR13: View conversion history  
- FR14: Re-download EPUBs  
- FR15: Delete files from history

**Epic 4: AI-Powered Conversion Engine**
- FR16: Detect complex elements (tables, charts, images, equations, multi-column)  
- FR17: Preserve table structures  
- FR18: Preserve images and charts  
- FR19: Render equations correctly  
- FR20: Reflow multi-column layouts  
- FR21: Handle mixed-language documents  
- FR22: Embed appropriate fonts  
- FR23: Detect document type and adapt strategy  
- FR24: 95%+ fidelity for complex PDFs  
- FR25: 99%+ fidelity for text-based PDFs  
- FR26: Auto-detect document structure  
- FR27: Auto-generate Table of Contents  
- FR28: Tag chapter breaks  
- FR29: Tag headers and titles  
- FR36: Generate reflowable EPUB files  
- FR37: EPUB file size ≤ 120% of PDF  
- FR39: EPUB compatibility with major e-readers  
- FR40: Preserve formatting on target devices

**Epic 5: Quality Preview & Download Experience**
- FR30: Initiate conversion with one action  
- FR31: View real-time conversion progress  
- FR32: See quality indicators during conversion  
- FR33: Receive quality report after conversion  
- FR34: Preview before/after comparison  
- FR35: \u003c2 minutes for 300-page book  
- FR38: Download converted EPUB files

**Epic 6: Usage Tiers & Limits Enforcement**
- FR41: Free tier: 5 conversions/month  
- FR42: Free tier: 50MB file size limit  
- FR43: Pro/Premium: unlimited conversions  
- FR44: Pro/Premium: no file size limits  
- FR45: Track monthly conversion count  
- FR46: Notify when approaching tier limits  
- FR47: Prevent conversions exceeding tier limits

---

### Coverage Validation

✅ **All 47 FRs are mapped to epics**

**Coverage Summary:**
- Epic 1 (Foundation): 0 direct FRs (infrastructure enabler)
- Epic 2 (Account): 7 FRs (FR1-FR7)
- Epic 3 (Upload): 8 FRs (FR8-FR15)
- Epic 4 (Conversion): 18 FRs (FR16-FR29, FR36-FR37, FR39-FR40)
- Epic 5 (Preview): 7 FRs (FR30-FR35, FR38)
- Epic 6 (Tiers): 7 FRs (FR41-FR47)

**Total:** 47 FRs covered ✓

---

### Epic Sequencing Rationale

**Why this order:**

1. **Foundation First** - Greenfield exception: Must establish project structure, deployment pipeline, and core infrastructure before building features

2. **User Identity Next** - Users need to create accounts before uploading files or converting PDFs (prerequisite for all user actions)

3. **Upload After Identity** - Once users can log in, they need to upload PDFs (prerequisite for conversion)

4. **Conversion Engine** - The CORE VALUE - AI-powered conversion that makes Transfer2Read different from competitors

5. **Quality Preview** - The novel UX pattern that builds trust by showing users the quality BEFORE download

6. **Tier Limits Last** - Once core value is proven, enforce business model (freemium → paid upgrades)

**Value Delivery Check:**

| Epic | User Value Delivered |
|------|---------------------|
| Epic 1 | Foundation exists (necessary exception) |
| Epic 2 | Users can sign up and log in ✅ |
| Epic 3 | Users can upload PDFs and see history ✅ |
| Epic 4 | Users get perfect EPUB conversions ✅ (CORE VALUE) |
| Epic 5 | Users verify quality before downloading ✅ (DIFFERENTIATOR) |
| Epic 6 | Users understand limits and can upgrade ✅ |

**All epics deliver incremental user value ✓**

---

## Step 3: Epic Decomposition

### Epic 1: Project Foundation & Deployment Pipeline

**Goal:** Establish technical foundation for all subsequent development  
**User Value:** Necessary infrastructure to enable the application to exist (Greenfield Exception)  
**FR Coverage:** Infrastructure enabler for all FRs

#### Story 1.1: Project Initialization & Supabase Setup

**User Story:**
As a **Developer**,  
I want **to initialize the project from scratch with Supabase configuration**,  
So that **I have a production-ready foundation with managed backend services.**

**Acceptance Criteria:**
- [ ] **Supabase Project Created:** New project at supabase.com with unique project URL
- [ ] **Storage Buckets Configured:**
  - `uploads` bucket (private) for user PDFs
  - `downloads` bucket (private) for generated EPUBs
- [ ] **Authentication Enabled:** Email/Password provider active in Supabase dashboard
- [ ] **Environment Variables Set:** `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY` documented
- [ ] Directory structure created: `transfer_app/frontend/`, `transfer_app/backend/`
- [ ] Git repository initialized with `.gitignore` for secrets
- [ ] **README.md** created with Supabase setup instructions

**Technical Notes:**
- Architecture ADR-002: Supabase as unified backend platform
- **NO starter template** - built from scratch for full control
- Supabase free tier sufficient for development
- Row Level Security (RLS) policies configured manually in later stories

**Prerequisites:** None

---

#### Story 1.2: Backend FastAPI & Supabase Integration

**User Story:**
As a **Developer**,  
I want **to set up FastAPI with Supabase Python client**,  
So that **the backend can authenticate users and access managed PostgreSQL.**

**Acceptance Criteria:**
- [ ] **FastAPI 0.122.0** installed with `uvicorn[standard]`
- [ ] **Supabase Python Client 2.24.0** installed and configured
- [ ] **Redis 8.4.0** container running via `docker-compose.yml` (for Celery only)
- [ ] Backend `.env` file with Supabase credentials:
  - `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
  - `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` (placeholders for now)
  - `REDIS_URL=redis://localhost:6379`
- [ ] **Supabase client initialized** in `backend/app/core/supabase.py`
- [ ] Health check endpoint `GET /api/health` returns:
  - `200 OK` with Supabase connection status
  - Redis connection status
- [ ] **SQLAlchemy 2.0.36** installed for local models (if needed)

**Technical Notes:**
- **Architecture:** Supabase handles PostgreSQL (no local DB container)
- **Supabase Python SDK:** Use for server-side admin operations (service role key)
- **No Alembic migrations** for Supabase-managed tables (use Supabase Studio)
- Docker only runs Redis (not PostgreSQL)

**Prerequisites:** Story 1.1

---

#### Story 1.3: Frontend Next.js & Supabase Client Setup

**User Story:**
As a **Developer**,  
I want **to set up Next.js 15 with Supabase JS client and shadcn/ui**,  
So that **I can build authenticated UI with the Professional Blue theme.**

**Acceptance Criteria:**
- [ ] **Next.js 15.0.3** initialized with TypeScript, Tailwind CSS, App Router
- [ ] **Supabase JS Client 2.46.1** installed: `@supabase/supabase-js`, `@supabase/auth-helpers-nextjs`
- [ ] **shadcn/ui** initialized (`npx shadcn-ui@latest init`)
- [ ] **Professional Blue theme** configured in `tailwind.config.ts`:
  - Primary: `#2563eb`, Secondary: `#64748b`, Accent: `#0ea5e9`
  - Success: `#10b981`, Warning: `#f59e0b`, Error: `#ef4444`
- [ ] **Supabase client** initialized in `src/lib/supabase.ts` (server and browser clients)
- [ ] **Frontend `.env.local`** configured:
  - `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
  - `NEXT_PUBLIC_API_URL=http://localhost:8000`
- [ ] System fonts configured (UX Spec Section 4.2)
- [ ] Basic layout with TopBar renders on `/` route

**Technical Notes:**
- UX Spec: Professional Blue color system (Section 4.1)
- Architecture: Supabase Auth Helpers for Next.js App Router
- Use separate clients for server components vs. client components

**Prerequisites:** Story 1.1

---

#### Story 1.4: Celery Worker & AI SDK Setup

**User Story:**
As a **Developer**,  
I want **to configure Celery workers with LangChain AI libraries**,  
So that **long-running AI-powered conversions can be processed asynchronously.**

**Acceptance Criteria:**
- [ ] **Celery 5.5.3** installed with Redis backend
- [ ] **LangChain 0.3.12** installed with OpenAI and Anthropic integrations:
  - `langchain-openai==0.2.9` (GPT-4o support)
  - `langchain-anthropic==0.2.5` (Claude 3 Haiku support)
- [ ] **PDF Processing:** `pymupdf==1.24.10`, `ebooklib` installed
- [ ] Celery app configured in `backend/app/core/celery_app.py`
- [ ] Worker entrypoint `backend/app/worker.py` created
- [ ] **Docker Compose:** Worker service added (shares backend code, mounts API keys)
- [ ] **Test task:** Dispatch AI call from API → Worker executes → Returns response
- [ ] Worker logs show LangChain initialization and API connectivity

**Technical Notes:**
- Architecture ADR-001: API-First Intelligence Architecture
- **No PyTorch/GPU dependencies** - all AI via OpenAI/Anthropic APIs
- Worker environment variables: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
- LangChain provides retry logic and fallback orchestration

**Prerequisites:** Story 1.2

---

#### Story 1.5: Vercel + Railway Deployment Configuration

**User Story:**
As a **DevOps Engineer**,  
I want **to configure deployment to Vercel (frontend) and Railway (backend + workers)**,  
So that **the application is production-ready with managed Supabase services.**

**Acceptance Criteria:**
- [ ] **Vercel Project:** Frontend connected to GitHub repo
  - Production and Preview environments configured
  - Environment variables: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_URL`
- [ ] **Railway Project:** Two services deployed:
  - **API Service:** FastAPI backend with Supabase keys, AI API keys
  - **Worker Service:** Celery worker with same environment
  - **Redis Service:** Managed Redis for Celery broker
- [ ] **Supabase Production:** Production Supabase project (separate from dev)
- [ ] **CORS Configuration:** Backend allows Vercel production domain
- [ ] **Health Check:** Public URLs accessible:
  - Frontend: `https://transfer2read.vercel.app`
  - Backend: `https://transfer-api.railway.app/api/health` → `200 OK`
- [ ] **Secrets Management:** All API keys stored in Railway secrets (not committed)
- [ ] **CI/CD:** GitHub Actions runs tests on PR before deployment

**Technical Notes:**
- Architecture: Vercel (frontend edge) + Railway (backend containers)
- **No database deployment** - Supabase is fully managed
- Railway auto-deploys from `main` branch

**Prerequisites:** Story 1.4

---

### Epic 2: User Identity & Account Management

**Goal:** Users can create accounts, log in, and manage their profiles  
**User Value:** Users can identify themselves, save their work, and access the platform securely  
**FR Coverage:** FR1, FR2, FR3, FR4, FR5, FR6, FR7

#### Story 2.1: Supabase Authentication Setup

**User Story:**
As a **Developer**,  
I want **to configure Supabase Auth for the backend and frontend**,  
So that **users can register, log in, and maintain secure sessions.**

**Acceptance Criteria:**
- [ ] **Supabase Auth Providers Enabled:**
  - Email/Password authentication active in Supabase dashboard
  - Email confirmation templates configured (welcome email, password reset)
- [ ] **User Table Extended:** Custom `user_metadata` fields in Supabase:
  - `tier` (enum: FREE, PRO, PREMIUM, default: FREE)
  - `created_at`, `updated_at` timestamps
- [ ] **Row Level Security (RLS) Policies:** Applied to `conversion_jobs` table:
  - Users can only read/write their own jobs
  - Policy: `auth.uid() = user_id`
- [ ] **Backend Auth Middleware:** Dependency created to validate Supabase JWT tokens
  - Extract `user_id` from JWT for protected routes
  - Return `401 Unauthorized` if token invalid
- [ ] **Test Endpoints Created:**
  - `POST /auth/test-protected` → Returns `user_id` from JWT
  - Unit tests validate token verification

**Technical Notes:**
- **Architecture:** Supabase Auth replaces fastapi-users (simpler, managed)
- **Security NFR12:** Passwords hashed by Supabase (bcrypt)
- **Security NFR13:** JWT tokens managed by Supabase (configurable expiry)
- **No password storage** in backend - Supabase handles all auth logic

**Prerequisites:** Story 1.2

---

#### Story 2.2: Frontend Supabase Auth UI

**User Story:**
As a **User**,  
I want **to sign up and log in using Supabase-powered authentication**,  
So that **I can securely access my account.**

**Acceptance Criteria:**
- [ ] **Login Page** (`/login`) created with:
  - Email and Password input fields (shadcn/ui components)
  - "Sign In" button triggers `supabase.auth.signInWithPassword()`
  - Error handling: Display auth errors ("Invalid credentials", "Email not confirmed")
  - "Forgot Password?" link (UI only for now)
- [ ] **Registration Page** (`/register`) created with:
  - Email and Password fields with validation (Zod + React Hook Form)
  - Password strength indicator
  - "Sign Up" button triggers `supabase.auth.signUp()`
  - Success message: "Check your email to confirm your account"
- [ ] **Auth State Management:**
  - `useUser` hook created using `@supabase/auth-helpers-nextjs`
  - Protected routes redirect to `/login` if not authenticated
  - Successful login redirects to `/dashboard`
- [ ] **Styling:** Professional Blue theme applied (shadcn/ui Card, Input, Button)

**Technical Notes:**
- **Supabase Client:** Use `createClientComponentClient()` for auth actions
- **Email Confirmation:** Required by default (staged rollout can disable)
- UX Spec: Clean, minimalist forms

**Prerequisites:** Story 1.3, Story 2.1

---

#### Story 2.3: Social Authentication (Google & GitHub)

**User Story:**
As a **User**,  
I want **to log in using my Google or GitHub account via Supabase**,  
So that **I don't have to remember another password.**

**Acceptance Criteria:**
- [ ] **Supabase OAuth Providers Configured:**
  - Google OAuth enabled in Supabase dashboard (Client ID/Secret from Google Cloud)
  - GitHub OAuth enabled (Client ID/Secret from GitHub Developer Settings)
- [ ] **Frontend Social Login Buttons:**
  - "Sign in with Google" and "Sign in with GitHub" buttons on `/login` and `/register`
  - Buttons trigger `supabase.auth.signInWithOAuth({ provider: 'google' })`
- [ ] **OAuth Callback Handling:**
  - Callback route `/auth/callback` handles OAuth redirect
  - Successful auth redirects to `/dashboard`
  - User account auto-created with `tier: FREE` on first social login
- [ ] **User Metadata:** Social logins populate `user_metadata` with provider info

**Technical Notes:**
- FR2: Social authentication
- Security NFR15: OAuth 2.0 standards (handled by Supabase)
- **Redirect URLs:** Configure in Supabase dashboard (e.g., `http://localhost:3000/auth/callback`)

**Prerequisites:** Story 2.1, Story 2.2

---

#### Story 2.4: Password Reset & User Profile

**User Story:**
As a **User**,  
I want **to reset my forgotten password and view my profile**,  
So that **I can manage my account security.**

**Acceptance Criteria:**
- [ ] **Forgot Password Flow:**
  - "Forgot Password" link on `/login` opens `/forgot-password` page
  - User enters email → Calls `supabase.auth.resetPasswordForEmail()`
  - Supabase sends password reset email with magic link
  - User clicks link → Redirected to `/reset-password` with token
- [ ] **Reset Password Page:**
  - Form accepts new password (with strength validation)
  - Submit calls `supabase.auth.updateUser({ password: newPassword })`
  - Success redirects to `/login` with confirmation message
- [ ] **User Profile Page** (`/settings`):
  - Displays user email (read-only)
  - Displays current tier (FREE/PRO/PREMIUM)
  - "Change Password" form (for email/password users only)
  - "Delete Account" button (confirmation dialog)

**Technical Notes:**
- FR4: Password reset
- FR5: View profile
- **Supabase handles email** sending (configure SMTP in dashboard or use default)

**Prerequisites:** Story 2.2

---

#### Story 2.5: Subscription Tier Display

**User Story:**
As a **User**,  
I want **to see my current subscription tier**,  
So that **I know what features and limits apply to me.**

**Acceptance Criteria:**
- [ ] Backend: User model includes `tier` enum (FREE, PRO, PREMIUM)
- [ ] Frontend: TopBar displays current tier badge (e.g., "Free" or "Pro")
- [ ] Settings page displays detailed tier information
- [ ] "Upgrade" button visible for Free tier users (links to placeholder pricing page)

**Technical Notes:**
- FR6: View subscription tier
- FR7: Upgrade tier (UI entry point)

**Prerequisites:** Story 2.2

---

### Epic 3: PDF Upload & File Management

**Goal:** Users can upload PDFs and manage their conversion history  
**User Value:** Users can get their PDF files into the system and track past conversions  
**FR Coverage:** FR8, FR9, FR10, FR11, FR12, FR13, FR14, FR15

#### Story 3.1: Supabase Storage Service Implementation

**User Story:**
As a **Developer**,  
I want **to implement file upload/download using Supabase Storage**,  
So that **users can securely manage PDFs and EPUBs with built-in authentication.**

**Acceptance Criteria:**
- [ ] **Supabase Storage Buckets:**
  - `uploads` bucket configured (private, RLS enabled)
  - `downloads` bucket configured (private, RLS enabled)
- [ ] **RLS Policies Created:**
  - `uploads`: Users can only upload/read files in folder `{user_id}/*`
  - `downloads`: Users can only read files in folder `{user_id}/*`
- [ ] **Backend Storage Service** (`backend/app/services/storage/supabase_storage.py`):
  - `upload_file(bucket, path, file_data)` → Returns public URL
  - `generate_signed_url(bucket, path, expires_in=3600)` → Returns temp URL
  - `delete_file(bucket, path)` → Removes file
- [ ] **File Naming Strategy:** `{user_id}/{job_id}/{filename}` to prevent collisions
- [ ] **Unit Tests:** Mock Supabase Storage client, test upload/download/delete
- [ ] **Lifecycle Policy:** Configure auto-delete after 30 days (via Supabase dashboard or SQL trigger)

**Technical Notes:**
- **Architecture ADR-002:** Supabase Storage (replaces generic S3)
- **Security NFR10:** Encryption at rest (Supabase default)
- **Security NFR14:** Auto-deletion after 30 days
- **No boto3 needed** - use `supabase.storage` API

**Prerequisites:** Story 1.2

---

#### Story 3.2: PDF Upload API with Supabase Integration

**User Story:**
As a **Developer**,  
I want **to create an API endpoint for PDF uploads to Supabase Storage**,  
So that **authenticated users can securely upload files.**

**Acceptance Criteria:**
- [ ] `POST /api/v1/upload` endpoint created:
  - **Authentication Required:** Extract `user_id` from Supabase JWT
  - **Input Validation:**
    - File type MUST be PDF (check magic bytes, not just extension)
    - File size validation based on user tier:
      - FREE: Max 50MB (FR10)
      - PRO/PREMIUM: Unlimited (FR11)
  - **Upload to Supabase Storage:**
    - Upload to `uploads/{user_id}/{job_id}/input.pdf`
    - Store file metadata in `conversion_jobs` table (Supabase PostgreSQL)
  - **Database Record:**
    - Insert into `conversion_jobs` table: `user_id`, `status: UPLOADED`, `input_path`, `created_at`
    - Return `{ "job_id": "uuid", "status": "UPLOADED" }`
- [ ] **Error Handling:**
  - 400: Invalid file type
  - 413: File too large for tier
  - 401: Unauthorized (no valid JWT)

**Technical Notes:**
- FR12: Validate PDF (use `python-magic` for mime-type)
- FR10/11: Size limits by tier
- **Supabase RLS** enforces user-specific folder access

**Prerequisites:** Story 3.1, Story 2.1

---

#### Story 3.3: Drag-and-Drop Upload UI

**User Story:**
As a **User**,  
I want **to drag and drop a PDF file onto the upload area**,  
So that **I can easily start the conversion process.**

**Acceptance Criteria:**
- [ ] `UploadZone` component created (shadcn/ui based)
- [ ] Drag enter/leave visual states (Blue border highlight)
- [ ] File selection via system dialog also supported
- [ ] Client-side validation (PDF only, max size check)
- [ ] Upload progress bar displayed during file transmission
- [ ] Error messages displayed (e.g., "File too large", "Not a PDF")
- [ ] Successful upload redirects to Job Status/Preview page

**Technical Notes:**
- UX Spec Section 7.1: `UploadZone` component
- UX Spec Section 4.5: Visual states (Light blue background on drag)

**Prerequisites:** Story 1.3, Story 3.2

---

#### Story 3.4: Conversion History Backend with Supabase

**User Story:**
As a **Developer**,  
I want **to track conversion jobs in Supabase PostgreSQL**,  
So that **users can view history and re-download files securely.**

**Acceptance Criteria:**
- [ ] **`conversion_jobs` Table** created in Supabase:
  - Columns: `id` (UUID), `user_id` (UUID FK to auth.users), `status` (enum), `input_path`, `output_path`, `quality_report` (JSONB), `created_at`, `completed_at`
  - **RLS Policy:** `SELECT/UPDATE/DELETE` allowed where `auth.uid() = user_id`
- [ ] **API Endpoints:**
  - `GET /api/v1/jobs` → List user's jobs (pagination), filters by `user_id` from JWT
  - `GET /api/v1/jobs/{id}` → Job details (validates ownership via RLS)
  - `DELETE /api/v1/jobs/{id}` → Soft delete record, schedule Supabase Storage file removal
  - `GET /api/v1/jobs/{id}/download` → Returns Supabase Storage signed URL (1-hour expiry)
- [ ] **Supabase RLS Enforcement:** Backend trusts RLS, no manual user_id filtering needed
- [ ] **Unit Tests:** Validate RLS policies prevent cross-user access

**Technical Notes:**
- FR13: View history
- FR14: Re-download (signed URLs)
- FR15: Delete history
- **Supabase RLS** provides automatic multi-tenancy

**Prerequisites:** Story 3.2

---

#### Story 3.5: Conversion History UI

**User Story:**
As a **User**,  
I want **to view a list of my past conversions**,  
So that **I can download them again or manage my files.**

**Acceptance Criteria:**
- [ ] History page created (`/history`)
- [ ] Table view of past jobs (Filename, Date, Status, Download button)
- [ ] Delete action with confirmation dialog
- [ ] Download button opens file/download link
- [ ] Empty state design ("No conversions yet - Upload your first PDF")
- [ ] Loading skeletons while fetching data

**Technical Notes:**
- UX Spec Section 6.3: History flow
- Use shadcn/ui Table component

**Prerequisites:** Story 3.4

---

### Epic 4: AI-Powered Conversion Engine (Core Value)

**Goal:** System converts complex PDFs to EPUBs with 95%+ fidelity  
**User Value:** **THE differentiator** - users get perfect conversions of complex technical documents  
**FR Coverage:** FR16-FR29, FR36-FR37, FR39-FR40

#### Story 4.1: Conversion Pipeline Orchestrator

**User Story:**
As a **Developer**,  
I want **to implement the main conversion workflow using Celery and Stirling-PDF**,  
So that **PDFs are reliably converted to HTML and then processed.**

**Acceptance Criteria:**
- [ ] Celery workflow (chain) defined: `convert_to_html -> extract_content -> identify_structure -> generate_epub`
- [ ] **Stirling-PDF Integration**: Call `StirlingPDFClient` to convert PDF to HTML.
- [ ] **Extract Content**: Parse and clean HTML using BeautifulSoup.
- [ ] **State updates**: Update Redis/DB at each step (e.g., "Converting to HTML...", "Analyzing Structure...").
- [ ] Error handling: Retries for Stirling API timeouts.
- [ ] Timeout configuration: 5 mins max per job.

**Technical Notes:**
- Architecture: Pipeline Pattern with Stirling Service.
- Use Celery Canvas.

**Prerequisites:** Story 1.4, Story 3.2

---

#### Story 4.2: Stirling-PDF Integration & AI Structure Analysis

**User Story:**
As a **Developer**,  
I want **to use Stirling-PDF for HTML conversion and GPT-4o for structure analysis**,  
So that **I get high-fidelity content with semantic meaning.**

**Acceptance Criteria:**
- [ ] **Stirling-PDF Client**: Implement client to POST PDF to Stirling API and retrieve HTML.
- [ ] **Content Extraction**: Implement `ContentAssembler` to parse HTML.
- [ ] **AI Structure Analysis**:
  - Prompt GPT-4o with HTML snippets/metadata.
  - Return JSON with TOC, Chapters, Title, Author.
- [ ] **Performance**: 
  - Stirling conversion ~10-30s.
  - AI analysis ~10-20s.

**Technical Notes:**
- **Architecture**: HTML-First Hybrid.
- **Cost**: Lower than Vision API (only text/structure analysis needed).
- **Retry Logic**: For both Stirling and OpenAI calls.

**Prerequisites:** Story 4.1

---

#### Story 4.3: AI-Powered Structure Recognition & TOC Generation

**User Story:**
As a **Developer**,  
I want **to use GPT-4o to analyze document structure and generate TOC**,  
So that **the final EPUB has semantic chapter organization.**

**Acceptance Criteria:**
- [ ] **Structure Analysis Prompt:**
  - Input: Full extracted text from PDF (or chunked for large docs)
  - Prompt: "Analyze this document. Identify: chapter titles, section headers, hierarchy (H1/H2/H3). Return JSON with TOC structure."
  - GPT-4o returns: `{ "toc": [{ "title": "Chapter 1", "level": 1, "page": 5 }, ...] }`
- [ ] **TOC Generation:**
  - Parse AI response to build EPUB NCX/NavMap structure (FR27)
  - Insert chapter breaks into content (FR28)
  - Tag hierarchical headers correctly (H1, H2, H3) (FR29)
- [ ] **Heuristic Fallback:**
  - If AI fails, use font-size heuristics (larger text = headers)
  - Detect common patterns: "Chapter X", "Section Y"
- [ ] **Output:** Structured intermediate format (JSON or enriched Markdown)

**Technical Notes:**
- FR26: Auto-detect structure
- FR27-FR29: TOC and header tagging
- **AI Advantage:** Better semantic understanding than pure heuristics

**Prerequisites:** Story 4.2

---

#### Story 4.4: EPUB Generation from AI-Analyzed Content

**User Story:**
As a **Developer**,  
I want **to convert AI-analyzed content into valid EPUB files**,  
So that **users can read on their e-readers with preserved formatting.**

**Acceptance Criteria:**
- [ ] **EPUB Generation Library:**
  - Use Python `ebooklib` for EPUB v3 creation
  - Alternative: `pandoc` CLI for Markdown → EPUB conversion
- [ ] **Content Assembly:**
  - Convert AI-detected elements to EPUB XHTML:
    - Tables → HTML `<table>` with CSS styling (FR17)
    - Images → Embedded images with `<img>` tags (FR18)
    - Equations → MathML or high-quality PNG fallback (FR19)
    - Multi-column content → Single-column XHTML (FR20)
- [ ] **Metadata Embedding:**
  - Title, Author (extracted from PDF or user-provided)
  - Cover image (first page thumbnail or custom)
  - AI-generated TOC from Story 4.3
- [ ] **Font Embedding:**
  - Embed fonts for special characters (FR22)
  - Support mixed-language documents (EN, ZH, JP, etc.)
- [ ] **EPUB Validation:**
  - Run `epubcheck` to validate EPUB 3.0 spec compliance
  - Verify file size ≤ 120% of original PDF (FR37)
- [ ] **Upload to Supabase Storage:**
  - Save EPUB to `downloads/{user_id}/{job_id}/output.epub`
  - Update `conversion_jobs` table with `output_path` and status `COMPLETED`

**Technical Notes:**
- FR36: Reflowable EPUB generation
- FR39-FR40: Compatibility with Apple Books, Kindle, Kobo
- **CSS Styling:** Custom stylesheet for consistent rendering

**Prerequisites:** Story 4.3

---

#### Story 4.5: AI-Based Quality Assurance & Confidence Scoring

**User Story:**
As a **Developer**,  
I want **to calculate quality confidence scores from AI analysis**,  
So that **users can trust conversion fidelity metrics.**

**Acceptance Criteria:**
- [ ] **Confidence Score Calculation:**
  - Aggregate AI confidence scores from GPT-4o responses
  - Weight by element complexity:
    - Simple text: 99% base confidence
    - Tables: AI confidence on table structure
    - Equations: AI confidence on LaTeX accuracy
    - Images: 100% (preserved as-is)
- [ ] **Detected Elements Count:**
  - Log: Tables found, Images found, Equations found (FR33)
  - Store in `quality_report` JSONB field
- [ ] **Warning Flags:**
  - Low confidence (<80%) on specific pages → Flag for user review
  - Example: "Page 45: Table detected but low confidence (72%)"
- [ ] **Quality Report JSON:**
  ```json
  {
    "overall_confidence": 95,
    "tables": { "count": 12, "avg_confidence": 93 },
    "images": { "count": 8 },
    "equations": { "count": 5, "avg_confidence": 97 },
    "warnings": ["Page 45: Low table confidence"]
  }
  ```
- [ ] Store quality report in `conversion_jobs.quality_report` (JSONB)

**Technical Notes:**
- FR24/25: Fidelity targets (95%+ complex, 99%+ text)
- **AI Advantage:** Real confidence scores vs. heuristic guesses
- Used for Epic 5 Quality Preview

**Prerequisites:** Story 4.2

---

### Epic 5: Quality Preview & Download Experience

**Goal:** Users verify conversion quality before downloading  
**User Value:** Confidence through visual proof - novel UX pattern that builds trust  
**FR Coverage:** FR30-FR35, FR38

#### Story 5.1: Real-time Progress Updates

**User Story:**
As a **User**,  
I want **to see the progress of my conversion in real-time**,  
So that **I know the system is working and when it will be finished.**

**Acceptance Criteria:**
- [ ] WebSocket or Polling mechanism implemented for Job Status
- [ ] Frontend updates progress bar and status text (e.g., "Analyzing Layout: 45%")
- [ ] "Detected Elements" counter updates live (FR32)
- [ ] Smooth animations for progress transitions
- [ ] Handling of connection loss/reconnect

**NEW ACCEPTANCE CRITERIA (from Epic 4 Retrospective Action 1.2: AI Cost Monitoring):**
- [ ] **AI Cost Tracking:** LangChain callbacks implemented to count tokens per AI call
  - Callback tracks: `prompt_tokens`, `completion_tokens`, `total_tokens`
  - Callback class: `backend/app/services/ai/cost_tracker.py`
  - Integrated with Story 4.2 (LayoutAnalyzer) and Story 4.3 (StructureAnalyzer)
  - Stored in `conversion_jobs.quality_report` JSONB field
- [ ] **Cost Estimation:** Calculate cost per job based on model pricing
  - GPT-4o: $2.50/1M input tokens, $10.00/1M output tokens
  - Claude 3 Haiku: $0.25/1M input tokens, $1.25/1M output tokens
  - Round to 4 decimal places (e.g., $0.1523)
- [ ] **Real-time Cost Display:** Progress UI shows estimated cost as jobs complete
  - Example: "Processing... Estimated cost: $0.12"
  - Updates incrementally as AI analysis stages complete
- [ ] **Quality Report Integration:** Add cost fields to quality_report JSON schema:
  ```json
  {
    "overall_confidence": 95,
    "estimated_cost": 0.15,
    "token_usage": {
      "prompt_tokens": 5000,
      "completion_tokens": 2000,
      "total_tokens": 7000
    }
  }
  ```

**NEW ACCEPTANCE CRITERIA (from Epic 4 Retrospective Action 1.3: Pre-Flight Checklist):**
- [ ] **Create Pre-Flight Integration Checklist Template**
  - Save to `.bmad/bmm/templates/pre-flight-checklist.md`
  - Template includes: Services & Dependencies, Data Flow, Error Handling, Testing, Documentation
  - Mandatory for all Epic 5 stories before marking "review"
  - Include checklist in PR for code review

**Technical Notes:**
- Architecture: Use Polling for MVP (simpler than WS with serverless) or SSE
- Update frequency: ~1-2 seconds
- **Estimated Effort Increase:** +3 hours (Action 1.2: 2-3h, Action 1.3: 30min)

**Prerequisites:** Story 4.1, Story 3.4

---

#### Story 5.2: Job Status & Quality Report Page

**User Story:**
As a **User**,  
I want **to see a summary of the conversion results**,  
So that **I can understand what was converted.**

**Acceptance Criteria:**
- [ ] Job Details page created (`/jobs/{id}`)
- [ ] Success state displays "Quality Report" summary (FR33)
- [ ] Metrics displayed: Number of pages, tables, images, equations
- [ ] "Confidence Score" visual indicator
- [ ] Call-to-action button: "Download EPUB" (Preview Comparison removed in QW.3)

**NEW ACCEPTANCE CRITERIA (from Epic 4 Retrospective Action 1.5: Quality Display Language):**
- [ ] **User-Friendly Quality Messaging:** Map technical confidence scores to plain English
  - **Mapping Rules:**
    - 95-100%: "Excellent - All elements preserved perfectly ✅"
    - 85-94%: "Very Good - Nearly all elements preserved ✅"
    - 75-84%: "Good - Most elements preserved ⚠️"
    - 60-74%: "Fair - Some elements may need review ⚠️"
    - <60%: "Review Required - Significant issues detected ❌"
  - **Element-Specific Messages:**
    - Tables (>90%): "12 tables detected and preserved"
    - Tables (70-90%): "12 tables detected, 2 may need review"
    - Tables (<70%): "12 tables detected, 5 require manual verification"
    - Equations (>90%): "All 8 equations rendered correctly"
    - Equations (<90%): "8 equations detected, 1 may have minor issues"
- [ ] **Quality Report UI Implementation:**
  - Overall quality level with emoji (✅/⚠️/❌)
  - User-friendly message (not raw confidence score)
  - Expandable element details (tables, images, equations counts)
  - Warning messages with page numbers and actionable guidance
  - **Estimated cost displayed** (from Action 1.2, Story 5.1): "Processing cost: $0.15"
  - User action prompt based on quality level

**Technical Notes:**
- UX Spec Section 6.2: Processing & Results
- Fetch data from `ConversionJob` and Quality Report JSON
- Implements PRD UX Principle: "Transparency Through Feedback"
- **Estimated Effort Increase:** +1-2 hours (Action 1.5)

**Prerequisites:** Story 5.1, Story 4.5, **Action 1.4 (Sample PDFs curated BEFORE Story 5.2 implementation)**

**CRITICAL PREREQUISITE (from Epic 4 Retrospective Action 1.4: Sample PDFs):**
**MUST COMPLETE BEFORE STORY 5.2 IMPLEMENTATION BEGINS:**
- [ ] **Test PDF Suite Curated (5 test PDFs):**
  1. Simple text PDF (10-20 pages, baseline)
  2. Complex technical book (50-100 pages, tables/images/equations)
  3. Multi-language document (EN + CJK characters)
  4. Large file (300+ pages, performance test)
  5. Edge case (damaged scan or unusual layout)
- [ ] All PDFs processed through Epic 4 pipeline
- [ ] Outputs saved: `tests/fixtures/epic-5-sample-pdfs/{1-5}/` (input.pdf, output.epub, quality_report.json, screenshots/)
- [ ] Expected quality metrics documented for each PDF
- [ ] Shared with frontend team for UI development
- **Estimated Effort:** +1-2 hours

---

#### Story 5.3: Split-Screen Comparison UI [REMOVED]

**Status:** REMOVED - Feature removed from MVP for simplified user experience (QW-3)

**Original User Story:**
As a **User**,
I want **to compare the original PDF side-by-side with the converted EPUB**,
So that **I can verify the layout and formatting fidelity.**

**Reason for Removal:**
Product decision to simplify the application and streamline the user experience. Quality verification is now handled entirely through the quality report on the job status page.

**Impact:**
- Preview comparison feature removed from MVP
- Users now rely on quality report for conversion confidence
- No split-screen UI, PDF viewer, or EPUB viewer components
- Dependencies removed: react-pdf, react-reader, pdfjs-dist, epubjs

---

#### Story 5.4: Download & Feedback Flow

**User Story:**
As a **User**,  
I want **to download the final EPUB and provide feedback**,  
So that **I can read my book and help improve the system.**

**Acceptance Criteria:**
- [ ] "Download EPUB" button triggers file download (FR38)
- [ ] "Report Issue" button allows user to flag specific pages/elements
- [ ] Simple feedback form ("Was this conversion good? 👍/👎")
- [ ] Confetti animation on successful download (Delight factor)

**NEW ACCEPTANCE CRITERIA (from Epic 4 Retrospective Action 1.1: Integration Test Suite):**
- [ ] **End-to-End Integration Test Suite Created:**
  - **Test File:** `tests/integration/test_full_pipeline.py`
  - **Test Scenarios (5 total):**
    1. Simple Text PDF (10-20 pages) → 99%+ confidence, <30s processing
    2. Complex Technical Book (50-100 pages, tables/images/equations) → 90-95% confidence
    3. Multi-Language Document (EN + CJK) → 95%+ confidence, fonts embedded
    4. Large File (300+ pages) → <2 min conversion (FR35), file size ≤ 120% PDF (FR37)
    5. Edge Case (corrupted/malformed) → <80% confidence, graceful degradation
  - **Test Flow:** PDF Upload → AI Analysis → Structure → EPUB → Quality → Download
  - **Success Criteria:**
    - All tests pass with real AI APIs (GPT-4o/Claude 3 Haiku)
    - Quality reports match expected ranges (±5%)
    - EPUBs validate against EPUB 3.0 spec (epubcheck)
    - File sizes ≤ 120% of PDF
  - **CI/CD Integration:** GitHub Actions monthly schedule (cost control)
  - **Budget:** $50/month AI API budget (~$10-15 per run)
- [ ] **Pre-Flight Checklist Applied (from Action 1.3, Story 5.1):**
  - Use template from `.bmad/bmm/templates/pre-flight-checklist.md`
  - Verify all integration points before marking "review"
  - Include completed checklist in PR

**Technical Notes:**
- Track download events for analytics
- Feedback stored in DB for model improvement
- **Estimated Effort Increase:** +5-7 hours (Action 1.1: 4-6h, Action 1.3 applied: 1h)

**Prerequisites:** Story 5.2

---

### Epic 6: Usage Tiers & Limits Enforcement

**Goal:** System enforces tier limits and enables upgrades  
**User Value:** Free users can try the service, paying users get unlimited access  
**FR Coverage:** FR41-FR47

#### Story 6.1: Usage Tracking with Supabase PostgreSQL

**User Story:**
As a **Developer**,  
I want **to track conversion usage per user in Supabase PostgreSQL**,  
So that **tier limits are enforced fairly.**

**Acceptance Criteria:**
- [ ] **`user_usage` Table** created in Supabase:
  - Columns: `user_id` (UUID FK), `month` (DATE), `conversion_count` (INT), `updated_at`
  - **RLS Policy:** Users can only read their own usage stats
- [ ] **Backend Service** (`backend/app/services/usage_tracker.py`):
  - `increment_usage(user_id)` → Increments count for current month
  - `get_usage(user_id)` → Returns current count and tier limit
  - Atomic increment using Supabase RPC or PostgreSQL function
- [ ] **Monthly Reset:**
  - Scheduled job (Celery Beat or Supabase pg_cron) resets counts on 1st of month
  - Alternative: Rolling 30-day window
- [ ] **Caching:**
  - Cache current user usage in Redis for fast lookups
  - Sync to Supabase PostgreSQL for persistence
- [ ] **Unit Tests:** Validate increment logic and reset behavior

**Technical Notes:**
- FR45: Track conversion count
- **Supabase PostgreSQL** provides ACID guarantees
- Redis caching reduces database hits during upload

**Prerequisites:** Story 1.2, Story 2.1

---

#### Story 6.2: Limit Enforcement Middleware

**User Story:**
As a **Developer**,  
I want **to block uploads or conversions if the user has exceeded their limit**,  
So that **the business model is respected.**

**Acceptance Criteria:**
- [ ] Middleware/Dependency created to check limits before `POST /upload`
- [ ] Check 1: File size limit (50MB for Free) (FR42)
- [ ] Check 2: Monthly conversion limit (5 for Free) (FR41)
- [ ] Return `403 Forbidden` with specific error code `LIMIT_EXCEEDED` if blocked
- [ ] Pro/Premium users bypass these checks (FR43, FR44)

**Technical Notes:**
- FR47: Prevent conversions
- Integrate with `UserUsage` service from Story 6.1

**Prerequisites:** Story 6.1, Story 3.2

---

#### Story 6.3: Upgrade Prompts & Paywall UI

**User Story:**
As a **User**,  
I want **to be notified when I hit a limit and easily upgrade**,  
So that **I can continue using the service without interruption.**

**Acceptance Criteria:**
- [ ] "Limit Reached" modal created (triggered by `LIMIT_EXCEEDED` error)
- [ ] Progress bar in Dashboard showing usage (e.g., "3/5 Free Conversions") (FR46)
- [ ] "Upgrade to Pro" banner on Dashboard
- [ ] Pricing page (static for now) listing features
- [ ] Upgrade button redirects to Stripe Checkout (or placeholder for MVP)

**Technical Notes:**
- FR46: Notify approaching limits
- UX Spec Section 6.4: Upgrade flow

**Prerequisites:** Story 6.2

---

#### Story 6.4: Basic Admin Dashboard

**User Story:**
As an **Admin**,  
I want **to view system stats and user activity**,  
So that **I can monitor the health of the application.**

**Acceptance Criteria:**
- [ ] Admin route `/admin` protected by `is_superuser` flag
- [ ] Dashboard showing: Total Users, Total Conversions, Active Jobs
- [ ] List of recent users and their tier status
- [ ] Ability to manually upgrade a user's tier (for support/testing)

**Technical Notes:**
- Use `sqladmin` or build simple React page
- Useful for managing the "Private Beta" phase

**Prerequisites:** Story 2.1

---

## Step 4: Final Review & Validation

### Breakdown Summary

| Epic | Stories | Est. Complexity | Key Deliverable |
|------|---------|-----------------|-----------------|
| **1. Foundation** | 5 | Medium | Project Repo, CI/CD, Core Services |
| **2. Identity** | 5 | Medium | Auth System, Profile, Tiers |
| **3. PDF Upload** | 5 | Medium | S3 Service, Upload UI, History |
| **4. AI Engine** | 5 | High | **Core Conversion Pipeline** |
| **5. Quality UX** | 4 | High | **Quality Report & Download** (Preview removed in QW.3) |
| **6. Usage Tiers** | 4 | Low | Limit Enforcement, Admin |
| **Total** | **28 Stories** | | **Full MVP** |

### Validation Summary (Updated 2025-12-01)

- ✅ **FR Coverage:** All 47 FRs are mapped to specific stories.
- ✅ **Architecture Alignment (NEW):**
    - **Frontend:** Next.js 15.0.3 + shadcn/ui + **Supabase JS Client 2.46.1**
    - **Backend:** FastAPI 0.122.0 + **Supabase Python Client 2.24.0** + **LangChain 0.3.12**
    - **AI:** **GPT-4o (OpenAI)** + **Claude 3 Haiku (Anthropic)** via LangChain (API-based)
    - **Database/Auth/Storage:** **Supabase** (managed PostgreSQL + Auth + File Storage)
    - **Queue:** Celery 5.5.3 + Redis 8.4.0
    - **Deployment:** **Vercel** (frontend) + **Railway** (backend + workers)
- ✅ **UX Alignment:**
    - "Professional Blue" theme (Epic 1, Story 1.3)
    - "Pre-Download Quality Verification" pattern (Epic 5)
    - Drag-and-drop Upload (Epic 3)
- ✅ **Story Quality:**
    - All stories have BDD Acceptance Criteria
    - All stories updated with Supabase and API-based AI implementation details
    - All stories have Prerequisites defined
    - **NEW:** Specific version numbers and library references (LangChain, Supabase clients)

**Architecture Changes Summary:**

| Component | Old (2025-11-27) | New (2025-12-01) |
|-----------|------------------|------------------|
| **Project Init** | Vintasoftware starter template | Built from scratch |
| **Database** | Self-managed PostgreSQL + Alembic | Supabase PostgreSQL (managed) |
| **Auth** | fastapi-users library | Supabase Auth (managed) |
| **Storage** | Generic S3 (boto3) | Supabase Storage with RLS |
| **AI Processing** | PyTorch local models (marker/surya) | LangChain + GPT-4o + Claude 3 Haiku (API) |
| **Deployment** | Vercel + Railway (DB in Railway) | Vercel + Railway + Supabase (managed) |

**Impact:** All 28 stories enhanced with specific Supabase and API-based AI implementation guidance.

### Next Steps

1. **Approve this Epic Breakdown**
2. **Initialize Project** (Start with Epic 1, Story 1.1)
3. **Hand off to Dev Agents** for implementation

---

## Epic 7: Launch Readiness (Post-MVP)

**Status:** PLANNED (Created: 2025-12-26)
**Goal:** Verify production readiness, performance, security, and user acceptance before public launch
**User Value:** Confidence that the system is stable, secure, and performant for real users
**Context:** All MVP features (Epics 1-6) are complete. This epic prepares for production launch.

---

### Story 7.1: Production Environment Verification

**User Story:**
As a **DevOps Engineer**,
I want **to verify that all production services are correctly configured and operational**,
So that **the application can serve real users reliably.**

**Acceptance Criteria:**

**Production Infrastructure:**
- [ ] **Vercel Frontend** fully deployed to production domain
  - Custom domain configured with SSL certificate
  - Environment variables verified: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_URL`
  - Preview deployments working for feature branches
- [ ] **Railway Backend API** operational on production URL
  - FastAPI service running with health check returning 200
  - Environment variables verified: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `REDIS_URL`
  - Auto-deploy from `main` branch verified
- [ ] **Railway Celery Worker** processing jobs
  - Worker logs show successful startup and AI SDK initialization
  - Test job dispatched and completed successfully
- [ ] **Railway Redis** accessible to API and Worker
  - Connection verified from both services
  - Persistence enabled for job queue durability

**Supabase Production:**
- [ ] **Production Supabase Project** configured separately from development
  - PostgreSQL database accessible
  - Row Level Security (RLS) policies verified on all tables
  - Storage buckets (`uploads`, `downloads`) configured with correct policies
  - Authentication providers enabled (Email, Google, GitHub OAuth)
- [ ] **Database Migrations** applied to production
  - All tables exist: `auth.users`, `conversion_jobs`, `user_usage`
  - Indexes created for performance
  - pg_cron or scheduled job for monthly usage reset configured

**API Keys & Secrets:**
- [ ] **All API keys rotated** for production (not using dev keys)
  - OpenAI API key with appropriate rate limits
  - Anthropic API key configured
  - Supabase service role key (NOT anon key for backend)
- [ ] **Secrets stored securely** in Railway environment variables (not in code)
- [ ] **.env files never committed** to git (verified in history)

**CORS & Security:**
- [ ] **CORS configuration** allows only production frontend domain
- [ ] **Rate limiting** enabled on API endpoints
- [ ] **HTTPS enforced** on all services (no HTTP fallback)

**Smoke Tests:**
- [ ] **End-to-End Smoke Test** on production:
  1. User can register and log in
  2. User can upload a PDF
  3. Conversion job completes successfully
  4. User can download EPUB
  5. Usage tracking increments correctly

**Technical Notes:**
- Use production Supabase project URL (separate from dev)
- Verify all services can reach each other (API → Supabase, Worker → Redis, etc.)
- Document production URLs and access procedures for team
- Set up staging environment identical to production for pre-release testing

**Prerequisites:** Epics 1-6 complete

---

### Story 7.2: Load & Performance Testing

**User Story:**
As a **QA Engineer**,
I want **to verify the system can handle expected load and meets performance targets**,
So that **users experience fast, reliable conversions at scale.**

**Acceptance Criteria:**

**Performance Baseline (Single User):**
- [ ] **Simple PDF conversion** (10-20 pages, text-only):
  - Upload → Processing → Download: **< 30 seconds end-to-end**
  - EPUB file size ≤ 120% of original PDF (FR37 validation)
- [ ] **Complex PDF conversion** (300 pages, tables/images/equations):
  - Processing time: **< 2 minutes** (FR35 validation)
  - AI cost per job: **< $1.00** (validate against Action 1.2 cost tracking)
  - Quality confidence score: **≥ 90%**
- [ ] **Frontend page load times:**
  - Landing page: < 2 seconds
  - Dashboard: < 3 seconds
  - Job status page: < 3 seconds (Preview comparison removed in QW.3)

**Concurrent Load Testing:**
- [ ] **10 concurrent users** uploading and converting PDFs:
  - All jobs complete successfully (no failures)
  - Average processing time increase: < 20% vs. single user
  - API response times: P95 < 500ms, P99 < 1s
- [ ] **50 concurrent users** (stress test):
  - System remains responsive (no crashes)
  - Celery worker queue depth monitored (max depth < 100)
  - Railway CPU/memory usage: < 80%

**AI API Rate Limits:**
- [ ] **OpenAI rate limits** tested:
  - Monitor rate limit headers in LangChain callbacks
  - Verify Claude 3 Haiku fallback triggers on rate limit error
  - Document API tier (e.g., Tier 3: 10,000 RPM)
- [ ] **Anthropic rate limits** tested:
  - Verify fallback or retry logic works

**Database Performance:**
- [ ] **Supabase PostgreSQL** under load:
  - Query response times: P95 < 100ms for `conversion_jobs` lookups
  - RLS policy overhead acceptable (< 10ms per query)
  - Connection pooling configured (pgBouncer if needed)
- [ ] **Redis** performance:
  - Job queue latency: < 10ms for enqueue/dequeue
  - Memory usage stable under load

**File Storage Performance:**
- [ ] **Supabase Storage** upload/download speeds:
  - 50MB PDF upload: < 10 seconds
  - EPUB download (signed URL): < 5 seconds
  - No 503 errors under concurrent load

**Load Testing Tools:**
- [ ] Use **Locust** or **k6** for load testing
- [ ] Test scenarios documented in `tests/load/scenarios.py`
- [ ] Load test report generated with metrics and graphs

**Performance Monitoring:**
- [ ] **Railway metrics dashboard** reviewed during tests
- [ ] **Sentry performance monitoring** (optional) capturing slow transactions
- [ ] Bottlenecks identified and documented for future optimization

**Technical Notes:**
- Run load tests from external network (not localhost) to simulate real conditions
- Monitor AI API costs during load testing (budget $20-50 for tests)
- Target: Support 100 conversions/day initially, 1000/day by month 3
- Document findings in `docs/sprint-artifacts/load-test-report-{date}.md`

**Prerequisites:** Story 7.1

---

### Story 7.3: Security Audit & Penetration Testing

**User Story:**
As a **Security Engineer**,
I want **to identify and fix security vulnerabilities before launch**,
So that **user data and the system are protected from attacks.**

**Acceptance Criteria:**

**Authentication & Authorization:**
- [ ] **Supabase Auth security** verified:
  - JWT token expiration working correctly (default: 1 hour)
  - Refresh token rotation enabled
  - Email confirmation required (prevents fake accounts)
  - Password strength enforced (min 8 chars, complexity rules)
- [ ] **OAuth security** validated:
  - Google/GitHub OAuth redirect URIs whitelisted (no open redirects)
  - CSRF protection enabled (Supabase default)
- [ ] **API endpoint authorization** tested:
  - All protected endpoints reject requests without valid JWT (401)
  - Users cannot access other users' jobs (403 test via RLS)
  - Admin endpoints require `is_superuser` flag

**OWASP Top 10 Validation:**
- [ ] **Injection attacks** (SQL, Command):
  - User inputs sanitized (Supabase prepared statements prevent SQL injection)
  - No `eval()` or `exec()` in Python backend
  - LangChain prompts sanitized (no prompt injection vulnerabilities)
- [ ] **Broken Authentication:**
  - Session management secure (Supabase JWT)
  - No hardcoded credentials in code (verified via `git grep` for API keys)
- [ ] **Sensitive Data Exposure:**
  - Passwords never stored (Supabase handles hashing)
  - API keys not logged or exposed in error messages
  - File storage: Private buckets with RLS (no public access)
- [ ] **XML External Entities (XXE):**
  - EPUB generation library (`ebooklib`) does not parse untrusted XML
  - PDF parsing (`pymupdf`) updated to latest version (CVE check)
- [ ] **Broken Access Control:**
  - RLS policies tested: User A cannot delete User B's jobs
  - File download URLs signed (1-hour expiry, user-specific)
- [ ] **Security Misconfiguration:**
  - Debug mode disabled in production (`FASTAPI_ENV=production`)
  - CORS restricted to production frontend domain only
  - Unnecessary HTTP methods disabled (e.g., no PUT on read-only endpoints)
- [ ] **Cross-Site Scripting (XSS):**
  - Next.js automatic XSS protection verified
  - User-uploaded filenames sanitized before display
  - shadcn/ui components do not render raw HTML from user input
- [ ] **Insecure Deserialization:**
  - Celery tasks do not deserialize untrusted data
  - JSON parsing uses safe methods (no `pickle`)
- [ ] **Using Components with Known Vulnerabilities:**
  - `npm audit` run on frontend (0 high/critical vulnerabilities)
  - `pip-audit` run on backend (0 high/critical vulnerabilities)
  - Supabase version up-to-date
- [ ] **Insufficient Logging & Monitoring:**
  - Failed login attempts logged
  - Conversion job failures logged with context
  - Unusual activity alerts configured (optional for MVP)

**Penetration Testing:**
- [ ] **Manual security testing** performed:
  - Attempt to access other users' files via URL manipulation
  - Test rate limiting by spamming API endpoints
  - Verify HTTPS enforcement (HTTP requests redirect to HTTPS)
  - Test file upload: Attempt to upload malicious files (e.g., JS disguised as PDF)
- [ ] **Automated scanning** (optional):
  - OWASP ZAP or Burp Suite scan of API endpoints
  - Snyk or Dependabot vulnerability scanning enabled on GitHub

**Data Privacy:**
- [ ] **GDPR compliance** (if applicable):
  - User data deletion flow works (delete account → cascade to jobs and files)
  - Privacy policy drafted (placeholder acceptable for MVP)
  - Cookie consent banner (if using analytics)
- [ ] **File retention policy** enforced:
  - Files auto-delete after 30 days (Security NFR14 validation)
  - Cron job or Supabase trigger tested

**Security Documentation:**
- [ ] **Security incident response plan** documented:
  - Contact procedures for security issues
  - Steps to rotate compromised API keys
  - Backup and restore procedures
- [ ] **Security findings report** created:
  - Document in `docs/sprint-artifacts/security-audit-report-{date}.md`
  - List vulnerabilities found and remediation steps
  - Sign-off from security reviewer (or Xavier if solo project)

**Technical Notes:**
- Use `safety` (Python) and `npm audit` for dependency vulnerability scanning
- Test with real attack scenarios (not just checklist review)
- Consider bug bounty program for post-launch (HackerOne, Bugcrowd)
- Budget 1-2 days for thorough security review

**Prerequisites:** Story 7.1

---

### Story 7.4: User Acceptance Testing (UAT)

**User Story:**
As a **Product Manager**,
I want **to validate the system with real beta users**,
So that **we launch with confidence that users find value and can complete workflows successfully.**

**Acceptance Criteria:**

**Beta User Recruitment:**
- [ ] **5-10 beta testers** recruited:
  - Mix of target personas: Students, researchers, professionals
  - At least 2 users with complex PDFs (technical books, multi-language docs)
  - At least 1 user with accessibility needs (screen reader, keyboard navigation)
- [ ] **Beta access configured:**
  - Invite-only registration (whitelist emails in Supabase)
  - OR: Public beta with "Beta" badge in UI

**UAT Test Scenarios:**
- [ ] **Scenario 1: Simple Conversion** (Happy Path):
  - User registers → Uploads 10-page PDF → Converts → Downloads EPUB
  - Success criteria: Completes without errors, EPUB opens in Apple Books/Calibre
  - Feedback: "Did the conversion meet your expectations? (1-5 stars)"
- [ ] **Scenario 2: Complex PDF** (Core Value Test):
  - User uploads 50-100 page technical book with tables/equations
  - Conversion completes with quality report showing 90%+ confidence
  - User reviews quality report (Preview comparison removed in QW.3)
  - Success criteria: User rates quality 4+ stars, downloads EPUB
- [ ] **Scenario 3: Multi-Language Document**:
  - User uploads PDF with English + Chinese/Japanese text
  - EPUB renders correctly with embedded fonts (no tofu/missing glyphs)
  - Success criteria: User confirms readability in e-reader
- [ ] **Scenario 4: Tier Limits** (Freemium Flow):
  - Free tier user converts 5 PDFs → Hits limit
  - Sees upgrade prompt → Understands value proposition
  - Success criteria: User either upgrades OR provides feedback on pricing
- [ ] **Scenario 5: Error Handling** (Edge Case):
  - User uploads corrupted or malformed PDF
  - System shows clear error message (not crash)
  - Success criteria: User understands issue and can retry

**Usability Testing:**
- [ ] **Navigation & UX feedback:**
  - Can users find upload button without instructions? (5/5 users succeed)
  - Is quality report clear and trustworthy? (User-friendly messages from Action 1.5 validated)
  - Are quality reports understandable? (User-friendly messages from Action 1.5 validated)
- [ ] **Performance perception:**
  - Do users feel conversion is "fast enough"? (Target: 4+ stars for 300-page book)
  - Is progress feedback clear during processing?

**Feedback Collection:**
- [ ] **Feedback mechanism** in app:
  - Post-download survey: "Rate your experience (1-5)" + open text
  - "Report Issue" button functional (Stories 5.2, 5.4)
- [ ] **User interviews** (optional):
  - 30-min call with 3-5 beta users
  - Ask: "What worked well? What frustrated you? Would you pay for this?"

**Bug Tracking:**
- [ ] **Beta bugs tracked** in GitHub Issues or project tracker:
  - Critical bugs (blocking launch) fixed immediately
  - Non-critical bugs (nice-to-have) documented for post-launch
- [ ] **UAT results documented:**
  - Pass/fail for each scenario
  - User quotes and feedback themes
  - Recommended fixes before launch

**Success Criteria (Launch Go/No-Go):**
- [ ] **80%+ users** complete Scenario 1 (simple conversion) successfully
- [ ] **70%+ users** rate quality 4+ stars on complex PDFs (Scenario 2)
- [ ] **0 critical bugs** (data loss, security issues, crashes)
- [ ] **Average user satisfaction:** 4+ stars overall

**Technical Notes:**
- Use Google Forms or Typeform for feedback surveys
- Track beta user emails in Supabase (flag: `beta_user: true`)
- Monitor Sentry errors during UAT period
- Budget 1 week for UAT (recruit → test → fix → retest)

**Prerequisites:** Story 7.1, Story 7.2 (performance validated)

---

### Story 7.5: Monitoring & Incident Response Setup

**User Story:**
As an **Operations Engineer**,
I want **to set up monitoring, alerting, and incident response procedures**,
So that **we can detect and fix issues quickly after launch.**

**Acceptance Criteria:**

**Application Monitoring:**
- [ ] **Railway Metrics** configured:
  - CPU, memory, disk usage dashboards visible
  - Alerts set for high resource usage (>80% for 5 minutes)
- [ ] **Supabase Dashboard** reviewed:
  - Database connection pool usage monitored
  - API request rate and error rate visible
  - Storage usage tracked (alert at 80% of quota)

**Error Tracking:**
- [ ] **Sentry** (or alternative) integrated:
  - Frontend errors captured (Next.js integration)
  - Backend errors captured (FastAPI integration)
  - Celery worker errors captured
  - Alerts configured: Slack/email on new error spike
- [ ] **Error rate baseline** established:
  - Acceptable error rate: < 1% of requests
  - Zero unhandled exceptions in critical paths (upload, conversion, download)

**Logging:**
- [ ] **Structured logging** implemented:
  - FastAPI logs include: `user_id`, `job_id`, `endpoint`, `duration`
  - Celery logs include: `task_name`, `job_id`, `ai_model_used`, `cost`
  - Log levels: DEBUG (dev), INFO (prod), ERROR (always)
- [ ] **Log aggregation** (optional for MVP):
  - Railway logs retained for 7 days (default)
  - Consider Papertrail/Logtail for longer retention

**Uptime Monitoring:**
- [ ] **Uptime checks** configured:
  - Use UptimeRobot, Pingdom, or Railway health checks
  - Monitor: Frontend (200 OK), Backend `/api/health` (200 OK)
  - Alert on downtime >2 minutes
- [ ] **Status page** (optional):
  - Public status page (status.transfer2read.com) using Statuspage.io
  - Shows: API status, conversion processing status

**AI API Monitoring:**
- [ ] **OpenAI API usage** tracked:
  - Daily token usage logged (from cost tracker, Action 1.2)
  - Alert if daily cost exceeds budget (e.g., >$50/day)
- [ ] **Anthropic API usage** tracked:
  - Monitor fallback frequency (should be rare if OpenAI reliable)

**Performance Monitoring:**
- [ ] **Slow query detection:**
  - Supabase performance insights reviewed
  - Queries >1s logged and investigated
- [ ] **Conversion time tracking:**
  - Average conversion time per job logged
  - Alert if average time exceeds 5 minutes (indicates worker issues)

**Incident Response Procedures:**
- [ ] **Runbook created** (`docs/operations/incident-response-runbook.md`):
  - **Incident 1: API Downtime**
    - Check Railway status dashboard
    - Restart services if needed
    - Verify Supabase connectivity
  - **Incident 2: Slow Conversions**
    - Check Celery worker logs
    - Verify Redis connection
    - Check AI API rate limits
  - **Incident 3: High Error Rate**
    - Check Sentry for error pattern
    - Review recent deployments (rollback if needed)
  - **Incident 4: Storage Quota Exceeded**
    - Run cleanup job (delete old files)
    - Verify 30-day auto-delete working
- [ ] **On-call rotation** (if team):
  - Designate primary contact for production issues
  - Define escalation path (e.g., Xavier as final escalation)
- [ ] **Post-incident review template:**
  - Document: What happened, Root cause, Resolution, Prevention

**Backup & Disaster Recovery:**
- [ ] **Supabase backups** verified:
  - Automatic daily backups enabled (Supabase default on paid tier)
  - Test restore procedure (spin up copy of DB from backup)
- [ ] **Code repository** backed up:
  - GitHub as source of truth
  - Consider secondary remote (GitLab mirror) for redundancy
- [ ] **Environment variables** documented:
  - All production secrets stored in password manager (1Password, LastPass)
  - Team has access in emergency

**Documentation:**
- [ ] **Operations manual** created (`docs/operations/`):
  - How to deploy to production
  - How to rotate API keys
  - How to scale workers (increase Railway replicas)
  - How to access production logs

**Go-Live Checklist:**
- [ ] **Pre-launch verification:**
  - All monitoring dashboards green (no errors)
  - Uptime checks passing for 24 hours
  - Team has tested incident response procedures
  - Contact info updated (support email, escalation phone)

**Technical Notes:**
- Start with free tiers (Sentry free, UptimeRobot free, Railway metrics included)
- Upgrade monitoring tools as revenue grows
- Monitor AI costs closely in first week (unexpected usage patterns)
- Document all monitoring URLs and credentials in team wiki

**Prerequisites:** Story 7.1, Story 7.2 (baseline metrics established)

---

### Epic 7 Summary

| Story | Complexity | Key Deliverable |
|-------|-----------|-----------------|
| **7.1 Production Verification** | Low | Production services validated |
| **7.2 Load Testing** | Medium | Performance benchmarks, load test report |
| **7.3 Security Audit** | Medium-High | Security audit report, vulnerabilities fixed |
| **7.4 UAT** | Medium | Beta feedback, launch go/no-go decision |
| **7.5 Monitoring Setup** | Low-Medium | Monitoring dashboards, incident runbook |
| **Total** | **5 Stories** | **Launch-Ready System** |

---
