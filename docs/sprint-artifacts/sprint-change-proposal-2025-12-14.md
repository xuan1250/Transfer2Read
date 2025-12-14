# Sprint Change Proposal: Epic 5 Enhancement with Epic 4 Action Items

**Date:** 2025-12-14
**Project:** Transfer2Read
**Scope:** Epic 5 - Quality Preview & Download Experience
**Change Type:** Direct Adjustment (Integrate Epic 4 Retrospective Actions)
**Facilitator:** Correct Course Workflow
**Approver:** xavier

---

## Executive Summary

Following the successful completion of Epic 4 (AI-Powered Conversion Engine), the retrospective identified **9 action items** for code quality, foundation work, and Epic 5 preparation. This proposal integrates **5 Priority 1 action items** (10-15 hours effort) directly into Epic 5 story acceptance criteria.

**Recommendation:** Approve integration of all Priority 1 actions into Epic 5 stories to prevent future rework, enable frontend development, and ensure production readiness.

**Impact:** +1-2 days Epic 5 timeline, significant quality improvement, prevents Epic 4-4 type integration gaps.

---

## Section 1: Issue Summary

### Problem Statement

**Triggering Event:** Epic 4 Retrospective (completed 2025-12-13)

**Issue Type:** Proactive quality improvement and Epic 5 preparation work

**Context:**
Epic 4 successfully delivered the core AI conversion engine with 100% test pass rate and all 5 stories approved. However, the retrospective revealed technical debt and preparation gaps that should be addressed before Epic 5:

1. **Integration Test Gap** - Story 4-4 required second code review due to integration issues (ContentAssembler not called by EpubGenerator). An end-to-end integration test would have caught this earlier.

2. **No AI Cost Monitoring** - Production risk: no visibility into AI API costs during Epic 4 development. Deferred from Epic 3, now critical for production pricing decisions.

3. **Missing Integration Checklist** - Story 4-4 and 4-5 had integration bugs. Pre-flight checklist template needed for complex stories.

4. **Frontend Blocked Without Test Data** - Epic 5 frontend developers cannot build Quality Report UI (Story 5.2) or Split-Screen Preview (Story 5.3) without sample conversion outputs.

5. **UX Language Undefined** - Technical confidence scores (95%) need user-friendly translations ("Excellent quality ✅") per PRD UX Principle "Transparency Through Feedback."

### Evidence

**From Epic 4 Retrospective (`docs/sprint-artifacts/epic-4-retrospective-2025-12-13.md`):**

**Story 4-4 Code Review Iteration:**
- **Initial Review:** BLOCKED - Core content assembly not integrated
- **Root Cause:** ContentAssembler service existed but never called
- **Time Cost:** ~2-4 hours rework for second review
- **Fix:** Full integration verification in second review → APPROVED

**Story 4-5 Post-Completion Bugs:**
- Missing `QualityReport` import in `job_service.py`
- `include_quality_details` query parameter not implemented
- **Fixed same day** (2025-12-13), minimal impact

**Integration Test Evidence:**
> "No end-to-end test: PDF upload → AI analysis → EPUB download. Story 4-4 blockers would have been caught by integration test."

**AI Cost Visibility Evidence:**
> "Unknown: Total AI API spend for Epic 4 implementation. No cost tracking in LangChain callbacks."

**Effort Estimates (from Action Items):**
- Action 1.1 (Integration Tests): 4-6 hours
- Action 1.2 (AI Cost Monitoring): 2-3 hours
- Action 1.3 (Pre-Flight Checklist): 30 minutes
- Action 1.4 (Sample PDFs): 1-2 hours
- Action 1.5 (Quality UX Language): 1-2 hours
- **Total:** 10-15 hours

---

## Section 2: Impact Analysis

### Epic Impact

**Epic 4 (AI-Powered Conversion Engine):**
- **Status:** ✅ COMPLETE (no changes needed)
- **Impact:** None - remains complete, actions are post-completion enhancements

**Epic 5 (Quality Preview & Download Experience):**
- **Status:** Backlog (ready to start)
- **Impact:** **PRIMARY TARGET** - All 5 Priority 1 actions integrate here
- **Dependencies Met:** 100% (per retrospective validation)
- **New Dependencies:**
  - **Action 1.4 (Sample PDFs):** REQUIRED before Story 5.2 implementation
  - **Action 1.5 (UX Language):** REQUIRED for Story 5.2 UI design
  - **Action 1.2 (Cost Monitoring):** Integrates into Story 5.1 real-time updates
  - **Action 1.1 (Integration Tests):** Validates Epic 5 + Epic 4 pipeline end-to-end

**Epic 6 (Usage Tiers & Limits):**
- **Status:** Backlog
- **Impact:** None - unaffected by quality improvements

### Story Impact

| Epic 5 Story | Current Stories | Actions Integrated | Effort Increase |
|--------------|----------------|-------------------|-----------------|
| **Story 5.1:** Real-time Progress Updates | 1 story | +2 AC (Action 1.2, 1.3) | +3 hours |
| **Story 5.2:** Quality Report Page | 1 story | +1 Prereq, +2 AC (Action 1.4, 1.5) | +2-3 hours |
| **Story 5.3:** Split-Screen Comparison | 1 story | Enhanced Prereqs (uses 1.4 outputs) | +0 hours |
| **Story 5.4:** Download & Feedback | 1 story | +2 AC (Action 1.1, 1.3 applied) | +5-7 hours |
| **Total Epic 5** | 4 stories | 5 actions | **+10-13 hours** |

### Artifact Conflicts

**PRD (Product Requirements Document):**
- ✅ **No conflicts** - All actions SUPPORT PRD goals
- ✅ **Alignment:**
  - Action 1.5 implements UX Principle "Transparency Through Feedback"
  - Action 1.2 supports NFR7 "Optimize AI processing costs"
  - Action 1.1 validates FR35 "<2 min conversion" and FR24/25 "95%+ fidelity"

**Architecture (`docs/architecture.md`):**
- ✅ **No conflicts** - Actions reinforce existing ADRs
- ✅ **Alignment:**
  - Action 1.2 (Cost Monitoring) reinforces ADR-001 (API-First Intelligence)
  - Action 1.1 (Integration Tests) validates ADR-002 (Supabase integration)

**Epics Document (`docs/epics.md`):**
- 🔄 **Changes Required:** Epic 5 stories need updated acceptance criteria
- **Impact:** Add 5 new acceptance criteria + 1 prerequisite (detailed in Section 4)

**UX Specifications:**
- ✅ **No conflicts** - Action 1.5 ENHANCES UX
- ✅ **Improves:** Quality Report UI with user-friendly messaging

**Test Strategy:**
- 🔄 **Changes Required:** New integration test suite (Action 1.1)
- **New Artifact:** `tests/integration/test_full_pipeline.py`

### Technical Impact

**Code Changes:**
- **New Services:** `backend/app/services/ai/cost_tracker.py` (Action 1.2)
- **Modified Services:** LangChain callbacks in `layout_analyzer.py`, `structure_analyzer.py` (Action 1.2)
- **New Tests:** `tests/integration/test_full_pipeline.py` (Action 1.1)
- **New Templates:** `.bmad/bmm/templates/pre-flight-checklist.md` (Action 1.3)
- **New Test Data:** `tests/fixtures/epic-5-sample-pdfs/` (Action 1.4)

**Database Schema:**
- ✅ **No changes** - `quality_report` JSONB field already exists (Epic 4, Story 4.5)
- **Enhancement:** Add `estimated_cost` and `token_usage` to quality_report JSON

**Infrastructure:**
- **CI/CD:** Add monthly integration test schedule (Action 1.1)
- **Budget:** +$50/month for AI integration tests (~$10-15 per run)

---

## Section 3: Recommended Approach

### Selected Path: Direct Adjustment

**Approach:** Integrate all 5 Priority 1 action items into Epic 5 story acceptance criteria.

### Story Integration Mapping

**Story 5.1 (Real-time Progress Updates):**
- **Action 1.2:** AI Cost Monitoring
  - Add LangChain callbacks to track token usage
  - Display estimated cost in real-time progress UI
  - Store cost data in `quality_report` JSONB
- **Action 1.3:** Pre-Flight Integration Checklist
  - Create template in `.bmad/bmm/templates/`
  - Mandatory for all Epic 5 stories before code review

**Story 5.2 (Job Status & Quality Report Page):**
- **Action 1.4:** Sample PDFs for Frontend Testing
  - PREREQUISITE: Curate 5 test PDFs before Story 5.2 begins
  - Process through Epic 4 pipeline
  - Save outputs: `tests/fixtures/epic-5-sample-pdfs/`
- **Action 1.5:** Quality Metrics Display Language
  - Map technical scores to user-friendly messages
  - Design emoji/icon set for quality levels
  - Implement in Quality Report UI

**Story 5.3 (Split-Screen Comparison UI):**
- **Uses Action 1.4 outputs:** Sample EPUBs for development/testing
- Enhanced prerequisites (dependency on Story 5.2)

**Story 5.4 (Download & Feedback Flow):**
- **Action 1.1:** Integration Test Suite
  - Create `tests/integration/test_full_pipeline.py`
  - 5 test scenarios (simple, complex, multi-language, large, edge case)
  - Validates full pipeline with real AI APIs
  - Add to CI/CD with monthly schedule

### Rationale

**Why Direct Adjustment:**

1. **Prevents Future Rework**
   - Story 4-4 second review cost ~4 hours
   - Action 1.1 (integration tests) prevents similar issues
   - ROI: 4-6 hours investment saves 10+ hours debugging

2. **Unblocks Epic 5 Development**
   - **Critical:** Action 1.4 (sample PDFs) REQUIRED for Story 5.2 and 5.3
   - Frontend cannot build Quality Report UI without real conversion outputs
   - Action 1.5 (UX language) needed for UI copy/design

3. **Production Readiness**
   - Action 1.2 (cost monitoring) critical before launch
   - Production pricing decisions require cost visibility
   - Deferred from Epic 3, cannot defer again

4. **Quality First**
   - Integration tests (Action 1.1) validate Epic 4 + Epic 5 end-to-end
   - Pre-flight checklist (Action 1.3) prevents integration gaps
   - Aligns with "build it right" philosophy

5. **Minimal Timeline Impact**
   - +10-13 hours across 4 stories
   - Epic 5 extends +1-2 days (from ~10-14 days to ~12-16 days)
   - 20-30% increase, acceptable for quality improvement

### Effort and Risk Assessment

**Effort Estimate:**
- **Original Epic 5:** 10-14 days (4 stories, frontend complexity)
- **Added Effort:** +10-13 hours (5 actions integrated)
- **New Epic 5 Estimate:** 12-16 days

**Risk Level:** **LOW**

**Risks Mitigated:**
- ✅ Frontend blocked without test data (Action 1.4 provides sample PDFs)
- ✅ Integration bugs (Action 1.1 catches issues early)
- ✅ Production cost surprises (Action 1.2 provides visibility)
- ✅ UX confusion (Action 1.5 translates technical scores)

**Risks Introduced:**
- ⚠️ Epic 5 timeline extends +1-2 days (acceptable trade-off)
- ⚠️ Monthly AI cost +$50 for integration tests (budgeted)

**Timeline Impact:**
- **MVP Delivery:** Minimal (1-2 days delay)
- **Quality Improvement:** Significant (integration tests, cost monitoring, UX clarity)

---

## Section 4: Detailed Change Proposals

### Change Proposal 1: Epic 5, Story 5.1 - Real-time Progress Updates

**Story ID:** Story 5.1
**Artifact:** `docs/epics.md` (Epic 5, Story 5.1)
**Section:** Acceptance Criteria

#### CURRENT ACCEPTANCE CRITERIA

```markdown
- [ ] WebSocket or Polling mechanism implemented for Job Status
- [ ] Frontend updates progress bar and status text (e.g., "Analyzing Layout: 45%")
- [ ] "Detected Elements" counter updates live (FR32)
- [ ] Smooth animations for progress transitions
- [ ] Handling of connection loss/reconnect
```

#### PROPOSED ADDITIONS

```markdown
**NEW ACCEPTANCE CRITERIA (from Action 1.2: AI Cost Monitoring):**

- [ ] **AI Cost Tracking:** LangChain callbacks implemented to count tokens per AI call
  - Callback tracks: `prompt_tokens`, `completion_tokens`, `total_tokens`
  - Callback class: `backend/app/services/ai/cost_tracker.py`
  - Integrated with Story 4.2 (LayoutAnalyzer) and Story 4.3 (StructureAnalyzer)
  - Stored in `conversion_jobs.quality_report` JSONB field

- [ ] **Cost Estimation:** Calculate cost per job based on model pricing
  - GPT-4o: $2.50/1M input tokens, $10.00/1M output tokens
  - Claude 3 Haiku: $0.25/1M input tokens, $1.25/1M output tokens
  - Formula: `(prompt_tokens / 1M * input_price) + (completion_tokens / 1M * output_price)`
  - Round to 4 decimal places (e.g., $0.1523)

- [ ] **Real-time Cost Display:** Progress UI shows estimated cost as jobs complete
  - Example: "Processing... Estimated cost: $0.12"
  - Updates incrementally as AI analysis stages complete
  - Final cost displayed on completion

- [ ] **Quality Report Integration:** Add cost fields to quality_report JSON schema
  ```json
  {
    "overall_confidence": 95,
    "estimated_cost": 0.15,
    "token_usage": {
      "prompt_tokens": 5000,
      "completion_tokens": 2000,
      "total_tokens": 7000
    },
    "elements": {
      "tables": { "count": 12, "avg_confidence": 93 },
      "images": { "count": 8 },
      "equations": { "count": 5, "avg_confidence": 97 }
    }
  }
  ```

**NEW ACCEPTANCE CRITERIA (from Action 1.3: Pre-Flight Checklist):**

- [ ] **Create Pre-Flight Integration Checklist Template**
  - Save to `.bmad/bmm/templates/pre-flight-checklist.md`
  - Template includes sections:
    - Services & Dependencies (all services instantiated and called)
    - Data Flow (input validation, transformations, output storage)
    - Error Handling (failure modes, graceful degradation, retries)
    - Testing (unit tests, integration tests, edge cases)
    - Documentation (completion notes, API contracts, known limitations)
  - Mandatory for all Epic 5 stories before marking "review"
  - Developer checks off items as story progresses
  - Include checklist in PR for code review
```

#### Rationale

- **Action 1.2 (AI Cost Monitoring):**
  - Deferred from Epic 3, critical for production pricing
  - Story 5.1 already displays real-time progress → natural fit for cost display
  - Prevents production cost surprises (NFR7: optimize AI costs)

- **Action 1.3 (Pre-Flight Checklist):**
  - Prevents Story 4-4 type integration gaps (ContentAssembler not integrated)
  - Creates culture of thoroughness before code review
  - Minimal effort (30 min template creation) with high ROI

#### Estimated Effort Increase

- **Action 1.2:** +2-3 hours
  - Create `cost_tracker.py` callback class (1 hour)
  - Integrate with LayoutAnalyzer and StructureAnalyzer (1 hour)
  - Frontend cost display UI (30 min)
  - Testing (30 min)

- **Action 1.3:** +30 minutes
  - Create template with sections (20 min)
  - Document usage in Epic 5 stories (10 min)

**Total:** +3 hours

---

### Change Proposal 2: Epic 5, Story 5.2 - Job Status & Quality Report Page

**Story ID:** Story 5.2
**Artifact:** `docs/epics.md` (Epic 5, Story 5.2)
**Sections:** Prerequisites + Acceptance Criteria

#### CURRENT PREREQUISITES

```markdown
**Prerequisites:** Story 5.1
```

#### PROPOSED PREREQUISITE ADDITION

```markdown
**Prerequisites:** Story 5.1, **Action 1.4 (Sample PDFs curated BEFORE Story 5.2 implementation begins)**
```

#### CURRENT ACCEPTANCE CRITERIA

```markdown
- [ ] Job Details page created (`/jobs/{id}`)
- [ ] Success state displays "Quality Report" summary (FR33)
- [ ] Metrics displayed: Number of pages, tables, images, equations
- [ ] "Confidence Score" visual indicator
- [ ] Call-to-action buttons: "Preview Comparison" and "Download EPUB"
```

#### PROPOSED ADDITIONS

```markdown
**NEW PREREQUISITE (from Action 1.4: Sample PDFs for Frontend Testing):**

**IMPORTANT:** Complete BEFORE Story 5.2 implementation begins.

- [ ] **Test PDF Suite Curated:**
  - **5 test PDFs** covering all scenarios:
    1. **Simple Text PDF** (10-20 pages, text-only)
       - No tables, images, or equations
       - Expected: 99%+ confidence, <30 seconds processing
    2. **Complex Technical Book** (50-100 pages)
       - Contains: 5+ tables, 10+ images, 5+ equations, multi-column layout
       - Expected: 90-95% confidence, warnings on complex tables
    3. **Multi-Language Document**
       - English + Chinese/Japanese characters
       - Tests CJK font embedding
       - Expected: 95%+ confidence, font-face CSS in EPUB
    4. **Large File** (300+ pages, performance test)
       - Mixed content (text, tables, images)
       - Expected: <2 minute conversion (FR35), file size ≤ 120% PDF (FR37)
    5. **Edge Case** (stress test)
       - Heavily damaged scan OR unusual layout
       - Expected: <80% confidence, multiple warnings

  - **Processing:** Run all 5 PDFs through Epic 4 pipeline
  - **Storage:** Save outputs to `tests/fixtures/epic-5-sample-pdfs/`
    ```
    tests/fixtures/epic-5-sample-pdfs/
    ├── 1-simple-text/
    │   ├── input.pdf
    │   ├── output.epub
    │   ├── quality_report.json
    │   └── screenshots/ (key pages)
    ├── 2-complex-technical/
    ├── 3-multi-language/
    ├── 4-large-file/
    └── 5-edge-case/
    ```
  - **Documentation:** Document expected quality metrics for each PDF
  - **Handoff:** Share with frontend team before Story 5.2 implementation

**NEW ACCEPTANCE CRITERIA (from Action 1.5: Quality Display Language):**

- [ ] **User-Friendly Quality Messaging:** Map technical confidence scores to plain English

  **Mapping Rules:**
  | Confidence Range | Quality Level | Message | Emoji | User Action |
  |------------------|---------------|---------|-------|-------------|
  | 95-100% | Excellent | All elements preserved perfectly | ✅ | Ready to download |
  | 85-94% | Very Good | Nearly all elements preserved | ✅ | Download with confidence |
  | 75-84% | Good | Most elements preserved, minor adjustments possible | ⚠️ | Preview flagged pages |
  | 60-74% | Fair | Some elements may need manual review | ⚠️ | Review recommended |
  | <60% | Review Required | Significant issues detected | ❌ | Manual review strongly recommended |

  **Element-Specific Message Templates:**
  - **Tables:**
    - HIGH confidence (>90%): "12 tables detected and preserved"
    - MEDIUM confidence (70-90%): "12 tables detected, 2 may need review"
    - LOW confidence (<70%): "12 tables detected, 5 require manual verification"
  - **Equations:**
    - HIGH (>90%): "All 8 equations rendered correctly"
    - MEDIUM (70-90%): "8 equations detected, 1 may have minor issues"
    - LOW (<70%): "8 equations detected, 3 require verification"
  - **Images:**
    - "8 images detected and preserved" (always 100% confidence)

- [ ] **Quality Report UI Implementation:**
  - Overall quality level with emoji (✅/⚠️/❌) prominently displayed
  - User-friendly message (e.g., "Very Good - Nearly all elements preserved")
  - Raw confidence score hidden or shown in "Details" section
  - Expandable element details (tables, images, equations counts)
  - Warning messages with page numbers and actionable guidance
    - Example: "Page 45: Table low confidence (72%) - Preview this page to verify accuracy"
  - **User action prompt** based on quality level (e.g., "Ready to download" vs. "Preview recommended")
  - **Estimated cost displayed** (from Action 1.2, Story 5.1): "Processing cost: $0.15"

- [ ] **UX Alignment:** Verify messaging follows PRD UX Principle "Transparency Through Feedback"
  - Plain English, no jargon
  - Clear next steps for users
  - Builds confidence through specific details
```

#### Rationale

- **Action 1.4 (Sample PDFs):**
  - **CRITICAL BLOCKER:** Frontend cannot build Quality Report UI without real conversion outputs
  - Must complete BEFORE Story 5.2 begins (prerequisite, not acceptance criteria)
  - Provides test data for Action 1.5 (UX language design)

- **Action 1.5 (Quality Display Language):**
  - Implements PRD UX Principle "Transparency Through Feedback"
  - Technical scores (95%) meaningless to users → "Excellent quality ✅" builds trust
  - Story 5.2 builds Quality Report page → ideal integration point

#### Estimated Effort Increase

- **Action 1.4 (Prerequisite):** +1-2 hours
  - Curate/find 5 test PDFs (30 min)
  - Run through Epic 4 pipeline (30 min)
  - Save outputs and document (30 min)

- **Action 1.5:** +1-2 hours
  - Design mapping rules and message templates (1 hour, collaborative with UX)
  - Implement in Quality Report UI (1 hour)

**Total:** +2-3 hours

---

### Change Proposal 3: Epic 5, Story 5.3 - Split-Screen Comparison UI

**Story ID:** Story 5.3
**Artifact:** `docs/epics.md` (Epic 5, Story 5.3)
**Section:** Prerequisites + Technical Notes

#### CURRENT PREREQUISITES

```markdown
**Prerequisites:** Story 5.2
```

#### PROPOSED CHANGE

```markdown
**Prerequisites:** Story 5.2 **(including Action 1.4: Sample PDFs curated)**
```

#### CURRENT TECHNICAL NOTES

```markdown
**Technical Notes:**
- UX Spec: "Pre-Download Quality Verification" pattern
- This is the **Core Differentiator** - needs high polish

**Prerequisites:** Story 5.2
```

#### PROPOSED ADDITIONS TO TECHNICAL NOTES

```markdown
**Technical Notes (ADDITIONS):**

**Test Data (from Action 1.4, Story 5.2):**
- Use sample EPUBs from `tests/fixtures/epic-5-sample-pdfs/` for development
  - **Simple text PDF:** Baseline rendering test
  - **Complex technical book:** Validate table/equation rendering in split-screen
  - **Multi-language document:** Test CJK font rendering in browser
  - **Large file:** Performance test (`react-pdf` + `react-reader` with 300+ pages)
  - **Edge case:** Test low-quality rendering and warning displays

**PDF Viewer Evaluation (from Epic 4 Retrospective Action 3.1):**
- Test `react-pdf` library performance with large PDFs
  - Load time benchmarks: 10-page, 50-page, 300-page PDFs
  - Memory usage during rendering
  - Scrolling performance (60fps target)
  - Initial render vs. lazy loading
- **Alternatives if `react-pdf` insufficient:**
  - PDF.js (Mozilla's library, more control but complex)
  - `<iframe>` embed (simplest, least features)
  - Server-side rendering to images (fallback for very large files)
- **Success Criteria:**
  - 300-page PDF loads in <5 seconds
  - Smooth scrolling (no jank)
  - Memory usage <500MB for large files

**EPUB Rendering Strategy (from Epic 4 Retrospective Action 3.2):**
- **Option A:** `react-reader` library (native EPUB rendering)
  - Pros: Native EPUB rendering, TOC navigation
  - Cons: May not match e-reader app rendering exactly
- **Option B:** Convert EPUB → HTML preview on backend
  - Pros: Full control over rendering, exact CSS match
  - Cons: Extra backend work, storage for HTML previews
- **Recommendation:** Prototype Option A first, evaluate rendering fidelity
  - Compare rendering to Apple Books/Calibre
  - If fidelity insufficient (<95% visual match), prototype Option B
- **Success Criteria:**
  - EPUB renders in <3 seconds
  - Visual fidelity acceptable (matches e-reader within 95%)
  - TOC navigation functional
```

#### Rationale

- Story 5.3 **depends on** Story 5.2's Action 1.4 outputs (sample EPUBs)
- Epic 4 Retrospective Priority 3 actions (3.1, 3.2) are Story 5.3 prep work
- No new acceptance criteria needed (design decisions, not deliverables)

#### Estimated Effort Increase

**+0 hours** (dependency enhancement, not new work)

---

### Change Proposal 4: Epic 5, Story 5.4 - Download & Feedback Flow

**Story ID:** Story 5.4
**Artifact:** `docs/epics.md` (Epic 5, Story 5.4)
**Section:** Acceptance Criteria

#### CURRENT ACCEPTANCE CRITERIA

```markdown
- [ ] "Download EPUB" button triggers file download (FR38)
- [ ] "Report Issue" button allows user to flag specific pages/elements
- [ ] Simple feedback form ("Was this conversion good? 👍/👎")
- [ ] Confetti animation on successful download (Delight factor)
```

#### PROPOSED ADDITIONS

```markdown
**NEW ACCEPTANCE CRITERIA (from Action 1.1: Integration Test Suite):**

- [ ] **End-to-End Integration Test Suite Created:**

  **Test File:** `tests/integration/test_full_pipeline.py`

  **Test Scenarios (5 total):**

  1. **Simple Text PDF** (Baseline Test)
     - Input: 10-20 page text-only PDF
     - Expected: 99%+ confidence, <30 seconds processing
     - Validation: EPUB validates against EPUB 3.0 spec (epubcheck)

  2. **Complex Technical Book**
     - Input: 50-100 pages with 5+ tables, 10+ images, 5+ equations, multi-column layout
     - Expected: 90-95% confidence, warnings on complex tables
     - Validation: Tables rendered as HTML `<table>`, equations as MathML or PNG

  3. **Multi-Language Document**
     - Input: English + Chinese/Japanese characters
     - Expected: 95%+ confidence, CJK fonts embedded
     - Validation: EPUB contains font-face CSS, characters render correctly

  4. **Large File** (Performance Test)
     - Input: 300+ pages, mixed content
     - Expected: <2 minute conversion (FR35), file size ≤ 120% PDF (FR37)
     - Validation: Performance targets met, file size validation

  5. **Edge Case** (Stress Test)
     - Input: Corrupted elements, missing TOC, malformed tables
     - Expected: <80% confidence, multiple warnings, graceful degradation
     - Validation: Pipeline completes without crashing, quality report reflects issues

  **Test Flow:** PDF Upload → AI Layout Analysis → Structure Recognition → EPUB Generation → Quality Scoring → Download

  **Success Criteria:**
  - All 5 tests pass with **real AI APIs** (GPT-4o/Claude 3 Haiku)
  - Quality reports match expected confidence ranges (±5%)
  - Generated EPUBs validate against EPUB 3.0 spec (epubcheck)
  - File sizes ≤ 120% of original PDF (FR37)
  - No pipeline crashes or unhandled exceptions

  **CI/CD Integration:**
  - Add to GitHub Actions workflow
  - **Schedule:** Monthly (not on every PR due to cost)
  - **Trigger:** Manual dispatch for pre-release testing
  - **Budget:** $50/month AI API budget (~$10-15 per full run)

  **Test Commands:**
  ```bash
  # Run integration tests (monthly)
  pytest tests/integration/test_full_pipeline.py -v --real-ai

  # Cost estimate: ~$10-15 per full test run
  ```

- [ ] **Pre-Flight Checklist Applied (from Action 1.3, Story 5.1):**
  - Use template from `.bmad/bmm/templates/pre-flight-checklist.md`
  - Verify all integration points before marking "review":
    - Download button triggers Supabase Storage signed URL
    - Feedback form submits to database
    - Integration test suite validates full Epic 5 + Epic 4 pipeline
  - Include completed checklist in PR for code review
```

#### Rationale

- **Action 1.1 (Integration Test Suite):**
  - **Root Cause:** Story 4-4 blockers (ContentAssembler not integrated) would have been caught by integration tests
  - **Prevention:** Monthly integration tests catch regressions before production
  - **Story 5.4 is ideal:** Completes Epic 5 delivery, integration test validates entire pipeline

- **Action 1.3 (Pre-Flight Checklist):**
  - Apply checklist created in Story 5.1
  - Ensures thoroughness before final Epic 5 code review

#### Estimated Effort Increase

- **Action 1.1:** +4-6 hours
  - Create test file structure (30 min)
  - Implement 5 test scenarios (2-3 hours)
  - Integrate with CI/CD (1 hour)
  - Document expected outputs (30 min)
  - Initial test run and debugging (1-2 hours)

- **Action 1.3:** +1 hour
  - Apply checklist to Story 5.4 (30 min)
  - Verify all items before code review (30 min)

**Total:** +5-7 hours

---

## Section 5: Implementation Handoff

### Change Scope Classification

**Classification:** **Moderate**

**Rationale:**
- **Not Minor:** 10-13 hours effort, changes 4 story acceptance criteria
- **Not Major:** No fundamental replan, no new epics, no architecture changes
- **Moderate:** Backlog reorganization within Epic 5, integration of quality improvements

### Handoff Recipients and Responsibilities

**Primary Owner:** **Development Team**

**Responsibilities:**
1. **Before Epic 5 Begins:**
   - Review updated Epic 5 acceptance criteria in `docs/epics.md`
   - Complete Action 1.4 (Sample PDFs) BEFORE starting Story 5.2

2. **During Epic 5 Implementation:**
   - **Story 5.1:** Implement Actions 1.2 (AI Cost Monitoring) and 1.3 (Pre-Flight Checklist)
   - **Story 5.2:** Implement Action 1.5 (Quality UX Language), use Action 1.4 outputs
   - **Story 5.3:** Use Action 1.4 sample EPUBs for testing
   - **Story 5.4:** Implement Action 1.1 (Integration Test Suite)

3. **Code Review:**
   - Apply Pre-Flight Checklist (Action 1.3) before marking stories "review"
   - Include checklist in PR description

**Secondary Owner:** **Product Owner / Scrum Master**

**Responsibilities:**
1. Approve Sprint Change Proposal (this document)
2. Update `docs/epics.md` with revised Epic 5 acceptance criteria (after approval)
3. Monitor Epic 5 timeline for +1-2 day impact
4. Schedule monthly integration test runs (Action 1.1)

**Tertiary Owner:** **UX Designer** (for Action 1.5)

**Responsibilities:**
1. Collaborate on Action 1.5 (Quality Display Language)
   - Review mapping rules and message templates
   - Provide emoji/icon recommendations
   - Validate user-friendly tone

### Deliverables

**Artifact Updates Required:**
1. **`docs/epics.md`** - Update Epic 5 stories with new acceptance criteria (4 stories affected)
2. **`.bmad/bmm/templates/pre-flight-checklist.md`** - Create template (Story 5.1)
3. **`tests/fixtures/epic-5-sample-pdfs/`** - Curate and process 5 test PDFs (Story 5.2 prerequisite)
4. **`tests/integration/test_full_pipeline.py`** - Create integration test suite (Story 5.4)
5. **`backend/app/services/ai/cost_tracker.py`** - Create cost tracking service (Story 5.1)

**Process Changes:**
1. Apply Pre-Flight Checklist to all Epic 5 stories before code review
2. Schedule monthly integration test runs (CI/CD)
3. Budget $50/month for AI integration test costs

### Success Criteria

**This change is successful when:**

1. ✅ Epic 5 stories have updated acceptance criteria in `docs/epics.md`
2. ✅ Frontend developers have access to 5 sample conversion outputs (Action 1.4)
3. ✅ Quality Report UI uses user-friendly language (Action 1.5)
4. ✅ Real-time progress displays estimated AI costs (Action 1.2)
5. ✅ Pre-Flight Checklist template exists and is used (Action 1.3)
6. ✅ Integration test suite validates full pipeline (Action 1.1)
7. ✅ Epic 5 completes within +1-2 days of original estimate
8. ✅ No Story 4-4 type integration gaps in Epic 5 (prevented by checklist + tests)

### Timeline

**Immediate (Today):**
- xavier approves Sprint Change Proposal

**Before Epic 5 Story 5.2 Begins:**
- Complete Action 1.4 (Sample PDFs) - **CRITICAL PREREQUISITE**
- Update `docs/epics.md` with revised acceptance criteria

**During Epic 5 Implementation:**
- Story 5.1: Implement Actions 1.2, 1.3 (+3 hours)
- Story 5.2: Implement Action 1.5 (+1-2 hours)
- Story 5.4: Implement Action 1.1 (+4-6 hours)

**After Epic 5 Completion:**
- Schedule monthly integration test runs
- Review AI cost data from Action 1.2
- Retrospective: Evaluate Pre-Flight Checklist effectiveness

---

## Appendix A: Action Items Reference

**Source:** `docs/sprint-artifacts/epic-4-action-items.md`

**Priority 1 (Integrated into Epic 5):**

| Action | Title | Effort | Integration Point | Status |
|--------|-------|--------|-------------------|--------|
| 1.1 | Integration Test Suite | 4-6 hours | Epic 5, Story 5.4 | 🟡 Pending |
| 1.2 | AI Cost Monitoring | 2-3 hours | Epic 5, Story 5.1 | 🟡 Pending |
| 1.3 | Pre-Flight Checklist | 30 min | Epic 5, Story 5.1 | 🟡 Pending |
| 1.4 | Sample PDFs | 1-2 hours | Epic 5, Story 5.2 (Prereq) | 🟡 Pending |
| 1.5 | Quality Display Language | 1-2 hours | Epic 5, Story 5.2 | 🟡 Pending |

**Priority 2 (Complete):**
- Action 2.1: Quality Report API ✅
- Action 2.2: EPUB Compatibility ✅
- Action 2.3: API Keys Configuration ✅

**Priority 3 (Epic 5 Prep, Referenced in Story 5.3):**
- Action 3.1: PDF Viewer Evaluation (Story 5.3 technical notes)
- Action 3.2: EPUB Rendering Strategy (Story 5.3 technical notes)
- Action 3.3: Real-Time Updates Decision (Story 5.1 architecture)

---

## Appendix B: Epic 5 Effort Comparison

| Metric | Original Epic 5 | With Actions Integrated | Delta |
|--------|----------------|------------------------|-------|
| **Stories** | 4 | 4 | 0 |
| **Effort** | 10-14 days | 12-16 days | +1-2 days |
| **Acceptance Criteria** | 17 | 27 | +10 |
| **Test Coverage** | Unit tests only | Unit + Integration | +Integration suite |
| **Production Readiness** | Basic | Full (cost monitoring, integration tests) | Significant |
| **Risk Level** | Medium (no integration tests) | Low (comprehensive testing) | Reduced |

---

## Sign-Off

**Prepared By:** Correct Course Workflow
**Date:** 2025-12-14
**Status:** ✅ **APPROVED**

**Approver:** xavier
**Approval Date:** 2025-12-14
**Decision:** APPROVED ✅

---

## Next Steps

1. ✅ Update `docs/epics.md` with revised Epic 5 acceptance criteria
2. ✅ Route to Development Team for implementation
3. ✅ Complete Action 1.4 (Sample PDFs) BEFORE starting Epic 5 Story 5.2
4. ✅ Apply Pre-Flight Checklist to all Epic 5 stories

---

*🤖 Generated with [Claude Code](https://claude.com/claude-code)*
