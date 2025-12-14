# Epic 4 Retrospective - Action Items

**Generated:** 2025-12-13
**Source:** Epic 4 Retrospective
**Epic:** Epic 4 - AI-Powered Conversion Engine
**Status:** ✅ Complete

---

## Action Items Summary

**Total Action Items:** 9
**Priority 1 (Before Epic 5):** 5 items
**Priority 2 (Complete):** 3 items ✅
**Priority 3 (Epic 5 Prep):** 4 items

---

## Priority 1: Code Quality (Before Epic 5)

### Action 1.1: Create Integration Test Suite for AI Pipeline

**Status:** 🟡 PENDING
**Owner:** Dev Team
**Effort:** 4-6 hours
**Cost:** $50/month AI API budget
**Blocker:** No, but prevents future rework

**Description:**
Create end-to-end integration test suite for the full conversion pipeline.

**Test Scenarios:**
1. **Simple Text PDF:** Baseline test (text-only, no complex elements)
2. **Complex Technical Book:** Tables, equations, multi-column layouts
3. **Multi-Language Document:** CJK font embedding validation
4. **Large File:** 300+ pages performance test
5. **Edge Cases:** Corrupted elements, missing TOC, malformed tables

**Test Flow:**
```
PDF Upload → AI Layout Analysis → Structure Recognition → EPUB Generation → Quality Scoring → Download
```

**Success Criteria:**
- All tests pass with real AI APIs (GPT-4o/Claude 3 Haiku)
- Quality reports match expected confidence ranges
- Generated EPUBs validate against EPUB 3.0 spec
- File sizes ≤ 120% of original PDF

**Test Commands:**
```bash
# Run integration tests (monthly)
pytest tests/integration/test_full_pipeline.py -v --real-ai

# Cost estimate: ~$10-15 per full test run
```

**Why This Matters:**
Story 4-4 blockers (ContentAssembler not integrated) would have been caught by this test suite. Prevents integration gaps in Epic 5.

**Deliverables:**
- [ ] Create `tests/integration/test_full_pipeline.py`
- [ ] Curate test PDF suite (5 PDFs covering all scenarios)
- [ ] Document expected outputs for each test PDF
- [ ] Add to CI/CD with monthly schedule

---

### Action 1.2: Implement AI Cost Monitoring

**Status:** 🟡 PENDING
**Owner:** Dev Team
**Effort:** 2-3 hours
**Blocker:** No, but critical for production pricing
**Integration Point:** Story 5.1 (Real-time Progress Updates)

**Description:**
Add LangChain callbacks to track token usage and estimate AI API costs per job.

**Implementation Plan:**

**Step 1: LangChain Callback Handler**
```python
# backend/app/services/ai/cost_tracker.py
from langchain.callbacks.base import BaseCallbackHandler

class CostTrackingCallback(BaseCallbackHandler):
    def __init__(self):
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0

    def on_llm_end(self, response, **kwargs):
        usage = response.llm_output.get("token_usage", {})
        self.prompt_tokens += usage.get("prompt_tokens", 0)
        self.completion_tokens += usage.get("completion_tokens", 0)
        self.total_tokens += usage.get("total_tokens", 0)

    def calculate_cost(self, model: str) -> float:
        """Calculate cost based on model pricing."""
        if model == "gpt-4o":
            input_cost = (self.prompt_tokens / 1_000_000) * 2.50
            output_cost = (self.completion_tokens / 1_000_000) * 10.00
        elif model == "claude-3-haiku":
            input_cost = (self.prompt_tokens / 1_000_000) * 0.25
            output_cost = (self.completion_tokens / 1_000_000) * 1.25
        else:
            return 0.0

        return round(input_cost + output_cost, 4)
```

**Step 2: Integration with Pipeline**
```python
# backend/app/tasks/conversion_pipeline.py
from app.services.ai.cost_tracker import CostTrackingCallback

@celery_app.task
def analyze_layout(job_id: str):
    cost_tracker = CostTrackingCallback()

    # Pass callback to LangChain
    result = layout_analyzer.analyze(pdf_path, callbacks=[cost_tracker])

    # Calculate and store cost
    estimated_cost = cost_tracker.calculate_cost("gpt-4o")

    # Add to quality_report
    quality_report["estimated_cost"] = estimated_cost
    quality_report["token_usage"] = {
        "prompt_tokens": cost_tracker.prompt_tokens,
        "completion_tokens": cost_tracker.completion_tokens,
        "total_tokens": cost_tracker.total_tokens
    }
```

**Step 3: Display in Quality Report**
```json
{
  "overall_confidence": 95,
  "estimated_cost": 0.15,
  "token_usage": {
    "prompt_tokens": 5000,
    "completion_tokens": 2000,
    "total_tokens": 7000
  },
  "elements": { ... }
}
```

**Success Criteria:**
- Cost estimates within ±10% of actual API charges
- Token counts logged for all AI calls
- Quality report includes `estimated_cost` field
- Dashboard shows total monthly AI spend

**Deliverables:**
- [ ] Create `backend/app/services/ai/cost_tracker.py`
- [ ] Integrate with Story 4.2 (Layout Analysis)
- [ ] Integrate with Story 4.3 (Structure Analysis)
- [ ] Update quality_report schema to include cost fields
- [ ] Add cost monitoring dashboard (admin view)

---

### Action 1.3: Pre-Flight Integration Checklist Template

**Status:** 🟢 CREATE NOW
**Owner:** Dev Team
**Effort:** 30 minutes

**Description:**
Create a markdown checklist template to verify integration completeness before marking complex stories as done.

**Template:**

```markdown
# Pre-Flight Integration Checklist

**Story:** [Story Number and Title]
**Date:** YYYY-MM-DD
**Developer:** [Name]

---

## Integration Verification

### Services & Dependencies
- [ ] All services instantiated in integration points (no unused imports)
- [ ] All service methods called where expected (verified with grep/search)
- [ ] All imports verified (no missing dependencies at runtime)
- [ ] Dependency injection configured correctly

### Data Flow
- [ ] Input data validated with Pydantic schemas
- [ ] Data transformations tested (e.g., AI response → XHTML)
- [ ] Output data stored correctly (database, storage)
- [ ] Data passed between pipeline stages validated

### Error Handling
- [ ] All failure modes covered (AI errors, network failures, validation errors)
- [ ] Graceful degradation implemented (fallbacks defined)
- [ ] Error messages user-friendly (no stack traces to users)
- [ ] Retry logic configured (exponential backoff)

### Testing
- [ ] Unit tests pass (100%)
- [ ] Integration test validates full data flow (if applicable)
- [ ] Edge cases tested (missing data, malformed input)
- [ ] Performance acceptable (no obvious bottlenecks)

### Documentation
- [ ] Completion notes updated with actual implementation
- [ ] API contracts documented (if new endpoints)
- [ ] Configuration variables documented
- [ ] Known limitations documented

---

## Sign-Off

- [ ] All checklist items verified
- [ ] Story ready for code review
- [ ] Integration points tested end-to-end

**Developer Signature:** _______________
**Date:** _______________
```

**Usage:**
1. Copy template to story directory before implementation
2. Check off items as story progresses
3. Verify all items before marking story as "review"
4. Include checklist in code review PR

**Deliverables:**
- [ ] Save template to `.bmad/bmm/templates/pre-flight-checklist.md`
- [ ] Add to story workflow (mandatory for HIGH complexity stories)
- [ ] Train team on usage

---

### Action 1.4: Prepare Sample PDFs for Frontend Testing

**Status:** 🟡 NEEDED (Before Story 5.2)
**Owner:** Dev Team
**Effort:** 1-2 hours

**Description:**
Curate a test PDF suite for Epic 5 frontend developers to build and test the preview UI.

**Test PDF Suite:**

1. **Simple Text PDF (Baseline)**
   - 10-20 pages, text-only
   - No tables, images, equations
   - Expected: 99%+ confidence, fast conversion

2. **Complex Technical Book**
   - 50-100 pages
   - Contains: 5+ tables, 10+ images, 5+ equations, multi-column layout
   - Expected: 90-95% confidence, warnings on complex tables

3. **Multi-Language Document**
   - English + Chinese/Japanese characters
   - Tests CJK font embedding
   - Expected: 95%+ confidence, font-face CSS in EPUB

4. **Large File (Performance Test)**
   - 300+ pages
   - Mixed content
   - Expected: <2 minute conversion (FR35), file size ≤ 120% PDF

5. **Edge Case (Stress Test)**
   - Heavily damaged scan OR unusual layout
   - Expected: Lower confidence (<80%), multiple warnings

**For Each PDF:**
- Run through Epic 4 pipeline
- Save conversion outputs:
  - Original PDF (for before/after comparison)
  - Generated EPUB
  - Quality report JSON
  - Screenshots of key pages

**Storage:**
```
tests/fixtures/epic-5-sample-pdfs/
├── 1-simple-text/
│   ├── input.pdf
│   ├── output.epub
│   ├── quality_report.json
│   └── screenshots/
├── 2-complex-technical/
│   ├── input.pdf
│   ├── output.epub
│   ├── quality_report.json
│   └── screenshots/
├── 3-multi-language/
├── 4-large-file/
└── 5-edge-case/
```

**Deliverables:**
- [ ] Curate 5 test PDFs (copyright-free or internal)
- [ ] Run conversions and save outputs
- [ ] Document expected quality metrics for each
- [ ] Share with frontend team before Story 5.2 begins

---

### Action 1.5: Design Quality Metrics Display Language

**Status:** 🟡 NEEDED (Before Story 5.2)
**Owner:** Dev Team + UX
**Effort:** 1-2 hours (collaborative session)

**Description:**
Map technical confidence scores to user-friendly language for the quality report UI.

**Current State (Technical):**
```json
{
  "overall_confidence": 94.5,
  "warnings": ["Page 45: Table low confidence (72%)"]
}
```

**Desired State (User-Friendly):**
```json
{
  "quality_level": "Very Good",
  "quality_message": "Nearly all elements preserved perfectly",
  "quality_emoji": "✅",
  "warnings": [
    {
      "severity": "WARNING",
      "page": 45,
      "message": "Table on page 45 may need review",
      "user_action": "Check this page in the preview to verify accuracy"
    }
  ]
}
```

**Mapping Rules:**

| Confidence Range | Quality Level | Message | Emoji | User Action |
|------------------|---------------|---------|-------|-------------|
| 95-100% | Excellent | All elements preserved perfectly | ✅ | Ready to download |
| 85-94% | Very Good | Nearly all elements preserved | ✅ | Download with confidence |
| 75-84% | Good | Most elements preserved, minor adjustments possible | ⚠️ | Preview flagged pages |
| 60-74% | Fair | Some elements may need manual review | ⚠️ | Review recommended |
| <60% | Review Required | Significant issues detected | ❌ | Manual review strongly recommended |

**Warning Message Templates:**

**Tables:**
- HIGH confidence (>90%): "12 tables detected and preserved"
- MEDIUM confidence (70-90%): "12 tables detected, 2 may need review"
- LOW confidence (<70%): "12 tables detected, 5 require manual verification"

**Equations:**
- HIGH: "All 8 equations rendered correctly"
- MEDIUM: "8 equations detected, 1 may have minor issues"
- LOW: "8 equations detected, 3 require verification"

**Deliverables:**
- [ ] Document mapping rules (technical → user-friendly)
- [ ] Create message templates for all element types
- [ ] Define emoji/icon set for quality levels
- [ ] Review with UX for tone and clarity
- [ ] Implement in Story 5.2 frontend code

---

## Priority 2: Epic 5 Foundation (Complete ✅)

### Action 2.1: Verify Quality Report API Integration ✅

**Status:** ✅ COMPLETE
**Completed:** 2025-12-13

**Evidence:**
- Story 4-5 bug fix: Added `QualityReport` import to `job_service.py`
- `GET /api/v1/jobs/{id}?include_quality_details=true` returns full quality report
- All 23 unit tests passing

**No further action needed.**

---

### Action 2.2: Test EPUB Compatibility ✅

**Status:** ✅ COMPLETE
**Completed:** 2025-12-13 (Story 4-4)

**Evidence:**
- EPUB 3.0 spec compliance validated
- `epub_validator.py` validates structure, XHTML, file size
- Font manager embeds CJK fonts correctly
- All 8 unit tests passing

**No further action needed.**

---

### Action 2.3: API Keys Configuration ✅

**Status:** ✅ COMPLETE
**Completed:** 2025-12-12 (Epic 3 Retrospective verification)

**Evidence:**
- `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` configured
- Live AI connectivity tests successful (Epic 3 retrospective)
- Both GPT-4o and Claude 3 Haiku operational

**No further action needed.**

---

## Priority 3: Epic 5 Preparation

### Action 3.1: PDF Viewer Library Evaluation

**Status:** 🟡 PENDING (Story 5.3 Prep)
**Owner:** Frontend Team
**Effort:** 2-3 hours
**Story:** 5.3 (Split-Screen Comparison UI)

**Description:**
Evaluate `react-pdf` performance with large PDFs to ensure smooth user experience.

**Evaluation Criteria:**

1. **Performance Benchmarks:**
   - Load time: 10-page PDF, 50-page PDF, 300-page PDF
   - Memory usage during rendering
   - Scrolling performance (60fps target)
   - Initial render vs. lazy loading

2. **Feature Support:**
   - Text selection (for copy-paste)
   - Zoom in/out
   - Page navigation
   - Search within PDF (nice to have)

3. **Browser Compatibility:**
   - Chrome, Firefox, Safari, Edge
   - Mobile browsers (iOS Safari, Chrome Mobile)

**Test PDFs:**
- Use Action 1.4 sample PDFs (especially large file)

**Alternatives if `react-pdf` insufficient:**
- PDF.js (Mozilla's library, more control but more complex)
- Embed with `<iframe>` (simplest, least features)
- Server-side rendering to images (fallback for very large files)

**Success Criteria:**
- 300-page PDF loads in <5 seconds
- Smooth scrolling (no jank)
- Memory usage <500MB for large files
- Works on all target browsers

**Deliverables:**
- [ ] Performance benchmark report
- [ ] Recommendation: `react-pdf` vs. alternative
- [ ] Implementation plan for Story 5.3

---

### Action 3.2: EPUB Browser Rendering Strategy

**Status:** 🟡 PENDING (Story 5.3 Prep)
**Owner:** Frontend Team
**Effort:** 3-4 hours (research + prototype)
**Story:** 5.3 (Split-Screen Comparison UI)

**Description:**
Decide how to render EPUB files in the browser for before/after comparison.

**Options:**

**Option A: `react-reader` (EPUB Renderer)**
- **Pros:** Native EPUB rendering, TOC navigation
- **Cons:** May not match e-reader app rendering exactly
- **Complexity:** Medium (library integration)

**Option B: Convert EPUB → HTML on Backend**
- **Pros:** Full control over rendering, exact CSS match
- **Cons:** Extra backend work, storage for HTML previews
- **Complexity:** Medium-High (new backend service)

**Option C: Hybrid Approach**
- **Pros:** HTML preview for speed + download full EPUB
- **Cons:** Two rendering paths to maintain
- **Complexity:** High (both A and B)

**Evaluation Criteria:**
1. **Rendering Fidelity:** How close to actual e-reader appearance?
2. **Performance:** Load time for 300-page EPUB
3. **Feature Support:** TOC navigation, text reflow, font adjustment
4. **Development Effort:** Time to implement
5. **Maintenance:** Long-term complexity

**Prototype Plan:**
1. Implement Option A with `react-reader`
2. Test with Action 1.4 sample EPUBs
3. Compare rendering to Apple Books/Calibre
4. If fidelity insufficient, prototype Option B
5. Document decision with rationale

**Success Criteria:**
- EPUB renders in <3 seconds
- Visual fidelity acceptable (matches e-reader within 95%)
- TOC navigation functional
- Works on all target browsers

**Deliverables:**
- [ ] Prototype implementation (Option A or B)
- [ ] Rendering fidelity comparison report
- [ ] Decision document with recommendation
- [ ] Implementation plan for Story 5.3

---

### Action 3.3: Real-Time Updates Architecture Decision

**Status:** 🟡 PENDING (Story 5.1 Prep)
**Owner:** Backend + Frontend Teams
**Effort:** 2-3 hours (collaborative decision)
**Story:** 5.1 (Real-time Progress Updates)

**Description:**
Choose architecture for real-time job status updates: Polling, Server-Sent Events (SSE), or WebSockets.

**Options Comparison:**

| Factor | Polling | SSE | WebSockets |
|--------|---------|-----|------------|
| **Complexity** | Low | Medium | High |
| **Server Load** | High (frequent requests) | Low (persistent connection) | Low (persistent connection) |
| **Real-time** | ~5 second delay | Real-time | Real-time |
| **Browser Support** | Universal | Modern browsers | Modern browsers |
| **Serverless Friendly** | Yes | Limited | No (requires stateful server) |
| **Bi-directional** | No | No (server→client only) | Yes |
| **Epic 3 Pattern** | Used (5-second polling) | Not used | Not used |

**Recommendation (from Epic 3 Retrospective):**
Start with **Polling** for MVP simplicity, evaluate SSE for Epic 6 if needed.

**Rationale:**
- Polling proven in Epic 3 (History UI)
- Serverless-friendly (Vercel deployment)
- Lowest implementation complexity
- Acceptable latency for conversion jobs (5-15 minute duration)

**Implementation Plan (Polling):**

**Frontend:**
```typescript
// Poll every 2 seconds while job is PROCESSING
useEffect(() => {
  if (job.status === 'PROCESSING') {
    const interval = setInterval(() => {
      refetchJob();
    }, 2000);
    return () => clearInterval(interval);
  }
}, [job.status]);
```

**Backend:**
- No changes needed (existing `GET /jobs/{id}` endpoint)
- Quality report updates visible on each poll

**Migration Path to SSE (Future):**
1. Add SSE endpoint: `GET /jobs/{id}/stream`
2. Stream quality updates as they occur
3. Frontend upgrades to use EventSource API
4. Polling remains as fallback for older browsers

**Deliverables:**
- [ ] Architecture decision documented
- [ ] Polling implementation plan for Story 5.1
- [ ] Future SSE migration plan (Epic 6 consideration)

---

## Tracking and Completion

### Action Items by Status:

**🟢 Complete (3):**
- Action 2.1: Quality Report API ✅
- Action 2.2: EPUB Compatibility ✅
- Action 2.3: API Keys Configuration ✅

**🟡 Pending Before Epic 5 (5):**
- Action 1.1: Integration Test Suite (4-6 hours)
- Action 1.2: AI Cost Monitoring (2-3 hours, integrate in Story 5.1)
- Action 1.3: Pre-Flight Checklist (30 minutes, create now)
- Action 1.4: Sample PDFs (1-2 hours, before Story 5.2)
- Action 1.5: Quality Display Language (1-2 hours, before Story 5.2)

**🟡 Pending During Epic 5 (4):**
- Action 3.1: PDF Viewer Evaluation (Story 5.3 prep)
- Action 3.2: EPUB Rendering Strategy (Story 5.3 prep)
- Action 3.3: Real-Time Updates Decision (Story 5.1 prep)

**Total Estimated Effort Before Epic 5:** 10-15 hours
**Total Estimated Cost:** $50/month (integration test AI budget)

---

## References

- **Source Retrospective:** `docs/sprint-artifacts/epic-4-retrospective-2025-12-13.md`
- **Epic 3 Retrospective:** `docs/sprint-artifacts/epic-3-retrospective.md`
- **Epic 5 Preview:** `docs/epics.md` (Stories 5.1-5.4)
- **Architecture:** `docs/architecture.md` (ADR-001: API-First Intelligence)
- **PRD:** `docs/prd.md` (UX Principles: Transparency Through Feedback)

---

*Generated from Epic 4 Retrospective - 2025-12-13*
