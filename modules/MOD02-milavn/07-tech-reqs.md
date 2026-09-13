---
step: 07-tech-reqs
module: MOD02
status: Sealed
approver: Architect
updated: 2026-09-13
items: "52 | approved: 52 | blockers: 0"
---

# 07 — Technical Requirements — MOD02 Milavn

## Revision history
| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-13 | Initial draft. One pass over all 88 Sealed FRs (via their 88 Sealed IA items), grouped into 47 FR-traced tech-req items (TR01–TR47) where FRs share one technical mechanism (e.g. the Activity/Occurrence write path, the notification-class dispatch path), plus 1 platform-level item (TR-PLAT-01) and 4 cross-cutting items (TR-CROSSCUT-01–04) applying `/MODULE-ARCHITECTURE-STANDARD.md`'s generic patterns once rather than re-deriving them per TR — 52 items total. Each re-checked against `/ARCHITECTURE.md`, `/PRODUCT-GUARDRAILS.md`, and `/MODULE-ARCHITECTURE-STANDARD.md` fresh. Produced the Admin & Governance Console plugin/view-registration contract (ADR-012) as a platform-level item (TR-PLAT-01) per IA065's DEC-001 and the Product Manager's explicit "shared platform capabilities" guardrail, after confirming MOD01-Vyapar's own pipeline has not yet reached Step 6/7 (it has only 01-04 Sealed; no 05/06/07 exist) and MOD03-Mangaly's Sealed `07-tech-reqs.md` does not define or reference any such contract — so Milavn is, on current evidence, the first module actually positioned to author it, matching ADR-012's own naming of Milavn as a candidate. TR23 (FR028, Organization/Community Calendar) defines only the minimal Organization scope entity needed for FR028, per the Product Manager's explicit "needs discipline" note — no Organization management feature set is introduced. No `modules/MOD02-milavn/architecture.md` exists yet for this module (unlike Mangaly's, which was produced ahead of schedule by explicit product-owner direction) — this is raised as an open blocker below rather than improvised inline; tech reqs in this pass are written directly against `/ARCHITECTURE.md`'s Container-level decisions and `/MODULE-ARCHITECTURE-STANDARD.md`'s generic internal patterns (schema-per-component, authorization chokepoint, event bus, RLS, idempotency, shared rate-limiting), which do not require a component list to state correctly — but the specific component names/boundaries TR items reference (Identity/Profile, Discovery, Activity/Occurrence, Circle, Trust, Location/Privacy, Public Page, Notification Dispatch, Safety/Moderation) are this pass's own reasonable inference from the FR/BR grouping, not a ratified component diagram, and should be reconciled against the real `architecture.md` once Solution Architecture produces one for this module. | Step 7 (Tech Reqs), autonomous execution, per `06-impact-analysis.md` (Sealed) as source. |

## Coverage check
| Parent FR | Tech req items | Covered |
|---|---|---|
| FR001–FR003 | TR01 | Yes |
| FR004 | TR02 | Yes |
| FR005 | TR03 | Yes |
| FR006, FR008 | TR04 | Yes |
| FR007, FR033 | TR05 | Yes |
| FR009 | TR06 | Yes |
| FR010 | TR07 | Yes |
| FR011 | TR08 | Yes |
| FR012 | TR09 | Yes |
| FR013 | TR10 | Yes |
| FR014 | TR11 | Yes |
| FR015, FR016 | TR12 | Yes |
| FR017 | TR13 | Yes |
| FR018 | TR14 | Yes |
| FR019, FR069 | TR15 | Yes |
| FR020, FR021 | TR16 | Yes |
| FR022 | TR17 | Yes |
| FR023 | TR18 | Yes |
| FR024 | TR19 | Yes |
| FR025 | TR20 | Yes |
| FR026 | TR21 | Yes |
| FR027 | TR22 | Yes |
| FR028 | TR23 | Yes |
| FR029 | TR24 | Yes |
| FR030, FR031 | TR25 | Yes |
| FR032 | TR26 | Yes |
| FR034 | TR27 | Yes |
| FR035, FR036, FR037 | TR28 | Yes |
| FR038 | TR29 | Yes |
| FR039, FR040, FR041 | TR30 | Yes |
| FR042, FR043 | TR31 | Yes |
| FR044, FR045 | TR32 | Yes |
| FR046, FR048 | TR33 | Yes |
| FR047 | TR34 | Yes |
| FR049 | TR35 | Yes |
| FR050 | TR36 | Yes |
| FR051, FR052, FR053, FR054, FR055 | TR37 | Yes |
| FR056, FR057, FR059, FR063 | TR38 | Yes |
| FR058 | TR39 | Yes |
| FR060 | TR40 | Yes |
| FR061, FR062 | TR41 | Yes |
| FR064 | TR42 | Yes |
| FR065 | TR43 (module-side) + TR-PLAT-01 (platform contract) | Yes |
| FR066, FR067, FR068 | TR44 | Yes |
| FR070, FR071, FR072, FR073, FR074, FR075 | TR45 | Yes |
| FR076–FR082 | TR46 | Yes |
| FR083–FR088 | TR47 | Yes |

## Set-level quality gate
| Check | Result |
|---|---|
| Every FR has at least one tech req item | Pass — see coverage table; grouped FRs share one real technical mechanism each, not artificially merged. |
| No tech req contradicts `/PRODUCT-GUARDRAILS.md` | Pass — explicitly re-checked ranking (TR05: relevance/locality/trust, no popularity-primary sort), reputation (TR27/TR28: never a public score, never purchasable, moderation never single-signal-automated per TR15/TR43), People Discovery (TR31/TR32: reason-required, no swipe/match), and Organization scope (TR23: minimal entity only, no management feature set). |
| No tech req contradicts `/ARCHITECTURE.md` | Pass — Milavn stays in the Core Platform monolith, `milavn` schema, all cross-module reads via in-process interface or async event per the Dependency resolution table; no new synchronous cross-container edge introduced. |
| No tech req invents a data-ownership/authorization pattern already fixed by `/MODULE-ARCHITECTURE-STANDARD.md` | Pass — TR-CROSSCUT-01 through 04 apply (not re-derive) idempotency, shared rate-limiting, the authorization chokepoint, and the in-process event bus exactly as that file specifies; TR16 applies RLS including its two named failure modes explicitly. |
| Every open item from Step 6 (IA065, IA028, IA046/048, IA005/038) addressed | Pass — TR43/TR-PLAT-01 (IA065), TR23 (IA028), TR33 (IA046/048), TR03/TR29 (IA005/038). |
| Coverage check has no blank rows | Pass |
| Every item's quality/confidence fields complete | Pass |

## Open blockers
| ID | Item | Resolution | From |
|---|---|---|---|
| ~~BLOCKER-002~~ (resolved) | `modules/MOD02-milavn/architecture.md` did not exist when this file was drafted. | **Resolved 2026-09-13:** `modules/MOD02-milavn/architecture.md` has been produced (Sealed) and ratifies the exact component grouping this file already used (Identity Bridge, Member Profile, Discovery & Ranking, Activity & Occurrence, Circle, Trust & Reputation, Location & Privacy, Connect, Public Page, Notification Dispatch, Safety & Moderation, Authorization Engine, Audit Bridge), plus reconciles TR-PLAT-01's Admin Console edge into the diagram. No tech req below required rework. | This pass |

---

## TR-PLAT-01 — Admin & Governance Console: Plugin/View-Registration Contract (shared platform capability)
**Traces from:** FR065 (platform-level obligation surfaced by IA065's DEC-001)
**Status:** Ready for Review **Confidence:** Medium — the contract shape below is a reasonable first cut against ADR-012's stated intent, but has not yet been reviewed by whoever eventually owns Payment Services/Counsel's own future admin surfaces. **Priority:** Must (blocks FR065)

**Technical requirement**
This is authored as a **platform-level** capability, living in the Admin & Governance Console container (`/ARCHITECTURE.md`'s no-module-owner container, ADR-012) — not inside Milavn's own codebase — even though Milavn is this pass's author, because ADR-012 fixes the console as a single shared shell with federated module views, and a bespoke per-module admin screen is exactly the anti-pattern the Product Manager's guardrail rejects. Ownership check performed before writing this: MOD01-Vyapar's pipeline currently has only Steps 1-4 Sealed (no `05-test-scenarios.md`, `06-impact-analysis.md`, or `07-tech-reqs.md` exist in `modules/MOD01-vyapar/`), and MOD03-Mangaly's Sealed `07-tech-reqs.md` neither defines nor references any admin/moderation contract. Milavn is therefore the first module whose pipeline has actually reached the point of needing this contract, and authors it here; the contract itself is written to be consumed by any future module (Vyapar, Mangaly, Samachar), not Milavn-specific.

Contract shape (REST/JSON, ADR-014's OpenAPI convention):
1. **View registration manifest** — each contributing module registers one or more `AdminViewDescriptor` records at deploy time (a static manifest file the module ships, not a runtime call): `{ module_id, view_id, title, nav_group ("moderation" | "disputes" | "policy"), required_permission_scope, list_endpoint, detail_endpoint, action_endpoints[] }`. The console reads all registered manifests to build its federated navigation shell; it never hardcodes a module's admin routes.
2. **List/detail data contract** — every registered `list_endpoint` returns a `AdminQueueItem[]` shape: `{ item_id, module_id, item_type, submitted_at, priority, status, summary_text, deep_link }`, so the console's shared queue-list component renders any module's queue identically without module-specific rendering code. Every `detail_endpoint` returns `{ item_id, case_detail (module-defined JSON blob, opaque to the console), available_actions[] }`.
3. **Action dispatch contract** — the console never mutates a module's data directly; it calls the module's own registered `action_endpoints[]` (e.g., `POST /milavn/admin/moderation/{item_id}/actions/{action_id}`), authenticated via a short-lived JWT scoped to the admin's resolved permission (Identity & Trust Service, ADR-004), and the module's own authorization chokepoint (per `/MODULE-ARCHITECTURE-STANDARD.md` §5) enforces the action, not the console.
4. **Audit** — every action dispatched through this contract publishes an audit event to the Audit Service (ADR-011) from the *owning module* (not the console), tagged `admin_action.{module_id}.{view_id}`, so the console itself never needs write access to `AuditStore`.

**Constraints surfaced**
- The console's plugin contract does not exist anywhere in this repository before this pass (confirmed per IA065). This TR is a first-cut spec, not an implemented service — Step 7a/8/9 for whichever container hosts the Admin & Governance Console must actually build it; Milavn's own Step 9 only implements the Milavn-side manifest + endpoints (TR43).
- No dedicated Admin & Governance Console module folder exists in this pipeline yet (it is a platform container per `/ARCHITECTURE.md`, not one of the seven business modules in `modules.md`) — there is currently no natural home for this contract's own implementation-tracking pipeline artifact. Flagged for Solution Architecture/whoever stands up that container's own Steps 1-9 to adopt this spec as its starting input rather than re-deriving one.

**Assumptions**
Future modules (Vyapar, Mangaly, Samachar) needing an admin surface will consume this same contract rather than each defining their own `AdminViewDescriptor` shape — if a future module's needs genuinely don't fit (e.g., a bulk-action UI this shape doesn't support), that is a contract-versioning decision for whoever owns the console container next, not a silent per-module fork.

**Decisions** (append-only)
- **DEC-001 (2026-09-13):** Authored as a platform-level TR rather than inside Milavn's own component set, per IA065's DEC-001 and `/PRODUCT-GUARDRAILS.md`'s "Shared platform capabilities" guardrail. Milavn is the authoring module by pipeline-position evidence (see Technical requirement above), not by default assumption.

**Review history**
- (none yet)

**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR01 — Minimal Member Profile Data Model and Enrichment Fields
**Traces from:** FR001, FR002, FR003
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
A `MilavnMemberProfile` record in the `milavn` schema (component: Identity/Profile), keyed by `member_id` (foreign key reference only, never a copy, into Identity & Trust Service's `Member` — per ADR-004, Milavn never forks its own login/identity table). Required fields at signup: locality, at least one interest tag, language preference (read from the shared i18n model, ADR-010, with a per-person override column here). Optional enrichment fields (photo, bio) are nullable columns that never gate any read/write path elsewhere in the module — enforced by having every other component's authorization/eligibility check reference only the required fields. Photo upload goes through Object Storage/CDN (`/ARCHITECTURE.md` System Context) via a pre-signed upload URL pattern; a failed/slow upload must not block profile save (the profile write and the media reference write are two separate transactions, with the media reference nullable until upload completes).

**Constraints surfaced**
Object Storage/CDN outage has no dedicated fallback test yet (IA003/IA013 both flagged this gap) — TR requires the enrichment-field save path to succeed independently of Object Storage's availability (already true by the two-transaction design above), and Step 10 should add the explicit Object Storage failure scenario IA003 named.

**Assumptions** Identity & Trust Service's own availability is out of this module's scope.
**Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR02 — Dashboard-Facing Read Contract for "Around You" and Reminder Surfacing
**Traces from:** FR004
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
Per IA004/IA026's flagged gap and `/ARCHITECTURE.md`'s Dependency resolution table (Dashboard→Milavn, in-process, internal Python interface), define an explicit `MilavnActivityFeedReader` interface module — the *only* public surface of the Discovery component that Dashboard is permitted to import. It exposes typed methods (`get_nearby_activities(locality, limit)`, `get_upcoming_for_member(member_id)`) backed by the same Pydantic models Discovery's own REST responses use, so a later Milavn container-extraction is a lift-and-shift per ADR's own stated pattern. Dashboard never queries the `milavn` schema directly (schema-per-component rule, `/MODULE-ARCHITECTURE-STANDARD.md` §4, applied at the cross-module level too, consistent with ADR-002's rejection of implicit shared-database reads). Any future change to Milavn's Activity/Occurrence schema must keep this interface's method signatures stable or version them explicitly — a breaking change here is a cross-module compatibility break, not an internal refactor.

**Constraints surfaced** None beyond the interface itself needing versioning discipline once Dashboard actually ships.
**Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR03 — Four Discovery Modes; External Map-Tile Provider Integration
**Traces from:** FR005
**Status:** Ready for Review **Confidence:** Medium — external provider choice is a placeholder pending real account setup. **Priority:** Must (Feed/List/Calendar/Search); Should (Map)

**Technical requirement**
Feed, List, Calendar, and Search modes query the `milavn` schema directly via the Discovery component's own filter/sort logic (no dedicated Search Service needed — ADR-018 confirms Postgres full-text search is sufficient at Milavn's realistic V1 scale for its rule-based ranking). Map mode additionally calls an **external map-tile provider**, named here per this project's config-placeholder convention (`/ARCHITECTURE.md` System Context did not previously name one — flagged by IA005). Provider choice: **MapTiler** (OpenStreetMap-based, has a genuine free/low-cost tier suited to a solo-founder-stage product, avoids Google Maps' higher per-load cost at this stage) — placeholder, swappable via config, not a hard vendor lock per the abstraction below.

Config entries (new `config/external_services.yaml`, sample values, real key supplied later):
```yaml
map_tile_provider:
  vendor: maptiler          # swappable: maptiler | mapbox | google
  api_key: "REPLACE_ME_MAPTILER_API_KEY"
  tile_url_template: "https://api.maptiler.com/maps/streets/{z}/{x}/{y}.png?key={api_key}"
  rate_limit_per_month: 100000   # free-tier sample ceiling; update once real plan chosen
```
The Web Client's Map mode component reads the tile URL template from this config, never hardcoded, so switching providers is a config change. Map mode's own failure fallback (already designed, TS010) degrades to List mode with a visible "map unavailable" notice — Feed/Calendar/Search are entirely unaffected since they have no dependency on this provider.

**Constraints surfaced** This is a genuinely new external dependency; flagged for the next `/ARCHITECTURE.md` revision pass to add to the System Context diagram's external-system inventory (not done here — that file's Sealed status means only its own agent edits it; recorded as a note for that agent).
**Assumptions** Real MapTiler account/key supplied later per the config-placeholder convention; sample values above are non-functional placeholders.
**Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR04 — Card Content Contract and "Why This?" Reason Generation
**Traces from:** FR006, FR008
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
Discovery's card-rendering API response is a fixed Pydantic schema carrying exactly the six required fields (title, type, locality, time, trust indicator, primary action) plus a `why_this_reason: str | None` field populated from TR05's ranking-factor computation. Reason generation is a pure function of the same inputs the ranking score already used (no separate data fetch) — if generation fails for an item, that item is silently excluded from the ranked list rather than rendered without a reason (per BR/FR's explainability requirement being a standing one, not best-effort, matching `/PRODUCT-GUARDRAILS.md`'s "Explainability" row).

**Constraints surfaced** none new.
**Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR05 — Deterministic Rule-Based Ranking (Locality, Interests, Trust, Freshness)
**Traces from:** FR007, FR033
**Status:** Ready for Review **Confidence:** Medium — ranking-weight tuning remains an ongoing product-risk surface, not a one-time build. **Priority:** Must

**Technical requirement**
A single `RankingEngine` module (Discovery component) computes a deterministic weighted score per candidate item from four typed inputs: locality proximity, interest-tag overlap, trust level (TR25's field), and recency/freshness. Per ADR-018, this is explicitly a rule-based scorer, not a full-text-relevance or ML-ranked engine — no dedicated Search Service or ranking model is introduced. Weights live in a versioned config object (not hardcoded per call site) so future tuning is a config change, auditable via the event bus (`/MODULE-ARCHITECTURE-STANDARD.md` §6) rather than a silent code edit. Per `/PRODUCT-GUARDRAILS.md`'s "Ranking philosophy," popularity/engagement counters are explicitly excluded from this input set — any future addition of a popularity-derived signal requires a recorded product decision here, not an incidental engineering addition.

**Constraints surfaced** A missing/null input field (locality, interests, trust, freshness) could silently skew ranking (IA007) — the engine must treat a null input as "lowest confidence for that factor," never as zero/excluded, and log a data-quality warning via the event bus.
**Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR06 — Progressive-Disclosure Filters
**Traces from:** FR009
**Status:** Ready for Review **Confidence:** High **Priority:** Should

**Technical requirement**
Filter parameters map directly to indexed columns on the `milavn` schema's Activity/Occurrence tables (locality, type, date range, trust level) via the Discovery component's own query builder; a second "advanced" tier of filters (further-refined interest tags) is a progressive UI disclosure only — no separate backend endpoint, same query builder with additional predicate clauses.

**Constraints surfaced** none. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR07 — Minimal Activity/Occurrence Creation Form
**Traces from:** FR010
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
`POST /milavn/activities` (Activity/Occurrence component) accepts the minimal required field set (title, type, locality, first occurrence time) and writes through the authorization chokepoint (`/MODULE-ARCHITECTURE-STANDARD.md` §5) resolving the creator's identity against Identity & Trust Service. This endpoint is a mutation a client could plausibly retry after a connectivity drop (mobile-first, tier-2/3 connectivity per `/MODULE-ARCHITECTURE-STANDARD.md` §4b) — it is idempotent: the client supplies a client-generated `Idempotency-Key` header, and a repeated key returns the original created record rather than creating a duplicate activity.

**Constraints surfaced** none beyond the idempotency requirement above, which is a real, not hypothetical, risk for this specific endpoint (creation is the supply-side entry point, IA010).
**Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR08 — Activity/Occurrence Data Model (Foundational)
**Traces from:** FR011
**Status:** Ready for Review **Confidence:** Medium — highest-blast-radius data-model decision in this module, per BR03 DEC-001; this pass records the technical requirement, actual schema is Step 7a's job. **Priority:** Must

**Technical requirement**
This tech req states the *behavioral contract* Step 7a's ER Model must implement, without drawing the schema itself (that is explicitly Step 7a's job, not this agent's): an Activity is the recurring/umbrella concept; an Occurrence is one concrete instance of it; every FR that reads "activity data" elsewhere in this module (participation, calendar, organizer tools, public page) must resolve to a specific Occurrence, never an ambiguous Activity-level record, and a single, standalone Occurrence with no recurrence must not be forced to carry an artificial parent Activity wrapper it doesn't need (per BR03's own non-forced-wrapper rule, TS021/TS022). Step 7a must treat this as its own highest-scrutiny item across its three-pass process, per IA011's explicit flag.

**Constraints surfaced** Every dependent FR's tech req below (TR09-TR11, TR38-TR40, TR44) assumes this contract holds; a Step 7a schema that violates the non-forced-wrapper rule would require rework across all of them.
**Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR09 — Edit and Cancel an Activity/Occurrence
**Traces from:** FR012
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
`PATCH`/`DELETE` on the Occurrence resource, authorization-chokepoint-gated to the organizer (and TR38's co-organizer delegation). Cancellation publishes an in-process domain event (`/MODULE-ARCHITECTURE-STANDARD.md` §6, transactional outbox — same DB transaction as the cancellation write) that TR13's notification dispatch subscribes to; this is the specific event type IA017 flagged as needing confirmed transactional-outbox treatment given its safety relevance, and this TR makes that requirement explicit rather than assumed.

**Constraints surfaced** none new. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR10 — Progressive Advanced Configuration (Capacity, Co-Host, Recurrence, Cover Image)
**Traces from:** FR013
**Status:** Ready for Review **Confidence:** High **Priority:** Should

**Technical requirement**
Additional nullable fields on the Occurrence/Activity write path (capacity, co-host reference, recurrence rule, cover image reference) exposed as a progressive-disclosure UI section, same creation/edit endpoints as TR07/TR09 — no separate endpoint. Cover image follows the same two-transaction Object Storage pattern as TR01 (optional/decorative, never blocks save).

**Constraints surfaced** none beyond TR01's already-flagged Object Storage failure-scenario gap, which applies here too.
**Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR11 — Immediate Shareable Link on Creation
**Traces from:** FR014
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
On successful creation (TR07), the response includes a canonical public URL for the Occurrence, generated deterministically from its id (no separate URL-shortening service needed at this scale) — this URL is the same one TR33's public-page route serves, so "immediate" means no additional round-trip is required before the link is shareable.

**Constraints surfaced** none. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR12 — Participation Record and Attendance-Status Lifecycle
**Traces from:** FR015, FR016
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
A `Participation` record (Activity/Occurrence component's owned schema) with a status state machine (Interested → Going → Attended/No-Show/Cancelled). The Interested/Going write (`POST /milavn/occurrences/{id}/participation`) is this module's single most-repeated write (IA015) — it must be idempotent (same `Idempotency-Key` pattern as TR07) and its p95 latency target is set explicitly in Step 8 given this criticality, not left as a generic default. Status transitions are read by TR27's reputation-signal computation (read-only consumer, never a writer into Participation).

**Constraints surfaced** none new. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR13 — Organizer Update/Cancellation Notification Dispatch
**Traces from:** FR017
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
A `NotificationDispatch` component publishes to the Message Broker on any Occurrence update/cancellation event (from TR09), addressed to every current Participation record's member. Per ADR-006, this must use a transactional outbox (write the outbox row in the same DB transaction as the cancellation/update) so a process crash between "the state changed" and "the notification was queued" cannot silently drop a safety-relevant cancellation notice (IA017's explicit flag). This is the Important-tier notification class (TR37) — always-delivered, not user-mutable.

**Constraints surfaced** Confirmed here, per IA017: the transactional outbox pattern is a hard requirement for this event type specifically, not a generic aspiration.
**Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR14 — Scale-Gated Optional QR Check-In
**Traces from:** FR018
**Status:** Ready for Review **Confidence:** High **Priority:** Should

**Technical requirement**
Client-side QR generation/scan via the browser camera API (mobile web); server-side, a check-in endpoint validates the scanned token against the Participation record and flips status to Attended. A manual-entry fallback path (organizer taps a name in a list) hits the same endpoint with a different auth path, required given real-world camera-permission variance (IA018) — this fallback is not optional polish, it is the primary reliability mechanism.

**Constraints surfaced** none new. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR15 — Non-Punitive No-Show Handling; No Automated Penalty From a Single Signal
**Traces from:** FR019, FR069
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
A No-Show status write (TR12) never triggers any automated consequential action (account restriction, visibility reduction) by itself — enforced structurally by having the reputation-signal computation (TR27) and any moderation action (TR43) live in genuinely separate code paths that never call each other directly; a No-Show can only surface as one qualitative input among several in TR28's reputation display, and any actual penalty requires a human decision through TR43's moderation queue. Per `/PRODUCT-GUARDRAILS.md`'s "Moderation" row, this is a standing architectural gate, not a per-feature judgment call.

**Constraints surfaced** none new. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR16 — Circle Create/Join/Leave and Type Enforcement
**Traces from:** FR020, FR021
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
`Circle` and `CircleMembership` records (Circle component, its own schema per `/MODULE-ARCHITECTURE-STANDARD.md` §4). Circle type (public/private, an enum, not a free-text field) is enforced at write time and read through Postgres RLS as a second, database-enforced layer (per §4's requirement for any privacy-sensitive data) — the application connects as a non-owning role with RLS policies applied to it (never the migration/owner role, per §4's first named failure mode), and the authorization-context session variable is set with `SET LOCAL` inside the request's own transaction (never plain `SET`, per §4's second named failure mode, relevant here because this platform runs behind PgBouncer-class pooling at scale).

**Constraints surfaced** Both RLS failure modes named in `/MODULE-ARCHITECTURE-STANDARD.md` §4 are explicitly confirmed handled here, per that file's own requirement that "we added RLS" state which role and which of SET/SET LOCAL is used.
**Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR17 — Organic Circle-Formation Suggestion (Scheduled Batch Job)
**Traces from:** FR022
**Status:** Ready for Review **Confidence:** Medium — genuinely new operational component for this module, per IA022's flag. **Priority:** Should

**Technical requirement**
A scheduled batch job (co-participation pattern detection, reading TR12's attendance history) runs on a fixed interval (e.g., nightly), not synchronously on every attendance write. Failure/retry semantics: a failed run logs and retries on the next scheduled interval rather than blocking or retrying immediately (a missed suggestion is a lost opportunity per IA022's own severity call, not a correctness issue justifying aggressive retry). The job's output writes suggestion records the Circle component's own UI surfaces read; it never auto-creates a Circle (per `/PRODUCT-GUARDRAILS.md`'s "Circle formation" row — suggests only, human still acts).

**Constraints surfaced** This is the first scheduled/batch component in this module — its scheduling infrastructure (cron-equivalent inside the FastAPI monolith, e.g. APScheduler, or a platform-level job runner if one exists) should be confirmed against whatever `/ARCHITECTURE.md` or a future revision names as the platform's standard scheduling mechanism, rather than each module picking its own; flagged since no such platform standard is currently named.
**Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR18 — Circle Membership Never a Precondition (Cross-Feature Authorization Audit)
**Traces from:** FR023
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
No authorization check anywhere in this module's authorization chokepoint (`/MODULE-ARCHITECTURE-STANDARD.md` §5) may reference Circle membership as a precondition for any capability outside the Circle component itself. This is enforced by code review discipline plus a lint-style static check (grep-equivalent CI gate scanning for cross-component imports of Circle's membership table from outside Circle's own public interface) — not a one-time test, per IA023's flag that this needs an ongoing regression check as new features are added.

**Constraints surfaced** none new. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR19 — Community Memory (Aggregated Circle Stats)
**Traces from:** FR024
**Status:** Ready for Review **Confidence:** High **Priority:** Should

**Technical requirement**
A read-only aggregation query (count of shared activities, tenure) computed on-demand per Circle, with a short-TTL cache given aggregation cost grows with circle size/history (IA024) — no separate materialized table needed at V1 scale; revisit if query latency becomes measurable at Step 8.

**Constraints surfaced** none. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR20 — Public Circle Visibility Follows Type
**Traces from:** FR025
**Status:** Ready for Review **Confidence:** High **Priority:** Should

**Technical requirement**
Public-page rendering (TR33) for a Circle-scoped item queries through the same RLS-enforced type check as TR16 — no second, independently-implemented visibility check; reuses TR16's chokepoint rather than re-deriving one, avoiding the "same pattern as" divergence risk `/MODULE-ARCHITECTURE-STANDARD.md` §4c warns about for a different concern but is equally applicable here.

**Constraints surfaced** none. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR21 — Personal Calendar
**Traces from:** FR026
**Status:** Ready for Review **Confidence:** High **Priority:** Should

**Technical requirement**
A read endpoint joining TR12's Participation records to Occurrence dates for the requesting member only; the same Dashboard-facing reminder-surfacing gap TR02 already resolves (one interface, reused, not a second one built for this FR).

**Constraints surfaced** none. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR22 — Circle Calendar
**Traces from:** FR027
**Status:** Ready for Review **Confidence:** High **Priority:** Should

**Technical requirement**
Scoped query joining TR16's Circle membership to Occurrence data, RLS-enforced (same mechanism as TR16) to prevent cross-circle leakage (IA027's flagged risk).

**Constraints surfaced** none. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR23 — Organization Scope: Minimal Entity for Organization Calendar (Should, Discipline-Scoped)
**Traces from:** FR028
**Status:** Ready for Review **Confidence:** Medium — deliberately minimal, per explicit Product Manager instruction. **Priority:** Should

**Technical requirement**
Per the Product Manager's explicit note ("Organization/calendar scope needs discipline so it doesn't expand unnecessarily") and IA028's flag that no BR/FR ever independently specified "Organization" as an entity, this TR defines **only** the minimal scope FR028 actually needs, and no more:

- A lightweight `OrganizationScope` reference: `{ organization_scope_id, display_name, created_by_member_id }` — no address, no member roster, no verification workflow, no admin hierarchy, no billing, none of the shape a full "Organization management" feature would eventually need.
- Its **only** function is to be a Calendar `scope` value an Occurrence can be tagged with (alongside Personal/Circle/Community), exactly mirroring TR22's Circle-scoped query pattern — an `OrganizationScope`-scoped calendar query is structurally identical to a Circle-scoped one, substituting the scope type.
- Membership/who-can-tag-an-occurrence-with-this-scope is **not** a new authorization model: it reuses the Activity/Occurrence component's existing organizer-authorization check (TR09) — whoever created the `OrganizationScope` record is its only writer for V1; there is no invite/join flow for it (that would be the "Organization management feature set" explicitly out of scope here).
- This entity's actual database representation is Step 7a's job, not decided here — this TR states only the behavioral minimum Step 7a must satisfy, per this agent's own boundary (does not draft schemas).

**Constraints surfaced** If a future BR/FR genuinely specifies Organization management (roster, roles, verification), that is new BR/FR work through Step 1/2, not an incremental expansion of this minimal entity — flagged explicitly so a future implementer doesn't quietly grow this into a full feature without going back through the pipeline.
**Assumptions** "Community" calendar scope (also named in FR028) requires no new entity at all — it is simply the existing public-visibility query (TR20/TR24) with no additional scope table.
**Decisions**
- **DEC-001 (2026-09-13):** Scoped to the minimal reference-entity shape above, explicitly rejecting a fuller Organization data model, per Product Manager direction recorded in `06-impact-analysis.md` IA028 and `/PRODUCT-GUARDRAILS.md`'s general discipline-preserving intent.

**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR24 — Public Calendar Includes Only Public-Marked Items
**Traces from:** FR029
**Status:** Ready for Review **Confidence:** High **Priority:** Should

**Technical requirement**
The public calendar query filters on TR16/TR20's visibility model (public type only) — same RLS mechanism, no separate implementation.

**Constraints surfaced** none. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR25 — Trust-Level Field and Display
**Traces from:** FR030, FR031
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
A `trust_level` enum field on the relevant entity (Activity/Organizer/Venue), computed by the Trust component and always resolving to exactly one value (never null/ambiguous, per BR07/IA030). This field is explicitly layered on top of, never duplicating, Identity & Trust Service's own Level-1/2 identity data (IA030's flagged cross-layer boundary) — the Trust component reads the platform identity level as one input but owns its own module-specific taxonomy value independently. Displayed via a shared rendering component wherever organizer/venue/activity trust appears.

**Constraints surfaced** No dedicated test currently exercises the cross-layer boundary itself (IA030) — flagged for Step 10 to add a scenario asserting Milavn's trust taxonomy never silently forks or duplicates platform identity data.
**Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR26 — Organizations/Venues Share the Partner-Verified Path
**Traces from:** FR032
**Status:** Ready for Review **Confidence:** High **Priority:** Should

**Technical requirement**
Venue verification reuses TR25's same Trust component code path (not a duplicate implementation) — independently achievable without any dependency on MOD01-Vyapar's business-listing data (IA032 confirmed no such dependency is required by this module's own BRs; this TR does not introduce one).

**Constraints surfaced** none. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR27 — Reputation Signals From Named Behaviours
**Traces from:** FR034
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
Milavn's own behaviour/feedback entities (Participation status, TR44's Feedback record) are read-only inputs to the shared reputation-scoring engine co-located in Identity & Trust Service (ADR-005) — Milavn is the sole writer of its own signal entities; the shared engine never writes into Milavn's schema. Per ADR-005's explicit coupling, any change to which Milavn fields feed the reputation engine requires coordinated deployment with Identity & Trust Service, not an independent Milavn release — this coordination point is recorded here explicitly (IA034's flag) rather than discovered at implementation time.

**Constraints surfaced** ADR-005's cross-service coordination requirement is real; Step 9 implementation must sequence any reputation-input schema change with Identity & Trust Service's own release, not ship it unilaterally.
**Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR28 — Reputation Never Public/Numeric/Purchasable
**Traces from:** FR035, FR036, FR037
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
The reputation API response contract (consumed by every UI surface) exposes only a qualitative enum/tag set (e.g., "Reliable attendee," "New to community") — the raw numeric score computed internally by TR27's engine is never serialized into any API response reachable by a client, enforced by an explicit API-contract test at the schema level (not just UI-level review), matching TS073/TS074's own framing. The payment-to-reputation isolation (FR036) is a standing structural gate: no code path anywhere may take a Payment Services event as an input to TR27's engine — this is checked now, before any paid tier exists, as a guardrail rather than an active integration.

**Constraints surfaced** FR036 is genuinely untestable in full until a paid tier exists (IA036) — recorded as a standing gate to be verified the moment Payment Services' benefit-trigger events are wired up.
**Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR29 — Approximate Location Display; External Geocoding/Locality Service
**Traces from:** FR038
**Status:** Ready for Review **Confidence:** Medium — provider choice is a placeholder pending real account setup. **Priority:** Must

**Technical requirement**
Location fields resolve through a City → Zone → Locality display hierarchy backed by an **external geocoding/locality-resolution service**, not currently named in `/ARCHITECTURE.md`'s System Context (flagged by IA038, same class of gap as TR03's map-tile provider). Provider choice: **OpenCage Geocoding API** (OSM-backed, has a usable free tier, straightforward REST interface matching ADR-014's REST-first convention) — placeholder, swappable via config.

Config entries (same `config/external_services.yaml` as TR03):
```yaml
geocoding_provider:
  vendor: opencage           # swappable: opencage | google_geocoding | here
  api_key: "REPLACE_ME_OPENCAGE_API_KEY"
  base_url: "https://api.opencagedata.com/geocode/v1/json"
  rate_limit_per_day: 2500   # free-tier sample ceiling; update once real plan chosen
  fallback_on_failure: "coarser_locality"   # never raw coordinates, never no-resolution
```
On resolution failure, the fallback is a coarser-than-intended granularity (privacy-safe, per IA038's own risk framing) never a failed/blocked write — the locality field is nullable and re-resolved asynchronously on retry rather than blocking profile/activity save.

**Constraints surfaced** Same System-Context documentation follow-up as TR03 — flagged for the next `/ARCHITECTURE.md` revision, not actioned here. No test currently covers the geocoding-failure fallback path (IA038) — flagged for Step 10.
**Assumptions** Real OpenCage account/key supplied later per config-placeholder convention.
**Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR30 — Location/Attendance Privacy Defaults and User-Controlled Precision
**Traces from:** FR039, FR040, FR041
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
A `LocationPrecisionSetting` record (Location/Privacy component) is the single, centrally-enforced source every location-consuming feature (TR03's Map mode, TR29's display hierarchy) must query through a shared helper function — not independently re-checked per consumer (IA041's explicit flag that this reduces the "a future feature forgets" risk). Precise location requires an explicit consent record (`ConsentGrant`) before any feature may request it; no feature currently exercises this path (IA039), so this is a standing guardrail with no current caller, verified structurally rather than functionally today. Private Circle/attendance data defaults to hidden, enforced by the same RLS mechanism as TR16.

**Constraints surfaced** The centralization requirement above is itself the fix for IA041's flagged risk — any future FR touching location must call the shared helper, not re-implement its own precision check.
**Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR31 — Reason-Based Person Suggestion; No Reason-Less List
**Traces from:** FR042, FR043
**Status:** Ready for Review **Confidence:** High **Priority:** Should

**Technical requirement**
Person-suggestion logic (drawing on Circle membership and participation history) always attaches a generated reason string to each suggested person, using the same reason-generation pattern as TR04 — enforced structurally by having the suggestion component's public interface return `{ person_ref, reason }` tuples only, never a bare list of person references (IA043's flagged anti-pattern), so a reason-less "nearby people" list is impossible to accidentally construct from this interface, not merely discouraged by convention.

**Constraints surfaced** none. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR32 — No Swipe/Match Mechanic; No Romantic/Matrimonial Framing
**Traces from:** FR044, FR045
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
TR31's suggestion UI is a static list with a reason, never a swipeable card stack or accept/reject gesture pattern — this is a component-level design constraint, not a copy-only one: the underlying interaction model (no binary match state, no mutual-like concept) has no data model support for it (no `Match` or `Like` entity exists anywhere in this module's schema, by design). All user-facing copy in this surface goes through the shared i18n content model (ADR-010) with an explicit style-guide entry banning romantic/matrimonial phrasing, checked by the same recurring copy-audit test class as TS089/TS090 (a regression gate, not a one-time check, per IA044/IA045).

**Constraints surfaced** none new. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR33 — Public Page: Server-Rendered/Crawlable Path for a React/TypeScript SPA
**Traces from:** FR046, FR048
**Status:** Ready for Review **Confidence:** Medium — resolves IA046/IA048's flagged architectural question directly. **Priority:** Must

**Technical requirement**
`/ARCHITECTURE.md`'s Web Client is fixed as a React/TypeScript SPA (ADR-014, `/IMPLEMENTATION-TEST-STANDARDS.md`), and most of the app is intentionally behind auth and never crawled — a pure client-side-rendered SPA is the right default for that. The public Activity/Occurrence page (BR11's core growth mechanism) is the one route that genuinely needs to be crawlable and fast on first paint for an unauthenticated visitor, which a pure CSR SPA cannot provide without a dedicated mechanism. Resolution: this route is served via a **separate, minimal server-side-rendering path** — a lightweight Node/Next.js-style (or FastAPI + Jinja2, keeping the stack Python-first per ADR-014's own preference to minimize new tooling) rendering layer that owns exactly the public-page route(s) and nothing else, sitting in front of the Core Platform monolith's `GET /milavn/public/occurrences/{id}` endpoint (same data the authenticated app reads, via TR11's canonical URL). This is a genuinely new rendering mode most of the app doesn't need (IA046's own framing) — it is scoped narrowly to public pages only, not adopted platform-wide, to avoid taking on SSR complexity for routes that don't need it.

Concretely: the rendering layer fetches the public-page data server-side (public API call, no auth), injects it into server-rendered HTML with the eight required content elements (TR34) and SEO metadata (title, description, Open Graph tags) present in the initial HTML response (not injected client-side after hydration, which would defeat the crawlability goal), then hydrates into the same React component tree the authenticated app uses for consistency.

**Constraints surfaced** This SSR path is a new deployable surface distinct from the SPA build — Step 8/9 must size it as its own lightweight component with its own availability target (it directly serves BR11's growth mechanism, so its downtime has business-visible cost even though it is architecturally simple).
**Assumptions** A dedicated SSR framework choice is deferred to Step 9 implementation detail; this TR fixes only that an SSR/pre-rendering mechanism is required and scoped to public pages, not which specific tool implements it.
**Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR34 — Public Page Content Contract (Eight Required Elements)
**Traces from:** FR047
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
The public-page API response (consumed by TR33's SSR layer) is a fixed Pydantic schema enforcing all eight required content elements are present (title, description, time/location, organizer identity + trust status from TR25, capacity/spots-remaining, safety guidelines if flagged high-risk per TR42, RSVP call-to-action, share affordances per TR35) — a response missing any field fails schema validation rather than silently rendering an incomplete page.

**Constraints surfaced** none. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR35 — Six Named Share Channels
**Traces from:** FR049
**Status:** Ready for Review **Confidence:** High **Priority:** Should

**Technical requirement**
Client-side Web Share API integration where supported, with an explicit per-channel fallback link (WhatsApp/SMS/email/copy-link/etc. deep-link URLs constructed client-side) for browsers lacking Web Share API support — no server dependency for this beyond TR11's canonical URL.

**Constraints surfaced** none. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR36 — Non-Public Item Never Has a Reachable Public Page
**Traces from:** FR050
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
TR33's SSR public-page endpoint (`GET /milavn/public/occurrences/{id}`) enforces the same RLS/visibility check as TR16/TR20 before returning any data — a non-public item returns 404 (never a 403 that confirms existence), so the visibility gate is enforced on the exact route a URL-guesser would hit, not only in the authenticated app's own UI. This is treated as a highest-severity check (IA050's explicit flag) — Step 8 (Security) must independently re-verify this specific route, not rely on this Tech Req alone.

**Constraints surfaced** Flagged explicitly for Step 8's own STRIDE pass to treat this route as a priority target, per IA050.
**Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR37 — Notification Class Dispatch (Important/Useful/Social/Opportunity)
**Traces from:** FR051, FR052, FR053, FR054, FR055
**Status:** Ready for Review **Confidence:** High **Priority:** Must (Important class); Should (others)

**Technical requirement**
A single `NotificationDispatch` component (shared by TR13) classifies every outbound notification into one of four classes and applies class-specific delivery/preference rules: Important (always delivered, TR13's transactional-outbox pattern, ADR-006) — Useful (reminders, user-mutable timing, backed by TR17-style scheduling) — Social (privacy-boundary-checked against TR30's visibility settings before send) — Opportunity (frequency user-controlled via a preference record). Milavn governs *what* and *when* to notify; the Notification & Communication Service governs actual delivery infrastructure (SMS/email/push) per ADR-006 — Milavn never calls an SMS/push provider directly.

**Constraints surfaced** none new beyond TR13's already-stated outbox requirement, which applies to the Important class specifically.
**Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR38 — Organizer Tools: Attendee Visibility, Update Broadcast, Delegation, RSVP-Gated Details
**Traces from:** FR056, FR057, FR059, FR063
**Status:** Ready for Review **Confidence:** High **Priority:** Must (FR056, FR063); Should (FR059)

**Technical requirement**
Attendee list visibility (organizer + delegated co-organizers only, via TR16-style authorization chokepoint check), organizer update broadcast (reuses TR13's dispatch to every current Participation record), co-organizer delegation (a `CoOrganizerGrant` record, revocable, checked at the same chokepoint as the primary organizer), and RSVP-gated exposure of organizer identity/location/capacity to participants who have RSVP'd (a baseline physical-safety accountability requirement per BR14 — non-negotiable, no scope reduction).

**Constraints surfaced** none new. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR39 — Capacity and Waitlist Management (Concurrency-Safe Promotion)
**Traces from:** FR058
**Status:** Ready for Review **Confidence:** Medium — concurrency edge case explicitly flagged, per IA058. **Priority:** Should

**Technical requirement**
Waitlist promotion on a withdrawal must use a database-level row lock (`SELECT ... FOR UPDATE` on the Occurrence's capacity counter, within the same transaction as the withdrawal write) to prevent two concurrent withdrawals from double-promoting or missing a promotion — the exact race condition IA058 flagged as untested. This is Should-priority functionally, but the concurrency-safety mechanism itself is not optional once built.

**Constraints surfaced** Explicitly resolves IA058's flagged gap; Step 10 must add a concurrent-withdrawal test scenario, which did not previously exist.
**Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR40 — Future AI Organizer Actions Respect Human Authorization Boundaries (Standing Gate)
**Traces from:** FR060
**Status:** Ready for Review **Confidence:** Medium — forward-looking; AI Service does not exist yet (ADR-009, deferred). **Priority:** Could (no active build)

**Technical requirement**
No implementation work required now. Recorded as a standing architectural constraint: if/when the AI Service (ADR-009) ships an organizer-facing action, that action must be gated through TR38's existing authorization chokepoint exactly like a human organizer action — the AI Service's own action-authorization tiers (understand→authorize→execute→record→confirm) sit *in front of* this module's chokepoint, never bypass it. No code exists to enforce this today because no caller exists yet; this TR exists so the constraint isn't lost between now and when AI Service ships.

**Constraints surfaced** none actionable today. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR41 — Reporting and Blocking
**Traces from:** FR061, FR062
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
A `Report` record (Safety/Moderation component's own schema) covering Activity/User/Organization/Content report types, feeding TR43's queue. Report submission publishes an audit event to the Audit Service (ADR-011, at-least-once) in the same transaction as the Report write (transactional outbox, same pattern as TR13) — a dropped audit event for a safety report is a compliance gap per IA061's flag, not acceptable best-effort. A `Block` record is enforced at every contact/appearance touchpoint via a single shared `is_blocked(actor, target)` helper function every consuming component (People Discovery/TR31, notification recipient filtering/TR37) calls — not independently re-checked per surface, same centralization discipline as TR30's location-precision helper, avoiding the "checked at every touchpoint separately" risk IA062 flagged.

**Constraints surfaced** Step 10 must add the explicit audit-event-delivery scenario for report submission, which IA061 flagged as currently untested.
**Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR42 — Safety Guidelines for High-Risk Activities
**Traces from:** FR064
**Status:** Ready for Review **Confidence:** High **Priority:** Should

**Technical requirement**
A `high_risk` boolean/tag on the Activity/Occurrence record (TR07's creation form) triggers display of a fixed safety-guideline content block (from the shared i18n content model) on both the authenticated detail view and TR34's public-page contract.

**Constraints surfaced** none. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR43 — Milavn-Side Moderation Queue (Consumes TR-PLAT-01, Not a Standalone Screen)
**Traces from:** FR065
**Status:** Ready for Review **Confidence:** Medium — depends on TR-PLAT-01's contract, which is itself a first-cut spec. **Priority:** Must

**Technical requirement**
UX20/UI20's Moderation Queue is **redesigned per IA065's DEC-001 to consume TR-PLAT-01's plugin/view-registration contract**, not implemented as a standalone Milavn admin screen. Concretely, Milavn's Safety/Moderation component:
1. Registers one `AdminViewDescriptor` (TR-PLAT-01 §1) for its moderation queue: `{ module_id: "milavn", view_id: "moderation_queue", nav_group: "moderation", required_permission_scope: "milavn.moderate", list_endpoint: "/milavn/admin/moderation", detail_endpoint: "/milavn/admin/moderation/{item_id}", action_endpoints: ["/milavn/admin/moderation/{item_id}/actions/{action_id}"] }`.
2. Implements `list_endpoint`/`detail_endpoint` returning TR-PLAT-01 §2's `AdminQueueItem`/case-detail shapes, sourced from TR41's `Report` records.
3. Implements the action endpoints (dismiss, warn, escalate, restrict) — each gated through this module's own authorization chokepoint (§5), never through console-granted access alone, and each publishing its own audit event (TR-PLAT-01 §4) and never a single-signal automated penalty (TR15's standing gate applies here too — every action here is a human decision by construction, since it only exists because a human accessed the console).
4. The console shell itself (navigation, list rendering, layout) is **not** built by Milavn — Milavn ships only the manifest + three endpoint groups above; UX20/UI20's visual designs are the reference for the *console's* shared queue-list component's actual look, not for a Milavn-owned page.

**Constraints surfaced** This TR is blocked on TR-PLAT-01's contract being real (not yet implemented anywhere) — Milavn's Step 9 implementation of this TR cannot complete integration testing until the Admin & Governance Console container actually exists and implements its side of the contract. Recorded as a sequencing dependency, not a Tech-Reqs-level blocker (this TR's own shape is fully specified).
**Assumptions** none beyond TR-PLAT-01's own.
**Decisions**
- **DEC-001 (2026-09-13):** UX20/UI20 redesigned to consume TR-PLAT-01 rather than remain standalone, per IA065's DEC-001.

**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR44 — Post-Event Feedback: Optional, Internal-Only, Never a Precondition
**Traces from:** FR066, FR067, FR068
**Status:** Ready for Review **Confidence:** High **Priority:** Should

**Technical requirement**
A `Feedback` record triggered only on a Participation status transition to Attended (TR12), optional (skippable), feeding TR27's reputation engine as an internal-only read input — never surfaced through any public/qualitative-display API beyond TR28's already-defined qualitative contract, and never a precondition anywhere else in the module (enforced the same structural way as TR18's Circle-membership audit: a CI-level scan for any gating logic referencing the Feedback table outside its own component).

**Constraints surfaced** none new. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR45 — Deferred Capabilities: External Events, AI Intent Mapping, Vyapar Demand-Signal, Sponsorship (No Build)
**Traces from:** FR070, FR071, FR072, FR073, FR074, FR075
**Status:** Ready for Review **Confidence:** Low — deferred, per each FR's own BR16/BR17/BR18 status. **Priority:** Could (no active build)

**Technical requirement**
No implementation in this pass. Recorded so each item's future technical shape is known when re-prioritized, not re-discovered from scratch:
- FR070/FR071 (external event ingestion, deferred BR16): will require naming an external event-source API in `/ARCHITECTURE.md`'s System Context (does not exist there today) and reuses TR25's trust taxonomy without modification.
- FR072/FR073 (AI intent mapping, action authorization, deferred ADR-009): gated entirely behind the AI Service's own existence; reuses TR40's standing authorization-boundary gate once that service ships.
- FR074 (surface local-business demand to Vyapar, deferred BR18): **this is a currently undeclared cross-module edge** — `modules.md`/`ARCHITECTURE.md` have no Milavn→Vyapar entry today (IA074's flag). When BR18 is prioritized, this needs its own entry in `/ARCHITECTURE.md`'s Dependency resolution table, following the same async/optional pattern already used for Milavn→Payment Services, before any Tech Req work proceeds — recorded here as a known gap for that future pass, not resolved now.
- FR075 (sponsorship labelling/payment-boundary, deferred BR18): reuses the already-declared, already-resolved Milavn→Payment Services async benefit-trigger edge — no new architecture work anticipated.

**Constraints surfaced** FR074's undeclared edge is the one genuine architecture gap among these deferred items; flagged explicitly rather than left implicit.
**Assumptions** "Deferred" means not yet scheduled, not never, per each source IA item's own note.
**Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR46 — Onboarding/Auth Scaffolding (Splash, Sign Up, Log In, Reset, OTP, Permission Priming)
**Traces from:** FR076, FR077, FR078, FR079, FR080, FR081, FR082
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
All identity-bearing flows (sign up, log in, reset, OTP verification) call Identity & Trust Service directly (ADR-004) — Milavn holds no credential data of its own. OTP endpoints require rate-limiting/lockout, implemented as **the platform's one shared rate-limiting utility** (`/MODULE-ARCHITECTURE-STANDARD.md` §4c) at the Identity & Trust Service layer — not a bespoke Milavn-side counter, and not re-implemented "following the same pattern" per endpoint (the exact divergence risk §4c exists to prevent). Location/notification permission priming (FR081/FR082) uses the browser Geolocation/Push APIs with a manual-entry / in-app-inbox fallback respectively, matching TS159-TS162's already-designed fallback behavior; splash screen checks auth state via Identity & Trust Service before routing to onboarding vs. home.

**Constraints surfaced** OTP rate-limiting is confirmed here as an Identity & Trust Service platform capability, per IA080's own flag — Milavn's Step 9 must not build its own OTP counter.
**Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR47 — App Shell Scaffolding (Navigation, Empty/Error States, Settings, Inbox, Help, Logout/Delete)
**Traces from:** FR083, FR084, FR085, FR086, FR087, FR088
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
Main navigation shell is standard SPA routing (Web Client, no new pattern). Generic empty/offline/error states are a single shared React component consuming every FR's own existing success/failure API contract (no new backend work; a cross-cutting frontend pattern only) — flagged with a CI lint check so new screens can't silently diverge from it (IA084's flag). Settings aggregates TR01/TR30's own data (no new writes). Notification inbox reads TR37's four notification classes via one aggregation query. Help/Support reuses TR41's Report mechanism for "Contact support" rather than a separate ticketing system. Logout/delete-account confirmation calls Identity & Trust Service for session termination and account-deletion initiation; **Milavn's own scope is the confirmation UI and deleting only its own `milavn`-schema data** — per IA088's explicit flag, the platform-wide propagation of that deletion to every other module a member may have data in is Identity & Trust Service's own orchestration responsibility, not something Milavn (or any single module) re-solves. Flagged here for whoever owns Identity & Trust Service's own Tech Reqs to confirm that orchestration is explicitly specified there — it is not re-specified in this file.

**Constraints surfaced** Platform-wide account-deletion propagation is explicitly out of this module's own scope, per IA088 — flagged as a cross-cutting platform requirement for Identity & Trust Service's own pipeline artifacts, not duplicated here.
**Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR-CROSSCUT-01 — Idempotent Mutation Endpoints (Applies Platform-Wide Within Milavn)
**Traces from:** Cross-cutting (`/MODULE-ARCHITECTURE-STANDARD.md` §4b); most directly TR07, TR12
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
Every mutation endpoint a client can plausibly queue and retry under Milavn's mobile-first, tier-2/3-connectivity user base (activity creation TR07, participation TR12, report submission TR41, feedback TR44) accepts a client-generated `Idempotency-Key` header at the API layer (owned by the API-layer component per §4b, not reimplemented per business-logic component) and returns the original result on a repeated key rather than re-executing.

**Constraints surfaced** none. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR-CROSSCUT-02 — One Shared Rate-Limiting Utility
**Traces from:** Cross-cutting (`/MODULE-ARCHITECTURE-STANDARD.md` §4c); most directly TR46 (OTP), TR07/TR12 (abuse-prone write endpoints)
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
One shared, DB-backed, parameterized (key/window/limit) rate-limiting utility, called by every abuse-prone endpoint in this module (repeated report submission, repeated activity creation from one account, repeated participation toggling) — not independently built per endpoint. OTP-specific rate-limiting itself lives at the Identity & Trust Service layer (TR46), consistent with that being a platform, not module, concern; this utility covers Milavn's own module-internal abuse-prone endpoints.

**Constraints surfaced** none. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR-CROSSCUT-03 — Authorization as a Structural Chokepoint
**Traces from:** Cross-cutting (`/MODULE-ARCHITECTURE-STANDARD.md` §5); applies to every write path in this file
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
Every component method that reads/writes consequential Milavn data takes an already-resolved authorization context as a parameter (never a bare member ID it resolves itself) — enforced by a single internal `AuthorizationContext` object every write path in TR07-TR44 above is required to accept. A method found taking a bare user ID and querying data with it is a defect against this file, checked in code review and, where feasible, a static-analysis CI rule.

**Constraints surfaced** none. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR-CROSSCUT-04 — In-Process Domain Event Bus for Cross-Component Side Effects
**Traces from:** Cross-cutting (`/MODULE-ARCHITECTURE-STANDARD.md` §6); most directly TR09/TR13 (cancellation), TR41 (report/audit), TR17 (circle suggestion)
**Status:** Ready for Review **Confidence:** High **Priority:** Must

**Technical requirement**
Any action needing multiple components to react (a cancellation triggering both notification dispatch and an audit entry; a report triggering both the moderation queue and an audit entry) publishes to an in-process pub/sub bus within the same DB transaction as the state change (transactional outbox) — components never import and call each other directly for these reactions. This is the mechanism underlying TR09/TR13's cancellation-to-notification flow and TR41's report-to-audit flow specifically, stated once here rather than re-derived per TR.

**Constraints surfaced** none. **Assumptions** none. **Decisions** none.
**Review history** (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13
