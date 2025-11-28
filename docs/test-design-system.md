# System-Level Test Design - Transfer2Read

**Generated:** 2025-11-28  
**Test Architect:** Murat (Master Test Architect)  
**Project Phase:** Phase 3 - Solutioning Gate Review  
**Workflow:** testarch-test-design (System-Level Mode)

---

## Executive Summary

Transfer2Read's hybrid intelligence architecture (Next.js + FastAPI + Celery + PyTorch AI) presents a **complex, multi-layer testing challenge**. The system's core value proposition - 95%+ fidelity PDF→EPUB conversion - demands rigorous quality validation across UI, API, async workers, and AI pipelines.

**Overall Testability Assessment: PASS with CONCERNS**

- ✅ **Controllability**: Good - API seeding, factory patterns, dependency injection supported
- ⚠️ **Observability**: CONCERNS - AI model behavior needs instrumentation, job progress tracking critical
- ✅ **Reliability**: Good - Clean separation (frontend/backend/worker), stateless design

**Critical Recommendations:**
1. Add AI model instrumentation for layout detection confidence scores
2. Implement comprehensive job progress telemetry (Celery task states → Redis → API)
3. Design PDF test corpus with known-good/known-bad samples for AI validation  
4. Plan performance testing for 100 concurrent conversion jobs (Celery scaling)

---

## 1. Testability Assessment

### 1.1 Controllability

**Can we control system state for testing?**

#### ✅ PASS: Data Seeding \u0026 Factories

**Architecture Support:**
- PostgreSQL with Alembic migrations → Database reset per test suite
- S3-compatible storage (boto3) → Mockable with `moto` library
- FastAPI dependency injection → Easily overridden in tests
- Celery task queue → Can be mocked or run synchronously in tests

**Recommendation:**
```python
# backend/tests/conftest.py - Test DB fixture
@pytest.fixture(scope="function", autouse=True)
async def test_db():
    """Auto-reset database for each test (isolation)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# backend/tests/factories.py - Data factories
class UserFactory(factory.Factory):
    class Meta:
        model = User
    
    email = factory.Faker('email')
    tier = 'FREE'
    hashed_password = 'hashed_password123'

class PDFUploadFactory(factory.Factory):
    class Meta:
        model = ConversionJob
    
    user_id = factory.SubFactory(UserFactory)
    status = 'QUEUED'
    input_file_key = factory.Faker('file_path', extension='pdf')
```

#### ✅ PASS: External Dependencies Mockable

**Architecture Support:**
- S3 storage → boto3 mockable with `moto`:
  ```python
  @mock_s3
  def test_upload_pdf():
      # S3 fully mocked
  ```
- Redis queue → Can use FakeRedis for synchronous tests
- PyTorch AI model → Load mock weights or use deterministic test fixtures

**Recommendation:** Create test fixtures for AI model outputs:
```python
# backend/tests/fixtures/ai_mock_responses.py
MOCK_LAYOUT_DETECTION = {
    "page_1": [
        {"type": "text", "bbox": [10, 10, 200, 50], "content": "Chapter 1"},
        {" type": "table", "bbox": [10, 60, 400, 200], "rows": 5, "cols": 3}
    ]
}
```

#### ⚠️ CONCERNS: Error Condition Triggering

**Issue:** Triggering specific error scenarios (S3 failure, AI model crash, Celery timeout) requires coordination.

**Mitigation:**
- Add environment variable: `TEST_MODE=true` to enable fault injection endpoints
- Create admin-only API endpoints for chaos engineering:
  ```python
  @app.post("/api/test/inject-fault")
  async def inject_fault(fault_type: str):
      """Admin-only: Inject faults for testing (disabled in production)."""
      if not settings.TEST_MODE:
          raise HTTPException(403)
      
      if fault_type == "s3_failure":
          raise S3UploadError("Simulated S3 failure")
  ```

**Overall Controllability Score: PASS** ✅

---

### 1.2 Observability

**Can we inspect system state and validate NFRs?**

#### ✅ PASS: API Observability

**Architecture Support:**
- FastAPI OpenAPI schema → Auto-generated API client for tests
- Structured logging (recommended in architecture) → Parseable logs
- Health check endpoint (`/api/health`) → Service status validation

**Recommendation:**
```python
# backend/app/api/v1/health.py
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": {
            "database": await db.ping(),  # "UP" | "DOWN"
            "redis": await redis.ping(),
            "s3": await s3.check_bucket(),
            "worker": await celery.inspect().active_queues()
        }
    }
```

#### ⚠️ CONCERNS: AI Model Observability

**Issue:** PyTorch DocLayout-YOLO model runs in Celery worker - how do we validate detection quality?

**Risk:** Model fails silently (e.g., detects 0 tables when PDF has 5 tables) → 95% fidelity target missed.

**Mitigation Plan:**
1. **Add confidence scores to quality report:**
   ```python
   quality_report = {
       "detected_elements": {
           "tables": 3,
           "images": 2,
           "equations": 5
       },
       "confidence_scores": {
           "avg_table_confidence": 0.89,  # 0-1 scale
           "avg_text_confidence": 0.95,
           "low_confidence_pages": [12, 45]  # Flag for manual review
       }
   }
   ```

2. **Create test corpus with ground truth:**
   ```python
   # backend/tests/fixtures/pdf_test_corpus.py
   TEST_PDFS = {
       "simple_text.pdf": {
           "expected_tables": 0,
           "expected_images": 1,
           "expected_equations": 0,
           "fidelity_target": 0.99
       },
       "complex_math_book.pdf": {
           "expected_tables": 15,
           "expected_images": 8,
           "expected_equations": 47,
           "fidelity_target": 0.95
       }
   }
   ```

3. **Instrument worker with telemetry:**
   ```python
   # backend/app/worker.py
   @celery_app.task(bind=True)
   def convert_pdf(self, job_id: str):
       # Update progress telemetry
       self.update_state(state='ANALYZING', meta={'progress': 10})
       layout = analyze_layout(pdf_path)  # PyTorch
       
       self.update_state(state='EXTRACTING', meta={'progress': 40, 'detected': len(layout.elements)})
       # ... continue with telemetry updates
   ```

**Overall Observability Score: CONCERNS** ⚠️  
**Action Required:** Implement AI confidence scoring + test corpus before Sprint 0.

---

### 1.3 Reliability

**Are tests isolated, reproducible, and loosely coupled?**

#### ✅ PASS: Stateless Design

**Architecture Support:**
- Frontend: Next.js App Router → Stateless React components
- Backend: FastAPI async → No shared mutable state
- Worker: Celery tasks → Isolated jobs, no inter-task dependencies
- Storage: S3 object storage → Immutable files (no race conditions)

**Strengths:**
- Parallel test execution safe (no shared state)
- Test isolation natural (each test gets clean DB + mocked S3)
- No race conditions (S3 uses UUIDs, DB uses transactions)

#### ✅ PASS: Reproducible Failures

**Architecture Support:**
- Deterministic waits: Can use `waitForResponse()` in Playwright tests
- HAR capture: FastAPI + Playwright enable network replay
- Seed data: Factory pattern with `faker` library for controlled randomness

**Recommendation:**
```typescript
// frontend/tests/e2e/conversion-flow.spec.ts
test('user converts PDF to EPUB', async ({ page }) => {
    const testPdf = 'fixtures/sample-tech-book.pdf';
    
    // Network-first: Intercept BEFORE upload
    const uploadPromise = page.waitForResponse('**/api/v1/upload');
    const jobPromise = page.waitForResponse(resp => 
        resp.url().includes('/api/v1/jobs/') && resp.status() === 200
    );
    
    await page.goto('/upload');
    await page.setInputFiles('[data-testid="pdf-upload"]', testPdf);
    
    const uploadResp = await uploadPromise;
    const { job_id } = await uploadResp.json();
    
    // Deterministic wait for job completion (no hardcoded timeout)
    await jobPromise;
    
    await expect(page.getByText('Conversion Complete')).toBeVisible();
});
```

#### ✅ PASS: Loosely Coupled Components

**Architecture Support:**
- Frontend ↔ Backend: REST API (mockable with MSW)
- Backend ↔ Worker: Message queue (Celery can run sync in tests)
- Backend ↔ S3: Service layer (`services/storage/`) → Dependency injection

**Overall Reliability Score: PASS** ✅

---

## 2. Architecturally Significant Requirements (ASRs)

### ASR-1: 95%+ Fidelity for Complex PDFs (FR24)

**Category:** PERF (Performance Quality)  
**Probability:** 3 (Likely - AI detection errors common)  
**Impact:** 3 (Critical - Core value proposition)  
**Risk Score:** 9 (CRITICAL BLOCKER)

**Testability Challenge:**
- How do we automatically validate "95% fidelity" without manual inspection?

**Mitigation:**
1. **Ground truth test corpus** (10-20 PDFs with known element counts)
2. **Automated fidelity calculation:**
   ```python
   def calculate_fidelity(detected, expected):
       """
       Fidelity = (Correct detections) / (Total expected elements)
       Example: Detected 18/20 tables correctly → 90% fidelity
       """
       correct = sum(1 for d in detected if d in expected)
       return correct / len(expected) if expected else 1.0
   ```
3. **Performance test:** Process 100 test PDFs, assert `avg_fidelity >= 0.95`

**Test Approach:**
- **Level:** Integration (backend + worker + AI model)
- **Tool:** Pytest with real PyTorch model (CPU mode for speed)
- **Priority:** P0 (blocks release if failing)

---

### ASR-2: <2 Minute Conversion for 300-Page Book (FR35, NFR1)

**Category:** PERF (Performance SLO)  
**Probability:** 2 (Possible - depends on PyTorch optimization)  
**Impact:** 2 (Degraded UX if slower)  
**Risk Score:** 4 (MEDIUM)

**Testability Challenge:**
- Celery async processing → Need to measure end-to-end latency

**Mitigation:**
1. **Performance benchmark test:**
   ```python
   @pytest.mark.performance
   async def test_conversion_speed_300_pages():
       start = time.time()
       
       job_id = await upload_pdf('fixtures/300-page-book.pdf')
       await poll_job_status(job_id, timeout=120)  # 2 min max
       
       elapsed = time.time() - start
       assert elapsed < 120, f"Conversion took {elapsed}s (target: <120s)"
   ```

2. **Profiling:**
   - Measure AI inference time per page: Target ~100ms/page CPU, ~28ms/page GPU
   - Measure EPUB generation time: Target <10s for 300 pages
   - Identify bottlenecks (I/O, CPU, AI model)

**Test Approach:**
- **Level:** E2E (API → Worker → S3)
- **Tool:** Pytest + `time` profiling
- **Priority:** P1 (user satisfaction, not blocker)

---

### ASR-3: Multi-Language Font Embedding (FR21, FR22)

**Category:** TECH (Technical Correctness)  
**Probability:** 2 (Possible - font edge cases)  
**Impact:** 2 (Degraded readability)  
**Risk Score:** 4 (MEDIUM)

**Testability Challenge:**
- How do we validate "no missing glyphs" in generated EPUB?

**Mitigation:**
1. **Test corpus with mixed languages:**
   - `chinese_english_mixed.pdf`
   - `japanese_tech_manual.pdf`
   - `korean_math_textbook.pdf`

2. **Glyph validation:**
   ```python
   def validate_epub_fonts(epub_path):
       """Extract EPUB and check embedded fonts."""
       with ZipFile(epub_path) as epub:
           fonts = [ for f in epub.namelist() if f.endswith(('.ttf', '.otf'))]
           assert len(fonts) > 0, "No fonts embedded"
           
           # Verify CJK font present for non-EN content
           if has_cjk_characters(epub):
               assert any('Noto' in f or 'CJK' in f for f in fonts), \
                   "Missing CJK font for Chinese/Japanese/Korean text"
   ```

**Test Approach:**
- **Level:** Integration (backend + EPUB generation)
- **Tool:** Pytest + `ebooklib` library
- **Priority:** P1 (affects specific user segments)

---

### ASR-4: 99.5% Uptime (NFR8)

**Category:** OPS (Operational Reliability)  
**Probability:** 2 (Possible - deployment issues)  
**Impact:** 2 (Degraded availability)  
**Risk Score:** 4 (MEDIUM)

**Testability Challenge:**
- Can't test "99.5% uptime" in pre-production

**Mitigation:**
1. **Health check validation:**
   ```typescript
   // frontend/tests/e2e/health.spec.ts
   test('health endpoint returns service status', async ({ request }) => {
       const resp = await request.get('/api/health');
       expect(resp.status()).toBe(200);
       
       const health = await resp.json();
       expect(health.services.database.status).toBe('UP');
       expect(health.services.redis.status).toBe('UP');
       expect(health.services.worker).toBeDefined();
   });
   ```

2. **Synthetic monitoring (post-launch):**
   - Pingdom/UptimeRobot checks every 1 minute
   - Alert if health check fails 3 consecutive times

**Test Approach:**
- **Level:** E2E (health endpoint validation)
- **Tool:** Playwright API testing
- **Priority:** P2 (operational maturity, not MVP blocker)

---

## 3. Test Levels Strategy

Based on Transfer2Read's hybrid architecture, I recommend this test distribution:

### 3.1 Recommended Test Pyramid

```
        E2E (20%)
       🔺 Critical user journeys
      /   \  - Upload PDF → Convert → Download EPUB
     /     \  - Account creation → Tier management
    /       \
   /__________\  Integration (40%)
  /           \  - API contract tests (FastAPI)
 /             \  - Worker task tests (Celery)
/______________\  - AI pipeline tests (PyTorch)
 
   Unit (40%)
   - Business logic (conversion heuristics)
   - Utility functions (PDF validation, EPUB generation)
   - Error handling (retries, fallbacks)
```

**Rationale:**
- **40% Unit:** Fast feedback on business logic (conversion algorithms, validation)
- **40% Integration:** Validate critical system boundaries (API, worker, AI)
- **20% E2E:** Cover core user journeys (upload → convert → download)

**This is NOT the typical 70/20/10 pyramid** because Transfer2Read's value is in **system integration** (AI + async processing), not just business logic.

---

### 3.2 Test Level Assignments

| Component | Test Level | Rationale |
|-----------|------------|-----------|
| **Frontend UI Components** | Component Tests (Playwright CT) | Isolated UI behavior (shadcn/ui components) |
| **Frontend User Flows** | E2E (Playwright) | Critical paths: upload, conversion progress, download |
| **Backend API Endpoints** | Integration (Pytest + TestClient) | Contract validation, auth, file upload |
| **Celery Conversion Pipeline** | Integration (Pytest + Celery eager mode) | AI processing, EPUB generation, S3 upload |
| **PyTorch AI Model** | Integration (Pytest + real model) | Layout detection accuracy, confidence scoring |
| **Business Logic** | Unit (Pytest) | PDF validation, TOC generation heuristics |
| **EPUB Generation** | Integration (Pytest + `ebooklib`) | Valid EPUB structure, font embedding |
| **S3 Storage Service** | Unit (Pytest + `moto`) | Upload, download, presigned URL generation |

---

## 4. NFR Testing Approach

### 4.1 Security (SEC)

**Tools:** Playwright (E2E auth/authz) + npm audit (CI) + OWASP ZAP (optional)

**Critical Tests:**
1. **Auth/Authz Validation:**
   ```typescript
   test('unauthenticated users cannot access protected routes', async ({ page }) => {
       await page.goto('/dashboard');
       await expect(page).toHaveURL(/\/login/);
   });
   
   test('free tier users cannot upload 100MB file', async ({ page, request }) => {
       // Login as FREE tier user
       await page.goto('/upload');
       const largePDF = 'fixtures/100mb-file.pdf';
       
       await page.setInputFiles('[data-testid="pdf-upload"]', largePDF);
       await expect(page.getByText('File size exceeds Free tier limit (50MB)')).toBeVisible();
   });
   ```

2. **Secret Handling:**
   ```python
   # backend/tests/test_security.py
   async def test_passwords_not_logged():
       """Ensure passwords never appear in logs or responses."""
       with patch('app.core.logging.logger') as mock_logger:
           response = await client.post('/auth/login', json={
               'email': 'test@example.com',
               'password': 'SecretPass123!'
           })
           
           # Check logs don't contain password
           for call in mock_logger.info.call_args_list:
               assert 'SecretPass123!' not in str(call)
   ```

**NFR Criteria:**
- ✅ PASS: All auth/authz tests green, no secrets in logs
- ⚠️ CONCERNS: Missing OWASP ZAP scan (optional for MVP)
- ❌ FAIL: Auth bypass possible or passwords logged

---

### 4.2 Performance (PERF)

**Tools:** k6 (load testing) + Playwright (Core Web Vitals)

**Critical Tests:**
1. **Load Testing (k6):**
   ```javascript
   // tests/nfr/performance.k6.js
   export const options = {
       stages: [
           { duration: '2m', target: 50 },  // Ramp to 50 concurrent users
           { duration: '5m', target: 50 },  // Sustain 50 users
           { duration: '2m', target: 100 }, // Spike to 100 users
           { duration: '3m', target: 100 },
       ],
       thresholds: {
           http_req_duration: ['p(95)<500'],  // 95% of requests < 500ms
           http_req_failed: ['rate<0.01'],    // Error rate < 1%
       }
   };
   
   export default function() {
       // Test API performance under load
       http.get(`${__ENV.BASE_URL}/api/jobs`);
       sleep(1);
   }
   ```

2. **Conversion Performance:**
   ```python
   @pytest.mark.performance
   async def test_concurrent_conversions():
       """Validate system handles 10 concurrent conversion jobs."""
       job_ids = []
       
       # Submit 10 jobs simultaneously
       async with asyncio.TaskGroup() as group:
           for i in range(10):
               task = group.create_task(
                   upload_and_convert(f'fixtures/test-{i}.pdf')
               )
               job_ids.append(task)
       
       # All jobs should complete within 5 minutes
       await asyncio.wait_for(
           poll_all_jobs(job_ids),
           timeout=300
       )
   ```

**NFR Criteria:**
- ✅ PASS: p95 < 500ms, handles 100 concurrent users, <2min per 300-page conversion
- ⚠️ CONCERNS: Approaching limits (p95 = 480ms) or insufficient load testing
- ❌ FAIL: SLO breached (p95 > 500ms) or job queue crashes under load

---

### 4.3 Reliability (Reliability)

**Tools:** Playwright (E2E error handling) + Pytest (API retry logic)

**Critical Tests:**
1. **Graceful Degradation:**
   ```typescript
   test('app handles S3 failure gracefully', async ({ page, context }) => {
       // Mock S3 failure
       await context.route('**/api/v1/upload', route => {
           route.fulfill({ status: 500, body: JSON.stringify({ error: 'S3 Upload Failed' }) });
       });
       
       await page.goto('/upload');
       await page.setInputFiles('[data-testid="pdf-upload"]', 'fixtures/sample.pdf');
       
       // User sees error message (not crash)
       await expect(page.getByText('Upload failed. Please try again.')).toBeVisible();
       await expect(page.getByRole('button', { name: 'Retry' })).toBeVisible();
   });
   ```

2. **Celery Retry Logic:**
   ```python
   async def test_worker_retries_on_transient_failure():
       """Worker retries 3 times before marking job as FAILED."""
       with patch('app.services.ai.analyze_layout') as mock_ai:
           # Fail twice, succeed on 3rd attempt
           mock_ai.side_effect = [
               Exception("Transient error"),
               Exception("Transient error"),
               { "tables": 3, "images": 2 }  # Success
           ]
           
           job_id = await submit_conversion_job('fixtures/test.pdf')
           await poll_job_status(job_id, expected_status='COMPLETED')
           
           assert mock_ai.call_count == 3  # Retried twice
   ```

**NFR Criteria:**
- ✅ PASS: Error handling, retries, health checks validated
- ⚠️ CONCERNS: Partial coverage or missing telemetry
- ❌ FAIL: No recovery path (500 error crashes app)

---

### 4.4 Maintainability (Maintainability)

**Tools:** GitHub Actions (coverage, audit) + Playwright (observability validation)

**Critical Checks:**
1. **Test Coverage (CI):**
   ```yaml
   # .github/workflows/test-coverage.yml
   - name: Run tests with coverage
     run: pytest --cov=app --cov-report=json
   
   - name: Check coverage threshold
     run: |
       COVERAGE=$(jq '.totals.percent_covered' coverage.json)
       if (( $(echo "$COVERAGE < 80" | bc -l) )); then
         echo "❌ Coverage $COVERAGE% below 80%"
         exit 1
       fi
   ```

2. **Vulnerability Scan (CI):**
   ```yaml
   - name: Run npm audit
     run: npm audit --audit-level=high
   
   - name: Run pip-audit
     run: pip-audit --require-hashes
   ```

**NFR Criteria:**
- ✅ PASS: >=80% coverage, <5% duplication, no critical vulnerabilities
- ⚠️ CONCERNS: Coverage 60-79% or unclear ownership
- ❌ FAIL: <60% coverage or critical vulnerabilities

---

## 5. Test Environment Requirements

### 5.1 Local Development

**Requirements:**
- Docker Desktop 4.x+ (PostgreSQL 17 + Redis 8 containers)
- Node.js 24.12.0 LTS
- Python 3.13.0
- 8GB RAM minimum (PyTorch model requires 2-4GB)

**Setup:**
```bash
# Start all services via Docker Compose
docker-compose up -d  # DB, Redis, S3 (LocalStack or MinIO)

# Backend tests
cd backend
pytest tests/

# Frontend tests
cd frontend
npm run test  # Vitest unit/component tests
npx playwright test  # E2E tests
```

---

### 5.2 CI Environment

**Recommended:** GitHub Actions with matrix strategy

```yaml
# .github/workflows/ci.yml
jobs:
  backend-tests:
    strategy:
      matrix:
        python-version: [3.11, 3.12, 3.13]
    steps:
      - uses: actions/setup-python@v4
      - run: pytest tests/ --cov=app

  frontend-tests:
    strategy:
      matrix:
        node-version: [22, 24]
    steps:
      - uses: actions/setup-node@v4
      - run: npm test
      - run: npx playwright test --shard=${{ matrix.shard }}/4

  e2e-tests:
    needs: [backend-tests, frontend-tests]
    steps:
      - run: docker-compose up -d
      - run: npx playwright test tests/e2e/
```

---

### 5.3 Staging Environment

**Purpose:** Pre-production validation before deploying to production

**Requirements:**
- Railway deployment (backend + worker + PostgreSQL + Redis)
- Vercel deployment (frontend)
- AWS S3 bucket (real storage, not mocked)
- Playwright E2E tests run against staging URL

**Smoke Tests:**
```typescript
// tests/e2e/smoke-staging.spec.ts
test.use({ baseURL: 'https://staging.transfer2read.com' });

test('staging smoke test: upload and convert', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Transfer2Read' })).toBeVisible();
    
    // Critical path validation
    await page.goto('/upload');
    await page.setInputFiles('[data-testid="pdf-upload"]', 'fixtures/sample-10-pages.pdf');
    
    await expect(page.getByText('Upload successful')).toBeVisible({ timeout: 30000 });
});
```

---

## 6. Testability Concerns

### ⚠️ CONCERN #1: AI Model Non-Determinism

**Issue:** PyTorch DocLayout-YOLO may produce different detection results across runs (model stochasticity).

**Impact:** Flaky tests if we assert exact element counts.

**Mitigation:**
1. **Use confidence score ranges instead of exact counts:**
   ```python
   # Instead of: assert detected_tables == 5
   assert 4 <= detected_tables <= 6, "Table detection variance acceptable"
   assert avg_table_confidence >= 0.85, "Confidence threshold met"
   ```

2. **Freeze model weights for tests:**
   - Use fixed pre-trained weights (no fine-tuning in tests)
   - Set `torch.manual_seed(42)` for reproducibility

**Owner:** Backend team  
**Deadline:** Before Sprint 0 (test infrastructure)  
**Status:** OPEN

---

### ⚠️ CONCERN #2: Celery Worker Isolation in Tests

**Issue:** Running Celery workers in test mode requires coordination (async tasks vs synchronous tests).

**Impact:** Slow tests if we wait for real async job completion.

**Mitigation:**
1. **Use Celery eager mode for unit/integration tests:**
   ```python
   # backend/tests/conftest.py
   @pytest.fixture(autouse=True)
   def celery_eager_mode():
       celery_app.conf.task_always_eager = True  # Run tasks synchronously
       yield
       celery_app.conf.task_always_eager = False
   ```

2. **Use real async workers for E2E tests:**
   - Spin up temporary worker in CI: `celery -A app.worker worker --loglevel=info &`
   - Poll job status with timeout: `await poll_job(job_id, timeout=120)`

**Owner:** Backend team  
**Deadline:** Before Epic 4 (Conversion Engine)  
**Status:** OPEN

---

### ⚠️ CONCERN #3: PDF Test Corpus Coverage

**Issue:** Testing "95% fidelity" requires diverse PDF samples (simple text, complex tables, equations, multi-language).

**Impact:** False confidence if we only test simple PDFs.

**Mitigation:**
1. **Curate 20-PDF test corpus:**
   - 5 simple text-based PDFs (target: 99% fidelity)
   - 5 complex technical books with tables (target: 95% fidelity)
   - 5 math/science books with equations (target: 95% fidelity)
   - 5 multi-language documents (EN+ZH+JP+KO) (target: 90% fidelity)

2. **Store corpus in `backend/tests/fixtures/pdf_test_corpus/`**

3. **Ground truth JSON:**
   ```json
   {
       "complex_math_book.pdf": {
           "pages": 342,
           "expected_elements": {
               "tables": 18,
               "images": 12,
               "equations": 156,
               "chapters": 12
           },
           "fidelity_target": 0.95
       }
   }
   ```

**Owner:** QA/Test Architect  
**Deadline:** Before Epic 4 (Conversion Engine)  
**Status:** OPEN

---

## 7. Recommendations for Sprint 0

Before starting implementation (Epics 2-6), complete these foundational test setup tasks:

### Sprint 0 Checklist

- [ ] **Install test frameworks:**
  - Backend: pytest, pytest-asyncio, pytest-cov, httpx (AsyncClient)
  - Frontend: Vitest, Playwright, @testing-library/react
  - Performance: k6

- [ ] **Configure CI pipeline:**
  - GitHub Actions workflows (test coverage, lint, audit)
  - Parallel test execution (Playwright sharding: `--shard=1/4`)
  - Coverage reporting (upload to Codecov or similar)

- [ ] **Create test fixtures:**
  - User factory (email, tier, hashed_password)
  - PDF upload factory (S3 key, status, created_at)
  - Conversion job factory (user_id, input/output keys)

- [ ] **Set up test databases:**
  - PostgreSQL test DB with auto-reset (transaction rollback)
  - Redis FakeRedis for queue mocking
  - S3 mock with `moto` library

- [ ] **Create PDF test corpus:**
  - 20 diverse PDFs with ground truth metadata
  - Store in `backend/tests/fixtures/pdf_test_corpus/`

- [ ] **Implement observability hooks:**
  - AI confidence scoring in quality reports
  - Job progress telemetry (Celery → Redis → API)
  - Health check endpoint (`/api/health`)

- [ ] **Write first smoke tests:**
  - Backend: `test_create_user_api()`
  - Frontend: `test_login_flow()`
  - E2E: `test_upload_pdf_successful()`

**Estimated Sprint 0 Effort:** 3-5 days  
**Owner:** Test Architect + Backend Lead + Frontend Lead

---

## 8. Quality Gate Criteria

Before proceeding from Phase 3 (Solutioning) → Phase 4 (Implementation), validate:

### Gate Criteria for Implementation Readiness

- [x] **Testability Review Complete:** This document finalized ✅
- [ ] **Sprint 0 Checklist Complete:** Test infrastructure ready
- [ ] **Test Corpus Ready:** 20 PDFs with ground truth
- [ ] **CI Pipeline Configured:** GitHub Actions workflows operational
- [ ] **Concerns Mitigated:** AI model instrumentation planned, worker isolation strategy defined
- [ ] **NFR Approach Validated:** Security, performance, reliability test strategies documented

**Current Gate Status: CONCERNS** ⚠️

**Action Required Before Phase 4:**
1. Complete Sprint 0 test infrastructure setup
2. Mitigate testability concerns (AI instrumentation, PDF corpus)
3. Validate pilot integration test (upload PDF → detect layout → generate EPUB)

**Recommended Timeline:**
- Sprint 0 (test setup): 1 week
- Epic 1 (Foundation): 2 weeks
- Then proceed to Epic 2-6 implementation

---

## 9. Summary

**Transfer2Read's architecture is well-designed for testability**, with clear separation of concerns (Next.js ↔ FastAPI ↔ Celery), dependency injection support, and mockable external services.

**Critical Success Factors:**
1. ✅ **Controllability:** API seeding, factory patterns, dependency injection
2. ⚠️ **Observability:** Needs AI confidence scoring + telemetry
3. ✅ **Reliability:** Stateless design, transaction isolation, reproducible tests

**High-Priority Risks to Mitigate:**
- **ASR-1 (95% fidelity):** Create test corpus with ground truth, automated fidelity scoring
- **Concern #1 (AI non-determinism):** Use confidence ranges, freeze model weights
- **Concern #3 (PDF corpus coverage):** Curate 20 diverse PDFs before Epic 4

**Recommended Test Strategy:**
- 40% Unit + 40% Integration + 20% E2E (NOT the standard pyramid due to system integration focus)
- k6 for load testing (performance NFR)
- Playwright for E2E (critical user journeys)
- Pytest for backend/worker integration

**Next Steps:**
1. Review this test design with the team
2. Complete Sprint 0 setup (test infrastructure, CI, fixtures)
3. Implement pilot integration test to validate approach
4. Proceed to Epic 1 (Foundation) implementation

---

**Test Architect Sign-Off:** Murat (Master Test Architect)  
**Generated:** 2025-11-28  
**Last Updated:** 2025-11-28  
**Status:** Ready for Review ✅
