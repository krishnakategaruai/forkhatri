---
project: ForKhatri
applies_to: 09-implementation-agent, 10-test-automation-agent
status: Approved
updated: 2026-09-06
---

# Implementation & Test Automation Standards — ForKhatri

**Read this file is a mandatory pre-req for both the Implementation Agent
(Step 9) and the Test Automation Agent (Step 10), before either writes a
single line of code.** It exists because naming and structure conventions
are project/stack-specific — nothing here is a universal law, most of it
is "the project picked one option from several valid ones, now hold the
line on it consistently." Where a section cites a real convention, the
source is named; where it's a project choice among several legitimate
options, that's stated too, so nobody mistakes a house-style pick for an
external standard.

**Stack: Python (FastAPI) backend, React (TypeScript) frontend, Postgres
as the primary data store.** Chosen for a strong async API story (useful
given the AI/local-intelligence and notification workloads described in
the Master PRD), a typed contract between services via Pydantic, and a
large talent pool for both sides of the stack.

## 1. Naming conventions

| Element | Convention | Example |
|---|---|---|
| Backend files/modules | `snake_case.py` | `business_requirements_service.py` |
| Frontend files (components) | `PascalCase.tsx` | `DashboardCard.tsx` |
| Frontend files (non-component: hooks, utils) | `camelCase.ts` | `useMemberTrust.ts` |
| Folders | `kebab-case` | `local-intelligence/` |
| Python classes / Pydantic models | `PascalCase` | `MemberProfile` |
| TS types / interfaces | `PascalCase` | `MemberProfile` |
| Python functions / variables | `snake_case` | `get_verified_members()` |
| TS functions / variables | `camelCase` | `getVerifiedMembers()` |
| Constants (true, module-level) | `UPPER_SNAKE_CASE` (both langs) | `MAX_TRUST_LEVEL` |
| SQL tables / columns | `snake_case`, plural table names | `matrimonial_profiles` |
| Branches | `feature/BR0x-fr0x-short-slug` (include the FR ID so a branch traces back to this pipeline's IDs) | `feature/BR02-fr03-business-verification` |
| Commit messages | **Conventional Commits** — `type(scope): description`, `type` ∈ `feat`, `fix`, `docs`, `refactor`, `test`, `chore`. Real external convention (not project-specific), and what Step 14's Keep a Changelog output expects as input. | `feat(vyapar): add business KYC verification per FR03` |

## 2. Requirement-level comment block (Implementation Agent, Step 9)

Per the pipeline rule: **no code is written for a requirement until its
comment block is complete.** The comment is per-requirement, not per-line.

**Exact format:**

```
# [TR0x] <one-line statement of intent>
# Approach: <why this approach was chosen, one or two sentences>
# Traces to: FR0x, SP0x (list every requirement this block of code satisfies)
```

TSX/TS equivalent uses `//` instead of `#`. Example (Python):

```python
# [TR03] Verify business PAN/GST against the registered owner before
# a Vyapar profile is marked "verified".
# Approach: automated verification per Trust principle 8.6 (Master PRD);
# falls back to manual review only when the automated check errors out.
# Traces to: FR03, SP02
def verify_business_identity(business_id: str) -> VerificationResult:
    ...
```

A file with implementation code but no such block above it, for any
requirement, is not compliant — the Implementation Agent's Definition of
Done treats this as a blocking gap, not a style nit.

## 3. Protected / frozen paths

| Path | Why it's frozen | Who can approve an exception |
|---|---|---|
| `**/migrations/**` (applied migrations) | Applied DB migrations are immutable history; fix forward with a new migration | Architecture reviewer |
| `**/generated/**` | Auto-generated (OpenAPI client, etc.) — hand-edits get overwritten | N/A — regenerate instead |

## 4. Test naming convention (Test Automation Agent, Step 10)

**This project's chosen convention:**
`Given_<precondition>_When_<action>_Then_<outcome>` — maps directly onto
the Given/When/Then scenarios Step 5 already writes, requiring no
translation between the two. Applies to both `pytest` test function names
and React/Vitest test descriptions (`describe`/`it` blocks read as one
Given/When/Then sentence).

**Test body structure — Arrange/Act/Assert (Given/When/Then equivalent):**
- One clear **Arrange** section (setup/preconditions)
- A single **Act** (the one action under test — not several)
- A single logical **Assert** (a test verifying multiple unrelated
  behaviors should be split, not asserted together)
- Cyclomatic complexity of a test should be effectively 1 — no
  conditional branching inside a test. If you need an `if` inside a test,
  that's two tests.

**Mocking rules per layer** (ties back to the Unit/Integration/E2E tag
Step 5 assigned to each scenario):
- **Unit:** mock all external dependencies (network, database, other
  services) — `pytest` uses `unittest.mock`/`pytest-mock`; frontend unit
  tests use Vitest mocks. A unit test with a live dependency has drifted
  into being an integration test and should be re-tagged, not left
  mislabeled.
- **Integration:** use real internal collaborators (real Postgres via a
  test container); mock only true external boundaries (SMS/OTP
  providers, payment gateways, external KYC APIs).
- **E2E:** no mocking — Playwright drives the real frontend against the
  real backend and a seeded test database. This is the one layer meant
  to prove the whole stack is actually wired together correctly.

## 5. Commands

| Command | Purpose | Healthy output example |
|---|---|---|
| `uvicorn app.main:app --reload` | Run backend dev server | server listening on :8000 |
| `pytest` | Run backend test suite | `N passed in Xs` |
| `ruff check .` | Backend lint | `All checks passed!` |
| `mypy .` | Backend type check | `Success: no issues found` |
| `npm run dev` | Run frontend dev server | Vite/Next dev server ready |
| `npm run test` | Run frontend unit/component tests | `Test Files N passed` |
| `npx playwright test` | Run E2E suite | `N passed` |
| `npm run lint` | Frontend lint | `0 problems` |
| `npm run build` | Frontend production build | `build succeeded` |

## 6. Things this project's agents keep getting wrong

A living, append-only correction log — same rule the blog's `CLAUDE.md`
uses: when an agent repeats a mistake twice, the correction goes here
permanently, not just fixed once in the moment.

| Date added | Mistake | Correction |
|---|---|---|
| | | |

## 7. Revision history

| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-06 | Initial version | Project kickoff — stack decided as Python/FastAPI + React |

## Approval

Engineering Manager / Tech Lead — [x] Approved — autonomous execution mode, 2026-09-06
