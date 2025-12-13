# Transfer2Read - Technical Specification: Epic 4 (AI-Powered Conversion Engine)

**Author:** xavier
**Date:** 2025-12-12
**Project Level:** Simple (Sprint Artifact)
**Change Type:** Feature Implementation (Core Engine)
**Development Context:** Brownfield (Existing Foundation)

---

## Context

### Available Documents

- **Product Brief:** Transfer2Read (AI PDF to EPUB converter)
- **Architecture:** API-First Intelligence (Supabase + FastAPI + Celery + LangChain)
- **Epics:** Epic 4 defined in `epics.md` (Stories 4.1 - 4.5)
- **Stack:** Validated (Next.js 15, FastAPI 0.122, Supabase, Celery 5.5)

### Project Stack

- **Frontend:** Next.js 15, Tailwind, shadcn/ui, Supabase Client
- **Backend:** FastAPI 0.122, Python 3.13
- **Async:** Celery 5.5 with Redis 8.4
- **AI:** LangChain 0.3, OpenAI (GPT-4o), Anthropic (Claude 3 Haiku)
- **Database:** Supabase PostgreSQL
- **Storage:** Supabase Storage

### Existing Codebase Structure

- **Backend Services:** `backend/app/services/` (Storage service exists)
- **Worker:** `backend/app/worker.py` (Basic setup exists)
- **Models:** `backend/app/models/` (Jobs table model exists)

---

## The Change

### Problem Statement

Users cannot currently convert complex PDFs (tables, multi-column, equations) into EPUBs with high fidelity. Existing tools (Calibre, etc.) destroy formatting. The core value proposition of Transfer2Read depends on this AI-powered engine which is not yet implemented.

### Proposed Solution

Implement the **AI Conversion Pipeline** using a distributed task queue (Celery) and a multi-model AI approach (LangChain):
1.  **Orchestrator:** A Celery workflow that manages the state of the conversion job.
2.  **Analysis:** GPT-4o (Vision) to detect layout elements (tables, images, text blocks).
3.  **Extraction:** Layout-aware text extraction and reconstruction.
4.  **Structuring:** AI-driven generation of TOC and chapter hierarchy.
5.  **Generation:** Production of valid EPUB 3 files with reflowable content.

### Scope

**In Scope:**
- Story 4.1: Conversion Pipeline Orchestrator (Celery workflow)
- Story 4.2: LangChain AI Layout Analysis Integration (GPT-4o + Claude)
- Story 4.3: AI-Powered Structure Recognition (TOC generation)
- Story 4.4: EPUB Generation (using `ebooklib`)
- Story 4.5: Quality Assurance Scoring (AI confidence check)

**Out of Scope:**
- Real-time UI updates (Epic 5 - though backend support will be added)
- Payment/Tier enforcement (Epic 6 - technically hooks will be present but logic is permissive)
- Mobile app support

---

## Implementation Details

### Source Tree Changes

#### [NEW] Backend AI Services
- `backend/app/services/ai/base.py` - Abstract base class for AI providers
- `backend/app/services/ai/gpt4.py` - GPT-4o implementation
- `backend/app/services/ai/claude.py` - Claude 3 Haiku implementation
- `backend/app/services/ai/chain.py` - LangChain orchestration logic

#### [NEW] Conversion Services
- `backend/app/services/conversion/pipeline.py` - Main orchestration logic
- `backend/app/services/conversion/analyzer.py` - Layout analysis logic
- `backend/app/services/conversion/extractor.py` - Content extraction logic
- `backend/app/services/conversion/epub_generator.py` - EPUB creation logic
- `backend/app/services/conversion/quality.py` - QA scoring logic

#### [MODIFY] Worker
- `backend/app/worker.py` - Register new Celery tasks (analyze, extract, generate)

#### [MODIFY] Job Management
- `backend/app/api/v1/jobs.py` - Update status endpoints to reflect pipeline stages
- `backend/app/models/job.py` - Add fields for `quality_score` and `stage_metadata`

### Technical Approach

**1. Pipeline Architecture (Celery Canvas)**
We will use a Celery `chord` or `chain`:
```python
workflow = chain(
    analyze_layout.s(job_id),
    extract_content.s(),
    identify_structure.s(),
    generate_epub.s(),
    calculate_quality_score.s()
)
```
Each task updates the `conversion_jobs` table with current status and progress %.

**2. AI Layout Analysis (LangChain)**
- **Input:** PDF Page Image (converted via PyMuPDF) + Text Layer
- **Model:** GPT-4o (Temperature 0)
- **Prompt:** "Identify bounding boxes for: tables, images, headers, footers. classify layout type."
- **Fallback:** If OpenAI times out, switch to Claude 3 Haiku with same schema.
- **Output:** JSON structure describing the page layout.

**3. EPUB Generation**
- Use `ebooklib` to construct the EPUB.
- Map recognized structures (Chapters, Sections) to NCX/Nav table.
- Inject CSS for responsive tables and images.

### Existing Patterns to Follow

- **Service Pattern:** All logic in `services/`, endpoint only dispatches tasks.
- **Pydantic Models:** Use strict schemas for all AI outputs (using `.with_structured_output()`).
- **Error Handling:** Custom exceptions caught in worker and logged to DB as `FAILED` status with reason.

### Integration Points

- **Supabase Storage:**
    - Read input PDF from `uploads/{user_id}/{job_id}/`
    - Write output EPUB to `downloads/{user_id}/{job_id}/`
- **Database:**
    - Update `conversion_jobs` status/progress.
- **Redis:**
    - Celery broker and result backend.

---

## Development Context

### Relevant Existing Code

- `backend/app/core/celery_app.py`: Celery configuration (Already exists, verified in Epic 1).
- `backend/app/services/storage/supabase_storage.py`: File access (Already exists, verified in Epic 3).

### Dependencies

**Framework/Libraries:**
- `langchain`: Orchestration
- `langchain-openai`: GPT-4o
- `langchain-anthropic`: Claude 3
- `pymupdf` (fitz): PDF rasterization and text access
- `ebooklib`: EPUB creation

**Internal Modules:**
- `app.core.config`: API Keys
- `app.db.session`: Database access

### Configuration Changes

- Ensure `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` are set in `.env` (and Railway).
- Configure Celery visibility timeout to 20 minutes (PDF processing is slow).

---

## Implementation Stack

- **Runtime:** Python 3.13
- **Queue:** Celery 5.5 / Redis 8.4
- **AI:** GPT-4o / Claude 3 Haiku via LangChain

---

## Technical Details

### AI Prompt Strategy
We will use **few-shot prompting** with LangChain's Pydantic output parsers to ensure valid JSON JSON.
- **Layout Element:** `{ "type": "table", "bbox": [x1, y1, x2, y2], "description": "Financial summary" }`
- **Structure Element:** `{ "type": "chapter_title", "text": "Chapter 1: Introduction", "level": 1 }`

### Error Handling
- **Transient (Network):** Celery auto-retry (3 attempts, exponential backoff).
- **Permanent (PDF Corrupt):** Fail job, update DB status, cleanup temp files.
- **AI Refusal:** If AI refuses to process (safety), fallback to heuristic extraction.

---

## Development Setup

```bash
# 1. Activate venv
source backend/venv/bin/activate

# 2. Install dependencies (if not already)
pip install -r backend/requirements.txt

# 3. Start Redis
docker-compose up -d redis

# 4. Start Worker (in separate terminal)
cd backend
celery -A app.worker worker --loglevel=info
```

---

## Implementation Guide

### Setup Steps
- [ ] Verify API Keys for OpenAI/Anthropic are active.
- [ ] Create `backend/app/services/ai/` and `backend/app/services/conversion/` directories.

### Implementation Steps

1.  **Setup AI Clients:** Implement `gpt4.py` and `claude.py` with LangChain.
2.  **Layout Analysis:** Implement `analyzer.py` using PyMuPDF + AI.
3.  **Structure Recognition:** Implement `structure.py` to build the TOC tree.
4.  **EPUB Generator:** Implement `epub_generator.py` mapping structure to EPUB chapters.
5.  **Pipeline Wiring:** Create the Celery tasks in `worker.py` and chain them.
6.  **Testing:** Run unit tests for each service + integration test with sample PDF.

### Testing Strategy

- **Unit:** Mock AI responses (save costs/time). Test JSON parsing and EPUB construction.
- **Integration:** Run full pipeline with a small "Golden Master" PDF (5 pages, 1 table, 1 image).
- **Cost Check:** Monitor token usage during dev.

### Acceptance Criteria

- [ ] Pipeline runs end-to-end without crashing.
- [ ] Tables are preserved as HTML `<table>` in EPUB (not images).
- [ ] TOC is correctly generated in `nav.xhtml`.
- [ ] Job status updates reflect in DB (Queued -> Analyzed -> Structuring -> Completed).
