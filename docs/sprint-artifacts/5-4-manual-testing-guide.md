# Story 5.4 Manual Testing Guide

**Story:** Download & Feedback Flow
**Date Created:** 2025-12-15
**Purpose:** Comprehensive manual testing instructions for validating all features
**Status:** For Tasks 7-10 completion (E2E, Pre-Flight, Accessibility, Integration Testing)

---

## Table of Contents

1. [Pre-Test Setup](#pre-test-setup)
2. [Test Environment Requirements](#test-environment-requirements)
3. [Test Scenarios](#test-scenarios)
   - [Download Flow Testing](#download-flow-testing)
   - [Confetti Animation Testing](#confetti-animation-testing)
   - [Feedback Widget Testing](#feedback-widget-testing)
   - [Issue Report Modal Testing](#issue-report-modal-testing)
   - [Error Handling Testing](#error-handling-testing)
   - [Accessibility Testing](#accessibility-testing)
   - [Cross-Browser Testing](#cross-browser-testing)
   - [Mobile Device Testing](#mobile-device-testing)
4. [Analytics Validation](#analytics-validation)
5. [Pre-Flight Checklist](#pre-flight-checklist)
6. [Test Results Template](#test-results-template)

---

## Pre-Test Setup

### 1. Start All Services

```bash
# Terminal 1: Start Redis
cd /Users/dominhxuan/Desktop/Transfer2Read
docker-compose up

# Terminal 2: Start Backend
cd backend
source venv/bin/activate  # or: . venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 3: Start Celery Worker
cd backend
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info

# Terminal 4: Start Frontend
cd frontend
npm run dev
```

### 2. Verify Services Running

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/docs (Swagger UI)
- **Redis:** `redis-cli ping` should return `PONG`
- **Database:** Verify Supabase project is accessible

### 3. Create Test User

1. Navigate to http://localhost:3000/login
2. Sign up with test credentials:
   - Email: `test@example.com`
   - Password: `Test123!@#`
3. Verify email (check Supabase Auth dashboard if needed)
4. Log in successfully

### 4. Create Test Job (Completed Conversion)

**Option A: Upload a Real PDF**
1. Navigate to http://localhost:3000/upload
2. Upload a small PDF file (test file: any 5-10 page PDF)
3. Wait for conversion to complete (status = COMPLETED)
4. Note the Job ID from URL: `/jobs/{job_id}`

**Option B: Use Backend Swagger UI (Faster)**
1. Go to http://localhost:8000/docs
2. Authorize with Supabase JWT token
3. Create a mock completed job for testing
4. Update job status to "COMPLETED" in database

---

## Test Environment Requirements

### Required Tools
- **Browsers:** Chrome, Firefox, Safari, Edge
- **Mobile Devices:** iOS (iPhone/iPad), Android (phone/tablet)
- **Screen Readers:** VoiceOver (Mac/iOS), NVDA (Windows), TalkBack (Android)
- **Network Tools:** Chrome DevTools Network tab, Throttling
- **Accessibility Tools:** axe DevTools browser extension

### Test Data
- **Valid Job ID:** From pre-test setup (COMPLETED status)
- **Invalid Job ID:** `00000000-0000-0000-0000-000000000000`
- **Other User's Job ID:** Create second account and job for auth testing

---

## Test Scenarios

### Download Flow Testing

#### Test Case 1.1: Successful Download
**AC:** #1 - Download EPUB button functionality

**Steps:**
1. Navigate to `/jobs/{valid_job_id}` with COMPLETED job
2. Verify "Download EPUB" button is visible and enabled
3. Click "Download EPUB" button
4. Observe browser behavior

**Expected Results:**
- ✅ Button displays "Download EPUB" text with Download icon
- ✅ New tab opens with signed Supabase Storage URL
- ✅ EPUB file downloads to browser's download folder
- ✅ Toast notification appears: "Download started! Your EPUB file is ready"
- ✅ Confetti animation plays (if first download - see next section)
- ✅ Button returns to normal state after download

**Pass/Fail:** Pass

**Notes:** When navigate to `/jobs/{valid_job_id}` with COMPLETED job, "Download EPUB" button is visible and enabled, but no Toast notification appears.

---

#### Test Case 1.2: Download Button Disabled State
**AC:** #1 - Button disabled while job status != COMPLETED

**Steps:**
1. Navigate to `/jobs/{job_id}` with status = PROCESSING
2. Observe download button state

**Expected Results:**
- ✅ "Download EPUB" button does NOT appear (only Preview button shown)
- ✅ Page shows JobProgress component with real-time updates

**Pass/Fail:** Pass

**Notes:** ___________________________________________

---

#### Test Case 1.3: Download Error - 404 (File Not Found)
**AC:** #1, #10 - Error handling for missing EPUB

**Steps:**
1. Manually delete EPUB file from Supabase Storage (or use invalid path)
2. Click "Download EPUB" button
3. Observe error handling

**Expected Results:**
- ✅ Button shows "Downloading..." briefly
- ✅ Error toast appears: "Download failed - Please try again later"
- ✅ Button returns to "Download EPUB" state (retry implicit)
- ✅ Console logs error details

**Pass/Fail:** Pass

**Notes:** Functionality is correct, but Toast notification does not appear.
Console logs error details: 127.0.0.1:50153 - "GET /api/v1/jobs/d9680c37-79b5-4648-b309-7089dec185b8/download HTTP/1.1" 500 Internal Server Error
---

#### Test Case 1.4: Download Error - 403 (Unauthorized)
**AC:** #1, #10 - Access control validation

**Steps:**
1. Log in as User A
2. Create/note Job ID for User A
3. Log out, log in as User B
4. Navigate to `/jobs/{user_a_job_id}`
5. Attempt to download

**Expected Results:**
- ✅ Page shows error: "You do not have permission to view this job"
- ✅ Download button not accessible
- ✅ "Back to History" button visible

**Pass/Fail:** Fail

**Notes:** Unauthorized error, test@example.com is User B is still download with jobs ID of User A and see all history of User A.

---

#### Test Case 1.5: Network Timeout Handling
**AC:** #1, #10 - Network error graceful degradation

**Steps:**
1. Open Chrome DevTools → Network tab
2. Set throttling to "Offline"
3. Click "Download EPUB" button
4. Wait for timeout

**Expected Results:**
- ✅ Error toast appears after fetch timeout
- ✅ Button returns to clickable state
- ✅ User can retry by clicking button again
- ✅ No browser crash or unhandled exception

**Pass/Fail:** Pass

**Notes:** Functionality is correct, but Toast notification does not appear.

---

### Confetti Animation Testing

#### Test Case 2.1: Confetti Plays on First Download
**AC:** #2 - Confetti animation on success

**Steps:**
1. Open `/jobs/{job_id}` in **incognito/private window**
2. Click "Download EPUB" button
3. Observe animation

**Expected Results:**
- ✅ Confetti animation plays immediately after download starts
- ✅ Animation uses Professional Blue theme colors (#2563eb, #0ea5e9, #10b981)
- ✅ Animation lasts 2-3 seconds
- ✅ Animation is celebratory (particles burst from center)
- ✅ localStorage key set: `confetti-shown-{job_id}` = "true"

**Pass/Fail:** Pass

**Notes:** ___________________________________________

---

#### Test Case 2.2: Confetti Does NOT Play on Subsequent Downloads
**AC:** #2 - Animation plays once per download

**Steps:**
1. Complete Test Case 2.1 first
2. Refresh page (F5)
3. Click "Download EPUB" button again

**Expected Results:**
- ✅ Download proceeds normally
- ✅ No confetti animation plays
- ✅ Toast notification still appears

**Pass/Fail:** Pass

**Notes:** ___________________________________________

---

#### Test Case 2.3: Confetti Respects Motion Sensitivity
**AC:** #2, #11 - Accessibility for motion sensitivity

**Steps:**
1. Open macOS System Settings → Accessibility → Display
2. Enable "Reduce motion"
3. Open `/jobs/{job_id}` in new incognito window
4. Click "Download EPUB"

**Expected Results:**
- ✅ Download proceeds normally
- ✅ No confetti animation plays (skipped for accessibility)
- ✅ Toast notification still appears
- ✅ `window.matchMedia('(prefers-reduced-motion: reduce)')` returns `true` in console

**Pass/Fail:** Pass

**Notes:** ___________________________________________

---

### Feedback Widget Testing

#### Test Case 3.1: Positive Feedback Submission
**AC:** #4 - Thumbs up feedback flow

**Steps:**
1. Navigate to `/jobs/{job_id}` with COMPLETED job
2. Scroll to "How was this conversion?" widget
3. Click "👍 Good" button
4. Observe state changes

**Expected Results:**
- ✅ "Good" button highlights (variant changes to default)
- ✅ "Submit Feedback" button appears below
- ✅ Click "Submit Feedback"
- ✅ Button shows "Submitting..." during API call
- ✅ Toast appears: "Thank you for your feedback! Your input helps us improve conversion quality."
- ✅ Widget replaced with success message: "✅ Thank you for your feedback!"
- ✅ Backend API called: `POST /api/v1/jobs/{job_id}/feedback` with `rating: "positive"`

**Pass/Fail:** Fail

**Notes:** Feedback widget shows up, click "submit feedback" button, it shows "Submitting..." but no toast notification appears. Widget is not replaced with success message. Backend API: INFO:     127.0.0.1:53771 - "OPTIONS /api/v1/jobs/650e6fef-5e17-407f-8bc7-56701c67d3fe/feedback HTTP/1.1" 200 OK
submit_feedback_error
Traceback (most recent call last):
  File "/Users/dominhxuan/Desktop/Transfer2Read/backend/app/api/v1/jobs.py", line 818, in submit_feedback
    job = job_service.get_job_by_id(job_id, current_user.user_id)
          ^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'JobService' object has no attribute 'get_job_by_id'
INFO:     127.0.0.1:53771 - "POST /api/v1/jobs/650e6fef-5e17-407f-8bc7-56701c67d3fe/feedback HTTP/1.1" 500 Internal Server Error
---

#### Test Case 3.2: Negative Feedback with Comment
**AC:** #4 - Thumbs down with optional comment

**Steps:**
1. Navigate to `/jobs/{job_id}` with COMPLETED job
2. Click "👎 Needs Improvement" button
3. Observe UI changes

**Expected Results:**
- ✅ "Needs Improvement" button highlights
- ✅ Textarea appears: "What went wrong? (optional)"
- ✅ Type comment: "Tables were misaligned on page 3"
- ✅ "Submit Feedback" button appears
- ✅ Click "Submit Feedback"
- ✅ API called with `rating: "negative"` and `comment: "Tables were misaligned on page 3"`
- ✅ Success toast and widget replaced with thank you message

**Pass/Fail:** Fail

**Notes:** Everthing is OFK same test case 3.1, but when Submit Feedback button is clicked, it shows "Submitting..." but no toast notification appears. Widget is not replaced with success message. Backend API: INFO:     127.0.0.1:53771 - "OPTIONS /api/v1/jobs/650e6fef-5e17-407f-8bc7-56701c67d3fe/feedback HTTP/1.1" 200 OK
submit_feedback_error
Traceback (most recent call last):
  File "/Users/dominhxuan/Desktop/Transfer2Read/backend/app/api/v1/jobs.py", line 818, in submit_feedback
    job = job_service.get_job_by_id(job_id, current_user.user_id)
          ^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'JobService' object has no attribute 'get_job_by_id'
INFO:     127.0.0.1:53771 - "POST /api/v1/jobs/650e6fef-5e17-407f-8bc7-56701c67d3fe/feedback HTTP/1.1" 500 Internal Server Error

---

#### Test Case 3.3: Feedback Submission Error Handling
**AC:** #4, #10 - API failure graceful degradation

**Steps:**
1. Open Chrome DevTools → Network tab
2. Right-click on feedback API call → Block request URL pattern
3. Click "👍 Good" → "Submit Feedback"
4. Observe error handling

**Expected Results:**
- ✅ Error toast appears: "Failed to submit feedback - Please try again later"
- ✅ Widget remains visible (not replaced with success state)
- ✅ User can retry submission
- ✅ No console errors or crashes

**Pass/Fail:** Fail

**Notes:** I see Request URL
http://localhost:8000/api/v1/jobs/650e6fef-5e17-407f-8bc7-56701c67d3fe/feedback/check
Request Method
GET
Status Code
404 Not Found
Remote Address
127.0.0.1:8000
Referrer Policy
strict-origin-when-cross-origin

---

### Issue Report Modal Testing

#### Test Case 4.1: Open Issue Report Modal
**AC:** #3 - Report issue button and modal

**Steps:**
1. Navigate to `/jobs/{job_id}` with COMPLETED job
2. Click "Report Issue" button (with Flag icon)
3. Observe modal appearance

**Expected Results:**
- ✅ Modal dialog opens with title "Report an Issue"
- ✅ Description text: "Help us improve by reporting problems with the conversion output."
- ✅ Form fields visible:
   - Issue Type dropdown (required)
   - Page Number input (optional)
   - Description textarea (required)
- ✅ "Cancel" and "Submit Report" buttons at bottom

**Pass/Fail:** Pass

**Notes:** ___________________________________________

---

#### Test Case 4.2: Submit Valid Issue Report
**AC:** #3 - Full issue report flow

**Steps:**
1. Open Issue Report modal (Test Case 4.1)
2. Fill form:
   - Issue Type: "Table Formatting"
   - Page Number: 42
   - Description: "The table on page 42 has misaligned columns. Data in column 3 appears in column 4."
3. Click "Submit Report"

**Expected Results:**
- ✅ Button shows "Submitting..." during API call
- ✅ API call: `POST /api/v1/jobs/{job_id}/issues` with correct data
- ✅ Success toast: "Issue reported successfully - Thank you for helping us improve!"
- ✅ Modal closes automatically
- ✅ Form resets (ready for next use if modal reopened)

**Pass/Fail:** Fail

**Notes:** When press "Submit Report" button, it shows "Submitting..." but no toast notification appears. Modal does not close automatically. Form is not reset. Back end API: INFO:     127.0.0.1:56347 - "POST /api/v1/jobs/650e6fef-5e17-407f-8bc7-56701c67d3fe/issues HTTP/1.1" 500 Internal Server Error
report_issue_error
Traceback (most recent call last):
  File "/Users/dominhxuan/Desktop/Transfer2Read/backend/app/api/v1/jobs.py", line 958, in report_issue
    job = job_service.get_job_by_id(job_id, current_user.user_id)
          ^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'JobService' object has no attribute 'get_job_by_id'
INFO:     127.0.0.1:56412 - "POST /api/v1/jobs/650e6fef-5e17-407f-8bc7-56701c67d3fe/issues HTTP/1.1" 500 Internal Server Error

---

#### Test Case 4.3: Issue Report Validation - Empty Description
**AC:** #3, #10 - Form validation

**Steps:**
1. Open Issue Report modal
2. Select Issue Type: "Missing Images"
3. Leave Description empty (or just whitespace)
4. Click "Submit Report"

**Expected Results:**
- ✅ Toast error appears: "Description too short - Please provide at least 10 characters describing the issue."
- ✅ Modal remains open
- ✅ No API call made
- ✅ User can correct and resubmit

**Pass/Fail:** Pass

**Notes:** But It appear "Please fill out this field".

---

#### Test Case 4.4: Issue Report Validation - Description Too Short
**AC:** #3 - Min 10 characters validation

**Steps:**
1. Open Issue Report modal
2. Enter Description: "Bad" (3 characters)
3. Click "Submit Report"

**Expected Results:**
- ✅ Frontend validation toast: "Description too short..."
- ✅ No API call made
- ✅ Character counter shows: "3/5000 characters"

**Pass/Fail:** Fail

**Notes:** Nothing appears.

---

#### Test Case 4.5: Issue Report - All Issue Types
**AC:** #3 - Dropdown options validation

**Steps:**
1. Open Issue Report modal
2. Click "Issue Type" dropdown
3. Verify all options present

**Expected Results:**
- ✅ "Table Formatting"
- ✅ "Missing Images"
- ✅ "Broken Chapters"
- ✅ "Incorrect Equations"
- ✅ "Font Issues"
- ✅ "Other"

**Pass/Fail:** Pass

**Notes:** ___________________________________________

---

#### Test Case 4.6: Issue Report Modal - Close/Cancel
**AC:** #3 - Modal dismissal

**Steps:**
1. Open Issue Report modal
2. Fill form partially
3. Test close methods:
   - Click "Cancel" button
   - Click outside modal (backdrop)
   - Press Escape key

**Expected Results:**
- ✅ All three methods close the modal
- ✅ Form resets on close
- ✅ No API call made
- ✅ No data persisted

**Pass/Fail:** Pass

**Notes:** ___________________________________________

---

### Error Handling Testing

#### Test Case 5.1: Duplicate Feedback Prevention
**AC:** #10 - Prevent multiple submissions

**Current Status:** ⚠️ **KNOWN ISSUE - Not implemented**

**Steps:**
1. Submit feedback (Test Case 3.1)
2. Refresh page
3. Observe widget state

**Expected Results (If Implemented):**
- ✅ Widget should show "You've already submitted feedback" or be hidden
- ✅ Database query checks for existing feedback on mount
- ✅ Buttons disabled if feedback already exists

**Actual Behavior:**
- ❌ Widget reappears and allows duplicate submissions

**Pass/Fail:** FAIL (Expected - needs implementation)

**Notes:** Add to action items for follow-up. It has some problem in Test case 3.1

---

#### Test Case 5.2: Authentication Expiry During Action
**AC:** #5, #10 - JWT expiration handling

**Steps:**
1. Log in and navigate to `/jobs/{job_id}`
2. Wait for JWT to expire (or manually clear Supabase session in localStorage)
3. Click "Download EPUB" or "Submit Feedback"

**Expected Results:**
- ✅ API returns 401 Unauthorized
- ✅ User redirected to login page with return URL
- ✅ After login, user returns to same job page

**Pass/Fail:** ____

**Notes:** ___________________________________________

---

### Accessibility Testing

#### Test Case 6.1: Keyboard Navigation - Download Flow
**AC:** #11 - All interactive elements keyboard accessible

**Steps:**
1. Navigate to `/jobs/{job_id}` with COMPLETED job
2. Use only keyboard (no mouse):
   - Tab to "Preview Comparison" button → Press Enter
   - Navigate back
   - Tab to "Download EPUB" button → Press Enter
   - Tab to "Report Issue" button → Press Enter

**Expected Results:**
- ✅ All buttons receive visible focus indicator
- ✅ Tab order is logical (Preview → Download → Report Issue)
- ✅ Enter key activates buttons
- ✅ Focus trapped in modal when "Report Issue" opened
- ✅ Escape key closes modal

**Pass/Fail:** Pass

**Notes:** The preview page not working:  GET /favicon.ico 200 in 20ms
 ⨯ TypeError: Object.defineProperty called on non-object
    at Object.defineProperty (<anonymous>)
    at (ssr)/./node_modules/react-pdf/node_modules/pdfjs-dist/build/pdf.mjs (.next/server/vendor-chunks/react-pdf.js:220:1)
    at (ssr)/./node_modules/react-pdf/dist/Document.js (.next/server/vendor-chunks/react-pdf.js:20:1)
    at eval (webpack-internal:///(ssr)/./src/components/business/PDFViewer.tsx:9:68)
    at (ssr)/./src/components/business/PDFViewer.tsx (.next/server/app/jobs/[id]/preview/page.js:181:1)
    at eval (webpack-internal:///(ssr)/./src/components/business/SplitScreenComparison.tsx:10:68)
    at (ssr)/./src/components/business/SplitScreenComparison.tsx (.next/server/app/jobs/[id]/preview/page.js:203:1)
    at eval (webpack-internal:///(ssr)/./src/app/jobs/[id]/preview/page.tsx:12:100)
    at (ssr)/./src/app/jobs/[id]/preview/page.tsx (.next/server/app/jobs/[id]/preview/page.js:159:1) {
  digest: '375690840'
}

---

#### Test Case 6.2: Keyboard Navigation - Feedback Widget
**AC:** #11 - Feedback buttons accessible

**Steps:**
1. Tab to "Good" button → Press Enter
2. Tab to "Needs Improvement" button → Press Enter
3. Tab to textarea (if negative selected) → Type comment
4. Tab to "Submit Feedback" button → Press Enter

**Expected Results:**
- ✅ All buttons keyboard accessible
- ✅ Focus visible on all interactive elements
- ✅ Enter/Space activates buttons
- ✅ Textarea accepts keyboard input

**Pass/Fail:** Pass

**Notes:** 

---

#### Test Case 6.3: Keyboard Navigation - Issue Report Modal
**AC:** #11 - Modal fully keyboard accessible

**Steps:**
1. Tab to "Report Issue" button → Press Enter
2. Inside modal:
   - Tab through: Issue Type dropdown → Page Number input → Description textarea → Cancel → Submit
   - Use Arrow keys in dropdown to select issue type
   - Press Escape to close modal

**Expected Results:**
- ✅ Focus enters modal on open
- ✅ Focus trapped within modal (can't tab to background)
- ✅ Dropdown accessible with Arrow keys
- ✅ Escape key closes modal and returns focus to "Report Issue" button

**Pass/Fail:** Pass

**Notes:** ___________________________________________

---

#### Test Case 6.4: Screen Reader - VoiceOver (macOS)
**AC:** #11 - ARIA labels and announcements

**Steps:**
1. Enable VoiceOver: Cmd + F5
2. Navigate to `/jobs/{job_id}`
3. Use VoiceOver to navigate page elements

**Expected Results:**
- ✅ "Download EPUB" button announced as "Download EPUB, button"
- ✅ "Report Issue" button announced with accessible label
- ✅ Feedback widget buttons announced: "Good, button" and "Needs Improvement, button"
- ✅ Issue Report modal announced: "Report an Issue, dialog"
- ✅ Form labels properly associated with inputs
- ✅ Error messages announced when validation fails
- ✅ Success toasts announced automatically

**Pass/Fail:** Pass

**Notes:** ___________________________________________

---

#### Test Case 6.5: Color Contrast Validation
**AC:** #11 - WCAG 2.1 AA compliance (4.5:1 minimum)

**Steps:**
1. Install axe DevTools browser extension
2. Navigate to `/jobs/{job_id}`
3. Run axe accessibility scan

**Expected Results:**
- ✅ No color contrast violations
- ✅ Button text legible against background
- ✅ Focus indicators visible and meet contrast ratio
- ✅ Error states have sufficient contrast

**Pass/Fail:** Fail

**Notes:** Ensure every ARIA progressbar node has an accessible name.To solve this problem, you need to fix at least (1) of the following:
aria-label attribute does not exist or is empty
aria-labelledby attribute does not exist, references elements that do not exist or references elements that are empty
Element has no title attribute

---

#### Test Case 6.6: ARIA Labels on Icon-Only Buttons
**AC:** #11 - Accessible labels for icon buttons

**Steps:**
1. Inspect "Download EPUB" button in DevTools
2. Check for aria-label or sr-only text

**Expected Results:**
- ✅ Button has accessible text (not just icon)
- ✅ Screen readers announce button purpose
- ✅ Download icon is decorative (`aria-hidden="true"`) or has alt text

**Pass/Fail:** Pass

**Notes:** ___________________________________________

---

### Cross-Browser Testing

#### Test Case 7.1: Chrome (Latest)
**AC:** #10 - Cross-browser compatibility

**Steps:**
Run all Download Flow, Feedback, and Issue Report tests in Chrome

**Expected Results:**
- ✅ All features work identically to Firefox/Safari
- ✅ Confetti animation renders correctly
- ✅ Modals display properly
- ✅ No console errors

**Pass/Fail:** Pass

**Notes:** Error in test case 

---

#### Test Case 7.2: Firefox (Latest)
**AC:** #10 - Cross-browser compatibility

**Steps:**
Run all Download Flow, Feedback, and Issue Report tests in Firefox

**Expected Results:**
- ✅ All features functional
- ✅ shadcn/ui components render correctly
- ✅ Download triggers correctly
- ✅ No browser-specific issues

**Pass/Fail:** Pass  

**Notes:** Error in test case

---

#### Test Case 7.3: Safari (Latest)
**AC:** #10 - Cross-browser compatibility

**Steps:**
Run all Download Flow, Feedback, and Issue Report tests in Safari

**Expected Results:**
- ✅ All features functional
- ✅ Downloads work (Safari has stricter popup blocking)
- ✅ localStorage accessible
- ✅ Webkit-specific CSS renders correctly

**Pass/Fail:** Pass

**Notes:** Error in test case

---

#### Test Case 7.4: Edge (Latest)
**AC:** #10 - Cross-browser compatibility

**Steps:**
Run all Download Flow, Feedback, and Issue Report tests in Edge

**Expected Results:**
- ✅ All features functional
- ✅ Chromium-based Edge behaves like Chrome
- ✅ No Edge-specific issues

**Pass/Fail:** Pass

**Notes:** Error in test case

---

### Mobile Device Testing

#### Test Case 8.1: iOS (iPhone)
**AC:** #10 - Mobile device compatibility

**Steps:**
1. Open http://localhost:3000 on iPhone (use ngrok for remote testing if needed)
2. Navigate to `/jobs/{job_id}`
3. Test all interactions

**Expected Results:**
- ✅ Responsive layout: buttons stack vertically on mobile
- ✅ Download button tappable (adequate touch target size)
- ✅ Feedback widget readable and functional
- ✅ Issue Report modal renders full-screen or properly sized
- ✅ Form inputs accessible with iOS keyboard
- ✅ Confetti animation plays (if not reduced motion)

**Pass/Fail:** Not yet, can do later

**Notes:** ___________________________________________

---

#### Test Case 8.2: Android (Phone)
**AC:** #10 - Mobile device compatibility

**Steps:**
1. Open app on Android device
2. Test all interactions

**Expected Results:**
- ✅ Responsive layout works correctly
- ✅ Download triggers correctly (Android download manager)
- ✅ Material Design elements render properly
- ✅ No Android-specific bugs

**Pass/Fail:** Not yet, can do later

**Notes:** ___________________________________________

---

#### Test Case 8.3: iPad (Tablet)
**AC:** #10 - Tablet compatibility

**Steps:**
1. Open app on iPad
2. Test in both portrait and landscape orientations

**Expected Results:**
- ✅ Layout adapts to tablet size (uses `sm:` breakpoints)
- ✅ Buttons arrange horizontally in landscape
- ✅ Modal sized appropriately for tablet screen

**Pass/Fail:** Not yet, can do later

**Notes:** ___________________________________________

---

## Analytics Validation

### Test Case 9.1: Feedback Event Logged
**AC:** #7 - Analytics tracking

**Steps:**
1. Submit positive feedback (Test Case 3.1)
2. Query Supabase `conversion_events` table:
   ```sql
   SELECT * FROM conversion_events
   WHERE event_type LIKE 'feedback_%'
   ORDER BY created_at DESC
   LIMIT 10;
   ```

**Expected Results:**
- ✅ New row with `event_type = "feedback_positive"`
- ✅ `job_id` matches test job
- ✅ `user_id` matches logged-in user
- ✅ `event_data` contains: `{"rating": "positive", "has_comment": false}`
- ✅ `created_at` timestamp is current

**Pass/Fail:** Faill

**Notes:** Error: Failed to run sql query: ERROR: 42P01: relation "conversion_events" does not exist LINE 1: SELECT * FROM conversion_events ^

---

### Test Case 9.2: Issue Report Event Logged
**AC:** #7 - Analytics tracking

**Steps:**
1. Submit issue report (Test Case 4.2)
2. Query Supabase `conversion_events` table:
   ```sql
   SELECT * FROM conversion_events
   WHERE event_type = 'issue_reported'
   ORDER BY created_at DESC
   LIMIT 10;
   ```

**Expected Results:**
- ✅ New row with `event_type = "issue_reported"`
- ✅ `event_data` contains: `{"issue_type": "table_formatting", "has_page_number": true, "description_length": <length>}`

**Pass/Fail:** Fail  

**Notes:** Error: Failed to run sql query: ERROR: 42P01: relation "conversion_events" does not exist LINE 1: SELECT * FROM conversion_events ^

---

### Test Case 9.3: Download Event Tracking
**AC:** #7 - Download events tracked

**Current Status:** ⚠️ **KNOWN ISSUE - Not implemented**

**Steps:**
1. Download EPUB (Test Case 1.1)
2. Query `conversion_events` table for download event

**Expected Results (If Implemented):**
- ✅ New row with `event_type = "download"`
- ✅ Contains job_id, user_id, timestamp

**Actual Behavior:**
- ❌ No download event logged

**Pass/Fail:** FAIL (Expected - needs implementation)

**Notes:** Marked as MEDIUM severity action item

---

## Pre-Flight Checklist

### Services & Dependencies

- [ ] Backend API running on http://localhost:8000
- [ ] Frontend running on http://localhost:3000
- [ ] Supabase PostgreSQL accessible
- [ ] Supabase Storage accessible
- [ ] Redis running (Celery backend)
- [ ] Database migration `008_feedback_and_issues_tables.sql` applied
- [ ] All three tables exist: `job_feedback`, `job_issues`, `conversion_events`
- [ ] RLS policies enabled on all tables

### Data Flow

- [ ] Download button → GET `/api/v1/jobs/{job_id}/download` → Signed URL → Browser download
- [ ] Feedback widget → POST `/api/v1/jobs/{job_id}/feedback` → Database insert → Analytics event
- [ ] Issue modal → POST `/api/v1/jobs/{job_id}/issues` → Database insert → Analytics event
- [ ] Confetti triggered on download success, localStorage prevents duplicates

### Error Handling

- [ ] 404 (Job not found) displays error alert
- [ ] 403 (Unauthorized) displays access denied message
- [ ] Network timeouts show error toast with retry option
- [ ] API failures show user-friendly error messages
- [ ] Form validation prevents invalid submissions

### Testing

- [ ] Unit tests: FeedbackWidget component (or manual test completed)
- [ ] Unit tests: IssueReportModal component (or manual test completed)
- [ ] Unit tests: confetti-utils accessibility (or manual test completed)
- [ ] Integration tests: Download flow (manual test completed)
- [ ] Integration tests: Feedback API (manual test completed)
- [ ] Integration tests: Issue API (manual test completed)
- [ ] E2E tests: Full pipeline (deferred - noted in review)
- [ ] Accessibility tests: Keyboard nav (manual test completed)
- [ ] Accessibility tests: Screen reader (manual test completed)
- [ ] Cross-browser tests: Chrome, Firefox, Safari, Edge (completed)
- [ ] Mobile tests: iOS, Android (completed)

### Documentation

- [ ] Story file updated with Dev Notes
- [ ] File List section complete with all new/modified files
- [ ] Completion Notes documenting key decisions
- [ ] Senior Developer Review appended to story
- [ ] Manual testing guide created (this document)

---

## Test Results Template

### Summary

**Tester:** _____________
**Date:** _____________
**Environment:** Local Development / Staging / Production
**Browser:** _____________
**Device:** _____________

### Test Results

| Test Case | Result | Notes |
|-----------|--------|-------|
| 1.1 - Successful Download | ☐ Pass ☐ Fail |  |
| 1.2 - Download Disabled State | ☐ Pass ☐ Fail |  |
| 1.3 - Download 404 Error | ☐ Pass ☐ Fail |  |
| 1.4 - Download 403 Error | ☐ Pass ☐ Fail |  |
| 1.5 - Network Timeout | ☐ Pass ☐ Fail |  |
| 2.1 - Confetti First Download | ☐ Pass ☐ Fail |  |
| 2.2 - Confetti No Repeat | ☐ Pass ☐ Fail |  |
| 2.3 - Confetti Motion Sensitivity | ☐ Pass ☐ Fail |  |
| 3.1 - Positive Feedback | ☐ Pass ☐ Fail |  |
| 3.2 - Negative Feedback w/ Comment | ☐ Pass ☐ Fail |  |
| 3.3 - Feedback Error Handling | ☐ Pass ☐ Fail |  |
| 4.1 - Open Issue Modal | ☐ Pass ☐ Fail |  |
| 4.2 - Submit Valid Issue | ☐ Pass ☐ Fail |  |
| 4.3 - Validation Empty Desc | ☐ Pass ☐ Fail |  |
| 4.4 - Validation Short Desc | ☐ Pass ☐ Fail |  |
| 4.5 - All Issue Types | ☐ Pass ☐ Fail |  |
| 4.6 - Close/Cancel Modal | ☐ Pass ☐ Fail |  |
| 5.1 - Duplicate Prevention | ☐ Pass ☐ Fail ☑ Known Issue |  |
| 5.2 - Auth Expiry | ☐ Pass ☐ Fail |  |
| 6.1 - Keyboard Nav Download | ☐ Pass ☐ Fail |  |
| 6.2 - Keyboard Nav Feedback | ☐ Pass ☐ Fail |  |
| 6.3 - Keyboard Nav Modal | ☐ Pass ☐ Fail |  |
| 6.4 - Screen Reader VoiceOver | ☐ Pass ☐ Fail |  |
| 6.5 - Color Contrast | ☐ Pass ☐ Fail |  |
| 6.6 - ARIA Labels | ☐ Pass ☐ Fail |  |
| 7.1 - Chrome | ☐ Pass ☐ Fail |  |
| 7.2 - Firefox | ☐ Pass ☐ Fail |  |
| 7.3 - Safari | ☐ Pass ☐ Fail |  |
| 7.4 - Edge | ☐ Pass ☐ Fail |  |
| 8.1 - iOS iPhone | ☐ Pass ☐ Fail |  |
| 8.2 - Android Phone | ☐ Pass ☐ Fail |  |
| 8.3 - iPad Tablet | ☐ Pass ☐ Fail |  |
| 9.1 - Feedback Analytics | ☐ Pass ☐ Fail |  |
| 9.2 - Issue Analytics | ☐ Pass ☐ Fail |  |
| 9.3 - Download Analytics | ☐ Pass ☐ Fail ☑ Known Issue |  |

### Overall Assessment

**Total Tests:** 33
**Passed:** ___
**Failed:** ___
**Known Issues (Expected):** 2
**Blockers:** ___

**Recommendation:** ☐ Approve for Production ☐ Changes Required ☐ Needs Further Testing

**Critical Issues Found:**
_____________________________________________________________________________

**Notes:**
_____________________________________________________________________________

---

## Appendix: Known Issues

### Issue 1: Duplicate Feedback Prevention Not Implemented
- **Severity:** MEDIUM
- **AC:** #10
- **Status:** Documented in code review, action item created
- **Workaround:** None - feature missing
- **Plan:** Implement in follow-up story or this story's revision

### Issue 2: Download Event Tracking Missing
- **Severity:** MEDIUM
- **AC:** #7
- **Status:** Documented in code review, action item created
- **Workaround:** None - feature missing
- **Plan:** Add analytics call in `page.tsx:78` after successful download

### Issue 3: E2E Integration Tests Deferred
- **Severity:** HIGH (for production readiness)
- **AC:** #8
- **Status:** Deferred due to cost ($50/month AI API budget)
- **Workaround:** Manual testing with real PDFs
- **Plan:** Implement in separate testing story with budget allocation

---

**End of Manual Testing Guide**
