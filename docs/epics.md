# Transfer2Read - Epic and Story Breakdown

**Project:** Transfer2Read  
**Generated:** 2025-11-27  
**Created by:** xavier (PM)  
**Context:** PRD + UX Design + Architecture  

---

## Document Purpose

This document provides a comprehensive breakdown of Transfer2Read into **implementable epics and detailed user stories**. Each story includes:
- BDD-style acceptance criteria
- Technical implementation guidance
- References to UX mockups and Architecture decisions
- Prerequisites and dependencies

**Usage:** Dev agents will use this document during Phase 4 (Implementation) to build the application story-by-story.

---

## Step 0: Workflow Mode Detection

🆕 **INITIAL CREATION MODE**

No existing epics found - Creating the initial epic breakdown.

**Available Context:**
- ✅ PRD (required) - Complete functional requirements
- ✅ Product Brief - Vision and market positioning  
- ✅ UX Design - Complete interaction patterns, mockups (Direction 3: Preview Focused), components
- ✅ Architecture - Technical stack (Next.js + FastAPI), deployment decisions, data models

**Context Quality:** EXCELLENT - Full planning phase complete (PRD + UX + Architecture)

This epic breakdown will incorporate ALL available context for maximum implementation clarity.

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

#### Story 1.1: Project Initialization & Monorepo Setup

**User Story:**
As a **Developer**,  
I want **to initialize the project repository with the Vintasoftware starter**,  
So that **I have a production-ready foundation with type safety and structure.**

**Acceptance Criteria:**
- [ ] Repo initialized using `vintasoftware/nextjs-fastapi-starter` template
- [ ] Directory structure matches Architecture doc (`frontend/`, `backend/`, `docker-compose.yml`)
- [ ] Frontend dependencies installed (`npm install`)
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] `docker-compose up` starts all services (frontend, backend, db) without errors
- [ ] Git repository initialized with `.gitignore` properly configured

**Technical Notes:**
- Follow Architecture: Next.js 14 (App Router) + FastAPI
- Ensure Python 3.11+ environment
- Configure basic linting (ESLint, Prettier, Ruff/Black)

**Prerequisites:** None

---

#### Story 1.2: Backend Core & Database Configuration

**User Story:**
As a **Developer**,  
I want **to configure FastAPI with PostgreSQL and Redis**,  
So that **the application has a working data layer and caching system.**

**Acceptance Criteria:**
- [ ] PostgreSQL 15+ container running via Docker
- [ ] Redis container running via Docker
- [ ] FastAPI configured with `asyncpg` driver and SQLAlchemy (Async)
- [ ] Database migration system (Alembic) initialized
- [ ] Basic health check endpoint `GET /api/health` returns 200 OK and DB status
- [ ] Environment variables configured for local development (`.env`)

**Technical Notes:**
- Architecture Decision: Use AsyncPG for performance
- Architecture Decision: Use Pydantic v2 for schema validation
- Verify connection strings in `backend/app/core/config.py`

**Prerequisites:** Story 1.1

---

#### Story 1.3: Frontend Foundation & UI Library

**User Story:**
As a **Developer**,  
I want **to set up Next.js with shadcn/ui and the Professional Blue theme**,  
So that **I can build UI components consistent with the UX design.**

**Acceptance Criteria:**
- [ ] Next.js 14 App Router configured
- [ ] Tailwind CSS installed and configured
- [ ] shadcn/ui initialized (`npx shadcn-ui@latest init`)
- [ ] "Professional Blue" color tokens added to `tailwind.config.ts` (Primary: `#2563eb`, etc.)
- [ ] Font families configured (Inter/Sans, Mono) per UX spec
- [ ] Basic layout component created (TopBar placeholder, Main content area)
- [ ] Landing page renders with correct theme colors

**Technical Notes:**
- UX Spec Section 4.1: Implement all color tokens
- UX Spec Section 4.2: Configure typography
- UX Spec Section 2.1: Use shadcn/ui copy-paste model

**Prerequisites:** Story 1.1

---

#### Story 1.4: Async Worker Infrastructure

**User Story:**
As a **Developer**,  
I want **to configure Celery with Redis**,  
So that **long-running PDF conversions can be processed in the background.**

**Acceptance Criteria:**
- [ ] Celery configured in `backend/app/core/celery_app.py`
- [ ] Redis configured as Celery broker and backend
- [ ] Worker entrypoint `backend/app/worker.py` created
- [ ] Docker Compose updated to include `worker` service
- [ ] Test task dispatched from API and executed by worker successfully
- [ ] Worker logs visible in Docker output

**Technical Notes:**
- Architecture ADR-002: Async Processing with Celery
- Ensure worker shares code/models with backend service

**Prerequisites:** Story 1.2

---

#### Story 1.5: Deployment Pipeline Configuration

**User Story:**
As a **DevOps Engineer**,  
I want **to configure deployment pipelines for Vercel and Railway**,  
So that **code changes are automatically deployed to production.**

**Acceptance Criteria:**
- [ ] Frontend project connected to Vercel (Production & Preview environments)
- [ ] Backend/Worker/DB services configured on Railway
- [ ] Environment variables synced to Vercel and Railway
- [ ] CI/CD pipeline (GitHub Actions) runs tests on PR
- [ ] Successful deployment of "Hello World" app to public URL
- [ ] Frontend can communicate with Backend in production environment

**Technical Notes:**
- Architecture Deployment Section: Vercel (Edge) + Railway (Container)
- Configure CORS on backend to allow Vercel domain

**Prerequisites:** Story 1.4

---

### Epic 2: User Identity & Account Management

**Goal:** Users can create accounts, log in, and manage their profiles  
**User Value:** Users can identify themselves, save their work, and access the platform securely  
**FR Coverage:** FR1, FR2, FR3, FR4, FR5, FR6, FR7

#### Story 2.1: Backend Authentication System

**User Story:**
As a **Developer**,  
I want **to implement the authentication backend using `fastapi-users`**,  
So that **the API supports secure registration, login, and token management.**

**Acceptance Criteria:**
- [ ] `fastapi-users` installed and configured with SQLAlchemy adapter
- [ ] User model created with fields: `email`, `hashed_password`, `is_active`, `is_superuser`, `tier` (default: FREE)
- [ ] JWT authentication transport configured (HttpOnly cookies + Bearer token)
- [ ] Endpoints exposed: `/auth/register`, `/auth/login`, `/auth/logout`
- [ ] Password hashing using bcrypt
- [ ] Protected route decorator (`@current_user`) created and tested
- [ ] Unit tests for auth flow (register -> login -> access protected route)

**Technical Notes:**
- Architecture: Use `fastapi-users` library
- Security NFR12: Bcrypt hashing
- Security NFR13: Session tokens expire (configure JWT lifetime)

**Prerequisites:** Story 1.2

---

#### Story 2.2: Frontend Authentication Pages

**User Story:**
As a **User**,  
I want **to sign up and log in using a clean, professional interface**,  
So that **I can access my account.**

**Acceptance Criteria:**
- [ ] Login page created (`/login`) with Email/Password form
- [ ] Registration page created (`/register`)
- [ ] Form validation (email format, password length) using Zod + React Hook Form
- [ ] Error handling (invalid credentials, user already exists) displayed clearly
- [ ] Successful login redirects to Dashboard
- [ ] "Forgot Password" link (UI only for now)
- [ ] Styling matches "Professional Blue" theme (shadcn/ui Card, Input, Button)

**Technical Notes:**
- UX Spec: Clean, minimalist forms
- Use `react-hook-form` for state management
- Integrate with API endpoints from Story 2.1

**Prerequisites:** Story 1.3, Story 2.1

---

#### Story 2.3: Social Authentication Integration

**User Story:**
As a **User**,  
I want **to log in using my Google or GitHub account**,  
So that **I don't have to remember another password.**

**Acceptance Criteria:**
- [ ] Backend: Google and GitHub OAuth clients configured in `fastapi-users`
- [ ] Frontend: "Sign in with Google" and "Sign in with GitHub" buttons added to Login/Register pages
- [ ] OAuth callback route handled correctly
- [ ] User account created automatically on first social login
- [ ] Environment variables for OAuth Client IDs/Secrets configured

**Technical Notes:**
- FR2: Social authentication
- Security NFR15: OAuth 2.0 standards

**Prerequisites:** Story 2.1, Story 2.2

---

#### Story 2.4: User Profile & Password Management

**User Story:**
As a **User**,  
I want **to view my profile and reset my password if forgotten**,  
So that **I can manage my account security.**

**Acceptance Criteria:**
- [ ] Backend: `/auth/forgot-password` and `/auth/reset-password` endpoints enabled
- [ ] Backend: Email sending service configured (can use console/mock for dev)
- [ ] Frontend: Forgot Password request page
- [ ] Frontend: Reset Password page (token via URL)
- [ ] Frontend: User Profile page (`/settings`) displaying email and current tier
- [ ] Users can change their password from the Settings page

**Technical Notes:**
- FR4: Password reset
- FR5: View profile

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

#### Story 3.1: S3 Storage Service Implementation

**User Story:**
As a **Developer**,  
I want **to implement a storage service wrapper for S3**,  
So that **the application can securely upload and download user files.**

**Acceptance Criteria:**
- [ ] `boto3` (or `aioboto3`) installed and configured
- [ ] Service class created with methods: `upload_file`, `generate_presigned_url`, `delete_file`
- [ ] S3 Bucket configured via environment variables
- [ ] Unit tests using `moto` to mock S3 interactions
- [ ] File naming strategy implemented (UUIDs to prevent collisions)
- [ ] Lifecycle policy configuration documented (auto-delete after 30 days)

**Technical Notes:**
- Architecture: Decouple storage from compute
- Security NFR10: Encryption at rest (S3 server-side encryption)
- Security NFR14: Auto-deletion policy

**Prerequisites:** Story 1.2

---

#### Story 3.2: PDF Upload API & Validation

**User Story:**
As a **Developer**,  
I want **to create an API endpoint for PDF uploads**,  
So that **users can send files to the server with proper validation.**

**Acceptance Criteria:**
- [ ] `POST /api/v1/upload` endpoint created
- [ ] Input validation: File type MUST be PDF (check magic bytes, not just extension)
- [ ] File size validation based on user tier (50MB for Free, Unlimited for Pro)
- [ ] File uploaded to S3 `uploads/` prefix
- [ ] Database record created in `conversion_jobs` table (Status: UPLOADED)
- [ ] Response returns `job_id`

**Technical Notes:**
- FR12: Validate PDF
- FR10/11: Size limits
- Use `python-magic` or similar for mime-type detection

**Prerequisites:** Story 3.1, Story 2.1 (for user tier check)

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

#### Story 3.4: Conversion History Backend

**User Story:**
As a **Developer**,  
I want **to track conversion jobs in the database**,  
So that **users can view their history and re-download files.**

**Acceptance Criteria:**
- [ ] `ConversionJob` model created (User FK, Status, Input/Output S3 Keys, Created At)
- [ ] `GET /api/v1/jobs` endpoint (List user's jobs, pagination)
- [ ] `GET /api/v1/jobs/{id}` endpoint (Job details)
- [ ] `DELETE /api/v1/jobs/{id}` endpoint (Soft delete record, schedule S3 deletion)
- [ ] `GET /api/v1/jobs/{id}/download` endpoint (Returns S3 presigned URL)

**Technical Notes:**
- FR13: View history
- FR14: Re-download
- FR15: Delete history

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
I want **to implement the main conversion workflow using Celery**,  
So that **the multi-step conversion process is managed reliably.**

**Acceptance Criteria:**
- [ ] Celery workflow (chain/chord) defined: `analyze -> extract -> structure -> generate`
- [ ] State updates sent to Redis/DB at each step (e.g., "Analyzing Layout...", "Generating EPUB...")
- [ ] Error handling: Retries for transient failures, specific error states for permanent failures
- [ ] Timeout configuration (FR35: <2 mins target, but set hard limit higher)
- [ ] Cancellation support (if user cancels job)

**Technical Notes:**
- Architecture: Pipeline Pattern
- Use Celery Canvas for workflow orchestration

**Prerequisites:** Story 1.4, Story 3.2

---

#### Story 4.2: Layout Analysis & OCR Integration

**User Story:**
As a **Developer**,  
I want **to integrate the `marker` or `surya` library**,  
So that **I can extract text, tables, and images with layout preservation.**

**Acceptance Criteria:**
- [ ] `marker-pdf` (or chosen engine) integrated into worker environment
- [ ] PDF processing task extracts Markdown with tables and equations (FR16, FR17, FR19)
- [ ] Images extracted and saved to temporary storage (FR18)
- [ ] Multi-column layouts correctly reflowed to single column (FR20)
- [ ] Performance benchmark: 300-page PDF processed within acceptable limits

**Technical Notes:**
- FR16-FR25: Core extraction requirements
- Ensure GPU acceleration is configured if available (or optimized CPU fallback)

**Prerequisites:** Story 4.1

---

#### Story 4.3: Structure Recognition & TOC Generation

**User Story:**
As a **Developer**,  
I want **to analyze the extracted content to identify chapters and headers**,  
So that **the final EPUB has a correct Table of Contents.**

**Acceptance Criteria:**
- [ ] Algorithm implemented to detect chapter headers (Heuristics + Font size analysis)
- [ ] Table of Contents (NCX/NavMap) data structure generated (FR27)
- [ ] Chapter breaks inserted into Markdown stream (FR28)
- [ ] Hierarchical headers (H1, H2, H3) correctly tagged (FR29)

**Technical Notes:**
- FR26: Auto-detect structure
- Output should be a structured intermediate format (e.g., JSON or enriched Markdown)

**Prerequisites:** Story 4.2

---

#### Story 4.4: EPUB Generation Service

**User Story:**
As a **Developer**,  
I want **to convert the structured Markdown into a valid EPUB file**,  
So that **users can read the content on their devices.**

**Acceptance Criteria:**
- [ ] `pandoc` or python `ebooklib` integration
- [ ] Markdown + Images converted to EPUB v3 format
- [ ] Metadata embedded (Title, Author, Cover Image)
- [ ] Custom CSS injected for consistent styling (FR22: Fonts)
- [ ] Validation: Generated EPUB passes `epubcheck`
- [ ] Output file saved to S3 and Job updated with download URL

**Technical Notes:**
- FR36: Reflowable EPUB
- FR39: Compatibility (Kindle/Apple Books)
- FR37: File size optimization

**Prerequisites:** Story 4.3

---

#### Story 4.5: Automated Quality Assurance

**User Story:**
As a **Developer**,  
I want **to run automated quality checks on the generated content**,  
So that **we can guarantee high fidelity.**

**Acceptance Criteria:**
- [ ] Confidence score calculated based on OCR confidence and layout complexity
- [ ] "Detected Elements" count (Tables, Images, Equations) logged (FR33)
- [ ] Warning flags generated for potential issues (e.g., "Low confidence on page 45")
- [ ] Quality report JSON stored with the job

**Technical Notes:**
- FR24/25: Fidelity targets
- Used for the "Quality Preview" epic later

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

**Technical Notes:**
- Architecture: Use Polling for MVP (simpler than WS with serverless) or SSE
- Update frequency: ~1-2 seconds

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
- [ ] Call-to-action buttons: "Preview Comparison" and "Download EPUB"

**Technical Notes:**
- UX Spec Section 6.2: Processing & Results
- Fetch data from `ConversionJob` and Quality Report JSON

**Prerequisites:** Story 5.1, Story 4.5

---

#### Story 5.3: Split-Screen Comparison UI

**User Story:**
As a **User**,  
I want **to compare the original PDF side-by-side with the converted EPUB**,  
So that **I can verify the layout and formatting fidelity.**

**Acceptance Criteria:**
- [ ] Split-screen component created (Left: PDF Viewer, Right: EPUB/HTML Viewer)
- [ ] Synchronized scrolling (scrolling left pane scrolls right pane)
- [ ] "Highlight Differences" toggle (optional for MVP, but good for "Preview Focused" direction)
- [ ] PDF rendered using `react-pdf`
- [ ] EPUB rendered using `react-reader` or raw HTML iframe
- [ ] Mobile responsive adaptation (Stack vertically or show tabs)

**Technical Notes:**
- UX Spec: "Pre-Download Quality Verification" pattern
- This is the **Core Differentiator** - needs high polish

**Prerequisites:** Story 5.2

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

**Technical Notes:**
- Track download events for analytics
- Feedback stored in DB for model improvement

**Prerequisites:** Story 5.2

---

### Epic 6: Usage Tiers & Limits Enforcement

**Goal:** System enforces tier limits and enables upgrades  
**User Value:** Free users can try the service, paying users get unlimited access  
**FR Coverage:** FR41-FR47

#### Story 6.1: Usage Tracking Service

**User Story:**
As a **Developer**,  
I want **to track how many conversions each user performs per month**,  
So that **we can enforce fair usage limits.**

**Acceptance Criteria:**
- [ ] `UserUsage` model created (User FK, Month, Conversion Count)
- [ ] Service method `increment_usage(user_id)` implemented
- [ ] Service method `get_usage(user_id)` returns current count and limit
- [ ] Background job (Celery beat) to reset usage counts on 1st of month (or rolling window)
- [ ] Unit tests for increment logic and reset logic

**Technical Notes:**
- FR45: Track conversion count
- Store in Redis for fast access, sync to DB for persistence

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
| **5. Quality UX** | 4 | High | **Split-Screen Preview** |
| **6. Usage Tiers** | 4 | Low | Limit Enforcement, Admin |
| **Total** | **28 Stories** | | **Full MVP** |

### Validation Checklist

- ✅ **FR Coverage:** All 47 FRs are mapped to specific stories.
- ✅ **Architecture Alignment:**
    - Stack: Next.js + FastAPI + Celery + Redis + Postgres (Confirmed in Epics 1, 4)
    - Auth: `fastapi-users` (Confirmed in Epic 2)
    - Storage: S3 (Confirmed in Epic 3)
    - AI: `marker`/`surya` (Confirmed in Epic 4)
- ✅ **UX Alignment:**
    - "Professional Blue" theme (Epic 1)
    - "Pre-Download Quality Verification" pattern (Epic 5)
    - Drag-and-drop Upload (Epic 3)
- ✅ **Story Quality:**
    - All stories have BDD Acceptance Criteria
    - All stories have Technical Notes
    - All stories have Prerequisites defined

### Next Steps

1. **Approve this Epic Breakdown**
2. **Initialize Project** (Start with Epic 1, Story 1.1)
3. **Hand off to Dev Agents** for implementation

---
