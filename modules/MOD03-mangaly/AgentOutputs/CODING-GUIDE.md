---
module: MOD03
step: module-coding-guide
status: Sealed
approver: Engineering Manager / Tech Lead
updated: 2026-09-12
---

# Coding Guide — MOD03 Mangaly

This is Mangaly's own supplement to `/IMPLEMENTATION-TEST-STANDARDS.md`
(project-wide — naming, comment-block format, test-naming convention,
mocking rules, protected paths). Read that file first; this one adds
what's specific to building *this* module — its internal component
structure (`architecture.md`), its resolved V1 decisions
(`v1-decisions.md`), and the extra discipline its sensitivity level earns
it. Where this file is silent, the project-wide standard governs. Where
they'd conflict, they don't — this file only adds, never overrides.

## 1. Stack — confirmed for Mangaly, with two specific refinements

The project-wide stack (Python/FastAPI, React/TypeScript, Postgres) was
validated against current (2026) practice specifically for this module's
profile — a regulated-data, mobile-first, isolated-container service —
not just assumed to still be right:

- **FastAPI stays.** Current guidance still names FastAPI the strong
  default for async, typed, OpenAPI-documented Python APIs, which is
  exactly Mangaly's shape (async event publishing to the Broker, heavy
  Pydantic-validated request/response contracts across 14 internal
  components). The one real alternative worth naming — Django REST
  Framework, favored for "regulated, slow-moving" CRUD-heavy systems —
  doesn't fit better here: Mangaly's regulatory weight lives in its data
  isolation and authorization discipline (`/MODULE-ARCHITECTURE-STANDARD.md`
  §§4-5, applied in `architecture.md` §3), not in needing Django's admin/ORM
  machinery, so FastAPI's lighter footprint remains the right call. No change.
- **Postgres stays, with one addition: Row-Level Security.** Schema-per-
  component (`/MODULE-ARCHITECTURE-STANDARD.md` §4, applied in `architecture.md`
  §3) is the primary isolation mechanism, enforced by import-boundary
  discipline. Add **Postgres RLS
  policies** as a second, database-enforced layer underneath it — current
  practice specifically recommends RLS for exactly this situation
  (regulated data where "even a buggy application query can't leak data
  across" a boundary). Concretely: every table in a schema owned by a
  business-logic component gets an RLS policy keyed on the Authorization
  Engine's own decision (a `current_setting('mangaly.authz_context')`
  session variable the Authorization Engine sets after it resolves the
  BR04 chain, before any query the requesting component issues). This
  means a bug in, say, the Communication component that accidentally
  queries outside its own authorized scope is blocked by Postgres itself,
  not only by code review having caught the mistake.
- **Frontend: Next.js (App Router), not a bare Vite/CRA SPA.** The
  project-level `/ARCHITECTURE.md` fixes "React/TypeScript SPA" at the
  architecture level (ADR-014, REST/JSON consumption) — that decision
  isn't reopened here. But *how* that SPA is actually built matters for
  Mangaly's named audience (tier-2/3 Indian connectivity, older
  parent-generation users, per this module's own BRs): current practice
  confirms Next.js is what "choosing React" concretely means in 2026 (the
  large majority of new React projects start there), and its route-level
  code-splitting and flexible rendering (static where a screen has no
  per-user data — e.g. Onboarding, Help & Support — client-rendered where
  it does) directly reduces first-load JS on a flaky connection compared
  to a single monolithic SPA bundle. This is an implementation-level
  refinement of the existing architecture decision, not a change to it —
  Next.js still talks to the same REST/JSON API, still is one deployable
  web client.

## 2. Backend project structure — mirrors `architecture.md` exactly

One FastAPI process, one Python package per component from `architecture.md`
§2, per the internal-deployment-shape pattern `/MODULE-ARCHITECTURE-STANDARD.md`
§3 fixes for every module. Do not add a component that isn't in
`architecture.md`, and do not split one of its components into two without
recording that decision there first — `architecture.md`, not this file,
owns Mangaly's component boundary.

```
mangaly-service/
  app/
    api/                    # FastAPI routers only — no business logic
    components/
      identity_bridge/      # thin
      profile/              # BR01, BR18
      home_circle/          # BR02, BR03, BR13
      authorization/        # BR04, BR05 — the chokepoint, see §3
      discovery/            # BR06
      compatibility/        # BR07
      trust/                # BR08
      connection/           # BR09, BR10
      communication/        # BR11, BR12
      safety/               # BR14, BR20-reporting
      lifecycle/            # BR18, BR19, BR20-guidance
      operations/           # BR16, schema-owning (case queue/decisions/appeals) —
                             # corrected from an earlier draft that mislabeled
                             # this "thin"; it never was
      notification_bridge/  # thin for delivery; owns mangaly_notification
                             # schema for the in-app inbox record (FR098,
                             # architecture.md §2.1/§3)
      audit_bridge/         # thin, schema-less end to end
    events/                 # the internal domain event bus (MODULE-ARCHITECTURE-STANDARD §6)
    idempotency/            # shared API-layer middleware — every client-
                             # queueable mutation endpoint honors a client-
                             # supplied idempotency key (MODULE-ARCHITECTURE-
                             # STANDARD §4b, resolves 06-impact-analysis.md IA102)
    rate_limiting/          # ONE shared utility (key, window, limit) — DB-
                             # backed counter, not in-memory. Login failures
                             # (Identity Bridge), OTP resend (Identity Bridge),
                             # and verifier invites (Trust & Verification) all
                             # call this same implementation; none builds its
                             # own counter table "following the same pattern"
                             # (MODULE-ARCHITECTURE-STANDARD §4c — added after
                             # a Tech Reqs review found three components each
                             # about to build their own copy)
    db/
      schemas/              # one migration namespace per component schema —
                             # twelve total, see architecture.md §3
    config/
      thresholds.py         # DEC-V1-005's age gate, DEC-V1-006's SLA windows —
                             # versioned settings, never hardcoded literals
      paging.py             # on-call paging integration for Tier 3/4 cases
                             # (DEC-V1-009) — vendor is a Step 7 choice, the
                             # trigger contract (auto-fire on Tier 3/4
                             # classification) is fixed here
  tests/
    unit/ integration/ e2e/ # mirrors 05-test-scenarios.md's layer tags exactly
```

Each `components/<name>/` package exposes exactly one public interface
module (`interface.py`) other components are allowed to import; everything
else in that package is private to it. A lint rule (not just a code-review
habit — `/MODULE-ARCHITECTURE-STANDARD.md` §3 requires this be enforced, not
merely conventional) blocks any import that reaches past a component's
`interface.py` into its internals.

## 2b. Frontend project structure — `mangaly-web/`

Next.js (App Router) per §1, TypeScript, one deployable web client.

```
mangaly-web/
  app/                      # App Router. One folder per route.
    layout.tsx              # Shell: <html>, I18nProvider, TabBar
    globals.css             # THE design tokens (04-ui.md) + component styles
    page.tsx                # "/" — launch routing (FR090)
    login/ signup/ reset/   # Auth screens (FR092-FR094)
    discover/ circle/ messages/ me/   # The four signed-in tabs
    status/                 # Build tracker — a development view, not product
  components/
    TabBar.tsx              # Primary nav
    form/                   # Field, SubmitButton — the UI03 shared template
    <Feature>.tsx           # Feature components, PascalCase
  lib/
    api.ts                  # Base fetch + API_BASE
    auth.ts                 # Auth calls (FR090/092/093/101)
    i18n/                   # config.ts, provider.tsx
    requirements.ts         # Build-tracker status
    traceability.json       # GENERATED — do not hand-edit (see §2c)
  locales/
    en/ hi/ te/             # One folder per language, one JSON per namespace
```

**Naming conventions.** Route folders are lowercase and match their URL
segment. Components are `PascalCase.tsx` and colocate under `components/`;
anything used by exactly one route may live beside it instead. Modules under
`lib/` are `camelCase.ts` and export named functions, never a default. CSS
classes are BEM-ish (`.field__input`, `.pill--live`) and live in `globals.css`
rather than per-component files, so the token vocabulary stays in one place and
two screens cannot style the same element differently.

**Every user-visible string comes from `locales/`, with no exceptions.** A
string typed into a component is a string that cannot be translated, and FR089
makes language a person-level preference across English, Hindi and Telugu
(ADR-010) — so a hardcoded label is not a cosmetic shortcut, it is content one
part of the intended audience cannot read. English is the fallback for every
key; `hi` and `te` files may be partial, and an untranslated key renders its
English text rather than a missing-key placeholder, so a partial translation is
never worse than none. Keys are namespaced by file (`auth:login.title`), and
the namespace matches the JSON filename.

**No hardcoded values, either.** Anything environment-specific (`API_BASE`,
ports, endpoints) reads from config, following the same placeholder convention
the backend uses.

## 2c. Traceability is generated, not maintained by hand

`mangaly-web/lib/traceability.json` holds the full parent map — every FR with
its BR, UX, UI, TS, IA, TR and SP ids — and is produced by extracting the
actual `**Traces from:**` lines out of `01-business-requirements.md` through
`08-security-performance.md`. It is regenerated rather than edited, so it
cannot drift from what those documents say; if a row looks wrong, the fix
belongs in the source document. Current extraction: 20 BR, 102 FR, 30 UX,
30 UI, 229 TS, 102 IA, 102 TR, 104 SP, with no FR missing a downstream
artifact.

Every feature module carries its chain in a header comment (for example
`FR093 · TR093 · UX03 · UI03 · TS206-TS208 · SP093`), so the specs a file must
satisfy are readable from the file itself.

## 3. The Authorization Engine is not optional to call

Every other component's `interface.py` method that reads or writes
consequential data takes an already-resolved authorization context as a
parameter — it does not resolve authorization itself, and it does not
accept a raw actor ID and decide on its own whether that actor may proceed.
Concretely:

```python
# [FR017] Every consequential access routes through one chokepoint before
# any component touches its own schema.
# Approach: the Authorization Engine is the only component permitted to
# resolve the BR04 chain; every other component receives an already-
# resolved AuthzContext, never a raw actor id, so "forgot to check
# authorization" is not a mistake an individual component can make.
# Traces to: FR017, FR018, TS038-TS043
def get_profile_for_viewer(authz: AuthzContext, candidate_id: str) -> Profile:
    ...
```

If you find yourself writing a component method that takes a bare user ID
and queries data with it, stop — that method is missing its `AuthzContext`
parameter and is not compliant with `/MODULE-ARCHITECTURE-STANDARD.md` §5's
authorization-chokepoint pattern (applied here per `architecture.md` §3),
regardless of whether it happens to produce a correct result in the case
you're testing.

## 4. Cross-component side effects go through the event bus, never a direct import

If component A's action needs component B to react (e.g. Safety recording
a report needs Audit Bridge, Notification Bridge, and Operations to each
do something), A publishes a domain event; it does not import B and call
it directly. Publish inside the same database transaction as the state
change that caused it (transactional outbox — the event row commits or
rolls back atomically with the state it describes), so an audit entry can
never be silently lost because the process crashed between "save the
report" and "tell Audit about it."

```python
# [FR069] Every consequential action publishes a reconstructable audit event.
# Approach: outbox pattern — the event insert is in the same transaction
# as the state change, so a crash can't produce a state change with no
# corresponding event.
# Traces to: FR069, FR052, TS119
async def submit_report(...) -> Report:
    async with db.transaction():
        report = await safety_repo.create_report(...)
        await events.publish(ReportSubmitted(report_id=report.id, ...))
    return report
```

## 5. Where to find already-decided values — don't re-derive them

Several things a naive implementer might be tempted to invent from scratch
are already decided in `v1-decisions.md`. Look there before picking your
own value:

| If you're about to decide... | Don't — it's already decided in `v1-decisions.md` |
|---|---|
| Which profile fields gate Discovery | DEC-V1-001 (the three-tier field list) |
| Discovery ranking weights | DEC-V1-002 (the 30/30/20/20 weighted model + diversity re-rank) |
| What a community discovery hint contains | DEC-V1-003 (structural field-level limits) |
| Verifier eligibility rules | DEC-V1-004 (Level-2-trust gate, rate limit, idempotency) — the rate limit itself calls the shared `rate_limiting/` utility (§1), same as login/OTP-resend; it does not get its own counter |
| The marriageable-age number | DEC-V1-005 — **and note it's a configured setting (`config/thresholds.py`), never a literal in business logic** |
| Safety severity tiers/SLAs | DEC-V1-006 (four tiers, response times) |
| Admin case workflow states | DEC-V1-007 (intake→triage→assignment→investigation→decision→audit→appeal) |
| Real-world-meeting safety copy | DEC-V1-008 (the five bullet points) |
| How a Tier 3/4 safety case actually reaches a human, and how suspected CSAM gets reported externally | DEC-V1-009 (on-call paging trigger contract; POCSO Rule 11 → cybercrime.gov.in/SJPU, with the Rule 11(2) source-material handover) |
| The personality-assessment instrument itself | **Genuinely still open** — see `v1-decisions.md`'s "What stays open" table. Build FR033's skip/non-blocking mechanics now; do not pick or hardcode an instrument. |

If a value isn't in that table and isn't in the BR/FR/UX/UI files either,
it's genuinely still open (see `v1-decisions.md`'s "What stays open" table)
— raise a blocker per this pipeline's standard handling, don't guess one.

## 6. Testing — map directly onto `05-test-scenarios.md`, don't re-derive test cases

Every one of the 229 scenarios in `05-test-scenarios.md` already has a
Given/When/Then, a Layer tag (Unit/Integration/E2E), and a Traces-from FR.
Step 10 (Test Automation) will formalize this, but while writing
implementation code:

- A scenario tagged **Unit** that asserts an absence ("no trust-score field
  exists anywhere," "no swipe-card model exists") is a real, valuable test
  — write it as a schema/contract assertion or a static check, not
  something to skip because "there's nothing to call."
- The Authorization Engine (§3) and the event bus (§4) are the two
  components worth the deepest test investment — TS038-TS043 and
  TS119-TS120 respectively already specify exactly what they need to prove.
- Mocking follows the project-wide rule exactly (Unit: mock everything
  external; Integration: real Postgres, mock only true external
  boundaries — for Mangaly that means the SMS/OTP provider and Identity &
  Trust Service specifically, both outside this container).

## 7. Security practices specific to this module's sensitivity

- **RLS is defense-in-depth, not the only control.** Application-level
  authorization (§3) is still mandatory even though RLS exists — RLS
  catches the bug, it doesn't replace the design discipline that prevents
  most bugs in the first place.
- **RLS must actually be enforced, not silently no-op'd** (per
  `06-impact-analysis.md` IA017 and `/MODULE-ARCHITECTURE-STANDARD.md` §4):
  confirm at setup time — not just at code-review time — that (a)
  MangalyService's runtime Postgres role does **not** own the tables its
  RLS policies restrict (RLS is bypassed entirely for a table's owner by
  default), and (b) the `mangaly.authz_context` session variable is set
  with **`SET LOCAL`**, never plain `SET`, wherever connections are pooled
  in transaction mode — a plain `SET` under pooling can leak one request's
  authorization context onto a different pooled connection's next
  transaction. Write an integration test that actually exercises this
  under the real pooling configuration before trusting it.
- **Every client-queueable mutation is idempotent, not just retried**
  (resolves `06-impact-analysis.md` IA102). A retried "send message" or
  "save profile edit" after a connectivity drop must safely no-op and
  return the original result on a repeated idempotency key, not create a
  duplicate record — this is a distinct failure mode from "the write was
  lost," and existing offline-resilience test scenarios (TS228-229) do not
  cover it, so add a dedicated test for duplicate-write prevention per
  queueable endpoint, don't assume TS228-229 already proves it.
- **Tier 3/4 safety escalation is not "the pipeline exists," it's "the
  pipeline's exits are reachable"** (DEC-V1-009, `06-impact-analysis.md`
  IA065/IA068/IA074). Building the graduated-response state machine
  without also wiring the on-call paging trigger and the CSAM
  law-enforcement reporting path leaves the two most legally consequential
  exits unbuilt behind a correct-looking pipeline. Treat both as required
  for this FR set to be considered actually complete, not as a follow-up.
- **The Evidence panel's backend contract has no document-rendering field,
  by construction** (resolves FR040's Fidelity flag, already recorded in
  `04-ui.md`). If you're implementing the Evidence endpoint and find
  yourself adding a raw file URL to its response model, that response
  model is wrong — the only endpoint permitted to return a raw verification
  document is the role-gated Admin Case detail endpoint (§2, `operations`
  component).
- **Anti-enumeration is a response-shape rule, not a copy-writing
  reminder** (resolves FR094's Fidelity flag). Login and Password-Reset
  both return the *identical* response body and status code for "wrong
  password" vs. "no such account" — verify this with a test that diffs the
  two responses byte-for-byte (TS207, TS211), not just a manual read of
  the error string.
- **Safety detection's data-scope boundary is enforced in the query layer,
  not just documented** (DEC-V1-006): the Safety component's repository
  layer should not have a method capable of reading Home Circle or
  Trust/Verification tables at all — not "a method that happens not to be
  called," an absence, so BR14 DEC-001's trust/safety separation can't be
  silently violated by a future feature adding a call that technically
  compiles.

## 8. Revision history

| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-12 | Initial version, written alongside `architecture.md` and `v1-decisions.md`, after Steps 1-5 Sealed for this module. Stack validated against current 2026 practice (FastAPI/Postgres confirmed, Next.js and Postgres RLS added as concrete refinements) rather than assumed unchanged from the project's original 2026-09-06 pick. | Engineering Manager / Tech Lead — krishna kategaru (autonomous), 2026-09-12. |
| 2026-09-12 | Updated every `MOD03-ADR-00x` reference to point at `/MODULE-ARCHITECTURE-STANDARD.md`'s corresponding section, after those four internal-architecture decisions were extracted from `architecture.md` into that new project-level, module-generic file. No guidance in this file changed — only what it cites. | Engineering Manager / Tech Lead — krishna kategaru (autonomous), 2026-09-12. |
| 2026-09-12 | Impact Analysis follow-up: corrected the Operations component's project-structure comment (schema-owning, not thin) and the component count (14, not 13); added the Notification Bridge's inbox schema, an `idempotency/` middleware module, and a `paging.py` config module to the project structure; added RLS-enforcement-verification and idempotent-mutation requirements to §7; added DEC-V1-009 and the still-open personality-assessment instrument to §5's lookup table — all resolving findings from `06-impact-analysis.md` (IA017, IA033, IA065/IA068/IA074, IA098, IA102). | Impact Analysis follow-up — krishna kategaru (autonomous), 2026-09-12. |
| 2026-09-13 | Tech Reqs review follow-up: a critique-mindset review of `07-tech-reqs.md` found rate-limiting (login failures, OTP resend, verifier invites) described three separate times as "the same pattern as" an earlier tech req rather than genuinely one shared implementation, spanning two different components. Added a `rate_limiting/` shared utility module to the project structure, per `/MODULE-ARCHITECTURE-STANDARD.md`'s new §4c. | Tech Reqs review follow-up — krishna kategaru (autonomous), 2026-09-13. |
| 2026-09-13 | Implementation follow-up, written while building the first vertical slice (FR090/FR092/FR093/FR101 auth) rather than planned in advance. Added **§2b** (frontend project structure for `mangaly-web/`, naming conventions, and the rule that every user-visible string lives in `locales/` — hardcoding a label is not a cosmetic shortcut when FR089/ADR-010 make language a person-level preference across English, Hindi and Telugu) and **§2c** (the parent-ID traceability map is generated by extracting the real `Traces from:` lines from Steps 1-8, never hand-maintained, so it cannot drift; every feature module carries its own chain in a header comment). Recorded here because neither the frontend structure nor the i18n rule existed anywhere in the pipeline's documents, and both are the kind of convention that is very cheap to fix now and very expensive once a hundred hardcoded strings exist. | Implementation follow-up — krishna kategaru (autonomous), 2026-09-13. |

## Approval

Engineering Manager / Tech Lead — [x] Approved — krishna kategaru (autonomous), 2026-09-12
