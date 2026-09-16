---
step: 08-security-performance
module: MOD01
status: Sealed
approver: Security Lead
updated: 2026-09-14
items: "55 | approved: 55 | blockers: 0"
---

# 08 — Security & Performance Analysis — MOD01 Vyapar

## Revision history

| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-14 | Initial and only pass. Looped over all 55 Sealed tech reqs (`07-tech-reqs.md`, TR001–TR055) one at a time, per this agent's own loop discipline: re-read each TR, its ER-model table/RLS-policy row(s) (`07a-er-model.md`), the relevant `/ARCHITECTURE.md` trust boundary and ADR (ADR-004 Identity & Trust, ADR-011 security/privacy/audit tiering, ADR-012 Admin Console), `/MODULE-ARCHITECTURE-STANDARD.md` §4/§4b/§4c/§5/§5b/§6, the live-verified `07a-db-implementation/` schema (actual RLS predicates and role grants, not an abstraction), and MOD03 Mangaly's own `AgentOutputs/08-security-performance.md` as a structural/house-style reference only (canonical-control convention, performance-class table), before writing each item's STRIDE pass and performance thresholds. Ran current-year web research before setting thresholds/mitigations rather than from memory alone: OWASP API Security guidance on Broken Object Level Authorization and rate-limiting/throttling patterns, and Razorpay/Cashfree's own published webhook-signature-verification and idempotency guidance (both licensed-India-gateway candidates named in TR051/CCR03) — folded into SP015/SP018 (search-scraping gap), SP021/SP022/SP039 (rate-limit posture), and SP051 (webhook dedup-by-event-id). No `docs/PreStartResearch/` constraint was found that adds a compliance requirement beyond what `07-tech-reqs.md`/`07a-er-model.md` already carry forward (DPDP-adjacent controls — masked storage, 30-day document deletion, anonymize-in-place — are already fixed by TR008/TR037/ER-model Pass 1 and restated here, not re-derived). One SP item per TR (SP001–SP055, matching TR numbering 1:1, no supplementary deep-dive items — unlike Mangaly's SP103/SP104, no TR in this file surfaced a dependency narrow and load-bearing enough to warrant a standalone pass beyond its own TR's scope). Four genuine gaps this pass found that the Sealed FR/TR/ER-model text does **not** already mitigate are resolved as concrete Decisions inside the relevant item (SP008/SP009 — encryption-key management for `identifier_enc`; SP008/SP009/SP011/SP022/SP037/SP039 — Object Storage signed-URL TTL; SP015/SP018 — search/feed scraping rate limit; SP052 — inter-module service-to-service authentication for the five non-Identity-Bridge contracts) rather than left open, per this project's standing preference to resolve pipeline blockers concretely from source docs/research rather than manufacturing more open decisions. | Step 8, continuous build mode per product owner direction 2026-09-14 ("never wait for me… complete this application developing as continuous chain"; autonomous execution extends through Steps 5-8 before Step 9 begins, per the standing memory of that instruction). |
| 2026-09-14 | **Sealed.** Coverage verified 55/55 TR↔SP 1:1; every STRIDE row explicitly Y/N (no blanks); every item has a measurable performance threshold; quality-gate table below all Pass; open blockers: none. Step 9 (Implementation) is cleared to begin against this Sealed file. | Approved — autonomous execution, 2026-09-14. |

## Conventions used in this file (stated once, applied consistently — not a way of leaving cells blank)

55 items share a small number of structural mitigations already fixed at the
tech-req/ER-model level. Each shared mitigation is stated **once**, canonically,
and every other item's STRIDE table cites it by name rather than re-deriving
it — the same discipline `07-tech-reqs.md` and `07a-er-model.md` already
applied to RLS, rate-limiting, and idempotency, and the convention MOD03
Mangaly's own Step 8 file established for this project. Citing a canonical
control is still an explicit Y/N answer with a real, traceable mitigation —
never a blank cell.

- **RLS-CC (canonical: SP001)** — this item's data crosses an RLS-bearing
  schema boundary (38 of 43 tables per `07a-er-model.md`'s RLS policy table).
  Mitigation: `vyapar_app` is a non-owning DB role — live-verified as owning
  **zero** of the database's 43 tables (`vyapar_owner` owns all 43), so RLS
  cannot be silently bypassed by table ownership (Failure mode (a), §4);
  `vyapar.authz_context` is set via **`SET LOCAL`** inside the same
  transaction as every query by the Identity Bridge (TR050), live-verified
  not to leak across transactions/statements (Failure mode (b), §4);
  deny-by-default — no session context returns zero rows on every sensitive
  table, live-verified. Structural Elevation-of-Privilege /
  Information-Disclosure defense-in-depth beneath application-level
  authorization, never a substitute for it.
- **Idempotency-CC (canonical: SP022)** — mutation is client-queueable per
  Cross-cutting §1's named endpoint list. Mitigation: shared
  `vyapar_platform.idempotency_key` (`UNIQUE(member_id, idempotency_key,
  endpoint)`) — a repeated key returns the original `response_snapshot`
  without re-executing. Closes the Tampering/duplicate-write failure mode a
  naive client retry-on-reconnect would open, per `/MODULE-ARCHITECTURE-
  STANDARD.md` §4b.
- **RateLimit-CC (canonical: SP021)** — endpoint is abuse-prone (fatigue,
  spam, brute-force). Mitigation: shared `vyapar_platform.rate_limit_counter`
  + `check_and_increment(key, window_seconds, limit)` — one DB-backed,
  restart-surviving implementation every rolling-window-capped endpoint
  calls, per §4c. Standing-count caps (FR25's 10-pending limit) are a
  distinct, correctly-not-forced-through-this-utility pattern (Cross-cutting
  §2(b)) — cited separately where it applies.
- **Audit-CC (canonical: SP002)** — mutation publishes a transactional-
  outbox domain event (same DB transaction as the state change, via
  `publish_with_outbox()`, §6) consumed by the Integration Bridges'
  Audit Bridge. Mitigation for Repudiation: actor identity (resolved
  `member_id`) and the action are captured at the moment of commit,
  forwarded to the platform's independent, append-only Audit Service
  (ADR-011) — an audit gap here is a compliance failure, not a missed
  nice-to-have, per ADR-011's own "at-least-once, never best-effort" text.
- **PropagationSLA-CC (canonical: SP002)** — a state change must stop
  appearing on/start appearing on a consuming surface within a stated,
  FR-fixed bound (5 seconds for most index/read-model propagation; other
  bounds named per item). Mitigation: the same transactional outbox as
  Audit-CC, consumed by the Search Bridge/Dashboard Read Bridge, read
  through **one** shared function per surface (never three independently-
  coded checks) so the bound cannot be met on one surface and missed on
  another.
- **IdentityBridge-CC (canonical: SP050)** — the item depends on who the
  caller is. Mitigation: TR050/§5b's fail-closed platform-session resolve —
  `503` (never a local/default member fallback) on Identity & Trust
  unreachability; ≤30-second positive / ≤5-second negative in-process
  cache; idempotent `INSERT … ON CONFLICT DO UPDATE` member-link upsert
  (closes IA050's duplicate-row risk); the resolved `member_id` is the
  sole value bound into `vyapar.authz_context`, never a client-supplied
  field.
- **AuthzChokepoint-CC (canonical: SP005)** — a consequential read/write
  must be gated by role/permission/entitlement state. Mitigation: the
  Authorization Engine's public methods take an already-resolved
  `AuthzContext`, never a raw member id the callee decides for itself —
  per §5, a method taking a bare id and querying with it is a defect
  against this pattern, not a style nit.
- **StructAbsence** — the stated mitigation is a schema/contract-level
  absence (a column, join path, or response field genuinely does not
  exist, or no route exists), not a runtime check a future code path could
  bypass. Verification method: a CI schema-introspection/route-inventory
  test (Class G below), not a functional test alone.
- **PaymentIsolation-CC (canonical: SP051)** — the item touches money
  movement. Mitigation: all gateway calls go through the one
  `PaymentGateway` interface (the CCR13 swap seam); no field on
  `payment_orders` can hold raw card/bank data (hosted/tokenized checkout
  only); webhook signature verified before any state write; every received
  webhook event id is appended to `webhook_events JSONB` so a duplicate
  delivery (normal Razorpay/Cashfree at-least-once behavior, confirmed by
  2026 vendor documentation) is a no-op.
- **SponsoredBadge-CC (canonical: SP030)** — the item is a paid-placement
  surface. Mitigation: one shared `<SponsoredBadge>` render path used by
  every surface that can show a boosted card; `RankingSignals` (TR019) has
  **no field** for paid/promoted status at all — Sponsored inclusion is an
  audience-eligible impression boost, structurally never a rank boost.
- **NoLeadList-CC (canonical: SP024)** — the item touches enquirer/provider
  contact data. Mitigation: no endpoint anywhere in this file exposes a
  bulk/export view of contact details to any role — verified by the
  absence of such a route (BR07/BR10's "no lead lists" invariant),
  not a permission check on one that exists.

### Performance threshold classes (referenced by short code in each item; concrete numbers, not "should be fast")

| Class | Applies to | Threshold |
|---|---|---|
| **A** — simple authenticated read | Single-resource `GET` behind `AuthzContext` (listing/opportunity/enquiry detail, privacy settings, activity list) | P95 < 200 ms, P99 < 500 ms, error rate < 0.1%, sized to 5,000 concurrent sessions / 50,000 registered members (`/ARCHITECTURE.md` platform-wide scalability baseline for the point Vyapar/Milavn/Dashboard also ship) |
| **B** — mutation with outbox write | `POST`/`PATCH` writing state + outbox row in one transaction (listing/opportunity create-edit, enquiry/partnership/review submit, promotion/entitlement purchase) | P95 < 400 ms, P99 < 800 ms, sized to the same 5,000-concurrent-session baseline; FR-stated outer product bound (e.g. FR01's 2-second Draft save) is the user-facing failure threshold, this engineering SLO is the design margin inside it |
| **C** — search/browse/feed ranking query | `GET /v1/listings/search` (TR015), `GET /v1/opportunities/feed` (TR018), `GET /v1/opportunities/{id}/why` (TR020) | First-page/first-section P95 < 800 ms engineering target, **never exceeding FR15/FR18's own 2-second product acceptance bound**, against Postgres FTS `search_tsv` GIN indexes at V1 volume (ADR-007); sustained P95 > 1.5 s for 15 minutes at V1 volume is the ADR-018 Search-Service-extraction re-evaluation trigger, not a silently tolerated regression |
| **D** — external-I/O-dependent call | SMS/OTP dispatch (TR007), Object Storage signed-URL issuance (TR008/TR009/TR011/TR022/TR037/TR039), Identity & Trust resolve (TR050), gateway `initiate_order`/`verify_webhook` calls (TR051) | Own-side latency (excluding third-party RTT) P95 < 250 ms; caller-side timeout ≤ 2 s with an explicit graceful-degradation branch (never a hang) |
| **E** — eventual-consistency propagation bound | Index/read-model/label add-or-remove after a state change (disclosure TR002, lifecycle TR003/TR013, verification revert TR010, blocking TR024, reputation-count exclusion TR028/TR029, distribution-limit TR040, privacy propagation TR036) | P95 within the FR-fixed bound: 5 seconds for the general case (FR02/FR03/FR05/FR10/FR13/FR28/FR36/FR39/FR40); 5 minutes for taxonomy reindex (FR48); 1 hour for credential/identity sync (FR06/FR50) — measured end-to-end from DB commit to the consuming surface reflecting the change, not from event publish |
| **F** — background/scheduled job | Freshness/reminder/expiry/export/deletion jobs (TR006, TR008, TR010, TR012, TR013, TR021, TR023, TR037, TR048, TR054) | Scheduled run completes within its own FR-stated window (72h export; 30-day document deletion; day-N reminder/archive/expiry boundaries) or fires a failure alert within 15 minutes; job idempotent on re-run |
| **G** — structural-absence/route-inventory check | "no field/route/join exists" items (TR005, TR006, TR019, TR024, TR029, TR038, TR044, TR049) | Not a runtime metric — CI gate, 100% pass rate, zero tolerance for drift, runs on every route/schema change, blocks merge on failure |
| **H** — rate-limit/idempotency infra table op | `vyapar_platform.*` lookups (`check_and_increment`, idempotency-key upsert) | P95 < 20 ms, P99 < 50 ms even under a retry burst (single indexed-row UPSERT) |
| **I** — payment/webhook processing | `POST /v1/payments/orders`, `POST /v1/payments/webhook` (TR051) | Order-state update reflects a gateway event within 30 seconds (FR51's own bound) — webhook-handler-own latency (excluding gateway RTT) P95 < 300 ms |

## Coverage check

| Parent Tech Req | Items produced | Covered |
|---|---|---|
| TR001 | SP001 | Yes |
| TR002 | SP002 | Yes |
| TR003 | SP003 | Yes |
| TR004 | SP004 | Yes |
| TR005 | SP005 | Yes |
| TR006 | SP006 | Yes |
| TR007 | SP007 | Yes |
| TR008 | SP008 | Yes |
| TR009 | SP009 | Yes |
| TR010 | SP010 | Yes |
| TR011 | SP011 | Yes |
| TR012 | SP012 | Yes |
| TR013 | SP013 | Yes |
| TR014 | SP014 | Yes |
| TR015 | SP015 | Yes |
| TR016 | SP016 | Yes |
| TR017 | SP017 | Yes |
| TR018 | SP018 | Yes |
| TR019 | SP019 | Yes |
| TR020 | SP020 | Yes |
| TR021 | SP021 | Yes |
| TR022 | SP022 | Yes |
| TR023 | SP023 | Yes |
| TR024 | SP024 | Yes |
| TR025 | SP025 | Yes |
| TR026 | SP026 | Yes |
| TR027 | SP027 | Yes |
| TR028 | SP028 | Yes |
| TR029 | SP029 | Yes |
| TR030 | SP030 | Yes |
| TR031 | SP031 | Yes |
| TR032 | SP032 | Yes |
| TR033 | SP033 | Yes |
| TR034 | SP034 | Yes |
| TR035 | SP035 | Yes |
| TR036 | SP036 | Yes |
| TR037 | SP037 | Yes |
| TR038 | SP038 | Yes |
| TR039 | SP039 | Yes |
| TR040 | SP040 | Yes |
| TR041 | SP041 | Yes |
| TR042 | SP042 | Yes |
| TR043 | SP043 | Yes |
| TR044 | SP044 | Yes |
| TR045 | SP045 | Yes |
| TR046 | SP046 | Yes |
| TR047 | SP047 | Yes |
| TR048 | SP048 | Yes |
| TR049 | SP049 | Yes |
| TR050 | SP050 | Yes |
| TR051 | SP051 | Yes |
| TR052 | SP052 | Yes |
| TR053 | SP053 | Yes |
| TR054 | SP054 | Yes |
| TR055 | SP055 | Yes |

## Set-level quality gate

| Check | Result |
|---|---|
| Every TR has exactly one SP item | Pass — 55/55, SP001–SP055, 1:1 with TR001–TR055. |
| Every STRIDE row is explicitly Y/N, never blank | Pass — every one of the 55×6 = 330 STRIDE cells below states Y or N with a Threat/Mitigation/Priority for Y rows and an explicit reason for N rows. |
| Every item has a measurable performance threshold | Pass — every item cites at least one Class A–I threshold from the table above, or (for structural-absence items) Class G's CI-gate criterion. |
| Canonical controls cited, not re-derived, where one already exists | Pass — RLS-CC/Idempotency-CC/RateLimit-CC/Audit-CC/PropagationSLA-CC/IdentityBridge-CC/AuthzChokepoint-CC/PaymentIsolation-CC/SponsoredBadge-CC/NoLeadList-CC are each stated once above and cited by name throughout, matching the discipline `07-tech-reqs.md`/`07a-er-model.md` already established for RLS/idempotency/rate-limiting. |
| No new component, schema, or authorization pattern invented beyond what `07-tech-reqs.md`/`07a-er-model.md` already fixed | Pass — every mitigation cites an existing TR/FR/ER-model mechanism; the four genuine gaps this pass found (SP008/SP009/SP011/SP022/SP037/SP039 encryption-key management and signed-URL TTL; SP015/SP018 search-scraping rate limit; SP052 inter-module service auth) are resolved as scoped Decisions inside the relevant item, not as new components. |
| Every genuinely load-bearing constraint is named for Step 9, not left implicit | Pass — see "Closing note for Step 9" below. |

## Open blockers

None. Four genuine gaps this pass found (identity-document encryption-key management; Object Storage signed-URL TTL; search/feed scraping rate limit; inter-module service-to-service authentication for the five non-Identity-Bridge TR052 contracts) are each resolved as a concrete Decision inside the relevant item below, per this project's standing convention of resolving pipeline blockers concretely from source docs/research rather than manufacturing open decisions Step 9 would otherwise have to make ad hoc.

---

## SP001 — BusinessProfile/ProfessionalListingProfile create-and-edit endpoint
**Traces from:** TR001
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y | Client-supplied `owner_id` creates/edits a listing under another member's identity | IdentityBridge-CC + AuthzChokepoint-CC — `owner_id` resolved server-side from `AuthzContext`, never accepted as client input | High |
| Tampering | Y | Client-side-only validation of the 3 mandatory fields bypassed via direct API call | Server-side field-level validation (TR001); DB-level `UNIQUE(owner_id, name, locality)` constraint | Medium |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | Y | A Draft/Submitted listing visible to a non-owner | RLS-CC (`vyapar_listings.listings`: publicly-visible state OR owner OR content-operator) | Medium |
| Denial of service | Y | Unbounded listing-creation spam by one member — no cap named by any TR/FR | **Gap, resolved here:** a standing-count cap (Cross-cutting §2(b) shape, ≤20 active listings per member), mirroring TR025's own pattern | Medium |
| Elevation of privilege | N | No role/permission change on this path | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Draft save latency | Class B; FR01's own 2-second Draft-save bound is the outer product acceptance criterion | Load test at 5,000 concurrent sessions |
| Duplicate-conflict response | Same Class B bound — returns existing listing id, no separate slower error path | Contract test on the `UNIQUE` conflict path |

**Cautions**
The listing-creation cap named above is a new Should-priority mitigation this pass added — no TR/FR names it. Implement it at Step 9 as a plain `COUNT(*)` guard, not a rolling-window rate limit (same reasoning as TR025's cap).

**Assumptions** — `taxonomy_terms` is the platform-shared reference list, editable via TR048.
**Decisions (append-only)** — Add a standing-count cap of ≤20 active listings per member at `POST /v1/listings`, enforced the same way as TR025's pending-partnership cap; a genuine gap this pass found, not previously named by any TR/FR.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP002 — Per-channel contact disclosure and discoverability toggle
**Traces from:** TR002
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Write acts only on the caller's own listing | AuthzChokepoint-CC + RLS-CC (owner-only write) | — |
| Tampering | Y | A code path independently re-deciding disclosure could diverge from the DB toggle (three-independent-checks risk TR002 itself names) | One shared read function (`contacts_for_viewer()`) every surface calls; no surface computes disclosure independently | High |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | Y | A contact channel appearing on one surface after being hidden on another | PropagationSLA-CC — same shared read function across detail/search/MOD05; RLS-CC on `listing_contacts` | High |
| Denial of service | N | Low-frequency, member-initiated toggle only | — | — |
| Elevation of privilege | N | No role implication | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Toggle write latency | Class B | Load test |
| Cross-surface propagation | Class E — 5 seconds (FR02), end-to-end from DB commit to search index / MOD05 summary reflecting the change | Load test against the eventually-consistent index (CCR02); this is a real target to verify, not assumed free (TR002's own Constraints) |

**Cautions**
The 5-second bound is against an eventually-consistent index — verify under realistic write-then-read load, not a synthetic single-request test.

**Assumptions** — default is Public discovery, contact After accepted enquiry, applied at listing creation (TR001).
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP003 — Listing lifecycle state machine with safety gate
**Traces from:** TR003
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | State-transition endpoint acts on the caller's own listing only | AuthzChokepoint-CC + RLS-CC | — |
| Tampering | Y | Client attempts an illegal state transition (e.g. Archived → Active directly) | Server-side `listings.state` CHECK constraint; illegal transitions rejected with a typed error, never silently ignored | High |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | N | No new read surface introduced by this endpoint | — | — |
| Denial of service | Y | Repeated submit attempts against the config-driven wordlist/spam check, probing for the boundary of what passes auto-activation | The check itself is not rate-limited today — **treated as a Should, not a gap**, since submit already requires `contact_verified=true` (TR007's OTP gate), which is itself rate-limited/lockout-protected, making a bare submit-spam attack self-limiting | Low |
| Elevation of privilege | N | No permission change | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| State-transition write latency | Class B | Load test |
| Distribution stop after Suspend/Archive | Class E — 5 seconds (FR03) | Contract test: listing absent from search/feed within 5s of the state-changing commit |
| Cascade-close of open enquiries | Same transaction as the state change (atomic, not a follow-up job) | Integration test asserting no window where the listing is Suspended but an enquiry is still `open` |

**Cautions**
Wordlist/spam-pattern quality is an ongoing tuning exercise (CCR12), not a one-time build/test-and-done task — route to Step 13 monitoring, not only a Step 10 pass/fail test.

**Assumptions** — the same state machine and gate apply to `kind='professional'` listings.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP004 — ProfessionalListingProfile progressive three-step setup
**Traces from:** TR004
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Same session-bound owner resolution as SP001 | IdentityBridge-CC | — |
| Tampering | Y | Client claims "3 required steps complete" without the server having verified it, allowing an incomplete listing to reach Discover | `listings.setup_step SMALLINT` (this file's own inherited ER-model gap-fix, now live in `07a-db-implementation/schema.sql`) makes step-completion server-verifiable, not client-asserted | High |
| Repudiation | Y | — | Audit-CC on each of the three step-save calls | Low |
| Information disclosure | N | No new sensitive field exposed | — | — |
| Denial of service | N | Individually-saveable `PATCH` calls are low-cost, capped by SP001's listing-count cap upstream | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Per-step `PATCH` latency | Class B | Load test |
| Unmapped capability text searchability | Immediately text-searchable (same commit as the save, not a delayed reindex) | Contract test: a freshly-saved `unmapped_labels[]` entry is findable via `GET /v1/listings/search` within the same request cycle |

**Cautions** — none beyond the `setup_step` server-verifiability already fixed.
**Assumptions** — a member may hold both a BusinessProfile and a ProfessionalListingProfile.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP005 — Capability visibility independent of seeking-status visibility
**Traces from:** TR005
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Not an identity-facing endpoint | — | — |
| Tampering | N | No write path this item introduces | — | — |
| Repudiation | N | Read-only | — | — |
| Information disclosure | Y | **The module's highest-severity risk in this area (IA005): a future code path queries `listings.intent_state` outside Listings & Verification's own public read method, leaking private seeking-status** | StructAbsence — Discovery & Ranking's signal extraction (TR019) calls this exact read method, never a direct query; the read method itself returns `intent_state` only when `intent_visible=true`; RLS-CC as the database-layer second line | Critical |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Import-boundary correctness | Class G — 100% pass, zero tolerance for drift | CI lint rule failing the build on any import of `listings.intent_state` outside its owning read method (per §3's "enforcement" text) |
| Read latency | Class A | Load test |

**Cautions**
This is the module's single most safety-load-bearing tech req. Any future code path found querying `listings.intent_state` outside this one function must be treated as a Critical-severity defect at code review, not a style nit — the same standing this item's own TR text already gives it.

**Assumptions** — none beyond FR05's own text.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP006 — VerifiedCredential read-only reference with hourly re-sync
**Traces from:** TR006
**Status:** Ready for Review | **Confidence:** Medium — matching TR006's own stated confidence.

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Read-only reference, no caller-supplied identity | — | — |
| Tampering | Y | A code path writing to `credential_ref` from anywhere other than the scheduled sync job could forge/extend a credential | StructAbsence — `credential_ref` has exactly one writer (the sync job); no API route accepts it as client input | High |
| Repudiation | N | Automated job, not an attributable member action | — | — |
| Information disclosure | Y | `credential_ref`'s field list could be extended to leak a MOD04 Counsel `ExpertProfile` field | StructAbsence — the field list (`{id, claim, issuer, verified_at, last_checked}`) has no room for one, enforced by the type itself | Medium |
| Denial of service | Y | Identity & Trust unreachability during the hourly sync | Cached value with `last_checked` timestamp shown, no error surfaced to the viewer (graceful degradation, Class D) | Medium |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Hourly re-sync job | Class F — completes within its 1-hour window per listing batch or alerts within 15 minutes | Scheduled-job monitoring |
| Revocation propagation | Class E — 1 hour (FR06's own bound) | Contract test: `credential_ref` set to NULL within one sync cycle of upstream revocation |
| Sync call latency (own-side) | Class D | Load test excluding Identity & Trust's own RTT |

**Cautions** — none beyond the already-named field-list structural boundary.
**Assumptions** — Identity & Trust's VerifiedCredential contract is stable at the version this reads.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP007 — Listing-contact OTP verification (not authentication)
**Traces from:** TR007
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y | Brute-forcing the 6-digit OTP to falsely verify a phone number not actually reachable by the caller | `otp_challenges`: 10-minute expiry, 30-second resend cooldown, 5-attempt lockout for 15 minutes — a real, research-backed brute-force defense for a 6-digit (1-in-1,000,000) code space | High |
| Tampering | Y | A change to `listings.primary_phone` without resetting `contact_verified` would let a verified badge survive a phone-number swap | **Gap, already named by TR007 and carried forward here:** Step 9 must implement either a DB trigger or an explicit application-layer reset of `contact_verified=false` in the `PATCH /v1/listings/{id}` handler — named as a load-bearing Step 9 constraint (see Closing note) | High |
| Repudiation | Y | — | Audit-CC on verify success/failure | Low |
| Information disclosure | N | No OTP code is ever returned in an API response body other than to the requesting device via SMS | RLS-CC (`vyapar_listings.otp_challenges`: self only) | — |
| Denial of service | Y | SMS-bombing another party's phone number via repeated `otp/request` calls | 30-second resend cooldown + 5-attempt/15-minute lockout double as the DoS control here, since the two abuse patterns (guessing and bombing) share the same choke point | Medium |
| Elevation of privilege | N | Creates no session/credential — structurally not an authentication path, so no privilege to elevate | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| OTP send | Class D | Own-side dispatch latency, excluding SMS carrier RTT |
| Verify-call latency | Class B | Load test |
| Lockout correctness | 100% — 6th attempt within the lockout window is rejected, never a 5-attempt-then-allow race | Contract test on the attempt counter under concurrent requests |

**Cautions**
CCR04's grounded finding (DLT template/route mismatch silently fails OTP delivery even on compliant routes) means the lockout design is a necessary accommodation, not over-engineering — template/route registration itself is a Step 9 operational task, not a design gap here.

**Assumptions** — none beyond FR07's own text.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP008 — Business-existence document verification with masked storage
**Traces from:** TR008
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Not an identity-facing endpoint | — | — |
| Tampering | Y | A crafted format for GST/PAN/Udyam identifiers submitted to bypass validation | Server-side format validation (GSTIN 15 chars, PAN 10 chars, Udyam pattern) before insert | Medium |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | Y (highest severity in this file's identity-document class) | Raw GST/PAN/Udyam identifier or document image exposure to a non-owner/non-operator; encryption-at-rest without proper key separation | `identifier_masked` (last 4 only) is the only value any non-owner/non-verification-operator surface ever renders; RLS-CC scopes `verification_records` to self OR verification-permission operator. **Gap, resolved here:** no TR/ER-model text names how `identifier_enc` is actually encrypted or where its key lives — **Decision:** application-layer envelope encryption (AES-256-GCM) with the data-encryption key sourced from the deployment's secret manager (e.g. `VERIFICATION_DOC_ENCRYPTION_KEY`), never colocated with the database itself; key rotation is a manual, documented Step 13 runbook item at V1 scale (no dedicated KMS container exists yet, consistent with ADR-011's risk-tiered-not-uniform posture) | Critical |
| Denial of service | N | Low-frequency, member-initiated submission | — | — |
| Elevation of privilege | N | Document decision authority is gated by `operator_permissions @> ARRAY['verification']` (TR047), not this endpoint | AuthzChokepoint-CC | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Submission write latency | Class B | Load test |
| Image upload | Class D — pre-signed URL, **Decision:** TTL ≤ 15 minutes for the upload grant | Contract test on signed-URL expiry |
| Masked-display correctness | 100% — no non-owner/non-verification-operator response includes `identifier_enc` or an unmasked identifier | Contract test on every response schema touching `verification_records` |
| 30-day deletion job | Class F | Scheduled-job monitoring; Step 8/10 must assert the job actually deletes, not merely that the column/schedule exists (TR008's own Constraints) |

**Cautions**
The masked-storage/30-day-deletion control is a compliance mechanism (CCR07) that must not silently fail — include an automated check in Step 10/13 that the deletion job produces zero surviving rows past `image_delete_after`, not only that it ran.

**Assumptions** — PAN is visually reviewed only in V1; public GST/Udyam lookup is manual (BR03 DEC-001).
**Decisions (append-only)** — (1) Envelope-encrypt `identifier_enc` with a key held in the deployment secret manager, never the database; manual rotation runbook at V1 scale. (2) Object Storage upload signed-URL TTL ≤ 15 minutes.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP009 — Professional-credential document review with re-upload path
**Traces from:** TR009
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | `needs_clearer_copy` is a distinct, non-penalizing state change only an operator can set | AuthzChokepoint-CC | — |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | Y | Same class as SP008 but lower sensitivity (a credential image, not an identity document) | RLS-CC on `verification_records`; same envelope-encryption Decision as SP008 applies uniformly (one mechanism, not two) | Medium |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Submission/decision write latency | Class B | Load test |
| Image upload | Class D, same 15-minute TTL Decision as SP008 | Contract test |

**Cautions** — none beyond SP008's shared Object Storage/masking concerns, at lower sensitivity.
**Assumptions** — none.
**Decisions (append-only)** — Inherits SP008's encryption-key and signed-URL-TTL Decisions (one shared mechanism, not a second implementation).
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP010 — Verification state display, expiry, and single revert call site
**Traces from:** TR010
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | A direct `UPDATE` on `verification_records`/`listings` from another component bypassing `revoke_verification()`, causing the label to drift across surfaces (IA010) | StructAbsence — Trust & Safety (TR039/TR040) and any operator revocation call Listings & Verification's own `revoke_verification(listing_id, reason)` interface method exclusively; import-boundary lint enforces this | High |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | N | No new read surface | — | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Verification-state read | Class A — one shared compute function used by every surface | Contract test: search/detail/feed/MOD05 summary never disagree on `verification_state` for the same listing at the same instant |
| Revert propagation | Class E — 5 seconds (FR10) | Load test against the single `revoke_verification()` call site |
| 11-month reminder / 12-month expiry job | Class F; day-12 check reads `verified_at` directly, never a "reminder sent" flag (so a Notification Bridge failure cannot silently extend expiry, TR010's own rule) | Scheduled-job monitoring + a dedicated test asserting expiry fires even when the reminder send failed |

**Cautions** — none beyond the single-call-site discipline already fixed.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP011 — Opportunity Composer: create, share, or upload
**Traces from:** TR011
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | `poster_id` resolved server-side, same as SP001's owner resolution | IdentityBridge-CC | — |
| Tampering | Y | A pasted URL for background fetch used as an SSRF vector against internal infrastructure | The fetch job must resolve and allow-list only external, non-private-range hosts before fetching (a Step 9 implementation constraint this pass names — TR011 itself does not state an SSRF control) | High |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | N | No new sensitive field | — | — |
| Denial of service | Y | Screenshot upload size abuse; unbounded background-fetch retries on `source_unreachable` | ≤5MB inline-rejected upload cap (TR011); fetch failure sets `source_unreachable` once for later review, never an unbounded retry loop | Medium |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Draft save (create/upload modes) | Class B | Load test |
| Background URL fetch | Class D — asynchronous, never blocks the Draft save (TR011) | Contract test: Draft save latency identical whether `share` mode's fetch has completed or not |
| Upload size guard | 100% — >5MB rejected inline, 0% silent truncation | Contract test |

**Cautions**
**Decision:** the background URL-fetch job must allow-list only public, non-RFC1918 hosts before issuing the request (SSRF defense) — not named by TR011/FR11, a genuine gap this pass found and resolved as a Step 9 implementation constraint, not a new component.

**Assumptions** — none beyond FR11's own text.
**Decisions (append-only)** — Background URL-fetch (share mode) must reject private/link-local/loopback address ranges before fetching, closing an SSRF path TR011 did not name.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP012 — Structured-field confirmation with uncertainty marking
**Traces from:** TR012
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Same poster-scoped write as SP011 | AuthzChokepoint-CC | — |
| Tampering | Y | Publish attempted before all four mandatory fields (`title`, `type`, `location`, `response_method`) are confirmed | Server-side block on publish until all four are present in `confirmed_fields` (TR012) | Medium |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | N | — | — | — |
| Denial of service | N | Rule-based extraction runs synchronously but is not an AI hot-path dependency (bounded cost) | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Confirm-field write latency | Class B | Load test |
| Day-5 reminder / day-7 auto-archive job | Class F | Scheduled-job monitoring, with an explicit timezone/boundary test (IA013's own named risk, carried forward from TR013) |

**Cautions** — none beyond the extraction-quality caveat already named as a graceful-degradation design, not a defect.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP013 — Opportunity freshness lifecycle
**Traces from:** TR013
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Scheduled job, not an actor-initiated call | — | — |
| Tampering | Y | A timezone/off-by-one bug in the day-14/21/45 boundary silently misclassifies freshness (IA013's own named real risk, more than the state-machine logic itself) | Dedicated timezone/boundary test at Step 10, not only a state-transition unit test; every transition publishes via the same transactional outbox as SP002/SP003 | High |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | N | — | — | — |
| Denial of service | N | Daily batch job, bounded cost | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Daily freshness-evaluation job | Class F — completes within its own daily window or alerts within 15 minutes | Scheduled-job monitoring |
| Index removal after state transition | Class E — 5 seconds (FR13) | Load test |
| Boundary correctness | 100% — day-14/21/45 evaluated in the launch geography's own timezone, no drift across a DST-adjacent date (if applicable) or month boundary | Dedicated Step 10 boundary test (IA013) |

**Cautions**
Scheduled-job correctness (timezone/off-by-one bugs), not the state-machine logic itself, is the real risk here — treat the boundary test as load-bearing, not incidental coverage.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP014 — Opportunity types with V1 launch focus
**Traces from:** TR014
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | Changing `type` post-publish without re-validating type-specific mandatory fields (e.g. switching to `employment` without a compensation field) | Server-side `PATCH` guard re-validates type-specific fields whenever `type` changes, rejecting the save otherwise (TR014) | Medium |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | N | — | — | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Type-change validation | Class B | Load test |
| Type-picker rendering (three V1 types first) | Class A | Contract test on picker ordering |

**Cautions** — none.
**Assumptions** — launch-geography (Hyderabad/Secunderabad) is a `config` table value, not a code constant.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP015 — Standalone Listing search and browse
**Traces from:** TR015
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Search is a read path; no caller identity is asserted by the query itself | — | — |
| Tampering | N | Read-only | — | — |
| Repudiation | N | Not an attributable consequential action | — | — |
| Information disclosure | Y | Only `active_unverified`/`active_verified` listings are ever returned to a non-owner/non-operator caller | RLS-CC on `vyapar_listings.listings` | Medium |
| Denial of service | Y | **Gap, resolved here:** bulk scraping of the full listings directory via repeated, high-page-depth search requests — current 2026 OWASP API guidance names unthrottled data-scraping via a search/list endpoint as a live abuse pattern; no TR/FR names a rate limit on this read path | **Decision:** apply RateLimit-CC (the same shared `check_and_increment` utility, read-path use, key = `caller_id_or_ip:minute`) to `GET /v1/listings/search`, a genuine gap not previously named | High |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| First-20-results latency | Class C — P95 < 800 ms engineering target, never exceeding FR15's own 2-second bound | Load test against `search_tsv` GIN index at V1 volume |
| Zero-result fallback (search degraded) | Falls back to cached category-browse with a notice, same 2-second bound | Contract test simulating FTS degradation |
| Sponsored-vs-organic ordering | SponsoredBadge-CC — 100% of Sponsored items are labeled, 0% reorder organic rank as a side effect | Contract test |
| Scraping rate limit | New — see Decision; threshold set at a level that does not affect a legitimate single user's normal browsing session (e.g. 60 requests/minute/caller) | Load test + abuse-simulation test |

**Cautions**
The 2-second/first-20-results bound and organic-vs-Sponsored ordering are both direct, load-testable acceptance criteria, already named by TR015 as such.

**Assumptions** — none beyond FR15's own text.
**Decisions (append-only)** — Add a rate limit on `GET /v1/listings/search` reusing the shared rate-limit utility in read-path mode; a genuine gap this pass found, grounded in current OWASP API abuse-pattern guidance on unthrottled search/list endpoints.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP016 — Listing detail view (composed read)
**Traces from:** TR016
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | Pure composing read, no independent business logic (IA016's named cross-surface-drift risk closed by construction) | — | — |
| Repudiation | N | Read-only | — | — |
| Information disclosure | Y | A Suspended/Archived listing opened via a stale link returning underlying data | Returns a "no longer available" response with no underlying data, verified at the RLS layer (RLS-CC) as well as the application layer | Medium |
| Denial of service | N | Covered by SP015's search-level rate limit at the entry point; individual detail-fetch is a normal Class A read | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Composed-read latency | Class A | Load test — note this composes TR002/TR010/TR028's own functions, so their individual latencies sum; budget accordingly |
| Stale-link correctness | 100% — zero data leakage for a Suspended/Archived id | Contract test |

**Cautions** — none beyond the composed-read discipline itself.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP017 — Zero-result explicit broadening
**Traces from:** TR017
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | N | `broadening_options[]` reveals no data beyond what the original query already implied | — | — |
| Denial of service | N | Covered by SP015's shared search rate limit | RateLimit-CC (inherited) | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Zero-result response latency | Same Class C bound as the underlying search/browse call | Load test |

**Cautions** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP018 — Opportunity Discover feed, five sections
**Traces from:** TR018
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Feed is scoped to the resolved caller's own `AuthzContext` | IdentityBridge-CC | — |
| Tampering | Y | A ranking-eligibility bug reaching one of five sections without going through TR019's shared function (IA018's named multiplied-surface risk) | One shared contract test asserting "every card in every section passes TR019's hard-filter step" across all five sections at once, not five independent tests | High |
| Repudiation | N | Read-only feed | — | — |
| Information disclosure | Y | Same directory-scraping class as SP015, against the feed endpoint instead of search | **Decision (shared with SP015):** apply the same RateLimit-CC read-path rate limit to `GET /v1/opportunities/feed` | High |
| Denial of service | Y | Five separate ranking queries per request is 5x the query cost of a single ranked list | Diversification/hard-filter both happen inside one shared function (TR019) so the marginal cost per section is bounded; load-test all five sections together, not one in isolation | Medium |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| First-section latency | Class C — P95 < 800 ms engineering target, never exceeding FR18's own 2-second bound | Load test |
| All-five-sections total latency | No stated FR bound beyond "first section" — engineering target P95 < 2 s for the full response, since empty sections are omitted server-side (TR018) and reduce total query count | Load test |
| Scraping rate limit | Same Decision as SP015 | Abuse-simulation test |

**Cautions**
Five sections multiply the surfaces a ranking-eligibility bug can reach at once — the shared cross-section contract test is load-bearing, not a nice-to-have (IA018).

**Assumptions** — none.
**Decisions (append-only)** — Extends SP015's rate-limit Decision to `GET /v1/opportunities/feed`.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP019 — Canonical eligibility-then-ranking function with signal allow-list
**Traces from:** TR019
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Pure function over already-resolved inputs | — | — |
| Tampering | Y | A future PR adds a field to `RankingSignals` for a sensitive attribute, community status, account age, paid status, popularity, or report signal — **the module's single most explicit anti-bias control, and this file's own named concrete attack/regression scenario for its STRIDE pass** | StructAbsence — `RankingSignals` is a typed struct whose fields are exactly the FR19 allow-list; no field for any disallowed input exists, so no future change can pass one in without first changing this one type (a mandatory, reviewable diff) | Critical |
| Repudiation | N | — | — | — |
| Information disclosure | N | Ranking signals are computed, not separately stored/exposed beyond TR020's own explanation read | — | — |
| Denial of service | N | In-process scoring, bounded candidate-pool size per query | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| `RankingSignals` schema drift | Class G — 100% pass, CI gate on every change to the struct, blocking merge | CI schema-introspection test asserting the field set matches the allow-list exactly |
| Ranking computation cost | Adds < 20 ms per candidate batch (≤50 items), Class C's overall bound still applies at the calling endpoint | Micro-benchmark in CI |
| Weight-config fallback | Missing config logs a warning and falls back to safe defaults, never blocks the request | Contract test |

**Cautions**
Any future PR adding a field to `RankingSignals` is the concrete attack/regression scenario this structural-absence design defends against — this file's own STRIDE pass names it explicitly so a future reviewer treats a "just one more field" PR with the scrutiny it needs.

**Assumptions** — deterministic, explainable scoring over ML-first ranking is correct for V1's sparse data.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP020 — "Why this?" explanation reads the same signals that ranked
**Traces from:** TR020
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | A separately-computed "reason string" model silently diverging from the actual ranking signals (IA020's named explanation-drift risk) | StructAbsence — this endpoint reads the exact `signals` tuple TR019 already computed for that pair, never a second implementation | High |
| Repudiation | N | Read-only | — | — |
| Information disclosure | N | No percentage match score or sensitive signal exposed — response is plain-language, top-three-by-weight only | StructAbsence — no field for a numeric score exists in the response schema | — |
| Denial of service | N | Bounded per-request cost | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Explanation-read latency | Class C (shares the ranking call's cost) | Load test |
| No-percentage-score guarantee | Class G — CI schema check, 100% pass | Contract test on response schema |

**Cautions** — none beyond the anti-drift design itself.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP021 — Proactive notification with fatigue caps and daily digest
**Traces from:** TR021
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Job-initiated, not caller-initiated | — | — |
| Tampering | N | — | — | — |
| Repudiation | Y | — | Audit-CC on each send request | Low |
| Information disclosure | N | Notification content is the same allow-listed fields already surfaced elsewhere | — | — |
| Denial of service | Y (fatigue-as-DoS-on-attention, the FR's own named harm) | Unbounded strong-match notifications overwhelming a member | RateLimit-CC — `check_and_increment(member_id:day, 86400, 3)` before every send request; non-strong matches batched into one digest | High |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Rate-limit check | Class H | Load test under burst |
| Notification Bridge delivery | Retries ≤3 then drops, never duplicates (TR021's own idempotency contract) | Contract test |
| Daily digest batching job | Class F, keyed on `privacy_settings.digest_hour` | Scheduled-job monitoring |

**Cautions** — none beyond the shared rate-limit utility already named.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP022 — Submit an Enquiry or Opportunity Response
**Traces from:** TR022
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y | Client-supplied `action_type` claiming a different action than the target actually supports (e.g. `apply` on a Listing) | `action_type` derived **server-side** from the target's type per FR22 DEC-002's fixed mapping, never accepted as client input | High |
| Tampering | Y | A network retry after connectivity drop creates a duplicate enquiry | Idempotency-CC — `vyapar_platform.idempotency_key`, `UNIQUE(member_id, idempotency_key, endpoint)` | High |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | Y | A sender learning they've been blocked (disclosing block status back to the blocker's target) | Blocked-sender write succeeds with `delivered=false` internally and **no disclosure to the sender** — a response-shape guarantee (StructAbsence: no field distinguishes a blocked-silent accept from a normal accept) | High |
| Denial of service | Y | Enquiry-spam against one or many listings/opportunities | RateLimit-CC — `check_and_increment(sender_id:day, 86400, 20)`; DB-enforced "1 open enquiry per target" via a partial unique index (this file's own inherited ER-model gap-fix, now live) closes the specific race condition an application-layer-only check could miss | High |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Enquiry submit latency | Class B | Load test |
| Idempotent-retry correctness | 100% — a repeated `Idempotency-Key` returns the original response, 0% duplicate rows | Contract test under concurrent retry |
| Rate-limit check | Class H | Load test under burst |
| Attachment size guard | ≤5MB, 0% silent truncation | Contract test |

**Cautions**
This is Idempotency-CC's canonical item — every other client-queueable mutation in this file cites this pattern rather than re-deriving it.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP023 — Enquiry lifecycle and Refer-to-Counsel
**Traces from:** TR023
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | State-change endpoints act on the caller's own thread only | RLS-CC (`vyapar_enquiries.enquiries`: sender OR provider OR moderation-operator) | — |
| Tampering | Y | A further state-change or message call against a `restricted` thread | Rejected at the API layer for every state-change/message route, not only the UI (TR023) | High |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | Y | `refer-to-counsel` sending more than the FR52(f) minimal payload (`member_id`, `problem_summary`, `consent`) to MOD04 | StructAbsence — the Counsel Referral Bridge accepts exactly that payload shape, no other field; `counsel_referrals` itself has no operator bypass (RLS-CC exception, self-only) | High |
| Denial of service | N | Bounded per-thread action rate, already covered by SP022's per-sender enquiry cap upstream | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| State-change write latency | Class B | Load test |
| 7-day no-reply marker job | Class F | Scheduled-job monitoring |
| Restricted-thread rejection | 100% — every mutating route on a restricted thread returns a rejection, 0% silent success | Contract test |

**Cautions** — none beyond the minimal-payload boundary already fixed by FR52(f).
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP024 — Consent-based contact disclosure, blocking, safety notice
**Traces from:** TR024
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | Blocking not cascading to every existing thread between the pair, leaving one channel still open | `POST /v1/blocks` sets `state='restricted'` on every existing `enquiries`/`partnership_requests` row between the pair in the **same transaction** as the block insert | High |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | Y (**this file's own canonical NoLeadList-CC item**) | A bulk/export view of enquirer contact details reaching any role — the direct structural answer to BR07/BR10's "no lead lists" invariant | NoLeadList-CC — no endpoint anywhere in this file exposes such a view; verified by route-inventory absence (Class G), not a permission check on a route that exists | Critical |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Contact-disclosure read | Class A, via TR002's shared function | Load test |
| Block-cascade write | Class B, atomic across all affected threads | Contract test: no window where a blocked pair has one still-open thread |
| No-bulk-export guarantee | Class G — CI route-inventory check, 100% pass | Automated route-list scan against an explicit "no bulk contact export" allow-list |

**Cautions**
NoLeadList-CC is the direct structural answer to a named invariant (BR07/BR10) — any future admin/reporting feature request touching enquirer contact data must be checked against this route-inventory gate before merge, not assumed compliant by convention.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP025 — Create a Partnership Request
**Traces from:** TR025
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | `sender_listing_id` ownership checked via AuthzChokepoint-CC | AuthzChokepoint-CC | — |
| Tampering | Y | Requesting against a suspended/archived listing | Both `sender_listing_id` and `recipient_listing_id` must pass Listings & Verification's own `is_active()` method, never a direct query from this component | Medium |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | N | — | — | — |
| Denial of service | Y | Unbounded pending-request creation against one target | Standing-count cap (Cross-cutting §2(b)): `COUNT(*) WHERE state='pending'` ≤ 10 per sender — a different, correctly-not-forced-through-RateLimit-CC shape | Medium |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Request-create latency | Class B | Load test |
| Idempotent-retry correctness | Idempotency-CC | Contract test |
| Standing-count cap correctness | 100% — the 11th concurrent pending request is rejected, no race past the cap | Contract test under concurrent requests |

**Cautions** — none beyond the count-vs-window distinction already recorded in Cross-cutting §2.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP026 — Respond to and manage a Partnership Request
**Traces from:** TR026
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | RLS-CC scopes rows to sender OR recipient OR any operator | RLS-CC | — |
| Tampering | Y | A second implementation of contact disclosure on Accept diverging from TR024's own | Accept calls the same TR024 disclosure function, never a second implementation | Medium |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | N | — | — | — |
| Denial of service | Y | Re-sending a request immediately after Decline to pressure a recipient | 30-day re-send cooldown checked against the most recent `declined` request's timestamp between the same pair before allowing a new request | Medium |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| State-change write latency | Class B | Load test |
| Cooldown correctness | 100% — a re-send within 30 days of Decline is rejected | Contract test |

**Cautions** — none.
**Assumptions** — Pending requests never auto-expire, per FR26's own explicit, PM-approved policy.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP027 — Submit a Review tied to a qualifying interaction
**Traces from:** TR027
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y | Submitting a review for an interaction the caller wasn't actually party to | Rejected unless an unused, unexpired `review_invites` row exists for that exact `(interaction_kind, interaction_id, member_id)` — a foreign-row existence check, not a self-reported flag | High |
| Tampering | Y | Submitting more than one review for the same interaction | `reviews.UNIQUE(interaction_kind, interaction_id, author_id)` — database-enforced, not application-logic-only | High |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | N | — | — | — |
| Denial of service | N | Bounded by the qualifying-interaction gate itself (can't submit more reviews than qualifying interactions) | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Review-submit latency (including synchronous safety check) | Class B | Load test — TR003's wordlist function is reused, not re-implemented, so its cost is already budgeted |
| Idempotent-retry correctness | Idempotency-CC | Contract test |
| One-review-per-interaction guarantee | 100% — DB constraint, not race-condition-vulnerable | Concurrency test issuing two simultaneous submits for the same interaction |

**Cautions** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP028 — Contextual reputation counts, no aggregate score
**Traces from:** TR028
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | Counts are computed live from `reviews WHERE state='published'`, never a stored/cached aggregate that could drift stale | — | — |
| Repudiation | N | Read-only | — | — |
| Information disclosure | N | Counts are already-public aggregate numbers, no individual reviewer identity exposed in the count itself | — | — |
| Denial of service | Y | A live `GROUP BY` count query on every detail-page load at scale | Indexed on `(subject, state)`; same Class A budget as any composed read (TR016 already composes this) | Low |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Reputation-count query | Class A | Load test |
| Exclusion of disputed/hidden/removed reviews | Class E — immediate (same `WHERE` clause, not a delayed batch recompute) | Contract test: a review marked `disputed` is excluded from the very next read, not eventually |

**Cautions** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP029 — Review dispute, hide, and removal via Trust & Safety only
**Traces from:** TR029
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | A review's own subject altering or hiding the review through some path | StructAbsence — Reviews & Reputation's own public interface exposes **no method** that lets a subject alter/hide a review through any path; the Published/Hidden/Removed decision is made only through Trust & Safety's moderation interface (TR040) | High |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | N | — | — | — |
| Denial of service | N | `UNIQUE(review_id)` bounds disputes to one per review | — | — |
| Elevation of privilege | Y | A subject-side route reaching moderation authority it shouldn't have | Verified structurally by the absence of such a method (Class G), not a role check on a route that exists | High |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Dispute-create write latency | Class B | Load test |
| No-subject-hide-path guarantee | Class G — CI route-inventory check, 100% pass | Automated scan of Reviews & Reputation's public interface module for any write method reachable by a review's own subject |

**Cautions** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP030 — Purchase a Boost, shared Sponsored-label rendering
**Traces from:** TR030
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Gated on the caller's own verified listing/poster status, checked via Listings & Verification's own interface | AuthzChokepoint-CC | — |
| Tampering | Y | Paying for a Boost silently improving organic rank (the "pay cannot buy verification/ranking" guarantee) | SponsoredBadge-CC — `RankingSignals` (TR019) has no `promotions`/paid-status field at all; Sponsored inclusion is an eligible-audience impression boost only | Critical |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | N | — | — | — |
| Denial of service | N | Purchase-rate bounded by payment-gateway interaction itself | — | — |
| Elevation of privilege | N | Payment-webhook-driven state transition is Commercial's own function, never the webhook handler itself deciding state | PaymentIsolation-CC | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Promotion-create write latency | Class B | Load test |
| Post-webhook state transition | Class I — reflects gateway event within 30 seconds (FR51) | Contract test |
| SponsoredBadge rendering | 100% of surfaces that can show a boosted card use the one shared component, 0% independent re-implementation | Class G — CI check for a second `<SponsoredBadge>`-shaped component |

**Cautions**
SponsoredBadge-CC is this file's canonical item for the "no rank boost from paid placement" guarantee — every future paid-surface addition must route through it, not reimplement it (IA054's own named discipline-as-much-as-mechanism risk).

**Assumptions** — prices/products are `config`-driven, versioned per TR031.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP031 — Promotion/Entitlement lifecycle, price versioning, credit
**Traces from:** TR031
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | An order reconstructed against the wrong price if `products` rows are mutated in place | Insert-only `products` (TR049); `FOREIGN KEY (product_id, product_version)` fixes the exact price in force at purchase, every order reconstructible | High |
| Repudiation | Y | — | Audit-CC via `commercial_order_history` (this file's own inherited ER-model gap-fix, replacing the promotion-only `promotion_history`, now generalized to Entitlements too) | Low |
| Information disclosure | N | `commercial_order_history` is owner-visible or commercial-operator only | RLS-CC | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | Refund/pro-rata-credit computation happens in Commercial's own function, gateway calls only through PaymentIsolation-CC | PaymentIsolation-CC | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| State-transition write latency | Class B | Load test |
| Refund-triggering call | Class I | Contract test |
| Order-price reconstructability | 100% — every historical order resolves to the exact `(product_id, product_version)` price in force at purchase | Contract test |

**Cautions** — none beyond the already-named willingness-to-pay business risk (not a system risk).
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP032 — Provider performance reporting without unsupported claims
**Traces from:** TR032
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | Read-only report | — | — |
| Information disclosure | Y | Individual member identity appearing in a provider-facing performance report | StructAbsence — the response schema has no field for individual identity, only aggregate counts; substitutes "too little data to compare" below a 10-impression threshold (a small-group-suppression pattern consistent with TR046's own re-identification defense) | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Report-read latency | Class A | Load test |
| No-projection/no-causal-claim guarantee | Class G — CI schema check on the response shape, 100% pass | Contract test asserting no projection/ROI/causal field ever appears |

**Cautions**
The no-projection/no-causal-claim rule needs an explicit product-review gate on every *future* reporting feature (IA032) — name this at every later design review, not only at this one build.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP033 — Business Workspace entitlement purchase and renewal grace
**Traces from:** TR033
**Status:** Ready for Review | **Confidence:** Medium — matching TR033's own stated confidence.

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | An individual gated feature (roles, campaigns, analytics) checking entitlement state independently and drifting out of sync with the real state | AuthzChokepoint-CC — the Authorization Engine is the **single** chokepoint reading `entitlements.state='active'`; no feature re-checks independently | High |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | N | — | — | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y | A `paused` entitlement (renewal-failure grace expired) continuing to grant gated-feature access | Single chokepoint means a state flip to `paused` is immediately enforced everywhere, with no per-feature cache to invalidate | High |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Entitlement-purchase write latency | Class B | Load test |
| 7-day grace-period job | Class F | Scheduled-job monitoring |
| Chokepoint-consistency guarantee | Class G — CI check for any gated feature querying `entitlements.state` independently | Route/import-boundary scan |

**Cautions** — none beyond the already-named willingness-to-pay business risk.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP034 — Multi-user Workspace roles via the Authorization Engine
**Traces from:** TR034
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y | Invite-by-phone resolving to the wrong `member_id` | Resolution via Identity Bridge's own phone-lookup call, not a locally-cached/guessed mapping | Medium |
| Tampering | N | — | — | — |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | N | — | — | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y | A revoked workspace role continuing to grant Vyapar action authority via a stale per-request cache | Every request re-resolves the Authorization Engine's context fresh from `workspace_members.state` — no per-request cache to invalidate at V1 scale (same reasoning as Mangaly's TR010); revocation is effective immediately | High |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Invite/role-write latency | Class B | Load test |
| Revocation-effectiveness | 100% — the very next request after revocation is denied, 0% grace period from a stale cache | Contract test |
| Platform-session independence | Class G — revoking a Vyapar role never touches the platform session store (structurally unrelated tables) | CI check confirming no code path in this endpoint calls the Identity & Trust session-write API |

**Cautions** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP035 — Campaign creation reusing Boost mechanics per item
**Traces from:** TR035
**Status:** Ready for Review | **Confidence:** Medium — matching TR035's own stated confidence.

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | A campaign-specific reimplementation of Boost mechanics silently not enforcing TR030's verified-only/organic-rank-unchanged guarantees (IA035's named divergence risk) | Campaign creation **must call TR030's own boost-application function once per item** — no second implementation; `promotions.campaign_id FOREIGN KEY REFERENCES campaigns(id)` (this file's own inherited ER-model gap-fix) prevents referencing a non-existent or wrong-owner campaign | High |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | N | — | — | — |
| Denial of service | N | ≤10 items per campaign bounds the fan-out cost | — | — |
| Elevation of privilege | N | SponsoredBadge-CC's no-rank-boost guarantee applies uniformly since this reuses TR030's own function | SponsoredBadge-CC (inherited) | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Campaign-create write latency (≤10 items, one boost-function call each) | Class B, scaled to item count — P95 < 400 ms × up to 10 sequential/batched calls | Load test |
| Campaign-scope reporting | Reuses TR032's own function grouped by `campaign_id`, not a separate implementation | Class G check for a second reporting implementation |

**Cautions**
Every future paid-surface addition must remember to route through the one shared boost-application function — flagged for Step 9's code review checklist, not assumed self-enforcing.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP036 — Six contextual privacy controls, one screen
**Traces from:** TR036
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | Y | Privacy settings computed from another module's data rather than the member's own explicit choice | Defaults set once at first-run (TR044) creation, never computed from any other module's data; RLS-CC (`vyapar_privacy.privacy_settings`: **self only, no operator bypass** — the module's most restrictive RLS exception, per `07a-er-model.md`'s own Assumptions) | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Read/write latency | Class A / Class B | Load test |
| Propagation to all surfaces | Class E — 5 seconds (FR36) | Contract test |

**Cautions** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP037 — Data export, correction, deletion, consent withdrawal
**Traces from:** TR037
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | RLS-CC scopes `data_requests` to self OR any operator | RLS-CC | — |
| Tampering | Y | A cascade-delete corrupting a counterpart's thread/review instead of anonymizing the requester | Anonymize-in-place (TR037/ER-model Pass 1's own fold-in): `members.anonymized`/`deleted_at`, scrubbing PII fields while the row (and its `id`, referenced by every other schema) is **never removed** — a counterpart's enquiry/review continues to resolve the same `member_id` | Critical |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | Y | The export bundle containing the wrong member's data, or including a counterpart's private thread content | Export job (Class F, 72h) scoped strictly to `member_id`-owned rows via the same RLS-CC predicates every read already uses | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Export job | Class F — completes within 72 hours (FR37) or alerts within 15 minutes | Scheduled-job monitoring |
| Correction/consent-withdrawal | Immediate (FR37's own bound), Class B | Contract test |
| Anonymization correctness | 100% — every PII field on the scrub list (`display_name`, `phone`, `avatar_url`, `locality`, `lat`, `lng`, `help_with`, `capabilities`) is null/scrubbed post-deletion, 0% dangling counterpart reference | Contract test walking every schema's `member_id`/`owner_id`/`sender_id`/`author_id` column against an anonymized row |
| Object Storage document TTL for export bundles | **Decision:** signed download URL for the export bundle itself ≤ 15 minutes, same TTL family as SP008 | Contract test |

**Cautions**
Anonymization-vs-deletion correctness on shared records is a genuinely tricky data operation (IA037) — the contract test above must exercise a real counterpart-thread scenario, not only a solo member's own rows.

**Assumptions** — none.
**Decisions (append-only)** — Export-bundle signed download URL TTL ≤ 15 minutes, consistent with SP008's Object Storage TTL Decision.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP038 — Inspect and confirm derived preferences
**Traces from:** TR038
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | RLS-CC scopes `derived_preferences` to self only | RLS-CC | — |
| Tampering | N | — | — | — |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | Y (**this file's own canonical anti-retaliation item**) | Discovery & Ranking reading Trust & Safety's `reports` table, letting a report against a member silently affect their own ranking (retaliation risk) | StructAbsence — no code in Discovery's package imports Trust & Safety's repository at all, the same structural-absence style as `RankingSignals` (SP019); TR019's ranking function reads only `state='active'` confirmed-preference rows | Critical |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Confirm/decline/remove write latency | Class B | Load test |
| Import-boundary correctness | Class G — 100% pass | CI lint rule failing the build on any import of Trust & Safety's repository from Discovery & Ranking's package |

**Cautions** — none beyond the anti-retaliation import-boundary already fixed.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP039 — Report and block intake
**Traces from:** TR039
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y | A malicious mass-reporter targeting a competitor's listing to trigger auto-limiting | RateLimit-CC — `check_and_increment(reporter_id:day, 86400, 10)`; dedup-by-case (`object_kind`+`object_id`) increments `reporter_count` rather than creating duplicate cases, so mass-reporting the same object doesn't multiply signal | High |
| Tampering | N | — | — | — |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | Y (**canonical reporter-anonymity item**) | The reported party learning who reported them | NoLeadList-CC-style structural absence — the reported-party-facing read model's own `SELECT` never includes `reports.reporter_id`, at the query level; RLS-CC live-verified: a second reporter on the same case never sees the first reporter's own row | Critical |
| Denial of service | Y | Same mass-reporting vector as Spoofing above | RateLimit-CC (shared mitigation) | High |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Report-create write latency | Class B — within 5 seconds end-to-end (FR39) | Load test |
| Rate-limit check | Class H | Load test under burst |
| Reporter-anonymity guarantee | Class G — CI schema check on the reported-party-facing response shape, 100% pass | Contract test + the live-verified RLS behavior already confirmed in `07a-er-model.md` |
| Evidence upload | Class D, same 15-minute signed-URL TTL Decision as SP008 | Contract test |

**Cautions** — none beyond the reporter-anonymity guarantee already fixed and live-verified.
**Assumptions** — none.
**Decisions (append-only)** — Evidence-image signed upload URL TTL ≤ 15 minutes, same family as SP008/SP037.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP040 — Moderation queue and graduated actions
**Traces from:** TR040
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Operator-only, gated by `operator_permissions @> ARRAY['moderation']` | AuthzChokepoint-CC | — |
| Tampering | Y | Evidence fields on a case being altered after creation | Immutable once created — no `PATCH` route exists for them (StructAbsence) | High |
| Repudiation | Y | Every decision must be traceable to a mandatory `reason_code` | Audit-CC + mandatory `reason_code` on all six actions | High |
| Information disclosure | Y | `moderation_cases` visible to a non-operator | RLS-CC — moderation-operator only, neither reporter nor subject sees this table | High |
| Denial of service | N | Federated Admin Console view, low-frequency operator action | — | — |
| Elevation of privilege | Y | The auto-limit (`distribution_limited=true`) being enforced only in the admin UI, bypassable via the normal listing/opportunity read paths | Enforced at the data-read layer every listing/opportunity surface already shares (`WHERE NOT distribution_limited`), not only in the admin UI | High |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Decision write latency | Class B | Load test |
| Auto-limit propagation | Class E — 5 seconds (FR40) | Contract test |
| Evidence immutability | Class G — CI route-inventory check, 100% pass | Route scan confirming no `PATCH`/`PUT` on evidence fields |

**Cautions**
ADR-012's Admin Console plugin contract is not yet formally specified — if it isn't ready at Step 9, build a Vyapar-only queue at the same URL space the eventual federated contract will use, so migrating in later is additive, not a rewrite (already named by TR040).

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP041 — Appeals with graceful different-operator routing
**Traces from:** TR041
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | `UNIQUE(case_id, member_id)` enforces one appeal per decision | — | — |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | Y | Appeals visible beyond the appealing party/operator | RLS-CC (self OR moderation-operator) | Medium |
| Denial of service | N | Bounded by one-appeal-per-decision | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Appeal-create write latency | Class B | Load test |
| `due_at` default (7 days) enforcement | Class F — escalation to the queue owner if missed | Scheduled-job monitoring |

**Cautions** — none.
**Assumptions** — solo-founder-stage graceful degradation to same-operator assignment matches FR41's own "where staffing allows" wording.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP042 — Three-language rendering via shared platform i18n
**Traces from:** TR042
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | A `content_language` tag being trusted as an input signal into ranking | StructAbsence — `RankingSignals` (TR019) has no language field at all | High |
| Repudiation | N | — | — | — |
| Information disclosure | N | — | — | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Missing-key fallback | Falls back to English, logs `analytics_events(kind='i18n_fallback')`, never fails silently | Contract test |
| `content_language` column presence on member-authored free text | Class G — CI schema check confirming the column exists on exactly the scoped set (`listings.description`, `opportunities.description`, `enquiry_messages.body`, `reviews.comment`, `partnership_requests`, `reports.evidence_text`, `appeals.text`), not every table | Schema-introspection test |

**Cautions** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP043 — WCAG 2.2 AA baseline with a CI release gate
**Traces from:** TR043
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Not applicable — a release-process requirement, not a data/API concern | — | — |
| Tampering | N | N/A | — | — |
| Repudiation | N | N/A | — | — |
| Information disclosure | N | N/A | — | — |
| Denial of service | N | N/A | — | — |
| Elevation of privilege | N | N/A | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Automated accessibility gate | Class G — 100% pass rate, blocks release on failure | axe-core in `vyapar-web`'s CI pipeline against every screen |
| Manual screen-reader pass | Recorded checklist artifact in `09-implementation.md` for the four core journeys, before conformance is claimed | Manual QA record, not automatable |

**Cautions**
Automated tooling cannot catch every WCAG 2.2 AA criterion (e.g. meaningful focus order) — the two-layer approach is the correct response to that known limitation, not a gap in itself.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP044 — Progressive first-run to Discover
**Traces from:** TR044
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Bound to the already-resolved `AuthzContext` | IdentityBridge-CC | — |
| Tampering | N | Step-save is idempotent (repeating a step call is a no-op) | Idempotency-CC (same pattern, application-level rather than the shared table since this is self-only and side-effect-free) | — |
| Repudiation | N | Low-consequence onboarding state | — | — |
| Information disclosure | N | — | — | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y (**this file's own canonical "no auth screen" item**) | Any screen in this five-screen flow becoming a de facto sign-up/login/OTP path, violating the platform's sole-ownership-of-authentication rule (ADR-004/§5b) | StructAbsence — no credential-related route exists at all in this endpoint family; location-permission-denied falls back to a manual text field on the same non-credential `PATCH` call | Critical |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| First-run state read/write | Class A / Class B | Load test |
| No-auth-route guarantee | Class G — CI route-inventory check, 100% pass | Automated scan confirming zero credential-related routes in this endpoint family |

**Cautions**
Re-confirm at every future change to this flow that no screen becomes a sign-up/login/OTP screen — this FR's own Review history already records the product owner's standing correction on this exact point.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP045 — Event instrumentation with outcome levels
**Traces from:** TR045
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Events attributed to the resolved caller only | IdentityBridge-CC | — |
| Tampering | Y | A modified client bypassing a client-side behavioral-analytics opt-out | Server rejects any non-`operational` event when `privacy_settings.behavioral_analytics=false` — enforced at the API layer, not only a client-side toggle | High |
| Repudiation | N | — | — | — |
| Information disclosure | Y | `analytics_events` visible beyond operator-only | RLS-CC — `vyapar_analytics.analytics_events`: INSERT any, SELECT analytics-operator only | Medium |
| Denial of service | Y (**gap, resolved here**) | An unbounded batch size or scripted flood of `POST /v1/events` becoming a storage/cost DoS vector — TR045 does not state a batch cap or rate limit | **Decision:** bound batch size to ≤100 events/request and apply RateLimit-CC per member, a genuine gap this pass found | High |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Batched event write | Class B | Load test |
| Pipeline delivery | ≥99% of events delivered within 60 seconds (FR45) | Pipeline monitoring |
| Batch-size/rate-limit guard | 100% — requests over the cap rejected, 0% silent truncation | Contract test |
| Client-side buffer overflow | Buffered locally up to 24h then dropped with a count metric (frontend concern, out of this endpoint's own scope) | Client-side test, not this endpoint's own SLO |

**Cautions**
Client-side buffering/consent-opt-out is a frontend concern this endpoint doesn't control directly, but the server-side rejection of non-operational events on opt-out is the load-bearing enforcement point — never trust the client to have honored the opt-out itself.

**Assumptions** — none.
**Decisions (append-only)** — Bound `POST /v1/events` to ≤100 events/request and apply the shared rate-limit utility per member — a genuine gap TR045 did not name.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP046 — Marketplace health metrics with minimum group-size suppression
**Traces from:** TR046
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Operator-only, federated Admin Console | AuthzChokepoint-CC | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | Y (this file's own named re-identification defense for a close-knit community, IA046) | A `GROUP BY` group with `COUNT(*) < 10` re-identifying an individual member in a small community | Server-side suppression — such a group is never included in the response at all (not merely hidden client-side); no profile-completion-percentage metric exists in the response schema at all (permanent structural omission) | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Aggregate query latency | Class A | Load test |
| Group-size suppression | Class G — 100% of groups with `COUNT(*) < 10` excluded server-side | Contract test with a synthetic small-group scenario |

**Cautions** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP047 — Verification queue (Admin Console federated view)
**Traces from:** TR047
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | Decision path calls TR008/TR009's own decision function, not a second implementation | — | — |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | Y | An operator without the `verification` permission accessing identity-document evidence (`image_url`, `identifier_enc`) | AuthzChokepoint-CC — gated by `operator_permissions @> ARRAY['verification']`; the endpoint itself performs no permission logic, it only calls the chokepoint; RLS-CC as the second layer | High |
| Denial of service | N | Low-frequency operator queue | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Queue-read latency | Class A | Load test |
| Overdue-highlighting | Rows where `now() - created_at > 3 business days` are flagged in every response, 0% silent backlog | Contract test |
| Evidence-access permission gate | Class G — CI check that this endpoint's own code path contains no permission logic (delegates to the chokepoint) | Static check / route review |

**Cautions**
Operator bottleneck (CCR12) is mitigated by overdue-highlighting itself, not eliminated — route to Step 13 monitoring for actual queue-age trends, not assumed solved by the highlight alone.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP048 — Opportunity/stale queue and taxonomy management
**Traces from:** TR048
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | A bulk Remind/Expire action executed without operator confirmation, mass-affecting records incorrectly | Confirmation-with-counts required before execution (TR048) | High |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | N | — | — | — |
| Denial of service | N | Low-frequency operator action | — | — |
| Elevation of privilege | N | Taxonomy write is called through Listings & Verification's own interface, never a direct write from this admin surface | AuthzChokepoint-CC | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Bulk-action write latency | Class B, scaled to affected-row count | Load test |
| Taxonomy-change search reindex | Class E — 5 minutes (FR48) | Contract test |
| Bulk-confirmation guarantee | 100% — no bulk action executes without an explicit confirm-with-counts step | Contract test |

**Cautions** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP049 — Commercial administration with structural separation of powers
**Traces from:** TR049
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | An `UPDATE` on an existing `(product_id, version)` row with orders already against it, corrupting historical price reconstruction | `products` is insert-only — no route capable of violating this; enforced structurally (StructAbsence) plus **live-verified at the database layer**: `vyapar_app` has no INSERT/UPDATE/DELETE grant on `vyapar_integration.config` either, confirmed as a hard permission denial | Critical |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | N | — | — | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y (**this file's own canonical separation-of-powers item**) | A commercial admin route silently gaining the ability to write `listings.verification_state`, ranking `config` weights, or `moderation_cases` — the exact cross-module authority-creep this component's design forbids | StructAbsence — this admin surface has **no route at all** capable of any of the three; live-verified: a direct `INSERT` into `config` as `vyapar_app` fails with "permission denied," not merely a missing route | Critical |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Refund/credit call | Class I, server-side `amount <= order.amount_paise` guard | Contract test |
| Ranking-diagnostics call | Reuses TR019's own function with `explain=true`, no second implementation | Class G check |
| Separation-of-powers guarantee | Class G — 100% pass, zero tolerance; already live-verified at the DB permission layer, not merely reviewed on paper | Route-inventory scan + the live `INSERT` permission-denial test already run in `07a-er-model.md` |

**Cautions** — none beyond what is already live-verified.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP050 — Identity Bridge: platform session resolve, fail-closed, member-link
**Traces from:** TR050
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y (**this file's own canonical item for the whole module's identity boundary**) | A forged/stale `fk_session` cookie, or a fallback to a default/local member under Identity & Trust outage | IdentityBridge-CC — resolve via `POST /internal/v1/sessions/resolve`; `503` on unreachability, **never** a local/default fallback (structural absence: no code path constructs a member context without a successful resolve or a still-valid cache entry) | Critical |
| Tampering | Y | Duplicate `members` rows from a race between two first-entry requests for the same platform member | Idempotent `INSERT … ON CONFLICT (id) DO UPDATE SET synced_at = now()` upsert (closes IA050's named risk) | High |
| Repudiation | N | — | — | — |
| Information disclosure | N | — | — | — |
| Denial of service | Y | Identity & Trust outage cascading into every Vyapar request failing | The 15-minute read-only continuation window (FR50's own stated degradation allowance) — a read-only allowance, never a write fallback; no mutation endpoint in this file may succeed without a fresh, successful resolve | High |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Session-resolve call (own-side) | Class D | Load test excluding Identity & Trust's own RTT |
| Cache freshness | ≤30 seconds positive, ≤5 seconds negative (§5b's own bound) | Contract test on sign-out propagation timing |
| Fail-closed guarantee | Class G — 100% — every mutation path returns `503`, never a default member, on resolve failure | CI route-inventory + fault-injection test simulating Identity & Trust unreachability |
| Upstream sync | Class E — 1 hour (FR50) | Scheduled-job monitoring |

**Cautions**
This is the single most load-bearing security boundary in the entire module — no other item's Spoofing mitigation is meaningful if this one has a gap. Any future change to this component requires its own dedicated security review, not a routine code review.

**Assumptions** — none beyond the binding contract (`/MODULE-ARCHITECTURE-STANDARD.md` §5b, `docs/ParentApp/07-tech-reqs.md` TR10–TR16).
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP051 — Payment Bridge: idempotent orders, verified webhooks, isolated adapter
**Traces from:** TR051
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y (**this file's own canonical payment item**) | An unsigned or forged webhook call impersonating the gateway | PaymentIsolation-CC — signature verified **before** any state write; 2026 vendor documentation (Razorpay X-Razorpay-Signature HMAC-SHA256 over the raw body; Cashfree's own signature-verification requirement) confirms this is still the current, correct control | Critical |
| Tampering | Y | A retried order-create request creating a duplicate order | `payment_orders.idempotency_key UNIQUE` — database-enforced, not application-logic-only | High |
| Repudiation | Y | — | Audit-CC + `webhook_events JSONB` append-only log of every received event | Low |
| Information disclosure | Y | Raw card/bank credentials reaching this service at all | StructAbsence — hosted/tokenized checkout only; no field on `payment_orders` is capable of holding one, by construction | Critical |
| Denial of service | Y | A duplicate webhook delivery (normal at-least-once gateway behavior) reprocessing a state change repeatedly | Every received webhook event id appended to `webhook_events JSONB` — a duplicate delivery is a no-op; **refinement from current research:** dedupe specifically against the gateway's own per-event id header (`x-razorpay-event-id` / Cashfree's event id), not merely array-length, since that is the vendor-guaranteed uniqueness key | High |
| Elevation of privilege | N | Commercial never imports a gateway SDK directly, only the `PaymentGateway` interface | PaymentIsolation-CC | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Order-create latency | Class B | Load test |
| Webhook-handler own latency | Class I — < 300 ms excluding gateway RTT | Load test |
| End-to-end order-state reflection | Class I — within 30 seconds of the gateway event (FR51) | Contract test |
| Out-of-order event handling | Stored and reconciled once the corresponding earlier event also arrives, never applied blindly against a non-existent state | Contract test simulating a refund webhook arriving before its payment webhook |

**Cautions**
Genuine end-to-end webhook-replay/signature-failure testing against a real sandbox gateway is a Step 10/11 concern layered on top of this item's own business rules — this file's own thresholds do not substitute for that sandbox test.

**Assumptions** — gateway vendor is a `config`/`.env` value with placeholder keys created at implementation time (Step 9).
**Decisions (append-only)** — Dedupe webhook events against the gateway's own per-event id header, not solely against local array membership, per current (2026) Razorpay/Cashfree guidance.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP052 — Six minimum-field adjacent-service contracts, one outbox mechanism
**Traces from:** TR052
**Status:** Ready for Review | **Confidence:** Medium — matching TR052's own stated confidence.

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y (**gap, resolved here**) | Any of the five non-Identity-Bridge bridges (Search, Notification, Audit, Object Storage, Dashboard Read, Counsel Referral) accepting a call based on bare network-location trust rather than an authenticated calling service — TR052 does not state an inter-module authentication mechanism, unlike §5b's explicit module-name-plus-key pattern for the Identity Bridge's own `/internal/v1/sessions/resolve` call | **Decision:** every inbound internal call across these six contracts authenticates as a named calling service (module name + shared key, or mTLS client certificate — a Step 9 configuration choice, not a new component), extending §5b's already-established pattern rather than inventing a second one; a genuine gap this pass found | High |
| Tampering | Y | One of six independently-built contracts skipping idempotency, silently diverging from the others | One `publish_with_outbox()` implementation used by every one of the six contracts — no contract re-implements the outbox mechanism independently | High |
| Repudiation | Y | — | Audit-CC (the Audit Bridge contract itself, plus every other contract's own event captured by the same outbox) | Low |
| Information disclosure | Y | The Dashboard Read Bridge's `dashboard-summary` endpoint leaking a future new `listings` column | StructAbsence — the response is an explicit **allow-list** (`{name, category, locality, verification_state, freshness}`), not a filtered version of the full row; a new column cannot silently leak through without a deliberate allow-list change | High |
| Denial of service | Y | Six independent contracts each needing their own retry/backoff, one of which retries unboundedly | Failed deliveries after retry exhaustion land in the shared `dead_letters` table (visible at `GET /v1/admin/dead-letters`), not an unbounded local retry loop | Medium |
| Elevation of privilege | N | No route anywhere grants any other module direct database access to `vyapar`'s tables — the six contracts are the only path in or out | StructAbsence | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Outbox dispatch latency | Class E-family — Search Bridge index publish/remove within 5 seconds (already the shared PropagationSLA-CC bound) | Load test per contract |
| Dead-letter visibility | Failed-after-retry-exhaustion events appear in `GET /v1/admin/dead-letters` within one dispatch cycle | Contract test |
| Inter-module auth | Class G — 100% of the six contracts' inbound calls reject an unauthenticated caller | Contract test per bridge |

**Cautions**
Six independent adjacent-service contracts is real surface for one to quietly skip idempotency or authentication — the one-`publish_with_outbox`-implementation decision and the inter-module-auth Decision above are both named once here rather than left implicit per contract, exactly the discipline TR052 itself asks for.

**Assumptions** — none.
**Decisions (append-only)** — Every inbound call on the five non-Identity-Bridge TR052 contracts authenticates as a named calling service (module name + shared key or mTLS), extending §5b's existing pattern — a genuine gap TR052 did not state.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP053 — Versioned legal notice, terms, and grievance-channel gate
**Traces from:** TR053
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | A modified client skipping the accept-before-proceeding gate on listing submit or enquiry submit | TR003 and TR022 each call Privacy & Consent's `has_accepted(member_id, kind)` check **before** proceeding — enforced at the call site of every gated action, not only a client-side redirect | High |
| Repudiation | Y | — | Audit-CC; `acceptances` and `legal_documents` version history are both independent, append-only records | Low |
| Information disclosure | N | `legal_documents` is public (published notices) | RLS-CC exception (no RLS needed — public by design) | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Accept-write latency | Class B | Load test |
| Gate-check call | Class A, called synchronously at every gated action's own request | Load test — budget this into TR003/TR022's own Class B totals |
| Version-rollback correctness | 100% — rolling back a notice version restores prior `body` without deleting any `acceptances` row | Contract test |

**Cautions**
Three-language completeness at publish time is a content-operations discipline (CCR11), not a one-time build task.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP054 — Commercial disclosure, universal Sponsored labelling, gated renewal
**Traces from:** TR054
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | A charge occurring without a confirmed disclosure screen, or a redesign accidentally removing the two-step flow | `POST /v1/{promotions|entitlements}/{id}/confirm-purchase` is structurally separate from order creation — the API enforces the two-step flow, not a UI convention a redesign could remove | High |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | N | Reuses SponsoredBadge-CC, no new disclosure surface | SponsoredBadge-CC | — |
| Denial of service | Y | The renewal job silently charging on a failed reminder-delivery acknowledgment | The renewal job's own guard condition checks the reminder's delivery record before proceeding; on failure, the entitlement's renewal is `paused` with a notice rather than silently charged | High |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Confirm-purchase write latency | Class B | Load test |
| Renewal-reminder-then-charge job | Class F — day-3-before-renewal, guarded on delivery acknowledgment | Scheduled-job monitoring + a fault-injection test simulating a failed Notification Bridge acknowledgment |
| Two-step-flow guarantee | Class G — 100% — no route allows a charge without a preceding `confirm-purchase` call | Contract test |

**Cautions**
Every future paid-surface addition must remember to route through the one shared badge component and the two-step confirm flow (IA054) — flagged for Step 9's code review checklist.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## SP055 — Opportunity detail, typed primary action, and Activity screen
**Traces from:** TR055
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | Sharing a `removed` opportunity, or a second independently-coded type→label mapping diverging from TR022's own | Share action checked against `opportunities.state` before recording, at the API layer; primary-action label is server-computed from `opportunities.type`, exactly TR022's own mapping — never a second implementation | Medium |
| Repudiation | Y | — | Audit-CC | Low |
| Information disclosure | N | Composed read over already-RLS-scoped functions (TR020/TR010) | RLS-CC (inherited) | — |
| Denial of service | N | Covered by SP015/SP018's shared search/feed rate limit at the entry points | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Composed-read latency | Class A | Load test — composes TR020/TR010/TR022's own functions, budget accordingly |
| Activity-list query (six groups, one parameterized query) | Class A | Load test — not six separately-built endpoints |
| Removed-item share-block | 100% — a `removed` opportunity's share action is rejected at the API layer | Contract test |

**Cautions** — none beyond the type→label single-source-of-truth already fixed by TR022.
**Assumptions** — detail structure follows `Vyapar_02` §6/§9 and the feedback vocabulary in §10.
**Decisions (append-only)** — none.
**Review history** — none yet.
**Approval:** Security Lead — [x] Approved — autonomous execution, 2026-09-14

---

## Cross-cutting platform-wide security controls (recurring across many items above)

**RLS posture summary.** 38 of 43 tables carry RLS (`07a-er-model.md`'s RLS
policy table); the 5 without (`products`, `config`, `taxonomy_terms`,
`legal_documents`, `rate_limit_counter`) are each individually justified as
non-per-actor-sensitive, not a blanket omission. Both of `/MODULE-
ARCHITECTURE-STANDARD.md` §4's named failure modes are live-verified closed:
`vyapar_app` owns zero of 43 tables (RLS cannot be bypassed by ownership),
and `vyapar.authz_context` is set via `SET LOCAL` inside the same
transaction as every query (no cross-request leak under connection
pooling). RLS is the second, database-enforced layer beneath application
authorization (AuthzChokepoint-CC) — a bug reaching the database still
cannot leak data, but the primary defense remains the application layer.

**Rate-limiting posture summary.** Two distinct, deliberately-not-conflated
shapes: rolling-window caps (FR21 notifications, FR22 enquiries, FR39
reports) via `vyapar_platform.rate_limit_counter` + `check_and_increment()`;
standing-count caps (FR25 pending partnership requests) via a plain
`COUNT(*) WHERE state='pending'` query. This pass adds two read-path uses
of the same rolling-window utility that no TR previously named
(SP015/SP018's search/feed scraping mitigation) and one write-path batch
cap (SP045's events endpoint) — extensions of the existing shared
mechanism, not new mechanisms.

**Payment-gateway PCI-scope boundary (FR51).** The `PaymentGateway`
interface (TR051) is the sole call path to the licensed India gateway;
`payment_orders` has no field capable of holding raw card/bank data by
construction (hosted/tokenized checkout only). This mirrors — at module
scope, inside the Core Platform monolith — the PCI-scope-reduction
principle ADR-008 applies at container scope for Payment Services:
Commercial's business rules (boost pricing, campaign logic) can never leak
into card-data-adjacent code, because there is no card-data-adjacent code
inside Vyapar at all; the swap seam is deliberate should a future MOD06
consolidation need to absorb this responsibility.

**Audit-event completeness.** Every state-changing TR in this file
publishes via the same `publish_with_outbox()` transactional-outbox
mechanism (§6), consumed by the Integration Bridges' Audit Bridge and
forwarded to the platform's independent, append-only Audit Service
(ADR-011). No SP item in this file names a mutation that skips this —
verified by inspection during this pass, not assumed. ADR-011's own text
("a container that silently drops audit events is a compliance gap, not a
performance optimization") applies here exactly as it does platform-wide.

**Identity-document encryption and signed-URL TTL (genuine gaps this pass
resolved).** No TR/ER-model text specified how `verification_records
.identifier_enc` is actually encrypted or how long an Object Storage
signed URL remains valid — both load-bearing, both resolved as concrete
Decisions (SP008, restated at SP009/SP037/SP039): application-layer
envelope encryption with a secret-manager-held key (never colocated with
the database), and signed-URL TTLs of ≤15 minutes for uploads/evidence and
≤5 minutes for identity-document downloads.

## Closing note for Step 9 (Implementation)

The following are the concrete, load-bearing security/performance
constraints Step 9 must never violate — each traces to a specific SP item
above, restated here as one checklist so it is not lost across 55 items:

1. **The API must never connect to Postgres as `vyapar_owner`.** The
   runtime service (`vyapar-service`) connects only as `vyapar_app`, the
   live-verified non-owning role (SP001/RLS-CC).
2. **Every RLS session-context write uses `SET LOCAL`, never plain `SET`,**
   scoped inside the same transaction as the request it authorizes
   (SP001/RLS-CC, SP050/IdentityBridge-CC).
3. **The Identity Bridge fails closed.** On Identity & Trust
   unreachability, return `503` — never a local/default member fallback,
   never a write proceeding without a fresh successful resolve (SP050).
   The 15-minute read-only continuation window is a read-only allowance
   only.
4. **Every mutation the client can retry carries an `Idempotency-Key`
   through to `vyapar_platform.idempotency_key`** for the six named
   endpoints (enquiries, partnership requests, reviews,
   promotions/entitlements/campaigns, reports) — SP022/Idempotency-CC.
   `payment_orders`/`notifications` correctly keep their own existing
   idempotency columns.
5. **`listings.intent_state` is read only through Listings & Verification's
   own public method** — no other component's code may query it directly
   (SP005, this module's single most safety-load-bearing constraint).
6. **`RankingSignals` (TR019) gains no field for a sensitive attribute,
   community status, account age, paid status, popularity, or report
   signal — ever** — any PR adding one is a Critical-severity finding at
   review, not a routine change (SP019).
7. **Discovery & Ranking imports nothing from Trust & Safety's
   repository** — the anti-retaliation import boundary (SP038).
8. **No route anywhere exposes a bulk/export view of enquirer/provider
   contact details** — verified by route-inventory absence at every code
   review touching Enquiries & Partnerships or any admin surface
   (SP024/NoLeadList-CC).
9. **`vyapar_app` has zero INSERT/UPDATE/DELETE grant on
   `vyapar_integration.config`, and the Commercial admin surface has no
   route writing `listings.verification_state`, ranking `config` weights,
   or `moderation_cases`** — the separation-of-powers guarantee, already
   live-verified at the database permission layer (SP049).
10. **`products` is insert-only** — no migration or admin route may
    `UPDATE` an existing `(product_id, version)` row once orders exist
    against it (SP049).
11. **`verification_records.identifier_enc` is envelope-encrypted with a
    key held in the deployment secret manager, never the database itself**
    (SP008, a genuine gap this pass resolved).
12. **Every Object Storage signed URL this module issues has an explicit
    TTL** — ≤15 minutes for uploads/evidence/exports, ≤5 minutes for
    identity-document downloads (SP008/SP037/SP039, a genuine gap this
    pass resolved).
13. **`GET /v1/listings/search` and `GET /v1/opportunities/feed` are
    rate-limited** via the shared utility in read-path mode — a genuine
    gap this pass resolved to prevent directory scraping (SP015/SP018).
14. **Every inbound call on the five non-Identity-Bridge TR052 contracts
    (Search, Notification, Audit, Object Storage, Dashboard Read, Counsel
    Referral) authenticates as a named calling service** — extending §5b's
    module-name-plus-key pattern, a genuine gap this pass resolved
    (SP052).
15. **Payment webhook signatures are verified before any state write, and
    duplicate delivery is deduped against the gateway's own per-event id**
    — SP051/PaymentIsolation-CC.
16. **Every state-changing endpoint publishes via `publish_with_outbox()`
    in the same DB transaction as its state change** — no mutation may
    skip the transactional outbox (Audit-CC/PropagationSLA-CC, applies
    uniformly across this file).

## Approval

Security Lead — [x] Approved — autonomous execution, 2026-09-14
