---
title: ForKhatri Single Source of Truth - Architecture Rework Analysis
date: 2026-09-14
status: Complete Research Report
---

# ForKhatri Single Source of Truth Architecture Rework

## Executive Summary

ForKhatri was architected as a **7-module platform ecosystem** (Vyapar, Milavn, Mangaly, Counsel, Dashboard, Payment Services, Loans & Finance). The design already mandates a **single Identity & Trust Service** as the source of truth for all authentication and member identity. 

**Current problem:** The auth layer is **designed but not built**. Mangaly currently has its own custom login/auth implementation that violates the architecture. Your vision to consolidate this into **"one ForKhatri app with one user identity, modules listed and discoverable"** aligns with the already-sealed architecture — it just needs to be **properly built and wired**.

---

## Current State vs. Target State

### Current Architecture (Today)
- **Seven modules designed, three being implemented** (Vyapar, Milavn, Mangaly)
- **Scattered auth state:**
  - Mangaly: **has custom login/auth built** (diverges from architecture) ❌
  - Vyapar: Design specs sealed; auth to be built per architecture ✅
  - Milavn: Design specs sealed; auth to be built per architecture ✅
  - Four other modules: planned (Counsel, Dashboard, Payment Services, Loans & Finance)
- **Architecture decision made:** All modules should use Identity & Trust Service (ADR-004) — **this is already the target design** ✅
- **Auth service status:** Designed but not implemented (still in "planned" state)

### Target Architecture (Your Vision)
- **One unified ForKhatri application**
- **One user identity** across the entire platform
- **Module discovery & navigation** from user's main dashboard/home
- **Single source of truth** for authentication and identity
- **Per-user module access** - users can navigate between available modules

---

---

## What's Already Decided (You Don't Need to Re-Litigate)

These are sealed architectural decisions from `/ARCHITECTURE.md`. They form the **baseline for this rework:**

✅ **Identity & Trust Service as sole identity source** (ADR-004): Every module authenticates through one service, using OAuth2/OIDC + short-lived JWTs. This is already the target.

✅ **No module builds its own login** (architecture decision, already in sealed BRs): 
- Vyapar: "authentication single source of truth = parent ForKhatri platform; Vyapar owns no login/signup/session/credential"
- Mangaly: "does not handle login/signup itself"
- Milavn: Implicit same pattern

✅ **Schema-per-module, no cross-container database sharing** (ADR-002): Each module owns its schema; no module duplicates another's auth tables.

✅ **Reputation is context-aware** (ADR-005): "A person trusted professionally is not automatically trusted matrimonially" — reputation scoring lives in Identity & Trust Service, reads each module's feedback.

✅ **Authorization as structural chokepoint** (Module Architecture Standard, §5): Every module must route data access through an authorization component, never a convention.

✅ **Modular monolith for low-regulatory modules, isolated containers for sensitive ones** (ADR-001): 
- Core Platform monolith: Vyapar, Milavn, Dashboard, Counsel
- Isolated: Mangaly (privacy), Loans & Finance (regulatory), Payment Services (money)

---

## Major Changes Required

### 1. **Identity & Authentication Layer** 🔴 CRITICAL — BLOCKING ALL OTHER MODULES

#### Current state:
- `Identity & Trust Service` designed in `/ARCHITECTURE.md` (ADR-004) but **not yet built**
- Mangaly has **custom login/auth implementation** that breaks architecture (must be removed)
  - Custom OTP flow
  - Custom member table
  - Custom session management
- Vyapar and Milavn: no auth code built (correctly waiting for platform to provide it)

#### What must happen (IN THIS ORDER):

**Phase 1: Build/Deploy Identity & Trust Service** (if not already done externally)
- Endpoint: `POST /login/send-otp` (sends OTP via SMS/Email)
- Endpoint: `POST /login/verify-otp` (issues JWT on successful OTP verification)
- Endpoint: `GET /me` (returns authenticated user's member record)
- Database: `IdentityDB` (Postgres, isolated) containing:
  - `member` table (single source of all users)
  - `credential` table (auth credentials, password hashes if needed)
  - `member_trust_level` table (reputation scores)
  - `verified_credential` table (professional licenses, KYC docs)
- Auth model: OAuth2/OIDC + short-lived JWTs (15-30 min expiry) + refresh tokens
- Support actor classes:
  - Member (consumer)
  - Professional/Expert (Vyapar/Counsel)
  - Organizer (Milavn)
  - Merchant (Payment Services)
  - Platform Admin

**Phase 2: Remove Mangaly's custom auth** (breaking change)
- **Delete from Mangaly's code:**
  - Login/signup endpoints (`POST /auth/login`, `POST /auth/signup`, etc.)
  - OTP verification logic
  - Session token generation
  - Custom `member` table and auth schema
  - Password/credential storage
- **Add to Mangaly's code:**
  - Middleware to validate JWT from platform (check token signature, expiry)
  - Middleware to extract `member_id` from JWT claim
  - Authorization component that checks: "Is this user allowed in Mangaly?" (module-access check)
  - Authorization component that checks: "Can this member see/act on this matrimonial entity?" (domain-specific)
  
**Phase 3: Wire Vyapar and Milavn to Identity & Trust Service**
- Same pattern as Mangaly above (no custom auth, just JWT validation + authorization checks)

**Phase 4: Consolidate frontend auth**
- One login screen for entire platform (not per-module)
- Upon successful OTP, user gets a platform-wide JWT
- All module UIs in the same app use the same session cookie/localStorage token
- User is already authenticated when navigating between modules

#### Key architectural constraint (from ADR-004):
- Identity & Trust Service is **the single point of failure for authentication**
- Requires 99.9% uptime SLA (higher than individual modules' 99.5%)
- Must be built for high availability from day one (load balancing, replication)
- No module ever bypasses it or caches identity decisions beyond short JWT TTL

#### Known implementation gotchas:
- **RLS + Connection Pooling** (from MODULE-ARCHITECTURE-STANDARD.md §4):
  - If using Postgres RLS for Mangaly's sensitive data: app must connect as **non-owning role**, not schema owner
  - Authorization context must use `SET LOCAL` (transaction-scoped), not `SET` (session-scoped), to avoid leakage under PgBouncer transaction mode
- **Idempotent endpoints** (§4b): OTP send/verify must be idempotent — repeated OTP requests must return same result, not create duplicate credentials

---

### 2. **User-to-Module Relationship & Module Registry** 🔴 CRITICAL

#### What exists today:
- Each module is built as a standalone feature
- No concept of "which modules can a user access"
- No module listing/discovery for users

#### What needs to happen:
- **Modules become features within ForKhatri**
- **Add `user_module_access` / `user_module_permissions` table** to track:
  - Which modules a user has access to
  - User's role within each module (member, professional, organizer)
  - Subscription/permission status per module
  
- **Create unified module registry** containing:
  - Module metadata (name, description, icon, etc.)
  - Module availability/status
  - Module versioning
  
- **User sees:**
  - Home dashboard showing all modules they can access
  - Module tiles/cards to enter each module
  - Module-specific branding but consistent platform chrome
  
- **Each module receives:**
  - Authenticated user context (from Identity & Trust Service)
  - Module-specific access check (via user_module_access table)
  - Pre-resolved authorization context (avoid each module re-checking access)

---

### 3. **Database Architecture** 🟡 MAJOR

#### Current:
- Core Platform DB: `vyapar`, `milavn`, `dashboard`, `counsel` schemas
- Mangaly DB: Isolated database with its own auth tables
- Identity DB: Empty/not yet built

#### Changes needed:
- **Identity/Trust DB** must contain:
  - `member` table (single source of all users)
  - `identity` / `credential` tables
  - `member_trust_level` (reputation)
  - ❌ **REMOVE** auth-related tables from Mangaly DB
  - ❌ **REMOVE** any auth tables from Core Platform DB

- **Core Platform DB** needs new schema:
  - Add `platform` schema for cross-module metadata:
    - `modules` table (registry of available modules)
    - `user_module_access` table (which users can access which modules)
    - `user_module_roles` / `user_module_permissions` (per-module roles)

- **Per-module databases** stay isolated but:
  - ❌ Remove duplicate user/member tables
  - ✅ Keep only module-specific data
  - ✅ Reference `member_id` from Identity DB (foreign key, read-only)

---

### 4. **Frontend Architecture** 🟡 MAJOR

#### Current:
- Each module has its own web app (separate React apps)
- Each has login screen, session management
- Ports: Vyapar 3001, Milavn 3001, Mangaly 3001

#### Changes needed:
- **One unified ForKhatri web app** (single React app):
  - Main entry point (login)
  - Home/dashboard showing module tiles
  - Sub-routes for each module (`/vyapar/*`, `/milavn/*`, `/mangaly/*`)
  
- **Shared frontend infrastructure:**
  - Unified session/auth context (shared across modules)
  - One localStorage for session token
  - One header with notifications, profile, module switcher
  - Consistent navigation patterns
  
- **Per-module UI remains:**
  - Module-specific features and UX preserved
  - Just wrapped in the unified shell

---

### 5. **API Layer** 🟡 MAJOR

#### Current:
- Each module has separate API server
- Vyapar API: 8001, Milavn API: 8001, Mangaly API: 8001

#### Changes needed:
- **One unified API gateway** or **unified backend service** that:
  - Handles all authentication (delegates to Identity & Trust)
  - Routes requests to appropriate module service
  - Enforces module-access checks
  - Provides module registry endpoints
  
- **Option A - API Gateway pattern:**
  - Kong, Traefik, or similar
  - Sits in front of module services
  - Centralizes auth/module-access logic
  - Pros: Loose coupling, modules stay separate
  - Cons: Extra infrastructure
  
- **Option B - Unified FastAPI service:**
  - One main API service that imports module code
  - Modular monolith but at the API level too
  - Pros: Simpler, consistent with ARCHITECTURE.md ADR-001
  - Cons: Tighter coupling

---

### 6. **Session & Authorization Flow** 🟡 MAJOR

#### Current flow (Mangaly example):
1. User navigates to Mangaly
2. Mangaly login screen
3. OTP verification in Mangaly's tables
4. Session stored in Mangaly's session/token
5. Mangaly checks its own `members` table

#### Target flow:
1. User navigates to ForKhatri (root)
2. ForKhatri checks session cookie
3. If missing → redirect to Identity & Trust login
4. Identity & Trust: OTP verification (single instance)
5. Session token issued, sets platform cookie
6. Redirect to ForKhatri home/dashboard
7. User sees module tiles (Vyapar, Milavn, Mangaly)
8. User clicks Vyapar → ForKhatri routes to `/vyapar/*`
9. Vyapar API receives request with platform JWT
10. Vyapar verifies:
    - Is token valid? (check with Identity & Trust OR local JWT validation)
    - Is user allowed in Vyapar? (check `user_module_access` table)
    - Then execute Vyapar business logic

---

### 7. **Module Boundary Changes** 🟡 MAJOR

#### What stays in each module:
- Module-specific business logic
- Module-specific database schema
- Module-specific API endpoints
- Module-specific UI

#### What moves OUT:
- Authentication (→ Identity & Trust Service)
- Module access control (→ Platform layer)
- User/member identity tables (→ Identity DB)
- Session management (→ Platform layer)

#### What moves IN:
- Each module now receives pre-validated `user_context` (who the user is, what module they're in)
- Each module checks if user can perform *this action in this module* (not if they can access the module at all — that's checked earlier)

---

## Specific Module Changes Required

### Mangaly (MOD03) — MOST IMPACTED ⚠️ BREAKING CHANGES

**Scope of removal:** Auth layer, member table, OTP system, session management  
**Impact:** Existing Mangaly users will lose their accounts and need to migrate

**What to DELETE:**
- [ ] `modules/MOD03-mangaly/mangaly-api/` auth endpoints:
  - `POST /auth/send-otp` 
  - `POST /auth/verify-otp`
  - `POST /auth/refresh-token`
  - `POST /auth/logout`
- [ ] Mangaly database schema:
  - `DROP TABLE IF EXISTS member CASCADE;`
  - `DROP TABLE IF EXISTS credential CASCADE;`
  - `DROP TABLE IF EXISTS session CASCADE;`
  - Any auth-related tables
- [ ] Middleware: Custom OTP verification logic
- [ ] Frontend: Custom login screen (`/login`, `/otp-verify`)

**What to KEEP (unchanged):**
- Profile data: `matrimonial_profile`, `photos`, `interests`, etc.
- Features: Matches, circles, communication
- All business logic for matrimonial domain
- Mangaly's own database schema for non-auth tables

**What to ADD:**
- [ ] Middleware: JWT validation
  - Validate signature (using public key from Identity & Trust Service)
  - Check expiry
  - Extract `member_id` claim
- [ ] Authorization component:
  - Module-access check: Is `member_id` allowed to use Mangaly?
  - Domain checks: Can this member see this profile, send this message, etc.
- [ ] Foreign key references:
  - All tables' `member_id` → foreign key to Identity DB `member.id` (read-only)
- [ ] API updates:
  - All endpoints now expect `Authorization: Bearer <JWT>` header
  - All responses include authenticated user context in request scope

**Data migration required:**
- Export existing Mangaly members to CSV/JSON
- Verify against phone numbers (primary key in new system)
- Import into Identity & Trust Service's `member` table
- Migration script needed (cannot silently drop data)

---

### Milavn (MOD02) — Moderate Changes

**Scope:** Auth layer not yet built, so build it correctly from the start

**What to BUILD (with platform integration):**
- [ ] No custom auth endpoints
- [ ] JWT validation middleware (same as Mangaly)
- [ ] Authorization component:
  - Module-access check for Milavn
  - Organizer verification (is `member_id` a verified organizer?)
  - Event permission checks (can this member see/RSVP/organize this event?)
- [ ] Foreign key references:
  - All organizer/attendee records → `member_id` from Identity DB

**Sealed design constraints to respect:**
- Organizer activation is a first-class success metric (PRODUCT-GUARDRAILS.md)
- Circles emerge from real participation, not cold group-creation
- Discovery ranking: locality + trust > popularity

---

### Vyapar (MOD01) — Minimal Changes (Best Starting Point)

**Scope:** Design sealed but code not yet written; build correctly from day one

**What to BUILD (correctly this time):**
- [ ] No custom auth, ever
- [ ] JWT validation middleware (same pattern)
- [ ] Authorization component:
  - Module-access check
  - Professional verification (can this member claim professional status, list opportunities?)
  - Business verification checks
- [ ] Foreign key references:
  - All professional profiles → `member_id` from Identity DB

**Sealed design constraints:**
- Opportunity listings are community-curated, not algorithmic
- Professional verification via external APIs (PAN, GST, licenses)
- Revenue from opportunity publication (not community belonging)

---

### Dashboard (MOD05) — MUST WAIT for other modules

**Status:** Reads from all other modules; can't build until at least Vyapar/Milavn exist  
**Changes needed:**
- JWT validation (same as all modules)
- Authorization component (read-only permissions check)
- Module registry query: "Which modules can this user see?"
- If Mangaly data is present, show privacy-filtered activity summary (one-way async event)

---

### Four Future Modules (Counsel, Payment Services, Loans & Finance)

**Pattern for all of them:** Same as above (no custom auth, just JWT validation + authorization)

---

## Shared Platform Services to Build/Wire

| Service | Status | Changes Needed |
|---------|--------|----------------|
| Identity & Trust Service | Not yet built | Build complete auth service |
| Module Registry / Platform DB | Not yet built | Create module listing & user-module-access logic |
| API Gateway or Unified API | Not yet built | Route requests, enforce module access |
| Notification Service | Designed but not built | Integrate with platform auth |
| Search Service | Designed but not built | Integrate with platform auth |
| Audit Service | Designed but not built | Integrate with platform auth |

---

## Code Organization Changes

### Today:
```
modules/
  MOD01-vyapar/
    vyapar-web/      ← standalone React app
    vyapar-api/      ← standalone FastAPI server
  MOD02-milavn/
    milavn-web/      ← standalone React app
    milavn-api/      ← standalone FastAPI server
  MOD03-mangaly/
    mangaly-web/     ← standalone React app with login
    mangaly-api/     ← standalone FastAPI server with auth tables
```

### Target:
```
platform/
  identity-trust-service/  ← NEW: centralized auth
  api-gateway/             ← NEW: or unified API service
  platform-web/            ← NEW: unified React app with module shell
    src/
      pages/
        login.tsx
        dashboard.tsx (module listing)
        vyapar-shell/
        milavn-shell/
        mangaly-shell/

modules/
  MOD01-vyapar/
    vyapar-api/      ← API only, no auth code
  MOD02-milavn/
    milavn-api/      ← API only, no auth code
  MOD03-mangaly/
    mangaly-api/     ← API only, auth removed, member table removed
```

---

## Key Decisions to Make (Not code yet, just scoping)

1. **Identity & Trust Service:**
   - Build it as a separate FastAPI service?
   - Or use an external provider (Auth0, Firebase Auth)?
   - Or use a platform-provided identity service (your mention of "parent platform")?

2. **Frontend Consolidation:**
   - Consolidate all three module UIs into one unified React app?
   - Or keep them separate but wrap them with a unified shell/router?

3. **API Layer:**
   - API Gateway pattern (Kong, Nginx) to sit in front?
   - Or unified FastAPI monolith with module imports?

4. **Database Consolidation:**
   - Create a new central `platform` schema in Core DB for module registry?
   - Or a separate `platform` database?

5. **Backward Compatibility:**
   - Do existing Mangaly users need to migrate?
   - Should there be a migration script?

---

## Risks & Blockers

| Risk | Severity | Notes |
|------|----------|-------|
| Mangaly data migration | 🔴 High | Mangaly has member accounts in its own table - need migration |
| Breaking changes | 🔴 High | Module APIs change significantly |
| Downtime during transition | 🔴 High | Can't easily run both old & new in parallel |
| Lost session tokens | 🟡 Medium | Users logged into Mangaly today need re-login |
| Module access model unclear | 🟡 Medium | Need to define subscription/permission rules |

---

## Next Steps (Once You Approve This Analysis)

1. **Design Identity & Trust Service** (if building internally)
   - Data model
   - Auth flows
   - Token format
   - API contract

2. **Design module registry & access control**
   - Database schema for `user_module_access`
   - Business rules for module availability
   - Per-module role types

3. **Design unified frontend**
   - Shell/layout components
   - Module routing
   - Session management

4. **Design API consolidation**
   - Gateway or unified service
   - Request routing rules
   - Module-access enforcement

5. **Plan migration path**
   - Export Mangaly member data
   - Import into Identity DB
   - Redirect existing users

---

## Priority Sequencing & Dependency Graph

To understand what must be built first:

```
1. Identity & Trust Service (blocks everything else)
   ↓
2. Module Registry + user_module_access table (allows user discovery)
   ↓
3. Mangaly auth removal + module integration (test case for pattern)
   ├→ Vyapar integration (correct example from scratch)
   └→ Milavn integration (moderate-complexity example)
   ↓
4. Unified frontend shell (wraps all modules)
   ↓
5. Dashboard + cross-module aggregation
```

**Critical path:** Step 1 (Identity Service) MUST exist before Mangaly can launch. Steps 2-4 can proceed in parallel once Step 1 is done.

---

## Decision Checklist (For You to Answer)

**Before any code changes, clarify these:**

1. **Identity & Trust Service:**
   - [ ] Is it already built as a shared platform capability, or does it need building?
   - [ ] If external: Auth0, Firebase, or another provider?
   - [ ] If internal: Should it be in this repo, or separate?

2. **Mangaly's existing users:**
   - [ ] Is there user data in Mangaly's custom member table today?
   - [ ] What should happen to existing Mangaly user accounts?
     - Option A: Migrate them to Identity & Trust Service
     - Option B: Wipe and start fresh (data loss)
     - Option C: Run parallel login for transition period

3. **Module registry & access control:**
   - [ ] Should all users have access to all modules, or are there tiers?
   - [ ] Is there a subscription model?
   - [ ] Should organizer/professional status be a prerequisite for certain modules?

4. **Frontend consolidation:**
   - [ ] Should Vyapar, Milavn, Mangaly be unified into one React app?
   - [ ] Or keep them separate but wrapped in a platform shell (iframe/routing)?
   - [ ] Single port (3001) for everything, or keep separate ports?

5. **API layer:**
   - [ ] API Gateway (Kong/Nginx) sitting in front of modules?
   - [ ] Or unified FastAPI service (matching ADR-001's monolith pattern)?
   - [ ] Single port (8000) for all module APIs, or keep 8001, 8002, 8003?

6. **Timeline & risk tolerance:**
   - [ ] Can Mangaly go offline temporarily for migration?
   - [ ] Is there a hard launch date that depends on this?

---

## Detailed Change Summary by Layer

| Layer | Current State | Changes Required | Effort | Blocker? |
|-------|---|---|---|---|
| **Identity Service** | Designed, not built | Build or integrate external provider | Large | YES 🔴 |
| **Mangaly auth** | Custom impl, needs removal | Delete custom auth, integrate platform | Large | YES 🔴 |
| **Vyapar auth** | Not built | Build with platform JWT from day one | Large | YES 🔴 |
| **Milavn auth** | Not built | Build with platform JWT from day one | Large | NO (parallel) |
| **Database schema** | 6 Postgres instances (Core, Identity, Mangaly, etc.) | Add platform schema for module registry | Medium | NO |
| **Module registry** | Not exists | Create `modules` table + `user_module_access` | Medium | NO |
| **Frontend** | 3 separate React apps | Consolidate or wrap in shell | Large | NO (can defer) |
| **API routing** | 3 separate services | Add gateway or consolidate | Large | NO (can defer) |
| **User-to-module model** | Not modeled | Add user_module_access, role mapping | Medium | NO |

---

## What Will Look Like After Rework (High-Level)

### Login Flow (New User)
1. User visits `forkhathri.app`
2. Redirected to login screen (one login for all modules)
3. Enters phone number → gets OTP
4. Verifies OTP → Identity & Trust Service issues JWT
5. Browser redirected to ForKhatri dashboard
6. User sees available modules: "Vyapar", "Milavn", "Mangaly"
7. User clicks "Mangaly" → goes to `/mangaly/*`
8. Mangaly app receives JWT in header, validates it
9. Checks: "Is this user allowed in Mangaly?" (from `user_module_access` table)
10. User can now use Mangaly features (profile, matches, circles, etc.)

### Session Flow (Subsequent Visits)
1. User visits `forkhathri.app`
2. Browser sends JWT from localStorage
3. Platform validates JWT with Identity & Trust Service (or local JWT validation)
4. User already authenticated → dashboard shows modules
5. No re-login needed

### Account Deletion (Platform-Level)
1. User deletes account from ForKhatri
2. Identity & Trust Service marks member as inactive
3. All modules immediately can't authenticate this user
4. No per-module deletion needed

---

## Realistic Effort Estimate

| Phase | Tasks | Duration | Risk |
|-------|-------|----------|------|
| **Phase 1: Build Identity & Trust Service** | Design schema, implement OTP flow, JWT issuance, integrate with SMS | 2-3 weeks | High (new service) |
| **Phase 2: Mangaly migration** | Remove auth, add JWT validation, migrate user data | 2-3 weeks | High (breaking change) |
| **Phase 3: Wire Vyapar & Milavn** | Build auth integrations in existing codebases | 1-2 weeks | Medium |
| **Phase 4: Module registry & access control** | Create platform schema, module listing endpoints | 1 week | Low |
| **Phase 5: Frontend consolidation** | Unified login, module shell, routing | 2-3 weeks | Medium |
| **Total** | **Full rework** | **8-12 weeks** | **High** |

---

**Status:** ✅ Research complete. Code has NOT been modified. This report is ready for your review and decision-making.

**Next step:** Please review the analysis, answer the decision checklist above, and indicate which changes to prioritize and start with.
