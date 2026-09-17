---
step: 06-impact-analysis
module: MOD03
status: Sealed
approver: Architect / Director
updated: 2026-09-12
items: "102 | approved: 102 | blockers: 0"
---

# 06 — Impact & Plan Analysis — MOD03 Mangaly

**Scope note for this run:** the requesting message asked for "impact and
security analysis" in one pass. Security & Performance is Step 8 in this
pipeline, running after Step 7 (Tech Reqs/ER Model) — it is not folded into
this file. This document is Step 6 (Impact Analysis) only: dependency
identification and risk assessment per FR, plus the worth check. STRIDE
threat modeling and performance-threshold analysis belong to Step 8 and are
out of scope here, though several items below flag concerns (severity-tier
paging infra, retention/legal-hold mechanics, screenshot-capture limits)
that Step 8 should pick up directly rather than re-discover.

## Revision history

| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-12 | Initial version. Looped over all 102 Sealed FRs from `02-functional-requirements.md` one at a time, per this agent's own loop discipline: re-read each FR, `/ARCHITECTURE.md`'s resolved container/edge/shared-concern tables, `modules/MOD03-mangaly/architecture.md`'s 13-component C4-L3 breakdown, `v1-decisions.md`'s resolved values, `/MODULE-ARCHITECTURE-STANDARD.md`'s generic patterns (schema-per-component, authorization chokepoint, in-process event bus), and `CODING-GUIDE.md`'s stated defect-prevention controls, before writing each item's dependency table, risk table, and worth check. Live web research performed for the two dependencies this codebase has not exercised before and that a named FR's own SLA/behavior depends on: (a) India SMS/OTP delivery reliability (route selection, DLT template mismatch, ~5–8% single-channel non-delivery rate even when compliant — feeds IA095's risk assessment); (b) Postgres RLS performance/pitfalls at scale (5–15% overhead on simple queries, worse on joins; the `SET` vs `SET LOCAL` PgBouncer pitfall; policies silently no-op if the connecting role owns the table — feeds every item touching the Authorization Engine's RLS layer, most directly IA017/IA018); (c) mobile screenshot-prevention limits (Android `FLAG_SECURE` is a real OS-level block; iOS has no equivalent, only after-the-fact detection — feeds IA056, directly grounding FR056's own "risk-reduction, not guarantee" disclosure requirement rather than treating it as a hypothetical caveat). No FR was found requiring a dependency `/ARCHITECTURE.md` doesn't already resolve. Three genuine architecture-level gaps were surfaced and are flagged (not treated as blockers, since each has a concrete next owner) rather than smoothed over: (1) the Notification Bridge is documented as a "thin, no-schema" bridge in `architecture.md` §2.1, but FR098 requires a *persistent* in-app inbox, which needs somewhere to live — flagged for Step 7 to resolve which component/schema owns inbox persistence; (2) FR102's offline/queued-write resilience requires every mutation endpoint the client can queue to be idempotent, a cross-cutting API contract requirement no single component's traceability currently names — flagged for Step 7; (3) FR033's personality-assessment instrument is a genuinely unselected, vendor/IP-shaped open item structurally identical to the BR08 verification-vendor and BR07 horoscope-mechanism categories `v1-decisions.md` already tracks as external-gated, but it was not captured in that file's "What stays open" table — flagged here rather than silently treated as resolved. | Impact Analysis (Step 6) — krishna kategaru (autonomous), 2026-09-12. |
| 2026-09-12 | **Follow-up: every finding this file raised has been addressed, ahead of Step 7, per explicit instruction to resolve everything correctly before implementation begins.** IA033 → `v1-decisions.md`'s "What stays open" table now names the personality-assessment instrument. IA065/IA068/IA074 → `v1-decisions.md` DEC-V1-009 names a concrete on-call paging mechanism and the actual, verified legal CSAM reporting channel (POCSO Rules 2020 Rule 11: SJPU/local police/cybercrime.gov.in, including the Rule 11(2) source-material handover obligation) — both now recorded as real edges in `architecture.md` §1, not policy commitments with no built mechanism. IA098 → `architecture.md` §2.1/§2.2/§3 now makes the Notification Bridge schema-owning for its in-app inbox record specifically, resolving the "thin, no-schema" vs. "requires persistence" contradiction directly (this also surfaced and fixed a pre-existing, unrelated inconsistency: Operations was mislabeled "thin bridge" in one place while already correctly called "Business logic" elsewhere in the same file — corrected, and the component count corrected from a stale 13 to the accurate 14). IA102 → `/MODULE-ARCHITECTURE-STANDARD.md` §4b names idempotent mutation endpoints as a required generic pattern for any offline-capable module, applied concretely in `architecture.md` §3 and `CODING-GUIDE.md` §7. IA017's RLS pooling-safety findings (non-owning DB role; `SET LOCAL` under transaction pooling) are now binding requirements in `/MODULE-ARCHITECTURE-STANDARD.md` §4 and `CODING-GUIDE.md` §7, not left as a risk-table note. IA092's interim-account-migration risk is now recorded in `v1-decisions.md`'s new "Known technical debt" section. No finding in this file was left unaddressed. | Impact Analysis follow-up, addressing every raised finding — krishna kategaru (autonomous), 2026-09-12. |
| 2026-09-14 | Post-seal correction: ForKhatri platform identity. Added dated correction notes under IA090, IA092, IA093, IA094, IA095 and IA101. IA092's named migration debt is now being retired by the platform Identity & Trust Service (PA-DEC-08, TR23): active accounts imported with ids and Argon2id hashes, pending accounts not imported, interim credential routes switched off by a setting. Retirement work is in progress and is not claimed complete here. Not re-sealed; awaits the owner's review. | Product-owner instruction, 2026-09-14. See `docs/ParentApp/00c-identity-and-entrance-decisions.md` and `docs/ParentApp/07-tech-reqs.md`. |

## Coverage check

| Parent FR | Impact items produced | Covered |
|---|---|---|
| FR001 | IA001 | Yes |
| FR002 | IA002 | Yes |
| FR003 | IA003 | Yes |
| FR004 | IA004 | Yes |
| FR005 | IA005 | Yes |
| FR006 | IA006 | Yes |
| FR007 | IA007 | Yes |
| FR008 | IA008 | Yes |
| FR009 | IA009 | Yes |
| FR010 | IA010 | Yes |
| FR011 | IA011 | Yes |
| FR012 | IA012 | Yes |
| FR013 | IA013 | Yes |
| FR014 | IA014 | Yes |
| FR015 | IA015 | Yes |
| FR016 | IA016 | Yes |
| FR017 | IA017 | Yes |
| FR018 | IA018 | Yes |
| FR019 | IA019 | Yes |
| FR020 | IA020 | Yes |
| FR021 | IA021 | Yes |
| FR022 | IA022 | Yes |
| FR023 | IA023 | Yes |
| FR024 | IA024 | Yes |
| FR025 | IA025 | Yes |
| FR026 | IA026 | Yes |
| FR027 | IA027 | Yes |
| FR028 | IA028 | Yes |
| FR029 | IA029 | Yes |
| FR030 | IA030 | Yes |
| FR031 | IA031 | Yes |
| FR032 | IA032 | Yes |
| FR033 | IA033 | Yes |
| FR034 | IA034 | Yes |
| FR035 | IA035 | Yes |
| FR036 | IA036 | Yes |
| FR037 | IA037 | Yes |
| FR038 | IA038 | Yes |
| FR039 | IA039 | Yes |
| FR040 | IA040 | Yes |
| FR041 | IA041 | Yes |
| FR042 | IA042 | Yes |
| FR043 | IA043 | Yes |
| FR044 | IA044 | Yes |
| FR045 | IA045 | Yes |
| FR046 | IA046 | Yes |
| FR047 | IA047 | Yes |
| FR048 | IA048 | Yes |
| FR049 | IA049 | Yes |
| FR050 | IA050 | Yes |
| FR051 | IA051 | Yes |
| FR052 | IA052 | Yes |
| FR053 | IA053 | Yes |
| FR054 | IA054 | Yes |
| FR055 | IA055 | Yes |
| FR056 | IA056 | Yes |
| FR057 | IA057 | Yes |
| FR058 | IA058 | Yes |
| FR059 | IA059 | Yes |
| FR060 | IA060 | Yes |
| FR061 | IA061 | Yes |
| FR062 | IA062 | Yes |
| FR063 | IA063 | Yes |
| FR064 | IA064 | Yes |
| FR065 | IA065 | Yes |
| FR066 | IA066 | Yes |
| FR067 | IA067 | Yes |
| FR068 | IA068 | Yes |
| FR069 | IA069 | Yes |
| FR070 | IA070 | Yes |
| FR071 | IA071 | Yes |
| FR072 | IA072 | Yes |
| FR073 | IA073 | Yes |
| FR074 | IA074 | Yes |
| FR075 | IA075 | Yes |
| FR076 | IA076 | Yes |
| FR077 | IA077 | Yes |
| FR078 | IA078 | Yes |
| FR079 | IA079 | Yes |
| FR080 | IA080 | Yes |
| FR081 | IA081 | Yes |
| FR082 | IA082 | Yes |
| FR083 | IA083 | Yes |
| FR084 | IA084 | Yes |
| FR085 | IA085 | Yes |
| FR086 | IA086 | Yes |
| FR087 | IA087 | Yes |
| FR088 | IA088 | Yes |
| FR089 | IA089 | Yes |
| FR090 | IA090 | Yes |
| FR091 | IA091 | Yes |
| FR092 | IA092 | Yes |
| FR093 | IA093 | Yes |
| FR094 | IA094 | Yes |
| FR095 | IA095 | Yes |
| FR096 | IA096 | Yes |
| FR097 | IA097 | Yes |
| FR098 | IA098 | Yes |
| FR099 | IA099 | Yes |
| FR100 | IA100 | Yes |
| FR101 | IA101 | Yes |
| FR102 | IA102 | Yes |

## Set-level quality gate

| Check | Result |
|---|---|
| Every FR analyzed | Pass — 102/102, IA001–IA102. |
| Cross-module dependencies checked against modules.md | Pass — modules.md declares exactly two Mangaly-relevant edges: MOD03→MOD06 (Payment Services, async `benefit_eligible` events, optional) and MOD05→MOD03 (Dashboard, async `mangaly.activity_summary` events, read-only, one-way). Both checked against every FR below. |
| No undeclared cross-module dependency found | Pass — no FR in this set calls, queries, or assumes state from Vyapar, Milavn, Counsel, Dashboard, Payment Services, or Loans & Finance beyond these two declared, already-resolved async edges. |
| Declared MOD03→MOD06 edge exercised by this FR set | **Observation, non-blocking:** none of the 102 Sealed FRs actually emit a `benefit_eligible` event — no FR in this set implements the premium-membership/enhanced-matchmaking/professional-matchmaking-fee capability `modules.md`'s MOD03 "Depends on" line names as the reason for this edge. This is not a gap in this FR set (BR01–BR20 as sealed genuinely do not include a monetization/paywall BR — the source `Mangaly_Master_Requirements_Input_v1.0.md`-derived BR set is candidate/family-experience-first, per this module's own build-order rationale), nor is it a defect in `modules.md`'s decomposition (the edge is correctly marked "optional" there for exactly this reason). Recorded here so Step 7 doesn't have to independently rediscover that this edge is currently dormant, not broken. |
| Declared MOD05←MOD03 edge exercised by this FR set | Pass, with one item flagged: IA081 (FR081, profile lifecycle transition) is the natural publisher of the `mangaly.activity_summary` event Dashboard subscribes to; no other FR needs to touch this edge, and IA081 confirms the event stays privacy-filtered per `/ARCHITECTURE.md`'s own resolution (never raw match/profile data). |
| Architecture-level gaps surfaced this pass | Three, none blocking (see Revision history): (1) Notification Bridge schema ownership for the persistent inbox (FR098) — flagged for Step 7; (2) cross-cutting idempotency requirement on every client-queueable mutation (FR102) — flagged for Step 7; (3) FR033's personality-assessment instrument is an unselected external-gated item not currently named in `v1-decisions.md`'s "What stays open" table — flagged for the Product Manager to either add there or confirm FR033 ships without it at V1 (see IA033's worth check). |

## Open blockers

None. Every genuinely external-gated dependency identified below (DPDP-Act
retention/legal-hold sign-off — FR050/FR053/FR054/FR101; verification-vendor
selection — FR035/FR037; the personality-assessment instrument — FR033; the
deliberately-deferred BR17 Agent layer — FR077/FR078) is named explicitly in
its own item's risk assessment and worth check, exactly as `v1-decisions.md`'s
own "What stays open" table already treats the first three categories — none
of these block this file's own Sealing, consistent with this pipeline's
established convention that a named, owned external dependency is not the
same thing as an open blocker.

---

## IA001 — Create and Save a Minimum Viable Profile
**Traces from:** FR001
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type (service/data/contract/module) | Cross-module? |
|---|---|---|
| Mangaly DB — `mangaly_profile` schema | data | No |
| Authorization Engine (existence-check does not itself gate save, but every subsequent read does) | contract, in-process | No |
| Identity & Trust Service (profile binds to an already-authenticated `member_id`) | service, sync REST/JWT | No |
| Audit Bridge → Audit Service (profile-created event, BR15) | service, async (Broker) | No |
| DEC-V1-001 existence-tier field list (`v1-decisions.md`) | data/config | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Mangaly DB schema | Low | Medium (a schema-migration mistake here blocks every downstream capability, since nothing else in the module has a profile without this) | Yes — TS001–TS002 assert save/reject on required-field completeness |
| Authorization Engine | Low at this FR (first-party write, no viewer yet) | Low | Yes — covered indirectly by TS001–TS002 |
| Identity & Trust Service | Low (stable, already the base dependency of every module per ADR-004) | Medium (an outage here blocks profile creation platform-wide, not just Mangaly) | Partial — TS001–TS002 test Mangaly's own save logic, not Identity & Trust availability/degradation behavior, which is a Step 8 (Security & Performance) concern |
| DEC-V1-001 field list | Low (now a resolved, versioned decision, not a live guess) | Low | Yes — the field list itself is fixed; TS001–TS002 exercise it directly |

**Worth check**
Yes, proceed. This is the first demoable slice by design (per the FR file's own PM sequencing note) and every dependency is already resolved (DEC-V1-001 closed the field-list gap the FR itself carried as Medium confidence). No new risk surfaces once DEC-V1-001 is applied.

**Assumptions** — Identity & Trust Service availability is a platform-level SLA (99.9% per `/ARCHITECTURE.md`'s Non-functional baselines), not re-litigated here.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA002 — Extend Profile Across All Categories, Including Declined Fields
**Traces from:** FR002
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Mangaly DB — `mangaly_profile` schema | data | No |
| Object Storage (photos, video introduction) | service | No |
| Authorization Engine (per-category edit is still the owner's own write, low authorization complexity, but every later read of these categories routes through it) | contract, in-process | No |
| Audit Bridge (category-level edit events) | service, async (Broker) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Mangaly DB schema (declined-vs-blank as a distinct state) | Medium (a common implementation shortcut is to store "declined" as null, indistinguishable from "never answered") | Medium (silently collapses a BR01-required distinction; would surface downstream as an incorrect completeness/fairness signal, not a crash) | Yes — TS003–TS005 explicitly assert declined is distinct from blank |
| Object Storage | Medium (upload failures on tier-2/3 connectivity are a realistic, named condition for this audience) | Medium (a failed photo/video upload blocking the rest of a category save would violate this FR's own "failed save on one category preserves edits for retry" rule) | Partial — TS003–TS005 cover the data-model distinction; large-media-upload-failure retry behavior is not obviously in scope of those two scenario IDs and should be confirmed at Step 7/10 |
| Authorization Engine | Low | Low | Yes |

**Worth check**
Yes, proceed as specified.

**Assumptions** — exact field schema per category remains implementation-stage per BR01 Constraints, as the FR itself already states; this does not block building the category-independence and declined-state behavior this FR actually requires.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA003 — Discoverability Tier Gate, Independent of Enhanced-Matching Tier
**Traces from:** FR003
**Status:** Ready for Review
**Confidence:** High (upgraded from the FR's own Medium — DEC-V1-001 now fixes the field list this FR's gate logic reads)

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Mangaly DB — `mangaly_profile` schema | data | No |
| Discovery & Ranking component (the actual enforcement point that calls this gate) | contract, in-process | No |
| DEC-V1-001 discoverability-tier field list | data/config | No |
| Authorization Engine (gate result feeds an authorization-adjacent decision — visibility) | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| DEC-V1-001 field list | Low (fixed, versioned) | High if wrong (a bug here either wrongly excludes legitimate candidates from Discovery — a real product-trust failure — or wrongly includes underqualified profiles) | Yes — TS006–TS007 directly assert this |
| Discovery & Ranking coupling | Low | Medium (this is the exact seam FR027 re-tests from the Discovery side; a divergence between FR003's gate and FR027's enforcement would be a real, silent defect) | Partial — TS006-007 and TS064-065 (FR027) test each side independently; no scenario explicitly asserts the two logics never diverge over time (e.g., a future edit to one without the other) |

**Worth check**
Yes, proceed. Recommend Step 7 model the tier-gate as one shared function/service call from both FR003's and FR027's enforcement points (not two independent implementations of the same rule), specifically to close the divergence risk noted above.

**Assumptions** — none beyond DEC-V1-001.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA004 — Enhanced-Matching Fields Are Optional and Non-Blocking
**Traces from:** FR004
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Mangaly DB — `mangaly_profile` schema | data | No |
| Compatibility Engine (must degrade gracefully to available-data-only explanations) | contract, in-process | No |
| Discovery & Ranking (must confirm zero eligibility penalty) | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Compatibility Engine graceful-degradation path | Medium (a "not enough data" code path is easy to under-test since it is the less-common branch) | Medium (if it throws instead of degrading, a candidate who legitimately declines enrichment gets a broken experience, not just a lower-richness one) | Yes — TS008–TS009 cover this directly |
| Discovery & Ranking | Low | Low | Yes |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA005 — Three-Tier Completeness Status Display
**Traces from:** FR005
**Status:** Ready for Review
**Confidence:** High (upgraded from the FR's own Medium — DEC-V1-001 resolves the tier mapping this display reads)

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Profile & Completeness component (FR001/FR003's tier calculations) | contract, in-process | No |
| DEC-V1-001 tier field list | data/config | No |
| API layer (read-only display endpoint) | contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Tier calculations (FR001/FR003) | Low (display-only, no independent logic of its own) | Low (a display bug here is confusing, not consequential — it does not change actual Discovery eligibility) | Yes — TS010–TS011 |

**Worth check**
Yes, proceed. Low-risk, UI-facing slice with no independent business logic of its own.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA006 — Media Visibility Follows Profile Authorization
**Traces from:** FR006
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Authorization Engine (FR017's chain, deny-by-default) | contract, in-process (structural chokepoint) | No |
| Object Storage (the actual media bytes) | service | No |
| Postgres RLS policy on `mangaly_profile` schema | data (infra control) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Authorization Engine | Low (chokepoint pattern by design, per `/MODULE-ARCHITECTURE-STANDARD.md` Section 5 — a component cannot accept a bare actor ID and decide for itself) | Critical if it fails — an authorization defect here is a direct sensitive-photo/video leak to an unauthorized viewer, the single most reputationally damaging failure mode this module has | Yes — TS012–TS013, plus TS038–TS043 (FR017's own suite) indirectly cover the underlying chain this FR calls |
| Object Storage access-URL generation | Medium (a common real-world bug class: a signed/pre-authorized media URL that does not expire, or is guessable/shareable) | High (an unexpired or guessable media URL bypasses the authorization check entirely — the check happens at the API layer, not necessarily at the storage layer) | Partial — TS012–TS013 test the authorization decision; whether the resulting media URL itself enforces access (not just the API that issues it) is a Step 8 (Security & Performance) STRIDE-relevant concern, not fully covered by a functional test scenario |

**Worth check**
Yes, proceed — this is a Must-priority FR with no viable simpler alternative. Flagging the signed-URL expiry/scoping question explicitly for Step 8, since a functional test scenario proving "authorization denies unauthorized viewers" does not by itself prove "the media URL an authorized viewer receives cannot be replayed by someone else."

**Assumptions** — Object Storage supports time-bound, per-request signed URLs (a standard capability of the object-storage/CDN class named in `/ARCHITECTURE.md`'s Container diagram); not independently verified against a specific vendor at this step.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA007 — Search for and Invite a User to a Home Circle
**Traces from:** FR007
**Status:** Ready for Review
**Confidence:** Medium — depends on a platform-level username-lookup capability this FR assumes exists but that `/ARCHITECTURE.md` does not explicitly name as a resolved Identity & Trust Service capability.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Mangaly DB — `mangaly_home_circle` schema | data | No |
| Identity & Trust Service (username lookup — see confidence note) | service, sync REST/JWT | No |
| Notification Bridge (invitee notification) | service, async (Broker) | No |
| Audit Bridge (invitation created) | service, async (Broker) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Identity & Trust Service username lookup | Medium (the FR's own Assumptions line already flags this as relying on a platform capability, not something Mangaly's BR/FR set independently confirms exists on the Identity & Trust Service's contract) | Medium (if this capability does not actually exist yet on Identity & Trust Service, this FR either cannot ship as specified or Mangaly must build its own directory lookup, duplicating identity data it should not own per ADR-004) | Partial — TS016–017 test invitation creation assuming the lookup succeeds; they do not test the lookup contract itself, since that contract's existence is exactly what is uncertain |
| Notification Bridge | Low | Low | Yes |

**Worth check**
Yes, proceed, but this is a genuine, concrete finding for Step 7: confirm with Identity & Trust Service's actual (or planned) API surface that a username-lookup-by-authenticated-caller endpoint exists before building against it as an assumption. If it does not exist yet (plausible, since Mangaly is the first module built and Identity & Trust Service itself is still being stood up alongside it per ADR-017), Mangaly needs either a narrow, explicitly-scoped addition to that service's contract or a documented interim (e.g., invite-by-phone/email rather than username) — not a silent workaround.

**Assumptions** — carries forward the FR's own stated assumption; not independently resolved by this pass.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA008 — Accept Invitation
**Traces from:** FR008
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Mangaly DB — `mangaly_home_circle` schema | data | No |
| Identity & Trust Service (invitee's own authenticated identity) | service, sync REST/JWT | No |
| Audit Bridge (acceptance event, BR15) | service, async (Broker) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Mangaly DB (expired/withdrawn invitation state) | Low | Low (worst case is a stale invitation acceptance, a data-integrity nuisance, not a safety issue) | Yes — TS018–019 |
| Audit Bridge | Low | Medium (Home Circle membership is the base fact every later authorization decision in this module keys off; an unrecorded acceptance event is a real accountability gap, not a cosmetic one) | Yes — TS018–019 assert membership-record creation, which implies the audit path |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA009 — Ignore or Decline Invitation
**Traces from:** FR009
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Mangaly DB — `mangaly_home_circle` schema | data | No |
| Audit Bridge (decline recorded distinctly from silence) | service, async (Broker) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Mangaly DB state model (decline vs. silence as genuinely distinct states) | Low | Low | Yes — TS020–021 |

**Worth check**
Yes, proceed. Simple, low-risk terminal-state FR with no external dependency of note.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA010 — Remove a Member or Leave Voluntarily
**Traces from:** FR010
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Mangaly DB — `mangaly_home_circle` schema | data | No |
| Authorization Engine (immediate revocation of ongoing access) | contract, in-process (structural chokepoint) | No |
| Audit Bridge (historical accountability preservation, BR15) | service, async (Broker) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Authorization Engine — "immediate" revocation | Medium (a genuine, well-known distributed-systems risk: if authorization context is cached — session tokens, RLS session variables — a removed member may retain effective access until that cache/session naturally expires, not truly immediately) | Medium (a removed/malicious former member retaining brief residual access to family matrimonial data is a real, not hypothetical, privacy failure mode for exactly the sensitivity level this module is isolated for) | Partial — TS022–024 test that future access is denied on the next authorization check; they do not obviously test the cache/session-invalidation latency window itself, which is where the real risk sits |
| Mangaly DB / Audit Bridge (history preserved) | Low | Low | Yes — TS022–024 |

**Worth check**
Yes, proceed, with a named follow-up for Step 7: specify the authorization-context/session invalidation mechanism precisely enough that "immediately" is a testable latency bound (e.g., no cached AuthzContext may outlive N seconds past a revocation event), not just a qualitative promise.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA011 — Report a False or Inappropriate Relationship Claim
**Traces from:** FR011
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Mangaly DB — `mangaly_home_circle` and `mangaly_operations` schemas | data | No |
| Operations component (BR16 case queue) | contract, in-process | No |
| Authorization Engine (withholds disputed access pending investigation) | contract, in-process | No |
| Audit Bridge | service, async (Broker) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Operations component (case creation) | Low | Medium (a report that fails to reach the BR16 queue is a false relationship claim left unresolved, which is exactly the risk BR02 named) | Yes — TS025–026 |
| Authorization Engine (access withheld pending review) | Low | Medium (same residual-access latency concern as IA010, applied to a disputed rather than voluntarily-removed relationship) | Partial — same caveat as IA010 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA012 — Solo-Candidate Parity and Re-Forming a Circle
**Traces from:** FR012
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Every business-logic component named in the FR (Profile, Discovery, Compatibility, Trust, Connection, Sharing, Communication, Contact Exchange, Safety, Accountability) | contract, in-process (negative-dependency check — none of these may require non-zero Home Circle membership) | No |
| Mangaly DB — `mangaly_home_circle` schema (zero-member state, re-founding) | data | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Every listed component's independence from Home Circle state | Medium (this is precisely the kind of implicit-coupling regression that creeps in over time — a future feature added to, say, Connection & Sharing that casually reads home_circle.members without an explicit reason is an easy accident, not a deliberate one) | High if it recurs (BR02's entire "additive, never a precondition" commitment collapses the moment any one capability quietly requires Home Circle membership) | Yes at a point-in-time — TS027–028 exercise a zero-member account against the full capability list; No as an ongoing regression guard — nothing in 05-test-scenarios.md's scope, as scoped, re-runs this check automatically whenever a new component or feature is added later |

**Worth check**
Yes, proceed. This FR is correctly framed as the closing invariant for BR02's whole FR group. Recommend Step 10 (Test Automation) tag TS027–028 specifically for inclusion in every future component's own regression suite, not just Home Circle's, given the "any future component could silently violate this" risk identified above.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---
## IA013 — Independent, Parallel Family Search
**Traces from:** FR013
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Discovery & Ranking component | contract, in-process | No |
| Authorization Engine (BR04 scope grant resolution) | contract, in-process (structural chokepoint) | No |
| Mangaly DB — `mangaly_home_circle` schema (relative's granted scope) | data | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Authorization Engine scope resolution | Low (chokepoint pattern) | Medium (an over-broad scope grant would let a relative search beyond what the candidate authorized, a direct BR04 violation) | Yes — TS029–030 assert both the zero-prior-activity case and scope-restriction enforcement |
| Discovery & Ranking | Low | Low | Yes |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA014 — Suggest a Profile (Suggestion ≠ Decision)
**Traces from:** FR014
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Discovery & Ranking (source of the suggested profile) | contract, in-process | No |
| Connection & Sharing (must NOT be auto-triggered — negative dependency) | contract, in-process | No |
| Mangaly DB — `mangaly_home_circle` schema (suggestion record) | data | No |
| Authorization Engine | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Connection & Sharing non-trigger boundary | Medium (a suggestion and a connection request are adjacent user actions in the same flow; a UI/API shortcut that conflates "suggest" with "send request" is an easy implementation mistake) | Medium (would silently let a family member initiate a BR09 action on the candidate's behalf without the candidate's own decision, violating BR03's core "initiation authority ≠ decision authority" rule) | Yes — TS031–032 explicitly assert a suggestion never auto-triggers a BR09 action |

**Worth check**
Yes, proceed as specified — this is BR03's central value proposition and the negative-dependency boundary is already well-covered by the named test scenario.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA015 — Independent Candidate Search and Family-Involvement Timing
**Traces from:** FR015
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Discovery & Ranking (candidate's own search activity) | contract, in-process | No |
| Authorization Engine (denies family visibility into candidate's private search by default) | contract, in-process (structural chokepoint) | No |
| Mangaly DB — `mangaly_home_circle` schema | data | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Authorization Engine default-deny on search-activity visibility | Low (deny-by-default is the chokepoint's own baseline behavior per FR017) | Medium (a leak here exposes a candidate's private search behavior to family without consent, a direct BR03/BR05 privacy violation) | Yes — TS033–034 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA016 — Private Family Notes, Forwarded Only with Candidate Approval
**Traces from:** FR016
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Mangaly DB — `mangaly_home_circle` schema (notes) | data | No |
| Authorization Engine (candidate-approval gate on forwarding) | contract, in-process (structural chokepoint) | No |
| Communication component (negative dependency — notes must not be able to capture private BR11 conversation content) | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Authorization Engine forwarding gate | Low | Medium (an unapproved note reaching the candidate is a direct BR03 privacy violation, though contained to family-authored content rather than third-party data) | Yes — TS035–037 |
| Communication content-capture boundary | Medium (a free-text note field is, by nature, capable of having private conversation content pasted into it by a family member with access to both surfaces) | Medium (this is a data-minimization/scope violation rather than an authorization bypass — the note author already has legitimate access to whatever they'd paste, so the harm is scope creep in what circulates via notes, not a new access grant) | Partial — TS035–037 test forwarding/approval mechanics; whether note content is checked against a "no captured private-communication content" rule is not obviously a testable technical control (it is closer to a policy/product-copy guardrail than an enforceable data-model constraint) |

**Worth check**
Yes, proceed. The Communication-content boundary is honestly a soft (policy-level) control, not a hard technical one — recommend Step 7 note this explicitly rather than imply a false sense of enforcement.

**Assumptions** — notes are scoped strictly to matrimonial evaluation content, per BR03 Assumptions; this is a product/policy boundary, not a database constraint.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA017 — Authorization Chain Evaluation, Deny by Default
**Traces from:** FR017
**Status:** Ready for Review
**Confidence:** High — but see the elevated-scrutiny note below; this is the single highest-blast-radius item in this file.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Every business-logic component (Profile, Home Circle, Discovery, Compatibility, Trust, Connection, Communication, Safety, Lifecycle) — each depends on this component as a mandatory chokepoint | contract, in-process (structural chokepoint, per `/MODULE-ARCHITECTURE-STANDARD.md` §5) | No |
| Identity & Trust Service (base identity/relationship resolution) | service, sync REST/JWT | No |
| Mangaly DB — `mangaly_authz` schema | data | No |
| Postgres RLS session-context variable (`mangaly.authz_context`) set by this component, read by every other schema's RLS policy | data (infra control, defense-in-depth per CODING-GUIDE §1/§7) | No |
| Audit Bridge (every grant/deny decision logged) | service, async (Broker) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Structural chokepoint correctness | Low (the whole point of the chokepoint pattern, per `/MODULE-ARCHITECTURE-STANDARD.md` §5 and CODING-GUIDE §3, is that a component *cannot* accept a bare actor ID and self-decide — this is enforced by a lint-blocked import boundary, not convention) | **Critical** — CODING-GUIDE itself names this and the event bus as "the two components worth the deepest test investment"; a defect here has structural blast radius across all ten business-logic components, per this module's own stated architecture rationale | Yes, uniquely strong for this item — TS038–TS043 exist specifically for this FR and CODING-GUIDE explicitly calls out this suite by name as the deepest-investment target |
| RLS defense-in-depth layer | Medium — live research (2026-09-12) confirms two concrete, real-world RLS pitfalls relevant here: (a) RLS is silently bypassed if the application connects as a role that owns the table rather than one RLS actually restricts; (b) under PgBouncer transaction-mode pooling, using `SET` instead of `SET LOCAL` for the session context variable lets the context leak across pooled connections/transactions, a genuine, previously-seen production bug class, not a hypothetical one | High if it recurs (a leaked or wrong `authz_context` under connection pooling would let one request's authorization decision apply to a different request/user's query, defeating the entire defense-in-depth purpose CODING-GUIDE §1 gives for adding RLS in the first place) | No — this is an infrastructure/connection-pooling configuration concern, not a business-logic behavior; nothing in `05-test-scenarios.md`'s FR-driven scenario set would catch a `SET` vs. `SET LOCAL` misconfiguration, since that is an integration/ops-level correctness question, explicitly flagged here for Step 7 (schema/connection-pooling design) and Step 8 (Security & Performance) rather than assumed covered |

**Worth check**
Yes, proceed — there is no alternative to building this component correctly; it is the foundation the rest of the module's privacy model depends on. Given the severity finding above, explicitly recommend Step 7 specify PgBouncer (or equivalent) pooling mode and confirm `SET LOCAL` (not `SET`) is used for the RLS context variable, and that the application's database role does not own the tables its RLS policies are meant to restrict — both are concrete, checkable design decisions, not vague cautions.

**Assumptions** — exact permission matrix/taxonomy remains implementation-stage per BR04 Constraints, as the FR itself states; this does not affect the chain-evaluation model or chokepoint pattern itself.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA018 — Candidate vs. Family Information as Separate Authorization Categories
**Traces from:** FR018
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Authorization Engine (`mangaly_authz` schema data model) | contract + data, in-process | No |
| Postgres RLS policies keyed on category | data (infra control) | No |
| Every component that stores or displays candidate vs. family data (Profile, Home Circle, Discovery, Connection & Sharing) | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Authorization data-model category separation | Low (this is a schema-design decision more than a runtime behavior — once modeled as two distinct grant types, conflation becomes structurally harder, not just discouraged) | Medium (a conflated grant would silently violate BR05's "Important Family Boundary," the same failure class as FR023) | Yes — TS044–045 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA019 — Plain-Language Capability Presentation
**Traces from:** FR019
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Authorization Engine (source of the capability facts being translated to copy) | contract, in-process | No |
| API/UI layer (copy rendering) | contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Copy/presentation layer | Low | Low (a copy-quality defect is a UX issue, not a security or data-exposure issue — the underlying authorization decision is unaffected) | Yes — TS046–047 |

**Worth check**
Yes, proceed. Lowest-risk item in this BR group — presentation-only, no independent logic.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA020 — Meaningful, Sufficient Information for Authorized Viewers
**Traces from:** FR020
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Authorization Engine (determines "authorized viewer" status) | contract, in-process | No |
| Profile & Completeness (source of the displayed content) | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Product-design discipline against reintroducing a teaser pattern | Medium (a future monetization feature — e.g., a premium-tier upsell — is the realistic path by which a teaser-style gate could be reintroduced, since it is a common commercial pattern in adjacent products this team may reference) | Medium (directly contradicts BR05's explicit non-goal and this module's stated differentiation from dating-app patterns) | Yes at a point-in-time — TS048–049; **No as an ongoing guard** against a future monetization feature reintroducing this pattern, similar to IA012's regression-guard gap |

**Worth check**
Yes, proceed. Recommend this invariant be added to whatever design-review checklist any future monetization/premium-tier FR is evaluated against, given the declared-but-unexercised MOD06 Payment Services edge noted in this file's Set-level quality gate — the moment a premium tier is actually built, this is exactly the FR it must not silently violate.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA021 — Separate Display of Candidate vs. Family Info; Visibility ≠ Searchability
**Traces from:** FR021
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Discovery & Ranking (searchability state, independent of per-viewer visibility) | contract, in-process | No |
| Authorization Engine (per-viewer visibility) | contract, in-process | No |
| Mangaly DB — `mangaly_discovery` and `mangaly_authz` schemas | data | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Searchability/visibility independence across two components | Medium (this is a genuine two-component integration risk: Discovery's index and Authorization's per-viewer grant are necessarily separate data paths, and conflating them — e.g., indexing only what a specific viewer can see, or exposing full content to anyone who can find a profile — are both plausible implementation mistakes in opposite directions) | Medium (over-conflation toward "visible if searchable" is a direct information-exposure defect; under-conflation toward "not searchable unless fully visible" would wrongly hide legitimate profiles from Discovery) | Yes — TS050–051 |

**Worth check**
Yes, proceed. Recommend Step 7 explicitly document these as two independently-queried states in the data model (a `searchable` flag on the Discovery index vs. a per-viewer `AuthzContext` resolution) so implementers do not conflate them by convenience.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA022 — No Popularity or Demand Signal Exposure
**Traces from:** FR022
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Profile & Completeness, Discovery & Ranking (both must lack any such field/counter, by construction) | contract, in-process (negative-dependency / absence check) | No |
| API/UI layer (must never render such a value even if one existed internally for analytics) | contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Absence-by-construction of view/rejection counters | Low if built as an absence from day one (per CODING-GUIDE §6, "no swipe-card model exists" is exactly this style of test — a schema/contract absence assertion) | High if it recurs (reintroducing any such signal, even for internal analytics that later leaks into a UI surface, is a direct violation of the module's core anti-dating-app differentiation) | Yes — TS052–053, and CODING-GUIDE §6 explicitly instructs this class of test be written as a real schema/contract assertion, not skipped for "having nothing to call" |

**Worth check**
Yes, proceed. The absence-testing discipline CODING-GUIDE already names for this exact pattern is the right control; no further mitigation needed at this step.

**Assumptions** — internal, non-user-facing analytics counters (if any exist for product-metrics purposes) are out of this FR's scope, which governs user-facing exposure only; Step 7/8 should confirm no such internal counter is ever wired into a ranking or display path.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA023 — Family-Boundary Enforcement Toward a Prospective Match
**Traces from:** FR023
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Authorization Engine (Home Circle exposure gate) | contract, in-process (structural chokepoint) | No |
| Discovery & Ranking (the surfacing event this FR governs) | contract, in-process | No |
| Home Circle component | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Authorization Engine Home-Circle-exposure gate | Low (chokepoint pattern) | High (this is the exact scenario BR05 names as its highest-risk point — a parent's search leaking their own Home Circle to a stranger candidate is a serious, reputationally damaging privacy failure) | Yes — TS054–055 |

**Worth check**
Yes, proceed — this is one of the highest-value, highest-risk protections in the module and is already well covered by both the chokepoint pattern and a dedicated test scenario.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA024 — Pause Without Signalling; Controlled Safety Exceptions
**Traces from:** FR024
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Profile & Completeness (pause state) | data, in-process | No |
| Authorization Engine (the narrow, audited exception path) | contract, in-process (structural chokepoint) | No |
| Safety Intelligence (BR14 trigger for the exception) | contract, in-process | No |
| Operations component (routes over-broad exceptions to human investigation) | contract, in-process | No |
| Audit Bridge (every exception logged) | service, async (Broker) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Pause-state non-broadcast | Low | Low (worst case is a cosmetic "away" indicator leak, not a data-exposure event) | Yes — TS056–059 |
| Safety-exception path | Medium (by definition, this is a deliberate authorization-rule bypass mechanism; any bypass mechanism, even a legitimate one, is disproportionately attractive as a target for misuse or scope-creep over time) | **High** — an over-broad or insufficiently-audited exception here would defeat FR017's entire deny-by-default model for exactly the cases where a candidate is most vulnerable (an active safety concern), which is the worst possible moment for an authorization control to weaken | Partial — TS056–059 cover the two named behaviors; whether the exception path itself gets the same "deepest test investment" CODING-GUIDE reserves for the Authorization Engine and event bus is not explicit — recommend it does, given this is the one place those two components' guarantees are deliberately relaxed |

**Worth check**
Yes, proceed — the capability is necessary (Safety Intelligence cannot function without some override path), but recommend Step 7/8 treat this exception path with the same test-investment priority CODING-GUIDE gives the Authorization Engine itself, not as a minor edge case of FR024.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---
## IA025 — Discovery Available to Candidates and Family, in Parallel
**Traces from:** FR025
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Discovery & Ranking component | contract, in-process | No |
| Authorization Engine (candidate vs. family scope) | contract, in-process | No |
| Mangaly DB — `mangaly_discovery` schema | data | No |
| Embedded Postgres full-text search within this schema (ADR-007/ADR-018 — no external Search Service) | infra pattern, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Discovery & Ranking / Authorization coupling | Low | Low (this FR is the base availability slice; correctness of *ranking* is FR026's separate, higher-stakes concern) | Yes — TS060–061 |
| Embedded Postgres FTS at V1 scale | Low (ADR-018 already confirmed V1 volume is far below the ~500K-row/~20K-DAU threshold where this stops being sufficient) | Low at V1; **grows over time** — this is a scaling assumption to monitor, not a defect | Yes for V1 scope; monitoring the ADR-018 threshold is correctly a Step 13 (Monitoring) concern, not a Step 5 test-scenario concern |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none beyond ADR-007/ADR-018's already-resolved scope.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA026 — Relevance-Based Ranking, Not Popularity-Primary
**Traces from:** FR026
**Status:** Ready for Review
**Confidence:** High (upgraded from the FR's own Medium — DEC-V1-002 now fixes the ranking weights and fairness methodology)

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Discovery & Ranking component | contract + data, in-process | No |
| DEC-V1-002 weighted ranking model (30/30/20/20 + diversity re-rank) | data/config | No |
| Compatibility Engine, Trust & Verification (inputs to the 20%/20% weights) | contract, in-process | No |
| DEC-V1-002's monthly automated fairness/parity report | operational process, not a component | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| DEC-V1-002 weight configuration | Low (fixed, versioned, and explicitly structured so popularity is "0% by construction," not merely unweighted) | High if the weights drift or are edited without the fairness-report process re-running (per DEC-V1-002's own stated trigger) | Yes for the structural rule — TS062–063 assert popularity has zero input; **No for the ongoing weight-tuning process** — the monthly parity report is a live-data, production-only process with no equivalent in `05-test-scenarios.md` (it cannot be, since it needs real usage data), so this is correctly a Step 13 (Monitoring) handoff, not a Step 5/6 gap |
| Compatibility/Trust as ranking inputs | Low | Medium (a bug in either upstream component would silently distort ranking rather than crash — the kind of defect that is easy to miss without the parity report specifically watching for it) | Partial — same reasoning as above |

**Worth check**
Yes, proceed. Recommend Step 13 (Monitoring) explicitly wire up DEC-V1-002's monthly parity report as a named, owned operational process before this ranking model reaches production — this file records that the process is specified, not that it is yet running.

**Assumptions** — none beyond DEC-V1-002.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA027 — Discoverability-Tier Exclusion Only, Not Enhanced-Matching
**Traces from:** FR027
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Discovery & Ranking (enforcement point) | contract, in-process | No |
| Profile & Completeness (FR003's tier gate, called from here) | contract, in-process | No |
| DEC-V1-001 discoverability-tier field list | data/config | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Shared tier-gate logic with FR003 | Low | Medium (same divergence risk already named in IA003 — this is the Discovery-side half of that same seam) | Partial — TS064–065 test this side; see IA003's recommendation that both sides call one shared function rather than reimplementing the rule twice |

**Worth check**
Yes, proceed — cross-referenced with IA003; same recommendation applies (one shared tier-gate implementation, not two).

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA028 — Fairness Safeguards and AI Ranking Transparency
**Traces from:** FR028
**Status:** Ready for Review
**Confidence:** Medium — carries forward the FR's own Medium confidence for fairness-testing methodology, though DEC-V1-002 substantially resolves it.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Discovery & Ranking component | contract, in-process | No |
| DEC-V1-002 fairness safeguards and monthly parity report | data/config + operational process | No |
| AI Service — **conditional only** ("if an AI-derived ranking signal is used, label it as inference") | service, conditional/deferred (ADR-009) | No — not cross-module (AI Service is a shared platform service, not a business module); and, per the already-completed FR-level architecture cross-check, this dependency is **not load-bearing**: FR028 succeeds whether or not AI Service exists |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Named de-biasing safeguards (wealth/status, education/profession-as-worth, locality exclusion, filter-bubble, sensitive-attribute inference) | Medium (these are exactly the failure modes a weighted-rule ranking system can reintroduce implicitly through correlated proxy fields, e.g., locality correlating with income) | High if unaddressed (this is the specific bias category the CMU/Tepper finding BR06 already cites was written to prevent) | Yes — TS066–068, plus DEC-V1-002's monthly parity report as an ongoing production check |
| AI Service conditional dependency | Low (ADR-009 correctly keeps this deferred; no FR forces it to exist) | Low at present; would become Medium the moment any AI ranking signal is actually introduced, since inference-labeling then becomes load-bearing rather than conditional | Yes — TS066–068 assert the labeling rule structurally, ready for whenever (if ever) this path activates |

**Worth check**
Yes, proceed. Re-confirms the FR-level architecture cross-check's own finding: this FR's AI reference stays conditional and does not force ADR-009's deferral to end early.

**Assumptions** — carries forward DEC-V1-002's own accepted trade-off (hand-tuned weights over a learned ranker, deliberately).

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA029 — Community-Assisted Discovery Hints
**Traces from:** FR029
**Status:** Ready for Review
**Confidence:** High (upgraded from the FR's own Medium — DEC-V1-003 now fixes the hint mechanics)

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Home Circle component (family submits the hint via a structured form) | contract, in-process | No |
| Discovery & Ranking (surfaces the hint card, capped at 1-in-20 feed items per DEC-V1-003) | contract, in-process | No |
| Mangaly DB — hint data model (per DEC-V1-003, structurally excludes name/photo/contact fields) | data (schema-design guarantee, not policy) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Hint data-model field exclusion | Low if built as a genuine schema-level absence (DEC-V1-003 is explicit: "the field doesn't exist to leak," not merely hidden in the UI) | High if built as a UI-only restriction instead (a hint record with a latent name/photo/contact field, merely not rendered, is one API-response change away from becoming a teaser-profile leak — exactly the non-goal DEC-V1-003 exists to prevent) | Partial — TS069–070 test the FR's behavior; whether Step 7's actual schema design honors "doesn't exist" vs. "exists but hidden" is a concrete thing for the ER Model (Step 7) to get right, and worth flagging explicitly since the distinction is easy to lose between decision and implementation |
| Discovery frequency cap (1-in-20) | Low | Low (a miscalibrated cap is a product-quality issue, not a privacy one) | Yes — TS069–070 |

**Worth check**
Yes, proceed. Flagging for Step 7/9: verify at ER-Model and implementation time that the hint entity genuinely has no name/photo/contact column, not just a UI that doesn't render one — this is the exact place a "resolved" decision could still be under-implemented.

**Assumptions** — none beyond DEC-V1-003.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA030 — Explainable, Non-Score Compatibility Reasons
**Traces from:** FR030
**Status:** Ready for Review
**Confidence:** Medium — carries forward the FR's own Medium confidence (underlying algorithm/weighting methodology remains open per BR07, though this FR fixes required behavior, not the algorithm).

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Compatibility Engine component | contract + data, in-process | No |
| Profile & Completeness (source data) | contract, in-process | No |
| Trust & Verification (fact-labeling source, feeds FR031) | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Compatibility Engine's explanation-generation logic | Medium (generating genuinely "concrete, explainable" reasons from structured profile data is a real content-generation problem, not just a data lookup — the FR's own Confidence note already flags the algorithm as open) | Medium (a defect here produces a generic or unconvincing explanation, a product-quality failure, not a privacy/safety one — bounded severity since FR031 separately guards against false-certainty claims) | Yes for the structural rule (no score, at least one concrete reason) — TS071–072; **Partial for explanation quality**, since "concrete and explainable" is inherently harder to assert with an automated test than a structural absence rule |

**Worth check**
Yes, proceed. The structural commitments (no score, at least one concrete reason) are fully testable and already covered; the open algorithm question is correctly BR07's own carried-forward item, not a new blocker this step introduces.

**Assumptions** — none beyond BR07's own open-algorithm note.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA031 — Fact vs. Inference, Alignment vs. Difference, No Certainty Claims
**Traces from:** FR031
**Status:** Ready for Review
**Confidence:** Medium — same open-algorithm caveat as FR030, plus a new dependency this pass surfaced (see below).

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Compatibility Engine | contract, in-process | No |
| Trust & Verification (fact source for the fact/inference label) | contract, in-process | No |
| A banned-claim content check (certainty-of-character/honesty/success language) applied to generated explanation text before display | contract/data — **not an already-named component in `architecture.md`** | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Fact vs. inference labeling | Low | Medium (mislabeling an algorithmic inference as a verified fact would directly contradict BR08's evidence-not-certification model this module is built around) | Yes — TS073–075 |
| Banned-claim content check | Medium (this FR's own acceptance criteria call for checking "generated explanation text... against a banned-claim list... before display," which is a real content-filtering mechanism `architecture.md`'s 13-component list does not explicitly assign to any owner) | Medium (a missed certainty claim is a product-trust/brand issue, not a data-exposure one, but is exactly the kind of language this module explicitly positions itself against) | Partial — TS073–075 assert the *outcome* (no certainty claims reach display); which component owns the *mechanism* (a template-based generator that structurally cannot phrase certainty claims, vs. a generate-then-filter pipeline) is an open implementation question for Step 7 |

**Worth check**
Yes, proceed, with a named finding for Step 7: assign explicit ownership of the banned-claim check to the Compatibility Engine's own interface (the simplest fix — templated explanation generation, where certainty language is structurally impossible to produce, is lower-risk than a generate-then-filter approach that depends on the filter never missing a phrasing).

**Assumptions** — none beyond BR07's own open-algorithm note.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA032 — Core Capability Fully Functional Without Optional Mechanisms
**Traces from:** FR032
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Compatibility Engine | contract, in-process | No |
| Profile & Completeness (profile/evidence data alone must be sufficient) | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Compatibility Engine's non-dependency on FR033/FR034 | Low | Medium (if the Must-priority core silently depended on the Should/Could optional mechanisms, that would invert BR07's own priority structure and break the product for the large majority of candidates who decline both) | Yes — TS076–077 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA033 — Optional Personality Assessment
**Traces from:** FR033
**Status:** Ready for Review
**Confidence:** Low — carries forward the FR's own Low confidence, and this pass surfaces a genuine gap: the assessment instrument itself is an unselected, externally-sourced dependency structurally identical to the categories `v1-decisions.md`'s "What stays open" table already tracks (verification vendor, DPDP legal sign-off), but it was not included there.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Compatibility Engine (consumes assessment results as one input) | contract, in-process | No |
| An unselected personality-assessment instrument (licensed third-party psychometric tool, or a custom-built non-clinical questionnaire) | service or content asset — **external/unselected, genuinely open** | No (external, not a ForKhatri module) |
| Mangaly DB — assessment-response storage | data | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Instrument selection/licensing | Medium (a licensed psychometric instrument carries IP/licensing cost and possibly usage restrictions; a custom-built questionnaire carries validity/credibility risk if it reads as pseudo-clinical) | Medium (the wrong choice risks either a "good/bad spouse" clinical-diagnosis framing the FR explicitly prohibits, or a costly licensing dependency for a Should-priority, optional feature) | Yes for the structural rules this FR does fix (skippable, no penalty, no clinical language) — TS078–081; **No for instrument selection itself**, since no scenario can test a choice that has not been made |
| Abandoned-assessment handling | Low | Low (a partial assessment used as complete would silently corrupt one candidate's own Compatibility signal, contained to that candidate, not a cross-candidate leak) | Yes — TS078–081 |

**Worth check**
Yes, with a scope note rather than an unqualified "proceed": since this is Should-priority (not Must) and the instrument is genuinely unselected, recommend the Product Manager either (a) add this to `v1-decisions.md`'s "What stays open" table alongside the structurally identical verification-vendor and DPDP items, naming Product/Legal as the owner, or (b) explicitly descope FR033 from the V1 build until an instrument is selected, shipping FR030–FR032's core capability alone. Building FR033's skip/non-blocking mechanics now (which this FR also requires) is safe either way, since that scaffolding is needed regardless of which instrument is eventually chosen.

**Assumptions** — none beyond what's stated above.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA034 — Horoscope: Opt-In, Separated, Non-Scientific
**Traces from:** FR034
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Compatibility Engine (isolated, opt-in-only input path) | contract, in-process | No |
| Mangaly DB — horoscope data field, separately toggled | data | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Opt-in isolation (must never influence a non-opted-in candidate) | Low | Medium (a leak here would silently affect a candidate's Compatibility signal without their consent, though contained to a Could-priority, non-scientific input, not a safety or privacy failure) | Yes — TS082–083 |

**Worth check**
Yes, proceed as specified — lowest-priority, well-bounded item in this BR group.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---
## IA035 — Evidence-and-Provenance Display Per Verification Layer
**Traces from:** FR035
**Status:** Ready for Review
**Confidence:** High (upgraded from the FR's own Medium for the *display model*, which is now fully fixed — vendor selection remains separately open per IA037)

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Trust & Verification component | contract + data, in-process | No |
| Identity & Trust Service (Level-1/2 base trust layer) | service, sync REST/JWT | No |
| Object Storage (evidence artifacts, summaries only per FR040) | service | No |
| Authorization Engine | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Six-layer independent display model | Low (structural, not algorithmic) | Medium (collapsing layers into one badge/score would directly violate BR08's "evidence, not score" foundation) | Yes — TS084–085 |
| Identity & Trust Service as Level-1/2 source | Low | Medium (an outage or data-shape mismatch here would leave the account-authenticity/identity layers unable to render, degrading trust display module-wide) | Yes for functional correctness; availability itself is a Step 8 concern |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA036 — Evidence Language Avoids Truth-Certification
**Traces from:** FR036
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Trust & Verification (copy/content layer) | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Copy governance (no absolute "true/confirmed" language) | Low | Medium (this is a legal/reputational guardrail — Mangaly asserting it "certified" a claim that later proves false is a liability exposure, not just a tone issue) | Yes — TS086–087 |

**Worth check**
Yes, proceed as specified. Recommend the same copy-review discipline named for other content-governance FRs (FR036, FR056, FR085's guidance copy) be consolidated into one Step 9 content-review pass rather than four independent ones.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA037 — Verification Circle: Bounded Confirmation with Anti-Abuse Safeguards
**Traces from:** FR037
**Status:** Ready for Review
**Confidence:** High (upgraded from the FR's own Medium — DEC-V1-004 now fixes the anti-abuse mechanics)

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Trust & Verification component | contract + data, in-process | No |
| Identity & Trust Service (verifier's own Level-2 trust-status check, per DEC-V1-004(a)) | service, sync REST/JWT | No |
| Notification Bridge (neutral-framing outreach to the invited verifier, per DEC-V1-004(e)) | service, async (Broker) | No |
| A rate-limiting mechanism enforcing DEC-V1-004(b)'s 5-invites/7-day window | data/infra — not an explicitly named component in `architecture.md` | No |
| Operations component (BR16 review of a verifier later found fraudulent, per DEC-V1-004(d)) | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Identity & Trust Service Level-2 gate | Low | Medium (accepting a sub-Level-2 verifier's confirmation as evidence would defeat DEC-V1-004's entire anti-abuse premise) | Yes — TS088–090 |
| Rate-limiting mechanism | Medium (this is a genuinely new, small piece of infrastructure — a per-account rolling-window counter — that `architecture.md`'s component list does not explicitly assign; a naive implementation as an in-memory counter would not survive a process restart or scale across instances) | Medium (a broken rate limit re-opens exactly the verifier-role-spam vector DEC-V1-004(b) exists to close, though the residual risk is bounded — DEC-V1-004 itself already accepts this doesn't fully stop a determined, already-Level-2 actor) | Partial — TS088–090 test the eligibility/idempotency rules; the rate-limit counter's own durability (DB-backed vs. in-memory) is an implementation detail worth Step 7 pinning down explicitly, given the "5 invites per rolling 7-day window" requirement needs to survive normal process restarts to mean anything |
| Verifier-invitation content neutrality | Low | Low (a leading/non-neutral framing is a data-quality risk to the evidence itself, not a security issue) | Yes — TS088–090 |

**Worth check**
Yes, proceed. Recommend Step 7 explicitly specify the rate-limit counter as DB-backed (e.g., a row in the `mangaly_trust` schema), not an in-memory cache, given the durability requirement above.

**Assumptions** — verification-vendor selection itself (as distinct from these anti-abuse mechanics) remains genuinely open per `v1-decisions.md`'s "What stays open" table; this item covers only the mechanics DEC-V1-004 resolves.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA038 — Request Mangaly/Admin Verification When No Community Verifier Exists
**Traces from:** FR038
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Trust & Verification component | contract, in-process | No |
| Operations component (BR16 admin verification workflow) | contract, in-process | No |
| DEC-V1-004's 1-hour verifier/evidence review SLA (BharatMatrimony-benchmarked) | data/config, operational commitment | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Operations workflow routing | Low | Medium (if this path is unavailable, Verification Circle (FR037) becomes a hard dependency for obtaining any verification at all, which this FR exists specifically to prevent) | Yes — TS091–092 |
| 1-hour SLA achievability | Medium (this is a real operational commitment, not just a technical one — it requires actual staffing capacity, which DEC-V1-007 already frames as a small on-call rotation, not 24/7 staffing) | Medium (missing the SLA is a service-quality failure, not a safety/privacy one, but is a named, externally-benchmarked commitment now on record) | No — SLA-achievement under real load is inherently a production/operational measure, not something a Step 5 test scenario proves; correctly a Step 13 (Monitoring) concern |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none beyond DEC-V1-004/DEC-V1-007.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA039 — No Trust Score or Reputation Ranking
**Traces from:** FR039
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Trust & Verification, Discovery & Ranking, Profile & Completeness (all must lack any such field, by construction) | contract, in-process (negative-dependency / absence check) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Absence-by-construction of any trust/reputation score | Low if built as an absence from day one | **Critical** if it recurs — this is one of BR08's absolute, named prohibitions and the module's central differentiation from a rating-based product | Yes — TS093–094, and CODING-GUIDE §6 names exactly this test class ("no trust-score field exists anywhere") as a real, valuable schema/contract assertion to write, not skip |

**Worth check**
Yes, proceed. Same absence-testing discipline as IA022; already correctly instrumented.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA040 — Sensitive Verification Documents Not Exposed Publicly
**Traces from:** FR040
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Trust & Verification component | contract, in-process | No |
| Object Storage (raw document storage) | service | No |
| Operations component (the only endpoint permitted to return a raw document, per CODING-GUIDE §7) | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Evidence-panel response contract excluding a document-rendering field | Low — CODING-GUIDE §7 already names this exact control by construction ("the Evidence panel's backend contract has no document-rendering field, by construction... the only endpoint permitted to return a raw verification document is the role-gated Admin Case detail endpoint") | **Critical if it fails** — a raw government-ID or similar sensitive document leaking to any non-admin surface is one of the most severe possible failures for this module | Yes — TS095–096, and this is exactly the kind of contract-shape rule CODING-GUIDE instructs be tested by diffing/asserting the response schema, not just manual review |

**Worth check**
Yes, proceed — this is already a well-specified, structurally-enforced control (an absent field, not a filtered one) rather than a policy relying on discipline. No further mitigation needed at this step.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA041 — Marriageable-Age Verification per Applicable Law
**Traces from:** FR041
**Status:** Ready for Review
**Confidence:** High (upgraded from the FR's own Medium — DEC-V1-005 resolves the threshold and its configuration mechanism)

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Trust & Verification component | contract, in-process | No |
| `config/thresholds.py` — DEC-V1-005's admin-configurable, versioned age-gate setting | data/config | No |
| Identity & Trust Service (base age/identity evidence) | service, sync REST/JWT | No |
| Discovery & Ranking (the eligibility gate this FR feeds) | contract, in-process | No |
| Prohibition of Child Marriage Act, 2006 (external legal fact — 21/18 threshold) | external legal constraint, not a system dependency | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Configured-setting (not hardcoded) implementation | Low if built per DEC-V1-005's explicit instruction | High if hardcoded instead (a 2021 amendment bill proposing to raise the threshold to 21 for women remains under legislative discussion; a hardcoded literal would require a code deployment to stay legally correct, exactly the risk DEC-V1-005 was written to avoid) | Yes — TS097–098 assert the configuration-not-literal requirement directly |
| Inconclusive age evidence | Low | High (age/marriageability is a hard legal gate; defaulting to "assume compliant" on inconclusive evidence would be a genuine legal-compliance failure, not just a UX rough edge) | Yes — TS097–098 |

**Worth check**
Yes, proceed. Recommend Step 13 (Monitoring) track the 2021 Amendment Bill's legislative status as a named watch item, since DEC-V1-005's entire value proposition is that a legislative change becomes an operator config change, not a redeploy — that only holds if someone is actually watching for the change.

**Assumptions** — none beyond DEC-V1-005.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA042 — Send Connection Request
**Traces from:** FR042
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Connection & Sharing component | contract + data, in-process | No |
| Discovery & Ranking (source of the profile being requested) | contract, in-process | No |
| Authorization Engine (on-behalf-of check for family-initiated requests) | contract, in-process (structural chokepoint) | No |
| Audit Bridge (requester identity/capacity, BR15) | service, async (Broker) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Authorization Engine on-behalf-of check | Low | Medium (an unauthorized family member sending a request on a candidate's behalf without proper authorization would be a direct BR04 violation, though bounded since the candidate still separately decides whether to pursue anything, per FR043/FR044) | Yes — TS099–100 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA043 — Recipient Review and Accept/Decline
**Traces from:** FR043
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Connection & Sharing component | contract, in-process | No |
| Compatibility Engine, Trust & Verification (pre-acceptance review information) | contract, in-process | No |
| Authorization Engine | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Pre-acceptance information availability (anti-teaser) | Medium (the same commercial-pressure risk named in IA020 applies here — withholding review information until acceptance is a common dating-app monetization pattern that could be reintroduced by a future feature without deliberate intent) | Medium (directly violates this FR's own "no teaser pattern" success criterion and BR05's broader anti-teaser commitment) | Yes — TS101–102 |
| No default/timeout-forced decision | Low | Low (a pending-forever request is a UX nuisance, not a safety issue) | Yes — TS101–102 |

**Worth check**
Yes, proceed as specified. Cross-referenced with IA020's same monetization-pressure risk category.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA044 — Acceptance Means Willingness to Explore Only
**Traces from:** FR044
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Connection & Sharing component | contract, in-process | No |
| Connection & Sharing / Communication / Home Circle (negative dependency — acceptance must not auto-trigger contact exchange or Home Circle exposure in any of these) | contract, in-process | No |
| API/UI copy layer | contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| No auto-triggered downstream effects | Low | Medium (an accidental auto-trigger would collapse the deliberate, staged progression this module's whole product model depends on — connection, then sharing, then contact exchange, then family involvement, each a separate deliberate act) | Yes — TS103–104 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA045 — Multiple Parallel Connections; No Forced Continued Engagement
**Traces from:** FR045
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Connection & Sharing — `mangaly_connection` schema (no single-current-match constraint) | data | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Non-exclusivity data model | Low | Medium (an accidental exclusivity constraint would reintroduce a "current match" dating-app dynamic this module explicitly rejects) | Yes — TS105–106 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA046 — Per-Category Independent Sharing
**Traces from:** FR046
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Connection & Sharing component | contract + data, in-process | No |
| Authorization Engine (per-category grant resolution) | contract, in-process (structural chokepoint) | No |
| Object Storage (additional photos/video categories) | service | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Per-category independence | Medium (a shared "reveal" flag spanning multiple categories is a plausible implementation shortcut that would violate this FR's core rule) | High (sharing "additional photos" also revealing phone/email would be a direct, serious privacy violation — exactly the failure mode named in the FR's own failure/edge outcome) | Yes — TS107–108 |

**Worth check**
Yes, proceed. Recommend Step 7's ER Model make each shareable category its own row/column with an independent grant timestamp, not a bitmask or combined flag, to make the independence structurally obvious rather than merely tested.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA047 — Clear Sharing Confirmation; No Automatic Disclosure
**Traces from:** FR047
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Connection & Sharing component | contract, in-process | No |
| Notification Bridge (confirmation to both parties) | service, async (Broker) | No |
| Audit Bridge (timestamped, attributable sharing action) | service, async (Broker) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| No-automatic-disclosure invariant | Low | High (an automated or connection-progress-triggered disclosure is a direct violation of this module's deliberate-action-only sharing model, the same failure class as FR059's contact-exchange equivalent) | Yes — TS109–110 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA048 — Family-Contact Category Requires Separate Authorization
**Traces from:** FR048
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Connection & Sharing component | contract, in-process | No |
| Authorization Engine (must resolve **two** independent authorization contexts — candidate's and family member's) | contract, in-process (structural chokepoint) | No |
| Home Circle component (family member's own authorization record) | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Two-context authorization coordination | Medium (this is a genuine integration risk: a naive implementation that checks only the candidate's own sharing authority — since the candidate is the one clicking "share" — would silently skip the family member's separate authorization requirement, since the family member isn't the one performing the UI action) | High (sharing a parent's contact details without that parent's own authorization is a serious, direct privacy violation of exactly the person least likely to notice it happened) | Yes — TS111–112 |

**Worth check**
Yes, proceed, but flag this as one of the higher-integration-risk items in this file precisely because the two-authorization-context requirement is easy to under-implement as a single check. Recommend Step 7 model this explicitly as "resolve `AuthzContext` for both the candidate and the referenced family member before authorizing the share," not as one call that happens to also check a family flag.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---
## IA049 — Enable Private In-Platform Communication
**Traces from:** FR049
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Communication component | contract + data, in-process | No |
| Connection & Sharing (accepted-connection precondition) | contract, in-process | No |
| Authorization Engine | contract, in-process (structural chokepoint) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Accepted-connection precondition | Low | Medium (allowing messaging without an accepted connection would bypass BR09's entire request/accept gate) | Yes — TS113–114 |
| No pre-exchange-of-contact requirement | Low | Low (this is the intended, differentiating behavior, not a risk) | Yes — TS113–114 |

**Worth check**
Yes, proceed. First demoable Communication slice with a clean, well-scoped dependency set.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA050 — No Permanent Chat History; Minimal-Necessary Retention
**Traces from:** FR050
**Status:** Ready for Review
**Confidence:** Low — carries forward the FR's own Low/Medium confidence; the retention window itself is explicitly gated on external DPDP Act legal sign-off per `v1-decisions.md`'s "What stays open" table, unchanged by this pass.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Communication component | contract + data, in-process | No |
| Background retention/lifecycle job scheduler | infra | No |
| DPDP Act legal sign-off on retention window/classification | external, legal | No |
| Audit Bridge (the six named retention-justification purposes) | service, async (Broker) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Retention-window/classification mechanics | High likelihood of remaining unresolved at this step, by design (this is the one item this pass cannot close — it is external-gated, exactly as `v1-decisions.md` already states) | High if launched without legal sign-off (a DPDP Act compliance gap for a communications feature holding family/matrimonial data is a genuine regulatory exposure, the reason this module is isolated at all per ADR-011) | No, by construction — a retention window that has not been legally set cannot be tested against a number that does not exist yet; `05-test-scenarios.md`'s TS115–116 correctly test the *behavioral commitment* (not a permanent, browsable log) rather than a specific duration |
| Background lifecycle job scheduler | Medium (any scheduled-job infrastructure carries a baseline risk of silent failure — see FR054's explicit failure-alerting requirement, which exists precisely because this risk is real) | Medium (see IA054) | Partial — see IA054 |

**Worth check**
Yes, proceed with building the behavioral commitment (minimal-necessity processing, no permanent browsable log) now, exactly as the FR itself specifies — but this file explicitly does **not** clear FR050 for production launch without the named external DPDP sign-off, consistent with `v1-decisions.md`'s own treatment of this exact item. This is not a new blocker introduced here; it is the same named external dependency carried forward.

**Assumptions** — none beyond `v1-decisions.md`'s own framing.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA051 — Access Control: No Routine Human Reading
**Traces from:** FR051
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Communication component | contract, in-process | No |
| Safety Intelligence (the one tightly-controlled access pathway, BR14/BR16) | contract, in-process | No |
| Audit Bridge (every access individually logged with case/purpose reference) | service, async (Broker) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Access restricted to the Safety pathway only | Medium (this is a genuine organizational/operational discipline risk as much as a technical one — an operator with database access could, in principle, query message content directly, bypassing the intended access pattern entirely) | **Critical if it recurs** — routine human reading of private communication is the single behavior this module's entire "not a conventional chat" design commitment (BR11) exists to prevent | Partial — TS117–118 test that the *application-level* access path is case-scoped and logged; whether raw database access is itself restricted (e.g., no engineer/operator role has ad hoc SQL access to the `mangaly_communication` schema in production) is an operational/infrastructure control, not something a functional test scenario can prove |

**Worth check**
Yes, proceed, with an explicit flag for Step 8 (Security & Performance): this FR's guarantee depends on production database access controls (who can run ad hoc queries against `mangaly_communication`) as much as on application code, and that operational control should be named explicitly rather than assumed to follow automatically from the application-layer design.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA052 — Audit Logging of Communication-Related Events
**Traces from:** FR052
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Communication component | contract, in-process | No |
| Internal Domain Event Bus (transactional outbox pattern, `/MODULE-ARCHITECTURE-STANDARD.md` §6) | contract, in-process | No |
| Audit Bridge → Audit Service | service, async (Broker) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Transactional outbox correctness | Low (this is exactly the pattern the event bus was built for, and CODING-GUIDE §4 shows the literal code pattern — the event insert commits atomically with the state change) | High if it fails (a crash between "message processed" and "event published" with no outbox guarantee would produce exactly the silent audit gap BR15 is designed to prevent) | Yes — CODING-GUIDE explicitly names TS119–TS120 as, alongside the Authorization Engine's TS038–043, the other suite worth the deepest test investment in this whole module |

**Worth check**
Yes, proceed. Already correctly identified by this module's own coding guide as one of the two highest-priority test-investment areas; no further mitigation needed at this step.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA053 — Evidence-Retention Exception and Incident Workflow Trigger
**Traces from:** FR053
**Status:** Ready for Review
**Confidence:** Low — carries forward the FR's own Low confidence; scope/duration/access-controls remain gated on the same DPDP legal sign-off as IA050, per `v1-decisions.md`.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Communication component (source data) | contract, in-process | No |
| Safety Intelligence (BR14 trigger) | contract, in-process | No |
| Operations component (BR16 controlled human-investigation workflow) | contract, in-process | No |
| DPDP Act legal sign-off on exception scope/duration | external, legal | No |
| Audit Bridge (every exception invocation individually logged) | service, async (Broker) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Exception scope/duration | Same as IA050 — genuinely gated, not resolved here | High (an over-broad or unbounded exception would be both a DPDP compliance risk and a direct violation of "no exception grants access to unrelated conversations," this FR's own acceptance criterion) | Partial — TS121–123 test the structural rules (individually logged, no cross-conversation leakage); the exact scope/duration ceiling cannot be tested until legally set |
| Routing to Operations on over-aggressive deletion | Low | Medium (a flagged incident that cannot be routed due to prior deletion is explicitly named as a case for an operational alert rather than a silently dropped case — this depends on FR054's alerting mechanism working) | Partial — depends on IA054's own finding |

**Worth check**
Yes, proceed on the same terms as IA050 — build the mechanism now, do not clear for production launch without DPDP sign-off. Not a new blocker; the same named external dependency.

**Assumptions** — none beyond `v1-decisions.md`'s framing.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA054 — Legal-Hold Handling and Lifecycle-Job Failure Behavior
**Traces from:** FR054
**Status:** Ready for Review
**Confidence:** Low — carries forward the FR's own Low confidence; legal-hold mechanics remain gated on the same DPDP sign-off as IA050/IA053.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Communication component | contract + data, in-process | No |
| Background retention/lifecycle job scheduler | infra | No |
| Operations component (failure alerting) | contract, in-process | No |
| DPDP Act legal sign-off on legal-hold mechanics | external, legal | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Legal-hold suspension of normal deletion | Same as IA050/IA053 — genuinely gated | High (data under an active legal hold being deleted by the normal lifecycle job is named in the FR itself as "a serious defect/incident," and correctly so — this could destroy evidence a court or regulator has required preserved) | Partial — TS124–126 test the required safe-failure *behaviors*; the underlying legal-hold trigger/scope is not yet defined to test against |
| Scheduled-job failure alerting | Medium (background job schedulers silently failing is one of the most common real-world operational failure modes in any system with lifecycle jobs — this is not a hypothetical risk category) | High (per this FR's own framing, an undetected failed lifecycle job could result in either indefinite over-retention or premature deletion of held data — both bad outcomes, in opposite directions) | Yes for the alerting *requirement* — TS124–126 assert every failure produces an alert; whether the alerting pipeline itself is reliable under a real infrastructure outage (the exact moment this matters most) is a Step 8 concern |

**Worth check**
Yes, proceed on the same terms as IA050/IA053. The failure-alerting mechanism (not gated on DPDP sign-off) should be built and tested now regardless of the still-open legal-hold scope question, since it protects against a real, independent operational risk.

**Assumptions** — none beyond `v1-decisions.md`'s framing.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA055 — Multiple Concurrent Conversations, No Seriousness Score
**Traces from:** FR055
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Communication — `mangaly_communication` schema (no exclusivity/seriousness model) | data | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Non-exclusivity/non-scoring data model | Low | Medium (same product-invariant class as FR045 — a seriousness score is exactly the kind of feature a future "improve engagement" initiative might propose without realizing it violates this module's core positioning) | Yes — TS127–128 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA056 — Capture-Risk-Reduction Measures with Honest Disclosure
**Traces from:** FR056
**Status:** Ready for Review
**Confidence:** Medium — carries forward the FR's own Medium confidence (specific technical mechanisms are implementation-stage); this pass grounds the disclosure requirement in a real, verified technical limitation rather than a hypothetical one.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Communication component | contract, in-process | No |
| Client-side OS-level capture-prevention APIs (Android `FLAG_SECURE`; no iOS equivalent) | client platform capability, external to this module's own build | No |
| UI copy layer (the "risk-reduction, not guarantee" disclosure) | contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Platform asymmetry between Android and iOS | Confirmed, not merely likely, via live research (2026-09-12): Android's `FLAG_SECURE` is a genuine OS-level block on screenshots/recording/casting for a window; iOS has **no equivalent** — Apple provides only after-the-fact detection (a notification that a screenshot was taken), never prevention, and neither platform's control survives a second physical device photographing the screen or a rooted/jailbroken device | Medium (this is not a defect to fix — it's a real, permanent technical asymmetry this FR's own "risk-reduction, not guarantee" framing already correctly anticipates; the risk is only in *under-disclosing* this to users, e.g., implying iOS gets the same protection Android does) | Yes for the disclosure requirement — TS129–130 assert the "risk-reduction, not guarantee" copy and the absence of an absolute-prevention claim; recommend the copy explicitly avoid implying platform parity, now that the asymmetry is confirmed rather than assumed |

**Worth check**
Yes, proceed — build Android's `FLAG_SECURE` as the concrete Android mechanism and rely on iOS's screenshot-taken notification for after-the-fact awareness only, with the disclosure copy accurately reflecting this asymmetry rather than treating both platforms as equivalent.

**Assumptions** — specific technical mechanisms remain an implementation-stage decision per BR11 DEC-003, as the FR states; this item narrows that decision to the two concretely available platform primitives rather than leaving it fully open.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA057 — Request Contact Information
**Traces from:** FR057
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Communication component (contact-exchange sub-flow) | contract + data, in-process | No |
| Authorization Engine (on-behalf-of check) | contract, in-process | No |
| Audit Bridge (requester identity/timestamp) | service, async (Broker) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Authorization Engine on-behalf-of check | Low | Medium (same class of risk as FR042 — an unauthorized family member requesting contact exchange on a candidate's behalf) | Yes — TS131–132 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA058 — Recipient-Controlled Decision, Internally Attributable
**Traces from:** FR058
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Communication component | contract, in-process | No |
| Authorization Engine (enforces requester ≠ decider even within one Home Circle) | contract, in-process (structural chokepoint) | No |
| Audit Bridge (full requester/decider/timestamp/content chain) | service, async (Broker) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Requester/decider role separation, even within one Home Circle | Medium (a naive implementation could treat "any authorized family member" as interchangeable for both requesting and deciding, since they're all in the same Home Circle — this FR explicitly requires the roles stay distinct even then) | Medium (a requester able to also approve their own request defeats the entire point of having a separate decision authority) | Yes — TS133–134 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA059 — No Automatic Exchange; No Unrequested Channel Disclosure
**Traces from:** FR059
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Communication component — `mangaly_communication` schema | data | No |
| Absence of any scheduled/automated job capable of triggering disclosure | negative-dependency (infra) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| No proxy-signal-triggered disclosure | Low | High (an elapsed-time or message-count-triggered contact reveal is exactly the "automatic escalation" dynamic this module explicitly rejects, and would be a serious, unrequested privacy exposure) | Yes — TS135–136 |
| One channel shared does not reveal another | Low | High (sharing phone number also exposing email is a direct violation of the "only the explicitly requested channel" rule, and a real privacy leak) | Yes — TS135–136 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA060 — Candidate Chooses Timing of Home Circle Involvement
**Traces from:** FR060
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Home Circle component | contract, in-process | No |
| Connection & Sharing (the specific connection being scoped) | contract, in-process | No |
| Authorization Engine | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| No automatic/time-based involvement trigger | Low | Medium (an automatic trigger — e.g., "after 10 messages, notify family" — would be a direct violation of candidate agency, the exact failure BR13 was written to prevent) | Yes — TS137–138 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA061 — Discovery-Level Involvement ≠ Connection-Level Involvement; Private Comm Stays Private
**Traces from:** FR061
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Home Circle component | contract, in-process | No |
| Connection & Sharing component | contract, in-process | No |
| Communication component (must not retroactively expose prior private messages) | contract, in-process | No |
| Authorization Engine | contract, in-process (structural chokepoint) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Discovery-level vs. connection-level involvement separation | Medium (a parent already independently involved in general Discovery is exactly the scenario where an implementer might assume "they're already involved, so why not here too" — a natural but incorrect simplification) | High (automatic visibility into a specific connection, or retroactive exposure of prior private messages once family is involved, are both serious, direct privacy violations of exactly the boundary this module's whole family-involvement model depends on) | Yes — TS139–140 |

**Worth check**
Yes, proceed, but flag alongside IA048 as one of the higher-integration-risk items in this file — the "already involved elsewhere, so treat as involved here" shortcut is a realistic implementation mistake given how naturally it would occur to someone unfamiliar with BR13's deliberate scoping.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA062 — Family-to-Family Introduction as a Distinct Step; No Cross-Side Exposure
**Traces from:** FR062
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Home Circle component (both sides' independent records) | contract + data, in-process | No |
| Connection & Sharing component | contract, in-process | No |
| Authorization Engine (must independently resolve two separate Home Circles' boundaries) | contract, in-process (structural chokepoint) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Cross-side Home Circle isolation | Medium (this is the same two-independent-context risk class already named in IA048 — two separate Home Circles' boundaries must both hold simultaneously, and a shortcut that treats "family introduced" as a single combined event rather than two independently-gated exposures is a realistic implementation error) | High (one side's family gaining automatic access to the other candidate's Home Circle is a serious cross-family privacy violation, and the highest-sensitivity transition point BR13 names) | Yes — TS141–142 |

**Worth check**
Yes, proceed, with the same recommendation as IA048: model this explicitly as two independent authorization resolutions (Family A's exposure, Family B's exposure), never one combined "introduction happened" event that implicitly grants both.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---
## IA063 — User-Initiated Reporting, Always Available, Never Downgraded
**Traces from:** FR063
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Safety Intelligence component | contract + data, in-process | No |
| API layer (reporting entry point reachable from every profile/message/interaction surface) | contract | No |
| Operations component (graduated-response pipeline entry, FR065) | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Universal reachability of the reporting entry point | Medium (this is a completeness risk more than a logic risk — every current and future screen must remember to surface it, which is the kind of thing that is easy to miss on a screen added later) | High (an unreportable surface is a direct safety gap, and BR14's own Constraint explicitly names this) | Yes at the FR-scenario level — TS143–144; **no ongoing regression guard** — the same category of gap as IA012, where a future screen could ship without the reporting entry point and nothing would automatically catch it |
| Non-downgrading based on automated-detection absence | Low | Medium (report triage referencing automated-detection absence as a dismissal criterion would silently deprioritize legitimate reports) | Yes — TS143–144 |

**Worth check**
Yes, proceed. Recommend Step 3/4's screen-inventory discipline (already used to catch FR090–FR102's missing prerequisite screens) be reapplied as an ongoing checklist item: every new screen added after this point must confirm reporting reachability, not just at initial launch.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA064 — Bounded Pattern Detection with AI Inference Labeling
**Traces from:** FR064
**Status:** Ready for Review
**Confidence:** High (upgraded from the FR's own Medium — DEC-V1-006 now fixes the detection-scope boundary)

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Safety Intelligence component | contract + data, in-process | No |
| Communication component (message metadata/text only, per DEC-V1-006's detection-scope boundary) | contract, in-process — **restricted query layer** | No |
| AI Service — **conditional only**, labeled as inference, not load-bearing (ADR-009 deferred) | service, conditional/deferred | No |
| Trust & Verification, Home Circle (negative dependency — Safety must **not** be able to query these, per DEC-V1-006 and CODING-GUIDE §7) | contract, in-process (absence, not a live dependency) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Detection-scope boundary (metadata/text only, 15 named categories) | Low if enforced in the query/repository layer as CODING-GUIDE §7 requires ("the Safety component's repository layer should not have a method capable of reading Home Circle or Trust/Verification tables at all — not a method that happens not to be called, an absence") | High if scope creeps (analyzing photo/video content, or reading Trust/Home Circle data, would violate BR14 DEC-001's operational separation of Safety from Trust, and expand data processing beyond what any named category justifies) | Yes — TS145–147, and CODING-GUIDE §7 already specifies the enforcement mechanism (repository-layer absence) precisely enough to be testable as a static/contract check, not just a runtime behavior |
| AI Service conditional dependency | Low (ADR-009 correctly deferred; this FR does not require it to exist) | Low at present | Yes — TS145–147 assert the inference-labeling rule structurally |

**Worth check**
Yes, proceed. This item is well-specified with a concrete, structural enforcement mechanism already named by CODING-GUIDE rather than left to convention.

**Assumptions** — none beyond DEC-V1-006.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA065 — Graduated Response Pipeline
**Traces from:** FR065
**Status:** Ready for Review
**Confidence:** High (upgraded from the FR's own Low — DEC-V1-006 resolves the severity taxonomy and thresholds this FR's stage-escalation logic needed)

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Safety Intelligence component | contract + data, in-process | No |
| Operations component (human-investigation stage) | contract, in-process | No |
| Notification Bridge (warning/nudge stage, on-call paging for Tier 3/4) | service, async (Broker) | No |
| DEC-V1-006 severity taxonomy and legally-grounded SLAs (24h acknowledge / 2h nudity-impersonation removal / 36h resolve per IT Rules 2021; immediate + external law-enforcement reporting for Tier 4/CSAM per POCSO) | data/config, legal constraint | No |
| An on-call paging mechanism for Tier 3/4 escalation | infra — **not an explicitly named component or provisioned service anywhere in this module's architecture** | No |
| External law-enforcement reporting channel (Tier 4, suspected CSAM) | external, legal | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Five-stage sequencing | Low | Medium (a case failing to reach the correct stage is a process-completeness defect) | Yes — TS148–150 |
| DEC-V1-006 SLA compliance under real staffing | Medium — DEC-V1-007 itself already names this explicitly as a real, unresolved operational risk: "a small on-call rotation, not 24/7 staffing... Tier 3/4's legal deadlines are the one place this small-team model has no slack at all" | **Critical** — missing the 2-hour nudity/impersonation removal ceiling or the CSAM reporting obligation is not merely a service-quality miss, it is a breach of a binding legal ceiling (IT Rules 2021) or a mandatory reporting obligation (POCSO), with real regulatory consequences | No — this is precisely the kind of live-staffing-capacity risk a functional test scenario cannot prove; it requires actual on-call paging infrastructure (e.g., a PagerDuty-class tool) to exist and be load-tested against realistic case-arrival rates, which is a Step 7 (provisioning) and Step 8 (Security & Performance) concern, not a Step 5 test-scenario gap |
| External law-enforcement reporting channel | Medium (this channel does not yet exist as a named, integrated capability anywhere in this module's architecture — it is currently a policy commitment, not a built integration) | Critical (a suspected-CSAM case that cannot actually be reported because no channel/procedure exists would be the single most severe compliance failure this module could have) | No — genuinely unbuilt; flagged explicitly |

**Worth check**
Yes, proceed with building the pipeline mechanics now — but this is the single most consequential finding in this entire file: DEC-V1-006/DEC-V1-007 already flag the Tier 3/4 staffing risk as real and unresolved, and this pass adds that the on-call paging infrastructure and the external law-enforcement reporting channel are not yet built at all. Recommend this be raised explicitly to Step 7/8 as a named, must-resolve-before-launch item, not folded silently into "the pipeline exists" — the pipeline's stage sequencing being correct does not mean its Tier 3/4 exits (paging, legal reporting) are actually reachable in production yet.

**Assumptions** — none beyond DEC-V1-006/DEC-V1-007's own framing.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA066 — Safety and Trust Remain Operationally Distinct
**Traces from:** FR066
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Safety Intelligence component | contract, in-process | No |
| Trust & Verification (negative dependency — Safety triage must not reference verification status) | contract, in-process (absence check) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Non-reference to verification status in triage logic | Low if enforced structurally (same repository-layer-absence pattern as IA064) | High (a verified candidate's safety case being deprioritized due to their verification status would be a serious safety failure disguised as a trust signal, exactly BR14 DEC-001's named risk) | Yes — TS151–152 |

**Worth check**
Yes, proceed as specified. Cross-referenced with IA064's same enforcement pattern.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA067 — Tightly Controlled Safety Access, No Routine Monitoring
**Traces from:** FR067
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Safety Intelligence component | contract, in-process | No |
| Audit Bridge (case-scoped access logging) | service, async (Broker) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Case-scoping of safety-purpose data access | Medium (same operational/infrastructure-control risk as IA051 — the application layer can enforce case-scoping, but production database access controls are what actually prevent a general-monitoring use pattern) | Critical if it recurs (general surveillance use of safety access tooling would be a severe misuse of a system built specifically to avoid exactly that) | Partial — same reasoning as IA051; recommend the same Step 8 database-access-control review cover both FR051 and FR067 together, since they are the same underlying operational control applied to two components |

**Worth check**
Yes, proceed. Cross-referenced with IA051's identical operational-control finding.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA068 — Severity Taxonomy and Escalation Thresholds
**Traces from:** FR068
**Status:** Ready for Review
**Confidence:** High — **the FR's own gap is now closed.** FR068 was written explicitly as an "Open Design Item" naming "Impact Analysis/Security & Performance stage" as the point of resolution; `v1-decisions.md`'s DEC-V1-006 has since resolved it with a taxonomy grounded in binding law (IT Rules 2021, POCSO) rather than an invented number.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| DEC-V1-006 four-tier severity taxonomy and SLAs | data/config, legal constraint | No |
| Safety Intelligence, Operations (the taxonomy's actual consumers, per FR065) | contract, in-process | No |
| IT Rules 2021 (as amended February 2026), POCSO Act (external, binding legal facts) | external legal constraint | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Taxonomy definition itself | Low — resolved, and grounded in verified, cited law rather than an internal guess | N/A — the FR's own failure condition ("production launching without a defined severity taxonomy... flagged as a release blocker") no longer applies | Yes — TS155–156 can now test against DEC-V1-006's concrete tiers where FR068 originally had nothing to test against |
| Operational reachability of the taxonomy's Tier 3/4 exits | Carried forward from IA065 — this is the taxonomy's *definition*, not its *operational readiness*; the paging/reporting-channel gap identified in IA065 is unaffected by this taxonomy now existing | Critical — see IA065 | See IA065 |

**Worth check**
Yes, proceed — and explicitly record that this FR's own named release-gate condition ("a named owner and milestone exist... for severity-taxonomy design... production launch is gated on this taxonomy's existence") is now satisfied by DEC-V1-006. The taxonomy existing is not the same as its Tier 3/4 exits being operationally reachable (see IA065) — both should be tracked, but as two distinct release gates, not one.

**Assumptions** — none beyond DEC-V1-006.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA069 — Record Actor, Capacity, and Authorization for Consequential Actions
**Traces from:** FR069
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Every business-logic component (Profile, Home Circle, Authorization, Discovery, Compatibility, Trust, Connection, Communication, Safety, Lifecycle, Operations — all publish events consumed here) | contract, in-process | No |
| Internal Domain Event Bus (transactional outbox) | contract, in-process | No |
| Audit Bridge → Audit Service | service, async (Broker) | No |
| Audit Log Store — append-only Postgres (ADR-011) | data — external, shared platform infra | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Completeness of "consequential action" coverage across every component | Medium (this is a completeness risk spanning the entire module — a new action added to any component later must remember to publish its audit event, the same "easy to forget on a future addition" risk class as IA012/IA063) | High (an unrecorded consequential action is a direct accountability gap, and this is the FR every other BR's own accountability language depends on) | Yes at present scope — the FR file itself notes "every action listed as consequential in BR02–BR14, BR16, BR18–BR20 has a corresponding audit-record schema"; **no ongoing regression guard** for future additions, same gap class as IA012/IA063 |

**Worth check**
Yes, proceed. Recommend a single, explicit Step 7/9 checklist item — "every new mutating endpoint must publish a corresponding domain event" — enforced by code review or a lint rule (consistent with this module's existing preference for lint-enforced rather than conventional discipline, per `/MODULE-ARCHITECTURE-STANDARD.md` §3's import-boundary precedent), rather than relying on each future engineer remembering BR15 unprompted.

**Assumptions** — storage substrate may be shared platform infrastructure (Audit Log Store, per ADR-011); this FR governs what must be logged, not where it physically lives.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA070 — Record Revocation, Change, and Dispute
**Traces from:** FR070
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Audit Bridge → Audit Service | service, async (Broker) | No |
| Audit Log Store — append-only Postgres (ADR-011 — architecturally guarantees non-destructive writes) | data | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Append-only guarantee | Low (this is an architecture-level property of the Audit Log Store itself, per ADR-011, not something each individual FR has to separately re-implement) | High if violated (an overwritten original record would defeat the entire accountability model retroactively, potentially concealing exactly the dispute it was meant to preserve evidence of) | Yes — TS159–160 |

**Worth check**
Yes, proceed. The append-only guarantee is correctly an architecture-level property (ADR-011), not a per-FR risk to independently re-litigate.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA071 — Audit Trail Not Exposed as Surveillance; Least-Privilege Admin Query
**Traces from:** FR071
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Audit Bridge | contract, in-process | No |
| Authorization Engine (denies ordinary end-users) | contract, in-process (structural chokepoint) | No |
| Operations component (case-scoped admin query) | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| End-user denial of another's audit trail | Low (Authorization Engine's deny-by-default baseline) | High (any end-user gaining visibility into another member's full audit trail would itself become the surveillance capability BR15 explicitly prohibits) | Yes — TS161–163 |
| Admin query case-scoping and self-logging | Low | Medium (an admin browsing unrelated records unlogged would be an internal-misuse risk, the same category of concern as IA051/IA067's operational-access-control finding) | Partial — same operational-control caveat as IA051/IA067 applies here as well |

**Worth check**
Yes, proceed. Cross-referenced with IA051/IA067's shared operational database-access-control finding — recommend Step 8 treat all three together as one review item.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA072 — Verification-Related Admin Workflow
**Traces from:** FR072
**Status:** Ready for Review
**Confidence:** High (upgraded from the FR's own Medium — DEC-V1-007 fixes the workflow states and DEC-V1-004 fixes the 1-hour SLA benchmark)

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Operations component | contract + data, in-process | No |
| Trust & Verification (outcome feeds back here) | contract, in-process | No |
| DEC-V1-007 workflow states (intake→triage→assignment→investigation→decision→audit→appeal) | data/config, process | No |
| Admin & Governance Console (federated view, ADR-012) | service, sync REST | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Workflow-outcome feedback to Trust & Verification | Low | Medium (a decision that doesn't actually reach BR08's evidence display would leave a verification request in permanent limbo from the candidate's perspective) | Yes — TS164–165 |
| Incomplete-evidence handling (mark incomplete, request more) | Low | Low (this is a workflow-quality safeguard against premature approve/deny, already correctly specified) | Yes — TS164–165 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none beyond DEC-V1-007.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA073 — False-Relationship Investigation Workflow
**Traces from:** FR073
**Status:** Ready for Review
**Confidence:** High (upgraded from the FR's own Medium — DEC-V1-007's workflow and DEC-V1-006's Tier 2 24h/36h SLA now apply)

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Operations component | contract, in-process | No |
| Home Circle (withheld access pending determination — same mechanism as FR011) | contract, in-process | No |
| DEC-V1-006/DEC-V1-007 (Tier 2 dispute SLA and workflow states) | data/config | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Withheld-access mechanism | Low | Medium (same residual-access-latency concern already named at IA010/IA011) | Partial — same caveat as IA010/IA011 |
| Pending/open case handling (no forced premature outcome) | Low | Low | Yes — TS166–167 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none beyond DEC-V1-006/DEC-V1-007.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA074 — Abuse/Fraud Investigation with Restriction, Block, and Escalation
**Traces from:** FR074
**Status:** Ready for Review
**Confidence:** High (upgraded from the FR's own Medium — DEC-V1-006/DEC-V1-007 now apply)

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Operations component | contract, in-process | No |
| Safety Intelligence (BR14 pipeline source) | contract, in-process | No |
| Audit Bridge (every restriction/block/escalation action linked to a case) | service, async (Broker) | No |
| DEC-V1-006/DEC-V1-007 (severity/staffing model) | data/config | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Evidence review and recorded outcome | Low | Medium | Yes — TS168–169 |
| Restriction/block/escalation action attribution | Low | High (an unattributed enforcement action would be both an accountability gap and, per FR076, a "never disclosed publicly" rule that depends on this attribution existing in the first place) | Yes — TS168–169 |
| Tier 3/4 operational reachability | Same finding as IA065 — carried forward, not re-litigated here | Critical (see IA065) | See IA065 |

**Worth check**
Yes, proceed. Same Tier 3/4 operational-readiness caveat as IA065/IA068 applies to this FR's own escalation path.

**Assumptions** — none beyond DEC-V1-006/DEC-V1-007.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA075 — Appeals Workflow
**Traces from:** FR075
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Operations component | contract, in-process | No |
| Audit Bridge (appeal outcome recorded) | service, async (Broker) | No |
| DEC-V1-007's "different operator where staffing allows" independence rule | data/config, process — **named accepted downside, not a resolved guarantee** | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Appeal-path completeness (every restriction/block type has one) | Low | Medium (a restriction type with no appeal path is a real due-process gap) | Yes — TS170–171 |
| Reviewer independence from the original decision | **High** — DEC-V1-007 itself explicitly names this as a genuine accepted downside of the small on-call staffing model ("a different operator than the original decision where staffing allows" — the "where staffing allows" qualifier is doing real, honest work here) | Medium (an appeal reviewed by the same operator who made the original decision is a weaker due-process guarantee than a genuinely independent review, though the decision itself remains subject to the same evidence standard either way) | No — a staffing-capacity constraint cannot be tested away by a functional scenario; this is a resourcing decision for whoever staffs Mangaly operations, correctly named as an accepted trade-off rather than hidden |

**Worth check**
Yes, proceed. Recommend this be surfaced explicitly to whoever owns Mangaly's operational staffing plan (not just engineering) as a known, accepted limitation at current team size — not something Step 6/7/8 can engineer around.

**Assumptions** — none beyond DEC-V1-007's own stated acceptance of this trade-off.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA076 — Admin Actions Audited, Least-Privilege, No Public Disclosure
**Traces from:** FR076
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Operations component | contract, in-process | No |
| Audit Bridge (100% of admin actions logged) | service, async (Broker) | No |
| Authorization Engine (operator role/scope enforcement, no "all access" role) | contract, in-process (structural chokepoint) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| 100% admin-action audit coverage | Low (same completeness-risk class as IA069, applied specifically to admin actions) | High (an unaudited admin action defeats FR076's own accountability guarantee for the module's most powerful role class) | Yes — TS172–173 |
| No "all access" admin role | Medium (a broad "superadmin" role is a common operational shortcut under real staffing pressure — exactly the kind of thing a small on-call team might reach for) | High (directly violates this FR's own explicit rule and undermines the case-scoping every other Operations-related item in this file depends on) | Yes at a point-in-time — TS172–173; ongoing enforcement depends on role definitions never drifting toward a broad-access shortcut, which is an operational-discipline risk, not a one-time technical one |

**Worth check**
Yes, proceed as specified. Recommend the "no all-access admin role" rule be enforced as a structural constraint (e.g., no role definition in the authorization data model is permitted to reference "all cases") rather than a policy convention, consistent with this module's broader preference for structural over conventional enforcement.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---
## IA077 — Scoped, Revocable, Attributable Agent Access
**Traces from:** FR077
**Status:** Ready for Review
**Confidence:** Low — carries forward the FR's own Low confidence; this is a deliberately deferred capability (BR17), not a build gap.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| No active component — BR17 is explicitly not built at V1 | — (future-state only) | No |
| Identity & Trust Service (future Agent identity type, if/when built) | service, future | No |
| Authorization Engine (future per-family/per-candidate scoping model) | contract, in-process, future | No |
| Audit Bridge (future per-Agent attribution) | service, future | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Premature or partial build | Low (BR17/DEC-001's sequencing gate is explicit and already respected by every other FR's design — nothing in the current 102-FR set requires or references an Agent capability) | High if violated (building any part of this ahead of BR17's own gate would be a direct violation of a deliberate, explicit product sequencing decision) | Yes — TS174–175 test the *required behavior for when this is eventually built*, correctly scoped as forward-looking rather than testing something that exists now |

**Worth check**
Yes — correct as specified not to build this now. This FR's only real job at this step is to confirm nothing else in the 102-FR set has silently started depending on an Agent capability that doesn't exist, and nothing has.

**Assumptions** — this FR describes required behavior for if/when this deferred capability is built, per BR17 DEC-001; not scheduled for the current build cycle.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA078 — Agents Cannot Gatekeep Exposure; Deferred Until Core Product Proven
**Traces from:** FR078
**Status:** Ready for Review
**Confidence:** Low — same deferred-capability caveat as IA077.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Discovery & Ranking (negative dependency — must have zero Agent-representation input, enforced by absence of any Agent-aware code path, per `architecture.md` §2.3) | contract, in-process (absence check) | No |
| DEC-V1-002's ranking weight formula (30/30/20/20 — no Agent-status term exists in it) | data/config | No |
| Product go/no-go gate referencing core-product maturity | process, not a system dependency | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Discovery's structural absence of Agent-aware logic | Low at present (DEC-V1-002's weighted formula, as specified, genuinely has no such term to begin with — this is verified by inspection of the formula itself, not merely asserted) | High if a future feature introduces one without recognizing the conflict (e.g., a future "professional-assisted" badge that inadvertently affects ranking would violate this FR even if BR17 itself remains formally unbuilt) | Yes — TS176–177, and this is the same absence-testing discipline as IA022/IA039; recommend Step 10 include this specific check in the same regression suite that guards FR022's no-popularity-signal rule, since both are "verify a specific input never entered the ranking formula" checks |

**Worth check**
Yes, correct as specified. Recommend explicitly cross-referencing DEC-V1-002's weight list whenever any future ranking-adjacent feature is proposed, precisely because this FR's guarantee depends on that list never silently growing a new term.

**Assumptions** — none beyond BR17 DEC-001.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA079 — Mark Matrimonial Search Concluded
**Traces from:** FR079
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Lifecycle & Outcomes component | contract + data, in-process | No |
| Profile & Completeness (lifecycle-state field) | contract, in-process | No |
| Authorization Engine (on-behalf-of check for Home Circle-initiated conclusion) | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Deliberate-action-only requirement (never inferred from reduced activity) | Medium (an "inactive user cleanup" or engagement-scoring feature is a plausible future addition that could easily conflate "hasn't logged in" with "search concluded" if this invariant isn't actively remembered) | Medium (an incorrectly auto-concluded profile would wrongly remove a still-searching candidate from Discovery, a real product-trust failure, though self-correctable via FR081's reactivation) | Yes — TS178–179 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA080 — Concluded Profile Excluded from Discovery/Compatibility Without Data Loss
**Traces from:** FR080
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Lifecycle & Outcomes component | contract, in-process | No |
| Discovery & Ranking, Compatibility Engine (must exclude concluded profiles) | contract, in-process | No |
| Audit Bridge / historical records (must remain intact) | data | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Exclusion from Discovery/Compatibility | Low | Medium (a concluded profile still surfacing to others is confusing and undermines trust in the "concluded" state's meaning) | Yes — TS180–181 |
| Historical data preservation | Low | High (deleting or invalidating historical connection/accountability records would directly violate BR15's accountability guarantees, retroactively, for a profile that is otherwise perfectly legitimate) | Yes — TS180–181 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA081 — Reactivate Concluded Profile; Lifecycle State Audited
**Traces from:** FR081
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Lifecycle & Outcomes component | contract, in-process | No |
| Trust & Verification (freshness-window check, avoids redundant re-verification) | contract, in-process | No |
| Audit Bridge (every transition recorded) | service, async (Broker) | No |
| Message Broker → Dashboard (`mangaly.activity_summary` event) | contract, async, **cross-module (MOD05 Dashboard)** | **Yes — declared edge, `/ARCHITECTURE.md` Dependency resolution table** |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Freshness-window re-verification skip | Low | Low (worst case is a minor UX friction if the skip logic is too conservative, or a small trust-freshness gap if too permissive — bounded, since BR08's freshness rules still apply, not bypassed) | Yes — TS182–183 |
| Lifecycle-transition audit completeness | Low | Medium (an unaudited reactivation would break the "fully reconstructable lifecycle history" this FR explicitly requires) | Yes — TS182–183 |
| Dashboard activity-summary event (privacy-filtered) | Low (the pattern itself is `/ARCHITECTURE.md`'s own resolved, deliberately async, one-way, privacy-filtered edge — chosen specifically because a synchronous pull would open an implicit read-path into Mangaly's sensitive store) | Medium if the event payload scope drifts (any future change that widens what "activity summary" includes must be re-checked against `/ARCHITECTURE.md`'s explicit "never raw match/profile data" constraint, since Dashboard is outside Mangaly's isolated container and trust boundary) | No test scenario in `05-test-scenarios.md` currently names this event payload's exact contents; recommend Step 7 define the event schema explicitly and Step 8 verify it against the privacy-filter constraint, since this is the one place this FR's data crosses Mangaly's isolation boundary at all |

**Worth check**
Yes, proceed. This FR is the natural, and currently only, publisher of the one active cross-module edge originating from Mangaly's data — flagging the event-schema definition explicitly for Step 7 rather than letting it be implied.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA082 — Invite/Capture Success Story Only With Full Consent
**Traces from:** FR082
**Status:** Ready for Review
**Confidence:** Medium — carries forward the FR's own Medium confidence (Could-priority, no source-document citation).

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Lifecycle & Outcomes component | contract + data, in-process | No |
| Lifecycle's own BR18 conclusion state (precondition) | contract, in-process | No |
| Notification Bridge (invitation to share) | service, async (Broker) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Per-party independent, explicit consent | Low | Medium (capturing a story based on one party's consent alone, or inferring consent from the BR18 conclusion action itself, would be a real, avoidable privacy violation for a Could-priority, non-essential feature) | Yes — TS184–185 |

**Worth check**
Yes, with a scope note: this is Could-priority and has no source-document citation, per the FR's own Confidence line — reasonable to build after the Must-priority FR set (FR001–FR088's core) is complete and stable, not in parallel with it.

**Assumptions** — none beyond BR19 DEC-001.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA083 — Declining Has Zero Effect on Account Status; Consent Audited and Revocable
**Traces from:** FR083
**Status:** Ready for Review
**Confidence:** Medium — same BR19 caveat as IA082.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Lifecycle & Outcomes component | contract, in-process | No |
| Every other capability (negative dependency — declining must have zero effect anywhere) | contract, in-process (absence check) | No |
| Audit Bridge (consent grant/modify/revoke events) | service, async (Broker) | No |
| A takedown mechanism for a revoked, already-published story | infra — **destination/publication channel unspecified per BR19 Assumptions** | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Zero-effect-on-account guarantee | Low | Medium (same completeness-risk class as IA012/IA063/IA069 — any future feature that inadvertently treats "declined a success story" as a signal would violate this) | Yes — TS186–187 |
| Revocation-triggered takedown | Medium (this depends on a publication channel — in-app, website, social — that BR19's own Assumptions explicitly defer as "a later marketing/distribution decision"; a takedown mechanism cannot be fully specified until that channel is chosen) | Medium (a revoked story still visible on an external channel because no takedown integration exists there would be a real, if contained, consent violation) | Partial — TS186–187 test the in-app/internal revocation event; takedown from an external, as-yet-undetermined channel cannot be tested until that channel exists |

**Worth check**
Yes, with the same scope note as IA082 — recommend the takedown mechanism be finalized only once the publication channel decision (out of this FR's scope) is actually made, rather than building a takedown integration against an undetermined destination.

**Assumptions** — none beyond BR19 Assumptions.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA084 — Published Story Excludes Undisclosed Sensitive Content
**Traces from:** FR084
**Status:** Ready for Review
**Confidence:** Medium — same BR19 caveat.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Lifecycle & Outcomes component | contract, in-process | No |
| Home Circle (exclude membership details) | contract, in-process | No |
| Communication (exclude private conversation content) | contract, in-process | No |
| Trust & Verification (exclude contact details beyond explicit approval) | contract, in-process | No |
| A manual pre-publication review process | process — human-in-the-loop, not a system component | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Cross-component data-minimization at publication time | Medium (this FR pulls from three separate sensitive sources — Home Circle, Communication, Trust — into one published artifact, which is inherently a higher-surface-area operation than most single-component FRs) | High (a published story leaking Home Circle membership or private communication content would be a serious privacy violation, compounded by being public rather than contained to authorized viewers) | Partial — TS188–189 assert a pre-publication review checklist exists; since this is explicitly a manual review process rather than an automated technical control, its reliability depends on human process discipline, not code correctness alone |

**Worth check**
Yes, with a recommendation: given the cross-component sensitivity and the reliance on a manual review step, recommend Step 7/8 also specify an automated pre-publication scan (e.g., a check that the published payload contains no fields sourced from the excluded categories) as a second, structural layer beneath the manual review — the same defense-in-depth principle this module already applies to authorization (RLS beneath application logic) applied here to publication review.

**Assumptions** — publication channel is a later marketing/distribution decision outside this FR, per BR19 Assumptions.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA085 — Optional Safety Guidance Before In-Person Introduction
**Traces from:** FR085
**Status:** Ready for Review
**Confidence:** High (upgraded from the FR's own Medium — DEC-V1-008 now drafts the actual guidance copy)

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Lifecycle & Outcomes component (primary presenter) | contract, in-process | No |
| Safety Intelligence (co-owner per `architecture.md`'s traceability table) | contract, in-process | No |
| DEC-V1-008's five-point guidance copy | data/config, content | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Optional, non-blocking presentation | Low | Medium (presenting this as a mandatory gate would directly violate BR20's explicit "optional" constraint, and add friction with no corresponding safety benefit since it can't be enforced anyway) | Yes — TS190–191 |
| Guidance content itself | Low — resolved by DEC-V1-008, grounded in named industry-standard content (Tinder/Bumble safety-tip baselines already researched at UX30) | Low — the substance is standard, non-controversial safety advice; DEC-V1-008 itself flags only the *surrounding disclaimer/liability-framing language* as needing a final legal pass before production, not this list's content | Yes — TS190–191; the narrower legal-framing check DEC-V1-008 names is a Step 8/pre-launch item, not a Step 5 test-scenario gap |

**Worth check**
Yes, proceed — DEC-V1-008 already closes the FR's own confidence gap; only the narrow disclaimer-language legal pass DEC-V1-008 itself names remains, and that is correctly scoped as a pre-launch check, not a blocker to building this now.

**Assumptions** — guidance is informational content, not a platform-mediated live-safety feature, per BR20 Assumptions.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA086 — Opt-In "Meeting Occurred" Note
**Traces from:** FR086
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Lifecycle & Outcomes component | contract + data, in-process | No |
| Connection & Sharing (note attaches to a specific connection) | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Manual-only trigger (never inferred) | Medium (same behavioral-inference-creep risk as IA079 — a future "engagement insight" feature inferring a meeting from message-pattern changes is a plausible, well-intentioned but rule-violating addition) | Medium (an incorrectly inferred meeting note is a data-integrity/trust issue, contained to that one connection, not a safety issue on its own) | Yes — TS192–193 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA087 — Report a Concern From a Real-World Meeting
**Traces from:** FR087
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Safety Intelligence (identical BR14 pipeline as FR063) | contract, in-process | No |
| Lifecycle & Outcomes (contextual link to the meeting) | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Identical-pipeline guarantee (no separate, weaker post-meeting path) | Medium (a separate "post-meeting feedback" flow is an intuitive but wrong design instinct — feedback and safety-incident reporting read as similar UI patterns, making an accidental divergence plausible) | High (a post-meeting incident is, per BR20's own Worth check, the highest-physical-risk moment in the entire journey; routing it through a weaker path would be a severe safety regression at exactly the wrong point) | Yes — TS194–195 |

**Worth check**
Yes, proceed as specified — correctly identified in the FR itself as addressing the journey's highest physical-risk moment, with no weaker alternative path built.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA088 — No Relationship-Progress Tracking; Platform Role Ends at Introduction
**Traces from:** FR088
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Lifecycle & Outcomes — `mangaly_lifecycle` schema (no relationship-status field beyond BR18 state + FR086 note) | data (absence check) | No |
| Every component (negative dependency — no scheduling/chaperone/coordination feature anywhere) | contract, in-process (absence check) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Absence of relationship-progress/scheduling features | Medium (this is exactly the kind of "helpful" feature a well-meaning future roadmap item — e.g., "let couples plan their next meeting in-app" — could introduce without recognizing it crosses this explicit non-goal) | Medium (scope creep into relationship-management territory would be a product-positioning failure and a direct violation of BR20's explicit non-goal and DEC-001's narrow scoping decision, though not itself a safety/privacy incident) | Yes at present — TS196–197; **same ongoing-regression-guard gap as IA012/IA022/IA039/IA078/IA083** — a future feature proposal is the realistic path by which this boundary erodes, and nothing currently re-checks it automatically |

**Worth check**
Yes, proceed as specified. Recommend this FR's boundary be added to whatever product-roadmap review checklist future feature proposals go through, given how directly a "helpful" feature could violate it without deliberate intent.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA089 — Person-Level Language Preference on Profile
**Traces from:** FR089
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Profile & Completeness component (owns the preference field) | contract + data, in-process | No |
| Shared i18n/translated-content library and locale-aware response shaping (ADR-010, Common Platform) | service/library — shared platform, not a business module | No |
| Discovery, Compatibility, Trust & Verification (downstream consumers reading this preference for rendering) | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Person-level (not session/device-level) persistence | Low | Medium (storing this only at the session/device level would silently break the FR's own requirement that every downstream surface read one consistent preference) | Yes — TS014–015 |
| Non-blocking of profile creation | Low | Low (correctly specified as a non-gating field; a defect here would be a minor onboarding-friction issue) | Yes — TS014–015 |
| ADR-010 shared i18n library availability | Low (platform-level, already resolved) | Medium (an outage or gap in the shared library would affect every module's localization, not just Mangaly's — a platform-wide, not Mangaly-specific, risk) | Yes for Mangaly's own field-storage behavior; the shared library's own reliability is a platform-level concern outside this file's scope |

**Worth check**
Yes, proceed as specified.

**Assumptions** — the rendering/translation mechanics that consume this preference are Common Platform infrastructure (ADR-010); this FR only fixes that the preference exists as person-level profile data.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---
## IA090 — Splash / Launch and Session Bootstrap
> **2026-09-14 correction:** the dependency is now Identity Bridge → `POST /internal/v1/sessions/resolve` (service key, ≤30 s cache, fail closed `503`), not a JWT check; fallback is the ForKhatri entrance, not Mangaly Login. See docs/ParentApp/07-tech-reqs.md TR14–TR16.
**Traces from:** FR090
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Identity Bridge → Identity & Trust Service (session/token validity check) | service, sync REST/JWT | No |
| Client-side routing logic (onboarding vs. login vs. main shell) | client capability, no backend component | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Session-validation latency/failure handling | Medium (network failure or an expired token on launch is a routine, not edge-case, condition for this module's named tier-2/3 connectivity audience) | Low (correctly bounded by the FR's own fallback-to-Login behavior; worst case is an extra login step, not data exposure) | Yes — TS198–200 |

**Worth check**
Yes, proceed as specified. Thin, low-risk, correctly identified by Step 3 as a necessary scaffolding screen.

**Assumptions** — session/token mechanics are Common Platform identity infrastructure; this FR only fixes Mangaly's own routing behavior on launch.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA091 — First-Run Onboarding
**Traces from:** FR091
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Client-side content only (no backend business logic) | client capability | No |
| Help & Support (FR100 — same content must be independently findable later) | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Full skippability, no repeat display | Low | Low (a UX annoyance at worst, not a data or safety risk) | Yes — TS201–202 |
| Content consistency with Help & Support | Low | Low (a divergence between onboarding copy and Help content would be a minor content-maintenance issue) | Yes — TS201–202 |

**Worth check**
Yes, proceed as specified. Lowest-risk item in the prerequisite-screen set.

**Assumptions** — content is illustrative/explanatory only, not a data-collection step.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA092 — Account Sign-Up (Candidate or Family-Member Entry Point)
> **2026-09-14 correction:** delivered by the ForKhatri platform identity, not by this module. See docs/ParentApp/07-tech-reqs.md TR12–TR16. Module screens for this flow redirect to the ForKhatri entrance. The "interim account-system duplication" risk above is the migration now planned in PA-DEC-08/TR23: active `mangaly_identity.account` rows move with ids, identifiers and Argon2id hashes; pending rows are not imported; the stale pending row is retired if that identifier later signs up through ForKhatri.
**Traces from:** FR092
**Status:** Ready for Review
**Confidence:** Medium — the FR's own Intent already names a genuine architectural interim: Mangaly is building its own minimal account-entry surface because no Common Platform Identity module exists yet, ahead of Mangaly in build order.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Identity Bridge (interim, Mangaly-built minimal account/credential surface) | contract + data, in-process | No |
| FR095 (identifier verification, OTP) | contract, in-process | No |
| External SMS/OTP Provider | service (third-party, external) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Interim account-system duplication | **High** likelihood this needs reconciliation later — the FR's own text states this plainly: "it should be reconciled with (or delegated to) a Common Platform Identity module's own sign-up screen once one exists" | Medium-High if migration is mishandled — migrating live candidate credentials/sessions from a Mangaly-built interim system into a future platform-wide Identity & Trust Service is a genuinely high-risk class of operation (live credential/session migration), even though it is not needed today | Yes for FR092's own behavior as specified — TS203–205; **No for the future migration itself**, since that migration doesn't exist yet to test — this is a forward-looking architectural debt item, not a current defect |
| Duplicate-identifier/weak-credential handling | Low | Medium (a duplicate account or weak credential accepted would be a basic account-security gap) | Yes — TS203–205 |

**Worth check**
Yes, proceed — there is no viable alternative given Mangaly's build-order position (ADR-016/017), and the FR itself already discloses this honestly rather than silently. Recommend recording this explicitly as a named technical-debt item for whenever a platform-wide Identity module is eventually built, so the future migration is planned rather than discovered.

**Assumptions** — the underlying credential-storage/session infrastructure is intended to become Common Platform once that module exists; this FR only fixes Mangaly's required entry-point behavior in the interim.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA093 — Login (Returning User)
> **2026-09-14 correction:** delivered by the ForKhatri platform identity, not by this module. See docs/ParentApp/07-tech-reqs.md TR12–TR16. Module screens for this flow redirect to the ForKhatri entrance. Anti-enumeration and rate limiting move to the platform (TR13, TR19, TR20).
**Traces from:** FR093
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Identity Bridge (interim account system, same as FR092) | contract, in-process | No |
| Anti-enumeration response-shape rule (CODING-GUIDE §7 — identical response body/status for "wrong password" vs. "no such account") | contract — already-decided defect-prevention control | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Anti-enumeration control | Low — CODING-GUIDE §7 already specifies this precisely enough to test as a byte-for-byte response diff, not a subjective copy review | Medium (an enumerable login endpoint lets an attacker confirm which phone numbers/emails have Mangaly accounts, a real privacy leak for a matrimonial platform where account existence itself can be sensitive information) | Yes — CODING-GUIDE explicitly names TS207/TS211 as the test that verifies this by diffing responses, not just reading error strings |
| Rate-limiting on repeated failures | Low | Medium (an unlimited retry surface enables credential-stuffing/brute-force attempts) | Yes — TS206–208 |

**Worth check**
Yes, proceed. The anti-enumeration control is already specified precisely enough (CODING-GUIDE §7) to be a testable, structural rule rather than a convention.

**Assumptions** — none beyond FR092's interim-system note.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA094 — Forgot / Reset Password
> **2026-09-14 correction:** delivered by the ForKhatri platform identity, not by this module. See docs/ParentApp/07-tech-reqs.md TR12–TR16. Module screens for this flow redirect to the ForKhatri entrance. The platform contract currently offers code sign-in instead of a reset endpoint.
**Traces from:** FR094
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Identity Bridge | contract, in-process | No |
| External SMS/OTP Provider (FR095's mechanism) | service (third-party, external) | No |
| Anti-enumeration rule (same CODING-GUIDE §7 control as IA093, applied to reset requests) | contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Token expiry/single-use enforcement | Low | Medium (a reusable or long-lived reset token is a real account-takeover vector) | Yes — TS209–211 |
| Anti-enumeration on reset requests | Low | Medium (same reasoning as IA093 — reset-request enumeration leaks account existence) | Yes — CODING-GUIDE §7 names TS211 explicitly for this |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none beyond FR092's interim-system note.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA095 — Phone/Email OTP Verification
> **2026-09-14 correction:** delivered by the ForKhatri platform identity, not by this module. See docs/ParentApp/07-tech-reqs.md TR12–TR16, TR19. Module screens for this flow redirect to the ForKhatri entrance. The SMS/DLT delivery-reliability finding above still applies, now to the platform's delivery provider (placeholders until chosen).
**Traces from:** FR095
**Status:** Ready for Review
**Confidence:** Medium — the underlying SMS/OTP delivery channel is a real-world reliability dependency, grounded by this pass's own research rather than assumed reliable.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Identity Bridge | contract, in-process | No |
| External SMS/OTP Provider (India-specific DLT-registered route) | service (third-party, external) | No |
| Trust & Verification (successful verification feeds BR08's account-authenticity layer) | contract, in-process | No |
| Notification & Communication Service (delivery infrastructure, if OTP dispatch routes through it rather than directly via Identity & Trust) | service, Common Platform | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| SMS/OTP delivery reliability | **Confirmed real, not hypothetical**, via live research (2026-09-12): even a fully DLT-compliant, correctly-routed transactional SMS still has a documented ~5–8% single-channel non-delivery rate in India due to carrier filtering, network conditions, and device settings; the single largest failure cause when it does happen is wrong-route selection (promotional vs. transactional/OTP route) or a DLT template mismatch, both configuration errors rather than random failures | Medium (a failed OTP blocks sign-up/password-reset/identifier-change entirely for the affected user — this is a real, measurable conversion/access risk for exactly the tier-2/3-connectivity audience this module names as a design constraint, not a rare edge case) | Partial — TS212–213 test the code-validity/expiry/resend-rate-limit behavior; they do not test against actual India-specific SMS delivery failure modes, since that requires either a real DLT-registered sender account or a Step 8/production-monitoring measurement, not a Step 5 functional scenario |
| Resend rate-limiting (abuse prevention) | Low | Medium (an unlimited resend path enables SMS-bombing abuse against a phone number, a real, named category of harassment) | Yes — TS212–213 |

**Worth check**
Yes, proceed — but recommend two concrete, research-grounded mitigations for Step 7/9 rather than assuming SMS alone is sufficient: (1) register on the correct transactional/OTP DLT route specifically (not promotional), since route misconfiguration is the single most common cause of delivery failure, not a rare fluke; (2) budget for an email or WhatsApp fallback channel for the ~5–8% of users whose SMS never arrives, consistent with current India-market practice for reaching >99% effective delivery — this is a real, named reliability gap this pass surfaced, not a hypothetical one.

**Assumptions** — underlying SMS/email delivery infrastructure is Common Platform, per modules.md's notification-delivery Shared Concern; the reliability finding above applies regardless of which platform component owns the actual provider integration.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA096 — Permission Priming: Location and Notifications
**Traces from:** FR096
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Discovery & Ranking (locality ranking input) | contract, in-process | No |
| Notification Bridge | service, async (Broker) | No |
| Client-side OS permission APIs (Android/iOS location and notification permission models) | client platform capability, external | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Graceful degradation on decline | Low | Medium (a declined permission accidentally blocking a capability, rather than just degrading it, would violate this FR's own core rule and BR06's own locality-ranking design, which already treats location as an enhancement, not a requirement) | Yes — TS214–215 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA097 — Main Navigation Shell and Home Circle Context Switcher
**Traces from:** FR097
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| API layer / client-side navigation shell | contract, no independent backend component | No |
| Authorization Engine (per-context authorization display) | contract, in-process | No |
| Home Circle component (list of contexts a user participates in) | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Active-context visibility | Low | Medium (an ambiguous active context could lead a user to take an action believing they're acting as themselves when actually acting on behalf of another candidate, or vice versa — a real, if self-correcting, confusion risk) | Yes — TS216–217 |
| Cross-context data leakage on switch | Medium (client-side state management bugs — e.g., a form's in-progress draft persisting across a context switch — are a common class of mobile-app defect, not specific to this module but genuinely realistic given the multi-context design) | Medium (in-progress data from one candidate-context leaking into another would be a privacy violation between two Home Circles this user happens to participate in, similar in nature to IA048/IA062's cross-side concerns but client-side rather than server-side) | Yes — TS216–217 explicitly test this; recommend continued attention here in Step 9/10 given the client-side (not server-authorized) nature of this specific risk |

**Worth check**
Yes, proceed as specified, with the cross-context data-leakage risk flagged as worth extra implementation care given its client-side nature (harder to catch via server-side authorization tests alone).

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA098 — Notification Inbox
**Traces from:** FR098
**Status:** Ready for Review
**Confidence:** Medium — this pass surfaces a genuine architecture gap: `architecture.md` §2.1 documents the Notification Bridge as "thin" and schema-less, but this FR requires persistent, per-user inbox storage.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Notification Bridge | contract, in-process | No |
| Internal Domain Event Bus (every component's events feed this) | contract, in-process | No |
| Persistent inbox storage — **schema ownership not yet resolved** | data — **architecture gap, see below** | No |
| Notification & Communication Service (delivery infrastructure, distinct from the in-app record) | service, Common Platform | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Inbox persistence schema ownership | **Confirmed gap, not hypothetical:** `architecture.md` §2.1 explicitly states thin bridges "own no schema of their own," yet FR098 requires "a persistent, in-app inbox the user can review at any time" — these two statements are in direct tension, and nothing in the current architecture document resolves which component's schema actually stores inbox entries | Medium (this is an implementation-planning gap, not a security/privacy one — the eventual answer is straightforward, e.g., the Notification Bridge becomes a genuine tenth schema-owning component, or inbox entries live in a new thin data store outside the 13-component model — but it needs an explicit decision, not a default assumption) | Yes for the FR's own required behavior — TS218–219; **No test can cover a schema-ownership decision that hasn't been made yet** |
| Event-type completeness (every named category produces an entry) | Medium (same completeness-risk class as IA069 — a future event type added to any component must remember to also produce an inbox entry) | Medium (a missing inbox entry means a user misses learning about a relevant event, a real but self-limiting product-quality gap) | Yes at present scope — TS218–219; same ongoing-regression caveat as other completeness items in this file |

**Worth check**
Yes, proceed with building the inbox behavior as specified — but explicitly flag the schema-ownership gap for Step 7's ER Model to resolve as a named decision (does the Notification Bridge become schema-owning, or does inbox persistence live elsewhere), not something Step 7 should have to independently rediscover from this FR's text alone.

**Assumptions** — underlying push-delivery infrastructure is Common Platform; this FR governs the in-app inbox record, not the delivery pipe — but that record needs an owner, which is the gap named above.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA099 — Account & App Settings
**Traces from:** FR099
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Profile & Completeness (language preference, FR089) | contract, in-process | No |
| Home Circle component (management entry point) | contract, in-process | No |
| Authorization Engine (pause/resume, FR024) | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Settings/profile-editing duplication or contradiction | Low | Low (a duplicated or contradicted setting is a UX/data-consistency issue, not a privacy or safety one) | Yes — TS220–222 |

**Worth check**
Yes, proceed as specified. Thin aggregator screen with no independent business logic.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA100 — Help & Support
**Traces from:** FR100
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Operations component (BR16 ticket path) | contract, in-process | No |
| Safety Intelligence (misrouting a safety-flagged ticket must route into FR063's pipeline, not a slower queue) | contract, in-process | No |
| FR091's onboarding content (must be independently findable here) | content reuse | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Correct routing of safety-flagged submissions | Medium (a general "help ticket" intake form is a plausible place for a user to describe a safety concern without realizing a dedicated, faster path exists — the routing logic must actively detect and redirect this, not assume users always pick the correct entry point) | **High** — given DEC-V1-006's legally-binding SLAs (24h acknowledge, 2h for nudity/impersonation, immediate for Tier 4), a safety-urgent issue stuck in a slower general-support queue could directly cause a legal-SLA miss, not just a poor user experience | Yes — TS223–224 explicitly test this exact routing requirement |

**Worth check**
Yes, proceed as specified — but given the legal-SLA stakes now established by DEC-V1-006, recommend this routing check receive the same test-investment priority CODING-GUIDE reserves for the Authorization Engine and event bus, since a routing miss here has the same downstream consequence as a Tier 3/4 case being handled late.

**Assumptions** — none.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA101 — Logout and Delete Account
> **2026-09-14 correction:** logout is ForKhatri sign-out (TR13, TR16), propagating to Mangaly within 30 seconds (TR15). Account deletion begins at the ForKhatri identity layer; the cross-module deletion contract is not yet specified.
**Traces from:** FR101
**Status:** Ready for Review
**Confidence:** Medium — carries forward the FR's own Medium confidence; the deletion-vs-retention boundary is gated on the same DPDP sign-off as FR050/FR053/FR054.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Identity Bridge (session termination) | contract, in-process | No |
| Communication, Trust & Verification, Home Circle data (subject to the retention rules FR050/FR053/FR054 govern) | data | No |
| Audit Bridge (the deletion event itself must be audited, per BR15) | service, async (Broker) | No |
| DPDP Act legal sign-off (same external dependency as FR050/FR053/FR054) | external, legal | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Logout (session-only) | Low | Low | Yes — TS225–227 |
| Deletion vs. retention disclosure | Same as IA050/IA053/IA054 — genuinely gated | High (an account deletion that silently retains more — or less — than legally required, or that fails to disclose an active legal hold before the user confirms, is the same category of DPDP compliance risk already named at IA050) | Partial — TS225–227 test the required disclosure *behavior*; the underlying retention schedule it discloses cannot be tested until DPDP sign-off resolves it, same as IA050 |

**Worth check**
Yes, proceed on the same terms as IA050/IA053/IA054 — build the disclosure/exception-handling behavior now; do not clear for production launch without the same named DPDP sign-off. Not a new blocker.

**Assumptions** — none beyond FR053/FR054's.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## IA102 — Offline / Network-Loss Resilience
**Traces from:** FR102
**Status:** Ready for Review
**Confidence:** Medium — this pass surfaces a genuine cross-cutting architecture requirement not currently named anywhere in `architecture.md`'s component list.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Client-side local queue/store (offline-first mutation queue) | client capability — **new technical capability, not in any existing component's traceability** | No |
| API layer — **every client-queueable mutation endpoint must be idempotent** | contract — **cross-cutting requirement, no single component named as owner** | No |
| Communication, Profile, Connection & Sharing (the components most likely to receive queued writes — messages, profile edits, connection actions) | contract, in-process | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Client-side offline queue | Medium (building a reliable offline-write queue on a mobile client is a genuinely nontrivial engineering problem — this is a well-known, real difficulty class, not a simple feature) | Medium (a lost or duplicated queued write is a data-integrity annoyance for the affected user, bounded in blast radius to that user's own actions) | Yes — TS228–229 test the required user-facing behavior; they do not, and cannot, prove the underlying client engineering is correct at scale — that is a Step 9/10 implementation-and-test concern |
| Mutation-endpoint idempotency | **High** likelihood of being missed if not named explicitly — without an idempotency key or equivalent mechanism, a retried "send message" or "save profile edit" request after a connectivity drop can create a **duplicate** record rather than safely no-op, which is a distinct and easy-to-overlook failure mode from the "message lost" case this FR's acceptance criteria emphasize | Medium (a duplicated message or duplicated profile-edit record is a data-quality defect, not a privacy/safety one, but could be confusing or embarrassing in a matrimonial-communication context — e.g., a message appearing to have been sent twice) | **No** — nothing in `05-test-scenarios.md`'s TS228–229 as scoped tests for duplicate-write prevention specifically; they test that a write eventually succeeds or clearly fails, not that a *retried* write is safely idempotent |

**Worth check**
Yes, proceed with building the offline-resilience behavior — but this is a genuine, concrete finding for Step 7: every mutation endpoint the client can plausibly queue and retry (message send, profile save, connection request/response, sharing grants) needs an explicit idempotency mechanism (e.g., a client-generated idempotency key persisted with the queued write), named as a cross-cutting API contract requirement rather than left implicit in FR102's client-side framing alone.

**Assumptions** — none beyond what's stated above.

**Decisions (append-only)** — none.

**Review history** — (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12

---

## Definition of Done — self-check

- **Coverage check has no blank rows.** Confirmed — 102/102 FRs have a produced IA item (IA001–IA102), listed in the Coverage check table above.
- **Every dependency has a risk assessment row.** Confirmed across all 102 items — each Dependency-identification table's rows are matched by a corresponding Risk-assessment row addressing likelihood, severity, and test-coverage adequacy; no dependency was left unassessed.
- **Cross-module dependency check is Pass.** Confirmed — the two edges `modules.md`/`/ARCHITECTURE.md` declare for Mangaly (MOD03→MOD06 optional `benefit_eligible` events; MOD05→MOD03 one-way `mangaly.activity_summary` events) were checked against every item; no undeclared cross-module dependency was found anywhere in the 102-FR set. The one active cross-module edge (IA081, publishing to Dashboard) is a declared, already-resolved pattern, not a new one. The declared-but-currently-unexercised MOD03→MOD06 edge is recorded as a non-blocking observation in the Set-level quality gate, not treated as a defect in either this FR set or `modules.md`'s own decomposition.
- **Every item's worth check has an explicit answer, not left implicit.** Confirmed — every one of IA001–IA102 states "Yes, proceed," "Yes, with [named scope note/recommendation]," or an equivalent explicit answer; none is left to be inferred from the risk table alone. No item returned "No" outright — the closest cases (FR033's unselected personality-assessment instrument, IA075's staffing-dependent appeal-review independence, IA065's Tier 3/4 operational-readiness gap) are each answered "Yes, with a named condition/recommendation," consistent with this step's own instruction to raise a genuine "not like this" finding back rather than silently proceeding, while not manufacturing a blocker where a scoped condition is the honest and sufficient answer.
- **No open blockers.** Confirmed — every genuinely external- or staffing-gated dependency (DPDP retention/legal-hold sign-off; verification-vendor selection; the newly-surfaced personality-assessment-instrument gap; BR17's deliberate deferral; DEC-V1-007's small-team staffing trade-off) is named explicitly, with an owner and a next step, in its own item and in this file's Open blockers section — none is left as a silent assumption.

Three items in particular carry findings this pass surfaced beyond what any prior Sealed file already stated, each with a concrete next owner rather than left open-ended: IA065/IA068/IA074 (Tier 3/4 on-call paging infrastructure and the external law-enforcement CSAM-reporting channel are not yet built, distinct from DEC-V1-006's taxonomy now being resolved — owner: Step 7/8), IA098 (Notification Bridge inbox-persistence schema ownership is undecided — owner: Step 7 ER Model), and IA102 (mutation-endpoint idempotency is a named cross-cutting requirement, not yet assigned — owner: Step 7). These are recorded as the most load-bearing handoffs from this file to Step 7.

## Approval

Architect / Director — [x] Approved — krishna kategaru (autonomous), 2026-09-12
