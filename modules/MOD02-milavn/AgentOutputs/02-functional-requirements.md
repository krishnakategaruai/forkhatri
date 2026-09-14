---
step: 02-functional-requirements
module: MOD02
status: Sealed
approver: Product Manager
updated: 2026-09-13
items: "88 | approved: 88 | blockers: 0"
---

# 02 — Functional Requirements — MOD02 Milavn

## Revision history
| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-12 | Initial draft: 75 FRs decomposed from all 18 Sealed BRs in `01-business-requirements.md`. Each BR group is ordered so its first FR is a thin, demoable slice and later FRs layer enrichment/edge cases/constraints on top, matching the pattern already established for MOD03 Mangaly's Step 2 output. BR16–BR18 (Could, explicitly deferred) each get a small, forward-looking FR pair rather than full decomposition, since their own BRs are traceability placeholders, not near-term build commitments. | First Step 2 run for MOD02, one pass over all 18 BRs per the Loop discipline (re-reading each BR in full, checking terminology consistency against FRs already written, and researching only where a BR was genuinely silent on a settled industry behavior). |
| 2026-09-12 | Second, critical approver-perspective review pass (mirroring the same second pass already run on the BR file). Found and fixed a real, garbled error in this file's own Set-level quality gate "Prioritized" row (self-contradicting Must/Could counts, corrected). More substantively, cross-checked every FR's inherited Must priority against the source thesis's own explicit §58 MVP boundary rather than trusting each parent BR's Priority label as automatically transitive to every one of its FRs: found four FRs whose specific capability is absent from §58's curated MVP list even though their parent BR (Must) covers other, genuinely-MVP capability alongside them — FR024 (Community Memory stats, thesis itself calls this "a powerful **long-term** feature," §35), FR029 (a standalone public calendar view, distinct from BR11's per-item public pages), FR058 (capacity/waitlist automation) and FR059 (co-organizer delegation, both drawn from persona description §8.4/§8.5 rather than §58's terse "attendee list, event updates" Organizer MVP bullet). Refined all four from Must to Should — each BR's other, genuinely-MVP FRs remain Must and are fully functional without them, per the Priority field's own "inherited/refined from parent BR" convention (Step 2 agent definition). No FR was found duplicating another, contradicting its parent BR, or missing a failure/edge outcome. | Second, critical approver-perspective review pass — krishna kategaru, 2026-09-12. |
| 2026-09-12 | Step 3 (UX) screen-inventory pass added 13 prerequisite-screen FRs (FR076–FR088) this file had no coverage for: Splash/Launch, Sign Up, Log In, Forgot Password, OTP Verification, Location and Notification permission priming, Main Navigation Shell, generic Empty/Offline/Error state handling, Account/Profile Settings, Notification Inbox, Help/Support, and Logout/Delete-Account confirmation. None trace to a Milavn business capability BR directly (the underlying identity/auth infrastructure is Common Platform per `modules.md` Shared Concerns, and this pipeline has no separate Common-Platform-tracked module) — each states this plainly in its own Intent per the Step 3 agent's explicit instruction, traced to the nearest sensible existing BR (mostly BR01) rather than left as a gap, consistent with "a mobile app without a login screen is not shippable." | Step 3 screen-inventory pass — krishna kategaru, 2026-09-12. |
| 2026-09-13 | FR065's `Traced to:` moved from UX15 to UX20 — Step 5's test-scenario pass found no moderator-facing screen had ever been designed for FR065's own "basic review queue," traced to an error in BR14's own "Affected users and systems" line (now corrected in `01-business-requirements.md`), and Step 3 added UX20 to close it. No change to FR065's own requirement text. | Traceability update following the BR14 correction and new UX20 — krishna kategaru, 2026-09-13. |
| 2026-09-13 | Authentication ownership corrected: login/auth is owned solely by the parent ForKhatri platform (one source of truth); FR076–FR080 and FR088 are marked platform-owned (hand-off briefs, not Milavn build scope); Milavn keeps only its post-login routing, onboarding (FR001–FR003) and profile settings (FR085). Nothing was deleted — the original text stays for traceability. | User correction "User login, authentication will be done by one source of truth, the parent ForKhatri" — krishna kategaru. |

## Coverage check
| Parent BR | FRs produced | Covered |
|---|---|---|
| BR01 — Minimal Identity, Locality, Interest and Language Profile | FR001–FR003 | Yes |
| BR02 — Contextual Local Discovery, With Explainable Ranking | FR004–FR009 | Yes |
| BR03 — Effortless Activity and Event Creation, With Recurrence | FR010–FR014 | Yes |
| BR04 — Participation and Attendance Lifecycle | FR015–FR019 | Yes |
| BR05 — Circles as an Emergent Community Primitive | FR020–FR025 | Yes |
| BR06 — First-Class Calendar Across Scopes | FR026–FR029 | Yes |
| BR07 — Visible Trust Taxonomy | FR030–FR033 | Yes |
| BR08 — Earned Reputation Signals | FR034–FR037 | Yes |
| BR09 — Privacy-First Location and Personal Information Handling | FR038–FR041 | Yes |
| BR10 — Contextual People Discovery, Distinct From Dating | FR042–FR045 | Yes |
| BR11 — Public, No-Login-Required Shareable Pages | FR046–FR050 | Yes |
| BR12 — Purposeful, Non-Spam Notifications | FR051–FR055 | Yes |
| BR13 — Progressive Organizer Tooling | FR056–FR060 | Yes |
| BR14 — Reporting, Blocking and Baseline Safety | FR061–FR065 | Yes |
| BR15 — Post-Event Feedback and Community-Engagement Signals | FR066–FR069 | Yes |
| BR16 — Future External Event Ecosystem (Could, deferred) | FR070–FR071 | Yes |
| BR17 — Future AI-Native Planning and Organizing (Could, deferred) | FR072–FR073 | Yes |
| BR18 — Future Local Commerce Layer (Could, deferred) | FR074–FR075 | Yes |
| (prerequisite screens, added by Step 3 — see Revision history) | FR076–FR088 | Yes |

## Set-level quality gate
| Check | Result |
|---|---|
| Comprehensive — every BR covered | Pass — no blank rows above; 88 FRs across 18 BRs plus 13 Step-3-added prerequisite screens. |
| Consistent | Pass — shared actor vocabulary (Participant, Circle Member, Activity Creator, Circle/Event Organizer, Organization, Venue) and shared cross-cutting rules (visible-trust-not-score, earned-not-bought reputation, deterministic V1 ranking) applied identically everywhere they recur. |
| Prioritized | Pass — 75 Must, 7 Should (FR024/FR029/FR058/FR059, each refined down from their Must-priority parent BR on second review; plus FR079/FR082/FR087, recovery-path/permission-priming/help screens that are real but not critical-path), 6 Could (FR070–FR075, inherited from their explicitly-deferred parent BRs, BR16–BR18). |
| No duplicates | Pass — BR07/BR08's Trust-vs-Reputation boundary and BR08/BR15's Reputation-vs-Feedback boundary are each kept distinct at the FR level, matching their parent BRs' own deliberate split. |
| Build-sequencing | Pass — within every BR, the first FR in that group is the thin, demoable slice; later FRs layer enrichment, edge cases, and cross-cutting constraints on top. |

## Open blockers
| ID | Item | What's needed | From |
|---|---|---|---|
| (none) | — | — | — |

No FR is fully Blocked. The following carry Medium/Low Confidence with an
explicit note rather than an invented resolution, each traceable to a
specific open point already flagged at the BR level: FR007/FR008 (BR02's
deferred exact ranking weights); FR013 (BR03's deferred advanced-config
field set); FR018 (BR04's deferred QR check-in threshold — "large" vs.
"small" event); FR022 (BR05's deferred circle-suggestion trigger
threshold); FR066 (BR15's deferred exact feedback question set);
FR070–FR075 (BR16–BR18's entire deferred future scope). These are
downstream design or explicitly-future-phase items, not research
questions the `researcher` subagent could resolve by lookup, consistent
with the BR file's own honest-gate convention.

---

## FR001 — Create Minimal Usable Profile
**Traces from:** BR01
**Traced to:** UX02 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a new participant completes onboarding, the system shall persist a
usable profile once locality and at least one interest are provided, and
shall reject completion naming any still-missing required field.

**Intent**
First demoable slice: a participant has a real, saved profile Discovery
can rank against.

**Success outcome**
Profile saves with locality and interests recorded; participant reaches
the home ("Around You") experience.

**Failure / edge outcome**
Missing locality or zero interests blocks completion, with the specific
gap named.

**Acceptance criteria**
- [ ] Onboarding completes once locality + at least one interest exist.
- [ ] Onboarding is blocked, with the specific missing item named, otherwise.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR01.
**Assumptions** — exact interest-category taxonomy is implementation-stage (BR01 Assumptions).

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR002 — Set and Update Person-Level Language Preference
**Traces from:** BR01
**Traced to:** UX02 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a participant sets or changes their language preference (English,
Hindi, or Telugu at V1), the system shall attach it to that person's own
record — not the app session or device alone — and shall make it
available as the input every other rendering surface reads for that
person's content.

**Intent**
Covers BR01's language-preference Constraint, keeping this Milavn-owned
fact distinct from the Common Platform i18n infrastructure that renders it.

**Success outcome**
Preference persists on the person's record and is readable by any
rendering surface (Discovery cards, circle pages, notifications).

**Failure / edge outcome**
An unset preference does not block FR001's profile completion — it
defaults to a platform-level fallback.

**Acceptance criteria**
- [ ] Preference is stored on the person's own record, not only session/device.
- [ ] An unset preference never blocks profile creation or any other capability.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR01.
**Assumptions** — the rendering/translation mechanism itself is Common Platform infrastructure (`ARCHITECTURE.md` ADR-010); this FR only fixes that the preference exists as person-level data.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR003 — Optional Profile Enrichment Never Gates Usability
**Traces from:** BR01
**Traced to:** UX02 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a participant adds optional profile detail (photo, bio, additional
interests), the system shall accept it without ever requiring it as a
precondition for any capability already available from FR001's minimum
state.

**Intent**
Enforces BR01's two-state (minimum-to-use vs. optional-enrichment) model —
closes this BR's group.

**Success outcome**
A participant with only locality + one interest uses Discovery, Circles,
and Activities identically to one with a fully filled-out profile.

**Failure / edge outcome**
Any feature found gating on optional-field completeness is a defect
against BR01's explicit rejection of a Mangaly-style completeness gate.

**Acceptance criteria**
- [ ] No capability available at FR001's minimum state is restricted by missing optional fields.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR01 DEC-001.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR004 — "Around You" Home Grouping
**Traces from:** BR02
**Traced to:** UX04 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a participant opens the home experience, the system shall group
locally-relevant activities/events into Today, Tomorrow, and This Weekend
sections, using the participant's locality and interests (FR001) as input.

**Intent**
First demoable Discovery slice — a real, working home screen.

**Success outcome**
Participant sees grouped, locally-relevant results immediately on open.

**Failure / edge outcome**
Zero results in a time group displays an explicit empty state, not a
blank/broken section.

**Acceptance criteria**
- [ ] Home groups results into Today/Tomorrow/This Weekend.
- [ ] An empty time group shows an explicit empty state.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR02.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR005 — Four Complementary Discovery Modes
**Traces from:** BR02
**Traced to:** UX05 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a participant is in Discovery, the system shall let them switch
between Feed, Calendar, Map, and Search modes without losing their active
locality/interest context.

**Intent**
Layers browsing flexibility onto FR004's default feed view.

**Success outcome**
Switching modes preserves locality/interest filtering across all four.

**Failure / edge outcome**
A mode switch that resets filters silently is a defect.

**Acceptance criteria**
- [ ] All four modes are reachable from Discovery.
- [ ] Locality/interest context persists across mode switches.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR02.
**Assumptions** — Map mode's exact geographic-intelligence depth is bounded by BR02's "no complex map intelligence" exclusion.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR006 — Six-Question Card Content
**Traces from:** BR02
**Traced to:** UX04 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When the system renders a Discovery card, it shall display what the
activity is, when it happens, where, who is hosting, how many are going,
and why it was surfaced to this viewer.

**Intent**
Fixes the minimum content contract every card must satisfy, regardless of
which discovery mode surfaced it.

**Success outcome**
Every card answers all six questions without requiring a tap-through.

**Failure / edge outcome**
A card missing any of the six elements is a defect, not an acceptable
simplification.

**Acceptance criteria**
- [ ] Every rendered card includes all six named elements.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR02.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR007 — Deterministic, Non-Popularity-Primary Ranking
**Traces from:** BR02
**Traced to:** UX04 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** Medium — exact ranking weights are implementation-stage
(BR02 Confidence note).

**Requirement (ISO 29148 form)**
When the system ranks Discovery results, it shall weigh locality/distance,
time fit, interest match, circle relevance, social relevance, trust
(BR07), availability, and freshness using a deterministic, rules-based
formula, and shall never use attendee-count/popularity as the primary
factor.

**Intent**
Core ranking logic layered onto FR004/FR005's browsing surfaces.

**Success outcome**
Ranking order reflects the named relevance factors, not raw popularity.

**Failure / edge outcome**
Popularity data found driving primary rank order is a defect.

**Acceptance criteria**
- [ ] Ranking's primary weighted factors exclude popularity.
- [ ] Ranking logic is rules-based, with no ML component in V1.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (exact weights
deferred) · Singular ✓ · Feasible ✓ · Verifiable ~ (same reason) ·
Correct ✓ · Conforming ✓

**Decisions** — none beyond BR02 DEC-001.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR008 — Explainable "Why This?" Reason Per Item
**Traces from:** BR02
**Traced to:** UX04 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** Medium — depends on FR007's ranking factors being resolved
enough to generate a concrete reason string.

**Requirement (ISO 29148 form)**
When the system surfaces a ranked item to a viewer, it shall attach a
concrete, one-line reason drawn from the actual ranking factors that
placed it (e.g. "Because you follow badminton," "3 people from your
circles are going"), and shall never surface an item with no stated
reason.

**Intent**
Fulfils FR006's "why" element with real, factor-grounded content rather
than a placeholder.

**Success outcome**
Every surfaced item's reason traces to an actual ranking input.

**Failure / edge outcome**
A generic, non-specific reason ("Recommended for you") is treated as a
defect, not an acceptable fallback.

**Acceptance criteria**
- [ ] Every surfaced item's reason names a specific, real ranking factor.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ~ (depends on FR007) · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR02.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR009 — Progressive-Disclosure Filters
**Traces from:** BR02
**Traced to:** UX05 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a participant refines Discovery results, the system shall offer
common filters (date, distance, category, free/paid, public/community/
circle) by default and shall keep less-common filters hidden until
requested, rather than exposing every possible filter at once.

**Intent**
Closes this BR's FR group with the anti-overload principle the thesis
names explicitly.

**Success outcome**
Default filter surface stays small; advanced filters are one tap away,
not pre-exposed.

**Failure / edge outcome**
A filter panel found exposing every possible option by default is a
defect against BR02's progressive-disclosure Constraint.

**Acceptance criteria**
- [ ] Default filter surface shows only the common set.
- [ ] Advanced filters are reachable without being shown by default.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR02.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR010 — Minimal Creation Form (What/When/Where/How-Many)
**Traces from:** BR03
**Traced to:** UX07 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When an Activity Creator starts "Make Something Happen," the system shall
let them complete creation using only an intent category (Play, Meet, Eat,
Learn, Work, Explore, Celebrate, Help), a when, a where, and a target
headcount, without routing them through any advanced field first.

**Intent**
First demoable Creation slice — a real, publishable activity from the
minimal form alone.

**Success outcome**
Creation completes from the four minimal fields; the item is immediately
live.

**Failure / edge outcome**
A creation flow that requires any advanced field (capacity tiers,
co-hosts) before completion is a defect.

**Acceptance criteria**
- [ ] Creation completes using only What/When/Where/How-many.
- [ ] No advanced field is required to reach a published state.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR03.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR011 — Activity/Occurrence Data Distinction
**Traces from:** BR03
**Traced to:** UX06 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a creator marks an activity as recurring, the system shall represent
it as one Activity with multiple occurrences, aggregating history and
attendance at the Activity level rather than fragmenting per occurrence.

**Intent**
Fixes the base data shape BR03 calls "essential," before any other FR in
this group depends on it.

**Success outcome**
A recurring activity's attendance/history view aggregates across all its
occurrences correctly.

**Failure / edge outcome**
Attendance/history found fragmented per-occurrence for a recurring
Activity is a defect requiring remodeling.

**Acceptance criteria**
- [ ] A recurring Activity's participation history aggregates across occurrences.
- [ ] A one-off event is representable without an unnecessary Activity wrapper.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR03 DEC-001.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR012 — Edit and Cancel an Activity or Occurrence
**Traces from:** BR03
**Traced to:** UX07 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a creator edits or cancels an activity or a specific occurrence, the
system shall apply the change at the scope the creator selected (the whole
Activity or a single occurrence) and shall notify existing participants of
the change (BR12).

**Intent**
Covers the ordinary lifecycle-management path on top of FR010/FR011.

**Success outcome**
Edits/cancellations apply at the correct scope; participants are notified.

**Failure / edge outcome**
A single-occurrence cancellation found silently cancelling the whole
recurring Activity (or vice versa) is a defect.

**Acceptance criteria**
- [ ] Edit/cancel scope (Activity vs. one occurrence) is explicit and respected.
- [ ] Existing participants are notified of the change.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR03.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR013 — Progressive Advanced Configuration
**Traces from:** BR03, BR13
**Traced to:** UX07 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** Medium — exact advanced-field set is implementation-stage.

**Requirement (ISO 29148 form)**
When a creator needs capacity tiers, co-hosts, or a waitlist, the system
shall surface those controls only on request, never as part of the
default creation path fixed by FR010.

**Intent**
Layers organizer-grade configuration onto the minimal creation flow
without burdening the ordinary Activity Creator.

**Success outcome**
Advanced controls are reachable but never pre-exposed to a creator who
doesn't need them.

**Failure / edge outcome**
Advanced fields appearing unconditionally in the default flow is a defect
against BR03/BR13's progressive-complexity Constraint.

**Acceptance criteria**
- [ ] Advanced configuration is opt-in, not shown by default.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (exact field set
deferred) · Singular ✓ · Feasible ✓ · Verifiable ~ (same reason) ·
Correct ✓ · Conforming ✓

**Decisions** — none beyond BR03/BR13.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR014 — Immediate Shareable Link on Creation
**Traces from:** BR03, BR11
**Traced to:** UX07 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When creation completes, the system shall immediately generate a
shareable public link for the activity/event, per BR11's public-page
model.

**Intent**
Closes this BR's group by connecting Creation directly to BR11's growth
mechanism, with zero extra creator effort.

**Success outcome**
A shareable link exists the instant creation completes.

**Failure / edge outcome**
A creation flow that completes without producing a shareable link is a
defect.

**Acceptance criteria**
- [ ] Every completed creation immediately has a working shareable link.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR03/BR11.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR015 — One-Tap Interested/Going
**Traces from:** BR04
**Traced to:** UX08 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a participant wants to signal intent to attend, the system shall let
them mark Interested or Going with a single tap, without any registration
form.

**Intent**
First demoable Participation slice — a real, recorded intent signal.

**Success outcome**
One tap records the participant's status against the activity/occurrence.

**Failure / edge outcome**
A flow requiring more than one tap (or any form) to reach Interested/Going
is a defect.

**Acceptance criteria**
- [ ] Interested/Going is reachable in exactly one tap.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR04.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR016 — Full Attendance-Status Lifecycle
**Traces from:** BR04
**Traced to:** UX08 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a participant's relationship to an occurrence changes, the system
shall track it through Interested, Going, Cancelled, Checked-In, Attended,
or No-show, and shall make the current and historical status queryable by
the participant and the organizer.

**Intent**
Extends FR015 into the full lifecycle every downstream signal (Reputation,
Feedback, Community Memory) depends on.

**Success outcome**
Status transitions are recorded accurately and queryable afterward.

**Failure / edge outcome**
A status transition with no recorded history entry is a defect.

**Acceptance criteria**
- [ ] All six named statuses are representable.
- [ ] Status history is queryable after the fact.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR04.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR017 — Organizer Update/Cancellation Reaches Participants
**Traces from:** BR04, BR12
**Traced to:** UX08 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When an organizer cancels or changes an occurrence a participant is
Interested/Going in, the system shall notify that participant through
BR12's Important notification class.

**Intent**
Connects the attendance lifecycle to the notification model so no
participant is left uninformed.

**Success outcome**
Every affected participant is notified of a cancellation/change.

**Failure / edge outcome**
A cancellation/change reaching zero notified participants is a defect.

**Acceptance criteria**
- [ ] Every Interested/Going participant is notified of a cancellation or material change.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR04/BR12.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR018 — Scale-Gated Optional QR Check-In
**Traces from:** BR04
**Traced to:** UX08 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** Medium — the exact "large vs. small event" threshold that
gates QR check-in is implementation-stage (BR04 Confidence note).

**Requirement (ISO 29148 form)**
When an organizer runs a larger event, the system shall offer QR check-in
as an optional attendance-confirmation method, and shall never require it
for small, casual sessions.

**Intent**
Adds scale-appropriate rigor on top of FR016's status model without
burdening every casual activity.

**Success outcome**
Large-event organizers can opt into QR check-in; small-session organizers
are never forced to.

**Failure / edge outcome**
QR check-in appearing as a mandatory step for a small casual session is a
defect against BR04's explicit "keep it simple" Constraint.

**Acceptance criteria**
- [ ] QR check-in is optional and organizer-initiated, never mandatory by default.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (threshold
deferred) · Singular ✓ · Feasible ✓ · Verifiable ~ (same reason) ·
Correct ✓ · Conforming ✓

**Decisions** — none beyond BR04 DEC-001.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR019 — Non-Punitive No-Show Handling
**Traces from:** BR04
**Traced to:** UX08 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a participant is marked No-show, the system shall record it as a
reliability signal for Reputation (BR08) and shall never apply an
automatic penalty, restriction, or public marker to that participant as a
result.

**Intent**
Closes this BR's group with its explicit anti-punitive rule.

**Success outcome**
No-shows feed reputation signals only; no visible/automatic penalty
occurs.

**Failure / edge outcome**
Any automatic restriction or public marker triggered by a no-show alone is
a defect.

**Acceptance criteria**
- [ ] A no-show never triggers an automatic restriction or public marker.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR04.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR020 — Create, Join and Leave a Circle
**Traces from:** BR05
**Traced to:** UX09 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a participant creates, joins, or leaves a circle, the system shall
apply the change immediately and shall never require any other member's
approval for a participant's own voluntary join/leave (subject to the
circle's own type-based access rule, e.g. Private requires an invite to
join).

**Intent**
First demoable Circles slice — real, working membership mechanics.

**Success outcome**
Join/leave completes immediately for the acting participant.

**Failure / edge outcome**
A voluntary leave blocked pending another member's approval is a defect.

**Acceptance criteria**
- [ ] Join (where the circle's type allows it) and leave complete immediately.
- [ ] No other member's approval is required for a voluntary leave.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR05.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR021 — Circle Type Enforcement
**Traces from:** BR05
**Traced to:** UX09 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a circle is created, the system shall require it be assigned exactly
one type (Public, Community, Private, Organization, Interest, Local, or
Recurring-Activity), and shall enforce that type's own visibility/access
rule for every subsequent join attempt and content view.

**Intent**
Fixes the access-control foundation FR020 and later BR11 public-page
behavior both depend on.

**Success outcome**
Every circle resolves to exactly one type, and that type's access rule is
enforced consistently.

**Failure / edge outcome**
A circle with an ambiguous or unenforced type is a defect.

**Acceptance criteria**
- [ ] Every circle has exactly one type.
- [ ] Join/view behavior matches that type's defined rule.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR05.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR022 — Organic Circle-Formation Suggestion
**Traces from:** BR05
**Traced to:** UX09 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** Medium — exact repeated-co-participation trigger threshold
is implementation-stage (BR05 Assumptions).

**Requirement (ISO 29148 form)**
When the system detects repeated co-participation among the same people
across occurrences of one Activity, it shall suggest forming a Circle
around that group, and shall never create the Circle without the
recipient's explicit acceptance.

**Intent**
The emergent-community mechanism BR05 names as an important innovation,
layered on top of FR016's attendance history.

**Success outcome**
A relevant group is offered a circle-formation suggestion they can accept
or decline.

**Failure / edge outcome**
A circle created without an explicit acceptance action is a defect against
BR05's "never forced" Constraint.

**Acceptance criteria**
- [ ] Circle-formation suggestions require an explicit accept action to create the circle.
- [ ] Declining a suggestion has no negative effect.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (trigger
threshold deferred) · Singular ✓ · Feasible ✓ · Verifiable ~ (same
reason) · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR05.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR023 — Circle Membership Never a Precondition
**Traces from:** BR05
**Traced to:** UX09 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a participant has zero circle memberships, the system shall provide
full, undiminished access to Discovery, Activity creation, and
Participation.

**Intent**
Direct enforcement of BR05's "never a mandatory precondition" rule.

**Success outcome**
A zero-circle participant uses every other capability without gating.

**Failure / edge outcome**
Any capability found implicitly requiring circle membership is a defect.

**Acceptance criteria**
- [ ] A zero-circle account exercises Discovery/Creation/Participation without restriction.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR05.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR024 — Community Memory Visible to Circle Members
**Traces from:** BR05
**Traced to:** UX09 (Step 3 UX)
**Priority:** Should
**Status:** Draft
**Confidence:** High — the requirement itself is clear; downgraded from
Must on second review because the thesis's own explicit MVP list (§58)
for Circles ("create, join, leave, members, activities, calendar") does
not include community-memory statistics, and the thesis separately calls
this "a powerful **long-term** feature" (§35) rather than an immediate one.
BR05's core membership mechanics (FR020–FR023) remain Must and are fully
functional without this FR.

**Requirement (ISO 29148 form)**
When a circle member views their circle, the system shall display its
member count, activity count, participation count, active-member count,
and milestones, visible at minimum to that circle's own members.

**Intent**
Turns FR020's bare membership mechanics into the "community infrastructure"
the thesis names.

**Success outcome**
Circle members see an accurate, current summary of their circle's health.

**Failure / edge outcome**
Stats that are stale or missing for an active circle are a defect.

**Acceptance criteria**
- [ ] All five named stats are visible to circle members.
- [ ] Non-Public circles do not expose these stats beyond their own members.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR05 DEC-001.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR025 — Public Circle Visibility Follows Circle Type
**Traces from:** BR05, BR11
**Traced to:** UX09 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a circle's type is Public, the system shall make its existence and
summary discoverable per BR11's public-page model; when its type is
Community, Private, or Organization, the system shall restrict that
visibility accordingly.

**Intent**
Closes this BR's group by connecting Circle types to BR11's public-page
mechanism.

**Success outcome**
A Public circle is discoverable externally; other types are not.

**Failure / edge outcome**
A non-Public circle found externally discoverable is a defect.

**Acceptance criteria**
- [ ] Only Public-type circles produce an externally discoverable page.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR05/BR11.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR026 — Personal Calendar
**Traces from:** BR06
**Traced to:** UX10 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a participant views their personal calendar, the system shall show
every occurrence they are Interested/Going in (BR04), in chronological
order.

**Intent**
First demoable Calendar slice.

**Success outcome**
Personal calendar accurately reflects the participant's own attendance
intent.

**Failure / edge outcome**
An occurrence the participant is Going to missing from their calendar is a
defect.

**Acceptance criteria**
- [ ] Every Interested/Going occurrence appears on the participant's own calendar.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR06.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR027 — Circle Calendar
**Traces from:** BR06
**Traced to:** UX10 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a circle member views their circle's calendar, the system shall show
every occurrence created under that circle.

**Intent**
Extends FR026's model to the circle scope.

**Success outcome**
Circle calendar reflects all of that circle's own occurrences.

**Failure / edge outcome**
An occurrence created under a circle missing from that circle's calendar
is a defect.

**Acceptance criteria**
- [ ] Every circle-linked occurrence appears on that circle's calendar.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR06.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR028 — Organization and Community Calendars
**Traces from:** BR06
**Traced to:** UX10 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a member views an organization's or the wider community's calendar,
the system shall show every occurrence created under that organization, or
every community-scoped occurrence respectively.

**Intent**
Extends FR026/FR027's model to the two remaining private/semi-private
scopes.

**Success outcome**
Organization and community calendars each reflect their own correctly
scoped occurrences.

**Failure / edge outcome**
Cross-scope leakage (a community occurrence appearing only under one
organization's calendar, or vice versa) is a defect.

**Acceptance criteria**
- [ ] Organization calendar shows only that organization's occurrences.
- [ ] Community calendar shows all community-scoped occurrences.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ~ (two
scopes with an identical structural rule, described together) ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR06.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR029 — Public Calendar Includes Only Public-Marked Items
**Traces from:** BR06, BR11
**Traced to:** UX10 (Step 3 UX)
**Priority:** Should
**Status:** Draft
**Confidence:** High — the requirement itself is clear; downgraded from
Must on second review because the thesis's own explicit MVP list (§58)
for Calendar ("personal, circle, community") does not include a public,
browsable calendar aggregation view — that is distinct from BR11's
per-item public pages (FR046–FR050), which remain Must. FR026–FR028
(personal/circle/community) remain Must and are fully functional without
this FR.

**Requirement (ISO 29148 form)**
When the system renders the public calendar, it shall include only
activities/events explicitly marked Public, and shall never include a
private or community-restricted item.

**Intent**
Closes this BR's group by tying Calendar's most exposed scope to BR11's
visibility rule.

**Success outcome**
Public calendar contains only genuinely public items.

**Failure / edge outcome**
A private/restricted item found on the public calendar is a defect
against BR09/BR11's privacy model.

**Acceptance criteria**
- [ ] Public calendar excludes every non-Public-marked item.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR06/BR11.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR030 — Every Item Resolves to Exactly One Trust Level
**Traces from:** BR07
**Traced to:** UX06 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When an activity/event is created or ingested, the system shall assign it
exactly one trust level from the defined taxonomy (ForKhatri Verified,
Community Verified, Partner Verified, External — Trusted Source,
Community Submitted).

**Intent**
First demoable Trust slice — a real, always-present classification.

**Success outcome**
Every item has an unambiguous, single trust level at all times.

**Failure / edge outcome**
An item with no assigned trust level, or more than one, is a defect.

**Acceptance criteria**
- [ ] Every activity/event has exactly one trust level at all times.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR07.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR031 — Trust Status Visibly Displayed
**Traces from:** BR07
**Traced to:** UX06 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When any viewer sees an activity/event card or page, the system shall
display its trust level directly on that surface, without requiring the
viewer to seek it out.

**Intent**
Fulfils BR07's "visible, not buried" Constraint on top of FR030's
classification.

**Success outcome**
Trust level is visible at a glance on every card/page.

**Failure / edge outcome**
A trust level reachable only through a secondary screen or settings menu
is a defect.

**Acceptance criteria**
- [ ] Trust level is visible directly on the card/page, zero extra taps.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR07.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR032 — Organizations and Venues Share the Partner-Verified Path
**Traces from:** BR07
**Traced to:** UX06 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a Venue or Organization seeks trust status, the system shall route it
through the same Partner Verified classification used for any other
trusted business/organization, rather than a separate venue-specific trust
model.

**Intent**
Fulfils modules.md's "venue verification" line via BR07's existing
taxonomy, as BR07 itself now states explicitly.

**Success outcome**
A verified venue and a verified business organization both resolve to the
same Partner Verified level, with the same visible treatment.

**Failure / edge outcome**
A separate, inconsistent trust label appearing for venues specifically is
a defect against BR07's unified-taxonomy Constraint.

**Acceptance criteria**
- [ ] Verified venues and verified business organizations both display as Partner Verified.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR07 (Proposed outcome, venue note).
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR033 — Trust Feeds Discovery Ranking
**Traces from:** BR07, BR02
**Traced to:** UX05 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When Discovery ranks results (FR007), it shall use each item's trust level
as one of the named ranking inputs.

**Intent**
Closes this BR's group by wiring Trust into the ranking formula it was
always meant to feed.

**Success outcome**
Trust level measurably influences ranking order alongside the other named
factors.

**Failure / edge outcome**
Trust level found to have zero effect on ranking is a defect against
FR007's own factor list.

**Acceptance criteria**
- [ ] Trust level is a live input to the ranking formula, not decorative-only.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR07/BR02.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR034 — Reputation Signals Computed From Named Behaviours
**Traces from:** BR08
**Traced to:** UX06 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When an organizer or participant's behaviour occurs (identity
verification, event completion, cancellation, attendance reliability,
report, community contribution), the system shall update their internal
reputation signals accordingly.

**Intent**
First demoable Reputation slice — a real, behaviour-driven internal model.

**Success outcome**
Reputation signals change measurably in response to the named behaviours.

**Failure / edge outcome**
A named behaviour with no effect on internal reputation signals is a
defect.

**Acceptance criteria**
- [ ] Each of the named behaviour categories updates an internal signal.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR08.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR035 — No Public Star Rating or Numeric Score
**Traces from:** BR08
**Traced to:** UX06 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When any user views another user's or organizer's profile or activity
page, the system shall never display a star rating, numeric score, or
aggregate reputation figure.

**Intent**
Absolute rule central to BR08's entire approach, layered onto FR034's
internal signal model.

**Success outcome**
No such score/rating exists anywhere in the product.

**Failure / edge outcome**
Any UI element rendering a star rating or numeric reputation score is a
defect requiring removal.

**Acceptance criteria**
- [ ] No screen displays a star rating or numeric reputation figure.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR08.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR036 — Reputation Never Purchasable
**Traces from:** BR08
**Traced to:** UX06 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When any paid tier or feature is offered to an organizer, the system shall
never let that payment directly raise a reputation signal.

**Intent**
Protects FR034's model from becoming pay-to-win.

**Success outcome**
No paid feature has any direct effect on reputation signals.

**Failure / edge outcome**
Any paid tier found to raise reputation directly is a defect requiring
correction.

**Acceptance criteria**
- [ ] No monetized feature has a coded effect on reputation signals.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR08.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR037 — Reputation Surfaced Qualitatively, Never as a Raw Score
**Traces from:** BR08
**Traced to:** UX06 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When the system wants to communicate an organizer's reliability to a
viewer, it shall express it through qualitative, evidence-style signals
(e.g. "organizer of 12 completed circle activities"), never as a raw
internal score value.

**Intent**
Closes this BR's group with the display-side counterpart to FR035's
prohibition.

**Success outcome**
Viewers see meaningful, honest signals without ever seeing an underlying
number.

**Failure / edge outcome**
Any surface leaking the raw internal reputation number is a defect.

**Acceptance criteria**
- [ ] User-facing reputation signals are always qualitative, never a raw internal number.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR08 DEC-001.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR038 — Approximate Location Display Hierarchy
**Traces from:** BR09
**Traced to:** UX04 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When the system displays a participant's or activity's location, it shall
present it as City → Zone → Locality → approximate distance, and shall
never display an exact home address.

**Intent**
First demoable Privacy slice — the concrete display rule Discovery/
Circles/People-Discovery all depend on.

**Success outcome**
Every location display uses the approximate hierarchy, never an exact
address.

**Failure / edge outcome**
Any surface displaying an exact home address is a defect requiring
immediate remediation.

**Acceptance criteria**
- [ ] No screen displays a participant's exact home address.
- [ ] Location display follows the City→Zone→Locality→distance model.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR09 DEC-001.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR039 — Explicit Consent Required for Precise Location
**Traces from:** BR09
**Traced to:** UX17 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When any feature would reveal another user's precise/live location, the
system shall require that user's explicit, specific consent for that
purpose before doing so.

**Intent**
Extends FR038's display rule to any future precise-location feature.

**Success outcome**
Precise location is never shown without a specific, prior consent record.

**Failure / edge outcome**
A precise location revealed without a matching consent record is a
defect/incident.

**Acceptance criteria**
- [ ] Every precise-location disclosure has a linked, specific consent record.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR09.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR040 — Private Circle/Attendance Hidden by Default
**Traces from:** BR09
**Traced to:** UX08 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a non-member views a Private circle or a non-attendee views a
private activity's attendance, the system shall deny that view by
default.

**Intent**
Direct enforcement of BR09's private-information Constraint at its two
most sensitive points.

**Success outcome**
Non-members/non-attendees never see private circle or attendance content.

**Failure / edge outcome**
Any non-member/non-attendee found able to view private content is a
defect/incident.

**Acceptance criteria**
- [ ] Private circle content is denied to non-members.
- [ ] Private attendance lists are denied to non-attendees.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ~ (two
instances of the same "private stays private" rule) · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR09.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR041 — User-Controlled Location-Sharing Precision
**Traces from:** BR09
**Traced to:** UX17 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a participant sets their own location-sharing preference, the system
shall let them choose the precision level shared for Discovery purposes,
and shall never default to a more precise setting than the participant
selected.

**Intent**
Closes this BR's group with the user-side control the thesis names
explicitly.

**Success outcome**
Participant's chosen precision is respected everywhere their location is
used.

**Failure / edge outcome**
A feature using a more precise location than the participant selected is
a defect.

**Acceptance criteria**
- [ ] Location precision used anywhere never exceeds the participant's own setting.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR09.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR042 — Reason-Based Person Suggestion
**Traces from:** BR10
**Traced to:** UX14 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When the system suggests another person to a participant, it shall attach
a concrete, shared-context reason (shared activity, interest, circle,
locality, or mutual connection).

**Intent**
First demoable People Discovery slice.

**Success outcome**
Every person suggestion carries a specific, real shared-context reason.

**Failure / edge outcome**
A person suggestion with no stated reason is a defect.

**Acceptance criteria**
- [ ] Every person suggestion states a specific shared-context reason.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR10.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR043 — No Reason-Less Nearby-People List
**Traces from:** BR10
**Traced to:** UX14 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When the system would otherwise surface people near a participant, it
shall never present a bare "people nearby" list lacking FR042's
shared-context reason.

**Intent**
Guards FR042's rule against the specific anti-pattern the thesis names as
"Bad."

**Success outcome**
No people-listing surface exists without a per-person context reason.

**Failure / edge outcome**
Any surface listing people by proximity alone is a defect.

**Acceptance criteria**
- [ ] No feature lists people by proximity/count alone, without a context reason.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR10.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR044 — No Swipe/Match Mechanic
**Traces from:** BR10
**Traced to:** UX14 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When any person-discovery interaction is designed, the system shall never
implement a swipe, like/pass, or mutual-match mechanic of any kind.

**Intent**
Hard-codes BR10's module-boundary rule as an implementation-level
prohibition.

**Success outcome**
No swipe/match interaction pattern exists anywhere in Milavn.

**Failure / edge outcome**
Any swipe/like/match-style interaction found anywhere is a defect
requiring removal, regardless of context.

**Acceptance criteria**
- [ ] No screen in Milavn implements a swipe, like/pass, or match mechanic.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR10 DEC-001.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR045 — No Romantic/Matrimonial Framing
**Traces from:** BR10
**Traced to:** UX14 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When any Milavn feature is designed or copy is written, the system shall
never present a romantic or matrimonial framing of a person-to-person
suggestion.

**Intent**
Closes this BR's group with the permanent, module-boundary non-goal.

**Success outcome**
No romantic/matrimonial language or framing appears anywhere in Milavn.

**Failure / edge outcome**
Any romantic/matrimonial framing found anywhere is a defect requiring
immediate correction, regardless of how it was introduced.

**Acceptance criteria**
- [ ] No user-facing copy or feature frames a suggestion as romantic/matrimonial.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR10 DEC-001.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR046 — Public Page Without Login
**Traces from:** BR11
**Traced to:** UX11 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When any visitor opens a link to a Public-marked event, circle,
organization, or activity, the system shall render its page without
requiring login.

**Intent**
First demoable Public Pages slice.

**Success outcome**
An unauthenticated visitor can open and view a Public item's page.

**Failure / edge outcome**
A Public item's page requiring login to view at all is a defect.

**Acceptance criteria**
- [ ] A Public item's page renders fully for an unauthenticated visitor.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR11.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR047 — Public Page Content Contract
**Traces from:** BR11
**Traced to:** UX11 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When the system renders a public page, it shall include title, image,
date, time, location, host, trust status (BR07), capacity, and an RSVP
entry point.

**Intent**
Fixes the minimum content contract for FR046's page.

**Success outcome**
Every public page includes all named elements.

**Failure / edge outcome**
A public page missing any named element is a defect.

**Acceptance criteria**
- [ ] Every public page includes all eight named elements.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR11.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR048 — Crawlable, Indexable Public Pages
**Traces from:** BR11
**Traced to:** UX11 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a search engine crawls a Public page, the system shall serve
content and metadata that allow it to be indexed, matching how current
comparable products (verified: Partiful) already operate their own public
event pages.

**Intent**
Fulfils the SEO/organic-discovery half of BR11's growth mechanism.

**Success outcome**
Public pages are indexable and appear in organic search results over
time.

**Failure / edge outcome**
A Public page that blocks crawling or omits indexable metadata is a
defect.

**Acceptance criteria**
- [ ] Public pages serve crawlable content and appropriate metadata for indexing.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR11 DEC-001.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR049 — Cross-Channel Sharing
**Traces from:** BR11
**Traced to:** UX11 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a user wants to share a Public item, the system shall provide direct
share paths for WhatsApp, Instagram, SMS, email, QR, and copy-link.

**Intent**
Fulfils the network-leverage half of BR11's growth mechanism.

**Success outcome**
A user reaches any of the six named channels in one action from the
public page.

**Failure / edge outcome**
Any named channel missing from the share options is a defect.

**Acceptance criteria**
- [ ] All six named share channels are available from the public page.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR11.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR050 — Private Items Never Exposed via Public Page
**Traces from:** BR11, BR09
**Traced to:** UX11 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When an item is not marked Public, the system shall never generate a
publicly reachable page for it.

**Intent**
Closes this BR's group with the boundary that keeps BR11 from leaking
BR09's privacy model.

**Success outcome**
Only explicitly Public items ever have a publicly reachable page.

**Failure / edge outcome**
A private/community-restricted item found reachable via a public URL is a
defect/incident.

**Acceptance criteria**
- [ ] No non-Public item has a reachable public page under any circumstance.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR11/BR09.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR051 — Important-Class Notifications Always Delivered
**Traces from:** BR12
**Traced to:** UX12 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a cancellation, location change, or organizer update occurs for an
occurrence a participant is Interested/Going in, the system shall deliver
an Important-class notification, and shall never suppress it via a general
frequency preference.

**Intent**
First demoable Notifications slice — the class that must never fail.

**Success outcome**
Every affected participant receives the Important notification regardless
of their general frequency settings.

**Failure / edge outcome**
An Important notification suppressed by a general mute/frequency setting
is a defect.

**Acceptance criteria**
- [ ] Important-class notifications are delivered regardless of general frequency preferences.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR12.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR052 — Useful-Class Reminders
**Traces from:** BR12
**Traced to:** UX12 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When an occurrence a participant is Going to is upcoming, the system shall
send an Useful-class reminder ahead of it.

**Intent**
Layers the second notification class onto FR051's foundation.

**Success outcome**
Participants receive a timely reminder before an occurrence they're Going
to.

**Failure / edge outcome**
No reminder sent for an upcoming Going occurrence is a defect.

**Acceptance criteria**
- [ ] A reminder is sent ahead of every upcoming Going occurrence.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR12.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR053 — Social-Class Notifications
**Traces from:** BR12
**Traced to:** UX12 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When someone relevant to a participant (a circle member, a mutual
connection) joins an activity the participant is also connected to, the
system shall send a Social-class notification.

**Intent**
Layers the third notification class onto the model.

**Success outcome**
Relevant social joins produce a Social-class notification.

**Failure / edge outcome**
A Social notification exposing private membership/attendance the recipient
isn't authorized to see is a defect against BR09.

**Acceptance criteria**
- [ ] Social-class notifications fire for relevant joins.
- [ ] Social notifications never expose information the recipient isn't authorized to see.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR12.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR054 — Opportunity-Class Notifications, User-Controlled Frequency
**Traces from:** BR12
**Traced to:** UX12 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a new activity matches a participant's interests, the system shall
offer an Opportunity-class notification, and shall let the participant
control or mute this class's frequency independently of the other three.

**Intent**
Layers the fourth, spam-riskiest class onto the model with its own control.

**Success outcome**
Opportunity notifications respect the participant's own frequency/mute
setting.

**Failure / edge outcome**
Opportunity notifications ignoring the participant's frequency/mute
setting is a defect.

**Acceptance criteria**
- [ ] Opportunity-class notifications respect an independent frequency/mute control.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR12 DEC-001.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR055 — Milavn Governs What/When, Not Delivery Infrastructure
**Traces from:** BR12
**Traced to:** UX12 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When Milavn decides a notification should be sent, the system shall hand
it to the platform's shared notification-delivery infrastructure for
actual transport (push/SMS/email/in-app), rather than Milavn building its
own delivery pipeline.

**Intent**
Closes this BR's group by respecting the Common Platform boundary named in
the BR file's Scope section.

**Success outcome**
Milavn's own code owns classification/urgency logic only; delivery
mechanics are the shared platform service's responsibility.

**Failure / edge outcome**
A Milavn-specific notification-delivery mechanism built in parallel to the
shared platform service is a defect against the module boundary.

**Acceptance criteria**
- [ ] Notification delivery is handled by the shared platform service, not a Milavn-specific pipeline.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR12 (Out of scope).
**Assumptions** — the shared platform notification service exists as a dependency, per `modules.md` Shared Concerns.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR056 — Attendee List Visible to Organizer Only
**Traces from:** BR13
**Traced to:** UX13 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a Circle/Event Organizer views their own activity/occurrence, the
system shall show them the attendee list, and shall never surface this
list to an ordinary participant.

**Intent**
First demoable Organizer Tooling slice.

**Success outcome**
Organizers see attendee lists; ordinary participants never do.

**Failure / edge outcome**
An ordinary participant found able to view the attendee list is a defect.

**Acceptance criteria**
- [ ] Only the organizer of a given item can view its attendee list.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR13.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR057 — Event Updates and Announcements
**Traces from:** BR13
**Traced to:** UX13 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When an organizer posts an update or announcement, the system shall
deliver it to every current participant via BR12's notification model.

**Intent**
Extends FR056's organizer surface with an outbound communication tool.

**Success outcome**
Every current participant receives the organizer's update.

**Failure / edge outcome**
An update reaching zero participants is a defect.

**Acceptance criteria**
- [ ] Organizer updates reach every current participant.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR13.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR058 — Capacity and Waitlist Management
**Traces from:** BR13
**Traced to:** UX13 (Step 3 UX)
**Priority:** Should
**Status:** Draft
**Confidence:** Medium — exact waitlist promotion mechanics are
implementation-stage; downgraded from Must on second review because the
thesis's own explicit MVP list (§58) for Organizer ("attendee list, event
updates") does not include capacity/waitlist automation — that comes from
the broader Circle/Event Organizer persona description (§8.4/§8.5), not
the curated MVP boundary itself. FR056–FR057 (attendee list, updates)
remain Must and are fully functional without this FR.

**Requirement (ISO 29148 form)**
When an occurrence reaches its stated capacity, the system shall offer the
organizer waitlist management, promoting waitlisted participants
automatically as spots free up unless the organizer intervenes.

**Intent**
Adds organizer-grade capacity control layered onto FR010's minimal
creation flow.

**Success outcome**
A full occurrence's waitlist promotes participants as capacity frees up.

**Failure / edge outcome**
A freed spot with a non-empty waitlist that goes unfilled is a defect.

**Acceptance criteria**
- [ ] A freed spot with a non-empty waitlist promotes the next waitlisted participant automatically.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (exact promotion
mechanics deferred) · Singular ✓ · Feasible ✓ · Verifiable ~ (same
reason) · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR13/BR03.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR059 — Co-Organizer Delegation
**Traces from:** BR13
**Traced to:** UX13 (Step 3 UX)
**Priority:** Should
**Status:** Draft
**Confidence:** High — the requirement itself is clear; downgraded from
Must on second review for the same reason as FR058: absent from the
thesis's explicit Organizer MVP bullet list (§58), drawn instead from the
broader persona description. FR056–FR057 remain Must and are fully
functional without this FR.

**Requirement (ISO 29148 form)**
When a primary organizer delegates co-organizer status to another user,
the system shall grant that person the same organizer-tooling access
(FR056–FR058) for that specific item.

**Intent**
Extends organizer capability to a shared-responsibility model.

**Success outcome**
A delegated co-organizer exercises the same tooling as the primary
organizer.

**Failure / edge outcome**
A delegated co-organizer found missing any of the primary organizer's
tooling is a defect.

**Acceptance criteria**
- [ ] A co-organizer's access matches the primary organizer's for that item.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR13.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR060 — Future AI Organizer Actions Respect Human Authorization Boundaries
**Traces from:** BR13
**Traced to:** UX13 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When any AI-assisted feature acts on an organizer's behalf, the system
shall enforce the same membership/authorization boundaries a human
organizer would face, and shall never let AI bypass them as a shortcut.

**Intent**
Closes this BR's group with the standing rule that must hold the moment
any AI-assisted organizer feature ships, however small.

**Success outcome**
An AI-assisted action is denied anything a human organizer in the same
role would be denied.

**Failure / edge outcome**
An AI-assisted action found bypassing an authorization check a human
organizer would face is a defect/incident.

**Acceptance criteria**
- [ ] AI-assisted organizer actions are checked against the same authorization rules as human actions.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR13 DEC-001.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR061 — Report an Activity, User, Organization or Content
**Traces from:** BR14
**Traced to:** UX15 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When any user wants to report an activity, user, organization, or piece of
content, the system shall let them submit that report from the relevant
surface at any time.

**Intent**
First demoable Safety slice.

**Success outcome**
A report is captured and reaches a moderation queue.

**Failure / edge outcome**
Reporting unavailable from any activity/user/organization/content surface
is a defect.

**Acceptance criteria**
- [ ] Report is reachable from any activity, user, organization, or content surface.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR14.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR062 — Block a User
**Traces from:** BR14
**Traced to:** UX15 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a user blocks another user, the system shall prevent the blocked
user from contacting or being surfaced to the blocking user going forward.

**Intent**
Complements FR061's reporting path with a direct, self-service protective
action.

**Success outcome**
A blocked user no longer contacts or appears to the blocking user.

**Failure / edge outcome**
A blocked user still able to contact or appear to the blocking user is a
defect.

**Acceptance criteria**
- [ ] A blocked user cannot contact the blocking user afterward.
- [ ] A blocked user is excluded from the blocking user's Discovery/People Discovery.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR14.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR063 — Organizer Identity, Location and Capacity Always Visible to RSVP'd Participants
**Traces from:** BR14
**Traced to:** UX15 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a participant has RSVP'd (Interested/Going) to an occurrence, the
system shall always show them the organizer's identity, the event
location, and its stated capacity.

**Intent**
Fixes the baseline physical-accountability rule BR14 names explicitly.

**Success outcome**
Every RSVP'd participant can see who's running it, where, and how big it
is.

**Failure / edge outcome**
Any of the three named elements hidden from an RSVP'd participant is a
defect.

**Acceptance criteria**
- [ ] Organizer identity, location, and capacity are all visible to an RSVP'd participant.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR14.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR064 — Safety Guidelines for High-Risk Activities
**Traces from:** BR14
**Traced to:** UX15 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When an activity is tagged as high-risk (e.g. physically strenuous,
minors/family-involving), the system shall present relevant safety
guidelines to participants before or at RSVP.

**Intent**
Adds category-specific safety content on top of FR063's baseline
accountability.

**Success outcome**
High-risk activities carry visible safety guidance for participants.

**Failure / edge outcome**
A high-risk activity with no safety guidance shown is a defect.

**Acceptance criteria**
- [ ] Every high-risk-tagged activity displays relevant safety guidelines.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR14.
**Assumptions** — exact high-risk tagging criteria and minors/family
additional safeguards are implementation-stage design (BR14 Out of
scope).

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR065 — Basic Moderation Queue, Scoped to Actual Usage
**Traces from:** BR14
**Traced to:** UX20 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a report (FR061) is submitted, the system shall route it into a
basic review queue that a moderator can act on, without requiring an
elaborate, speculative moderation system beyond what actual usage
justifies.

**Intent**
Closes this BR's group with the launch-scoped moderation baseline BR14
explicitly calls for.

**Success outcome**
Every submitted report reaches a queue a moderator can review and act on.

**Failure / edge outcome**
A submitted report that never reaches any reviewable queue is a defect.

**Acceptance criteria**
- [ ] Every submitted report appears in a moderator-reviewable queue.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR14 DEC-001.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR066 — Optional Post-Event Feedback Prompt
**Traces from:** BR15
**Traced to:** UX16 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** Medium — exact question set is implementation-stage
(BR15 Assumptions).

**Requirement (ISO 29148 form)**
When a participant's attendance is marked Attended (BR04), the system
shall offer an optional feedback prompt — did this help them do something
they wanted to do, and would they participate again — with optional
additional detail.

**Intent**
First demoable Feedback slice.

**Success outcome**
An Attended participant can optionally answer the prompt.

**Failure / edge outcome**
The prompt appearing as a required step before any other action is a
defect against BR15's "always optional" Constraint.

**Acceptance criteria**
- [ ] The feedback prompt is always skippable.
- [ ] Skipping has no visible or functional consequence.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (exact question
set deferred) · Singular ✓ · Feasible ✓ · Verifiable ~ (same reason) ·
Correct ✓ · Conforming ✓

**Decisions** — none beyond BR15.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR067 — Feedback Feeds Reputation Internally, Never Publicly
**Traces from:** BR15, BR08
**Traced to:** UX16 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When feedback is submitted, the system shall feed it into the organizer's
internal reputation signals (BR08), and shall never expose individual
feedback as a public rating or review.

**Intent**
Connects FR066's capture point to BR08's existing model without
duplicating or contradicting its no-public-rating rule.

**Success outcome**
Feedback measurably informs internal reputation; no individual feedback is
ever public.

**Failure / edge outcome**
Any surface exposing individual feedback publicly is a defect against both
BR08 and BR15.

**Acceptance criteria**
- [ ] Feedback updates internal reputation signals.
- [ ] No individual feedback response is ever displayed publicly.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR15 (Constraints).
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR068 — Feedback Never a Precondition
**Traces from:** BR15
**Traced to:** UX16 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a participant declines or ignores the feedback prompt, the system
shall leave every other capability fully available, with no gating of any
kind.

**Intent**
Direct enforcement of BR15's "always optional, never a precondition"
Constraint.

**Success outcome**
Declining feedback has zero effect on any other capability.

**Failure / edge outcome**
Any capability found gated on having submitted feedback is a defect.

**Acceptance criteria**
- [ ] No feature requires prior feedback submission to function.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR15.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR069 — No Automated Penalty From Feedback Alone
**Traces from:** BR15, BR14
**Traced to:** UX16 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When feedback about an organizer is negative, the system shall never
trigger an automatic restriction or suspension from that feedback alone —
any consequential action against an organizer routes only through BR14's
reporting/moderation path.

**Intent**
Closes this BR's group by keeping the lightweight satisfaction signal
separate from consequential moderation action.

**Success outcome**
Negative feedback informs reputation only; no automatic organizer
restriction ever results from feedback alone.

**Failure / edge outcome**
Any automatic organizer restriction triggered by feedback volume/sentiment
alone is a defect.

**Acceptance criteria**
- [ ] No automated restriction/suspension logic reads feedback as its sole trigger.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR15 (Out of scope).
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR070 — External Event Ingestion, Normalization and Deduplication (Future)
**Traces from:** BR16
**Traced to:** UX19 (Step 3 UX)
**Priority:** Could
**Status:** Draft
**Confidence:** Low — explicitly deferred; BR16 itself is a scope-
traceability placeholder, not a near-term build commitment.

**Requirement (ISO 29148 form)**
When (in a future phase) an external source is connected, the system
shall ingest, normalize, validate, and deduplicate its events against
Milavn's own canonical records before indexing them into Discovery.

**Intent**
Records the required shape of this future capability so it is not
reinvented inconsistently whenever it is eventually prioritized.

**Success outcome**
For whenever built: external events appear in Discovery without
duplicating an existing native or previously-ingested record.

**Failure / edge outcome**
Not applicable at this stage — no ingestion exists to fail.

**Acceptance criteria**
- [ ] (Deferred) Not evaluated until this capability is prioritized.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (deferred) ·
Singular ✓ · Feasible ~ (deferred) · Verifiable ~ (deferred) · Correct ✓ ·
Conforming ✓

**Decisions** — none beyond BR16.
**Assumptions** — not scheduled for the current SDLC cycle (BR16
Assumptions).

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR071 — External Events Reuse the Existing Trust Taxonomy (Future)
**Traces from:** BR16, BR07
**Traced to:** UX19 (Step 3 UX)
**Priority:** Could
**Status:** Draft
**Confidence:** Low — same deferred-capability caveat as FR070.

**Requirement (ISO 29148 form)**
When (in a future phase) an external event is ingested, the system shall
classify it under BR07's existing taxonomy (typically External — Trusted
Source), and shall not build a separate trust model for external content.

**Intent**
Closes this BR's group by tying the future capability back to an
already-decided model rather than deferring that decision too.

**Success outcome**
For whenever built: external events display trust status using the same
taxonomy as native ones.

**Failure / edge outcome**
Not applicable at this stage.

**Acceptance criteria**
- [ ] (Deferred) Not evaluated until this capability is prioritized.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ~ (deferred) · Verifiable ~ (deferred) · Correct ✓ ·
Conforming ✓

**Decisions** — none beyond BR16 (Constraints).
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR072 — Natural-Language Intent Mapped to Existing Structured Operations (Future)
**Traces from:** BR17
**Traced to:** UX19 (Step 3 UX)
**Priority:** Could
**Status:** Draft
**Confidence:** Low — explicitly deferred; BR17 itself is a scope-
traceability placeholder.

**Requirement (ISO 29148 form)**
When (in a future phase) a participant expresses natural-language or
voice intent, the system shall translate it into the same structured
Discovery/Creation/Calendar operations already defined by FR004–FR029, via
an authorized tool-calling layer.

**Intent**
Records the required shape of this future capability, anchored to
already-built structured operations rather than a parallel system.

**Success outcome**
For whenever built: natural-language requests resolve to the same
underlying operations a manual action would produce.

**Failure / edge outcome**
Not applicable at this stage.

**Acceptance criteria**
- [ ] (Deferred) Not evaluated until this capability is prioritized.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (deferred) ·
Singular ✓ · Feasible ~ (deferred) · Verifiable ~ (deferred) · Correct ✓ ·
Conforming ✓

**Decisions** — none beyond BR17.
**Assumptions** — not scheduled for the current SDLC cycle.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR073 — AI-Initiated Actions Authorized and Attributable (Future)
**Traces from:** BR17, BR13
**Traced to:** UX19 (Step 3 UX)
**Priority:** Could
**Status:** Draft
**Confidence:** Low — same deferred-capability caveat as FR072.

**Requirement (ISO 29148 form)**
When (in a future phase) an AI-initiated action would be consequential,
the system shall require the same authorization and produce the same
attributable record as a human-initiated equivalent (FR060), and shall
not ship before the core structured product (FR001–FR069) is stable.

**Intent**
Closes this BR's group by tying the future AI capability's guardrail to
the one already established for organizer tooling (FR060), rather than
inventing a separate rule.

**Success outcome**
For whenever built: no AI-initiated action bypasses authorization a human
equivalent would face.

**Failure / edge outcome**
Not applicable at this stage.

**Acceptance criteria**
- [ ] (Deferred) Not evaluated until this capability is prioritized.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ~ (deferred) · Verifiable ~ (deferred) · Correct ✓ ·
Conforming ✓

**Decisions** — none beyond BR17 (Constraints).
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR074 — Surface Local-Business Demand to Vyapar (Future)
**Traces from:** BR18
**Traced to:** UX19 (Step 3 UX)
**Priority:** Could
**Status:** Draft
**Confidence:** Low — explicitly deferred; BR18 itself is a scope-
traceability placeholder.

**Requirement (ISO 29148 form)**
When (in a future phase) a circle/activity generates identifiable local-
business demand (e.g. a venue or equipment need), the system shall surface
that demand to MOD01 Vyapar, without itself capturing any payment.

**Intent**
Records the required shape of this future capability, respecting the
Vyapar/Payment Services module boundary from the start.

**Success outcome**
For whenever built: demand signals reach Vyapar; Milavn never processes a
transaction itself.

**Failure / edge outcome**
Not applicable at this stage.

**Acceptance criteria**
- [ ] (Deferred) Not evaluated until this capability is prioritized.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (deferred) ·
Singular ✓ · Feasible ~ (deferred) · Verifiable ~ (deferred) · Correct ✓ ·
Conforming ✓

**Decisions** — none beyond BR18.
**Assumptions** — not scheduled for the current SDLC cycle.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR075 — Clearly Labelled Sponsorship, Payment Capture Stays With MOD06 (Future)
**Traces from:** BR18
**Traced to:** UX19 (Step 3 UX)
**Priority:** Could
**Status:** Draft
**Confidence:** Low — same deferred-capability caveat as FR074.

**Requirement (ISO 29148 form)**
When (in a future phase) an activity carries sponsorship, the system shall
display that sponsorship clearly and visibly labelled, and shall route
any actual payment capture to MOD06 Payment Services rather than
processing it within Milavn.

**Intent**
Closes this BR's group by fixing the two non-negotiable rules (labelling,
module boundary) before any commerce mechanics are designed.

**Success outcome**
For whenever built: sponsored content is never presented as
unsponsored, and Milavn never touches payment capture directly.

**Failure / edge outcome**
Not applicable at this stage.

**Acceptance criteria**
- [ ] (Deferred) Not evaluated until this capability is prioritized.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ~ (deferred) · Verifiable ~ (deferred) · Correct ✓ ·
Conforming ✓

**Decisions** — none beyond BR18 (Constraints).
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR076 — Splash/Launch Screen
> **Ownership correction (2026-09-13, product decision):** user login and authentication have one source of truth, the parent **ForKhatri platform** (Common Platform Identity & Trust Service). Milavn does not design, build, or test its own Splash, Sign Up, Log In, Forgot/Reset Password, OTP, or Logout/Delete-Account flows; it consumes the member identity the platform has already resolved (`identity_bridge` in `architecture.md`). The text below is kept unchanged for traceability and as the hand-off brief to the platform team; nothing in it is Milavn implementation scope.

**Traces from:** BR01 (nearest existing BR — see Intent)
**Traced to:** UX01 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When the app is launched, the system shall display a brief branded splash
state while it determines the user's authentication state, then route
them to either onboarding (FR001) or the home experience (FR004).

**Intent**
Added by UX (Step 3) as a required prerequisite screen — no existing BR
names it, but a mobile-first web app without a launch/routing state is
not shippable. Traced to BR01 as the nearest existing BR since it gates
entry to the identity/profile flow.

**Success outcome**
Launch resolves quickly to the correct next screen based on auth state.

**Failure / edge outcome**
An indeterminate auth state (e.g. expired session) routes to Log In
(FR078) rather than hanging on the splash state.

**Acceptance criteria**
- [ ] Splash resolves to onboarding or home based on actual auth state.
- [ ] An indeterminate/expired auth state routes to Log In, never a hang.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond this FR's own Intent.
**Assumptions** — the underlying authentication-state check itself is
Common Platform Identity & Trust Service infrastructure (`modules.md`
Shared Concerns); this FR only fixes Milavn's own routing behavior once
that state is known.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR077 — Sign Up
> **Ownership correction (2026-09-13, product decision):** user login and authentication have one source of truth, the parent **ForKhatri platform** (Common Platform Identity & Trust Service). Milavn does not design, build, or test its own Splash, Sign Up, Log In, Forgot/Reset Password, OTP, or Logout/Delete-Account flows; it consumes the member identity the platform has already resolved (`identity_bridge` in `architecture.md`). The text below is kept unchanged for traceability and as the hand-off brief to the platform team; nothing in it is Milavn implementation scope.

**Traces from:** BR01 (nearest existing BR — see Intent)
**Traced to:** UX01 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a new user wants an account, the system shall let them sign up with
an email or phone number, and shall hand off to OTP verification (FR080)
before granting access to onboarding (FR001).

**Intent**
Added by UX (Step 3) as a required prerequisite screen — a mobile-first
web app without an account-creation path is not shippable. The underlying
identity/authentication infrastructure is Common Platform (`modules.md`
Shared Concerns); this FR fixes only the screen/flow shape Milavn's own
onboarding funnel needs from it.

**Success outcome**
A new user completes sign-up and reaches OTP verification.

**Failure / edge outcome**
An email/phone already registered is rejected with a clear path to Log In
instead, not a generic error.

**Acceptance criteria**
- [ ] Sign-up accepts email or phone.
- [ ] A duplicate account attempt offers Log In rather than a generic error.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond this FR's own Intent.
**Assumptions** — credential storage/validation itself is Common Platform
Identity & Trust Service infrastructure; this FR fixes only the
user-facing flow shape.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR078 — Log In
> **Ownership correction (2026-09-13, product decision):** user login and authentication have one source of truth, the parent **ForKhatri platform** (Common Platform Identity & Trust Service). Milavn does not design, build, or test its own Splash, Sign Up, Log In, Forgot/Reset Password, OTP, or Logout/Delete-Account flows; it consumes the member identity the platform has already resolved (`identity_bridge` in `architecture.md`). The text below is kept unchanged for traceability and as the hand-off brief to the platform team; nothing in it is Milavn implementation scope.

**Traces from:** BR01 (nearest existing BR — see Intent)
**Traced to:** UX01 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a returning user wants to access their account, the system shall let
them log in with their registered email/phone, and shall route them to
the home experience (FR004) on success.

**Intent**
Added by UX (Step 3) as a required prerequisite screen, for the same
reason as FR077.

**Success outcome**
A returning user reaches home directly on successful login.

**Failure / edge outcome**
Incorrect credentials are rejected with a clear retry path and a route to
Forgot Password (FR079).

**Acceptance criteria**
- [ ] Successful login routes directly to home.
- [ ] Failed login offers a Forgot Password path.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond this FR's own Intent.
**Assumptions** — same as FR077.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR079 — Forgot/Reset Password
> **Ownership correction (2026-09-13, product decision):** user login and authentication have one source of truth, the parent **ForKhatri platform** (Common Platform Identity & Trust Service). Milavn does not design, build, or test its own Splash, Sign Up, Log In, Forgot/Reset Password, OTP, or Logout/Delete-Account flows; it consumes the member identity the platform has already resolved (`identity_bridge` in `architecture.md`). The text below is kept unchanged for traceability and as the hand-off brief to the platform team; nothing in it is Milavn implementation scope.

**Traces from:** BR01 (nearest existing BR — see Intent)
**Traced to:** UX01 (Step 3 UX)
**Priority:** Should
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a user cannot log in, the system shall let them request a password
reset via their registered email/phone, and shall let them set a new
password after verifying that request.

**Intent**
Added by UX (Step 3) as a required prerequisite screen; Should rather than
Must since it is recovery-path, not the critical path itself (FR077/FR078
already cover account creation and ordinary login).

**Success outcome**
A user regains access after completing the reset flow.

**Failure / edge outcome**
An unrecognized email/phone gives a neutral response (not confirming
whether an account exists), consistent with standard account-enumeration
protection.

**Acceptance criteria**
- [ ] Reset request does not reveal whether an account exists for a given email/phone.
- [ ] Successful reset lets the user log in with the new password immediately.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond this FR's own Intent.
**Assumptions** — same as FR077.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR080 — OTP / Phone-Email Verification
> **Ownership correction (2026-09-13, product decision):** user login and authentication have one source of truth, the parent **ForKhatri platform** (Common Platform Identity & Trust Service). Milavn does not design, build, or test its own Splash, Sign Up, Log In, Forgot/Reset Password, OTP, or Logout/Delete-Account flows; it consumes the member identity the platform has already resolved (`identity_bridge` in `architecture.md`). The text below is kept unchanged for traceability and as the hand-off brief to the platform team; nothing in it is Milavn implementation scope.

**Traces from:** BR01 (nearest existing BR — see Intent)
**Traced to:** UX01 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a user needs to verify a phone number or email (sign-up, password
reset), the system shall send a one-time code and let them enter it to
complete verification, supporting platform autofill where available.

**Intent**
Added by UX (Step 3) as a required prerequisite screen, shared by FR077
and FR079.

**Success outcome**
A correctly-entered or autofilled code completes verification.

**Failure / edge outcome**
An incorrect or expired code is rejected with a clear resend option, not
a dead end.

**Acceptance criteria**
- [ ] Verification supports platform autofill of the received code.
- [ ] An expired/incorrect code offers a resend path.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond this FR's own Intent.
**Assumptions** — OTP delivery itself is Common Platform notification
infrastructure (`modules.md` Shared Concerns).

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR081 — Location Permission Priming
**Traces from:** BR09
**Traced to:** UX02 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When Discovery first needs the user's locality, the system shall show a
benefit-focused explanation before triggering the platform's native
location-permission prompt, and shall let the user decline and still set
locality manually (per BR01/BR09's approximate-locality model).

**Intent**
Added by UX (Step 3) as a required prerequisite screen — a soft-ask
priming step before the one-shot native permission prompt, since a denied
native prompt cannot easily be re-asked.

**Success outcome**
A user who grants permission gets locality auto-detected; a user who
declines still sets locality manually with zero loss of core function.

**Failure / edge outcome**
A declined permission never blocks onboarding or Discovery — it falls
back to manual locality entry (FR001).

**Acceptance criteria**
- [ ] A soft-ask explanation appears before the native permission prompt.
- [ ] Declining location access does not block any other capability.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR09.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR082 — Notification Permission Priming
**Traces from:** BR12
**Traced to:** UX02 (Step 3 UX)
**Priority:** Should
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When the user first reaches a moment where a notification would be
valuable (e.g. after their first RSVP), the system shall show a
benefit-focused explanation before triggering the native
notification-permission prompt.

**Intent**
Added by UX (Step 3) as a required prerequisite screen; Should rather than
Must since the product remains fully usable without push notifications
enabled (in-app notification inbox, FR086, still works).

**Success outcome**
Permission is requested at a moment of clear, demonstrated value, not at
first launch.

**Failure / edge outcome**
A declined permission never blocks any other capability — in-app
notifications (FR086) still function.

**Acceptance criteria**
- [ ] The priming moment is tied to a concrete action (e.g. first RSVP), not first launch.
- [ ] Declining push notifications does not block in-app notifications.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR12.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR083 — Main Navigation Shell
**Traces from:** BR02 (nearest existing BR — see Intent)
**Traced to:** UX03 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When an authenticated user is anywhere in the core app, the system shall
present a persistent bottom navigation bar giving one-tap access to Home
(Discovery), Circles, Calendar, Notifications, and Profile.

**Intent**
Added by UX (Step 3) as a required prerequisite screen — the persistent
chrome every other screen in the core app renders within. Traced to BR02
since Discovery/Home is the app's primary destination.

**Success outcome**
Every core-app screen is reachable from the nav bar in one tap.

**Failure / edge outcome**
A screen found unreachable from the nav bar (requiring a multi-step
detour) is a defect.

**Acceptance criteria**
- [ ] All five named destinations are reachable in one tap from anywhere in the core app.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond this FR's own Intent.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR084 — Generic Empty, Offline and Error State Handling
**Traces from:** BR02 (nearest existing BR — see Intent)
**Traced to:** UX18 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When any screen has no content, loses connectivity, or encounters an
error, the system shall present a specific, actionable empty/offline/error
state rather than a blank screen or a generic technical error message.

**Intent**
Added by UX (Step 3) as a required, cross-cutting prerequisite pattern —
applies to every screen in this inventory, not one BR specifically; traced
to BR02 as the highest-traffic surface where this pattern is most visible.

**Success outcome**
Every screen has a defined, specific empty/offline/error treatment.

**Failure / edge outcome**
A blank screen or raw technical error message shown to the user anywhere
is a defect.

**Acceptance criteria**
- [ ] No screen shows a blank state or raw technical error to the user.
- [ ] Offline state offers a retry action, not a dead end.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond this FR's own Intent.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR085 — Account and Profile Settings Screen
**Traces from:** BR01
**Traced to:** UX17 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a user wants to manage their account, the system shall provide a
settings screen exposing profile editing (FR001/FR003), language
preference (FR002), and location-sharing precision (FR041) as a single,
organized destination.

**Intent**
Added by UX (Step 3) as a required container screen for existing
profile/preference FRs that had no single screen named for them yet.

**Success outcome**
A user finds and edits any profile/preference control from one screen.

**Failure / edge outcome**
Any existing profile/preference FR found with no reachable UI surface is a
defect.

**Acceptance criteria**
- [ ] Profile, language, and location-precision controls are all reachable from this one screen.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond this FR's own Intent.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR086 — Notification Inbox Screen
**Traces from:** BR12
**Traced to:** UX12 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a user opens Notifications, the system shall list all four
notification classes (FR051–FR054) in one reverse-chronological inbox,
distinguishing Important-class items visually from the other three.

**Intent**
Added by UX (Step 3) as a required container screen for FR051–FR055's
notification classes, which had no single screen named for them yet.

**Success outcome**
A user sees all their notifications in one place, with Important items
clearly distinguished.

**Failure / edge outcome**
A notification generated by FR051–FR054 that never appears in this inbox
is a defect.

**Acceptance criteria**
- [ ] All four notification classes appear in this inbox.
- [ ] Important-class items are visually distinguished from the other three.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond this FR's own Intent.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR087 — Help/Support Screen
**Traces from:** (none — pure technical necessity, see Intent)
**Traced to:** UX17 (Step 3 UX)
**Priority:** Should
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a user needs help, the system shall provide a reachable support
destination with common questions and a contact/report path (reusing
FR061's reporting mechanism where relevant).

**Intent**
Added by UX (Step 3) as a required prerequisite screen with no BR behind
it — a genuine technical/product necessity (a shippable app needs a help
path) rather than a traced business capability.

**Success outcome**
A user finds help or a contact path without leaving the app.

**Failure / edge outcome**
No reachable help/support destination anywhere in the app is a defect.

**Acceptance criteria**
- [ ] A help/support destination is reachable from Account Settings (FR085).

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond this FR's own Intent.
**Assumptions** — none.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date

---

## FR088 — Logout and Delete-Account Confirmation
> **Ownership correction (2026-09-13, product decision):** user login and authentication have one source of truth, the parent **ForKhatri platform** (Common Platform Identity & Trust Service). Milavn does not design, build, or test its own Splash, Sign Up, Log In, Forgot/Reset Password, OTP, or Logout/Delete-Account flows; it consumes the member identity the platform has already resolved (`identity_bridge` in `architecture.md`). The text below is kept unchanged for traceability and as the hand-off brief to the platform team; nothing in it is Milavn implementation scope.

**Traces from:** BR01
**Traced to:** UX17 (Step 3 UX)
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a user logs out or requests account deletion, the system shall
require an explicit confirmation step for deletion specifically (not
logout), and shall clearly state what deletion does and does not remove.

**Intent**
Added by UX (Step 3) as a required prerequisite screen — deletion is a
high-stakes, irreversible action needing a deliberate confirmation step,
per the same "high-stakes action needs a modal, not a bottom sheet"
principle applied throughout this module's UX.

**Success outcome**
Logout is immediate; deletion requires explicit confirmation and clearly
communicates its effect.

**Failure / edge outcome**
Account deletion completing without an explicit confirmation step is a
defect.

**Acceptance criteria**
- [ ] Logout requires no confirmation step.
- [ ] Deletion requires an explicit confirmation step and states its effect.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond this FR's own Intent.
**Assumptions** — the actual account-deletion mechanics (data retention/
purge timelines) are Common Platform Identity & Trust Service
infrastructure; this FR fixes only the user-facing confirmation flow.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- (none yet)

**Approval:** Product Manager / BA — [ ] Approved — name, date
