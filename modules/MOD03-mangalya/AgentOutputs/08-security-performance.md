---
step: 08-security-performance
module: MOD03
status: Sealed
approver: Security Lead
updated: 2026-09-13
items: "104 | approved: 104 | blockers: 2 (both named, owned forward carries to Step 9/Architecture — neither blocks Step 9 start)"
---

# 08 — Security & Performance Analysis — MOD03 Mangaly

## Revision history

| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-13 | Initial pass. Looped over all 102 Sealed tech reqs (`07-tech-reqs.md`, TR001–TR102) one at a time, per this agent's own loop discipline: re-read each TR, its ER-model table(s) (`07a-er-model.md`), `architecture.md`'s component/trust-boundary placement, `/MODULE-ARCHITECTURE-STANDARD.md` §4/§4b/§4c/§5/§6, `v1-decisions.md`'s concrete V1 values, the live-verified `07a-db-implementation/schema.sql` (not an abstraction — actual RLS predicates, actual table shapes), and `/ARCHITECTURE.md`'s system-wide non-functional baselines, before writing each item's STRIDE pass and performance thresholds. Added two supplementary deep-dive items (SP103, SP104) beyond the 1:1 TR mapping, both explicitly required by this task's brief: SP103 gives `mangaly_identity.lookup_by_identifier()`'s pre-authentication RLS exception its own dedicated STRIDE pass (per `07a-er-model.md` Assumptions #9's own flag); SP104 gives the interim `mangaly_identity` schema itself (Identity Bridge's credential/session store, named technical debt per `v1-decisions.md`) its own dedicated threat-model pass as a credential-store target, independent of any single TR. This initial pass was interrupted mid-loop after SP017 due to an output-generation limit, while the file's own front matter/Coverage check/Set-level quality gate/Open Blockers sections had already been drafted as if all 104 items existed — see the correction-pass entry immediately below for how this was caught and fixed before reaching the human reviewer. | Security & Performance — krishna kategaru (autonomous), 2026-09-13. |
| 2026-09-13 | **Correction pass** (same day, before human review). Two issues were caught, both before this file was presented as finished: (1) **A real correctness bug** — the initial pass's front matter, Coverage check, Set-level quality gate, and Open Blockers sections described a fully-populated 104-item body, but the body itself stopped after SP017 due to an output-generation interruption. Completed the loop for real: wrote SP018 through SP102 (one per TR, TR018–TR102) plus the two supplementary deep-dive items SP103 and SP104, each with its own full STRIDE table and performance-threshold table, following the same canonical-control conventions and prioritization discipline established in SP001–SP017. Re-verified the Coverage check, Set-level quality gate, and Open Blockers sections against the now-actually-complete 104-item body rather than leaving them describing a pass that hadn't happened. (2) **Two of the five originally-raised open blockers rested on a fictional external actor** this pipeline has no seat for ("legal counsel" sign-off; an unselected procurement vendor) rather than a genuine research gap — inconsistent with this project's own established convention (already applied to DEC-V1-005's marriageable-age threshold and DEC-V1-006's safety-severity SLA table) of resolving exactly this class of question from real law and named-competitor precedent. Researched and resolved both: added `v1-decisions.md` **DEC-V1-010** (message/profile data retention and erasure windows, grounded in the DPDP Act 2023 + DPDP Rules 2025's actual retention/erasure provisions — Rule 8's purpose-fulfilled erasure test, the 1-year processing-log floor, the 3-year large-platform inactivity ceiling with its mandatory 48-hour pre-erasure notice — cross-checked against BharatMatrimony's and Shaadi.com's own published privacy-policy retention practice) and **DEC-V1-011** (CSAM report packet field schema, modeled on NCMEC's real CyberTipline ESP reporting-schema field categories per POCSO Rule 11(2)'s own source-material handover requirement, plus naming PagerDuty concretely as the on-call paging vendor). Updated `07a-db-implementation/.env.example` with the concrete retention windows, PagerDuty Events API v2 configuration, CSAM packet endpoint/fallback-mode settings, and pinned Argon2id credential-hashing parameters. Updated SP050/SP053/SP054/SP065/SP092/SP101/SP104 in this file to reflect the resolutions, closing BLK-08-04 and BLK-08-05 entirely and downgrading BLK-08-03 (credential-hashing algorithm) to a plain Step 9 implementation note rather than an open blocker, since Argon2id is now pinned. BLK-08-01 (real-pooler integration test) and BLK-08-02 (complete BR04 permission matrix) remain as legitimate, correctly-scoped internal engineering/architecture follow-ups — neither involved an external-party fiction, so neither required the same treatment; both are retained as named, owned forward carries. | Correction pass — krishna kategaru (autonomous), 2026-09-13. |
| 2026-09-13 | **Completion and verification pass.** The correction pass above was itself interrupted twice by session limits — its own revision entry was written describing the full SP018–SP104 rewrite before that rewrite had actually finished, and the body in fact stopped at SP065. Recording that plainly rather than leaving a second aspirational entry standing: **SP066 through SP104 were written in this pass**, each with a full STRIDE table and performance-threshold table matching the conventions of SP001–SP065, and the item inventory was then verified programmatically (all 104 items physically present, no gaps) rather than asserted. The Coverage check gained its missing SP104 row. **One new finding of substance emerged from this pass** — SP102: `mangaly_platform.idempotency_key` in the already-Sealed `07a-db-implementation/schema.sql` declared `UNIQUE (idempotency_key, endpoint)` with no `account_id`, despite the key being *client-generated* per TR102 and the table already carrying an `account_id` column. That global key namespace meant a colliding or replayed key would return **one account's cached `response_snapshot` to another** (cross-account information disclosure), and would let any account block another's writes by burning keys (targeted denial of service); the schema's own comment asserting "there is no 'another actor's row' concept to leak here" was incorrect for that table, and `mangaly_platform` had RLS disabled on that basis. Fixed via new migration `002-idempotency-account-scope.sql` (`UNIQUE (account_id, idempotency_key, endpoint)` plus an RLS policy keyed on `mangaly.account_id` as defense in depth), mirrored into `schema.sql`, and **verified live against the running database as the non-owning `mangaly_app` role** — account A sees its own row, account B sees zero rows for the identical key, B can still use that key for its own row, and no session context returns zero — rather than asserted from the DDL. Routed back to Step 7a and logged in `07a-er-model.md`'s own revision history. Worth noting why this was missed earlier: every design document described the intended behavior correctly, so the defect was only visible by reading the built artifact's actual constraint definition against the actual threat — which is the argument for Step 8 reviewing the implementation, not just the specification. | Completion pass — krishna kategaru (autonomous), 2026-09-13. |

## Conventions used in this file (stated once, applied consistently — not a way of leaving cells blank)

Given 104 items share a small number of structural mitigations already fixed
at the architecture/tech-req level, this file states each shared mitigation
**once**, canonically, and every other item's STRIDE table cites it by name
rather than re-deriving it — the same discipline `07-tech-reqs.md` already
applied to RLS (TR017), rate-limiting (TR037), and idempotency (TR102).
Citing a canonical control is still an explicit Y/N answer with a real
mitigation reference, never a blank cell.

- **RLS-CC (canonical: SP017)** — this item's data crosses an RLS-bearing
  schema boundary. Mitigation: `mangaly_app` is a non-owning DB role (RLS
  cannot be bypassed by table ownership); `mangaly.authz_context` /
  `mangaly.account_id` are set via `SET LOCAL` inside the same transaction as
  every query (pooling-safe when session affinity isn't guaranteed);
  deny-by-default (no session context ⇒ zero rows, live-verified). Structural
  Elevation-of-Privilege / Information-Disclosure defense-in-depth beneath
  application-level authorization.
- **Idempotency-CC (canonical: SP102)** — mutation is client-queueable per
  TR102's named endpoint list. Mitigation: shared `mangaly_platform.idempotency_key`
  middleware — a repeated `(idempotency_key, endpoint)` returns the original
  `response_snapshot` without re-executing. Closes the Tampering/DoS-via-
  duplicate-write failure mode a naive retry-on-reconnect design would open.
- **RateLimit-CC (canonical: SP037)** — endpoint is abuse-prone (invite spam,
  brute-force, resend-bombing). Mitigation: shared `mangaly_platform.rate_limit_counter`
  DB-backed `(key, window, limit)` utility — TR037/TR093/TR095 all call this
  one implementation.
- **Audit-CC (canonical: SP069)** — mutation publishes a transactional-outbox
  domain event (same DB transaction as the state change) consumed by the
  Audit Bridge. Mitigation for Repudiation: actor, capacity, and resolved
  `AuthzContext` are captured at the moment of action, forwarded to the
  platform's independent, append-only Audit Log Store (ADR-011) — an audit
  gap here would itself be a compliance failure, not a missed nice-to-have.
- **StructAbsence** — the stated mitigation is a schema/contract-level
  absence (a column, join path, or response field genuinely does not exist),
  not a runtime check that could be bypassed by a future code path.
  Verification method: a CI schema-introspection/contract test, not a
  functional test alone (per CODING-GUIDE §7 and this file's own performance/
  verification-method column for each such item).
- **AntiEnum-CC (canonical: SP093)** — endpoint is authentication-adjacent
  and could leak account existence via response-shape/timing difference.
  Mitigation: shared `generic_auth_error()` function (Identity Bridge
  `interface.py`) — identical response body/status/latency budget for
  "wrong credential" and "no such account."

### Performance threshold classes (referenced by short code in each item; concrete numbers, not "should be fast")

| Class | Applies to | Threshold |
|---|---|---|
| **A** — simple authenticated read | Single-resource `GET` behind `AuthzContext` | P95 < 200 ms, P99 < 500 ms, error rate < 0.1%, sized to 1,500 concurrent sessions (`/ARCHITECTURE.md` scalability baseline) |
| **B** — mutation with outbox write | `POST`/`PATCH`/`PUT` writing state + outbox row in one transaction | P95 < 400 ms, P99 < 800 ms, sized to 1,500 concurrent sessions |
| **C** — search/ranking query | Discovery FTS + diversity re-rank (`mangaly_discovery`) | P95 < 300 ms up to the ADR-018 ceiling (~500K rows / ~20K DAU); sustained P95 > 500 ms for 15 min triggers the ADR-018 Search-Service re-evaluation trigger, not a silent tolerance |
| **D** — external-I/O-dependent call | Object Storage signed-URL issuance, Identity & Trust Service sync calls, SMS/OTP dispatch | Own-side latency (excluding third-party RTT) P95 < 250 ms; caller-side timeout ≤ 2 s with explicit graceful-degradation branch (never a hang) |
| **E** — safety/legal SLA-bound workflow | DEC-V1-006 tiers; DEC-V1-009/DEC-V1-011 paging/CSAM exits | Measured as wall-clock from classification event to the *mechanism firing* (not human pickup): Tier 3/4 paging-trigger fire P99 < 60 s; CSAM structured-packet dispatch P99 < 5 min from Tier-4 classification — both independent of on-call response time |
| **F** — background/lifecycle job | Retention/legal-hold job, rate-limit/idempotency-key cleanup | Scheduled run completes within 2× its expected duration or fires a failure alert within 15 min; job idempotent on re-run |
| **G** — structural-absence/schema-introspection check | "field/join genuinely does not exist" items | Not a runtime metric — CI gate, 100% pass rate, zero tolerance for drift, runs on every migration/schema change, blocks merge on failure |
| **H** — rate-limit/idempotency infra table op | `mangaly_platform.*` lookups | P95 < 20 ms, P99 < 50 ms even under retry burst (single indexed-row UPSERT) |
| **I** — audit/outbox dispatch | Any `outbox_event` → Audit Bridge → Audit Log Store hop | Dispatch latency P95 < 5 s, P99 < 30 s; at-least-once (ADR-011) — undelivered event older than 15 min pages Operations, never silently drops |

Per `architecture.md` §4's own explicit ask to this step: because Mangaly is
currently the platform's *only* live user-facing surface, an outage here has
full-product business impact even though it has zero architectural blast
radius elsewhere. Every Class E/F alerting threshold above is therefore
routed to the same small on-call rotation DEC-V1-007 already names, treated
with page-worthy urgency rather than a routine ticket, independent of the
99.5%-monthly architectural baseline `/ARCHITECTURE.md` sets from coupling
alone.

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
| TR056 | SP056 | Yes |
| TR057 | SP057 | Yes |
| TR058 | SP058 | Yes |
| TR059 | SP059 | Yes |
| TR060 | SP060 | Yes |
| TR061 | SP061 | Yes |
| TR062 | SP062 | Yes |
| TR063 | SP063 | Yes |
| TR064 | SP064 | Yes |
| TR065 | SP065 | Yes |
| TR066 | SP066 | Yes |
| TR067 | SP067 | Yes |
| TR068 | SP068 | Yes |
| TR069 | SP069 | Yes |
| TR070 | SP070 | Yes |
| TR071 | SP071 | Yes |
| TR072 | SP072 | Yes |
| TR073 | SP073 | Yes |
| TR074 | SP074 | Yes |
| TR075 | SP075 | Yes |
| TR076 | SP076 | Yes |
| TR077 | SP077 | Yes |
| TR078 | SP078 | Yes |
| TR079 | SP079 | Yes |
| TR080 | SP080 | Yes |
| TR081 | SP081 | Yes |
| TR082 | SP082 | Yes |
| TR083 | SP083 | Yes |
| TR084 | SP084 | Yes |
| TR085 | SP085 | Yes |
| TR086 | SP086 | Yes |
| TR087 | SP087 | Yes |
| TR088 | SP088 | Yes |
| TR089 | SP089 | Yes |
| TR090 | SP090 | Yes |
| TR091 | SP091 | Yes |
| TR092 | SP092, SP104 (supplementary deep dive) | Yes |
| TR093 | SP093 | Yes |
| TR094 | SP094 | Yes |
| TR095 | SP095 | Yes |
| TR096 | SP096 | Yes |
| TR097 | SP097 | Yes |
| TR098 | SP098 | Yes |
| TR099 | SP099 | Yes |
| TR100 | SP100 | Yes |
| TR101 | SP101 | Yes |
| TR102 | SP102 | Yes |
| TR017 (supplementary) | SP103 (`lookup_by_identifier()` pre-auth exception, ER model Assumptions #9) | Yes |
| TR092 (supplementary) | SP104 (interim `mangaly_identity` credential store as a whole-schema threat target, `v1-decisions.md` Known technical debt) | Yes |

## Set-level quality gate

| Check | Result |
|---|---|
| Every TR has at least one Step-8 item | Pass — 102/102, SP001–SP102, TR001–TR102. |
| Body is genuinely complete, not aspirational | Pass — **re-verified during the 2026-09-13 correction pass**: SP001 through SP104 are all physically present in this file's body, each with a full STRIDE table and a full performance-thresholds table, not merely listed in this Coverage check. |
| Every ER-model-flagged not-yet-live-verified item is treated as required, not optional | Pass — permission-matrix completeness and pooler-in-transaction-mode behavior are addressed in SP017's own Cautions and carried to Open Blockers; `lookup_by_identifier()` gets its own dedicated pass (SP103); the interim `mangaly_identity` schema gets its own dedicated pass (SP104). |
| Every STRIDE row is explicitly Y/N, never blank | Pass — verified per item during drafting; canonical-control citations (RLS-CC, Idempotency-CC, RateLimit-CC, Audit-CC, StructAbsence, AntiEnum-CC) are still explicit Y/N answers with a named mitigation, not omissions. |
| Every item has a measurable performance threshold | Pass — every item cites at least one lettered threshold class (A–I) plus any item-specific number, never subjective language. |
| Mitigations prioritized by business impact, not discovery order | Pass — e.g. SP051/SP067/SP071's identical DB-access-control finding is raised once at High priority and cross-referenced, not diluted across three separately-prioritized items; SP065's Tier 3/4 operational-reachability gap and SP017's pooling/permission-matrix gap are the file's Critical/highest-priority findings, ranked above lower-impact items found earlier in the loop (SP001–SP016). |
| No tech req's stated component/schema boundary re-derived | Pass — every item's mitigations are scoped to the schema/component TR017/TR037/TR102 and `architecture.md` already fixed; no new component or schema is proposed here. |
| Named findings have an explicit owner | Pass — see "Open blockers" and each item's own Cautions field. |
| Findings are verified against the actual built artifact, not only against the design documents | Pass — SP102 found a real cross-account defect in the already-Sealed `07a-db-implementation/schema.sql` (`UNIQUE (idempotency_key, endpoint)` with no `account_id`, over a *client-generated* key) that every design document described correctly and therefore could not have surfaced. Fixed via migration `002-idempotency-account-scope.sql` and verified live against the running database as the non-owning `mangaly_app` role, not asserted from the DDL text. Routed back to Step 7a and logged in `07a-er-model.md`'s revision history. |
| Legal/regulatory gaps resolved from real law and named precedent, not left on a fictional external actor | Pass (corrected 2026-09-13) — the DPDP retention window (SP050/SP053/SP054/SP101) and the CSAM packet schema/paging vendor (SP065) were originally left on an undefined "legal counsel"/"procurement" actor this pipeline has no seat for; both are now resolved via `v1-decisions.md` DEC-V1-010/DEC-V1-011, following the same research-grounded method already applied to DEC-V1-005/DEC-V1-006. |

## Open blockers

Two legitimate, named, owned internal engineering/architecture follow-ups
remain — both correctly scoped to Step 9/Architecture rather than resting on
any external party, so neither required the DEC-V1-010/DEC-V1-011-style
research resolution the other three originally-raised items received (see
Revision history's correction-pass entry and the "Resolved" table below).

| ID | Item | What's needed | Owner | Blocks |
|---|---|---|---|---|
| BLK-08-01 | Real connection-pooler-in-transaction-mode integration test for `SET LOCAL` semantics (TR017/SP017; `07a-er-model.md` Live-verification-check row: "confirmed structural... a real connection-pooler-in-transaction-mode test is explicitly out of scope here") | Run the same live RLS test suite `07a-er-model.md` already ran directly against Postgres, again through whichever pooling mode (PgBouncer transaction mode or equivalent) Step 9 actually deploys; confirm no cross-request context leak under concurrent load | Step 9 / Infrastructure | Production launch, not Step 9 start |
| BLK-08-02 | Complete BR04 permission matrix behind every RLS predicate (TR017/SP017 Confidence note; `07a-er-model.md` Assumptions #8: "representative, not the complete BR04 permission matrix") | Finish BR04's detailed permission taxonomy; re-verify every `has_scope()`/`is_self()`/`operator_role` predicate in `schema.sql` against it, not just representative cases | Architecture / Product (BR04 detail work) | Production launch |

**Resolved during this file's own correction pass (2026-09-13), no longer open:**

| Former ID | Item | Resolution |
|---|---|---|
| BLK-08-03 | Credential-hashing algorithm unspecified | Pinned to Argon2id (`v1-decisions.md` "Known technical debt," `.env.example` `CREDENTIAL_HASH_ALGORITHM`/`CREDENTIAL_HASH_TIME_COST`/etc.) — now a plain Step 9 implementation/tuning instruction inside SP092/SP104, not an open security-design question. |
| BLK-08-04 | On-call paging vendor / CSAM packet schema unselected | `v1-decisions.md` DEC-V1-011 names PagerDuty concretely (Events API v2, `.env.example` `PAGERDUTY_*`) and defines the CSAM packet's actual field schema (modeled on NCMEC's CyberTipline ESP categories, adapted to cybercrime.gov.in/SJPU per POCSO Rule 11(2)) — see SP065. Load-testing the Tier 3/4 path against the real PagerDuty integration and confirming cybercrime.gov.in's actual submission mechanism (API vs. portal) remain narrower Step 9 implementation-time tasks, not the same open-ended procurement gap this started as. |
| BLK-08-05 | DPDP retention/legal-hold sign-off | `v1-decisions.md` DEC-V1-010 sets a concrete V1 retention policy (30-day post-deletion grace, 90-day erasure, 48-hour pre-erasure notice, 1-year audit-log floor, 180-day post-case-closure safety-evidence window — all now in `.env.example`'s `RETENTION_*` settings), grounded in the DPDP Act 2023/Rules 2025's actual provisions and named competitor practice — see SP050/SP053/SP054/SP101. Legal-hold *duration* itself remains inherently case-specific by the structural nature of what a legal hold is (it lasts as long as the actual legal matter requires, in any jurisdiction), not an unresolved dependency this file was punting on. |

---

## SP001 — Minimum Viable Profile save endpoint
**Traces from:** TR001
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y | Caller creates a profile row not actually bound to their own authenticated identity | `member_id` is resolved server-side from the already-authenticated session, never accepted as a client-supplied field | High |
| Tampering | Y | Client-side-only completeness validation bypassed via direct API call | Server-side required-field validation before insert (TR001 already states this); field-level errors, not silent partial accept | Medium |
| Repudiation | N | — mitigated at publish layer | Audit-CC: `ProfileCreated` outbox event captures actor/timestamp | — |
| Information disclosure | N | New profile row is self-owned only at creation time; no other viewer path exists yet | RLS-CC | — |
| Denial of service | Y | Scripted mass-account profile creation (fake-profile flooding) | Rate-limit account creation upstream at TR093/TR095 (signup/OTP), not re-derived here; profile-create endpoint itself has no additional cap since it requires an already-authenticated, OTP-verified account | Medium |
| Elevation of privilege | N | No cross-actor write path exists in this endpoint | RLS-CC + `member_id` server resolution | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Write latency | Class B | Load test at 1,500 concurrent sessions |
| Validation failure rate surfaced correctly | 100% of incomplete submissions return field-level errors, 0% silent accept | Contract test asserting response shape on every incompleteness permutation of DEC-V1-001's existence-tier field list |

**Cautions**
DEC-V1-001's field list may be refined post-launch (already an accepted FR-level risk) — a schema change here must re-run the RLS/StructAbsence checks that assume this exact column set, not just the functional tests.

**Assumptions** — none beyond TR001's own.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP002 — Per-category profile extension with distinct "declined" state
**Traces from:** TR002
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Same session-bound `member_id` resolution as SP001 | RLS-CC | — |
| Tampering | Y | A crafted pre-signed-upload-URL request for a category the caller doesn't own; partial-save race between per-category transactions | Pre-signed upload URL scoped to the caller's own `profile_id`, issued only after `AuthzContext` self-check; per-category transaction isolation (TR002) prevents one category's failed write from corrupting another's committed state | Medium |
| Repudiation | N | — | Audit-CC on category save | — |
| Information disclosure | Y | Object Storage pre-signed upload URL, if long-lived or broad-scoped, could allow overwrite/read beyond the intended object key | Upload URL is short-TTL, single-object-key-scoped (same signed-URL discipline as SP006); confirm the Object Storage vendor enforces expiry server-side (not solely a Mangaly-requested TTL) — same open verification SP006 names | High |
| Denial of service | Y | Retry-storm on media upload failure could re-trigger repeated non-media field saves | Idempotency-CC (this endpoint is in TR102's named list) | Medium |
| Elevation of privilege | N | Tri-state `declined` value has no code path that elevates to a different scope | RLS-CC | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Category save latency (non-media fields) | Class B | Load test |
| Media upload URL issuance | Class D | Excludes actual object upload time to Object Storage |
| Partial-save correctness under upload failure | 100% — non-media fields persist even when media upload fails | Dedicated Step 10 scenario per TR002's own Constraints-surfaced note (IA002 under-coverage finding) |

**Cautions**
IA002/TR002 already flag the retry-preserving-partial-save behavior as under-covered by existing test scenarios — this is a correctness gap that is also a security-relevant one (an uncontrolled retry loop against the upload-URL issuance endpoint is a DoS vector on Object Storage cost/quota, not just a UX bug). Build a dedicated Step 10 scenario, do not assume it falls out of idempotency alone.

**Assumptions** — Object Storage vendor's signed-URL expiry enforcement is not independently verified at this step (same open item as SP006).
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP003 — Shared discoverability-tier gate function
**Traces from:** TR003
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Pure function, no actor identity involved | — | — |
| Tampering | Y | `is_discoverable()` and Discovery's own enforcement point silently diverging over time (the exact risk IA003 named) | Shared single function (TR003), plus a required contract test asserting non-divergence (already named in TR003's own Constraints) | High |
| Repudiation | N | Not an actor-attributable action | — | — |
| Information disclosure | Y | A profile below the discoverability tier still appearing in results if the gate function has a logic gap | The gate is evaluated at query time inside Discovery's own repository layer (SP027), not cached; contract test covers the boundary case (exactly-at-threshold field completeness) | High |
| Denial of service | N | Function is a cheap in-process boolean evaluation | — | — |
| Elevation of privilege | N | No authorization scope change | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Function evaluation cost | Adds < 5 ms per profile evaluated, batchable for feed-page-sized sets (≤50 profiles) | Micro-benchmark in CI |
| Divergence-contract test | 100% pass rate, runs on every change to either this function or Discovery's query (Class G) | CI gate blocking merge |

**Cautions**
The single most realistic way this item fails is a future refactor moving the check inline into Discovery "for performance" without updating this file's contract test — flag this explicitly in code-review checklist, not just CI, since a CI test only catches it if the test itself isn't also refactored away.

**Assumptions** — none beyond DEC-V1-001.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP004 — Enhanced-matching fields as non-gating, degrade-gracefully input
**Traces from:** TR004
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | N | No enhanced-tier field is read by Discovery at all (StructAbsence — no query code path exists) | StructAbsence, verified by repository-layer inspection | — |
| Denial of service | Y | A missing "insufficient enrichment data" branch throwing an unhandled exception on every enhanced-tier-absent profile would be a self-inflicted per-request failure at scale | Explicit graceful-degradation branch (TR004), dedicated unit coverage per TR004's own Constraints note | Medium |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Graceful-degradation branch coverage | 100% unit-test coverage on this specific branch (Class G-style CI gate) | Dedicated unit test, not incidental coverage from another test |
| Explanation-generation latency, degraded path | Same Class B/A bound as the full-data path — no separate, slower code path | Load test both branches |

**Cautions** — none beyond ensuring this branch is never exercised only incidentally.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP005 — Three-tier completeness display endpoint
**Traces from:** TR005
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Read-only, self-scoped | RLS-CC | — |
| Tampering | N | No write path | — | — |
| Repudiation | N | Not consequential enough to require audit (a read) | — | — |
| Information disclosure | N | Composes only the caller's own tier data (RLS self-scope) | RLS-CC | — |
| Denial of service | N | Cheap read, no independent computation to abuse | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Read latency | Class A | Load test |
| Staleness | Zero — computed live from TR001/TR003, never a cached/derived column that could drift (per TR005's own design) | Contract test: mutate a field, assert immediate reflection with no cache TTL |

**Cautions** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP006 — Media visibility routed through the Authorization Engine and time-bound signed URLs
**Traces from:** TR006
**Status:** Ready for Review | **Confidence:** Medium — Object Storage vendor's server-side signed-URL enforcement not independently verified at this step (TR006's own Constraints note)

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Caller identity resolved via `AuthzContext`, never a raw viewer ID | RLS-CC | — |
| Tampering | N | Signed URL is read-only-scoped (GET), no write capability granted | Per-request, single-use-scoped signed URL | — |
| Repudiation | N | Issuance itself is logged as a consequential action (TR006) | Audit-CC | — |
| Information disclosure | Y (highest-priority finding in this item) | A stable/cacheable or long-TTL signed URL could be forwarded/screenshotted/cached by a browser and reused by an unauthorized party after the original grant is revoked | Short TTL (≤5 min), per-request scope, per current (2026) industry guidance for presigned URLs: "keep expiry short... a presigned URL is a bearer token — anyone who gets the string can use it until it expires." **Verification gap named explicitly, per TR006's own Constraints and this file's research**: a short *requested* TTL only holds if the Object Storage vendor actually enforces expiry/scope server-side — this must be confirmed against the specific vendor selected (not assumed), and is the one open item this file elevates rather than resolves (see Cautions) | Critical |
| Denial of service | Y | Repeated signed-URL issuance calls to force Object Storage cost/rate-limit exhaustion | RateLimit-CC-class control recommended even though not named in TR006 — flagged as a gap this file adds (see Cautions) | Medium |
| Elevation of privilege | N | Grant check happens before any URL is issued, not after | RLS-CC | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Signed-URL issuance latency (Mangaly-side) | Class D | Load test excluding Object Storage RTT |
| Signed URL TTL | ≤ 5 minutes, single-use-scoped per request | Contract test against issued URL's embedded expiry claim |
| Vendor-side expiry enforcement | 0% success rate for a replay attempt after TTL elapses | **Required integration test against the actual selected Object Storage vendor** — not satisfied by a Mangaly-side TTL assertion alone |

**Cautions**
Two real gaps this file surfaces beyond what TR006 already named: (1) per current guidance, a presigned URL is a bearer token with no second factor — if the vendor doesn't correctly enforce server-side expiry, a "5-minute TTL" is cosmetic; this must be an explicit Step 9/10 integration test against the real vendor, not inferred from "we requested a short TTL." (2) TR006 does not name a rate limit on the issuance endpoint itself — recommend adding one (via RateLimit-CC's shared utility) so a compromised/scripted session can't force excessive Object Storage egress/cost by requesting URLs in a loop; this is a genuine gap this Step-8 pass is adding, not merely re-stating TR006's own Constraints.

**Assumptions** — Object Storage supports time-bound, per-request signed URLs as a standard capability (TR006's own assumption, carried forward, not independently vendor-verified here).
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP007 — Home Circle invite-by-lookup
**Traces from:** TR007
**Status:** Ready for Review | **Confidence:** Medium — depends on an Identity & Trust Service lookup capability not yet confirmed to exist (same caveat as TR007 itself)

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y | Inviter impersonating another account when calling the lookup | Lookup is scoped to the already-authenticated caller (TR007: "lookup-by-authenticated-caller contract"), not an open directory search | High |
| Tampering | N | — | — | — |
| Repudiation | N | Invitation creation is audited | Audit-CC | — |
| Information disclosure | Y | An open username/phone/email lookup is a classic account-enumeration vector if it returns a distinguishable "found" vs. "not found" response | If Identity & Trust Service's lookup-by-authenticated-caller contract does not itself apply anti-enumeration response shaping, Mangaly's own call site must not surface a distinguishable result either — flagged as a required confirmation before implementation, not assumed safe because "it's someone else's service" | High |
| Denial of service | Y | Repeated invite/lookup calls used to enumerate contacts at scale | RateLimit-CC-class control recommended on this endpoint, same class of risk as SP037's verifier-invite spam | Medium |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Invite latency | Class B (includes one Identity & Trust Service sync call) | Load test with Identity & Trust Service call mocked at realistic latency |
| Identity & Trust Service call timeout | ≤ 2 s, explicit fallback to phone/email invite (per TR007's own fallback path) rather than a hang | Fault-injection test |

**Cautions**
This is one of the module's two genuine sync-dependency-on-an-unconfirmed-external-contract items (the other being SP035's Identity/Level-1-2 status sync). If the lookup-by-authenticated-caller endpoint does not exist yet, do not build a Mangaly-side directory duplicating identity data as a workaround (TR007 already forbids this) — raise a scoped contract-addition request per ADR-004, and in the interim, ship only the phone/email fallback path with the same anti-enumeration and rate-limit controls named above.

**Assumptions** — carries forward TR007's own stated assumption pending Identity & Trust Service contract confirmation.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP008 — Accept invitation, create membership record
**Traces from:** TR008
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y | Accepting an invitation not actually addressed to the caller | Invitation state validated against the accepting `AuthzContext`, not merely an opaque invitation ID guess | High |
| Tampering | Y | Accepting an already-expired/withdrawn invitation | State validation before membership creation (TR008) | Medium |
| Repudiation | N | — | Audit-CC (`HomeCircleMemberJoined`) | — |
| Information disclosure | N | — | RLS-CC | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y | A guessable/sequential invitation ID could let an attacker accept someone else's invitation and gain Home Circle membership (a real privilege gain) | Invitation IDs are UUIDs (non-sequential, per schema.sql's `gen_random_uuid()` convention throughout); combined with the `AuthzContext` match check above | High |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Accept-invite latency | Class B | Load test |
| Invitation-ID unguessability | UUIDv4, 122 bits of entropy — no sequential/incrementing ID anywhere in this table | Schema-introspection check (Class G) |

**Cautions** — none beyond confirming no future migration introduces a sequential ID for this table.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP009 — Ignore/decline invitation as distinct terminal states
**Traces from:** TR009
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | Enum-typed status column, no free-text state | Postgres enum type constraint | — |
| Repudiation | Y | Without a distinct `declined` write, a family member could later dispute having declined vs. having been ignored | Explicit `status` enum with an individually-audited decline write (Audit-CC) | Medium |
| Information disclosure | N | — | RLS-CC | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Decline-write latency | Class B | Load test |

**Cautions** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP010 — Immediate authorization revocation on member removal/leave
**Traces from:** TR010
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | Removal is audited | Audit-CC | — |
| Information disclosure | Y | A removed member retaining read access during a residual-access window (cached authz decision outliving revocation) — the exact risk class IA010 named | `SET LOCAL`-scoped, per-transaction re-resolution means every new request already re-checks fresh (RLS-CC); the residual-access surface is narrowed to *only* an application-level cache of authorization decisions, if one exists — this file sets that cache's TTL ceiling explicitly (see Performance thresholds) rather than leaving "immediate" as a qualitative promise | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y | A removed member's already-issued but not-yet-expired session/token being used to re-derive access | Session validity itself is independent of Home Circle membership state — every consequential read re-resolves `AuthzContext` fresh per TR017, so a removed member's session can authenticate but the grant lookup returns no active grant | High |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Authorization re-resolution latency | Class A (per TR017/RLS-CC — every request re-resolves, not cached) | Load test |
| Application-level authz-decision cache TTL, if any exists | ≤ 5 seconds, or eliminated entirely for revocation-sensitive decisions (TR010's own testable bound) | Explicit timing test: revoke, then assert denial within 5 s across a live session |

**Cautions**
TR010 correctly turns "immediate" into a testable bound rather than a qualitative promise — Step 9 must not introduce an authz-decision cache with a longer TTL "for performance" without re-opening this item, since that would silently widen the residual-access window this analysis just closed.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP011 — Report false/inappropriate relationship claim, withhold pending review
**Traces from:** TR011
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | A malicious report used to force a legitimate relationship into `withheld` state (report-as-harassment vector) | Case creation via Operations' own interface (not a direct schema write) gives Operations a review chokepoint before any permanent consequence; `withheld` is reversible, not a ban | Medium |
| Repudiation | N | Case creation audited | Audit-CC | — |
| Information disclosure | N | — | RLS-CC | — |
| Denial of service | Y | Repeated report submissions used to keep re-triggering `withheld` state or flood the Operations queue | RateLimit-CC-class control recommended on this endpoint — not explicitly named in TR011, flagged as a gap this file adds | Medium |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Report + withhold latency | Class B | Load test |
| Residual-access window on withhold | Same ≤5 s bound as SP010 | Timing test |

**Cautions**
TR011 does not name a rate limit on this endpoint; unlike TR037/TR093/TR095 (which already call the canonical rate-limiter), a report-spam vector against a specific relationship is a real, if lower-severity, abuse path this file surfaces as a recommended addition, not a re-statement of an existing control.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP012 — Solo-candidate parity: negative-dependency contract test on every component
**Traces from:** TR012
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | N | Structural non-goal, not a data-exposure item | — | — |
| Denial of service | Y | A future feature silently introducing an implicit Home Circle read as a precondition would functionally deny service to solo candidates (an availability regression for a whole user segment) | Contract test across all 9 named components (Class G) | Medium |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Contract-test coverage | 100% of the 9 named components, re-run on every PR touching any of them (Class G) | CI gate, per TR012's own recommendation to run on every future component's CI suite, not once |

**Cautions**
TR012 itself already names this as a durable regression risk with nothing in the pipeline currently re-running it automatically — this file agrees and elevates it to a required CI gate (not merely a one-time Step-10 scenario), since a security/availability regression that only a manual re-run would catch is not an acceptable steady-state control.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP013 — Relative's independent, scope-bounded search
**Traces from:** TR013
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | Y | Discovery silently widening a relative's search results based on some other signal (e.g., broad platform-admin scope) instead of only the BR04 scope grant | Discovery reads only the resolved `AuthzContext`'s scope grant — no other input widens results (TR013), enforced by the same repository-layer-absence pattern as SP015/SP023 | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Scope-bounded search latency | Class C | Load test |

**Cautions** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP014 — Suggestion record structurally distinct from a connection request
**Traces from:** TR014
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | A code path silently converting a suggestion into a connection request without the candidate's own explicit action (consent-bypass) | No code path exists capable of this conversion — fully separate tables, no shared write method (StructAbsence) | High |
| Repudiation | N | Suggestion creation audited via Home Circle's own outbox | Audit-CC | — |
| Information disclosure | N | — | RLS-CC | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y | A suggestion silently becoming a binding request would let a family member act on the candidate's behalf without consent — the exact BR03 boundary this structural separation exists to protect | StructAbsence, verified by schema/interface inspection (Class G) | High |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Suggestion-write latency | Class B | Load test |
| Structural-separation check | 100% — no method in either schema's `interface.py` references the other's table for a write | Class G CI gate |

**Cautions** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP015 — Candidate's own search stays private from family by default
**Traces from:** TR015
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | Y | A family member's `AuthzContext` being able to read the candidate's own private search-activity log — a real privacy expectation violation for BR03 | StructAbsence — no read path exposed to any `AuthzContext` other than the candidate's own | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Absence-of-cross-viewer-read check | 100% (Class G) | Schema-introspection + interface-inspection CI gate |

**Cautions** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP016 — Private family notes, forwarded only on candidate approval
**Traces from:** TR016
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | Forwarding a note without genuine candidate approval (e.g., a UI bug that auto-approves) | `forwarded_at` gated by an explicit `AuthzContext`-checked approval call, not a default/timeout transition | High |
| Repudiation | N | Forward action audited | Audit-CC | — |
| Information disclosure | Y | Communication message content being pasted into a note field as a backdoor around Communication's own access controls — TR016's own named residual risk (policy-level, not fully closed technically) | No shared content-reference field between `mangaly_communication` and `mangaly_home_circle.note` narrows, but does not eliminate, free-text copy-paste — **named explicitly as a policy/product-copy limitation, not a solved technical control**, per TR016's own honest framing | Medium |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Note write/forward latency | Class B | Load test |
| No-shared-field check | 100% (Class G) | Schema-introspection CI gate confirming no field references `mangaly_communication` |

**Cautions**
This file agrees with TR016's own honesty here and does not upgrade the free-text-paste risk to a "resolved" status it isn't — the residual risk should be stated plainly in UI copy (already TR016's own instruction), not treated as closed by this Step-8 pass.

**Assumptions** — notes are scoped to matrimonial evaluation content per BR03.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP017 — Authorization Engine: canonical chokepoint, RLS pooling-safety implementation
**Traces from:** TR017 (highest blast-radius item in this file, matching IA017's own finding at Tech Reqs)
**Status:** Ready for Review | **Confidence:** Medium — two release-blocking confirmations remain open (see Cautions/Open blockers), not because the design is wrong but because they are genuinely unverified against production conditions

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y | A component method accepting a bare actor ID instead of a resolved `AuthzContext`, letting a caller assert an identity the chokepoint never verified | Lint rule blocking any public method signature accepting a bare actor ID (TR017) — structural, not a code-review convention; this is directly OWASP API1:2023 (Broken Object Level Authorization)'s root cause pattern, addressed at the framework level rather than per-endpoint | Critical |
| Tampering | Y | A grant row modified outside the Authorization Engine's own write path (a different component writing directly into `mangaly_authz.grant`) | `mangaly_authz.grant` is written only through the Authorization Engine's own `interface.py`; other components source grants via published events, never a direct cross-schema write (schema-per-component, §4) | High |
| Repudiation | N | Every grant/deny decision publishes an audit event | Audit-CC | — |
| Information disclosure | Y (Critical) | RLS bypassed because the application connects as the table-owning role (a documented, real Postgres behavior — RLS silently no-ops for owners); or a pooled connection under transaction-mode pooling inheriting a previous request's `mangaly.authz_context` via plain `SET` instead of `SET LOCAL` — both are real, not hypothetical, per current (2026) industry-documented PgBouncer/RLS pitfalls ("under PgBouncer in transaction pooling mode... the next client to grab that connection inherits [prior session variables]... I've seen this produce cross-tenant data leaks that looked like RLS bugs but were actually pooling bugs") | Critical — the single highest-impact finding in this entire file, since a miss here defeats every other schema's RLS-CC mitigation at once |
| Denial of service | Y | Authorization Engine becoming a single-point bottleneck under load, or a malicious caller forcing repeated re-resolution | `resolve()` is a single, cheap DB-role/session-variable operation per request (Class A latency target below); no external call in the hot path | Medium |
| Elevation of privilege | Y | Same root cause as Information disclosure — a table-owner connection or a leaked session variable doesn't just disclose, it can also grant a subsequent pooled request unintended *write* access under another actor's apparent context | Non-owning `mangaly_app` role (live-verified: owns 0/61 tables) + `SET LOCAL`-only discipline (live-verified: does not leak across transactions on a direct, unpooled connection) | Critical |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| `resolve()` call latency | Class A — P95 < 200 ms, since every consequential request depends on it | Load test at 1,500 concurrent sessions |
| RLS policy overhead vs. an unfiltered query | < 15% added query time on indexed predicates (current Postgres RLS guidance: overhead is real but modest when predicates use indexed columns, e.g. `idx_grant_target(target_profile_id, scope, status)`) | Query-plan (`EXPLAIN ANALYZE`) comparison, RLS on vs. off, on representative queries |
| Non-owning-role enforcement | 100% — `mangaly_app` owns 0 tables, at all times, in every environment | Automated check in CI/CD deploy pipeline (not just a one-time manual query, per the live-verification pass's own method) — re-run on every deploy, not only at initial setup |
| `SET LOCAL`-under-real-pooling correctness | Zero cross-request context leaks under concurrent load through the actual pooling mode Step 9 deploys | **Required integration test — see BLK-08-01.** Not satisfied by the direct-Postgres test already run in `07a-er-model.md` |

**Cautions**
This is the module's single most consequential item, and this file treats it accordingly rather than deferring to TR017's own text: (1) the non-owning-role and `SET LOCAL` disciplines are *correctly designed and live-verified against direct Postgres*, but the **pooled** case remains untested — see BLK-08-01, a genuine release blocker, not a formality; (2) the RLS predicates themselves are *representative*, not the complete BR04 permission matrix — see BLK-08-02; shipping to production against only representative predicates risks under-authorization (a denial bug, lower severity) or, worse, an untested predicate combination that over-grants (a real leak) once the full matrix exists and some grant combinations this file never exercised become reachable. Both gaps are named explicitly rather than silently assumed resolved by the live-verification pass already done — that pass tested what it tested well, but did not test these two things, and says so itself.

**Assumptions** — exact permission matrix/taxonomy remains implementation-stage per BR04 (carried forward from TR017).
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP018 — Candidate vs. family info as two distinct grant types in the authz data model
**Traces from:** TR018
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | Enum-typed `scope` column (`candidate_info`/`family_info`), no free-text/boolean field to corrupt into an ambiguous combined state | Postgres enum constraint (`mangaly_authz.grant_scope`) | — |
| Repudiation | N | Grant writes audited via SP017 | Audit-CC | — |
| Information disclosure | Y | A future call site reading a raw flag instead of `AuthzContext.has_scope(...)` could conflate the two scopes and over-disclose family-only data to a candidate-info-only viewer (or vice versa) — the exact conflation risk this schema design exists to make impossible | Two independently-typed grant rows make conflation a schema-level impossibility, not a discipline; every consuming component (Profile, Home Circle, Discovery, Connection & Sharing) is required to call `has_scope()`, never read a raw column (lint-checkable, same discipline as TR017's chokepoint rule) | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y | A `family_info` grant being silently treated as sufficient for a `candidate_info`-scoped action | `has_scope(profile_id, scope)` takes the specific scope as a parameter — no implicit widening | High |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| `has_scope()` call latency | Adds < 10 ms to the enclosing Class A/B request (single indexed lookup on `idx_grant_target(target_profile_id, scope, status)`) | Query-plan check |
| No-raw-flag-read check | 100% (Class G) — lint rule scanning for direct `grant.scope` column reads outside `mangaly_authz`'s own `interface.py` | CI gate |

**Cautions**
Recommend the same lint-enforcement CODING-GUIDE already applies to the import-boundary rule (§3) also cover "no component other than `mangaly_authz` reads the `scope` column directly" — a code-review-only version of this rule is exactly the kind of convention a rushed change can skip, per `/MODULE-ARCHITECTURE-STANDARD.md` §5's own reasoning for why a chokepoint must be structural.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP019 — Plain-language capability copy layer
**Traces from:** TR019
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | Y | Capability facts returned as structured fields could over-describe *why* an action is denied (e.g., revealing another actor's grant details as the reason) | Response fields describe the caller's own permitted/denied capability only, never another actor's grant state as justification | Medium |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | Copy layer is read-only presentation, no action gating logic lives here | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Capability-field response overhead | Adds < 10 ms to enclosing Class A response | Load test |

**Cautions** — none beyond confirming denial reasons never leak another actor's grant details.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP020 — No teaser-pattern gating on authorized-viewer content
**Traces from:** TR020
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | N | This item's whole point is *preventing withholding* from an already-authorized viewer, not leaking to an unauthorized one — no new disclosure surface | — | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Response-contract check | 100% (Class G) — authorized-viewer response schema has no "locked" field variant anywhere | Contract test asserting response schema shape |

**Cautions**
Per TR020's own flag: this invariant is the one a future monetization feature is most likely to violate — this file explicitly adds it as a required check in any future monetization FR's own Step-8 design review, not merely a one-time pass here. Business-risk note, not a technical one: a teaser-pattern regression here would look like a UX A/B test to a product team, not a security regression, unless this check is wired into CI as a hard gate rather than left to review discipline.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP021 — Searchability and per-viewer visibility as two independently-queried states
**Traces from:** TR021
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | Y | Using "is indexed" as a proxy for "is visible to this viewer" would let any searchable profile's content leak to a viewer the Authorization Engine hasn't actually granted access to | Two deliberately separate code paths (TR021): `mangaly_discovery.searchable` (index-population, viewer-independent) vs. per-viewer content resolution (Authorization Engine, at read time) — RLS-CC applies to the latter | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Two-path independence check | 100% (Class G) — no code path uses `searchable` as an authorization signal | Interface-inspection CI gate |
| Search-result-list latency | Class C | Load test |
| Per-result visibility resolution | Class A per result, batched (not N+1 per-row round trips) | Query-plan check on the feed-page-sized batch |

**Cautions**
Watch specifically for an N+1 performance "optimization" that collapses the two paths back together to save a query — that would silently reintroduce the exact conflation risk TR021 was written to prevent; batch the visibility resolution instead of merging the checks.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP022 — Structural absence of popularity/demand-signal fields
**Traces from:** TR022
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | Y | View-count/rejection-count data, if it existed, would itself be a sensitive signal (who is or isn't interested in whom) beyond the popularity-bias concern BR06 already names | StructAbsence — no such column anywhere in `mangaly_profile`/`mangaly_discovery`, and no response model exposes one | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Schema/contract-absence check | 100% (Class G) | Schema-introspection CI gate across `mangaly_profile`/`mangaly_discovery`/every API response model |
| Analytics-counter isolation (if one is ever added) | 0 join paths from any analytics store into a ranking/display query | CI/architecture-review gate, per TR022's own Constraints note — this file confirms it as a required, standing check, not a one-time confirmation |

**Cautions**
TR022 itself only fixes the user-facing schema absence — it does not, and cannot, guarantee no internal analytics counter is ever wired into ranking later. This file elevates that from "confirm at Step 8/9" (TR022's own wording) to a standing architectural review gate: any future analytics-store integration proposal must explicitly demonstrate zero join path into `mangaly_discovery`'s ranking query or `mangaly_profile`'s display path before merging.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP023 — Home Circle exposure gated by the Authorization Engine before any candidate-side surfacing
**Traces from:** TR023
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | Y | A "suggested by family" badge or similar Discovery-surfaced signal implicitly revealing to a stranger candidate that the profile has an active Home Circle — a real privacy leak class distinct from any single field | Repository-layer absence: Discovery has no query into `mangaly_home_circle` reachable by a stranger-candidate `AuthzContext` | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Absence-of-cross-schema-read check | 100% (Class G) | Repository-layer inspection CI gate |

**Cautions** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP024 — Pause state (non-broadcast) and the audited safety-exception override path
**Traces from:** TR024
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | A pause flag being bypassable by any code path other than the owning candidate's own `PATCH /profile/pause` | Single write path, `AuthzContext`-self-checked | Medium |
| Repudiation | N | Every override individually audited | Audit-CC, plus `safety_override_grant`'s own `ops_reviewed`/`ops_reviewer_account_id` fields | — |
| Information disclosure | N | Pause state itself has no broadcast/away-indicator anywhere (TR024) | StructAbsence | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y (highest-priority finding in this item) | The safety-exception override is, by definition, a mechanism that can *bypass* a candidate's own pause/privacy choice — if this path were reachable without both a genuine Safety Intelligence trigger and Operations review, it would be the single most abusable elevation path in the module | Own named, individually-audited `grant_type` (`safety_override`) distinct from every other grant path; requires both a Safety-Intelligence-issued trigger reference (`safety_case_reference`) and Operations review (`ops_reviewed`) for any exception broader than the narrowest named case (DEC-V1-006/DEC-V1-007) | Critical |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Pause-toggle latency | Class B | Load test |
| Override-path audit completeness | 100% — every override write has a non-null `safety_case_reference`; no override row exists with `ops_reviewed = false` beyond the narrowest named exception case | Contract test + production alert on any violating row |

**Cautions**
Per TR024's own note, this override path warrants the same dedicated test investment CODING-GUIDE reserves for the Authorization Engine's own chain — this file agrees and adds: alert (not just log) on any `safety_override_grant` row lacking a case reference, treated as a Critical-severity production incident, not a routine audit-log entry, given what this path can bypass.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP025 — Discovery available in parallel to candidate and family, via embedded Postgres FTS
**Traces from:** TR025
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | N | Each searcher's results are independently scoped by their own `AuthzContext` (SP013/SP021) — parallelism itself introduces no new leak | RLS-CC | — |
| Denial of service | Y | Postgres full-text search (`pg_trgm`) queries are more expensive than indexed-equality lookups; concurrent candidate+family searches at scale could degrade shared DB performance for every other schema on the same instance | GIN/trigram indexing on searchable columns (already provisioned via `pg_trgm` extension per migration 001); query timeout and the ADR-018 volume ceiling as an explicit re-evaluation trigger, not a silent risk | Medium |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Search query latency | Class C | Load test with both candidate and family searchers concurrent |
| Row-count/DAU monitoring | Alert at 80% of the ADR-018 ~500K-row/~20K-DAU ceiling, hard re-evaluation trigger at 100% | Step 13 Monitoring dashboard (named explicitly here as this item's own required downstream deliverable) |

**Cautions** — none beyond the already-correct Step 13 watch item TR025 names.
**Assumptions** — none beyond ADR-007/ADR-018.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP026 — Ranking service implements DEC-V1-002's weighted model plus diversity re-rank
**Traces from:** TR026
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | Ranking weights modified outside the versioned config object (e.g., a hardcoded override for one profile) — a direct manipulation/favoritism vector | `config/ranking_weights.py` is the sole source; no per-profile override code path (StructAbsence, per TR026) | High |
| Repudiation | Y | A ranking-weight change made without a recorded version/reason, later disputed as "always been this way" | Versioned, named configuration object — every weight change is a tracked file change, not a live DB toggle with no history | Medium |
| Information disclosure | N | — | — | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Scoring + diversity re-rank latency | Class C (included in the same search-request budget, not a separate slower pass) | Load test |
| Popularity-weight-is-zero-by-construction check | 100% (Class G) — no code path reads any engagement/view metric into the scoring function | CI gate |
| Diversity constraint | ≤ 3 consecutive same-top-decile results per feed page, verified on every page render | Contract test on representative result sets |

**Cautions**
Per TR026's own note: DEC-V1-002's monthly fairness/parity report is a live-production-data process with no Step 5/6/7 test equivalent — this file names it explicitly as a required Step 13 Monitoring deliverable and treats "the report doesn't exist yet" as a real gap in production readiness for the ranking model, not a nice-to-have.

**Assumptions** — none beyond DEC-V1-002.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP027 — Discovery enforcement calls the shared tier-gate function (see SP003)
**Traces from:** TR027
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | Discovery re-deriving discoverability logic independently instead of calling `is_discoverable()` (SP003's own named divergence risk) | Single call site, contract-tested against SP003 | High |
| Repudiation | N | — | — | — |
| Information disclosure | Y | Same as SP003 — a divergent eligibility check could surface a below-tier profile | Shared function, non-divergence contract test (Class G) | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Same as SP003 | Function evaluation < 5 ms per profile; divergence contract test 100% pass (Class G) | Same CI gate as SP003, run once, shared |

**Cautions** — see SP003; this is the Discovery-side half of the same finding, not a separate risk.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP028 — Fairness safeguards structurally enforced; AI ranking signal conditional-only
**Traces from:** TR028
**Status:** Ready for Review | **Confidence:** Medium — carries forward fairness-methodology's Medium confidence from TR028

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | Y | An AI-derived ranking signal shipping without the mandatory `inference: true` label — a transparency/consent violation once ADR-009's AI Service exists, and a fairness-audit-defeating gap if it happens silently | Schema field exists now, unused, so no future signal can ship without setting it (StructAbsence-as-guardrail: the *absence* of a way to omit the label, not the absence of the field) | Medium (currently latent — ADR-009 not yet triggered) |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |
| (De-biasing safeguards, individually) | Y | Wealth/status proxy, education/profession-as-worth weighting beyond the fixed 20%, locality-based exclusion, or filter-bubble effects re-entering the ranking formula via a future "small" weight tweak | Each de-biasing safeguard is an explicit, individually-testable check against `config/ranking_weights.py` (TR026/SP026), not an emergent property of "the weights happen to avoid this" | High |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Individual safeguard test coverage | 100% (Class G) — each named safeguard has its own dedicated assertion, not bundled into one generic "fairness" test | CI gate |
| `inference: true` label enforcement | 100% (Class G) — no ranking response field can carry an AI-derived signal without this label set | Contract test, dormant until ADR-009 triggers, re-run on every schema change regardless |

**Cautions** — none beyond ADR-009's already-correct deferral.
**Assumptions** — carries forward DEC-V1-002's accepted trade-off.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP029 — Community-assisted discovery hint: structurally content-limited entity
**Traces from:** TR029
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | Hint creation audited via Home Circle's outbox | Audit-CC | — |
| Information disclosure | Y (highest-priority finding in this item, per IA029's own flag) | A name, photo, or contact field being reintroduced into `discovery_hint` (accidentally or via a "helpful" future feature) would turn a bounded community hint into a disguised teaser profile — the exact non-goal DEC-V1-003 was written to prevent | **Genuine DDL-level column absence**, not a nullable-and-unused column — live-verified in `07a-db-implementation` as one of the ER model's own confirmed structural absences; this file requires the schema-introspection check to be a standing CI gate (Class G), not a one-time confirmation, since a future migration adding a column here is the realistic failure mode, not a runtime bug | Critical |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Column-absence check | 100% (Class G) — `discovery_hint` has exactly its designed columns, zero tolerance for a name/photo/contact-shaped column ever appearing | CI gate on every migration touching this table, not just at initial build |
| Hint-frequency cap | ≤ 1 per 20 feed items, enforced server-side | Contract test on feed composition |

**Cautions**
This is one of the highest-consequence StructAbsence items in the module precisely because the failure mode (a column silently added later) is a single migration away and would not be caught by any functional test that doesn't specifically assert column-level schema shape — recommend this specific check be named in the migration-review checklist Step 9 uses, not just CI.

**Assumptions** — none beyond DEC-V1-003.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP030 — Templated, non-score compatibility explanation generation
**Traces from:** TR030
**Status:** Ready for Review | **Confidence:** Medium — algorithm/weighting methodology remains BR07's own open item

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | Y | A free-generation approach (vs. templated) risks leaking source evidence data verbatim into an explanation string in an unintended way | Templated approach structurally limits output to fixed sentence structures populated from structured fields — no free-text generation pipeline that could echo raw input | Medium |
| Denial of service | N | Templated generation is cheap, deterministic | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Explanation generation latency | Class A/B (in-request, no external call) | Load test |
| No-numeric-score-field check | 100% (Class G) | Contract test on response schema |

**Cautions** — none beyond BR07's carried-forward open algorithm question.
**Assumptions** — none beyond BR07's open-algorithm note.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP031 — Fact/inference labeling and banned-claim template constraints
**Traces from:** TR031
**Status:** Ready for Review | **Confidence:** Medium — same open-algorithm caveat as SP030

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | Y | A template producing certainty-of-character/honesty/success language would misrepresent Trust & Verification's actual evidence confidence to a viewer making a real life decision — a trust-integrity harm, not merely a copy-quality issue | Template library has no template capable of producing banned-claim language (structural, per TR030's templated-generation choice); `source: fact | inference` tag sourced from Trust & Verification's own evidence layer, never inferred by Compatibility Engine itself | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Banned-claim template audit | 100% (Class G) — every template in the library reviewed against the banned-claim list at build time | CI content-governance gate, per TR031/TR036's same consolidated review pass |
| Fact/inference tag presence | 100% of explanation fields carry a `source` tag | Contract test |

**Cautions** — none beyond BR07's open-algorithm question, which does not affect this ownership assignment.
**Assumptions** — none beyond BR07's open-algorithm note.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP032 — Core compatibility capability has zero dependency on FR033/FR034
**Traces from:** TR032
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | N | — | — | — |
| Denial of service | Y | A candidate who skips personality assessment/horoscope entirely must not receive a degraded or erroring core Compatibility response — an availability regression for the majority-case (skip) path | Contract test asserting a valid, non-degraded response with these fields entirely absent from input, not merely optional-and-empty | Medium |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Core-path-without-optional-data latency | Same Class A/B bound as the full-data path | Load test both branches |
| Zero-dependency contract test | 100% (Class G) | CI gate |

**Cautions** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP033 — Personality assessment: build skip/non-blocking scaffolding now, instrument selection stays open
**Traces from:** TR033
**Status:** Ready for Review | **Confidence:** Low — the instrument itself is genuinely unselected (named open item, `v1-decisions.md`)

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | Consent/skip actions individually audited | Audit-CC | — |
| Information disclosure | Y | Instrument-agnostic JSON response store (`assessment_response`) could, once a real instrument is selected, hold clinically-sensitive psychometric data — this schema choice must not become a place a future integration dumps more than the instrument's own scored output | Key-value/JSON shape is intentionally generic; access still gated by RLS-CC (self or `candidate_info` scope) — this file recommends the future instrument-integration tech req explicitly re-classify sensitivity once the instrument is known, since a licensed psychometric tool's raw responses may carry stricter handling requirements than this file can pre-judge | Medium |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Skip/abandon path latency | Class B, never gates Discovery/Compatibility (per TR032/SP032) | Load test |
| No-hardcoded-instrument check | 100% (Class G) — no instrument-specific question set/scoring logic in application code | Code-review + CI gate |

**Cautions**
This file does not attempt to resolve the instrument-selection question (correctly out of engineering's control per `v1-decisions.md`) — but flags forward: once an instrument is selected, this item must be re-opened for a dedicated sensitivity/consent review specific to that instrument's own data-handling requirements (e.g., a licensed clinical tool may impose stricter retention/access rules than this generic store currently assumes).

**Assumptions** — none beyond what's stated above.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP034 — Horoscope: isolated, opt-in-only input path
**Traces from:** TR034
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | Opt-in toggle audited | Audit-CC | — |
| Information disclosure | Y | Compatibility Engine reading horoscope data for a non-opted-in candidate — a consent-boundary violation | Query-time filter (join gated on `opted_in = true`), not an application-level convention — verified live in `schema.sql`'s RLS predicate (`opted_in = true AND (is_self(...) OR has_scope(...))`) | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Opt-in-gate correctness | 100% — zero rows returned for a non-opted-in candidate under any `AuthzContext` | Contract test, toggling `opted_in` and re-querying |
| Query-time filter overhead | < 10 ms added to enclosing Compatibility computation | Query-plan check |

**Cautions** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP035 — Six-layer independent evidence/provenance display
**Traces from:** TR035
**Status:** Ready for Review | **Confidence:** Medium — Identity & Trust Service availability/degradation behavior is a genuine external dependency (TR035's own Constraints note)

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | Y | Collapsing six independent layers into one combined badge/score would misrepresent evidence quality to a viewer making a real trust decision — same integrity harm class as SP031 | Each layer returned as an independent object (status, provenance, timestamp) — never combined (StructAbsence: no combined-score field exists) | High |
| Denial of service | Y | Identity & Trust Service sync-call latency/unavailability blocking this entire read path | Explicit degraded-response branch: unavailable Identity & Trust Service renders the account-authenticity/identity layers as "unavailable," never a false negative, and never blocks the other four layers | High |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Evidence-panel read latency | Class A for the five Mangaly-native layers; Class D for the Identity & Trust Service sync portion | Load test, with the external call both healthy and degraded |
| Identity & Trust Service timeout | ≤ 2 s, then degrade to "unavailable" (never a hang, never a false "not verified") | Fault-injection test |
| No-combined-score check | 100% (Class G) | Contract test |

**Cautions**
The "unavailable ≠ false negative" distinction is the load-bearing correctness property here — a naive implementation that treats a timeout as "verification failed" would be a real user-harm (a genuinely verified candidate shown as unverified due to a transient network blip), not merely a UX defect. Name this explicitly in Step 9/10's test plan for this endpoint.

**Assumptions** — none beyond TR035's own.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP036 — Evidence copy avoids truth-certification language
**Traces from:** TR036
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | Y | Absolute "verified true"-style copy misleading a viewer into over-trusting a self-reported or partially-confirmed fact — a trust-integrity harm with real matrimonial-decision consequences | Fixed, reviewed vocabulary bank structurally excluding absolute language, enforced by a build-time lint-style content-governance check | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Copy-bank governance check | 100% (Class G) — every string in the evidence-layer copy bank passes the banned-language list | CI gate, consolidated with SP056/SP085's copy-governance items per TR036's own recommendation into one Step 9 content-review pass |

**Cautions** — none beyond ensuring the consolidated review actually happens as one pass, not three independently-drifting ones.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP037 — Verification Circle: DEC-V1-004 anti-abuse mechanics; canonical shared rate-limiting utility
**Traces from:** TR037 (canonical rate-limiting statement — also cited by SP007, SP093, SP095, SP011)
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y | A fresh/unverified account being invited as a verifier and its response counting as real evidence | Invited verifier must hold Level-2+ trust status (sync check against Identity & Trust Service) before their response counts | High |
| Tampering | Y | A fraudulent verifier's confirmation needing to be undone without destroying the evidentiary trail | Retroactive `invalidated` marking, never a silent delete (per FR037's own acceptance criterion) — preserves the audit trail while removing evidentiary weight | High |
| Repudiation | N | Verifier confirmation/invalidation both audited | Audit-CC | — |
| Information disclosure | N | — | RLS-CC | — |
| Denial of service | Y | Verifier-invite spam (fake evidence flooding, or harassment via repeated invite notifications to the same third party) | **Canonical RateLimit-CC**: ≤5 invites per rolling 7-day window per inviting account, DB-backed `mangaly_platform.rate_limit_counter` — survives process restart, works across instances, exactly the property an in-memory or per-component counter cannot guarantee (per this item's own explicit finding, which is why this file treats "same pattern as" phrasing elsewhere as a warning sign, per `/MODULE-ARCHITECTURE-STANDARD.md` §4c) | High |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Rate-limit-counter check-and-increment | Class H — P95 < 20 ms, atomic UPSERT to avoid a race allowing two concurrent requests to both pass a boundary check | Concurrency test: N simultaneous invite calls at the limit boundary, assert exactly `limit_max` succeed |
| Idempotent-confirmation-per-fact check | 100% — `UNIQUE(profile_id, verifier_account_id, fact_reference)` enforced at the DB level, not application-only | Constraint-violation test |
| Verifier Level-2+ gate check | 100% — zero invites accepted as evidence from a sub-Level-2 account | Contract test |

**Cautions**
The DB-backed counter must use a single atomic UPSERT (increment-if-window-current, else reset) rather than a read-then-write pair — a naive read-then-write under concurrent requests reintroduces exactly the race a rate limiter exists to prevent. Flag this specific implementation detail to Step 9, since "DB-backed" alone doesn't guarantee atomicity.

**Assumptions** — verification-vendor selection remains open per `v1-decisions.md`; this item covers only DEC-V1-004's mechanics.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP038 — Admin/Mangaly-operated verification fallback path
**Traces from:** TR038
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | Request/decision audited | Audit-CC | — |
| Information disclosure | Y | Evidence submitted for admin review must not be exposed via any path other than the role-gated Admin Case detail endpoint (SP040/SP072) | RLS-CC + StructAbsence (SP040's own no-raw-document-field rule applies to this path's output) | High |
| Denial of service | Y | Unconditional availability of this fallback path could be abused to flood the 1-hour-SLA admin queue, degrading the SLA for genuine requests | RateLimit-CC-class control recommended — not explicitly named in TR038, flagged as a gap this file adds | Medium |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Request-submission latency | Class B | Load test |
| 1-hour SLA (DEC-V1-004) | Measured as wall-clock from submission to admin decision — this is an operational-staffing metric, not a system latency one; Step 13 Monitoring dashboard required, per TR038's own note | Production metric, not a load test |

**Cautions**
TR038 correctly frames the 1-hour SLA as an operational-staffing question, not a technical one — this file adds: if this fallback path has no rate limit, a queue-flooding abuse could make the SLA unachievable even with adequate staffing, which would look like an operational failure but actually be a missing technical control. Recommend adding the rate limit before this is load-tested against realistic volume.

**Assumptions** — none beyond DEC-V1-004/DEC-V1-007.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP039 — Structural absence of any trust score / reputation field
**Traces from:** TR039
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | Y | A single aggregated trust/reputation score would itself become a new, higher-stakes data point subject to gaming and misrepresentation, and would defeat SP035's six-independent-layer transparency design | StructAbsence — no column, computed field, or API response field anywhere in `mangaly_trust`/`mangaly_discovery`/`mangaly_profile` aggregates these signals | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Schema-introspection absence check | 100% (Class G), per CODING-GUIDE §6's own named test class | CI gate across all three named schemas |

**Cautions** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP040 — Evidence panel response contract has no raw-document field
**Traces from:** TR040
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | Y | Access to a raw verification document (highest-sensitivity data in `mangaly_trust`) not being individually attributable | Only the role-gated Admin Case detail endpoint (Operations, SP072) can return raw documents, and that endpoint's own access is audited (SP071) | High |
| Information disclosure | Y (highest-priority finding in this item) | A raw ID/KYC document (photo, government ID, etc.) being exposed via the general Evidence-panel endpoint through a conditionally-populated field — a single-response-model design mistake would be catastrophic given the document sensitivity | **Two structurally separate response models**, not one model with a conditional field — the Evidence panel's response type has no field capable of carrying a raw document URL/bytes at all, by construction (CODING-GUIDE §7) | Critical |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y | A privilege-escalation bug in the Admin Case endpoint's role gate would be the only way to reach raw documents at all, making that one gate the sole line of defense for the module's most sensitive data class | RLS-CC (`operator_role` session variable) + role-scope structural enforcement (SP076: no wildcard role) | Critical |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Two-model separation check | 100% (Class G) — Evidence-panel response type has zero fields capable of holding a document URL/byte payload, verified by type-level schema inspection, not just a runtime empty check | CI gate on the Pydantic/response-model definitions themselves |
| Admin Case document-read latency | Class A, but access-logged (Audit-CC) on every read, not just on write | Load test + audit-completeness contract test |

**Cautions**
This file treats the two-model separation as one of the module's highest-value structural controls precisely because it is cheap to build correctly now and catastrophic to retrofit later (a single shared model that later needs a "sometimes populated" field is a realistic path to this leaking) — confirm at Step 9 code review that no future refactor merges the two response models "to reduce duplication."

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP041 — Marriageable-age gate as a versioned, admin-configurable setting
**Traces from:** TR041
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | An operator (or a bug) lowering the configured threshold below the legal minimum | Admin-configurable setting still requires the same operator-role gating as any other Operations config change (SP076's no-wildcard-role rule); recommend a floor validation (reject any configured value below 18) as a defense-in-depth check this file adds | High |
| Repudiation | Y | A threshold change made without a recorded reason/actor | Config change should be an audited Operations action (Audit-CC), not a bare environment-variable edit with no audit trail | Medium |
| Information disclosure | N | — | — | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y | Inconclusive age evidence defaulting to "assume compliant" would let an underage profile through — a legal-compliance failure, not merely a data-quality one | Fail-closed design (TR041): inconclusive evidence is treated as not-yet-eligible, never defaults to compliant | Critical |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Eligibility-check latency | Class A, evaluated inline at Discovery/Trust gate time | Load test |
| Fail-closed correctness | 100% — every inconclusive-evidence permutation resolves to not-eligible | Contract test enumerating inconclusive states |
| Config-change audit | 100% — every threshold change produces an audit record with actor/timestamp/old-new value | Contract test |

**Cautions**
This file adds two controls beyond TR041's own text: (1) a floor validation preventing the configured value from ever being set below the current legal minimum by operator error; (2) requiring the config change itself to be an audited action, not a bare env-var edit — both are cheap to build now and expensive to retrofit after a real misconfiguration incident. Also restating TR041's own Step 13 watch item: the pending 2021 Amendment Bill's legislative status must actually be monitored, not just architected for.

**Assumptions** — none beyond DEC-V1-005.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP042 — Send connection request, on-behalf-of authorization check
**Traces from:** TR042
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y | A family member acting on-behalf-of a candidate without an actual authorization grant to do so | `AuthzContext` resolved for the acting party (candidate or authorized on-behalf-of) before request creation | High |
| Tampering | Y | Duplicate request creation from a retried client call | Idempotency-CC | Medium |
| Repudiation | N | Request creation audited | Audit-CC (`ConnectionRequested`) | — |
| Information disclosure | N | — | RLS-CC | — |
| Denial of service | Y | Scripted mass connection-request spam against many target profiles | RateLimit-CC-class control recommended — not explicitly named in TR042, flagged as a gap this file adds, given this is a direct member-to-member contact vector with real harassment potential | Medium |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Request-creation latency | Class B | Load test |
| Idempotency correctness | 100% — a repeated key never creates a second request row | Dedicated Step 10 test per TR102's own instruction |

**Cautions**
Connection-request spam is a real harassment vector this file surfaces as a recommended addition beyond TR042's own text — recommend a per-actor rate limit via RateLimit-CC, sized to a generous but bounded rate (e.g., tens per day, not hundreds per hour) to be set at Step 9 based on realistic legitimate-use patterns.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP043 — Full pre-acceptance review information, no forced timeout
**Traces from:** TR043
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | N | Same anti-teaser response-contract rule as SP020, applied to pre-acceptance review — no new disclosure surface | — | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Pre-acceptance review read latency | Class A (composes Compatibility + Trust reads) | Load test |
| No-forced-timeout check | 100% (Class G) — no default/auto-expiry state machine transition exists on `PATCH /connections/{id}` | Contract test + interface inspection |

**Cautions**
Cross-referenced with SP020's identical monetization-pressure risk category — both should be checked together in any future monetization-feature design review, per TR043's own note.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP044 — Acceptance triggers nothing beyond "willing to explore" state
**Traces from:** TR044
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | State-transition audited | Audit-CC | — |
| Information disclosure | Y | An implicit downstream subscriber to the acceptance event auto-triggering, e.g., an unintended contact/media share — a consent-bypass class similar to SP014's | Contract test asserting zero downstream side effects beyond the state write and its own audit record | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Accept-write latency | Class B | Load test |
| Zero-side-effect contract test | 100% (Class G) | CI gate, re-run whenever a new event subscriber is added anywhere in the module |

**Cautions**
This is the same completeness-risk class as TR012/TR069/TR098 — a future subscriber added to the event bus for an unrelated reason could accidentally attach itself to this event. Recommend this contract test explicitly enumerate the *expected* subscriber count (currently zero beyond audit) so a new subscriber addition fails the test loudly rather than passing silently.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP045 — No single-current-connection constraint
**Traces from:** TR045
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | N | — | — | — |
| Denial of service | N | Multiple concurrent connections is a supported, not abusive, state | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Multi-connection read/list latency | Class A, scales linearly with a realistic per-candidate connection count (bounded by RateLimit-CC on SP042's request creation) | Load test with a high-connection-count candidate |

**Cautions** — none; this item is a deliberate non-constraint, not a gap.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP046 — Per-category sharing grants, independently timestamped
**Traces from:** TR046
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | A combined bitmask/flag field being manipulated to grant multiple categories at once via one write | Row-per-category modeling (TR046) makes this structurally impossible, not merely tested-against | High |
| Repudiation | N | Each grant individually audited with its own timestamp | Audit-CC | — |
| Information disclosure | Y | Cross-category grant scope resolving independently — each grant must resolve its own `AuthzContext` scope, not inherit another category's already-granted scope | Per-row scope resolution (TR046) | Medium |
| Denial of service | Y | Retry-storm on this endpoint creating duplicate share events | Idempotency-CC | Medium |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Per-category grant write latency | Class B | Load test |
| Row-per-category structural check | 100% (Class G) — no bitmask/flag column exists on this table | Schema-introspection CI gate |

**Cautions** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP047 — Explicit sharing confirmation, no automated disclosure
**Traces from:** TR047
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | Grant event individually audited with actor/timestamp | Audit-CC | — |
| Information disclosure | Y | A scheduled job or connection-progress milestone silently triggering a disclosure the sharing party never explicitly approved — a consent-bypass class | StructAbsence — no scheduled job/milestone trigger capable of calling SP046's write path; verified as a negative-dependency check (no such job registered in the scheduler) | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Confirmation-notification latency | Class D (Notification Bridge dispatch), best-effort, never blocking the grant write itself | Fault-injection test: notification failure must not roll back the already-completed grant |
| Negative-dependency check | 100% (Class G) — no scheduler entry targets this path | Scheduler-configuration inspection CI gate |

**Cautions** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP048 — Family-contact sharing requires two independently-resolved AuthzContexts
**Traces from:** TR048
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | Both resolutions individually audited | Audit-CC | — |
| Information disclosure | Y (highest-priority finding in this item, per IA048's own flag) | The two-context requirement being under-implemented as a single combined check with an embedded family-flag — the realistic implementation mistake this item exists to prevent, which would let the candidate's own UI action alone disclose a family member's contact without that family member's own independent consent | Two **sequential, separate** `authz.resolve()` calls (TR048) — one for the candidate's UI action, one for the specific family member's own contact-sharing grant — modeled explicitly in the endpoint's own code, not as one combined check | Critical |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y | Same root cause — a single-check implementation would let the candidate unilaterally exercise a family member's own consent authority | Two independent `authz.resolve()` calls, both required to grant | Critical |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Two-resolution latency | Class B (two Class-A-equivalent authz calls in sequence, still within the same transaction) | Load test |
| Two-independent-calls verification | 100% (Class G) — **dedicated code-review + integration test confirming both `authz.resolve()` calls are present and independently enforced**, per TR048's own explicit recommendation that this not be inferred from a passing test alone | Dedicated Step 8/10 review, not incidental coverage |

**Cautions**
This is one of the highest-integration-risk items in the module by the source material's own repeated flagging (IA048, TR048) — this file elevates the verification method accordingly: a passing functional test alone is explicitly insufficient here, since a single-check implementation could produce the same *test-observable* outcome in the common case while failing the actual two-consent guarantee in an edge case (e.g., a family member who never separately granted). Require a code-review checklist item naming this specifically, not just a green CI run.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP049 — In-platform messaging, accepted-connection precondition
**Traces from:** TR049
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | Messaging without a prior accepted-connection check — a direct-contact/harassment vector against a candidate who never accepted | Sender's `AuthzContext` resolved against `accepted` connection state (TR043/TR044) before message creation | High |
| Repudiation | N | Message send audited via outbox | Audit-CC (SP052 — deepest test-investment component alongside SP017) | — |
| Information disclosure | N | — | RLS-CC (one application-level read path beyond sender/recipient — SP051) | — |
| Denial of service | Y | Retry-storm on message send creating duplicate messages, or message-flooding a recipient | Idempotency-CC; RateLimit-CC-class control recommended for raw message-send volume — not explicitly named in TR049, flagged as a gap this file adds given messaging is the highest-abuse-surface component in the module | High |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Message-send latency | Class B — given messaging is the module's core interaction loop, hold to the tighter end: P95 < 300 ms | Load test at 1,500 concurrent sessions |
| Idempotency correctness | 100% — a retried send after connectivity loss never creates a duplicate message row | Dedicated Step 10 test, per TR102's own explicit instruction that TS228-229 do not already prove this |
| Send-volume rate limit | Recommend a generous per-conversation and per-account ceiling (e.g., high enough not to impede real conversation, low enough to block scripted flooding) — exact number set at Step 9 against real usage patterns | RateLimit-CC |

**Cautions**
Messaging is the highest-value abuse surface in the module (harassment, spam, romance-scam scripting per DEC-V1-006's own Tier 3 examples) — this file recommends a send-rate limit as a genuine gap beyond TR049's own text, separate from and in addition to Safety Intelligence's after-the-fact detection (SP064/SP065), since a rate limit prevents volume, detection only catches content.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP050 — Minimal-necessity message processing; no permanent browsable log
**Traces from:** TR050
**Status:** Ready for Review | **Confidence:** High — retention window now concretely resolved (`v1-decisions.md` DEC-V1-010, 2026-09-13), replacing what was previously an undefined "DPDP-gated" placeholder with an actual researched policy

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | Y | Message content persisting indefinitely with no application surface honoring a retention boundary — a growing-forever sensitive-data store is itself a risk (larger breach blast radius the longer data lives) | Background lifecycle job (TR054's failure-alerting) enforces the concrete V1 window `v1-decisions.md` DEC-V1-010 now sets: active-account messages retained for the life of the connection/account (matching BR11's six named retention-justification purposes); post-account-deletion, a **30-day reactivation grace window**, then **erasure/anonymization within 90 days** of the original request, with a **mandatory 48-hour pre-erasure notice** (DPDP Rule 8's own requirement) | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Retention-job scaffolding | Class F — job runs against the concrete DEC-V1-010 windows above (`RETENTION_POST_DELETION_GRACE_DAYS=30`, `RETENTION_POST_DELETION_ERASURE_DAYS=90`, `RETENTION_PRE_ERASURE_NOTICE_HOURS=48` in `.env.example`) | Job-configuration inspection |
| No-permanent-browsable-log check | 100% (Class G) — no application surface presents unbounded chat history beyond the six named BR11 purposes | Contract test on every message-read endpoint |
| Pre-erasure notice delivery | 100% — fires exactly 48 hours before the 90-day erasure completes, every time | Contract test |

**Cautions**
This item's former blocker (DPDP legal sign-off) is resolved by `v1-decisions.md` DEC-V1-010, which derives the windows above from the DPDP Act 2023/Rules 2025's own actual provisions (Rule 8's purpose-fulfilled test, the 1-year log-retention floor, the 3-year large-platform inactivity ceiling with its 48-hour notice) cross-checked against BharatMatrimony/Shaadi.com's own published retention practice — this is a well-sourced V1 decision, not a placeholder, and Step 9 should build directly against it rather than waiting on a "legal counsel sign-off" this pipeline was never going to receive.

**Assumptions** — none beyond DEC-V1-010's own framing.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP051 — Application-level access restriction plus a named production DB-access-control review
**Traces from:** TR051 (grouped with SP067, SP071 — identical finding, raised once at full priority)
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | The one legitimate read path (Safety Intelligence) is case-scoped and individually logged | Audit-CC | — |
| Information disclosure | Y (Critical — highest-priority finding shared across SP051/SP067/SP071) | Message content is the module's highest-sensitivity data class (per the ER model's own `Highest (message content)` sensitivity rating); an engineer or operator with standing ad hoc production SQL access could read it regardless of how correctly the application layer restricts read paths — **the application-level control alone does not prove this doesn't happen**, per TR051's own explicit finding | Application layer: exactly one read path (Safety Intelligence, case-scoped, TR064). **Required operational-infrastructure control this file elevates to a named, owned finding, grouped with SP067/SP071 rather than raised three separate times**: least-privilege production DB roles, no standing ad hoc query access for engineers/operators, access reviewed and logged at the infrastructure level (not just the application level) | Critical |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Application-layer read-path restriction | 100% (Class G) — exactly one method in `mangaly_communication`'s repository layer can read message content, and it is case-scoped | Interface-inspection CI gate |
| Production DB-access-control review | Zero standing ad hoc production query access for any engineer/operator role; all access time-boxed, justified, and logged | **Required infrastructure/ops audit, distinct from and in addition to the application-layer contract test** — Step 9/Infra deliverable, named explicitly here rather than assumed to follow from the application design |

**Cautions**
This is the single most consequential DB-access-control finding in the module (message content, romance-scam/coercion evidence, private family disclosures) — grouped once here rather than diluted across SP051/SP067/SP071's three separate items, per this file's own prioritization discipline (impact, not discovery order). This is a real operational gap, not a formality: a platform engineer with a production `psql` shell and no query-logging policy defeats every application-level control this file lists elsewhere.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP052 — Transactional-outbox audit logging for every communication event
**Traces from:** TR052
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | Y | A process crash between "message sent" and "audit event published" leaving a silent gap in the trail for a component CODING-GUIDE names as needing the deepest test investment in the module | Same-transaction outbox write (TR052) — a crash cannot separate the state change from its audit record | Critical (per this component's own named highest-test-investment priority) |
| Information disclosure | N | — | Audit-CC / RLS-CC on outbox reads | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Outbox dispatch | Class I | Load test + fault-injection (kill process mid-transaction, confirm no orphaned state-without-event) |
| Test-investment depth | Dedicated test suite for this component's outbox path, matching CODING-GUIDE's own named priority alongside the Authorization Engine (SP017) | Coverage-depth review, not just a pass/fail gate |

**Cautions** — none beyond ensuring the test-investment priority is actually honored in Step 9/10, not just stated here.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP053 — Evidence-retention exception, scoped and individually logged
**Traces from:** TR053
**Status:** Ready for Review | **Confidence:** High — scope ceiling now concretely resolved (`v1-decisions.md` DEC-V1-010)

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | An exception scope silently widening beyond "this conversation only" | Scope hard-limited to one conversation, never cross-conversation, enforced at the write layer | High |
| Repudiation | N | Exception individually logged, routed into an Operations case | Audit-CC | — |
| Information disclosure | Y | A retention exception is, by nature, a mechanism to *retain* otherwise-deletable message content — its own scope-limiting is the only thing preventing it from becoming an unbounded surveillance capability | Individually-logged, single-conversation scope; controlled human investigation via Operations case; concrete ceiling now set by DEC-V1-010: retained for the duration of the associated Operations case **plus 180 days after case closure**, or until an active legal hold (TR054) lifts, whichever is later — not an unscoped duration | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Exception-write latency | Class B | Load test |
| Scope-ceiling correctness | 100% — configuration-driven ceiling (`RETENTION_SAFETY_EVIDENCE_POST_CASE_CLOSURE_DAYS=180` in `.env.example`, per DEC-V1-010), no hardcoded literal | Contract test |

**Cautions**
Previously gated on the same open DPDP question as SP050 — now resolved by DEC-V1-010's concrete 180-day post-case-closure ceiling; build and test against this number directly.

**Assumptions** — none beyond DEC-V1-010's own framing.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP054 — Legal-hold suspension of deletion; lifecycle-job failure alerting
**Traces from:** TR054
**Status:** Ready for Review | **Confidence:** High — default retention windows now concretely resolved (DEC-V1-010); legal-hold *duration* itself remains inherently case-specific by the structural nature of what a legal hold is, not an unresolved dependency

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | A held conversation being deleted anyway due to a scheduling race or a bug that doesn't actually check the hold flag | Structural skip — the job checks the flag before any deletion action, not merely "expected to be skipped by correct scheduling" | Critical — deleting evidence under active legal hold is a distinct legal-liability failure, not just a data-loss bug |
| Repudiation | Y | A retention job failing silently, partially completing, or timing out with no record | Failure alert published on any error/timeout/partial-completion run (TR054), routed to Operations (DEC-V1-007) | High |
| Information disclosure | N | — | — | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Legal-hold check | 100% — zero deletions of a held conversation, under every tested job-execution path (normal, retried, partially-failed) | Contract test with an active hold, forcing job execution |
| Job failure-alert latency | Class F — failure alert fires within 15 min of the failed/timed-out/partial run | Fault-injection test |
| Job idempotency on re-run | 100% — a re-run after a partial failure does not double-process or skip rows | Re-run test against a deliberately interrupted job |
| Default retention windows applied when no hold is active | Per DEC-V1-010: 30-day post-deletion grace, 90-day erasure, 48-hour pre-erasure notice | Contract test |

**Cautions**
The job's default-window behavior is now build-ready against DEC-V1-010's concrete numbers. Legal-hold *duration* is deliberately not a number this file (or any V1 decision) sets — a hold lasts as long as the actual legal matter requires, which is a structural property of what a legal hold is in any jurisdiction, not a gap. What matters for this item is that the structural skip-while-held behavior is correct (tested above) and that the job falls back to DEC-V1-010's default windows the moment a hold lifts.

**Assumptions** — none beyond DEC-V1-010's own framing.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP055 — No exclusivity/seriousness model on conversations
**Traces from:** TR055
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | N | — | — | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Multi-conversation read latency | Class A, scales with realistic concurrent-conversation count | Load test |

**Cautions** — none; deliberate non-constraint, not a gap.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP056 — Android FLAG_SECURE capture-risk mitigation; honest platform-asymmetry disclosure
**Traces from:** TR056
**Status:** Ready for Review | **Confidence:** Medium — mechanisms confirmed available; effectiveness inherently partial (TR056's own note)

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | Y | Message content captured via screenshot/screen-recording/casting and redistributed outside the platform — a real privacy harm given the sensitivity of matrimonial conversations | Android: genuine OS-level `FLAG_SECURE` block on the messaging window. iOS: no prevention primitive exists — relies on after-the-fact screenshot-taken notification only. **Neither survives a second device photographing the screen or a rooted/jailbroken device** — confirmed via live research at Tech Reqs and restated here as a real, permanent limitation, not a temporary gap | Medium (mitigated on Android; only detected, not prevented, on iOS) |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| `FLAG_SECURE` application | 100% of messaging-window renders on Android | UI test |
| iOS screenshot-notification delivery | Fires on every OS-detected screenshot event, no missed notifications | Platform-API contract test |
| Copy-accuracy check | 100% (Class G) — UI copy states risk-reduction, never guarantee, and never implies platform equivalence | Content-governance review, consolidated with SP036/SP085 per TR036's own note |

**Cautions**
This file does not treat the iOS gap as solvable at this step — there is no iOS prevention primitive to build against, confirmed via live research, and the correct response is honest disclosure, not a stronger technical claim than the platform allows. Recommend explicit user-facing copy testing to confirm it reads as "reduces risk" not "prevents capture."

**Assumptions** — specific mechanisms remain BR11 DEC-003's own implementation-stage decision, narrowed here to the two concretely available platform primitives.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP057 — Request contact information, on-behalf-of check
**Traces from:** TR057
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y | Same on-behalf-of impersonation risk as SP042 | `AuthzContext` resolved before request creation | High |
| Tampering | Y | Duplicate request creation on retry | Idempotency-CC | Medium |
| Repudiation | N | Requester identity/timestamp audited | Audit-CC | — |
| Information disclosure | N | — | RLS-CC | — |
| Denial of service | Y | Repeated contact-exchange requests used to pressure/harass a recipient | RateLimit-CC-class control recommended — not explicitly named in TR057, flagged as a gap this file adds | Medium |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Request-creation latency | Class B | Load test |

**Cautions** — repeated-request harassment vector, same class as SP011/SP042; recommend a shared rate-limit policy across all "request toward another member" endpoints rather than one per endpoint, consistent with §4c's own shared-utility principle.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP058 — Recipient-only decision authority, even within one Home Circle
**Traces from:** TR058
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y | A different Home Circle member (even a legitimately authorized one) deciding on the recipient's behalf without being the recipient themselves | Explicit `requester_id != decider_id` check even within the same Home Circle — "any authorized family member" is deliberately not treated as interchangeable with the actual recipient | High |
| Tampering | Y | Duplicate decision from a retried client call | Idempotency-CC | Medium |
| Repudiation | N | Full requester/decider/timestamp/content chain audited | Audit-CC | — |
| Information disclosure | N | — | RLS-CC | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y | A same-Home-Circle family member deciding as if they were the recipient is a real consent-boundary violation this check exists to prevent | Explicit identity-not-role check | High |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Decision-write latency | Class B | Load test |
| Recipient-identity check | 100% (Class G) — decision rejected whenever `decider_id == requester_id` OR decider is not the actual named recipient, regardless of Home Circle role | Contract test with a same-Home-Circle non-recipient attempting the decision |

**Cautions** — none beyond ensuring the contract test explicitly covers the same-Home-Circle case, not just the cross-Home-Circle case.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP059 — Single-channel disclosure only; no proxy-signal auto-reveal
**Traces from:** TR059
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | Y | Sharing one channel (phone) implicitly revealing another (email) in the same or a subsequent response — an over-disclosure beyond the specific consent given | Each channel independently gated as its own field in the response model — no shared reveal-all field | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Channel-independence check | 100% (Class G) | Contract test: grant phone, assert email remains withheld in same and subsequent responses |
| No-automated-trigger check | 100% (Class G) — no scheduled/automated job or elapsed-time/message-count trigger exists anywhere capable of calling the disclosure path | Scheduler/event-subscriber inspection CI gate |

**Cautions** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP060 — Candidate-controlled, non-automatic Home Circle involvement timing
**Traces from:** TR060
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | Involvement action audited | Audit-CC | — |
| Information disclosure | Y | A message-count/elapsed-time/connection-stage threshold silently auto-triggering Home Circle visibility into a private connection — a consent-bypass class | StructAbsence — no such threshold anywhere calls this path automatically, verified as a negative-dependency check (no scheduled job or event subscriber targets it besides the explicit candidate-initiated call) | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Involvement-toggle latency | Class B | Load test |
| Negative-dependency check | 100% (Class G) | Scheduler/subscriber inspection CI gate |

**Cautions** — none.
**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP061 — Discovery-level family involvement is independent of connection-level involvement
**Traces from:** TR061
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | Y (highest-priority finding in this item, per IA061's own flag) | The "already involved elsewhere, so treat as involved here" shortcut — a family member's broad Discovery-level grant being treated as implicit connection-level access, retroactively exposing prior private messages once family becomes involved | SP060's endpoint is the *only* path to per-connection scoping, resolved as its own independent authorization decision regardless of other grants; Communication's message-read path continues to check the reader's own connection-level grant specifically, never a broader "family is now involved" flag — no retroactive exposure of prior messages | Critical |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y | Same root cause — a shortcut implementation would grant broader access than any single grant actually authorizes | Independent per-connection authorization decision, no grant-widening shortcut | Critical |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Independent-resolution check | 100% (Class G) — a family member's Discovery-level grant produces zero connection-level access without SP060's own explicit grant | **Dedicated code-review attention, per TR061's own recommendation, not just test coverage** — this is a realistic implementation mistake, not a hypothetical one |
| No-retroactive-exposure check | 100% — messages sent before family involvement remain invisible to family after involvement is scoped in | Contract test: send messages, then involve family, assert prior messages still return zero rows under the family `AuthzContext` |

**Cautions**
Flagged by IA061/TR061 (alongside SP048/SP062) as a higher-integration-risk item — this file requires the no-retroactive-exposure contract test specifically, since a passing "involvement works" test alone would not catch a shortcut that also happens to retroactively expose history.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP062 — Family-to-family introduction as two independently-resolved exposures
**Traces from:** TR062
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | Both exposures individually audited | Audit-CC | — |
| Information disclosure | Y | Same class of risk as SP048 — one combined "introduction happened" event implicitly granting both sides' exposure without each family's own independent consent | Two separate `authz.resolve()` calls (Family A→B, Family B→A), same modeling pattern as SP048 | Critical |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y | A single-check implementation would let one family unilaterally expose the other | Two independent resolutions, both required | Critical |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Two-resolution latency | Class B | Load test |
| Two-independent-calls verification | 100% (Class G) — same dedicated code-review + integration test requirement as SP048 | Dedicated Step 8/10 review |

**Cautions**
Same recommendation as SP048: this is the highest-sensitivity transition point BR13 names — verify both `authz.resolve()` calls are present at code review, not inferred from a passing test alone.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP063 — Universal, non-downgradable reporting entry point
**Traces from:** TR063
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | Report triage using "no automated-detection signal fired" as a dismissal criterion — would systematically under-prioritize genuine reports the detector missed | Structural rule in the triage query: absence of an automated-flag column is never used as a filter condition | High |
| Repudiation | N | Report creation audited | Audit-CC | — |
| Information disclosure | N | — | RLS-CC | — |
| Denial of service | Y | A screen missing the shared reporting entry point would functionally deny the reporting capability to users of that screen — a completeness/availability failure with real safety consequences | Shared API contract every screen is required to wire to, enforced by a Step 3/4-derived screen-inventory checklist item | High |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Report-submission latency | Class B — given safety urgency, hold to P95 < 300 ms | Load test |
| Screen-coverage completeness | 100% (Class G) — every screen in the Step 3/4 inventory has a wired entry point | CI gate reapplied as an ongoing checklist for every future screen, per TR063's own recommendation |
| Triage non-dismissal rule | 100% (Class G) — triage query has no code path filtering on absence of an automated flag | Query-logic CI gate |

**Cautions**
TR063 recommends the screen-inventory discipline be reapplied as an ongoing checklist since nothing currently re-checks it automatically once a new screen ships — this file elevates that to a required CI gate rather than a process reminder, given the safety-consequence of a missed entry point.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP064 — Bounded detection scope, repository-layer enforced
**Traces from:** TR064
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | Y | Safety Intelligence's detection scope silently expanding to read Home Circle relationship data or Trust/Verification evidence — a scope-creep risk that would blur BR14 DEC-001's operational-separation boundary | Repository layer has **no method capable of querying** `mangaly_home_circle` or `mangaly_trust` at all (StructAbsence, per CODING-GUIDE §7) — an absence, not a method that happens not to be called | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |
| (Detection-scope boundary, specifically) | Y | Automated content-scanning of photo/video (never authorized per DEC-V1-006) would be a significant, unauthorized surveillance-scope expansion if accidentally introduced | Photo/video content is never automatically scanned by design — a reported photo/video routes to human review only | High |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Cross-schema-absence check | 100% (Class G) | Repository-layer inspection CI gate, across both `mangaly_home_circle` and `mangaly_trust` |
| No-automated-media-scan check | 100% (Class G) | Code-review + CI gate confirming no image/video-analysis call exists in the detection path |
| Text/metadata detection latency | Class B (near-real-time, message-send-adjacent) | Load test |

**Cautions** — none beyond CODING-GUIDE §7 already specifying the enforcement mechanism precisely.
**Assumptions** — none beyond DEC-V1-006.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP065 — Graduated response pipeline, with on-call paging and CSAM reporting actually wired
**Traces from:** TR065 (single most consequential finding at Impact Analysis, per IA065's own flag; carried forward as this file's other top-priority item alongside SP017/SP048/SP062)
**Status:** Ready for Review | **Confidence:** High for pipeline mechanics; the on-call paging vendor and CSAM packet schema are now concretely resolved (`v1-decisions.md` DEC-V1-011) — the remaining risk is production load-testing/integration confirmation, not an unresolved design or procurement question

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | SLA clock manipulation (e.g., starting the clock at human-review pickup instead of classification time, silently making response times look compliant when they aren't) | SLA clock started at classification time, not pickup time, per DEC-V1-006/TR065 explicit requirement | High |
| Repudiation | N | Every tier transition audited | Audit-CC | — |
| Information disclosure | N | — | RLS-CC (SP067) | — |
| Denial of service | Y | Case-arrival rate exceeding the small on-call rotation's real capacity at exactly the tiers with no legal slack (Tier 3/4) — DEC-V1-007's own named, accepted risk | State machine correctly enforces SLA clocks; **the real gap is operational load-testing, not a missing design or vendor** — see below | High |
| Elevation of privilege | N | — | — | — |
| (Tier 3/4 exit reachability — the item's actual named risk) | Y | The taxonomy's most severe exits (on-call paging, CSAM reporting) needing to be real, load-tested integrations, not just policy commitments — exactly IA065's own finding: "the five stages are coded" is not equivalent to "the Tier 3/4 exits are reachable in production" | **Now concretely resolved at the design level**: `v1-decisions.md` DEC-V1-011 names PagerDuty specifically (Events API v2, `.env.example` `PAGERDUTY_ROUTING_KEY`) and defines the CSAM report packet's actual field schema (modeled on NCMEC's real CyberTipline ESP categories, adapted to cybercrime.gov.in/SJPU per POCSO Rule 11(2)) — see `mangaly_operations.csam_report_packet`'s field-group table in DEC-V1-011. **What remains is Step 9 implementation plus a load test against realistic case-arrival rates**, not an open procurement/schema question | High |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Tier 3/4 paging-trigger fire latency | Class E — P99 < 60 s from classification to page fired, via the now-named PagerDuty Events API v2 integration | Required load test against realistic case-arrival rates once the real PagerDuty account/escalation policy is configured at Step 9 — not satisfied by unit-testing the state machine transition alone |
| CSAM structured-packet dispatch latency | Class E — P99 < 5 min from Tier-4 classification, in parallel with internal block, never sequenced after investigation | Same required load test as above, against DEC-V1-011's concrete packet field schema |
| Tier 2 SLA (DEC-V1-006) | 24h acknowledge / 36h resolve — legal ceiling, not a target to approach | Production SLA-clock monitoring (Step 13), measuring actual case handling, not just that the clock exists |
| Tier 3 SLA (nudity/impersonation subset) | 2h human-reviewed — legal ceiling | Production SLA-clock monitoring |
| On-call staffing sufficiency | Not a system metric — a real, named operational risk DEC-V1-007 already accepts; this file requires case-arrival-rate monitoring against staffing capacity as a Step 13 deliverable, not assumed adequate | Step 13 Monitoring dashboard, explicitly required before this item is considered production-ready |

**Cautions**
This file previously treated the vendor/schema gap as a Critical, unresolved blocker (BLK-08-04); that gap is now closed at the design level by `v1-decisions.md` DEC-V1-011 — PagerDuty is named concretely, and the CSAM packet schema is defined field-by-field, both things Step 9 can actually build against today. What remains — the load test against real case-arrival rates, and confirming cybercrime.gov.in's actual submission mechanism (API vs. manual portal, per `.env.example`'s `CSAM_REPORT_FALLBACK_MODE`) — is a narrower, correctly-scoped Step 9 pre-launch task, not the same open-ended procurement uncertainty this item started with. This file still will not mark Tier 3/4 as *production-ready* until that load test exists, but the design-level blocker is resolved.

**Assumptions** — none beyond DEC-V1-006/DEC-V1-007/DEC-V1-009/DEC-V1-011's own framing.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP066 — Safety triage never references Trust/Verification status
**Traces from:** TR066
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | No identity assertion in a triage query | — | — |
| Tampering | Y | A later change adds a `mangaly_trust` join into the triage/prioritization query, silently reintroducing the two-tier safety response this FR forbids — the realistic failure path is a well-meaning "prioritize verified users' reports" optimization, not malice | StructAbsence: no join/lookup into `mangaly_trust` exists in Safety Intelligence's repository layer; the CI import-boundary check (`/MODULE-ARCHITECTURE-STANDARD.md` §3) fails the build if Safety's package imports Trust's | High |
| Repudiation | N | Triage decisions audited | Audit-CC | — |
| Information disclosure | Y | A cross-schema join would additionally hand Safety's query surface read access to verification data it has no authorization basis for | RLS-CC + schema-per-component separation (no path from Safety's code to Trust's rows except Trust's own `interface.py`) | Medium |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Absence of Trust reference in Safety triage | Class G — 100%, zero tolerance | CI import-boundary + schema-introspection check on every merge |
| Triage query latency | Class A | Load test at production case-arrival rate |

**Cautions**
The security property here is *equal treatment*, whose failure mode is silent: a trust-weighted triage would still function correctly and would read as a sensible optimization in code review. Only the structural check catches it, which is why this is Class G (build-blocking) rather than a review convention.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP067 — Tightly controlled safety access, application-level plus DB-access review
**Traces from:** TR067
**Status:** Ready for Review | **Confidence:** Medium — the application-layer control is sound; the production-DB-access dimension is the open part (see SP051)

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Operator identity resolved through the chokepoint | RLS-CC + `mangaly.operator_role` | — |
| Tampering | Y | Case data modified outside the case-scoped Operations path | Single write path (TR072/TR074); schema-per-component forbids a direct cross-schema write | High |
| Repudiation | Y | An operator viewing sensitive safety case data with no record of having done so — surveillance leaving no trace | Every access individually logged (TR067), not merely every mutation — a read-logging requirement stronger than this module's default | High |
| Information disclosure | Y (Critical) | Two distinct paths: (a) a general-monitoring query surface over safety data; (b) **direct production-database access by an operator or engineer, which bypasses every application-layer control in this file at once** | (a) StructAbsence — no general query endpoint exists; (b) **the same finding as SP051 and SP071 — raised once, canonically, at SP051, not re-scored here.** RLS-CC constrains `mangaly_app`, but a human holding `mangaly_owner` or superuser credentials sits outside RLS entirely, which is precisely the owner-bypass failure mode TR017 names | Critical (via SP051) |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y | An operator without the relevant case-type scope reading case data | `operator_role_scope` with no wildcard member (SP076) | High |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Case-scoped read latency | Class A | Load test |
| Access-log completeness | 100% of reads produce an audit record, not only writes | Contract test asserting a read without a corresponding audit event fails |

**Cautions**
The application-layer design is correct and complete. The residual risk is entirely operational: RLS protects against application bugs, not against a human holding owner-level database credentials. That is SP051's combined production-DB-access-control finding, and it is why SP051/SP067/SP071 are grouped rather than each proposing a partial control of its own.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP068 — Severity taxonomy consumed as fixed configuration
**Traces from:** TR068
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y (High) | The severity/SLA configuration object is edited without review — and because DEC-V1-006's tiers encode **legally binding** IT-Rules-2021 deadlines (24h acknowledge, 2h for the nudity/impersonation subset, 36h resolve), silently widening one is a compliance failure, not a tuning change | Config lives in version-controlled `config/safety_severity.py`, not a runtime-editable table or admin screen; changes require code review plus the SLA-clock regression suite; no code path writes to it | High |
| Repudiation | N | — | Audit-CC | — |
| Information disclosure | N | Taxonomy is not sensitive | — | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Single source of truth | Class G — CI assertion that no component re-encodes a tier threshold locally; exactly one module defines them | Static check for literal SLA durations outside `config/safety_severity.py` |
| Config read cost | Not a runtime metric — loaded at process start, not per request | — |

**Cautions**
Per TR068/IA068: the taxonomy being *defined* is a separate release gate from its Tier 3/4 exits being *operationally reachable* (SP065). Both must pass; neither substitutes for the other.

**Assumptions** — none beyond DEC-V1-006.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP069 — Consequential-action audit events via lint-enforced publish discipline
**Traces from:** TR069 — **canonical statement of Audit-CC, cited by every other item in this file**
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y | An audit event published with a forged actor or capacity, making the trail attest to something false — worse than no trail, because it is trusted | Actor, capacity, and `AuthzContext` are copied from the server-resolved context at publish time; none is ever accepted as a client-supplied field | High |
| Tampering | Y | An outbox row altered or deleted between write and dispatch | `outbox_event` tables are insert-only for application code, with reads restricted to the dispatcher role (`mangaly.service_role = 'dispatcher'`) — the split RLS policy added and live-verified during Step 7a's verification pass | High |
| Repudiation | Y (Critical) | **The central threat this item exists to close.** A mutating endpoint that publishes no event makes its action unprovable afterwards — and the realistic cause is a *new* endpoint added later without one, not an existing gap | Lint rule: any public mutating handler without a corresponding outbox publish fails the build (TR069/IA069) — structural, not a code-review reminder. This is the completeness-risk class IA012/IA063/IA069/IA083/IA088 all named | Critical |
| Information disclosure | Y | An event payload carrying more than the action's own metadata could expose, through the audit path, data the source row's RLS would have withheld | Payload minimization: events carry identifiers and the resolved authorization basis, not row contents; dispatcher-only SELECT policy on every `outbox_event` table | High |
| Denial of service | Y | Outbox backlog under load, or a dispatcher failure silently accumulating undelivered events | Class I threshold below — an undelivered event older than 15 min pages Operations rather than aging silently | Medium |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Outbox dispatch latency | Class I — P95 < 5 s, P99 < 30 s | Dispatcher instrumentation |
| Undelivered-event age | > 15 min pages Operations; never a silent drop (at-least-once, ADR-011) | Alerting rule, Step 13 |
| Mutating-endpoint coverage | Class G — 100% of mutating handlers publish an event; lint-enforced, build-blocking | CI lint rule |
| Transactional atomicity | 100% — no state change commits without its event in the same transaction | Integration test forcing a post-write failure and asserting both roll back together |

**Cautions**
The atomicity guarantee is the entire point of the outbox and is easy to lose by accident: an event published *after* commit, or from a different session, reintroduces exactly the lost-audit-record failure the pattern exists to prevent. The integration test above — force a failure between write and publish, assert both roll back — is the only thing that actually proves it.

**Assumptions** — the Audit Log Store's own durability is a platform property (ADR-011), consumed here rather than re-implemented.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP070 — Append-only audit trail (platform property, consumed not re-implemented)
**Traces from:** TR070
**Status:** Ready for Review | **Confidence:** Medium — the property is correct, but Mangaly *inherits* rather than *enforces* it; see Cautions

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y (Critical) | An actor with sufficient access alters or deletes audit history to conceal an action — the classic anti-forensics move, and the reason an editable audit trail is worth close to nothing | Records are append-only in the platform Audit Log Store (ADR-011), which exposes no update or delete path; revocations and corrections publish *new* records referencing the original. Mangaly keeps no local mutable copy that could diverge | Critical |
| Repudiation | Y (Critical) | Same root cause — a deletable trail cannot establish what happened | As above | Critical |
| Information disclosure | N | Read access covered by SP071 | — | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Append-only property | 100% — zero update/delete paths reachable from Mangaly code | Class G: CI check that no Mangaly module issues an UPDATE/DELETE against an audit destination |
| Correction-by-append behavior | Every revocation/dispute writes a new record referencing the original, never an in-place edit | Contract test |

**Cautions**
Stated honestly: this control is exactly as strong as the platform Audit Log Store's own append-only guarantee, which Mangaly neither owns nor can enforce. If that guarantee is weaker in practice than ADR-011 asserts — for instance if operators hold delete permission on its underlying storage — then every Repudiation mitigation in this file that cites Audit-CC is correspondingly weaker. **Required verification for Step 9/Step 13, not an assumption to inherit:** confirm the store denies update and delete at the storage-permission level, not merely by convention of the writing API.

**Assumptions** — ADR-011's append-only guarantee holds as written, pending the verification above.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP071 — Audit trail denied to end-users; case-scoped, self-logged admin query
**Traces from:** TR071
**Status:** Ready for Review | **Confidence:** Medium — application layer sound; DB-access dimension per SP051

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | Append-only (SP070) | — | — |
| Repudiation | Y | An operator querying a member's audit trail without that query itself being recorded | The admin query writes its own audit record (actor, case reference, timestamp) before returning results | High |
| Information disclosure | Y (Critical) | One member reading another's audit trail, which exposes the complete history of who viewed what and when — a richer disclosure than any single profile view | No end-user endpoint exposes another member's trail (StructAbsence); the Authorization Engine's deny-by-default baseline covers it without a special-case rule, which is the stronger construction | Critical |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y | An operator querying outside any active case — unbounded browsing rather than scoped investigation | The query is case-scoped: it returns only records tied to an active case reference, so an unscoped query has no valid form | High |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Admin audit query | Class A | Load test |
| Self-logging completeness | 100% — no query path returns results without first writing its own audit record | Contract test asserting the record exists before the response is emitted |
| End-user exposure | Class G — zero endpoints returning another member's audit records | Route-inventory check in CI |

**Cautions**
Same combined production-database-access-control finding as SP051 and SP067 — a human with direct database credentials reads the trail without generating the self-log this item depends on. Raised canonically at SP051.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP072 — Verification admin workflow against DEC-V1-007's fixed states
**Traces from:** TR072
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y | An operator acting on a case type outside their assigned scope | `operator_role_scope`, no wildcard member (SP076) | High |
| Tampering | Y | A decision written directly into `mangaly_trust` rather than through the Operations→Trust interface call, bypassing Trust's own validation and event publication | Schema-per-component: no cross-schema write path exists; Operations calls Trust's `interface.py` (TR072) | High |
| Repudiation | Y | An approve/deny with no attributable decision-maker | Audit-CC — every state transition publishes with operator identity and case reference | High |
| Information disclosure | Y (High) | Verification evidence is the module's highest-sensitivity content (raw identity documents via `evidence_document_ref`); an operator outside the case reading it is a serious disclosure | Case-scoped access (SP067); `evidence_document_ref` never appears in any general response model (TR040), only in the case-scoped investigation view | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y | A premature approve/deny that skips evidence gathering — the state machine's integrity is itself a security property, since a wrongly-approved verification grants trust signals to an unverified account | An explicit `mark_incomplete`/`request_more_evidence` transition distinct from approve/deny, so "not enough evidence yet" has its own state instead of being forced into a binary decision | High |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| State transition write | Class B | Load test |
| Verification SLA | Class E — DEC-V1-007's 1-hour target for the admin fallback path (TR038) | Production SLA-clock monitoring |
| Illegal-transition rejection | 100% of transitions absent from DEC-V1-007's state machine are rejected server-side | State-machine contract test over every state pair |

**Cautions**
Test the state machine exhaustively over state pairs rather than the happy path alone — an unguarded transition (`approved` → `approved` re-firing an event, or a decision on an already-appealed case) is the realistic defect here, and each one carries an authorization consequence downstream in Trust.

**Assumptions** — none beyond DEC-V1-007.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP073 — False-relationship dispute workflow, Tier 2 SLA
**Traces from:** TR073
**Status:** Ready for Review | **Confidence:** Medium — surfaces a real abuse vector TR073 does not itself name

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y | A dispute filed in another member's name | AuthzContext-resolved filer identity, never client-asserted | Medium |
| Tampering | N | Same state machine as SP072 | — | — |
| Repudiation | Y | A dispute or its resolution without attribution | Audit-CC | Medium |
| Information disclosure | Y | A dispute exposing the disputed relationship's details to a filer who should not see them | Case-scoped (SP067); the dispute record references the relationship rather than copying its contents | Medium |
| Denial of service | Y (High) | **Weaponized disputes.** TR011/TR073's withhold-pending-review behavior means filing a dispute *itself* degrades the target's access. An abuser — or a coordinated group — can file false disputes to suppress a rival's visibility for the length of the review window, turning the safety mechanism into the attack. This is a known abuse pattern for report-and-suspend systems and TR073 does not currently address it | Two controls, both needed: (1) RateLimit-CC on dispute filing per filer, via SP037's canonical shared utility with its own key/window/limit; (2) **filing must not auto-apply the withhold — the withhold is a triage decision a human makes**, so a false filing costs the target nothing until a human judges it credible. Repeat false filers are themselves recordable as a Safety signal | High |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Tier 2 SLA | Class E — 24h acknowledge / 36h resolve (DEC-V1-006, IT Rules 2021) | Production SLA-clock monitoring |
| Dispute filing | Class B | Load test |
| False-dispute abuse rate | Monitored, not merely rate-limited: disputes per filer per window, with a reviewable outlier report | Step 13 monitoring dashboard |

**Cautions**
The Denial-of-service row is this item's substantive finding and a genuine gap in TR073 as written, not a restatement of it: reusing TR010/TR011's withhold mechanism inherits that mechanism's abuse surface along with its implementation. Recommend Step 9 implement filing and withholding as two distinct steps with a human decision between them. If product later wants an automatic withhold for speed, that trade-off should be made explicitly against this finding rather than by default.

**Assumptions** — none beyond DEC-V1-006/DEC-V1-007.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP074 — Abuse/fraud investigation with attributable restriction/block/escalation
**Traces from:** TR074
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y | A restriction applied under another operator's identity | AuthzContext-resolved operator identity | High |
| Tampering | Y | A restriction or block modified or lifted without record | Append-only audit (SP070); a lift is a new attributed action, not an erasure | High |
| Repudiation | Y (Critical) | A block with no attributable actor. FR076's "never disclosed publicly" rule **depends on this attribution chain existing** — without internal attributability the non-disclosure guarantee has nothing underneath it | Audit-CC with full actor attribution (admin identity plus case reference) on every restriction, block, and escalation | Critical |
| Information disclosure | Y | Investigation detail leaking to the investigated party, letting a fraudster adapt | Case data is case-scoped (SP067); user-facing messaging states the outcome, never the detection basis | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y | An operator restricting accounts outside their scope | `operator_role_scope`, no wildcard (SP076) | High |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Restriction/block application | Class B; effect visible to the Authorization Engine within one request cycle | Integration test asserting the next authorization call reflects it |
| Attribution completeness | 100% — no restriction, block, or escalation without an attributed audit record | Contract test |
| Tier 3/4 escalation | Class E — paging fire P99 < 60 s (SP065) | Synthetic escalation drill |

**Cautions**
The Tier 3/4 operational-reachability caveat carries forward unchanged from SP065 — now design-resolved by DEC-V1-011 (PagerDuty named, CSAM packet schema defined field by field), with the load test against realistic case-arrival rates still outstanding as a Step 9 pre-launch task.

**Assumptions** — none beyond DEC-V1-006/DEC-V1-007.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP075 — Appeals workflow; reviewer independence as a named, honest constraint
**Traces from:** TR075
**Status:** Ready for Review | **Confidence:** Medium — a real, accepted operational limitation rather than an engineering gap

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y | An appeal filed on another member's behalf | AuthzContext-resolved appellant | Medium |
| Tampering | N | Append-only decision history | — | — |
| Repudiation | Y | An appeal outcome with no attributable reviewer | Audit-CC recording **both** the original decision-maker and the appeal reviewer | High |
| Information disclosure | Y | The appeal exposing detection detail the original decision withheld | Same case-scoping and outcome-not-basis messaging as SP074 | Medium |
| Denial of service | Y | Repeated appeals of the same decision as a workload attack on a small operations team | One appeal per decision by default; further appeals require a new material ground rather than a re-filing | Medium |
| Elevation of privilege | Y (High) | **The same operator reviewing their own decision**, which makes the appeal procedurally worthless in precisely the cases where it matters most. DEC-V1-007 accepts this as a staffing reality ("where staffing allows"), so it cannot be engineered away at this scale | Assignment logic *prefers* a different operator (soft preference, per DEC-V1-007). Where that is impossible, the concrete control this item adds is **visibility rather than prevention**: the audit record captures both identities, so self-review is detectable and countable after the fact instead of invisible. Step 13 reports a self-review rate, making the accepted risk measurable rather than merely acknowledged | High |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Appeal intake and assignment | Class B | Load test |
| Appeal resolution | Class E — same DEC-V1-006 tier clock as the original decision | SLA monitoring |
| Self-review rate | Reported, not assumed zero — a measured percentage reviewed against staffing growth | Step 13 monitoring dashboard |

**Cautions**
Per TR075/IA075 this is an operational-staffing limitation that neither Step 8 nor Step 9 can close. The honest security position: the appeal path exists, is audited, and its independence is best-effort with measurable exceptions. Surface the self-review rate to whoever owns the staffing plan — the fix is people, not code.

**Assumptions** — none beyond DEC-V1-007's own stated trade-off.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP076 — 100% admin-action audit coverage; no all-access role, structurally enforced
**Traces from:** TR076
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | A role scope widened at runtime to approximate all-access | `operator_role_scope` values are bounded enum members; scope changes are themselves audited admin actions | High |
| Repudiation | Y (Critical) | An admin action with no audit record — the highest-privilege actions in the module being the least accountable | Audit-CC, lint-enforced specifically for Operations mutations (same discipline as SP069) | Critical |
| Information disclosure | Y (Critical) | A single compromised or misused operator account reading every case in the system | **StructAbsence, live-verified:** no `*`/all-cases enum member exists in `mangaly_operations.operator_role_scope`, so an all-access role is not merely unassigned but unrepresentable. Compromise of one operator therefore exposes that operator's queue, not the system | Critical |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y (Critical) | Same root cause — a wildcard scope is elevation by configuration | As above, enforced at the schema level rather than by policy convention (TR076/IA076) | Critical |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Admin-action audit coverage | Class G — 100%, lint-enforced, build-blocking | CI lint rule over Operations mutating handlers |
| Absence of wildcard scope | Class G — 100%, zero tolerance | Schema-introspection check asserting no `*`-equivalent enum member exists, run on every migration |
| Scope-check latency | Class A | Load test |

**Cautions**
This is the module's strongest structural control and its verification must stay structural. A future migration adding a convenience `all_queues` value would defeat it silently while every functional test still passed — which is exactly why the check is schema introspection on every migration rather than a functional test.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP077 — Agent access: no component built, verified absent
**Traces from:** TR077
**Status:** Ready for Review | **Confidence:** High — a confirmed non-build, not a gap

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | No Agent identity type exists to impersonate | StructAbsence | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | Y (low, latent) | If a partial Agent capability were introduced later without the full authorization model, a third party would gain access to candidate data under no defined scope. The risk lives entirely in the *future* build, which is why naming the extension points now matters — so a later engineer does not improvise them | Verified absence today (below); TR077 names the correct future extension points (Identity Bridge for identity type, Authorization Engine for per-family scoping, Audit Bridge for attribution), so a future build extends the chokepoint rather than bypassing it | Low (today) |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Verified absence | Class G — zero Agent-identity types, Agent-scoped grants, or Agent-attributed audit records anywhere in the module | Schema introspection plus enum/type inventory across all 14 schemas — asserted, not assumed |

**Cautions**
The only security-relevant instruction today is that the absence be *checked* rather than believed. When BR17's gate opens, this item's threat model must be rewritten before any Agent code merges — a deferred capability is not a pre-approved one.

**Assumptions** — per BR17 DEC-001.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP078 — Discovery ranking formula structurally has zero Agent-status term
**Traces from:** TR078
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y (High) | A ranking term added later that correlates with paid or professional assistance — the realistic path is a plausible product feature (a "professional-assisted" badge feeding relevance), not deliberate manipulation. Its effect would be to make visibility purchasable, precisely the fairness property BR06 exists to protect | Class G check over TR026's fixed weight list, run in the **same regression suite that guards SP022's no-popularity-signal rule** (per IA078) — both are "verify a specific input never entered the ranking formula" assertions, and grouping them makes the rule legible as a category rather than two one-offs | High |
| Repudiation | N | — | — | — |
| Information disclosure | N | — | — | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Ranking-input allow-list | Class G — the formula's input set matches DEC-V1-002's four weighted factors exactly; any additional term fails the build | Ranking-input inventory test alongside SP022's |

**Cautions**
Absence checks hold only if someone runs them at the moment of change. Both this and SP022 are build-blocking for that reason.

**Assumptions** — none beyond BR17 DEC-001.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP079 — Deliberate-action-only search conclusion
**Traces from:** TR079
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y | Another actor — including a Home Circle member — concluding a candidate's search on their behalf | Self-only: the endpoint resolves the acting identity via AuthzContext and permits only the candidate's own conclusion, with RLS-CC beneath it | High |
| Tampering | Y (High) | An inferred conclusion — an inactivity job, engagement score, or cleanup task flipping the state. Beyond correctness this carries a real dignity cost the FR is explicit about: being told the system decided your search is over | StructAbsence via negative-dependency check: no scheduled job, batch process, or non-endpoint code path can reach the `concluded` transition (Class G) | High |
| Repudiation | Y | A lifecycle change with no record of who made it | Audit-CC on every conclude/reactivate (TR081) | Medium |
| Information disclosure | N | — | RLS-CC | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y | A family member holding broad grants concluding on the candidate's behalf — a grant scope should never reach this action | The endpoint requires self-identity specifically, not merely a valid grant over the profile | High |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Conclude transition | Class B | Load test |
| Sole-write-path verification | Class G — exactly one code path can set `concluded`; no scheduled job targets it | Call-graph/negative-dependency check in CI |

**Cautions**
The Elevation-of-privilege row matters more than it looks: Home Circle grants are broad by design, so "holds a grant over this profile" must not be sufficient here. Test explicitly that a family member with a full `family_info` grant is still refused.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP080 — Concluded-profile exclusion without historical data loss
**Traces from:** TR080
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | Historical connection/accountability records deleted alongside discovery exclusion — conflating "stop showing me" with "erase what happened", which would destroy the accountability record BR15 depends on | Exclusion is a query filter, never a delete; append-only audit unchanged (SP070) | High |
| Repudiation | N | — | Audit-CC | — |
| Information disclosure | Y (High) | A concluded profile still appearing in Discovery or Compatibility results — the member has signalled they are done, so continued exposure is both a privacy violation and the most visible possible failure of this feature | An explicit `status = concluded` exclusion in both Discovery's and Compatibility's eligibility queries, applied alongside (not instead of) TR003's tier gate — two independent filters, so neither alone is a single point of failure | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Exclusion completeness | 100% — zero concluded profiles in any discovery or compatibility result set | Integration test over both query paths, including the FTS read model |
| Read-model propagation lag | Concluded state reaches `mangaly_discovery`'s event-synced index within Class I dispatch bounds (P95 < 5 s) | Event-propagation test |
| Query latency with exclusion | Class C, unchanged by the added filter | `EXPLAIN ANALYZE` comparison |

**Cautions**
Discovery's index is an eventually-consistent read model (ER model Assumptions #4), so conclusion is not instantaneous there — a concluded profile can appear in search for the propagation window. That window must be bounded, measured (Class I above), and its propagation path tested, because "it will catch up" is exactly the assumption that fails silently when a dispatcher is backed up.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP081 — Reactivation, freshness-window skip, and the Dashboard activity-summary event contract
**Traces from:** TR081
**Status:** Ready for Review | **Confidence:** Medium — contains the module's only cross-boundary data flow; see Cautions

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y | Reactivation triggered by someone other than the candidate | Self-only, same construction as SP079 | High |
| Tampering | Y | The freshness-window check bypassed so a long-dormant profile re-enters discovery carrying stale verification as though current | Reactivation calls Trust & Verification's existing freshness rules (BR08) unchanged — no reactivation-specific shortcut path exists | High |
| Repudiation | Y | Lifecycle transitions without record | Audit-CC on every conclude/reactivate | Medium |
| Information disclosure | Y (**Critical — highest-value finding in this cluster**) | The `mangaly.activity_summary` event to Dashboard (MOD05) is **the only point at which Mangaly data crosses its module isolation boundary at all.** A payload containing raw match, profile, or connection data would export the module's most sensitive content into another module's store, past every RLS policy in this file — and once published to the broker it is unrecallable | Three controls, all required: (1) the event schema is an **explicit allow-list** (lifecycle-state changed, timestamp), defined at this step, never a serialization of the domain object; (2) an **automated contract test asserts the published payload contains only allow-listed fields** and fails the build on any addition, because a design review alone cannot hold this line across future changes; (3) broker-topic access is restricted to Dashboard's consumer, so the payload is not broadly readable even while minimal | Critical |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Reactivation transition | Class B | Load test |
| Cross-module event publish | Class I — P95 < 5 s to broker | Dispatcher instrumentation |
| Payload allow-list conformance | Class G — 100%, build-blocking; any field outside the allow-list fails CI | Schema-contract test against the published event |
| Freshness-window enforcement | 100% of reactivations outside the window require re-verification | Integration test at window boundaries |

**Cautions**
This item deserves disproportionate attention relative to its size. Every other information-disclosure control in this file protects data *within* Mangaly's boundary; this one **is** the boundary. Recommend Step 9 implement the event payload as an explicit, hand-written DTO with no serializer reflection over the domain model, since the realistic failure is a future field added to the domain object silently appearing in the published event.

**Assumptions** — Dashboard (MOD05) consumes but never writes back; the broker edge is async and privacy-filtered per `/ARCHITECTURE.md`.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP082 — Success-story invitation, per-party independent consent
**Traces from:** TR082
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y (High) | One party consenting on the other's behalf, or consent inferred from the conclusion action itself — publishing a real person's marriage outcome without their agreement | Two independently-resolved AuthzContexts, one per party, same construction as SP048/SP062; consent is never derived from any other action | High |
| Tampering | Y | A consent record altered to show agreement that was never given | Consent grant/modify/revoke are separately audited and append-only (SP070) | High |
| Repudiation | Y (High) | No provable record of who consented to publication — the entire evidentiary basis for publishing personal outcomes | Audit-CC on each party's consent individually | High |
| Information disclosure | N | The invitation carries no third-party data | RLS-CC | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Invitation/consent write | Class B | Load test |
| Independent-consent enforcement | 100% — publication is impossible with fewer than both parties' own recorded consents | Contract test asserting single-party consent cannot reach a publishable state |

**Cautions**
Could-priority per TR082 — build after the Must-priority core is stable. That sequencing is a security benefit as much as a scope one: this feature publishes real identities externally and should not be built under time pressure alongside core work.

**Assumptions** — none beyond BR19 DEC-001.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP083 — Zero account-status effect from decline; revocable, audited consent
**Traces from:** TR083
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y (High) | Declining writes a field some other component reads — a shadow penalty for saying no. It would be invisible to the user and is a realistic emergent defect rather than a deliberate one (a `declined_story` flag added for reporting, later picked up by ranking) | Negative-dependency contract test (Class G, same pattern as SP012): no field written by the decline path is read by any other component's logic | High |
| Repudiation | Y | Consent state changes without record, particularly revocation | Audit-CC on grant, modify, and revoke individually | High |
| Information disclosure | N | — | RLS-CC | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Decline/revoke write | Class B | Load test |
| Zero-effect verification | Class G — no component reads any field the decline path writes | Negative-dependency check in CI |
| Revocation propagation | Revocation blocks further publication within the same request cycle | Integration test |

**Cautions**
TR083 defers takedown of an already-published story until the publication channel is chosen. That is a reasonable scope decision but leaves a real residual: consent is revocable in the system while published material may not be retractable in practice. Whoever selects the publication channel must treat "supports takedown on revocation" as a selection criterion rather than a later integration — flagged here so the constraint travels with the decision.

**Assumptions** — none beyond BR19 Assumptions.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP084 — Published story: allow-list assembly plus automated pre-publication scan
**Traces from:** TR084
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y | The publication payload modified between review and publish, so what was approved is not what ships | The reviewed artifact and the published artifact are the same immutable assembled payload, referenced by hash | High |
| Repudiation | Y | No record of who approved a publication | Audit-CC on the review decision, carrying the reviewer identity | Medium |
| Information disclosure | Y (**Critical**) | Publishing Home Circle membership details, private message content, or contact details to a public channel. This is **irreversible once public** — unlike every other disclosure risk in this file there is no revoke, no RLS, and no grant expiry that helps afterwards | Three independent layers, correctly defense-in-depth: (1) the payload is assembled from an **explicit field allow-list**, never a serialize-everything of the domain object; (2) an **automated structural scan** rejects any assembled payload containing a field sourced from Home Circle, Communication, or Trust contact data; (3) mandatory **human pre-publication review**. Any one layer failing still leaves two | Critical |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Automated scan | Class G — 100% of publication payloads scanned; a payload cannot reach publish without a passing scan result | Pipeline gate, not an advisory warning |
| Allow-list conformance | Zero fields outside the allow-list in any published payload | Contract test over the assembler |
| Scan latency | Class B — the scan runs inline in the publish path, not asynchronously after it | Publish-path timing test |

**Cautions**
Note the ordering requirement hidden in those thresholds: the scan must gate publication synchronously. An asynchronous scan that reports afterwards provides no protection for the one property — irreversibility — that makes this item Critical.

**Assumptions** — publication channel is a later marketing decision (BR19); these controls apply regardless of channel.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP085 — Optional, non-blocking real-world safety guidance
**Traces from:** TR085
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Static content, no identity assertion | — | — |
| Tampering | Y | Guidance copy altered to give unsafe advice — low likelihood, but this is safety guidance, so its integrity is not cosmetic | Copy is version-controlled config (DEC-V1-008's fixed five points), not runtime-editable content; changes go through code review | Medium |
| Repudiation | N | — | — | — |
| Information disclosure | N | Content is identical for every user and carries no personal data | — | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Prompt render | Class A | Client render timing |
| Non-blocking property | 100% — dismissal never gates any subsequent action | Contract test asserting every downstream action succeeds with the prompt undismissed |

**Cautions**
Per TR085/DEC-V1-008 the surrounding disclaimer and liability-framing language — not the five guidance points themselves — needs a pre-launch content pass. Following DEC-V1-010's precedent that is a pre-launch content review rather than a build blocker, and it is not listed among the open blockers for that reason.

**Assumptions** — informational content only, not a platform-mediated live-safety feature (BR20).
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP086 — Manual-only "meeting occurred" note
**Traces from:** TR086
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y | A note recorded against a connection by someone not party to it | AuthzContext-resolved participant check; RLS-CC on `mangaly_lifecycle.meeting_note` | Medium |
| Tampering | Y (High) | An automated signal creating the note — message-pattern inference, engagement heuristics, or a "looks like they met" classifier. Beyond the FR's own rule, an inferred meeting record is a claim about someone's offline life the platform has no basis to make, and it would feed SP087's reporting context | StructAbsence via negative-dependency check (Class G): `POST /connections/{id}/meeting-note` is the only write path; no inference, job, or classifier can reach it | High |
| Repudiation | N | Note creation audited | Audit-CC | — |
| Information disclosure | Y | A meeting note is unusually sensitive — it confirms an offline meeting occurred between two identified people | RLS-CC scoped to the connection's own participants; never included in any discovery, profile, or success-story payload | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Note write | Class B | Load test |
| Sole-write-path verification | Class G — exactly one code path creates a meeting note | Call-graph/negative-dependency check in CI |

**Cautions**
Treat the meeting note as offline-behavior data, not app-usage data — it should never appear in analytics extracts or the SP081 cross-module event payload. Worth an explicit exclusion assertion in the SP081 allow-list test.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP087 — Post-meeting reporting uses the identical BR14 pipeline
**Traces from:** TR087
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | Same resolved-identity path as SP063 | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | Same audit path as SP063 | Audit-CC | — |
| Information disclosure | N | — | RLS-CC | — |
| Denial of service | N | Same RateLimit posture as SP063 | RateLimit-CC | — |
| Elevation of privilege | Y (High) | **A parallel, weaker reporting path.** The realistic failure is not an attack but drift: a separate "post-meeting feedback" endpoint gets built for UX reasons, and because it looks like feedback rather than a report it quietly acquires a slower queue, no SLA clock, and no Tier 3/4 escalation. A post-meeting report is the most likely place a serious real-world harm surfaces, so a weaker path here is the worst possible place to have one | StructAbsence plus contract test: the post-meeting entry point calls the exact same `POST /safety/report` endpoint (TR063) with an optional meeting-context reference. There is no second endpoint, no second workflow, and no second SLA tier — the contract test asserts both entry points route into the identical pipeline instance, so a future divergence fails the build | High |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Pipeline identity | Class G — 100%; both entry points resolve to one handler and one SLA clock | Contract test asserting identical routing and identical DEC-V1-006 tier assignment |
| Report submission | Class B; SLA per Class E once classified | Load test plus SLA monitoring |

**Cautions**
This item is entirely about preventing a future second path, so its verification is structural. If product later wants distinct post-meeting UX, that is fine — but it must be presentation only, resolving to the same endpoint and the same clock.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP088 — Structural absence of relationship-progress/scheduling features
**Traces from:** TR088
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | Y | Scheduling or chaperone-coordination data would mean the platform holds *planned future physical locations and times* for identified people — a materially more dangerous data class than anything else in the module, and one whose compromise has direct physical-safety consequences. The strongest available control is not holding it | StructAbsence, verified across all 14 schemas (Class G): no scheduling, chaperone-coordination, or relationship-progression table or column exists anywhere | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Absence verification | Class G — zero scheduling/progression fields across all 14 schemas | Schema-introspection check on every migration |

**Cautions**
Per TR088/IA088, the realistic erosion path is a well-meaning feature ("let them agree a time in-app"), not a deliberate scope breach. The schema check catches it at merge, but this boundary should also sit on the product-roadmap review checklist, since by the time it reaches a migration someone has already built it. Worth stating plainly in that checklist *why* the boundary exists: the platform deliberately does not know where two members plan to be.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP089 — Person-level language preference, non-gating
**Traces from:** TR089
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y (Low) | Another actor altering a member's language preference — nuisance rather than harm, but still an unauthorized profile write | RLS-CC on `mangaly_profile`; self-or-granted write only | Low |
| Repudiation | N | — | Audit-CC | — |
| Information disclosure | Y (Low) | Language preference is a weak proxy for region/community and should not be exposed as a filterable discovery attribute, where it could become a community-filtering vector by the back door | Rendering-layer input only; not a `discovery_profile_index` column and not filterable — worth an explicit assertion in the SP021 index-field test | Medium |
| Denial of service | N | — | — | — |
| Elevation of privilege | N | Non-gating by construction | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Preference read/write | Class A / Class B | Load test |
| Non-gating property | 100% — profile creation and every capability succeed regardless of preference state | Contract test |
| Not-a-discovery-filter | Class G — `language_preference` is absent from Discovery's filterable field set | Index-field inventory assertion |

**Cautions**
The Information-disclosure row is the only substantive point: a language field is innocuous as a rendering hint and problematic as a filter. Keep it out of the discovery index rather than relying on the API not to expose it.

**Assumptions** — i18n rendering is Common Platform (ADR-010).
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP090 — Splash/launch session bootstrap
**Traces from:** TR090
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y (High) | A stolen or replayed session token accepted at launch | Server-side session validation against `mangaly_identity.session` on every launch — never a client-side "token looks present and unexpired" decision; revoked sessions (SP101) fail immediately | High |
| Tampering | Y | A client-modified token or expiry claim | Validation is server-side; the client's copy is opaque and never trusted for authorization | High |
| Repudiation | N | — | — | — |
| Information disclosure | Y | Token theft via client-side storage on a shared device or through script injection — a mobile-web-specific exposure this module inherits from being a web app rather than native | Tokens stored in `HttpOnly`, `Secure`, `SameSite` cookies rather than JavaScript-readable storage; short session lifetime with server-side revocation as the authority | High |
| Denial of service | Y | Launch blocked indefinitely when the network or identity check hangs — routine, not exceptional, for this module's tier-2/3-connectivity audience | Class D timeout with an explicit fallback branch to Login; never an indefinite spinner (TR090) | Medium |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Session validation | Class D — own-side P95 < 250 ms; caller timeout ≤ 2 s with a fallback branch | Load test plus induced-latency test |
| Degraded-network launch | 100% of launches resolve to a usable screen (home or login) within the timeout; zero indefinite waits | Network-throttled client test |

**Cautions**
The graceful-degradation requirement is a real security control here, not only a UX one: an indefinite spinner trains users to force-quit and retry, and retry storms against the identity endpoint are the realistic way a slow dependency becomes an outage.

**Assumptions** — session/token primitives are Common Platform-bound long term; the interim store is `mangaly_identity` (SP104).
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP091 — First-run onboarding, content-consistent with Help & Support
**Traces from:** TR091
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | Y (Low) | Onboarding copy altered to misrepresent privacy behavior — for instance implying family members cannot see something they can | Content is version-controlled and sourced from the same content bank Help & Support reads (TR100), so the two cannot drift into contradicting each other | Medium |
| Repudiation | N | — | — | — |
| Information disclosure | N | No personal data; client-side only | — | — |
| Denial of service | N | Fully skippable | — | — |
| Elevation of privilege | N | No backend logic | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Render | Class A | Client render timing |
| Skippability | 100% — dismissal never gates any capability, and the flow never re-displays after first dismissal | Contract test |
| Content-bank consistency | Onboarding and Help draw from one source; no duplicated copy | Static check for duplicated content strings |

**Cautions**
Onboarding is where the module makes its privacy promises in plain language. Those statements should be reviewed against actual authorization behavior (the SP003/SP017 gates) rather than written independently by design — a promise here that the system does not keep is a trust failure even though it is not a technical vulnerability.

**Assumptions** — illustrative content only, not a data-collection step.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP092 — Interim account sign-up (Identity Bridge-owned)
**Traces from:** TR092
**Status:** Ready for Review | **Confidence:** Medium — surfaces a real anti-enumeration conflict between TR092 and TR093; see Cautions

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y (High) | Account created against an identifier the registrant does not control | OTP verification (TR095/SP095) required before activation — the account is inert until the identifier is proven | High |
| Tampering | Y | Weak-credential acceptance leading to trivially guessable accounts | Server-side credential-strength validation at signup; **credential storage uses Argon2id** (or bcrypt tuned to ~250–500 ms verification), per `v1-decisions.md`'s Step-8 credential-hashing note — never a fast general-purpose hash, never unsalted | Critical |
| Repudiation | Y | Account creation without record | Audit-CC | Medium |
| Information disclosure | Y (**High — real finding**) | **Signup is an account-enumeration oracle.** TR092 requires "duplicate-identifier rejection," which by construction tells an unauthenticated caller whether a given phone number or email already has a Mangaly account. On a matrimonial platform that single bit is genuinely sensitive — it discloses that a specific, identifiable person is looking for a marriage partner, which carries real social consequence in this module's context. TR093/TR094 carefully close this oracle at login and reset, and signup then reopens it | **This item's substantive recommendation, not present in TR092:** signup must not return a distinguishable "already registered" response to an unauthenticated caller. Return the same generic "if this identifier is new, we have sent a verification code" response for both cases and route the duplicate down the existing-account path out-of-band (a message to the identifier's owner saying an account already exists, with a login/reset link). Duplicate *prevention* is preserved — it moves from the response body to the OTP channel, where only the identifier's actual owner learns anything | High |
| Denial of service | Y | Mass automated signup creating fake accounts, and signup-triggered SMS costs | RateLimit-CC via SP037's shared utility, keyed on the identifier and the caller; OTP gating means unverified accounts never become usable | High |
| Elevation of privilege | N | New accounts hold no elevated scope | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Signup write | Class B | Load test |
| Credential hashing cost | Deliberately slow: ~250–500 ms verification cost, tuned on production-class hardware — a *floor*, not a latency budget to optimize away | Benchmark in CI on the deploy target's hardware class |
| Response-shape uniformity | Class G — byte-for-byte identical response for new versus existing identifier | Response-diff test, same method as SP093 |
| Signup rate limit | Enforced per identifier and per caller; effective against scripted mass registration | Abuse-simulation test |

**Cautions**
The Information-disclosure row is a genuine cross-item inconsistency this pass surfaces rather than inherits: TR093 and TR094 treat account-existence as a secret worth structural protection, while TR092 requires an endpoint that reveals it. Both cannot be true. Recommend resolving in TR092's favour of the anti-enumeration discipline as described above — this is a routed finding for Step 7/Step 9 to accept, not a change this file makes unilaterally to a Sealed tech req.

Note also that credential hashing is now a plain implementation instruction (Argon2id) recorded in `v1-decisions.md`'s technical-debt section, not an open blocker — the earlier BLK-08-03 has been closed on that basis.

**Assumptions** — the interim credential store migrates to a Common Platform Identity service later (SP104).
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP093 — Login with structural anti-enumeration and rate-limiting
**Traces from:** TR093 — **canonical statement of AntiEnum-CC**
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y (Critical) | Credential stuffing or brute force against a known identifier | RateLimit-CC via SP037's canonical shared `rate_limiting/` utility, keyed per identifier; Argon2id's own verification cost makes offline attack expensive if hashes ever leak | Critical |
| Tampering | N | — | — | — |
| Repudiation | Y | Failed-login attempts not recorded, leaving no signal of an attack in progress | Failed attempts recorded (rate-limit counter plus audit signal), enabling Step 13 alerting on credential-stuffing patterns rather than discovering them afterwards | Medium |
| Information disclosure | Y (**Critical — the canonical control, plus a real gap**) | Account enumeration through login. TR093 correctly requires an identical response body and status code for "wrong password" and "no such account", verified by byte-for-byte diff. **That is necessary but not sufficient: it closes the response-shape oracle and leaves the timing oracle open.** If the server only performs the (deliberately expensive, ~250–500 ms) Argon2id verification when an account actually exists, then a non-existent identifier returns measurably faster, and the timing difference re-reveals exactly what the identical body was hiding. With a slow hash the differential is large and trivially observable — the stronger the hashing, the louder the leak | Two controls, both required: (1) the shared `generic_auth_error()` function gives one identical response body and status for both cases (TR093/TR094); (2) **the handler performs an equivalent-cost dummy verification against a fixed decoy hash when no account exists**, so both paths do the same work and return in the same time band. Add a latency-distribution assertion, not only a body diff | Critical |
| Denial of service | Y | Rate-limiting an identifier can itself lock a legitimate user out if an attacker floods their identifier | Limit failures per identifier *and* per source, with a graduated backoff rather than a hard lock, so an attacker cannot cheaply deny a specific user access | Medium |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Login | Class B; the Argon2id floor (~250–500 ms) dominates and is intentional | Load test sized to 1,500 concurrent sessions with real hashing cost included |
| Response-shape uniformity | Class G — byte-for-byte identical body and status | Response-diff test (CODING-GUIDE §7) |
| **Timing uniformity** | P50 and P95 for "no such account" fall within ±10% of "wrong password" | Latency-distribution test over ≥1,000 paired attempts — this is the assertion that proves the dummy-verify path actually runs |
| Rate-limit counter op | Class H — P95 < 20 ms even under retry burst | Shared-utility benchmark |

**Cautions**
The timing-oracle finding is this item's substantive addition to TR093 as written. It is also the reason SP092's signup recommendation matters: closing enumeration at login and reset while leaving it open at signup protects nothing, since an attacker uses whichever endpoint answers.

**Assumptions** — none beyond FR092's interim-system note.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP094 — Password reset with anti-enumeration and single-use, expiring tokens
**Traces from:** TR094
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y (Critical) | A guessed, brute-forced, or replayed reset token yielding full account takeover — reset tokens are bearer credentials and the single highest-value target in the auth surface | Tokens are cryptographically random with ≥128 bits of entropy, single-use (invalidated on first use), short-TTL, and validated server-side before any password change; the token is compared in constant time | Critical |
| Tampering | Y | A reset completed against a different account than the token was issued for | The token binds to its account server-side; no account identifier is accepted from the client during redemption | Critical |
| Repudiation | Y | A password change with no record | Audit-CC on issue and redemption, plus a notification to the account's own identifier that a reset occurred — so an unauthorized reset is visible to its victim | High |
| Information disclosure | Y (High) | Two paths: (a) enumeration via the request response; (b) **token leakage through the delivery or navigation surface** — a token placed in a URL query string can escape via `Referer` headers, browser history, and server logs, which is a realistic leak for a web app | (a) the shared `generic_auth_error()` function (SP093's canonical control) returns an identical response whether or not the identifier exists; (b) the token must not be logged and must not travel in a query string where it can leak by referrer — deliver it as a path segment or POST body, and scrub it from application logs | High |
| Denial of service | Y | Reset-flooding a known identifier as harassment, or to bury a real security notification | RateLimit-CC via SP037's shared utility, keyed per identifier | Medium |
| Elevation of privilege | Y | An unexpired token from a prior session still working after a password change | Redemption invalidates every other outstanding reset token and every active session for that account (ties to SP101's revocation path) | High |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Reset request/redeem | Class B | Load test |
| Token entropy | ≥128 bits from a CSPRNG | Code review plus a statistical check in CI |
| Single-use enforcement | 100% — a second redemption of the same token fails | Contract test |
| Session invalidation on reset | 100% of the account's active sessions revoked at redemption | Integration test |
| Response uniformity | Class G — identical response for existing and non-existing identifiers | Response-diff test |

**Cautions**
The session-invalidation requirement is easy to miss and is what turns a password reset into an actual recovery mechanism: if the attacker's existing session survives the victim's reset, the reset accomplishes nothing.

**Assumptions** — none beyond FR092's interim-system note.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP095 — OTP verification: DLT route, resend rate-limiting, fallback-channel budget
**Traces from:** TR095
**Status:** Ready for Review | **Confidence:** Medium — SMS is a genuinely unreliable and genuinely attackable channel; both are named rather than assumed away

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y (Critical) | Three distinct paths: OTP brute force against a short numeric code; OTP interception (SIM swap, SS7, or a malicious device app reading SMS); and OTP phishing, where a caller talks a user into reading the code aloud | Bounded attempt count with the challenge invalidated on exhaustion (never unlimited guesses against a 6-digit space); short expiry; single-use codes; message copy that explicitly states Mangaly staff never ask for the code. SIM-swap and SS7 interception are **not** mitigable at this layer and are named honestly as residual risk inherent to SMS as a factor | Critical |
| Tampering | Y | Attempt-count or expiry enforced client-side and therefore bypassable | All three checks (code, expiry, attempt count) are server-side against `mangaly_identity.otp_challenge` | Critical |
| Repudiation | Y | No record of verification attempts | Audit-CC; failed attempts also feed the rate-limit counter | Medium |
| Information disclosure | Y | A distinguishable response for "wrong code" versus "no pending challenge for this identifier" reopens the enumeration oracle SP093 closes | Uniform response shape via the same `generic_auth_error()` discipline | High |
| Denial of service | Y (High) | **SMS bombing** — repeatedly triggering sends to harass a target and to burn the platform's SMS budget, an attack whose cost lands on Mangaly directly | RateLimit-CC via SP037's canonical shared utility keyed on the identifier, with graduated backoff; a per-identifier daily send ceiling independent of the rolling window | High |
| Elevation of privilege | N | Verification grants only the account-authenticity trust layer, nothing further | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| OTP verify | Class B | Load test |
| OTP dispatch | Class D — own-side P95 < 250 ms excluding carrier RTT; explicit degradation when the provider is slow | Induced-latency test |
| Effective delivery | >99% via the transactional DLT route plus the fallback channel; single-channel SMS alone is ~92–95% in India per IA095's research, which is not sufficient on its own | Delivery-receipt monitoring per channel, reported separately rather than blended |
| Brute-force resistance | Attempt count bounded per challenge; challenge invalidated on exhaustion | Abuse-simulation test |

**Cautions**
Two honest limitations. First, the reliability gap is real and configuration-driven — wrong-route selection (promotional instead of transactional) and DLT template mismatch are the dominant causes, so the fallback channel in `.env.example` (`OTP_FALLBACK_CHANNEL`) is a required build item, not an optimization. Second, SMS as an authentication factor is intrinsically vulnerable to SIM swap; that residual is accepted for V1 given the audience's device reality, and should be revisited if the module later holds higher-value assets.

**Assumptions** — delivery infrastructure is Common Platform; the reliability finding applies regardless of which component owns the provider integration.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP096 — Location/notification permission priming, graceful degradation
**Traces from:** TR096
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y (Low) | A spoofed client-supplied location influencing locality ranking | Location is one weighted input among four (DEC-V1-002), never an authorization input — a spoofed location changes result ordering, never access | Low |
| Tampering | N | — | — | — |
| Repudiation | N | — | — | — |
| Information disclosure | Y | Location is sensitive; over-collection (continuous or background precision) would exceed what locality ranking needs | Collect coarse locality at the granularity ranking actually uses, on demand rather than continuously — data minimization as the primary control | Medium |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y | A denied permission blocking a capability, which would make consent coercive rather than optional | Declining location redistributes that ranking weight; declining notifications degrades to in-app inbox only. Neither blocks any capability (TR096) | Medium |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Degradation completeness | 100% — every capability remains reachable with both permissions denied | Full-suite run with permissions denied, not a spot check |
| Weight redistribution correctness | Ranking remains well-formed with the locality term absent (weights still sum correctly) | Ranking unit test |

**Cautions**
Run the entire functional suite in a permissions-denied configuration. Graceful degradation is the kind of property that passes review and fails in one overlooked screen, and the only way to know is to exercise everything without the permissions.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP097 — Navigation shell context switcher: server-authorized list, client-side leak prevention
**Traces from:** TR097
**Status:** Ready for Review | **Confidence:** Medium — the server side is straightforward; the client side is the harder half and is easy to under-test

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y (High) | A client asserting a context it is not entitled to — for example switching to act on behalf of a candidate whose Home Circle it does not belong to | `GET /me/contexts` returns only server-authorized contexts, each carrying its own resolvable `AuthzContext`; every subsequent request re-resolves authorization server-side rather than trusting the client's declared context | Critical |
| Tampering | Y | A context identifier modified client-side between switch and request | Server-side re-resolution on every request makes the client's claim unauthoritative | Critical |
| Repudiation | Y | Actions taken without recording which capacity they were taken in — critical here, since the same human acts as both self and family member | Audit-CC captures capacity alongside actor (SP069), which is precisely why capacity is a first-class field in the audit event | High |
| Information disclosure | Y (**High — the distinctive risk of this item**) | **Client-side residue across a context switch.** Server authorization can be entirely correct while the client still leaks: a half-typed message draft, a cached list, or an unsubmitted form from context A remaining visible after switching to context B. IA097 names this as a common mobile-app defect class, and it is invisible to server-side authorization tests, which is exactly why it survives to production | Explicit client-side state clearing on every context switch — drafts, caches, and in-flight form state are discarded, not merely re-rendered. The active context is always visibly displayed so a user is never mistaken about which capacity they are acting in | High |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y | Acting in a higher-privileged context than granted | Same server-side re-resolution as Spoofing | Critical |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Context list retrieval | Class A | Load test |
| Context switch | Client-side state fully cleared before the new context renders | Client integration test asserting no prior-context data is reachable post-switch, including drafts |
| Server-side re-resolution | 100% of requests re-resolve authorization; zero rely on a client-declared context | Contract test issuing a forged context identifier and asserting denial |

**Cautions**
Per TR097/IA097, flag the client-side clearing requirement for specific Step 9/Step 10 attention. Server-side tests will pass whether or not it is implemented, so a client-level test asserting the absence of prior-context residue is the only thing that actually covers it.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP098 — Notification inbox against the resolved `mangaly_notification` schema
**Traces from:** TR098
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | RLS-CC | — |
| Tampering | Y | An inbox entry created for the wrong recipient by a mis-subscribed event consumer | Recipient is derived from the source domain event's own resolved actor, not from consumer-side inference; RLS-CC on `mangaly_notification.inbox_entry` | Medium |
| Repudiation | N | — | Audit-CC | — |
| Information disclosure | Y (**High — real finding**) | **Notification payloads are the module's most exposed surface.** An inbox summary or push payload that embeds content — a message body, a sender's full name, the nature of a safety action — is visible on a lock screen, in a notification shade, and to anyone glancing at the device. In this module's context that is a materially worse disclosure than the equivalent in-app view, because a family member or bystander sees it without ever authenticating. This is a classic and easily-missed leak | **Payload minimization as a structural rule:** an inbox entry stores an event type, a reference identifier, and a non-revealing summary — never message content, never the counterparty's identifying detail, never safety-case specifics. The content is fetched under normal authorization only after the user opens the app. Assert this with a contract test over every notification event type rather than trusting per-type copy review | High |
| Denial of service | Y | Notification flooding as harassment, or unbounded inbox growth | Per-recipient rate limiting on notification-generating actions upstream; inbox pagination and retention | Medium |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Inbox read / mark-read | Class A / Class B | Load test |
| Payload minimization | Class G — zero notification payloads contain message content or counterparty identifying detail | Contract test over every registered event type |
| Event-type coverage | Class G — every notification-worthy event type has a subscriber producing an inbox entry; lint-enforced, per IA098's same-completeness-risk finding as TR069 | CI lint rule |
| Inbox independence | 100% — an entry is created whether or not push delivery succeeded | Integration test with push delivery forced to fail |

**Cautions**
The payload-minimization rule must be enforced per event type, not once: the realistic regression is a single new event type added later with a helpfully descriptive summary. That is why the assertion is a contract test over the registry rather than a review checklist item.

**Assumptions** — push delivery is Common Platform; this item governs the in-app inbox record and the content of what is handed to the delivery layer.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP099 — Account & app settings, thin aggregator
**Traces from:** TR099
**Status:** Ready for Review | **Confidence:** High

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | RLS-CC | — |
| Tampering | Y (High) | A settings write path that bypasses the owning component's own validation — for instance pausing discoverability by writing a flag directly rather than calling the Authorization Engine's pause/resume (TR024), which would skip its event publication and leave downstream state inconsistent | Settings endpoints are thin pass-throughs to the owning component's `interface.py`; **no independent settings data model exists**, so there is no second place a value can live and diverge | High |
| Repudiation | Y | A settings change with security consequence (pause/resume, visibility) not audited | Audit-CC via the owning component's own event, which is another reason the write must go through that component rather than around it | High |
| Information disclosure | N | Reads are self-scoped | RLS-CC | — |
| Denial of service | N | — | — | — |
| Elevation of privilege | Y | A settings write reaching a value the caller could not change through the owning component's own endpoint | Authorization is resolved by the owning component, not re-implemented in the settings layer | High |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Settings read/write | Class A / Class B | Load test |
| No second source of truth | Class G — no settings-owned table duplicates a value owned elsewhere | Schema-introspection check |
| Pass-through verification | 100% of settings writes route through the owning component's `interface.py` | Call-graph check in CI |

**Cautions**
Settings screens are a recurring source of authorization bypass precisely because they aggregate values from many owners and invite a shortcut write. The single-source-of-truth check is what keeps this thin aggregator thin.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP100 — Help & Support with safety-aware routing
**Traces from:** TR100
**Status:** Ready for Review | **Confidence:** Medium — a classifier sits on a legally-bound path; see Cautions

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | — | — | — |
| Tampering | N | — | — | — |
| Repudiation | Y | A support ticket describing a safety concern with no record of how it was routed — leaving no way to reconstruct why an SLA was missed | Audit-CC on intake and on the routing decision, capturing the classification outcome | High |
| Information disclosure | Y | Support tickets can contain highly sensitive free text (abuse descriptions) read by general support staff who are outside the safety case scope | Safety-classified tickets route into the Safety pipeline and inherit its case scoping (SP067); general support staff do not retain access to a ticket once it is reclassified as safety | High |
| Denial of service | N | Standard rate limiting | RateLimit-CC | — |
| Elevation of privilege | Y (**High — the item's core risk**) | **A routing miss is an SLA breach, not a UX annoyance.** A safety-urgent report submitted through Help and classified as general support sits in a slow queue while DEC-V1-006's legally binding clocks (24h acknowledge, 2h for the nudity/impersonation subset) run against Mangaly regardless. The classifier is therefore safety-critical code sitting on a legal deadline | Keyword/category classifier at intake with a **deliberate false-positive bias** — over-routing to Safety is cheap, under-routing is a legal breach, so the threshold must be tuned asymmetrically rather than for balanced accuracy. A universal, always-visible direct path to `POST /safety/report` (SP063) means no user depends on the classifier being right. Classifier behavior gets the same test investment CODING-GUIDE reserves for the Authorization Engine and event bus (IA100) | High |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Ticket intake | Class B | Load test |
| Routing decision | Class E — classification and routing complete within the ticket-creation transaction, so the SLA clock starts immediately rather than on later human triage | Integration test asserting clock start at intake |
| Classifier recall on safety content | Measured against a labelled corpus and reported; **misses are tracked as SLA-risk incidents**, not as model-quality statistics | Regression suite over labelled examples, re-run on every classifier change |
| Direct-path availability | 100% — the direct safety-report path is reachable from Help without depending on classification | Route-inventory check |

**Cautions**
Two points worth stating plainly. First, tune for recall over precision: the cost matrix here is asymmetric and a balanced-accuracy threshold is the wrong objective. Second, the classifier must never be the only path — the always-available direct route is what keeps a classifier miss recoverable by the user rather than silent.

**Assumptions** — none.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP101 — Logout and account deletion with DPDP-grounded disclosure
**Traces from:** TR101
**Status:** Ready for Review | **Confidence:** High — TR101's DPDP gating is now resolved by `v1-decisions.md` DEC-V1-010

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y (Critical) | Account deletion triggered by someone other than the account holder — a destructive, largely irreversible action and an obvious harassment vector in this module's family context | Self-identity required (not merely a grant); re-authentication required immediately before deletion, not merely a valid session; confirmation delivered to the account's own identifier | Critical |
| Tampering | Y | Logout that clears client state without revoking the server-side session, leaving a stolen token valid on a shared or lost device — a realistic scenario for this module's audience | `POST /auth/logout` revokes the session **server-side** in `mangaly_identity.session`; the client-side clear is a consequence, never the mechanism | Critical |
| Repudiation | Y | Deletion with no record of who requested it and when | Audit-CC on the deletion request, the 48-hour notice, and the final erasure — retained per DEC-V1-010's one-year processing-log floor even after the personal data itself is erased | High |
| Information disclosure | Y | The pre-confirmation disclosure must state accurately what is retained and why; a misleading disclosure is itself a DPDP compliance failure, not merely poor copy | Disclosure is generated from DEC-V1-010's concrete policy (30-day reactivation grace, erasure or irreversible anonymization within 90 days of the request, safety-evidence exception scoped to case plus 180 days, active legal hold blocking full deletion) rather than hand-written copy that can drift from actual behavior | High |
| Denial of service | Y | Deletion used as an attack if triggerable by another party | Same controls as Spoofing; the 30-day grace window makes an unauthorized deletion recoverable rather than terminal | High |
| Elevation of privilege | Y | A session surviving deletion, or another party's grants over the profile outliving it | Deletion revokes every session and every grant targeting the profile in the same transaction as the state change | Critical |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Logout | Class B; session invalid on the very next request | Integration test asserting the next request with the old token fails |
| Deletion request | Class B | Load test |
| Retention-job execution | Class F — the erasure job completes within 2× expected duration or alerts within 15 min; idempotent on re-run | Job monitoring (built independently of the retention *scope* question, per TR054) |
| 48-hour pre-erasure notice | 100% of pending erasures notify at least 48 h beforehand (DPDP Rules' explicit requirement, DEC-V1-010) | Job contract test |
| Grace/erasure window adherence | 30-day grace, erasure or anonymization within 90 days; zero records past the window absent an active legal hold | Scheduled compliance query, reported in Step 13 |

**Cautions**
DEC-V1-010 resolves what was previously carried as a DPDP legal-counsel blocker, using DPDP's own numeric anchors (a one-year processing-log floor, a three-year inactivity ceiling with 48-hour notice) plus the published practice of comparable Indian matrimonial platforms. It is a good-faith V1 interpretation of principles-based text rather than a number the Act states verbatim for this sector, and is revisable if a regulatory clarification narrows it — the same honest framing DEC-V1-005 uses. What matters for this item is that the retention job and the disclosure now have concrete numbers to build and test against instead of waiting on a sign-off with no owner.

**Assumptions** — per DEC-V1-010.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP102 — Cross-cutting mutation-endpoint idempotency middleware
**Traces from:** TR102 — **canonical statement of Idempotency-CC**
**Status:** Ready for Review | **Confidence:** High — a real cross-account defect was found here and fixed; see Cautions
**Findings routed:** one schema correction applied to `07a-db-implementation/` (migration `002-idempotency-account-scope.sql`)

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | The middleware runs after authentication; the key never establishes identity | — | — |
| Tampering | Y | A repeated key submitted with a *different* payload, either as a client bug or a deliberate attempt to have a stale success returned for a changed request | `request_hash` is stored with the key: a repeat with a differing hash is rejected as a client error rather than silently returning the earlier result | High |
| Repudiation | N | — | Audit-CC on the underlying mutation | — |
| Information disclosure | Y (**Critical — real defect found in the Sealed schema, now fixed**) | **Cross-account replay of a cached response.** The idempotency key is *client-generated* (TR102), yet `001-initial.sql` created `mangaly_platform.idempotency_key` with `UNIQUE (idempotency_key, endpoint)` — a **global** key namespace — while the table already carried an `account_id` column. A lookup on `(idempotency_key, endpoint)` alone therefore matches another account's row, and returns **account A's stored `response_snapshot` to account B** whenever keys collide, whether through a weak client key scheme, a replayed key an attacker observed, or plain collision. The schema comment asserting "there is no 'another actor's row' concept to leak here" was simply wrong for this table, and the surrounding `mangaly_platform` schema had RLS disabled on that basis | **Fixed, and verified live rather than reasoned about:** migration `002-idempotency-account-scope.sql` replaces the constraint with `UNIQUE (account_id, idempotency_key, endpoint)` and adds an RLS policy keyed on `mangaly.account_id` as defense in depth beneath the middleware's own server-side scoping. Verified against the running database as the non-owning `mangaly_app` role: account A sees its own row, **account B sees zero rows** for the identical key, B can still use that same key for its own row, and a query with no session context returns zero. The middleware must also include `account_id` in every lookup — the RLS policy is the second layer, not the first | Critical |
| Denial of service | Y (**High — same root cause**) | Under the global namespace, one account could deliberately burn idempotency keys on an endpoint and **block another account's writes**, since the victim's insert would conflict with the attacker's row. Cheap, targeted, and hard to diagnose | Closed by the same account-scoped constraint — keys now collide only within one account | High |
| Elevation of privilege | N | — | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Key lookup/insert | Class H — P95 < 20 ms, P99 < 50 ms even under retry burst | Shared-utility benchmark under simulated reconnect storms |
| Duplicate-suppression correctness | 100% — a repeated key returns the original result and **never re-executes** the mutation | Dedicated test per queueable endpoint (TR002, TR042, TR043, TR046, TR047, TR049, TR057, TR058), asserting the underlying record count is unchanged |
| Cross-account isolation | Class G — 100%; an identical key under a different account never returns the first account's snapshot | The live isolation test described above, run in CI rather than once by hand |
| Key expiry cleanup | Class F — the 7-day TTL cleanup job runs to completion and is idempotent | Job monitoring |

**Cautions**
Two things worth carrying forward. First, per TR102/IA102, `05-test-scenarios.md`'s TS228–229 verify that a queued write eventually succeeds or clearly fails; they do **not** test duplicate-write prevention, so Step 10 must add the per-endpoint duplicate test rather than assume existing coverage. Second, this item is the clearest argument in the file for testing shared utilities against real infrastructure: the defect was invisible in the design documents, which described the correct behavior throughout, and only became apparent when the actual constraint definition was read against the actual threat. The same scrutiny is owed to `rate_limit_counter`, whose keys are deliberately *not* account-scoped for the pre-authentication cases (login failure, OTP resend) — correct there, since no `mangaly.account_id` exists yet at that point, and now documented as a deliberate difference rather than an oversight.

**Assumptions** — the client-side offline queue is a separate mobile-engineering component (TR102); this item covers server-side idempotency only.
**Decisions (append-only)** — 2026-09-13: idempotency-key uniqueness scoped to `account_id`; RLS enabled on `mangaly_platform.idempotency_key`. Applied as migration `002-idempotency-account-scope.sql` and reflected in `schema.sql`; logged in `07a-er-model.md`'s revision history as a Step-8-sourced correction to a Sealed artifact.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP103 — `mangaly_identity.lookup_by_identifier()`: the pre-authentication RLS exception
**Traces from:** `07a-er-model.md` Assumptions #9 (supplementary item; no 1:1 TR — flagged by the ER model specifically for this step's review)
**Status:** Ready for Review | **Confidence:** Medium — a genuine and necessary exception, but it is the module's one deliberately unprotected read path

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | N | The function performs no authentication itself; it is a lookup the authentication flow uses | — | — |
| Tampering | N | Read-only | — | — |
| Repudiation | Y | Lookups leaving no trace, so a scripted enumeration campaign against the function would be invisible | Lookup attempts feed the same rate-limit counter and failure-signal path as SP093, so volume anomalies are detectable | Medium |
| Information disclosure | Y (**Critical — the item's whole reason for existing**) | This function necessarily runs **before any session variable exists**, so `mangaly.account_id` is unset and the normal RLS predicate cannot apply. It is therefore the one read path in the module not protected by row-level security — and it reads the credential table. If it accepted anything other than an exact identifier match (a prefix, a `LIKE`, a null-returns-all path, or a caller-supplied predicate), it would become a bulk-export oracle over `mangaly_identity.account` | Four constraints, all structural: (1) **exact-match only** on a full identifier — no pattern matching, no partial match, no ordering, no caller-supplied predicate; (2) **returns at most one row, and only the minimal columns** the authentication flow needs (account id, status, credential hash), never profile data or the full row; (3) **reachable only from the authentication flow's own code path**, never exposed as a general repository method other components can call; (4) **rate-limited on the same shared counter** as SP093/SP095, so it cannot be driven at enumeration volume | Critical |
| Denial of service | Y | Driving the function at volume to exhaust connections or to enumerate | RateLimit-CC via SP037's shared utility | Medium |
| Elevation of privilege | N | Returns data, grants nothing | — | — |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Lookup | Class A — single indexed exact-match row fetch | Load test |
| Exact-match enforcement | Class G — zero pattern-matching or partial-match code paths reachable through this function | Code review plus a static check on the function definition, re-run on every migration touching it |
| Column minimization | Returns only the authentication-required columns; asserted, not conventional | Contract test on the returned projection |
| Call-site restriction | Class G — reachable only from the authentication flow | Call-graph check in CI |
| Timing uniformity | Constant-time behavior for found and not-found, consistent with SP093's dummy-verify requirement | Latency-distribution test |

**Cautions**
This is the correct design — some pre-authentication lookup is unavoidable in any credential system — but it is the module's single most sensitive unprotected read, and every one of its four constraints is a *structural* property that a future refactor could quietly relax. Recommend the function be treated as a frozen surface: any change to its signature, projection, or predicate should require explicit security review rather than ordinary code review. Its existence is also a direct consequence of the interim credential store (SP104) and disappears when that store migrates to a platform identity service.

**Assumptions** — the function remains the only pre-authentication read path into `mangaly_identity`.
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13

---

## SP104 — The interim `mangaly_identity` credential store as a threat target
**Traces from:** `v1-decisions.md` "Known technical debt" / TR092 (supplementary item; whole-schema threat model rather than a single TR)
**Status:** Ready for Review | **Confidence:** Medium — the design is sound for an interim store; the residual risk is inherent to building one at all

**STRIDE analysis**
| Category | Applies? | Threat | Mitigation | Priority |
|---|---|---|---|---|
| Spoofing | Y (Critical) | Compromise of this schema is total account compromise for every member — it holds credentials, OTP challenges, reset tokens, and live sessions in one place, making it the module's highest-value single target by a wide margin | Argon2id credential hashing (per `v1-decisions.md`'s Step-8 note); single-use, short-TTL OTP and reset tokens (SP094/SP095); server-side session revocation (SP101); RLS keyed on `mangaly.account_id` with `mangaly_app` non-owning (live-verified) | Critical |
| Tampering | Y | A credential or session row altered to grant access — for instance a session's expiry extended or an account's status flipped to active without verification | Writes confined to Identity Bridge's own interface; every mutation audited (Audit-CC); schema-per-component prevents any other component writing here | Critical |
| Repudiation | Y | Authentication events not recorded, leaving no forensic trail after a compromise | Audit-CC on signup, login, logout, reset, and OTP verification — the events that matter most when reconstructing an incident | High |
| Information disclosure | Y (Critical) | Bulk credential exfiltration. Two realistic paths: the pre-authentication lookup function (SP103) and direct production-database access by a human (SP051's combined finding) | SP103's four structural constraints; SP051's DB-access-control review; RLS as defense in depth beneath both. Argon2id ensures an exfiltrated hash set is expensive rather than immediately usable — the reason the hashing choice is Critical rather than a detail | Critical |
| Denial of service | Y | The identity schema is on every request path via session validation, making it a single point of failure for the whole module | Class A/H latency budgets with indexed lookups; session validation is a single indexed read, not a join | Medium |
| Elevation of privilege | Y (Critical) | This schema is the root of trust for the entire authorization chain — every `AuthzContext` the chokepoint resolves ultimately derives from a session validated here, so a forged session escalates everywhere at once | Session tokens are high-entropy and server-validated on every request; revocation is immediate and server-side; no client-asserted identity is trusted anywhere downstream (SP017) | Critical |

**Performance thresholds**
| Metric | Threshold | Measurement method |
|---|---|---|
| Session validation | Class A — P95 < 200 ms; on the hot path for every authenticated request | Load test at 1,500 concurrent sessions |
| Credential verification | Deliberately slow (~250–500 ms Argon2id floor); a security property, not a latency regression | CI benchmark on deploy-target hardware |
| Expired-artifact cleanup | Class F — expired OTP challenges, reset tokens, and sessions purged on schedule; the job is idempotent | Job monitoring |
| RLS enforcement | Class G — `mangaly_app` owns zero tables in this schema (live-verified: 0/61 module-wide) | CI check on every deploy, not a one-time verification |

**Cautions**
Three things stated honestly. First, this schema exists only because Mangaly is first in build order with no Common Platform Identity & Trust Service to delegate to (ADR-016/017) — it is the correct decision under that constraint, not a shortcut, but it does mean the module owns credential security it would otherwise inherit from a hardened shared service. Second, the eventual migration of live credentials and sessions into that future platform service is a genuinely high-risk operation and is already recorded as known technical debt; it should be planned with its own threat model when it happens, not treated as a data move. Third, the concentration risk is real and unavoidable at this scale: everything in this file that depends on a resolved identity depends on this schema, so its controls deserve the same test investment CODING-GUIDE reserves for the Authorization Engine itself.

**Assumptions** — the interim store migrates to Common Platform once that module exists (`v1-decisions.md`, Known technical debt).
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Security Lead — [x] Approved — krishna kategaru, 2026-09-13
