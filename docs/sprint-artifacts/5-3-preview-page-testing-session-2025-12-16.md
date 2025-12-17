# Story 5.3 Preview Comparison Page - Testing Session

**Date:** 2025-12-16
**Story:** 5.3 Split-Screen Comparison UI
**Status:** Testing and bug fixes
**Tester:** dev-story workflow (requested by xavier)

## Summary

Testing session to verify the Preview Comparison page functionality for Epic 5. This page displays a split-screen view comparing the original PDF with the converted EPUB, allowing users to visually verify conversion quality before downloading.

## Issues Found and Fixed

### Issue #1: Authentication Token Not Working ✅ FIXED

**Severity:** HIGH
**Location:** `frontend/src/components/business/SplitScreenComparison.tsx:76, 90`

**Problem:**
The component was attempting to fetch the authentication token from `localStorage.getItem('supabase-auth-token')`, which doesn't exist. Supabase stores session data differently and requires using the `supabase.auth.getSession()` method.

**Impact:**
- Preview page would fail to load PDF and EPUB files
- Users would see "Failed to fetch PDF file" / "Failed to fetch EPUB file" errors
- Authentication headers were invalid, causing 401 errors from backend

**Root Cause:**
The code was using an incorrect pattern for retrieving the Supabase auth token. The correct pattern used elsewhere in the app (e.g., `useJob` hook) retrieves the session via `supabase.auth.getSession()` and uses `session.access_token`.

**Fix Applied:**
```typescript
// BEFORE (INCORRECT):
const pdfResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/jobs/${job.id}/files/input`, {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('supabase-auth-token')}`,
  },
});

// AFTER (CORRECT):
const { data: { session }, error: sessionError } = await supabase.auth.getSession();

if (sessionError || !session) {
  throw new Error('Authentication required. Please log in again.');
}

const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const authHeader = `Bearer ${session.access_token}`;

const pdfResponse = await fetch(`${apiUrl}/api/v1/jobs/${job.id}/files/input`, {
  headers: {
    'Authorization': authHeader,
    'Content-Type': 'application/json',
  },
});
```

**Changes Made:**
1. Added `import { createClient } from '@/lib/supabase/client';`
2. Added `const supabase = createClient();` in component
3. Updated `fetchFileUrls` function to use `supabase.auth.getSession()`
4. Used `session.access_token` for authentication header
5. Added better error messages with status codes
6. Added `supabase` to useEffect dependency array

**Files Modified:**
- `frontend/src/components/business/SplitScreenComparison.tsx`

**Testing:**
- ✅ TypeScript build passes with no errors
- ✅ Component compiles successfully
- ⏳ Functional testing pending (requires authenticated session with completed job)

---

## Testing Checklist

### Prerequisites
- [x] Backend server running on http://localhost:8000
- [x] Frontend server running on http://localhost:3000
- [ ] User authenticated with Supabase
- [ ] At least one completed conversion job available
- [ ] Sample PDF and EPUB files in Supabase Storage

### Functional Tests

#### Test 1: Authentication Guard
- [ ] Navigate to `/jobs/{id}/preview` without authentication
- **Expected:** Redirect to `/login?returnUrl=/jobs/{id}/preview`
- **Actual:** _Pending_

#### Test 2: Job Status Validation
- [ ] Navigate to preview page for job with status != COMPLETED
- **Expected:** Show alert "Preview is only available for completed conversions"
- **Actual:** _Pending_

#### Test 3: File Loading
- [ ] Navigate to preview page for completed job
- **Expected:**
  - Show loading skeleton
  - Fetch PDF signed URL from `/api/v1/jobs/{id}/files/input`
  - Fetch EPUB signed URL from `/api/v1/jobs/{id}/download`
  - Display both files in split-screen layout
- **Actual:** _Pending_

#### Test 4: Split-Screen Layout (Desktop)
- [ ] View preview on desktop screen (≥1024px)
- **Expected:** Side-by-side layout with PDF on left, EPUB on right
- **Actual:** _Pending_

#### Test 5: Vertical Stack Layout (Tablet)
- [ ] View preview on tablet screen (768px-1023px)
- **Expected:** Vertical stack with PDF on top, EPUB below
- **Actual:** _Pending_

#### Test 6: Tabbed Layout (Mobile)
- [ ] View preview on mobile screen (<768px)
- **Expected:** Tabs with "PDF" and "EPUB" options
- **Actual:** _Pending_

#### Test 7: PDF Viewer Controls
- [ ] Click Previous/Next page buttons
- [ ] Click zoom controls (Fit Width, Fit Page, 100%, 150%, 200%)
- [ ] Verify current page indicator updates
- **Expected:** PDF viewer responds correctly to all controls
- **Actual:** _Pending_

#### Test 8: EPUB Viewer
- [ ] Verify EPUB content renders with proper formatting
- [ ] Check if TOC navigation works
- [ ] Verify chapter structure preserved
- **Expected:** EPUB displays correctly with formatting intact
- **Actual:** _Pending_

#### Test 9: Scroll Synchronization
- [ ] Scroll PDF to page 10
- [ ] Verify EPUB auto-scrolls to corresponding chapter
- [ ] Scroll EPUB to chapter 3
- [ ] Verify PDF auto-scrolls to corresponding page
- [ ] Toggle sync off
- [ ] Verify scrolling is independent
- **Expected:** Bidirectional sync works when enabled
- **Actual:** _Pending_

#### Test 10: Keyboard Shortcuts
- [ ] Press Arrow Left/Right → Navigate PDF pages
- [ ] Press +/- → Zoom in/out
- [ ] Press S → Toggle synchronization
- [ ] Press Esc → Return to job results page
- **Expected:** All keyboard shortcuts work
- **Actual:** _Pending_

#### Test 11: Toolbar Actions
- [ ] Click "Back to Results" button
- [ ] Click "Download EPUB" button
- [ ] Click sync toggle button
- **Expected:** All toolbar actions work correctly
- **Actual:** _Pending_

#### Test 12: Error Handling
- [ ] Test with job that has no input file
- [ ] Test with job that has no output file
- [ ] Test with network timeout (throttle to Slow 3G)
- [ ] Test with 403 error (access other user's job)
- **Expected:** User-friendly error messages with retry button
- **Actual:** _Pending_

### Performance Tests

#### Test 13: Load Time
- [ ] Load preview with 10-page PDF
- [ ] Load preview with 50-page PDF
- [ ] Load preview with 300-page PDF
- **Expected:**
  - 10-page: <2 seconds
  - 50-page: <3 seconds
  - 300-page: <5 seconds
- **Actual:** _Pending_

#### Test 14: Memory Usage
- [ ] Open Chrome DevTools → Performance Monitor
- [ ] Load 300-page PDF
- [ ] Scroll through entire document
- **Expected:** Memory usage <500MB
- **Actual:** _Pending_

#### Test 15: Scrolling Performance
- [ ] Open Chrome DevTools → Performance tab
- [ ] Record scrolling session
- [ ] Analyze frame rate
- **Expected:** 60fps maintained during scrolling
- **Actual:** _Pending_

### Cross-Browser Tests

#### Test 16: Chrome
- [ ] Test all functionality in Chrome
- **Expected:** All features work
- **Actual:** _Pending_

#### Test 17: Firefox
- [ ] Test all functionality in Firefox
- **Expected:** All features work
- **Actual:** _Pending_

#### Test 18: Safari
- [ ] Test all functionality in Safari
- **Expected:** All features work (note: PDF.js may have differences)
- **Actual:** _Pending_

#### Test 19: Edge
- [ ] Test all functionality in Edge
- **Expected:** All features work
- **Actual:** _Pending_

### Accessibility Tests

#### Test 20: Keyboard Navigation
- [ ] Tab through all interactive elements
- [ ] Verify focus indicators visible
- [ ] Verify logical tab order
- **Expected:** All controls keyboard-accessible
- **Actual:** _Pending_

#### Test 21: Screen Reader (Optional)
- [ ] Test with VoiceOver (macOS) or NVDA (Windows)
- [ ] Verify page changes announced
- [ ] Verify sync toggle state announced
- **Expected:** Screen reader compatibility
- **Actual:** _Pending_

#### Test 22: Color Contrast
- [ ] Run axe DevTools audit
- [ ] Verify WCAG 2.1 AA compliance
- **Expected:** No color contrast violations
- **Actual:** _Pending_

---

## Known Issues

### Issue #2: Backend Endpoint Verification Needed
**Status:** To be verified
**Description:** Need to verify the backend endpoint `/api/v1/jobs/{job_id}/files/input` is working correctly with authentication and returning proper signed URLs.

### Issue #3: EPUB Viewer CFI Mapping
**Status:** Implemented in previous code review session
**Description:** EPUB Canonical Fragment Identifier (CFI) mapping for precise chapter navigation. Implementation was added on 2025-12-15 (EPUBViewer.tsx:105-164).

---

## Test Environment

**Frontend:**
- URL: http://localhost:3000
- Next.js: 15.5.7
- React: 19.2.1
- TypeScript: 5.x

**Backend:**
- URL: http://localhost:8000
- FastAPI: 0.122.0
- Python: 3.12.9

**Database:**
- Supabase PostgreSQL
- Supabase Storage for file storage

---

## Next Steps

1. **Manual Testing Required:**
   - Create a test conversion job (upload PDF, wait for completion)
   - Navigate to `/jobs/{id}/preview` and test all functionality
   - Document results in this file

2. **Automated Testing:**
   - Implement component tests (PDFViewer, EPUBViewer, SplitScreenComparison)
   - Implement integration tests with Playwright
   - Set up visual regression tests

3. **Performance Benchmarking:**
   - Run Chrome DevTools profiling with 300-page PDF
   - Document load times, memory usage, FPS

4. **Cross-Browser Testing:**
   - Test on Chrome, Firefox, Safari, Edge
   - Document any browser-specific issues

5. **Accessibility Audit:**
   - Run axe DevTools audit
   - Test with screen reader
   - Verify WCAG 2.1 AA compliance

---

## Questions for User (xavier)

1. **What specific problems are you seeing with the Preview Comparison page?**
   - Authentication errors?
   - Files not loading?
   - Layout issues?
   - Scroll sync not working?
   - Other visual/functional bugs?

2. **Do you have a completed job we can use for testing?**
   - If yes, what's the job ID?
   - Does the job have both PDF and EPUB files in Supabase Storage?

3. **What browser are you using for testing?**
   - Chrome, Firefox, Safari, Edge?
   - Desktop or mobile?

4. **Are you logged in when you navigate to the preview page?**
   - If not, does it redirect you to login?

5. **Any error messages in the browser console?**
   - Can you share the console logs?

---

## Fixed Issues Summary

✅ **Issue #1:** Authentication token retrieval fixed - now using `supabase.auth.getSession()` instead of localStorage
✅ **Build Verification:** Frontend builds successfully with no TypeScript errors
✅ **Backend Status:** Backend server running on port 8000
✅ **Frontend Status:** Frontend development server running

---

**Report Status:** IN PROGRESS - Awaiting user feedback on specific issues and manual testing
