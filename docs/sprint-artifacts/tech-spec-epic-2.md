# Epic Technical Specification: User Identity & Account Management

Date: 2025-12-11
Author: xavier
Epic ID: 2
Status: Draft

---

## Overview

Epic 2 establishes the complete user identity and authentication system for Transfer2Read using Supabase as the unified backend platform. This epic implements secure user registration, login (including social authentication), password management, and profile/tier visibility. Upon completion, users will be able to create accounts, securely access the platform, manage their credentials, and understand their subscription tier - laying the foundation for all subsequent user-facing features.

This epic covers **7 Functional Requirements (FR1-FR7)** and represents a critical prerequisite for all user-specific functionality including file uploads, conversion history, and usage tracking.

## Objectives and Scope

### Objectives
1. Enable secure user registration via email/password
2. Enable secure user registration and login via social providers (Google, GitHub)
3. Implement Supabase-based authentication with JWT token validation
4. Provide password reset/recovery functionality
5. Display user profile information and subscription tier

### In Scope
- Supabase Auth configuration (Email/Password, Google OAuth, GitHub OAuth)
- Backend authentication middleware for JWT validation
- Frontend authentication UI (Login, Register, Forgot Password, Reset Password)
- User profile page with tier display
- Row Level Security (RLS) policies for user data isolation
- `user_metadata` extension for tier storage

### Out of Scope
- Payment processing and actual subscription upgrades (stub UI only)
- Email/password verification customization (using Supabase defaults)
- Advanced security features (MFA, session management beyond Supabase defaults)
- Admin user management

## System Architecture Alignment

### Components Referenced
| Component | Role | Source |
|-----------|------|--------|
| **Supabase Auth** | Managed authentication service | Architecture ADR-002 |
| **Supabase PostgreSQL** | User metadata storage, RLS enforcement | Architecture ADR-002 |
| **Next.js 15 Frontend** | Auth UI pages and state management | Architecture Section: Project Structure |
| **FastAPI Backend** | JWT validation middleware, protected routes | Architecture Section: Security Architecture |

### Architecture Constraints
- **Architecture ADR-002:** Use Supabase as unified backend platform for auth, database, and storage
- **Security NFR12:** Passwords hashed using bcrypt (handled by Supabase)
- **Security NFR13:** JWT tokens with configurable expiry (managed by Supabase)
- **Security NFR15:** OAuth 2.0 standards for social authentication

### Technology Stack (Epic 2 Specific)
- `@supabase/supabase-js@2.46.1` - Frontend auth client
- `@supabase/auth-helpers-nextjs` - Next.js App Router integration
- `supabase-py@2.24.0` - Backend auth verification
- shadcn/ui components - Auth form UI

## Detailed Design

### Services and Modules

| Service/Module | Responsibility | Location |
|----------------|----------------|----------|
| **Supabase Auth Client (Frontend)** | Handle signup, signin, signout, OAuth flows | `frontend/src/lib/supabase.ts` |
| **useUser Hook** | React hook for auth state management | `frontend/src/hooks/useUser.ts` |
| **Auth Middleware (Backend)** | Validate Supabase JWT tokens, extract user_id | `backend/app/core/auth.py` |
| **Protected Route HOC** | Wrap pages requiring authentication | `frontend/src/components/auth/AuthGuard.tsx` |

### Data Models and Contracts

**Supabase `auth.users` Extension (via `raw_user_meta_data`):**

```sql
-- User metadata stored in auth.users.raw_user_meta_data
{
  "tier": "FREE" | "PRO" | "PREMIUM",  -- Default: "FREE"
  "created_at": "ISO timestamp",
  "updated_at": "ISO timestamp"
}
```

**RLS Policies for `conversion_jobs` (already created in Epic 1):**

```sql
-- Users can only access their own jobs
CREATE POLICY "Users can access own jobs" ON conversion_jobs
  FOR ALL USING (auth.uid() = user_id);
```

**TypeScript Types:**

```typescript
// frontend/src/types/auth.ts
export type SubscriptionTier = 'FREE' | 'PRO' | 'PREMIUM';

export interface UserProfile {
  id: string;
  email: string;
  tier: SubscriptionTier;
  createdAt: string;
  provider?: 'email' | 'google' | 'github';
}
```

**Pydantic Schemas (Backend):**

```python
# backend/app/schemas/auth.py
from enum import Enum
from pydantic import BaseModel

class SubscriptionTier(str, Enum):
    FREE = "FREE"
    PRO = "PRO"
    PREMIUM = "PREMIUM"

class AuthenticatedUser(BaseModel):
    user_id: str
    email: str
    tier: SubscriptionTier
```

### APIs and Interfaces

**Backend Auth Endpoints:**

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `POST` | `/auth/test-protected` | Test endpoint returning user_id from JWT | ✅ Yes |

**Auth Middleware Dependency:**

```python
# backend/app/core/auth.py
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())
) -> AuthenticatedUser:
    """Extract and validate user from Supabase JWT token."""
    # Validate JWT using Supabase service client
    # Return AuthenticatedUser or raise 401
```

**Frontend Auth Actions:**

| Action | Supabase Method | Usage |
|--------|-----------------|-------|
| Sign Up | `supabase.auth.signUp({ email, password })` | `/register` page |
| Sign In | `supabase.auth.signInWithPassword({ email, password })` | `/login` page |
| Social Login | `supabase.auth.signInWithOAuth({ provider })` | Google/GitHub buttons |
| Sign Out | `supabase.auth.signOut()` | TopBar user menu |
| Reset Password Request | `supabase.auth.resetPasswordForEmail(email)` | `/forgot-password` |
| Update Password | `supabase.auth.updateUser({ password })` | `/reset-password` |
| Get User | `supabase.auth.getUser()` | `useUser` hook |

### Workflows and Sequencing

**Authentication Flow:**

```
1. User visits /login or /register
2. Frontend validates form inputs (Zod + React Hook Form)
3. Frontend calls Supabase Auth method
4. Supabase validates credentials and returns JWT + user object
5. Frontend stores session in browser (handled by Supabase client)
6. Frontend redirects to /dashboard
7. Subsequent API calls include JWT in Authorization header
8. Backend middleware validates JWT and extracts user_id
```

**OAuth Flow:**

```
1. User clicks "Sign in with Google/GitHub"
2. Frontend calls supabase.auth.signInWithOAuth({ provider: 'google' })
3. Browser redirects to provider's OAuth consent screen
4. User authorizes application
5. Provider redirects to /auth/callback with token
6. Supabase exchanges token and creates/updates user
7. Frontend receives session and redirects to /dashboard
```

**Password Reset Flow:**

```
1. User clicks "Forgot Password" on /login
2. User enters email on /forgot-password
3. Frontend calls supabase.auth.resetPasswordForEmail(email)
4. Supabase sends magic link email
5. User clicks link → opens /reset-password with token
6. User enters new password
7. Frontend calls supabase.auth.updateUser({ password })
8. User redirected to /login with success message
```

## Non-Functional Requirements

### Performance

| Metric | Target | Notes |
|--------|--------|-------|
| Auth API response time | < 200ms | Supabase edge network |
| Token validation time | < 50ms | Backend JWT verification |
| Page load (auth pages) | < 1s | Optimized form components |

### Security

| Requirement | Implementation |
|-------------|----------------|
| **NFR12: Password hashing** | Supabase uses bcrypt with secure rounds |
| **NFR13: Session expiry** | JWT tokens expire after Supabase-configured period |
| **NFR15: OAuth 2.0 standards** | Supabase implements OAuth 2.0 for Google/GitHub |
| **NFR17: Input validation** | Zod schemas validate all form inputs |
| HTTPS only | Supabase enforces HTTPS for all auth endpoints |
| CSRF protection | Supabase Auth Helpers handle CSRF tokens |

### Reliability/Availability

| Aspect | Guarantee |
|--------|-----------|
| Supabase Auth uptime | 99.9% SLA |
| Fallback | Graceful error messages on auth failures |
| Session persistence | Browser local storage maintains session across refreshes |

### Observability

| Signal | Implementation |
|--------|----------------|
| Auth failures | Log failed login attempts (no PII) |
| OAuth errors | Log provider errors for debugging |
| Backend middleware | Log JWT validation failures |

## Dependencies and Integrations

### External Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| `@supabase/supabase-js` | 2.46.1 | Frontend Supabase client |
| `@supabase/auth-helpers-nextjs` | Latest | Next.js App Router auth helpers |
| `supabase` (Python) | 2.24.0 | Backend Supabase admin client |
| `react-hook-form` | 7.x | Form state management |
| `zod` | 3.x | Schema validation |
| `@hookform/resolvers` | 3.x | Zod + React Hook Form integration |

### Integration Points

| System | Integration Type | Notes |
|--------|-----------------|-------|
| **Supabase Auth** | Primary auth provider | Email, Google, GitHub |
| **Supabase PostgreSQL** | User metadata storage | RLS for data isolation |
| **Google Cloud Console** | OAuth client credentials | Requires Google Cloud project |
| **GitHub Developer Settings** | OAuth app credentials | Requires GitHub OAuth app |

## Acceptance Criteria (Authoritative)

### From PRD Functional Requirements

| AC# | FR | Acceptance Criteria | Testable Condition |
|-----|----|--------------------|-------------------|
| AC1 | FR1 | Users can create accounts using email/password | Given valid email and password, when signup submitted, then account created and confirmation email sent |
| AC2 | FR2 | Users can create accounts using Google or GitHub | When user clicks social login button, then OAuth flow completes and account created |
| AC3 | FR3 | Users can log in securely | Given valid credentials, when login submitted, then user redirected to dashboard with valid session |
| AC4 | FR4 | Users can reset forgotten passwords | Given registered email, when reset requested, then magic link email sent and password can be changed |
| AC5 | FR5 | Users can view account profile | When user visits /settings, then email and tier displayed |
| AC6 | FR6 | Users can see current subscription tier | When user logged in, then tier badge visible in TopBar |
| AC7 | FR7 | Users see upgrade path | When Free tier user visits settings, then "Upgrade" button visible |

### Additional Technical Acceptance Criteria

| AC# | Criteria | Testable Condition |
|-----|----------|-------------------|
| AC8 | Backend validates Supabase JWT | Given valid JWT, when protected endpoint called, then user_id extracted and returned |
| AC9 | Invalid JWT rejected | Given expired/malformed JWT, when protected endpoint called, then 401 Unauthorized returned |
| AC10 | RLS enforces user isolation | Given user A and user B, when user A queries, then only user A's data returned |

## Traceability Mapping

| AC | Spec Section | Component(s)/API(s) | Test Approach |
|----|--------------|---------------------|---------------|
| AC1 | Supabase Auth Setup | `/register`, `supabase.auth.signUp()` | Integration test: submit form, verify user created |
| AC2 | Social Authentication | `/login`, OAuth buttons | Manual test: complete OAuth flow |
| AC3 | Frontend Supabase Auth UI | `/login`, `supabase.auth.signInWithPassword()` | Integration test: login with valid credentials |
| AC4 | Password Reset & User Profile | `/forgot-password`, `/reset-password` | Manual test: email flow |
| AC5 | Password Reset & User Profile | `/settings` page | Integration test: verify profile data displayed |
| AC6 | Subscription Tier Display | TopBar, `user_metadata.tier` | Integration test: verify tier badge |
| AC7 | Subscription Tier Display | `/settings`, "Upgrade" button | UI test: verify button visibility for FREE tier |
| AC8 | Auth Middleware | `backend/app/core/auth.py` | Unit test: mock JWT, verify extraction |
| AC9 | Auth Middleware | `backend/app/core/auth.py` | Unit test: invalid JWT returns 401 |
| AC10 | RLS Policies | Supabase PostgreSQL | Integration test: cross-user query fails |

## Risks, Assumptions, Open Questions

### Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **OAuth provider configuration complexity** | Medium | Low | Detailed setup instructions in story |
| **Email deliverability issues** | Low | Medium | Use Supabase default email service for MVP, upgrade later |
| **Session management edge cases** | Low | Low | Rely on battle-tested Supabase Auth Helpers |

### Assumptions

1. Supabase free tier is sufficient for development and initial production
2. Supabase Auth email templates are acceptable for MVP
3. Users will have access to Google or GitHub accounts for social login
4. JWT token expiry defaults from Supabase are acceptable

### Open Questions

1. **Email branding:** Should we customize Supabase email templates for Transfer2Read branding?
   - **Recommendation:** Use defaults for MVP, customize post-launch
2. **Session duration:** What should the JWT token expiry be?
   - **Recommendation:** Use Supabase default (1 hour access, 7 day refresh)
3. **Rate limiting:** Should we implement login attempt rate limiting?
   - **Recommendation:** Supabase has built-in rate limiting, sufficient for MVP

## Test Strategy Summary

### Automated Tests

**Backend (Pytest):**
- Unit tests for JWT validation middleware
- Unit tests for AuthenticatedUser extraction
- Integration tests for protected endpoint behavior

**Frontend (Vitest + React Testing Library):**
- Unit tests for form validation (Zod schemas)
- Component tests for login/register forms
- Integration tests for auth state management (useUser hook)

### Manual Verification

**Story 2.1 (Supabase Auth Setup):**
- Verify Supabase dashboard shows Email/Password provider enabled
- Verify RLS policies in Supabase SQL editor

**Story 2.2 (Frontend Auth UI):**
- Complete signup flow with new email
- Complete login flow with existing user
- Verify redirect to /dashboard after login

**Story 2.3 (Social Auth):**
- Complete Google OAuth flow end-to-end
- Complete GitHub OAuth flow end-to-end
- Verify new user created with FREE tier

**Story 2.4 (Password Reset):**
- Request password reset email
- Click magic link and set new password
- Verify login with new password works

**Story 2.5 (Tier Display):**
- Verify tier badge shows in TopBar
- Verify Upgrade button visible for FREE users
