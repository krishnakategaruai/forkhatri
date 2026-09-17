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
| 2026-09-14 | **FR089–FR101 added** for the capabilities the owner asked for during Step 9 beyond the sealed MVP: ask-first discovery, smart fill, activity thread, moments, circle board, person page, circle locality, trust-scoped messaging, live expressions with expressive avatars, weekly digest, poster share, use-where-I-am, notification de-duplication/live status. Each entry carries the requirement, the *why*, the owner decision that sourced it and acceptance criteria; nothing sealed was changed. | Owner: "are you also updating .md files on what you're doing for that FR and why — I want each agent responsible and accounted" — krishna kategaru (autonomous). |
| 2026-09-15 | **FR102 added — Paid spots.** Milavn's full side of paid activities (price, hold, waitlist offers, refund rule, organizer totals, payment history) behind a provider-agnostic Payment Services port; the payment vendor and MOD06 are recorded as an external blocker. | Owner: "payments section and everything you can implement, but skip the payment vendor — keep it as a blocker" — krishna kategaru (autonomous). |
| 2026-09-15 | **FR112–FR113 added — regulars and photo privacy** (research roadmap items 11–12): keep my spot each time in a free series, own "X of the last Y", welcome back after a miss; "don't include me", ask before sharing, instant removal of a photo of me. | Owner: "do rigorous research … make Milavn much better in behaviour" — krishna kategaru (autonomous). |
| 2026-09-17 | **FR115–FR124 added** — the remaining twelve capabilities the owner picked: circle join questions and approval, assistants, circle polls (which day / which one), free right now, conversation cards, familiar faces, the steady-host label, followed calendars with an .ics feed, chapters under an umbrella, and community drives. | Owner's selection from the 2026-09-17 research — krishna kategaru (autonomous). |
| 2026-09-17 | **FR114 added — bringing someone with you.** The owner reviewed a capability study of Meetup, Luma, Partiful, Eventbrite, Posh, Dice, WhatsApp Communities, Bumble BFF, Timeleft, 222, Peanut, Geneva, Heylo, BAND, Nextdoor, Strava, Discord, Couchsurfing, Kutumb and Mera Samaj, and picked 14 capabilities to add. This is the first of them. | Owner's selection from the 2026-09-17 research — krishna kategaru (autonomous). |
| 2026-09-15 | **FR106 added — would meet again** (research roadmap item 5): private picks among people who were there; both told once only when mutual; "You'd both meet again" on People. | Same owner instruction — krishna kategaru (autonomous). |

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
| (Step 9 additions on owner decisions, 2026-09-14 — see Revision history and `DESIGN-DIRECTION-2030.md`) | FR089–FR101 | Yes |
| (Step 9 addition on owner instruction, 2026-09-15 — paid spots; see `RESEARCH-BEHAVIOUR-2026.md` for the behaviour roadmap FR103+) | FR102 | Yes |
| (Step 9 research roadmap, 2026-09-15 — showing up) | FR103–FR105 | Yes |
| (Step 9 research roadmap, 2026-09-15 — belonging and safety) | FR107–FR109 | Yes |
| (Step 9 research roadmap, 2026-09-15 — discovery that fits) | FR110–FR111 | Yes |
| (Step 9 research roadmap, 2026-09-15 — regulars and photo privacy) | FR112–FR113 | Yes |
| (Step 9 research roadmap, 2026-09-15 — would meet again) | FR106 | Yes |
| (Step 9, competitor research picks, 2026-09-17) | FR114 | Yes |
| (Step 9, competitor research picks, 2026-09-17 — the rest of the batch) | FR115–FR124 | Yes |

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

## FR089 — Ask-First Natural-Language Discovery
> **Added in Step 9 on an explicit owner decision (2026-09-14).** Recorded here so the requirement, its reason and its source are owned by a number, tested in `05-test-scenarios.md`, and accounted for in `09-implementation.md`.

**Traces from:** BR02
**Traced to:** UX04/UX05; `09-implementation.md` IMP21–IMP24
**Priority:** Must
**Status:** Implemented (Step 9), awaiting owner approval of the text
**Confidence:** High

**Requirement (ISO 29148 form)**
When a member types or speaks a request in English, Hindi or Telugu (e.g. "badminton this weekend near me"), the system shall interpret it into discovery filters, show the interpretation back as editable chips before results are shown, and, when nothing matches, widen the search step by step (distance, then date) and say so.

**Intent (why)**
Thesis §31–§32 and §40 call for natural-language and voice interaction; Brand §13–§14 for text-and-voice in Indian languages. Deterministic parsing over the module's own vocabulary keeps the interpretation legible and keeps AI out of the permission path (§33).

**Source / decision**
Owner instruction 2026-09-14 ("make yourself live in 2030 with all AI upgrades"); DESIGN-DIRECTION-2030.md §3.1.

**Acceptance criteria**
- [x] Typed and spoken asks produce the same filters.
- [x] Every understood token is shown as a chip and can be cleared.
- [x] An empty result widens once for distance and once for date, each announced to the person.
- [x] Works in en, hi, te.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR090 — Smart Fill for Activity Creation
> **Added in Step 9 on an explicit owner decision (2026-09-14).** Recorded here so the requirement, its reason and its source are owned by a number, tested in `05-test-scenarios.md`, and accounted for in `09-implementation.md`.

**Traces from:** BR03
**Traced to:** UX07; `09-implementation.md` IMP21–IMP24
**Priority:** Must
**Status:** Implemented (Step 9), awaiting owner approval of the text
**Confidence:** High

**Requirement (ISO 29148 form)**
When a member describes an activity in one line ("badminton tomorrow 7pm at Madhapur for 8 people"), the system shall pre-fill category, title, time, place and capacity, show which words it used, and require the member to confirm before anything is created.

**Intent (why)**
Thesis §31 (natural-language creation: extract activity, date, time, locality, capacity; user confirms; then create). Category words stay in the title ("Chai and chapters" is a name).

**Source / decision**
Owner instruction 2026-09-14; DESIGN-DIRECTION-2030.md §3.1.

**Acceptance criteria**
- [x] No activity is created without the Create tap.
- [x] Matched words are echoed as chips.
- [x] Unmatched fields stay empty for the member to fill.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR091 — Activity Thread ("Plan Together")
> **Added in Step 9 on an explicit owner decision (2026-09-14).** Recorded here so the requirement, its reason and its source are owned by a number, tested in `05-test-scenarios.md`, and accounted for in `09-implementation.md`.

**Traces from:** BR04
**Traced to:** UX06; `09-implementation.md` IMP21–IMP24
**Priority:** Must
**Status:** Implemented (Step 9), awaiting owner approval of the text
**Confidence:** High

**Requirement (ISO 29148 form)**
When a member is going to, interested in, waitlisted for, checked in to or organising an activity, the system shall give them a message thread with the other people in that set; nobody else can read or write it.

**Intent (why)**
Thesis §57 takes "simple coordination" from WhatsApp; §68 says not a WhatsApp clone. Attendance stays private (FR040) because only the RSVP set sees the thread.

**Source / decision**
Owner instruction 2026-09-14 ("why limit ourselves with MVP scope"); DESIGN-DIRECTION-2030.md.

**Acceptance criteria**
- [x] A non-participant receives 403 on read and write.
- [x] Blocked pairs never see each other's messages.
- [x] A member can retract their own message.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR092 — Moments (Photos After an Activity)
> **Added in Step 9 on an explicit owner decision (2026-09-14).** Recorded here so the requirement, its reason and its source are owned by a number, tested in `05-test-scenarios.md`, and accounted for in `09-implementation.md`.

**Traces from:** BR15
**Traced to:** UX06; `09-implementation.md` IMP21–IMP24
**Priority:** Must
**Status:** Implemented (Step 9), awaiting owner approval of the text
**Confidence:** High

**Requirement (ISO 29148 form)**
When an activity has happened, the system shall let the people who were there (checked in, attended, or organising) add photos to it, visible to the same set; others cannot see them.

**Intent (why)**
Strava's "activity becomes identity" and Meetup's event photos, kept private to the people who were there so no one's attendance is exposed (FR040).

**Source / decision**
Owner instruction 2026-09-14; DESIGN-DIRECTION-2030.md.

**Acceptance criteria**
- [x] Upload is refused for people who were not there.
- [x] JPEG/PNG/WebP only.
- [x] The uploader can remove their own photo.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR093 — Circle Board
> **Added in Step 9 on an explicit owner decision (2026-09-14).** Recorded here so the requirement, its reason and its source are owned by a number, tested in `05-test-scenarios.md`, and accounted for in `09-implementation.md`.

**Traces from:** BR05
**Traced to:** UX09; `09-implementation.md` IMP21–IMP24
**Priority:** Must
**Status:** Implemented (Step 9), awaiting owner approval of the text
**Confidence:** High

**Requirement (ISO 29148 form)**
When a member belongs to a circle, the system shall give the circle a members-only board for posts; non-members cannot read it.

**Intent (why)**
Meetup's group discussions, scoped to membership (FR023: nothing outside the Circle package reads membership).

**Source / decision**
Owner instruction 2026-09-14.

**Acceptance criteria**
- [x] Non-members get an empty board and cannot post.
- [x] Posts are shown newest first with author and time.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR094 — Person Page
> **Added in Step 9 on an explicit owner decision (2026-09-14).** Recorded here so the requirement, its reason and its source are owned by a number, tested in `05-test-scenarios.md`, and accounted for in `09-implementation.md`.

**Traces from:** BR10
**Traced to:** UX10; `09-implementation.md` IMP21–IMP24
**Priority:** Must
**Status:** Implemented (Step 9), awaiting owner approval of the text
**Confidence:** High

**Requirement (ISO 29148 form)**
When a member taps another person anywhere in the app, the system shall show a page with that person's name, bio, interests, earned reputation labels, locality at the precision that person chose, the circles the two share, and the public activities they host — and nothing about their attendance history.

**Intent (why)**
Thesis §22 (contextual people discovery), §21 (privacy), FR040/FR041. No follow, like or open message button: you meet people at activities.

**Source / decision**
Owner instruction 2026-09-14.

**Acceptance criteria**
- [x] Blocked pairs get 404, not a hint.
- [x] Locality is clamped to the person's own precision setting.
- [x] Attendance history is never listed.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR095 — Circle Home Locality and Nearby Discovery
> **Added in Step 9 on an explicit owner decision (2026-09-14).** Recorded here so the requirement, its reason and its source are owned by a number, tested in `05-test-scenarios.md`, and accounted for in `09-implementation.md`.

**Traces from:** BR05
**Traced to:** UX09; `09-implementation.md` IMP21–IMP24
**Priority:** Must
**Status:** Implemented (Step 9), awaiting owner approval of the text
**Confidence:** High

**Requirement (ISO 29148 form)**
When a member discovers circles, the system shall list circles in their own locality first (Near me / All), and a new circle shall default to its creator's locality or "anywhere".

**Intent (why)**
Thesis §84 #6 local relevance; the owner asked "can I find nearby circles?" and the answer was no.

**Source / decision**
Owner question 2026-09-14; migration 012.

**Acceptance criteria**
- [x] Circles carry an approximate place only (FR038).
- [x] Near me returns only circles in the viewer's locality or city-wide ones.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR096 — Trust-Scoped Messaging
> **Added in Step 9 on an explicit owner decision (2026-09-14).** Recorded here so the requirement, its reason and its source are owned by a number, tested in `05-test-scenarios.md`, and accounted for in `09-implementation.md`.

**Traces from:** BR10
**Traced to:** UX21 (new); `09-implementation.md` IMP21–IMP24
**Priority:** Must
**Status:** Implemented (Step 9), awaiting owner approval of the text
**Confidence:** High

**Requirement (ISO 29148 form)**
When a member wants to message another person, the system shall allow it only if the two already share an activity or a circle and neither has blocked the other; it shall support 1:1 and group chats, photos, emoji reactions, typing and presence ("active now"), delivered live.

**Intent (why)**
Thesis §41 lists messaging under the mobile primary experience; §57 takes simple coordination from WhatsApp; Brand §15 forbids likes/followers (reactions instead). Trust scope is decided by one definer helper so it cannot be bypassed.

**Source / decision**
Owner decision 2026-09-14 ("i want messaging system like snapchat"; "yes i agree with your recommendations"); DESIGN-DIRECTION-2030.md §5–§6.

**Acceptance criteria**
- [x] A stranger receives 403 with a plain explanation.
- [x] A non-member of a conversation receives 404 on read.
- [x] Events (message, reaction, retract, typing, presence) arrive over the socket within a second; polling covers a lost socket.
- [x] No read receipts, no forwarding chains, no broadcast lists.
- [x] The chat shows why the two people can talk: the next activity they share (date and time), otherwise the circle they share, linked; approximate place only. *(Added 2026-09-14 with chat room v3, IMP26: the trust scope is made visible instead of implied.)*
- [x] Presence is honest: **Here now** only while the person has this conversation open; **Active now** when they used Milavn in the last two minutes; otherwise **Active N min / h / d ago**. *(IMP26 — added after the owner saw "Here now" for someone who had already left.)*

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR097 — Live Expressions and Expressive Avatars
> **Added in Step 9 on an explicit owner decision (2026-09-14).** Recorded here so the requirement, its reason and its source are owned by a number, tested in `05-test-scenarios.md`, and accounted for in `09-implementation.md`.

**Traces from:** BR10
**Traced to:** UX21 (new); `09-implementation.md` IMP21–IMP24
**Priority:** Must
**Status:** Implemented (Step 9), awaiting owner approval of the text
**Confidence:** High

**Requirement (ISO 29148 form)**
When two or more members are in a chat, the system shall show each person as an expressive cartoon avatar whose face animates with that person's current expression; the expression shall come from on-device face detection (opt-in, camera indicator visible) or from a manual mood row, and only the expression word — never an image — shall leave the device.

**Intent (why)**
The owner's Snapchat reference: "their emotion is actually shown as avatar shows, like smiling". Thesis §21 privacy-first and Brand §9 privacy by design rule out sending video.

**Source / decision**
Owner decision 2026-09-14 (video skipped for now).

**Acceptance criteria**
- [x] Expressions are one of: smile, laugh, surprised, wink, thinking, love, neutral.
- [x] No frame is uploaded; the API only ever receives the word.
- [x] Camera is opt-in per chat and visibly indicated; the mood row works without a camera.
- [x] The other person's avatar rises above the composer while they are in the chat (Snapchat's *Friends in Chat* pattern) and, with the header avatar, animates within a second of a change; in group chats avatars also sit beside messages. *(Chat room v3, IMP26: the v2 always-on "stage" panel was removed.)*
- [x] Your own avatar is the mood control: a tray shows you in all seven expressions; a tap shares your live mood, tapping the chosen one again sends it as a sticker message.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR098 — Personal Weekly Digest
> **Added in Step 9 on an explicit owner decision (2026-09-14).** Recorded here so the requirement, its reason and its source are owned by a number, tested in `05-test-scenarios.md`, and accounted for in `09-implementation.md`.

**Traces from:** BR02
**Traced to:** UX04; `09-implementation.md` IMP21–IMP24
**Priority:** Must
**Status:** Implemented (Step 9), awaiting owner approval of the text
**Confidence:** High

**Requirement (ISO 29148 form)**
When a member opens Home, the system shall show up to three sentences composed from their own real data (things they are going to, what is on today/tomorrow near them, how many have circle-mates going), in their language.

**Intent (why)**
Thesis §67 "immediately understand"; no model, no invention — sentences from counts.

**Source / decision**
Owner instruction 2026-09-14.

**Acceptance criteria**
- [x] Every number in the digest is a real count from the person's own view.
- [x] Available in en, hi, te.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR099 — Shareable Poster Image
> **Added in Step 9 on an explicit owner decision (2026-09-14).** Recorded here so the requirement, its reason and its source are owned by a number, tested in `05-test-scenarios.md`, and accounted for in `09-implementation.md`.

**Traces from:** BR11
**Traced to:** UX06; `09-implementation.md` IMP21–IMP24
**Priority:** Must
**Status:** Implemented (Step 9), awaiting owner approval of the text
**Confidence:** High

**Requirement (ISO 29148 form)**
When a member shares an activity, the system shall offer a poster image (cover, title, date, place, host, QR of the public link) rendered on the device, suitable for WhatsApp status and Instagram stories.

**Intent (why)**
Thesis §43 (share through WhatsApp, Instagram, SMS, email, QR); a link alone is not what people forward in India.

**Source / decision**
Owner instruction 2026-09-14; DESIGN-DIRECTION-2030.md §3.3.

**Acceptance criteria**
- [x] Rendered locally; nothing uploaded.
- [x] QR opens the public page without login (FR046).

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR100 — Use Where I Am (One-Shot Device Position)
> **Added in Step 9 on an explicit owner decision (2026-09-14).** Recorded here so the requirement, its reason and its source are owned by a number, tested in `05-test-scenarios.md`, and accounted for in `09-implementation.md`.

**Traces from:** BR09
**Traced to:** UX04; `09-implementation.md` IMP21–IMP24
**Priority:** Must
**Status:** Implemented (Step 9), awaiting owner approval of the text
**Confidence:** High

**Requirement (ISO 29148 form)**
When a member taps "Use where I am", the system shall read the device position once, snap it to the nearest approximate locality, and show Around You for that locality for the current session — without storing coordinates or changing the profile.

**Intent (why)**
Owner question "does the app take real-time location now?" answered honestly; thesis §21 and FR038 forbid exact locations and tracking.

**Source / decision**
Owner instruction 2026-09-14 ("real time right now").

**Acceptance criteria**
- [x] No coordinates are persisted.
- [x] The stored profile locality is unchanged.
- [x] The choice can be cleared.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR101 — Notification De-duplication and Live Status
> **Added in Step 9 on an explicit owner decision (2026-09-14).** Recorded here so the requirement, its reason and its source are owned by a number, tested in `05-test-scenarios.md`, and accounted for in `09-implementation.md`.

**Traces from:** BR12
**Traced to:** UX04/UX15; `09-implementation.md` IMP21–IMP24
**Priority:** Must
**Status:** Implemented (Step 9), awaiting owner approval of the text
**Confidence:** High

**Requirement (ISO 29148 form)**
The system shall not deliver the same notification (member, class, title, source activity) twice within 24 hours, shall refuse an identical organizer update within an hour, and shall mark activities that are on right now as Live and those starting within 90 minutes with a countdown.

**Intent (why)**
Thesis §84 #13 need over noise; §39 notifications with purpose; live status computed on the device.

**Source / decision**
Owner instruction 2026-09-14; migration 011.

**Acceptance criteria**
- [x] Join/withdraw/join produces one alert for the organizer.
- [x] The second identical announcement inside an hour returns 409.
- [x] Live and countdown states refresh at least every minute.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓


## FR102 — Paid Spots
> **Added in Step 9 on an explicit owner instruction (2026-09-15).** Recorded here so the requirement, its reason and its source are owned by a number, tested in `05-test-scenarios.md` (TS193–TS195), and accounted for in `09-implementation.md` (IMP27).

**Traces from:** BR18 (paid and sponsored activity boundary: capture stays with MOD06), thesis §38 (no-shows), §53–§55 (revenue values)
**Traced to:** `09-implementation.md` IMP27; TS193–TS195
**Priority:** Must
**Status:** Implemented (Step 9) on Milavn's side; the payment vendor and MOD06 Payment Services are an external blocker
**Confidence:** High

**Requirement (ISO 29148 form)**
When an organizer sets a price for an activity, the system shall let a member take a spot only by paying through Payment Services; hold the spot for 15 minutes while the payment is in progress so no two people pay for one spot; place members on a free waitlist when the activity is full and offer a freed spot to the next person in order with a payment window; refund in full when a member withdraws before the organizer's refund cutoff and always when the organizer cancels or a lapsed payment finds the activity full; show the organizer totals only; lock the price and refund window once anyone is paying or has paid; and never store card or UPI data or let payment data influence trust or ranking.

**Intent (why)**
Some activities have real costs (a court booking, a food crawl). The thesis says to "monetise value creation, not community belonging" (§53) and never to make trust purchasable (§55), so free stays the default and nothing about a free activity changes. Research on deposits shows that charging to commit pushes most people away (Halpern et al. 2015, *NEJM*: 14% vs 90% acceptance), so a price is for real costs only, and the refund rule is one clear sentence the member reads before paying.

**Source / decision**
Owner, 2026-09-15: "payments section and everything you can implement, but you can skip adding the payment vendor; this is an external dependency which I will take care of; keep this as a blocker, but implementation-wise complete what all you could."

**Acceptance criteria**
- [x] A price is optional on create and edit (₹1 to ₹1,00,000) with a refund window of until the start, 1 day, 2 days or 1 week before.
- [x] The free Going toggle is refused on a paid activity; joining returns a hold and a checkout, or a free waitlist place when full.
- [x] A held spot counts as taken for everyone; a hold that lapses gives the spot back and it is offered to the waitlist.
- [x] Withdrawing before the cutoff refunds in full; after the cutoff the member is told before confirming that there is no refund.
- [x] An organizer cancellation refunds every paid spot automatically; members are notified at every money moment.
- [x] The organizer sees totals only (paid spots, collected, refunded, people paying now) and never who paid.
- [x] The price and refund window cannot change once anyone is paying or has paid.
- [x] Payment events are accepted only from Payment Services with its key; a redelivered event changes nothing.
- [x] Trust and discovery code never reads payment data (FR036).
- [ ] Money actually moves through the payment vendor via MOD06 Payment Services — **blocked (external dependency)**.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR103 — Still Coming? (Free the Spot Kindly)
> **Added in Step 9 from the owner's research instruction (2026-09-15)** — `RESEARCH-BEHAVIOUR-2026.md` roadmap item 2. Tested in TS196; built in IMP28.

**Traces from:** BR05 (showing up), thesis §38 (no-shows: "confirmation requests", "still coming? prompts", "do not punish users")
**Traced to:** `09-implementation.md` IMP28; TS196
**Priority:** Must
**Status:** Implemented (Step 9)
**Confidence:** High

**Requirement (ISO 29148 form)**
When a member is going to an activity that starts within the next day, the system shall ask once whether they are still coming, in the app and on the activity page, offering "Yes, I'm coming" and "Can't make it · free my spot"; freeing a spot shall immediately promote the next person on the waitlist (or, for a paid spot, follow the refund rule); the question shall never mention penalties, and it shall not be asked of the host or of someone who joined in the last three hours.

**Intent (why)**
A reminder that says a missed spot affects someone else cut missed appointments from 21.1% to 14.2% and raised early cancellations from 17.2% to 26.3% (Berliner Senderey et al. 2020, 161,587 appointments). Early cancellation is the real win for organizers: the spot goes to someone who will come.

**Acceptance criteria**
- [x] Sent 20–28 hours before the start to people going who have not confirmed, at most once each.
- [x] The words name the waitlist when people are waiting ("so the person on the waitlist can join"), and point paid spots to the refund rule.
- [x] "Yes, I'm coming" is recorded once and the question disappears; "free my spot" promotes the waitlist.
- [x] No penalty, score or label is ever attached to an answer.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR104 — Two Reminders That Repeat the Member's Plan
> **Added in Step 9 from the owner's research instruction (2026-09-15)** — roadmap item 3. Tested in TS197; built in IMP28.

**Traces from:** FR052 (reminders), BR05
**Traced to:** IMP28; TS197
**Priority:** Must
**Status:** Implemented (Step 9)
**Confidence:** High

**Requirement (ISO 29148 form)**
The system shall remind a member who is going three days before an activity (day, time, locality, "put it in your calendar") and two hours before it (time, locality and, when given, the member's own travel plan, with a welcome line for someone coming alone); members who are only interested shall get one nudge the day before; no reminder shall be sent twice.

**Intent (why)**
Two reminders beat one (Steiner et al. 2018: missed visits 4.4% with reminders 3 days and 1 day before, versus 5.3–5.8% with one). Repeating a person's own plan is what makes planning prompts work (Nickerson & Rogers 2010).

**Acceptance criteria**
- [x] 66–78 hours and 90–150 minutes windows; each reminder claimed in the database before sending, so overlapping runs never duplicate.
- [x] The two-hour reminder repeats the travel plan and, for "on my own", suggests saying hello to the host.
- [x] The host is never sent attendee reminders.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR105 — One-Tap Plan: How and With Whom
> **Added in Step 9 from the owner's research instruction (2026-09-15)** — roadmap item 4. Tested in TS198; built in IMP28.

**Traces from:** BR05, FR015
**Traced to:** IMP28; TS198
**Priority:** Should
**Status:** Implemented (Step 9)
**Confidence:** High

**Requirement (ISO 29148 form)**
When a member is going or waitlisted, the activity page shall ask, optionally and in place, how they are getting there (on foot, two-wheeler, car, cab or auto, metro or bus) and who they are coming with (on my own, a friend, family); the answer shall be visible only to the member and the host, changeable at any time, and repeated back in the two-hour reminder.

**Intent (why)**
Asking when and how raised follow-through in large field experiments (Milkman et al. 2011: 33.1% → 37.3%; Nickerson & Rogers 2010: +4.1 points, +9.1 for people living alone). "On my own" also lets a host welcome a newcomer (FR108, planned).

**Acceptance criteria**
- [x] Two chip rows, saved on tap, collapsing to "Your plan: … · Change" once both are answered.
- [x] Unknown values are refused; only people going or waitlisted can set a plan.
- [x] Setting a plan does not postpone the "still coming?" check.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR107 — Thank the Host, and One Private Question Afterwards
> **Added in Step 9 from the owner's research instruction (2026-09-15)** — `RESEARCH-BEHAVIOUR-2026.md` roadmap item 6. Tested in TS199; built in IMP29.

**Traces from:** BR08 (reputation and feedback), FR066–FR069, owner decision "no public star ratings"
**Traced to:** `09-implementation.md` IMP29; TS199
**Priority:** Must
**Status:** Implemented (Step 9)
**Confidence:** High

**Requirement (ISO 29148 form)**
After a member has attended an activity, the system shall let them thank the host once (a one-tap preset or their own words, up to 140 characters, rewordable) and answer one private question, "Would you come again? Yes / Maybe / No", with an optional line; the host shall be notified of a thank-you once, in the attendee's words, and shall see only counts (came, first-timers, would come again) plus the notes sent to them; a host thanked three times shall earn the qualitative label "Appreciated host"; no individual answer is shown to anyone.

**Intent (why)**
People undervalue how much thanks means to the person thanked (Kumar & Epley 2018) and a short, specific thank-you keeps volunteers going (Grant & Gino 2010). One tap-scale question beats long surveys (Galesic & Bosnjak 2009) and star ratings inflate until they carry no information (Zervas et al. 2021), which the owner already ruled out.

**Acceptance criteria**
- [x] Only people who checked in or attended can thank or answer; the host cannot thank themselves.
- [x] A reworded thank-you does not notify the host again.
- [x] Unknown answers are refused as invalid input.
- [x] "After the activity" is visible to the host only.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR108 — Welcome Newcomers
> **Added in Step 9 from the owner's research instruction (2026-09-15)** — roadmap item 7. Tested in TS200; built in IMP29.

**Traces from:** BR05, FR056 (attendee list), FR105
**Traced to:** IMP29; TS200
**Priority:** Must
**Status:** Implemented (Step 9)
**Confidence:** High

**Requirement (ISO 29148 form)**
When a member joins an activity and has never checked in to an earlier one, the system shall tell the host "{name} is going · first time" with a suggestion to say hello, mark them "First time" (and "On their own" when their plan says so) on the host's attendee list, and show the member a "Your first Milavn activity" card saying the host will look out for them and that coming alone is normal; the card is never shown to the host.

**Intent (why)**
Newcomers stay when someone welcomes them early (Choi et al. 2010; the Wikipedia Teahouse experiment, Morgan & Halfaker 2018), and adjustment depends on knowing what to expect and feeling accepted (Bauer et al. 2007).

**Acceptance criteria**
- [x] First-timer is computed from real check-ins before the activity's start, not from account age.
- [x] Host notification, attendee chips and the member card behave as stated; a returning member is not marked.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR109 — Share My Plan With Family
> **Added in Step 9 from the owner's research instruction (2026-09-15)** — roadmap item 8. Tested in TS201; built in IMP29.

**Traces from:** BR12 (safety), FR063, FR064, owner decision "locality only, never exact locations"
**Traced to:** IMP29; TS201
**Priority:** Should
**Status:** Implemented (Step 9)
**Confidence:** High

**Requirement (ISO 29148 form)**
When a member is going to an activity, the activity page shall offer "Share my plan with family", which opens WhatsApp with the activity title, date and time, locality, the host's first name, the activity link and "I'll message you when I'm back"; for activities starting between 6 pm and 6 am for members in Telangana, it shall add the Telangana Police T-Safe instruction (dial 100, option 8); it shall never share a live or exact location.

**Intent (why)**
Safety built into the format is what the best IRL products do (Timeleft, 222, Bumble "Share Date", Snap Map) and matters more in India, where women's evening mobility is constrained and phones are often shared (Time Use Survey 2019; Sambasivan et al. 2018). WhatsApp is how families already coordinate; T-Safe is a real, free state service.

**Acceptance criteria**
- [x] Opens a WhatsApp share with the stated content in the member's language; no location beyond the locality.
- [x] T-Safe line only for evening activities and members in Telangana cities.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR110 — Who It's For, and Food and Drink
> **Added in Step 9 from the owner's research instruction (2026-09-15)** — `RESEARCH-BEHAVIOUR-2026.md` roadmap item 9. Tested in TS202; built in IMP30.

**Traces from:** BR02 (discovery), FR005, FR009, FR010
**Traced to:** `09-implementation.md` IMP30; TS202
**Priority:** Must
**Status:** Implemented (Step 9); "women only" deferred (see Open items)
**Confidence:** High

**Requirement (ISO 29148 form)**
An organizer shall be able to mark who an activity is for (Family & kids, Elder-friendly, Beginners welcome) and, for food and celebration activities, what food and drink to expect (Veg, Jain options, Non-veg served, Alcohol-free), with vegetarian and alcohol-free pre-selected for Eat and Celebrate activities until the organizer changes them; vegetarian and non-vegetarian cannot both be claimed; members shall see these on the activity page and filter discovery by them and by "Free".

**Intent (why)**
Whether a member can come at all often depends on family, elders, first-timers and food: 81% of Indians limit meat and 39% are vegetarian (Pew 2021), and community events default to vegetarian and alcohol-free (India research track). The Discover "Free" chip was a disabled placeholder saying "everything is free"; with paid spots (FR102) it must be a real filter.

**Acceptance criteria**
- [x] Tags stored and returned on cards; unknown tags and veg + non-veg together refused.
- [x] Veg and alcohol-free pre-selected for Eat and Celebrate until the organizer touches the food row.
- [x] Discover filters: Free, Family & kids (main row); who it's for and food in More filters.
- [ ] "Women only" — **deferred:** enforcing it needs a gender attribute the platform identity does not hold (basic identity only); logged as an open item rather than shipped as an unenforceable label.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR111 — Honest Discovery: Returning Hosts, Fair Start, Variety and "Not Interested"
> **Added in Step 9 from the owner's research instruction (2026-09-15)** — roadmap item 10. Tested in TS203; built in IMP30.

**Traces from:** BR02, FR007 (ranking), FR008 (why this)
**Traced to:** IMP30; TS203
**Priority:** Must
**Status:** Implemented (Step 9)
**Confidence:** High

**Requirement (ISO 29148 form)**
Discovery ranking shall (a) raise activities by hosts at whose activities the member has checked in before and say so ("You've been to Priya's activities before"); (b) give a host who has never held an activity a small boost when the activity is nearby and, when that decides the reason, say "New host nearby, giving them a fair start"; (c) show no host more than twice in the first ten results; and (d) let a member mark an activity "Not interested" with a reason (not my thing, too far, bad time, not this host), removing it from their discovery and, for "not this host", that host's activities for 60 days — never removing an activity the member has already joined.

**Intent (why)**
For brand-new events the organizer is the strongest signal (Zhang & Wang 2015); simple, checkable explanations earn trust (Herlocker et al. 2000); recommenders starve new hosts unless they get a fair share (Abdollahpouri et al. 2019); variety keeps discovery useful (Kaminskas & Bridge 2016); user control with a reason raises satisfaction (Harper et al. 2015).

**Acceptance criteria**
- [x] Returning-host reason appears only from the member's own check-ins; the helper answers only for the member bound to the request.
- [x] Fair-start boost only when nearby and only for hosts with no held activity.
- [x] Per-host cap in the top ten; nothing is hidden by the cap.
- [x] "Not interested" reasons validated; joined activities stay visible.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR112 — Regulars: Keep My Spot Each Time, Own Attendance Count, Welcome Back
> **Added in Step 9 from the owner's research instruction (2026-09-15)** — `RESEARCH-BEHAVIOUR-2026.md` roadmap item 11. Tested in TS204; built in IMP31.

**Traces from:** BR03 (recurrence), BR04 (participation), BR12 (notifications), FR012 (series), FR103–FR104 (reminders)
**Traced to:** IMP31; TS204
**Priority:** Should
**Status:** Implemented (Step 9)
**Confidence:** High

**Requirement (ISO 29148 form)**
On a free activity in a series, a member who has checked in at least once in that series shall be able to tap "Keep a spot for me each time". The system shall then (a) give them a spot (or a waitlist place when full) on every upcoming date at once, (b) do the same whenever the host adds a new date and tell them "Your spot is kept… Can't make it? Free it in one tap", and (c) let them stop at any time. The series section shall show the member their own "You've been to X of the last Y" (last four held dates), never a streak, and never to anyone else. When a member's previous date in the series ended as no-show or cancelled, the three-day reminder shall begin "We missed you last time; glad you're coming." Paid series and the host are refused; a member blocked either way with the host is never added.

**Intent (why)**
Friendships come from repeated time together (Hall 2019), and habits form in a stable context (Wood & Neal 2007), so returning should cost nothing. A warm message after a miss was the most effective of 54 gym interventions (Milkman et al. 2021) while a broken streak makes people quit (Silverman & Barasch 2023) — so a count and a welcome, never a streak. Requiring one past check-in keeps newcomers from being crowded out by holds from strangers; paid spots are never taken on anyone's behalf.

**Acceptance criteria**
- [x] Opt-in only, one tap, reversible; upcoming dates kept at once; new dates kept automatically with a notification.
- [x] Refused for paid series, for the host, and for someone who has not come yet (409, localised).
- [x] "X of the last Y" is answered only for the member bound to the request.
- [x] Welcome-back wording only after a missed previous date; no streak language anywhere.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR113 — Photo Privacy: Ask Before Sharing, "Don't Include Me", Remove a Photo of Me
> **Added in Step 9 from the owner's research instruction (2026-09-15)** — roadmap item 12. Tested in TS205; built in IMP31.

**Traces from:** BR09 (privacy), BR14 (safety), FR092 (moments)
**Traced to:** IMP31; TS205
**Priority:** Must
**Status:** Implemented (Step 9)
**Confidence:** High

**Requirement (ISO 29148 form)**
A member shall be able to set "Photos of me: Please don't include me" in Profile settings. Before someone who was at an activity shares a photo from it, the system shall show the names (first name and last initial) of people who were there and asked not to be pictured, and require two confirmations — everyone clearly in the photo is fine with it being shared; no children in it, or their parents agreed — before the Share button works. Anyone who can see a photo and did not share it shall be able to tap "I'm in this photo · remove it"; the photo is hidden for everyone at once and the person who shared it is told it was taken down, without being told who asked. People who cannot see the thread cannot remove anything.

**Intent (why)**
An identifiable photo is personal data under India's DPDP Act and Rules 2025, and consent to take a photo is not consent to publish it. Online photo abuse is a documented harm for women in South Asia (Sambasivan et al. 2018/2019). Removal must be instant and blame-free so nobody has to argue to get a photo of themselves taken down.

**Acceptance criteria**
- [x] The opt-out list is shown only to people who were there, and only lists people who were there.
- [x] Share is disabled until both confirmations are ticked.
- [x] Removal is immediate, hides the photo for everyone, notifies the uploader without the requester's name.
- [x] A member who cannot view the thread gets 404.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR106 — Would Meet Again (Private, Mutual Only)
> **Added in Step 9 from the owner's research instruction (2026-09-15)** — `RESEARCH-BEHAVIOUR-2026.md` roadmap item 5. Tested in TS206; built in IMP32. (Numbered in roadmap order, written after FR113.)

**Traces from:** BR10 (people discovery, distinct from dating), BR15 (post-event signals), FR042–FR045
**Traced to:** IMP32; TS206
**Priority:** Should
**Status:** Implemented (Step 9)
**Confidence:** High

**Requirement (ISO 29148 form)**
Once an activity has started, a member who was there (checked in, or the host/co-host) shall see "Would you meet anyone again?" with the other people who were there, and may privately pick or un-pick any of them. A pick shall never be shown to the person picked, and there shall be no counts anywhere. When two people have picked each other, both shall be told once — "You and {name} would both meet again" — and each shall appear on the other's People page under "You'd both meet again". Un-picking removes the connection silently for both; picking again never re-notifies. People who were not there see no one and cannot pick; blocked pairs never appear.

**Intent (why)**
After a first conversation people underestimate how much the other person liked them (Boothby et al. 2018, "the liking gap"), so they rarely follow up and one-off meetings do not become friendships (Hall 2019). A mutual, private choice removes the risk of rejection; Meetup's Connections uses the same idea. Keeping it mutual only, count-free and activity-framed keeps Milavn distinct from dating (FR044–FR045).

**Acceptance criteria**
- [x] Candidates only for someone who was there, only after the start, never themselves or a blocked person.
- [x] One-sided picks invisible to the other person, never notified.
- [x] Mutual: both told exactly once; listed for both; un-pick removes it for both.
- [x] Someone who was not there gets 404 when picking.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR115 — Joining a Circle: A Question or Two, and the Organizer's Yes
> **Added in Step 9 from the owner's picks of the competitor research (2026-09-17)** — picks 2 and 3 (Meetup membership questions and approval; Luma, Geneva, Heylo).

**Traces from:** BR05 (circles), FR020–FR021 (join/leave), BR14 (safety)
**Traced to:** IMP35–IMP37; TS209–TS211
**Priority:** Must
**Status:** Implemented (Step 9)
**Confidence:** High

**Requirement (ISO 29148 form)**
A circle shall be either open (join at once, unchanged) or ask-first. An ask-first circle may carry up to three short questions; someone asking to join answers them and the request waits. An organizer or assistant shall see who is waiting and what they answered, and may let them in or not, once. The person asking shall see that they are waiting, and shall be told when they are let in; a decline shall never be announced to them. Someone outside the circle shall be able to read the questions without being able to read anything else about the circle.

**Intent (why)**
Every product that runs real communities screens the door: Meetup asks up to five questions and holds each request as pending, Luma has approval-required registration, and Heylo reports that admission friction is exactly what makes members trust a group. For a women-only walking circle or a neighbourhood group, "how do you know us?" is the difference between a community and a public square. The decline is deliberately silent: being turned down by name helps nobody, and the person can see the state themselves.

**Acceptance criteria**
- [x] Open circles behave exactly as before.
- [x] Questions are readable to a non-member (name, policy, questions only — migration 026).
- [x] One pending request per person; asking twice changes nothing.
- [x] Only an organizer or assistant sees the answers or decides; everyone else gets an empty list and a 403.
- [x] Being let in is notified; a decline is not.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR116 — Familiar Faces
> **Added in Step 9 from the owner's picks of the competitor research (2026-09-17)** — pick 27 (Meetup's Familiar Faces).

**Traces from:** BR10 (people discovery), FR042–FR045, BR09 (privacy)
**Traced to:** IMP35–IMP37; TS209–TS211
**Priority:** Should
**Status:** Implemented (Step 9)
**Confidence:** High

**Requirement (ISO 29148 form)**
A member's page for another member shall show how many past activities the two of them were both at, counted only from activities where both were checked in or attended, answered only for the member making the request, and never for a blocked pair.

**Intent (why)**
Friendship comes from repeated time together (Hall 2019; Reis et al. 2011) — the second and third meeting is where an acquaintance becomes a friend. Telling someone "you have both been to three of these" is worth more than any new-people suggestion, and it is a fact they already know from having been there.

**Acceptance criteria**
- [x] Counted from both people's own attendance only.
- [x] Answers only for the viewer bound to the request (definer, migration 027).
- [x] Zero for a stranger; never shown for a blocked pair.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR117 — The Host Who Keeps Showing Up
> **Added in Step 9 from the owner's picks of the competitor research (2026-09-17)** — pick 20 (Meetup's 2026 "Super Organizer" badge).

**Traces from:** BR08 (earned reputation), FR034–FR037
**Traced to:** IMP35–IMP37; TS209–TS211
**Priority:** Should
**Status:** Implemented (Step 9)
**Confidence:** High

**Requirement (ISO 29148 form)**
The reputation labels shall include "Hosts regularly, rarely cancels" for a member who has held five or more activities with at most one cancellation. It shall remain a qualitative label like every other, shall never be a score, rank or streak, and shall disappear again if the member starts cancelling.

**Intent (why)**
Meetup is adding a Super Organizer badge for hosts who run consistently good groups. Milavn already earns "appreciated host" from real thank-yous; this is the other half a community notices by itself — the person whose activity actually happens, month after month. Keeping it reversible is what stops it becoming a status symbol.

**Acceptance criteria**
- [x] Five held activities and at most one cancellation.
- [x] Replaces the weaker host labels rather than stacking with them.
- [x] No number is exposed anywhere.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR118 — Conversation Cards
> **Added in Step 9 from the owner's picks of the competitor research (2026-09-17)** — pick 9 (Timeleft's table cards; 222's written intro).

**Traces from:** BR15 (post-event and belonging), FR108 (welcoming newcomers)
**Traced to:** IMP35–IMP37; TS209–TS211
**Priority:** Should
**Status:** Implemented (Step 9)
**Confidence:** High

**Requirement (ISO 29148 form)**
From about an hour before an activity starts until it ends, a member who is going (or its host) shall be offered a few conversation prompts chosen by the activity's category, in a stable order for everyone at that activity, with one tap to see another. The prompts shall not be shown to anyone who is not going.

**Intent (why)**
Timeleft puts printed prompt cards on every table and 222 sends a written introduction before the event, both because the hardest part of meeting strangers is the first two minutes. The prompts are written for this community: answerable by an eighteen-year-old and by a grandmother, and never about money, marriage, caste or politics.

**Acceptance criteria**
- [x] Only for people who are going, only around the time it happens.
- [x] Same cards, same order, for everyone at that activity.
- [x] No storage, no moderation surface — they are content in the codebase.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR119 — Free Right Now
> **Added in Step 9 from the owner's picks of the competitor research (2026-09-17)** — pick 8 (Couchsurfing Hangouts).

**Traces from:** BR10 (people), BR09 (privacy), FR038/FR041 (locality only)
**Traced to:** IMP35–IMP37; TS209–TS211
**Priority:** Should
**Status:** Implemented (Step 9)
**Confidence:** High

**Requirement (ISO 29148 form)**
A member shall be able to say they are free for the next fifteen minutes to four hours, with a locality they type and a short note, and to take it back at any time. It shall be visible only to members who share a circle with them, never to a blocked member, and it shall expire by itself. No location shall ever be read from the device.

**Intent (why)**
Most meeting up is not planned a week ahead — someone is free this evening and would rather not spend it alone, which is the whole reason Couchsurfing's Hangouts exist. Restricting it to shared circles keeps it a message to people you already know, not a broadcast to strangers.

**Acceptance criteria**
- [x] Shared-circle only; blocked pairs never see each other.
- [x] Expires without anyone acting; the window is capped at four hours.
- [x] Locality is typed, never sensed.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR120 — Asking the Circle: Which Day, or Which One
> **Added in Step 9 from the owner's picks of the competitor research (2026-09-17)** — picks 6 and 7 (Partiful date polls; Dice Groups).

**Traces from:** BR05 (circles), BR03 (creation), FR024 (circle board)
**Traced to:** IMP35–IMP37; TS209–TS211
**Priority:** Must
**Status:** Implemented (Step 9)
**Confidence:** High

**Requirement (ISO 29148 form)**
A member of a circle shall be able to ask one question with two to six answers, either times ("which morning suits everyone?") or activities already posted ("which one shall we go to?"). Any member may pick several answers and change their mind until it is settled; who picked what shall be visible by name inside the circle. Only the person who asked may settle it, after which a date question offers to create the activity at the most-picked time.

**Intent (why)**
Partiful polls guests for a date before the event exists, which is how a family or a badminton group actually decides; Dice added Groups so friends can vote on which show to attend before anyone commits. Both are the same small primitive. Names are shown because inside a circle "Meera and Ravi can do Sunday" is the useful part — the same thing a WhatsApp poll shows.

**Acceptance criteria**
- [x] Two to six options; a question of up to 160 characters.
- [x] Several picks allowed; changeable until settled.
- [x] Voters visible by name to circle members only (RLS).
- [x] Only the asker settles it; settling offers the activity at the most-picked time.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR121 — Assistants: An Organizer Should Not Be Alone
> **Added in Step 9 from the owner's picks of the competitor research (2026-09-17)** — pick 17 (Meetup's leadership roles).

**Traces from:** BR05 (circles), BR13 (organizer tooling), FR059 (delegation)
**Traced to:** IMP35–IMP37; TS209–TS211
**Priority:** Must
**Status:** Implemented (Step 9)
**Confidence:** High

**Requirement (ISO 29148 form)**
A circle's organizer shall be able to ask any member to help run it, and to step them back down. An assistant shall see and decide join requests and be told when someone is waiting; an assistant shall not appoint other assistants, change the organizer, or delete the circle. Nobody shall be able to give themselves a role.

**Intent (why)**
Meetup gives a group co-organizers, assistant organizers and event organizers, and its own guidance — with the research this module already cites (Liu & Suel on thousands of Meetup groups) — says groups survive when the organizer is not carrying everything alone. Milavn circles had exactly two states: the person who created it, and everyone else.

**Acceptance criteria**
- [x] Only an organizer sets roles; self-service is refused.
- [x] The creator's own role cannot be edited.
- [x] An assistant can read and decide join requests, and is notified of them.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR122 — Follow a Calendar, Not Just an Activity
> **Added in Step 9 from the owner's picks of the competitor research (2026-09-17)** — pick 23 (Luma's subscribable Calendars).

**Traces from:** BR06 (calendar), BR11 (public pages), FR026–FR029
**Traced to:** IMP35–IMP37; TS209–TS211
**Priority:** Should
**Status:** Implemented (Step 9)
**Confidence:** High

**Requirement (ISO 29148 form)**
A member shall be able to follow a host, privately, so that host's public activities appear in their calendar; and a calendar feed (.ics) for that host shall be subscribable from any calendar app without signing in. The feed shall contain only public activities, and following shall never be disclosed to the host.

**Intent (why)**
Luma's strongest idea is that a calendar is a thing you follow, so every new date the host posts lands in your own calendar automatically — exactly what a weekly badminton or a monthly satsang needs. Milavn could export one activity at a time, so a regular host's community had to keep coming back to look. The feed is public-only by necessity: a subscription URL is unauthenticated by nature.

**Acceptance criteria**
- [x] Following is private to the follower.
- [x] The feed carries public activities only, from a month back.
- [x] It is a valid calendar file any app can subscribe to.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR123 — Chapters Under One Umbrella
> **Added in Step 9 from the owner's picks of the competitor research (2026-09-17)** — pick 18 (Meetup Pro Networks).

**Traces from:** BR05 (circles), BR02 (discovery)
**Traced to:** IMP35–IMP37; TS209–TS211
**Priority:** Should
**Status:** Implemented (Step 9)
**Confidence:** High

**Requirement (ISO 29148 form)**
A circle shall be able to sit under a named umbrella, set by its own organizer. Anyone signed in shall be able to see an umbrella's chapters — name, locality, how many members, and whether that chapter asks before letting people in — and belonging to one chapter shall grant no access to another: joining still goes through that chapter's own door.

**Intent (why)**
One community often runs in several cities, which is why Meetup Pro has networks. A samaj is exactly this shape: Hyderabad, Mumbai, Bengaluru, and an overseas chapter, one community. Making chapters findable is the point; making them shared would quietly undo each chapter's own privacy.

**Acceptance criteria**
- [x] Only a chapter's organizer attaches or detaches it.
- [x] The chapter list exposes name, place, size and door policy only.
- [x] No membership, post or activity crosses between chapters.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR124 — A Drive for Something the Community Needs
> **Added in Step 9 from the owner's picks of the competitor research (2026-09-17)** — pick 14 (Mera Samaj's fundraising; Heylo's dues).

**Traces from:** BR05 (circles), BR13 (organizer tooling), FR102 (paid spots and the payments port)
**Traced to:** IMP35–IMP37; TS209–TS211
**Priority:** Must
**Status:** Implemented (Step 9)
**Confidence:** High

**Requirement (ISO 29148 form)**
An organizer or assistant shall be able to open a drive inside a circle with a title, a purpose, an optional target and an optional closing date. A member shall be able to promise an amount with a short note, change it, or take it back. Every member shall see the totals — promised, how many people, and how much has actually arrived — and nobody but the organizers shall see who promised what. Money shall not move inside Milavn until Payment Services exists; until then an organizer marks by hand what has arrived.

**Intent (why)**
This is the one capability the Indian community products have that none of the Western ones do. Mera Samaj's own case study is an admin collecting in a few months what had taken twelve years by hand; Heylo builds recurring dues for clubs. A samaj collects constantly — for a hall, a scholarship, a family in trouble — and today that happens in a WhatsApp group with a screenshot of a UPI payment and a hand-kept list.

**Acceptance criteria**
- [x] Only an organizer or assistant opens or closes a drive.
- [x] Totals are visible to the circle; individual amounts only to organizers.
- [x] Promises are clearly labelled as promises while payments are off (blocker B1).
- [x] `paid_at`/`payment_reference` are where a real payment will attach, with nothing else to change.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

## FR114 — Bringing Someone With You
> **Added in Step 9 from the owner's pick of the competitor research (2026-09-17)** — item 1 of 14. Tested in TS208; built in IMP34.

**Traces from:** BR04 (participation lifecycle), BR03, FR015–FR016 (join/withdraw), FR058 (capacity and waitlist), FR105 (coming with)
**Traced to:** IMP34; TS208
**Priority:** Must
**Status:** Implemented (Step 9)
**Confidence:** High

**Requirement (ISO 29148 form)**
When creating a free activity the host shall choose how many extra people each person may bring (none, 1, 2 or 3; at most 4). A member who is Going shall then be able to say how many they are bringing, in one tap, without leaving the page. Every count the app shows shall include those guests: capacity, spots left, "full", and the total shown next to the going count. When a party does not fit, the whole party shall go on the waitlist together and shall be promoted only when there is room for all of them — never split, and never moved down the queue. A member already Going who raises their guest count beyond the room left shall be refused with a plain message, never silently waitlisted. Guests shall not be available on paid activities, where a spot is bought per person. The organizer's attendee list shall show who is bringing how many.

**Intent (why)**
In this community an activity is rarely attended alone — a spouse, a cousin, a child comes along. Every comparable product treats this as part of the RSVP: Meetup counts up to five guests per RSVP against capacity and holds a party on the waitlist until it fits, Partiful makes plus-ones a first-class object, and 222 offers a plus-one precisely so nobody has to arrive alone. Milavn could previously record only the sentiment ("coming with: family") in a plan note that no capacity arithmetic ever saw, so a host with twelve spots could have twenty people turn up.

**Acceptance criteria**
- [x] Host sets the allowance; it is refused on paid activities and above 4.
- [x] Guests count towards capacity, spots left and "full" everywhere, including cards and the public page.
- [x] A party that does not fit waits together and is promoted only when it fits; a smaller party behind it is taken first only when the bigger one cannot fit.
- [x] Raising guests beyond the room left is refused (409) and never demotes someone already going.
- [x] Withdrawing clears the guests; bringing fewer frees room and promotes whoever now fits.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

