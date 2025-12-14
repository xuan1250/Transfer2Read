# Real-Time Progress Updates Architecture

## Overview

Transfer2Read implements real-time conversion progress updates using a **polling-based architecture** for MVP deployment on serverless platforms (Vercel + Railway).

## Communication Strategy

### Decision: HTTP Polling (MVP)

**Chosen Approach:** HTTP Polling via REST API
**Polling Interval:** 2 seconds during active conversion
**Endpoint:** `GET /api/v1/jobs/{job_id}/progress`

### Rationale

| Factor | WebSocket | SSE | **Polling (Selected)** |
|--------|-----------|-----|------------------------|
| **Serverless Support** | Limited (Railway OK, Vercel Edge issues) | Partial (timeouts on long connections) | ✅ Full support |
| **Implementation Complexity** | High (connection management, reconnection) | Medium | ✅ Low |
| **Frontend Compatibility** | Modern browsers only | Good | ✅ Universal |
| **Infrastructure Requirements** | Persistent connections, stateful workers | Long-lived connections | ✅ Stateless |
| **Cost** | Higher (connection overhead) | Medium | ✅ Lower |
| **Latency** | ~100ms | ~100ms | ~2 seconds (acceptable for conversion feedback) |

**Conclusion:** Polling provides the best balance of simplicity, serverless compatibility, and acceptable UX for conversion progress (users expect 1-2 minute conversions, not instant updates).

### Future Enhancement

When infrastructure supports persistent connections:
- **Option A:** WebSocket via FastAPI WebSocket endpoint
- **Option B:** Server-Sent Events (SSE) via Starlette EventSource
- **Migration Path:** Minimal frontend changes (swap `useJobProgress` implementation)
- **Fallback:** Keep polling for browsers without WebSocket support

## Architecture Components

### 1. Backend Progress API

**Endpoint:** `GET /api/v1/jobs/{job_id}/progress`

**Purpose:** Lightweight endpoint returning ONLY progress data (not full job object)

**Response Schema:**
```json
{
  "job_id": "uuid",
  "status": "PROCESSING",
  "progress_percentage": 50,
  "current_stage": "layout_analysis",
  "stage_description": "Detecting tables and images...",
  "elements_detected": {
    "tables": 12,
    "images": 8,
    "equations": 5,
    "chapters": 15
  },
  "estimated_time_remaining": 45,
  "estimated_cost": 0.12,
  "quality_confidence": 94,
  "timestamp": "2025-12-14T10:30:00Z"
}
```

**Performance Requirements:**
- Response time: <200ms target
- Concurrent requests: Handle 100+ simultaneous polling clients
- Database queries: Efficient indexed lookups (job_id primary key)
- Payload size: <1KB (minimal JSON)

### 2. Conversion Pipeline Progress Updates

**Integration Points:**

Each Celery task in the conversion pipeline emits progress updates:

1. **Upload Complete** → 10%
2. **Layout Analysis Start** → 25%
3. **Layout Analysis Complete** → 50%
   - Elements detected updated
   - Estimated cost updated
4. **Structure Recognition** → 75%
   - Chapters detected updated
5. **EPUB Generation** → 95%
6. **Quality Scoring Complete** → 100%
   - Quality confidence updated

**Storage:** Progress metadata stored in `conversion_jobs` table JSONB field

**Example Update Call:**
```python
update_job_progress(job_id, {
    "progress_percentage": 25,
    "current_stage": "layout_analysis",
    "stage_description": "Analyzing layout...",
    "timestamp": datetime.utcnow().isoformat()
})
```

### 3. Frontend Polling Hook

**Hook:** `useJobProgress(jobId: string)`

**Behavior:**
- Start polling when job status = QUEUED or PROCESSING
- Poll every 2 seconds (configurable via `PROGRESS_POLLING_INTERVAL`)
- Stop polling when status = COMPLETED or FAILED
- Cleanup interval on component unmount

**Implementation:** TanStack Query with `refetchInterval`

**Error Handling:**
- Retry failed requests (max 3 attempts)
- Exponential backoff (1s, 2s, 4s, max 10s)
- Visual "Reconnecting..." indicator on connection loss

### 4. Progress UI Component

**Component:** `JobProgress.tsx`

**Displays:**
- Animated progress bar (0-100%)
- Current stage description
- Element detection counters (tables, images, equations, chapters)
- Estimated time remaining
- **Real-time AI cost estimate** (from AC #6)
- Quality confidence score (when available)

**Visual Feedback:**
- Smooth progress bar animation (300ms transition)
- Element counters increment in real-time (not all at once)
- Checkmark icons when elements complete
- Color-coded quality score (green >90%, yellow 70-90%, red <70%)

## AI Cost Tracking Integration

### LangChain Callback Implementation

**Purpose:** Track token usage during AI API calls to calculate estimated cost per job

**Implementation:**
- Callback class: `CostTrackerCallback` in `backend/app/services/ai/cost_tracker.py`
- Integrated with `LayoutAnalyzer` and `StructureAnalyzer`
- Tracks: `prompt_tokens`, `completion_tokens`, `total_tokens`

**Cost Calculation:**
```python
# GPT-4o pricing
input_cost = (prompt_tokens / 1_000_000) * 2.50   # $2.50/1M input tokens
output_cost = (completion_tokens / 1_000_000) * 10.00  # $10.00/1M output tokens
total_cost = round(input_cost + output_cost, 4)  # Round to 4 decimal places
```

**Storage:**
```json
{
  "quality_report": {
    "overall_confidence": 95,
    "estimated_cost": 0.15,
    "token_usage": {
      "prompt_tokens": 5000,
      "completion_tokens": 2000,
      "total_tokens": 7000
    }
  }
}
```

**Real-Time Display:**
- Progress UI shows: "Processing... Estimated cost: $0.12"
- Updates incrementally as AI stages complete (layout analysis → structure recognition)

## Connection Handling and Reliability

### Reconnection Strategy

**Network Interruption Handling:**
1. Polling request fails (network error, timeout)
2. React Query automatic retry (max 3 attempts)
3. Exponential backoff delay: 1s → 2s → 4s → 10s (max)
4. Visual indicator: "Reconnecting..." displayed to user
5. Resume from current state (don't reset progress bar)

**Stale Connection Detection:**
- If no progress update for >30 seconds during PROCESSING → Force refresh
- Check `timestamp` field to detect stale data

**Graceful Degradation:**
- If polling fails repeatedly → Display last known progress + "Connection lost" message
- User can manually refresh or retry
- Job continues processing in background (Celery worker independent)

## Performance Optimization

### Update Throttling

**Backend:**
- Pipeline emits updates at key stages only (not continuous)
- Avoid overwhelming database with write operations
- Batch element count updates per page analyzed

**Frontend:**
- Polling interval: 2 seconds (not faster)
- React Query deduplication prevents duplicate requests
- `useMemo` for expensive calculations (progress percentage)

### Payload Optimization

**Delta Updates:**
- Only send changed fields (not full job object)
- Example: `{ "progress_percentage": 55, "elements_detected": { "tables": 15 } }` (18 bytes) vs. full job JSON (500+ bytes)

**Efficient Serialization:**
- Pydantic V2 fast JSON serialization
- No nested queries (single table read: `conversion_jobs`)

**Connection Cleanup:**
- `useEffect` cleanup function stops polling on unmount
- React Query garbage collection removes cached data

## Configuration

### Environment Variables

**Backend (`backend/app/core/config.py`):**
```python
# AI Cost Tracking
OPENAI_INPUT_COST_PER_1M = 2.50
OPENAI_OUTPUT_COST_PER_1M = 10.00
ANTHROPIC_INPUT_COST_PER_1M = 0.25
ANTHROPIC_OUTPUT_COST_PER_1M = 1.25

# Progress Polling
PROGRESS_POLLING_INTERVAL = 2000  # milliseconds
```

**Frontend (`frontend/.env.local`):**
```bash
NEXT_PUBLIC_PROGRESS_POLLING_INTERVAL=2000  # milliseconds
```

## Testing Strategy

### Backend Unit Tests
- Test `ProgressUpdate` schema validation
- Test progress endpoint with different job states (QUEUED, PROCESSING, COMPLETED, FAILED)
- Test cost calculation with mock token counts
- Mock Celery task updates

### Frontend Unit Tests
- Test `useJobProgress` hook polling logic
- Test progress component rendering with different states
- Test error handling and retry logic

### Integration Tests
- Run full conversion pipeline with progress updates enabled
- Poll progress endpoint during conversion
- Verify progress sequence: 10% → 25% → 50% → 75% → 95% → 100%
- Verify element counts increment correctly
- Verify estimated cost appears after AI stages

### Performance Tests
- Measure progress endpoint latency (<200ms target)
- Test concurrent polling (100 users polling different jobs)
- Ensure efficient database query performance

## Error Handling

### Job Failures
- If job status = FAILED → Stop polling, display error message
- Error message includes timestamp and suggested actions
- User can retry conversion or contact support

### Connection Errors
- Retry with exponential backoff (max 3 attempts)
- Display "Reconnecting..." during retry
- Fallback to last known progress if all retries fail

### Timeout Scenarios
- If no update for >10 minutes → Stop polling, display timeout message
- User can manually refresh or check job history

## Security Considerations

### Authentication
- Progress endpoint requires valid Supabase JWT token
- Extract `user_id` from JWT to validate job ownership

### Authorization
- RLS policy: `auth.uid() = user_id` prevents cross-user access
- Return 404 if job not found (don't leak job IDs)
- Return 403 if user doesn't own job

### Rate Limiting
- Consider implementing rate limits on progress endpoint (optional)
- Prevent abuse: Max 1 request per second per job_id

## Migration Path to WebSocket/SSE

### When to Migrate
- When Railway/Vercel infrastructure supports persistent connections
- When user base grows and polling overhead becomes significant
- When real-time latency <1s becomes critical

### Migration Steps
1. Implement WebSocket endpoint: `WS /api/v1/jobs/{job_id}/stream`
2. Backend pushes progress updates via WebSocket (no client polling)
3. Frontend: Modify `useJobProgress` to use WebSocket client
4. Keep polling as fallback for browsers without WebSocket support
5. Feature flag: `USE_WEBSOCKET=true` to gradually roll out

### Backward Compatibility
- Polling endpoint remains available
- Frontend auto-detects WebSocket support
- Graceful fallback to polling if WebSocket unavailable

## References

- [Story 5.1 Context](../docs/sprint-artifacts/5-1-real-time-progress-updates.context.xml)
- [Architecture ADR-003: Async Processing with Celery](../docs/architecture.md#adr-003-async-processing-with-celery)
- [UX Design Spec Section 6.2: Processing & Results](../docs/ux-design-specification.md#62-processing--results---progress-feedback)

---

**Document Status:** Design Complete
**Implementation Status:** In Progress
**Last Updated:** 2025-12-14
**Author:** Dev Agent (Story 5.1 Implementation)
