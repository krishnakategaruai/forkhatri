---
step: 01-business-requirements
module: MOD02
status: Sealed
approver: Product Manager
updated: 2026-09-12
items: "18 | approved: 18 | blockers: 0"
---

# 01 — Business Requirements — MOD02 Milavn

## Revision history
| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-12 | Initial draft: 17 Business Requirements derived from `docs/PreStartResearch/milavn/Milavn — Complete Product Discovery, Strategy & Product Planning Thesis.md` (self-declared status: "Master Product Definition / Source of Truth"), cross-checked against `modules/modules.md`'s MOD02 scope line. Grounded with independently-verified current competitor research (Meetup's 2026 roadmap, Partiful's Explore/SEO documentation, WhatsApp's January 2026 group-events feature) rather than accepting the thesis's own competitor citations at face value, per this project's standing practice of verifying competitor-app claims directly. | First Step 1 run for MOD02. |
| 2026-09-12 | All 17 BRs reviewed against the nine-point quality gate, prioritized, and approved. File sealed. | Product Manager approval — krishna kategaru, 2026-09-12. |
| 2026-09-12 | Second pass: reviewed the sealed 17-BR file critically from the approver's own seat rather than re-confirming the first pass. Found and fixed two real gaps against `modules.md`'s already-approved MOD02 scope, which the source thesis itself under-emphasizes: (1) "organizer/event/**venue** verification" had no explicit tie-back — resolved by naming Venue's place in BR07's existing trust taxonomy rather than inventing a separate venue-specific model; (2) "post-event feedback and community-engagement signals" (with `EventFeedback` as named owned data) had no corresponding BR at all — the source thesis treats the equivalent idea (§65) only as a metrics-measurement technique, and that relative silence had let an already-approved capability fall through. Added new BR15 (Post-Event Feedback and Community-Engagement Signals, Must) and renumbered the three deferred/Could BRs from BR15–BR17 to BR16–BR18 accordingly. No other gap, hallucinated citation, or over-engineered BR was found on this pass; all `§`-references were re-checked against the source thesis directly. File re-approved as 18 BRs. | Second, critical approver-perspective review pass — krishna kategaru, 2026-09-12. |
| 2026-09-12 | Third pass, prompted by Step 2's own critical review of its FR decomposition: Step 2 found that this BR-level Must priority had been treated as automatically transitive to every FR beneath it, when three BRs (BR05, BR06, BR13) each bundle a genuinely-MVP capability (per the thesis's own explicit §58 list) together with a related but not-explicitly-MVP one from the same BR's Proposed Outcome. Added DEC-002 to each of BR05, BR06, and BR13 recording that the affected FRs (Community Memory under BR05; the standalone public-calendar view under BR06; capacity/waitlist management and co-organizer delegation under BR13) were refined to Should at Step 2, and annotated each BR's `Traced to:` field accordingly, so this BR file and `02-functional-requirements.md` stay consistent without either file silently diverging from the other. No BR's own Priority field changed — only the record of which of their FRs Step 2 legitimately refined downward. | Third pass, following Step 2's critical review — krishna kategaru, 2026-09-12. |
| 2026-09-13 | Fourth pass, prompted by a real gap Step 5 (Test Scenarios) surfaced: no moderator-facing screen existed anywhere in Steps 3/4 for BR14's own "basic report/review queue," even though FR065 explicitly requires one. Root-caused to BR14's own "Affected users and systems" line, which incorrectly stated admin/moderation was "out of scope" — an apparent copy-paste artifact from a different module's equivalent BR, directly contradicting this BR's own Proposed Outcome. Corrected the line and added DEC-002 recording the fix, since the wrong statement here — not any gap in Steps 3/4's own work — was the actual root cause of the missing screen. | Fourth pass, following a gap surfaced at Step 5 — krishna kategaru, 2026-09-13. |
| 2026-09-13 | Authentication ownership corrected: login/auth is owned solely by the parent ForKhatri platform (one source of truth); BR01's "login" wording is read as the platform's login, not a Milavn-built one; Milavn's BR01 scope is the minimal profile (locality, interests, language) captured after the platform has authenticated the person. Nothing was deleted — the original text stays for traceability. | User correction "User login, authentication will be done by one source of truth, the parent ForKhatri" — krishna kategaru. |

## Scope of this step

This file covers every Business Requirement needed to deliver MOD02 —
Milavn: a locality/interest/language-aware participant identity;
contextual local discovery across feed, calendar, map and search with
explainable (never opaque-score) ranking; effortless activity and event
creation distinguishing a recurring "Activity" from its individual
occurrences; the participation and attendance lifecycle; Circles as an
emergent, never-forced community primitive; a first-class calendar
spanning personal/circle/community/public scopes; a visible trust taxonomy
for activities, organizers and sources; earned (never purchased or
publicly rated) reputation; privacy-first location and personal-data
handling; contextual people discovery deliberately separated from dating;
public, no-login-required shareable pages; purposeful notifications;
progressive organizer tooling; and baseline reporting/blocking/safety for
real-world physical activities.

The authoritative source for every BR below is `docs/PreStartResearch/
milavn/Milavn — Complete Product Discovery, Strategy & Product Planning
Thesis.md`. That document declares its own status as "Master Product
Definition / Source of Truth" and its closing instruction (§109,
"Source-of-Truth Decision") directs exactly this: "The next agent must not
redefine the product. It should translate this product thesis into
requirements and identify genuine ambiguities/blockers." This is the same
relationship `modules.md`'s own MOD03 Mangaly entry already establishes
for its Master Requirements Input — a deep, module-specific product
definition that *deepens*, not contradicts, `modules.md`'s necessarily
brief one-paragraph MOD02 scope line ("Community meetups, professional
gatherings, workshops, and social/interest-based events; event creation
and organizer management; event discovery, registration and participation;
organizer/event/venue verification; post-event feedback and
community-engagement signals"). Every capability named above traces to
that line at the right level of abstraction — Circles, the
Activity/occurrence split, and contextual people discovery are
elaborations of "community meetups... social/interest-based events" and
"community-engagement signals," not a scope expansion beyond it.

`modules.md`'s MOD02 "Out of scope" line is respected without exception:
matrimonial/dating discovery (→ MOD03 Mangaly, independently reinforced by
the thesis's own explicit non-goal, §23 "No Dating Creep" and §79); paid
one-on-one professional advisory sessions (→ MOD04 Counsel);
business-to-business networking not tied to a specific event (→ MOD01
Vyapar); actual payment capture for paid/ticketed events (→ MOD06 Payment
Services, consistent with the thesis's own revenue thesis, §53–§56,
describing *that* paid capability may exist without specifying collection
mechanics — see BR18); and externally-sourced local announcements not
created by a Milavn organizer (→ MOD05 Dashboard's Local Information
Intelligence, matching the thesis's own Samachar/Milavn boundary, §77).

`modules.md` estimated 5 BRs for this module before this thesis existed;
this file needs more (17) for the same reason MOD03 Mangaly's own estimate
(the standard 5–8 guideline) was explicitly exceeded (10–15+) once its own
deep source document existed — see DEC-001 below for why the thesis's
specificity does not compress into 5 coarse units without losing real,
separately-verifiable business rules.

**Delivery form factor, corrected from the source thesis.** §41 of the
thesis frames Milavn as "mobile-first product + web companion" — two
separate delivery surfaces, a native mobile app as primary and a web
surface as secondary for organizers/SEO/public pages. That split does not
hold for this project: ForKhatri's architecture is already decided,
platform-wide, as a single mobile-first *responsive web app* (one
React/TypeScript SPA web client, `ARCHITECTURE.md` C4 container diagram;
Master PRD §34 "modern web experience" now, native apps deferred
platform-wide, not per-module) — the same architecture every other
ForKhatri module, including Mangaly, is built on. Every capability the
thesis assigns to "web" (public pages, organizer tools, calendars,
administration) and everything it assigns to "mobile" (discovery,
participation, notifications, location-aware use) is therefore delivered
through the *same* responsive web app, not two separate surfaces — this
corrects the thesis's own framing; it is not a new architecture decision
being made here.

**Multilingual support.** As corrected for Mangaly
(`modules/MOD03-mangaly/01-business-requirements.md`, 2026-09-10), the
platform's shared i18n library and translated-content data model are
Common Platform infrastructure (`modules.md` Shared Concerns;
`ARCHITECTURE.md` ADR-010, applied "across every container"), but Milavn
is not exempt from consuming it: a participant's language preference is
Milavn-owned profile data (captured directly in BR01 below, avoiding the
after-the-fact correction Mangaly's equivalent BR needed), and every
Milavn-authored surface (activity/event cards, circle pages, notifications)
renders through that shared model from V1.

**Explicitly out of this file's scope**, per `modules.md`'s Shared
Concerns and MOD02's own boundaries, and therefore not converted into a
Milavn BR even though the source thesis discusses them:
- Base identity/authentication and the platform-level trust/reputation
  *infrastructure* — Common Platform capability. Milavn's own BRs (BR07,
  BR08) cover only the Milavn-specific trust taxonomy and reputation
  signals layered on top of that platform identity.
- AI-assistant infrastructure, search infrastructure, and
  notification-delivery infrastructure — Common Platform capabilities;
  Milavn-specific behavioural constraints on them (e.g. thesis §33, "AI
  must not become a shortcut around permissions") are captured inside the
  relevant BR (BR13, BR17) rather than as a separate capability BR.
- Actual payment/ticketing capture, venue-booking commerce, and sponsorship
  transactions — MOD06 Payment Services (and MOD01 Vyapar for
  business/venue supply); Milavn BRs describe *that* a paid capability may
  exist only where the thesis commits to it (BR18), without specifying
  collection mechanics.
- External event ingestion from other platforms, deduplication, and
  cross-platform booking — explicitly a Phase 3/future capability per the
  thesis itself (§16–§17, §52, §60), recorded only as a low-priority,
  explicitly-deferred BR (BR16) for traceability, not built now.
- AI-native natural-language planning, an AI "organizer assistant," and
  voice interaction — explicitly a Phase 4/future capability per the
  thesis (§72–§75, §102–§103), recorded as a low-priority, explicitly
  deferred BR (BR17) for the same reason.
- Go-to-market, cold-start/seeding strategy, launch geography, and
  validation experiments (thesis §90–§98) — real and important, but a
  go-to-market/operations concern, not a business *requirement* on the
  product itself; not converted into a BR here.
- Dating/swipe mechanics, matrimonial discovery, or any romantic-matching
  framing — explicit, permanent MOD02 non-goal (thesis §23, §79;
  `modules.md`) — called out as a hard boundary within BR10 rather than
  restated globally.

## Set-level quality gate
| Check | Result |
|---|---|
| Comprehensive — covers full module scope | Pass — every MVP area named in the thesis's own §58 ("Identity," "Discovery," "Circles," "Activities," "Events," "Calendar," "Organizer," "Trust," "Notifications") maps to at least one BR below, plus the cross-cutting necessities the thesis treats as non-negotiable even at MVP (Privacy §21, Safety §82–§83, the dating/matching boundary §23), `modules.md`'s own two explicit MOD02 commitments the source thesis itself under-emphasizes (organizer/**venue** verification, folded into BR07; post-event feedback/community-engagement signals, BR15 — see the second review pass in Revision history), and three explicitly-deferred future-scope BRs (BR16–BR18) recorded for traceability to `modules.md`'s approved long-term direction. |
| Consistent — no contradicting BRs | Pass — all 18 BRs share the same product invariants (rules-based MVP ranking over ML, §48–§49; evidence/earned signals over scores, §18/§20; progressive complexity, §70) and the same actor vocabulary (Participant, Circle Member, Activity Creator, Circle/Event Organizer, Organization, Venue, §8). |
| Prioritized — every BR ranked | Pass — 15 Must (BR01–BR15, matching the thesis's own MVP definition, §58, plus `modules.md`'s explicit feedback commitment), 3 Could (BR16–BR18, matching the thesis's own explicitly-deferred Phase 3/4 and commerce scope, §59–§60). |
| No duplicates/overlaps | Pass — Trust (BR07, pre-existing verification status of an activity/organizer/source) is kept distinct from Reputation (BR08, behaviour earned over time) and from Feedback (BR15, a subjective satisfaction signal that *feeds* Reputation rather than duplicating it), per the thesis's own separate treatment (§18 vs. §20 vs. §65); Circles (BR05) absorbs Community Memory (§35) as one of its own properties rather than spinning it into a duplicate BR. |

## Open blockers
| ID | Item | What's needed | From |
|---|---|---|---|
| (none) | — | — | — |

No open blockers. Every genuine ambiguity the thesis itself flags (exact
ranking weights, exact moderation thresholds, exact circle-suggestion
trigger conditions, pricing/commission structure) is an implementation-
stage or Phase-3/4 design question the thesis itself defers, not a
business-requirements-level gap.

---

## BR01 — Minimal Identity, Locality, Interest and Language Profile
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
A participant wants to discover local activities, but today there is no
lightweight way to establish who they roughly are, where they roughly are,
and what they care about — without forcing them through a heavyweight
signup that the source thesis explicitly warns kills adoption for younger
users (§40: avoid "long registration forms," "mandatory profile
completion," "unnecessary fields").

**Proposed outcome**
Onboarding captures only what Discovery genuinely needs to function:
approximate locality (per BR09's privacy hierarchy), a set of interests
drawn from defined categories, and a language preference — matching the
thesis's own MVP identity scope exactly ("login, profile, locality,
interests, privacy," §58). Everything else (photo, bio, extended profile
detail) is optional enrichment, never required to reach a usable state.

**Affected users and systems**
Participant (owns/edits); Discovery (BR02) reads locality/interests as
ranking input; every rendering surface (Discovery cards, circle pages,
notifications) reads the language preference.

**Constraints**
- Must not require more than locality + interests to reach a usable,
  Discovery-eligible state (§40).
- Locality must follow BR09's approximate hierarchy (City → Zone →
  Locality) — never an exact home address at this stage.
- Language preference (English, Hindi, or Telugu at V1, per
  `ARCHITECTURE.md` ADR-010's day-one language set) is attached to the
  person's own record, not the app session, and is Milavn-owned profile
  data — the underlying rendering/translation mechanism stays Common
  Platform infrastructure (see "Multilingual support" above).

**Out of scope (for this BR specifically)**
Full social-profile/bio building (optional enrichment, not required);
organizer-specific identity attributes (BR13); professional identity
fields belonging to Vyapar/Counsel, not duplicated here.

**Worth check**
Without this, Discovery (BR02) has no locality or interest signal to rank
against — the entire product flywheel (Discover → Participate → Connect →
Contribute) starts here; removing it removes the product's entry point.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of choosing between a rich profile-completion
  model (as Mangaly's BR01 uses, with a three-tier completeness gate) and
  a simpler model for Milavn, facing the fact that Milavn participation is
  materially lower-stakes than a matrimonial profile and the thesis never
  calls for excluding sparse profiles from Discovery, we chose a simple
  two-state model (minimum-to-use vs. optional-enrichment) over Mangaly's
  three-tier gate, to avoid importing complexity this module's own source
  document never asks for, accepting that this deliberately does not reuse
  a pattern from elsewhere in the pipeline where the underlying need
  differs.

**Assumptions**
- Interest categories themselves (sports, professional, cultural, etc.)
  are implementation-stage taxonomy work, not frozen here.

**Traced to:** FR001–FR003 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-12

---

## BR02 — Contextual Local Discovery Across Feed, Calendar, Map and Search, With Explainable Ranking
**Priority:** Must
**Status:** Ready for Review
**Confidence:** Medium — the underlying ranking algorithm is intentionally
a "thin," deterministic V1 mechanism (thesis §48–§49); the business need
for relevance-based, explainable discovery is firmly established, but the
eventual ranking weights are genuinely unresolved at this stage.

**Problem**
People are surrounded by fragmented signals about local activities —
WhatsApp groups, Instagram, flyers, word of mouth — with no single trusted
layer connecting them (thesis §1). A naive discovery design (pure
chronological or attendee-count/popularity ranking) would reproduce the
same popularity-contest dynamic this project has already rejected
elsewhere, and would fail the thesis's own explicit "Why This?" standard
for recommendation trust (§28).

**Proposed outcome**
An "Around You" home experience groups activities into Today/Tomorrow/This
Weekend (§24); four complementary discovery modes — Feed, Calendar, Map,
Search (§25) — let the user switch between browsing styles; every card
answers What/When/Where/Who/Who's-going/Why in one glance (§27); ranking
weighs locality/distance, time fit, interest match, circle relevance,
social relevance, trust (BR07), availability, and freshness (§49), never
popularity as the primary factor; every surfaced item carries a concrete,
one-line reason ("Because you follow badminton," "3 people from your
circles are going," §28).

**Affected users and systems**
Participant, Circle Member; reads Identity (BR01), Trust (BR07); feeds
Participation (BR04).

**Constraints**
- Ranking must not use attendee-count/popularity as its primary driver.
- Every ranked item must carry a stated reason; an unexplained ranking is
  a defect (§28).
- V1 ranking is a deterministic, rules-based formula, not machine learning
  — the thesis is explicit: "Rules > Machine Learning," and "Do not
  over-engineer this initially. A deterministic ranking system is
  sufficient for MVP" (§48–§49).
- Filters must avoid overload; progressive disclosure is preferred over
  exposing every possible filter at once (§26).

**Out of scope (for this BR specifically)**
A machine-learning recommendation engine (explicit non-MVP, §59);
natural-language/voice discovery (Phase 4, folded into BR17); complex
geographic/map intelligence beyond basic distance display (explicit
non-MVP, §59).

**Worth check**
This is the entry point to the thesis's own central product loop, Discover
→ Participate → Connect → Contribute (§67) — without genuinely relevant,
explainable discovery, no other capability in this module has anything to
operate on.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ~ (four discovery modes
described together as one coherent capability, a deliberate structural
choice since they share one ranking/explanation model) · Feasible ✓ ·
Verifiable ~ (exact ranking weights are FR/implementation-stage work) ·
Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of the thesis's own longer-term ambition for
  machine-learning-driven recommendations (§48, "Later introduce ML"), we
  chose a deterministic, rules-based V1 formula over any ML component, to
  follow the thesis's own explicit instruction not to over-engineer the
  first version, accepting that ranking quality will be cruder at launch
  than an eventual learned model, consistent with the identical call this
  project already made for Mangaly's Compatibility ranking (BR06/BR07)
  under the same reasoning.
- DEC-002 · In the context of needing to verify the thesis's own
  competitor-precedent claims rather than restate them uncritically, we
  independently confirmed that Meetup's published 2026 roadmap corroborates
  the thesis's "unified member/organizer experience" framing
  ([Meetup Blog, 2026 roadmap](https://www.meetup.com/blog/2026-meetup-roadmap/)),
  which supports (without itself dictating) this BR's emphasis on
  relevance/continuity over raw popularity.

**Assumptions**
- None beyond the Constraints above.

**Traced to:** FR004–FR009 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-12

---

## BR03 — Effortless Activity and Event Creation, With Recurrence
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
Today, organizing something ("Badminton this Saturday, need 4 people")
means falling back to informal WhatsApp coordination, because any
structured alternative implies a form-heavy "event creation" workflow the
thesis explicitly rejects as too heavy for an ordinary participant (§8.3:
"They should not have to become a sophisticated event organizer"; §30).

**Proposed outcome**
Creation asks only What (a small set of intent categories — Play, Meet,
Eat, Learn, Work, Explore, Celebrate, Help), When, Where, and How-many
(§30, §71 "Make Something Happen"); advanced configuration (capacity
tiers, co-hosts, waitlists) appears only when the creator actually needs
it (§70, progressive complexity). The system distinguishes a recurring
**Activity** concept ("Sunday Badminton") from its individual
**occurrences** (specific dated instances), so history, attendance, and
recommendations aggregate correctly at the Activity level without
duplicating the underlying concept (§15). A creator can edit, cancel, and
immediately get a shareable link (BR11).

**Affected users and systems**
Activity Creator, Circle/Event Organizer; feeds Participation (BR04),
Calendar (BR06), Discovery (BR02).

**Constraints**
- Creation must be completable through the minimal What/When/Where/
  How-many form without being routed through advanced fields first (§30,
  §40).
- Activity and its occurrences must be modelled so history/attendance
  aggregate at the Activity level, not fragment per-occurrence (§15) —
  the thesis calls this distinction "essential."
- Every created item must produce a shareable link/page per BR11.

**Out of scope (for this BR specifically)**
Complex ticketing or paid-capacity management (explicit non-MVP, §59);
AI-assisted natural-language creation (§31, Phase 4, folded into BR17);
external-source event ingestion (BR16).

**Worth check**
Without a near-zero-friction creation path, the thesis's own "Activity
Creator" persona cannot exist at all (§8.3), and the supply side of the
entire discovery flywheel has nothing to feed on.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of the thesis calling the Activity/occurrence
  distinction "essential" (§15) but not specifying its exact data shape,
  we chose to fix this distinction at the business-requirements level now
  rather than leaving it entirely to FR/architecture, to avoid a costly
  downstream remodel if the base concept were gotten wrong, over deferring
  it, accepting that the exact schema (which fields live on the Activity
  vs. the occurrence) remains implementation-stage work.

**Assumptions**
- None beyond the Constraints above.

**Traced to:** FR010–FR014 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-12

---

## BR04 — Participation and Attendance Lifecycle
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
Without a structured way to express and track intent to attend, an
organizer cannot gauge real turnout, and none of the signals the rest of
this module depends on — reputation (BR08), community memory (BR05),
recommendations (BR02) — have anything real to read from.

**Proposed outcome**
A participant expresses Interested or Going with one tap — "no
complicated registration" (§30). Status progresses through Interested,
Going, Cancelled, Checked-In, Attended, or No-show (§37). Organizers
receive updates and can communicate cancellations. QR check-in is
available for larger events but is explicitly unnecessary and not
required for small casual sessions (§37) — a call independently
corroborated by current industry direction: Meetup's own 2026 roadmap
commits to "simplified attendance tracking with QR-code check-ins" as a
real, current feature direction, and Partiful already ships QR check-in
for its ticketed events ([Meetup Blog, 2026 roadmap](https://www.meetup.com/blog/2026-meetup-roadmap/)).
No-show handling favours reminders and waitlists over punitive gamification
(§38).

**Affected users and systems**
Participant, Activity Creator, Circle/Event Organizer; feeds Reputation
(BR08), Community Memory (BR05), Calendar (BR06).

**Constraints**
- The default participation action is one tap; QR check-in is an opt-in
  scaling mechanism for larger events only, never a requirement for small
  sessions (§37).
- No-show handling must not aggressively penalize users — it produces
  reliability signals (BR08), not punishment (§38).

**Out of scope (for this BR specifically)**
Deposit/paid-commitment mechanics for high-demand events (a named future
idea, §38, not MVP); complex automated waitlist logic beyond a basic queue.

**Worth check**
This is the record of the thing the whole product exists to cause —
real-world participation — and every downstream signal in this module
depends on it existing accurately; without it, the north-star metric the
thesis itself names, "Meaningful Participations per Active Member" (§62),
cannot even be measured.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of QR check-in being a real, current feature
  direction at comparable products, we kept it explicitly optional and
  scale-gated rather than a blanket requirement, per the thesis's own
  direct instruction ("For small cricket/badminton sessions: QR check-in
  is unnecessary. Keep it simple," §37), over building it as a universal
  requirement, to avoid forcing infrastructure-heavy check-in onto every
  casual activity.

**Assumptions**
- None beyond the Constraints above.

**Traced to:** FR015–FR019 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-12

---

## BR05 — Circles as an Emergent Community Primitive
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
Forcing a user to create or join a formal "group" before they have a
reason to produces exactly the friction the thesis explicitly rejects
(§13: "Do not force users to create communities before they have a
reason"). Yet participants who keep showing up to the same activity
clearly want continuity — the thesis's own "Circle Member" persona (§8.2).

**Proposed outcome**
A Circle is a persistent group tied to a shared activity, interest,
locality, or purpose (§12). Circles form organically: the system
recognizes repeated co-participation and *suggests* circle formation
("You seem to regularly play together. Create a Badminton Circle?," §13)
— it never forces the conversion. Circle types include Public, Community,
Private, Organization, Interest, Local, and Recurring-Activity (§14). Each
circle retains its own community memory — member count, activity count,
participation count, active-member count, milestones (§35) — visible to
its own members, turning Milavn into persistent community infrastructure
rather than a bare listing tool.

**Affected users and systems**
Participant, Circle Member, Circle Organizer, Organization.

**Constraints**
- Circle creation/membership must never be a mandatory precondition for
  using Discovery, Activities, or Events (§13).
- Circle-formation suggestions are a system prompt the user can accept or
  decline — never an automatic, forced conversion.
- Community-memory statistics are visible to circle members; visibility
  beyond that follows the circle's own type (Public vs. Private/Community).

**Out of scope (for this BR specifically)**
Circle-internal chat/messaging beyond structured participation
coordination (BR12's territory; the thesis is explicit that Milavn should
not "build another WhatsApp," §36); AI-driven circle-health insight
narratives (a named future idea, §75, Phase-4-adjacent, folded into BR17).

**Worth check**
Circles are the mechanism that converts one-off participation into
"community becomes more active" — the closing loop of the thesis's own
flywheel (§11). Without them, Milavn is a one-shot event board with no
retention structure, and the thesis's stated ambition to be "community
infrastructure," not an event-listing app (§86), has no vehicle.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ~ (Community Memory
folded in as a property of a circle rather than split into its own BR —
see DEC-001) · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of the thesis describing Community Memory (§35)
  as "a powerful long-term feature" of a circle rather than a standalone
  capability, we folded it into this BR rather than giving it its own BR,
  over treating it separately, because it is a property/view of a
  Circle's own participation data, not an independently justifiable
  business capability — keeping the BR set from fragmenting an emergent
  detail into its own unit.
- DEC-002 · In the context of Step 2's own critical review pass checking
  every inherited-Must FR against the thesis's explicit §58 MVP list, and
  finding that Community Memory's own source citation here (§35, "a
  powerful **long-term** feature") already signals it is not core-MVP even
  though this BR overall is Must, we let Step 2 refine the Community
  Memory FR specifically to Should rather than treating this BR's own Must
  priority as automatically transitive to every FR beneath it — this BR's
  core membership mechanics (join/leave/type/never-a-precondition) remain
  Must and are fully functional without Community Memory.

**Assumptions**
- Exact circle-suggestion trigger thresholds (how many repeated
  co-participations before a suggestion fires) are implementation-stage
  tuning, not fixed here.

**Traced to:** FR020–FR025 (Step 2 Functional Requirements) — Must except
FR024 (Community Memory), refined to Should per DEC-002.

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-12

---

## BR06 — First-Class Calendar Across Personal, Circle, Community and Public Scopes
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
Without a persistent calendar object, Milavn is only a momentary discovery
feed — a user has no way to see their own committed schedule between
sessions, and a circle/organization has no way to represent its own
recurring cadence at all (§34).

**Proposed outcome**
Calendar is a first-class product object, not a view computed on the fly:
Personal (my activities), Circle (a circle's activities), Organization,
Community, and Public (discoverable) calendars each exist (§34), giving
Milavn persistent utility beyond a single discovery session.

**Affected users and systems**
Participant, Circle Member, Circle/Event Organizer, Organization; reads
Participation (BR04); interacts with public visibility rules from BR11.

**Constraints**
- Personal calendar reflects only what that person is Interested/Going in,
  respecting the same visibility rules as BR04/BR09.
- Public calendar entries include only activities/events explicitly marked
  Public (BR11).

**Out of scope (for this BR specifically)**
External calendar sync/export (Google/Apple Calendar) — a real, useful
integration, but not named by the thesis as part of its MVP scope;
deferred as a future enhancement.

**Worth check**
The thesis names this explicitly as giving "Milavn a persistent utility
beyond discovery" (§34) — without it, the product gives a user no reason
to return between discovery sessions, undermining the "Return" stage of
its own flywheel (§11).

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of Calendar appearing throughout the thesis as
  an input/output of several other capabilities (Discovery, Circles,
  Activities), we gave it its own BR rather than treating it as a feature
  of any one of them, over folding it into Discovery or Circles, because
  the thesis explicitly elevates it to first-class-object status (§34)
  with its own distinct scopes that recur across the rest of this module —
  the same role Accountability (BR15) plays across Mangaly's BR set.
- DEC-002 · In the context of Step 2's own critical review pass checking
  every inherited-Must FR against the thesis's explicit §58 MVP list
  ("Calendar: personal, circle, community" — no "public" scope named),
  we let Step 2 refine the standalone public-calendar-view FR to Should
  rather than treating this BR's own Must priority as automatically
  transitive to every scope it lists — personal, circle, and community
  calendars remain Must and are fully functional without a separate public
  calendar aggregation view (which is distinct from BR11's own Must-level
  per-item public pages).

**Assumptions**
- None beyond the Constraints above.

**Traced to:** FR026–FR029 (Step 2 Functional Requirements) — Must except
FR029 (public calendar view), refined to Should per DEC-002.

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-12

---

## BR07 — Visible Trust Taxonomy for Activities, Organizers and Sources
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
A user cannot tell whether "Badminton Saturday" is an officially-run,
community-verified, or an entirely unverified submission — and hiding that
distinction inside a backend system produces exactly the uncertainty the
thesis wants trust to remove (§18–§19).

**Proposed outcome**
Every activity/event carries a visible trust status drawn from a defined
taxonomy — ForKhatri Verified, Community Verified, Partner Verified,
External — Trusted Source, Community Submitted (§18) — communicated
simply and visibly on the surface itself (e.g. "✓ ForKhatri Verified,"
"Source: Hyderabad District Government," §19), never buried in a settings
screen the user has to seek out. This BR is also where `modules.md`'s
explicit "organizer/event/**venue** verification" commitment is satisfied:
a Venue (thesis §8.7, "eventually venues become participants in the
ecosystem") resolves to the same taxonomy as any other actor — typically
Partner Verified ("Trusted organization/business," §18) — rather than
needing a separate venue-specific trust model.

**Affected users and systems**
Participant, Circle/Event Organizer, Organization, Venue; consumed by
Discovery (BR02) as a ranking input.

**Constraints**
- Every activity/event must resolve to exactly one of the named trust
  levels; none may be left ambiguous.
- Trust status must be visible on the card/page itself, not only on
  request (§19).

**Out of scope (for this BR specifically)**
The actual verification workflow/vendor selection mechanics for achieving
Partner or Community verification (implementation-stage, analogous to
Mangaly BR08's deferred verifier-eligibility mechanics); trust attribution
for externally-ingested events (BR16, deferred).

**Worth check**
The thesis names trust as "one of Milavn's strongest opportunities"
specifically because it "inherits ForKhatri's broader trust philosophy"
(§18) — without a visible taxonomy, every other capability (Discovery,
Circles, Participation) operates on unverifiable claims.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of choosing between a visible labeling model
  and a "trust score," we chose visible labeling exactly as the thesis
  specifies (§19), over any scored/aggregated alternative, consistent
  with this project's now-established anti-opaque-score pattern (Mangaly
  BR08's identical "evidence, not score" principle) — both derive
  independently from the same ForKhatri trust philosophy this thesis names
  explicitly (§18), so the consistency is not coincidental.

**Assumptions**
- None beyond the Constraints above.

**Traced to:** FR030–FR033 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-12

---

## BR08 — Earned Reputation Signals, Never Purchased or Publicly Rated
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
A crude public star-rating system — which the thesis explicitly rejects
(§20) — would recreate the same popularity-contest/gaming dynamic this
project has already rejected for Mangaly's trust model. But having no
reputation signal at all leaves a repeat organizer's real reliability
invisible to a new participant deciding whether to show up.

**Proposed outcome**
Internal, earned signals — identity verification, organizer history,
attendance reliability, cancellation behaviour, event completion,
participant reports, community contributions, organizer consistency (§20)
— inform how an organizer or participant is perceived, without ever
becoming a purchasable or publicly star-rated score.

**Affected users and systems**
Circle/Event Organizer, Participant (as reputation subject and as
consumer of another's signals).

**Constraints**
- No public star rating or numeric reputation score may be displayed to
  ordinary users (§20, explicit).
- Reputation signals must be earned through actual platform behaviour,
  never purchasable via any paid tier (§20; §55 names "make trust
  purchasable" as something Milavn must never monetize).

**Out of scope (for this BR specifically)**
Any user-facing leaderboard or ranking of organizers by reputation (would
reintroduce a popularity contest); public review/comment systems on
organizers (not named by the thesis, and inconsistent with its own
reputation philosophy).

**Worth check**
The thesis explicitly separates this from Trust (BR07) as its own model
(§20) and names the underlying principle — "reputation should be earned,
not bought" — as aligned with the wider ForKhatri principle. Removing it
leaves no way to distinguish a reliable long-standing organizer from a
first-time one, undermining the organizer trust the whole product depends
on.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of Trust (BR07) and Reputation both concerning
  "can I believe this," we kept them as two separate BRs, over merging
  them, mirroring Mangaly's own BR07/BR08 split, because the thesis itself
  names them as separate sections with separate rules (§18 vs. §20) rather
  than one blended concept — pre-existing verification status versus
  behaviour earned over time are genuinely different things.

**Assumptions**
- None beyond the Constraints above.

**Traced to:** FR034–FR037 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-12

---

## BR09 — Privacy-First Location and Personal Information Handling
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
Without an explicit location-privacy model, the product defaults to either
useless discovery (no location signal at all) or a real safety/privacy
risk — exposing a participant's exact home location or private attendance
— which the thesis explicitly names as unacceptable (§21).

**Proposed outcome**
Location is represented and shown as an approximate hierarchy — City →
Zone → Locality → approximate distance (§21, §50) — never a participant's
exact home address. Private attendance, private circle membership, and
other sensitive personal information are never exposed without explicit
permission (§21). Location sharing is selected, approximate, optional, and
privacy-controlled by the user at all times (§50).

**Affected users and systems**
Participant; consumed by Discovery (BR02), Circles (BR05, for
locality-based circles), People Discovery (BR10).

**Constraints**
- No feature may display another user's exact home address or precise
  live location without their explicit, specific consent for that purpose.
- Private circle membership and private attendance default to hidden from
  non-members/non-attendees (§21).

**Out of scope (for this BR specifically)**
Live/real-time location sharing between users (not named by the thesis as
an MVP or clearly-scoped future feature); precise geofencing/proximity
alerts.

**Worth check**
This is a foundational safety and trust precondition for every other
capability that uses location — the thesis names it as a "must" boundary
(§21), not an optional refinement, and getting it wrong would be a
genuine, not cosmetic, safety failure.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of the thesis specifying an exact location
  granularity model (City → Zone → Locality → approximate distance, §21,
  §50), we adopted it as written rather than inventing an alternative
  scheme, over any other granularity model, because the thesis is explicit
  and unambiguous on this point and there is no product reason to deviate.

**Assumptions**
- None beyond the Constraints above.

**Traced to:** FR038–FR041 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-12

---

## BR10 — Contextual People Discovery, Deliberately Distinct From Dating
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
A generic "500 people near you" directory both fails to be useful — the
thesis explicitly labels this pattern "Bad" (§22) — and risks Milavn
drifting into exactly the profile → swipe → match pattern this project has
already built a dedicated module (Mangaly) to own deliberately and
separately (§23, §79).

**Proposed outcome**
People discovery surfaces a reason-based connection ("You both regularly
play badminton in Jubilee Hills," §22) derived from shared activities,
interests, circles, participation, locality, or mutual connections — never
a bare nearby-people list. The relationship model is strictly Activity →
Context → Participation → Natural connection, never Profile → Swipe →
Match (§23).

**Affected users and systems**
Participant, Circle Member; reads Participation (BR04), Circles (BR05),
Location (BR09).

**Constraints**
- Every surfaced person-to-person suggestion must carry a stated
  shared-context reason; a reason-less "nearby people" list must never
  exist (§22).
- No swipe, like/pass, or match mechanic of any kind may be implemented in
  Milavn — that model belongs exclusively to Mangaly (§23, §79; explicit
  `modules.md` MOD02/MOD03 boundary).

**Out of scope (for this BR specifically)**
Any romantic or matrimonial framing, however lightweight — a permanent
non-goal, not merely deferred; direct messaging between people who have
not shared a context (interacts with BR12's structured-communication
boundary).

**Worth check**
The thesis calls this separation "strategically important" (§23) —
getting it wrong would duplicate Mangaly's purpose inside a different
module and blur `modules.md`'s own explicit MOD02/MOD03 boundary.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of the thesis dedicating a whole section to
  "No Dating Creep" (§23), we treated this as a hard Constraint on this
  BR rather than a separate non-goal BR, over giving it its own BR,
  consistent with how every other module in this pipeline (see Mangaly
  BR09/BR14) expresses non-goals inside the relevant capability's own
  Out-of-scope section rather than as standalone BRs.

**Assumptions**
- None beyond the Constraints above.

**Traced to:** FR042–FR045 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-12

---

## BR11 — Public, No-Login-Required Shareable Pages for Events and Circles
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
Requiring login before anyone can even see what an event is creates
exactly the friction that kills the viral, share-driven discovery loop the
thesis depends on (§42–§43); this is also the mechanism by which Milavn
benefits from networks it doesn't own (WhatsApp, Instagram) instead of
competing with them (§43).

**Proposed outcome**
Every event, circle, organization, and activity marked Public has a clean,
shareable page viewable without login — showing title, image, date, time,
location, host, trust status (BR07), capacity, and an RSVP entry point
(§42). Pages are crawlable/indexable for organic search discovery,
consistent with how a comparable current product already operates this
exact pattern: Partiful's own help documentation confirms its public event
pages are SEO-optimized, and that public events are additionally surfaced
through a dedicated "Explore" discovery feed
([Partiful Help Center](https://help.partiful.com/hc/en-us/articles/50122568026651-How-can-I-make-my-events-discoverable);
[Partiful Blog, 2026](https://partiful.com/blog/post/the-best-way-to-get-your-event-discovered-in-2026)).
Sharing works through WhatsApp, Instagram, SMS, email, QR, and copy-link
(§43).

**Affected users and systems**
Any visitor (unauthenticated); Circle/Event Organizer (as the page's
subject); interacts with BR06's public calendar.

**Constraints**
- A public page must never expose information a private/non-public
  event or circle would otherwise protect (BR09) — "public" applies only
  to items the creator explicitly marked Public.
- Since this platform ships as a single mobile-first responsive web app
  (not a native app requiring install), this capability is close to free
  architecturally — the actual requirement is deliberate
  visibility/authentication design, not new infrastructure.

**Out of scope (for this BR specifically)**
Paid/ticketed checkout on the public page itself (→ MOD06 Payment
Services); analytics/attribution tracking on shared links
(implementation-stage enhancement, not a business requirement).

**Worth check**
This is the mechanism the "Discover" stage of the thesis's own flywheel
(§11) relies on beyond Milavn's own installed base — without it, growth is
capped at whoever already opened the app, undermining the thesis's own
"own the real-world participation layer" ambition (§85–§86).

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of the thesis citing Partiful's public-page
  discoverability as precedent, we independently verified this claim
  against Partiful's own current help documentation (2026) rather than
  restating the thesis's citation uncritically, per this project's
  standing practice of not asserting a competitor's behaviour without
  checking it directly — the claim held up and is cited above with its
  actual source.

**Assumptions**
- None beyond the Constraints above.

**Traced to:** FR046–FR050 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-12

---

## BR12 — Purposeful, Non-Spam Notifications
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
A community/events product that notifies indiscriminately trains users to
ignore or mute it, defeating its own purpose (§39). But withholding a
genuinely important notification — a cancellation, a location change — is
a real harm to someone about to travel to a now-cancelled activity.

**Proposed outcome**
Four notification classes each carry their own urgency/frequency rules:
Important (cancellation, location change, organizer update), Useful
(upcoming reminders), Social (a relevant person joined an activity), and
Opportunity (a new activity matching interests) (§39). This mirrors how a
comparable current product already scopes its own event notifications
narrowly rather than broadcasting generally: WhatsApp's January 2026
group-events feature ships custom early reminders and RSVP tracking as
distinct, purposeful notification types, not a blanket alert stream
([Thurrott, Jan 2026](https://www.thurrott.com/cloud/331453/whatsapp-improves-its-groups-feature-with-member-tags-and-event-reminders);
[MacRumors, Jan 2026](https://www.macrumors.com/2026/01/07/whatsapp-group-chats-three-new-features/)).

**Affected users and systems**
Participant, Circle/Event Organizer; consumes the platform's shared
notification-delivery infrastructure (Common Platform concern).

**Constraints**
- Important-class notifications (cancellation, location/time change) are
  always delivered; they are never suppressed by a user's general
  notification-frequency preference.
- Opportunity-class notifications must respect an explicit
  frequency/mute control — the class most likely to become spam if
  uncontrolled.

**Out of scope (for this BR specifically)**
The underlying notification-delivery infrastructure itself
(push/SMS/email pipeline) — Common Platform capability (`modules.md`
Shared Concerns); this BR governs only what Milavn decides to notify about
and how urgently, not how the message is technically delivered.

**Worth check**
Notifications are the mechanism that brings a participant back for the
"Return" stage of the flywheel (§11) between discovery sessions — without
disciplined classes, the feature either goes unused (over-muted) or
actively damages retention (spam-driven opt-out).

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of choosing between the thesis's four-class
  taxonomy and a simpler binary (important/not-important) model, we kept
  the four classes exactly as specified (§39), over collapsing them,
  because Social and Opportunity have materially different
  urgency/frequency needs that a binary model would blur together.

**Assumptions**
- None beyond the Constraints above.

**Traced to:** FR051–FR055 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-12

---

## BR13 — Progressive Organizer Tooling, Hidden From Ordinary Participants
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
The thesis names progressive complexity as "one of the most important UX
principles" (§70): exposing organizer-level complexity (capacity,
waitlist, co-hosts, analytics) to every ordinary participant would
contradict the "simple for beginners" design goal (§40) and bury the
product's real value under controls most users never need.

**Proposed outcome**
A Circle/Event Organizer sees progressively more capability as their
responsibility grows — attendee list, event updates/announcements,
capacity/waitlist management, co-organizer delegation, basic participation
counts (§8.4, §8.5, §70) — while an ordinary participant's experience
never surfaces this complexity. Any AI assistance eventually available to
organizers must respect existing visibility/membership/organizer
permissions and must never bypass them as a shortcut — the thesis is
explicit: "AI must not become a shortcut around permissions" (§33), with a
worked example of an AI correctly refusing to disclose private attendance.

**Affected users and systems**
Circle/Event Organizer (primary); Participant (must never see this
surface); interacts with future AI organizer tooling (BR17).

**Constraints**
- Organizer-only controls (attendee list, analytics, capacity/waitlist
  management) must be inaccessible to a non-organizer, not merely hidden
  by default UI.
- Any future AI/automation acting on an organizer's behalf must respect
  the same membership/authorization boundaries a human organizer would
  (§33).

**Out of scope (for this BR specifically)**
Advanced analytics/dashboards beyond basic attendee/participation counts
(explicit non-MVP, §59); AI-driven organizer automation itself (Phase 4,
folded into BR17).

**Worth check**
Without this, either participants are overwhelmed by irrelevant controls
(contradicting §40's core design principle) or organizers lack the tools
the thesis explicitly says they need (§8.4/§8.5) — both are named, real
deficiencies, not cosmetic gaps.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of the AI-permission-boundary rule (§33)
  applying the moment *any* AI-assisted organizer feature ships, we
  captured it here as a standing constraint rather than deferring it
  entirely to BR17's future-AI BR, over waiting until the full Phase-4
  vision exists, so the rule cannot be silently forgotten by whichever
  team ships the first AI-assisted organizer feature, however small.
- DEC-002 · In the context of Step 2's own critical review pass checking
  every inherited-Must FR against the thesis's explicit §58 MVP list
  ("Organizer: attendee list, event updates" — no capacity/waitlist or
  co-organizer bullet named), we let Step 2 refine the capacity/waitlist-
  management and co-organizer-delegation FRs to Should rather than
  treating this BR's own Must priority as automatically transitive to
  every capability its Proposed Outcome lists — attendee list and event
  updates/announcements remain Must and are fully functional without
  waitlist automation or co-organizer delegation.

**Assumptions**
- None beyond the Constraints above.

**Traced to:** FR056–FR060 (Step 2 Functional Requirements) — Must except
FR058 (capacity/waitlist) and FR059 (co-organizer delegation), refined to
Should per DEC-002.

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-12

---

## BR14 — Reporting, Blocking and Baseline Safety for Real-World Activities
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
Any product that connects people around real-world physical activities
needs a minimum safety/moderation baseline from day one — the thesis names
this as universal ("every community platform needs," §82), not optional,
and physical meetups carry a genuine safety risk a purely digital product
does not.

**Proposed outcome**
Users can report an activity, a user, an organization, or content, and
can block a user (§82). Every activity/event has a clearly-owned organizer
identity, a visible location, and a stated capacity (§83). High-risk
activities carry safety guidelines, and additional safeguards apply where
minors/family activities are involved (§83). Moderation starts simple — a
basic report/review queue and organizer controls, not an elaborate system
built ahead of real usage (§82, explicit: "do not build an enormous
moderation system before usage exists").

**Affected users and systems**
All actors (as reporters or subjects of a report); Circle/Event Organizer
(accountable identity); a Milavn Moderator/Operations role, which this BR
requires exist to actually staff the "basic report/review queue" its own
Proposed Outcome commits to — this role's *scope* is deliberately kept to
the launch-scale baseline named in the Constraints below, not "out of
scope" entirely (a correction made on second review: this line originally,
incorrectly, read as excluding admin/moderation altogether, which does
not match this BR's own Proposed Outcome or FR065).

**Constraints**
- Report and block must be available from any activity, user,
  organization, or content surface at all times.
- Organizer identity and event location must never be hidden from a
  participant who has RSVP'd — baseline accountability for physical
  meetups.
- Moderation tooling scope must match actual usage — a basic queue at
  launch, not a speculative full system (§82).

**Out of scope (for this BR specifically)**
Real-time in-activity safety monitoring or emergency-response integration
(not named by the thesis as MVP); a dedicated child-safety product surface
beyond "additional safeguards where minors/family activities are involved"
being flagged as a requirement for later design (§83).

**Worth check**
Physical, real-world meetups carry genuine physical-safety risk that a
purely digital product doesn't. The thesis treats this as a baseline
necessity, not a differentiator — removing it would make the product
irresponsible to ship at all.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of the thesis itself calling for a simple
  launch-scope moderation system ("start simple," §82), we scoped this BR
  to exactly that baseline rather than building out the full
  moderation/safety system speculatively, over a more elaborate system,
  consistent with this project's now-established practice of resolving
  concretely from source docs rather than manufacturing extra scope.
- DEC-002 · In the context of Step 5's test-scenario pass discovering that
  no moderator-facing UX/UI screen existed for the "basic report/review
  queue" this BR's own Proposed Outcome requires, we traced the root
  cause to this BR's own "Affected users and systems" line incorrectly
  stating admin/moderation was "out of scope" — an apparent copy-paste
  artifact from a different module's equivalent BR, contradicting this
  BR's own Proposed Outcome and FR065. We corrected the line rather than
  leaving it as a standing contradiction, over patching only the
  downstream UX/UI gap, because the wrong statement here is what caused
  Steps 3/4 to skip designing that screen in the first place.

**Assumptions**
- None beyond the Constraints above.

**Traced to:** FR061–FR065 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-12

---

## BR15 — Post-Event Feedback and Community-Engagement Signals
**Priority:** Must
**Status:** Ready for Review
**Confidence:** Medium — `modules.md`'s approved MOD02 scope explicitly
commits to this capability ("post-event feedback and community-engagement
signals," with `EventFeedback` named as owned data), but the source thesis
itself treats the equivalent idea (§65) only as a measurement/survey
technique rather than a fully specified product capability — this BR is
written to satisfy the former without a source-thesis citation as detailed
as the rest of this file.

**Problem**
Once an activity or event concludes, there is currently no structured way
to learn whether it actually delivered value to the people who attended,
or whether they'd do it again — and `modules.md`'s own approved MOD02
scope already commits this module to "post-event feedback and
community-engagement signals" as an owned capability (`Data owned:
Event, EventRegistration/Participation, OrganizerVerificationRecord,
EventFeedback`). Because the source thesis discusses the underlying idea
only as a north-star-metric measurement technique (§65: "Did this activity
help you do something you wanted to do?", "Would you participate again?"),
there is a real risk of this already-approved capability being silently
dropped for lack of a thesis-level feature citation as prominent as this
file's other BRs.

**Proposed outcome**
After an activity/event concludes (or a participant's attendance is marked
per BR04), the participant can optionally answer a short, lightweight
feedback prompt — did this help them do something they wanted to do, and
would they participate again (§65) — with optional free-text or category
detail. Feedback is never a precondition for anything else in the product.
It feeds two things only: (a) the organizer's own earned-reputation
signals (BR08's "event completion... community contributions" inputs),
and (b) the module's own product-quality measurement (the thesis's North
Star metric family, §61–§65) — never a public rating visible to other
participants.

**Affected users and systems**
Participant (provides feedback); Circle/Event Organizer (subject — sees
only aggregate, not per-person, feedback); feeds Reputation (BR08).

**Constraints**
- Feedback is always optional; it is never a precondition for anything
  else in the product, consistent with BR04's "no-shows aren't punished"
  principle.
- Feedback must never become a public rating/review visible to other
  users — it strengthens BR08's internal reputation signals and may inform
  organizer-facing aggregate insight, but is not a public review system,
  following directly from BR08's own no-public-rating constraint (§20).

**Out of scope (for this BR specifically)**
Any public-facing review/rating display (explicit non-goal, shared with
BR08); feedback-driven automated penalties (e.g. automatic organizer
suspension triggered by feedback alone) — any consequential action against
an organizer stays on BR14's reporting/moderation path, never this
lightweight satisfaction signal alone.

**Worth check**
`modules.md`'s own approved MOD02 scope explicitly names this capability
and its owned data entity; omitting it would silently drop something the
module's already-approved decomposition committed to, regardless of how
much or little emphasis the deeper source thesis happens to give the same
idea.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of `modules.md` committing MOD02 to post-event
  feedback while the source thesis frames the equivalent idea (§65) only
  as a measurement/survey technique rather than a fully specified feature,
  we still wrote it as its own BR here rather than treating the thesis's
  relative silence as license to drop it, over omitting it, because
  `modules.md`'s already-approved module scope is itself an authoritative
  source this step's own instructions require respecting, independent of
  which source document happens to emphasize a given capability more.

**Assumptions**
- Exact feedback question set/format is implementation-stage design, not
  frozen here — the thesis's own two example questions (§65) establish the
  spirit, not a final questionnaire.

**Traced to:** FR066–FR069 (Step 2 Functional Requirements)

**Review history**
- 2026-09-12 — Added during a second, critical approver-perspective review
  pass over the initial 17-BR draft, after finding that `modules.md`'s
  explicit "post-event feedback and community-engagement signals" /
  `EventFeedback` commitment had no corresponding BR (the source thesis's
  own relative silence on this point had let it fall through) — approved,
  krishna kategaru.

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-12

---

## BR16 — Future External Event Ecosystem and Cross-Platform Ingestion
**Priority:** Could
**Status:** Ready for Review
**Confidence:** Low — explicitly a deferred, future capability across the
source thesis, with exact ingestion/deduplication mechanics, source
selection, and trust attribution all intentionally unspecified pending the
core (Level 1/2) product proving itself first.

**Problem**
The thesis's own long-term vision has Milavn become "everything happening
around you" (§17) by ingesting events from external sources — government
sites, partner organizations, other event platforms — deduplicating them
against Milavn's own records, and linking out to external booking/
ticketing, rather than Milavn rebuilding every ticketing platform itself
(§17). This is explicitly a Phase 3, not MVP, capability: "MVP: Only Level
1 + Level 2. Level 3 and Level 4 come later" (§16, §60).

**Proposed outcome**
For whenever this is built: external sources are ingested, normalized,
validated, deduplicated against existing canonical events, attributed with
the appropriate trust level (External — Trusted Source, per BR07's
taxonomy), and indexed into the same Discovery surface as native Milavn
events, linking out to the source's own booking/ticketing (§17, §52).

**Affected users and systems**
Participant (as a Discovery consumer of external events); future
EventSource/ingestion pipeline.

**Constraints**
- Must reuse BR07's trust taxonomy rather than inventing a separate one
  for external content.
- Must not be implemented before the native (Level 1/2) product is proven,
  per the thesis's own explicit phasing (§16, §60).

**Out of scope (for this BR specifically)**
Any ingestion/deduplication mechanism at all — this BR exists purely for
traceability to `modules.md`'s approved scope and the thesis's own
long-term vision, not as work to build now.

**Worth check**
This BR passes the worth check narrowly and differently than BR01–BR14:
it is not needed for V1, but its absence from this document entirely would
silently drop a capability the source thesis explicitly names as real
future direction (§16–§17, §52). Recording it now, as a low-priority,
explicitly-deferred BR, preserves traceability without pretending it is a
near-term build commitment — the same reasoning that already established
this exact pattern for Mangaly's BR17 (Future Agent Layer).

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of every mention of external-event ingestion in
  the source thesis being marked explicitly as Phase 3/future, we recorded
  it as a low-priority, explicitly-deferred BR rather than omitting it
  entirely, over silence, modelling this directly on Mangaly's own BR17
  precedent for the identical reason: a future reviewer should not mistake
  its absence for an oversight.

**Assumptions**
- "Future" means "not in the current SDLC cycle for this module," not
  "never" — consistent with the thesis's own phased roadmap (§60).

**Traced to:** FR070–FR071 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-12

---

## BR17 — Future AI-Native Natural-Language Planning and Organizing
**Priority:** Could
**Status:** Ready for Review
**Confidence:** Low — explicitly a deferred, future capability; the
thesis's own reasoning for sequencing it last ("AI cannot compensate for
bad event data, weak identity, poor calendars... First build the
structured world. Then AI becomes powerful," §102) is treated here as
binding, not aspirational.

**Problem**
The thesis's Phase 4 vision includes natural-language discovery ("Find me
something active on Sunday morning"), an AI "Personal Weekend Planner," an
AI "Organizer" able to create/manage recurring activities on request, and
eventual voice interaction (§72–§75, §102–§103) — all explicitly sequenced
after the structured, reliable non-AI product (BR01–BR14) already works.

**Proposed outcome**
For whenever this is built: a conversational/voice interface translates
natural-language intent into the same structured Discovery/Activity-
creation/Calendar operations already defined by BR02–BR06, via an
authorized tool-calling layer — understand → recommend → authorize →
execute → record → confirm (§32, §103) — never bypassing the
authorization/consent boundaries those BRs already establish.

**Affected users and systems**
Participant, Circle/Event Organizer (as future AI-interface users); the
platform's own AI-assistant infrastructure (Common Platform concern).

**Constraints**
- Must not ship before the core structured product (BR01–BR14) is stable,
  per the thesis's own explicit sequencing (§102).
- Every AI-initiated consequential action must be authorized and
  attributable exactly as a human-initiated one would be — shared with
  BR13's identical rule (§33).

**Out of scope (for this BR specifically)**
Any natural-language or voice interface implementation at all — this BR
exists purely for scope traceability, not as work to build now.

**Worth check**
Same reasoning as BR16: recorded for traceability to the thesis's real
long-term direction, not a near-term build commitment; omitting it would
understate the module's actual approved future scope.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of AI-assistant infrastructure being a Common
  Platform concern (`modules.md` Shared Concerns) while the thesis
  describes Milavn-specific AI *behaviour*, we scoped this BR to the
  Milavn-specific behavioural requirement (respect authorization, use the
  tool-calling structure) rather than claiming to own the AI runtime
  itself, over describing a Milavn-built AI system, to respect the module
  boundary the same way Mangaly's own AI-related constraints do.

**Assumptions**
- None beyond the Constraints above.

**Traced to:** FR072–FR073 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-12

---

## BR18 — Future Local Commerce Layer: Venue Marketplace, Event Services and Sponsorship
**Priority:** Could
**Status:** Ready for Review
**Confidence:** Low — explicitly deferred; pricing, commission structure,
and vendor/partner selection are all intentionally open per the thesis's
own revenue thesis.

**Problem**
The thesis's revenue thesis (§53–§56) and cross-module integration
sections (§76–§78) describe monetizing value-creation around participation
— venue marketplace, event-services matching, sponsorship, partner-funded
benefits — rather than charging for community belonging itself. This is
explicitly cross-module (Vyapar for local business supply, Payment
Services for actual transactions, Pay Bills for partner-funded benefits)
and explicitly not MVP (§59).

**Proposed outcome**
For whenever this is built: Milavn surfaces local-business demand
generated by circles/activities (e.g. a cricket circle needing a ground)
to Vyapar (§76); sponsorship of specific activities is possible but must
be clearly labelled, never deceptive (§54–§55); none of this ever makes
ordinary community participation itself paywalled (§53, explicit:
"Ordinary users should not feel: 'I have to pay to participate in my
community.'").

**Affected users and systems**
Circle/Event Organizer, Venue, Organization; MOD01 Vyapar (business
supply), MOD06 Payment Services (transaction capture), MOD07-adjacent Pay
Bills (partner-funded benefits).

**Constraints**
- Actual payment capture/collection is MOD06 Payment Services' capability,
  not Milavn's own (`modules.md`'s explicit "Depends on: MOD06 (Payment
  Services) — paid/ticketed events, sponsorships, premium-networking
  fees"); this BR only establishes *that* Milavn may surface paid/
  sponsored/partner capability, never its transaction mechanics.
- Sponsored content must always be clearly and visibly labelled as such
  (§54).

**Out of scope (for this BR specifically)**
Any specific pricing, commission structure, or vendor/partner selection —
all explicitly deferred by the thesis itself, consistent with how
Mangaly's own monetization-adjacent BRs (BR01, BR17) were treated.

**Worth check**
Recorded for scope traceability to `modules.md`'s explicit Payment
Services dependency line and the thesis's own revenue thesis, without
pretending pricing/commerce mechanics are resolved at this stage.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of Mangaly's own equivalent monetization
  treatment already establishing a pattern in this pipeline (describe
  *that* a paid capability may exist, never specify how money moves), we
  applied the identical pattern here rather than inventing a different
  one, over resolving pricing/commission questions prematurely, for
  cross-module consistency.

**Assumptions**
- "Future" means "not in the current SDLC cycle for this module," not
  "never" — consistent with the thesis's own phased roadmap (§60) and the
  precedent set by BR16/BR17.

**Traced to:** FR074–FR075 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-12
