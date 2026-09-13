---
step: 07-tech-reqs
module: MOD03
status: Sealed
approver: Architect
updated: 2026-09-13
items: "102 | approved: 102 | blockers: 0"
---

# 07 — Technical Requirements — MOD03 Mangaly

## Revision history

| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-13 | Initial version. Looped over all 102 Sealed, impact-analyzed FRs (`06-impact-analysis.md`, IA001–IA102) one at a time, per this agent's own loop discipline: re-read each FR/IA pair, `modules/MOD03-mangaly/architecture.md`'s 14-component C4-L3 breakdown and its component→BR/FR traceability table, `/MODULE-ARCHITECTURE-STANDARD.md`'s generic patterns (schema-per-component + RLS, idempotent mutation endpoints, authorization chokepoint, in-process domain event bus), `v1-decisions.md`'s resolved V1 values, and `CODING-GUIDE.md`'s stated project structure and defect-prevention controls, before writing each item's technical requirement and any surfaced constraint. Tech reqs are written strictly against `architecture.md`'s already-fixed component/schema boundaries — no competing decomposition invented. Does not draft an ER diagram, schema DDL, or database migration — that is Step 7a's (`step7a-er-model-agent`) exclusive scope, invoked only after this file Seals. Two architecture-level gaps `06-impact-analysis.md` explicitly flagged as "owner: Step 7" are resolved here at the tech-req level: (1) FR098's Notification Bridge inbox-persistence schema ownership — already resolved one layer up in `architecture.md`'s own 2026-09-12 follow-up revision (Notification Bridge now owns `mangaly_notification`); TR098 below states the concrete endpoint/query shape against that resolved schema. (2) FR102's cross-cutting mutation-endpoint idempotency requirement — already named as a required generic pattern in `/MODULE-ARCHITECTURE-STANDARD.md` §4b and reflected in `CODING-GUIDE.md`'s `idempotency/` middleware module; TR102 below states which endpoints must honor it and TR049/TR042/TR002/etc. cross-reference it rather than re-deriving it per component. Every other IA-surfaced finding (shared tier-gate function for FR003/FR027; DB-backed rate-limit counter for FR037; on-call paging + CSAM reporting wiring for FR065/FR068/FR074; DB-access-control review for FR051/FR067/FR071; RLS non-owning-role + `SET LOCAL` requirement for every RLS-bearing item; anti-enumeration response-shape rule for FR093/FR094; Android `FLAG_SECURE`/iOS-asymmetry disclosure for FR056; SMS/OTP DLT-route + fallback-channel recommendation for FR095) is carried into its own item's Constraints-surfaced field as an explicit, named item, not smoothed over. | Tech Requirements (Step 7) — krishna kategaru (autonomous), 2026-09-13. |
| 2026-09-13 | Critique-mindset review (explicit instruction: check folder structure, mutation correctness, data structures, loose coupling, correct system-design pattern usage, and — specifically — that utilities are genuinely common, not duplicated per call site). Found one real gap: TR037, TR093, and TR095 each described their rate-limiting as "the same pattern as" an earlier item rather than one shared implementation, spanning two different components (Identity Bridge, Trust & Verification) — exactly the divergence risk class `/MODULE-ARCHITECTURE-STANDARD.md` §4b's idempotency pattern already exists to prevent for a different concern. Added §4c to that file (one shared, parameterized rate-limiting utility), added a `rate_limiting/` module to `CODING-GUIDE.md`'s project structure, made TR037 the canonical statement (mirroring TR017's role for RLS) with TR093/TR095 now calling the same implementation rather than re-deriving it, and consolidated TR093/TR094's anti-enumeration response shape into one shared `generic_auth_error()` function both call. Everything else reviewed (folder structure/naming consistency, mutation-before-authorization ordering, structural-absence enforcement, event-bus/outbox usage, loose coupling via component interfaces rather than direct schema access) held up with no further correction needed. | Critique review — krishna kategaru (autonomous), 2026-09-13. |
| 2026-09-13 | **Sealed.** Approver re-verified coverage (102/102 FR↔TR, 1:1), the corrected quality-gate row, and open blockers (none — all remaining items are named, owned external dependencies per `v1-decisions.md` convention, not blockers) before approving. All 102 items ticked Approved. Step 7a (ER Model & Database Implementation) is cleared to begin against this Sealed file. | Approved — krishna kategaru, 2026-09-13. |

## Coverage check

| Parent FR | Tech req items | Covered |
|---|---|---|
| FR001 | TR001 | Yes |
| FR002 | TR002 | Yes |
| FR003 | TR003 | Yes |
| FR004 | TR004 | Yes |
| FR005 | TR005 | Yes |
| FR006 | TR006 | Yes |
| FR007 | TR007 | Yes |
| FR008 | TR008 | Yes |
| FR009 | TR009 | Yes |
| FR010 | TR010 | Yes |
| FR011 | TR011 | Yes |
| FR012 | TR012 | Yes |
| FR013 | TR013 | Yes |
| FR014 | TR014 | Yes |
| FR015 | TR015 | Yes |
| FR016 | TR016 | Yes |
| FR017 | TR017 | Yes |
| FR018 | TR018 | Yes |
| FR019 | TR019 | Yes |
| FR020 | TR020 | Yes |
| FR021 | TR021 | Yes |
| FR022 | TR022 | Yes |
| FR023 | TR023 | Yes |
| FR024 | TR024 | Yes |
| FR025 | TR025 | Yes |
| FR026 | TR026 | Yes |
| FR027 | TR027 | Yes |
| FR028 | TR028 | Yes |
| FR029 | TR029 | Yes |
| FR030 | TR030 | Yes |
| FR031 | TR031 | Yes |
| FR032 | TR032 | Yes |
| FR033 | TR033 | Yes |
| FR034 | TR034 | Yes |
| FR035 | TR035 | Yes |
| FR036 | TR036 | Yes |
| FR037 | TR037 | Yes |
| FR038 | TR038 | Yes |
| FR039 | TR039 | Yes |
| FR040 | TR040 | Yes |
| FR041 | TR041 | Yes |
| FR042 | TR042 | Yes |
| FR043 | TR043 | Yes |
| FR044 | TR044 | Yes |
| FR045 | TR045 | Yes |
| FR046 | TR046 | Yes |
| FR047 | TR047 | Yes |
| FR048 | TR048 | Yes |
| FR049 | TR049 | Yes |
| FR050 | TR050 | Yes |
| FR051 | TR051 | Yes |
| FR052 | TR052 | Yes |
| FR053 | TR053 | Yes |
| FR054 | TR054 | Yes |
| FR055 | TR055 | Yes |
| FR056 | TR056 | Yes |
| FR057 | TR057 | Yes |
| FR058 | TR058 | Yes |
| FR059 | TR059 | Yes |
| FR060 | TR060 | Yes |
| FR061 | TR061 | Yes |
| FR062 | TR062 | Yes |
| FR063 | TR063 | Yes |
| FR064 | TR064 | Yes |
| FR065 | TR065 | Yes |
| FR066 | TR066 | Yes |
| FR067 | TR067 | Yes |
| FR068 | TR068 | Yes |
| FR069 | TR069 | Yes |
| FR070 | TR070 | Yes |
| FR071 | TR071 | Yes |
| FR072 | TR072 | Yes |
| FR073 | TR073 | Yes |
| FR074 | TR074 | Yes |
| FR075 | TR075 | Yes |
| FR076 | TR076 | Yes |
| FR077 | TR077 | Yes |
| FR078 | TR078 | Yes |
| FR079 | TR079 | Yes |
| FR080 | TR080 | Yes |
| FR081 | TR081 | Yes |
| FR082 | TR082 | Yes |
| FR083 | TR083 | Yes |
| FR084 | TR084 | Yes |
| FR085 | TR085 | Yes |
| FR086 | TR086 | Yes |
| FR087 | TR087 | Yes |
| FR088 | TR088 | Yes |
| FR089 | TR089 | Yes |
| FR090 | TR090 | Yes |
| FR091 | TR091 | Yes |
| FR092 | TR092 | Yes |
| FR093 | TR093 | Yes |
| FR094 | TR094 | Yes |
| FR095 | TR095 | Yes |
| FR096 | TR096 | Yes |
| FR097 | TR097 | Yes |
| FR098 | TR098 | Yes |
| FR099 | TR099 | Yes |
| FR100 | TR100 | Yes |
| FR101 | TR101 | Yes |
| FR102 | TR102 | Yes |

## Set-level quality gate

| Check | Result |
|---|---|
| Every FR has at least one tech req | Pass — 102/102, TR001–TR102. |
| Every tech req traces to exactly one FR (its parent) and cites the IA item it was written against | Pass — see each item's "Traces from" line. |
| No tech req invents a component, schema, or authorization/event-bus pattern `architecture.md` or `/MODULE-ARCHITECTURE-STANDARD.md` hasn't already fixed | Pass — every item names an existing component from `architecture.md` §2.2/§2.3 and, where it touches data, an existing schema from `architecture.md` §3. Two items (TR037's rate-limit counter, TR031's banned-claim check) name a *new table inside an existing schema-owning component*, not a new component — consistent with the "components own schemas, not the reverse" principle. |
| The two Step-6-flagged architecture gaps are resolved, not re-opened | Pass — FR098 (TR098) builds against `architecture.md`'s now-resolved `mangaly_notification` schema; FR102 (TR102) builds against `/MODULE-ARCHITECTURE-STANDARD.md` §4b's now-fixed idempotency pattern. Neither is treated as newly open by this file. |
| RLS pooling-safety requirement (non-owning DB role; `SET LOCAL`) applied consistently | Pass — every item whose data crosses an authorization boundary (the large majority of the 12 schema-owning components) states this as a Constraint, not left implicit; TR017 states the canonical, once-only implementation and every other item cross-references it rather than re-deriving it. |
| Idempotency requirement applied consistently to every client-queueable mutation | Pass — TR002, TR042, TR043, TR046, TR047, TR049, TR057, TR058 (the named message-send/profile-save/connection/sharing/contact-exchange endpoints) each cross-reference TR102's cross-cutting middleware rather than inventing a per-endpoint mechanism. |
| Rate-limiting is one shared utility, not one per abuse-prone endpoint | Pass (corrected 2026-09-13) — a review found TR037/TR093/TR095 originally each described rate-limiting as "the same pattern as" another item rather than one shared implementation, spanning two components (Identity Bridge, Trust & Verification). Fixed: TR037 is now the canonical statement of a shared `rate_limiting/` utility (`/MODULE-ARCHITECTURE-STANDARD.md` §4c); TR093/TR095 call the same implementation with their own key/window/limit. TR093/TR094's anti-enumeration response shape similarly consolidated into one shared `generic_auth_error()` function both call. |
| Every genuinely external-gated item is named, not silently treated as resolved | Pass — DPDP retention/legal-hold sign-off (TR050/TR053/TR054/TR101), verification-vendor selection (TR035/TR037/TR038), the personality-assessment instrument (TR033), the deferred BR17 Agent layer (TR077/TR078), and the on-call-paging/CSAM-reporting vendor/format choice (TR065) are each named with an explicit owner in their own Constraints/Assumptions fields. |

## Open blockers

None. Every genuinely external-gated dependency this file's own items carry forward (DPDP Act retention/legal-hold sign-off; verification-vendor selection; the personality-assessment instrument; the deliberately-deferred BR17 Agent layer; on-call-paging vendor and CSAM structured-handoff format) is named explicitly in its own item, with an owner, exactly as `v1-decisions.md` and `06-impact-analysis.md` already treat these categories — a named, owned external dependency is not the same thing as an open blocker, per this pipeline's established convention.

---

## TR001 — Minimum Viable Profile save endpoint
**Traces from:** FR001 (IA001)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Add `POST /profile` (Profile & Completeness component, `mangaly_profile` schema) accepting exactly DEC-V1-001's existence-tier field list (name, DOB, gender, city/locality, ≥1 photo; phone/identifier already exists from FR092). Validates required-field completeness server-side (not client-only) before insert; rejects with field-level errors on incompleteness rather than a generic failure. Binds the new profile row to the already-authenticated `member_id` resolved by the Identity Bridge — this endpoint does not itself authenticate. On success, publishes a `ProfileCreated` domain event (transactional outbox, same DB transaction as the insert, per `/MODULE-ARCHITECTURE-STANDARD.md` §6) consumed by the Audit Bridge for BR15.

**Constraints surfaced**
`mangaly_profile` RLS policy must key off `mangaly.authz_context`; MangalyService's runtime DB role must not own this table (per TR017's canonical RLS requirement — do not re-derive here).

**Assumptions** — DEC-V1-001's field list is the correct existence tier; may be refined post-launch as a normal FR-level refinement, not a re-opening of this tech req.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR002 — Per-category profile extension with distinct "declined" state
**Traces from:** FR002 (IA002)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`PATCH /profile/{category}` (Profile & Completeness) accepts one category's fields per call. Data model represents each field as a tri-state (`unset` / `declined` / `value`), never collapsing `declined` to `null` — this is a column-level modeling requirement, not a UI-only distinction. A failed save on one category must not roll back or discard edits to any other already-saved category (per-category transaction scope). Photo/video uploads route to Object Storage via a pre-signed upload URL issued by this endpoint; on upload failure, the category's other (non-media) fields still persist, and the client can retry the media upload independently. This endpoint is client-queueable (offline edits) and therefore honors TR102's idempotency-key middleware.

**Constraints surfaced**
Object Storage upload failure/retry semantics were flagged by IA002 as under-covered by TS003–005 — build the retry-preserving-partial-save behavior explicitly rather than assuming it falls out of the per-category transaction scope alone; confirm at Step 10 with a dedicated scenario.

**Assumptions** — exact per-category field schema stays implementation-stage per BR01 Constraints (unaffected by this tech req, which fixes behavior, not the field list).
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR003 — Shared discoverability-tier gate function
**Traces from:** FR003 (IA003)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Implement `is_discoverable(profile) -> bool` as a single function inside Profile & Completeness's `interface.py`, evaluated against DEC-V1-001's discoverability-tier field list. Discovery & Ranking (TR027) calls this exact function at query time — it does not reimplement the field-completeness check independently. This directly closes IA003's named divergence risk (two independent implementations of the same rule silently drifting apart over time).

**Constraints surfaced**
Add a contract test asserting Discovery's enforcement point and this function never diverge (IA003's own recommendation) — name this explicitly to Step 10, since neither TS006–007 nor TS064–065 alone tests non-divergence over time.

**Assumptions** — none beyond DEC-V1-001.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR004 — Enhanced-matching fields as non-gating, degrade-gracefully input
**Traces from:** FR004 (IA004)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Compatibility Engine's explanation-generation path (TR030) must have an explicit "insufficient enrichment data" branch that returns a valid, non-error response using only available-data fields — never an exception or a blocked call when enhanced-matching fields are absent. Discovery & Ranking's eligibility check (TR003/TR027) must not read any enhanced-matching-tier field at all — enforced as a repository-layer absence (the discoverability-tier function has no code path that queries enhanced-tier columns), consistent with this module's structural-absence enforcement style (CODING-GUIDE §7).

**Constraints surfaced** — none beyond the graceful-degradation branch itself, which IA004 flags as an easy-to-under-test code path; ensure it has dedicated unit coverage, not just incidental coverage from other tests.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR005 — Three-tier completeness display endpoint
**Traces from:** FR005 (IA005)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`GET /profile/completeness` (Profile & Completeness) is a pure read composing TR001/TR003's own tier calculations — it computes no independent business logic and stores no separate completeness value that could drift from the underlying field state (avoids a cached/derived-column staleness bug class).

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR006 — Media visibility routed through the Authorization Engine and time-bound signed URLs
**Traces from:** FR006 (IA006)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`GET /profile/{id}/media` (Profile & Completeness) takes an already-resolved `AuthzContext` (never a raw viewer ID) per TR017's chokepoint pattern, and only on a grant issues a **time-bound, single-use-scoped, per-request signed URL** from Object Storage (short TTL, e.g. 5 minutes) rather than a stable/cacheable URL. The signed-URL issuance call itself is logged as a consequential action (Audit Bridge).

**Constraints surfaced**
IA006 flags that a functional test proving "authorization denies unauthorized viewers" does not by itself prove "the issued URL can't be replayed by someone else" — Step 8 (STRIDE) must independently verify the Object Storage vendor's signed-URL implementation actually enforces expiry/scope server-side, not just that Mangaly requests a short TTL.

**Assumptions** — Object Storage (per `/ARCHITECTURE.md`'s Container diagram) supports time-bound, per-request signed URLs as a standard capability; not independently verified against a specific vendor at this step.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR007 — Home Circle invite-by-lookup
**Traces from:** FR007 (IA007)
**Status:** Ready for Review | **Confidence:** Medium — depends on an Identity & Trust Service username-lookup capability not yet confirmed to exist. | **Priority:** Must

**Technical requirement**
`POST /home-circle/invite` (Home Circle, `mangaly_home_circle` schema) calls Identity & Trust Service's lookup-by-authenticated-caller contract to resolve the invitee, then creates a pending-invitation record and publishes a domain event consumed by the Notification Bridge.

**Constraints surfaced**
Per IA007's own finding: confirm with Identity & Trust Service's actual (or planned) API surface that a username-lookup-by-authenticated-caller endpoint exists before implementation starts. If it does not exist yet, this tech req's fallback is invite-by-phone/email (already-known identifiers from FR092/FR095) rather than a Mangaly-built directory duplicating identity data — raise this as a scoped, narrow addition request to Identity & Trust Service's contract, not a silent Mangaly-side workaround, per ADR-004.

**Assumptions** — carries forward the FR's own stated assumption pending that confirmation.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR008 — Accept invitation, create membership record
**Traces from:** FR008 (IA008)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /home-circle/invitations/{id}/accept` (Home Circle) validates invitation state (not expired/withdrawn) before creating a membership row; publishes `HomeCircleMemberJoined` in the same transaction (outbox), consumed by Audit Bridge.

**Constraints surfaced** — none beyond standard state-validation.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR009 — Ignore/decline invitation as distinct terminal states
**Traces from:** FR009 (IA009)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`mangaly_home_circle.invitation` gets an explicit `status` enum (`pending` / `accepted` / `declined` / `expired`) — decline is a distinct write, not the absence of a row or a timeout-only state, so declined vs. silently-ignored-until-expiry remain independently queryable and independently audited.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR010 — Immediate authorization revocation on member removal/leave
**Traces from:** FR010 (IA010)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`DELETE /home-circle/members/{id}` (Home Circle) writes the removal, and the Authorization Engine's session-context resolution must treat any cached `AuthzContext`/RLS session variable as invalidated within a **stated, testable bound** — since `mangaly.authz_context` is set per-transaction via `SET LOCAL` (TR017), every new request already re-resolves it fresh; the residual-access window this tech req must close is any **application-level cache** of authorization decisions (if one exists) — cap its TTL at ≤5 seconds, or eliminate the cache for revocation-sensitive decisions entirely. Historical Home Circle records are preserved (no hard delete), per Audit Bridge's append-only guarantee.

**Constraints surfaced**
IA010 correctly names this as a genuine distributed-systems risk (cached sessions/tokens outliving revocation) — this tech req makes "immediate" a testable latency bound rather than a qualitative promise, per IA010's own recommendation.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR011 — Report false/inappropriate relationship claim, withhold pending review
**Traces from:** FR011 (IA011)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /home-circle/report` (Home Circle) creates a `mangaly_operations` case record (via Operations' interface, not a direct cross-schema write) and flips the disputed relationship's authorization grant to `withheld` state until the case resolves — same withheld-access mechanism as TR010/TR073.

**Constraints surfaced** — same residual-access-latency caveat as TR010.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR012 — Solo-candidate parity: negative-dependency contract test on every component
**Traces from:** FR012 (IA012)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
No component's `interface.py` may require a non-empty Home Circle membership as a precondition to any of its public methods — this is a structural absence, enforced by a contract test that exercises every listed capability (Profile, Discovery, Compatibility, Trust, Connection, Sharing, Communication, Safety, Accountability) against a zero-Home-Circle-member account and asserts full functionality.

**Constraints surfaced**
IA012 names this as a durable regression risk — a future feature added to any component could silently introduce an implicit Home Circle read. Recommend this contract test run as part of every future component's own CI suite (Step 10), not a one-time check, since nothing in the current pipeline re-runs it automatically on unrelated changes.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR013 — Relative's independent, scope-bounded search
**Traces from:** FR013 (IA013)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Discovery & Ranking's search endpoint takes the relative's `AuthzContext`, which the Authorization Engine resolves from the candidate's own BR04 scope grant recorded in `mangaly_home_circle`. Discovery never widens results based on any other signal — the scope grant is the sole boundary.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR014 — Suggestion record structurally distinct from a connection request
**Traces from:** FR014 (IA014)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /home-circle/suggest` writes to a `mangaly_home_circle.suggestion` table — a schema/entity fully separate from `mangaly_connection`'s request table, with no code path capable of converting a suggestion row directly into a connection request without the candidate's own explicit `POST /connections` call. This is a structural, not just a UI-level, non-trigger boundary.

**Constraints surfaced** — none beyond the structural-separation requirement itself.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR015 — Candidate's own search stays private from family by default
**Traces from:** FR015 (IA015)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Discovery & Ranking's search-activity log (if any is kept for the candidate's own use) has no read path exposed to any `AuthzContext` other than the candidate's own — enforced as a repository-layer absence, per the same pattern as TR064/TR066's Safety/Trust separation.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR016 — Private family notes, forwarded only on candidate approval
**Traces from:** FR016 (IA016)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`mangaly_home_circle.note` rows default to family-only visibility; `POST /home-circle/notes/{id}/forward` requires the candidate's own explicit `AuthzContext`-gated approval before the note becomes visible to the candidate. Communication's message content is never copyable into a note field via any API (no shared content-reference field between the two schemas) — this narrows, but does not fully close, the free-text-paste risk IA016 already names as a soft/policy control.

**Constraints surfaced**
IA016 is explicit that "no captured private-communication content" is a policy/product-copy guardrail, not a hard technical one — this tech req does not claim to enforce it structurally beyond preventing a direct API-level copy path; state this limitation plainly in the UI copy rather than implying full enforcement.

**Assumptions** — notes are scoped to matrimonial evaluation content per BR03 Assumptions — a product/policy boundary.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR017 — Authorization Engine: canonical chokepoint, RLS pooling-safety implementation
**Traces from:** FR017 (IA017 — highest blast-radius item in this file, per Impact Analysis's own finding)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
The Authorization Engine (`mangaly_authz` schema) is the only component permitted to resolve the BR04 permission chain. Its `resolve(actor, target, action) -> AuthzContext` is the single call every other component's public interface method requires as a parameter — enforced by a **lint rule** (not a code-review convention) that blocks any method signature accepting a bare actor ID, per `/MODULE-ARCHITECTURE-STANDARD.md` §5 and CODING-GUIDE §3. On resolution, it sets `SET LOCAL mangaly.authz_context = ...` (never plain `SET`) inside the current transaction only, which every other schema's RLS policies key off via `current_setting('mangaly.authz_context')`. **This is the canonical statement of the RLS pooling-safety requirement; every other tech req in this file that touches an RLS-bearing schema cross-references this item rather than re-deriving it.** Every grant/deny decision publishes an audit event (outbox pattern) to the Audit Bridge.

**Constraints surfaced**
Per IA017's live research finding: (a) MangalyService's runtime Postgres role must be a **non-owning role** with RLS policies explicitly applied to it — the migration/schema-owner role must never be the same role the application connects as, since RLS silently no-ops for a table's owner; (b) whatever connection-pooling mode Step 7a/9 selects (PgBouncer or equivalent) must be confirmed to either guarantee session affinity or the application must exclusively use `SET LOCAL` (never `SET`) for `mangaly.authz_context` — a plain `SET` under transaction-mode pooling can leak one request's context onto a different pooled connection's next transaction. Both are release-blocking configuration confirmations, not optional hardening, and must be verified by an integration test that exercises the real pooling configuration (CODING-GUIDE §7), not asserted from code review alone.

**Assumptions** — exact permission matrix/taxonomy remains implementation-stage per BR04 Constraints; does not affect the chokepoint pattern or chain-evaluation model itself.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR018 — Candidate vs. family info as two distinct grant types in the authz data model
**Traces from:** FR018 (IA018)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`mangaly_authz`'s grant table models candidate-information access and family-information access as two independently-typed grant rows (a `scope` enum column, e.g. `candidate_info` / `family_info`), never a single combined boolean — making conflation a schema-level impossibility rather than a discipline the application must maintain. Every component storing or displaying either category (Profile, Home Circle, Discovery, Connection & Sharing) reads through `AuthzContext.has_scope(...)`, never a raw flag.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR019 — Plain-language capability copy layer
**Traces from:** FR019 (IA019)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Should

**Technical requirement**
API responses expose the Authorization Engine's capability facts (what this viewer may/may not do) as structured, named fields the client renders into plain-language copy — the API layer does not embed copy strings server-side (keeps copy iteration a frontend/content change, not a backend deploy).

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR020 — No teaser-pattern gating on authorized-viewer content
**Traces from:** FR020 (IA020)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Once `AuthzContext` grants "authorized viewer," the profile-read endpoint (TR001/TR002's read path) returns full permitted content in one response — no partial/teaser response shape gated behind a second, separate unlock action. This is a response-contract rule, testable by asserting the authorized-viewer response schema has no "locked" field variant.

**Constraints surfaced**
IA020 flags this as the exact invariant a future premium-tier/monetization feature (the currently-dormant MOD03→MOD06 `benefit_eligible` edge) is most likely to violate — record this explicitly as a required check on any future monetization FR's own design review, not just at this step.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR021 — Searchability and per-viewer visibility as two independently-queried states
**Traces from:** FR021 (IA021)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`mangaly_discovery` carries its own `searchable` boolean/index entry, resolved independently of any specific viewer. Per-viewer content visibility is resolved separately, at read time, by the Authorization Engine. Discovery's index-population job never restricts indexing to what a specific viewer can see, and the profile-read endpoint never uses "is indexed" as a proxy for "is visible to this viewer" — the two are deliberately separate code paths, per IA021's own recommendation.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR022 — Structural absence of popularity/demand-signal fields
**Traces from:** FR022 (IA022)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`mangaly_profile` and `mangaly_discovery` schemas have no view-count, rejection-count, or similar demand-signal column anywhere, and no API response model exposes one — a schema/contract absence, not a suppressed-in-UI field. If an internal, non-user-facing analytics counter is ever added for product metrics, it lives in a separate analytics store never joined into any ranking or display query path.

**Constraints surfaced**
Per IA022: confirm at Step 8/9 that no internal analytics counter (if one exists) is ever wired into a ranking or display path — this tech req fixes the user-facing schema absence, not an organizational guarantee about future analytics work.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR023 — Home Circle exposure gated by the Authorization Engine before any candidate-side surfacing
**Traces from:** FR023 (IA023)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Any Discovery-surfaced event that could imply Home Circle existence to a prospective match (e.g., a "suggested by family" badge) routes through `AuthzContext` resolution first — the candidate's Home Circle composition is never exposed to a stranger candidate under any code path, enforced as a repository-layer absence in Discovery's queries into `mangaly_home_circle`.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR024 — Pause state (non-broadcast) and the audited safety-exception override path
**Traces from:** FR024 (IA024)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`PATCH /profile/pause` sets a `mangaly_profile.status = paused` flag with no broadcast/away-indicator surfaced anywhere. The safety-exception override (Safety Intelligence-triggered, Authorization Engine-executed) is implemented as its **own named, individually-audited grant type** in `mangaly_authz` — distinct from every other grant path — requiring both a Safety Intelligence-issued trigger reference and Operations review for any exception broader than the narrowest named case, per DEC-V1-006/DEC-V1-007's escalation model.

**Constraints surfaced**
Per IA024: this override path gets the same test-investment priority CODING-GUIDE reserves for the Authorization Engine's own chain (TS038–043) — recommend a dedicated Step 10 suite for the exception path specifically, not folded into FR024's general test coverage as a minor edge case.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR025 — Discovery available in parallel to candidate and family, via embedded Postgres FTS
**Traces from:** FR025 (IA025)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`GET /discovery/search` (Discovery & Ranking, `mangaly_discovery` schema) is queryable independently by both the candidate's and any authorized relative's `AuthzContext`, in parallel, with no shared "one active searcher" state. Search uses Postgres full-text search indexes inside this schema (ADR-007/ADR-018) — no external Search Service call.

**Constraints surfaced**
Per ADR-018/IA025: monitor V1 row-count/DAU against the ~500K-row/~20K-DAU threshold where embedded FTS stops being sufficient — this is correctly a Step 13 (Monitoring) watch item, not a Step 7 build gap.

**Assumptions** — none beyond ADR-007/ADR-018.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR026 — Ranking service implements DEC-V1-002's weighted model plus diversity re-rank
**Traces from:** FR026 (IA026)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Discovery & Ranking's scoring function implements DEC-V1-002's fixed weights (locality/relocation 30%, partner-preference 30%, lifestyle/compatibility overlap 20%, evidence/verification completeness 20%, popularity 0% by construction — no code path reads any engagement/view metric into this function at all) as a versioned, named configuration object (`config/ranking_weights.py`, consistent with `config/thresholds.py`'s pattern), followed by a diversity re-ranking pass (no more than 3 consecutive same-top-decile results per feed page).

**Constraints surfaced**
DEC-V1-002's monthly automated fairness/parity report is a live-production-data process with no Step 5/6/7 test equivalent — name it explicitly as a Step 13 (Monitoring) deliverable that must exist before this ranking model is trusted at scale, not assumed to follow automatically from building the weighted function correctly.

**Assumptions** — none beyond DEC-V1-002.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR027 — Discovery enforcement calls the shared tier-gate function (see TR003)
**Traces from:** FR027 (IA027)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Discovery's own eligibility filter calls `is_discoverable()` (TR003) as its sole gating check — it does not independently re-derive discoverability-tier logic. This is the Discovery-side half of TR003's shared-function requirement, stated here explicitly so the enforcement point and the gate definition are never built as two separate implementations.

**Constraints surfaced** — same divergence-risk note as TR003.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR028 — Fairness safeguards structurally enforced; AI ranking signal conditional-only
**Traces from:** FR028 (IA028)
**Status:** Ready for Review | **Confidence:** Medium — carries forward fairness-methodology's Medium confidence. | **Priority:** Must

**Technical requirement**
DEC-V1-002's named de-biasing safeguards (no wealth/status proxy, no education/profession-as-worth weighting beyond the fixed 20%, no locality-based exclusion, filter-bubble mitigation via the diversity re-rank) are implemented as explicit, individually-testable checks against the ranking weight config (TR026), not left to "the weights happen to avoid this." If/when an AI-derived ranking signal is ever introduced (conditional on ADR-009's AI Service existing — not required for V1), the ranking response schema carries a mandatory `inference: true` label on any such signal — this label field exists in the schema now, unused, so a future AI signal cannot ship without it.

**Constraints surfaced** — none beyond ADR-009's already-correct deferral.
**Assumptions** — carries forward DEC-V1-002's accepted trade-off (hand-tuned weights over a learned ranker).
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR029 — Community-assisted discovery hint: structurally content-limited entity
**Traces from:** FR029 (IA029)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Should

**Technical requirement**
`mangaly_home_circle.discovery_hint` table has **no name, photo, or contact column at all** — not a nullable column that happens to stay empty, a genuine absence at the DDL level, per DEC-V1-003's own "the field doesn't exist to leak" instruction. Discovery's feed-injection logic caps hint-card frequency at ≤1-per-20 feed items server-side (not a client-side display convention).

**Constraints surfaced**
IA029 flags this explicitly as "the exact place a resolved decision could still be under-implemented" — Step 7a's ER Model must build this table with the column genuinely absent, and Step 8/9 should include a schema-introspection check (not just a functional test) confirming no name/photo/contact column exists on this table.

**Assumptions** — none beyond DEC-V1-003.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR030 — Templated, non-score compatibility explanation generation
**Traces from:** FR030 (IA030)
**Status:** Ready for Review | **Confidence:** Medium — algorithm/weighting methodology remains BR07's own open item. | **Priority:** Must

**Technical requirement**
Compatibility Engine (`mangaly_compatibility` schema) generates explanations via a **templated** approach (fixed sentence structures populated from structured profile/trust data) rather than free-generation — this is the concrete mechanism choice IA031 recommends specifically because it structurally cannot phrase a certainty claim, avoiding a generate-then-filter pipeline's dependency on the filter never missing a phrasing. Response never includes a numeric score field.

**Constraints surfaced** — none beyond BR07's own carried-forward open algorithm question, which this tech req does not need to resolve to satisfy FR030's structural commitments.
**Assumptions** — none beyond BR07's open-algorithm note.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR031 — Fact/inference labeling and banned-claim template constraints
**Traces from:** FR031 (IA031)
**Status:** Ready for Review | **Confidence:** Medium — same open-algorithm caveat as TR030. | **Priority:** Must

**Technical requirement**
Every explanation template (TR030) carries a `source: fact | inference` tag sourced from Trust & Verification's own evidence layer — never inferred by the Compatibility Engine itself. Ownership of the banned-claim check (certainty-of-character/honesty/success language) is assigned explicitly to the Compatibility Engine's own `interface.py`, implemented as the template library itself having no template capable of producing such language (structural, per TR030's templated-generation choice) — resolving IA031's own finding that `architecture.md`'s component list did not previously assign this ownership.

**Constraints surfaced** — none beyond the ownership assignment this tech req makes explicit.
**Assumptions** — none beyond BR07's open-algorithm note.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR032 — Core compatibility capability has zero dependency on FR033/FR034
**Traces from:** FR032 (IA032)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Compatibility Engine's core explanation path (TR030/TR031) reads only profile/evidence data available from the Must-priority field set (DEC-V1-001) — a contract test asserts the core path produces a valid, non-degraded response with personality-assessment and horoscope fields entirely absent from the input, not merely optional-and-present-but-empty.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR033 — Personality assessment: build skip/non-blocking scaffolding now, instrument selection stays open
**Traces from:** FR033 (IA033)
**Status:** Ready for Review | **Confidence:** Low — the instrument itself is genuinely unselected. | **Priority:** Should

**Technical requirement**
Build `mangaly_compatibility.assessment_response` as an instrument-agnostic key-value/JSON response store, plus the skip/abandon/non-penalty mechanics (never gates Discovery or the core Compatibility path, per TR032) — all buildable now, independent of which instrument is eventually selected. Do **not** hardcode a specific instrument's question set or scoring logic into application code.

**Constraints surfaced**
Per IA033/`v1-decisions.md`'s "What stays open" table: instrument selection (licensed psychometric tool vs. custom questionnaire) is a genuine Product/Legal procurement decision, not resolvable at this step. This tech req's scaffolding does not depend on that choice and should proceed regardless; the instrument integration itself is a separate, later tech req once Product selects one.

**Assumptions** — none beyond what's stated above.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR034 — Horoscope: isolated, opt-in-only input path
**Traces from:** FR034 (IA034)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Could

**Technical requirement**
`mangaly_compatibility.horoscope` is a separately-toggled table joined into the Compatibility Engine's input set only when the owning candidate's own opt-in flag is true — enforced as a query-time filter, not an application-level convention, so a non-opted-in candidate's Compatibility computation has no code path that can read this table at all.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR035 — Six-layer independent evidence/provenance display
**Traces from:** FR035 (IA035)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`GET /trust/{profile_id}/evidence` (Trust & Verification, `mangaly_trust` schema) returns each of the six verification layers as an independent object (status, provenance, timestamp) — never collapsed into one combined badge/score field. Account-authenticity/identity layers source from Identity & Trust Service's Level-1/2 status via a sync call; a degraded/unavailable response from that service renders those two layers as "unavailable," not as a false negative.

**Constraints surfaced** — Identity & Trust Service availability/degradation behavior for this read path is a Step 8 concern, not resolved here.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR036 — Evidence copy avoids truth-certification language
**Traces from:** FR036 (IA036)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Trust & Verification's evidence-layer copy strings are drawn from a fixed, reviewed vocabulary bank that structurally excludes absolute "true/confirmed/certified" language (e.g., "self-reported," "confirmed by [N] verifier(s)," never "verified true"). Enforced as a content-governance list checked at build time (a lint-style check against the copy bank), not a runtime filter.

**Constraints surfaced**
Per IA036: consolidate this content-review discipline with FR056's and FR085's copy-governance items into one Step 9 content-review pass rather than three independent ones.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR037 — Verification Circle: DEC-V1-004 anti-abuse mechanics; canonical shared rate-limiting utility
**Traces from:** FR037 (IA037)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /trust/verification-circle/invite` (Trust & Verification) requires the invited verifier to hold Level-2+ trust status (sync check against Identity & Trust Service) before their eventual response counts as evidence. Rate limiting (≤5 invites per rolling 7-day window per inviting account) calls the shared `rate_limiting/` utility (per `/MODULE-ARCHITECTURE-STANDARD.md` §4c and `CODING-GUIDE.md`'s project-structure entry) — a single, parameterized (key, window, limit) DB-backed counter, not an in-memory cache and not a component-local table Trust & Verification builds for itself. **This is the canonical statement of the shared rate-limiting requirement; TR093 and TR095 below call this exact same utility with their own key/window/limit parameters — they do not build their own counters "following the same pattern," per IA037's explicit finding that an in-memory or per-component counter would not survive a process restart or scale across instances, and per the divergence risk this file's own TR003/TR027 pairing already had to correct once.** A verifier's confirmation is idempotent per candidate-fact pair (unique constraint, not application-level dedup alone). A verifier later found fraudulent has their confirmation marked `invalidated` (never deleted) and their own account flagged into an Operations case (BR16). Outreach notification copy is fixed, neutral-framing text (no per-request customization that could introduce leading language).

**Constraints surfaced** — none beyond the shared-utility requirement this tech req already resolves.
**Assumptions** — verification-vendor selection itself remains open per `v1-decisions.md`; this tech req covers only DEC-V1-004's mechanics, which do not depend on which vendor is eventually chosen.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR038 — Admin/Mangaly-operated verification fallback path
**Traces from:** FR038 (IA038)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /trust/admin-verification-request` (Trust & Verification → Operations) is available unconditionally, not gated on a failed or attempted Verification Circle request first — Operations' workflow (DEC-V1-007) targets the 1-hour BharatMatrimony-benchmarked SLA (DEC-V1-004) for this path specifically.

**Constraints surfaced**
IA038 correctly notes the 1-hour SLA's achievability is an operational-staffing question (DEC-V1-007's small on-call rotation), not purely technical — name it as a Step 13 (Monitoring) measured metric, not a Step 5/7 test assertion.

**Assumptions** — none beyond DEC-V1-004/DEC-V1-007.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR039 — Structural absence of any trust score / reputation field
**Traces from:** FR039 (IA039)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
No column, computed field, or API response field anywhere in `mangaly_trust`, `mangaly_discovery`, or `mangaly_profile` aggregates verification/trust signals into a single score or ranking value — a schema/contract absence, verified by a static schema-introspection test per CODING-GUIDE §6's own named test class for exactly this pattern.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR040 — Evidence panel response contract has no raw-document field
**Traces from:** FR040 (IA040)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
The Evidence-panel response model (TR035) has **no field capable of carrying a raw document URL/bytes** — by construction, per CODING-GUIDE §7. The only endpoint permitted to return a raw verification document is the role-gated Admin Case detail endpoint inside Operations (TR072), which is a structurally separate response model from the Evidence panel's, not the same model with a conditionally-populated field.

**Constraints surfaced** — none; this is already fully specified by CODING-GUIDE §7 and requires no new design decision, only correct implementation against the two separate response models.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR041 — Marriageable-age gate as a versioned, admin-configurable setting
**Traces from:** FR041 (IA041)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`config/thresholds.py` (per DEC-V1-005) stores the current 21(men)/18(women) marriageable-age threshold as a versioned, admin-configurable setting read at eligibility-check time by Trust & Verification and Discovery's eligibility gate — never a literal in business logic. Inconclusive age evidence from Identity & Trust Service fails closed (treated as not-yet-eligible), never defaults to "assume compliant."

**Constraints surfaced**
Per IA041: name the 2021 Prohibition of Child Marriage (Amendment) Bill's legislative status as a Step 13 (Monitoring) watch item — DEC-V1-005's entire value proposition (config change, not redeploy) only holds if someone is actually watching for the change.

**Assumptions** — none beyond DEC-V1-005.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR042 — Send connection request, on-behalf-of authorization check
**Traces from:** FR042 (IA042)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /connections` (Connection & Sharing, `mangaly_connection` schema) resolves `AuthzContext` for the acting party (candidate or authorized family member acting on-behalf-of) before creating the request row; publishes `ConnectionRequested` (outbox) for Audit Bridge. This endpoint is client-queueable and honors TR102's idempotency-key middleware.

**Constraints surfaced** — none beyond standard on-behalf-of resolution.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR043 — Full pre-acceptance review information, no forced timeout
**Traces from:** FR043 (IA043)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`GET /connections/{id}/review` returns full Compatibility Engine and Trust & Verification information available to the recipient before any accept/decline decision — same anti-teaser response-contract rule as TR020, applied to the pre-acceptance review surface specifically. `PATCH /connections/{id}` (accept/decline) has no default/auto-expiry state machine transition that forces a decision.

**Constraints surfaced** — cross-referenced with TR020's identical monetization-pressure risk category; both should be checked together in any future monetization-feature design review.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR044 — Acceptance triggers nothing beyond "willing to explore" state
**Traces from:** FR044 (IA044)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`PATCH /connections/{id}` (accept) writes only the connection's own state transition — it publishes no event that Communication, Connection & Sharing (contact/media sharing), or Home Circle subscribe to as an auto-trigger. A contract test asserts zero downstream side effects fire from this one event beyond the connection-state write and its own audit record.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR045 — No single-current-connection constraint
**Traces from:** FR045 (IA045)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`mangaly_connection` schema has no unique constraint or business-logic check limiting a candidate to one active connection at a time — multiple concurrent accepted connections are a fully supported, unconstrained state.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR046 — Per-category sharing grants, independently timestamped
**Traces from:** FR046 (IA046)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`PATCH /connections/{id}/share/{category}` (Connection & Sharing) writes each shareable category (additional photos, video, etc.) as its **own row with its own independent grant timestamp** in `mangaly_connection.sharing_grant` — never a combined bitmask/flag field, per IA046's own recommendation to make independence structurally obvious rather than merely tested. Each grant resolves its own `AuthzContext` scope independently. Client-queueable; honors TR102's idempotency middleware.

**Constraints surfaced** — none beyond the row-per-category modeling requirement this tech req already fixes.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR047 — Explicit sharing confirmation, no automated disclosure
**Traces from:** FR047 (IA047)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
TR046's grant write only ever originates from a direct, explicit API call the sharing party initiates — no scheduled job, connection-progress milestone, or other automated trigger is capable of calling this endpoint. Both parties receive a Notification Bridge confirmation; the grant event is individually audited with actor/timestamp.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR048 — Family-contact sharing requires two independently-resolved AuthzContexts
**Traces from:** FR048 (IA048)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`PATCH /connections/{id}/share/family-contact` explicitly resolves **two separate `AuthzContext` calls** — one for the candidate performing the UI action, one for the specific family member whose contact is being shared — and requires both to grant before the share proceeds. This is modeled as two sequential `authz.resolve()` calls in the endpoint's own code, not one combined check with an embedded family-flag, per IA048's explicit recommendation given this is one of the highest integration-risk items in the module.

**Constraints surfaced**
Flagged by IA048 as a higher-integration-risk item precisely because the two-context requirement is easy to under-implement as a single check — recommend a dedicated Step 8/10 review specifically confirming both `authz.resolve()` calls are present and independently enforced, not inferred from a passing test alone.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR049 — In-platform messaging, accepted-connection precondition
**Traces from:** FR049 (IA049)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /messages` (Communication, `mangaly_communication` schema) requires the sender's `AuthzContext` to resolve against an `accepted` connection state (TR043/TR044) — messaging with no prior contact-info exchange is the default, intended path, not a special case. Client-queueable; honors TR102's idempotency-key middleware (a retried send after connectivity loss must not create a duplicate message row).

**Constraints surfaced** — none beyond TR102's cross-reference.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR050 — Minimal-necessity message processing; no permanent browsable log
**Traces from:** FR050 (IA050)
**Status:** Ready for Review | **Confidence:** Low — retention window itself externally gated. | **Priority:** Must

**Technical requirement**
`mangaly_communication` design ensures no application surface presents a permanent, freely browsable chat history beyond what the six named BR11 retention-justification purposes require; a background lifecycle job (with the failure-alerting behavior specified in TR054) enforces whatever retention window is legally set. **Build now:** the behavioral commitment and the job scaffolding. **Do not build now:** a specific numeric retention duration.

**Constraints surfaced**
Same as `v1-decisions.md`'s own framing: exact retention window and legal-hold classification require formal DPDP Act legal sign-off — a named, external, non-engineering dependency. This tech req does not clear FR050 for production launch without that sign-off; it is not a new blocker, the same one `v1-decisions.md` already carries.

**Assumptions** — none beyond `v1-decisions.md`'s framing.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR051 — Application-level access restriction plus a named production DB-access-control review
**Traces from:** FR051 (IA051)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`mangaly_communication`'s message content has exactly one application-level read path: the Safety Intelligence pathway (TR064), case-scoped and individually logged (actor, case reference, timestamp) via Audit Bridge. No other component, including Operations, has a read method against this schema's message-content table.

**Constraints surfaced**
Per IA051: the application-layer control alone does not prove no engineer/operator role has ad hoc production SQL access to `mangaly_communication` — flag this explicitly to Step 8 as a required operational-infrastructure control (least-privilege production DB roles, no standing ad hoc query access) to be verified, not assumed to follow automatically from the application design. Group with TR067/TR071's identical finding for one combined Step 8 review.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR052 — Transactional-outbox audit logging for every communication event
**Traces from:** FR052 (IA052)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Every consequential Communication action (send, contact-exchange request/decision, capture-risk incident) publishes its domain event inside the same DB transaction as the state change (outbox pattern, `/MODULE-ARCHITECTURE-STANDARD.md` §6, CODING-GUIDE §4's literal code example). This is one of the two components CODING-GUIDE names as warranting the deepest test investment in the module (alongside the Authorization Engine) — build with that priority, not as an incidental side effect of the messaging endpoint.

**Constraints surfaced** — none; already correctly the module's own highest-priority test-investment area.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR053 — Evidence-retention exception, scoped and individually logged
**Traces from:** FR053 (IA053)
**Status:** Ready for Review | **Confidence:** Low — same DPDP gating as TR050. | **Priority:** Must

**Technical requirement**
The Safety Intelligence-triggered evidence-retention exception writes an individually-logged exception record (scope: this conversation only, never cross-conversation) into `mangaly_communication`, routed into an Operations case (BR16) for controlled human investigation. Scope/duration ceiling is a parameter read from configuration, not hardcoded, so it can be set once DPDP sign-off resolves it without a redeploy.

**Constraints surfaced** — same DPDP legal-gating dependency as TR050; build the mechanism now, do not clear for production launch without sign-off.
**Assumptions** — none beyond `v1-decisions.md`'s framing.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR054 — Legal-hold suspension of deletion; lifecycle-job failure alerting
**Traces from:** FR054 (IA054)
**Status:** Ready for Review | **Confidence:** Low — legal-hold mechanics DPDP-gated; failure-alerting is not. | **Priority:** Must

**Technical requirement**
The retention/lifecycle background job checks for an active legal-hold flag on a conversation before any deletion action — a held conversation is structurally skipped, not merely expected to be skipped by correct scheduling. The job publishes a failure alert (routed to Operations, per DEC-V1-007) on any run that errors, times out, or partially completes — build and test this failure-alerting path now, independent of the still-open legal-hold scope question, per IA054's own recommendation that this protects against a real, independent operational risk.

**Constraints surfaced** — legal-hold scope/duration remains DPDP-gated (same as TR050/TR053); failure-alerting reliability under a real infrastructure outage is a Step 8 concern.
**Assumptions** — none beyond `v1-decisions.md`'s framing.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR055 — No exclusivity/seriousness model on conversations
**Traces from:** FR055 (IA055)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`mangaly_communication`'s conversation table has no seriousness-score or exclusivity-state column, and multiple concurrent conversations per candidate are fully supported with no cross-conversation constraint.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR056 — Android FLAG_SECURE capture-risk mitigation; honest platform-asymmetry disclosure
**Traces from:** FR056 (IA056)
**Status:** Ready for Review | **Confidence:** Medium — specific mechanisms confirmed available; effectiveness inherently partial. | **Priority:** Should

**Technical requirement**
The Android client applies `FLAG_SECURE` on the messaging window (a genuine OS-level block on screenshot/recording/casting for that window). The iOS client relies on the OS's after-the-fact screenshot-taken notification only — there is no iOS prevention primitive to build against. UI copy states risk-reduction, not guarantee, and must not imply the two platforms have equivalent protection.

**Constraints surfaced**
Per IA056's live research: this asymmetry is confirmed, permanent, and does not survive a second physical device photographing the screen on either platform, or a rooted/jailbroken device — the disclosure copy must reflect this honestly rather than treat both platforms as equivalent.

**Assumptions** — specific mechanisms remain BR11 DEC-003's own implementation-stage decision; this tech req narrows it to the two concretely available platform primitives.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR057 — Request contact information, on-behalf-of check
**Traces from:** FR057 (IA057)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /contact-exchange/request` (Communication's contact-exchange sub-flow) resolves the requester's `AuthzContext` (candidate or authorized-on-behalf-of family member) before creating the request; audited with requester identity/timestamp. Client-queueable; honors TR102's idempotency middleware.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR058 — Recipient-only decision authority, even within one Home Circle
**Traces from:** FR058 (IA058)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`PATCH /contact-exchange/{id}` (accept/decline) requires the deciding `AuthzContext` to be the recipient's own — the Authorization Engine's resolution explicitly checks `requester_id != decider_id` even when both belong to the same Home Circle, rather than treating "any authorized family member" as interchangeable. Full requester/decider/timestamp/content chain is audited. Client-queueable; honors TR102's idempotency middleware.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR059 — Single-channel disclosure only; no proxy-signal auto-reveal
**Traces from:** FR059 (IA059)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Sharing one contact channel (phone) never reveals another (email) in the same or any subsequent response — each channel is its own independently-gated field in the contact-exchange response model. No scheduled/automated job or elapsed-time/message-count trigger exists anywhere capable of calling the disclosure path — confirmed as a negative-dependency contract check (no such job is registered in the scheduler).

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR060 — Candidate-controlled, non-automatic Home Circle involvement timing
**Traces from:** FR060 (IA060)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /connections/{id}/involve-home-circle` is the sole trigger for scoping a specific connection to Home Circle visibility — no message-count, elapsed-time, or connection-stage threshold anywhere calls this automatically, verified as a negative-dependency check (no scheduled job or event subscriber targets this path besides the explicit candidate-initiated call).

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR061 — Discovery-level family involvement is independent of connection-level involvement
**Traces from:** FR061 (IA061)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
A family member's general Discovery-level `AuthzContext` grant carries **no implicit** connection-level grant — TR060's endpoint is the only path to per-connection Home Circle scoping, resolved as its own independent authorization decision regardless of the family member's other, unrelated grants. Prior private messages (TR049) are never retroactively exposed once family involvement is scoped in — Communication's message-read path continues to check the reader's own connection-level grant, not a broader "family is now involved" flag.

**Constraints surfaced**
Flagged by IA061 (alongside TR048/TR062) as a higher-integration-risk item — the "already involved elsewhere, so treat as involved here" shortcut is a realistic implementation mistake; recommend explicit code-review attention here, not just test coverage.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR062 — Family-to-family introduction as two independently-resolved exposures
**Traces from:** FR062 (IA062)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /connections/{id}/introduce-families` resolves **two separate `AuthzContext` calls** — Family A's exposure to Family B, and Family B's exposure to Family A — as two independent authorization decisions, never one combined "introduction happened" event that implicitly grants both sides. Same modeling pattern as TR048.

**Constraints surfaced**
Same recommendation as TR048: this is the highest-sensitivity transition point BR13 names — model explicitly as two `authz.resolve()` calls, verify both are present at code review, not inferred from a passing test alone.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR063 — Universal, non-downgradable reporting entry point
**Traces from:** FR063 (IA063)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /safety/report` (Safety Intelligence) is exposed as a shared API contract every screen/surface component is required to wire a UI entry point to — enforced by a Step 3/4-derived screen-inventory checklist item (per IA063's own recommendation) rather than left to each screen's own implementer to remember. Report triage never references "no automated-detection signal fired" as a dismissal criterion — this is a structural rule in the triage query (absence of an automated-flag column being used as a filter condition).

**Constraints surfaced**
Per IA063: recommend Step 3/4's screen-inventory discipline be reapplied as an ongoing checklist for every future screen, since nothing currently re-checks this automatically once a new screen ships after this point.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR064 — Bounded detection scope, repository-layer enforced
**Traces from:** FR064 (IA064)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Safety Intelligence's repository layer (`mangaly_safety`) has **no method capable of querying `mangaly_home_circle` or `mangaly_trust` tables at all** — an absence, per CODING-GUIDE §7, not a method that happens not to be called. Detection analyzes only message metadata and text against the 15 named DEC-V1-006 categories; photo/video content is never automatically scanned (a reported photo/video routes to human review only). Any AI-derived signal (conditional on ADR-009) carries a mandatory `inference: true` label, same schema pattern as TR028.

**Constraints surfaced** — none; CODING-GUIDE §7 already specifies the enforcement mechanism precisely enough to implement directly.
**Assumptions** — none beyond DEC-V1-006.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR065 — Graduated response pipeline, with on-call paging and CSAM reporting actually wired
**Traces from:** FR065 (IA065 — single most consequential finding in Impact Analysis)
**Status:** Ready for Review | **Confidence:** High for pipeline mechanics; the operational-readiness gap below is the item's real risk. | **Priority:** Must

**Technical requirement**
Safety Intelligence's five-stage pipeline (nudge → acknowledge/restrict → human-review → block+page → CSAM-report, per DEC-V1-006's tiers) is implemented as an explicit state machine in `mangaly_safety`, with each tier's SLA clock (24h/2h/36h per IT Rules 2021; immediate for Tier 4) started at classification time, not at human-review pickup time. **Tier 3/4 classification auto-fires two integrations that must exist as real, provisioned dependencies before this pipeline can be considered complete, not merely "the pipeline exists":** (a) an on-call paging call to a PagerDuty-class service (Operations component, `config/paging.py`, per CODING-GUIDE §2 — vendor is a procurement choice, the auto-fire trigger contract is fixed here); (b) for suspected CSAM specifically, an automatic case creation plus a structured hand-off packet (flagged content, provenance/source metadata, reporting-candidate/account identifiers) routed to cybercrime.gov.in and/or the SJPU, fired in parallel with the internal block, per POCSO Rules 2020 Rule 11(2) — never sequenced after internal investigation completes.

**Constraints surfaced**
Per IA065: DEC-V1-006/DEC-V1-007 already name the small on-call rotation's Tier 3/4 SLA risk as real and unresolved — this tech req's own completion criterion is explicitly **both** the state machine **and** these two integrations being live and load-tested against realistic case-arrival rates (a Step 8 Security & Performance and Step 13 Monitoring responsibility this tech req hands off explicitly, not silently assumes). Do not treat "the five stages are coded" as equivalent to "the Tier 3/4 exits are reachable in production."

**Assumptions** — none beyond DEC-V1-006/DEC-V1-007/DEC-V1-009's own framing.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR066 — Safety triage never references Trust/Verification status
**Traces from:** FR066 (IA066)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Same repository-layer-absence pattern as TR064: Safety Intelligence's triage/prioritization query has no join or lookup into `mangaly_trust`'s verification-status data — a verified candidate's case receives no priority adjustment based on that status.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR067 — Tightly controlled safety access, application-level plus named DB-access review
**Traces from:** FR067 (IA067)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Safety Intelligence case data is readable only via the case-scoped Operations investigation path (TR072/TR074) — no general-monitoring query surface exists. Every access individually logged via Audit Bridge.

**Constraints surfaced**
Same operational database-access-control finding as TR051 — group with TR051/TR071 for one combined Step 8 production-DB-access-control review, per IA067's own cross-reference.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR068 — Severity taxonomy consumed as fixed configuration, not re-derived per component
**Traces from:** FR068 (IA068)
**Status:** Ready for Review | **Confidence:** High — FR's own gap now closed by DEC-V1-006. | **Priority:** Must

**Technical requirement**
DEC-V1-006's four-tier taxonomy and SLA table is implemented as a single versioned configuration object (`config/thresholds.py`-adjacent, e.g. `config/safety_severity.py`) that Safety Intelligence (classification) and Operations (SLA-clock enforcement, TR065/TR072–076) both read from — never independently re-encoded in each consuming component.

**Constraints surfaced**
Per IA068: this taxonomy's *definition* being resolved is distinct from its Tier 3/4 exits' *operational readiness* (TR065) — track as two separate release gates, not one.

**Assumptions** — none beyond DEC-V1-006.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR069 — Consequential-action audit events via lint-enforced publish discipline
**Traces from:** FR069 (IA069)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Every mutating endpoint across all 11 schema-owning business-logic components publishes a domain event (transactional outbox) capturing actor, capacity (candidate/family/admin), and the resolved `AuthzContext` that authorized the action — consumed by the Audit Bridge, which forwards to the platform Audit Log Store (ADR-011) rather than keeping a local copy.

**Constraints surfaced**
Per IA069: enforce "every new mutating endpoint must publish a corresponding domain event" as a **lint rule**, not a code-review reminder — consistent with this module's existing preference for lint-enforced discipline over convention (`/MODULE-ARCHITECTURE-STANDARD.md` §3's import-boundary precedent). This closes the completeness-risk class named across IA012/IA063/IA069/IA083/IA088 for future additions specifically for the audit-event dimension.

**Assumptions** — storage substrate may be shared platform infrastructure (Audit Log Store, ADR-011); this tech req governs what must be logged, not where it physically lives.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR070 — Append-only audit trail (platform property, not re-implemented)
**Traces from:** FR070 (IA070)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Revocation, change, and dispute events publish new audit records referencing the original (never overwriting or deleting it) — relies on the Audit Log Store's own append-only guarantee (ADR-011, platform-level), not a Mangaly-specific re-implementation of that property.

**Constraints surfaced** — none; correctly an architecture-level property this tech req consumes rather than re-derives.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR071 — Audit trail denied to end-users; case-scoped, self-logged admin query
**Traces from:** FR071 (IA071)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
No end-user-facing endpoint exposes another member's audit trail — the Authorization Engine's deny-by-default baseline covers this without a special-case rule. The admin query endpoint (Operations) is case-scoped (returns only records tied to an active case reference) and itself generates an audit record of the query (actor, case reference, timestamp).

**Constraints surfaced**
Same operational database-access-control finding as TR051/TR067 — group all three for one combined Step 8 review, per IA071's own cross-reference.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR072 — Verification admin workflow against DEC-V1-007's fixed states
**Traces from:** FR072 (IA072)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Operations (`mangaly_operations` schema) implements DEC-V1-007's workflow (intake→triage→assignment→investigation→decision→audit→appeal) as an explicit state machine for verification cases specifically, with a `mark_incomplete` / `request_more_evidence` transition distinct from approve/deny (prevents premature decisions). Decision outcomes write back to Trust & Verification's own evidence display (TR035) via the Operations→Trust interface call, not a direct cross-schema write.

**Constraints surfaced** — none beyond DEC-V1-007's own already-fixed states.
**Assumptions** — none beyond DEC-V1-007.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR073 — False-relationship dispute workflow, Tier 2 SLA
**Traces from:** FR073 (IA073)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
The same Operations state machine (TR072) handles false-relationship disputes under DEC-V1-006's Tier 2 SLA (24h acknowledge / 36h resolve). Withheld-access mechanism reuses TR010/TR011's implementation — not a third, independently-built variant.

**Constraints surfaced** — same residual-access-latency caveat already named at TR010/TR011.
**Assumptions** — none beyond DEC-V1-006/DEC-V1-007.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR074 — Abuse/fraud investigation with attributable restriction/block/escalation
**Traces from:** FR074 (IA074)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Operations' investigation workflow for Safety-sourced cases (TR065) records every restriction/block/escalation action with full actor attribution (admin identity, case reference) via Audit Bridge — a precondition for FR076's own "never disclosed publicly" rule, which depends on this attribution chain existing.

**Constraints surfaced**
Tier 3/4 operational-reachability caveat carried forward unchanged from TR065 — not re-litigated here.

**Assumptions** — none beyond DEC-V1-006/DEC-V1-007.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR075 — Appeals workflow; reviewer-independence as a named, honest constraint
**Traces from:** FR075 (IA075)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Every restriction/block/deny decision type has a corresponding `POST /operations/cases/{id}/appeal` path. The workflow attempts to assign a different operator than the original decision-maker where staffing allows (a soft preference in the assignment logic, not a hard database constraint, per DEC-V1-007's own "where staffing allows" qualifier) — same evidence standard applies to the appeal review regardless of reviewer identity.

**Constraints surfaced**
Per IA075: reviewer independence under the current small on-call staffing model is a genuine, accepted operational limitation, not something Step 7 can engineer around — surface this explicitly to whoever owns Mangaly's operational staffing plan, not just engineering.

**Assumptions** — none beyond DEC-V1-007's own stated trade-off.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR076 — 100% admin-action audit coverage; no all-access role, structurally enforced
**Traces from:** FR076 (IA076)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Every Operations mutation publishes an audit event (same lint-enforced discipline as TR069, applied specifically to admin actions). The authorization data model's role definitions have **no role capable of referencing "all cases"** — every operator role's scope is a bounded case-type/queue reference, enforced as a schema-level constraint (no `scope = *` value is a valid enum member), not a policy convention, per IA076's own recommendation for structural over conventional enforcement.

**Constraints surfaced** — none beyond the structural-enforcement mechanism this tech req already fixes.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR077 — Agent access: no component built, per BR17's explicit deferral
**Traces from:** FR077 (IA077)
**Status:** Ready for Review | **Confidence:** Low — deliberately deferred, not a build gap. | **Priority:** Deferred (BR17)

**Technical requirement**
No implementation work at this build cycle. This tech req exists only to state the confirmation Impact Analysis already performed: no other tech req in this file (TR001–TR102 collectively) introduces any Agent-identity type, Agent-scoped authorization grant, or Agent-attributed audit record. When BR17's own gate (time and adoption data) opens this for a future build cycle, the future component would extend Identity Bridge (Agent identity type), Authorization Engine (per-family/per-candidate Agent scoping model), and Audit Bridge (per-Agent attribution) — named here only so a future engineer has the correct extension points, not as work scheduled now.

**Constraints surfaced** — none; this is a confirmed non-build, not an open item requiring resolution now.
**Assumptions** — describes required behavior for if/when this deferred capability is built, per BR17 DEC-001.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR078 — Discovery ranking formula structurally has zero Agent-status term
**Traces from:** FR078 (IA078)
**Status:** Ready for Review | **Confidence:** Low — same deferred-capability caveat as TR077. | **Priority:** Deferred (BR17)

**Technical requirement**
DEC-V1-002's ranking weight configuration (TR026) is verified by inspection to have no Agent-status term today. This tech req's only actionable requirement now: any future ranking-adjacent feature proposal (e.g., a "professional-assisted" badge) must be checked against TR026's fixed weight list before shipping, specifically because this FR's guarantee depends on that list never silently growing a new term.

**Constraints surfaced**
Recommend Step 10 include this check in the same regression suite that guards TR022's no-popularity-signal rule, per IA078's own recommendation — both are "verify a specific input never entered the ranking formula" checks.

**Assumptions** — none beyond BR17 DEC-001.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR079 — Deliberate-action-only search conclusion
**Traces from:** FR079 (IA079)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`PATCH /profile/lifecycle/conclude` (Lifecycle & Outcomes, `mangaly_lifecycle` schema) is the sole path to a `concluded` state — no inactivity-duration job, engagement-scoring feature, or other inferred-from-behavior mechanism is capable of calling it, verified as a negative-dependency check (no scheduled job targets this transition).

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR080 — Concluded-profile exclusion without historical data loss
**Traces from:** FR080 (IA080)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Discovery and Compatibility Engine's eligibility queries explicitly exclude `mangaly_lifecycle.status = concluded` profiles (an additional filter alongside TR003's tier gate). No historical connection/accountability record referencing a concluded profile is deleted or invalidated — Audit Bridge's append-only guarantee (TR070) applies unchanged.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR081 — Reactivation, freshness-window verification skip, and the Dashboard activity-summary event contract
**Traces from:** FR081 (IA081)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`PATCH /profile/lifecycle/reactivate` checks Trust & Verification's freshness window (per BR08's existing rules, unchanged, not bypassed) before deciding whether re-verification is required. Every lifecycle transition (conclude/reactivate) publishes an audit event (outbox). This endpoint is also the sole publisher of the `mangaly.activity_summary` event to Dashboard (MOD05) via the Message Broker — the **event schema must be explicitly defined at this step**, containing only a privacy-filtered summary (e.g., lifecycle-state changed, timestamp) and never raw match/profile/connection data, per `/ARCHITECTURE.md`'s own resolved constraint for this edge.

**Constraints surfaced**
Per IA081: this is the one place Mangaly's data crosses its isolation boundary at all — define the event schema explicitly now (not left implicit) and have Step 8 verify the payload against the "never raw match/profile data" constraint before this edge goes live.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR082 — Success-story invitation, per-party independent consent
**Traces from:** FR082 (IA082)
**Status:** Ready for Review | **Confidence:** Medium — Could-priority, no source-document citation. | **Priority:** Could

**Technical requirement**
`POST /lifecycle/success-story/invite` (Lifecycle & Outcomes) requires the BR18 conclusion state as precondition, then requires **each party's own explicit, independent consent** — never inferred from the conclusion action itself or from one party's consent alone.

**Constraints surfaced**
Per IA082: Could-priority, build after the Must-priority FR001–FR088 core is complete and stable, not in parallel with it.

**Assumptions** — none beyond BR19 DEC-001.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR083 — Zero account-status effect from decline; revocable, audited consent
**Traces from:** FR083 (IA083)
**Status:** Ready for Review | **Confidence:** Medium — same BR19 caveat. | **Priority:** Could

**Technical requirement**
Declining a success-story invitation writes no field anywhere that any other component's logic reads (verified as a negative-dependency contract test, same pattern as TR012). Consent grant/modify/revoke are each individually audited. A takedown mechanism for an already-published, later-revoked story is deferred until the publication channel (in-app/website/social) is actually chosen, per BR19's own Assumptions — building a takedown integration against an undetermined destination is explicitly out of scope for now.

**Constraints surfaced**
Per IA083: finalize the takedown mechanism only once the publication-channel decision is made; do not build against an undetermined destination.

**Assumptions** — none beyond BR19 Assumptions.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR084 — Published story: manual review plus an automated pre-publication data-minimization scan
**Traces from:** FR084 (IA084)
**Status:** Ready for Review | **Confidence:** Medium — same BR19 caveat. | **Priority:** Could

**Technical requirement**
The success-story publication payload is assembled from an explicit allow-list of fields (never a general serialize-everything approach), structurally excluding Home Circle membership details, private Communication content, and Trust & Verification contact details beyond explicit approval. In addition to the required manual pre-publication review, add an **automated structural check** that the assembled payload contains no field sourced from these three excluded categories — the same defense-in-depth principle this module already applies to authorization (RLS beneath application logic), per IA084's own recommendation.

**Constraints surfaced** — none beyond the automated-scan addition this tech req already specifies.
**Assumptions** — publication channel is a later marketing/distribution decision outside this FR, per BR19 Assumptions.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR085 — Optional, non-blocking safety guidance using DEC-V1-008's fixed copy
**Traces from:** FR085 (IA085)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Should

**Technical requirement**
Lifecycle & Outcomes presents DEC-V1-008's five-point guidance copy before an in-person introduction milestone, as a dismissable, non-blocking prompt — no gate on any subsequent action.

**Constraints surfaced**
Per DEC-V1-008/IA085: only the surrounding disclaimer/liability-framing language (not the five bullet points themselves) needs a final legal pass before production — a pre-launch check, not a build blocker.

**Assumptions** — guidance is informational content, not a platform-mediated live-safety feature, per BR20 Assumptions.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR086 — Manual-only "meeting occurred" note
**Traces from:** FR086 (IA086)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Should

**Technical requirement**
`POST /connections/{id}/meeting-note` is the sole write path for this note — no message-pattern-change inference, engagement-scoring heuristic, or other automated signal can create one, verified as a negative-dependency check.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR087 — Post-meeting reporting uses the identical BR14 pipeline, no weaker path
**Traces from:** FR087 (IA087)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
The post-meeting report entry point calls the exact same `POST /safety/report` endpoint (TR063) with an optional meeting-context reference — there is no separate "post-meeting feedback" endpoint, workflow, or SLA tier. A contract test asserts both entry points route into the identical pipeline instance.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR088 — Structural absence of relationship-progress/scheduling features
**Traces from:** FR088 (IA088)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`mangaly_lifecycle` has no field or table beyond the BR18 conclusion state and TR086's meeting note — no scheduling, chaperone-coordination, or relationship-status-progression data model exists anywhere in the module, verified as a schema-introspection absence check across all 14 components.

**Constraints surfaced**
Per IA088: add this boundary explicitly to whatever product-roadmap review checklist future feature proposals go through, since a well-meaning "helpful" feature (e.g., in-app meeting scheduling) is the realistic path by which this non-goal erodes without deliberate intent.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR089 — Person-level language preference, non-gating
**Traces from:** FR089 (IA089)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Should

**Technical requirement**
`mangaly_profile.language_preference` is a person-level (not session/device-level) column, read by Discovery, Compatibility, and Trust & Verification's rendering layers via the shared platform i18n library (ADR-010) for locale-aware response shaping. Does not gate profile creation (TR001).

**Constraints surfaced** — none; the shared i18n library's own reliability is a platform-level concern outside this file's scope.
**Assumptions** — rendering/translation mechanics that consume this preference are Common Platform infrastructure (ADR-010); this tech req only fixes that the preference exists as person-level profile data.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR090 — Splash/launch session bootstrap
**Traces from:** FR090 (IA090)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
Client-side routing checks session/token validity via the Identity Bridge on launch; on network failure or expired token, falls back to Login rather than blocking indefinitely — a routine, not edge-case, condition for this module's tier-2/3-connectivity audience.

**Constraints surfaced** — none; session/token mechanics themselves are Common Platform identity infrastructure.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR091 — First-run onboarding, content-consistent with Help & Support
**Traces from:** FR091 (IA091)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Should

**Technical requirement**
Onboarding content is client-side only (no backend business logic), fully skippable, never re-displayed after first dismissal (a client-persisted flag). Content is sourced from the same content bank Help & Support (TR100) reads from, to avoid drift between the two.

**Constraints surfaced** — none.
**Assumptions** — content is illustrative/explanatory only, not a data-collection step.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR092 — Interim account sign-up (Identity Bridge-owned), named migration debt
**Traces from:** FR092 (IA092)
**Status:** Ready for Review | **Confidence:** Medium — genuine, disclosed architectural interim. | **Priority:** Must

**Technical requirement**
`POST /auth/signup` (Identity Bridge) builds Mangaly's own minimal credential/session store — the only viable choice given Mangaly's build-order position ahead of a Common Platform Identity module (ADR-016/017). Validates duplicate-identifier and weak-credential rejection. Calls FR095's OTP verification (TR095) before activating the account.

**Constraints surfaced**
Per IA092/`v1-decisions.md`'s "Known technical debt": this interim system will require migrating live credentials/sessions into a future platform-wide Identity & Trust Service once one exists — a genuinely high-risk future operation, named explicitly now (per the standing convention this pipeline uses for disclosed-not-hidden risk) so it is planned, not discovered later. No action required of this build beyond building FR092 exactly as specified.

**Assumptions** — the underlying credential-storage/session infrastructure is intended to become Common Platform once that module exists.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR093 — Login with structural anti-enumeration and rate-limiting
**Traces from:** FR093 (IA093)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /auth/login` (Identity Bridge) returns the **identical response body and HTTP status code** for "wrong password" and "no such account" — verified with a byte-for-byte response diff test (CODING-GUIDE §7), not a manual copy read. Rate-limits repeated failures per identifier by calling **TR037's canonical shared `rate_limiting/` utility** with its own key/window/limit parameters — this is the same implementation TR037 and TR095 call, not a separately-built counter.

**Constraints surfaced** — none; already precisely specified by CODING-GUIDE §7. The anti-enumeration response-shape logic itself should also be one shared function inside Identity Bridge's own `interface.py` (e.g. `generic_auth_error()`) that TR094 also calls, rather than each endpoint independently formatting the same response body — the same "don't re-derive a shared rule per call site" discipline this file already applies to rate-limiting (TR037) and the discoverability gate (TR003/TR027).
**Assumptions** — none beyond FR092's interim-system note.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR094 — Password reset with anti-enumeration and single-use, expiring tokens
**Traces from:** FR094 (IA094)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`POST /auth/reset` (Identity Bridge) calls the same shared `generic_auth_error()` function TR093 uses (see TR093's Constraints) for its own anti-enumeration response, rather than independently formatting an equivalent-looking response body. Reset tokens are single-use (invalidated on first use) and time-bound (short TTL), checked server-side before allowing a password change.

**Constraints surfaced** — none.
**Assumptions** — none beyond FR092's interim-system note.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR095 — OTP verification: correct DLT route, resend rate-limiting, fallback-channel budget
**Traces from:** FR095 (IA095)
**Status:** Ready for Review | **Confidence:** Medium — SMS delivery is a real, measured external reliability constraint. | **Priority:** Must

**Technical requirement**
`POST /auth/otp/verify` (Identity Bridge) validates OTP code/expiry/attempt-count; successful verification feeds Trust & Verification's account-authenticity layer (TR035). Resend is rate-limited per identifier by calling **TR037's canonical shared `rate_limiting/` utility** (same implementation as TR037/TR093, own key/window/limit) to prevent SMS-bombing abuse.

**Constraints surfaced**
Per IA095's live research: even a fully DLT-compliant transactional SMS has a documented ~5–8% single-channel non-delivery rate in India, most commonly from wrong-route selection (promotional vs. transactional) or a DLT template mismatch — both configuration errors, not random failures. Two concrete mitigations, named explicitly rather than left implicit: (1) register on the correct transactional/OTP DLT route specifically; (2) budget for an email or WhatsApp fallback channel for users whose SMS never arrives, to reach >99% effective delivery — this is a real reliability gap this pass surfaces, not a hypothetical one, and should be scoped as its own line item, not assumed solved by "we use an SMS provider."

**Assumptions** — underlying SMS/email delivery infrastructure is Common Platform per `modules.md`'s notification-delivery Shared Concern; the reliability finding applies regardless of which platform component owns the provider integration.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR096 — Location/notification permission priming, graceful degradation
**Traces from:** FR096 (IA096)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Should

**Technical requirement**
Declining location permission degrades locality-ranking input to Discovery's weighted formula (TR026) to "unavailable, weight redistributed" — never blocks any capability. Declining notification permission degrades to in-app-only inbox delivery (TR098) — never blocks any capability.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR097 — Navigation shell context switcher: server-authorized context list, client-side leak prevention
**Traces from:** FR097 (IA097)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Must

**Technical requirement**
`GET /me/contexts` (API layer, backed by Home Circle) returns the authenticated user's full list of participation contexts (self, or on-behalf-of a specific candidate), each carrying its own resolvable `AuthzContext`. The active context is always visibly displayed client-side. Any in-progress client-side form/draft state is explicitly cleared on context switch (a client-engineering requirement, not a server-authorization one) — this closes the cross-context data-leakage risk IA097 names as a common mobile-app defect class, distinct from and in addition to server-side authorization correctness.

**Constraints surfaced**
Per IA097: flag the client-side draft-clearing requirement for extra Step 9/10 implementation attention specifically because it is a client-side (not server-authorized) risk, harder to catch via server-side authorization tests alone.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR098 — Notification inbox against the resolved `mangaly_notification` schema
**Traces from:** FR098 (IA098 — architecture gap now resolved one layer up in `architecture.md`)
**Status:** Ready for Review | **Confidence:** High — schema ownership resolved. | **Priority:** Must

**Technical requirement**
`GET /notifications` and `PATCH /notifications/{id}/read` (Notification Bridge) read/write `mangaly_notification` — the schema `architecture.md`'s own 2026-09-12 follow-up revision assigns to the Notification Bridge specifically for in-app inbox persistence (distinct from the actual push/SMS/email delivery call, which stays a thin pass-through to the Common Platform Notification & Communication Service). Every component that publishes a notification-worthy domain event (Profile, Home Circle, Connection, Communication, Safety, Operations) has its event consumed here to create one inbox entry, independent of whether the underlying push delivery succeeded.

**Constraints surfaced**
Per IA098: event-type completeness (every named notification category actually produces an inbox entry) carries the same future-addition completeness risk as TR069 — apply the same lint-enforced "new event type must have a subscriber producing an inbox entry" discipline, not left to convention.

**Assumptions** — underlying push-delivery infrastructure is Common Platform; this tech req governs the in-app inbox record specifically.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR099 — Account & app settings, thin aggregator
**Traces from:** FR099 (IA099)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Should

**Technical requirement**
Settings screen's backing endpoints are thin reads/writes into already-owned data (Profile's language preference TR089, Home Circle's management entry point, Authorization Engine's pause/resume TR024) — no independent settings data model or business logic introduced here, avoiding a second source of truth for any of these values.

**Constraints surfaced** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR100 — Help & Support with safety-aware routing
**Traces from:** FR100 (IA100)
**Status:** Ready for Review | **Confidence:** High | **Priority:** Should

**Technical requirement**
`POST /support/ticket` (Operations) applies a keyword/category classifier at intake that detects a safety-concern description and **redirects it into the FR063 Safety reporting pipeline** (TR063), not a slower general-support queue — this routing check gets the same test-investment priority CODING-GUIDE reserves for the Authorization Engine and event bus, per IA100's own recommendation, given a routing miss here has the same downstream legal-SLA consequence (DEC-V1-006) as a Tier 3/4 case being handled late.

**Constraints surfaced**
Per IA100: given DEC-V1-006's legally-binding SLAs, a safety-urgent issue stuck in general support is a legal-SLA-miss risk, not merely a UX one — treat this routing logic as safety-critical code, not a convenience feature.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR101 — Logout and account deletion with DPDP-gated disclosure
**Traces from:** FR101 (IA101)
**Status:** Ready for Review | **Confidence:** Medium — deletion-vs-retention boundary DPDP-gated. | **Priority:** Must

**Technical requirement**
`POST /auth/logout` (session-only) is unconditional and immediate. `POST /account/delete` (Identity Bridge, coordinating with Communication/Trust/Home Circle's own retention rules) discloses to the user, before confirmation, whether any data will be retained (and why) or whether an active legal hold blocks full deletion — the disclosure mechanism is buildable now; the specific retention schedule it discloses is not, per the same DPDP gating as TR050/TR053/TR054. The deletion event itself is audited (BR15).

**Constraints surfaced** — same DPDP legal-gating dependency as TR050/TR053/TR054; not a new blocker.
**Assumptions** — none beyond FR053/FR054's framing.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

---

## TR102 — Cross-cutting mutation-endpoint idempotency middleware
**Traces from:** FR102 (IA102 — the second of the two Step-6-flagged architecture gaps, resolved here)
**Status:** Ready for Review | **Confidence:** Medium — client-side offline queue engineering is a genuinely nontrivial problem; the idempotency mechanism itself is fully specified. | **Priority:** Must

**Technical requirement**
Implement a shared `idempotency/` middleware at the API layer (per `/MODULE-ARCHITECTURE-STANDARD.md` §4b and `CODING-GUIDE.md`'s already-named project-structure entry) that every client-queueable mutation endpoint honors: the client generates and persists an idempotency key alongside each locally-queued write; the API layer stores `(idempotency_key, endpoint, result)` and, on a repeated key, returns the original result **without re-executing the mutation**. This is a single, shared implementation — not re-derived per component. **Endpoints required to honor this middleware:** TR002 (profile category save), TR042 (connection request), TR043 (accept/decline), TR046 (per-category share grant), TR047 (share confirmation), TR049 (message send), TR057 (contact-exchange request), TR058 (contact-exchange decision). The client-side offline mutation queue itself (local persistence, retry-on-reconnect) is a separate, genuinely nontrivial mobile-engineering component, built to guarantee eventual delivery of a queued write, not just idempotency on retry.

**Constraints surfaced**
Per IA102: this is a **distinct failure mode from "the write was lost"** — without this middleware, a retried request after a connectivity drop can silently create a duplicate record. `05-test-scenarios.md`'s TS228–229 test that a write eventually succeeds or clearly fails; they do **not** test duplicate-write prevention specifically — Step 10 must add a dedicated test per queueable endpoint asserting a repeated idempotency key does not duplicate the underlying record, per CODING-GUIDE §7's own explicit instruction not to assume TS228–229 already proves this.

**Assumptions** — none beyond what's stated above.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Architect — [x] Approved — krishna kategaru, 2026-09-13

## Definition of Done — self-check (Tech Reqs only; ER Model/Step 7a not gated on)

- Coverage check has no blank rows — 102/102 FRs have a tech req (TR001–TR102). Pass.
- Every item's Status/Confidence/Priority fields are complete — no blank field in any of the 102 items. Pass.
- Every tech req is consistent with `architecture.md`'s component/schema boundaries and `/MODULE-ARCHITECTURE-STANDARD.md`'s generic patterns — no tech req invents a data-ownership or authorization approach those files hadn't already fixed; verified item-by-item during drafting (see Revision history). Pass.
- No open blockers — every genuinely external-gated dependency (DPDP sign-off, verification-vendor selection, the personality-assessment instrument, the deferred BR17 layer, on-call-paging/CSAM-channel vendor choice) is named with an owner in its own item, consistent with `06-impact-analysis.md`'s and `v1-decisions.md`'s own established treatment of these categories. Pass.
- This file does not draft an ER diagram, schema DDL, or migration, and does not seal `07a-er-model.md` — that remains Step 7a's exclusive scope, invoked only once this file is Sealed by explicit human approval.

## Approval

Architect — [ ] Approved — name, date
