# Sprint Change Proposal - Railway to Docker Deployment

**Date:** 2026-01-08
**Project:** Transfer2Read
**Product Manager:** xavier
**Change Type:** Infrastructure Pivot (Cloud → Self-Hosted)
**Scope:** Major - Affects PRD, Architecture, and Epic Breakdown

---

## 1. Issue Summary

### Problem Statement

Transfer2Read's current architecture documents specify deployment to **Vercel (frontend) + Railway (backend/workers)** with managed cloud services. However, Railway's pricing model is cost-prohibitive for the project owner. The deployment strategy must shift to **Docker-based self-hosted infrastructure** running on local hardware for both development and production environments.

### Context

**When Discovered:** Pre-implementation (planning phase)
**Discovery Method:** User-initiated strategic decision based on cost analysis
**Trigger:** Railway subscription costs exceed budget constraints

### Evidence

1. **Architecture Document (Line 122):** Explicitly states "Deployment: Vercel + Railway"
2. **Architecture Document (Lines 413-869):** 450+ lines of Railway/Vercel deployment configuration
3. **Epics Document (Line 42, Story 1.5):** References "Vercel + Railway" as deployment target
4. **User Statement:** "Railway is expensive, so my computer is easy can be run backend"
5. **Target Environment:** "Local dev + self-hosted production on my computer"

---

## 2. Impact Analysis

### Epic Impact

**Affected Epics:**
- ✅ **Epic 1 (Foundation):** Story 1.5 requires complete rewrite
- ✅ **Epic 7 (Production Readiness):** Stories 7.1, 7.2, 7.4 require updates

**Unaffected Epics:**
- ✅ **Epics 2-6 (Features):** No impact - deployment is transparent to application features

**Assessment:**
- **2 of 7 epics** require modifications
- **5 of 28 total stories** need updates (1 complete rewrite, 4 targeted edits)
- **No new epics or stories required** - Docker deployment fits within existing Epic 1 scope

### Artifact Conflicts

#### PRD Conflicts (5 Changes)

1. **NFR25 (Auto-Scaling):** ❌ Cannot auto-scale on self-hosted hardware → **REMOVE**
2. **NFR21 (Horizontal Scaling):** ❌ Cannot add servers on single machine → **REVISE** to vertical scaling
3. **NFR8 (99.5% Uptime):** ⚠️ Cannot guarantee SLA without redundancy → **REVISE** to best-effort
4. **NFR6 (100 Concurrent Users):** ⚠️ Now hardware-dependent → **REVISE** to reflect host limits
5. **CDN Delivery (Line 242):** ❌ No CDN in self-hosted → **REVISE** to direct serving

**MVP Scope Impact:** ✅ **NO CHANGE** - Core conversion functionality unaffected

#### Architecture Conflicts (2 Major Changes)

1. **Decision Summary Table (Line 122):** Vercel + Railway → Docker Compose
2. **Deployment Architecture Section (Lines 413-869):** Complete replacement with Docker-based deployment guide

#### Epic/Story Conflicts (5 Story Updates)

1. **Epic Metadata (Line 43):** Update deployment tech stack reference
2. **Story 1.5 (Lines 403-431):** Complete rewrite - "Vercel + Railway Configuration" → "Docker Compose Configuration"
3. **Story 7.1 (Lines 1259-1322):** Update production verification from cloud services to Docker containers
4. **Story 7.2 (Line 1356-1357):** Replace Railway metrics with Docker stats
5. **Story 7.4 (Lines 1594-1683):** Update monitoring from cloud dashboards to Docker-native tools

### Technical Impact

**Infrastructure Changes:**
- **Before:** Multi-cloud (Vercel edge + Railway containers + Supabase SaaS)
- **After:** Single-host Docker (all services containerized) + Supabase SaaS

**Component Mapping:**

| Component | Before | After | Change Type |
|-----------|--------|-------|-------------|
| Frontend | Vercel Edge | Docker container (port 3000) | Platform change |
| Backend API | Railway container | Docker container (port 8000) | Platform change |
| Worker | Railway container | Docker container | Platform change |
| Redis | Railway managed | Docker container (port 6379) | Platform change |
| Database/Auth | Supabase SaaS | Supabase SaaS | ✅ NO CHANGE |
| Storage | Supabase SaaS | Supabase SaaS | ✅ NO CHANGE |

**Key Technical Differences:**
- ❌ No edge CDN (Vercel) → Static assets served from Next.js
- ❌ No auto-scaling (Railway) → Manual scaling via `docker-compose scale`
- ❌ No managed Redis (Railway) → Self-managed Redis in Docker
- ✅ Same application code - no code changes required
- ✅ Same external dependencies (Supabase, OpenAI, Anthropic)

**Performance Implications:**
- Concurrent users now limited by host hardware (CPU cores, RAM)
- No global CDN → Slower static asset delivery for remote users (acceptable for self-hosted)
- Local Redis potentially faster than cloud Redis (no network latency)

**Security Implications:**
- ✅ Same application-level security (Supabase RLS, JWT auth)
- ⚠️ Host machine security now critical (firewall, SSH hardening)
- ⚠️ No managed service SLAs (uptime dependent on host availability)

---

## 3. Recommended Approach

### Selected Path: **Option 1 - Direct Adjustment**

Modify existing stories and documentation to reflect Docker deployment. No epic restructuring, no MVP scope changes.

### Rationale

1. **Minimal Disruption:** Changes isolated to infrastructure stories (Epic 1, 7)
2. **Clear Scope:** Exactly 12 targeted changes across 3 documents
3. **Low Risk:** Docker Compose is simpler than multi-cloud orchestration
4. **Cost Effective:** Achieves primary goal (eliminate Railway costs)
5. **MVP Preserved:** All user-facing features unchanged
6. **Timeline Maintained:** Docker setup may be faster than cloud provisioning

### Alternatives Considered

**Option 2: Rollback Previous Work**
- ❌ Not applicable - no implementation completed yet
- Status: Not viable

**Option 3: Reduce MVP Scope**
- ❌ Not needed - MVP fully achievable with Docker deployment
- Status: Viable but unnecessary

---

## 4. Detailed Change Proposals

### PRD Changes (docs/prd.md)

#### Change #1: Remove Auto-Scaling NFR
- **Line 495**
- **Action:** DELETE NFR25
- **Reason:** Auto-scaling requires cloud infrastructure

#### Change #2: Revise Horizontal Scaling NFR
- **Line 488**
- **Before:** "Architecture supports horizontal scaling to accommodate 10x user growth"
- **After:** "Architecture supports vertical scaling within host hardware limits to accommodate user growth"
- **Reason:** Self-hosted can only scale vertically (CPU/RAM upgrades)

#### Change #3: Revise Uptime Guarantee NFR
- **Line 458**
- **Before:** "Web application maintains 99.5% uptime"
- **After:** "Web application maintains best-effort uptime (dependent on host hardware and network availability)"
- **Reason:** Cannot guarantee SLA without redundant infrastructure

#### Change #4: Revise Concurrent Users NFR
- **Line 456**
- **Before:** "System handles concurrent conversions for up to 100 users simultaneously"
- **After:** "System handles concurrent conversions limited by host hardware resources (CPU cores, RAM, disk I/O)"
- **Reason:** Performance now hardware-dependent

#### Change #5: Remove CDN Reference
- **Line 242**
- **Before:** "CDN delivery for static assets"
- **After:** "Static assets served directly from Next.js (optimized with compression)"
- **Reason:** No CDN in self-hosted deployment

### Architecture Changes (docs/architecture.md)

#### Change #6: Update Decision Summary Table
- **Line 122**
- **Before:** `| **Deployment** | **Vercel + Railway** | N/A | CUSTOM | Vercel for frontend (edge network), Railway for backend containers. |`
- **After:** `| **Deployment** | **Docker Compose** | N/A | CUSTOM | Self-hosted Docker containers for frontend, backend, worker, and Redis. |`

#### Change #7: Replace Deployment Architecture Section
- **Lines 413-869 (MAJOR REPLACEMENT)**
- **Action:** Replace entire "Deployment Architecture" and "Production Deployment Architecture" sections
- **New Content Includes:**
  - Docker Compose configuration (`docker-compose.yml`)
  - Dockerfile specifications for frontend and backend
  - Environment variable configuration (`.env` file)
  - Deployment commands (`docker-compose up -d`, logs, health checks)
  - Production considerations (hardware requirements, security, backups, monitoring)
  - Scaling guidance (vertical scaling, worker replicas)

### Epic/Story Changes (docs/epics.md)

#### Change #8: Update Deployment Tech Stack Reference
- **Line 43**
- **Before:** "**Deployment:** Updated to **Vercel** (frontend) + **Railway** (backend + workers)"
- **After:** "**Deployment:** Self-hosted **Docker Compose** (frontend + backend + workers + Redis)"

#### Change #9: Complete Rewrite of Story 1.5
- **Lines 403-431 (COMPLETE STORY REPLACEMENT)**
- **Old Title:** "Vercel + Railway Deployment Configuration"
- **New Title:** "Docker Compose Deployment Configuration"
- **New User Story:** "As a DevOps Engineer, I want to configure Docker Compose for self-hosted deployment, so that the application can run on local hardware with all services containerized."
- **New Acceptance Criteria:**
  - Docker Compose file created with 4 services
  - Dockerfiles for frontend and backend
  - Environment configuration (`.env` file)
  - Health checks verified (frontend, backend, Redis, worker)
  - Service communication validated
  - Documentation updated

#### Change #10: Update Story 7.1 (Production Verification)
- **Lines 1259-1322**
- **Actions:**
  - Replace Vercel/Railway service verification with Docker container health checks
  - Update environment variable validation for Docker context
  - Replace cloud monitoring with `docker-compose ps` and health endpoints
  - Update technical notes for Docker network connectivity

#### Change #11: Update Story 7.2 (Load Testing)
- **Lines 1356-1357**
- **Before:** "Railway CPU/memory usage: < 80%"
- **After:** "Docker container resource usage: `docker stats` shows CPU/memory < 80% of host capacity"

#### Change #12: Update Story 7.4 (Monitoring & Observability)
- **Lines 1594-1683**
- **Actions:**
  - Replace "Railway Metrics" with "Docker Container Metrics" (docker stats, optional Prometheus)
  - Update log management from Railway logs to `docker-compose logs` with rotation
  - Replace Railway health checks with Docker healthcheck directives
  - Update incident response runbook for Docker commands
  - Update operations manual for Docker deployment/scaling procedures

---

## 5. Implementation Handoff

### Change Scope Classification

**Scope:** **Moderate** - Requires backlog reorganization and documentation updates

**Complexity:** Medium
- 12 discrete changes across 3 documents
- 1 major section replacement (Architecture deployment)
- 1 complete story rewrite (Story 1.5)
- 10 targeted edits (PRD NFRs + Epic updates)

**Effort Estimate:** 2-4 hours
- PRD updates: 30 minutes
- Architecture section replacement: 1-2 hours (writing + review)
- Epic/Story updates: 1 hour
- Final review and consistency check: 30 minutes

**Risk Assessment:** Low
- No code changes required
- No feature changes
- Documentation-only updates
- Docker is well-established technology

### Handoff Recipients

**Primary:** **Product Manager (PM)** - xavier
- **Responsibility:** Review and approve all documentation changes
- **Action:** Execute the 12 documented changes to PRD, Architecture, and Epics
- **Deliverables:** Updated PRD.md, Architecture.md, Epics.md

**Secondary:** **Architect** (optional consultation)
- **Responsibility:** Review Docker Compose architecture for technical soundness
- **Action:** Validate Docker configuration in new Architecture section

**Tertiary:** **Development Team** (implementation phase)
- **Responsibility:** Implement Story 1.5 (Docker Compose setup) when Epic 1 begins
- **Action:** Create `docker-compose.yml`, Dockerfiles, environment configuration

### Success Criteria

✅ **Documentation Updated:**
- All 12 changes applied to PRD, Architecture, and Epics documents
- No remaining Vercel/Railway references in deployment sections
- Docker deployment fully documented with examples

✅ **Consistency Validated:**
- PRD NFRs align with Docker capabilities (no auto-scaling, vertical scaling only)
- Architecture deployment section provides complete Docker setup guide
- Epic 1 Story 1.5 acceptance criteria reflect Docker deployment

✅ **Implementation Ready:**
- Story 1.5 provides clear, actionable acceptance criteria for Docker setup
- Epic 7 stories provide Docker-based verification and monitoring procedures
- Team has clear documentation for self-hosted deployment

### Next Steps

1. **PM (xavier):** Review this Sprint Change Proposal
2. **PM:** Apply all 12 approved changes to documentation
3. **PM:** Mark this change proposal as "Implemented"
4. **PM:** Proceed with workflow-status → sprint-planning (next workflow)
5. **Dev Team:** Implement Story 1.5 during Epic 1 execution

---

## 6. Summary

### Change Overview

**Issue:** Railway cloud deployment costs exceed budget
**Solution:** Pivot to Docker Compose self-hosted deployment
**Scope:** 12 documentation changes across PRD, Architecture, and Epics
**Impact:** Infrastructure only - no feature changes

### Artifacts Modified

| Document | Changes | Type |
|----------|---------|------|
| **docs/prd.md** | 5 NFR updates | Targeted edits |
| **docs/architecture.md** | 2 major updates | 1 table update, 1 section replacement |
| **docs/epics.md** | 5 story updates | 1 complete rewrite, 4 targeted edits |

### MVP Impact

✅ **NO CHANGE** - All MVP features remain achievable with Docker deployment

### Timeline Impact

✅ **NO DELAY** - Docker setup may be faster than cloud provisioning

### Cost Impact

✅ **POSITIVE** - Eliminates Railway subscription costs ($20-100/month)

### Risk Assessment

✅ **LOW** - Docker is simpler than multi-cloud orchestration, well-established technology

---

## Approval

**Status:** Awaiting Final User Approval

**Prepared By:** John (Product Manager Agent)
**Date:** 2026-01-08
**Change Proposal ID:** SCP-2026-01-08-RAILWAY-TO-DOCKER

---

*This Sprint Change Proposal was generated through the BMad Method Course Correction workflow, analyzing impact across all project artifacts and providing a systematic path forward for the deployment infrastructure pivot.*
