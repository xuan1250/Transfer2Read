# Story 2.2: Frontend Supabase Auth UI

Status: ready-for-dev

## Story

As a **User**,
I want **to sign up and log in using Supabase-powered authentication**,
So that **I can securely access my account.**

### Context Reference

- docs/sprint-artifacts/2-2-frontend-supabase-auth-ui.context.xml

## Acceptance Criteria

1. **Login Page** (`/login`) created with:
   - Email and Password input fields (shadcn/ui components)
   - "Sign In" button triggers `supabase.auth.signInWithPassword()`
   - Error handling: Display auth errors ("Invalid credentials", "Email not confirmed")
   - "Forgot Password?" link (UI only for now)

2. **Registration Page** (`/register`) created with:
   - Email and Password fields with validation (Zod + React Hook Form)
   - Password strength indicator
   - "Sign Up" button triggers `supabase.auth.signUp()`
   - Success message: "Check your email to confirm your account"

3. **Auth State Management:**
   - `useUser` hook created using `@supabase/auth-helpers-nextjs`
   - Protected routes redirect to `/login` if not authenticated
   - Successful login redirects to `/dashboard`

4. **Styling:** Professional Blue theme applied (shadcn/ui Card, Input, Button)

## Tasks / Subtasks

- [ ] Task 1: Set up Supabase client and auth hooks (AC: #3)
  - [ ] 1.1: Verify `@supabase/supabase-js@2.46.1` and `@supabase/auth-helpers-nextjs` installed
  - [ ] 1.2: Create `frontend/src/lib/supabase/client.ts` with browser client:
    - Export `createClientComponentClient()` for client components
    - Export `createServerComponentClient()` for server components
  - [ ] 1.3: Create `frontend/src/lib/supabase/server.ts` for server-side auth:
    - Export `createServerClient()` using cookies
  - [ ] 1.4: Create `frontend/src/hooks/useUser.ts` custom hook:
    - Use `useEffect` to listen to `supabase.auth.onAuthStateChange()`
    - Return `{ user, loading, signOut }` interface
  - [ ] 1.5: Test hook by rendering in simple test component

- [ ] Task 2: Create authentication pages with shadcn/ui (AC: #1, #2, #4)
  - [ ] 2.1: Install required shadcn/ui components:
    - `npx shadcn-ui@latest add button card input label`
    - `npm install react-hook-form zod @hookform/resolvers`
  - [ ] 2.2: Create `/app/login/page.tsx`:
    - Centered Card layout with Professional Blue styling
    - Email + Password input fields (shadcn/ui Input)
    - "Sign In" button (shadcn/ui Button variant="default")
    - "Forgot Password?" link (text-sm, text-blue-600)
    - "Don't have an account? Sign Up" link to `/register`
  - [ ] 2.3: Create `/app/register/page.tsx`:
    - Similar Card layout to login page
    - Email + Password + Confirm Password fields
    - Password strength indicator component (custom or use zxcvbn)
    - "Sign Up" button
    - "Already have an account? Login" link to `/login`
  - [ ] 2.4: Create `frontend/src/components/auth/PasswordStrengthIndicator.tsx`:
    - Visual bar showing weak/medium/strong
    - Color coded: red (weak), yellow (medium), green (strong)
    - Criteria display: length, uppercase, number, special char

- [ ] Task 3: Implement login form logic (AC: #1)
  - [ ] 3.1: Add React Hook Form to `/app/login/page.tsx`:
    - Use `useForm` with Zod resolver
    - Schema: email (valid format), password (min 8 chars)
  - [ ] 3.2: Implement `onSubmit` handler:
    - Call `supabase.auth.signInWithPassword({ email, password })`
    - Handle success: router.push('/dashboard')
    - Handle error: display error message below form (using Alert component)
  - [ ] 3.3: Error message handling:
    - "Invalid login credentials" → "Email or password is incorrect"
    - "Email not confirmed" → "Please check your email and confirm your account"
    - Network errors → "Unable to connect. Please try again."
  - [ ] 3.4: Add loading state during sign-in (disable button, show spinner)

- [ ] Task 4: Implement registration form logic (AC: #2)
  - [ ] 4.1: Add React Hook Form to `/app/register/page.tsx`:
    - Zod schema: email, password (min 8 chars, 1 uppercase, 1 number), confirmPassword
    - Validate password === confirmPassword
  - [ ] 4.2: Integrate PasswordStrengthIndicator:
    - Update as user types password
    - Block submission if password is "weak"
  - [ ] 4.3: Implement `onSubmit` handler:
    - Call `supabase.auth.signUp({ email, password })`
    - Handle success: show success message "Check your email to confirm your account"
    - Display email sent confirmation UI (not redirect yet)
  - [ ] 4.4: Error handling:
    - "User already registered" → "This email is already registered. Try logging in?"
    - Weak password → "Password must be at least 8 characters with uppercase and number"

- [ ] Task 5: Implement auth state management and route protection (AC: #3)
  - [ ] 5.1: Create `frontend/src/components/auth/AuthGuard.tsx` HOC:
    - Use `useUser()` hook
    - If `loading === true`, show loading spinner
    - If `user === null`, redirect to `/login` using Next.js redirect
    - If authenticated, render children
  - [ ] 5.2: Create `/app/dashboard/page.tsx` placeholder:
    - Wrap content with `<AuthGuard>`
    - Display "Welcome, {user.email}" message
    - Add "Sign Out" button
  - [ ] 5.3: Implement sign-out functionality:
    - Call `supabase.auth.signOut()`
    - Redirect to `/login` after sign-out
  - [ ] 5.4: Test protected route behavior:
    - Navigate to `/dashboard` while logged out → redirects to `/login`
    - Login successfully → redirects to `/dashboard`
    - Sign out → redirects to `/login`

- [ ] Task 6: Apply Professional Blue theme styling (AC: #4)
  - [ ] 6.1: Verify `tailwind.config.ts` has Professional Blue theme colors:
    - Primary: `#2563eb`, Secondary: `#64748b`, Accent: `#0ea5e9`
    - Success: `#10b981`, Warning: `#f59e0b`, Error: `#ef4444`
  - [ ] 6.2: Style login/register pages:
    - Centered layout with max-width container
    - Card shadow and rounded corners
    - Button uses `bg-blue-600 hover:bg-blue-700`
    - Input focus ring using `focus:ring-blue-500`
  - [ ] 6.3: Add responsive design:
    - Mobile: full-width card with padding
    - Desktop: fixed-width centered card (max-w-md)

- [ ] Task 7: Manual testing and integration verification (AC: #1, #2, #3)
  - [ ] 7.1: Test new user registration flow:
    - Submit /register form with valid email
    - Verify "Check your email" message appears
    - Check Supabase dashboard for new user (status: unconfirmed)
  - [ ] 7.2: Test email confirmation (if available):
    - Click confirmation link in email
    - Verify redirect to app with confirmed status
  - [ ] 7.3: Test login flow with confirmed user:
    - Enter valid credentials on /login
    - Verify redirect to /dashboard
    - Verify user email displayed
  - [ ] 7.4: Test error scenarios:
    - Invalid email format → validation error
    - Wrong password → "Invalid credentials" error
    - Unconfirmed email login → "Email not confirmed" error
    - Weak password on registration → blocked submission
  - [ ] 7.5: Test sign-out flow:
    - Click sign-out button on /dashboard
    - Verify redirect to /login
    - Verify cannot access /dashboard without login

## Dev Notes

### Architecture Context

**Frontend Auth Flow (from Architecture):**
- Use `createClientComponentClient()` for browser-side auth actions (login, signup, signout)
- Use `createServerComponentClient()` for server-side session checks (future use)
- JWT tokens automatically stored in cookies by Supabase Auth Helpers
- Session persists across page refreshes via localStorage

**Supabase Client Types:**
- **Browser Client:** For client components, includes realtime subscriptions
- **Server Client:** For server components and API routes, uses cookies for auth

**Security Considerations:**
- Use HTTPS only (enforced by Supabase)
- Never expose `SUPABASE_SERVICE_KEY` in frontend
- Use `NEXT_PUBLIC_SUPABASE_ANON_KEY` (safe to expose)

### Project Structure Notes

**Files to Create:**
```
frontend/
├── src/
│   ├── app/
│   │   ├── login/
│   │   │   └── page.tsx                    # NEW: Login page
│   │   ├── register/
│   │   │   └── page.tsx                    # NEW: Registration page
│   │   └── dashboard/
│   │       └── page.tsx                    # NEW: Protected dashboard placeholder
│   ├── components/
│   │   ├── auth/
│   │   │   ├── AuthGuard.tsx               # NEW: Protected route HOC
│   │   │   └── PasswordStrengthIndicator.tsx  # NEW: Password strength UI
│   │   └── ui/                             # shadcn/ui components (auto-generated)
│   ├── hooks/
│   │   └── useUser.ts                      # NEW: Auth state hook
│   └── lib/
│       └── supabase/
│           ├── client.ts                   # NEW: Browser Supabase client
│           └── server.ts                   # NEW: Server Supabase client
```

**Dependencies to Verify/Add:**
- `@supabase/supabase-js@2.46.1` (should exist from Story 1.3)
- `@supabase/auth-helpers-nextjs` (should exist from Story 1.3)
- `react-hook-form@7.x`
- `zod@3.x`
- `@hookform/resolvers@3.x`

### UX Design Alignment

**From UX Spec Section 4:**
- **Professional Blue Theme:** Primary button `bg-blue-600`, hover `bg-blue-700`
- **Clean, Minimal Forms:** White cards on light gray background
- **Typography:** System fonts, clear hierarchy
- **Spacing:** Consistent padding (p-6 for cards, mb-4 for form fields)

**Form Best Practices:**
- Autofocus email field on page load
- Show validation errors inline (below fields)
- Disable submit button while loading
- Clear, actionable error messages

### References

- [Source: docs/architecture.md#Supabase-Client-Setup] - Client initialization patterns
- [Source: docs/architecture.md#Security-Architecture] - Auth security requirements
- [Source: docs/sprint-artifacts/tech-spec-epic-2.md#Frontend-Auth-Actions] - Supabase method reference
- [Source: docs/epics.md#Story-2.2] - Original acceptance criteria
- [Supabase Auth UI](https://supabase.com/docs/guides/auth/auth-helpers/nextjs) - Next.js integration guide
- [shadcn/ui Forms](https://ui.shadcn.com/docs/components/form) - Form component examples

### Learnings from Previous Story

**From Story 2-1-supabase-authentication-setup (Status: done):**

- **Supabase Auth Configuration Complete:**
  - Email/Password provider enabled in Supabase dashboard
  - Email confirmation required (users must verify email via magic link)
  - JWT tokens configured with 1-hour access, 7-day refresh (Supabase defaults)
  - **Action:** Frontend signup will trigger confirmation email automatically

- **User Metadata Structure:**
  - New users automatically get `tier: FREE` via Supabase trigger
  - Stored in `auth.users.raw_user_meta_data.tier`
  - **Action:** Can display tier in UI after login (Story 2.5)

- **Backend Auth Middleware Ready:**
  - `POST /auth/test-protected` endpoint available for testing JWT flow
  - Backend validates Supabase JWT tokens
  - **Action:** Can test full auth flow (frontend login → backend API call) to verify integration

- **Testing Guidance:**
  - Test users can be created in Supabase dashboard for development
  - Email confirmation can be bypassed in development (Supabase → Auth → Settings → "Confirm email" toggle)
  - **Recommendation:** Keep email confirmation enabled to match production behavior

- **SQL Artifacts Created:**
  - `conversion_jobs` table with RLS policies exists
  - Users isolated by `auth.uid() = user_id` policy
  - **Note:** RLS will automatically work once user logs in via frontend

- **Environment Variables Confirmed:**
  - `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` should already be in `frontend/.env.local` (from Story 1.3)
  - **Action:** Verify these are set before starting frontend development

- **CORS Configuration:**
  - Production domain `https://transfer2read.vercel.app` already in backend allowed origins
  - **Note:** Frontend auth will work for both local dev and production

[Source: docs/sprint-artifacts/2-1-supabase-authentication-setup.md#Dev-Agent-Record]

### Testing Strategy

**Component Tests (Vitest + React Testing Library):**
- Test LoginPage form validation (invalid email, missing password)
- Test RegisterPage password strength validation
- Test PasswordStrengthIndicator component rendering
- Test useUser hook auth state changes

**Integration Tests (Manual):**
1. Full signup flow: register → receive email → confirm → login
2. Login with valid credentials → dashboard redirect
3. Login with invalid credentials → error message
4. Access protected route without auth → login redirect
5. Sign out → login redirect

**Accessibility Tests:**
- Keyboard navigation works (Tab through forms)
- Labels properly associated with inputs
- Error messages announced to screen readers
- Focus management on page load

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

## Change Log

- **2025-12-11 (Draft):** Story created from Epic 2 requirements, incorporates learnings from Story 2.1
