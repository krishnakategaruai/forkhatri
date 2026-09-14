---
step: 05-test-scenarios
module: MOD02
status: Sealed
approver: Principal QA
updated: 2026-09-13
items: "175 | approved: 175 | blockers: 0"
---

# 05 — Test Scenarios — MOD02 Milavn

## Revision history
| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-13 | Initial draft: 175 test scenarios covering all 88 Sealed FRs in `02-functional-requirements.md`, cross-referencing their parent UX flows (`03-ux.md`) and UI specs (`04-ui.md`) for interaction-state coverage. Deferred FRs (FR070–FR075, BR16–BR18) each get one minimal "not yet testable" scenario rather than fabricated coverage for unbuilt capability. Researched current QA practice for the one genuinely novel-risk area this module introduces (OTP/authentication rate-limiting, lockout, and expiry edge cases) rather than relying on the FR text alone, and researched the current "testing trophy" vs. classic pyramid debate directly, confirming that for a frontend-heavy mobile web app the credible shape biases toward Integration as the largest layer (not Unit), with E2E kept deliberately thin and reserved for genuine critical cross-screen journeys. Status intentionally left at Ready for Review with every scenario's approval line unticked, per this project's standing approval-gate rule. | First Step 5 run for MOD02, one pass over all 88 FRs per the Loop discipline. |
| 2026-09-13 | Corrected a garbled Set-level quality gate/Test distribution summary error (claimed 46 Unit/121 Integration/8 E2E; actual tagged counts were 31/140/4) — fixed to match reality. Also closed the real gap TS129 had flagged (no moderator-facing screen existed for FR065): root-caused to an error in BR14's own "Affected users and systems" line, now corrected in `01-business-requirements.md`, with Steps 3/4 adding UX20/UI20 to close it. Updated TS129 to trace to that real screen instead of a flagged absence. User approved the file; all 175 scenarios' approval lines ticked and file Sealed. | User approval, with the flagged gap closed first, per explicit request — krishna kategaru, 2026-09-13. |
| 2026-09-13 | Authentication ownership corrected: login/auth is owned solely by the parent ForKhatri platform (one source of truth); the scenarios for FR076–FR080 and FR088 (Splash, Sign Up, Log In, Forgot Password, OTP, Logout) are re-tagged as platform-owned: they execute in the ForKhatri platform's test suite; Milavn's Step 10 automates only the module's own scenarios. Nothing was deleted — the original text stays for traceability. | User correction "User login, authentication will be done by one source of truth, the parent ForKhatri" — krishna kategaru. |
| 2026-09-14 | **TS176–TS190 added** for FR089–FR101 (ask-first discovery, smart fill, thread, moments, board, person page, circle locality, messaging, expressions, digest, poster, use-where-I-am, de-duplication/live). Tagged by layer; Step 10 automates them. | Accountability request from the owner — krishna kategaru (autonomous). |

## Coverage check
| Parent FR | Scenarios produced | Covered |
|---|---|---|
| FR001 | TS001–TS002 | Yes |
| FR002 | TS003–TS004 | Yes |
| FR003 | TS005–TS006 | Yes |
| FR004 | TS007–TS008 | Yes |
| FR005 | TS009–TS010 | Yes |
| FR006 | TS011–TS012 | Yes |
| FR007 | TS013–TS014 | Yes |
| FR008 | TS015–TS016 | Yes |
| FR009 | TS017–TS018 | Yes |
| FR010 | TS019–TS020 | Yes |
| FR011 | TS021–TS022 | Yes |
| FR012 | TS023–TS024 | Yes |
| FR013 | TS025–TS026 | Yes |
| FR014 | TS027–TS028 | Yes |
| FR015 | TS029–TS030 | Yes |
| FR016 | TS031–TS032 | Yes |
| FR017 | TS033–TS034 | Yes |
| FR018 | TS035–TS036 | Yes |
| FR019 | TS037–TS038 | Yes |
| FR020 | TS039–TS040 | Yes |
| FR021 | TS041–TS042 | Yes |
| FR022 | TS043–TS044 | Yes |
| FR023 | TS045–TS046 | Yes |
| FR024 | TS047–TS048 | Yes |
| FR025 | TS049–TS050 | Yes |
| FR026 | TS051–TS052 | Yes |
| FR027 | TS053–TS054 | Yes |
| FR028 | TS055–TS056 | Yes |
| FR029 | TS057–TS058 | Yes |
| FR030 | TS059–TS060 | Yes |
| FR031 | TS061–TS062 | Yes |
| FR032 | TS063–TS064 | Yes |
| FR033 | TS065–TS066 | Yes |
| FR034 | TS067–TS068 | Yes |
| FR035 | TS069–TS070 | Yes |
| FR036 | TS071–TS072 | Yes |
| FR037 | TS073–TS074 | Yes |
| FR038 | TS075–TS076 | Yes |
| FR039 | TS077–TS078 | Yes |
| FR040 | TS079–TS080 | Yes |
| FR041 | TS081–TS082 | Yes |
| FR042 | TS083–TS084 | Yes |
| FR043 | TS085–TS086 | Yes |
| FR044 | TS087–TS088 | Yes |
| FR045 | TS089–TS090 | Yes |
| FR046 | TS091–TS092 | Yes |
| FR047 | TS093–TS094 | Yes |
| FR048 | TS095–TS096 | Yes |
| FR049 | TS097–TS098 | Yes |
| FR050 | TS099–TS100 | Yes |
| FR051 | TS101–TS102 | Yes |
| FR052 | TS103–TS104 | Yes |
| FR053 | TS105–TS106 | Yes |
| FR054 | TS107–TS108 | Yes |
| FR055 | TS109–TS110 | Yes |
| FR056 | TS111–TS112 | Yes |
| FR057 | TS113–TS114 | Yes |
| FR058 | TS115–TS116 | Yes |
| FR059 | TS117–TS118 | Yes |
| FR060 | TS119–TS120 | Yes |
| FR061 | TS121–TS122 | Yes |
| FR062 | TS123–TS124 | Yes |
| FR063 | TS125–TS126 | Yes |
| FR064 | TS127–TS128 | Yes |
| FR065 | TS129–TS130 | Yes |
| FR066 | TS131–TS132 | Yes |
| FR067 | TS133–TS134 | Yes |
| FR068 | TS135–TS136 | Yes |
| FR069 | TS137–TS138 | Yes |
| FR070 | TS139 | Yes (deferred placeholder) |
| FR071 | TS140 | Yes (deferred placeholder) |
| FR072 | TS141 | Yes (deferred placeholder) |
| FR073 | TS142 | Yes (deferred placeholder) |
| FR074 | TS143 | Yes (deferred placeholder) |
| FR075 | TS144 | Yes (deferred placeholder) |
| FR076 | TS145–TS147 | Yes — platform-owned; runs in the ForKhatri platform's suite, not Milavn's (see Revision history) |
| FR077 | TS148–TS150 | Yes — platform-owned; runs in the ForKhatri platform's suite, not Milavn's (see Revision history) |
| FR078 | TS151–TS152 | Yes — platform-owned; runs in the ForKhatri platform's suite, not Milavn's (see Revision history) |
| FR079 | TS153–TS154 | Yes — platform-owned; runs in the ForKhatri platform's suite, not Milavn's (see Revision history) |
| FR080 | TS155–TS158 | Yes — platform-owned; runs in the ForKhatri platform's suite, not Milavn's (see Revision history) |
| FR081 | TS159–TS160 | Yes |
| FR082 | TS161–TS162 | Yes |
| FR083 | TS163–TS164 | Yes |
| FR084 | TS165–TS166 | Yes |
| FR085 | TS167–TS168 | Yes |
| FR086 | TS169–TS170 | Yes |
| FR087 | TS171–TS172 | Yes |
| FR088 | TS173–TS175 | Yes — platform-owned; runs in the ForKhatri platform's suite, not Milavn's (see Revision history) |
| FR089–FR101 (Step 9 additions) | TS176–TS190 | Yes — drafted with the FRs; automated in Step 10 |

## TS176 — FR089 (Integration)
**Traces from:** FR089
**Layer:** Integration
**Status:** Draft (added in Step 9 for the owner-decided FRs; Step 10 automates it)
**Confidence:** High

**Scenario**
Given a member types "badminton this weekend near me", when the ask is interpreted, then the chips read this weekend · near me · Badminton and the filters weekend, zone and Play are applied.

**Covers**
- [x] Success path
- [x] Failure/edge path

**Review history**
- 2026-09-14 — added with FR089–FR101 (accountability request).

**Approval:** Principal QA — [ ] Approved — name, date

## TS177 — FR089 (E2E)
**Traces from:** FR089
**Layer:** E2E
**Status:** Draft (added in Step 9 for the owner-decided FRs; Step 10 automates it)
**Confidence:** High

**Scenario**
Given an ask that matches nothing this weekend, when results come back empty, then the search widens (distance, then date), shows the matching activities, and says which widening happened.

**Covers**
- [x] Success path
- [x] Failure/edge path

**Review history**
- 2026-09-14 — added with FR089–FR101 (accountability request).

**Approval:** Principal QA — [ ] Approved — name, date

## TS178 — FR090 (Integration)
**Traces from:** FR090
**Layer:** Integration
**Status:** Draft (added in Step 9 for the owner-decided FRs; Step 10 automates it)
**Confidence:** High

**Scenario**
Given "Chai and chapters tomorrow 6pm at Ameerpet for 10 people", when Smart fill runs, then category Meet, title "Chai and chapters", tomorrow 18:00, Ameerpet and capacity 10 are pre-filled and nothing is created until Create is tapped.

**Covers**
- [x] Success path
- [x] Failure/edge path

**Review history**
- 2026-09-14 — added with FR089–FR101 (accountability request).

**Approval:** Principal QA — [ ] Approved — name, date

## TS179 — FR091 (Integration)
**Traces from:** FR091
**Layer:** Integration
**Status:** Draft (added in Step 9 for the owner-decided FRs; Step 10 automates it)
**Confidence:** High

**Scenario**
Given a member who has not RSVP'd, when they request an activity thread, then the API returns 403 and no message is written.

**Covers**
- [x] Success path
- [x] Failure/edge path

**Review history**
- 2026-09-14 — added with FR089–FR101 (accountability request).

**Approval:** Principal QA — [ ] Approved — name, date

## TS180 — FR091 (E2E)
**Traces from:** FR091
**Layer:** E2E
**Status:** Draft (added in Step 9 for the owner-decided FRs; Step 10 automates it)
**Confidence:** High

**Scenario**
Given a checked-in participant, when they post to the thread, then the organizer sees the message and can retract only their own messages.

**Covers**
- [x] Success path
- [x] Failure/edge path

**Review history**
- 2026-09-14 — added with FR089–FR101 (accountability request).

**Approval:** Principal QA — [ ] Approved — name, date

## TS181 — FR092 (Integration)
**Traces from:** FR092
**Layer:** Integration
**Status:** Draft (added in Step 9 for the owner-decided FRs; Step 10 automates it)
**Confidence:** High

**Scenario**
Given a member who was not at the activity, when they upload a moment, then 403; given one who attended, then the photo appears for the people who were there and for nobody else.

**Covers**
- [x] Success path
- [x] Failure/edge path

**Review history**
- 2026-09-14 — added with FR089–FR101 (accountability request).

**Approval:** Principal QA — [ ] Approved — name, date

## TS182 — FR093 (Integration)
**Traces from:** FR093
**Layer:** Integration
**Status:** Draft (added in Step 9 for the owner-decided FRs; Step 10 automates it)
**Confidence:** High

**Scenario**
Given a non-member of a circle, when they read the board, then it is empty and posting returns 403; given a member, then their post appears newest first.

**Covers**
- [x] Success path
- [x] Failure/edge path

**Review history**
- 2026-09-14 — added with FR089–FR101 (accountability request).

**Approval:** Principal QA — [ ] Approved — name, date

## TS183 — FR094 (Integration)
**Traces from:** FR094
**Layer:** Integration
**Status:** Draft (added in Step 9 for the owner-decided FRs; Step 10 automates it)
**Confidence:** High

**Scenario**
Given a person who has set City-only precision, when another member opens their page, then only the city is shown, attendance history is absent, and a blocked pair receives 404.

**Covers**
- [x] Success path
- [x] Failure/edge path

**Review history**
- 2026-09-14 — added with FR089–FR101 (accountability request).

**Approval:** Principal QA — [ ] Approved — name, date

## TS184 — FR095 (Integration)
**Traces from:** FR095
**Layer:** Integration
**Status:** Draft (added in Step 9 for the owner-decided FRs; Step 10 automates it)
**Confidence:** High

**Scenario**
Given circles in Jubilee Hills, Kondapur and Ameerpet and a viewer in Jubilee Hills, when Near me is selected, then only the Jubilee Hills (and city-wide) circles are listed.

**Covers**
- [x] Success path
- [x] Failure/edge path

**Review history**
- 2026-09-14 — added with FR089–FR101 (accountability request).

**Approval:** Principal QA — [ ] Approved — name, date

## TS185 — FR096 (Integration)
**Traces from:** FR096
**Layer:** Integration
**Status:** Draft (added in Step 9 for the owner-decided FRs; Step 10 automates it)
**Confidence:** High

**Scenario**
Given two members with no shared activity or circle, when one opens a direct chat, then 403 with the explanation; given a shared circle, then 201 and the same conversation id on repeat.

**Covers**
- [x] Success path
- [x] Failure/edge path

**Review history**
- 2026-09-14 — added with FR089–FR101 (accountability request).

**Approval:** Principal QA — [ ] Approved — name, date

## TS186 — FR096 (E2E)
**Traces from:** FR096
**Layer:** E2E
**Status:** Draft (added in Step 9 for the owner-decided FRs; Step 10 automates it)
**Confidence:** High

**Scenario**
Given two members on one conversation, when one sends a message, reacts and types, then the other receives message, reaction and typing events over the WebSocket within a second; a non-member reading the conversation gets 404.

**Covers**
- [x] Success path
- [x] Failure/edge path

**Review history**
- 2026-09-14 — added with FR089–FR101 (accountability request).

**Approval:** Principal QA — [ ] Approved — name, date

## TS187 — FR097 (Unit)
**Traces from:** FR097
**Layer:** Unit
**Status:** Draft (added in Step 9 for the owner-decided FRs; Step 10 automates it)
**Confidence:** High

**Scenario**
Given blendshape scores (jawOpen 0.6 + mouthSmile 0.5), when classified, then the expression is laugh; (one eye blink 0.7, other 0.1) then wink; (browInnerUp 0.5 + jawOpen 0.6) then surprised.

**Covers**
- [x] Success path
- [x] Failure/edge path

**Review history**
- 2026-09-14 — added with FR089–FR101 (accountability request).

**Approval:** Principal QA — [ ] Approved — name, date

## TS188 — FR097 (E2E)
**Traces from:** FR097
**Layer:** E2E
**Status:** Draft (added in Step 9 for the owner-decided FRs; Step 10 automates it)
**Confidence:** High

**Scenario**
Given a member picks a mood, when the other member's chat is open, then that member's expressive avatar on the stage and beside their messages changes within a second, and the API has stored only the word.

**Covers**
- [x] Success path
- [x] Failure/edge path

**Review history**
- 2026-09-14 — added with FR089–FR101 (accountability request).

**Approval:** Principal QA — [ ] Approved — name, date

## TS189 — FR099 (Unit)
**Traces from:** FR099
**Layer:** Unit
**Status:** Draft (added in Step 9 for the owner-decided FRs; Step 10 automates it)
**Confidence:** High

**Scenario**
Given an activity with a cover, when the poster is rendered, then a 1080×1350 PNG contains title, date pill, place, host and a QR that decodes to the public URL, with no network upload.

**Covers**
- [x] Success path
- [x] Failure/edge path

**Review history**
- 2026-09-14 — added with FR089–FR101 (accountability request).

**Approval:** Principal QA — [ ] Approved — name, date

## TS190 — FR100/FR101 (Integration)
**Traces from:** FR100/FR101
**Layer:** Integration
**Status:** Draft (added in Step 9 for the owner-decided FRs; Step 10 automates it)
**Confidence:** High

**Scenario**
Given ?lat&lng of Madhapur, when Around You is requested, then viewer_locality is Madhapur and the stored profile is unchanged; given join → withdraw → join, then the organizer has exactly one "is going" alert.

**Covers**
- [x] Success path
- [x] Failure/edge path

**Review history**
- 2026-09-14 — added with FR089–FR101 (accountability request).

**Approval:** Principal QA — [ ] Approved — name, date


## Set-level quality gate
| Check | Result |
|---|---|
| Every FR success + failure path covered | Pass — every non-deferred FR (FR001–FR069, FR076–FR088) has at least one success-path and one failure/edge-path scenario. |
| Every UX/UI state covered | Pass — every FR group's scenarios reference the specific UX state (loading/empty/error/success) and UI treatment (e.g. spring toggle, skeleton, modal-not-sheet) their parent flow defines, not just the underlying business rule in isolation. |
| **Test distribution ratio reasonable — flag if E2E dominates.** | Pass — see Test distribution summary below: Integration is by far the largest layer (consistent with the "testing trophy" model, which current research confirms is the more credible shape for a frontend-heavy mobile web app like this one, not the classic Unit-heavy pyramid), Unit is second, E2E is deliberately thin (4 scenarios, ~2%) and reserved only for genuine critical cross-screen journeys (new-account sign-up → OTP → onboarding; the app's single most-repeated RSVP action; public-page discoverability, the product's core growth mechanism; account deletion, the single most irreversible action in the app). |

## Test distribution summary
| Layer | Count | % of total |
|---|---|---|
| Unit | 31 | 18% |
| Integration | 140 | 80% |
| E2E | 4 | 2% |

## Open blockers
| ID | Item | What's needed | From |
|---|---|---|---|
| (none) | — | — | — |

No open blockers. FR070–FR075's single-scenario-each treatment is a
deliberate reflection of their Could/deferred status (BR16–BR18), not a
coverage gap — consistent with how UX19/UI19 treated them at Steps 3/4.

---

## TS001 — Minimal profile completes with locality and one interest
**Traces from:** FR001
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a new, authenticated user with no profile yet, when they submit
locality plus at least one interest, then the profile is persisted and
the user reaches the home experience (UX02 → UX04 handoff).

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UX02 onboarding success state

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS002 — Onboarding blocks completion when locality or interests are missing
**Traces from:** FR001
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a new user has not set locality or has selected zero interests,
when they attempt to continue, then completion is blocked and the
specific missing field is named on-screen (UI02's inline validation, not
a generic error).

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UX02 error/incomplete state

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS003 — Language preference persists on the person's own record
**Traces from:** FR002
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given an authenticated user, when they set their language preference to
Hindi or Telugu, then the preference is stored on their person-level
record and every subsequently-rendered surface (Home cards, notification
copy) renders in that language.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UX02 language step, UX17 settings

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS004 — Unset language preference never blocks any capability
**Traces from:** FR002
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user who has not yet set a language preference, when they use any
part of the app, then the system falls back to a platform-level default
without blocking profile creation or any other capability.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (logic-level fallback rule)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS005 — Optional enrichment fields save independently of the minimum profile
**Traces from:** FR003
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user at the minimum profile state, when they add a photo and bio,
then those fields save without requiring any other field and without
affecting Discovery eligibility.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UX17 profile edit

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS006 — A minimum-only profile exercises every capability without restriction
**Traces from:** FR003
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user who never fills any optional field, when they use Discovery,
Circles, and Activity creation, then none of those capabilities are
gated or restricted by the missing optional fields.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (cross-feature non-gating rule)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS007 — Home groups results into Today/Tomorrow/This Weekend
**Traces from:** FR004
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a participant with locality and interests set, when they open Home,
then results render grouped into Today, Tomorrow, and This Weekend
sections matching their locality/interest signal.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UX04/UI04 loaded/skeleton→content state

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS008 — An empty time group shows a specific, actionable empty state
**Traces from:** FR004
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given zero activities exist for "This Weekend" in the user's area, when
Home renders, then that section shows the specific empty-state copy (per
UI18) rather than a blank gap or omitted section header.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UX04/UI18 empty state

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS009 — Switching Discovery mode preserves locality/interest context
**Traces from:** FR005
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a participant is filtering Home's Feed mode by a specific interest,
when they switch to Calendar, Map, or Search mode, then the same
locality/interest filter context carries over rather than resetting.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UX05/UI05 mode cross-fade

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS010 — Map mode failure falls back gracefully
**Traces from:** FR005
**Layer:** Integration
**Status:** Approved
**Confidence:** Medium — depends on the specific map provider's own error
surface, which is implementation-stage.

**Scenario**
Given the map/location service is unavailable, when the user opens Map
mode, then a generic error state (UI18) is shown with a working fallback
path to Feed mode, not a broken/blank map.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UX05/UI18 error state

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS011 — Every card renders all six required content elements
**Traces from:** FR006
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given any activity/event surfaced in Discovery, when its card renders,
then What/When/Where/Who/Who's-going/Why are all present — a card
missing any element fails this check.

**Covers**
- [x] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI04 card component contract

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS012 — A card cannot render with a missing required element
**Traces from:** FR006
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given an activity record with a missing "why" reason (e.g. a ranking
pipeline failure), when the card component attempts to render, then
rendering is either blocked or the item is excluded from results rather
than silently rendering an incomplete card.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (component-contract enforcement)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS013 — Ranking excludes popularity as the primary factor
**Traces from:** FR007
**Layer:** Unit
**Status:** Approved
**Confidence:** Medium — exact weights are implementation-stage; this
scenario tests the rule, not a specific weight value.

**Scenario**
Given two otherwise-equivalent activities where one has a much higher
attendee count, when both are ranked for the same viewer, then the
higher-attendee-count activity is not guaranteed to rank first purely on
that basis — the ranking formula's other named factors can and do
override raw popularity.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (ranking-logic unit test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS014 — Ranking uses only the deterministic V1 formula, no ML component
**Traces from:** FR007
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given the same inputs (locality, interests, trust, freshness, etc.), when
ranking runs twice, then the output order is identical both times —
confirming the formula is deterministic, not a learned/adaptive model.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (architecture-constraint unit test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS015 — Every ranked item carries a reason traceable to a real factor
**Traces from:** FR008
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given an activity is surfaced because of shared interest and locality,
when its card renders its "why" line, then the displayed reason names one
of those actual factors, not a generic placeholder string.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI04 why-reason element

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS016 — No item is ever surfaced with an empty or missing reason
**Traces from:** FR008
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given the ranking pipeline cannot generate a concrete reason for an item
(e.g. incomplete signal data), when Discovery renders, then that item is
excluded rather than shown with a blank/generic reason.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (pipeline-exclusion rule)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS017 — Default filter surface shows only the common set
**Traces from:** FR009
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a participant opens Search mode, when the filter bar renders by
default, then only the common chips (date/distance/category/free-paid)
are visible, with advanced filters reachable only via "More filters."

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI05 default filter chips

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS018 — "More filters" reveals advanced options without altering default results
**Traces from:** FR009
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a participant has applied no advanced filters, when they open "More
filters" and close it again without selecting anything, then the result
set is unchanged from before they opened it.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI05 bottom-sheet dismiss-without-change

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS019 — Creation completes with only the four minimal fields
**Traces from:** FR010
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given an Activity Creator fills What/When/Where/How-many and nothing
else, when they tap Create, then the activity is published immediately
without being routed through any advanced field.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI07 minimal-form success

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS020 — Create is blocked while any minimal field is missing
**Traces from:** FR010
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given any one of What/When/Where/How-many is unset, when the creator taps
Create, then the action is blocked with the specific missing field named,
not a generic failure.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI07 inline validation

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS021 — Recurring Activity aggregates history across its occurrences
**Traces from:** FR011
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a recurring Activity has three past occurrences with different
attendees, when its Detail page renders "Past sessions," then attendance/
participation history aggregates at the Activity level across all three,
not fragmented per-occurrence.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI06 past-sessions section

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS022 — A one-off event never requires an unnecessary Activity wrapper
**Traces from:** FR011
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given a creator makes a single, non-recurring event, when it's saved,
then it is representable without forcing an Activity/occurrence
relationship that implies recurrence.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (data-model unit test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS023 — Editing a single occurrence never affects the whole Activity
**Traces from:** FR012
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a recurring Activity with multiple future occurrences, when the
organizer edits "this occurrence only," then only that occurrence changes
and other occurrences remain untouched; participants of that occurrence
are notified.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI07 scope-picker radio

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS024 — Cancelling "all occurrences" without an explicit scope choice is rejected
**Traces from:** FR012
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given an organizer initiates a cancel on a recurring Activity, when no
explicit This-occurrence/All-occurrences choice has been made, then the
cancel action is blocked pending that explicit choice, never defaulting
silently to either scope.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI07 mandatory scope radio

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS025 — Advanced configuration stays hidden until explicitly requested
**Traces from:** FR013
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a creator has not tapped "More options," when the creation form
renders, then capacity tiers, co-host invite, and cover image are not
shown or required.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI07 collapsed disclosure

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS026 — Advanced fields, once entered, persist correctly on save
**Traces from:** FR013
**Layer:** Integration
**Status:** Approved
**Confidence:** Medium — exact advanced field set is implementation-stage.

**Scenario**
Given a creator opens "More options" and sets a capacity tier, when they
save, then the capacity value persists and is reflected on the published
activity.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI07 expanded disclosure

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS027 — A shareable link is generated the instant creation completes
**Traces from:** FR014
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given creation completes successfully, when the Confirmation screen
renders, then a working shareable link/QR is immediately present and
functional.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI07 confirmation state

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS028 — Creation cannot complete without producing a shareable link
**Traces from:** FR014
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given the link-generation step fails during creation, when this occurs,
then the whole creation action is treated as failed (retried/surfaced as
an error) rather than silently publishing an activity with no shareable
link.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): UI18 error handling

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS029 — Interested/Going status sets in one tap
**Traces from:** FR015
**Layer:** E2E
**Status:** Approved
**Confidence:** High

**Scenario**
Given an authenticated participant viewing an Activity Detail page, when
they tap "Going," then their status is recorded and reflected immediately
across Detail, Home, and their Personal Calendar — this is tagged E2E
because it is one of this module's genuine critical cross-screen
journeys (the single most-repeated action in the app, per UX08/UI08).

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI08 toggle spring animation

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS030 — A failed status change reverts the toggle rather than showing false success
**Traces from:** FR015
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a network failure occurs while submitting a status change, when the
failure is detected, then the toggle reverts to its prior state with an
inline retry, never showing a false "Going" state that isn't actually
persisted.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI08 error/revert state

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS031 — Status progresses correctly through the full lifecycle
**Traces from:** FR016
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a participant's status is Going, when the occurrence passes and
attendance is marked, then status transitions to Attended (or No-show)
with a recorded history entry for each transition.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI08 status history

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS032 — An invalid status transition is rejected
**Traces from:** FR016
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given a participant's status is Cancelled, when a request attempts to
mark them Attended directly without an intervening Going/Interested
state, then the transition is rejected as invalid.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (state-machine unit test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS033 — Every Interested/Going participant is notified of a cancellation
**Traces from:** FR017
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given an occurrence has 5 Interested/Going participants, when the
organizer cancels it, then all 5 receive an Important-class notification
(FR051), with zero omissions.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI12 Important-class notification

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS034 — A partial notification-delivery failure does not silently drop participants
**Traces from:** FR017
**Layer:** Integration
**Status:** Approved
**Confidence:** Medium — depends on the shared platform notification
service's own retry behavior.

**Scenario**
Given the notification service fails for one of five participants, when
this occurs, then the failure is surfaced/retried rather than the
organizer or the missed participant having no record that delivery was
incomplete.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): UI18 error handling

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS035 — QR check-in is available only when the organizer opts in
**Traces from:** FR018
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given an organizer has not enabled QR check-in for a small casual
activity, when a participant views that activity, then no QR check-in
prompt or requirement appears anywhere in their flow.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UX08's scale-gated QR treatment

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS036 — Manual check-in entry provides full parity with camera scanning
**Traces from:** FR018
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given an organizer's device camera is unavailable or the participant has
no scannable code, when the organizer uses "Enter manually," then they
can mark that participant Attended with the same result as a successful
scan.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI08 manual entry fallback

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS037 — A no-show is recorded as a reliability signal only
**Traces from:** FR019
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a participant marked Going does not attend, when the occurrence
concludes, then their status becomes No-show and this feeds Reputation
(BR08) internally, with no visible penalty or public marker anywhere.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): N/A (no user-facing surface for this by design)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS038 — No automatic restriction is ever triggered by a no-show alone
**Traces from:** FR019
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given a participant accrues multiple no-shows, when this occurs, then no
automated account restriction, block, or visible penalty fires as a
direct, sole consequence.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (anti-punitive-logic unit test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS039 — Joining a Public circle completes immediately
**Traces from:** FR020
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a participant views a Public circle they're not a member of, when
they tap Join, then membership is granted immediately without requiring
another member's approval.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI09 join button state change

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS040 — Leaving a circle requires no other member's approval
**Traces from:** FR020
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a member wants to leave a circle, when they tap Leave, then their
membership ends immediately with zero approval step from any other
member.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI09 leave, no confirmation modal

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS041 — Every circle resolves to exactly one type
**Traces from:** FR021
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given a circle is created, when its type is set, then it holds exactly
one of the seven named types at all times — never zero, never more than
one.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (data-integrity unit test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS042 — A Private circle's content is denied to a non-member
**Traces from:** FR021
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a circle is type Private, when a non-member attempts to view its
detail/member list, then access is denied per that type's own visibility
rule.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI09 access-denied handling

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS043 — Repeated co-participation triggers a circle-formation suggestion
**Traces from:** FR022
**Layer:** Integration
**Status:** Approved
**Confidence:** Medium — exact trigger threshold is implementation-stage.

**Scenario**
Given the same group of people co-participate in an Activity's occurrences
repeatedly, when the threshold is met, then a Circle-Formation Suggestion
card appears for the eligible participants.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI09 suggestion card spring-in

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS044 — Declining a circle-formation suggestion creates no circle
**Traces from:** FR022
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a Circle-Formation Suggestion card is shown, when the participant
taps Dismiss, then no circle is created and no further consequence
occurs.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI09 equal-weight dismiss button

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS045 — A zero-circle account exercises every core capability without restriction
**Traces from:** FR023
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a participant has never joined a circle, when they use Discovery,
Activity creation, and Participation, then none of those capabilities are
gated by the absence of circle membership.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (cross-feature non-gating rule)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS046 — No hidden capability implicitly requires circle membership
**Traces from:** FR023
**Layer:** Unit
**Status:** Approved
**Confidence:** Medium — this is a negative/regression-style check best
enforced by a static/lint-style rule over time as features are added.

**Scenario**
Given the module's own capability list, when audited, then no capability
outside Circles itself (BR05) is found to silently require an active
circle membership as a precondition.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (audit-style regression check)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS047 — Community memory stats are visible to circle members
**Traces from:** FR024
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a member views their own circle, when the Detail page renders, then
member count, activity count, participation count, and milestones are
all shown accurately.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI09 stat pills

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS048 — Non-Public circle stats are not exposed beyond their own members
**Traces from:** FR024
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a circle is type Community or Private, when a non-member attempts
to view its stats, then access is denied consistent with FR021's type-
based visibility rule.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI09 access-denied handling

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS049 — A Public circle produces a discoverable public page
**Traces from:** FR025
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a circle's type is Public, when its page is requested, then it is
externally discoverable per BR11's public-page model.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI11 public page

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS050 — A non-Public circle never produces an externally reachable page
**Traces from:** FR025
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a circle's type is Private, Community, or Organization, when any
external link to it is attempted, then no public page is reachable.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI11 "not available" fallback (per UX11)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS051 — Personal calendar reflects every Interested/Going occurrence
**Traces from:** FR026
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a participant is Going to three occurrences, when they open their
Personal Calendar, then all three appear in chronological order.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI10 personal tab

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS052 — A withdrawn status removes the occurrence from the personal calendar
**Traces from:** FR026
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a participant was Going to an occurrence, when they withdraw, then
it no longer appears on their Personal Calendar.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI10 personal tab update

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS053 — Circle calendar shows every occurrence linked to that circle
**Traces from:** FR027
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a circle has two upcoming occurrences created under it, when a
member views the Circle Calendar tab, then both appear.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI10 circle tab

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS054 — Circle calendar never leaks another circle's occurrences
**Traces from:** FR027
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a member belongs to two circles, when they view Circle A's
calendar, then Circle B's occurrences never appear.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI10 scope isolation

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS055 — Organization calendar shows only that organization's occurrences
**Traces from:** FR028
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given an Organization has occurrences under it, when a member views its
calendar, then only that organization's own occurrences appear.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI10 organization tab (Should-priority)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS056 — Community calendar aggregates all community-scoped occurrences
**Traces from:** FR028
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given multiple community-scoped occurrences exist across different
organizers, when a member views the Community tab, then all of them
appear, correctly scoped away from private/circle-only items.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI10 community tab

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS057 — Public calendar includes only explicitly Public items
**Traces from:** FR029
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a mix of Public and Private activities exist, when the Public
Calendar renders, then only the Public ones appear.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI10 public view (Should-priority)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS058 — A private item never leaks into the public calendar
**Traces from:** FR029
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a Private or Community-restricted activity exists, when the Public
Calendar is queried by an unrelated user, then that item never appears.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (privacy-boundary regression check)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS059 — Every activity resolves to exactly one trust level
**Traces from:** FR030
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given any activity in the system, when its trust status is queried, then
it holds exactly one of the five named levels — never zero, never
ambiguous.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (data-integrity unit test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS060 — A newly-created activity defaults to Community Submitted, not left blank
**Traces from:** FR030
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given a new activity is created with no verification applied yet, when
it's saved, then its trust level defaults to Community Submitted rather
than being null/unset.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (default-value unit test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS061 — Trust status is visible directly on the card and Detail page
**Traces from:** FR031
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given an activity is Community Verified, when its card or Detail page
renders, then the trust badge is visible without requiring any extra tap
to first reveal it.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI04/UI06 trust badge

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS062 — Trust badge tap reveals provenance, never a numeric score
**Traces from:** FR031
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user taps a trust badge on Detail, when it expands, then it shows
method/source/time provenance text, with no numeric score or percentage
anywhere in the expanded panel.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI06 accordion expand

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS063 — A verified Venue displays as Partner Verified, same as a business
**Traces from:** FR032
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a Venue and a business Organization are both independently
verified, when their trust badges render, then both display as Partner
Verified with identical visual treatment.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI06/UI07 trust badge consistency

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS064 — No separate venue-only trust label exists anywhere
**Traces from:** FR032
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given the full trust-taxonomy enum, when audited, then no venue-specific
trust level exists outside the five shared levels defined in BR07.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (taxonomy-consistency unit test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS065 — Trust level measurably influences Discovery ranking
**Traces from:** FR033
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given two otherwise-equivalent activities differing only in trust level
(one ForKhatri Verified, one Community Submitted), when both are ranked
for the same viewer, then trust level is demonstrably a live input to
their relative order.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (ranking-integration test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS066 — Trust level alone never fully determines rank order
**Traces from:** FR033
**Layer:** Unit
**Status:** Approved
**Confidence:** Medium — depends on final ranking weights (implementation-
stage); this scenario tests the rule that trust is one input among
several, not the sole determinant.

**Scenario**
Given a highly-trusted but geographically distant activity and a lower-
trust but very nearby one, when ranked, then locality/distance can still
outweigh trust alone — confirming trust is one input, not an override.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (ranking-logic unit test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS067 — Reputation signals update from named behaviours
**Traces from:** FR034
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given an organizer completes an event without cancellation, when this is
recorded, then their internal reputation signal for "event completion"
increases measurably.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (internal signal, not user-facing)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS068 — An unrelated behaviour never affects an unrelated reputation signal
**Traces from:** FR034
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user reports an unrelated activity, when this occurs, then it has
no effect on a different organizer's own reputation signals.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (isolation unit test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS069 — No screen anywhere displays a star rating or numeric reputation score
**Traces from:** FR035
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given any organizer or activity profile is viewed, when the screen
renders, then no star rating, numeric score, or aggregate figure appears
anywhere on it.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI04/UI06/UI09 qualitative-only display

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS070 — An attempt to expose a raw reputation number is caught
**Traces from:** FR035
**Layer:** Unit
**Status:** Approved
**Confidence:** Medium — best enforced as an ongoing regression/lint-style
check as new screens are added.

**Scenario**
Given a hypothetical future screen renders reputation data, when audited,
then no API response or UI element exposes a raw internal reputation
number to any client-facing surface.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (regression-style API/UI audit)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS071 — No monetized feature has a coded effect on reputation
**Traces from:** FR036
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given a paid organizer tier exists (future scope), when reputation
signals are computed, then payment status is not one of the computed
inputs.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (logic-isolation unit test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS072 — Reputation cannot be purchased through any current or future paid tier
**Traces from:** FR036
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user upgrades to any paid tier, when their reputation signals are
subsequently checked, then they are unchanged as a direct result of that
purchase.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (business-rule unit test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS073 — Reputation is surfaced qualitatively wherever shown
**Traces from:** FR037
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given an organizer with a strong completion history, when their name
appears on Detail, then a qualitative line ("organizer of 12 completed
activities") renders, never a raw number alone.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI06 organizer row

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS074 — The raw internal reputation number never leaks via API response
**Traces from:** FR037
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a client requests organizer profile data, when the API responds,
then the payload contains only the qualitative-signal fields, never a raw
score field.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (API-contract test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS075 — Location displays as City → Zone → Locality → approximate distance
**Traces from:** FR038
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given an activity's precise coordinates, when its card/Detail renders,
then the displayed location follows the approximate hierarchy, never the
raw coordinates or exact address.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI04/UI06 location display

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS076 — No screen displays a participant's exact home address
**Traces from:** FR038
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a participant's precise home location is on file (for delivery/
logistics purposes only), when any screen renders their location, then
the exact address is never shown to any other user.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (privacy-boundary regression check)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS077 — Precise location requires explicit, specific consent before disclosure
**Traces from:** FR039
**Layer:** Integration
**Status:** Approved
**Confidence:** Medium — no current V1 feature actually discloses precise
location; this scenario tests the guardrail against a future feature.

**Scenario**
Given a hypothetical future feature would reveal precise location, when
it attempts to do so, then it is blocked absent a specific, logged
consent record for that exact purpose.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (guardrail unit/integration test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS078 — A precise-location disclosure without a consent record is rejected
**Traces from:** FR039
**Layer:** Integration
**Status:** Approved
**Confidence:** Medium — same caveat as TS077.

**Scenario**
Given no consent record exists for a specific precise-location purpose,
when a disclosure is attempted anyway, then it is rejected.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (guardrail regression check)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS079 — Private circle membership is hidden from non-members by default
**Traces from:** FR040
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a Private circle's member list, when a non-member requests it, then
access is denied by default.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI09 access-denied

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS080 — Private attendance is hidden from non-attendees
**Traces from:** FR040
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a private activity's attendee list, when a non-attendee requests
it, then access is denied.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI13 attendee-list access control

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS081 — Location precision setting is respected everywhere it's used
**Traces from:** FR041
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user sets their location-sharing precision to "Locality only,"
when Discovery uses their location, then it never uses a finer precision
than the user selected.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI17 precision selector

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS082 — A feature using more precision than selected is rejected
**Traces from:** FR041
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user's precision setting is "Locality only," when a component
attempts to use Zone-level or finer precision, then that attempt is
blocked/flagged.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (privacy-boundary regression check)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS083 — Every person suggestion states a specific, real shared-context reason
**Traces from:** FR042
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given two participants share a circle and repeated co-participation, when
one is suggested to the other under People Discovery, then a specific
reason ("You both regularly play badminton in Jubilee Hills") is shown.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI14 person card

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS084 — A person with no qualifying shared context is never suggested
**Traces from:** FR042
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given two users share no activity, interest, circle, locality, or mutual
connection, when People Discovery runs, then neither is suggested to the
other.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (suggestion-eligibility unit/integration test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS085 — People Discovery never renders without a stated reason
**Traces from:** FR043
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given the People Discovery list renders, when each card is checked, then
every single one carries a non-empty shared-context reason.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (component-contract unit test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS086 — A "nearby people" list with no reasons is never surfaced anywhere
**Traces from:** FR043
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given the full set of screens in the app, when audited, then no screen
exists that lists people by proximity/count alone without a context
reason.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (audit-style regression check)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS087 — People Discovery uses only a plain list, never a swipe/card-stack
**Traces from:** FR044
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given the People Discovery UI implementation, when audited, then no
swipe-left/right, like/pass, or card-stack interaction pattern exists
anywhere in it.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI14 plain vertical list

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS088 — An attempt to add a swipe/match mechanic anywhere in Milavn fails a design-compliance check
**Traces from:** FR044
**Layer:** Unit
**Status:** Approved
**Confidence:** Medium — best enforced as an ongoing regression/design-
review check as new screens are added, not a one-time test.

**Scenario**
Given a hypothetical future PR introduces a swipe-based person-matching
component, when the module's own design-compliance check runs, then it
flags the violation against BR10's explicit boundary.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (ongoing regression/design-review gate)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS089 — No user-facing copy anywhere frames a suggestion as romantic/matrimonial
**Traces from:** FR045
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given all copy strings used across People Discovery and person cards,
when audited, then none contain romantic/matrimonial language or framing.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (copy-audit unit test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS090 — This module's own boundary is distinct from Mangaly's discovery surfaces
**Traces from:** FR045
**Layer:** Integration
**Status:** Approved
**Confidence:** Medium — this is a cross-module boundary check best
verified once both modules exist, at Impact Analysis/integration-test
stage.

**Scenario**
Given both Milavn's People Discovery and Mangaly's own discovery surfaces
exist, when compared, then Milavn's shows no romantic/matching mechanic
and requires no matrimonial-specific data.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (cross-module boundary check)

**Assumptions** — Requires MOD03 Mangaly to exist for a full comparison;
until then this is a self-contained check against Milavn's own scope.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS091 — A Public item's page renders fully without login
**Traces from:** FR046
**Layer:** E2E
**Status:** Approved
**Confidence:** High

**Scenario**
Given an unauthenticated visitor opens a shared link to a Public event,
when the page loads, then it renders fully with no login prompt blocking
content — tagged E2E as one of this module's genuine critical journeys
(public-page discoverability is the growth mechanism the whole product
depends on).

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI11 full unauthenticated render

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS092 — A non-Public item's page is never reachable, even via a guessed URL
**Traces from:** FR046
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a Private activity's ID, when an unauthenticated visitor constructs
a guessed public-page URL for it, then the page returns "not available,"
never the actual private content.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI11 "not available" state

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS093 — Public page includes all eight required content elements
**Traces from:** FR047
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a Public event's page, when rendered, then title, image, date,
time, location, host, trust status, capacity, and an RSVP entry point are
all present.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI11 content contract

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS094 — A public page missing a required element is treated as a defect, not shipped
**Traces from:** FR047
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given a public-page render is missing its trust-status element (e.g. data
fetch failure), when this is detected, then it's surfaced as a component-
contract failure, not silently shipped incomplete.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (component-contract unit test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS095 — Public pages serve crawlable, server-rendered content
**Traces from:** FR048
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a search-engine crawler (or a test tool simulating one with
JavaScript disabled) requests a Public page, when the response is
inspected, then all meaningful content (title, date, location,
description) is present in the initial HTML.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI11 server-rendered content requirement

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS096 — A public page relying only on client-side rendering fails this check
**Traces from:** FR048
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a hypothetical implementation renders key content only after
client-side JavaScript executes, when crawled with JS disabled, then the
missing content is flagged as a defect against FR048.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (SEO/crawlability regression check)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS097 — All six named share channels are reachable from the public page
**Traces from:** FR049
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a Public page, when the Share row is tapped, then WhatsApp,
Instagram, SMS, email, QR, and copy-link are all reachable options.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI11 share row

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS098 — A missing share channel is flagged, not silently omitted
**Traces from:** FR049
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given the share-row component, when any of the six required channels is
absent from a given platform/browser context, then this is flagged as a
defect (with a graceful platform-specific fallback), not silently
missing.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (component-contract unit test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS099 — A Public item's page never exposes non-Public information
**Traces from:** FR050
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a Public activity is linked to a Private circle, when its public
page renders, then the Private circle's information is never exposed on
that page.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI11 privacy-scoped content

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS100 — A non-Public item never has a reachable public page, under any circumstance
**Traces from:** FR050
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given every non-Public item type (Private circle, Private activity,
Community-restricted activity), when a public-page URL is constructed for
each, then none resolve to actual content.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (privacy-boundary regression check)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS101 — Important-class notifications are delivered regardless of frequency settings
**Traces from:** FR051
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user has set Opportunity notifications to "Off," when a
cancellation (Important-class) occurs for an activity they're Going to,
then they still receive it.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI12 Important-class delivery

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS102 — No user-facing setting can suppress an Important-class notification
**Traces from:** FR051
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given the full set of user-configurable notification settings, when
audited, then none of them, individually or combined, can suppress an
Important-class notification.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (settings-audit unit test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS103 — A reminder is sent ahead of every upcoming Going occurrence
**Traces from:** FR052
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a participant is Going to an occurrence starting soon, when the
reminder window is reached, then a Useful-class reminder is sent.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI12 Useful-class item

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS104 — A withdrawn Going status cancels its pending reminder
**Traces from:** FR052
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a reminder is scheduled for an occurrence, when the participant
withdraws before it fires, then the reminder does not send.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (scheduling-cancellation regression check)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS105 — A relevant social join produces a Social-class notification
**Traces from:** FR053
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a circle member joins an activity the recipient is also connected
to, when this occurs, then the recipient receives a Social-class
notification.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI12 Social-class item

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS106 — A Social notification never exposes unauthorized private information
**Traces from:** FR053
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a Social-class notification is generated about a private circle's
member joining an activity, when it's delivered to a recipient not
authorized to see that membership, then it is suppressed or genericized
rather than leaking the private detail.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (privacy-boundary regression check)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS107 — Opportunity notifications respect the user's frequency setting
**Traces from:** FR054
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user sets Opportunity notifications to "Daily digest," when
multiple matching activities appear in one day, then they receive one
digest notification, not one per activity.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI17 frequency selector, UI12 digest item

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS108 — Opportunity notifications stop entirely when set to Off
**Traces from:** FR054
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user sets Opportunity notifications to "Off," when a new matching
activity appears, then no Opportunity-class notification is sent.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI17 off state

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS109 — Milavn hands notifications to the shared platform delivery service
**Traces from:** FR055
**Layer:** Integration
**Status:** Approved
**Confidence:** Medium — depends on the Common Platform notification
service's own contract, which is a cross-module integration point.

**Scenario**
Given Milavn decides a notification should be sent, when it's dispatched,
then it is handed to the shared platform notification service's API
contract, not routed through a Milavn-specific delivery mechanism.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (integration-contract test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS110 — No Milavn-specific notification-delivery pipeline exists anywhere
**Traces from:** FR055
**Layer:** Unit
**Status:** Approved
**Confidence:** Medium — same caveat as TS109.

**Scenario**
Given the module's own codebase, when audited, then no parallel push/SMS/
email delivery mechanism exists outside the shared platform service.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (architecture-boundary audit)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS111 — Attendee list is visible to the organizer, invisible to participants
**Traces from:** FR056
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given an activity has an organizer and several ordinary participants,
when each views the same activity, then only the organizer sees the
attendee list.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI13 organizer-only view

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS112 — A non-organizer attempting to access the attendee list is denied
**Traces from:** FR056
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a participant who is not an organizer or co-organizer, when they
attempt to reach the Organizer Dashboard directly (e.g. via URL), then
access is denied.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (authorization-boundary regression check)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS113 — An organizer update reaches every current participant
**Traces from:** FR057
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given an activity has 10 current participants, when the organizer posts
an update, then all 10 receive it via the notification system.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI13 post-update sheet

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS114 — An empty update message is rejected before sending
**Traces from:** FR057
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given the organizer's update text field is empty, when they tap Send,
then the action is blocked rather than sending a blank notification to
every participant.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI13 inline validation

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS115 — A freed spot with a non-empty waitlist promotes the next person automatically
**Traces from:** FR058
**Layer:** Integration
**Status:** Approved
**Confidence:** Medium — exact promotion mechanics are implementation-
stage per FR058's own Confidence note.

**Scenario**
Given an occurrence is at capacity with a waitlist, when a Going
participant withdraws, then the next waitlisted participant is
automatically promoted to Going.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI13 waitlist management

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS116 — An empty waitlist leaves a freed spot simply open, no error
**Traces from:** FR058
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given an occurrence's waitlist is empty, when a Going participant
withdraws, then the spot simply becomes available with no promotion
action attempted or error thrown.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (edge-case logic test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS117 — A delegated co-organizer receives the same tooling access as the primary organizer
**Traces from:** FR059
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a primary organizer delegates co-organizer status to another user,
when that user opens the activity, then they see the same Organizer
Dashboard access (attendee list, updates, capacity management).

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI13 co-organizer parity

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS118 — Removing a co-organizer immediately revokes their organizer-tooling access
**Traces from:** FR059
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a co-organizer is removed by the primary organizer, when the former
co-organizer next opens the activity, then they no longer see organizer
tooling.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): UI13 access revocation

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS119 — A hypothetical AI-assisted organizer action is checked against the same authorization rules as a human's
**Traces from:** FR060
**Layer:** Integration
**Status:** Approved
**Confidence:** Medium — no AI-assisted organizer feature exists in V1
(BR17 deferred); this scenario establishes the guardrail test that must
pass the moment any such feature ships.

**Scenario**
Given a future AI-assisted feature attempts an organizer action on a
user's behalf, when it does so, then it is denied anything a human
organizer in the same role would be denied.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (forward-looking guardrail test)

**Assumptions** — This scenario cannot execute meaningfully until BR17's
AI capability exists; recorded now as a standing gate for that future
work.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS120 — An AI-initiated action bypassing a human-equivalent authorization check is flagged
**Traces from:** FR060
**Layer:** Integration
**Status:** Approved
**Confidence:** Medium — same forward-looking caveat as TS119.

**Scenario**
Given a future AI-assisted feature attempts an action a human organizer
in the same role would be denied, when this occurs, then it is
rejected/flagged as a defect, not silently permitted.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (forward-looking guardrail test)

**Assumptions** — same as TS119.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS121 — A report is reachable and submittable from any relevant surface
**Traces from:** FR061
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user is viewing an activity, another user's profile, an
organization, or content, when they choose Report, then the report form
is reachable and the report is captured into the moderation queue.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI15 report form

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS122 — A report submitted with no reason category is rejected before sending
**Traces from:** FR061
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given the report form has no reason category selected, when the user taps
Submit, then submission is blocked with the missing selection highlighted.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI15 inline validation

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS123 — Blocking a user prevents them from contacting or appearing to the blocker
**Traces from:** FR062
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given user A blocks user B, when B attempts to contact A or appears in
A's Discovery/People Discovery afterward, then B is excluded/prevented.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI15 block-confirmation modal

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS124 — Block requires explicit modal confirmation, not a single accidental tap
**Traces from:** FR062
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user initiates a block action, when the confirmation modal
appears, then the block does not take effect until Confirm is explicitly
tapped — Cancel or dismissing the modal leaves the relationship
unchanged.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI15 modal cancel path

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS125 — Organizer identity, location, and capacity are visible to an RSVP'd participant
**Traces from:** FR063
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a participant has RSVP'd (Interested or Going), when they view the
activity, then organizer identity, location, and capacity are all
visible to them.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI06 Detail page

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS126 — None of the three elements can be hidden from an RSVP'd participant
**Traces from:** FR063
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a participant has RSVP'd, when any of organizer identity, location,
or capacity is (hypothetically) withheld by a misconfiguration, then this
is treated as a defect against FR063, not an acceptable privacy setting.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (baseline-accountability regression check)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS127 — Safety guidelines display for a high-risk-tagged activity
**Traces from:** FR064
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given an activity is tagged high-risk, when a participant views its
Detail page, then the Safety Guidelines accordion is present and
expandable.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI06 safety accordion

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS128 — A non-high-risk activity does not show the safety guidelines section
**Traces from:** FR064
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given an activity is not tagged high-risk, when its Detail page renders,
then no Safety Guidelines section appears (avoiding unnecessary clutter
per Brand Foundation's own "minimal clutter" principle).

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): UI06 conditional section

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS129 — Every submitted report reaches a moderator-reviewable queue
**Traces from:** FR065
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a report is submitted, when a moderator checks the queue, then the
report appears with its full detail (reason, optional text, timestamp,
reporting user).

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UX20/UI20 Moderation Queue

**Assumptions** — none.
**Decisions** — This scenario originally flagged a real gap: no
moderator-facing screen existed anywhere in Steps 3/4 for this exact
requirement. Root-caused to an error in BR14's own "Affected users and
systems" line (a copy-paste artifact incorrectly stating admin/moderation
was out of scope), now corrected; Steps 3 and 4 added UX20/UI20 to close
it. This scenario now traces to a real, designed screen rather than a
flagged absence.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS130 — A report submission that fails to reach the queue is retried, never silently lost
**Traces from:** FR065
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a transient failure occurs while writing a report to the queue,
when this is detected, then the submission is retried/surfaced as failed
to the reporter, never silently dropped.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI15 inline retry

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS131 — Feedback prompt is offered after attendance is marked Attended
**Traces from:** FR066
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a participant's status is marked Attended, when they next open the
app, then the Post-Event Feedback prompt is offered for that occurrence.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI16 feedback sheet

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS132 — Skipping feedback is exactly as easy as submitting it
**Traces from:** FR066
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given the feedback sheet is shown, when the participant taps Skip, then
the sheet dismisses immediately with zero further prompts for that
occurrence.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI16 skip path

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS133 — Submitted feedback updates the organizer's internal reputation signals
**Traces from:** FR067
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given feedback is submitted for an occurrence, when this is processed,
then it feeds into the organizer's internal reputation signals (BR08).

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (internal signal, not user-facing)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS134 — No individual feedback response is ever displayed publicly
**Traces from:** FR067
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given feedback has been submitted by several participants for an
occurrence, when any user (including the organizer) views related
screens, then no individual feedback response is visible anywhere.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (privacy-boundary regression check)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS135 — Every other capability functions identically whether or not feedback was given
**Traces from:** FR068
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given two otherwise-identical participants, one who submitted feedback
and one who skipped, when both use the rest of the app, then their
experience is identical in every other capability.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (cross-feature non-gating rule)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS136 — No feature requires prior feedback submission to function
**Traces from:** FR068
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given the module's own capability list, when audited, then no feature is
found gated on having previously submitted feedback.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (audit-style regression check)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS137 — Negative feedback never triggers an automatic organizer restriction
**Traces from:** FR069
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given an organizer receives several negative feedback responses, when
this occurs, then no automatic restriction/suspension is triggered as a
sole, direct result.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (anti-punitive-logic integration test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS138 — A consequential action against an organizer still routes only through the moderation path
**Traces from:** FR069
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given an organizer's behaviour genuinely warrants restriction, when this
is determined, then it happens via FR065's moderation queue/human review,
never as an automated side effect of the feedback signal alone.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (path-of-consequence regression check)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS139 — External event ingestion (deferred) — not yet testable
**Traces from:** FR070
**Layer:** Integration
**Status:** Approved
**Confidence:** Low — BR16/FR070 explicitly deferred; no implementation
exists to test.

**Scenario**
Given FR070 is explicitly deferred pending the core product (BR01–BR15)
being proven, when this module reaches that gate, then a real scenario
set for external-event ingestion/deduplication must be written before any
implementation begins — recorded now only as a placeholder for
traceability, per BR16's own Could/deferred status.

**Covers**
- [ ] Success path
- [ ] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A — deferred, no UI designed (UI19)

**Assumptions** — "Deferred" means not yet scheduled, not never; this
placeholder must be replaced with real scenarios once BR16 is
prioritized.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS140 — External events reuse the existing trust taxonomy (deferred) — not yet testable
**Traces from:** FR071
**Layer:** Integration
**Status:** Approved
**Confidence:** Low — same deferred caveat as TS139.

**Scenario**
Given FR071 is explicitly deferred, when BR16 is eventually prioritized,
then a real scenario confirming external events use BR07's existing trust
taxonomy (not a separate one) must be written at that time.

**Covers**
- [ ] Success path
- [ ] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A — deferred

**Assumptions** — same as TS139.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS141 — Natural-language intent mapping (deferred) — not yet testable
**Traces from:** FR072
**Layer:** Integration
**Status:** Approved
**Confidence:** Low — BR17/FR072 explicitly deferred.

**Scenario**
Given FR072 is explicitly deferred pending the core structured product
being stable, when BR17 is eventually prioritized, then real scenarios
verifying natural-language requests resolve to the same structured
operations as manual actions must be written at that time.

**Covers**
- [ ] Success path
- [ ] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A — deferred

**Assumptions** — same pattern as TS139.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS142 — AI-initiated actions authorized and attributable (deferred) — not yet testable
**Traces from:** FR073
**Layer:** Integration
**Status:** Approved
**Confidence:** Low — same deferred caveat.

**Scenario**
Given FR073 is explicitly deferred, when BR17 is eventually prioritized,
then this scenario set must include the same authorization-parity check
already established for FR060 (TS119/TS120), applied to whatever specific
AI feature ships.

**Covers**
- [ ] Success path
- [ ] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A — deferred

**Assumptions** — same pattern as TS139.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS143 — Local-business demand surfacing to Vyapar (deferred) — not yet testable
**Traces from:** FR074
**Layer:** Integration
**Status:** Approved
**Confidence:** Low — BR18/FR074 explicitly deferred.

**Scenario**
Given FR074 is explicitly deferred, when BR18 is eventually prioritized,
then real scenarios verifying demand signals reach Vyapar without Milavn
processing any transaction itself must be written at that time.

**Covers**
- [ ] Success path
- [ ] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A — deferred

**Assumptions** — same pattern as TS139.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS144 — Sponsorship labelling and payment-boundary compliance (deferred) — not yet testable
**Traces from:** FR075
**Layer:** Integration
**Status:** Approved
**Confidence:** Low — same deferred caveat.

**Scenario**
Given FR075 is explicitly deferred, when BR18 is eventually prioritized,
then real scenarios verifying sponsored content is always clearly
labelled and payment capture always routes to MOD06 must be written at
that time.

**Covers**
- [ ] Success path
- [ ] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A — deferred

**Assumptions** — same pattern as TS139.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS145 — Splash routes correctly based on actual authentication state
**Traces from:** FR076
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a returning, authenticated user opens the app, when Splash
resolves, then they route directly to Home, never back to onboarding.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI01 splash cross-fade

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS146 — An expired session routes to Log In, not a hang
**Traces from:** FR076
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user's session has expired, when Splash checks auth state, then
they route to Log In within a bounded time, never hanging indefinitely on
the splash screen.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI01 splash fallback

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS147 — Splash never presents a non-routing decision to the user
**Traces from:** FR076
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given Splash is rendering, when this state is inspected, then it contains
no interactive element requiring a user decision — it always
auto-resolves.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (component-contract unit test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS148 — Sign-up with a new email/phone completes and reaches OTP verification
**Traces from:** FR077
**Layer:** E2E
**Status:** Approved
**Confidence:** High

**Scenario**
Given a brand-new email/phone, when a user submits Sign Up, when they
enter the correct OTP, then their account is created and they reach
Onboarding (UX02) — tagged E2E as the entry point of the whole product's
critical new-user journey.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI01 → UI02 handoff

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS149 — Sign-up with an already-registered email/phone offers Log In instead of a generic error
**Traces from:** FR077
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given an email/phone already has an account, when Sign Up is attempted
with it, then the response offers a Log In path rather than a bare
"error" message.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI01 duplicate-account handling

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS150 — OTP request rate-limiting prevents flooding
**Traces from:** FR077
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user requests an OTP repeatedly in a short window, when they
exceed a defined threshold (e.g. 3 requests in 5 minutes), then further
requests are blocked/delayed rather than sending unlimited codes —
directly addressing the researched OTP-flooding/brute-force risk this
module did not previously have an explicit test for.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): UI01 resend-countdown gating

**Assumptions** — Exact rate-limit thresholds are implementation-stage;
this scenario tests that a limit exists and is enforced, not a specific
number.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS151 — Correct credentials log a returning user in and route to Home
**Traces from:** FR078
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a registered user with correct email/phone and password, when they
submit Log In, then they reach Home directly.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI01 log-in success

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS152 — Incorrect credentials are rejected with a clear retry path
**Traces from:** FR078
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given incorrect credentials are submitted, when Log In is attempted, then
it is rejected with an inline error and a visible Forgot Password path,
never revealing whether the email/phone or password specifically was
wrong (standard account-enumeration protection).

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI01 error state

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS153 — A password-reset request never reveals whether an account exists
**Traces from:** FR079
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a reset is requested for both a registered and an unregistered
email/phone, when each is submitted, then both receive an identical
neutral response.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI01 neutral confirmation

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS154 — A completed reset allows immediate log-in with the new password
**Traces from:** FR079
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user completes the reset flow with a new password, when they
subsequently log in with it, then access succeeds immediately.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI01 reset → login handoff

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS155 — A correctly-entered OTP completes verification
**Traces from:** FR080
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a valid, unexpired OTP is entered, when submitted (manually or via
autofill), then verification completes and the user proceeds.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI01 OTP success

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS156 — An expired OTP is rejected with a clear resend option
**Traces from:** FR080
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given an OTP has passed its expiration window, when it's entered, then it
is rejected with a message and a resend option, not a confusing generic
failure.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI01 expired-code handling

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS157 — Requesting a new OTP invalidates all previously-issued codes
**Traces from:** FR080
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user requests a second OTP after the first, when they attempt to
verify using the first (now-superseded) code, then it is rejected —
directly addressing the researched "concurrent OTPs" edge case (only the
most recent code should ever be valid).

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (code-invalidation logic test)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS158 — Repeated failed OTP attempts trigger a temporary lockout
**Traces from:** FR080
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user enters an incorrect OTP repeatedly, when a defined failed-
attempt threshold is reached, then further attempts are temporarily
locked out — directly addressing the researched brute-force risk (a
six-digit OTP is trivially guessable without attempt-limiting on the
verification endpoint itself, not just the request endpoint).

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): UI01 lockout messaging

**Assumptions** — Exact lockout threshold/duration is implementation-
stage; this scenario tests that a lockout mechanism exists, not a
specific number.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS159 — Granting location permission auto-fills locality and advances onboarding
**Traces from:** FR081
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user taps "Use my location" and grants the native permission,
when this resolves, then their locality auto-fills and onboarding
advances to Interests.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI02 location success

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS160 — Denying location permission falls back to manual entry without blocking
**Traces from:** FR081
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user denies the native location prompt, when this occurs, then
the manual locality picker is revealed and onboarding proceeds once they
complete it manually — never blocked by the denial itself.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI02 manual-picker fallback

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS161 — Notification permission priming appears tied to first RSVP, not first launch
**Traces from:** FR082
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user has never RSVP'd, when they browse the app, then no
notification-permission priming appears; when they complete their first
Going action, then the priming appears at that specific moment.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI08 permission-priming banner

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS162 — Declining push notifications never blocks in-app notifications
**Traces from:** FR082
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user declines the native notification-permission prompt, when
notification-worthy events subsequently occur, then they still appear in
the in-app Notification Inbox (UI12).

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI12 in-app-only delivery

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS163 — All five nav destinations are reachable in one tap from anywhere in the core app
**Traces from:** FR083
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user is on any core-app screen, when they tap any of the five nav
bar tabs, then they land on that section in exactly one tap.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI03 tab navigation

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS164 — The nav bar never appears on pre-authentication screens
**Traces from:** FR083
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user is on Splash, Sign Up, Log In, or a Public Page (pre-login),
when these screens render, then the persistent nav bar is absent.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): UI01/UI11 chrome-free rendering

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS165 — Every screen shows a specific empty/error/offline state, never a blank one
**Traces from:** FR084
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given every screen in the inventory (UI01–UI18) is audited for its empty/
error handling, when checked, then each references a specific, non-
generic treatment rather than an unhandled blank state.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [ ] Relevant UX/UI state(s): UI18 pattern applied across the app

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS166 — Offline mode shows a non-blocking banner and auto-retries on reconnect
**Traces from:** FR084
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user loses connectivity mid-session, when this is detected, then
a non-blocking offline banner appears, cached content (if any) remains
usable, and normal function resumes automatically on reconnect.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI18 offline banner

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS167 — All profile/preference controls are reachable from Account & Settings
**Traces from:** FR085
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user opens Settings, when they look for profile editing, language,
appearance, and location precision, then all four are present and
functional from this one screen.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI17 settings list

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS168 — A save failure on any settings control is retryable, not silently lost
**Traces from:** FR085
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a settings save fails (e.g. network issue), when this occurs, then
the specific control shows an inline retry rather than silently reverting
without explanation.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI17 inline error

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS169 — All four notification classes appear in the inbox, Important visually distinguished
**Traces from:** FR086
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given notifications of all four classes exist for a user, when they open
the inbox, then all four appear, with Important-class items carrying the
distinct border/weight treatment from the other three.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI12 class-differentiated list

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS170 — A notification generated but never delivered to the inbox is a defect
**Traces from:** FR086
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given the system generates a notification event (of any class), when the
inbox is subsequently checked, then that event appears — an event
generated but absent from the inbox is flagged as a defect.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (delivery-completeness regression check)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS171 — Help/Support is reachable and its FAQ/contact path functions
**Traces from:** FR087
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user opens Help & Support from Settings, when they browse FAQs or
tap Contact Support, then both paths function (FAQ answers expand;
contact reuses the Report mechanism where relevant).

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI17 help screen

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS172 — No reachable help/support destination is ever entirely absent
**Traces from:** FR087
**Layer:** Unit
**Status:** Approved
**Confidence:** High

**Scenario**
Given the app's full settings/navigation structure, when audited, then a
help/support destination is reachable from at least one always-available
location (Settings).

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [ ] Relevant UX/UI state(s): N/A (navigation-completeness audit)

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS173 — Logout completes immediately without a confirmation step
**Traces from:** FR088
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user taps Log Out, when this action fires, then their session
ends immediately with no confirmation modal required.

**Covers**
- [x] Success path
- [ ] Failure/edge path
- [x] Relevant UX/UI state(s): UI17 immediate logout

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS174 — Account deletion requires explicit modal confirmation and states its effect
**Traces from:** FR088
**Layer:** E2E
**Status:** Approved
**Confidence:** High

**Scenario**
Given a user taps Delete Account, when the confirmation modal appears
with its explanation text, then deletion does not proceed until the
explicit confirmation step is completed — tagged E2E as one of this
module's genuine critical journeys (the single most irreversible action
in the entire app, warranting full-journey verification, not just a
component check).

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI17/UI15 modal confirmation

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13

---

## TS175 — Cancelling the delete-account modal leaves the account fully intact
**Traces from:** FR088
**Layer:** Integration
**Status:** Approved
**Confidence:** High

**Scenario**
Given the delete-account confirmation modal is open, when the user taps
Cancel or dismisses it, then the account, profile, and all data remain
completely unchanged.

**Covers**
- [ ] Success path
- [x] Failure/edge path
- [x] Relevant UX/UI state(s): UI17 modal cancel path

**Assumptions** — none.
**Decisions** — none.

**Review history**
- (none yet)

**Approval:** Principal QA — [x] Approved — krishna kategaru, 2026-09-13
