---
project: ForKhatri
title: Platform Consolidation — Files to Update Checklist
date: 2026-09-14
status: Update Plan
scope: All sealed & in-progress pipeline artifacts
---

# Files to Update for Platform Consolidation

This checklist shows which `.md` files need to be updated based on the new unified identity architecture (documents `01-PLATFORM-CONSOLIDATION-RESEARCH.md` and `02-PLATFORM-CONSOLIDATION-ARCHITECTURE.md`).

**Color coding:**
- 🔴 **CRITICAL** — Breaking changes, must update before implementation
- 🟡 **MAJOR** — Significant updates required
- 🟢 **MODERATE** — Updates needed but not blocking
- 🔵 **MINOR** — Informational updates, can defer

---

## ROOT-LEVEL PLATFORM FILES

### 🔴 ARCHITECTURE.md
**What:** Platform-wide container, module, and shared service architecture  
**Current state:** Sealed (2026-09-12)  
**Why update:** Needs explicit section on unified Identity & Trust Service + platform consolidation model  
**Changes:**
- [ ] Update Container diagram to show `ForkhatriShell` as host application
- [ ] Add section: "User-to-Module Relationship Model" (user_module_access table)
- [ ] Update Module → Container mapping to clarify per-module isolation applies only to business logic (auth is unified)
- [ ] Add new ADR-019: "Unified Platform Identity with Per-Module Tiers"
  - Justifies: one platform_user table + independent per-module tier systems
  - Contrasts with: siloed auth per module
  - Trade-offs: simplified auth operations vs. per-module auth customization
- [ ] Update shared concern resolution (Identity & Trust Service section) to reflect module-access gateway
- [ ] Update non-functional baselines: Identity & Trust Service availability stays 99.9% (confirmed unchanged)
**Effort:** Medium (adds 1-2 new sections, 1 ADR)  
**Blocks:** Nothing (informational), but provides critical context for all module updates

---

### 🟡 MODULE-ARCHITECTURE-STANDARD.md
**What:** Pattern template for internal architecture of each module  
**Current state:** Sealed (2026-09-12)  
**Why update:** Needs section on "no module implements its own auth"  
**Changes:**
- [ ] Add §6a: "Authentication and Authorization Pattern"
  - No module builds login, signup, OTP, session management
  - All modules receive pre-validated JWT in Authorization header
  - Each module validates JWT (signature, expiry) but never issues tokens
  - Each module checks module-access (is user allowed in THIS module?) and domain authorization (can user DO this action?)
  - Both checks are structural chokepoints (§5 pattern), not conventions
- [ ] Add §6b: "Module-Specific Tier/Role Authorization"
  - Each module maintains its own tier enum (free, pro, elite vs. creator, pro, etc.)
  - Tiers are independent across modules (not inherited)
  - Authorization middleware enforces tier checks on sensitive endpoints
- [ ] Update §4 (Data Ownership): Clarify that `user_id` foreign keys point to platform Identity DB (read-only)
**Effort:** Small (adds 2 sections, clarifications)  
**Blocks:** All module updates (teams need this reference)

---

### 🟡 PRODUCT-GUARDRAILS.md
**What:** Non-negotiable product decisions that all requirements must respect  
**Current state:** Sealed (2026-09-13)  
**Why update:** Needs guardrails for platform consolidation, module tiers, and unified identity  
**Changes:**
- [ ] Add new guardrail row: **"Unified Identity"**
  - Rule: "One platform_user table is the single source of truth for all users across all modules"
  - One login for entire platform (no per-module accounts)
  - Modules cannot create or manage user identity; they only reference it
- [ ] Add new guardrail row: **"Independent Module Tiers"**
  - Rule: "User's tier/access level in one module is independent of tier in other modules"
  - Example: "User can be 'Pro' in Vyapar and 'Free' in Mangaly simultaneously"
  - No role/tier inheritance across modules
- [ ] Add new guardrail row: **"Module Access from Dashboard"**
  - Rule: "Users access modules only through the unified ForKhatri dashboard, not direct URLs"
  - Example: "vyapar.forkhatri.app must redirect to forkhatri.app if user not authenticated there"
  - Dashboard is the sole navigation hub
- [ ] Add to Standing PM Checkpoint: "Are we maintaining one user identity across modules?" (question 1)
**Effort:** Small (adds 3-4 guardrail rows)  
**Blocks:** Module-level BR/FR reviews (will reference these)

---

### 🟢 IMPLEMENTATION-TEST-STANDARDS.md
**What:** Tech stack, testing pyramid, code standards  
**Current state:** Fixed (per ARCHITECTURE.md ADR-001)  
**Why update:** Add JWT/auth testing standards + Module Federation deployment testing  
**Changes:**
- [ ] Add section: "Authentication & JWT Testing"
  - Mock JWT generation for unit tests
  - Real Identity & Trust Service integration tests
  - JWT expiry/refresh scenarios
  - Invalid/expired token handling
- [ ] Add section: "Module Federation Testing"
  - Module remoteEntry.js availability checks
  - Cross-module context passing (auth context)
  - Shared scope negotiation validation
- [ ] Add section: "Tier-Based Access Testing"
  - Each endpoint should have test cases for each tier
  - Rate limiting + tier tests
  - Tier upgrade/downgrade scenarios
**Effort:** Medium (adds testing requirements)  
**Blocks:** Implementation (teams need clear test standards)

---

## MODULE 1: VYAPAR (MOD01)

### Status: Pipeline Steps 1-4 Sealed (BR, FR, UX, UI complete)

### 🟡 01-business-requirements.md
**Current:** Sealed  
**Why update:** Auth/identity section needs consolidation  
**Changes:**
- [ ] **BR-03 (Authentication)** — REPLACE current text:
  - OLD: "Vyapar users sign up with phone/email, OTP verification"
  - NEW: "Vyapar is part of ForKhatri platform. Users authenticate once through platform identity service. Vyapar recognizes users via platform JWT."
- [ ] **BR-03 (User Verification)** — CLARIFY:
  - Business verification (PAN, GST) is separate from authentication
  - Platform handles authentication; Vyapar handles business verification
- [ ] Update architecture cross-check section to reference new `02-PLATFORM-CONSOLIDATION-ARCHITECTURE.md`
**Effort:** Small (1-2 BR sections)  
**Blocks:** Nothing (Vyapar still builds, auth just changes source)

---

### 🟢 02-functional-requirements.md
**Current:** Sealed  
**Why update:** Auth/identity FRs need consolidation  
**Changes:**
- [ ] **FR-02 (User Login/Registration)** — REMOVE or REDIRECT:
  - Remove FRs about "user enters phone, receives OTP, creates password"
  - Replace with: "User is already authenticated via platform. Vyapar receives JWT in request context."
- [ ] **FR-03 (Session Management)** — REMOVE:
  - Sessions are managed by platform (not Vyapar)
- [ ] **FR-04 (Professional Verification)** — KEEP (this is domain-specific, not auth):
  - Business verification logic stays in Vyapar
  - But now references platform's `verified_credential` table (read-only)
**Effort:** Small-Medium (remove ~3-5 FRs, add 1-2 new ones about JWT handling)  
**Blocks:** Nothing (can proceed to implementation with this change)

---

### 🟢 03-ux.md
**Current:** Sealed  
**Why update:** Remove login flow UX  
**Changes:**
- [ ] Remove flow: "User Sign Up"
- [ ] Remove flow: "User Login via OTP"
- [ ] Remove screens: "Sign Up Screen", "OTP Entry Screen", "Password Creation Screen"
- [ ] Keep flow: "Professional Profile Setup" (happens post-login, in Vyapar)
- [ ] Keep screens: Business category selection, business details, verification upload
**Effort:** Small (remove ~2-3 flows, 4-5 screens)  
**Blocks:** Nothing (UX work was speculative, domain UX stays)

---

### 🟢 04-ui.md
**Current:** Sealed  
**Why update:** Remove login screen designs  
**Changes:**
- [ ] Remove: Sign Up Screen design
- [ ] Remove: OTP Verification Screen design
- [ ] Remove: Password Creation Screen design
- [ ] Keep: Professional profile screens, verification upload screens, opportunity listing screens
**Effort:** Small (remove ~3 UI screens)  
**Blocks:** Nothing (visual work was speculative)

---

### Note on 05+ (Test Scenarios, Impact Analysis, etc.):
Since Vyapar hasn't progressed past Step 4 yet, these files don't exist. When Step 5+ agents run, they'll see the updated BR/FR/UX/UI and account for platform auth automatically.

---

## MODULE 2: MILAVN (MOD02)

### Status: Pipeline Steps 1-7a Complete (through ER Model, some ahead)

### 🟡 01-business-requirements.md
**Current:** Sealed  
**Why update:** Auth/identity section needs consolidation  
**Changes:**
- [ ] Update authentication BR:
  - Remove: "Milavn users sign up independently"
  - Add: "Milavn users are part of ForKhatri platform. Authentication is unified."
- [ ] Keep: Organizer verification (domain-specific, independent)
**Effort:** Small (1-2 BR edits)  
**Blocks:** Dependent modules (Dashboard, etc.)

---

### 🟡 02-functional-requirements.md
**Current:** Sealed  
**Why update:** Remove auth FRs, keep organizer/event FRs  
**Changes:**
- [ ] Remove FRs: User login, signup, session management
- [ ] Keep FRs: Event creation, RSVP, organizer profile, circle formation
- [ ] Add FR: "Accept JWT from platform, extract user_id for event RSVP/attendance tracking"
**Effort:** Small-Medium (remove ~3-4 FRs, add 1 new one)  
**Blocks:** Nothing (core event logic unchanged)

---

### 🟡 03-ux.md
**Current:** Sealed  
**Why update:** Remove login flows  
**Changes:**
- [ ] Remove flow: "User Sign Up"
- [ ] Remove flow: "User Login"
- [ ] Remove screens: Sign up, login
- [ ] Keep: Event discovery, RSVP, organizer profile, circle flows
**Effort:** Small (remove ~2 flows, 3-4 screens)  
**Blocks:** Nothing

---

### 🟡 04-ui.md
**Current:** Sealed  
**Why update:** Remove login screen designs  
**Changes:**
- [ ] Remove: Sign up, login screen designs
- [ ] Keep: Event discovery, RSVP, circle screens
**Effort:** Small (remove ~2-3 screen designs)  
**Blocks:** Nothing

---

### 🟡 05-test-scenarios.md
**Current:** Sealed  
**Why update:** Remove auth tests, keep event/community tests  
**Changes:**
- [ ] Remove scenarios: User signup, login, OTP verification
- [ ] Keep scenarios: Event creation, RSVP, circle formation, organizer verification
- [ ] Add scenarios: JWT validation (receive token, extract user_id), module access (verify user can access Milavn)
- [ ] Add scenarios: Rate limiting on RSVP/event-creation (per MODULE-ARCHITECTURE-STANDARD.md §4c)
**Effort:** Medium (remove ~5 scenarios, add ~3 new ones, update ~5 existing)  
**Blocks:** Nothing (Step 10 Testing agent will see these)

---

### 🟡 06-impact-analysis.md
**Current:** Sealed  
**Why update:** Verify assumptions still hold with platform auth  
**Changes:**
- [ ] Re-verify: Removing auth dependency on Milavn doesn't break event creation?
  - Answer: Yes, events created with platform user_id (simpler)
- [ ] Re-verify: Organizer verification still works?
  - Answer: Yes, Milavn queries platform's verified_credential table (read-only)
- [ ] Conclusion: Impact Analysis still valid, no blocking dependencies
**Effort:** Small (re-read, verify, note completion)  
**Blocks:** Nothing

---

### 🟡 07-tech-reqs.md
**Current:** Sealed  
**Why update:** Replace auth tech reqs with JWT validation tech reqs  
**Changes:**
- [ ] Remove TR: "Implement OTP service integration"
- [ ] Remove TR: "Implement session storage (Redis/DB)"
- [ ] Add TR: "Validate JWT signature using public key from Identity & Trust Service"
- [ ] Add TR: "Extract user_id from JWT claim for all requests"
- [ ] Add TR: "Check module_access: Is this user allowed in Milavn?"
- [ ] Add TR: "Implement rate limiting for RSVP (10 per hour per user, stored in Postgres)"
- [ ] Keep TR: "Verify organizer status (read from platform verified_credential table)"
**Effort:** Medium (replace ~3-4 TRs, add ~4 new ones)  
**Blocks:** Step 8 (Security & Performance agent will review these)

---

### 🟡 07a-er-model.md
**Current:** Sealed  
**Why update:** Remove auth tables, add foreign key to platform  
**Changes:**
- [ ] Delete tables: `user`, `credential`, `session`, `otp`
- [ ] For each remaining table that has `user_id`:
  - [ ] Verify FK: `user_id` → REFERENCES identity_db.platform_user(user_id)`
  - [ ] Make FK read-only (application never writes to Identity DB)
- [ ] Delete schema: If there was a `user` or `auth` schema, drop it
- [ ] Add note: "All user records are owned by Identity DB. Milavn only stores references."
**Effort:** Medium (schema cleanup, FK verification)  
**Blocks:** Step 7a (ER Model agent must re-seal after this)

---

### 🟢 modules/MOD02-milavn/architecture.md
**Current:** Exists  
**Why update:** Update to reference platform identity pattern  
**Changes:**
- [ ] Add section: "Authentication & Authorization"
  - Pattern: Validate JWT, extract user_id, check module access
  - Reference MODULE-ARCHITECTURE-STANDARD.md §6a-6b
- [ ] Update component diagram if it shows auth components (remove or rename)
**Effort:** Small (add 1 section)  
**Blocks:** Nothing (informational)

---

## MODULE 3: MANGALY (MOD03)

### Status: Pipeline Steps 1-8 Complete (through Security & Performance, Step 9 in progress)

### 🔴 01-business-requirements.md
**Current:** Sealed  
**Impact:** BREAKING — Auth is being completely removed  
**Why update:** Mangaly's current BR assumes custom login/auth; must be rewritten  
**Changes:**
- [ ] **BR-01 (User Identity & Authentication)** — COMPLETE REWRITE:
  - OLD: "Mangaly users sign up with phone/email, OTP, password creation, matrimonial profile"
  - NEW: "Users are part of ForKhatri platform. Authentication is unified via platform. Mangaly receives authenticated user context. Mangaly users create matrimonial profile as first-use onboarding."
- [ ] **BR-02 (User Verification/Trust)** — CLARIFY:
  - Platform handles Level-1/2 trust (identity verification)
  - Mangaly handles Level-3 trust (matrimonial-specific: photo verification, circles, attendance)
- [ ] Remove BR: Any BR about "user account creation", "OTP", "password", "session"
- [ ] Update architecture cross-check: Reference new platform architecture docs
**Effort:** Large (1-2 BRs completely rewritten, architecture section updated)  
**Re-seal:** YES — This is a significant change; must go back to Step 1 reviewer or be re-sealed after changes
**Blocks:** Everything downstream (Steps 2+) until this is updated

---

### 🔴 02-functional-requirements.md
**Current:** Sealed  
**Impact:** BREAKING — Auth FRs removed, module access FRs added  
**Why update:** Remove all identity/auth FRs; keep matrimonial FRs  
**Changes:**
- [ ] Delete FRs: "User Signup", "User Login via OTP", "Password Management", "Session Management"
  - Estimate: Remove ~10-15 FRs
- [ ] Delete FRs: "Email/SMS Notifications for auth" (platform handles this)
- [ ] Keep FRs: All matrimonial domain FRs (profile creation, matches, circles, communication, etc.)
- [ ] Add FR-NEW: "Module Access Check"
  - User has JWT from platform
  - Mangaly checks: Is this user allowed to access Mangaly?
  - If yes: Continue
  - If no: Redirect to platform (not your responsibility)
  - Tag: API layer, tier-based, mandatory
- [ ] Add FR-NEW: "Tier-Based Feature Visibility"
  - "Free" users: See basic profiles, limited matches
  - "Premium" users: Full profile search, premium match insights
  - "Elite" users: VIP features, priority support
  - Tag: API layer, business logic
- [ ] Add FR-NEW: "Rate Limiting on Messages"
  - Free tier: 5 messages/day
  - Premium: 50/day
  - Elite: Unlimited
  - Tag: API layer, rate limiting (per MODULE-ARCHITECTURE-STANDARD.md §4c)
**Effort:** Large (remove ~10-15 FRs, add ~5 new ones, rewrite ~10 existing)  
**Re-seal:** YES — Significant change
**Blocks:** Everything downstream

---

### 🔴 03-ux.md
**Current:** Sealed  
**Impact:** BREAKING — Remove entire login/signup flow  
**Why update:** Login screens no longer exist  
**Changes:**
- [ ] Delete flows: "User Sign Up", "User Login via OTP", "Password Recovery"
  - Estimate: Remove 3 flows, 8-10 screens
- [ ] Delete screens: All login/signup/onboarding-auth screens
- [ ] Keep flows: Profile setup (now second step after platform login), profile discovery, matching, circles, communication
- [ ] Add flow (simple): "Platform Login → Mangaly Onboarding"
  - User logs in at forkhatri.app
  - Clicks "Mangaly" tile
  - Mangaly loads with authenticated context
  - First screen: "Create Your Matrimonial Profile" (not login)
  - User fills profile, uploads photo → Done
  - Next: Discover matches
**Effort:** Large (remove 3 flows, 8-10 screens, add 1 flow with 3-4 screens)  
**Re-seal:** YES  
**Blocks:** Step 4 (UI agent)

---

### 🔴 04-ui.md
**Current:** Sealed  
**Impact:** BREAKING — Remove login screen designs  
**Why update:** UI for login/signup no longer needed  
**Changes:**
- [ ] Delete: Sign Up screen design
- [ ] Delete: OTP Entry screen design
- [ ] Delete: Password Creation screen design
- [ ] Delete: Session/profile avatar UI (moved to platform shell)
- [ ] Keep: Profile discovery screens, matching screens, circle screens, messaging screens, search/filter screens
- [ ] Add: Matrimonial profile creation screen (lightweight onboarding)
**Effort:** Large (remove 5-6 screen designs, add 1 new, update header UI to remove session badge)  
**Re-seal:** YES  
**Blocks:** Step 5 (Test Scenarios agent)

---

### 🔴 05-test-scenarios.md
**Current:** Sealed  
**Why update:** Remove all auth test scenarios  
**Changes:**
- [ ] Remove scenarios: User signup, OTP verification, password reset, session expiry, login
  - Estimate: Remove ~15-20 scenarios
- [ ] Keep scenarios: All matrimonial domain tests (profile creation, matching, circle management, messaging)
- [ ] Add scenarios:
  - "User without JWT cannot access Mangaly API" (401 response)
  - "User with expired JWT cannot access Mangaly API" (401 response)
  - "Free-tier user cannot see premium match insights" (403 response)
  - "Rate limiting: Free user hits 5-msg limit, 6th message rejected" (429 response)
  - "Premium user upgrades to Elite, new tier features appear" (feature visibility)
- [ ] Tag new scenarios: "API layer - JWT validation", "API layer - tier validation", "API layer - rate limiting"
**Effort:** Large (remove ~15-20, add ~5-10 new, update tag distribution)  
**Re-seal:** YES  
**Blocks:** Step 6 (Impact Analysis agent)

---

### 🟡 06-impact-analysis.md
**Current:** Sealed  
**Why update:** Removing auth is a HUGE change; re-analyze impact  
**Changes:**
- [ ] **Impact 1: User Migration**
  - Current Mangaly users exist in `mangaly_user` table
  - Must migrate to platform `platform_user` table
  - Dependencies: All Mangaly tables with `user_id` FK
  - Mitigation: Migration script + 7-day support window
- [ ] **Impact 2: Existing User Sessions**
  - All logged-in Mangaly users will be logged out
  - Must navigate to forkhatri.app, log in again
  - Mitigation: In-app notification 1 week before migration
- [ ] **Impact 3: API Contracts**
  - All Mangaly endpoints will now require JWT in Authorization header
  - Mobile clients must update (if any)
  - Mitigation: Version endpoints (v1 with custom auth, v2 with JWT) for gradual migration
- [ ] **Impact 4: Database Schema Changes**
  - Dropping `user`, `credential`, `session`, `otp` tables is destructive
  - Cannot easily roll back
  - Mitigation: Backup entire MangalyDB before migration; keep backup for 30 days
- [ ] **Dependency Check:**
  - Dashboard reads Mangaly data? Yes → Dashboard must accept new JWT pattern (fine, same platform auth)
  - Payment Services reads Mangaly data? Yes → Same JWT pattern (fine)
  - Any external systems? None known
- [ ] **Go/No-Go Decision:** 
  - Impact is HIGH but manageable
  - Recommendation: Execute during scheduled maintenance window; notify users; monitor closely
**Effort:** Large (deep analysis, multiple impact vectors)  
**Requires:** User approval to proceed (breaking change)  
**Re-seal:** YES — Impacts downstream; must be reviewed

---

### 🟡 07-tech-reqs.md
**Current:** Sealed  
**Impact:** BREAKING — Auth tech reqs completely replaced  
**Why update:** Remove all auth/OTP/session tech reqs; add JWT/module-access reqs  
**Changes:**
- [ ] Delete tech reqs: OTP integration, session storage, password hashing, email/SMS for auth
  - Estimate: Remove ~8-10 TRs
- [ ] Add tech reqs:
  - "TR-NEW-1: JWT Validation"
    - Fetch public key from Identity & Trust Service endpoint
    - Validate JWT signature (RS256)
    - Check expiry
    - Extract user_id, module_access, tiers claims
    - Tag: API layer, security-critical
  - "TR-NEW-2: Module Access Gate"
    - Query platform.user_module_access table
    - If no row for (user_id, 'mangaly'): Reject 403
    - If tier changed: Use database value over JWT claim
    - Tag: API layer, authorization
  - "TR-NEW-3: Tier-Based Feature Gating"
    - Every profile/match endpoint returns different data based on tier
    - Implement as middleware or per-endpoint check
    - Tag: API layer, business logic
  - "TR-NEW-4: Rate Limiting (Shared Utility)"
    - Implement one shared rate limiter (per MODULE-ARCHITECTURE-STANDARD.md §4c)
    - Parameterized: key (user_id), window (86400s), limit (5 for free tier, etc.)
    - Backed by Postgres (not in-memory)
    - Tag: API layer, abuse prevention
  - "TR-NEW-5: Idempotent Mutation Endpoints"
    - Every mutation (send message, profile update, match action) must be idempotent
    - Implement idempotency key (per MODULE-ARCHITECTURE-STANDARD.md §4b)
    - Store key + result in database
    - Tag: API layer, offline resilience
- [ ] Keep tech reqs: All matrimonial domain features (profile storage, matching algorithm, circle management, etc.)
**Effort:** Very Large (remove ~8-10 TRs, add ~5 detailed TRs with sub-items)  
**Re-seal:** YES  
**Blocks:** Step 7a (ER Model) and Step 8 (Security & Performance)

---

### 🔴 07a-er-model.md
**Current:** Sealed  
**Impact:** BREAKING — Delete auth tables, restructure  
**Why update:** Remove entire auth schema, add platform FK  
**Changes:**
- [ ] **Schema Changes:**
  - Delete schema: `user` (or `auth`), if exists
  - Delete tables: `user`, `credential`, `session`, `otp`, `password_reset`
  - Delete columns: `password`, `password_hash`, `salt`, `session_token`, `created_at` (move to platform)
- [ ] **Foreign Key Updates:**
  - For every table with `user_id` column:
    - Verify: `ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY (user_id) REFERENCES identity_db.platform_user(user_id)`
    - Verify: Application never writes to this FK
  - Tables affected: `matrimonial_member`, `matches`, `circle`, `circle_member`, `message`, `conversation`, etc.
- [ ] **New Tables:**
  - None (keep existing matrimonial schema)
- [ ] **New View (optional, for convenience):**
  - Create `v_member_with_platform_info` (join matrimonial_member with platform_user for UI queries)
  - Not required, but helpful for debugging
- [ ] **Documentation:**
  - Add note: "All user records are sourced from Identity DB. This schema only maintains references."
  - Add note: "Application connects to MangalyDB as non-owning role for RLS enforcement (per MODULE-ARCHITECTURE-STANDARD.md §4)"
**Effort:** Very Large (schema review, FK verification, data migration planning)  
**Migration Plan:** 
  - Phase 1 (before go-live): Backup full MangalyDB
  - Phase 2 (offline window): Export user data, drop auth tables, import to Identity DB, verify FKs
  - Phase 3 (post go-live): Monitor for orphaned records
**Re-seal:** YES — Data model is foundational  
**Blocks:** Step 8 (Security & Performance) and Step 9 (Implementation)

---

### 🟡 08-security-performance.md
**Current:** Sealed  
**Why update:** JWT validation + tier-based authorization threat modeling  
**Changes:**
- [ ] Add threat: "JWT Tampering"
  - Threat: Attacker modifies JWT claims (tier: 'elite' instead of 'free')
  - Mitigation: JWT signature validation + API re-validates tier in database
  - Severity: HIGH → MITIGATED
- [ ] Add threat: "Tier Bypass via Replay Attack"
  - Threat: Attacker replays old JWT with higher tier
  - Mitigation: Short JWT TTL (1 hour) + token rotation on refresh
  - Severity: MEDIUM → MITIGATED
- [ ] Add threat: "Module Access Bypass"
  - Threat: Attacker tries to access Mangaly without module_access row
  - Mitigation: API checks platform.user_module_access table; if missing, returns 403
  - Severity: HIGH → MITIGATED
- [ ] Add performance threshold: "JWT validation must complete < 10ms per request"
  - Mitigation: Cache public key in memory, refresh every 24 hours
- [ ] Add performance threshold: "Rate limiting check must complete < 5ms"
  - Mitigation: Postgres with index on (user_id, endpoint, window_start)
**Effort:** Medium (add ~5 threat models, 2-3 performance items)  
**Re-seal:** YES — Security is foundational  
**Blocks:** Step 9 (Implementation)

---

### 🟢 CODING-GUIDE.md
**Current:** Exists  
**Why update:** Update auth section, add JWT validation examples  
**Changes:**
- [ ] Remove section: "Authentication & Session Management"
- [ ] Add section: "JWT Validation & Authorization"
  - Code example: How to validate JWT in a FastAPI endpoint
  - Code example: How to extract user_id from JWT
  - Code example: How to check module access
  - Code example: How to enforce tier-based authorization
- [ ] Add section: "Tier-Based Feature Gating"
  - Code example: Conditional response based on user tier
- [ ] Add section: "Rate Limiting Pattern"
  - Code example: Using shared rate-limit utility
**Effort:** Small (remove 1 section, add 3-4 sections with code examples)  
**Blocks:** Implementers (helps coding)

---

### 🟢 architecture.md (Mangaly-specific)
**Current:** Exists  
**Why update:** Update to reference platform identity, remove auth components  
**Changes:**
- [ ] Remove component: "AuthenticationEngine" (if exists)
- [ ] Remove component: "SessionManager" (if exists)
- [ ] Add component: "AuthorizationBridge"
  - Role: Receives JWT, validates it, extracts user_id
  - Dependencies: Public key endpoint from Identity Service
  - Owned by: API layer
- [ ] Add section: "Authentication & Authorization Pattern"
  - Reference MODULE-ARCHITECTURE-STANDARD.md §6a-6b
  - Clarify: Mangaly does NOT authenticate; it authorizes
- [ ] Update component diagram: Remove auth flow, show JWT validation entry point
**Effort:** Small (component diagram update, 1-2 sections)  
**Blocks:** Nothing (informational, helps implementers)

---

### 🟡 v1-decisions.md
**Current:** Exists  
**Why update:** Record breaking change: auth removal  
**Changes:**
- [ ] Add decision: "AUTH-MIGRATION-001: Unified Platform Authentication"
  - Date: 2026-09-14
  - Decision: Remove Mangaly's custom auth, integrate with ForKhatri platform identity
  - Rationale: Platform consolidation; one user identity across all modules; simplified operations
  - Impact: Existing users must migrate; API contracts change; database schema changes
  - Migration: See 06-impact-analysis.md for details
  - Status: APPROVED (by user on 2026-09-14)
**Effort:** Small (add 1 decision record)  
**Blocks:** Implementers (helps understand WHY this happened)

---

### 🟢 modules/MOD03-mangaly/architecture.md
**Current:** Exists  
**Why update:** Update to remove auth architecture, clarify authorization pattern  
**Changes:**
- [ ] Remove section: "Authentication Architecture" (if exists)
- [ ] Remove components from diagram: Auth engines, session stores
- [ ] Add section: "Authorization & Module Access Pattern"
  - JWT validation as structural chokepoint (per MODULE-ARCHITECTURE-STANDARD.md §5)
  - Tier-based authorization enforcement
  - Reference to platform Identity & Trust Service
- [ ] Update component interactions: Show JWT flowing into API layer
**Effort:** Small (remove 1 section, add 1 section, update diagram)  
**Blocks:** Nothing (informational)

---

## CROSS-MODULE FILES

### 🟡 modules/modules.md
**Current:** Sealed (the modules decomposition)  
**Why update:** Reflect platform consolidation  
**Changes:**
- [ ] Add section: "Platform Consolidation Layer"
  - New shared concern: Unified Identity & Module Access
  - How it's resolved: Identity & Trust Service + Platform API Gateway
  - Which modules depend on it: All 7 modules
- [ ] Update modules section: Clarify each module's scope excludes authentication
  - Example: "MOD03-Mangaly: Matrimonial features. Authentication: Platform responsibility."
- [ ] Add note: "User-to-Module Relationship Model"
  - All users are platform users
  - Module access is independent
  - Tiers are module-specific
**Effort:** Small (add 2 sections, update module descriptions)  
**Re-seal:** Possibly (if this was Sealed; likely it was)  
**Blocks:** Nothing major (informational consolidation)

---

### 🟢 docs/ParentApp/ (If it exists as separate track)
**Current:** Exists (Parent App / ForKhatri Shell pipeline)  
**Why update:** Add references to consolidated identity  
**Changes:**
- [ ] In Parent App 01-BR: Clarify ForKhatri is the shell/dashboard; modules are content within it
- [ ] In Parent App 03-UX: Describe: Login → Dashboard (module tiles) → Click to enter module
- [ ] In Parent App 04-UI: Show module tiles, module switcher navigation
- [ ] Cross-reference the new consolidated architecture docs
**Effort:** Medium (several docs have additions)  
**Blocks:** Parent App pipeline (if running separately)

---

## SUMMARY TABLE

| File | Status | Severity | Changes | Effort | Re-seal? |
|------|--------|----------|---------|--------|----------|
| ARCHITECTURE.md | Sealed | 🟡 MAJOR | Add platform consolidation section + ADR-019 | Medium | Likely |
| MODULE-ARCHITECTURE-STANDARD.md | Sealed | 🟡 MAJOR | Add auth pattern section | Small | Likely |
| PRODUCT-GUARDRAILS.md | Sealed | 🟡 MAJOR | Add platform consolidation guardrails | Small | Likely |
| IMPLEMENTATION-TEST-STANDARDS.md | Fixed | 🟢 MODERATE | Add JWT/auth testing standards | Medium | No |
| MOD01 01-BR | Sealed | 🟡 MAJOR | Update auth BR | Small | Yes |
| MOD01 02-FR | Sealed | 🟢 MODERATE | Remove auth FRs | Small-Med | Yes |
| MOD01 03-UX | Sealed | 🟢 MODERATE | Remove login flows | Small | Yes |
| MOD01 04-UI | Sealed | 🟢 MODERATE | Remove login screens | Small | Yes |
| MOD02 01-BR | Sealed | 🟡 MAJOR | Update auth BR | Small | Yes |
| MOD02 02-FR | Sealed | 🟡 MAJOR | Remove auth FRs, add tier FRs | Med | Yes |
| MOD02 03-UX | Sealed | 🟡 MAJOR | Remove login flows | Small | Yes |
| MOD02 04-UI | Sealed | 🟡 MAJOR | Remove login screens | Small | Yes |
| MOD02 05-TS | Sealed | 🟡 MAJOR | Update test scenarios | Med | Yes |
| MOD02 06-IA | Sealed | 🟢 MODERATE | Re-verify impact | Small | Yes |
| MOD02 07-TR | Sealed | 🟡 MAJOR | Replace auth TRs with JWT TRs | Med | Yes |
| MOD02 07a-ER | Sealed | 🟡 MAJOR | Update schema, FKs | Med | Yes |
| MOD02 architecture.md | Exists | 🟢 MODERATE | Add auth pattern section | Small | No |
| MOD03 01-BR | Sealed | 🔴 CRITICAL | Complete rewrite (auth removal) | Large | YES |
| MOD03 02-FR | Sealed | 🔴 CRITICAL | Remove auth FRs, add tier FRs | Large | YES |
| MOD03 03-UX | Sealed | 🔴 CRITICAL | Remove login flows | Large | YES |
| MOD03 04-UI | Sealed | 🔴 CRITICAL | Remove login screens | Large | YES |
| MOD03 05-TS | Sealed | 🔴 CRITICAL | Remove auth scenarios, add JWT scenarios | Large | YES |
| MOD03 06-IA | Sealed | 🔴 CRITICAL | Re-analyze (breaking change) | Large | YES |
| MOD03 07-TR | Sealed | 🔴 CRITICAL | Replace auth TRs, add JWT/tier TRs | Very Large | YES |
| MOD03 07a-ER | Sealed | 🔴 CRITICAL | Delete auth tables, add FKs | Very Large | YES |
| MOD03 08-SP | Sealed | 🟡 MAJOR | Add JWT/tier threat models | Med | YES |
| MOD03 CODING-GUIDE | Exists | 🟢 MODERATE | Update auth section | Small | No |
| MOD03 architecture.md | Exists | 🟢 MODERATE | Update auth pattern | Small | No |
| MOD03 v1-decisions.md | Exists | 🟢 MODERATE | Record auth migration decision | Small | No |
| modules.md | Sealed | 🟢 MODERATE | Add platform consolidation section | Small | Likely |

---

## SEQUENCING: Which to Update First?

**Phase 1: Platform-level files (foundation)**
1. ✅ ARCHITECTURE.md (add consolidation section + ADR-019)
2. ✅ MODULE-ARCHITECTURE-STANDARD.md (add auth pattern §6a-6b)
3. ✅ PRODUCT-GUARDRAILS.md (add consolidation guardrails)
4. ✅ IMPLEMENTATION-TEST-STANDARDS.md (add JWT testing standards)

**Phase 2: Vyapar (least impacted, good starting point)**
5. ✅ MOD01 01-BR (small update)
6. ✅ MOD01 02-FR (small update)
7. ✅ MOD01 03-UX (small removal)
8. ✅ MOD01 04-UI (small removal)
9. ✅ modules.md (add platform consolidation section)

**Phase 3: Milavn (moderate impact, clarifies pattern)**
10. ✅ MOD02 01-BR through 07a-ER (all 8 files, see individual efforts)
11. ✅ MOD02 architecture.md

**Phase 4: Mangaly (highest impact, requires careful migration planning)**
12. ✅ MOD03 01-BR through 08-SP (all 8+ files, see individual efforts)
13. ✅ MOD03 supporting docs (CODING-GUIDE, v1-decisions, architecture)
14. ✅ Finalize migration plan (Step 6 Impact Analysis stage)

---

**Status:** This is your update roadmap. Ready to start Phase 1 (platform-level updates)?
