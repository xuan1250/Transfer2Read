# Architectural Decision: Performance Target Revision

**Decision Date:** 2025-12-01
**Decision By:** Product (xavier) + Architect (winston)
**Status:** ✅ APPROVED
**Related:** Implementation Readiness Report - CONCERN #1

---

## Context

**Original Requirement (PRD NFR1):**
- "300-page PDF in <2 minutes"

**Architectural Reality (ADR-001: API-First Intelligence):**
- GPT-4o API latency: 2-5 seconds per page
- Sequential processing: 300 pages × 3s avg = ~15 minutes
- Parallel processing (10x): 300 pages ÷ 10 × 3s = ~1.5 minutes (but higher costs)

**Gap Identified:**
- 2.5x-7.5x mismatch between PRD requirement and architectural estimates
- Risk of unmet user expectations if marketed as "<2 minutes"

---

## Decision

**Selected Option: B - Revise PRD Target (Realistic Expectations)**

### Revised Performance Targets

**Primary Target (NFR1 Updated):**
- **Complex PDFs (300 pages with tables/equations/images): <5 minutes**

**Tiered Targets for Clarity:**
- Simple PDFs (<100 pages, text-only): **<2 minutes**
- Complex PDFs (tables, equations, images): **<5 minutes**
- Very large PDFs (500+ pages): **<10 minutes**

### Marketing Message
- "Convert complex PDFs in **minutes, not hours**"
- "95%+ fidelity + speed you can trust"
- Emphasis on quality over raw speed

---

## Rationale

**Why Option B (Revise Target):**

1. **Aligns with Architecture**
   - API-based approach has inherent latency
   - 5-minute target achievable with current design (sequential processing)
   - No complex parallelization needed for MVP

2. **Still Competitive**
   - Most converters: 10-20+ minutes OR fail entirely on complex PDFs
   - 5 minutes with 95%+ fidelity is significantly better than alternatives
   - Quality differentiation more valuable than speed differentiation

3. **Cost-Effective**
   - Avoids excessive API costs from aggressive parallelization
   - Freemium model sustainable with sequential processing
   - Can optimize costs before pursuing speed optimization

4. **Quality-First for MVP**
   - Prioritizes core value proposition (95%+ fidelity)
   - Speed optimization can be post-MVP enhancement
   - Early adopters value quality over speed

5. **Optimization Path Preserved**
   - Can pursue 2-minute target in post-MVP with Option A (parallel processing)
   - Measure actual performance during Epic 4 implementation
   - Data-driven decision on whether to invest in speed optimization

**Why Not Option A (Parallel Processing):**
- Higher complexity (async coordination, retry logic)
- Higher API costs (10x concurrent calls)
- Rate limit risk with OpenAI (10,000 TPM tier)
- Can revisit post-MVP if demand warrants investment

**Why Not Option C (Page Sampling):**
- Sacrifices fidelity (98% vs. 99%)
- Added complexity (sampling logic, heuristics)
- Conflicts with core value proposition (95%+ fidelity)

---

## Implementation Actions

### 1. Update PRD (docs/prd.md)

**NFR1 - REVISED:**
```markdown
## NFR1: Conversion Performance

**Target:** Complex PDFs (300 pages with tables, equations, images) must convert in <5 minutes.

**Tiered Performance Targets:**
- Simple PDFs (<100 pages, text-only): <2 minutes
- Complex PDFs (300 pages, tables/equations/images): <5 minutes
- Very large PDFs (500+ pages): <10 minutes

**Rationale:** API-based AI processing (GPT-4o) provides state-of-the-art quality (95%+ fidelity) with realistic latency. 5 minutes for complex documents is significantly faster than competitors (10-20+ minutes or failure). Quality over raw speed for MVP.

**Post-MVP:** Explore parallel processing optimization to approach 2-minute target.
```

**FR35 - REVISED:**
```markdown
## FR35: Real-Time Processing

Users should see conversion complete within **5 minutes** for 300-page complex PDFs.

**Acceptance Criteria:**
- 90th percentile conversion time: <5 minutes for 300-page complex PDFs
- 90th percentile conversion time: <2 minutes for 100-page simple PDFs
- Progress updates every 10 seconds during conversion
- Estimated time remaining displayed after 25% completion
```

### 2. Update Architecture (docs/architecture.md)

**Add to "Conversion Pipeline Architecture" section:**

```markdown
### Performance Targets (Updated 2025-12-01)

**Decision:** Revised from original <2 min target to <5 min for complex PDFs (ADR-001 Supplement)

**Rationale:** API-First Intelligence (GPT-4o) prioritizes quality (95%+ fidelity) over raw speed. 5-minute target aligns with API latency reality while maintaining competitive advantage.

**Tiered Performance:**
- Simple (text-only, <100 pages): ~1-2 minutes
- Complex (tables/equations/images, 300 pages): ~3-5 minutes
- Very large (500+ pages): ~7-10 minutes

**Implementation Strategy:**
- Sequential page processing for MVP (cost-effective)
- Per-page telemetry to measure actual performance
- Post-MVP: Evaluate parallel processing if <3 min target needed

**Competitive Positioning:**
- Transfer2Read: 5 min + 95%+ fidelity
- Competitors: 10-20 min + 70% fidelity (or failure)
- Differentiation: Quality + reasonable speed, not raw speed
```

### 3. Update Story 4.1 Acceptance Criteria (docs/epics.md)

**Story 4.1: Conversion Pipeline Orchestrator - ADD:**

```markdown
**Performance Requirements (Decision 2025-12-01):**
- [ ] Timeout configuration: 10-minute hard limit (2x target)
- [ ] Performance metrics logging:
  - Record conversion start/complete timestamps
  - Log per-page processing time (AI analysis + EPUB generation)
  - Track API latency (GPT-4o response time per request)
  - Store in `quality_report.performance` JSONB field
- [ ] Performance classification:
  - Tag job as "simple" (<100 pages, no images/tables) or "complex"
  - Calculate pages_per_minute metric
  - Flag if conversion time exceeds target (alert for optimization)
```

### 4. Update Story 4.2 Acceptance Criteria (docs/epics.md)

**Story 4.2: LangChain AI Layout Analysis - REVISE:**

**OLD:**
```
Performance: 300-page PDF in ~5-15 minutes (API latency), parallel processing
```

**NEW:**
```markdown
**Performance Targets (Decision 2025-12-01):**
- [ ] Simple PDFs (<100 pages, text-only): <2 minutes (target: ~60 pages/min)
- [ ] Complex PDFs (300 pages, tables/equations/images): <5 minutes (target: ~60 pages/min)
- [ ] Very large PDFs (500+ pages): <10 minutes (target: ~50 pages/min)
- [ ] Measure and log actual conversion times per PDF complexity
- [ ] 90th percentile must not exceed targets + 20% buffer

**Performance Measurement:**
- [ ] Record `conversion_duration_seconds` in quality_report JSONB
- [ ] Calculate `pages_per_minute` metric: (page_count / duration) × 60
- [ ] Tag job complexity: "simple" | "complex" | "large"
- [ ] Log API latency per page (GPT-4o response time)
- [ ] Alert if job exceeds 6 minutes (20% over target) for future optimization
```

---

## Success Metrics

**During Epic 4 Implementation:**
- Measure actual conversion times on test corpus (20 PDFs)
- Calculate average time by complexity (simple/complex/large)
- Validate 90th percentile <5 min for complex PDFs

**Post-Launch Monitoring:**
- Track conversion time percentiles (p50, p90, p99)
- Monitor user feedback: Is 5 minutes acceptable?
- Identify optimization opportunities if consistently <3 min (over-engineered)

**Post-MVP Decision Point:**
- If user demand for faster conversions, invest in parallel processing (Option A)
- If <3 minutes consistently, tighten target to <3 min
- If approaching 5-min limit, investigate optimization (parallel, Claude for simple pages)

---

## Communication Plan

**Internal (Team):**
- Update PRD, Architecture, Epics docs before Epic 4 Sprint Planning (Week 8)
- Communicate to backend team: Performance targets are realistic, not aspirational
- Test Design: Add performance benchmarking to Sprint 0 or Epic 4

**External (Users/Marketing):**
- Marketing message: "Minutes, not hours" (avoid specific time claims)
- Product page: "Convert 300-page technical books in ~5 minutes"
- Emphasize quality differentiation (95%+ fidelity) over speed
- User expectation: "Fast enough + perfect quality" not "fastest possible"

---

## Review and Approval

**Reviewed By:**
- ✅ Product (xavier) - Approved 2025-12-01
- ✅ Architect (winston) - Approved 2025-12-01

**Next Review:** After Epic 4 completion (measure actual performance vs. targets)

**Revision History:**
- 2025-12-01: Initial decision (Option B selected)

---

**Related Documents:**
- Implementation Readiness Report: CONCERN #1 (resolved)
- PRD: NFR1, FR35 (to be updated)
- Architecture: ADR-001 Supplement (performance targets)
- Epics: Story 4.1, Story 4.2 (acceptance criteria updates)

**Decision Type:** Architectural (impacts technical implementation + product requirements)
**Impact Level:** HIGH (affects core NFR and user expectations)
**Status:** APPROVED - Ready for implementation in Week 8
