# Pre-Flight Integration Checklist

**Story:** ___________________________
**Date:** ____________________________
**Developer:** _______________________

## 1. Services & Dependencies

- [ ] All external services are accessible (Supabase, AI APIs, Redis)
- [ ] Environment variables configured correctly
- [ ] Service health checks passing
- [ ] API rate limits understood and handled
- [ ] Required dependencies installed (no missing packages)

## 2. Data Flow

- [ ] Data flows correctly through all pipeline stages
- [ ] Database schema changes applied (migrations run)
- [ ] Data serialization/deserialization working (JSON, JSONB)
- [ ] RLS policies enforced correctly
- [ ] API endpoints return correct response schemas

## 3. Error Handling

- [ ] All error paths covered with try-except/try-catch
- [ ] Graceful degradation implemented where applicable
- [ ] User-facing error messages clear and actionable
- [ ] Errors logged for debugging (no sensitive data exposed)
- [ ] Network errors handled with retry logic

## 4. Testing

- [ ] Unit tests passing (backend + frontend)
- [ ] Integration tests passing
- [ ] Edge cases tested (network failures, invalid data, timeouts)
- [ ] Performance tests passing (if applicable)
- [ ] Manual end-to-end test completed successfully

## 5. Documentation

- [ ] Relevant documentation updated (architecture, API docs)
- [ ] Code comments added for complex logic
- [ ] README updated if new setup steps required
- [ ] Changelog updated with implemented features
- [ ] Implementation summary created

## 6. Code Review Readiness

- [ ] Code follows project style guide
- [ ] No commented-out code or debug statements
- [ ] No hardcoded secrets or sensitive data
- [ ] PR description includes completed checklist
- [ ] Story file updated with completion notes

## 7. Integration-Specific Checks

### Real-Time Updates (Story 5.1)

- [ ] TanStack Query installed and QueryProvider configured
- [ ] useJobProgress hook polling correctly (2-second interval)
- [ ] JobProgress component renders progress bar, element counters, cost
- [ ] Progress endpoint returns ProgressUpdate schema
- [ ] Polling stops when job status is COMPLETED or FAILED
- [ ] Connection loss handled with retry logic
- [ ] Job status page integrates JobProgress component
- [ ] Environment variable NEXT_PUBLIC_API_URL configured

### AI Cost Tracking (Story 5.1)

- [ ] CostTrackerCallback implemented for LangChain
- [ ] Token usage tracked in AI service calls
- [ ] Cost calculation tested with mock token counts
- [ ] Estimated cost displayed in progress UI
- [ ] Cost stored in quality_report.estimated_cost field

## Notes

(Add any additional notes or observations below)

---

## Completion Confirmation

I confirm that all checklist items have been verified and the story is ready for code review.

**Signed:** ___________________________
**Date:** ____________________________
