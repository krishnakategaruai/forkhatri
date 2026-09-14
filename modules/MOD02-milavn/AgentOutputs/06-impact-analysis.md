---
step: 06-impact-analysis
module: MOD02
status: Sealed
approver: Architect / Director
updated: 2026-09-13
items: "88 | approved: 88 | blockers: 0"
---

# 06 — Impact & Plan Analysis — MOD02 Milavn

## Revision history
| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-13 | Initial draft: dependency identification + risk assessment + worth check for all 88 Sealed FRs, cross-checked against `/ARCHITECTURE.md` (Sealed, mandatory pre-req) and `/modules/modules.md`'s declared dependency map. No existing repo code to grep (Milavn is greenfield — no module has reached Implementation yet), so dependency identification is against the *decided* architecture (container/service boundaries, ADRs) rather than actual code, per this step's own explicit instruction for that case. One genuine blocker found: FR065's Moderation Queue (UX20/UI20, added at Step 3/4 to close a gap Step 5 surfaced) was designed as a standalone screen, but `/ARCHITECTURE.md` ADR-012 requires every module's admin view to integrate against the Admin & Governance Console's shared plugin/view-registration contract — a contract that does not yet exist anywhere in this repository, and ADR-012 itself names Milavn as one of the two candidate modules (with Vyapar) expected to define it first. Raised as a blocker for Step 7 (Tech Reqs), not silently built around. | First Step 6 run for MOD02, one pass over all 88 FRs per the Loop discipline (re-reading each FR, `modules.md`'s dependency map, and `/ARCHITECTURE.md`'s relevant container boundaries fresh per item). |
| 2026-09-13 | Product Manager reviewed and approved the full Step 6 pass (product thesis, direction, and V1 capability selection all confirmed aligned with `/PRODUCT-GUARDRAILS.md`, newly created from this same review). BLOCKER-001 resolved by explicit PM/architect decision: the Admin & Governance Console plugin/view-registration contract will be defined now as a shared platform capability (Step 7), not built as a bespoke Milavn-only admin screen — because Vyapar, Mangaly, Milavn, and Samachar moderation will all need the same governance surface eventually, and building it once avoids N bespoke rebuilds (per the new standing guardrail "Shared platform capabilities" in `/PRODUCT-GUARDRAILS.md`). IA065 updated accordingly; all 88 items' approvals ticked; file Sealed. | User's explicit Step 6 approval message, acting as Product Manager, resolving the one open blocker. |

## Coverage check
| Parent FR | Impact items produced | Covered |
|---|---|---|
| FR001–FR088 | IA001–IA088 | Yes |

## Set-level quality gate
| Check | Result |
|---|---|
| Every FR analyzed | Pass — IA001–IA088, one per FR. |
| Cross-module dependencies checked against modules.md | Pass — every FR's dependency table explicitly marks cross-module (another business module) vs. platform-infrastructure (shared, no-module-owner container) vs. same-container (Core Platform monolith), per `/ARCHITECTURE.md`'s own explicit distinction. |
| No undeclared cross-module dependency found | Resolved — one undeclared/unresolved dependency was found (FR065's Moderation Queue needs the Admin & Governance Console's plugin/view-registration contract, ADR-012, not yet specified anywhere) and was raised as a blocker rather than quietly built around. The Product Manager has since made an explicit resolution decision (see Open blockers below, and `/PRODUCT-GUARDRAILS.md`'s "Shared platform capabilities" guardrail): define the shared contract now as a platform capability at Step 7, rather than a bespoke Milavn screen. This converts the item from an open blocker into a scoped Step 7 action item. |

## Open blockers
| ID | Item | Resolution | From |
|---|---|---|---|
| ~~BLOCKER-001~~ (resolved) | Admin & Governance Console plugin/view-registration contract does not exist yet, but FR065's Moderation Queue (UX20/UI20) needs to integrate against it per ADR-012 | **Resolved by explicit PM/architect decision, 2026-09-13:** define the Admin & Governance Console's plugin/view-registration contract now, as a shared platform capability, not as a bespoke Milavn-only admin screen — Vyapar, Mangaly, Milavn and Samachar moderation will all eventually need the same governance surface. Step 7 (Tech Reqs) must produce this contract as a platform-level technical requirement (naming Milavn as the first consumer, since Milavn's own pipeline reached this point first — Step 7 should still check whether Vyapar's pipeline has already progressed further before finalizing ownership), and FR065's Moderation Queue (UX20/UI20) must be redesigned in Step 7 to consume that contract rather than remain a standalone screen. | IA065 |

---

## IA001 — Minimal Identity, Locality, Interest and Language Profile
**Traces from:** FR001
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type (service/data/contract/module) | Cross-module? |
|---|---|---|
| Core Platform DB, `milavn` schema | Data store | No (same-container, per ADR-002) |
| Identity & Trust Service | Service (platform infra, no module owner) | No — shared platform service, not another business module |
| Shared i18n / translated-content model | Contract (platform-level, ADR-010) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Core Platform DB, `milavn` schema | Low (standard CRUD) | Medium (profile is the foundational entity every other FR reads) | Yes — TS001/TS002 cover success/failure |
| Identity & Trust Service | Low | High (auth outage blocks all onboarding) | Partially — TS001/TS002 assume auth already succeeded; no scenario tests Identity & Trust Service unavailability itself (a platform-level concern, appropriately owned by that service's own test suite, not Milavn's) |
| Shared i18n model | Low | Low (language rendering, not a blocking dependency) | Yes — TS003/TS004 |

**Worth check**
Yes, proceed as specified. No new risk surfaced beyond what BR01/FR001 already anticipated.

**Assumptions** — Identity & Trust Service's own availability/test coverage is out of this module's scope (owned by that service).
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA002 — Person-Level Language Preference
**Traces from:** FR002
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB, `milavn` schema (person-level preference field) | Data store | No |
| Shared i18n / translated-content model (ADR-010) | Contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| `milavn` schema field | Low | Low | Yes — TS003/TS004 |
| Shared i18n model | Low | Low — a rendering fallback exists per FR002's own Assumptions | Yes |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none beyond FR002's own.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA003 — Optional Profile Enrichment Never Gates Usability
**Traces from:** FR003
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB, `milavn` schema | Data store | No |
| Object Storage / CDN | Service (platform infra) | No — for photo/bio media upload |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| `milavn` schema | Low | Low | Yes — TS005/TS006 |
| Object Storage / CDN | Low | Medium (a media-upload outage should degrade gracefully, not block profile save) | Partially — TS005 covers the field-save path but no scenario explicitly tests Object Storage unavailability; flagged for Step 10 to add when Storage is actually integrated |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA004 — "Around You" Home Grouping
**Traces from:** FR004
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB, `milavn` schema (Activity/Occurrence data) | Data store | No |
| Embedded Postgres full-text/filter query (Search, ADR-007) | Service (platform infra, shared library) | No |
| MOD05 Dashboard (reads Milavn events for community-activity surfacing) | Module | **Yes** — declared in `modules.md`/`ARCHITECTURE.md` as a hard, in-process dependency (Dashboard → Milavn) |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| `milavn` schema query | Medium (query complexity grows with data volume) | Medium | Yes — TS007/TS008 |
| Embedded search/filter | Low (V1 scale is well under ADR-018's threshold) | Low | Partially — TS007 exercises grouping, not query performance at scale |
| Dashboard's read dependency | Low (in-process, same monolith — no network failure mode) | Medium (a schema change here without coordination could silently break Dashboard's read model) | No dedicated scenario exists for this cross-module read contract — flagged for Step 7 to define the exact read-model shape Dashboard consumes, so a future Milavn schema change doesn't silently break Dashboard |

**Worth check**
Yes, proceed as specified — with the flagged note that Step 7 must define the Dashboard-facing read contract explicitly (an internal Python interface per ADR-003's pattern rule), not leave it as an implicit schema dependency.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA005 — Four Complementary Discovery Modes
**Traces from:** FR005
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB, `milavn` schema | Data store | No |
| Embedded Postgres full-text search (Search, ADR-007/ADR-018) | Service (platform infra) | No |
| External map-tile provider (for Map mode) | External service | No (external system, not a ForKhatri module — falls outside `/ARCHITECTURE.md`'s System Context boundary as drawn; flagged as a new external dependency not currently named in the Context diagram) |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| `milavn` schema | Low | Low | Yes — TS009 |
| Embedded search | Low | Low (ADR-018 confirms Milavn's ranking is rule-based, not free-text-relevance, so this stays lightweight) | Yes |
| External map-tile provider | Medium (third-party service, own uptime/rate-limit risk) | Medium (Map mode degrades; Feed/Calendar/Search remain unaffected since they don't depend on it) | Yes — TS010 covers the fallback behavior |

**Worth check**
Yes, proceed — with a note for Step 7: the external map-tile provider is a genuinely new external dependency `/ARCHITECTURE.md`'s System Context diagram does not currently name. This is not a blocker (Map mode is P0 per Step 3 but the rest of Discovery functions without it), but Step 7/8 should add it to the architecture's external-system inventory rather than let it stay undocumented.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA006 — Six-Question Card Content
**Traces from:** FR006
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB, `milavn` schema | Data store | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| `milavn` schema | Low | Low (a rendering-contract concern, not a data-integrity one) | Yes — TS011/TS012 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA007 — Deterministic, Non-Popularity-Primary Ranking
**Traces from:** FR007
**Status:** Draft
**Confidence:** Medium — ranking-weight tuning is a genuine ongoing risk
surface even though the mechanism itself is simple.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB, `milavn` schema (locality, interests, trust, freshness fields) | Data store | No |
| BR07's trust taxonomy (FR030) | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| `milavn` schema fields | Low | Medium (a missing/null field could silently skew ranking) | Yes — TS013/TS014 |
| Trust taxonomy as ranking input | Low | Medium | Yes — TS065/TS066 cover this from FR033's side |

**Worth check**
Yes, proceed as specified. ADR-018 already confirms the deterministic, rule-based approach is architecturally appropriate at Milavn's V1 scale — no re-litigation needed.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA008 — Explainable "Why This?" Reason Per Item
**Traces from:** FR008
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR007's ranking factors | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| FR007 ranking factors | Low | Low (a generation failure excludes the item rather than corrupting the feed) | Yes — TS015/TS016 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA009 — Progressive-Disclosure Filters
**Traces from:** FR009
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB, `milavn` schema (filterable fields) | Data store | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| `milavn` schema | Low | Low | Yes — TS017/TS018 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA010 — Minimal Creation Form
**Traces from:** FR010
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB, `milavn` schema | Data store | No |
| Identity & Trust Service (creator identity) | Service (platform infra) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| `milavn` schema write | Low | Medium (this is the supply-side entry point — a write failure blocks all downstream Discovery content) | Yes — TS019/TS020 |
| Identity & Trust Service | Low | Medium | Covered indirectly via IA001's assessment |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA011 — Activity/Occurrence Data Distinction
**Traces from:** FR011
**Status:** Draft
**Confidence:** Medium — this is explicitly named (BR03 DEC-001) as the
highest-blast-radius data-model decision in this module; Impact Analysis
treats it with matching seriousness.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB, `milavn` schema (Activity, Occurrence tables/relationship) | Data store | No |
| Every FR that reads Activity/Occurrence data (participation, calendar, organizer tools) | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Activity/Occurrence data model | Medium (getting this wrong requires a costly remodel across many dependent FRs) | High (BR03 DEC-001 itself names this as the reason it was fixed at BR-level rather than left to FR/architecture) | Yes — TS021/TS022 directly test the aggregation and non-forced-wrapper rules |

**Worth check**
Yes, proceed as specified — this is exactly the kind of foundational data-model decision Step 7 (ER Model) must treat as its own highest-scrutiny item, per that step's own three-pass process, echoing BR03's own DEC-001 reasoning.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA012 — Edit and Cancel an Activity or Occurrence
**Traces from:** FR012
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR011's Activity/Occurrence model | Intra-module contract | No |
| Notification & Communication Service (cancellation alerts) | Service (platform infra, async via Message Broker) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| FR011 data model | Low (once FR011 itself is correctly built) | Medium | Yes — TS023/TS024 |
| Notification Service | Low (async, eventual delivery per ADR-006) | Medium (a cancellation notification is safety-relevant, per BR04) | Yes — TS033/TS034 cover this from FR017's side |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA013 — Progressive Advanced Configuration
**Traces from:** FR013
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB, `milavn` schema (capacity/co-host/recurrence/cover-image fields) | Data store | No |
| Object Storage / CDN (cover image) | Service (platform infra) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| `milavn` schema | Low | Low | Yes — TS025/TS026 |
| Object Storage | Low | Low (cover image is optional/decorative, not blocking) | Partially — no dedicated Object Storage failure scenario yet, same gap as IA003 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA014 — Immediate Shareable Link on Creation
**Traces from:** FR014
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR046–FR050's public-page model (BR11) | Intra-module contract | No |
| CDN / URL-shortening or canonical-URL scheme | Service (platform infra, implementation-stage) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Public-page model | Low | Medium (this is the entry point to the product's own growth mechanism, per BR11's Worth check) | Yes — TS027/TS028 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA015 — One-Tap Interested/Going
**Traces from:** FR015
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB, `milavn` schema (Participation record) | Data store | No |
| FR011's Activity/Occurrence model | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Participation write | Low | High (this is the single most-repeated write in the entire app, per UI08's own framing — any latency/reliability issue here is highly visible) | Yes — TS029/TS030, tagged E2E specifically because of this criticality |

**Worth check**
Yes, proceed as specified — and its E2E tagging at Step 5 is the right call given this dependency's criticality.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA016 — Full Attendance-Status Lifecycle
**Traces from:** FR016
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR015's Participation record | Intra-module contract | No |
| FR034's Reputation-signal computation (reads status transitions) | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Status state machine | Low | Medium | Yes — TS031/TS032 |
| Reputation read | Low | Low (read-only consumer) | Yes — TS067 covers this from FR034's side |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA017 — Organizer Update/Cancellation Reaches Participants
**Traces from:** FR017
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Notification & Communication Service | Service (platform infra, async via Message Broker) | No |
| FR015's Participation records (recipient list) | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Notification Service | Low (per ADR-006, at-least-once delivery via transactional outbox) | High (a dropped cancellation notification is a real-world safety issue — a participant could travel to a cancelled activity) | Yes — TS033/TS034, including the partial-failure scenario |

**Worth check**
Yes, proceed as specified. Flag for Step 7: confirm the transactional outbox pattern ADR-006 requires is actually implemented for this specific event type, given its safety relevance.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA018 — Scale-Gated Optional QR Check-In
**Traces from:** FR018
**Status:** Draft
**Confidence:** Medium — depends on client-side camera API support across
the device range this community product needs to serve.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Browser camera API (mobile web) | External/platform capability | No (browser capability, not a ForKhatri container) |
| Core Platform DB, `milavn` schema | Data store | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Browser camera API | Medium (mobile web camera access varies by browser/permission state) | Low (manual-entry fallback exists, per FR018's own design) | Yes — TS036 explicitly tests the fallback path |

**Worth check**
Yes, proceed as specified. The manual-entry fallback (already designed) is what makes this dependency's real-world variability a non-issue.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA019 — Non-Punitive No-Show Handling
**Traces from:** FR019
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR034's Reputation-signal computation | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Reputation signal write | Low | Medium (a coding error here could accidentally introduce an automated penalty, contradicting BR04's explicit anti-punitive Constraint) | Yes — TS037/TS038 directly test this boundary |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA020 — Create, Join and Leave a Circle
**Traces from:** FR020
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB, `milavn` schema (Circle, Membership) | Data store | No |
| Identity & Trust Service | Service (platform infra) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Circle/Membership writes | Low | Medium | Yes — TS039/TS040 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA021 — Circle Type Enforcement
**Traces from:** FR021
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR020's Circle model | Intra-module contract | No |
| FR004/FR011's authorization checks (reused for circle-scoped visibility) | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Circle type enum enforcement | Low | Medium (a type-enforcement bug directly risks a privacy leak) | Yes — TS041/TS042 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA022 — Organic Circle-Formation Suggestion
**Traces from:** FR022
**Status:** Draft
**Confidence:** Medium — the suggestion-trigger job is a new kind of
background/batch process this module hasn't otherwise needed.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR016's attendance history | Intra-module contract | No |
| A new scheduled/batch analysis job (co-participation pattern detection) | New component, implementation-stage | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Attendance history read | Low | Low | Yes — TS043/TS044 |
| New batch job | Medium (a new operational component — scheduling, failure/retry semantics — not yet specified) | Low (a missed/delayed suggestion is a lost opportunity, not a correctness/safety issue) | Partially — TS043/TS044 test the suggestion's *effect*, not the batch job's own reliability, which Step 7 should specify |

**Worth check**
Yes, proceed as specified — flagging for Step 7 that the batch-job's scheduling/failure semantics need explicit technical requirements, since this is a genuinely new kind of component for this module.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA023 — Circle Membership Never a Precondition
**Traces from:** FR023
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Every other FR's authorization check (must not reference circle membership) | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Cross-feature authorization logic | Low | Medium (a regression here could silently break the product for solo, non-circle participants) | Partially — TS045 covers the current state; TS046 explicitly notes this needs an ongoing regression check as new features are added, not a one-time test |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA024 — Community Memory Visible to Circle Members
**Traces from:** FR024
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB, `milavn` schema (aggregated stats) | Data store | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Stats aggregation query | Medium (aggregation cost grows with circle size/history) | Low (Should-priority, per Step 2's own refinement) | Yes — TS047/TS048 |

**Worth check**
Yes, proceed as specified — Should priority (already established at Step 2) remains appropriate; no new information changes that call.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA025 — Public Circle Visibility Follows Circle Type
**Traces from:** FR025
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR021's type enforcement | Intra-module contract | No |
| FR046–FR050's public-page model | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Type-to-visibility mapping | Low | Medium (privacy-boundary risk if miswired) | Yes — TS049/TS050 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA026 — Personal Calendar
**Traces from:** FR026
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR015's Participation records | Intra-module contract | No |
| MOD05 Dashboard (reads Milavn events for reminder surfacing) | Module | **Yes** — declared hard dependency, in-process |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Participation read | Low | Low | Yes — TS051/TS052 |
| Dashboard's reminder-surfacing read | Low (in-process) | Medium (same coordination concern as IA004) | Same gap as IA004 — flagged once, applies to both |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA027 — Circle Calendar
**Traces from:** FR027
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR020's Circle model, FR011's Activity/Occurrence model | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Scoped query | Low | Medium (cross-circle leakage risk) | Yes — TS053/TS054 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA028 — Organization and Community Calendars
**Traces from:** FR028
**Status:** Draft
**Confidence:** Medium — "Organization" as a full first-class entity is
not otherwise deeply modeled yet in this module's BR/FR set.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| A new Organization entity/scope (not otherwise detailed in BR01–BR20) | New component, implementation-stage | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Organization entity | Medium (this Should-priority scope was never given its own dedicated BR/FR depth — it rides along inside BR06's Calendar requirement) | Low (Should-priority; the app is fully usable without it) | Yes — TS055/TS056 test the behavior as specified, but Step 7 will need to actually define what an "Organization" is structurally, since no BR/FR gave it its own entity definition |

**Worth check**
Yes, proceed, with an explicit note for Step 7: since "Organization" as a schema entity was never independently specified (it appears only as a Calendar scope), Tech Reqs/ER Model should confirm whether it needs its own lightweight entity now or can be deferred until BR/FR work defines Organizations more fully — do not let Organization Calendar force a premature, under-specified Organization data model.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA029 — Public Calendar Includes Only Public-Marked Items
**Traces from:** FR029
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR021/FR025's visibility model | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Visibility-scoped query | Low | Medium (privacy-boundary risk) | Yes — TS057/TS058 |

**Worth check**
Yes, proceed as specified — Should priority remains appropriate.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA030 — Every Activity Resolves to Exactly One Trust Level
**Traces from:** FR030
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB, `milavn` schema (trust-level field) | Data store | No |
| Identity & Trust Service (Level-1/2 identity, the platform layer this module's Level-3-equivalent trust taxonomy sits on top of) | Service (platform infra) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Trust-level field | Low | Medium | Yes — TS059/TS060 |
| Identity & Trust Service layering | Low | Medium (this module's own trust taxonomy must stay clearly layered on top of, not duplicating, platform identity — per BR07's own DEC-001 boundary reasoning) | Covered conceptually by IA001; no dedicated cross-layer scenario exists yet, flagged for Step 7 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA031 — Trust Status Visibly Displayed
**Traces from:** FR031
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR030's trust-level field | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Rendering contract | Low | Low | Yes — TS061/TS062 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA032 — Organizations and Venues Share the Partner-Verified Path
**Traces from:** FR032
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR030's trust taxonomy | Intra-module contract | No |
| MOD01 Vyapar (potential source of an existing verified-business record, if a Venue is also a Vyapar business listing) | Module | Possibly — not currently declared in `modules.md`'s dependency map; flagged below |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Trust taxonomy reuse | Low | Low | Yes — TS063/TS064 |
| Potential Vyapar overlap | Low (Milavn's own BR07 treats Venue verification as independently achievable, not requiring Vyapar) | Low (if a venue happens to also be a Vyapar `ProfessionalListingProfile`, that's a data-quality nicety, not a functional dependency) | Not applicable — this module's own BRs never require the Vyapar link; noted only so Step 7 doesn't invent an undeclared dependency here |

**Worth check**
Yes, proceed as specified. No cross-module dependency actually exists here — Milavn verifies venues independently, matching `modules.md`'s own module-boundary decisions.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA033 — Trust Feeds Discovery Ranking
**Traces from:** FR033
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR007's ranking formula, FR030's trust level | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Ranking-input wiring | Low | Medium | Yes — TS065/TS066 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA034 — Reputation Signals Computed From Named Behaviours
**Traces from:** FR034
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Common reputation infrastructure, co-located in Identity & Trust Service (ADR-005) | Service (platform infra) | No |
| Core Platform DB, `milavn` schema (this module's own feedback/behaviour entities, read by the shared scoring engine) | Data store | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Shared reputation engine (Identity & Trust Service) | Medium (per ADR-005, any reputation-model change requires Identity & Trust Service deployment coordination, not an independent Milavn release) | Medium | Yes — TS067/TS068, but flagged: coordination process with Identity & Trust Service's own release cadence is a Step 7/9 operational concern, not fully testable at this module's own level |

**Worth check**
Yes, proceed as specified — with an explicit note that ADR-005's cross-service coordination requirement is real and should be surfaced in Step 7's technical requirements, not discovered at implementation time.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA035 — No Public Star Rating or Numeric Score
**Traces from:** FR035
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Every UI surface displaying organizer/participant information | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| UI-surface audit | Low | Medium (a violation here directly contradicts a named product invariant) | Yes — TS069/TS070, with TS070 explicitly flagged as an ongoing regression check |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA036 — Reputation Never Purchasable
**Traces from:** FR036
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| MOD06 Payment Services (future paid-tier features) | Module | **Yes** — declared as an optional, async, benefit-trigger-only edge; this FR's own concern is that the *reverse* direction (payment influencing reputation) must never exist |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Payment-to-reputation isolation | Low (no paid tier exists yet — BR18/BR17/BR16 are all deferred) | Medium (a future paid-tier feature could accidentally wire this incorrectly if this constraint isn't carried forward) | Yes — TS071/TS072, though genuinely testable only once a paid tier exists; recorded now as a standing gate |

**Worth check**
Yes, proceed as specified — this FR is a forward-looking guardrail more than an immediate build item, and is correctly scoped that way.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA037 — Reputation Surfaced Qualitatively, Never as a Raw Score
**Traces from:** FR037
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR034's reputation signals | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| API/UI contract | Low | Medium (an API leak of the raw score would be a real, if quiet, product-invariant violation) | Yes — TS073/TS074, including an explicit API-contract test |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA038 — Approximate Location Display Hierarchy
**Traces from:** FR038
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB, `milavn` schema (locality fields) | Data store | No |
| External geocoding/locality-resolution service (implied by City/Zone/Locality hierarchy) | External service | No — not currently named in `/ARCHITECTURE.md`'s System Context; flagged, same class of gap as IA005's map-tile provider |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| `milavn` schema | Low | Medium (privacy-relevant) | Yes — TS075/TS076 |
| External geocoding service | Medium | Medium (a resolution failure could fall back to a coarser-than-intended granularity, which is privacy-safe, or fail to resolve at all, which degrades UX but not privacy) | Not yet covered — flagged for Step 7/10 |

**Worth check**
Yes, proceed as specified, with the same external-dependency documentation note as IA005.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA039 — Explicit Consent Required for Precise Location
**Traces from:** FR039
**Status:** Draft
**Confidence:** Medium — no current feature actually exercises this path
(per FR039's own Confidence note).

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB, `milavn` schema (consent record) | Data store | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Consent record | Low | Low today (no feature uses it yet); High if a future feature bypasses it | Yes — TS077/TS078, recorded as a standing guardrail |

**Worth check**
Yes, proceed as specified — a guardrail worth having in place before it's needed, not after.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA040 — Private Circle/Attendance Hidden by Default
**Traces from:** FR040
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR021's circle type, FR056's attendee-list authorization | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Authorization checks | Low | High (privacy-boundary regression) | Yes — TS079/TS080 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA041 — User-Controlled Location-Sharing Precision
**Traces from:** FR041
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB, `milavn` schema (precision setting) | Data store | No |
| FR005/FR038's location-consuming features | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Setting enforcement across consumers | Medium (every location-consuming feature must independently respect this setting — an easy place for a future feature to forget) | Medium | Yes — TS081/TS082 |

**Worth check**
Yes, proceed as specified — flagging for Step 7 that this setting should be enforced centrally (a shared query helper), not independently re-checked by every consuming FR, to reduce the "a future feature forgets" risk.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA042 — Reason-Based Person Suggestion
**Traces from:** FR042
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR020's circle membership, FR016's participation history | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Suggestion-generation logic | Low | Low | Yes — TS083/TS084 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA043 — No Reason-Less Nearby-People List
**Traces from:** FR043
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR042's suggestion logic | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Component-contract enforcement | Low | Medium (a violation here reproduces the exact anti-pattern BR10 rejects) | Yes — TS085/TS086 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA044 — No Swipe/Match Mechanic
**Traces from:** FR044
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| MOD03 Mangaly (the module this boundary exists to stay distinct from) | Module | No direct technical dependency — this is a boundary/non-dependency, explicitly confirmed by `modules.md`'s own MOD02/MOD03 split |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Design-compliance drift over time | Medium (a future feature request could reintroduce this pattern without realizing the boundary reason) | High (a business-scope violation, not a bug) | Yes — TS087/TS088, with TS088 explicitly framed as an ongoing regression/design-review gate |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA045 — No Romantic/Matrimonial Framing
**Traces from:** FR045
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| All user-facing copy in People Discovery | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Copy audit | Low | High (business-boundary violation) | Yes — TS089/TS090 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA046 — Public Page Without Login
**Traces from:** FR046
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Web Client (React/TypeScript SPA), server-side rendering path | Contract (platform architecture, ADR-014's REST/OpenAPI pattern) | No |
| Identity & Trust Service (must NOT gate this page) | Service (platform infra) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Server-rendering path | Medium (this is a genuinely new rendering mode most of the rest of the app doesn't need — most screens are behind auth) | High (this page is the product's core growth mechanism, per BR11) | Yes — TS091/TS092, tagged E2E for exactly this criticality |

**Worth check**
Yes, proceed as specified — and flag for Step 7: confirm the Web Client's SPA architecture (ADR: React/TypeScript SPA) actually supports a genuinely server-rendered, crawlable public-page mode, since a pure client-side-rendered SPA would need a specific SSR/pre-rendering solution for this page type that most of the rest of the app (behind auth, not crawled) doesn't require.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA047 — Public Page Includes All Eight Required Content Elements
**Traces from:** FR047
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR030's trust status, FR010's activity data | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Content-contract enforcement | Low | Medium | Yes — TS093/TS094 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA048 — Public Pages Serve Crawlable, Server-Rendered Content
**Traces from:** FR048
**Status:** Draft
**Confidence:** Medium — same server-rendering architecture question as IA046.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Same server-rendering path as FR046 | Contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Server-rendering / SEO metadata | Medium (same architectural question as IA046) | High (SEO is a core growth-thesis dependency) | Yes — TS095/TS096 |

**Worth check**
Yes, proceed as specified — same Step 7 flag as IA046, not a separate one.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA049 — All Six Named Share Channels Are Reachable
**Traces from:** FR049
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Browser Web Share API / platform share-sheet | External/platform capability | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Web Share API support variance across browsers | Medium (not universally supported; graceful per-channel fallback needed) | Low (a missing channel degrades convenience, not a core function) | Yes — TS097/TS098 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA050 — A Non-Public Item Never Has a Reachable Public Page
**Traces from:** FR050
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR021/FR025's visibility model | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Visibility-gate enforcement on the public route | Low | High (a bypass here is a direct privacy breach, publicly reachable by URL) | Yes — TS099/TS100 |

**Worth check**
Yes, proceed as specified — this is one of the highest-severity checks in the whole module (a public URL bypass) and deserves emphasis at Step 8 (Security) too, not just here.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA051 — Important-Class Notifications Always Delivered
**Traces from:** FR051
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Notification & Communication Service | Service (platform infra, async via Message Broker) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Notification Service delivery guarantee | Low (ADR-006's at-least-once/outbox pattern) | High (safety-relevant) | Yes — TS101/TS102 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA052 — Useful-Class Reminders
**Traces from:** FR052
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Notification & Communication Service | Service (platform infra) | No |
| A scheduling component (reminder timing) | New component, implementation-stage | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Notification Service | Low | Low | Yes — TS103/TS104 |
| Scheduling component | Medium (new component, same class of risk as IA022's batch job) | Low | Yes — TS104 covers cancellation; scheduling reliability itself flagged for Step 7 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA053 — Social-Class Notifications
**Traces from:** FR053
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Notification & Communication Service | Service (platform infra) | No |
| FR040's private-membership visibility rules | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Notification Service | Low | Low | Yes — TS105 |
| Privacy-boundary interaction | Low | High (a Social notification is a genuinely new surface where a private-membership leak could occur — worth explicit attention) | Yes — TS106 directly tests this |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA054 — Opportunity-Class Notifications, User-Controlled Frequency
**Traces from:** FR054
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Notification & Communication Service | Service (platform infra) | No |
| FR007's ranking/matching logic (source of "new matching activity") | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Notification Service | Low | Low | Yes — TS107/TS108 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA055 — Milavn Governs What/When, Not Delivery Infrastructure
**Traces from:** FR055
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Notification & Communication Service's own published API/event contract | Service (platform infra) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Contract stability | Low | Medium (if the Notification Service's own contract changes, every module publishing to it is affected — a platform-level coordination risk, not unique to Milavn) | Yes — TS109/TS110 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA056 — Attendee List Visible to Organizer Only
**Traces from:** FR056
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR015's Participation records, Identity & Trust Service (organizer identity check) | Intra-module contract / Service (platform infra) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Authorization check | Low | High (privacy-boundary) | Yes — TS111/TS112 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA057 — An Organizer Update Reaches Every Current Participant
**Traces from:** FR057
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Notification & Communication Service, FR015's Participation records | Service (platform infra) / Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Recipient-list completeness | Low | Medium | Yes — TS113/TS114 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA058 — Capacity and Waitlist Management
**Traces from:** FR058
**Status:** Draft
**Confidence:** Medium — automatic promotion logic is a genuinely new
piece of business logic, per FR058's own Confidence note.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR015's Participation records | Intra-module contract | No |
| Notification & Communication Service (promotion notice) | Service (platform infra) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Promotion logic | Medium (concurrency risk — two withdrawals racing against one waitlist slot) | Low (Should-priority; a double-promotion or missed promotion is annoying, not safety-critical) | Yes — TS115/TS116, though neither explicitly tests the concurrent-withdrawal race condition; flagged for Step 7/10 |

**Worth check**
Yes, proceed as specified — Should priority remains appropriate; flag the concurrency edge case for Step 7's technical requirements.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA059 — Co-Organizer Delegation
**Traces from:** FR059
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Identity & Trust Service, FR056's authorization model | Service (platform infra) / Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Delegation/revocation logic | Low | Medium | Yes — TS117/TS118 |

**Worth check**
Yes, proceed as specified — Should priority remains appropriate.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA060 — Future AI Organizer Actions Respect Human Authorization Boundaries
**Traces from:** FR060
**Status:** Draft
**Confidence:** Medium — forward-looking guardrail; no AI Service exists
yet (ADR-009, deferred).

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| AI Service (deferred, ADR-009) | Service (platform infra, not yet built) | No |
| FR056/FR059's authorization model | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| AI Service (future) | Low today (doesn't exist); the risk is real only once it ships | High, when it applies | Yes — TS119/TS120, explicitly recorded as forward-looking |

**Worth check**
Yes, proceed as specified — appropriately scoped as a standing gate rather than active work, consistent with ADR-009's own deferral.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA061 — Report an Activity, User, Organization or Content
**Traces from:** FR061
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB, `milavn` schema (Report record) | Data store | No |
| Audit Service (report submission is a consequential, auditable event) | Service (platform infra, async via broker, ADR-011) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Report write | Low | Medium | Yes — TS121/TS122 |
| Audit Service | Low (ADR-011 requires at-least-once delivery) | Medium (a dropped audit event for a safety report is a compliance/accountability gap) | Not directly tested — flagged for Step 10 to add an explicit audit-event scenario |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA062 — Blocking a User Prevents Contact/Appearance
**Traces from:** FR062
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB, `milavn` schema (Block record) | Data store | No |
| FR042's People Discovery, notification-recipient filtering | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Block-enforcement across every touchpoint | Medium (must be checked at every contact/appearance surface, not just one) | High | Yes — TS123/TS124 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA063 — Organizer Identity, Location and Capacity Visible to RSVP'd Participants
**Traces from:** FR063
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR015's Participation records | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Visibility rule | Low | High (baseline physical-safety accountability) | Yes — TS125/TS126 |

**Worth check**
Yes, proceed as specified — this is a non-negotiable baseline per BR14; no scope change warranted.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA064 — Safety Guidelines for High-Risk Activities
**Traces from:** FR064
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR010's activity-tagging (high-risk flag) | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Tagging/display logic | Low | Medium | Yes — TS127/TS128 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA065 — Basic Moderation Queue, Scoped to Actual Usage
**Traces from:** FR065
**Status:** Draft — blocker resolved by explicit PM decision, action item scoped to Step 7
**Confidence:** Medium — the queue/case-detail mechanics themselves are
simple; the remaining work is architectural integration, not the feature logic.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Core Platform DB, `milavn` schema (Report/Case records) | Data store | No |
| FR061's Report records | Intra-module contract | No |
| **Admin & Governance Console** (ADR-012 — every module's admin view must integrate against its shared plugin/view-registration contract) | Platform infra (no module owner) | No — not another business module, but a required platform-level integration point per `/ARCHITECTURE.md`'s own explicit rule |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Report/Case records | Low | Medium | Yes — TS129/TS130 |
| **Admin & Governance Console plugin contract** | **Certain — the contract does not exist anywhere in this repository yet** | **High — building UX20/UI20 as a bespoke standalone admin screen (as currently designed) would need rework once the real console contract is defined, and ADR-012 explicitly names Milavn as one of the two candidate modules (with Vyapar) expected to define that contract first** | No — this is precisely the kind of undeclared/unresolved dependency this step exists to catch; not a testable gap but an architectural one |

**Worth check**
**Yes, with a scope change: this FR is still worth building, but not exactly as UX20/UI20 currently specify it.** FR065's Moderation Queue must be redesigned against the Admin & Governance Console's plugin/view-registration contract (ADR-012), not as an independent standalone screen. This does not block the rest of Milavn's build — every other FR proceeds independently.

**Assumptions** — Whether Vyapar or Milavn actually ships the first admin view first is not yet evidenced (unlike Mangaly's build-order, which `/ARCHITECTURE.md` ADR-016 confirms with direct evidence) — Step 7 should check Vyapar's own pipeline status before finalizing which module owns authoring the shared contract; either way, Milavn consumes it.

**Decisions**
- **DEC-001 (2026-09-13):** Per explicit Product Manager decision (see `/PRODUCT-GUARDRAILS.md`, "Shared platform capabilities" guardrail), BLOCKER-001 is resolved by defining the Admin & Governance Console's plugin/view-registration contract now, as a shared platform capability at Step 7, rather than building a bespoke Milavn-only admin screen. Rationale: Vyapar, Mangaly, Milavn, and Samachar moderation will all eventually need the same governance surface — building it once avoids repeated bespoke rework. FR065's Moderation Queue (UX20/UI20) will be redesigned in Step 7 to consume this shared contract.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA066 — Optional Post-Event Feedback Prompt
**Traces from:** FR066
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR016's Attended status | Intra-module contract | No |
| Core Platform DB, `milavn` schema (Feedback record) | Data store | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Trigger timing (on Attended) | Low | Low | Yes — TS131/TS132 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA067 — Feedback Feeds Reputation Internally, Never Publicly
**Traces from:** FR067
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR034's reputation-signal computation | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Internal-only data flow | Low | Medium (a leak here compounds both BR08's and BR15's privacy Constraints) | Yes — TS133/TS134 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA068 — Feedback Never a Precondition
**Traces from:** FR068
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Every other capability's own gating logic (must not reference feedback state) | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Cross-feature gating audit | Low | Medium | Yes — TS135/TS136, with TS136 flagged as an ongoing regression check |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA069 — No Automated Penalty From Feedback Alone
**Traces from:** FR069
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR065's moderation path (the only legitimate route to a consequential action) | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Anti-automated-penalty logic | Low | Medium | Yes — TS137/TS138 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA070 — External Event Ingestion, Normalization and Deduplication (Deferred)
**Traces from:** FR070
**Status:** Draft
**Confidence:** Low — BR16 explicitly deferred; no dependency analysis is
meaningful before a real design exists.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Not applicable — deferred | — | — |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Not applicable — deferred | — | — | TS139 (placeholder) |

**Worth check**
Not evaluated — deferred per BR16's own Could/deferred status; re-run this Impact Analysis item for real once BR16 is prioritized, since a real dependency (external event source APIs, none currently named in `/ARCHITECTURE.md`'s System Context) will exist at that point and needs proper analysis, not a placeholder.

**Assumptions** — "Deferred" means not yet scheduled, not never.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA071 — External Events Reuse the Existing Trust Taxonomy (Deferred)
**Traces from:** FR071
**Status:** Draft
**Confidence:** Low — same deferred caveat as IA070.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Not applicable — deferred | — | — |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Not applicable — deferred | — | — | TS140 (placeholder) |

**Worth check**
Not evaluated — deferred, same as IA070.

**Assumptions** — same as IA070.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA072 — Natural-Language Intent Mapping (Deferred)
**Traces from:** FR072
**Status:** Draft
**Confidence:** Low — BR17/AI Service explicitly deferred (ADR-009).

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| AI Service (deferred, ADR-009 — not yet built) | Service (platform infra) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| AI Service | Not applicable until built | Not applicable | TS141 (placeholder) |

**Worth check**
Not evaluated — deferred, consistent with ADR-009's own deferral of the AI Service container itself. Re-run once AI Service exists.

**Assumptions** — same pattern as IA070.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA073 — AI-Initiated Actions Authorized and Attributable (Deferred)
**Traces from:** FR073
**Status:** Draft
**Confidence:** Low — same deferred caveat as IA072.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| AI Service (deferred) | Service (platform infra) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| AI Service | Not applicable | Not applicable | TS142 (placeholder) |

**Worth check**
Not evaluated — deferred, same as IA072.

**Assumptions** — same pattern as IA070.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA074 — Surface Local-Business Demand to Vyapar (Deferred)
**Traces from:** FR074
**Status:** Draft
**Confidence:** Low — BR18 explicitly deferred.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| MOD01 Vyapar | Module | **Yes — but not currently declared anywhere in `modules.md`'s dependency map or `/ARCHITECTURE.md`'s resolved edges** |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Undeclared Milavn→Vyapar edge | Not applicable until BR18 is prioritized | Would be Medium once real (a new cross-module edge needs its own integration-pattern resolution, per the same process `/ARCHITECTURE.md` already applied to every other edge) | TS143 (placeholder) |

**Worth check**
Not evaluated — deferred. Flagging now, while deferred, so it isn't missed later: **when BR18 is prioritized, this specific edge (Milavn → Vyapar, demand-signal surfacing) will need its own entry in `/ARCHITECTURE.md`'s dependency-resolution table**, the same way every other cross-module edge already has one — it does not currently exist there because BR18 didn't exist when `/ARCHITECTURE.md` was written.

**Assumptions** — same pattern as IA070.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA075 — Sponsorship Labelling and Payment-Boundary Compliance (Deferred)
**Traces from:** FR075
**Status:** Draft
**Confidence:** Low — BR18 explicitly deferred.

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| MOD06 Payment Services | Module | **Yes — already declared** (Milavn → Payment Services, optional, async benefit-trigger events, per `modules.md`/`ARCHITECTURE.md`) |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Payment Services edge | Not applicable until BR18 is prioritized | Low — the existing async, optional edge pattern already covers this class of interaction; no new edge type is needed | TS144 (placeholder) |

**Worth check**
Not evaluated — deferred. Unlike IA074, this dependency is already correctly declared and resolved in `/ARCHITECTURE.md` (the existing benefit-trigger event pattern), so no new architecture work is anticipated when BR18 is eventually prioritized — a smaller gap than IA074's.

**Assumptions** — same pattern as IA070.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA076 — Splash/Launch Screen
**Traces from:** FR076
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Identity & Trust Service (auth-state check) | Service (platform infra) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Identity & Trust Service | Low | Medium (every user's first interaction) | Yes — TS145/TS146/TS147 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA077 — Sign Up
**Traces from:** FR077
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Identity & Trust Service (account creation, credential storage) | Service (platform infra) | No |
| Notification Service (OTP delivery, via Identity & Trust) | Service (platform infra) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Identity & Trust Service | Low | High (ADR-004 names this the platform's single highest-availability requirement) | Yes — TS148/TS149/TS150, including the researched rate-limiting edge case |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA078 — Log In
**Traces from:** FR078
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Identity & Trust Service | Service (platform infra) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Identity & Trust Service | Low | High | Yes — TS151/TS152 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA079 — Forgot/Reset Password
**Traces from:** FR079
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Identity & Trust Service, Notification Service | Service (platform infra) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Identity & Trust Service | Low | Medium | Yes — TS153/TS154 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA080 — OTP / Phone-Email Verification
**Traces from:** FR080
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Identity & Trust Service, Notification Service (OTP delivery) | Service (platform infra) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Identity & Trust Service / Notification Service | Low | High (a brute-forceable OTP endpoint without rate-limiting is a real, researched security risk — see TS150/TS157/TS158) | Yes — TS155–TS158, directly addressing the researched OTP-flooding and brute-force risks |

**Worth check**
Yes, proceed as specified — flagging for Step 7/8 that OTP rate-limiting/lockout must be implemented at the Identity & Trust Service layer (it is a platform capability, not something Milavn builds itself), consistent with FR080's own Assumptions.

**Assumptions** — none beyond FR080's own.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA081 — Location Permission Priming
**Traces from:** FR081
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Browser Geolocation API | External/platform capability | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Browser Geolocation API | Medium (permission variance across browsers/devices) | Low (manual fallback exists) | Yes — TS159/TS160 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA082 — Notification Permission Priming
**Traces from:** FR082
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Browser/OS push-notification permission API | External/platform capability | No |
| Notification Service (in-app fallback) | Service (platform infra) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Push permission API | Medium | Low (in-app inbox fallback exists) | Yes — TS161/TS162 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA083 — Main Navigation Shell
**Traces from:** FR083
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Web Client (React/TypeScript SPA) routing | Contract (platform architecture) | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| SPA routing | Low | Medium | Yes — TS163/TS164 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA084 — Generic Empty, Offline and Error State Handling
**Traces from:** FR084
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Every FR's own success/failure API contract (this pattern consumes, not produces, those contracts) | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Cross-cutting pattern consistency | Medium (applies to every screen; easy for one to drift from the pattern) | Low | Yes — TS165/TS166 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA085 — Account and Profile Settings Screen
**Traces from:** FR085
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR002, FR041's own settings data | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Settings aggregation | Low | Low | Yes — TS167/TS168 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA086 — Notification Inbox Screen
**Traces from:** FR086
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR051–FR054's notification classes | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Class-aggregation display | Low | Medium | Yes — TS169/TS170 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA087 — Help/Support Screen
**Traces from:** FR087
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| FR061's reporting mechanism (reused for "Contact support") | Intra-module contract | No |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Reuse of Report mechanism | Low | Low | Yes — TS171/TS172 |

**Worth check**
Yes, proceed as specified.

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13

---

## IA088 — Logout and Delete-Account Confirmation
**Traces from:** FR088
**Status:** Draft
**Confidence:** High

**Dependency identification**
| Dependency | Type | Cross-module? |
|---|---|---|
| Identity & Trust Service (session termination, account-deletion mechanics) | Service (platform infra) | No |
| Every module's own data (a deletion must eventually be reflected everywhere the member has data — Vyapar, Dashboard, etc., if this member also uses those modules) | Platform-wide concern | Potentially, at the platform level, though not something Milavn itself orchestrates |

**Risk assessment**
| Dependency | Likelihood | Severity | Existing test coverage adequate? |
|---|---|---|---|
| Identity & Trust Service | Low | High (account deletion is the single most irreversible action in the app, per UI17/UX17's own framing) | Yes — TS173/TS174/TS175, with TS174 tagged E2E for exactly this reason |
| Platform-wide deletion propagation | Medium (a member using multiple ForKhatri modules needs their deletion to actually reach every module's data, not just Milavn's) | High | Not testable at Milavn's own module level — this is a platform-wide (Identity & Trust Service-orchestrated) concern that should be verified at the platform/integration level, not duplicated per-module |

**Worth check**
Yes, proceed as specified — flagging for Step 7/8 that the actual cross-module data-deletion orchestration (once a member deletes their account) is a platform-level (Identity & Trust Service) responsibility `/ARCHITECTURE.md` should own explicitly, not something each module re-solves independently; Milavn's own FR088 correctly scopes itself to the confirmation UI and its own data only.

**Assumptions** — none beyond FR088's own.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Architect / Director — [x] Approved — krishna kategaru, 2026-09-13
