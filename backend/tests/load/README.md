# Load Testing Guide

This directory contains load testing infrastructure for the Transfer2Read PDF to EPUB conversion system.

## Overview

Load tests validate that the system meets performance targets under various load conditions:

- **Performance Baseline**: Single-user performance for simple and complex PDFs
- **Concurrent Load**: 10-50 concurrent users performing conversions
- **API Performance**: Response time validation (P95 < 500ms, P99 < 1s)
- **Database Performance**: Supabase PostgreSQL and Redis under load
- **Storage Performance**: Supabase Storage upload/download speeds

## Prerequisites

1. **Install Locust**:
   ```bash
   pip install locust
   ```

2. **Start Docker Compose stack**:
   ```bash
   docker-compose up -d
   ```

3. **Verify services are running**:
   ```bash
   docker-compose ps
   curl http://localhost:8000/api/health
   ```

4. **Prepare test PDFs** (see Test Data section below)

## Running Load Tests

### Quick Start

```bash
# Navigate to backend directory
cd backend

# Run baseline test (1 user, 5 minutes)
locust -f tests/load/scenarios.py --users 1 --spawn-rate 1 --run-time 5m --host http://localhost:8000 --headless

# Run normal load test (10 users, 10 minutes)
locust -f tests/load/scenarios.py --users 10 --spawn-rate 1 --run-time 10m --host http://localhost:8000 --headless

# Run stress test (50 users, 15 minutes)
locust -f tests/load/scenarios.py --users 50 --spawn-rate 5 --run-time 15m --host http://localhost:8000 --headless
```

### Web UI Mode

For interactive monitoring with charts and real-time statistics:

```bash
# Start Locust web UI
locust -f tests/load/scenarios.py --web-host 0.0.0.0 --host http://localhost:8000

# Open browser to http://localhost:8089
# Configure users, spawn rate, and start test from UI
```

### Test Scenarios

The load testing suite includes two user types:

1. **ConversionUser**: Simulates realistic user behavior with PDF uploads and conversions
   - Tasks: Health check, simple PDF upload, complex PDF upload, job polling, downloads
   - Weights: Health check (3x), simple PDF (2x), complex PDF (1x)

2. **ApiPerformanceUser**: Tests API endpoint performance without AI processing
   - Tasks: Health check, job status queries
   - Used for validating response time targets (P95 < 500ms, P99 < 1s)

## Test Data

### Required Test PDFs

Place the following test PDFs in `tests/fixtures/load-test-pdfs/`:

1. **simple-text.pdf** (10-20 pages, text-only)
   - Performance target: < 30 seconds end-to-end
   - EPUB size target: ≤ 120% of PDF size

2. **complex-technical.pdf** (300 pages, tables/images/equations)
   - Performance target: < 2 minutes
   - AI cost target: < $1.00 per job
   - Quality confidence score target: ≥ 90%

3. **multi-language.pdf** (optional, for compatibility testing)

4. **large-file.pdf** (optional, >50MB for storage performance)

5. **edge-case.pdf** (optional, corrupted or unusual layout)

### Creating Test PDFs

If you don't have test PDFs, you can:

1. **Use sample PDFs from the internet** (ensure copyright compliance)
2. **Generate synthetic PDFs** using Python libraries:
   ```python
   from reportlab.lib.pagesizes import letter
   from reportlab.pdfgen import canvas

   def create_simple_pdf(filename, num_pages=15):
       c = canvas.Canvas(filename, pagesize=letter)
       for i in range(num_pages):
           c.drawString(100, 750, f"Page {i+1}")
           c.drawString(100, 700, "This is a simple text PDF for load testing.")
           c.showPage()
       c.save()

   create_simple_pdf("tests/fixtures/load-test-pdfs/simple-text.pdf")
   ```

## Performance Targets

From PRD (Non-Functional Requirements):

| Metric | Target |
|--------|--------|
| Simple PDF conversion (10-20 pages) | < 30 seconds end-to-end |
| Complex PDF conversion (300 pages) | < 2 minutes |
| AI cost per job | < $1.00 |
| EPUB file size | ≤ 120% of PDF size |
| API response time (P95) | < 500ms |
| API response time (P99) | < 1s |
| Frontend landing page | < 2s |
| Frontend dashboard | < 3s |
| Frontend job status page | < 3s |
| Celery queue depth (max) | < 100 jobs |
| Docker CPU/memory usage | < 80% of host capacity |

## Monitoring During Tests

### Docker Container Metrics

Monitor resource usage in a separate terminal:

```bash
# Real-time stats
docker stats

# Specific containers
docker stats backend-api backend-worker redis
```

Watch for:
- CPU usage > 80%
- Memory usage > 80%
- Network I/O patterns

### Celery Worker Queue Depth

```bash
# Connect to Redis and monitor queue
docker exec -it redis redis-cli

# In Redis CLI
> LLEN celery

# Monitor in real-time (refresh every 2 seconds)
> watch -n 2 "docker exec redis redis-cli LLEN celery"
```

### Database Performance

Monitor Supabase dashboard during tests:
- Query response times
- Connection pool usage
- RLS policy overhead

### Locust Metrics

Locust automatically tracks:
- Total requests
- Failures
- Response times (avg, min, max, percentiles)
- Requests per second (RPS)
- Active users

## Generating Load Test Reports

After running tests, generate a comprehensive report:

```bash
# Locust can export data to CSV
locust -f tests/load/scenarios.py --users 10 --run-time 10m --host http://localhost:8000 --csv=load-test-results --headless

# This creates:
# - load-test-results_stats.csv (aggregated stats)
# - load-test-results_stats_history.csv (time-series data)
# - load-test-results_failures.csv (failure log)
```

Create a final report in `docs/sprint-artifacts/load-test-report-{date}.md` with:
- Test scenarios and configuration
- Performance metrics vs. targets
- Graphs (response time distribution, throughput, error rate)
- Resource utilization patterns
- Bottleneck analysis and recommendations

## Troubleshooting

### Test PDFs Not Found

```
Warning: Test PDF not found at tests/fixtures/load-test-pdfs/simple-text.pdf
```

**Solution**: Ensure test PDFs are placed in the correct directory.

### Connection Refused

```
ConnectionError: HTTPConnectionPool(host='localhost', port=8000)
```

**Solution**: Verify Docker Compose stack is running:
```bash
docker-compose ps
docker-compose logs backend-api
```

### High Failure Rate

If tests show high failure rates:

1. Check backend logs: `docker-compose logs backend-api`
2. Check worker logs: `docker-compose logs backend-worker`
3. Verify Supabase credentials in `.env`
4. Check Redis connectivity: `docker exec redis redis-cli ping`

### Rate Limiting

If you hit OpenAI or Anthropic rate limits:

1. Monitor LangChain callbacks for rate limit headers
2. Reduce concurrent users or test duration
3. Implement backoff/retry logic (if not already present)
4. Consider upgrading AI API tier

## Cost Management

**AI API Costs**:
- Budget $20-50 for comprehensive load testing
- Monitor costs in OpenAI and Anthropic dashboards
- Set budget alerts to avoid overruns
- Use simple PDFs for most tests to minimize AI processing

**Cost Estimation**:
- Simple PDF (~15 pages): $0.05 - $0.10 per job
- Complex PDF (~300 pages): $0.50 - $1.00 per job
- 10 users × 10 minutes × 2 conversions/user = ~$10-20 total

## Next Steps

After completing load tests:

1. Review `load-test-report-{date}.md` in `docs/sprint-artifacts/`
2. Identify top 3 bottlenecks (prioritized by impact)
3. Document optimization recommendations
4. Update architecture if scaling changes needed
5. Mark Story 7-2 as complete in sprint-status.yaml

## References

- [Locust Documentation](https://docs.locust.io/)
- [PRD - Non-Functional Requirements](../../docs/prd.md#Non-Functional-Requirements)
- [Architecture - Performance Considerations](../../docs/architecture.md#Performance-Considerations)
- [Story 7-2 Acceptance Criteria](../../docs/sprint-artifacts/7-2-load-performance-testing.md)
