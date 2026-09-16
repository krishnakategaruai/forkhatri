---
step: 06-impact-analysis
module: MOD01
status: Sealed
approver: Product Manager
items: "55 | approved: 55 | blockers: 0"
updated: 2026-09-14
---

# 06 — Impact & Plan Analysis — MOD01 Vyapar

## Revision history

| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-14 | Initial version. Looped over all 55 Sealed FRs from `02-functional-requirements.md` one at a time: re-read each FR against its parent BR in `01-business-requirements.md`, `modules/modules.md`'s declared MOD01 dependency map, `/ARCHITECTURE.md`'s Container diagram, Dependency-resolution table, and Shared-concern-resolution table (ADR-004/005/006/007/008/010/011/013/018/019/020/021), and `/MODULE-ARCHITECTURE-STANDARD.md`'s generic patterns (schema-per-component, authorization chokepoint, idempotent mutation endpoints, shared rate-limiting), before writing each item's dependency table, risk table, and worth check. No MOD01-specific `architecture.md` exists yet (Step 7a builds it); this file therefore reasons from `/ARCHITECTURE.md`'s Module→Container row for Vyapar (Core Platform monolith, `vyapar` schema in Core Platform DB — no dedicated container) rather than a component-level breakdown, and flags for Step 7 the same way `/MODULE-ARCHITECTURE-STANDARD.md` §1 expects. Live web research performed for the two dependencies this module has not exercised before and whose SLA-shaped acceptance criteria (FR07, FR51) depend on real-world behaviour rather than assumption: (a) India SMS/OTP delivery reliability — DLT-registered transactional routes reach roughly 98% delivery, but real deployments still see template-mismatch/route-mismatch silent failures and one cited real-world case lost ~8% of OTP sends to a mix of channel and DLT rejection issues; this feeds CCR04 and directly grounds FR07's own 5-attempt/15-minute-lockout design as a necessary accommodation, not over-engineering. (b) Payment-gateway webhook idempotency/signature/ordering pitfalls (Razorpay/Cashfree-class India gateways) — duplicate webhook delivery on network retry is a normal, expected gateway behaviour, not an edge case, and out-of-order events (a refund webhook arriving before its payment webhook) are a documented real occurrence; this feeds CCR03 and directly confirms FR51's own idempotency-key and signed-webhook-verification acceptance criteria as necessary, matching real precedent rather than a hypothetical caveat. No FR was found requiring a dependency `/ARCHITECTURE.md` doesn't already resolve. One genuine reconciliation point, not a gap, is recorded explicitly rather than smoothed over: `modules/modules.md`'s original MOD01 "Depends on: MOD06 (Payment Services)" line is superseded for V1 by the Sealed BR17/FR51 decision to collect payment directly through an external gateway, with MOD06 downgraded to a future, optional, async benefit-trigger-event edge — already reconciled in `/ARCHITECTURE.md`'s own Dependency-resolution table row ("MOD01 Vyapar → MOD06 Payment Services — Optional, benefit-trigger events"), so this is not an undeclared cross-module dependency, it is a documented, sealed supersession. | Impact Analysis (Step 6) — autonomous execution per product owner direction 2026-09-14. |

## Coverage check

| Parent FR | Impact items produced | Covered |
|---|---|---|
| FR01 | IA001 | Yes |
| FR02 | IA002 | Yes |
| FR03 | IA003 | Yes |
| FR04 | IA004 | Yes |
| FR05 | IA005 | Yes |
| FR06 | IA006 | Yes |
| FR07 | IA007 | Yes |
| FR08 | IA008 | Yes |
| FR09 | IA009 | Yes |
| FR10 | IA010 | Yes |
| FR11 | IA011 | Yes |
| FR12 | IA012 | Yes |
| FR13 | IA013 | Yes |
| FR14 | IA014 | Yes |
| FR15 | IA015 | Yes |
| FR16 | IA016 | Yes |
| FR17 | IA017 | Yes |
| FR18 | IA018 | Yes |
| FR19 | IA019 | Yes |
| FR20 | IA020 | Yes |
| FR21 | IA021 | Yes |
| FR22 | IA022 | Yes |
| FR23 | IA023 | Yes |
| FR24 | IA024 | Yes |
| FR25 | IA025 | Yes |
| FR26 | IA026 | Yes |
| FR27 | IA027 | Yes |
| FR28 | IA028 | Yes |
| FR29 | IA029 | Yes |
| FR30 | IA030 | Yes |
| FR31 | IA031 | Yes |
| FR32 | IA032 | Yes |
| FR33 | IA033 | Yes |
| FR34 | IA034 | Yes |
| FR35 | IA035 | Yes |
| FR36 | IA036 | Yes |
| FR37 | IA037 | Yes |
| FR38 | IA038 | Yes |
| FR39 | IA039 | Yes |
| FR40 | IA040 | Yes |
| FR41 | IA041 | Yes |
| FR42 | IA042 | Yes |
| FR43 | IA043 | Yes |
| FR44 | IA044 | Yes |
| FR45 | IA045 | Yes |
| FR46 | IA046 | Yes |
| FR47 | IA047 | Yes |
| FR48 | IA048 | Yes |
| FR49 | IA049 | Yes |
| FR50 | IA050 | Yes |
| FR51 | IA051 | Yes |
| FR52 | IA052 | Yes |
| FR53 | IA053 | Yes |
| FR54 | IA054 | Yes |
| FR55 | IA055 | Yes |

## Set-level quality gate

| Check | Result |
|---|---|
| Every FR analyzed | Pass — 55/55, IA001–IA055. |
| Cross-module dependencies checked against modules.md | Pass — `modules/modules.md`'s MOD01 row declares exactly three module-level edges: MOD01→MOD06 (payment collection, superseded for V1 self-containment by Sealed BR17/FR51, downgraded to optional async benefit-trigger events per `/ARCHITECTURE.md`'s Dependency-resolution table), MOD01→MOD04 (optional referral, FR23/FR52f), and MOD05→MOD01 (read-only summary, FR52e). All three checked against every FR below. |
| No undeclared cross-module dependency found | Pass — no FR in this set calls, queries, or assumes write access to Milavn, Mangaly, Dashboard, Counsel, Payment Services, or Loans & Finance beyond these three declared, already-resolved edges. Identity & Trust, Search, Notification, Audit, and Object Storage are platform shared services, not sibling business modules, per `/ARCHITECTURE.md`'s "Platform containers with no module owner" list. |
| Declared MOD01→MOD04 edge exercised by this FR set | Pass — FR23 ("Refer to Counsel" action) is the sole trigger; FR52(f) is the contract it uses. No other FR touches this edge. |
| Declared MOD05←MOD01 edge exercised by this FR set | Pass — FR52(e) is the contract; FR02 and FR05 are the two FRs whose visibility rules that contract must actually honor (hidden contact channels, private seeking status). |
| Declared MOD01→MOD06 edge (superseded for V1) | Pass, with the supersession recorded above — no FR in this set emits or depends on a MOD06 synchronous call; FR51 is a direct external-gateway integration, not a MOD06 call, exactly as BR17 decided. |
| Architecture-level gaps surfaced this pass | One, non-blocking: MOD01 has no `architecture.md` yet (no dedicated component/schema breakdown inside the `vyapar` schema), unlike MOD03's precedent. Flagged for Step 7/7a to produce one before Tech Reqs finalizes component-level ownership (see IA050, IA052, and the closing note below). |

## Open blockers

None. `modules/modules.md`'s superseded MOD01→MOD06 dependency line above is a documented, sealed reconciliation, not an open blocker; the missing `architecture.md` is a forward pointer to Step 7/7a's own Definition of Done, not a Step 6 blocker.

## Cross-cutting risk register

Platform-wide risks that recur across many FRs are analyzed once here and referenced by ID (CCR0x) from each item's risk table below, rather than being re-explained 55 times.

| ID | Risk | Affects (representative FRs) | Severity | Mitigation (already in the Sealed FR/BR set or Architecture) |
|---|---|---|---|---|
| CCR01 | Identity & Trust Service outage or unreachable session-resolve call | Nearly every FR (every authenticated action) | Critical — every module's auth path depends on it (ADR-004, ADR-019); it fails closed (`503`) by design | FR50's 15-minute read-only degradation window for members already holding a valid platform session; ADR-019's fail-closed `503` (never a local auth fallback); platform's own 99.9% availability target (`/ARCHITECTURE.md` Non-functional baselines) exceeds Core Platform's 99.5% |
| CCR02 | Search Service degradation — embedded Postgres full-text search's relevance/index-lag ceiling (ADR-007, superseded in part by ADR-018) | FR15, FR17, FR18, FR19, FR20, FR48 | Medium — a quality/latency cap, not an outage; becomes a real re-evaluation trigger only past ADR-018's row-count/latency threshold | FR15's cached-category-browse fallback with a "search temporarily unavailable" notice; FR48's 5-minute taxonomy-to-search refresh SLA; ADR-018's capability/volume-based re-evaluation trigger (not yet reached at Vyapar's V1 scale) |
| CCR03 | Payment-gateway outage, duplicate webhook delivery, or out-of-order webhook events (grounded 2026-09-14 web research: duplicate delivery on gateway-side retry is normal Razorpay/Cashfree-class behaviour, not an edge case; a refund webhook arriving before its payment webhook is a documented real occurrence) | FR30, FR31, FR33, FR35, FR51, FR54 | High — blocks every V1 monetization path at once; a mishandled duplicate/out-of-order webhook can double-credit or wrongly refund | FR51's idempotency key per order, signed-webhook verification before processing, 24-hour Awaiting-Payment retry window, and status-poll fallback exist specifically because this failure mode is real and expected, not hypothetical |
| CCR04 | SMS/OTP delivery reliability for the platform's shared OTP-sending capability FR07 reuses (grounded 2026-09-14 web research: DLT-registered transactional routes reach ~98% delivery, but template-mismatch and route-mismatch cause silent, undetected failures at the telecom scrubbing layer; one cited real deployment lost ~8% of sends) | FR07 (and, transitively, FR03's Draft→Active-Unverified gate and every downstream verification FR that assumes a listing eventually leaves Draft) | Medium — a delivery failure blocks one listing's onboarding, not the platform, but at scale it silently suppresses V1 supply | FR07's 5-attempt/30-second-resend/15-minute-lockout design already accommodates real non-delivery rather than assuming a single OTP always arrives; template/route registration is an operational task for Step 9, flagged here so it isn't silently assumed solved |
| CCR05 | Notification Service delivery failure, retry-induced duplication, or notification fatigue | FR21, FR23 (no-reply marker), FR40, FR41, FR45 | Medium — a missed notification is a lost-engagement risk, not a data-integrity risk | ADR-006's async, eventual-delivery model with an outbox pattern; FR21's explicit "retried up to 3 times then dropped, never duplicated" rule and daily/digest caps |
| CCR06 | Audit Service outage or dropped audit event | Every state-changing FR (all 55, per the shared "Audit event" definition) — highest-consequence for FR03, FR08, FR10, FR29, FR39, FR40, FR41, FR49 | High for dispute/compliance-bearing FRs; Medium elsewhere | ADR-011's at-least-once delivery requirement (a silently dropped audit event is treated as a compliance gap, not a performance optimization); FR52's dead-letter visibility in the FR49 operator queue |
| CCR07 | Object Storage/CDN outage, or a retention/masking control failing silently (PAN masked-display and 30-day deletion is a compliance control, not a cosmetic one) | FR08, FR09, FR11, FR37, FR47 | Medium-High — an outage blocks verification evidence upload/review; a masking/deletion failure is a real compliance exposure, not just an availability one | FR08's explicit encrypted-storage/masked-display/30-day-auto-delete acceptance criteria; FR52(d)'s MOD01-access-policy scoping of all stored media |
| CCR08 | MOD05 Dashboard read-contract privacy leak — the summary contract exposing a private contact channel or private seeking-status field it should never see | FR02, FR05, FR15, FR36, FR52(e) | Critical if it occurs — this is exactly the harm BR12's privacy invariants exist to prevent, and it would be a cross-module trust breach, not a Vyapar-internal bug | FR52(e)'s explicit "public fields only, no contact, no private intent, no write path" contract; FR02/FR05's independent, testable visibility settings that the contract must honor rather than reinterpret |
| CCR09 | MOD04 Counsel referral scope creep — the referral action drifting into carrying appointment or payment state it was never meant to exchange | FR23, FR52(f) | Low — a single explicit, member-consented action with an intentionally minimal payload (member id, problem summary, consent flag) | FR52(f)'s explicit "no appointment or payment state exchanged" contract boundary; FR23's requirement that the referral "changes nothing else in the thread" |
| CCR10 | Taxonomy/category drift across Search, Admin Console, and member-authored free text (unmapped capability labels, category renames/merges) | FR01, FR04, FR15, FR19, FR48 | Medium — bad taxonomy directly degrades the module's core discovery promise (BR05) | FR04's unmapped-label-still-searchable-by-text fallback; FR48's versioned taxonomy management with alias-preserving merges and a 5-minute search-refresh SLA |
| CCR11 | i18n/translation completeness gap — a system string, taxonomy label, or legal/commercial disclosure missing its Hindi/Telugu translation at release | FR42, FR43, FR44, FR53, FR54 | Medium — English fallback is graceful for ordinary UI text, but a legal notice or commercial disclosure shown in the wrong language undermines FR53/FR54's own compliance intent | FR42's "100% of MOD01 system strings before release, fallback to English + logged" acceptance criterion; ADR-010's shared i18n data model applied consistently |
| CCR12 | Manual verification-operator bottleneck — a solo-founder-stage human process, not an architecture gap, that can silently grow past its own SLA | FR08, FR09, FR10, FR47 | Medium — the 3-business-day target is stated as an internal operating target, not a contractual SLA, so a backlog degrades trust slowly and quietly rather than failing loudly | FR47's overdue-highlighting in the operator queue; BR03's own explicit acknowledgment that this is a deliberately lightweight V1 policy, not an automated one |
| CCR13 | Direct-gateway-to-future-MOD06 migration/adapter risk — the day a payment-consolidation decision is made, the adapter swap must not become a rewrite | FR51 (and everything monetization-adjacent built on it: FR30, FR31, FR33, FR35, FR54) | Medium, deliberately deferred — a technical-debt risk, not a launch risk | FR51's explicit "gateway adapter isolated behind one internal payment interface" acceptance criterion is the named swap seam; BR17 DEC-002/FR51 DEC-001 already record this as an accepted, future, non-blocking option |
| CCR14 | DPDP/BR18 proportionate-compliance-posture risk — the deliberate choice to defer formal legal sign-off to a scaling milestone rather than gate V1 on it | FR37, FR53, FR54, and indirectly every FR handling personal data | Medium — an explicit, Product-Manager-approved risk acceptance appropriate to an early-stage product, not a silently-missed gap | FR53's versioned-notice-with-recorded-acceptance mechanism; BR18's own explicit statement that a formal counsel engagement is a future scaling milestone |

---

## IA001 — Create and edit a BusinessProfile
**Traces from:** FR01
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type (service/data/contract/module) | Cross-module? |
|---|---|---|
| Core Platform DB — `vyapar` schema, BusinessProfile table | data | No |
| Identity & Trust Service (owner `member_id`) | service, in-process → sync REST (CCR01) | No |
| Platform-shared taxonomy reference list | data/config (CCR10) | No |
| FR03 lifecycle gate (Draft state) | in-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| `vyapar` schema write | Low | Medium — a migration mistake here blocks every downstream Business capability | Yes — FR01's own acceptance criteria cover mandatory-field validation and duplicate name+locality rejection directly |
| Identity & Trust (CCR01) | Low | See CCR01 | Partial — Step 5 test scenarios cover Vyapar's own save logic, not Identity & Trust's own availability behaviour (a Step 8 concern) |
| Taxonomy list (CCR10) | Low | See CCR10 | Yes — the unmapped-label fallback is itself an explicit acceptance criterion of the sibling FR04 |

**Worth check**
Yes, proceed. This is the first demoable slice in the build-order note; every dependency is already resolved and the "three-question minimum" design (DEC-001) deliberately keeps this FR's own blast radius small.

**Assumptions:** Taxonomy is platform-shared and editable via FR48, as stated in FR01's own Assumptions.

**Decisions (append-only):** None.

**Review history:** None yet.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA002 — Business contact and visibility controls
**Traces from:** FR02
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB — `vyapar` schema, BusinessProfile contact/visibility fields | data | No |
| Search Service index (must drop a listing within 5 seconds of "discoverable" toggling off) | service (CCR02) | No |
| MOD05 Dashboard read-side summary contract | contract, async/cached read (CCR08) | Yes (MOD05) |
| Enquiry thread rendering (FR22–FR24) | in-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Search index propagation | Medium — a 5-second SLA against an eventually-consistent index is tight | Medium — a stale cached search result briefly showing a hidden channel is exactly what FR02's own failure/edge outcome forbids | Partial — the 5-second bound is stated as an acceptance criterion but its enforcement is a Step 8 performance concern, not yet test-automated |
| MOD05 contract (CCR08) | Low | Critical if breached — see CCR08 | Yes — FR02's own acceptance criteria explicitly test that hidden channels never appear in the MOD05 summary |
| Enquiry thread contact reveal (FR24) | Low | Medium — the two FRs must agree on disclosure-level semantics or a channel could leak in one surface and not another | Yes — FR24 traces the same "After accepted enquiry" level defined here |

**Worth check**
Yes, proceed. Owner-controlled disclosure is the mechanism that makes every later contact-sharing FR (FR22, FR24) safe; without it those FRs would have no consented boundary to enforce.

**Assumptions:** Default is Public discovery, contact After accepted enquiry, per FR02's own stated default.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA003 — Listing lifecycle (submit, activate, suspend, archive)
**Traces from:** FR03
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR07 OTP contact-verification gate | in-module contract | No |
| Automated safety check (prohibited-content wordlist, spam pattern) | in-module component, config-driven | No |
| FR40 moderation queue (routing on safety-check failure) | in-module contract | No |
| Search Service index removal on Suspend/Archive | service (CCR02) | No |
| Audit Service (every transition) | service (CCR06) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| FR07 gate | Low | High — if the OTP gate can be bypassed, the "listing contact verification" baseline BR03 depends on is void for every listing that slips through | Yes — FR03's acceptance criteria explicitly require server-side enforcement of illegal transitions |
| Automated safety check | Medium — wordlists/spam patterns need ongoing tuning | Medium — a false negative lets unsafe content go Active-Unverified immediately; a false positive routes legitimate listings to manual review, straining CCR12 | Partial — content/spam-pattern quality is inherently a tuning exercise, not fully verifiable by a fixed test suite |
| Search removal on suspend (CCR02) | Low | Medium | Yes — the 5-second removal bound is a direct acceptance criterion |
| Audit (CCR06) | Low | High for this FR specifically — a lost audit event on suspension removes the accountability trail BR13/BR16 depend on | See CCR06 |

**Worth check**
Yes, proceed. This FR is the structural backbone every other listing-facing FR assumes exists (state, label, audit); deferring it would leave FR01/FR04/FR08 with nowhere to attach their own state transitions.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA004 — Create and edit a ProfessionalListingProfile with progressive setup
**Traces from:** FR04
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB — `vyapar` schema, ProfessionalListingProfile table | data | No |
| Platform-shared taxonomy reference list (structured choice + free-text escape hatch) | data/config (CCR10) | No |
| FR48 taxonomy-review queue (unmapped labels) | in-module contract | No |
| Identity & Trust Service (owner `member_id`) | service (CCR01) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Taxonomy free-text fallback (CCR10) | Medium — free-text capability entry is inherently open-ended | Medium — an unmapped label that never gets reviewed silently degrades search relevance for that member | Yes — FR04's own acceptance criteria require the unmapped label to remain text-searchable and queued for FR48 review |
| Identity & Trust (CCR01) | Low | See CCR01 | Partial, same as IA001 |

**Worth check**
Yes, proceed. Professional/freelancer discovery is a co-equal, named BR02 capability; the three-step minimum design directly answers this FR's own stated risk (abandonment before value is shown).

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA005 — Capability visibility separate from opportunity-seeking visibility
**Traces from:** FR05
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB — `vyapar` schema, ProfessionalListingProfile intent-state field | data | No |
| FR19 ranking signal allow-list (private intent must never leak into a public score) | in-module contract | No |
| MOD05 Dashboard read-side summary contract | contract (CCR08) | Yes (MOD05) |
| FR38 derived-preference confirmation flow | in-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| FR19 allow-list enforcement | Medium — a ranking-signal allow-list is only as strong as its enforcement point; a future FR19 change could accidentally reintroduce a private-intent input | Critical if it leaks — this is the exact harm cross-cutting BR rule 6 exists to prevent | Yes — FR19's own acceptance criteria name the signal allow-list as excluding this class of input explicitly |
| MOD05 contract (CCR08) | Low | Critical if breached — see CCR08 | Yes — FR05's own acceptance criteria state "Search/detail/MOD05 never render private intent" as a direct test target |

**Worth check**
Yes, proceed. This is one of the module's most safety-load-bearing FRs (cross-cutting rule 6, BR12) — separating the two visibility axes is what makes "I'm an accountant" publishable without exposing "I'm looking for work," a stated non-negotiable invariant.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA006 — Shared VerifiedCredential reference, distinct from Counsel ExpertProfile
**Traces from:** FR06
**Status:** Ready for Review
**Confidence:** Medium — matches the FR's own stated confidence, dependent on the Identity & Trust read contract.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Identity & Trust Service — `VerifiedCredential` shared record (ADR-013) | service, sync read + cached fallback (CCR01) | No (platform-owned shared entity, not another business module) |
| Explicit non-dependency: MOD04 Counsel ExpertProfile | contract boundary (must never be read or joined) | Yes, in the negative sense — the risk is an accidental read, not an intended one |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Identity & Trust VerifiedCredential read | Low (per CCR01, plus this FR's own explicit "last cached status, no error to viewer" degradation path) | Medium — a stale-but-harmless display, not a safety issue, by design | Yes — FR06's own acceptance criteria test the 1-hour revocation-sync bound directly |
| Accidental ExpertProfile linkage/exposure | Low — the FR is explicit that no Counsel data is read or shown | High if it ever occurred — this is precisely the "no profile merge" boundary ADR-013 and BR02 both exist to protect | Yes — FR06's third acceptance criterion is exactly this check ("No Counsel data is read or shown") |

**Worth check**
Yes, proceed, as a Should. It is real trust value (one credential fact reused across modules) but the module functions without it, matching its own Should priority and Medium confidence honestly.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA007 — Phone/OTP contact baseline on every Listing
**Traces from:** FR07
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Platform's shared OTP-sending capability (SMS channel, ADR-006 → external SMS provider) | service, async (CCR04) | No |
| FR03 lifecycle gate (no Listing leaves Draft unverified) | in-module contract | No |
| FR50 identity boundary (explicit non-authentication clarification) | in-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| OTP delivery reliability (CCR04, grounded by 2026-09-14 research: template/route mismatch causes silent, undetected failure even on DLT-compliant routes) | Medium — this is a real, documented failure mode for India SMS OTP, not a hypothetical one | Medium — a failed OTP blocks one listing's onboarding and, if systemic, silently suppresses V1 supply | Partial — FR07's 5-attempt/15-minute-lockout design anticipates retries but there is no automated test for actual carrier-level delivery failure; that is inherently an operational/monitoring concern for Step 13, not a Step 10 test |
| FR03 gate enforcement | Low | High — see IA003 | Yes |
| Authentication/verification boundary confusion (FR50) | Low, now explicitly corrected across the FR set | Medium — conflating this with member login would be a real product-boundary violation | Yes — FR07's fourth acceptance criterion explicitly tests "creates no session, credential, or login state" |

**Worth check**
Yes, proceed. This is the universal, no-exceptions legitimacy baseline BR03 is built on, directly precedented by Justdial/WorkIndia/Apna's own OTP-first patterns (BR03 DEC-003); CCR04's finding strengthens rather than weakens the case for the specific retry/lockout design already specified.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA008 — Business-existence document submission and operator review
**Traces from:** FR08
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Object Storage/CDN (encrypted document/image storage, masked display, 30-day auto-delete) | service (CCR07) | No |
| Public GST/Udyam lookup portals (manual operator spot-check) | external third-party service | No |
| FR47 operator queue (Admin Console) | in-module contract | No |
| Manual verification-operator process | operational/human (CCR12) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Object Storage retention/masking (CCR07) | Low likelihood of an outage, but the masking/30-day-deletion control is a compliance mechanism that must not silently fail | High — a masking or deletion-schedule failure on a PAN upload is a real DPDP-relevant exposure, not a cosmetic bug (this is the exact class of concern BR03 DEC-004 already resolved for Aadhaar) | Partial — FR08's acceptance criteria state the masked-storage/30-day-deletion rule as testable, but automated verification of an actual deletion-schedule job is a Step 8/10 concern, not yet built |
| Public GST/Udyam lookup availability | Low-Medium — these are external government portals outside Vyapar's control | Low — a manual spot-check failing over to "Pending" longer is an operator-experience cost, not a data-integrity risk | N/A — external portal availability is not something MOD01's own test suite can assert |
| Operator bottleneck (CCR12) | Medium at solo-founder stage | Medium — see CCR12 | Yes — FR47's overdue-highlighting is a direct, testable acceptance criterion |

**Worth check**
Yes, proceed, exactly as specified. BR03 DEC-002/DEC-003/DEC-004 already resolved the harder open questions (no mandatory GSTIN, Aadhaar dropped for a verified UIDAI-compliance reason); this FR is the correctly-scoped implementation of an already-settled policy, not a new open risk.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA009 — Professional-credential document review
**Traces from:** FR09
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Object Storage (credential document, ≤5MB) | service (CCR07) | No |
| FR47 operator queue | in-module contract | No |
| Manual verification-operator process | operational/human (CCR12) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Object Storage (CCR07) | Low | Medium — lower stakes than FR08's identity documents; a credential image is not the same masking-sensitivity class as PAN | Yes — FR09's acceptance criteria are narrower and directly testable (one document per request, named claim + issuer) |
| Operator bottleneck (CCR12) | Medium | Medium | Yes — same "Needs clearer copy" re-upload path is a direct, testable acceptance criterion |

**Worth check**
Yes, proceed, as a Should. It gives professional listings a scoped, plain-language credential claim rather than a vague "verified professional" badge — necessary for BR03's honesty principle but genuinely secondary to FR07/FR08's universal baseline.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA010 — Verification state display, expiry, and revert
**Traces from:** FR10
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR08/FR09 verification records (source of truth for the displayed state) | in-module contract | No |
| FR39 report/dispute pipeline (triggers early revert) | in-module contract | No |
| Notification Service (11-month reconfirmation reminder) | service (CCR05) | No |
| Every listing-rendering surface (FR15, FR16, FR18, FR55, MOD05 summary) | in-module + cross-module fan-out (CCR08) | Yes (MOD05, read-only) |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Multi-surface label consistency | Medium — the label must render identically on every one of the surfaces listed, a classic place for one surface to drift | High — cross-cutting rule 3 (verification/paid/reputation are separate, never conflated) is one of the module's most repeated non-negotiables; a drifted label directly undermines member trust | Partial — FR10's own acceptance criteria test the state machine and timing bounds, but cross-surface rendering consistency is more naturally a UI-layer/Step 10 integration-test concern than a unit-level one |
| Notification reminder failure (CCR05) | Low-Medium | Low — FR10's own failure/edge outcome explicitly states "reconfirmation notification failure does not extend expiry," so a missed reminder degrades UX, not correctness | Yes — that exact rule is a stated acceptance criterion |
| FR39 dispute trigger | Low | Medium — a dispute must revert the label within 5 seconds; a lag here is a trust-signal accuracy issue | Yes — the 5-second bound is a direct acceptance criterion |

**Worth check**
Yes, proceed. "Verification is evidence at a time, not a permanent guarantee" is a core BR03 invariant with real consumer-protection weight; without expiry/revert, a revoked or stale claim would keep displaying as current, which is a materially worse outcome than not verifying at all.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA011 — Opportunity Composer: create, share, or upload with source segment
**Traces from:** FR11
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB — `vyapar` schema, Opportunity table (Draft state) | data | No |
| Object Storage (screenshot upload ≤5MB) | service (CCR07) | No |
| Explicit non-dependency: MOD05 Dashboard's Local Information Intelligence (autonomous public-source ingestion) | contract boundary — MOD01 never calls this pipeline | Yes, in the negative sense (a boundary Vyapar must not cross, not one it depends on) |
| URL-fetch handling for "Share a pasted URL" (source-unreachable flagging) | in-module component, external HTTP fetch | No (external third-party sites, not a ForKhatri module) |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Object Storage (CCR07) | Low | Low-Medium — a screenshot upload failure is recoverable (retry), not a data-integrity risk | Yes — the ≤5MB/unsupported-type inline-error path is a direct acceptance criterion |
| Accidental drift into autonomous ingestion | Low — the FR's own design (member-initiated, three explicit entry modes) structurally prevents this, but a future feature addition (e.g., an auto-suggest-from-web feature) could accidentally cross the line | Critical if it occurred — this is exactly the MOD05 boundary `modules/modules.md`'s Step 0 decomposition drew, and BR04's own scope note treats it as a first-order constraint, not a detail | Partial — no automated test can prove a future feature won't cross this line; it is a design-review discipline, not a testable invariant today |
| External URL fetch reliability | Medium — pasted URLs from arbitrary external sites will sometimes error or time out | Low — FR11's own failure/edge outcome explicitly accepts this ("still accepted as a Draft with a source-unreachable flag") | Yes — that is a direct, stated acceptance criterion |

**Worth check**
Yes, proceed. The Community/Public-External source-segment tag (BR04 DEC-001) is the specific mechanism that lets Vyapar honor the source corpus's broader opportunity vision without silently absorbing MOD05's autonomous-ingestion scope — removing this FR would either lose that value or reopen the boundary risk.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA012 — Structured fields, uncertainty marking, and contributor confirmation
**Traces from:** FR12
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR11 Draft Opportunity (input) | in-module contract | No |
| Rule-based field-extraction component (optional AI assistance explicitly not a hot-path dependency) | in-module component | No |
| Notification Service (day-5 reminder) | service (CCR05) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Extraction quality on Share/Upload input | Medium-High — screenshots and pasted text are inherently messy | Low — by design, poor extraction degrades to "ask the member to enter the four material fields manually," never to a fabricated fact; this is the exact mechanism cross-cutting rule 8 requires | Yes — the failure/edge outcome ("if inference produced no usable fields... asked to enter manually") is a direct acceptance criterion |
| Day-5/day-7 reminder-then-archive timing (CCR05) | Low-Medium | Low | Yes — stated timing is a direct acceptance criterion |

**Worth check**
Yes, proceed. This FR is what keeps FR11's WhatsApp-forward-style input from ever becoming a confidently-displayed fact it isn't — a direct implementation of cross-cutting rules 7 and 8, which the module's Sealed BR file treats as non-negotiable.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA013 — Opportunity lifecycle, freshness, and expiry
**Traces from:** FR13
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR18 Discover feed exclusion (non-Active states) | in-module contract | No |
| Search Service index removal on state change | service (CCR02) | No |
| Notification Service (day-14 reminder) | service (CCR05) | No |
| Audit Service (provenance retention through Removed state) | service (CCR06) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Timer-driven state transitions (day-14/day-21/deadline-or-day-45) | Medium — scheduled-job correctness (a cron/worker) is a common source of off-by-one or timezone bugs | High — a stuck-Active stale record is precisely the harm BR04's "stale inventory must never look current" invariant exists to prevent | Partial — the timing rules themselves are directly testable acceptance criteria, but the underlying scheduler's own reliability is more of a Step 8/13 operational concern |
| Search/feed exclusion propagation (CCR02) | Low-Medium | Medium — see CCR02 | Yes — the 5-second exclusion bound is a direct acceptance criterion |

**Worth check**
Yes, proceed. Without enforced freshness, the module's supply side degrades into an unaccountable message board — exactly the failure BR04's Worth check names directly.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA014 — Opportunity types with V1 launch focus
**Traces from:** FR14
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB — `vyapar` schema, Opportunity.type field + type-specific sections | data | No |
| FR18 proactive-notification exclusion for "Other" types | in-module contract | No |
| Launch-geography configuration (Hyderabad/Secunderabad working assumption) | data/config | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Type-specific mandatory-field re-validation on type change | Low-Medium | Low-Medium — a stale mandatory field surviving a type change is a data-quality issue, not a safety one | Yes — "type change after publish re-validates type-specific mandatory fields" is a direct acceptance criterion |
| "Other" type exclusion from proactive notification | Low | Low — this is an intentional V1 scope limit (BR04 DEC-003), not a defect | Yes — directly testable |

**Worth check**
Yes, proceed. The V1 wedge (Employment, Freelance/Project, Local Business/Professional Service) is taken directly from the source corpus's own explicit recommendation (critqureport §24) rather than invented, which is the strongest possible grounding a launch-scope decision can have.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA015 — Standalone Listing search and browse
**Traces from:** FR15
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Search Service — embedded Postgres full-text search (ADR-007/018) | service (CCR02) | No |
| FR02 contact-disclosure / discoverability settings | in-module contract | No |
| FR30 Sponsored-label rendering | in-module contract | No |
| FR10 verification-state label | in-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Search relevance/latency at scale (CCR02) | Low at V1 volume, per ADR-018's own threshold analysis | Medium — a slow or poor-relevance search directly undermines this FR's core promise (an "ordinary find-me-a-plumber" experience) | Partial — the 2-second/first-20-results bound is a direct acceptance criterion; actual relevance quality is inherently a Step 8/13 tuning concern, not a binary pass/fail test |
| Private-field leakage into results (FR02/FR05) | Low | Critical if it occurred — same class of harm as CCR08 | Yes — FR15's own acceptance criteria and FR02/FR05's independently test this |
| Sponsored/organic-order integrity (FR30) | Low | High — pay-to-win ranking is an explicit cross-cutting-rule-3 violation if it ever happened | Yes — "organic order unaffected by payment" is a direct acceptance criterion |

**Worth check**
Yes, proceed. This is the FR that resolves BR05's core Worth-check tension directly — it is the standalone "just find me a business" surface the Product Manager explicitly confirmed as co-equal scope, distinct from `Vyapar_02`'s opportunity-only Discover tab (FR15 DEC-001).

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA016 — Listing detail view with trust context and action
**Traces from:** FR16
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR10 verification-state label | in-module contract | No |
| FR28 reputation-signal display | in-module contract | No |
| FR02 contact-disclosure rules | in-module contract | No |
| FR22 "Enquire Now" primary action | in-module contract | No |
| FR39 Report action | in-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Aggregating five distinct in-module contracts on one screen | Medium — the more contracts a single view composes, the more places one can silently drift out of sync (e.g., FR02 tightens disclosure but FR16 doesn't re-render in time) | Medium — the harm is a stale or inconsistent display, not data loss | Partial — each contributing FR has its own acceptance criteria, but there is no single FR that tests the composed screen's cross-contract consistency end-to-end; that is a UI-integration (Step 10) concern |
| Stale-link handling (Suspended/Archived listing) | Low-Medium | Low — the correct behaviour (no data shown) is itself the safe default | Yes — directly stated as an acceptance criterion |

**Worth check**
Yes, proceed. This is the single screen that has to make verified/paid/reputation/member-provided distinctions legible at a glance — the direct implementation surface for cross-cutting rules 2, 3, and 9.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA017 — Zero-result broadening
**Traces from:** FR17
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Search Service (re-run with broadened radius/filters) | service (CCR02) | No |
| FR11 "Post what you need" fallback | in-module contract | No |
| FR21 "Notify me when something matches" fallback | in-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Silent constraint relaxation (the thing this FR explicitly forbids) | Low — the FR's own design requires every broadening step to be explicit and user-selected | High if it ever happened silently — this is a direct trust violation, not a UX nicety | Yes — "no silent relaxation of any user-set hard filter" is a direct acceptance criterion |
| Second-zero-result fallback chaining into FR11/FR21 | Low | Low | Yes — the fallback offer is a stated acceptance criterion |

**Worth check**
Yes, proceed, as a Should. It is a real quality-of-experience improvement over a bare "no results" dead end, and it is explicitly non-manipulative by design (broadening is always user-chosen and labelled).

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA018 — Opportunity Discover feed sections
**Traces from:** FR18
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR19 eligibility-before-ranking engine | in-module contract | No |
| FR13 lifecycle exclusions (non-Active states) | in-module contract | No |
| FR30 Sponsored-card labelling and eligible-audience confinement | in-module contract | No |
| FR04 enrichment prompt (sparse-profile fallback) | in-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| FR19 eligibility engine correctness | Medium — a five-section feed multiplies the surfaces a ranking bug can reach at once | High — an ineligible record leaking into any section is a direct hard-eligibility violation (cross-cutting rule 2) | Yes — FR19's own acceptance criteria test hard-filter precedence directly, and this FR requires "every card is eligible" as its own acceptance criterion |
| First-section load latency (2-second bound) | Medium at scale | Medium — a slow Discover load directly undermines the module's core engagement loop | Partial — the bound is a stated acceptance criterion; sustained performance under real load is a Step 8 concern |
| Sponsored-card confinement | Low | High if violated — same pay-to-win concern as IA015 | Yes |

**Worth check**
Yes, proceed. Five sections implementing "structure → retrieve → eligibility → score → rank → diversify → distribute" is the direct operationalization of BR06's entire relevance/distribution thesis; without it, opportunity discovery collapses to a flat, unranked list.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA019 — Eligibility-before-ranking with configuration-driven deterministic scoring
**Traces from:** FR19
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Ranking-weight configuration store | data/config | No |
| Signal allow-list (explicitly excludes sensitive attributes, community status, account age, paid status, popularity, report signals) | in-module contract, config-enforced | No |
| Every FR that produces a ranked list (FR15, FR17, FR18, FR20, FR55) | in-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Signal allow-list drift (a future change accidentally adding a prohibited input) | Medium over time — this is the single highest-leverage place a well-intentioned "let's also factor in X" change could quietly reintroduce a prohibited signal | Critical if it occurred — this is the module's most explicit anti-bias/anti-discrimination control (cross-cutting rules 4, 5, 7) and BR06's Constraints list names it directly | Yes at this FR's own level (the allow-list is a direct, testable acceptance criterion), but ongoing drift-prevention is a code-review/architecture discipline (§5 of `/MODULE-ARCHITECTURE-STANDARD.md`'s authorization-chokepoint pattern is the right analog to apply here at Step 7), not something one test suite guarantees forever |
| Configuration-missing fallback | Low | Low — "safe defaults logged as a warning" is an explicit, graceful failure mode | Yes — directly stated |

**Worth check**
Yes, proceed. Deterministic, explainable scoring over ML-first ranking (FR19 DEC-001) is the correct choice for sparse V1 data and matches BR06's own explicit risk-acceptance; the allow-list is the load-bearing control worth flagging forward into Step 7/Step 8 as a structural chokepoint, not just a config list.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA020 — "Why this opportunity" explanation
**Traces from:** FR20
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR19 ranking signals (must be the same signals used for ranking, not a separate explanation model) | in-module contract | No |
| FR30 Sponsored disclosure line | in-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Explanation-signal drift from actual ranking signals | Low-Medium — the risk is a future implementation shortcut computing a separate "reason string" instead of reading FR19's actual contributing signals | High if it drifted — an explanation that doesn't match the real ranking logic is a form of the "opaque AI matchmaking" BR06 explicitly rules out, even if unintentional | Yes at the acceptance-criteria level ("derived from the same approved signals used for ranking" is directly stated), but this is exactly the kind of invariant that needs a shared implementation, not two independently-built code paths (per `/MODULE-ARCHITECTURE-STANDARD.md`'s recurring "same pattern as" warning sign) |

**Worth check**
Yes, proceed. Explainability is a stated platform-level guardrail value (see PRODUCT-GUARDRAILS.md's "Explainability" row for the sibling Milavn module, and this file's own BR06 Constraints), and this FR is the module's direct implementation of it.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA021 — Proactive notification and digest with fatigue limits
**Traces from:** FR21
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Notification & Communication Service (push/in-app, digest) | service (CCR05) | No |
| FR19 "strong match" threshold configuration | in-module contract | No |
| FR14 "Other"-type exclusion | in-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Notification Service reliability/duplication (CCR05) | Low-Medium | Medium — a duplicate send is a real annoyance risk against the module's own stated fatigue-management goal | Yes — "no duplicate sends on retry" is a direct acceptance criterion |
| Daily-cap/digest-hour enforcement | Low | Medium — exceeding the cap would directly violate BR06's "relevant reach, not maximum reach" principle | Yes — directly testable |

**Worth check**
Yes, proceed, as a Should. It converts passive discovery into proactive reach for the members most likely to benefit, while its explicit caps are the direct mechanism preventing the "volume... overwhelm[ing] members" harm BR06's Problem statement names.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA022 — Submit an Enquiry or Opportunity Response
**Traces from:** FR22
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB — `vyapar` schema, Enquiry table | data | No |
| Notification Service (provider delivery within 10 seconds) | service (CCR05) | No |
| Object Storage (attachment ≤5MB) | service (CCR07) | No |
| FR24 blocked-sender handling | in-module contract | No |
| Shared rate-limiting utility (20/day cap, 1-open-per-target) | in-module component, per `/MODULE-ARCHITECTURE-STANDARD.md` §4c | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Rate-limit implementation (§4c) | Medium — this is exactly the class of endpoint `/MODULE-ARCHITECTURE-STANDARD.md` §4c warns tends to get reimplemented per-feature rather than shared; Vyapar will also need rate limits on FR39 (reports) and FR25 (partnership requests) | Medium — a rate-limit bug either fails to cap abuse or wrongly blocks legitimate use | Not yet — no `architecture.md` exists to confirm one shared utility will be used rather than three independently-built counters; flagged for Step 7 to resolve explicitly, the same way MOD03's own Step 6 pass flagged it (that file's IA-equivalent finding, since fixed, is exactly this pattern) |
| Blocked-sender non-disclosure (FR24) | Low | Medium — silently not delivering while showing "Submitted" is deliberate, correct behaviour per FR22's own design, but a bug that instead discloses the block would be a real safety regression | Yes — "blocked-sender handling without disclosure" is a direct acceptance criterion |
| 10-second delivery bound (CCR05) | Low-Medium | Low-Medium | Yes — directly stated |

**Worth check**
Yes, proceed. This is the FR that makes discovery actionable (BR07's core Worth check) — but the rate-limiting-utility question above should be resolved once, explicitly, in Step 7's `architecture.md`, not independently reinvented per abuse-prone endpoint.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA023 — Provider manages the Enquiry lifecycle
**Traces from:** FR23
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR22 Enquiry record (state machine) | in-module contract | No |
| FR28 provider-responsiveness signal (7-day no-response marker) | in-module contract | No |
| MOD04 Counsel — "Refer to Counsel" referral contract | contract, async (CCR09) | Yes (MOD04) |
| FR52(f) minimum-field referral payload | contract | Yes (MOD04) |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Restricted-thread transition rejection | Low | Medium — a state-change bug on a Restricted thread would let further messaging happen against an explicit safety control | Yes — "state changes on a Restricted thread are rejected" is a direct acceptance criterion |
| MOD04 referral scope creep (CCR09) | Low | Low — see CCR09; the payload is intentionally minimal | Yes — FR23/FR52(f) both state "changes nothing else in the thread" / "no appointment or payment state exchanged" as direct, testable boundaries |
| 7-day no-response marker feeding FR28 | Low | Medium — this marker becomes a reputation signal, so its correctness matters for BR09's fairness invariants (no retaliation, no gaming) | Yes — the day-7 threshold is a direct acceptance criterion |

**Worth check**
Yes, proceed. This is the FR that resolves the FR52(f) referral gap the Product Manager's own approver check (2026-09-12 revision) identified and filled — a well-grounded correction, not a late addition covering for a missing capability.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA024 — Consent-based contact disclosure, blocking, and safety guidance
**Traces from:** FR24
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR02 contact-disclosure-level settings | in-module contract | No |
| FR23 enquiry state (In Progress trigger for disclosure) | in-module contract | No |
| Block/report subsystem (FR39) | in-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Disclosure timing correctness (only after Accept, only per channel setting) | Medium — this composes two independent settings systems (FR02 levels, FR23 state) and both must agree | High — premature or over-broad disclosure is exactly the "personal details exposed too early" harm BR07's Problem statement names | Yes — "disclosure only after acceptance and per channel setting" is a direct, testable acceptance criterion |
| Bulk/export contact-list prevention | Low | Critical if violated — this is the explicit "no lead lists" invariant BR07/BR10 both repeat | Yes — "export or bulk view of enquirer contact details is not available to any role" is a direct acceptance criterion |

**Worth check**
Yes, proceed. Purpose-limited, revocable disclosure is what keeps the enquiry mechanism from becoming an informal contact-leak path — a direct, necessary safeguard, not an optional add-on.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA025 — Create a Partnership Request
**Traces from:** FR25
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB — `vyapar` schema, PartnershipRequest table | data | No |
| FR03 Active-Listing requirement (both sides) | in-module contract | No |
| Notification Service | service (CCR05) | No |
| Shared rate-limiting utility (10-pending cap) | in-module component (same §4c concern as IA022) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Rate-limit implementation reuse | Medium — same finding as IA022; flagged once here rather than repeated per endpoint | Medium | Not yet — same Step 7 flag as IA022, folded into one architecture decision rather than three |
| Active-Listing gate on both sides | Low | Medium — allowing a request without an Active Listing would blur the "not a follower graph" boundary BR08 draws | Yes — directly stated as an acceptance criterion |

**Worth check**
Yes, proceed, as a Should. Structured business networking without a social graph is a real, named capability distinct from an enquiry, but core discovery/enquiries function without it — matching the Should priority honestly.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA026 — Respond to and manage a Partnership Request
**Traces from:** FR26
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR25 PartnershipRequest (state machine) | in-module contract | No |
| FR02 contact-disclosure level (post-Accept reveal) | in-module contract | No |
| FR27 review eligibility (Accepted → Closed feeds reputation) | in-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| No-auto-expiry-of-Pending policy | Low | Low-Medium — an intentional, PM-approved open policy choice (BR08's own Constraints note this explicitly), not a defect | Yes — "no auto-expiry of Pending" is a direct acceptance criterion |
| 30-day Decline re-send cooldown | Low | Low — prevents a mild harassment pattern (repeated re-asks after decline) | Yes — directly stated |

**Worth check**
Yes, proceed, same rationale as IA025 (they share one BR08 capability, split for build-order granularity).

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA027 — Submit a Review tied to a qualifying interaction
**Traces from:** FR27
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR23 Enquiry-Resolved/Closed state, FR26 PartnershipRequest-Accepted-then-Closed state | in-module contract | No |
| FR40 automated safety check (before Publish) | in-module contract | No |
| Identity & Trust — reputation-aggregation read (ADR-005) | service (CCR01) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Qualifying-interaction enforcement | Medium — this is the single control preventing arbitrary/unearned reviews, and it must correctly recognize every valid interaction path (Enquiry and PartnershipRequest alike) | High — a bypass here would let Vyapar become exactly the "unbounded public ratings" product BR09's Problem statement explicitly rejects | Yes — "qualifying-interaction rule enforced; one review per party per interaction" is a direct acceptance criterion |
| Auto-hide on fraudulent-thread removal | Low | Medium — a review surviving its own removed underlying thread would be a dangling, misleading trust signal | Yes — directly stated as an acceptance criterion |

**Worth check**
Yes, proceed. Interaction-tied reviews are what let BR09 avoid popularity bias and review manipulation while still providing real accountability — the module's Worth check for BR09 depends directly on this control existing.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA028 — Contextual reputation display with no new-member penalty
**Traces from:** FR28
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR27 Review records (source of counts) | in-module contract | No |
| FR19 trust signal input (counts only above 3-interaction threshold) | in-module contract | No |
| FR29 dispute/hide exclusion from counts | in-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| "New on Vyapar" cold-start fairness | Low | Medium — a ranking or display bug that silently penalized new members would directly violate cross-cutting rule 5 ("no history is not a negative signal") | Yes — directly stated as an acceptance criterion |
| Hidden/Removed review exclusion timing (5 seconds) | Low-Medium | Medium — a lagging exclusion would let a disputed/removed review keep affecting a count it should no longer influence | Yes — directly stated |

**Worth check**
Yes, proceed. Contextual counts instead of an aggregate score is the direct mechanism BR09 relies on to avoid a misleading, gameable "leaderboard" feel.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA029 — Review dispute, hide, and removal
**Traces from:** FR29
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR40 moderation queue | in-module contract | No |
| FR28 count recalculation on outcome | in-module contract | No |
| Audit Service (full audit history preserved in all outcomes) | service (CCR06) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| No-provider-side-edit-or-hide guarantee | Low | High — a provider being able to unilaterally suppress an unfavorable review would defeat BR09's entire accountability purpose | Yes — "no provider-side edit/hide capability" is verified "by absence of such an action for the provider role," a direct, testable negative acceptance criterion |
| One-dispute-per-review limit | Low | Low-Medium — prevents repeated dispute harassment of the same review | Yes — directly stated |

**Worth check**
Yes, proceed, as a Should. Due process for disputed reviews is necessary to keep BR09's anti-gaming/non-retaliation guarantee credible, without which the review system itself would create a new safety problem (as BR09's own Worth check warns).

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA030 — Purchase an Opportunity or Listing Boost
**Traces from:** FR30
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR51 payment-gateway integration (order creation, payment confirmation) | in-module contract → external gateway (CCR03) | No (direct external gateway, not MOD06) |
| FR10 Active-Verified eligibility gate | in-module contract | No |
| FR18/FR15 Sponsored-label rendering across every surface | in-module contract | No |
| Promotion product/price configuration | data/config | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Payment-gateway integration (CCR03) | Low-Medium — see CCR03's grounded research finding | High — a payment-state bug here is a direct financial-integrity and trust issue (a member paying without the Promotion activating, or vice versa) | Partial — FR30's own failure/edge outcomes (24-hour Awaiting-Payment window, mid-boost suspension credit) are stated acceptance criteria, but genuine payment-integration testing (sandbox webhooks, signature failures) is inherently a Step 8/10/11 concern layered on top of this FR's business rules |
| Verified-only eligibility gate | Low | High — allowing an unverified listing to boost would directly violate cross-cutting rule 3 (payment cannot buy verification) | Yes — "unverified Listing → Boost unavailable" is a direct acceptance criterion |
| Organic-rank non-interference | Low | Critical if violated — the module's entire pay-to-win guardrail rests on this | Yes — "organic rank of all records is unchanged" is a direct acceptance criterion |

**Worth check**
Yes, proceed. This is the FR that actually operationalizes BR10's monetization thesis (the V1 commercial catalog resolved directly from the pricing source's own roadmap) — without it, the module has no revenue mechanism at all, which BR10's Worth check treats as a real gap, not an acceptable simplification.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA031 — Promotion lifecycle, price versioning, cancellation, and credit
**Traces from:** FR31
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR51 payment-gateway refund/credit issuance | in-module contract → external gateway (CCR03) | No |
| FR49 refund-retry-failure surfacing (Admin Console) | in-module contract | No |
| Product/price version history | data | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Price-version-at-purchase-time storage | Low | High — losing the price-in-force-at-purchase would make historical orders un-reconstructible, a direct violation of this FR's own stated success outcome | Yes — "product/price version stored per order" is a direct acceptance criterion |
| Refund-issuance failure handling (CCR03) | Low-Medium | Medium — a failed refund silently disappearing (rather than retried and surfaced) would be a real financial-trust harm | Yes — "refund request failure → retried and surfaced in the FR49 queue" is a direct acceptance criterion |

**Worth check**
Yes, proceed. Transparent, auditable, reconstructible commercial records are the specific control that keeps FR30's monetization capability from becoming an opaque billing system — a necessary companion FR, not a separable nice-to-have.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA032 — Provider performance reporting without unsupported claims
**Traces from:** FR32
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR45 analytics-event instrumentation (source of counts) | in-module contract | No |
| FR23/FR27 confirmed-outcome signals | in-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Unsupported-claim prevention (no projections, ROI guarantees, causal statements) | Low-Medium — this is a copy/product-behaviour discipline as much as a technical one, and easy for a future feature to violate unintentionally ("show projected reach" is a very natural feature request) | Medium — an ROI or causal claim would be a real consumer-protection concern under BR18's proportionate-disclosure posture | Yes at this FR's own level ("shall not display projections, ROI guarantees, or causal statements" is a direct, testable negative acceptance criterion), but this is the kind of rule that needs an explicit product-review gate on every future reporting feature, not just a one-time test |
| Member-level-data suppression in reports | Low | High — showing individual member identity in a provider-facing report would be a direct privacy violation (BR12) | Yes — "no individual member identity is ever shown in reports" is a direct acceptance criterion |

**Worth check**
Yes, proceed, as a Should. It is what makes FR30's paid promotion honest rather than a black box, directly supporting BR10's "defensible measures only" constraint.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA033 — Purchase and manage a Business Workspace entitlement
**Traces from:** FR33
**Status:** Ready for Review
**Confidence:** Medium — matches the FR's own stated confidence; product scope is configuration and willingness-to-pay is unproven.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR51 payment-gateway integration (Entitlement purchase, renewal) | in-module contract → external gateway (CCR03) | No |
| FR34 multi-user administration (included capability) | in-module contract | No |
| FR35 campaign management (included capability) | in-module contract | No |
| FR32 provider analytics (included capability) | in-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Payment-gateway renewal handling (CCR03) | Low-Medium | Medium — a 7-day grace period with a payment failure that silently fails to notify would surprise a paying business | Yes — "renewal payment failure → 7-day grace with notices, then Entitlement Paused" is a direct acceptance criterion |
| No-effect-on-verification/ranking/eligibility guarantee | Low | Critical if violated — the exact same pay-to-win concern as IA030, applied to a subscription rather than a per-boost purchase | Yes — "no effect on verification/reputation/ranking/eligibility" is a direct acceptance criterion |
| Willingness-to-pay uncertainty (business risk, not a dependency risk) | Medium-High — named directly in the FR's own Confidence note | Low from a system-risk standpoint (a low-adoption feature is a product-metrics concern, not a defect); it is the underlying reason this FR is Should, not Must | N/A — not a testable system risk |

**Worth check**
Yes, proceed, as a Should, exactly as scoped. The pricing source's own V1 roadmap places Business Workspace in V1 (BR10's monetization-phase table), but the module's core discovery/enquiry loops do not depend on it — this FR is honestly optional relative to the rest of the build.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA034 — Multi-user business administration roles
**Traces from:** FR34
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Identity & Trust Service (invite by phone number → resolves to a `member_id`) | service (CCR01) | No |
| FR33 Workspace entitlement (gates this capability) | in-module contract | No |
| Authorization chokepoint for Vyapar's own Admin/Operator role split | in-module component, per `/MODULE-ARCHITECTURE-STANDARD.md` §5 | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Immediate-revocation propagation | Low-Medium | High — a delayed revocation would let a removed operator keep acting for the business, a real authorization-integrity failure | Yes — "immediate revocation; actions attributed to individuals" is a direct acceptance criterion |
| Session/authentication-boundary confusion (this FR explicitly clarifies the Vyapar role vs. the platform session are different things) | Low, now explicitly corrected in the FR text itself | Medium — conflating "revoke Vyapar Operator role" with "end platform session" would be a real product-boundary error, exactly the class of confusion FR50's post-seal correction fixed elsewhere | Yes — the FR's own text states this distinction directly, and it is consistent with FR50's DEC-001 |
| 30-day invitation expiry for a non-member invitee | Low | Low | Yes — directly stated |

**Worth check**
Yes, proceed, as a Should, tied directly to FR33's Workspace entitlement — auditable delegated authority is necessary once a business has multiple people acting on its behalf, but is meaningless without FR33 already purchased.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA035 — Community/Opportunity Campaign creation
**Traces from:** FR35
**Status:** Ready for Review
**Confidence:** Medium — matches the FR's own stated confidence (pricing model places this in V1; BR11 itself is Should).

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR33 Workspace entitlement (gates this capability) | in-module contract | No |
| FR30 Boost mechanics (applied per campaign item) | in-module contract | No |
| FR32 campaign-level reporting | in-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Boost-rule reuse per item (rather than a separate campaign-boost implementation) | Low-Medium — the same "same pattern as" risk class named in `/MODULE-ARCHITECTURE-STANDARD.md` §4c, applied here to boost mechanics instead of rate-limiting | Medium — two divergent boost implementations (standalone vs. campaign) would risk one enforcing the pay-to-win guardrails and the other silently not | Yes at the FR-text level ("apply FR30 boost rules to each item" is stated directly), but Step 7's `architecture.md` should confirm this as literally one shared component, not two implementations, the same flag as IA022/IA025 |
| Mid-campaign item-leaving-Active handling | Low | Low-Medium — "Paused with credit per FR31" is the correct, already-specified behaviour | Yes — directly stated |

**Worth check**
Yes, proceed, as a Should. It is packaged distribution for repeat providers built entirely out of already-specified boost mechanics (FR30/FR31/FR32) — genuinely low incremental risk if those mechanics are correctly reused rather than reimplemented.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA036 — Contextual privacy controls
**Traces from:** FR36
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR02 contact disclosure, FR05 seeking-status visibility (two of the six controls this FR unifies) | in-module contract | No |
| MOD05 Dashboard read contract (must honor these defaults) | contract (CCR08) | Yes (MOD05) |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Privacy-by-default value correctness across six controls | Low-Medium | High — a wrong default (e.g., seeking-status defaulting to visible) would be a direct BR12 violation reaching every new member automatically | Yes — the specific defaults (contact after acceptance; seeking private; commercial communications off) are direct acceptance criteria |
| No-cross-module-inference guarantee | Low | High if violated — this is the exact harm BR12's Constraints section names first ("no cross-module inference such as treating activity in another module as... consent to contact") | Yes — "no cross-module data used for defaults" is a direct acceptance criterion |

**Worth check**
Yes, proceed. Cross-cutting rule 7/8 and BR12's entire privacy-by-default posture depend on this FR existing as the single place all six controls live, rather than six independently-defaulted settings scattered across other FRs.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA037 — Data access, correction, deletion, and consent withdrawal
**Traces from:** FR37
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB — `vyapar` schema, full member-data export/deletion routine | data | No |
| Object Storage (evidence/media deletion) | service (CCR07) | No |
| FR31 active-paid-order deferral rule | in-module contract | No |
| DPDP-aligned compliance posture (BR18, CCR14) | compliance/legal | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Anonymization-vs-deletion correctness (counterpart-record preservation) | Medium — this is a genuinely tricky data operation: deleting a member must not silently corrupt a counterpart's enquiry/review thread | High — either failure mode (over-deleting a counterpart's record, or under-deleting the requesting member's own data) is a real compliance and product-integrity problem | Partial — the 72-hour export / 30-day deletion / listed-retention-exceptions bounds are direct acceptance criteria, but anonymization correctness on shared records is exactly the kind of thing that needs a dedicated data-model decision at Step 7a (ER Model), not just an FR-level test |
| Deletion-during-active-paid-order deferral (CCR03 adjacency) | Low | Medium — deleting a member with an active Promotion mid-flight without deferring correctly could orphan a payment record | Yes — "deletion while a paid Promotion is active → informed it completes after the order closes or is cancelled" is a direct acceptance criterion |

**Worth check**
Yes, proceed. This is the FR that makes BR12's rights language (access, correction, deletion, consent withdrawal) real rather than aspirational — proportionate to DPDP-aligned practice exactly as BR18 frames it, and a genuine necessity for member trust.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA038 — Inspect and confirm derived preferences
**Traces from:** FR38
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR19 ranking-signal input (confirmed preferences feed here, reports never do) | in-module contract | No |
| FR55 "Not interested" reason capture (source of the repeated-pattern signal) | in-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Reports-excluded-as-preference-input guarantee | Low | Critical if violated — this is one of the module's most explicit anti-retaliation controls (cross-cutting rule 10, BR13's Constraints), and it intersects directly with FR39's reporting flow | Yes — "reports excluded as inputs" is a direct acceptance criterion |
| Confirmation-required-before-application gate | Low | Medium — a silently-applied inferred preference would violate cross-cutting rule 7/8's "require contributor confirmation" principle | Yes — "proposal with evidence; confirmation required" is a direct acceptance criterion |

**Worth check**
Yes, proceed, as a Should. This is the module's explainable-learning mechanism (BR12/BR06's shared "nothing silent" principle) — genuinely valuable for long-term relevance quality, but the module functions without it at launch.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA039 — Report and block
**Traces from:** FR39
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR40 moderation queue (destination) | in-module contract | No |
| FR24 Block mechanism (offered in the same flow) | in-module contract | No |
| Object Storage (evidence images, ≤3) | service (CCR07) | No |
| Shared rate-limiting utility (10 reports/day) | in-module component (same §4c concern as IA022/IA025) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Reporter-anonymity guarantee | Low | Critical if violated — exposing a reporter's identity to the reported party is a direct retaliation-enablement risk, which BR13's Problem statement names explicitly ("close-knit community trust may... suppress reporting against respected members") | Yes — "reporter identity hidden from the reported party" is a direct acceptance criterion |
| Duplicate-report merge correctness | Low-Medium | Low-Medium — a failure to merge would inflate case counts without changing the underlying safety signal | Yes — "duplicate reports on the same object merge into one case with a reporter count" is a direct acceptance criterion |
| No-effect-on-ranking-preferences guarantee | Low | High if violated — same class of harm as cross-cutting rule 10 | Yes — directly stated |

**Worth check**
Yes, proceed. This is the entry point to the entire Trust & Safety system BR13 exists to justify — without a working, safe report path, every downstream moderation capability (FR40, FR41) has nothing to act on.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA040 — Moderation queue and graduated actions
**Traces from:** FR40
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR39 Report intake, FR03/FR27/FR29 automated-flag sources | in-module contract | No |
| Admin Console (operator UI, permission model) | contract, shared platform console (ADR-012) | No (platform-owned shared console, not another business module) |
| Notification Service (outcome + appeal-path communication) | service (CCR05) | No |
| Audit Service (every action, immutable evidence) | service (CCR06) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| High/Critical auto-limit-pending-review correctness | Low-Medium | High — a failure to auto-limit a Critical item would leave known-severe harm distributing normally while "under review," directly contradicting BR13's Constraints | Yes — "High/Critical items shall be auto-limited from distribution pending review" is a direct acceptance criterion |
| Evidence immutability (operators cannot edit evidence) | Low | High — mutable evidence would undermine the entire audit/appeal chain's credibility | Yes — directly stated |
| Escalation-on-missed-target (never an automatic permanent ban) | Low-Medium | Medium — the module deliberately chose graduated response over automation (BR13 DEC-002); a scheduler bug that instead silently auto-banned would violate that explicit design choice | Yes — "escalation in the queue... no automatic permanent ban" is a direct acceptance criterion |
| Admin Console plugin-contract dependency (ADR-012 flags this contract as needing its own lightweight spec, "expected: Vyapar or Milavn in V1") | Medium — ADR-012 itself names Vyapar as a likely first mover on this, meaning the contract may not yet exist when Vyapar needs it | Medium — building against an unspecified console contract risks rework once the contract is formalized | Not yet — flagged directly for Step 7, consistent with ADR-012's own open item |

**Worth check**
Yes, proceed. This is BR13's operational core; the one real forward risk (the Admin Console plugin contract not yet being formally specified) is a Step 7 sequencing item to resolve, not a reason to defer this FR.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA041 — Appeals and outcome communication
**Traces from:** FR41
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR40 moderation outcome (trigger) | in-module contract | No |
| Notification Service (decision communication) | service (CCR05) | No |
| Different-operator routing (staffing-dependent) | operational/human (CCR12) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Different-reviewer routing "where staffing allows" | High at solo-founder stage — a one-person Trust & Safety operation cannot literally route to a different operator | Low — the FR's own wording ("where staffing allows") already anticipates and accepts this at V1 scale, matching BR13's own Assumption that the founder may be the sole T&S owner initially | Yes — the conditional wording is itself the acceptance criterion; this is a correctly-scoped, honest limitation, not a hidden gap |
| Overturn-restores-fully correctness | Low-Medium | Medium — an incomplete restoration (e.g., a listing restored but its verification state not) would leave the member worse off than a clean overturn should | Yes — "Overturned restores the object/account" fully is a direct acceptance criterion |

**Worth check**
Yes, proceed. Due process without a heavy legal apparatus (BR13/BR18's shared proportionality theme) is exactly the right-sized version of appeals for this product's actual stage.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA042 — Language selection and rendering (English, Hindi, Telugu)
**Traces from:** FR42
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Shared platform i18n library and translated-content data model (ADR-010) | platform-level shared library (CCR11) | No |
| FR19 signal allow-list (language must not be a ranking input) | in-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| String-coverage completeness at release (CCR11) | Medium — a 100%-before-release bar across three languages is an ongoing content-operations discipline, not a one-time build task | Medium — a missing string degrades to a logged English fallback, a graceful but real inclusion gap for the exact members BR14's Problem statement is written for | Yes at the mechanism level ("fallback to English + logged" is a direct acceptance criterion); actual translation completeness is a content-operations metric to track, not a binary test |
| Language-as-ranking-signal exclusion | Low | Medium — same class of harm as FR19's other excluded signals | Yes — "language not in the FR19 signal allow-list" is a direct acceptance criterion |

**Worth check**
Yes, proceed. Multilingual support without hidden ranking effects is a stated platform-level day-one requirement (ADR-010) and a direct BR14 necessity, not a V2 nicety, given the module's own community-density thesis.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA043 — Accessibility baseline
**Traces from:** FR43
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Every MOD01 screen (this FR is cross-cutting across the whole UI surface) | in-module, cross-FR | No |
| CI automated accessibility tooling | in-module/build-pipeline component | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Automated-check coverage gaps (automated tooling cannot catch every WCAG 2.2 AA criterion, e.g., meaningful focus order) | Medium — this is a well-known limitation of accessibility automation generally, not specific to this module | Medium — an accessibility gap excludes exactly the members BR14's Worth check identifies as needing this baseline most | Partial — the FR itself already accounts for this by requiring both an automated CI gate and a recorded manual screen-reader pass of core journeys, which is the correct two-layer approach, but the manual pass is a release-process step, not an automatable regression test |
| Release-gate enforcement (a failing screen blocks release) | Low | Medium — a bypassed gate would let an inaccessible screen ship | Yes — "a screen failing an automated check blocks release of that screen" is a direct acceptance criterion |

**Worth check**
Yes, proceed. WCAG 2.2 AA as a testable baseline (not just a claimed target) is the correct level of rigor for a platform whose own BR14 explicitly names accessibility as a supply/demand/safety necessity, not a compliance afterthought.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA044 — Progressive first-run to discovery
**Traces from:** FR44
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR50 platform sign-in entry point (this FR begins only after it) | in-module contract → platform Identity & Trust (CCR01) | No |
| FR36 privacy defaults (set during first-run) | in-module contract | No |
| FR45 abandonment-step logging | in-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Accidental reintroduction of a Vyapar-owned auth/sign-up screen | Low, given the explicit 2026-09-14 correction already applied across the FR set | High if it recurred — this is precisely the boundary violation the product owner's standing correction (see FR50 DEC-001) exists to prevent, and it is the kind of thing a rushed UI change could reintroduce without realizing it | Yes — "none of the 5 screens is a sign-up, login, or OTP sign-in screen" is a direct, explicit acceptance criterion added specifically because of this history |
| Location-permission-denied fallback | Low | Low — manual locality entry is already the specified fallback | Yes — directly stated |

**Worth check**
Yes, proceed. This FR is the concrete embodiment of the platform's "one ForKhatri identity and entrance" guardrail (see PRODUCT-GUARDRAILS.md checkpoint 9) at the exact seam where a module most commonly reinvents login — its explicit acceptance criteria are a deliberate, necessary safeguard, not boilerplate.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA045 — Event instrumentation with outcome levels
**Traces from:** FR45
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Platform analytics pipeline (99% within 60 seconds target) | service, async | No |
| FR37 behavioral-analytics-consent withdrawal (gates event emission) | in-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Consent-withdrawal enforcement on event emission | Low-Medium | High — emitting behavioral events after a member withdrew consent would be a direct BR12/BR18 compliance violation | Yes — "members who withdraw behavioral-analytics consent emit only the operational minimum" is a direct acceptance criterion |
| Local-buffering-then-drop on pipeline outage | Low | Low-Medium — the FR's own design (buffer 24 hours, then drop with a count metric) is the correct graceful-degradation choice | Yes — directly stated |
| Level-tag correctness (impression vs. confirmed outcome never collapsed) | Medium — this discipline (BR15's core "lineage without inferring causality" principle) is easy to erode over many event types | Medium — collapsed levels would make FR32's and FR46's downstream "no unsupported causal claims" guarantees impossible to honor | Yes at this FR's own level (a direct acceptance criterion), but this is exactly the kind of invariant that benefits from one shared event-emission utility (per `/MODULE-ARCHITECTURE-STANDARD.md`'s recurring theme) rather than per-event-type ad hoc tagging |

**Worth check**
Yes, proceed. This FR is the evidentiary foundation for FR32 (honest provider reporting) and FR46 (marketplace health) alike — without it, both of those FRs would have no real data to report against.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA046 — Marketplace health metrics view
**Traces from:** FR46
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR45 event stream (sole data source) | in-module contract | No |
| Admin Console (operator analytics permission) | contract, shared platform console (ADR-012) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Minimum-group-size suppression (k=10) | Low-Medium | Medium — a failure to suppress small groups would risk re-identifying an individual member from an aggregate metric, a real privacy issue in a close-knit community (BR12) | Yes — "groups under 10 are suppressed" is a direct acceptance criterion |
| Profile-completion-percentage exclusion (explicitly rejected as a metric) | Low | Low — an intentional product-philosophy guardrail (avoiding a gamifiable vanity metric), not a technical risk | Yes — "profile-completion percentage is not offered as a metric" is a direct, testable negative acceptance criterion |

**Worth check**
Yes, proceed, as a Should. It is the operator-facing tool that turns FR45's raw events into an actual health signal distinguishing a working marketplace from a noisy feed — valuable but not required for the member-facing product to function.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA047 — Verification queue in the Admin Console
**Traces from:** FR47
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR08/FR09 BusinessVerificationRecord queue | in-module contract | No |
| Object Storage (uploaded evidence images, auto-delete per FR08) | service (CCR07) | No |
| Admin Console (permission-gated evidence access) | contract, shared platform console (ADR-012) | No |
| Manual verification-operator process | operational/human (CCR12) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Permission-gating of evidence access | Low | High — identity/business-existence documents are sensitive; an under-permissioned view would be a real data-exposure risk | Yes — "operators without the permission cannot open evidence" is a direct acceptance criterion |
| Overdue-highlighting against the 3-business-day target (CCR12) | Low-Medium | Medium — see CCR12; the highlight is the only mechanism preventing a silent backlog at solo-founder scale | Yes — directly stated |

**Worth check**
Yes, proceed. This is the FR that makes BR03's entire verification promise operable rather than theoretical — a queue with no working interface would leave every submitted document stuck.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA048 — Opportunity review, stale queue, and taxonomy management
**Traces from:** FR48
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR12 unconfirmed/"source unreachable" Opportunity flags | in-module contract | No |
| FR13 Stale/Expired lifecycle states | in-module contract | No |
| Search Service (taxonomy changes applied within 5 minutes) | service (CCR02, CCR10) | No |
| Admin Console (operator content permission) | contract, shared platform console (ADR-012) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Alias preservation on taxonomy merge (CCR10) | Low-Medium | Medium — losing an alias on merge would silently break search for members who used the old term | Yes — "merging taxonomy terms preserves both labels as aliases" is a direct acceptance criterion |
| Bulk-action confirmation (Remind/Expire at scale) | Low | Medium — an unconfirmed bulk action against many records could mass-expire or mass-remind incorrectly | Yes — "bulk actions require confirmation with counts" is a direct acceptance criterion |
| 5-minute search-refresh SLA (CCR02) | Low-Medium | Low-Medium | Yes — directly stated |

**Worth check**
Yes, proceed. BR16's own framing ("founder/operator surfaces the source plan requires, grown alongside the product") is honest about this being operational necessity rather than a showcase feature — without it, FR11/FR12's Opportunity pipeline and FR04's taxonomy fallback would have no operator-side resolution path.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA049 — Commercial administration and audit review
**Traces from:** FR49
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR31 Promotion/Entitlement state and product/price version history | in-module contract | No |
| FR51 refund/credit processing (via gateway) | in-module contract → external gateway (CCR03) | No |
| Audit Service (searchable log) | service (CCR06) | No |
| Admin Console (commercial permission) | contract, shared platform console (ADR-012) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| No-override-of-verification/relevance/safety guarantee | Low | Critical if violated — this is the load-bearing separation-of-powers control between commercial operations and every trust-signal system in the module (cross-cutting rules 2, 3) | Yes — "no ability to change verification state, organic relevance, or safety decisions from this area" is a direct, testable negative acceptance criterion |
| Refund-exceeding-order-value rejection | Low | Medium — a bound failure here is a direct financial-integrity bug | Yes — directly stated |

**Worth check**
Yes, proceed. This is the operational control surface that keeps FR30/FR31/FR33/FR35's commercial capabilities auditable and reversible rather than opaque — necessary the moment any real money moves through the module.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA050 — Identity & Trust integration
**Traces from:** FR50
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Identity & Trust Service — session resolve, member id, display name, trust level, VerifiedCredential references | service, sync REST/cookie-resolve (CCR01), per ADR-004/019/021 | No (platform-owned shared service, not another business module) |
| `vyapar.members` member-link table (thin identity bridge) | data | No |
| ForKhatri web entrance (`platform/forkhatri-web`), Next.js Multi-Zones (ADR-020) | platform-level container | No |
| docs/ParentApp/07-tech-reqs.md TR10–TR16 (binding contract this FR consumes) | contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Identity & Trust Service unavailability (CCR01) | Low, per platform's own 99.9% target | Critical — every authenticated MOD01 action depends on this | See CCR01; FR50's own 15-minute read-only degradation window is the specific, already-designed mitigation |
| Fail-open regression (a future change accidentally falling back to a local/default member on resolve failure) | Low, given ADR-019's explicit fail-closed design and this FR's own "no Vyapar-owned credential, session, or authentication fallback exists" acceptance criterion | Critical if it occurred — this would silently reintroduce exactly the forked-identity risk ADR-004/021 and the product owner's 2026-09-14 standing correction were written to prevent | Yes — this negative case is a direct, explicit acceptance criterion, precisely because of the correction history recorded in FR50's own Review history |
| Member-link just-in-time creation correctness | Low-Medium | Medium — a bug here could either duplicate a member-link row or fail to create one on first entry, per `/MODULE-ARCHITECTURE-STANDARD.md` §5b's own "ensure the module's own member-link row exists" step | Partial — FR50's acceptance criteria cover the contract-level behaviour; the concrete `vyapar.members` schema/idempotent-creation logic is properly a Step 7a (ER Model) responsibility, flagged here since no MOD01 `architecture.md` exists yet to confirm it |

**Worth check**
Yes, proceed, exactly as corrected. This FR is the single most load-bearing dependency in the entire module — every other FR's "authenticated member" precondition traces back to it — and its 2026-09-14 correction (removing all Vyapar-owned auth surface) is a direct, necessary alignment with ADR-004/019/021 and the platform's "one ForKhatri identity" guardrail, not a scope reduction that weakens the module.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA051 — Direct payment-gateway integration (self-contained V1)
**Traces from:** FR51
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Licensed external payment gateway (hosted/tokenized checkout, signed webhooks) | external third-party service (CCR03) | No |
| FR30/FR31/FR33/FR35/FR54 (every FR built on this payment interface) | in-module contract | No |
| Internal payment interface / adapter (the explicit future-MOD06-swap seam) | in-module component (CCR13) | No |
| `.env`/config-driven gateway provider keys | data/config | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Webhook signature/idempotency/ordering (CCR03, grounded by 2026-09-14 research: duplicate delivery and out-of-order events are normal Razorpay/Cashfree-class gateway behaviour) | Medium — this is a documented, expected real-world pattern, not a rare edge case | High — an unhandled duplicate or out-of-order webhook could double-process a payment state or apply a refund before its originating charge is recorded | Yes at the acceptance-criteria level ("idempotency key per order," "signed webhooks verified," "duplicate webhooks are ignored via the idempotency key") — these are exactly the mitigations the grounded research confirms are necessary, not precautionary over-engineering; genuine end-to-end webhook-replay testing is a Step 10/11 concern once a sandbox gateway is wired up |
| Raw-card/credential exposure | Very Low, by design (hosted/tokenized checkout only) | Critical if it ever occurred — this would be a PCI-DSS-relevant, legally serious failure | Yes — "raw card or bank credentials shall never reach MOD01" is a direct, structural acceptance criterion (hosted checkout by construction, not a filter) |
| Future MOD06 adapter swap (CCR13) | Low now, deferred | Medium, deferred | Yes — the adapter-isolation acceptance criterion is the concrete, already-built swap seam |

**Worth check**
Yes, proceed. Self-contained V1 payment collection (BR17 DEC-002, resolving BLOCKER-002) is the correct call for a solo-founder-stage launch — it avoids a hard cross-module dependency on a MOD06 container that does not exist yet, while the adapter-isolation design keeps a future consolidation cheap rather than a rewrite.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA052 — Loosely coupled platform and adjacent-module contracts
**Traces from:** FR52
**Status:** Ready for Review
**Confidence:** Medium — matches the FR's own stated confidence; adjacent owners must accept the minimum-field contracts.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| (a) Search Service — index publish/remove | service (CCR02) | No |
| (b) Notification Service — template id + member id + parameters only | service (CCR05) | No |
| (c) Audit Service — shared event definition | service (CCR06) | No |
| (d) Object Storage — MOD01 access policy | service (CCR07) | No |
| (e) MOD05 Dashboard — read-only, privacy-filtered summary, no write path | contract (CCR08) | Yes (MOD05) |
| (f) MOD04 Counsel — explicit consented referral only | contract (CCR09) | Yes (MOD04) |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| (e) MOD05 contract enforcement — "rejected by contract" for a private-field request | Low | Critical if it ever accepted such a request — see CCR08 | Yes — "MOD05 requesting a private field → rejected by contract" is a direct, testable acceptance criterion |
| (f) MOD04 referral minimality | Low | Low — see CCR09 | Yes — directly stated |
| Idempotent-retry / dead-letter behaviour across all six contracts | Medium — six independent adjacent-service contracts is a lot of surface for one to quietly skip idempotency | Medium — a non-idempotent retry on any of the six could double-index, double-notify, or double-audit | Yes at the acceptance-criteria level ("every call shall carry an idempotency key where retried... fail without corrupting MOD01 state"), consistent with `/MODULE-ARCHITECTURE-STANDARD.md` §4b's general idempotent-mutation-endpoint pattern — but as with IA050, no MOD01 `architecture.md` yet exists to confirm which single component owns this uniformly across all six, rather than six independent implementations |
| No-direct-database-access-from-any-other-module guarantee | Low, structurally — `/ARCHITECTURE.md` ADR-002 already rejects shared-database access platform-wide | Critical if violated — this is the platform's own foundational data-isolation guarantee, not just a Vyapar-specific rule | Yes — "no direct database access from any other module" is a direct, testable acceptance criterion, and it is also structurally enforced by ADR-002's schema-per-module + no-cross-container-database-sharing design |

**Worth check**
Yes, proceed. This FR is the single place BR17's "one owner per entity, smallest practical loosely-coupled integration shape" principle is made concrete across all six adjacent contracts at once — exactly the kind of consolidating FR that prevents six independently-drifting integrations. The one real forward action is naming, in Step 7's `architecture.md`, which single MOD01 component owns idempotency/dead-letter handling for all six, rather than leaving it implicit.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA053 — Privacy notice, terms, and grievance contact
**Traces from:** FR53
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Versioned notice/terms content store (three languages) | data (CCR11) | No |
| FR39/FR40 Report and moderation-outcome screens (grievance channel display) | in-module contract | No |
| BR18 proportionate compliance posture | compliance/legal (CCR14) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Acceptance-record completeness before first publish/enquiry | Low-Medium | High — a member publishing or enquiring without a recorded acceptance would be a direct compliance gap under BR18's own proportionate posture | Yes — "acceptance recorded before first publish/enquiry" is a direct acceptance criterion |
| Re-prompt on new notice version, without deleting acceptance history | Low | Medium — losing historical acceptance records on a version rollback would break the auditability BR18/BR12 both require | Yes — "notice version rollback restores the prior text without deleting acceptance history" is a direct acceptance criterion |
| Three-language completeness at time of publish (CCR11) | Medium | Medium — a missing-language legal notice undermines the transparency this FR exists to provide | Partial — same CCR11 limitation as IA042 |

**Worth check**
Yes, proceed. This is the direct implementation of BR18's proportionate DPDP-aligned transparency posture — deliberately scoped to avoid a heavy legal gate while still making the notice/terms/grievance mechanism real and auditable.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA054 — Commercial disclosure and renewal transparency
**Traces from:** FR54
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR30/FR31/FR33/FR35 every paid-placement/renewal surface | in-module contract | No |
| Notification Service (3-day renewal reminder) | service (CCR05) | No |
| BR18 non-misleading-commercial-communication rule | compliance/legal (CCR14) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Universal "Sponsored" labelling across every paid surface | Medium — every future paid-surface addition must remember to apply this label; it is a discipline as much as a mechanism | High if a surface were missed — an unlabelled paid placement is a direct FTC/consumer-protection-style disclosure failure, and a direct cross-cutting-rule-3 violation in spirit | Yes at the FR-text level ("no paid surface is unlabelled" is a direct acceptance criterion), but this is exactly the kind of invariant that benefits from one shared rendering component every paid-card surface must use, not per-surface reimplementation — flagged for Step 7's architecture decisions the same way as IA020's explanation-signal-reuse concern |
| Renewal-reminder-gates-auto-renewal correctness | Low-Medium | Medium — the FR's own explicit rule ("renewal proceeds only if the reminder was sent successfully, else it is paused") is a real safeguard against silent, un-notified charging | Yes — directly stated as an acceptance criterion |

**Worth check**
Yes, proceed. This is the FR that makes every commercial capability in BR10/BR11 legally and ethically defensible rather than merely functional — a necessary companion to FR30/FR31/FR33/FR35, not a separable compliance afterthought.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## IA055 — Opportunity detail, member actions, and Activity
**Traces from:** FR55
**Status:** Ready for Review
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR10/FR28 poster trust context | in-module contract | No |
| FR20 "Why this?" entry | in-module contract | No |
| FR22 typed primary action (Enquire/Apply/Propose/Contact/Register) | in-module contract | No |
| FR38 "Not interested" reason feeding derived-preference proposals | in-module contract | No |
| FR39 Report action | in-module contract | No |
| External source website (Public/External "Apply on source website" link) | external third-party service | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Primary-action type-adaptation correctness (five typed actions plus two external-link variants) | Medium — seven distinct primary-action presentations on one screen is real branching complexity | Medium — showing the wrong action type (e.g., "Apply" on a Local Service item) would be a real usability/trust defect, though not a safety one | Yes at the acceptance-criteria level ("primary action adapted to type; External link only for Public/External items" is a direct, testable criterion) |
| External-link-unreachable flagging into FR48 | Low-Medium | Low-Medium — the correct behaviour (flag for operator review) is already specified | Yes — directly stated |
| Share-of-Removed-item blocking | Low | Medium — sharing a Removed item would circulate content Trust & Safety already determined should not distribute | Yes — "Share of a Removed item is blocked" is a direct acceptance criterion |

**Worth check**
Yes, proceed. This FR closed a real specification gap the Product Manager's own approver check found (2026-09-12 revision: "no FR specified the Opportunity detail screen... a gap UX would have hit immediately") — its addition was itself a correction to an incomplete decomposition, not new scope, and Step 3 (UX) and Step 4 (UI) both already built against it as Sealed.

**Approval:** Product Manager - [x] Approved - autonomous execution, 2026-09-14

---

## Overall worth check — is MOD01 Vyapar, as specified, still worth building?

This is the second and last "worth check" in the pipeline (the first ran at BR Step 1). Having now traced dependencies and risk across all 55 FRs, the question is asked honestly against the evidence above, `PRODUCT-GUARDRAILS.md`, and `01-business-requirements.md`'s own guardrail commitments — not rubber-stamped.

**Evidence for proceeding:**

- **No undeclared cross-module dependency surfaced across 55 FRs.** The only three module-level edges this module needs (MOD06 payment — superseded to optional/async for V1, MOD04 referral, MOD05 read summary) were already declared in `modules/modules.md` and already resolved in `/ARCHITECTURE.md`'s Dependency-resolution table. A 55-FR impact pass finding zero surprises here is itself evidence the Step 0/Step 0b decomposition was sound.
- **The module's stated guardrail invariants (cross-cutting rules 1–14 in `01-business-requirements.md`) are each independently, testably enforced by at least one FR**, not merely asserted: verification/paid/reputation separation (FR10, FR15, FR30, FR33, FR49), private-intent non-leakage (FR05, FR19, FR36), no-lead-list/no-bulk-contact-export (FR24, FR32), anti-retaliation (FR38, FR39), and the MOD05 privacy-filtered read boundary (FR52e) all have a direct, named acceptance criterion, not just a policy statement. That is the same standard `PRODUCT-GUARDRAILS.md` sets for the platform generally (its checkpoint question 4, "does it preserve trust/privacy?", and its "shared platform capabilities" and "no automated punitive action from a single signal" rows for the sibling Milavn module apply with equal force here and are honored, not narrowed).
- **The highest-severity risks found (CCR01 Identity & Trust outage, CCR03 payment-gateway webhook handling, CCR08 MOD05 privacy-contract breach) each already have a named, Sealed mitigation in the FR text itself**, not a mitigation this Step 6 pass had to invent — FR50's 15-minute degradation window, FR51's idempotency/signature verification (now grounded by real 2026-09-14 research on gateway behaviour rather than assumption), and FR52(e)'s contract-level rejection of private-field requests were all already specified before this analysis began. This pass found real risks worth naming, but not a single one that requires re-opening a Sealed FR's scope.
- **The module's own V1 scope discipline (BR03's lightweight verification, BR04's three-type wedge, BR10's V1-only commercial catalog) consistently chose the smaller, shippable option over the more elaborate one at every genuine fork** — exactly the "can a solo founder realistically build and operate it?" standard `PRODUCT-GUARDRAILS.md`'s standing checkpoint question 7 asks, applied here to a different module than the one that checklist was first written against, and it holds up.

**Evidence weighed but not disqualifying:**

- Two forward, non-blocking flags recur across multiple items rather than being one-off: (1) no MOD01 `architecture.md` exists yet to confirm several cross-cutting mechanisms (idempotency/dead-letter ownership across FR52's six contracts, one shared rate-limiting utility across FR22/FR25/FR39, one shared boost-mechanics implementation across FR30/FR35, one shared "Sponsored" rendering component across every paid surface) are built once rather than reinvented per FR — this is squarely Step 7/7a's job per `/MODULE-ARCHITECTURE-STANDARD.md`'s own stated purpose, not a Step 6 gap; (2) the manual-verification-operator bottleneck (CCR12) and the DPDP-proportionate-posture (CCR14) are both real, but both are explicit, Product-Manager-approved risk acceptances appropriate to an early-stage, founder-built product, recorded as such in BR03/BR18 themselves, not risks this pass discovered for the first time.
- Willingness-to-pay for FR33/FR35 (Business Workspace/Campaigns) is genuinely unproven, exactly as their own Confidence notes say — but they are correctly scoped as Should, not Must, so an unvalidated monetization hypothesis does not gate the module's core discovery/enquiry value.

**Verdict: Yes — MOD01 Vyapar as specified is still worth building as scoped.** The dependency/risk analysis strengthens rather than weakens the case: every genuinely high-severity risk already has a specified mitigation, no hidden cross-module coupling was found, and the module's guardrail commitments are enforced by name, not merely stated. Proceed to Step 7 (Tech Requirements) and Step 7a (ER Model), with the two forward flags above (component/idempotency ownership; shared-utility reuse for rate-limiting, boost mechanics, and Sponsored-label rendering) carried forward explicitly rather than left implicit.

## Closing note for Step 7

Step 7 (Tech Requirements) and Step 7a (ER Model) should treat the following as inputs from this pass, not rediscoveries:

1. **No `modules/MOD01-vyapar/architecture.md` exists yet.** Produce one per `/MODULE-ARCHITECTURE-STANDARD.md` §1 before or during Tech Reqs, applying: component decomposition from the module's own BR/FR language (§2); one process, modular internally, inside the Core Platform monolith (§3, per `/ARCHITECTURE.md`'s Vyapar row); schema-per-component inside the `vyapar` schema plus RLS for sensitive data (§4, with the two named RLS failure modes — non-owning DB role, `SET LOCAL` under pooling — confirmed explicitly); idempotent mutation endpoints (§4b) for FR22/FR25/FR30/FR39/FR51/FR52's queueable writes; one shared rate-limiting utility (§4c) for FR22/FR25/FR39's abuse-prone endpoints, not three independent counters; an authorization chokepoint (§5) for FR19's signal allow-list and FR34's role split; and the Identity Bridge pattern (§5b) for FR50.
2. **Name one owning component each** for: idempotency/dead-letter handling across FR52's six adjacent contracts (IA052); boost-mechanics reuse across FR30/FR35 (IA035); "Why this?" explanation-signal reuse tied to FR19's actual ranking signals (IA020); and universal "Sponsored" label rendering across every paid surface (IA054) — each was flagged above as a place `/MODULE-ARCHITECTURE-STANDARD.md`'s "same pattern as" divergence risk could otherwise recur.
3. **The `vyapar.members` identity-bridge table's exact schema and just-in-time-creation idempotency** (IA050) and the **member-deletion anonymization-vs-counterpart-preservation logic** (IA037) are both genuinely ER-Model-shaped decisions, not FR-level details — Step 7a should resolve both explicitly.
4. **CCR03/CCR04's grounded research findings** (payment-gateway webhook duplication/ordering; India SMS/OTP delivery reliability) should inform Step 8's STRIDE/performance thresholds for FR51 and FR07 directly, rather than Step 8 independently re-researching the same precedent.
