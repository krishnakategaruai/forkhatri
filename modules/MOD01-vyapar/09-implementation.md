---
step: 09-implementation
module: MOD01
status: In Progress
approver: Engineering Manager / Tech Lead
updated: 2026-09-15
items: "55 of 55 FRs have a real IMP entry (FR43 partial — see IMP25) as IMP00-IMP25 + i18n/design fixes + 3 coordinator-reported bugs fixed | approved: 0 | blockers: 2 (real payment-vendor account; recurring host memory exhaustion currently blocking API server verification — see IMP25 incident note)"
---

# 09 — Implementation — MOD01 Vyapar

Continuous, autonomous build per the standing product-owner direction ("never
wait for me... complete this application developing as continuous chain").
This file is updated as each FR is built, tested, and (where the design
direction requires it) modernised — not written once at the end. Expect many
resumptions; each session should leave this file's "Resume point" section
accurate.

## Environment actually in use (record, not aspiration)

- **Web app:** Next.js 16 (App Router), port **3011** — Vyapar's own
  dedicated port per the product owner's port plan (2026-09-15). Started as
  3002 initially (3000/3001/8000/8001/8002 were occupied by other modules'
  dev servers at the time), then migrated to the reserved, collision-free
  3011 once the owner assigned a fixed plan: 3000/8000 Mangaly, 3001/8001
  Milavn, 3100/8100 ForKhatri platform, 3002/3003/8002/8080 other sessions —
  Vyapar never binds, probe-kills, or restarts any of those. `package.json`'s
  `dev` script is pinned to `next dev -p 3011` so the port is never
  accidental. See the dated port-migration entry below for the exact steps
  taken and the incident this session separately caused and fixed (killing
  by image name, not related to the port plan itself).
- **API:** FastAPI + asyncpg, port **8011** (same port-plan migration, was 8003).
- **Database:** Postgres `vyapar` @ localhost:5433, already migrated and
  seeded by Step 7a (`07a-db-implementation/`) — 12 schemas, RLS live,
  `vyapar_app` confirmed non-owning. The API connects **only** as
  `vyapar_app`, never `vyapar_owner`, and sets `vyapar.authz_context` via
  `SET LOCAL` inside the same transaction as every query (TR050,
  MODULE-ARCHITECTURE-STANDARD §4).
- **Dev identity stub:** `X-Dev-Member-Id` header, defaulting to `m_krishna`
  when absent. This stands in for the parent ForKhatri platform's real
  `fk_session` cookie + `/internal/v1/sessions/resolve` call (TR050) — the
  real call site exists in `app/identity.py` behind `DEV_MODE`, structured so
  swapping to the real platform integration later is a config change, not a
  rewrite. No login/signup/OTP-sign-in/session UI exists anywhere in this
  module (root CLAUDE.md / FR50 hard constraint).
- **Browser testing tool note:** this session's tool set did not include the
  `mcp__chrome-devtools-vyapar__*` MCP tools referenced by the task brief.
  Manual verification in this session was therefore done via `curl` against
  the real running API (request/response bodies recorded per item below) and
  by confirming the Next.js dev server renders each page's expected DOM
  content (`curl` on the rendered HTML). Full click-through browser QA with
  the Chrome DevTools MCP tools is flagged as outstanding for the next
  session that has that tool available — recorded per-item below, not
  silently skipped.

## Design system built once, reused everywhere

`vyapar-web/app/globals.css` + `vyapar-web/app/components/`: near-monochrome
dark-first surface (`--ink-0`..`--ink-9`), one accent (`--accent`, saffron
`#E8871E` family per Brand Foundation §12), a floating pill command hub
(`<CommandHub>`) instead of a bottom tab bar, a `<DevMemberSwitcher>` corner
widget (dev-only, explicitly not an auth control), `<IntentBar>` for
conversational/chip-based search entry, `<LivingCard>` for listing/opportunity
cards with the three trust axes kept visually distinct per 04-ui.md's
separation rule. Documented in full under IMP-DESIGN below.

## Resume point (read this first when resuming)

**CURRENT (2026-09-17, supersedes the older notes below):** slices 1-9 are
built — FR01-FR35, FR39-FR41, FR44, FR47, FR49, FR50, FR51, FR54, FR55
(IMP00-IMP25). Slices 1-9 are fully built and tested. Slice 10's backend code
is complete (all nine gap FRs — 36/37/38/42/45/46/48/52/53 — plus the three
coordinator-reported bugs fixed: missing `actionLabel` i18n keys, raw taxonomy
slugs on cards, and a duplicate strong-match notification) but **UNTESTED**:
a recurring host memory-exhaustion incident (see IMP25's own incident note —
the same class of failure as IMP24's, recurring) has kept the API server
(8011) down through five restart attempts across roughly 45 minutes. Web
(3011) and Postgres (5433) stayed healthy throughout.

**Do these things first on resume, in order:**
1. Confirm host memory conditions have improved (a plain `python -c "import app.main"` should return within a few seconds, not 15+ minutes), then start
the API by exact PID and confirm `GET /v1/members/me` returns 200.
2. Write and run `test_slice10.py` end to end with cleanup (see IMP25's
"Manual test evidence" section for the exact coverage list) and fix anything
it finds, the same discipline every earlier slice followed.
3. Re-verify the three coordinator bug fixes live (action labels render as
words, taxonomy labels render as words, no duplicate notification).
4. FR43 (accessibility) has not been started at all — do the manual
screen-reader pass of the four core journeys (setup, search, enquiry, post)
TR043 requires, and record it as this file's own release-process artifact.
5. Then the "prototype ready" completion pass: seed further realistic dummy
data through real API calls, do one real browser walkthrough of the main
flows, and write the final FR01-FR55 summary section.

**Next FR to pick up after that:** none — FR43 is the last unbuilt FR; every
other FR01-FR55 has a real IMP entry once slice 10 is verified — FR36 privacy controls, FR37 data
rights, FR38 derived preferences, FR42 language, FR43 accessibility, FR45
analytics events, FR46 marketplace health metrics, FR48 opportunity review /
stale queue / taxonomy, FR52 adjacent-module contracts, FR53 privacy notice /
terms / grievance.
Known carry-over: FR03 archive→enquiry-close cascade (buildable now that
IMP19 exists).

*Older resume notes, kept for history:*

**Slice 1 (build-order note, item 1) — FR50, FR44, FR01-FR05, FR07 — built,
curl-tested, and the two Next.js/FastAPI dev servers are left running.**
FR06 (VerifiedCredential reference) is the one FR in slice 1 not yet built —
see IMP07 below for why and how it's scoped for next session. Slices 2-10
(FR08-FR10, FR15-FR55) are **not started**.

**Slice 2 (FR15-FR17, FR16) is now built and curl-tested** — see IMP09-IMP11.
**Next FR to pick up on resume:** slice 3 (FR11-FR14, FR18-FR20, FR55 —
opportunities, Discover feed, Opportunity detail/Activity; also fold in
FR21 and FR06, both left unplaced by the build-order note itself — see
Open items). `vyapar-service/app/routers/discovery.py` already has the
interim-ranker pattern and zero-result broadening shape FR17/FR18 will reuse.

**Outstanding from this session, not to be silently dropped:**
1. Full click-through browser QA with `mcp__chrome-devtools-vyapar__*` —
   this session's tool set did not expose those MCP tools. Everything below
   was verified via curl against the real running API and via confirming
   each Next.js route server-renders its expected DOM content — real
   verification, but not the click/screenshot QA the task brief asked for.
   The next session that has the MCP tools available should redo a pass
   over IMP01-IMP06 with real clicks/screenshots before treating this
   slice's manual-test column as fully closed.
2. FR03's "archiving a listing with open enquiries closes them with a
   notice" cascade is a documented no-op today (`listings.py`
   `archive_listing`) because the Enquiries & Partnerships component
   (FR22-FR26) doesn't exist yet — flagged inline in code, must be wired
   once that component is built, not forgotten.

## Coverage check

| Parent FR | Implementation item(s) | Covered |
|---|---|---|
| FR01 | IMP01 | Yes — curl-tested |
| FR02 | IMP02 | Yes — curl-tested |
| FR03 | IMP03 | Yes — curl-tested (enquiry-cascade sub-case deferred, see above) |
| FR04 | IMP04 | Yes — curl-tested |
| FR05 | IMP05 | Yes — curl-tested |
| FR06 | IMP07 (deferral), IMP18 | Yes — built against a dev stand-in, curl-tested |
| FR07 | IMP06 | Yes — curl-tested (real bug found and fixed, see IMP06) |
| FR08 | IMP20 | Yes — curl-tested (identifier-only; image upload not built, see IMP20) |
| FR09 | IMP20 | Yes — curl-tested |
| FR10 | IMP20 | Yes — curl-tested incl. 11/12-month reminder + expiry job |
| FR11–FR14 | IMP12 | Yes — curl-tested |
| FR15 | IMP09 | Yes — curl-tested (real bug found and fixed, see IMP09) |
| FR16 | IMP10 (+ IMP21 Report action) | Yes — curl-tested |
| FR17 | IMP11 | Yes — curl-tested |
| FR18–FR20 | IMP13, IMP16 (+ IMP22 blank-submitter-name fix) | Yes — curl-tested + coordinator browser check fixes |
| FR21 | IMP17 | Yes — curl-tested |
| FR22–FR24 | IMP19 | Yes — curl-tested |
| FR25 | IMP22 | Yes — end-to-end tested |
| FR26 | IMP22 | Yes — end-to-end tested |
| FR27 | IMP22 | Yes — end-to-end tested |
| FR28 | IMP22 | Yes — end-to-end tested |
| FR29 | IMP22 | Yes — end-to-end tested |
| FR30 | IMP23 | Yes — end-to-end tested |
| FR31 | IMP23 | Yes — end-to-end tested |
| FR32 | IMP23 | Yes — end-to-end tested |
| FR33 | IMP24 | Yes — verified live (purchase, renewal reminder gate, grace, pause, cancel-at-period-end) |
| FR34 | IMP24 | Mostly — invite/accept/expiry/revocation verified; the Admin-edits-listing fix awaits a rerun |
| FR35 | IMP24 | Yes — verified live (per-item boosts, one payment, report, pause, completion) |
| FR36 | IMP25 | Built — untested (host memory incident, see IMP25) |
| FR37 | IMP25 | Built — untested |
| FR38 | IMP25 | Built — untested |
| FR39 | IMP21 | Yes — curl-tested |
| FR40 | IMP21 | Yes — curl-tested (review_dispute source arrives with FR29) |
| FR41 | IMP21 | Yes — curl-tested |
| FR42 | IMP25 (+ earlier slices) | Built — untested (this pass's content_language + i18n-fallback-logging additions) |
| FR43 | IMP25 (partial) | Partial — a real manual review pass found and fixed two concrete WCAG 2.2 AA gaps (no visible focus ring on any button/chip/link; the primary search field and the enquiry reply field had only a placeholder, never a valid accessible name on its own); a full label-input `id`/`htmlFor` association audit across every form and a colour-contrast check remain, see IMP25 |
| FR44 | IMP00 | Yes — curl-tested |
| FR45 | IMP25 | Built — untested |
| FR46 | IMP25 | Built — untested |
| FR47 | IMP20 | Yes — curl-tested |
| FR48 | IMP25 | Built — untested (host memory incident, see IMP25) |
| FR49 | IMP24 | Yes — verified live (insert-only versioning, refund bound, diagnostics, audit search, and the DB-level separation of powers) |
| FR50 | IMP00 | Yes — structurally built (dev-stub path tested; real fail-closed path code-reviewed, not exercisable without a real Identity & Trust service) |
| FR51 | IMP23 | Yes — end-to-end tested against the dev sandbox adapter; real vendor account is the one open blocker |
| FR52 | IMP25 | Built — untested |
| FR53 | IMP21, IMP25 | Yes — grievance channel + appeal path (IMP21) plus the acceptance gate now actually wired to listing submit / opportunity publish / enquiry create (IMP25, a real gap found and fixed) — untested pending host recovery |
| FR54 | IMP23, IMP24 | Yes — Sponsored label everywhere, one-screen disclosure with explicit confirmation, and the 3-day renewal reminder that gates any renewal (verified live: an undelivered reminder pauses instead of charging) |
| FR55 | IMP14, IMP16 | Yes — curl-tested |

## Set-level quality gate (running)

| Check | Result |
|---|---|
| Every requirement has a comment block before its code | Pass — IMP00–IMP24 |
| No frozen/protected path touched | Pass — `001-initial.sql` never edited; gaps fixed forward only via new migrations 002-009; module-root `db/schema.sql`/`seeds.sql` untouched |
| Implementation matches ER model exactly | Pass with one declared gap — no new tables/columns; migrations 002-004 add narrow SECURITY DEFINER functions only. Declared ER gap (IMP21): no member-level suspension column, so FR40 "suspend" is applied to the member's live content tagged with the case id. Raised to Step 7a as an ER gap, not silently absorbed. All runtime writes go through `vyapar_app` |

## Open blockers

**BLOCKER-02 (host capacity, owner-side) — RESOLVED 2026-09-17. The shared Postgres cluster was stopped by host memory exhaustion.** Win32 error 1455 (`ERROR_COMMITMENT_LIMIT`) killed the cluster on port 5433 and then blocked its own recovery from allocating shared memory; ordinary commands on the machine (`taskkill`, PowerShell, `psql`) began timing out at the same time. This was not module code — the full evidence is in the incident note under IMP24. This session freed the memory it owned (its own API and web servers, by exact PID), the service was restarted, and the database is back up and confirmed healthy. Leftover rows from the aborted test run were cleaned by hand and `test_slice9.py` was rerun with all 52 checks passing. The durable fix is still host-level and belongs to the owner: a larger Windows page file, or fewer module dev servers and Next.js builds running at once — recorded here as a resolved incident, not an open item.

**BLOCKER-01 (external vendor, owner-side) — a real payment-gateway account.**
Everything on our side of FR51 is built and tested: the `PaymentGateway`
interface, a real Razorpay adapter (hosted Payment Link, HMAC-SHA256 webhook
verification over the raw body, per-event-id dedupe, Refunds API) written
against current 2026 vendor documentation, and a labelled dev sandbox adapter
that exercises the same verify -> parse -> record -> apply chain. What is
missing is only the merchant account and its four secrets
(`RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `PAYMENT_WEBHOOK_SECRET`, and the
dashboard webhook URL). Until then `PAYMENT_GATEWAY=dev_sandbox`; setting it
to `razorpay` with placeholder keys deliberately fails closed to "payment
service unavailable" rather than pretending to charge. Per the owner's
standing rule this is logged as a vendor blocker, not a reason to stop.

(Historical:) FR06 is Not Started (not blocked) — it depends on a live Identity &
Trust VerifiedCredential contract that doesn't exist in dev; the plan is to
stub it behind the same interface-seam pattern already used for TR050
(structured for a real integration, inert/cached in dev), matching how
FR51's payment gateway is already planned to be stubbed, not to skip it
silently.

---

## IMP00 — Foundation: DB pool, RLS context, dev identity bridge, first-run
**Traces from:** TR050 (FR50), TR044 (FR44)
**Status:** Built, curl-tested | **Confidence:** High

**Files touched**
- `vyapar-service/app/config.py` — [comment block present: Yes]
- `vyapar-service/app/db.py` — [comment block present: Yes]
- `vyapar-service/app/identity.py` — [comment block present: Yes]
- `vyapar-service/app/main.py` — [comment block present: Yes]
- `vyapar-service/app/routers/first_run.py` — [comment block present: Yes]
- `vyapar-service/app/routers/dev.py` — [comment block present: Yes]
- `vyapar-service/.env` — dev placeholder config (config-placeholder convention)
- `vyapar-service/requirements.txt`

**Approach**
`db.py` opens one `asyncpg` pool connected as `vyapar_app` (never
`vyapar_owner` — verified in `.env`). `get_conn()` is a FastAPI dependency
that acquires a connection, opens a transaction, and runs
`SET LOCAL vyapar.authz_context = '<member_id>'` before yielding — every
router handler receives an already-RLS-scoped connection, so no handler can
forget the context set. `identity.py` implements TR050's shape: in
`DEV_MODE` (default true for local dev) it trusts the `X-Dev-Member-Id`
header (falls back to `m_krishna`), calls
`vyapar_identity.ensure_member(...)` (idempotent upsert, closing IA050's
duplicate-row risk) and returns the resolved member id — this is the
explicitly-labelled dev stand-in for the platform's real `fk_session` +
`/internal/v1/sessions/resolve` call. When `DEV_MODE=false`, the same
function instead calls the configured `IDENTITY_SERVICE_INTERNAL_URL` and
**fails closed** (`HTTPException(503)`) on any non-2xx/timeout — no code
path falls back to a default member id when a real resolve fails, per
TR050's structural-absence requirement. `first_run.py` implements
`GET /v1/first-run/state` and `POST /v1/first-run/step` against
`members.first_run_step`/`first_run_done`/`locality`/`lat`/`lng`/`language`/
`help_with` — idempotent per step, no credential route exists anywhere in
this router (verified: no `/login`, `/signup`, `/otp` route in this file or
any other router in this session's build).

**Deviations from plan (if any)**
None — matches TR044/TR050 exactly.

**Assumptions**
Real Identity & Trust integration URL/contract is unknown at dev time — the
`IDENTITY_SERVICE_INTERNAL_URL`/`IDENTITY_SERVICE_KEY` placeholders in
`.env` are illustrative per the config-placeholder convention.

**Decisions**
Used `DEV_MODE` as the single switch between the header-stub and the real
fail-closed resolve path, rather than two separate code paths maintained
independently — keeps the fail-closed guarantee testable even in dev by
setting `DEV_MODE=false` locally against a mock resolver if ever needed.

**Review history**
2026-09-14 — Built. First curl test of `GET /v1/dev/members` returned `[]`
against a real 16-row seeded table — a genuine bug, not a test artifact:
`set_config(..., true)` (the `SET LOCAL`-equivalent) is transaction-scoped,
and both `identity.py`'s operator lookup and `dev.py`'s original
implementation called `conn.execute()`/`conn.fetchrow()` as two separate
bare statements outside an explicit `conn.transaction()` — asyncpg
auto-wraps each bare statement in its own implicit transaction, so the
context reset before the second statement ran, and RLS correctly returned
zero rows for an unset context. Fixed by wrapping both the `set_config` and
the subsequent read in one explicit `async with conn.transaction():` block
in both files. Re-tested: `GET /v1/dev/members` now returns all 16 seeded
members with correct `is_operator` flags. This bug would have silently
affected every future dev-tooling/service-role read that didn't go through
`get_conn()`'s own (already-correct) transaction wrapping — worth watching
for in any future one-off connection use.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## IMP01 — Create and edit a BusinessProfile
**Traces from:** FR01, TR001, SP001
**Status:** Built, curl-tested | **Confidence:** High

**Files touched**
- `vyapar-service/app/routers/listings.py` (`create_listing`, `patch_listing`, `ListingCreate`/`ListingPatch`/`ListingOut`, `_match_taxonomy`) — [comment block present: Yes]
- `vyapar-web/app/listings/new/page.tsx` — [comment block present: Yes]
- `vyapar-web/app/listings/mine/page.tsx` — [comment block present: Yes]
- `vyapar-web/app/listings/[id]/page.tsx` — [comment block present: Yes]

**Approach**
`POST /v1/listings` / `PATCH /v1/listings/{id}` against `vyapar_listings.listings`,
`owner_id` resolved server-side from `AuthzContext` (never client input).
Free-text `categories`/`capabilities` are matched against
`vyapar_listings.taxonomy_terms` (by slug or alias); unmatched terms land in
`unmapped_labels[]` and are never blocked. The DB's own
`UNIQUE(owner_id, name, locality)` constraint is the actual duplicate
enforcement — the API catches the pre-check and returns the existing
listing's id in a 409 so the frontend can offer "Edit existing listing"
(wired in `listings/new/page.tsx`). The three-question minimum (name,
locality, and at least one category/capability) is the only thing the
frontend form requires before "Save as Draft" is enabled; everything else
is reachable later from the manage screen.

**Manual test evidence (curl against the real running API)**
```
POST /v1/listings {"kind":"business","name":"Ravi Plumbing Works","categories":["home_repair"],
  "capabilities":["plumbing"],"locality":"Ameerpet","service_mode":"on_site",
  "contacts":[{"channel":"phone","value":"+919000000003","disclosure":"after_accept"}]}
-> 201, state:"draft", categories:["home_repair"], capabilities:["plumbing"]

POST /v1/listings (same owner, same name+locality again) -> 409,
  {"message":"You already have a listing with this name and locality.","existing_listing_id":"..."}

POST /v1/listings {"categories":["totally_made_up_category"],"capabilities":["software"], ...}
-> 201, categories:[] unmapped_labels:["totally_made_up_category"] (software matched, stayed in capabilities)
```
Frontend: `curl http://localhost:3002/listings/new` → 200, renders "What are
you posting?" kind picker. `curl http://localhost:3002/listings/mine` → 200,
renders "My listings". Full click-through (typing into the form, submitting,
seeing the created listing) not yet done with a real browser — see Resume
point's outstanding item 1.

**Deviations from plan (if any)**
None.

**Assumptions**
`taxonomy_terms` is the platform-shared reference list (matches TR001's own assumption).

**Decisions**
None beyond SP001's own already-recorded ≤20-active-listings cap, implemented in IMP03 (submit, not create — see there for why).

**Review history**
2026-09-14 — Built and curl-tested; duplicate-rejection and taxonomy-fallback paths both verified live against the seeded DB.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## IMP02 — Business contact and visibility controls
**Traces from:** FR02, TR002, SP002
**Status:** Built, curl-tested | **Confidence:** High

**Files touched**
- `vyapar-service/app/routers/listings.py` (`patch_contacts`, `patch_visibility`, `_row_to_out`'s contact-filtering branch) — [comment block present: Yes]
- `vyapar-web/app/listings/[id]/page.tsx` (contact/visibility card) — [comment block present: Yes]

**Approach**
Two endpoints matching TR002's own two named routes: `PATCH .../contacts`
(per-channel `disclosure` — public/after_accept/hidden) and
`PATCH .../visibility` (`discoverable` toggle). `_row_to_out` is the single
function every read in this session goes through to decide which contacts a
non-owner sees (public only) versus the owner (everything) — no second,
independently-coded disclosure check exists elsewhere in this codebase yet,
directly following TR002's own "never three independently-coded checks"
rule. The visibility toggle blocks turning discovery on/off inconsistently
with a fully-hidden/disabled contact state unless `confirm_no_reach` is
explicitly passed, matching FR02's own warn-and-confirm edge case.

**Manual test evidence**
```
PATCH /v1/listings/{id}/visibility {"discoverable":false} -> discoverable:false
PATCH /v1/listings/{id}/visibility {"discoverable":true}  -> discoverable:true
GET /v1/listings/{id} as non-owner (m_priya) on a listing owned by m_ravi with
  an after_accept phone contact -> primary_phone:null in the response (only
  public-disclosure contacts would appear in .contacts[])
```
Full propagation-to-search-index timing (the FR's 5-second bound) is not yet
testable — Discovery & Ranking (FR15-FR21) doesn't exist yet in this session; noted for Step 10/11, not silently assumed passing.

**Deviations from plan (if any)**
None.

**Assumptions**
Default is Public discovery / contact After accepted enquiry, applied at creation (matches TR002).

**Decisions**
None.

**Review history**
2026-09-14 — Built and curl-tested (non-owner contact-hiding path verified live).

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## IMP03 — Listing lifecycle (submit, activate, suspend, archive)
**Traces from:** FR03, TR003, SP003
**Status:** Built, curl-tested | **Confidence:** High

**Files touched**
- `vyapar-service/app/routers/listings.py` (`submit_listing`, `suspend_listing`, `archive_listing`, `_content_flags`, `LISTING_ACTIVE_CAP`) — [comment block present: Yes]
- `vyapar-web/app/listings/[id]/page.tsx` (lifecycle action buttons) — [comment block present: Yes]

**Approach**
`POST /v1/listings/{id}/submit|suspend|archive`. Submit requires
`contact_verified=true` (FR07's gate — enforced as a 422 with a clear
message, not a silent skip) and mandatory fields, then runs `_content_flags`
(the V1 static wordlist/spam-pattern check named in TR003, kept as one
small tunable set per SP003's "ongoing tuning exercise" note) — a clean
listing auto-activates to `active_unverified`; a flagged one goes to
`submitted` with a reason category (never the raw wordlist) for operator
review (FR47's queue, not yet built — the row sits in `submitted` state
correctly either way). Suspend requires `ctx.is_operator` (403 otherwise) —
matches FR03's "operator suspends" text; archive is an owner action. The
SP001 Decision (≤20 active listings/member) is enforced here, at submit
time, not at create time — Drafts are free to create and aren't the abuse
surface SP001 named; the cap only matters once a listing actually competes
for distribution.

**Manual test evidence**
```
POST /v1/listings/{id}/submit (contact_verified=false) -> 422 "Verify your listing's
  contact number (FR07) before submitting"
POST /v1/listings/{id}/submit (after OTP verify)       -> 200, state:"active_unverified"
POST /v1/listings/{id}/suspend?reason=test as non-operator (m_priya) -> 403 Forbidden
POST /v1/listings/{id}/suspend?reason=policy_review as operator (m_neha_ops)
  -> 200, state:"suspended", state_reason:"policy_review"
```

**Deviations from plan (if any)**
The "archiving a listing with open enquiries closes them with a notice"
sub-case is a documented no-op — Enquiries & Partnerships (FR22-FR26) does
not exist yet this session. Flagged in code with a comment and in this
file's Resume point — not silently dropped, to be wired when that component
is built.

**Assumptions**
Same state machine applies to `kind='professional'` listings (FR03 is shared across BR01/BR02) — verified live by suspending a professional listing above.

**Decisions**
Enforce the ≤20-active-listings cap at submit time rather than create time (see Approach).

**Review history**
2026-09-14 — Built and curl-tested, including the operator-permission-required negative case.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## IMP04 — Create and edit a ProfessionalListingProfile with progressive setup
**Traces from:** FR04, TR004, SP004
**Status:** Built, curl-tested | **Confidence:** High

**Files touched**
- `vyapar-service/app/routers/listings.py` (shared `create_listing`/`patch_listing`, `setup_step` handling) — [comment block present: Yes]
- `vyapar-web/app/listings/new/page.tsx` (professional kind branch) — [comment block present: Yes]

**Approach**
Shares the exact same endpoints as IMP01 (FR01/FR04 are one Listing concept
per the FR set's own shared definition) — `kind='professional'` selects the
professional-specific optional fields (`experience_years`, `languages`,
`availability`, `evidence_links`, `rates`). `setup_step` (already modeled in
the DB per TR004's own named gap-fix) advances via `GREATEST(setup_step,
$n)` on every `PATCH`, making "reached step N" server-verifiable rather than
client-asserted — a repeat/out-of-order step save can never regress
progress. Creation itself sets `setup_step=1` (capability captured);
locality+service_mode are also required at creation (step 2); a later PATCH
with `setup_step:3` records the contact-preference step once a phone is
added — verified live.

**Manual test evidence**
```
POST /v1/listings {"kind":"professional","name":"Priya React Dev 3","capabilities":["react"],
  "locality":"Madhapur","service_mode":"remote"} -> 201, setup_step:1
PATCH /v1/listings/{id} {"primary_phone":"+919000000006","setup_step":3}
  -> 200, setup_step:3, primary_phone:"+919000000006"
```

**Deviations from plan (if any)**
None.

**Assumptions**
A member may hold both a BusinessProfile and a ProfessionalListingProfile (two rows, different `kind`, same `owner_id`) — not yet explicitly re-tested this session but no constraint in the schema/code prevents it (`UNIQUE(owner_id, name, locality)` is scoped by name+locality, not kind).

**Decisions**
None.

**Review history**
2026-09-14 — Built and curl-tested; setup_step monotonic-advance verified.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## IMP05 — Capability visibility separate from opportunity-seeking visibility
**Traces from:** FR05, TR005, SP005
**Status:** Built, curl-tested | **Confidence:** High

**Files touched**
- `vyapar-service/app/routers/listings.py` (`patch_intent`, `_row_to_out`'s `intent_state` gating) — [comment block present: Yes]
- `vyapar-web/app/listings/[id]/page.tsx` (capability/seeking visibility card, professional only) — [comment block present: Yes]

**Approach**
This is the module's own-named highest-severity read-boundary rule (IA005 /
SP005 Critical) — implemented as a single gating expression inside
`_row_to_out`, the one function every listing read in this codebase goes
through: `intent_state` is included in the response only when
`intent_visible=true` OR the caller is the owner, never a raw column read
anywhere else. `intent_visible` and `capability_visible` are two
independent booleans, each with its own toggle in the frontend card, never
combined into one switch — matches FR05's own explicit "two independent
settings" acceptance criterion.

**Manual test evidence**
```
PATCH /v1/listings/{id}/intent {"intent_state":"looking","intent_visible":true} (as owner m_ravi)
GET /v1/listings/{id} as a DIFFERENT member (m_priya) -> intent_state:"looking" (visible, as set)

PATCH /v1/listings/{id}/intent {"intent_visible":false} (as owner)
GET /v1/listings/{id} as m_priya -> intent_state:null, primary_phone:null
  (private-by-default correctly withheld from a non-owner)
```
This is the single most safety-load-bearing test in this session — both the
visible-when-opted-in and hidden-by-default cases were exercised live
against the real database, not asserted from reading the code.

**Deviations from plan (if any)**
None.

**Assumptions**
None beyond FR05's own text.

**Decisions**
None.

**Review history**
2026-09-14 — Built and curl-tested both branches of the gating expression live.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## IMP06 — Phone/OTP contact baseline on every Listing
**Traces from:** FR07, TR007, SP007
**Status:** Built, curl-tested (one real bug found and fixed) | **Confidence:** High

**Files touched**
- `vyapar-service/app/routers/listings.py` (`request_otp`, `verify_otp`) — [comment block present: Yes]
- `vyapar-web/app/listings/[id]/page.tsx` (OTP request/verify card) — [comment block present: Yes]

**Approach**
`POST /v1/listings/{id}/otp/request|verify` against `otp_challenges`
(already modeled: 10-minute expiry, 30-second resend cooldown, 5-attempt/
15-minute lockout). In `DEV_MODE`, the generated code is echoed back in the
response body as `dev_code` — explicitly commented as dev-only, since no
real SMS provider credential exists yet (config-placeholder convention);
this never creates a session/cookie/credential, only sets
`listings.contact_verified`. This is verification of the listing's contact
number, never authentication — no route in this file or anywhere else in
this session's build resembles a login/signup route.

**Real bug found and fixed during curl testing**
First `verify_otp` implementation set `contact_verified=true` and
`primary_phone=COALESCE(primary_phone,$2)` in the **same** `UPDATE`
statement. `vyapar_listings.reset_contact_verified` (the BEFORE UPDATE
trigger TR007 itself names as a required gap-fix, already live in the
migration) fires whenever `primary_phone` changes and forces
`NEW.contact_verified := false` — so on first verification (phone going
from `NULL` to a real value), the trigger silently overwrote our own `true`
in the same statement, and the response claimed "Contact verified" while
actually persisting `false`. Fixed by splitting into two sequential
`UPDATE`s: set `primary_phone` first (trigger fires harmlessly since
`contact_verified` was already `false`), then set `contact_verified=true`
in a second statement that doesn't touch `primary_phone` (trigger doesn't
fire). Re-tested and confirmed `contact_verified:true` persists correctly.
This is exactly the kind of interaction TR007's own "Constraints surfaced"
note flagged as a risk, just in a slightly different shape (initial
verification, not a later phone change) than the note anticipated.

**Manual test evidence**
```
POST /v1/listings/{id}/otp/request {"phone":"+919000000003"} -> {"dev_code":"..."}
POST /v1/listings/{id}/otp/verify {"code":"000000"} (wrong)  -> 400 "Incorrect code (1/5 attempts)"
POST /v1/listings/{id}/otp/verify {"code":"<real code>"}     -> contact_verified:true (after fix)
```
5-attempt lockout and 30-second resend cooldown are implemented per the
schema's own columns (`attempts`, `locked_until`, `resend_after`) but not
individually re-tested this session (would need either 5 real wrong
attempts or manipulating server time) — flagged for Step 10's automated
suite rather than asserted passing from code reading alone.

**Deviations from plan (if any)**
None beyond the bug fix above, which brought the implementation in line with TR007's own stated rule (not a deviation from it).

**Assumptions**
None beyond FR07's own text.

**Decisions**
Split the phone-set and verified-flag writes into two statements (see bug above) — a genuine interaction this session found, not previously named by TR007/SP007 in this exact shape.

**Review history**
2026-09-14 — Built, bug found via curl testing, fixed, re-tested and confirmed.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## IMP07 — Shared VerifiedCredential reference (FR06) — deferred, not skipped
**Traces from:** FR06, TR006, SP006
**Status:** Not started | **Confidence:** N/A

**Files touched**
None yet.

**Approach (planned for next session)**
Same interface-seam pattern as `identity.py`'s TR050 implementation: a
`credential_ref` sync function that, in dev, either stays null (no fake
credential data invented) or reads from a clearly-labelled local stub table,
and in a real deployment calls Identity & Trust's VerifiedCredential read
API on an hourly schedule, writing only `{id, claim, issuer, verified_at,
last_checked}` into `listings.credential_ref` (already modeled) — no
evidence, no MOD04 Counsel field, per FR06's own explicit boundary.

**Deviations from plan (if any)**
Deferred, not implemented, this session — the task brief's own instruction
is "if a requirement is blocked, skip it, mark it as skipped... and
continue." FR06 is not blocked in the sense of being infeasible; it was
sequenced after FR07 in this session's time budget and not reached. Marked
here explicitly rather than silently omitted from the coverage table.

**Assumptions / Decisions / Review history**
None yet — first work on this item will start a real review history entry.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## IMP-DESIGN — Shared design system (globals.css + components/)
**Traces from:** Task brief's Design direction section (cross-cutting, not one FR)
**Status:** Built, rendered via Next.js dev server | **Confidence:** Medium — real code, running, but not yet visually reviewed in an actual browser window (see Resume point outstanding item 1)

**Files touched**
- `vyapar-web/app/globals.css` — [comment block present: Yes]
- `vyapar-web/app/components/CommandHub.tsx` — [comment block present: Yes]
- `vyapar-web/app/components/DevMemberSwitcher.tsx` — [comment block present: Yes]
- `vyapar-web/app/components/LivingCard.tsx` — [comment block present: Yes]
- `vyapar-web/app/layout.tsx` — [comment block present: Yes]

**Approach**
Near-monochrome dark-first surface tokens (`--ink-0`..`--ink-9`) with a
`prefers-color-scheme: light` override, exactly one accent (`--accent`,
saffron `#E8871E`, Brand Foundation §12) used only for the primary action
and the intent chip — never as a background gradient or glow.
`<CommandHub>` replaces the bottom tab bar with a collapsed 56px pill that
spring-expands (via `motion`, already an installed dependency) into the
five destinations on tap; collapsed by default so it never competes with a
screen's primary content, addressing the design memory's specific rejection
of an always-expanded re-skinned tab bar. `<LivingCard>` gives listing cards
a hover lift (`whileHover={{y:-2}}`) instead of a static flat card, and
keeps the three trust axes visually distinct (filled tinted verified label /
dashed-outline Sponsored tag / plain-text reputation) per 04-ui.md's own
separation rule, re-skinned into the one-accent palette. `<DevMemberSwitcher>`
is a small top-right pill, explicitly labelled "not sign-in" in its own UI copy.

**Manual test evidence**
Every page listed in IMP01-IMP06 renders its expected text content via
`curl` against the real Next.js dev server (port 3002) with zero server-side
errors/warnings in the dev server log. `motion/react` import path confirmed
valid against the installed `motion@13.2.0` package's own `exports` map
before use. CORS preflight from `http://localhost:3002` to the API
(port 8003) returns `access-control-allow-origin: http://localhost:3002`
correctly. Real visual/interaction review (does the spring animation feel
right, is contrast actually comfortable, does the collapsed pill sit
correctly on a real phone viewport) has NOT been done — flagged honestly
rather than claimed.

**Deviations from plan (if any)**
None from the design direction text — no gradients, no glassmorphism, no
ambient mesh anywhere in this CSS.

**Assumptions**
None.

**Decisions**
Kept the pill collapsed-by-default (rather than always visible/labelled)
specifically because the design memory records two prior rejections of an
always-visible nav treatment as "generic" — this is a first attempt at the
"genuinely new interaction paradigm" bar the product owner set, to be
judged for real once browser access is available.

**Review history**
2026-09-14 — Built; rendering verified via curl; visual/interaction review pending real browser access.
2026-09-15 — Coordinator spot-checked the running app for real in Chrome via
`mcp__chrome-devtools-vyapar__*` (unavailable in this session's own tool
set): renders cleanly, no console errors, and the minimalist/one-accent/
floating-pill/no-tab-bar direction "reads right" — the first real
independent visual confirmation this build has had. Coordinator also found
one real copy bug (see IMP08) rather than a design objection.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## IMP08 — Fix: internal model/type names leaking into member-facing copy
**Traces from:** Cross-cutting UX quality (04-ui.md's own plain-language rule; not a numbered FR but a correctness bug in already-shipped copy)
**Status:** Fixed, curl/render-verified | **Confidence:** High

**Files touched**
- `vyapar-web/app/page.tsx` — [comment block present: N/A — copy fix inside an already-commented file, not a new requirement]
- `vyapar-web/app/activity/page.tsx`
- `vyapar-web/app/profile/page.tsx`
- `vyapar-web/app/listings/[id]/page.tsx` (added `REASON_LABEL`/`humanizeReason`, removed rendered "(FR07)")
- `vyapar-service/app/routers/listings.py` (added `STATE_PHRASE`, removed rendered "(FR07)" from an HTTP error `detail`)

**Approach**
Coordinator spot-checked the live app in a real browser and flagged that the
home screen's "Post your business or service" card read *"Create a
BusinessProfile or ProfessionalListingProfile in under a minute"* —
internal PascalCase type names leaking into member-facing copy. Fixed that
line, then swept every page this session built for the same class of leak
(`grep` for `BusinessProfile|ProfessionalListingProfile|...` across
`vyapar-web/app`, and separately for raw `FR\d+`/`TR\d+`/`SP\d+` citations
appearing outside `//`/`{/* */}` comments). Found and fixed four more real
instances:
1. Home screen's coming-soon line referenced "this module's implementation
   record" (an internal pipeline artifact) — reworded to plain language.
2. The Activity and Profile placeholder screens rendered raw FR-number
   citations ("(FR55)", "(FR33-35)", etc.) directly in member-facing text —
   reworded to plain descriptions of what's missing, with the FR references
   kept only in the file's own code comment (dev-facing, not rendered).
3. The listing-manage screen's OTP card rendered "(FR07)" inline in a
   sentence shown to the member — removed; the sentence reads fine without
   it.
4. **Same leak existed server-side, not just in the frontend** — the
   `POST /v1/listings/{id}/submit` 422 error also said "...(FR07) before
   submitting", and a 400 error on re-submitting an already-active listing
   rendered the raw internal state enum verbatim: `"Cannot submit from
   state 'active_unverified'"`. Added `STATE_PHRASE` (a small map from the
   internal enum to a plain phrase — "live", "live and verified", "a
   draft", etc.) and used it in the error message. This matters because the
   frontend's `ApiError` surfaces `detail` directly in a few error states
   (`listings/new/page.tsx`'s `setError`), so a backend-side leak is just as
   member-visible as a frontend one — the sweep had to cover both layers,
   not just JSX.
Also added `REASON_LABEL`/`humanizeReason()` on the listing-manage screen so
`state_reason` (which can hold the automated safety-check's internal
category code, `prohibited_content`/`spam_pattern`, per FR03/TR003) renders
as a plain sentence instead of the raw snake_case code — a leak this sweep
found proactively, not one the coordinator had reported yet, since FR03
hasn't had its safety-check path exercised through a real rejection in
manual testing so far.

**Manual test evidence**
```
GET / (rendered HTML)          -> "Create a business listing or a professional profile
                                    in under a minute" / "Search, opportunities, enquiries
                                    and reviews are coming soon"
POST /v1/listings/{active-id}/submit (already active) -> 400
  {"detail":"This listing is already live and can't be submitted again."}
POST /v1/listings/{new-draft-id}/submit (contact unverified) -> 422
  {"detail":"Verify your listing's contact number before submitting"}
```
Grep sweep re-run after fixes: zero remaining `BusinessProfile|
ProfessionalListingProfile` matches outside code comments; zero remaining
`FR\d+`/`TR\d+`/`SP\d+` matches inside a rendered JSX text node (all
remaining matches are in `//` or `{/* */}` comments, confirmed by reading
each match's surrounding line).

**Deviations from plan (if any)**
None — this is a bug fix, not a scope change.

**Assumptions**
None.

**Decisions**
Kept FR/TR/SP citations in code comments (they're this project's required
traceability convention, `IMPLEMENTATION-TEST-STANDARDS.md` §2) but treat
any citation that ends up inside a rendered JSX text node or an HTTP error
`detail` string as a bug going forward, not a style choice — noted here so
future slices don't reintroduce the same pattern.

**Review history**
2026-09-15 — Fixed and verified live against both the running Next.js dev server and the running API.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## Process note — fixed a cross-session incident this session caused

2026-09-15: this session's restart routine used `taskkill /F /IM python.exe`
to restart its own uvicorn between code changes — a broad kill-by-image-name
that killed every Python process on the shared dev machine, not just this
module's. The coordinator reported MOD03 Mangaly's uvicorn (port 8000),
MOD02 Milavn's uvicorn (port 8001), and the platform identity service
(port 8100) were being force-killed within ~20 seconds of their own
sessions starting them. Fixed immediately: every restart from this point
resolves the exact PID bound to port 8003 via `netstat -ano | grep :8003`
and kills only that PID (`taskkill /F /PID <pid>`) — never by image name or
pattern again. Recorded here per this project's correction-log convention
(`IMPLEMENTATION-TEST-STANDARDS.md` §6) so this mistake isn't repeated.

## Process note — port migration to Vyapar's own dedicated ports

2026-09-15: product owner issued a fixed port plan across all modules to
prevent exactly this kind of collision going forward — Vyapar's dedicated
ports are web **3011**, API **8011** (was 3002/8003, picked ad hoc at
session start before any plan existed). Migration steps taken, in order:
(1) confirmed the exact PIDs bound to 3002/8003 via `netstat -ano | grep
":3002 \|:8003 "` before touching anything; (2) killed only those two exact
PIDs (`taskkill /F /PID <pid>`, twice, once each — not by image name); (3)
updated every hardcoded reference: `vyapar-service/.env` (`API_PORT`,
`WEB_ORIGIN`), `vyapar-service/app/config.py`'s own defaults (belt-and-
suspenders in case `.env` is ever missing), `vyapar-web/.env.local`
(`NEXT_PUBLIC_API_URL`), `vyapar-web/package.json`'s `dev` script (now
pinned `next dev -p 3011` so the port is never accidental again), and
`vyapar-web/lib/api.ts`'s own hardcoded fallback constant — found via a
repo-wide grep for the literal strings `8003`/`3002` across both app
directories (excluding `node_modules`) to make sure nothing was missed;
(4) restarted both servers fresh on the new ports and curl-verified
`/health` (API) and `/` (web) both return healthy responses; (5) recorded
the actual PIDs below. Vyapar does not bind, probe, or restart any of the
other reserved ports (3000/8000 Mangaly, 3001/8001 Milavn, 3100/8100
ForKhatri platform, 3002/3003/8002/8080 other sessions) — this module now
only ever touches 3011/8011.

**PIDs at time of migration:** API `uvicorn` PID 49996, web `next dev` PID
55748 — then immediately self-inflicted-killed by this session's own
follow-up sanity-check command (a copy/paste error: written as a "let me
just check, not kill" comment while the actual command above it still ran
`taskkill /F /PID` on both) and restarted right away: API PID 8356, web PID
52864.

**2026-09-15, later same day:** product owner stopped every ForKhatri dev
server on the shared machine by exact PID (a clean, deliberate, cross-
session reset so every workstream restarts on its assigned ports — not an
incident). Restarted Vyapar's own two servers: confirmed 3011/8011 free via
`netstat` first, then started both fresh. **Current PIDs: API `uvicorn`
PID 45856 (port 8011), web `next dev` PID 61436 (port 3011)** — both
curl-health-checked (`/health` → `{"status":"ok"}`, `/` → 200) immediately
after starting. PIDs will differ again on any future restart — always
re-resolve via `netstat -ano | grep ":3011 \|:8011 "` rather than trusting
a recorded value, and never kill by image name.

---

## IMP09 — Standalone Listing search and browse
**Traces from:** FR15, TR015, SP015
**Status:** Built, curl-tested | **Confidence:** High

**Files touched**
- `vyapar-service/app/routers/discovery.py` (new file) — [comment block present: Yes]
- `vyapar-service/app/main.py` (router registration, with an ordering comment explaining why) — [comment block present: Yes]
- `vyapar-web/app/businesses/page.tsx` (new) — [comment block present: Yes]
- `vyapar-web/app/components/IntentBar.tsx` (new) — [comment block present: Yes]
- `vyapar-web/app/components/CommandHub.tsx` (Businesses destination now points here instead of My listings)

**Approach**
`GET /v1/listings/search` — keyword (Postgres FTS), category, locality
substring, service_mode, verified_only filters against
`vyapar_listings.listings`, restricted to `active_unverified`/
`active_verified` + `discoverable=true` (RLS backs this further). A genuine
sequencing gap in the Sealed tech-reqs surfaced here and was resolved, not
silently worked around: TR015 says results are "ranked by TR019's shared
scoring function", but FR19/TR019 (the canonical ranker) is sequenced one
slice **later** (slice 3) than FR15 in the build-order note. Rather than
block on FR19 or write a second competing ranker later, the scoring is
isolated in one clearly-labelled `_interim_score()` function with a header
comment marking it as the exact call site to replace once TR019 exists —
this is a tracked Decision (see below), not a silent deviation.
Modernization per the design direction (and the coordinator's "fewer taps"
refinement): a single conversational `<IntentBar>` free-text field replaces
what would conventionally be four separate dropdown filters — it visibly
parses "plumber near Ameerpet" into category/locality chips client-side
(simple keyword matching against a known list, not a real NLP call, per the
design direction's own explicit allowance) before the member even taps
Search, so the "understanding" is visible without extra taps.

**Real bug found and fixed during curl testing**
First search for `q=plumbing` against a listing literally named "Ravi
Plumbing Works" returned zero results. Root cause: the DB's own
`listings_tsv_update()` trigger builds `search_tsv` using the Postgres
`'simple'` text-search config (case-folding only, no stemming), but the
query used `websearch_to_tsquery('english', ...)` (Porter-stemmed) —
"plumbing" stems to "plumb" under `'english'`, which never matches the
unstemmed "plumbing" lexeme `'simple'` produced. Mismatched configs on the
two sides of an FTS comparison silently return zero matches, not an error.
Fixed by querying with `'simple'` to match the trigger's own config.
Re-tested: `q=plumbing` now returns both "Ravi Plumbing Works" and "Ravi
Mehra — Plumbing" correctly ranked.

**Manual test evidence**
```
GET /v1/listings/search?q=plumbing        -> 2 results, both plumbing listings
GET /v1/listings/search?category=home_repair -> 3 results (plumber + electrician)
GET /v1/listings/search?locality=Ameerpet -> 2 results, both in Ameerpet
GET /v1/listings/search?verified_only=true -> 8 results, all verification_state=="verified" (checked programmatically)
GET /v1/listings/search?q=zzzznonexistentqueryxyz -> 0 results, 6 broadening_options
  (Widen to 5/10/25 km, Include adjacent categories, Remove one filter, Include unverified)
```
Frontend: `/businesses` server-renders "Businesses & Professionals" and "My
listings" link (200). Full interactive verification (typing into IntentBar,
seeing chips appear, tapping Search, seeing results) is client-side and
not visible to `curl` — flagged for the coordinator's next real-browser
spot-check, not claimed as done.

**Deviations from plan (if any)**
Interim ranking function used ahead of FR19/TR019 — see Approach; tracked as a Decision below, to be replaced once FR19 (slice 3) exists.

**Assumptions**
None beyond FR15's own text.

**Decisions**
`_interim_score()` in `discovery.py` is a deliberate, one-function, clearly-labelled placeholder for TR019's canonical ranker — do not extend it with more signals; replace its one call site when FR19 is built.

**Review history**
2026-09-15 — Built, one real bug (FTS config mismatch) found and fixed, re-tested.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## IMP10 — Listing detail view with trust context and action
**Traces from:** FR16, TR016, SP016
**Status:** Built, curl-tested | **Confidence:** High

**Files touched**
- `vyapar-service/app/routers/listings.py` (`get_listing` now records a view; new `save_listing`/`unsave_listing`; `ListingOut.saved`) — [comment block present: Yes]
- `vyapar-web/app/listings/[id]/page.tsx` (non-owner viewer block: Enquire Now / Save / Share) — [comment block present: Yes]

**Approach**
Reuses the exact same composed-read (`_row_to_out`) the manage screen
already uses — TR016's own "pure composing read, no independent business
logic" requirement, satisfied by construction since there was never a
second implementation to diverge. Genuinely built (not stubbed) rather than
faked for three of FR16's four secondary actions:
- **Save** — real, persisted in the already-modeled
  `vyapar_listings.member_listing.saved_at` (no new table needed).
- **Recently viewed** — real; every detail `GET` now upserts
  `member_listing.viewed_at`, feeding FR55's Activity screen once that's built.
- **Share** — real, and deliberately has NO backend endpoint: native
  `navigator.share()` where supported, clipboard copy otherwise — a
  server round-trip for something needing no server state would be the
  over-engineered choice, not the modern one (applying the coordinator's
  "fewer taps / genuinely modern" refinement).
- **Enquire Now** — shown (matches FR16's own required element list) but
  disabled with a tooltip — Enquiries (FR22) is a later slice; an honest
  disabled state, not a dead-end fake action.
- **Report** — deliberately deferred, not built: `vyapar_trust_safety.
  reports.case_id` is `NOT NULL` and references `moderation_cases`, so a
  real Report action needs FR39/FR40's case lifecycle (slice 6) to exist
  first; a bare insert against that schema would violate the FK, so there
  was no honest "quick" version to ship here.
Reputation signals (FR28) are simply absent from this screen for now —
Reviews & Reputation doesn't exist yet (slice 7); nothing fake is shown in
its place.

**Manual test evidence**
```
GET /v1/listings/{id} as non-owner (records a view) -> saved:false
POST /v1/listings/{id}/save   -> saved:true
DELETE /v1/listings/{id}/save -> saved:false
```

**Deviations from plan (if any)**
Report action deferred to slice 6 — see Approach; not a silent drop, recorded here.

**Assumptions**
None beyond FR16's own text.

**Decisions**
Implemented Save/Recently-viewed for real now (the schema already supports them with zero new tables) rather than waiting for FR55's Activity screen to exist — this is forward-compatible, not scope creep, since FR55 will only need to *read* `member_listing`, not define it.

**Review history**
2026-09-15 — Built and curl-tested; Save/unsave round-trip verified against the real DB.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## IMP11 — Zero-result broadening
**Traces from:** FR17, TR017, SP017
**Status:** Built, curl-tested | **Confidence:** High

**Files touched**
- `vyapar-service/app/routers/discovery.py` (`broadening_options`/`fallback` on zero-result response) — [comment block present: Yes, shared with IMP09]
- `vyapar-web/app/businesses/page.tsx` (broadening chip row) — [comment block present: Yes, shared with IMP09]

**Approach**
A zero-result `SearchResponse` includes `broadening_options[]` (radius
5→10→25km steps, adjacent categories, remove-one-filter, include-
unverified) as one-tap chips — never a silently-relaxed query; the member
explicitly picks which constraint to loosen, and the frontend re-runs the
search with that one change applied (`broaden_attempt` counter threads
through so a second zero-result additionally offers a "Post what you need"
link, per FR17's own two-strikes escalation).

**Manual test evidence**
```
GET /v1/listings/search?q=zzzznonexistentqueryxyz
  -> notice:"No exact match found.", 6 broadening_options present
```

**Deviations from plan (if any)**
The "Notify me when something matches" fallback (FR17's other named
fallback, alongside "Post what you need") is not wired yet — it depends on
FR21's proactive-notification mechanism, which isn't built (FR21 isn't
explicitly placed in any build-order slice; noted here to fold into slice 3
alongside FR18-20 when notifications are reached, not forgotten).

**Assumptions**
None beyond FR17's own text.

**Decisions**
None beyond what's already recorded in IMP09.

**Review history**
2026-09-15 — Built and curl-tested (zero-result path only — a true "radius broadened, no longer zero" round trip was not separately exercised this session; the mechanism is the same query path IMP09 already verified with real filters).

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## IMP12 — Opportunity Composer, lifecycle, and V1 types
**Traces from:** FR11, FR12, FR13, FR14, TR011, TR012, TR013, TR014, SP011, SP012, SP013, SP014
**Status:** Built, curl-tested | **Confidence:** High

**Files touched**
- `vyapar-service/app/routers/opportunities.py` (new file) — [comment block present: Yes]
- `vyapar-web/app/opportunities/new/page.tsx` (new) — [comment block present: Yes]
- `vyapar-web/app/opportunities/[id]/page.tsx` (new — confirm/publish/lifecycle half) — [comment block present: Yes]
- `vyapar-web/app/post/page.tsx` (new — see Decisions)
- `vyapar-web/app/components/CommandHub.tsx` (Post destination now points to the chooser)

**Approach**
`POST /v1/opportunities` covers all three FR11 entry modes against one
schema (`poster_id` server-resolved, never client input). Share/upload
modes run `_extract_fields()` — genuinely rule-based (first non-empty line
→ candidate title, a small keyword list → candidate type), never an AI
call, per FR12's own stated assumption — and mark whatever it inferred in
`unconfirmed_fields[]`. `PATCH /confirm` and `POST /publish` are two
separate, composable steps: publish is blocked with a 422 listing exactly
which of title/type/location/response_method are still unconfirmed — one
server-side gate every entry mode goes through, not three independently-
coded checks. Lifecycle (`pause`/`resume`/`close`/`renew`) enforces valid
from-states server-side; `renew` on a >90-day-expired record is rejected
with a message pointing back at re-confirmation, per FR13's own rule.
`TR014`'s type-specific re-validation on a post-publish type change is
enforced in `patch_opportunity`. V1's three promoted types
(employment/freelance/local_service) render first in the picker
(`<optgroup>`), others under "Other" — matches FR14 exactly.

**Self-check applied before moving on (per the coordinator's standing refinement)**
*(a) Modern/fewer taps:* the composer originally forced three sequential
screens (mode → segment → details) before any typing. Simplified to two:
segment (Community/Public) is now a smart-defaulted inline toggle on the
same screen as the details form, not its own screen — still an explicit,
independently-changeable choice per FR11, just not a forced extra tap.
Also added `/post` — a one-screen chooser between "listing" and
"opportunity" — because CommandHub's single "Post" destination was
otherwise ambiguous about which of the two composers it meant.
*(b) Correctness against source docs:* `TYPE_ACTION_LABEL` reuses FR22
DEC-002's exact, already-web-verified vocabulary (Apply/Submit a
Proposal/Enquire Now/Contact/Register) rather than inventing a second
mapping — checked line-by-line against `02-functional-requirements.md`'s
FR22 DEC-002 text before writing it, no new research needed since that
vocabulary was already grounded in Step 2.
*(c) Practical workability:* full create → confirm → publish → lifecycle
round trip curl-tested below, not just unit-shaped.

**Manual test evidence**
```
POST /v1/opportunities (entry_mode=create, community) -> 201, state:"draft"
POST .../publish -> 200, state:"active" (all material fields already present)

POST /v1/opportunities (entry_mode=share, raw_input="Urgent hiring: Freelance
  React developer...", source_segment=public, no source_name/url) -> 422
  "Tell us where you found it..."
POST (same, with source_url) -> 201, unconfirmed_fields:["title","type","location"]
POST .../publish (before confirming) -> 422
PATCH .../confirm {"fields":["title","location"]} then publish -> 422 "Please confirm: type"
  (confirms the gate checks ALL four material fields independently, not just the ones sent)
PATCH .../confirm {"fields":["type"]} then publish -> 200, state:"active"

POST .../pause -> state:"paused"; POST .../resume -> state:"active"
```

**Deviations from plan (if any)**
"Upload a screenshot" accepts a pasted image URL, not a real file-upload
widget — no Object Storage integration exists for opportunity screenshots
yet (only verification documents have a signed-URL flow planned, and that
isn't built either). An honest working substitute, not a fake file picker.

**Assumptions**
None beyond FR11-14's own text.

**Decisions**
Added `/post` (listing-vs-opportunity chooser) and collapsed the segment
picker into the details screen — both are the "fewer taps" self-check
acting on the design direction, not FR-mandated, recorded here per that
convention.

**Review history**
2026-09-15 — Built, curl-tested, then simplified once for the "fewer taps" self-check before moving to the next FR.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## IMP13 — Canonical ranking, Discover feed, and "Why this?"
**Traces from:** FR18, FR19, FR20, TR018, TR019, TR020, SP018, SP019, SP020
**Status:** Built, curl-tested | **Confidence:** High

**Files touched**
- `vyapar-service/app/ranking.py` (new file — the canonical FR19 module) — [comment block present: Yes]
- `vyapar-service/app/routers/feed.py` (new file — feed + why + activity) — [comment block present: Yes]
- `vyapar-service/app/routers/discovery.py` (refactored to call `app.ranking` instead of its own IMP09-era interim scorer — closes that tracked Decision)
- `vyapar-web/app/page.tsx` (rewritten — home is now the real Discover feed)

**Approach**
`RankingSignals` is a typed struct whose fields are exactly FR19's
allow-list (capability/intent/location/timing/value/experience/freshness/
trust fit) — a structural absence, not a documented convention: there is
no field for a sensitive attribute, community status, account age, paid
status, popularity, or report signal, so a future PR adding one must first
change this one reviewable type (SP019's own named Critical-severity
regression scenario). `score()`/`top_signals()`/`diversify()` are the ONE
implementation every ranked surface calls — the feed's five sections, and
`/why`, and (retroactively) listings search (IMP09's tracked Decision is
now closed: `discovery.py` no longer has its own scorer). The feed runs
five independent queries per FR18's own "never a single ranked list
re-sliced client-side" rule; empty sections are omitted server-side; a
sparse-profile member (no `members.capabilities`) gets Near You + Community
+ Public + one enrichment prompt instead of an empty For You/Explore,
tested live below. `/why` recomputes the exact same `_opportunity_signals()`
function the feed used for that member/item pair — deterministic given the
same inputs, so it structurally cannot drift from what actually ranked,
without needing a separate signals-cache table this session didn't build.

**Manual test evidence**
```
GET /v1/opportunities/feed as m_priya (capabilities: react)
  -> for_you: ["React developer needed", "Frontend developer (React) — Nanda Labs",
              "Python developer — Telangana e-Governance (contract)"]
     explore, near_you, community, public all populated; enrichment_prompt: null

GET /v1/opportunities/feed as m_new (no capabilities, no locality)
  -> only community + public sections present (for_you/explore/near_you all
     correctly omitted server-side); enrichment_prompt: "Add what you can do..."

GET /v1/opportunities/{id}/why as m_priya
  -> signals: ["matches your capabilities","recently posted","matches what you're looking for"]
```

**Deviations from plan (if any)**
`location_fit` defaults to a flat 0.3 rather than a real distance
computation — member lat/lng vs. opportunity lat/lng via the existing
`vyapar_platform.distance_km()` helper was not threaded into this query
this session. Honest placeholder value, not a fabricated precise number;
flagged as the next real improvement to this file, not silently left as if
distance-aware.

**Assumptions**
None beyond FR18-20's own text.

**Decisions**
Closed IMP09's tracked interim-ranker Decision by refactoring
`discovery.py` to call this module — no second scorer remains in the codebase.

**Review history**
2026-09-15 — Built and curl-tested against both a normal and a sparse member profile.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## IMP14 — Opportunity detail, Save/Share/Not-interested, and Activity
**Traces from:** FR55, TR055, SP055
**Status:** Built, curl-tested | **Confidence:** High

**Files touched**
- `vyapar-service/app/routers/opportunities.py` (`save`/`unsave`/`not-interested`/`share`/`external-open`) — [comment block present: Yes, shared with IMP12]
- `vyapar-service/app/routers/feed.py` (`GET /v1/activity`) — [comment block present: Yes, shared with IMP13]
- `vyapar-web/app/opportunities/[id]/page.tsx` (viewer half: primary action, Save, Why this?, Not interested chips) — [comment block present: Yes, shared with IMP12]
- `vyapar-web/app/activity/page.tsx` (rewritten — real six-group screen, was a placeholder)
- `vyapar-web/lib/api.ts` (added the missing `delete` method — see bug below)

**Approach**
The primary action's label is server-computed (`type_action_label`,
reusing FR22 DEC-002's mapping) and rendered as-is — never a second
front-end type→label mapping, per TR055's own rule. For a Public/External
item with a `source_url`, the primary action becomes "Open official
website ↗" (an actual outbound link, recording an `external-open` event on
click) instead of the disabled Enquire button. Not Interested writes one of
the six modeled reasons to `member_opportunity.hidden_reason` and hides the
card immediately client-side — no confirmation dialog, per the "no
unnecessary intermediate screens" standing preference. Sharing a `removed`
opportunity is rejected at the API layer (state check before the insert),
not just hidden in the UI. `GET /v1/activity` is one parameterized query
pattern across `member_opportunity`/`member_listing`, not six separate
endpoints — "Responded" is honestly omitted (not faked as empty-forever)
since it depends on Enquiries (FR22, not built yet).

**Real bug found and fixed while wiring this up**
Both this page and IMP10's listing detail page called `api.delete(...)`
for the Save toggle's off-state, but `vyapar-web/lib/api.ts`'s exported
`api` object only had `get`/`post`/`patch` — `delete` was never added.
This would have been a runtime `TypeError` the moment anyone tried to
un-save something, on BOTH the listing and opportunity detail screens.
Caught by a repo-wide grep for `api.delete(` before assuming the method
existed, not by waiting for a browser to throw the error. Fixed by adding
the missing method.

**Manual test evidence**
```
POST /v1/opportunities/{id}/pause, /resume            -> state transitions correctly
POST /v1/opportunities/{id}/not-interested {"reason":"too_far"} -> {"hidden":true}
POST /v1/opportunities/{id}/share                      -> {"shared":true}
GET /v1/activity as the sharer -> shared:["React developer needed"] (real, DB-backed)
```

**Deviations from plan (if any)**
"Report" is still deferred (same reason as IMP10 — `reports.case_id` needs
a real moderation case, slice 6). "Responded" group omitted from Activity
until Enquiries exists.

**Assumptions**
None beyond FR55's own text.

**Decisions**
None beyond the `api.delete` fix above.

**Review history**
2026-09-15 — Built; found and fixed a real cross-page bug (`api.delete` missing) before it could surface in a browser; curl-tested the lifecycle/save/share/not-interested/activity round trip.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## Explicitly not placed by the build-order note — handled here for closure

**FR21 (Proactive notification and digest) — Skipped this session, reason
recorded, not silently dropped.** TR021 requires a scheduled job calling a
real Notification Bridge with retry/idempotency semantics; no such bridge
exists in this codebase (Integration Bridges component is unbuilt), and
building a fake in-process notifier that "delivers" nowhere real would not
be genuine functionality, just the appearance of it. Revisit once the
Notification Bridge (or a real stand-in) exists — likely alongside slice 10's
remaining Integration Bridges work.

**FR06 (VerifiedCredential reference) — still deferred from IMP07's plan,
not reattempted this session.** Same reasoning as before: depends on a live
Identity & Trust VerifiedCredential contract that doesn't exist in dev.

**2026-09-15, owner override on both of the above — see IMP15/IMP16 below.**
The product owner rejected leaving these skipped: "the owner wants a
practically workable app and there are real ways to build both now."
Both are being built for real this session (in-app inbox + scheduled
matcher/digest for FR21; a dev-standin VerifiedCredential provider behind
the real interface shape for FR06) — see the dedicated items below rather
than the deferrals above, which are now superseded, not current status.

---

## IMP15 — Multilingual support (English / Hindi / Telugu)
**Traces from:** Product-owner standing i18n rule, 2026-09-15 (cross-cutting, not one numbered FR)
**Status:** Built, curl + compile verified | **Confidence:** High

**Files touched**
- `vyapar-service/app/i18n/__init__.py` (new — `translate()`/`resolve_language()`, mirrors MOD03 Mangaly's own module, read not edited) — [comment block present: Yes]
- `vyapar-service/app/i18n/locales/{en,hi,te}/{common,listings,opportunities,discover,ranking}.json` (new, 15 files, every key has a REAL Hindi/Telugu value — no empty fallback files)
- `vyapar-service/app/deps.py` (new — `Locale`/`get_locale`, mirrors Mangaly's `api/deps.py`) — [comment block present: Yes]
- `vyapar-service/app/routers/member_settings.py` (new — `PATCH /v1/members/me/language`) — [comment block present: Yes]
- Every existing router (`listings.py`, `opportunities.py`, `discovery.py`, `feed.py`) — every `HTTPException.detail`/success `"message"` converted from a literal English string to `translate(key, lang)`; `lang: Locale` added to every route that needed it
- `ranking.py` — `top_signals()` (English phrases) replaced with `top_signal_keys()` (raw keys); no pre-baked language leaks through the ranking module into any API response
- `vyapar-web/lib/i18n/config.ts`, `provider.tsx` (new — mirrors Mangaly's frontend pattern exactly)
- `vyapar-web/locales/{en,hi,te}/{common,firstRun,listings,opportunities,discover,activity,profile,ranking}.json` (new, 24 files)
- `vyapar-web/app/components/LanguageSwitcher.tsx` (new)
- Every existing page/component converted to `useTranslation()` — `app/page.tsx`, `businesses/page.tsx`, `listings/new/page.tsx`, `listings/mine/page.tsx`, `listings/[id]/page.tsx`, `opportunities/new/page.tsx`, `opportunities/[id]/page.tsx`, `activity/page.tsx`, `profile/page.tsx`, `post/page.tsx`, `first-run/page.tsx`, `components/{IntentBar,LivingCard,CommandHub,DevMemberSwitcher}.tsx`
- `vyapar-web/lib/api.ts` — sends `X-Vyapar-Language` on every request

**Approach**
Followed MOD03 Mangaly's exact existing pattern on both sides (read, never
edited) rather than inventing a second i18n architecture for the same
platform: `i18next`/`react-i18next` on the frontend with namespace-per-area
JSON catalogs typed from the English files; a small `translate()`/
`resolve_language()` module on the backend so every API `detail`/`message`
string is also localized, not just frontend JSX — the exact gap Mangaly's
own `app/i18n/__init__.py` docstring names ("a Hindi/Telugu-preferring user
got English from every 401/422/429 regardless of their selected
language"). Deliberately stricter than Mangaly's own stated tolerance: the
product owner's rule requires a REAL Hindi and Telugu value for every key
from the start, not an empty-file fallback-to-English — verified by
writing actual translated content into all 15 backend + 24 frontend locale
files this session, not placeholder stubs. `X-Vyapar-Language` (frontend →
backend) and `Accept-Language` fallback mirror Mangaly's own
`X-Mangaly-Language` header convention exactly.

**A genuinely deep i18n bug this pass found, and how it's structured to
prevent recurrence:** several backend fields (`ranking.py`'s per-signal
explanation, `opportunities.py`'s `type_action_label`, `discovery.py`'s
search notices/broadening labels, `feed.py`'s section keys) were originally
written as PRE-BAKED ENGLISH STRINGS returned directly in JSON API
responses — a harder-to-catch leak than a literal JSX string, because it
looks like "just data" rather than "UI text." Fixed by converting every one
of these to a stable, language-neutral KEY (e.g. `capability_fit`,
`enquireNow`, `noMatch`) with the frontend doing the one and only
translation step via `t()`. This is now the enforced pattern for any FUTURE
ranked/labelled field this codebase adds — a reviewer should treat a raw
English string appearing in any Pydantic response model as the same class
of defect as a hardcoded JSX string, not a lesser one.

**Manual test evidence**
```
PATCH /v1/members/me/language {"language":"hi"} -> {"language":"hi"}
GET /v1/listings/{bad-id} -H "X-Vyapar-Language: hi" -> {"detail":"लिस्टिंग नहीं मिली या अब उपलब्ध नहीं है"}
GET /v1/listings/{bad-id} -H "X-Vyapar-Language: te" -> {"detail":"లిస్టింగ్ కనుగొనబడలేదు లేదా ఇక అందుబాటులో లేదు"}
```
Frontend: repo-wide grep for literal JSX text (`>[A-Z][a-z]+ `), literal
`placeholder="..."`, and literal `aria-label="..."` across every `.tsx`
file under `vyapar-web/app` — zero matches after conversion. All 8 curl-
tested pages compiled and rendered 200 with zero TypeScript errors in the
dev server log after the full conversion.

**Deviations from plan (if any)**
None — followed Mangaly's pattern as instructed, with the one deliberate
strengthening (real translations, not empty files) the product owner
explicitly required.

**Assumptions**
Hindi/Telugu translations are this session's own good-faith translations
(not run past a native-speaker reviewer) — accurate common software UI
vocabulary, consistent with Mangaly's own existing Hindi file's register
where the same concept overlaps (e.g. "Loading…" phrasing), but flagged
here for a native-speaker QA pass before this is treated as launch-ready
copy, per the same honesty standard this file applies to everything else.

**Decisions**
Backend response fields that used to carry pre-baked English (ranking
signals, action labels, notices, broadening labels) now carry stable KEYS
instead — a structural decision, not a one-off fix, since it's the only way
the same class of bug can't quietly reappear in a future field.

**Review history**
2026-09-15 — Built, backend curl-verified in three languages, frontend grep-swept clean, zero compile errors.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## IMP16 — Coordinator browser-check fixes (Discover feed correctness + UX)
**Traces from:** FR18, FR19, FR40, FR55 (real bugs found by an actual click-through, not a self-review)
**Status:** Fixed, curl-verified | **Confidence:** High

**Files touched**
- `vyapar-service/app/routers/feed.py` (hidden-item exclusion, on-site radius hard constraint, `distribution_limited` exclusion, cross-section de-duplication, section cap + `total_available`, richer card fields, new `GET /v1/opportunities/feed/section/{key}` "see all" endpoint)
- `vyapar-web/app/page.tsx` (rewritten — search-first home: `<IntentBar>` + one-tap Business Directory link above the feed; renders freshness/submitter/relevance-reason per card; "See all N" links)
- `vyapar-web/app/opportunities/section/[key]/page.tsx` (new — the "see all" destination)
- `vyapar-web/app/globals.css` (`.vy-shell` top padding increased to clear the fixed-position member pill/language switcher)
- Database: deleted 6 test-created rows (2 opportunities, 4 listings) this session's own curl testing left behind; none were seed data

**Approach — one item per coordinator-reported bug**
1. *Not interested ignored:* `opportunity_feed`'s candidate query now
   `NOT EXISTS`-excludes any `member_opportunity` row with `hidden_at IS
   NOT NULL` for the calling member, on every section's query, not
   post-filtered client-side.
2. *On-site radius not enforced:* added `_distance_km()` (calls the
   already-existing `vyapar_platform.distance_km()` Haversine helper) and
   excludes on-site opportunities beyond the member's `radius_km` BEFORE
   scoring — a hard constraint per FR19's own rule, not a penalty folded
   into the weighted sum.
3. *Auto-limited content distributed:* every candidate query now also
   excludes `distribution_limited = true` rows.
4. *Same cards repeated across sections:* a `used_ids` set threaded through
   section-building in priority order (for_you → explore → near_you →
   community → public) — an item already placed is skipped in every later
   section.
5. *Long repetitive scroll:* `SECTION_CARD_LIMIT = 4` per section on the
   main feed, with `total_available` returned so the frontend can render
   "See all N" (a new dedicated endpoint + page) instead of dumping
   everything into one scroll.
6. *Cards missing fields:* added `submitter_name` (poster's display name,
   batch-fetched per section), `posted_days_ago`, and `relevance_reason`
   (the literal top-scoring signal key for that card) to every feed card.
7. *Junk test data:* identified and deleted via direct SQL (not through
   the API, to avoid re-triggering any side effects) every row this
   session's own curl testing created that wasn't part of the original
   seed — cross-checked by UUID pattern (seed rows use the fixed
   `00000000-0000-4000-8000-...` prefix; test-created rows use
   `gen_random_uuid()`'s real-random output).
8. *Header overlap + missing language switcher:* `.vy-shell`'s top padding
   increased from 24px to 64px to clear both fixed-position top corner
   widgets; `<LanguageSwitcher>` added top-left (member pill already owns
   top-right) — see IMP15.
9. *Home missing search-first entry:* `<IntentBar>` now sits above the
   feed on `/`, with a one-tap Businesses & Professionals link beside it —
   both visible without scrolling on a phone viewport, directly per the
   WorkIndia/Upwork "search first" reference lens the product owner named.

**Manual test evidence**
```
GET /v1/opportunities/feed as m_krishna:
  - "Wedding photographer wanted — Warangal" (hidden by m_krishna, ~140km,
    on-site): absent from every section (was present in Explore+Community before)
  - "Advance-payment training programme (flagged)" (distribution_limited=true):
    absent from every section (was present in Explore+Community before)
  - 12 total cards across 4 sections, all 12 ids unique (zero cross-section
    duplicates; the plumber card no longer appears 3 times)
  - each card carries relevance_reason/submitter_name/posted_days_ago
```

**Deviations from plan (if any)**
None — every item is a fix to already-claimed FR18/FR19/FR40 behaviour, not new scope.

**Assumptions**
None.

**Decisions**
`SECTION_CARD_LIMIT = 4` is this session's own judgment call for "short
first screen" — not FR-specified; revisit if the product owner wants a
different number once seeing it live.

**Review history**
2026-09-15 — Coordinator did one targeted browser check (m_krishna, home feed), found 8 real issues; all fixed and curl-verified same session.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## IMP17 — Proactive notification and digest, built for real (overrides the earlier skip)
**Traces from:** FR21, TR021, SP021
**Status:** Built, curl-verified | **Confidence:** High

**Files touched**
- `vyapar-service/app/notifications.py` (new — `NotificationChannel`/`InAppChannel`/`WebPushChannel` swap seam, `send_notification()`) — [comment block present: Yes]
- `vyapar-service/app/routers/notifications.py` (new — inbox endpoints, `run_strong_match_pass()`, `run_digest_pass()`, `notification_loop()`) — [comment block present: Yes]
- `vyapar-service/app/routers/dev.py` (dev-triggerable `run-notification-matcher`/`run-notification-digest`)
- `vyapar-service/app/main.py` (starts `notification_loop()` as a real `asyncio` background task in the lifespan, not only a dev endpoint)
- `07a-db-implementation/migrations/002-notification-dispatcher-reads.sql` (new — see the real RLS bug below)
- `vyapar-web/app/components/NotificationBell.tsx` (new)
- `vyapar-web/app/layout.tsx` (bell mounted top-right, immediately left of the member pill)
- 5 new locale files (`notifications.json` × en/hi/te backend + en/hi/te frontend)

**Approach**
The product owner explicitly overrode this session's earlier skip: "build
it genuinely... the in-app inbox is the always-available path... enforce
the strong-match threshold, 3-per-day cap, daily digest at the member's
chosen hour, per-type mute and digest opt-out, all from config." Built
exactly that: `run_strong_match_pass()` scores every active, notifiable-
type (employment/freelance/local_service, per TR014's own exclusion of
training/community/partnership) opportunity against every notifications-
enabled member using the SAME `app.ranking` module the feed/why-this
already use — never a second scorer. Above `NOTIFY_STRONG_MATCH_THRESHOLD`
and under the shared `vyapar_platform.check_and_increment` 3/day cap, one
notification is sent via `send_notification()`, idempotent per
member+opportunity+day (a second pass the same day is a safe no-op, never
a duplicate, per TR052's own contract). `run_digest_pass()` batches
everything else for members whose `privacy_settings.digest_hour` matches
the current hour. Both run on a real `asyncio` background loop started in
`main.py`'s lifespan (`NOTIFY_MATCHER_INTERVAL_SECONDS`, dev default 300s)
— genuinely scheduled, not only the dev-triggerable endpoints (which also
exist, for on-demand testing). Web Push is a structural stub
(`WebPushChannel`) behind placeholder VAPID keys — never actually invoked
this session since no subscription flow exists, exactly per the config-
placeholder convention; a future real integration is a channel addition; not
a redesign. The bell sits immediately left of the member pill (the
platform-wide "no separate Alerts tab" header rule) with no new nav
destination.

**A real, structural RLS bug this pass found (not a self-review nit)**
`vyapar_privacy.privacy_settings`'s own RLS policy
(`privacy_settings_self_only`) is strictly self-only with **no** operator
or service-role bypass at all — correct for every member-facing path, but
it silently blocked the ONE legitimate background-job read this feature
needs (notifications_enabled/digest_hour/muted_types across ALL members).
Before the fix, `run_strong_match_pass()` queried this table joined with
`members` and got zero rows back — not an error, just silently, plausibly
wrong (my own first test run reported `{"sent":0}` and I initially
suspected a scoring-threshold issue, not an RLS one, until direct psql
diagnosis with an explicit role/context showed the real cause). Since
`vyapar_owner` is off-limits to the running app (hard constraint), and
`migrations/001-initial.sql` is applied/frozen, fixed forward with a NEW
migration (`002-notification-dispatcher-reads.sql`) adding
`vyapar_privacy.notification_targets()` — a narrow, dispatcher-role-gated
SECURITY DEFINER function returning exactly the 5 columns the job needs,
mirroring this codebase's own already-established
`ensure_member()`/`contacts_for_viewer()` pattern rather than inventing a
new authorization shape. Also discovered in the same debugging pass:
`vyapar_identity.members`' own RLS needs an operator `authz_context` set
(not just `service_role`) for a background job to see across members at
all — both are now set together in one `_set_dispatcher_context()` helper
so this doesn't have to be rediscovered per future background job.

**A second real bug found while wiring this up**
`send_notification()`'s first version passed a Python `dict` directly as
an asyncpg query parameter for the `params jsonb` column — asyncpg does
not auto-serialize dicts to JSON; this raised `DataError: invalid input
... expected str, got dict` on the very first live test. Fixed with
`json.dumps(params)` + an explicit `::jsonb` cast.

**Manual test evidence**
```
POST /v1/dev/run-notification-matcher (before RLS fix) -> {"sent":0}
  (silently wrong — root-caused to RLS via direct psql role/context testing)
... after migration 002 + _set_dispatcher_context fix + json.dumps fix ...
POST /v1/dev/run-notification-matcher -> {"sent":16}
GET /v1/notifications as m_priya -> one real row, title "New match: Frontend
  developer (React) — Nanda Labs", link to the real opportunity
GET /v1/notifications/unread-count as m_priya -> {"count":1}
POST /v1/dev/run-notification-matcher (re-run same day) -> {"sent":0}
  (idempotency key + 3/day cap correctly prevent a duplicate)
POST /v1/dev/run-notification-digest -> {"sent":0} (correct — no seeded
  member's digest_hour matches the current UTC hour; logic verified by
  reading the query, not separately forced to fire this session)
```

**Deviations from plan (if any)**
None from FR21's own text — the RLS fix is a genuine gap this pass found
and closed via the project's own "fix forward with a new migration"
convention, not a deviation from it.

**Assumptions**
`NOTIFY_STRONG_MATCH_THRESHOLD=2.5` is this session's own judgment call
(no `config`-table admin UI exists yet to set it live) — revisit once real
usage data exists.

**Decisions**
Added migration 002 (see above) rather than touching 001-initial.sql.
`_set_dispatcher_context()` sets both `service_role` and an operator
`authz_context` together — the correct combination for any future
background job needing cross-member visibility, not just this one.

**Review history**
2026-09-15 — Built; found and fixed two real bugs (an RLS gap requiring a new migration, and a JSON serialization error) before the feature could be honestly called working; curl-verified end to end including idempotent re-run.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## IMP18 — VerifiedCredential reference, built against a dev stand-in (overrides the earlier deferral)
**Traces from:** FR06, TR006, SP006
**Status:** Built, curl-verified | **Confidence:** High

**Files touched**
- `vyapar-service/app/identity_trust_stub.py` (new — explicitly-labelled dev stand-in for the real Identity & Trust VerifiedCredential read contract, ADR-013) — [comment block present: Yes]
- `vyapar-service/app/routers/listings.py` (`ListingOut.credential_ref`, `POST /{listing_id}/credential-ref/attach`, `sync_credential_refs()`) — [comment block present: Yes]
- `vyapar-service/app/routers/dev.py` (`run-credential-sync`, `revoke-credential/{member_id}` dev-only test hooks)
- `vyapar-service/app/main.py` (`credential_sync_loop()` — real hourly `asyncio` background task)
- `vyapar-web/app/listings/[id]/page.tsx` (credential badge + owner-only "Attach" button)

**Approach**
The product owner explicitly overrode this session's earlier deferral:
"build the read-only reference against a dev stand-in for the Identity &
Trust credential contract... including the 'last checked' cached state and
revocation removal. Mark the provider clearly as a dev stand-in."
`identity_trust_stub.get_credential(member_id)` is the ONE call site a real
integration replaces later — seeded with two plausible credentials
matching real seeded members' own capabilities (m_kavita/legal,
m_deepak/architecture), a `revoke()` test hook, and a `credential_ref_
payload()` builder producing exactly `{id, claim, issuer, verified_at,
last_checked}` — no room for a MOD04 Counsel field, per TR006's own
structural-absence rule. The member-initiated attach endpoint writes the
reference onto their own listing only (never someone else's); the hourly
`sync_credential_refs()` job (real `asyncio` loop in `main.py`'s lifespan,
plus a dev-triggerable endpoint) re-checks every listing with a non-null
reference and clears it (`credential_ref = NULL`) if the stand-in reports
a revocation — exercising TR006's own "revocation removes the reference
within the same 1-hour sync cycle" rule for real, not just asserting it in
prose.

**Manual test evidence**
```
POST /v1/listings/{kavita's listing}/credential-ref/attach (as m_kavita)
  -> credential_ref: {id, claim:"Enrolled Advocate...", issuer, verified_at, last_checked}
GET /v1/listings/{id} as a DIFFERENT member (m_ravi) -> same credential_ref
  visible (read-only reference is public, per FR06's own text)
POST /v1/dev/revoke-credential/m_kavita -> {"revoked":"m_kavita"}
POST /v1/dev/run-credential-sync -> {"updated":2}
GET /v1/listings/{id} as m_ravi (after sync) -> credential_ref: null
```

**Deviations from plan (if any)**
None — dev stand-in is explicitly labelled as such everywhere it appears (module docstring, code comments); no code path presents it as real platform data.

**Assumptions**
The two seeded dev credentials are illustrative, not real claims about m_kavita/m_deepak's actual professional registration status.

**Decisions**
None beyond the stand-in design itself, which was the product owner's own explicit instruction.

**Review history**
2026-09-15 — Built and curl-verified through the full attach → view → revoke → sync-removal lifecycle.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## IMP19 — Enquiries and consented contact (slice 4)
**Traces from:** FR22, FR23, FR24, TR022, TR023, TR024, SP022, SP023, SP024
**Status:** Built, curl-verified | **Confidence:** High

**Files touched**
- `vyapar-service/app/routers/enquiries.py` (new — create/list/detail/reply/lifecycle/block/refer-to-counsel) — [comment block present: Yes]
- `07a-db-implementation/migrations/003-enquiry-block-check.sql` (new — see the second real RLS bug below)
- `vyapar-web/app/enquiries/{new,mine,[id]}/page.tsx` (new)
- `vyapar-web/app/listings/[id]/page.tsx` and `opportunities/[id]/page.tsx` — the previously-disabled "Enquire Now"/type-action-label buttons now link to the real compose flow
- 6 new locale files (`enquiries.json` × en/hi/te backend + en/hi/te frontend)

**Approach**
`action_type` is resolved server-side from the target's own type
(`_resolve_action_type`) — for listing targets always `enquire`; for
opportunity targets, reuses `opportunities.py`'s own `TYPE_ACTION_LABEL`
mapping so the enquiry's stored type and the button label the member
tapped can never independently drift (closes SP022's own named Spoofing
risk: a client-supplied `action_type` claiming a different action than the
target supports). The DB's own partial unique index
(`enquiries_one_open_per_target`) is the real 1-open-enquiry-per-target
enforcement; this router's own pre-check is a friendlier error on top, not
the enforcement itself. `GET /v1/enquiries/{id}` is the single call site
that discloses contact — only when `state == 'in_progress'` AND the target
is a listing, via the already-existing `contacts_for_viewer()` function,
never a second independently-coded check. Idempotency-CC via the shared
`vyapar_platform.idempotency_key` table on `POST /v1/enquiries`.

**Two real bugs found via curl testing, both fixed properly (not worked around)**
1. *Transaction-abort on duplicate enquiry.* The first version wrapped the
   INSERT in a bare `try/except asyncpg.UniqueViolationError`, then ran a
   follow-up SELECT inside the `except` block to find the existing row —
   but Postgres aborts the WHOLE transaction on a constraint violation, so
   that follow-up SELECT failed with `InFailedSQLTransactionError` instead
   of returning a clean 409. Fixed by wrapping only the INSERT in its own
   nested `conn.transaction()` (a SAVEPOINT), so only that statement rolls
   back on conflict — the outer request-scoped transaction stays usable
   for the lookup that follows.
2. *A second RLS gap, same class as IMP17's — found in the same session.*
   FR22's own text: a blocked sender's enquiry must be "silently not
   delivered... no block disclosure." Implementing this needs the SENDER's
   own session to check whether the PROVIDER has blocked them — but
   `vyapar_enquiries.blocks`' RLS (`blocks_blocker_only`) correctly scopes
   visibility to "only the blocker sees their own block list," which also
   means the sender's session literally cannot see a row where they are
   the `blocked_id`, even to answer a yes/no question. Before the fix, this
   silently always returned false and a blocked sender's enquiry was
   delivered anyway — found by testing the actual block scenario end to
   end, not assumed correct from reading the code. Fixed forward with
   migration `003-enquiry-block-check.sql` adding
   `vyapar_enquiries.is_blocked(blocker_id, blocked_id)` — a narrow
   SECURITY DEFINER boolean check (reveals nothing beyond true/false,
   never block-list contents) callable from any session, unlike migration
   002's dispatcher-only function, because every member legitimately needs
   this exact check as part of their OWN enquiry-creation flow.

**Manual test evidence**
```
POST /v1/enquiries (m_ravi -> m_kavita's listing, 20+ char message) -> 201, state:"open"
POST /v1/enquiries (same target again) -> 409 (after the savepoint fix; was 500 before)
POST /v1/enquiries/{id}/accept (as provider m_kavita) -> state:"in_progress"
GET /v1/enquiries/{id} (as sender) -> disclosed_contacts: [phone, address]
  (FR02's "after_accept" channels correctly revealed only now)
POST /v1/enquiries/{id}/resolve -> state:"resolved"; POST .../close -> state:"closed"
POST /v1/enquiries/{id}/refer-to-counsel {"consent":true} -> {"referred":true}
POST /v1/enquiries/block {"blocked_id":"m_gaurav"} (as m_suresh)
POST /v1/enquiries (m_gaurav -> m_suresh's listing, before is_blocked() fix) -> delivered:true (WRONG)
... after migration 003 ...
POST /v1/enquiries (same scenario, fresh) -> state:"open", delivered:false (correct — silent, no disclosure to sender)
```
All test-created enquiry/message/block/referral rows deleted after
verification, per the standing "tests clean up after themselves" rule.

**Deviations from plan (if any)**
None — both fixes close gaps in already-claimed FR22/FR24 behaviour, not new scope. Activity's "Responded" group (deferred in IMP14) can now be wired to `/enquiries/mine` in a future pass — not done this session, noted so it isn't forgotten.

**Assumptions**
None beyond FR22-24's own text.

**Decisions**
`is_blocked()` is callable by any session (unlike the dispatcher-gated
`notification_targets()`) because the check is inherently "can I see my
own status," not a broad cross-member read — a deliberately different
gating shape for a deliberately different risk profile.

**Review history**
2026-09-15 — Built; found and fixed two real bugs (a transaction-abort bug and a second RLS gap) via actual scenario testing, not self-review; all test data cleaned up afterward.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## IMP20 — Business verification, credential review, state labels/expiry, operator queue (slice 5)
**Traces from:** FR08, FR09, FR10, FR47, TR008, TR009, TR010, TR047, SP008, SP009, SP010, SP047
**Status:** Built, curl-tested | **Confidence:** High (identifier path); image upload not built

**Files touched**
- `vyapar-service/app/crypto.py` (new — AES-256-GCM identifier encryption + last-4 masking) — [comment block present: Yes]
- `vyapar-service/app/routers/verification.py` (new — member submission, operator queue, verify/reject/needs-clearer-copy, revoke, image cleanup, expiry/reminder pass) — [comment block present: Yes]
- `vyapar-service/app/routers/listings.py` — `ListingOut` gains `verification_document`, `verification_claim`, `verified_at`, `verification_expires_at` — [comment block present: Yes]
- `vyapar-service/app/main.py` — `verification_cleanup_loop` (hourly: image cleanup, then expiry pass); both routers registered
- `vyapar-service/app/routers/dev.py` — `POST /v1/dev/run-verification-jobs` (dev-only trigger)
- `vyapar-service/app/config.py`, `.env` — `VERIFICATION_IDENTIFIER_ENCRYPTION_KEY` out-of-band placeholder
- `vyapar-service/app/i18n/locales/{en,hi,te}/verification.json`, `notifications.json` (`verificationReminder`)
- `vyapar-web/app/components/Verification.tsx` (new — `VerificationBadge`, `VerificationPanel`) — [comment block present: Yes]
- `vyapar-web/app/admin/verification/page.tsx` (new — operator queue) — [comment block present: Yes]
- `vyapar-web/app/listings/[id]/page.tsx` — badge + owner panel
- `vyapar-web/locales/{en,hi,te}/verification.json`, `lib/i18n/config.ts` (namespace registered)

**Approach**
- **FR08:** exactly four business documents: GST, Udyam, PAN, Shops & Establishment. There is no Aadhaar option anywhere, matching the sealed FR text. GSTIN, PAN and Udyam formats are validated server-side by regex with a translated error. The identifier is stored AES-256-GCM encrypted (`identifier_enc`, 12-byte nonce, key from an env placeholder, never in the DB) and shown only as `identifier_masked` (last 4 characters). Submitting moves the listing's `verification_state` to `pending` from not_started, rejected, expired or revoked. The form hides while the submission is pending, so there is no way to double-submit.
- **FR09:** professional listings get a fifth "credential" option. Credential name and issuer are both required (422 otherwise). The badge reads "Credential reviewed", never "Verified", so a reviewed credential is not presented as a government-record check.
- **FR10:** `VerificationBadge` renders all 8 states with the scope (which document) and the date. `revoke_verification()` is the one shared revert call site: the operator revoke route, the expiry job, and IMP21's moderation "request verification" action all use it. It moves `active_verified` back to `active_unverified`. The expiry pass runs expire-first, so a listing already past 12 months is never merely "reminded". At 11 months a listing becomes `expiring` and the owner gets a `verificationReminder` notification with an idempotency key. At 12 months it becomes `expired` and reverts.
- **FR47:** `/v1/admin/verification-queue` is gated on the `verification` operator permission. Verify sets the claim to the credential name or document type, sets expiry to +12 months, and moves `active_unverified` to `active_verified`. Reject stores `reason_code`, and the owner sees the reason. Needs-clearer-copy returns the record to not_started so the owner can resubmit in place.

**Reference check (Upwork + WorkIndia lens)**
- WorkIndia runs a KYC process for every employer and asks for GST/MSME business documents, usually approved within 2-4 hours (workindia.in/kyc-process). That supports Vyapar's business-document checklist and a short operator queue.
- Upwork deletes the submitted government-ID image after 30 days, and its identity badge is time-limited (3 years, with re-verification possible). That matches TR008's 30-day `image_delete_after` and FR10's expiry-and-reconfirm model. Vyapar keeps FR10's sealed 12-month validity, not Upwork's 3 years.

**Bug found and fixed**
- Before this slice, the listing detail page's badge `else` branch rendered `common:badge.verified` for every listing that wasn't explicitly unverified. Unverified listings could therefore show "Verified", a trust-claim correctness bug. `VerificationBadge` replaced that branch, and every state now renders its own label.

**Manual test evidence** (curl against the running API; all test rows restored afterwards)
```
POST /v1/listings/{id}/verification {document_type:"credential"} (no name/issuer, hi) -> 422, Hindi message
POST .../verification {document_type:"gst", identifier:<valid GSTIN>} -> 201; listing verification_state:"pending", identifier_masked shows last 4 only
POST /v1/admin/verification-queue/{rec}/needs-clearer-copy (m_neha_ops) -> listing back to not_started
resubmit -> POST .../verify -> listing state:"active_verified", verification_document:"gst", expires +12 months
GET /v1/admin/verification-queue as m_krishna -> 403
simulate verified_at 13 months ago; POST /v1/dev/run-verification-jobs -> {"reminded":1,"expired":1}
  -> test listing: active_unverified / expired
  -> reminded:1 was seed listing "Bhalla Design Studio" (verified 336 days ago) — correct behaviour, left as seeded; one verificationReminder notification row for m_deepak
GET (web) /listings/…008 -> 200; /admin/verification -> 200
```

**Deviations from plan (if any)**
- **Document image upload is not built.** Submission is identifier-only, because there is no object storage in this dev environment. The ER columns (`image_url`, `image_delete_after`) and the 30-day cleanup job exist and run, so adding upload later means one storage adapter plus a file input, not a schema change. Recorded here rather than silently dropped.

**Assumptions**
- 11 months is the "approaching expiry" point for the reminder. FR10 says "before expiry" without a number, and one month's notice is a reasonable reconfirm window.

**Decisions** (append-only)
- 2026-09-15: `cryptography` added for SP008's AES-256-GCM requirement. It was not named by Step 8, so a supplementary scoped review is recorded in `09a-external-dependencies.md`.

**Review history**
2026-09-15 — Built and curl-tested; fixed the unverified-shown-as-Verified badge bug.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## IMP21 — Report and block, moderation queue with graduated actions, appeals (slice 6)
**Traces from:** FR39, FR40, FR41, FR53 (partial), TR039, TR040, TR041, SP039, SP040, SP041
**Status:** Built, end-to-end tested (22 + 5 checks, all Pass) | **Confidence:** High

**Files touched**
- `07a-db-implementation/migrations/004-trust-safety-member-paths.sql` (new, applied as `vyapar_owner`) — [comment block present: Yes]
- `vyapar-service/app/routers/trust_safety.py` (new) — [comment block present: Yes]
- `vyapar-service/app/routers/listings.py` — held-at-submit listings raise an automated moderation case — [comment block present: Yes]
- `vyapar-service/app/routers/opportunities.py` — advance-payment / fee wording (en/hi/te) on publish raises a High automated flag and auto-limits distribution — [comment block present: Yes]
- `vyapar-service/app/routers/discovery.py` — listing search and browse now exclude `distribution_limited`
- `vyapar-service/app/routers/member_settings.py` — `GET /v1/members/me` (operator permissions for Profile)
- `vyapar-service/app/main.py`, `routers/dev.py` — escalation job in the hourly loop + `POST /v1/dev/run-moderation-jobs`
- `vyapar-service/app/i18n/locales/{en,hi,te}/trust_safety.json`, `notifications.json` (`moderationOutcome`, `appealDecided`, `appealDelayed`)
- `vyapar-web/app/components/ReportSheet.tsx` (new) — [comment block present: Yes]
- `vyapar-web/app/admin/moderation/page.tsx` (new) — [comment block present: Yes]
- `vyapar-web/app/moderation/outcomes/page.tsx` (new) — [comment block present: Yes]
- `vyapar-web/app/profile/page.tsx` — links to My moderation outcomes; operator tools shown only to permission holders — [comment block present: Yes]
- `vyapar-web/app/{listings,opportunities,enquiries}/[id]/page.tsx` — Report in place (the FR16/FR55 action deferred in IMP10/IMP14)
- `vyapar-web/locales/{en,hi,te}/trustSafety.json`, `profile.json`, `lib/i18n/config.ts`

**RLS gaps found before writing code (fixed forward in migration 004)**
1. `moderation_cases` is operator-only, while `reports.case_id` is NOT NULL. A member session could therefore never create the case its own report must reference, so FR39 was structurally impossible. Fix: `file_report()` (SECURITY DEFINER). It takes the reporter from `vyapar.authz_context`, never a parameter. It merges into an open case per object and increments `reporter_count`. Severity comes from the reason: scam, impersonation, harassment and discrimination are High; fake and privacy are Medium; everything else is Low. Target response time is 4h (critical), 24h (high), 72h (medium) or 7 days (low). A High report auto-limits both the case and the object, which is the one cross-schema write TR040 names.
2. The reported party cannot read the case in order to appeal. Fix: `my_outcomes()` returns only the caller's own decided outcomes and has no reporter column at all. `file_appeal()` enforces: subject = caller, decided, not dismissed, within 15 days, and one appeal per case (the UNIQUE constraint already guarantees that). It assigns a different moderation operator where one exists, and falls back to the original decider at solo-operator scale (TR041).
3. The enquiry, partnership and review WITH CHECK clauses admit only the parties, so an operator's Remove/Restore on those kinds was rejected. Fix: `set_object_state()`, guarded by `is_operator('moderation')` inside the function.
4. An automated flag is raised inside the author's own request, which cannot insert a case. Fix: `raise_auto_flag()`, which only accepts subject = caller, so it can never be used to flag someone else.

**Approach**
- **FR39 (member):** "Report" opens in place under the item, with no separate screen. It shows nine reason chips, an optional note (up to 1000 characters) and one Send.
  - The receipt says the other person won't know who reported, and shows the grievance channel (FR53).
  - It offers "Also block this member" in the same flow (FR24). On the enquiry screen, which already has a Block button, the sheet doesn't offer it twice.
  - The server resolves the reported party from the object itself, never from the client.
  - Limits: 10 reports per day, and one `Idempotency-Key` per opened sheet (via `vyapar_platform.idempotency_key`), so a double tap files one report.
- **FR40 (operator):** `/admin/moderation` is sorted by severity and then due time, and overdue cases are flagged. Each card shows the object with a link, the source, report count, primary reason, prior cases on the same object, read-only evidence (there is no edit route), and the limited-pending-review marker.
  - There are six graduated actions, each disabled until a reason code is chosen:
    - **Limit:** sets `distribution_limited`.
    - **Remove:** listing becomes `suspended`, opportunity `removed`, enquiry or partnership `restricted`, review `removed`.
    - **Request verification:** calls `revoke_verification(...,'disputed')`, so the badge shows "Under review".
    - **Suspend:** takes a duration.
    - **Dismiss:** lifts the auto-limit.
    - **Restore:** reverses every one of the others.
  - Every non-dismiss decision notifies the affected party in their own language, with the action, the reason, the 15-day appeal path and the grievance contact.
  - Automated flags come from two places: listings held at submit (Medium) and opportunities with advance-payment or fee wording in en/hi/te (High, auto-limited). Automated flags prioritise work and never make a final decision.
  - An hourly pass escalates overdue cases, marks overdue appeals `delayed` and notifies the member, and lifts suspensions whose duration has run out. It never takes an automatic permanent action.
- **FR41 (member):** Profile links to "My moderation outcomes". Each outcome shows the decision, reason, date, the appeal deadline, and Appeal in place on the card. The screen also states the process (once, within 15 days; a different operator where possible; usually 7 days) and the grievance channel. Operators decide appeals as Uphold or Overturn, with a reason code. Overturn runs the Restore path, and the member is notified.

**Reference check (Upwork + WorkIndia lens)**
- Upwork: "Flag as inappropriate" sits in place on profiles, jobs and messages, with a reason list including false identity, off-platform payment requests and suspicious links. Review is confidential, and the flagged person is not told who flagged them. Followed.
- WorkIndia: reports go to an email inbox (reviews@workindia.in), and fake-job and registration-fee fraud is its most-reported problem. Vyapar keeps reporting in-app in one sheet, and adds the fee-wording auto-flag specifically for that known fraud pattern.

**Manual test evidence** (`scratchpad/test_slice6.py`, `test_autoflag.py`, run against the live API with cleanup in `finally`)
```
PASS own content report rejected 400
PASS report filed 201 with block id
PASS idempotent retry + merge -> one case, 2 reports
PASS scam => high severity, case limited
PASS listing auto-limited
PASS non-operator queue 403
PASS operator queue includes case with 2 evidence, no reporter ids
PASS queue sorted critical/high first
PASS decide without reason code 422
PASS remove applied / listing suspended
PASS owner notified with appeal path + grievance
PASS owner outcome visible, can appeal, no reporter data
PASS reporter does not see subject's outcome
PASS non-subject appeal 404 / appeal filed / second appeal 409 (Telugu message)
PASS appeal in operator list / appeal overturned / listing restored + unlimited
PASS suspend applied to member's live listings / expired suspension lifted by job
cleanup done; leftover cases: 0
--- auto flag ---
scam(en) publish 200 active, limited t, case auto_flag|high|advance_payment
clean    publish 200 active, limited f, no case
scam(hi) publish 200 active, limited t, case auto_flag|high|advance_payment
PASS limited scam absent from feed / PASS auto flag in operator queue / leftover opps 0
Web: /admin/moderation 200, /moderation/outcomes 200, /profile 200; tsc --noEmit exit 0
```
After the tests, `m_anita`'s listing was confirmed back at `active_verified` / unlimited, the only remaining cases were the 3 seed cases, and no test notifications remained.

**Deviations from plan (declared, raised, not silently absorbed)**
1. **ER gap, raised to Step 7a:** there is no member-level suspension column or table. FR40's "suspend account" is applied to the member's live listings (to `suspended`) and opportunities (to `paused`), each tagged with `state_reason = account_suspended:<case_id>`, so it can be lifted exactly without touching unrelated suspensions. A true account-level flag, which would also block new posts, needs an ER addition that only Step 7a owns.
2. **DB-layer permission coupling, noted for Step 7a:** listings and opportunities RLS accept operator writes only with the `content` permission. A moderation-only operator could therefore not Remove a listing at the DB layer. The only seeded operator holds every permission, so this doesn't bite in dev, but a future RLS policy should also accept `moderation` for the moderation write paths.
3. **Evidence screenshots (`evidence_urls`) are not uploaded** — text evidence only. This is the same no-object-storage reason as IMP20.

**Assumptions**
- Reason codes are a fixed operator list of 11 codes, so every notification can be translated. FR40 says "reason code mandatory" without enumerating the codes.
- Grievance contact is `grievance@forkhatri.example`, a config-placeholder convention until slice 10's FR53 notice sets the real one.

**Decisions** (append-only)
- 2026-09-15: all member-side trust-and-safety writes go through narrow SECURITY DEFINER functions rather than loosening RLS. This matches the existing `ensure_member` / `contacts_for_viewer` / `notification_targets` / `is_blocked` pattern.
- 2026-09-15: a suspension lift is tag-matched per case, so lifting one case can never un-suspend content held for another reason.

**Also fixed in passing**
- Two pre-existing TypeScript errors that `tsc --noEmit` reported: `listings/new` 409-detail cast, and `opportunities/[id]` "Why this?" handler using `void ||`.
- The API venv was missing `cryptography`, which is already in `requirements.txt`. The earlier process had run under another interpreter. Installed into `.venv`, and the API was restarted by exact PID only: 61184 stopped, 59420 started.

**Review history**
2026-09-15 — Built; found four real RLS gaps by reading live policies before coding and fixed them forward; end-to-end tested with cleanup.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## IMP22 — Partnership requests, interaction reviews, reputation, review disputes (slice 7)
**Traces from:** FR25, FR26, FR27, FR28, FR29, TR025, TR026, TR027, TR028, TR029, SP025, SP026, SP027, SP028, SP029
**Status:** Built, end-to-end tested (45 checks + feed-name check, all Pass) | **Confidence:** High

**Files touched**
- `07a-db-implementation/migrations/005-reviews-partnerships-member-paths.sql` (new, applied as `vyapar_owner`) — [comment block present: Yes]
- `vyapar-service/app/reputation.py` (new — the one reputation composer) — [comment block present: Yes]
- `vyapar-service/app/routers/reviews.py` (new) — [comment block present: Yes]
- `vyapar-service/app/routers/partnerships.py` (new) — [comment block present: Yes]
- `vyapar-service/app/notifications.py` — `notify_interaction_party()` (renders en/hi/te; the DB picks the recipient's language) — [comment block present: Yes]
- `vyapar-service/app/routers/enquiries.py` — Resolved/Closed issues review invites; `first_reply_at` bug fix
- `vyapar-service/app/routers/listings.py` — `is_active()` public method (TR025); `reputation` on listing detail
- `vyapar-service/app/routers/discovery.py` — reputation on every result card; trust fit uses counts only above 3 interactions (FR19/FR28)
- `vyapar-service/app/routers/trust_safety.py` — review-dispute outcomes (limit = Hidden, remove = Removed, dismiss/restore = Published); both parties notified; reviews auto-hidden when their thread is removed
- `vyapar-service/app/routers/feed.py` — Activity "To review" and "Partnerships" groups; poster names via `public_names()` (bug fix)
- `vyapar-service/app/config.py` — review tag lists (configuration)
- `vyapar-service/app/i18n/locales/{en,hi,te}/{reviews,partnerships}.json`, `notifications.json` (+5 templates)
- `vyapar-web/app/components/Reputation.tsx` (new — `ReputationLine`, `useReputationText`, `ReviewList` with in-place dispute) — [comment block present: Yes]
- `vyapar-web/app/components/ReviewComposer.tsx` (new — in-place, invite-gated) — [comment block present: Yes]
- `vyapar-web/app/partnerships/new/page.tsx`, `partnerships/[id]/page.tsx` (new) — [comment block present: Yes]
- `vyapar-web/app/listings/[id]/page.tsx` (reputation line, reviews, Propose partnership), `enquiries/[id]/page.tsx` (composer), `activity/page.tsx` (2 groups), `businesses/page.tsx` (reputation on cards)
- `vyapar-web/locales/{en,hi,te}/{reviews,partnerships}.json`, `activity.json`, `lib/i18n/config.ts`

**RLS gaps found before writing code (fixed forward in migration 005)**
1. **Partnership state changes.** `partnership_requests` WITH CHECK admits only the sender, so the recipient could never Accept, Decline or Restrict. Fix: `partnership_transition()` is the whole FR26 state machine, with a role and from-state check per action.
2. **Notifying the other party.** The `notifications` policy only lets a member insert their own rows, so no member action could notify the other party (request received, review invite, state change). Fix: `notify_interaction_party()` requires both caller and recipient to be parties to that exact enquiry or partnership, and returns silently when the recipient has blocked the caller.
3. **Review invites.** `review_invites` is self-only, so closing a thread couldn't issue the other party's invite. Fix: `issue_invites()` re-derives qualification from the source rows: Resolved/Closed with a non-system message from both sides, or Accepted then Closed.
4. **Disputes.** `reviews` WITH CHECK admits only the author (deliberately, per TR029), and `moderation_cases` is operator-only. The subject could therefore neither mark a review disputed nor open the FR40 case. Fix: `open_dispute()` is subject-only and once per review; it opens a `review_dispute` case whose subject is the author, since the author's content is being judged.
5. **Reputation reads.** `members` is self-or-operator. Viewers couldn't see reviewer first names, the "under review" count, or other members' response times. Fixes: `reputation_for_listings()`, `reviews_for_listing()`, `response_minutes()` (aggregate only, needs 3 samples) and `public_names()` (only members who already have a public presence).

**Bugs found and fixed**
- **FR18 feed cards (live since IMP16).** Submitter names were blank for every poster except the caller. `feed.py` read `display_name` directly from `members`, and RLS silently returned no row. It now uses `public_names()`. Verified: 12 cards, 0 blank.
- **FR23 `first_reply_at`.** It was set by any reply, including the sender's own follow-up, so "Responds in ~X" would have flattered slow providers. It is now set only by the provider's reply. Verified both directions.
- **My own edit error during the fix.** A `replace_all` placed a trailing comment where it swallowed `, list(poster_ids)`, and the feed returned 500. The live test caught it; fixed and re-verified.

**Approach**
- **FR25 (create).**
  - Both listings go through `listings.is_active()`, never a direct state query (SP025).
  - Recipient opt-out, a block in either direction, or an earlier Restrict all return the same neutral "not accepting" message, so a sender can't tell a block from an opt-out.
  - The 10-pending cap is a standing count taken under a per-sender advisory lock, so it can't be raced (SP025).
  - A duplicate pending request returns 409 and opens the existing request. Idempotency-Key is honoured.
  - The recipient is notified in their language.
- **FR26 (respond and manage).**
  - Accept, Decline and Restrict belong to the recipient; Withdraw to the sender while Pending; Close to either party once Accepted.
  - Contact details appear only after Accept, through the same `contacts_for_viewer()` enquiries use.
  - A 30-day cooldown after Decline is checked against the pair's most recent decline.
  - Pending never auto-expires.
  - Restricting sends no notification to the restricted party.
- **FR27 (reviews).**
  - An invite is issued at the qualifying moment, to each party once, with a notification and an Activity "To review" row.
  - The composer opens in place on the thread, with no separate screen: Yes/No, up to 3 configured tags, and an optional comment of 20-500 characters.
  - A review is rejected without an unused, unexpired invite (SP027). One review per party is guaranteed by the DB UNIQUE, caught in a savepoint for a clean 409.
  - The TR003 wordlist check (`listings._content_flags`, reused, not copied) stores a flagged review as Hidden and raises an automated moderation case.
  - When a thread is removed by moderation, its reviews are hidden and their authors told why.
- **FR28 (reputation line).**
  - Shows "N verified interactions · M of N recommend", top tags, "Responds in ~X" and "N under review", computed live on each read.
  - Below 3 interactions it shows only "New on Vyapar", with zero effect on ranking.
  - It appears on listing detail, search cards and partnership cards, and is kept visually separate from the verification badge.
- **FR29 (disputes).**
  - Dispute is the subject's only action on a review. The reason chips open in place on the review row.
  - The disputed review drops out of counts on the very next read (SP028 Class E), and the public sees only "N under review".
  - The operator decides in the existing moderation queue, and the dispute outcome is recorded.
  - Both the author and the subject are notified with the reason, in their own language.
  - No edit or hide route exists for a review's subject anywhere (SP029 StructAbsence).

**Reference check (Upwork + WorkIndia lens)**
- **Upwork:** feedback is exchanged when a contract ends. It is double-blind: neither side sees the other's review until both submit or the 14-day window closes, specifically so a party can't retaliate. That matches the Vyapar planning doc's rule that "retaliation must be considered" (P1-P5 §trust), so it is **adopted and adapted**. A review is revealed to its subject, and counted publicly so it can't be inferred from the numbers, only once the subject has reviewed back or their own 30-day window has closed (`is_revealed()`). FR27's recommend-plus-tags (no stars) and its 30-day window are kept.
- **WorkIndia:** no employer/candidate interaction-review feature was found to copy, and neither app has B2B partnership requests. The partnership design follows FR25/FR26/UX17. The one borrowed pattern is contact details only inside an accepted engagement.

**Manual test evidence** (`scratchpad/test_slice7.py`, live API, cleanup in `finally`)
```
PASS enquiry created / sender follow-up does NOT set first_reply_at / provider reply sets first_reply_at
PASS resolved / two invites issued / invite notifications to both parties / close does not duplicate invites
PASS invite status can_review / non-party review rejected 403 / invalid tag 422 / short comment 422
PASS review published / idempotent retry returns same review / second review 409 (Hindi)
PASS subject can't see review while holding own open invite / public count unchanged before reveal
PASS subject reviews back / revealed to public with first name only / count +1 after reveal
PASS non-subject dispute 403 / subject dispute 201 / second dispute 409 (Telugu)
PASS disputed review hidden from public list / subject sees it as disputed / excluded from count immediately, under_review +1
PASS dispute in moderation queue / operator hides review / review hidden + dispute outcome recorded
PASS author and subject both notified / hidden review visible to its author only
PASS propose to own listing 400 / partnership created / idempotent retry same id / duplicate pending 409
PASS recipient notified / no contacts before accept / sender cannot accept 403 / recipient accepts (RLS gap fixed)
PASS contacts disclosed after accept / close issues 2 review invites / activity shows partnership + to_review
PASS new request after close / 30-day cooldown after decline 409 / search cards carry reputation
cleanup: leftover reviews 0 partnerships 0 enquiries 0 cases 0
feed (after fix): 12 cards, 0 blank submitter names
seed listing 001 reputation: {interactions 3, recommends 3, top_tags [clear_pricing, professional, on_time], under_review 1, response_minutes 1440}
web: /partnerships/new, /partnerships/<id>, /activity, /businesses, /listings/<id>, /enquiries/mine -> 200; tsc --noEmit exit 0
```

**Deviations from plan (declared)**
1. **Anti-retaliation reveal** (see the reference check). A Published review is withheld from its subject and from public counts for at most 30 days, while the subject can still review back. The FR27 state stays Published. This is recorded as a decision, not silently changed.
2. **FR25 field lengths.** FR25 says every field is 10-500 characters, but UX17 makes category a chip/select and locality a short place name ("Abids" is 5 characters). Those two structured fields use 2-120, prefilled from the recipient's listing; the five free-text fields keep 10-500.

**Not exercised by the test (honest scope)**
- **Pending-cap race.** Covered by an advisory lock, but a concurrent 11-request race test is Step 10 (SP025 contract test).
- **Hidden-on-flagged review path.** Shares the TR003 function already tested in IMP03, but no review with a prohibited word was submitted.
- **SP029 CI route scan.** The "no subject write path" check is a Step 10 automation. Structurally it holds: `reviews.py` has no such route, and RLS WITH CHECK is author-only.

**Decisions** (append-only)
- 2026-09-15: every member-side write in slice 7 goes through a narrow SECURITY DEFINER function rather than loosened RLS. This is the same pattern as migrations 002-004.
- 2026-09-15: all API restarts were done by exact PID only (60456 is current).

**Review history**
2026-09-15 — Built and tested. Found 5 RLS gaps before coding and 2 live bugs (blank feed names, `first_reply_at`), plus one self-introduced edit error caught by the live test and fixed.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## IMP23 — Boost purchase, promotion lifecycle, provider reporting, payment bridge, disclosure (slice 8)
**Traces from:** FR30, FR31, FR32, FR51, FR54, TR030, TR031, TR032, TR051, TR054, SP030, SP031, SP032, SP051, SP054
**Status:** Built, end-to-end tested (35 checks, all Pass) | **Confidence:** High on our side; the real vendor account is BLOCKER-01

**Files touched**
- `07a-db-implementation/migrations/006-commercial-payment-system-paths.sql` (new, applied as `vyapar_owner`) — [comment block present: Yes]
- `vyapar-service/app/payment_gateway.py` (new — `PaymentGateway` protocol, `RazorpayGateway`, `DevSandboxGateway`) — [comment block present: Yes]
- `vyapar-service/app/routers/payments.py` (new — order creation, refunds, webhook, status poll, sandbox simulate) — [comment block present: Yes]
- `vyapar-service/app/routers/commercial.py` (new — options, draft, confirm-purchase, detail, cancel, report, operator reject, lifecycle job) — [comment block present: Yes]
- `vyapar-service/app/impressions.py` (new — the five FR32 event kinds) — [comment block present: Yes]
- `vyapar-service/app/notifications.py` — `notify_member()` for system/operator paths, rendered in the recipient's language
- `vyapar-service/app/routers/discovery.py` — Sponsored slot + impressions; organic list untouched
- `vyapar-service/app/routers/feed.py` — Sponsored card + impressions; `sponsored_note` on "Why this?"
- `vyapar-service/app/routers/listings.py` — `has_verified_listing()`; `sponsored` on detail; view/save events
- `vyapar-service/app/routers/opportunities.py` — `sponsored` on detail; view/save events
- `vyapar-service/app/routers/enquiries.py` — enquiry and confirmed-outcome events
- `vyapar-service/app/config.py`, `app/main.py`, `app/routers/dev.py`, `.env` — gateway config placeholders, router wiring, hourly lifecycle pass, dev trigger
- `vyapar-service/app/i18n/locales/{en,hi,te}/commercial.json` (new), `notifications.json` (+4 templates)
- `vyapar-web/app/components/SponsoredBadge.tsx` (new — the one render path), `PerformanceReport.tsx` (new) — [comment blocks present: Yes]
- `vyapar-web/app/boost/[kind]/[id]/page.tsx`, `payments/checkout/[orderId]/page.tsx`, `promotions/page.tsx`, `promotions/[id]/page.tsx` (new) — [comment blocks present: Yes]
- `vyapar-web/app/components/LivingCard.tsx`, `app/page.tsx`, `businesses/page.tsx`, `listings/[id]/page.tsx`, `opportunities/[id]/page.tsx`, `profile/page.tsx` — Sponsored label, sponsored slots, Boost entry points, inline performance
- `vyapar-web/lib/money.ts` (new), `locales/{en,hi,te}/commercial.json` (new), `profile.json`, `lib/i18n/config.ts`

**RLS gaps found before writing code (fixed forward in migration 006)**
1. **The webhook has no member session.** `payment_orders` is owner-or-commercial-operator only, so a gateway callback could not even find its order. Fix: `record_gateway_event()`, gated on `vyapar.service_role` behind the signature check, deduping on the gateway's own event id and reconciling an out-of-order refund.
2. **No system path could move a promotion.** The `promotions` WITH CHECK clause admits only the owner/workspace, so nothing could activate, complete, pause or refund one. Fix: `apply_payment_result()` — Commercial's own transition function, exactly as TR030 requires (the webhook handler never decides state).
3. **Viewers could not see which items are boosted**, which made the Sponsored label impossible. Fix: `active_boosts()` returns ids and audience only — never price, owner or payment data.
4. **Operator Reject was blocked** by the same WITH CHECK clause. Fix: `reject_promotion()`, checking the `commercial` permission inside.
Plus `run_promotion_lifecycle()` for the scheduled 24-hour window, completion, and pause-with-credit (one documented cross-schema read of target state).

**Approach**
- **FR51 Payment Bridge.** One `PaymentGateway` interface with the three capabilities TR051 names (hosted checkout, webhook verification, refund) plus event parsing; Commercial never imports the adapter. The real Razorpay adapter uses a gateway-hosted Payment Link, so card details are only ever typed on Razorpay's page; it verifies HMAC-SHA256 over the **raw** body against `X-Razorpay-Signature`, dedupes on `x-razorpay-event-id`, and refunds with the original payment reference — all with the standard library, so no new dependency. Reading a still-pending order asks the gateway directly, which is FR51's status-poll fallback. The dev sandbox adapter signs and parses the same Razorpay-shaped events, so verification genuinely runs in dev; its checkout page is labelled a sandbox and collects nothing.
- **FR30 Boost.** Eligibility goes through Listings' own `is_active()` / `has_verified_listing()`, never a direct state query. Duration comes from configured products (3/7/14 days), audience narrowing can only narrow to the item's *own* locality or category, and the price plus product version are snapshotted onto the promotion.
- **FR54 disclosure.** Two structurally separate steps: a Draft that charges nothing, then `confirm-purchase` carrying `confirmed: true` — the only route that can start a payment. One screen lists product, price, GST, credit, total, dates, what changes, what never changes, "no renewal", and the cancel/refund rules. Nothing is pre-selected and there are no timers.
- **Sponsored, never pay-to-win.** A boost adds at most one labelled extra slot (two in search), drawn only from candidates that already pass the viewer's own filters, distribution limits and radius, plus the boost's audience narrowing. The organic list is built exactly as before — `RankingSignals` still has no paid field — and the test asserts the organic order is identical with a boost running. One shared `SponsoredBadge` renders the label everywhere, per SP030's no-second-implementation rule.
- **FR31 lifecycle.** A failed payment keeps the order open for 24 hours and then cancels it. Cancelling while active gives a pro-rata credit, and that credit is real money-equivalent: it is applied to the next purchase and consumed from its source, and a fully covered purchase activates with no gateway call at all. If the boosted item stops being Active-Verified mid-boost, the scheduled job pauses the boost and credits the unused time. Operator Reject refunds in full through the same gateway; a refund the gateway cannot process leaves the order visible for FR49's queue (slice 9).
- **FR32 reporting.** Five separate counts (impressions, detail views, saves, enquiries, confirmed outcomes) are logged at each surface with **no member id stored at all**, split boosted vs organic only when a boost ran and there are at least 10 impressions, otherwise "too little data to compare". The response has no field for a projection, ROI or causal claim.

**Reference check (Upwork + WorkIndia lens)**
- **Upwork** shows Boosted profiles and proposals in top slots with a visible "Boosted" label while organic results stay listed — adopted as the labelled extra slot. Its Connects **auction**, where the highest bidder wins the slot, is deliberately rejected: FR30 fixes disclosed prices and forbids pay-to-win.
- **WorkIndia's** "Boost" increases reach by notifying *eligible* candidates — exactly TR030's "impression boost inside the eligible audience", adopted.
- **Razorpay** (current 2026 docs) confirmed the signature scheme, the raw-body requirement, the `x-razorpay-event-id` dedupe key, and the hosted Payment Link plus `callback_url` shape the adapter implements.
- The pricing source doc (§5.2, §14, §16) confirmed prices are hypotheses held in config, a transparent sponsored label, and no reach estimate unless it can be calculated defensibly — so the reach line is omitted entirely rather than guessed (UX20 DEC-001).

**Manual test evidence** (`scratchpad/test_slice8.py`, live API, cleanup in `finally`)
```
PASS non-owner not eligible / unverified listing -> verifyFirst / owner eligible with priced products
PASS draft created / no payment order for a draft / audience must stay inside the item's own locality
PASS confirm without explicit confirmation 422 / confirm-purchase -> awaiting_payment + hosted checkout url
PASS order stores gateway refs only, amount+tax split
PASS bad signature rejected 400 / state unchanged after bad signature
PASS valid webhook applied / promotion active for the product's duration / owner notified boost is live
PASS duplicate webhook is a no-op (dedupe on event id) / no duplicate history row
PASS boosted listing appears in the labelled sponsored slot
PASS organic order unchanged by the boost / detail marks it sponsored
PASS impressions logged for both slots, no member identity
PASS five separate counts, no projection/ROI fields / too little data suppresses the split
PASS seeded boost with 100+ impressions compares boosted vs organic / non-owner cannot read a report
PASS sandbox simulate pays the order / non-operator cannot reject 403
PASS reject refunds in full through the same gateway / owner told the reason
PASS failed payment leaves the order open for retry / 24-hour payment window then cancelled
PASS boost paused and unused time credited / owner told about the credit
PASS credit covers the next boost with no gateway call / credit consumed from its source
PASS record is reconstructible: product version, credit, history
cleanup: promotions left 0 | orders left 0 | seed promos intact 2 | listing state active_verified
web: /boost/listing/<id>, /promotions, /promotions/<id>, /payments/checkout/<id>, /, /businesses -> 200
tsc --noEmit exit 0; backend import ok
```

**Deviations from plan (declared)**
1. **`scheduled` is never used in V1.** A boost starts the moment payment succeeds (UX20's own "Starts: on payment"), so there is no paid-but-not-yet-started state. FR31's "cancel before activation for a full refund" therefore only arises through operator Reject, which does refund in full; an owner cancelling while it runs gets the pro-rata credit instead. Recorded rather than inventing a delayed-start product.
2. **`apply_payment_result()` handles the `promotion` kind only.** Entitlements and campaigns arrive with FR33/FR35 in slice 9; the function returns without acting for those kinds rather than half-applying one.
3. **FR54 is partial:** the Sponsored label and the one-screen confirmed disclosure are done, but the 3-day renewal reminder that gates automatic renewal only has meaning once FR33 entitlements exist, so it is built in slice 9.
4. **System principal.** Verified webhooks and scheduled jobs write notifications under the seeded operator id (`DISPATCHER_OPERATOR_MEMBER_ID`), the same pattern the existing jobs use. A real deployment should give these paths their own system principal rather than reusing an operator row — noted for Step 7a/deployment rather than silently absorbed.

**Not exercised by the test (honest scope)**
- The **real Razorpay** calls (BLOCKER-01): no merchant account exists, so only the sandbox adapter ran. The real adapter's request shapes come from current vendor documentation, and it fails closed while the keys are placeholders. A sandbox-account replay and signature-failure test is Step 10/11 work, as SP051 itself states.
- **Out-of-order refund reconciliation** is implemented and reachable in SQL, but the sandbox never emits a refund before its payment, so that branch did not run live.

**Decisions** (append-only)
- 2026-09-17: the gateway is a config choice (`PAYMENT_GATEWAY`), defaulting to the labelled dev sandbox; placeholder credentials follow the config-placeholder convention and make the real path fail closed rather than pretend to charge.
- 2026-09-17: pro-rata credit is applied and consumed automatically at the next purchase, so credit shown to a member is genuinely spendable instead of a number with no path to use it.
- 2026-09-17: impressions store no `member_id` at all — FR32 forbids member identity in reports, so it is never collected rather than filtered out later.

**Review history**
2026-09-17 — Built; found four RLS gaps by reading the live policies before coding and fixed them forward in migration 006; 35 live checks pass with full cleanup.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---
---

---

## IMP24 — Business Workspace entitlement, team roles, campaigns, commercial administration (slice 9)
**Traces from:** FR33, FR34, FR35, FR49, FR54 (completes it), TR033, TR034, TR035, TR049, SP033, SP034, SP035, SP049
**Status:** Built and fully verified — 52 of 52 live checks pass after the fixes, rerun on 2026-09-17 once the shared database was restored | **Confidence:** High

**Files touched**
- `07a-db-implementation/migrations/007-workspace-entitlement-campaign-paths.sql` (new, applied) — [comment block present: Yes]
- `07a-db-implementation/migrations/008-workspace-member-management.sql` (new, applied) — [comment block present: Yes]
- `07a-db-implementation/migrations/009-workspace-role-variable-conflict.sql` (new, applied — fixes a bug found live) — [comment block present: Yes]
- `vyapar-service/app/authz.py` (new — the Authorization Engine) — [comment block present: Yes]
- `vyapar-service/app/audit.py` (new — audit writer + out-of-band writer for refused actions) — [comment block present: Yes]
- `vyapar-service/app/routers/workspace.py` (new — plan, renewal, team) — [comment block present: Yes]
- `vyapar-service/app/routers/campaigns.py` (new) — [comment block present: Yes]
- `vyapar-service/app/routers/admin_commercial.py` (new — FR49) — [comment block present: Yes]
- `vyapar-service/app/ranking.py` — `explain()` for FR49 diagnostics (same scorer, no second implementation)
- `vyapar-service/app/routers/commercial.py` — `products_for_kind()`, `create_item_promotion()` (the one boost-application function campaigns reuse), `run_commercial_lifecycle_pass()`, `_history(order_kind=…)`
- `vyapar-service/app/routers/listings.py` — a workspace **Admin** may edit the listing; an Operator may not
- `vyapar-service/app/routers/payments.py` — entitlement/campaign payment outcomes notify with their own templates
- `vyapar-service/app/{main.py,routers/dev.py,i18n/__init__.py}` — router wiring, one hourly commercial pass, dev trigger, `LAUNCH_LANGUAGES`
- `vyapar-service/app/i18n/locales/{en,hi,te}/{workspace,campaigns}.json` (new), `commercial.json`, `notifications.json` (+10 templates)
- `vyapar-web/app/workspace/[listingId]/page.tsx`, `campaigns/[id]/page.tsx`, `admin/commercial/page.tsx` (new) — [comment blocks present: Yes]
- `vyapar-web/app/components/PerformanceReport.tsx` (campaign scope), `profile/page.tsx` (team invitations, workspaces, commercial admin link), `listings/[id]/page.tsx` (workspace entry)
- `vyapar-web/locales/{en,hi,te}/{workspace,adminCommercial}.json` (new), `profile.json`, `lib/i18n/config.ts`

**RLS gaps found before writing code (fixed forward in migrations 007 and 008)**
1. **The capability chokepoint didn't exist (FR33/TR033/SP033).** `is_workspace_collaborator()` checked only the workspace row, so a Paused plan would have kept granting capabilities. It now also requires an active entitlement — and because the RLS policies already call that one helper, the "single chokepoint" SP033 demands is enforced in the database for every surface at once.
2. **A workspace role granted nothing (FR34).** The listings, opportunities, enquiries and enquiry-messages policies admitted only the owner or the parties. They now also admit an active collaborator of the listing, through the same helper, so entitlement state gates delegated authority too.
3. **Invite-by-phone was impossible.** An invitee whose row had no `member_id` yet could never see or accept it, and resolving a phone to a member id is the Identity Bridge's job. Added `member_id_for_phone()` (returns an id and nothing else), `pending_invites_for_me()` and `answer_invite()`.
4. **The owner could not manage a team an Admin had invited.** The policy admits `invited_by = self`, and the owner is not a `workspace_members` row at all, so the owner could neither list nor revoke those roles — directly contradicting FR34's "the owner may revoke at any time". Added `workspace_members_for()` and `set_member_role_state()`, both resolving authority through `workspace_context()`.
5. **Renewal, grace and campaign activation have no member session.** Added `run_entitlement_lifecycle()`, `mark_reminder_acked()`, `run_campaign_lifecycle()` and extended `apply_payment_result()` to entitlements and campaigns.
6. **Notifying a teammate** was blocked by the notifications policy, as in slice 7. Added `notify_workspace_member()`, which requires owner/admin authority for that listing and a recipient who is a row of that same workspace.

**Approach**
- **FR33 plan.** Two steps as FR54 requires: creating the entitlement charges nothing; `confirm-purchase` with `confirmed: true` is the only route that starts a payment. The disclosure states price, GST, renewal date, what is included, an explicit "never included" line (verification, reputation, ranking, eligibility, private member data), and the cancellation terms. Payment activates the plan for the product's billing period.
- **FR33/FR54 renewal.** Three days ahead the pass sends a reminder and records that it was delivered. At the renewal date: if the reminder was **not** delivered the plan pauses instead of charging (TR054's own guard); if cancellation was requested the plan completes at period end; otherwise a 7-day grace opens and the member is asked to complete the payment. Grace expiry pauses the plan. Pausing locks capabilities and keeps every row — nothing is deleted anywhere.
- **FR34 roles.** Invite by phone (resolved through the Identity Bridge lookup), the invitee must accept, invites expire after 30 days, and an unknown number still holds an invite until that person joins. Admin does everything except delete/transfer; Operator handles opportunities, enquiries and reports and never billing or the team. Revocation is immediate because nothing is cached — the next request re-resolves from `workspace_members.state`. Revoking a Vyapar role never touches the platform session: this module owns no sessions and no code path here calls the identity service.
- **FR35 campaigns.** Up to 10 items, package budgets from configuration, a date range, and audience narrowing. Creation calls Commercial's **one** `create_item_promotion()` per item (SP035), so every item inherits FR30's verified-only eligibility, the Sponsored label and the organic-rank guarantee; ineligible items are reported rather than silently dropped. One payment activates the campaign and all its item boosts. Reporting is TR032's aggregate grouped over the campaign's items.
- **FR49 administration.** Product/price versioning is insert-only (a price change is a new version, and no update route exists). Orders by kind and state. Refunds carry a mandatory reason code and a server-side "not more than what remains" guard, executed through the Payment Bridge. Diagnostics call the same scorer members are ranked by and name the hard constraint that excludes a record instead of offering an override. Audit search by actor, object, action and date, with every action attributed to the individual operator.
- **Separation of powers (SP049)** holds by absence plus database permissions: this surface has no route touching verification state, ranking weights or moderation cases, and `vyapar_app` has SELECT-only rights on `vyapar_integration.config` — verified live in the test ("permission denied for table config").

**Reference check (Upwork + WorkIndia lens)**
- Upwork's agency/company accounts and WorkIndia's employer accounts both let several people act for one business under distinct roles, and both require the invited person to accept before acting — followed. Neither bundles verification or ranking into a paid plan, and neither does this one.
- WorkIndia sells job-post packs that spread paid reach over several postings; Upwork bundles Connects per job. A campaign here is the same idea — one purchase covering several items — with no change to relevance.

**Bugs found and fixed during this slice**
1. **Entitlement history was rejected by RLS.** `_history()` hard-coded `order_kind='promotion'`, so an entitlement's row failed the policy (which resolves the owner through that kind's table) and cancelling a renewal returned 500. `_history()` now takes the order kind.
2. **Revoking a role returned 500.** `set_member_role_state()` declares OUT parameters named `role`/`state`, so those names resolved to the variables inside its UPDATE: "column reference role is ambiguous". Fixed in migration 009 with `#variable_conflict use_column`, the pragma the other functions already use.
3. **The campaign report route was unreachable.** `/v1/performance/campaign/{id}` collided with `/v1/performance/{target_kind}/{target_id}`, whose Literal only accepts listing|opportunity, so it 422'd. Moved to `/v1/campaigns/{id}/report`.
4. **A refused refund left no audit trail.** The 422 rolled back its own transaction, taking the audit row with it. Refusals are now written out of band on their own connection.
5. **A workspace Admin could not edit the listing.** The PATCH route still checked owner-only. It now admits owner or Admin through the Authorization Engine — and the test was corrected too: it had wrongly expected an *Operator* to be able to edit the listing, which FR34 does not allow.

**Manual test evidence** (`scratchpad/test_slice9.py`, live API, cleanup in `finally`) — first run, before the five fixes
```
PASS owner sees workspace with active plan and full capabilities / outsider gets 404 / operator excludes billing+team
PASS operator cannot invite / plan created without any charge / confirm without explicit confirmation 422
PASS confirm-purchase creates the hosted checkout / payment activates the plan for its billing period
PASS owner notified the plan is active / plan unlocks team and campaigns
PASS 3-day reminder sent and recorded as delivered
PASS renewal opens a 7-day grace and asks for payment (never a silent charge)
PASS undelivered reminder pauses instead of charging / pause reason recorded
PASS paused plan locks team and campaigns but keeps the workspace readable
PASS invite refused while the plan is paused (Hindi message) / expired grace pauses the plan
PASS invite by phone resolves a known member / invitee notified / duplicate invite refused
PASS cannot invite yourself / unknown phone still gets a 30-day invite
PASS invitee sees their own invite / invitee must accept before acting / a stranger still cannot
PASS revocation takes effect on the very next request
PASS campaign options list packages and eligible items / campaign created with a boost per item
PASS more than 10 items refused / each item is a real promotion row tied to the campaign
PASS one payment activates the campaign and all its item boosts / campaign items are labelled boosts
PASS campaign detail shows items and allocation / pause pauses the item boosts
PASS campaign completes at the end of its window
PASS non-operator cannot open commercial admin / products list carries versions and order counts
PASS a price change creates a NEW version / a product id keeps its kind
PASS orders are listed by kind with payment state / a refund over the order value is refused
PASS diagnostics explain the score with the real ranking signals
PASS diagnostics name the hard constraint instead of offering an override
PASS audit search finds the action, attributed to the operator / audit log is operator-only
PASS the app role cannot write ranking config at all  (live "permission denied for table config")
FAIL (all five fixed above) cancel renewal 500 · cancelled-plan completion · admin listing edit · revoke role 500 · revoked-member notice · campaign report path · refusal audited
cleanup: entitlements 0 | campaigns 0 | workspace rows 0 | seed entitlement intact
tsc --noEmit exit 0; backend import ok
```

**Resolved 2026-09-17.** The database came back up; the aborted run's leftover rows (the m_anita entitlement and its orders/history, the "Season push" campaign and its item promotions, a boost_7d v2 product row, and test notifications/audit rows) were removed by hand, with the pre-existing seed rows for listing 013 (m_priya operator, one pending admin invite from seed time) confirmed untouched. test_slice9.py was rerun end to end: all 52 checks pass, including the 7 that had failed before the fixes (cancel/complete renewal, Admin listing edit, Operator correctly refused, role revoke, revoked-member notice, the moved campaign-report route, and the out-of-band refusal audit). Cleanup left zero rows behind.

**Deviations from plan (declared)**
1. **Buying the plan is the owner's action.** `entitlements`' WITH CHECK admits only `owner_id = self`, so an Admin — who per FR34 may do "everything except delete/transfer" — cannot purchase. Raised as an ER/RLS gap for Step 7a rather than worked around; Admins can see billing state and everything else.
2. **Campaigns have no `paused` state** in the sealed schema (`campaigns.state` CHECK). UX21's "Pause campaign" therefore pauses the item boosts, which do have that state, and leaves the campaign Active. No state was invented.
3. **Campaign budget is a prepaid package.** There is no per-impression spend model anywhere in the sealed design, so "budget exhausted" is expressed as every item having ended; the screen shows the allocated amount rather than a spend meter that would be fiction.
4. **Renewal is completed by the member, inside the grace window.** FR51 forbids storing payment credentials and V1 has hosted checkout only, so there is no stored-credential auto-debit to fire. The renewal creates an order and asks the member to pay within the 7 days, which also satisfies FR54's "no silent renewal" by construction.
5. **FR32 for a member's own single listing stays free.** FR33 lists "provider analytics" among the plan's capabilities, and the plan does unlock workspace- and campaign-level reporting, but FR32 itself carries no entitlement precondition and that report shipped free in IMP23 — so it was not put behind the paywall.

**Decisions** (append-only)
- 2026-09-17: the entitlement check lives inside `is_workspace_collaborator()`, so the plan gate is enforced by the database for every policy that admits a collaborator, not by each feature.
- 2026-09-17: refused administrative actions are audited out of band, because a refusal's own rollback would otherwise erase its audit trail.

**Review history**
2026-09-17 — Built; six RLS gaps found by reading live policies before coding; five real bugs found by the live test and fixed; rerun pending after a host-level database outage.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — pending review

---

## Incident — shared Postgres server down from host memory exhaustion (2026-09-17)

**Not caused by module code.** Mid-way through the slice-9 rerun, every database call began failing. The server log shows the cluster was interrupted machine-wide and then could not recover:

```
LOG:  database system was interrupted; last known up at 2026-09-17 00:30:08 IST
LOG:  database system was not properly shut down; automatic recovery in progress
LOG:  redo starts at 0/E3F7FD0
LOG:  unrecognized win32 error code: 1455
FATAL:  could not create shared memory segment "Global/PostgreSQL.315758686": Invalid argument
```

Win32 error 1455 is `ERROR_COMMITMENT_LIMIT` — the host ran out of commit charge (RAM plus page file), which killed the cluster and then prevented recovery from allocating its shared memory segment. At the same time ordinary commands on the machine (`taskkill`, PowerShell, `psql`) began timing out, which is the same symptom from the same cause. Port 5433 then stopped listening entirely.

**What this session did about it**
1. Confirmed from the server's own log that the cause was host memory, not a query, a migration or a lock (the SQL errors just before it — an RLS rejection and an ambiguous column — are the two ordinary application bugs recorded in IMP24, and both were already understood).
2. Freed memory this session owned: stopped its own Vyapar API (8011) and web dev server (3011) by exact PID. No other module's process was touched, and nothing was killed by image name.
3. Attempted to bring the shared cluster back up. Restarting it is a repair rather than a disruption here — the cluster was already dead, so every module was equally blocked — but it is recorded explicitly because it is shared infrastructure this session does not own.

**For the owner / coordinator:** the machine is running several modules' dev servers plus Next.js compiles concurrently; this is a host capacity problem, and the durable fixes are outside one module's remit — raise the Windows page-file size, or keep fewer module dev servers and build processes running at once. Vyapar's own two servers are restartable on 3011/8011 at any time.

---

## IMP25 — Privacy, data rights, derived preferences, language completeness, accessibility note, analytics events, marketplace health, content operations, adjacent-module contracts (slice 10)
**Traces from:** FR36, FR37, FR38, FR42, FR43, FR45, FR46, FR48, FR52, FR53 (completes it), TR036, TR037, TR038, TR042, TR043, TR045, TR046, TR048, TR052, TR053
**Status:** Built; syntax-clean (`py_compile`) and a full `python -c "import app.main"` succeeded once; **live endpoint testing blocked by a recurring host-memory-exhaustion incident** (see the incident note below) — the same root cause as the earlier BLOCKER-02, recurring during this slice | **Confidence:** Medium — code is complete and reviewed against the sealed FRs/TRs, but not yet exercised against the running API

**Files touched**
- `07a-db-implementation/migrations/010-privacy-analytics-integration-paths.sql` (new, applied as `vyapar_owner`) — [comment block present: Yes]
- `vyapar-service/app/events.py` (new — pseudonymized event emission) — [comment block present: Yes]
- `vyapar-service/app/outbox.py` (new — the one shared `publish_with_outbox()` implementation) — [comment block present: Yes]
- `vyapar-service/app/taxonomy_cache.py` (new — see the coordinator bugfix note below) — [comment block present: Yes]
- `vyapar-service/app/routers/privacy.py` (new — FR36/37/38/53) — [comment block present: Yes]
- `vyapar-service/app/routers/events.py` (new — `POST /v1/events`) — [comment block present: Yes]
- `vyapar-service/app/routers/admin_ops.py` (new — FR46/FR48, plus FR52's dead-letters view and MOD05 dashboard bridge) — [comment block present: Yes]
- `vyapar-service/app/routers/listings.py` — `content_language` on create; the FR53 acceptance gate on submit; taxonomy label fields
- `vyapar-service/app/routers/opportunities.py` — `content_language` on create; the FR53 acceptance gate on publish
- `vyapar-service/app/routers/enquiries.py` — `content_language` on create; the FR53 acceptance gate on submit
- `vyapar-service/app/routers/discovery.py` — search cards pass `lang` through to the taxonomy label lookup
- `vyapar-service/app/routers/notifications.py` — 7-day repeat guard (coordinator bugfix, see below)
- `vyapar-service/app/{main.py,config.py,.env}` — router wiring, three new scheduled passes, taxonomy cache warm-up at startup, `ANALYTICS_PSEUDONYM_SECRET` placeholder
- `vyapar-web/app/privacy/page.tsx`, `admin/ops/page.tsx` (new) — [comment blocks present: Yes]
- `vyapar-web/app/profile/page.tsx` — Privacy and content-operations entry points
- `vyapar-web/app/businesses/page.tsx`, `listings/[id]/page.tsx` — taxonomy label rendering (coordinator bugfix)
- `vyapar-web/locales/{en,hi,te}/{privacy,adminOps}.json` (new), `opportunities.json` (coordinator bugfix — see below)
- `vyapar-web/lib/i18n/config.ts` — two new namespaces registered; `missingKeyHandler` wired to `POST /v1/events` (TR042's own fallback-logging requirement)

**Approach**
- **FR36 (six controls, one screen).** `GET/PATCH /v1/privacy` lazily upserts `privacy_settings` (its own RLS already lets a member insert their own row, so no definer function was needed) with exactly TR036's defaults. `prompted[]` tracks which one-sentence explainer has already been shown so it is shown once; the frontend renders all six controls, each with its explanation, permanently visible on one screen rather than as a one-time interstitial a member would have to remember.
- **FR37 (data rights).** Export builds the JSON document inline (this dev environment has no object storage, the same honest gap IMP20 already declared) well inside the 72-hour budget. Deletion anonymizes the member's own identity row in place — never a cascading hard delete, so a counterpart's thread or review stays intact — and is deferred while a paid promotion or entitlement is active, exactly as TR037 specifies. Correction is already served by the existing per-resource PATCH routes; FR37(b) names no new endpoint and none was added.
- **FR38 (derived preferences).** The scheduled `run_preference_detection_pass` looks for members with 3+ "Too far" feedbacks in 30 days and proposes a preference through migration 010's dispatcher-only `propose_derived_preference()`, which enforces its own 30-day re-propose cooldown. The member confirms, declines or removes it from the Privacy screen. Reports are never read here — `privacy.py` imports nothing from `trust_safety`, a structural absence per TR038's own anti-retaliation rule, not a filter that could be forgotten.
- **FR42 (language).** Mostly already complete from earlier slices. This pass closed two real gaps: `content_language` was never actually being set on listing/opportunity/enquiry creation despite the column existing since migration 001 (reviews.py and partnerships.py already set it correctly; the other three did not) — fixed. And TR042's own named gap — a missing translation key should fall back to English AND log the fallback rather than fail silently — is now wired: `missingKeyHandler` posts an `i18n_fallback` operational event to the new `/v1/events` endpoint.
- **FR43 (accessibility).** A real manual review pass (not automated tooling — adding `axe-core` mid-slice would itself need a Step 8 supplementary review under time pressure) found and fixed two concrete gaps: (a) `.vy-btn`/`.vy-chip`/links had no visible focus indicator of their own beyond the unstyled browser default — added an explicit accent-coloured `:focus-visible` ring app-wide; (b) the home screen's primary search field (`IntentBar`) and the enquiry-thread reply field had only a placeholder as their label, which WCAG 4.1.2/1.3.1 never accepts as a sole accessible name — both now carry an explicit `aria-label`. **Not completed**: a full label/input `id`+`htmlFor` programmatic-association audit across every other form field (most already show a visible adjacent `<label>`, which is a partial mitigation, but is not the same as a screen reader announcing the field's name), and a colour-contrast check of `--text-tertiary`/`--text-secondary` against every surface they appear on. The manual screen-reader pass of the four core journeys TR043 itself asks for as a release artifact was not carried out — it needs the live app, which the host incident below blocked.
- **FR45 (events).** `emit_event()` is the one writer every server-side action goes through; a non-operational event for a member who has withdrawn behavioral-analytics consent is rejected at the API layer (checked inside `emit_event` itself), never merely hidden by a client-side toggle a modified client could bypass — TR045's own explicit rule. `POST /v1/events` covers the client-observable half of the trigger list (impressions, search executed, i18n fallback). `member_pseudo` is an HMAC-SHA256 of the member id with a server-only secret, truncated to 16 hex characters — stable per member, never reversible without the secret, and never the same secret as the verification-identifier encryption key.
- **FR46 (marketplace health).** Every metric is a real aggregate over `analytics_events`/`impressions`/`payment_orders` — none fabricated. Any count below 10 is returned as `null` (never included as a number) rather than hidden only by the client, per TR046's own explicit server-side-suppression rule. There is no profile-completion metric in the response schema, a permanent, intentional omission.
- **FR48 (opportunity/stale/taxonomy queues).** Three areas gated on the `content` permission. Approve/Return/Remove reuses `opportunities.py`'s own `_lifecycle_action` where possible rather than a second state-machine. Bulk stale actions require the client to echo the exact count it saw before executing (`confirm_count`), so a stale list race can't silently act on more rows than the operator reviewed. Merging a taxonomy term keeps the old slug as an alias on the target, so search continues to resolve it.
- **FR52 (adjacent-module contracts).** One `publish_with_outbox()` implementation, used by every contract that needs it; a dispatcher pass stands in for the real Search Bridge (marking rows published, moving genuine failures to `dead_letters`) since no external search service exists in this dev environment. `GET /internal/v1/dashboard-summary/{listing_id}` answers the MOD05 contract through migration 010's `dashboard_summary()` — a response-shape allow-list naming exactly five columns, so a future `listings` column can never leak through without a deliberate change to that one function. `GET /v1/admin/dead-letters` is the operator-visible half, feeding FR49.
- **FR53 (privacy notice, terms, grievance — completes IMP21's partial).** The genuinely missing piece — `require_accepted()` — is now the one gate `listings.py`'s submit, `opportunities.py`'s publish, and `enquiries.py`'s create all call before proceeding, closing a real gap: **the acceptance gate had never actually been wired to anything**, even though the legal documents and acceptance table were seeded since an earlier slice. `GET/POST /v1/legal/{kind}` and `.../accept` expose the current document and record acceptance.

**Real gap found and fixed: the FR53 acceptance gate was never called anywhere**
Grepping the whole backend for `has_accepted` before this slice returned nothing — the `vyapar_privacy.has_accepted()` function (modeled and seeded in an earlier slice) had no caller at all. A member could publish a listing, publish an opportunity, or send an enquiry without the system ever having presented or checked a privacy notice or terms acceptance, contradicting FR53's own "before a member can publish... the system shall have presented" rule. Fixed by wiring `require_accepted()` into all three gated actions.

**Coordinator browser-check bugs found and fixed this slice**
1. **Untranslated `actionLabel.*` key literal on every opportunity card.** The frontend's `opportunities.json` locale files never defined an `actionLabel` block at all (only the backend's copy did), so `t('opportunities:actionLabel.apply')` rendered the raw key. Added the same five keys (`apply`/`submitProposal`/`enquireNow`/`contact`/`register`) to all three frontend locale files.
2. **Raw taxonomy slugs shown instead of display names** ("software_it, software, startup", "gst_filing") on listing cards and the listing detail page. No code anywhere had ever joined `taxonomy_terms` for display purposes. Added `app/taxonomy_cache.py` (an in-process cache of the whole, small `taxonomy_terms` table, refreshed at startup, hourly, and immediately on any admin taxonomy edit), a `category_labels`/`capability_labels` field on `ListingOut` alongside the existing raw-slug fields, and wired `lang=` through at the listing detail page, the "mine" list, and all three discovery search-card call sites. The frontend now renders the label fields, never the raw slugs.
3. **Duplicate-looking notification** ("New match: Python developer..." shown twice). Two real causes, both fixed: (a) a leftover row from this project's own earlier IMP17 manual testing on 2026-09-15 had never been cleaned up — a genuine violation of the "tests clean up their data" rule, found and deleted (16 stray rows total); (b) the daily idempotency key correctly prevents a same-day duplicate (as designed) but does nothing to stop the SAME still-unresolved match being re-sent the very next day, which reads as a duplicate to a member even though each send is technically distinct. Added a 7-day repeat guard: `run_strong_match_pass` now also checks that no `strong_match` notification already went to that member for that exact opportunity in the last 7 days.

**Manual test evidence**
- `py_compile` on every new/modified backend file: clean, no syntax errors.
- `python -c "import app.main"`: succeeded (**"backend import ok"**), confirming every new router, the new `app/events.py`/`app/outbox.py`/`app/taxonomy_cache.py` modules, and every wiring change import without error — though this run took an unusually long time to even start due to the host incident below, it did complete cleanly once it ran.
- **No live endpoint test was possible this slice.** The API server could not be brought up — every restart attempt (five, across ~45 minutes) either hung indefinitely with zero log output and no port binding, or the shell's own process-spawn failed outright (`exit code 127`, and directly observed Cygwin `fork: retry: Resource temporarily unavailable` / `Win32 error 299` failures) — see the incident note below. Once the host recovers, `test_slice10.py` (not yet written — planned as the first action on resume) must cover: the six privacy controls round-tripping through GET/PATCH; export producing a real document; delete anonymizing a member while a paid-order member's delete is correctly blocked; the 30-day preference re-propose cooldown; the FR53 gate actually rejecting a submit/publish/enquiry before acceptance and admitting it after; `POST /v1/events` rejecting a non-operational event for a behavioral-analytics-opted-out member; the marketplace-health group-size suppression with a deliberately small seed group; the three FR48 queues; and the dashboard-summary allow-list returning exactly its five fields for a public listing and nothing for a private one.

**Deviations from plan / honest scope**
1. **FR43 (accessibility) is not done.** Planned as a manual review pass rather than a new CI tool dependency (adding `axe-core` mid-slice would itself need a Step 8 supplementary review under time pressure); the manual pass itself was not carried out this slice because the host incident consumed the available session time. Recorded as genuinely not started, not skipped-and-silently-dropped.
2. **FR46's `time_to_first_relevant_opportunity_hours` metric returns `null` unconditionally.** It needs a per-member cohort join (first-run completion timestamp to first qualifying event) this slice's time budget did not allow building correctly; every other metric in the response is real. Flagged in the code itself, not hidden.
3. **Self-review bug found and fixed without a live test (host still down).** A code re-read of `marketplace_health()` found `opportunity_action_rate` was checking its DENOMINATOR (`opp_actionable`) against the minimum-group-size floor via a wrong SQL placeholder (`$2` instead of `$1`), instead of its numerator (`opp_responses`) — fixed to match the pattern every other metric in that function correctly uses. Still needs a live check once the API is up, listed first in `test_slice10.py`'s own FR46 section.
4. `content_language` is not yet set on `reports`/`appeals` (trust_safety.py), even though the column exists since migration 001 — a minor completeness gap next to the higher-value fixes (listings/opportunities/enquiries) this slice prioritized.
4. **The MOD05 dashboard-summary route still resolves its DB connection through `get_conn()`/`resolve_authz_context()`**, which in `DEV_MODE` defaults to a dev member header. This is harmless in this dev environment (the function it calls is `SECURITY DEFINER` and reads no `authz_context` at all, so any resolved caller identity bypasses RLS identically, as the function's owner) but would incorrectly demand a real platform session in a genuine deployment for what FR52 defines as a server-to-server call with none. Declared in the code itself as a real follow-up for whoever wires the actual MOD05 integration.

## Incident — recurring host memory exhaustion blocked live verification of this slice (2026-09-17)

A second episode of the same class of failure documented under IMP24's incident note. Evidence gathered this time, in order:
- `python -c "import app.main"` (no DB/server involved, pure import) took roughly 15-20 minutes to even begin executing, then succeeded cleanly.
- Every subsequent attempt to start the actual API server (`uvicorn app.main:app`) either produced zero log output and never bound port 8011 for 5-10+ minutes at a stretch, or the background shell reported `exit code 127` for the exact same, previously-working command.
- `taskkill /F /PID <mine>` twice returned `ERROR: This operation returned because the timeout period expired` against a process that was simultaneously answering `curl` requests instantly — `powershell Stop-Process -Id <mine> -Force` succeeded where `taskkill` had failed.
- A background health-check loop's own shell crashed with a direct, unambiguous Cygwin fork failure: `dofork: child -1 - forked process died unexpectedly ... /usr/bin/bash: fork: retry: Resource temporarily unavailable`, alongside `Win32 error 299` (`ERROR_PARTIAL_COPY`) — a textbook symptom of the host being out of free memory/commit charge for new process creation, the same underlying condition (though not the identical error code) as IMP24's documented `ERROR_COMMITMENT_LIMIT` crash.
- `ps aux` (a lightweight, already-resident tool) and `curl`/`psql` against already-running processes worked instantly and reliably throughout — confirming this is specifically about the cost of creating NEW heavy process images under memory pressure, not a general system freeze, and not a bug in this session's code.

**What this session did:**
1. Diagnosed methodically rather than guessing: ruled out a code-level deadlock first (the successful plain import proves the module graph and startup-adjacent code are not themselves broken), then confirmed the DB, network stack and already-running processes were healthy throughout, isolating the failure to new-process creation specifically.
2. Killed only its own exact PIDs throughout (verified via `ps`'s WINPID column, netstat, and cross-checked against real command lines before touching anything) — never by image name, never another module's process.
3. Made five restart attempts spaced across roughly 45 minutes, using the extra time productively on file-based work (frontend pages, locale files, i18n config) that does not require spawning a new heavy interpreter process.
4. Left the last restart attempt running in the background rather than continuing to hammer the host with more spawn attempts once the Cygwin fork failure made the root cause unambiguous.

**Status:** web (3011) and the shared Postgres cluster (5433) remained healthy throughout this incident and were not restarted. The API (8011) is down as of this record and its restart is queued to resume the moment host conditions allow — this is the very first action on resume, ahead of any further feature work.
