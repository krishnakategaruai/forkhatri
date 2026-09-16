---
step: 07-tech-reqs
module: MOD01
status: Sealed
approver: Architect
updated: 2026-09-14
items: "55 | approved: 55 | blockers: 0"
---

# 07 — Technical Requirements — MOD01 Vyapar

## Revision history

| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-14 | Initial version. Looped over all 55 Sealed, impact-analyzed FRs (`06-impact-analysis.md`, IA001–IA055) one at a time per this agent's own loop discipline: re-read each FR/IA pair, `/ARCHITECTURE.md`'s Vyapar row (Core Platform monolith, `vyapar` schema, no dedicated container — ADR-002) and relevant ADRs (004 Identity, 006 Notification, 007/018 Search, 010 i18n, 011 Audit, 012 Admin Console, 013 VerifiedCredential, 014 API style, 019/020/021 Identity Bridge/entrance/no-second-account), `/MODULE-ARCHITECTURE-STANDARD.md`'s generic patterns (§2 component decomposition, §3 modular-monolith internals, §4/§4b/§4c schema-ownership/idempotency/rate-limiting, §5/§5b authorization chokepoint/Identity Bridge, §6 domain event bus), and the existing scaffold (`vyapar-web` Next.js 16 App Router, `vyapar-service` FastAPI/asyncpg, `db/schema.sql` draft, `db/seeds.sql`), before writing each item's technical requirement. Does **not** draft an ER diagram, schema DDL, or migration — that is Step 7a's exclusive scope, invoked only after this file Seals (per `docs/PIPELINE-STEP7-REFACTOR.md` and this agent's own definition). No `modules/MOD01-vyapar/architecture.md` exists yet — `06-impact-analysis.md`'s own closing note asked Step 7 to produce one, but this agent's definition is explicit that authoring that file is not this agent's role (it is Solution Architecture's/Step 7a's, per the Step 7 refactor's stated division of labor); instead, §"Component decomposition" below **decides and records** Vyapar's own component list (required to write internally-consistent tech reqs against real boundaries, not invented per-item) and explicitly flags it as a decision pending graduation into a formal `architecture.md` file by whichever agent that belongs to — this is a forward-pointer note, not a Step 7 blocker, consistent with `/MODULE-ARCHITECTURE-STANDARD.md` §1's own framing of when that file gets written. Reviewed the existing `db/schema.sql` draft against every FR while writing; five concrete, named gaps surfaced (below and in the closing note) rather than silently worked around. | Tech Requirements (Step 7) — autonomous execution per product owner direction 2026-09-14 ("never wait for me... complete this application developing as continuous chain"; Steps 5–8 run to completion, self-sealing, before Step 9). |
| 2026-09-14 | **Sealed.** Coverage verified 55/55 FR↔TR 1:1; quality-gate table below all Pass; open blockers: none (the five schema gaps and the architecture.md forward-pointer are named, owned items carried into the closing note for Step 7a, not blockers against this file). Step 7a (ER Model & Database Implementation) is cleared to begin against this Sealed file. | Approved — autonomous execution, 2026-09-14. |

## Coverage check

| Parent FR | Tech req items | Covered |
|---|---|---|
| FR01 | TR001 | Yes |
| FR02 | TR002 | Yes |
| FR03 | TR003 | Yes |
| FR04 | TR004 | Yes |
| FR05 | TR005 | Yes |
| FR06 | TR006 | Yes |
| FR07 | TR007 | Yes |
| FR08 | TR008 | Yes |
| FR09 | TR009 | Yes |
| FR10 | TR010 | Yes |
| FR11 | TR011 | Yes |
| FR12 | TR012 | Yes |
| FR13 | TR013 | Yes |
| FR14 | TR014 | Yes |
| FR15 | TR015 | Yes |
| FR16 | TR016 | Yes |
| FR17 | TR017 | Yes |
| FR18 | TR018 | Yes |
| FR19 | TR019 | Yes |
| FR20 | TR020 | Yes |
| FR21 | TR021 | Yes |
| FR22 | TR022 | Yes |
| FR23 | TR023 | Yes |
| FR24 | TR024 | Yes |
| FR25 | TR025 | Yes |
| FR26 | TR026 | Yes |
| FR27 | TR027 | Yes |
| FR28 | TR028 | Yes |
| FR29 | TR029 | Yes |
| FR30 | TR030 | Yes |
| FR31 | TR031 | Yes |
| FR32 | TR032 | Yes |
| FR33 | TR033 | Yes |
| FR34 | TR034 | Yes |
| FR35 | TR035 | Yes |
| FR36 | TR036 | Yes |
| FR37 | TR037 | Yes |
| FR38 | TR038 | Yes |
| FR39 | TR039 | Yes |
| FR40 | TR040 | Yes |
| FR41 | TR041 | Yes |
| FR42 | TR042 | Yes |
| FR43 | TR043 | Yes |
| FR44 | TR044 | Yes |
| FR45 | TR045 | Yes |
| FR46 | TR046 | Yes |
| FR47 | TR047 | Yes |
| FR48 | TR048 | Yes |
| FR49 | TR049 | Yes |
| FR50 | TR050 | Yes |
| FR51 | TR051 | Yes |
| FR52 | TR052 | Yes |
| FR53 | TR053 | Yes |
| FR54 | TR054 | Yes |
| FR55 | TR055 | Yes |

## Set-level quality gate

| Check | Result |
|---|---|
| Every FR has exactly one tech req | Pass — 55/55, TR001–TR055, 1:1 with FR01–FR55. |
| Every tech req traces to the FR it was written against and reflects its IA item | Pass — see each item's "Traces from" line; IA-surfaced findings (rate-limiting/idempotency/boost-reuse/Sponsored-label divergence risks; the architecture.md gap; the ER-Model-shaped anonymization decision) are carried into the relevant item's Constraints, not smoothed over. |
| No tech req invents a component, schema-ownership, or authorization pattern that `/MODULE-ARCHITECTURE-STANDARD.md` hasn't already fixed | Pass — every item names one of the 13 components decided below and, where it touches data, an existing or explicitly-flagged-as-missing table in `db/schema.sql`. |
| Rate-limiting is one shared utility, not one per abuse-prone endpoint | Pass — TR022 (enquiries), TR025 (partnerships), TR039 (reports) all call the one utility decided in "Cross-cutting technical decisions" §2, distinguishing rolling-window caps from standing-count caps rather than forcing both into one shape. |
| Idempotency is one shared mechanism, not one column per table | Pass — TR051 (payments) already has one; TR022/TR025/TR027/TR030/TR033/TR035/TR039 (client-queueable writes) are named in §1 below as needing the same shared `Idempotency-Key` mechanism, flagged as a schema gap for Step 7a rather than left implicit. |
| RLS pooling-safety requirement (non-owning DB role; `SET LOCAL`) stated, not assumed | Pass, with a named gap — §3 below states the requirement explicitly and records that the current `db/schema.sql` draft implements neither RLS nor schema-per-component separation yet; carried to Step 7a's closing note as the single most load-bearing gap in this file. |
| Explanation-signal, boost-mechanics, and Sponsored-label reuse (IA020/IA035/IA054's named divergence risks) resolved to one implementation each | Pass — TR020 reads TR019's own cached signal tuple; TR035 calls TR030's boost-application function per campaign item; TR030/TR054 both name one shared `<SponsoredBadge>` render path. |
| Every genuinely external-gated or schema-level dependency is named, not silently treated as resolved | Pass — payment gateway vendor selection (TR051), SMS/OTP provider template/route registration (TR007), public GST/Udyam lookup portals (TR008/TR047), and the five schema gaps (§ below) are each named with an explicit owner. |

## Open blockers

None. The five schema/DB-structural gaps this pass surfaced (idempotency-key table, rate-limit-counter table, RLS/schema-per-component separation, two missing FKs/columns, one missing history table) are named, owned items for Step 7a's ER Model pass — per this agent's own Definition of Done, that dependency does not gate this file's own seal, only Step 7a's start. The missing `modules/MOD01-vyapar/architecture.md` file is likewise a named forward-pointer, not a blocker against this step's own Tech-Reqs-only scope.

---

## Component decomposition (Vyapar) — decided here, recorded for graduation into `architecture.md`

No `modules/MOD01-vyapar/architecture.md` exists yet. Per this agent's own role definition, authoring that file is not this agent's job — but writing internally-consistent tech reqs requires *a* real, named set of component boundaries to write against, rather than 55 independently-invented ones. The list below is decided directly from the module's own source language: the FR set's Shared definitions and its own "Build-order note" already group the module as "profiles → discovery → opportunities → enquiries → trust → commercial → operations" (`02-functional-requirements.md`), and BR17/FR52 already name six adjacent-service contracts as one integration surface. Per `/MODULE-ARCHITECTURE-STANDARD.md` §2, this decomposition is built from that existing language, not re-derived independently — the fewest components capturing genuinely distinct technical responsibilities, not one component per BR.

**Placement recap (decided in `/ARCHITECTURE.md`, not here):** Vyapar is not a dedicated container — it is a business-logic module inside the Core Platform monolith (ADR-001/ADR-002), backed by one Postgres schema (`vyapar`) inside the Core Platform DB. `/MODULE-ARCHITECTURE-STANDARD.md` §3's "one process, modular internally" therefore applies with `vyapar-service` (FastAPI) as that one process, and §4's schema-per-component discipline applies *inside* that one module-level schema slot — a decision Step 7a must make concrete (see §3 below and the closing note).

| # | Component | Owns (schema/tables, once split per §3 below) | FRs |
|---|---|---|---|
| 1 | **Identity Bridge** (thin) | `members` (identity-link only) | FR44, FR50 |
| 2 | **Listings & Verification** | `listings`, `listing_contacts`, `otp_challenges`, `verification_records`, `taxonomy_terms` (shared reference, written here) | FR01–FR10, FR47 |
| 3 | **Opportunities** | `opportunities`, `member_opportunity` (write side) | FR11–FR14, FR48, FR55 (shared with ENQ/REV/SAFE for the composed read) |
| 4 | **Discovery & Ranking** | no owned tables — reads via LST/OPP/REV public interfaces only; owns the ranking/eligibility/explanation *logic* | FR15–FR21, FR38 (read side) |
| 5 | **Enquiries & Partnerships** | `enquiries`, `enquiry_messages`, `blocks`, `partnership_requests` | FR22–FR26 |
| 6 | **Reviews & Reputation** | `review_invites`, `reviews`, `review_disputes` | FR27–FR29 |
| 7 | **Commercial** | `products`, `promotions`, `promotion_history`, `entitlements`, `workspace_members`, `campaigns`, `impressions` | FR30–FR35, FR49, FR54 |
| 8 | **Payment Bridge** | `payment_orders` (the CCR13 swap seam — isolated on purpose from Commercial's business rules) | FR51 |
| 9 | **Privacy & Consent** | `privacy_settings`, `legal_documents`, `acceptances`, `data_requests`, `derived_preferences` (write side) | FR36–FR38, FR53 |
| 10 | **Trust & Safety** | `moderation_cases`, `reports`, `appeals` | FR39–FR41 |
| 11 | **Analytics** | `analytics_events` | FR45–FR46 |
| 12 | **Integration Bridges** (Search / Notification / Audit / Object Storage / Dashboard-Read / Counsel-Referral — six thin sub-bridges, grouped because none owns member-facing business logic) | `dead_letters`, `config`, `counsel_referrals` | FR52 (and the async side of FR02/03/13/21/23/40/48) |
| 13 | **Authorization Engine** | no owned tables — the chokepoint every other component's consequential methods call | FR05 (enforcement), FR19 (signal allow-list), FR34 (role split) |

Notes on fold-ins (recorded per §2's "no silent deviation" requirement):
- FR42 (i18n) and FR43 (accessibility) are **cross-cutting presentation concerns**, not components — they apply to every component's API responses/frontend screens and are addressed once in TR042/TR043 rather than as a 14th component.
- FR47/FR48/FR49 ("Admin Console" queues) are **not** a separate Admin Ops component — per ADR-012, the Admin Console is a platform-owned shared shell; Vyapar contributes federated *views* into each already-owning component's own data (LST for FR47, OPP for FR48, COM for FR49), never a fourteenth component that duplicates their schemas.
- The **Payment Bridge** is split out from **Commercial** even though both are "commercial," specifically because CCR13/FR51 DEC-001 name the gateway adapter as the deliberate future-MOD06 swap seam — merging it into Commercial would blur that seam.

**Forward pointer:** this table should graduate into `modules/MOD01-vyapar/architecture.md` (component diagram, traceability table, placement recap) per `/MODULE-ARCHITECTURE-STANDARD.md` §1, written by whichever role this project's pipeline assigns that file to (Solution Architecture / Step 0b's pattern, or folded into Step 7a's own output) — not by this agent. Nothing above should be treated as re-opened once that file exists; it should cite this table, not re-derive it.

## Cross-cutting technical decisions

**1. Idempotency (`/MODULE-ARCHITECTURE-STANDARD.md` §4b).** Every client-queueable mutation — `POST /v1/enquiries` (TR022), `POST /v1/partnership-requests` (TR025), `POST /v1/reviews` (TR027), `POST /v1/promotions|entitlements|campaigns` purchase (TR030/TR033/TR035), `POST /v1/reports` (TR039) — accepts a client-supplied `Idempotency-Key` header; on a repeated key, the API layer returns the original response rather than re-executing. `payment_orders.idempotency_key` and `notifications.idempotency_key` already exist as one-off columns in the draft schema; **gap 1**: there is no *shared* idempotency-key store for the other six endpoints above — Step 7a should add one shared `idempotency_keys(key TEXT PRIMARY KEY, endpoint TEXT, response_body JSONB, created_at)` table and one shared API-layer middleware, not six more one-off columns (mirrors Mangaly's TR102 canonical-middleware pattern).

**2. Rate limiting (§4c).** One shared utility, two modes, both legitimate and needed (not one forced into the other): (a) **rolling-window** caps — FR21 notifications (3/day), FR22 enquiries (20/day), FR39 reports (10/day) — backed by **gap 2**: a shared `rate_limit_counters(key TEXT, window_start TIMESTAMPTZ, count INT, PRIMARY KEY(key, window_start))` table Step 7a should add, checked via one `check_and_increment(key, window_seconds, limit)` function every rate-limited endpoint calls; (b) **standing-count** caps — FR25 partnership requests (10 pending at once) — a plain `COUNT(*) WHERE state='pending'` query against the owning table, which is the correct tool for a cap on concurrently-open records rather than a rolling window, and should not be forced through the same counter table.

**3. Row-Level Security and schema-per-component (§4) — the largest gap this pass found.** The current `db/schema.sql` draft creates **one flat `vyapar` schema** holding all 13 components' tables, with **no RLS policies, no non-owning application DB role, and no `SET LOCAL` session-context wiring** anywhere in the file. `/MODULE-ARCHITECTURE-STANDARD.md` §4 requires schema-per-component ownership *inside* Vyapar's one module-level schema slot (ADR-002 fixes the module-level granularity; §4 asks for a further split inside it) plus RLS as a second, database-enforced layer for sensitive data (listings, opportunities, enquiries, partnership_requests, reviews, verification_records, privacy_settings, data_requests, workspace_members). **Gap 3, named explicitly for Step 7a**: decide and implement (a) either genuine per-component Postgres schemas (`vyapar_listings`, `vyapar_opportunities`, …, mirroring Mangaly's `mangaly_profile`/`mangaly_home_circle` naming) or one physical schema with strictly enforced per-table application-layer ownership (both are §4-compliant; the draft has chosen neither, explicitly); (b) RLS policies on every sensitive table above, keyed on a `vyapar.authz_context` session variable that the Authorization Engine (component 13) sets via **`SET LOCAL`** (never plain `SET`, per §4's named connection-pooling failure mode) once the Identity Bridge (TR050) resolves the caller; (c) confirmation that `vyapar-service`'s runtime DB connection role is a **non-owning** role distinct from the migration/owner role the RLS policies are applied to (§4's other named failure mode — RLS is silently bypassed for a table's owning role by default).

**4. Dead-letter handling.** One shared `publish_with_outbox(event)` helper (transactional outbox — publish in the same DB transaction as the state change that caused it, per §6) used by every domain event in this file (TR002, TR003, TR013, TR030, TR048, and the rest of §"Integration Bridges" traffic in TR052); exhausted retries land in the already-modeled `dead_letters` table, surfaced to operators at `GET /v1/admin/dead-letters` (feeds FR49/TR049's queue). One implementation, not one per integration point.

**5. Authorization chokepoint (§5).** The Authorization Engine component's public methods take an already-resolved `AuthzContext` (member id + role/permission set + entitlement state), never a raw member id — every other component's consequential read/write calls it first (TR005, TR019, TR034, TR047 name this explicitly; it applies uniformly).

**6. Scheduled jobs required.** Distinct background workers this FR set requires, none of which exists as code yet (`vyapar-service/app/` has no code written): credential hourly re-sync (TR006); verification 11-month reminder / 12-month expiry (TR010); opportunity draft day-5 reminder / day-7 archive (TR012); opportunity day-14 reminder / day-21 stale / deadline-or-day-45 expiry (TR013); strong-match notification + daily digest batching (TR021); enquiry 7-day no-response marker (TR023); PAN/credential-image 30-day deletion (TR008); data-export within 72h (TR037); entitlement renewal-reminder day-3 gate (TR054); taxonomy-change search reindex within 5 minutes (TR048); dead-letter retry backoff (§4 above).

## External integrations

- **Payment gateway** (TR051) — a licensed India gateway (Razorpay/Cashfree-class per the grounded CCR03 research), hosted/tokenized checkout, signed webhooks; vendor selection is a Step 9 procurement choice, isolated behind the `PaymentGateway` interface so the choice is swappable.
- **SMS/OTP provider** (TR007) — the platform's own shared, already-existing OTP-sending capability (ADR-006), reused **only** for listing-contact verification, never for authentication; DLT template/route registration is an operational task named by CCR04, not assumed solved.
- **Object Storage/CDN** (TR008, TR009, TR011, TR022, TR037, TR039) — verification documents, opportunity screenshots, enquiry attachments, review-dispute evidence; masked-display + 30-day auto-delete for identity documents is a compliance control (CCR07), not cosmetic.
- **Public GST/Udyam lookup portals** (TR008, TR047) — manual operator reference links only, no API integration in V1, per BR03 DEC-001.
- **Search** — embedded Postgres full-text search (`search_tsv` GIN indexes already in the draft schema) per ADR-007/018, not an external service call, at Vyapar's V1 volume.

---

## TR001 — BusinessProfile/ProfessionalListingProfile create-and-edit endpoint
**Traces from:** FR01
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /v1/listings` and `PATCH /v1/listings/{id}` (Listings & Verification) against the `listings` table. Server-side validation of the mandatory three fields (name, ≥1 category, locality) blocks submission with field-level errors — never client-only validation. The draft schema's `UNIQUE (owner_id, name, locality)` constraint enforces the duplicate rule directly; on conflict, the API returns the existing listing's id so the client can offer "edit existing" rather than a bare error. Free-text capability/category input that maps to no `taxonomy_terms` row is stored in `unmapped_labels[]`, remaining text-searchable via the same GIN index.

**Constraints surfaced**
None beyond the taxonomy free-text fallback (CCR10), already covered by the sibling FR04's own acceptance criteria.

**Assumptions** — `taxonomy_terms` is the platform-shared reference list, editable via TR048.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR002 — Per-channel contact disclosure and discoverability toggle
**Traces from:** FR02
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`PATCH /v1/listings/{id}/contacts` (per-channel `disclosure` on `listing_contacts`) and `PATCH /v1/listings/{id}/visibility` (`listings.discoverable`). Either write publishes a domain event in the same DB transaction (transactional outbox, per Cross-cutting §4) consumed by the Search Bridge (index update/removal) and the Dashboard Read Bridge (MOD05 summary cache invalidation) — the 5-second bound is this event-consumption SLA, not a synchronous call. A GET on the listing detail, search result, or MOD05 summary must all resolve disclosure through the same one read function (never three independently-coded checks) so a channel cannot appear on one surface after being hidden on another.

**Constraints surfaced**
The 5-second propagation bound against an eventually-consistent index (CCR02) is a genuine latency target to load-test at Step 8, not assumed free.

**Assumptions** — default is Public discovery, contact After accepted enquiry (FR02's own stated default), applied at listing creation (TR001).
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR003 — Listing lifecycle state machine with safety gate
**Traces from:** FR03
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /v1/listings/{id}/submit|suspend|archive` (Listings & Verification) enforcing the `listings.state` CHECK constraint server-side; illegal transitions rejected with a typed error, never silently ignored. Submit requires `contact_verified = true` (TR007's gate) and passes a config-driven wordlist/spam check (read from the shared `config` table) before auto-activating to `active_unverified`; a failing check instead creates a `moderation_cases` row (`source='auto_flag'`) and leaves the listing at `submitted`, visible only to its owner. Suspend/Archive publish the same TR002 domain event (Search Bridge removal within 5s) and cascade-close open `enquiries` for that listing with a system note to each enquirer.

**Constraints surfaced**
Wordlist/spam-pattern quality is an ongoing tuning exercise (CCR12), not a one-time build task — flag for Step 13 monitoring, not a Step 10 pass/fail test alone.

**Assumptions** — the same state machine and gate apply to `kind='professional'` listings (FR03 is shared across BR01/BR02).
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR004 — ProfessionalListingProfile progressive three-step setup
**Traces from:** FR04
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Same `POST/PATCH /v1/listings` family (Listings & Verification), `kind='professional'`. The three required steps (capability, where/how, contact preference) are enforced as three separate, individually-saveable `PATCH` calls; every other field (experience, languages, availability, evidence links, rates) is optional and independently patchable. Unmapped capability free text goes to `unmapped_labels[]`, queued for TR048's taxonomy review, and remains immediately text-searchable — never blocked pending review.

**Constraints surfaced**
**Gap:** `db/schema.sql`'s `listings` table has no column tracking which of the three required steps is complete (only `members.first_run_step` exists, which is a different, member-level concept from FR44). Step 7a should add a `listings.setup_step SMALLINT` (or equivalent) so "reach Discover before completing optional fields" is a server-verifiable state, not inferred client-side.

**Assumptions** — a member may hold both a BusinessProfile and a ProfessionalListingProfile (two `listings` rows, different `kind`, same `owner_id`).
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR005 — Capability visibility independent of seeking-status visibility
**Traces from:** FR05
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`listings.intent_state`/`intent_visible`/`capability_visible` (already modeled) are two independently-settable booleans. Listings & Verification's own public read method is the **sole** place that decides whether to include `intent_state` in a response — it returns it only when `intent_visible = true`. Discovery & Ranking's signal extraction (TR019) calls this exact read method rather than querying `listings.intent_state` directly, structurally preventing the private-intent leak IA005 names as the module's highest-severity risk in this area (an import-boundary enforcement, not a documented convention).

**Constraints surfaced**
This is the module's most safety-load-bearing tech req (cross-cutting rule 6) — Step 8's STRIDE pass should treat any future code path that queries `listings.intent_state` outside this one function as a defect, not a style nit.

**Assumptions** — none beyond FR05's own text.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR006 — VerifiedCredential read-only reference with hourly re-sync
**Traces from:** FR06
**Status:** Ready for Review | **Confidence:** Medium — depends on the Identity & Trust read contract, matching the FR's own stated confidence. | **Priority:** Should

**Technical requirement**
`listings.credential_ref JSONB` (already modeled: `{id, claim, issuer, verified_at, last_checked}`) is populated and refreshed by a scheduled job (Cross-cutting §6) calling Identity & Trust's VerifiedCredential read contract (ADR-013) hourly for every listing with a non-null reference. On read, if `last_checked` is stale (Identity & Trust unreachable), the listing detail shows the cached value with its `last_checked` timestamp and no error surfaced to the viewer. Revocation upstream removes the reference (sets `credential_ref = NULL`) within the same 1-hour sync cycle.

**Constraints surfaced**
No MOD04 Counsel `ExpertProfile` field exists anywhere in this reference or its storage — enforced by the field list itself (`{id, claim, issuer, verified_at, last_checked}` has no room for one), not merely by convention.

**Assumptions** — Identity & Trust's VerifiedCredential contract is stable at the version this reads.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR007 — Listing-contact OTP verification (not authentication)
**Traces from:** FR07
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /v1/listings/{id}/otp/request` and `POST /v1/listings/{id}/otp/verify` (Listings & Verification) against the already-modeled `otp_challenges` table (`attempts`, `expires_at` at 10 minutes, `resend_after` at 30 seconds, `locked_until` at 5 failed attempts for 15 minutes). This reuses the platform's shared SMS-sending capability (Integration Bridges) — explicitly **not** a call to Identity & Trust — and creates no session, cookie, or credential of any kind. On success, sets `listings.contact_verified = true`. A change to `listings.primary_phone` must reset `contact_verified` to `false`.

**Constraints surfaced**
**Gap:** no trigger or application-level check in the draft schema currently fires on a `primary_phone` change to reset `contact_verified` — Step 7a should add either a DB trigger or the application layer must enforce this explicitly in the `PATCH /v1/listings/{id}` handler; naming it here so it isn't silently missed. Separately, CCR04's grounded finding (DLT template/route mismatch causes silent OTP delivery failure even on compliant routes) means the 5-attempt/15-minute-lockout design is a necessary accommodation, not over-engineering — template/route registration itself is a Step 9 operational task.

**Assumptions** — none beyond FR07's own text.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR008 — Business-existence document verification with masked storage
**Traces from:** FR08
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /v1/listings/{id}/verification` (Listings & Verification, `verification_records` table, `kind='business'`) accepts exactly one of {GST, Udyam, PAN, Shops & Establishment}, format-validates the identifier server-side where a format exists (GSTIN 15 chars, PAN 10 chars, Udyam pattern) before insert, stores the identifier encrypted (`identifier_enc`) with a masked display copy (`identifier_masked`, last 4 only), and routes the image upload through the Object Storage Bridge's pre-signed-URL flow. `image_delete_after` is set to `decided_at + 30 days` and enforced by the scheduled deletion job named in Cross-cutting §6. Aadhaar is never offered as a document type — enforced by the CHECK constraint's fixed value list, structurally, not by a UI omission alone.

**Constraints surfaced**
The masked-storage/30-day-deletion control is a compliance mechanism (CCR07) that must not silently fail — Step 8/10 should include an explicit automated check that the deletion job actually runs and actually deletes, not just that the column exists.

**Assumptions** — PAN is visually reviewed only in V1 (no government-database check), per BR03; public GST/Udyam lookup is manual (BR03 DEC-001).
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR009 — Professional-credential document review with re-upload path
**Traces from:** FR09
**Status:** Ready for Review | **Confidence:** High | **Priority:** Should

**Technical requirement**
Same endpoint family as TR008, `kind='credential'`, capturing `credential_name`/`issuer`. The `verification_records.state` CHECK already includes `needs_clearer_copy` as a distinct, non-penalizing re-upload state (not a rejection) — the operator decision endpoint must be able to set this state without affecting the listing's other verification history.

**Constraints surfaced** — none beyond TR008's shared Object Storage/masking concerns, at lower sensitivity (a credential image, not an identity document).
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR010 — Verification state display, expiry, and single revert call site
**Traces from:** FR10
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Listing detail reads compute `verification_state` from `verification_records`' latest decision plus `listings.verified_at`/`verification_expires_at` — one function, used by every rendering surface (search, detail, feed, MOD05 summary) so the label cannot drift between surfaces (IA010's named risk). A scheduled job (Cross-cutting §6) sends the 11-month reconfirmation reminder via the Notification Bridge and flips `verification_state` to `expired` at 12 months if unconfirmed. Trust & Safety's report/dispute pipeline (TR039/TR040) and any operator revocation call Listings & Verification's own `revoke_verification(listing_id, reason)` interface method — never a direct `UPDATE` on `verification_records`/`listings` from another component — so the 5-second revert bound has exactly one call site to guarantee, not several independently-written ones.

**Constraints surfaced**
A missed reconfirmation-reminder notification must not extend expiry (FR10's own stated rule) — the expiry job's day-12 check reads `verified_at` directly, never a "reminder was sent" flag, so a Notification Bridge failure cannot silently grant extra time.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR011 — Opportunity Composer: create, share, or upload
**Traces from:** FR11
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /v1/opportunities` (Opportunities), `entry_mode IN ('create','share','upload')`, `source_segment` mandatory (`community`|`public`, with `source_name`/`source_url` required when `public`). Screenshot upload (`upload` mode) routes through the Object Storage Bridge (≤5MB, inline error otherwise). "Share a pasted URL" triggers an **asynchronous** background fetch (Cross-cutting §6's job list) that never blocks the initial Draft save — on fetch failure, `source_unreachable` is set for later review (TR048), not surfaced as an error to the submitter.

**Constraints surfaced**
The explicit non-dependency on MOD05's autonomous public-source ingestion pipeline (IA011) is preserved structurally: this endpoint is member-initiated only, with no code path that could be triggered by an external crawl — a design-review discipline to re-confirm at each future feature addition, not a one-time test.

**Assumptions** — none beyond FR11's own text.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR012 — Structured-field confirmation with uncertainty marking
**Traces from:** FR12
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`PATCH /v1/opportunities/{id}/confirm` (Opportunities), operating on the already-modeled `unconfirmed_fields[]`/`confirmed_fields[]` arrays. Rule-based field extraction runs synchronously at create time for `share`/`upload` modes (never an AI hot-path dependency, per FR12's own stated assumption); publish is blocked server-side until `title`, `type`, `location`, `response_method` are all present in `confirmed_fields`. The day-5 reminder / day-7 auto-archive for unconfirmed Drafts is one scheduled job (Cross-cutting §6), not client-side logic.

**Constraints surfaced** — none beyond the extraction-quality caveat already named in IA012 (a graceful-degradation design, not a defect).
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR013 — Opportunity freshness lifecycle
**Traces from:** FR13
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
One scheduled job (Cross-cutting §6) evaluates every `active` opportunity daily: day-14 reminder (from `last_confirmed_at`), day-21 → `stale`, deadline-or-day-45 → `expired`. Every state transition publishes the same TR002 domain-event pattern (transactional outbox) consumed by the Search Bridge for index removal within 5 seconds. Renewal (`Pause`/`Resume`/`Close`/`Renew`) resets `last_confirmed_at`; renewing a record `expired` for >90 days re-requires TR012's material-field confirmation rather than a bare state flip.

**Constraints surfaced**
Scheduled-job correctness (off-by-one/timezone bugs) is named by IA013 as the real risk here, not the state-machine logic itself — Step 10 should include a dedicated timezone/boundary test for the day-14/21/45 job, not only a state-transition unit test.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR014 — Opportunity types with V1 launch focus
**Traces from:** FR14
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`opportunities.type` CHECK (already modeled: employment/freelance/local_service/partnership/training/community). The three V1-promoted types render first in the type picker and are the only types eligible for FR18's proactive-notification path (TR021 explicitly excludes `training`/`community`/`partnership` from that path). A server-side `PATCH` guard re-validates type-specific mandatory fields (compensation for employment; scope+budget for freelance; service window for local_service) whenever `type` changes after publish, rejecting the save otherwise.

**Constraints surfaced** — none.
**Assumptions** — launch-geography (Hyderabad/Secunderabad) is a `config` table value, not a code constant.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR015 — Standalone Listing search and browse
**Traces from:** FR15
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`GET /v1/listings/search` (Discovery & Ranking) against `listings.search_tsv` (GIN index, already modeled) with keyword/category/locality-radius/service_mode/availability/verification_state/freshness filters, ranked by TR019's shared scoring function. A completely separate endpoint/surface from `GET /v1/opportunities/feed` (TR018) — this must work correctly with zero Opportunities in the system, per FR15 DEC-001's explicit standalone-discovery scope. Falls back to cached category-browse with a "search temporarily unavailable" notice if the Postgres FTS query path degrades (CCR02); at V1's embedded-Postgres-search scale (ADR-007/018), this fallback path is a DB-health check, not a separate service-outage handler.

**Constraints surfaced**
The 2-second/first-20-results bound and organic-vs-Sponsored ordering (TR030's shared badge, never reordering) are both direct, load-testable acceptance criteria for Step 8.

**Assumptions** — none beyond FR15's own text.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR016 — Listing detail view (composed read)
**Traces from:** FR16
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`GET /v1/listings/{id}` (Listings & Verification) is a pure composing read over TR002's disclosure function, TR010's verification-state function, and TR028's reputation-count function, plus TR022's enquiry-eligibility check for the primary action — it computes no independent business logic of its own, avoiding the cross-surface drift IA016 names as the real risk of a five-contract composed screen. A Suspended/Archived listing opened via a stale link returns a "no longer available" response with no underlying data.

**Constraints surfaced** — none beyond the composed-read discipline itself.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR017 — Zero-result explicit broadening
**Traces from:** FR17
**Status:** Ready for Review | **Confidence:** High | **Priority:** Should

**Technical requirement**
`GET /v1/listings/search` and `GET /v1/opportunities/search` both return a `broadening_options[]` array (radius step 5→10→25km, adjacent categories, remove-one-filter, include-unverified) on a zero-result response — an explicit, user-selectable response field, never a silently-relaxed query. A second zero-result response additionally includes `fallback: {post_link, notify_link}` pointing to TR011 (Post) and TR021 (Notify me).

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR018 — Opportunity Discover feed, five sections
**Traces from:** FR18
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`GET /v1/opportunities/feed` (Discovery & Ranking) computes For You / Explore / Near You / Community / Public as five separate queries, each running TR019's shared eligibility-then-ranking function against a different candidate pool — never a single ranked list re-sliced client-side, since eligibility must be enforced identically in every section. Empty sections are omitted **server-side** (not sent then hidden client-side). A sparse-profile member (no capability data) receives Near You + Community + Public plus one enrichment prompt (TR004) instead of an empty For You.

**Constraints surfaced**
Five sections multiply the surfaces a ranking-eligibility bug can reach at once (IA018) — Step 10 should assert "every card in every section passes TR019's hard-filter step" as one shared contract test across all five, not five independent ones.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR019 — Canonical eligibility-then-ranking function with signal allow-list
**Traces from:** FR19
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
One function, `rank_opportunities(member_ctx, candidates) -> [(item, score, signals)]`, inside Discovery & Ranking's own interface module — the **only** implementation every ranked-list endpoint (TR015, TR017, TR018, TR020, TR055) calls; none reimplements eligibility or scoring independently. Hard-constraint exclusion (non-Active state, member exclusions/blocks, radius when on-site, eligibility mismatch, safety restrictions) runs as a repository-layer filter **before** scoring — excluded records never reach the weighted-sum step, so a hard constraint can never degrade to a soft penalty. The scoring inputs are a typed `RankingSignals` struct whose fields are exactly the FR19 allow-list (capability/intent/location/timing/value/experience/freshness/trust fit) — this is a **structural absence**: no field for sensitive attributes, community status, account age, paid status, popularity, or report signals exists on the struct at all, so no future change can pass one in without first changing this one type. Weights read from `config`; missing configuration logs a warning and falls back to safe defaults (never blocks the request). Final pass applies diversification (≤3 consecutive results sharing a provider or type).

**Constraints surfaced**
This is the module's single most explicit anti-bias control (cross-cutting rules 4/5/7) — Step 8's STRIDE pass should specifically threat-model "a future PR adds a field to `RankingSignals`" as the concrete attack/regression scenario this structural-absence design defends against.

**Assumptions** — deterministic, explainable scoring over ML-first ranking (FR19 DEC-001) is correct for V1's sparse data.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR020 — "Why this?" explanation reads the same signals that ranked
**Traces from:** FR20
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`GET /v1/opportunities/{id}/why` reads the exact `signals` tuple TR019's ranking call already computed for that member/item pair — it is never a separately-computed "reason string" model, closing the explanation-drift risk IA020 names by construction rather than by later contract-test discipline alone. Renders the top three by weight in plain language plus any material gap; falls back to "matched your search" when fewer than one signal applies (a search-only result). A Sponsored item additionally appends "shown to more people because the provider paid for reach," sourced from an active `promotions` row for that target — never a percentage match score anywhere in the response.

**Constraints surfaced** — none beyond the anti-drift design itself.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR021 — Proactive notification with fatigue caps and daily digest
**Traces from:** FR21
**Status:** Ready for Review | **Confidence:** High | **Priority:** Should

**Technical requirement**
A scheduled job (Cross-cutting §6) evaluates newly-`active` opportunities against the `config`-driven "strong match" threshold, per member with `privacy_settings.notifications_enabled = true`, excluding `training`/`community`/`partnership` types (TR014). Before requesting a send, it calls the shared rate-limit utility (Cross-cutting §2, key = `member_id:day`, limit = 3); non-strong matches are batched into one digest job keyed on `privacy_settings.digest_hour`. Both paths request delivery through the Notification Bridge (Integration Bridges), which itself retries up to 3 times then drops — never duplicates, per its own idempotency contract (TR052).

**Constraints surfaced** — none beyond the shared rate-limit utility already named in Cross-cutting §2.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR022 — Submit an Enquiry or Opportunity Response
**Traces from:** FR22
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /v1/enquiries` (Enquiries & Partnerships) against the `enquiries` table. `action_type` is derived **server-side** from the target's type per FR22 DEC-002's mapping (Listing→`enquire`, Employment→`apply`, Freelance/Project→`propose`, Business partnership→`contact`, Training/Community→`register`) — never accepted as client input. Message length (20–1000 chars) and attachment size (≤5MB via Object Storage Bridge) are validated server-side. Honors the `Idempotency-Key` mechanism (Cross-cutting §1) and calls the shared rate-limit utility (key = `sender_id:day`, limit = 20). Blocked-sender handling: a `blocks` row between the pair causes the write to succeed (`state='open'`) with `delivered=false` internally and no disclosure to the sender.

**Constraints surfaced**
**Gap:** the draft schema has no partial unique index enforcing "1 open enquiry per target" — Step 7a should add `CREATE UNIQUE INDEX ON enquiries (sender_id, COALESCE(listing_id, opportunity_id)) WHERE state NOT IN ('resolved','closed','withdrawn')` (or equivalent), so this is a database-enforced invariant, not only an application-layer check that a race condition could bypass.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR023 — Enquiry lifecycle and Refer-to-Counsel
**Traces from:** FR23
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`PATCH /v1/enquiries/{id}/reply|resolve|close|withdraw|restrict` (Enquiries & Partnerships), state machine over `enquiries.state`; a `restricted` thread rejects every further state-change or message call at the API layer, not just the UI. `POST /v1/enquiries/{id}/refer-to-counsel` writes to `counsel_referrals` (already modeled) with exactly the FR52(f) minimal payload (`member_id`, `problem_summary`, `consent`) via the Integration Bridges' Counsel Referral Bridge — no other field, and it changes nothing else on the thread. A scheduled job (Cross-cutting §6) marks a 7-day-no-reply enquiry with `state_reason='no_response_yet'` (never changing `state` itself), feeding TR028's `response_minutes` signal.

**Constraints surfaced** — none beyond the minimal-payload boundary already fixed by FR52(f).
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR024 — Consent-based contact disclosure, blocking, safety notice
**Traces from:** FR24
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`GET /v1/enquiries/{id}` computes contact-channel visibility by calling TR002's own disclosure function — never a second, independently-coded check — returning a channel only when its `listing_contacts.disclosure = 'after_accept'` (or `public`) **and** `enquiries.state = 'in_progress'`. A one-line safety notice is shown once per thread, tracked via `enquiries.safety_notice_seen`. `POST /v1/blocks` inserts into `blocks` and, in the same transaction, sets `state='restricted'` on every existing `enquiries`/`partnership_requests` row between the pair — ending the thread and preventing new enquiries both ways going forward (enforced by TR022's blocked-sender check reading the same `blocks` table).

**Constraints surfaced**
No endpoint anywhere in this file exposes a bulk/export view of enquirer contact details to any role — a direct, structural response to the "no lead lists" invariant (BR07/BR10), verified by the absence of such a route rather than a permission check on one that exists.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR025 — Create a Partnership Request
**Traces from:** FR25
**Status:** Ready for Review | **Confidence:** High | **Priority:** Should

**Technical requirement**
`POST /v1/partnership-requests` (Enquiries & Partnerships) requires both `sender_listing_id` and `recipient_listing_id` to pass Listings & Verification's own `is_active(listing_id)` public method (never a direct query against `listings.state` from this component). The 10-pending cap is a **standing-count** check (Cross-cutting §2(b)): `COUNT(*) FROM partnership_requests WHERE sender_id = ? AND state = 'pending'`, not the rolling-window rate-limit utility. Honors `Idempotency-Key` (Cross-cutting §1).

**Constraints surfaced** — none beyond the count-vs-window distinction already recorded in Cross-cutting §2.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR026 — Respond to and manage a Partnership Request
**Traces from:** FR26
**Status:** Ready for Review | **Confidence:** High | **Priority:** Should

**Technical requirement**
`PATCH /v1/partnership-requests/{id}/accept|decline|withdraw|restrict|close` (Enquiries & Partnerships), state machine over `partnership_requests.state`. Accept discloses contact via the same TR024 disclosure function (never a second implementation). The 30-day re-send cooldown after Decline is enforced by checking the most recent `declined` request's timestamp between the same (sender, recipient) pair before allowing a new `POST /v1/partnership-requests`.

**Constraints surfaced** — none.
**Assumptions** — Pending requests never auto-expire, per FR26's own explicit, PM-approved policy.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR027 — Submit a Review tied to a qualifying interaction
**Traces from:** FR27
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /v1/reviews` (Reviews & Reputation) is rejected unless an unused, unexpired `review_invites` row exists for that `(interaction_kind, interaction_id, member_id)` — the qualifying-interaction rule is thus enforced by a foreign-row existence check, not a business-logic flag that could drift out of sync with the invite table. `reviews`' `UNIQUE (interaction_kind, interaction_id, author_id)` constraint enforces one review per party per interaction at the database level. Trust & Safety's automated safety check (reusing TR003's wordlist function, never a second copy) runs synchronously before insert. Honors `Idempotency-Key` (Cross-cutting §1).

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR028 — Contextual reputation counts, no aggregate score
**Traces from:** FR28
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Listing/professional detail reads compute reputation counts (`N verified interactions`, `N of M recommend`, top tags, `response_minutes`) via one query over `reviews WHERE state='published'` grouped by subject — never a stored/cached aggregate score column that could drift stale. "New on Vyapar" renders below 3 interactions with explicitly no negative ranking treatment; TR019's ranking function reads these same counts (never a separately-computed trust number) and only above the 3-interaction threshold. `review_disputes`/hidden/removed reviews are excluded from the count query's `WHERE` clause directly, so exclusion is immediate rather than a delayed batch recompute.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR029 — Review dispute, hide, and removal via Trust & Safety only
**Traces from:** FR29
**Status:** Ready for Review | **Confidence:** High | **Priority:** Should

**Technical requirement**
`POST /v1/reviews/{id}/dispute` (Reviews & Reputation) inserts into `review_disputes` (`UNIQUE(review_id)` already enforces one dispute per review) and sets `reviews.state='disputed'`. The actual Published/Hidden/Removed decision is made **only** through Trust & Safety's moderation interface (TR040) writing back `reviews.state` — Reviews & Reputation's own public interface exposes no method that lets a provider (the review's subject) alter or hide a review through any path, which is how "no provider-side edit/hide capability" is verified structurally (by the absence of such a method), not just by a role check that a bug could bypass.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR030 — Purchase a Boost, shared Sponsored-label rendering
**Traces from:** FR30
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /v1/promotions` (Commercial) creates a `promotions` row (`draft`→`awaiting_payment`), gated on the target's `verification_state='verified'` (Listings) or its poster's listing being verified (Opportunities) — checked via Listings & Verification's own interface, never a direct query. On the Payment Bridge's webhook success (TR051), Commercial's own state-transition function (not the webhook handler itself) moves the row to `scheduled`/`active`. **One** shared `<SponsoredBadge>` render function/component is used by every surface that can show a boosted card (search TR015, feed TR018, detail TR016) — this directly closes IA054's named risk of the label being reimplemented per surface and, on any one surface, forgotten.

**Constraints surfaced**
Organic rank must never change as a side effect of this endpoint — TR019's ranking function takes no `promotions`/paid-status field as an input (already structurally enforced by TR019's `RankingSignals` type), so Sponsored inclusion is an *audience-eligible impression boost*, never a rank boost.

**Assumptions** — prices/products are `config`-driven, versioned per TR031.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR031 — Promotion/Entitlement lifecycle, price versioning, credit
**Traces from:** FR31
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
State machine over `promotions.state`/`entitlements.state` (Commercial); product/price version stored via the `FOREIGN KEY (product_id, product_version) REFERENCES products(id, version)` already modeled on both tables, so every order is reconstructible against the exact price in force at purchase. Cancellation before activation calls the Payment Bridge (TR051) for a full refund; cancellation during activity computes a pro-rata credit into `credit_paise`. Operator Reject (safety) auto-triggers the same refund path with a reason.

**Constraints surfaced**
**Gap:** `promotion_history` exists but there is no equivalent `entitlement_history` (or one shared, kind-agnostic history table) — since FR31's own text explicitly covers "a Promotion **or** Entitlement," Step 7a should generalize one history table (e.g. `commercial_order_history(order_kind, order_id, from_state, to_state, reason, at)`) rather than leave Entitlements without an owner-visible state history.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR032 — Provider performance reporting without unsupported claims
**Traces from:** FR32
**Status:** Ready for Review | **Confidence:** High | **Priority:** Should

**Technical requirement**
`GET /v1/promotions/{id}/report` (Commercial + Analytics) reads `impressions` (already modeled, deliberately kept separate from `analytics_events` per the draft schema's own comment) plus TR023/TR027's confirmed-outcome counts, split boosted-vs-organic by date. The response schema has no field for a projection, ROI figure, or causal statement — a response-shape guarantee, not a copy-review rule alone — and substitutes `"too little data to compare"` when the period's impression count is below 10. No individual member identity appears anywhere in the payload (aggregate counts only).

**Constraints surfaced**
The no-projection/no-causal-claim rule needs an explicit product-review gate on every *future* reporting feature (IA032's own finding) — naming this here so a later "show projected reach" feature request is caught at design review, not shipped by default.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR033 — Business Workspace entitlement purchase and renewal grace
**Traces from:** FR33
**Status:** Ready for Review | **Confidence:** Medium — matches the FR's own stated confidence (unproven willingness to pay). | **Priority:** Should

**Technical requirement**
`POST /v1/entitlements` (Commercial), same payment flow as TR030/TR051. `entitlements.grace_until` (already modeled) implements the 7-day renewal-failure grace period with notices before `state` moves to `paused` (capabilities locked, all data retained — no delete). The Authorization Engine is the **single** chokepoint that gates FR34/FR35/FR32-via-Workspace capability access by reading `entitlements.state='active'` — no individual gated feature (multi-user roles, campaigns, provider analytics) checks entitlement state independently, closing the same "pay cannot buy verification/ranking" guarantee class as TR030 for a subscription rather than a per-boost purchase.

**Constraints surfaced** — none beyond the already-named willingness-to-pay business risk (not a system risk).
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR034 — Multi-user Workspace roles via the Authorization Engine
**Traces from:** FR34
**Status:** Ready for Review | **Confidence:** High | **Priority:** Should

**Technical requirement**
`POST /v1/workspace/{listing_id}/invite` (Commercial, `workspace_members`, invite-by-phone resolving to a `member_id` via Identity Bridge's phone-lookup call). The Admin/Operator permission split is enforced by the Authorization Engine on every Vyapar action a workspace member takes — not independently re-checked by each of Commercial's own endpoints. Revocation (`state='revoked'`) is effective immediately because every request re-resolves the Authorization Engine's context fresh from `workspace_members.state`; there is no per-request cache to invalidate at V1 scale (same reasoning as Mangaly's TR010). Revoking a Vyapar role never touches the member's platform session (FR34's own explicit clarification, consistent with FR50 DEC-001) — the two are structurally unrelated tables (`workspace_members` vs. the platform's own session store, which Vyapar never touches).

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR035 — Campaign creation reusing Boost mechanics per item
**Traces from:** FR35
**Status:** Ready for Review | **Confidence:** Medium — matches the FR's own stated confidence. | **Priority:** Should

**Technical requirement**
`POST /v1/campaigns` (Commercial, `campaigns.item_refs`, ≤10 items) **must call TR030's own boost-application function once per item** — this tech req is the literal fix for IA035's named divergence risk (a campaign-specific reimplementation silently not enforcing TR030's verified-only/organic-rank-unchanged guarantees). Reporting is TR032's own function called at campaign scope (grouped by `campaign_id`), not a separate report implementation.

**Constraints surfaced**
**Gap:** `promotions.campaign_id` is an unconstrained `UUID` column with no `FOREIGN KEY` to `campaigns.id` — Step 7a should add `FOREIGN KEY (campaign_id) REFERENCES campaigns(id)` so an item cannot reference a non-existent or wrong-owner campaign.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR036 — Six contextual privacy controls, one screen
**Traces from:** FR36
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`GET/PATCH /v1/privacy` (Privacy & Consent) exposes exactly the six controls already modeled on `privacy_settings`, whose defaults (`contact_disclosure='after_accept'`, `seeking_visible=false`, `commercial_comms=false`, others as modeled) are set once at first-run (TR044) creation of the row — never computed from any other module's data (`privacy_settings.prompted[]` tracks which contextual first-set explainer was already shown, so it is shown once, not on every visit).

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR037 — Data export, correction, deletion, consent withdrawal
**Traces from:** FR37
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /v1/privacy/export|delete|withdraw-consent` (Privacy & Consent) against `data_requests` (already modeled with `due_at`/`retained_categories`). The export job (Cross-cutting §6) completes within 72 hours. Deletion **anonymizes** the requesting member's own `enquiries.sender_id`/`reviews.author_id`/etc. to a tombstone identity rather than cascading a hard delete that would corrupt a counterpart's thread or review — IA037 correctly names this as an ER-Model-shaped decision, not an FR-level detail; **this tech req fixes the behavior contract only** (anonymize the requester, never cascade-delete a counterpart's record) and hands the concrete tombstone schema design to Step 7a explicitly. Deletion while a paid `promotions`/`entitlements` row is active is deferred until that order closes or cancels (TR031), per FR37's own stated rule.

**Constraints surfaced**
Anonymization-vs-deletion correctness on shared records is a genuinely tricky data operation (IA037) — named here as Step 7a's responsibility, not smoothed over as "already handled."

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR038 — Inspect and confirm derived preferences
**Traces from:** FR38
**Status:** Ready for Review | **Confidence:** High | **Priority:** Should

**Technical requirement**
`derived_preferences` (already modeled) with `POST /v1/preferences/{id}/confirm|decline|remove` (Privacy & Consent). TR019's ranking function reads only `state='active'` rows here as confirmed-preference input; Trust & Safety's `reports` table is **never** queried by Discovery & Ranking at all — enforced as an import-boundary absence (no code in Discovery's package imports Trust & Safety's repository), the same structural-absence style as TR019's `RankingSignals` type, directly answering cross-cutting rule 10's anti-retaliation guarantee.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR039 — Report and block intake
**Traces from:** FR39
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /v1/reports` (Trust & Safety) creates or merges into a `moderation_cases` row (dedup by `object_kind`+`object_id` within an already-open case, incrementing `reporter_count` rather than creating a duplicate case). No read model Trust & Safety exposes to the reported party includes reporter identity, at the query level (the reported-party-facing endpoint's `SELECT` never includes `reports.reporter_id`). Honors the rate-limit utility (Cross-cutting §2, key = `reporter_id:day`, limit = 10). Offers Block (TR024) in the same request flow.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR040 — Moderation queue and graduated actions
**Traces from:** FR40
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`GET /v1/admin/moderation-queue`, `POST /v1/admin/moderation-cases/{id}/decide` (Trust & Safety, federated into the platform Admin Console per ADR-012). Six actions (Limit/Remove-Hide/Restore/Request-verification/Suspend/Dismiss) each require a mandatory `reason_code`. High/Critical severity sets `moderation_cases.distribution_limited=true` **at report-merge time**, and every distribution query in Listings & Verification/Opportunities filters `WHERE NOT distribution_limited` — the auto-limit is enforced at the data-read layer every listing surface already shares, not only in the admin UI. Evidence fields on a case are immutable once created (no `PATCH` route exists for them).

**Constraints surfaced**
ADR-012 itself names the Admin Console plugin contract as not yet formally specified and expects Vyapar or Milavn to be the first mover. If the platform-wide contract isn't ready when this ships, build a Vyapar-only queue screen at the same URL space the eventual federated contract will use, so migrating in later is additive, not a rewrite — this is the concrete first exercise of that open platform item, named here rather than assumed resolved.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR041 — Appeals with graceful different-operator routing
**Traces from:** FR41
**Status:** Ready for Review | **Confidence:** High | **Priority:** Should

**Technical requirement**
`POST /v1/appeals` (Trust & Safety, `appeals` table, `UNIQUE(case_id, member_id)` already enforces one appeal per decision, `due_at` defaults to 7 days). Queue assignment excludes the original case's `operator_id` from the assignable pool where more than one staffed operator exists, degrading gracefully to same-operator assignment at solo-founder scale — matching FR41's own "where staffing allows" wording exactly, rather than papering over it with a rule that assumes staff that doesn't exist yet.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR042 — Three-language rendering via shared platform i18n
**Traces from:** FR42
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
All MOD01 UI strings live in per-language resource files (en/hi/te) consumed via the shared platform i18n library (ADR-010); a missing key falls back to English and logs an `analytics_events` row (`kind='i18n_fallback'`) rather than failing silently. Taxonomy display names already have `name_hi`/`name_te` columns on `taxonomy_terms`. Language is explicitly absent from `RankingSignals` (TR019) — never a ranking input.

**Constraints surfaced**
**Gap:** member-authored free text (`listings.description`, `opportunities.description`, etc.) has no `content_language` column today, so "member content untouched with a language tag" (FR42's own acceptance criterion) is not yet storable — Step 7a should add this column wherever member free text is stored.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR043 — WCAG 2.2 AA baseline with a CI release gate
**Traces from:** FR43
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
An automated accessibility check (e.g. axe-core) runs in `vyapar-web`'s CI pipeline against every screen; a failing screen blocks that screen's release, per FR43's own stated rule. A manual screen-reader pass of the four core journeys (setup, search, enquiry, post) is recorded as a checklist artifact in the module's implementation record (`09-implementation.md`) before conformance is claimed — this is a release-process requirement, not a database or API concern, and is named here as such rather than invented a data model for.

**Constraints surfaced**
Automated tooling cannot catch every WCAG 2.2 AA criterion (e.g. meaningful focus order) — the two-layer approach (automated gate + recorded manual pass) is the correct response to that known limitation, not a gap in itself.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR044 — Progressive first-run to Discover
**Traces from:** FR44
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`GET /v1/first-run/state`, `POST /v1/first-run/step` (Identity Bridge) against `members.first_run_step`/`first_run_done` (already modeled). Server-side step-save is idempotent (repeating a step call is a no-op on the same step). None of the five screens is a sign-up/login/OTP-sign-in screen — enforced by this endpoint family having no credential-related route at all (a structural absence, the same style as TR005/TR019/TR038), directly answering the product owner's standing correction this FR's own Review history records. Location-permission-denied falls back to a manual `locality` text field on the same `PATCH /v1/first-run/step` call.

**Constraints surfaced** — none beyond re-confirming, per FR44's own explicit acceptance criterion, that no screen in this flow is an auth screen.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR045 — Event instrumentation with outcome levels
**Traces from:** FR45
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /v1/events` (batched) writes `analytics_events` (Analytics) with a mandatory `level` tag (`impression`/`view`/`action`/`attributed_outcome`/`confirmed_outcome`/`operational`, already modeled). The server **rejects** any non-`operational` event when `privacy_settings.behavioral_analytics=false` for that member — enforced at the API layer, not only by a client-side opt-out a modified client could bypass. Client-side buffering (24h, then drop-with-count-metric) on pipeline unavailability is a frontend/local-storage concern, out of this endpoint's own scope.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR046 — Marketplace health metrics with minimum group-size suppression
**Traces from:** FR46
**Status:** Ready for Review | **Confidence:** High | **Priority:** Should

**Technical requirement**
`GET /v1/admin/marketplace-health` (Analytics, federated into Admin Console) aggregates `analytics_events`/`impressions`; every `GROUP BY` in this query suppresses groups with `COUNT(*) < 10` **server-side** — such a group is never included in the response at all, not merely hidden by the client — directly closing the re-identification risk IA046 names for a close-knit community. No profile-completion-percentage metric exists in this endpoint's response schema, an intentional, permanent omission.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR047 — Verification queue (Admin Console federated view)
**Traces from:** FR47
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`GET /v1/admin/verification-queue` (Listings & Verification, federated into Admin Console per ADR-012), ordered oldest-first, highlighting rows where `now() - created_at > 3 business days`. `POST /v1/admin/verification-queue/{id}/verify|reject|needs-clearer-copy` calls TR008/TR009's own decision path. Evidence (`image_url`, `identifier_enc`) access is gated by the Authorization Engine checking `members.operator_permissions @> ARRAY['verification']` — the endpoint itself performs no permission logic, it only calls the chokepoint.

**Constraints surfaced** — none beyond CCR12's already-named operator-bottleneck risk, mitigated by the overdue-highlighting itself.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR048 — Opportunity/stale queue and taxonomy management
**Traces from:** FR48
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`GET/POST /v1/admin/opportunities-queue`, `/v1/admin/stale-queue` (bulk Remind/Expire, confirmation-with-counts required before execution), `/v1/admin/taxonomy` (add/merge/rename) — Opportunities and Listings & Verification respectively (taxonomy is owned by Listings & Verification per the component table, called here through its own interface, never a direct write from this admin surface). Merge preserves both labels via `taxonomy_terms.aliases[]`/`merged_into` (already modeled) so search continues to resolve the old term. Every taxonomy change publishes the same TR002/TR003 domain-event pattern, consumed by the Search Bridge for reindex within 5 minutes.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR049 — Commercial administration with structural separation of powers
**Traces from:** FR49
**Status:** Ready for Review | **Confidence:** High | **Priority:** Should

**Technical requirement**
`GET/POST /v1/admin/commercial` (Commercial, federated into Admin Console): product/price versioning is **insert-only** on `products` (never an `UPDATE` on an existing `(id, version)` row with orders against it — the table's own comment already states this rule; the API layer must have no route capable of violating it). Refund/credit calls the Payment Bridge (TR051) with a server-side `amount <= order.amount_paise` guard. Ranking diagnostics (`GET /v1/admin/commercial/diagnostics/{id}`) calls TR019's own ranking function with `explain=true` — never a second, independently-written diagnostic implementation that could silently disagree with the real ranking logic. This admin surface has **no route at all** that writes `listings.verification_state`, ranking `config` weights, or `moderation_cases` — the separation-of-powers guarantee (cross-cutting rules 2/3) is enforced by route absence, not a permission check on a route that exists.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR050 — Identity Bridge: platform session resolve, fail-closed, member-link
**Traces from:** FR50
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Implements `/MODULE-ARCHITECTURE-STANDARD.md` §5b exactly, per its own binding contract (`docs/ParentApp/07-tech-reqs.md` TR10–TR16): read the `fk_session` cookie; resolve via `POST /internal/v1/sessions/resolve` with an in-process cache of ≤30 seconds (negative results ≤5 seconds); on Identity & Trust unreachability, return `503` — **never** a local/default member fallback (a structural absence: no code path in the Identity Bridge constructs a member context without a successful resolve or a still-valid cache entry). The `members` row is created just-in-time on first entry via `INSERT ... ON CONFLICT (id) DO UPDATE SET synced_at = now()` — an idempotent upsert keyed on the platform member id, directly closing IA050's named duplicate-row risk. The resolved `member_id` is bound into `SET LOCAL vyapar.authz_context` (Cross-cutting §3) for the request's transaction. Unauthenticated visitors are redirected to `${FORKHATRI_ENTRANCE_URL}/?return_to=...`.

**Constraints surfaced**
Members holding a valid platform session continue read-only in Vyapar for up to 15 minutes during an Identity & Trust outage (FR50's own stated degradation window) — this is a read-only allowance, not a write fallback; no mutation endpoint in this file may succeed without a fresh, successful resolve.

**Assumptions** — none beyond the binding contract cited above.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR051 — Payment Bridge: idempotent orders, verified webhooks, isolated adapter
**Traces from:** FR51
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /v1/payments/orders` (Payment Bridge) creates a `payment_orders` row; the `idempotency_key` column's `UNIQUE` constraint means a retried request with the same key returns the original row rather than creating a duplicate order — the mechanism is database-enforced, not application-logic-only. `POST /v1/payments/webhook` verifies the gateway's signature **before** any state write and is itself idempotent: every received webhook event id is appended to `webhook_events JSONB`, so a duplicate delivery (normal Razorpay/Cashfree-class behavior per CCR03's grounded research) is a no-op, and an out-of-order event (e.g. a refund webhook arriving before its payment webhook) is stored and reconciled once the corresponding earlier event also arrives, rather than applied blindly against a state that doesn't exist yet. All gateway calls (`initiate_order`, `verify_webhook`, `issue_refund`) go through one `PaymentGateway` interface — Commercial (TR030/TR031/TR033/TR035/TR049) never imports a gateway SDK directly, only this interface, which is the concrete CCR13 swap seam for a future MOD06 consolidation. Raw card/bank credentials never reach this service by construction (hosted/tokenized checkout only — there is no field on `payment_orders` capable of holding one).

**Constraints surfaced**
Genuine end-to-end webhook-replay/signature-failure testing against a real sandbox gateway is a Step 10/11 concern layered on top of this tech req's business rules, not something this file itself can verify.

**Assumptions** — gateway vendor is a `config`/`.env` value with placeholder keys created at implementation time (Step 9), per FR51's own stated assumption.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR052 — Six minimum-field adjacent-service contracts, one outbox mechanism
**Traces from:** FR52
**Status:** Ready for Review | **Confidence:** Medium — matches the FR's own stated confidence (adjacent owners must accept these minimum-field contracts). | **Priority:** Must

**Technical requirement**
One shared `publish_with_outbox(event)` helper (Integration Bridges, Cross-cutting §4) is the single implementation every one of the six contracts uses: (a) Search Bridge — index publish/remove within 5s, already exercised by TR002/TR003/TR013/TR048; (b) Notification Bridge — template id + member id + parameters only, exercised by TR021/TR023/TR041/TR054; (c) Audit Bridge — the shared audit-event definition, exercised implicitly by every state-changing TR in this file; (d) Object Storage Bridge — pre-signed upload/fetch under MOD01's own access policy, exercised by TR008/TR009/TR011/TR022/TR037/TR039; (e) Dashboard Read Bridge (MOD05) — `GET /internal/v1/dashboard-summary/{listing_id}` returns only `{name, category, locality, verification_state, freshness}`, an explicit **response-shape allow-list** (not a filtered version of the full row), so a future column added to `listings` cannot silently leak through this endpoint without a deliberate change to the allow-list itself; (f) Counsel Referral Bridge (MOD04) — the same `counsel_referrals` write TR023 already defines. Failed deliveries after retry exhaustion land in the shared `dead_letters` table, visible at `GET /v1/admin/dead-letters` (feeds TR049). No route anywhere grants any other module direct database access to `vyapar`'s tables — the six contracts above are the only path in or out.

**Constraints surfaced**
Six independent adjacent-service contracts is real surface for one to quietly skip idempotency — the one-`publish_with_outbox`-implementation decision is the direct answer to that, named once here rather than left implicit per contract.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR053 — Versioned legal notice, terms, and grievance-channel gate
**Traces from:** FR53
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`legal_documents`/`acceptances` (Privacy & Consent, already modeled, three-language `UNIQUE(kind, version, language)`). `POST /v1/legal/accept` records `(member_id, kind, version)`. TR003 (listing submit) and TR022 (enquiry submit) each call Privacy & Consent's `has_accepted(member_id, kind)` check **before** proceeding — the gate is enforced at the call site of every gated action, not only by a client-side redirect a modified client could skip. Rolling back a notice version restores the prior `body` text without deleting any row in `acceptances` — version history and acceptance history are two independent, both-append-only records.

**Constraints surfaced** — three-language completeness at publish time is a content-operations discipline (CCR11), not a one-time build task.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR054 — Commercial disclosure, universal Sponsored labelling, gated renewal
**Traces from:** FR54
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Every paid-placement surface uses TR030's own shared `<SponsoredBadge>` render path — restated here as this FR's own requirement, not a second implementation. Purchase/renewal requires an explicit `POST /v1/{promotions|entitlements}/{id}/confirm-purchase` call, structurally separate from order creation, so "no charge without a confirmed disclosure screen" is a two-step flow the API enforces, not a UI convention a redesign could accidentally remove. The renewal-reminder job (Cross-cutting §6, day-3-before-renewal) must record a successful Notification Bridge acknowledgment before the renewal job is permitted to proceed; on failure, the entitlement's renewal is `paused` with a notice rather than silently charged — the renewal job's own guard condition checks the reminder's delivery record, not merely that 3 days have elapsed.

**Constraints surfaced**
Every future paid-surface addition must remember to route through the one shared badge component (IA054's named discipline-as-much-as-mechanism risk) — flagged here for Step 9's code review checklist, not assumed self-enforcing.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## TR055 — Opportunity detail, typed primary action, and Activity screen
**Traces from:** FR55
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`GET /v1/opportunities/{id}` (Opportunities) composes TR020's why-this, TR010's poster trust context, and TR022's server-computed primary-action label (derived from `opportunities.type`, exactly as TR022 already defines — never a second, independently-coded type→label mapping) plus the two external-link variants ("Apply on source website" / "Open official website") for `source_segment='public'` items. `POST /v1/opportunities/{id}/not-interested` writes `member_opportunity.hidden_reason` (one of the six modeled reasons), feeding TR038's derived-preference proposal pipeline. `GET /v1/activity` lists the six groups (Saved/Responded/Shared/Posted/Recently viewed/Completed) via one parameterized query over `member_opportunity`/`member_listing`, not six separately-built endpoints. Sharing a `removed` item is blocked at the API layer (checked against `opportunities.state` before allowing the share action to record).

**Constraints surfaced** — none beyond the type→label single-source-of-truth already fixed by TR022.
**Assumptions** — detail structure follows `Vyapar_02` §6/§9 and the feedback vocabulary in §10, per FR55's own stated assumption.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Architect — [x] Approved — autonomous execution, 2026-09-14

---

## Closing note for Step 7a (ER Model & Database Implementation)

This file is Sealed and does not wait on Step 7a's own three-pass process to begin. Step 7a should treat the following as inputs from this pass, not rediscoveries — each was surfaced against the real, already-loaded `db/schema.sql` draft and `db/seeds.sql`, not invented abstractly:

1. **The largest gap: schema-per-component + RLS is not yet implemented.** `db/schema.sql` creates one flat `vyapar` schema holding all 13 components' tables, with no RLS policies, no non-owning application DB role, and no `SET LOCAL` session-context wiring anywhere. Cross-cutting §3 above names the two concrete, research-confirmed failure modes (`/MODULE-ARCHITECTURE-STANDARD.md` §4) Step 7a must design against explicitly: RLS silently not applying to an owning role, and session-context leakage under transaction-mode connection pooling if plain `SET` is used instead of `SET LOCAL`.
2. **Idempotency-key table (Cross-cutting §1)** — one shared `idempotency_keys` table and middleware for `POST /v1/enquiries`, `/v1/partnership-requests`, `/v1/reviews`, `/v1/promotions|entitlements|campaigns`, `/v1/reports`, rather than a one-off column per table (the pattern `payment_orders`/`notifications` already use ad hoc).
3. **Rate-limit-counter table (Cross-cutting §2)** — one shared `rate_limit_counters` table for the three rolling-window caps (FR21, FR22, FR39); the two standing-count caps (FR25's pending limit) correctly stay as plain `COUNT(*)` queries and need no new table.
4. **Five named, narrow schema fixes**, each already called out at its own TR: a `listings.setup_step` column (TR004); a trigger or app-layer reset of `contact_verified` on phone change (TR007); a partial unique index enforcing "1 open enquiry per target" (TR022); a generalized Promotion/Entitlement history table (TR031); an FK from `promotions.campaign_id` to `campaigns.id` (TR035); a `content_language` column wherever member free text is stored (TR042).
5. **The member-deletion anonymization-vs-counterpart-preservation schema (TR037)** is explicitly handed to Step 7a as an ER-Model-shaped decision, per IA037's own finding — this file fixes only the behavior contract (anonymize the requester, never cascade-delete a counterpart's record), not the concrete tombstone/anonymization table design.
6. **The component decomposition and traceability table** under "Component decomposition (Vyapar)" above should graduate into a formal `modules/MOD01-vyapar/architecture.md` (component diagram, placement recap) once that file's actual owner is assigned by the pipeline's Step 0b/Solution Architecture pattern — Step 7a may be the practical place this happens, given it already needs the same component boundaries to design schema ownership; if so, cite this file's table rather than re-deriving it.
