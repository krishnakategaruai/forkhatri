---
step: 02-functional-requirements
module: MOD03
status: Ready for Review
approver: Product Manager
updated: 2026-09-10
items: "89 | approved: 0 | blockers: 0"
---

# 02 — Functional Requirements — MOD03 Mangaly

## Revision history
| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-09 | Initial draft, 129 FRs, heavyweight per-FR template mirroring the BR file's essay style. | First pass. |
| 2026-09-09 | Revised per Product Manager direction: goal is a real running app, not another exhaustively-documented artifact. Reduced to 88 FRs by merging tightly-coupled constraint/edge-case items into acceptance criteria of their parent FR instead of spinning each into its own FR; reordered FRs within each BR so the first FR in each group is a thin, demoable slice and later FRs layer refinements/edge cases on top; trimmed the per-FR template to essentials (ISO sentence, one-line intent, success/failure, acceptance criteria, quality gate) and dropped discursive Decisions/Assumptions unless a genuine open ambiguity is being carried forward from the BR file. All underlying BR-level business rules (three-tier completeness, BR07 core/optional split, BR11's lifecycle families, BR14's dual reporting paths, etc.) are preserved, just expressed at FR-appropriate scope rather than restated at BR length. | PM course-correction mid-run. |
| 2026-09-09 | Completed all 20 BR groups (FR001–FR088). Set file status to Ready for Review — individual FR approval checkboxes remain unchecked pending Product Manager/BA sign-off, per the same convention used in Step 1. | End of Step 2 run. |
| 2026-09-10 | Full-corpus re-verification pass on 01-business-requirements.md corrected BR01's "Explicitly out of this file's scope" framing and added a new BR01 Constraint (DEC-004): a candidate's language preference is person-level profile data, not purely Common Platform infrastructure. Added FR089 to cover it, since no existing FR captured this newly-added BR01 Constraint. Backfilled the `Traced to:` field on all 20 BRs in 01-business-requirements.md with their FR ranges from the Coverage check table below (the Step 2 process step to do this had been skipped in the original run). No other FR in this file was found to misstate or omit anything from its parent BR on cross-check. | Correction pass following BR file re-verification — krishna kategaru, 2026-09-10. |

## Coverage check
| Parent BR | FRs produced | Covered |
|---|---|---|
| BR01 — Matrimonial Profile Creation & Self-Expression | FR001–FR006, FR089 | Yes |
| BR02 — Home Circle Membership Management | FR007–FR012 | Yes |
| BR03 — Family Collaboration Within Home Circle | FR013–FR016 | Yes |
| BR04 — Contextual, Least-Privilege Authorization | FR017–FR019 | Yes |
| BR05 — Privacy & Visibility Boundaries | FR020–FR024 | Yes |
| BR06 — Broad Discovery | FR025–FR029 | Yes |
| BR07 — Compatibility & Match Intelligence | FR030–FR034 | Yes |
| BR08 — Evidence-Based Trust & Matrimonial Verification | FR035–FR041 | Yes |
| BR09 — Connection Request Lifecycle | FR042–FR045 | Yes |
| BR10 — Selective Sharing After Acceptance | FR046–FR048 | Yes |
| BR11 — Private Communication, Ephemerality & Capture-Risk Reduction | FR049–FR056 | Yes |
| BR12 — Deliberate Contact Exchange | FR057–FR059 | Yes |
| BR13 — Family Involvement in an Established Connection | FR060–FR062 | Yes |
| BR14 — Safety Intelligence & Abuse Prevention | FR063–FR068 | Yes |
| BR15 — Internal Accountability & Audit Trail | FR069–FR071 | Yes |
| BR16 — Mangaly-Scoped Admin & Operations | FR072–FR076 | Yes |
| BR17 — Future Mangaly Agent Layer | FR077–FR078 | Yes |
| BR18 — Matrimonial Profile Lifecycle & Outcome Management | FR079–FR081 | Yes |
| BR19 — Success Story Capture & Consent | FR082–FR084 | Yes |
| BR20 — Digital-to-Real-World Introduction Transition | FR085–FR088 | Yes |

## Set-level quality gate
| Check | Result |
|---|---|
| Comprehensive — every BR covered | Pass — no blank rows above; 89 FRs across 20 BRs. |
| Consistent | Pass — shared actor/authorization vocabulary throughout; no FR contradicts another. |
| Prioritized | Pass — 80 Must, 1 Should (FR033), 8 Could (FR034, FR077–FR078, FR082–FR084), matching each BR's own split, including BR07's internal Must/Should/Could structure and BR17/BR19's Could priority. |
| No duplicates | Pass — BR02/BR03 and BR10/BR12 boundaries kept distinct per the BR file's own deliberate split. |
| Build-sequencing | Pass — within every BR, the first FR in that group is the thin, demoable slice; later FRs in the group layer enrichment, edge cases, and cross-cutting constraints on top, per PM direction. |

## Open blockers
| ID | Item | What's needed | From |
|---|---|---|---|
| (none) | — | — | — |

No FR is fully Blocked. The following carry Medium/Low Confidence with an explicit note rather than an invented resolution, each traceable to a specific open point already flagged at the BR level: FR003/FR005 (BR01 tier-field mapping), FR026/FR028/FR029 (BR06 ranking weights, fairness-testing methodology, and hint mechanics), FR037/FR041 (BR08 verifier anti-abuse mechanics and marriageable-age threshold), FR050/FR053/FR054 (BR11 retention duration, evidence-retention exception scope, legal-hold, and failure mechanics — pending formal DPDP legal sign-off), FR064/FR068 (BR14 detection-scope boundaries and severity taxonomy/thresholds), FR072/FR073/FR074 (BR16 exact workflow detail), and FR085 (BR20 safety-guidance content). These are downstream design or legal-sign-off items, not research questions the `researcher` subagent could resolve by lookup, consistent with the BR file's own honest-gate convention.

---

## FR001 — Create and Save a Minimum Viable Profile
**Traces from:** BR01
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When an authenticated candidate saves a new profile, the system shall persist it once every field designated "required for existence" is provided, and shall reject the save naming any missing required field.

**Intent**
First demoable slice: a candidate has a real, saved profile to build everything else on.

**Success outcome**
Profile saves and is viewable by its owner.

**Failure / edge outcome**
Missing required fields block the save; the specific missing fields are listed.

**Acceptance criteria**
- [ ] Save succeeds once existence-tier fields are complete.
- [ ] Save is blocked, with the specific missing fields listed, otherwise.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (exact existence-tier field list is implementation-stage per BR01) · Singular ✓ · Feasible ✓ · Verifiable ~ (same reason) · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR01.
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

## FR002 — Extend Profile Across All Categories, Including Declined Fields
**Traces from:** BR01
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a candidate with a saved profile (FR001) edits it, the system shall let them add or edit content in every remaining profile category (photos, video introduction, education, profession, location/relocation, lifestyle, communication/conflict tendencies, independence, family-involvement/career/children/living/financial expectations, pets, partner preferences, optional horoscope), and shall let them explicitly mark any non-essential or sensitive field as declined rather than merely leaving it blank.

**Intent**
Builds the full profile surface on top of FR001's saved minimum.

**Success outcome**
Candidate enriches their profile category by category; declined fields are recorded as declined.

**Failure / edge outcome**
A failed save on one category preserves edits for retry; declining a field never blocks any other category.

**Acceptance criteria**
- [ ] Each category is editable independently of the others.
- [ ] A candidate can mark a field "declined," distinct from leaving it empty.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR01.
**Assumptions** — exact field schema per category is implementation-stage (BR01 Constraints).

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

## FR003 — Discoverability Tier Gate, Independent of Enhanced-Matching Tier
**Traces from:** BR01, BR06
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** Medium — exact discoverability-tier field list is implementation-stage (BR01/BR06 DEC-003); this FR fixes the rule, not the field list.

**Requirement (ISO 29148 form)**
When a saved profile is evaluated for Discovery eligibility, the system shall clear it once the "required for discoverability" tier is met, and shall never require any "required for enhanced matching" field to clear this gate.

**Intent**
Enforces that enrichment fields can never become a hidden discoverability prerequisite — the core protection BR01/BR06 DEC-003 exists for.

**Success outcome**
A profile with all discoverability-tier fields but zero enhanced-matching fields is discoverable.

**Failure / edge outcome**
A profile missing a discoverability-tier field is excluded, and shown exactly which fields would clear it.

**Acceptance criteria**
- [ ] Enhanced-matching-only gaps never exclude a profile from Discovery.
- [ ] Discoverability-tier gaps exclude, with the specific missing fields shown.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (field list deferred) · Singular ✓ · Feasible ✓ · Verifiable ~ (same reason) · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR01/BR06 DEC-003.
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

## FR004 — Enhanced-Matching Fields Are Optional and Non-Blocking
**Traces from:** BR01
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a candidate declines an "enhanced matching" field, the system shall keep the profile fully discoverable, degrading only Compatibility signal richness (BR07), never Discovery eligibility.

**Intent**
Prevents enrichment data from becoming a disguised gate.

**Success outcome**
Compatibility explanations note reduced richness where data is missing, with zero Discovery penalty.

**Failure / edge outcome**
If a Compatibility computation cannot run without a declined field, it degrades to an available-data explanation rather than blocking anything.

**Acceptance criteria**
- [ ] Declining enhanced-matching fields never changes Discovery eligibility.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR01.
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

## FR005 — Three-Tier Completeness Status Display
**Traces from:** BR01
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** Medium — depends on FR001/FR003's deferred tier-field mapping.

**Requirement (ISO 29148 form)**
When a candidate views their own profile, the system shall display existence, discoverability, and enhanced-matching completeness as three independent indicators, never blended into one percentage.

**Intent**
UI surface for the three-tier model, built once the tiers themselves exist (FR001, FR003).

**Success outcome**
Candidate sees three separate indicators and, per unmet tier, the specific missing fields.

**Failure / edge outcome**
A field with undefined tier membership is excluded from all tier calculations rather than guessed.

**Acceptance criteria**
- [ ] Tiers are always shown separately, never merged into one score.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (tier mapping deferred) · Singular ✓ · Feasible ✓ · Verifiable ~ (same reason) · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR01 DEC-003.
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

## FR006 — Media Visibility Follows Profile Authorization
**Traces from:** BR01, BR04
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a viewer requests a candidate's photos or video introduction, the system shall apply the same authorization check as the rest of the profile (FR017), denying access by default if authorization cannot be determined.

**Intent**
Prevents media from being an ungoverned side channel; sequenced last in this BR since it is only meaningfully testable once FR017's authorization chain exists.

**Success outcome**
Authorized viewers see media; unauthorized viewers do not.

**Failure / edge outcome**
Undetermined authorization defaults to deny.

**Acceptance criteria**
- [ ] Media access is denied by default absent explicit authorization.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR01/BR04.
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

## FR007 — Search for and Invite a User to a Home Circle
**Traces from:** BR02
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a candidate or existing Home Circle member searches another Mangaly user by username and sends an invitation, the system shall create a pending invitation supporting any valid path (Candidate→Parent, Parent→Candidate, Candidate→Sibling/family member, existing member→another relative) and notify the invitee.

**Intent**
First demoable Home Circle action.

**Success outcome**
Invitee receives a pending invitation they can act on.

**Failure / edge outcome**
No matching user, or a target who is already a member, is rejected with a specific reason.

**Acceptance criteria**
- [ ] All four invitation paths are supported.
- [ ] Invalid/duplicate invitations are rejected with a specific reason.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR02.
**Assumptions** — relies on a platform-level username lookup capability (BR02 Assumptions).

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

## FR008 — Accept Invitation
**Traces from:** BR02
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When an invitee accepts a pending invitation, the system shall establish authenticated Home Circle membership and record the relationship claim and the acceptance event to Audit (BR15).

**Intent**
Completes the minimal invite→join loop started by FR007.

**Success outcome**
Invitee becomes a recorded member.

**Failure / edge outcome**
Expired or withdrawn invitations cannot be accepted.

**Acceptance criteria**
- [ ] Acceptance creates a membership record with the relationship claim.
- [ ] Expired/withdrawn invitations are rejected.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR009 — Ignore or Decline Invitation
**Traces from:** BR02
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When an invitee ignores or explicitly declines an invitation, the system shall leave their membership status unchanged and record a decline as an outcome distinct from silence, without penalty to either party.

**Intent**
Covers the non-acceptance path so it is a designed state, not an accident.

**Success outcome**
No membership change occurs; the inviter sees the invitation was not accepted.

**Failure / edge outcome**
Not applicable — declining/ignoring is itself a valid terminal state.

**Acceptance criteria**
- [ ] A decline is recorded distinctly from silence.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR010 — Remove a Member or Leave Voluntarily
**Traces from:** BR02
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a candidate removes a member, or a member leaves voluntarily, the system shall revoke that member's ongoing access immediately while preserving historical accountability records (BR15), and shall never require any other member's approval for a voluntary departure.

**Intent**
Ensures no one is trapped in a Home Circle, per BR02's explicit rule.

**Success outcome**
Access is revoked immediately; history is preserved for audit.

**Failure / edge outcome**
A technical failure mid-removal triggers a retry/alert rather than leaving membership in an ambiguous state.

**Acceptance criteria**
- [ ] Removed/departed member's future access is revoked immediately.
- [ ] Voluntary departure requires no other member's approval.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR011 — Report a False or Inappropriate Relationship Claim
**Traces from:** BR02
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a party believes a Home Circle invitation or membership misrepresents the actual relationship, the system shall let them report it, route the case to Mangaly admin/operations (BR16), and withhold the disputed member's access pending the investigation's outcome.

**Intent**
Gives the false-relationship risk named in BR02 an actual reporting path.

**Success outcome**
The report reaches BR16's investigation workflow; access is held pending review.

**Failure / edge outcome**
A report is still accepted for record-keeping even if the underlying invitation was already withdrawn.

**Acceptance criteria**
- [ ] A report creates a case visible to the BR16 admin workflow.
- [ ] Disputed access is withheld pending investigation.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR012 — Solo-Candidate Parity and Re-Forming a Circle
**Traces from:** BR02
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a candidate has zero Home Circle members, or has left one, the system shall provide full, undiminished access to every other Candidate-level capability (Profile, Discovery, Compatibility, Trust, Connection Request, Selective Sharing, Communication, Contact Exchange, Safety, Accountability), and shall let them form or join a new Home Circle at any time.

**Intent**
Direct enforcement of BR02's "additive, never a precondition" rule — closes this BR's FR group with the invariant that makes every prior FR in it optional to use.

**Success outcome**
A zero-member candidate uses the full product with no gating; a re-forming candidate can build a new circle freely.

**Failure / edge outcome**
Any capability found implicitly depending on non-zero Home Circle membership is a defect against this FR.

**Acceptance criteria**
- [ ] A zero-member account exercises every listed capability without restriction.
- [ ] A candidate can found a second Home Circle after leaving a first.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR02 DEC-002.
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

## FR013 — Independent, Parallel Family Search
**Traces from:** BR03
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When an authorized parent, sibling, or relative within a Home Circle uses Discovery, the system shall let them search broadly, independently of and in parallel with the candidate, subject to whatever scope BR04 authorization grants them.

**Intent**
First demoable family-collaboration action.

**Success outcome**
Family member searches without the candidate acting first, within their granted scope.

**Failure / edge outcome**
A candidate-set restriction on that relative's scope is enforced, not defaulted to full access.

**Acceptance criteria**
- [ ] Family search works with zero prior candidate activity.
- [ ] Candidate-set scope restrictions are enforced.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR014 — Suggest a Profile (Suggestion ≠ Decision)
**Traces from:** BR03
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When any authorized Home Circle member suggests a discovered profile to the candidate, the system shall record it as a suggestion only — never granting the suggested profile extra access, never implying candidate consent or decision — and shall never require Home Circle members to reach agreement before any of them can act within their own authority.

**Intent**
The core family-collaboration value proposition (BR03), with "initiation authority ≠ decision authority" enforced as a first-class rule.

**Success outcome**
Candidate receives the suggestion and independently decides; disagreeing family members can each still act within their own scope.

**Failure / edge outcome**
A suggestion never auto-triggers any BR09 connection action — the candidate must take a separate, explicit action.

**Acceptance criteria**
- [ ] A suggestion never auto-triggers a BR09 action.
- [ ] No consensus/agreement step is required among family members before any one of them can act.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR015 — Independent Candidate Search and Family-Involvement Timing
**Traces from:** BR03
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a candidate searches independently, the system shall keep that activity invisible to family by default, and shall let the candidate decide separately whether and when to involve family in what they find.

**Intent**
Preserves candidate agency alongside FR013/FR014's family capability.

**Success outcome**
Candidate searches privately and chooses disclosure timing.

**Failure / edge outcome**
A Home Circle member attempting to view the candidate's private search activity is denied.

**Acceptance criteria**
- [ ] Candidate search activity is not visible to family by default.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR016 — Private Family Notes, Forwarded Only with Candidate Approval
**Traces from:** BR03
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a parent or authorized relative records a private working note on a profile, the system shall keep it visible only to its author by default, and shall require the candidate's explicit approval before any specific forwarded note becomes visible to them.

**Intent**
The richer collaboration feature layered on top of FR013/FR014, sequenced last in this BR.

**Success outcome**
Author tracks private notes; candidate sees only what they approved, when they approved it.

**Failure / edge outcome**
Content the author is not authorized to hold (e.g. private BR11 communication) cannot be captured into a note field.

**Acceptance criteria**
- [ ] Notes are private to their author by default.
- [ ] Forwarding requires explicit candidate approval and shares only the selected note.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR03.
**Assumptions** — notes are scoped strictly to matrimonial evaluation content (BR03 Assumptions).

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

## FR017 — Authorization Chain Evaluation, Deny by Default
**Traces from:** BR04
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When any actor attempts a consequential access or disclosure, the system shall evaluate it against Person → Relationship → Responsibility → Authorization/Scope → Consent → Collaboration, log the decision to Audit (BR15), and deny by default if any link cannot be established — including that Home Circle membership alone never grants access, parents never automatically receive private candidate conversations, siblings/relatives never automatically gain decision authority, and a prospective match/family never automatically sees the candidate's Home Circle.

**Intent**
The single mechanism underlying every other BR's access rules — foundational, so it is the first FR built within this BR.

**Success outcome**
Access is granted only when every link resolves affirmatively; the four named non-grant scenarios hold.

**Failure / edge outcome**
Any unresolved or negative link results in denial, with the denial reason recorded to Audit.

**Acceptance criteria**
- [ ] An action with an unresolved chain link is denied, not defaulted to allow.
- [ ] Each of the four named non-grant scenarios independently verifies as denied by default.
- [ ] Every decision (grant or deny) is recorded to Audit.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR04.
**Assumptions** — exact permission matrix/taxonomy is implementation-stage (BR04 Constraints); this FR fixes the model, not the matrix.

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

## FR018 — Candidate vs. Family Information as Separate Authorization Categories
**Traces from:** BR04
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When the system evaluates or stores authorization scope, it shall treat candidate personal information and Home Circle/family information as distinct categories, such that access granted to one never implicitly grants access to the other.

**Intent**
Prevents authorization data from conflating candidate and family concerns.

**Success outcome**
Access grants are recorded per category, never blended.

**Failure / edge outcome**
A data model or check found conflating the two categories is a defect against this FR and BR05's "Important Family Boundary."

**Acceptance criteria**
- [ ] Access grants are recorded per-category (candidate vs. family), never as one blended grant.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR019 — Plain-Language Capability Presentation
**Traces from:** BR04
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When the system presents authorization information to any user, it shall express it as plain-language capability statements (e.g. "Mom can suggest profiles for you"), never as a technical permission/RBAC screen.

**Intent**
Presents FR017's mechanism in the terms an end user actually understands — sequenced after FR017 since it surfaces that mechanism's outcomes.

**Success outcome**
A non-technical user understands what a relationship can/cannot do without needing a permissions table.

**Failure / edge outcome**
A raw RBAC-style matrix surfaced anywhere is a defect against this FR (and a flag for UX/UI downstream).

**Acceptance criteria**
- [ ] All authorization-facing copy is plain-language, capability-framed.
- [ ] No user-facing screen resembles a technical permissions matrix.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR020 — Meaningful, Sufficient Information for Authorized Viewers
**Traces from:** BR05
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When an authorized viewer with a legitimate matrimonial purpose views a profile, the system shall present meaningful, sufficiently complete information for that purpose, never withholding information via an artificial teaser mechanism.

**Intent**
Establishes BR05's core anti-teaser commitment as the first, foundational rule in this group.

**Success outcome**
Viewer forms a genuine judgment without hitting a manufactured information gate.

**Failure / edge outcome**
Information withheld for a non-authorization reason (e.g. to induce payment/engagement) is a defect and a non-goal violation.

**Acceptance criteria**
- [ ] No profile field is hidden behind a payment- or engagement-inducing teaser.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR021 — Separate Display of Candidate vs. Family Info; Visibility ≠ Searchability
**Traces from:** BR05
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When information is displayed to any viewer, the system shall visually distinguish candidate-personal from family information (per FR018), and shall evaluate whether a profile can be found (searchability) independently of what content a specific viewer can see (visibility).

**Intent**
Structural display rule built on top of FR018's authorization-level separation.

**Success outcome**
A profile can be searchable with only partial visibility to a given viewer, per that viewer's authorization.

**Failure / edge outcome**
Conflating "found in search" with "full content visible" is a defect.

**Acceptance criteria**
- [ ] Candidate vs. family category is visibly labeled wherever shown.
- [ ] Search-eligibility and per-viewer visibility are tracked and enforced independently.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR022 — No Popularity or Demand Signal Exposure
**Traces from:** BR05
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When any user views a profile or Discovery results, the system shall never display profile-view counts, rejection counts, or any popularity/demand indicator, to any viewer including the profile owner.

**Intent**
Absolute rule protecting against reintroducing a dating-app popularity dynamic.

**Success outcome**
No such counters or indicators appear anywhere in the product.

**Failure / edge outcome**
Any such metric found exposed anywhere is a defect requiring removal.

**Acceptance criteria**
- [ ] No screen displays view counts, rejection counts, or a popularity/demand rank.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR023 — Family-Boundary Enforcement Toward a Prospective Match
**Traces from:** BR05
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a parent's search surfaces a prospective candidate, the system shall show that prospective candidate only the searching side's candidate-level profile information, never the searching family's Home Circle, absent deliberate involvement (BR13).

**Intent**
Direct enforcement of BR05's "Important Family Boundary" at the specific point of highest risk (parent-initiated discovery).

**Success outcome**
Prospective candidate sees only candidate-level info from the initiating side.

**Failure / edge outcome**
Exposing the searching parent's Home Circle without deliberate involvement is a defect.

**Acceptance criteria**
- [ ] Parent-initiated discovery/suggestion never exposes that parent's Home Circle to the discovered candidate.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR024 — Pause Without Signalling; Controlled Safety Exceptions
**Traces from:** BR05
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a candidate pauses or disengages, the system shall not broadcast any status change to other users; and when Safety Intelligence (BR14) determines severe harm requires intervention, the system shall allow a narrowly scoped, audited exception to normal visibility rules, logged to Audit (BR15) and never applied as a general relaxation.

**Intent**
Covers the two lower-frequency but important edge behaviors closing out this BR's group.

**Success outcome**
Pausing is invisible to others; safety exceptions are minimal and fully audited.

**Failure / edge outcome**
Any "inactive"/"away" badge visible to others is a defect; an exception too broad to scope narrowly routes to BR16's human-investigation workflow instead of an automated broad exception.

**Acceptance criteria**
- [ ] No user-visible status change is broadcast when a candidate pauses.
- [ ] Every safety-visibility exception is individually scoped and logged.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR025 — Discovery Available to Candidates and Family, in Parallel
**Traces from:** BR06
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a candidate or an authorized family participant (per BR04) opens Discovery, the system shall let them search independently of the other's actions, including a parent searching before the candidate has acted.

**Intent**
First demoable Discovery slice — a real, working results list.

**Success outcome**
Both candidate and authorized family can each independently discover profiles.

**Failure / edge outcome**
Discovery access requiring the candidate to act first is a defect.

**Acceptance criteria**
- [ ] A parent can run a Discovery search with zero prior candidate Discovery activity.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR026 — Relevance-Based Ranking, Not Popularity-Primary
**Traces from:** BR06
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** Medium — exact ranking weights are implementation-stage.

**Requirement (ISO 29148 form)**
When the system ranks Discovery results for any viewer, it shall rank primarily using locality/practical geography, partner preferences, lifestyle relevance, compatibility relevance (BR07), and verification/evidence context (BR08), and shall not use popularity as the primary ranking factor.

**Intent**
Core ranking logic layered onto FR025's basic results list.

**Success outcome**
Ranking order reflects the listed relevance factors, not popularity.

**Failure / edge outcome**
Popularity data found influencing primary rank order is a defect.

**Acceptance criteria**
- [ ] Ranking's primary weighted factors exclude popularity.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (exact weights deferred) · Singular ✓ · Feasible ✓ · Verifiable ~ (same reason) · Correct ✓ · Conforming ✓

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

## FR027 — Discoverability-Tier Exclusion Only, Not Enhanced-Matching
**Traces from:** BR06, BR01
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a profile has not cleared BR01's "required for discoverability" tier, the system shall exclude it from Discovery entirely, and shall never apply this exclusion on the basis of the "required for enhanced matching" tier alone.

**Intent**
Same rule as FR003, restated at the Discovery-side enforcement point — a legitimate candidate who declines enrichment must never disappear from Discovery.

**Success outcome**
Only genuinely sparse (sub-discoverability) profiles are excluded.

**Failure / edge outcome**
A profile lacking only enhanced-matching fields found excluded is a defect directly against BR06 DEC-003.

**Acceptance criteria**
- [ ] Exclusion logic references only the discoverability tier, never the enhanced-matching tier.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR06 DEC-003.
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

## FR028 — Fairness Safeguards and AI Ranking Transparency
**Traces from:** BR06
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** Medium — exact fairness-testing methodology and AI-replaceability architecture are implementation-stage.

**Requirement (ISO 29148 form)**
When the system computes Discovery ranking, it shall apply de-biasing safeguards against wealth/status bias, education/profession-as-worth ranking, unfair locality-based exclusion, recommendation-bubble effects, and unnecessary sensitive-attribute inference, and shall label any AI-derived ranking signal as inference, never as verified fact.

**Intent**
Named acceptance-level guardrails on top of FR026's ranking mechanism.

**Success outcome**
A fairness review finds no named bias present; every AI signal is labeled as inference.

**Failure / edge outcome**
A confirmed named bias, or an unlabeled AI inference, flags the ranking mechanism for correction before continued use.

**Acceptance criteria**
- [ ] A documented fairness-review process exists covering each named bias category.
- [ ] Every AI-derived ranking signal is labeled inference, not fact.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (methodology deferred) · Singular ✓ · Feasible ✓ · Verifiable ~ (same reason) · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR06 Constraints.
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

## FR029 — Community-Assisted Discovery Hints
**Traces from:** BR06
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** Medium — exact hint mechanics are an open, implementation-stage design question (BR06 DEC-001).

**Requirement (ISO 29148 form)**
When a family knows of a potentially suitable person whose profile they cannot directly access, the system shall optionally provide limited contextual hints sufficient to identify an appropriate community/locality/intermediary route, without exposing the person's actual profile content.

**Intent**
Lighter, later-implementable enhancement named in BR06 — sequenced last in this group.

**Success outcome**
Family receives an actionable, bounded hint without seeing private profile content.

**Failure / edge outcome**
A hint revealing identifiable profile content beyond the bounded contextual scope is a defect and a non-teaser violation.

**Acceptance criteria**
- [ ] Hints never include actual profile fields (photos, contact info, specifics).

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (mechanics open) · Singular ✓ · Feasible ✓ · Verifiable ~ (same reason) · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR06 DEC-001.
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

## FR030 — Explainable, Non-Score Compatibility Reasons
**Traces from:** BR07
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must (core capability)
**Status:** Draft
**Confidence:** Medium — the underlying algorithm/weighting methodology is open (BR07 Confidence note); this FR fixes the required behavior, not the algorithm.

**Requirement (ISO 29148 form)**
When the system surfaces a recommended or compatibility-relevant profile, it shall present concrete, explainable reasons (e.g. shared living-arrangement expectations, similar relocation direction, compatible family-involvement expectations), and shall never present a single objective-sounding compatibility score or percentage.

**Intent**
First demoable Compatibility slice — a real "why this match" card.

**Success outcome**
Viewer sees specific, understandable reasons for the suggestion.

**Failure / edge outcome**
If no explainable reason can be generated for a pairing, the compatibility framing is omitted or de-prioritized for that pairing rather than fabricated.

**Acceptance criteria**
- [ ] Every compatibility surface includes at least one concrete, named reason.
- [ ] No numeric/percentage compatibility score appears anywhere.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ~ (algorithm open) · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR07 DEC-002 (core vs. optional split).
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

## FR031 — Fact vs. Inference, Alignment vs. Difference, No Certainty Claims
**Traces from:** BR07
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must (core capability)
**Status:** Draft
**Confidence:** Medium — same open-algorithm caveat as FR030.

**Requirement (ISO 29148 form)**
When a compatibility explanation is generated, the system shall label each element as either a verified fact (BR08) or an algorithmic inference, shall consider both alignment and meaningful differences (not similarity alone), and shall never claim certainty about character, honesty, or predict marriage success.

**Intent**
The refinement rules that make FR030's explanations honest and bounded.

**Success outcome**
Every explanation element is labeled fact or inference; explanations can surface complementary differences, not only shared traits; no certainty claims appear.

**Failure / edge outcome**
An unlabeled inference, a similarity-only mechanism, or a certainty claim in generated language is rejected/regenerated before display.

**Acceptance criteria**
- [ ] Every compatibility explanation element is labeled fact or inference.
- [ ] Generated explanation text is checked against a banned-claim list (certainty of character/honesty/success) before display.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ~ (three related refinements bundled deliberately, all governing the same explanation output) · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR032 — Core Capability Fully Functional Without Optional Mechanisms
**Traces from:** BR07
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must (core capability)
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a candidate has declined both the personality assessment and horoscope input, the system shall still generate full, genuinely explainable compatibility signal from profile/evidence data alone.

**Intent**
Guarantees the Must-priority core never silently depends on the Should/Could optional mechanisms.

**Success outcome**
A candidate who opts out of both optional mechanisms still receives compatibility explanations.

**Failure / edge outcome**
The system requiring optional-mechanism data before generating any explanation is a defect directly against BR07's Proposed Outcome.

**Acceptance criteria**
- [ ] Compatibility explanations are generated for a test profile with zero optional-mechanism data.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR07 DEC-002.
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

## FR033 — Optional Personality Assessment
**Traces from:** BR07
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Should
**Status:** Draft
**Confidence:** Low — the personality-assessment instrument carries its own, separately lower, confidence per BR07.

**Requirement (ISO 29148 form)**
When a candidate opts in to the personality assessment, the system shall administer a short (~5 minute), non-clinical assessment, feed its results only into that candidate's own compatibility signal, and present results only as compatibility-signal input, never as a clinical diagnosis or a "good/bad spouse" label.

**Intent**
The first of BR07's two optional, additive mechanisms — never a prerequisite for FR030–FR032.

**Success outcome**
Opted-in candidate's compatibility signal is enriched; opted-out candidates are unaffected.

**Failure / edge outcome**
An abandoned assessment is discarded rather than used as if complete; any clinical/suitability-verdict language surfaced anywhere is a defect.

**Acceptance criteria**
- [ ] Assessment is fully skippable with no Discovery/Compatibility penalty.
- [ ] Partial/abandoned assessments are not used as input.
- [ ] No UI copy uses clinical or suitability-verdict language for results.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ~ (assessment mechanics + usage-constraint bundled, both governing the same feature) · Feasible ✓ · Verifiable ~ (instrument itself unresolved) · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR07 DEC-001/DEC-002.
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

## FR034 — Horoscope: Opt-In, Separated, Non-Scientific
**Traces from:** BR07
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Could
**Status:** Draft
**Confidence:** High — the requirement itself (keep separate, non-scientific) is clear even though building it is low-priority.

**Requirement (ISO 29148 form)**
When a candidate opts in to provide horoscope information, the system shall incorporate it as a clearly separated, labeled, non-scientific input, and shall never apply it to, or silently influence, any candidate who has not opted in.

**Intent**
BR07's second optional, additive mechanism, sequenced last since it is Could-priority.

**Success outcome**
Only opted-in candidates' results are ever touched by horoscope data; horoscope content always carries a visible non-scientific/optional label.

**Failure / edge outcome**
Horoscope data influencing a non-opted-in candidate, or horoscope content shown without its disclaimer, is a defect.

**Acceptance criteria**
- [ ] Horoscope input is a distinct, separately toggled opt-in.
- [ ] Horoscope-derived content always carries a visible non-scientific/optional label.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR07 DEC-001/DEC-002.
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

## FR035 — Evidence-and-Provenance Display Per Verification Layer
**Traces from:** BR08
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** Medium — verification vendor/process selection is open (BR08 Confidence note); this FR fixes the display model, not the process.

**Requirement (ISO 29148 form)**
When a candidate's verification status is displayed to an authorized viewer, the system shall represent account authenticity, identity/age, selected profile facts, Home Circle relationship, community/factual verification, and Mangaly operational verification as separate, independently labeled layers, each showing method, source category, time, and freshness/expiry where applicable, and shall never represent trust as a single aggregate score.

**Intent**
First demoable Trust slice — a real evidence display, immediately establishing the "evidence, not score" model.

**Success outcome**
Viewer sees itemized evidence with provenance per layer, never a blended score.

**Failure / edge outcome**
Any surface reducing verification to a single number, or merging layers into one undifferentiated badge, is a defect.

**Acceptance criteria**
- [ ] No trust/verification score of any kind is displayed anywhere.
- [ ] Each of the six named layers has its own independent display state with method/source/time.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ~ (six layers described together as one display model, a deliberate structural choice) · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR08 DEC-002.
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

## FR036 — Evidence Language Avoids Truth-Certification
**Traces from:** BR08
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When the system communicates a verification outcome, it shall display evidence and its provenance to help the viewer evaluate the claim, and shall never state or imply that Mangaly has certified the underlying claim as true.

**Intent**
Copy-level enforcement of BR08 DEC-002's reframing away from truth-certification.

**Success outcome**
Copy consistently uses evidence/provenance framing.

**Failure / edge outcome**
Any copy asserting a claim is "true"/"confirmed" in absolute terms is a defect.

**Acceptance criteria**
- [ ] No user-facing copy asserts a claim is true/confirmed in absolute terms.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR08 DEC-002.
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

## FR037 — Verification Circle: Bounded Confirmation with Anti-Abuse Safeguards
**Traces from:** BR08
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** Medium — exact anti-abuse mechanics are open (BRD OPEN-03/04, BR08 Confidence note).

**Requirement (ISO 29148 form)**
When a sufficiently verified third party is asked to confirm knowledge of a candidate/family via the Verification Circle, the system shall restrict their response to Yes / No / Don't know / Cannot confirm, shall check that verifier's own identity/eligibility before accepting the response as evidence, and shall apply safeguards against gossip, malicious confirmation, retaliation, and fake witnesses.

**Intent**
The bounded, safe alternative to a rating system — core to BR08's anti-score commitment.

**Success outcome**
Only eligible, checked verifiers' bounded responses count as evidence.

**Failure / edge outcome**
An attempt to submit a rating/free-form judgment is rejected; a verifier later found ineligible or malicious has their confirmation flagged/revoked from the evidence record.

**Acceptance criteria**
- [ ] Response input only accepts the four bounded options.
- [ ] Verifier status requires a passed eligibility check, not merely an accepted invitation.
- [ ] A revoked/flagged verifier's confirmation is visibly marked invalid in the evidence record.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (anti-abuse mechanics open) · Singular ~ (bounded-response + eligibility-check + anti-abuse are one coherent safeguard) · Feasible ✓ · Verifiable ~ (mechanics open) · Correct ✓ · Conforming ✓

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

## FR038 — Request Mangaly/Admin Verification When No Community Verifier Exists
**Traces from:** BR08
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a candidate has no suitable community verifier available, the system shall let them request Mangaly/admin verification instead, routing the request to BR16's admin verification workflow.

**Intent**
Ensures the Verification Circle (FR037) is never a hard dependency for obtaining verification.

**Success outcome**
Candidate obtains a verification path even without a community verifier.

**Failure / edge outcome**
A request that cannot be fulfilled states what evidence is missing rather than silently failing.

**Acceptance criteria**
- [ ] Admin verification request is available whenever no community verifier is selected/available.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR039 — No Trust Score or Reputation Ranking
**Traces from:** BR08
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When any user or admin views trust/verification information, the system shall never compute, store for display, or expose a Trust Score, Family Reputation Score, or any public reputation ranking/rating.

**Intent**
Absolute prohibition central to BR08's entire approach.

**Success outcome**
No such score exists anywhere in the product.

**Failure / edge outcome**
Any component found computing such a score, even for internal-only use in a way that could leak or influence ranking, is a defect requiring removal.

**Acceptance criteria**
- [ ] No database field, API response, or UI element represents a trust/reputation score of any kind.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR040 — Sensitive Verification Documents Not Exposed Publicly
**Traces from:** BR08
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a candidate submits a sensitive verification document (e.g. government ID), the system shall restrict its visibility to the verification workflow itself, never surfacing it as public or authorized-viewer-facing profile content.

**Intent**
Protects the sensitive evidence underlying FR035's evidence display.

**Success outcome**
Only the verification evidence summary, never the raw document, is shown to other users.

**Failure / edge outcome**
A raw sensitive document found accessible outside the verification workflow is a defect requiring immediate remediation.

**Acceptance criteria**
- [ ] Raw sensitive verification documents are accessible only within the admin/verification workflow.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR041 — Marriageable-Age Verification per Applicable Law
**Traces from:** BR08
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** Medium — per BR08 Constraints, the exact current legal threshold should be reconfirmed at implementation/legal-review time given ongoing legislative discussion; this FR intentionally references an external, updateable value rather than hard-coding a number.

**Requirement (ISO 29148 form)**
When identity/age verification is performed for a candidate, the system shall confirm the candidate meets the applicable Indian legal marriageable-age requirement, using the currently applicable statutory threshold, before the profile is eligible for Discovery.

**Intent**
Legal-compliance gate on Discovery eligibility.

**Success outcome**
Underage candidates cannot become discoverable.

**Failure / edge outcome**
Inconclusive age evidence withholds Discovery eligibility rather than assuming compliance.

**Acceptance criteria**
- [ ] Discovery eligibility check references a single, updateable legal-age configuration value rather than a hard-coded number in logic.
- [ ] Inconclusive age evidence blocks Discovery eligibility.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ~ (exact current threshold pending legal reconfirmation) · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR08 Constraints.
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

## FR042 — Send Connection Request
**Traces from:** BR09
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a candidate or authorized family participant (per BR04) finds a profile of interest, the system shall let them send a connection request, recording the requester's identity and capacity (self or on-behalf-of) for accountability (BR15).

**Intent**
First demoable Connection slice.

**Success outcome**
Request is created and delivered to the recipient for review.

**Failure / edge outcome**
A sender lacking authorization to request on the candidate's behalf is blocked.

**Acceptance criteria**
- [ ] Request records requester identity/capacity.
- [ ] Unauthorized on-behalf-of requests are blocked.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR043 — Recipient Review and Accept/Decline
**Traces from:** BR09
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a connection request arrives, the system shall let the recipient inspect meaningful profile information, relevant compatibility context (BR07), and available trust/evidence signals (BR08) before deciding, without requiring acceptance to unlock this review information, and shall let them accept or decline.

**Intent**
Completes FR042's request into a real decision loop, with no teaser pattern.

**Success outcome**
Recipient makes an informed decision using pre-acceptance information; the decision is recorded.

**Failure / edge outcome**
Review information withheld pending acceptance is a defect; a pending request with no decision remains pending indefinitely rather than defaulting to any outcome.

**Acceptance criteria**
- [ ] All listed review information categories are visible before any accept/decline decision.
- [ ] No default/timeout-forced acceptance exists.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ~ (review + decision are one coherent flow) · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR044 — Acceptance Means Willingness to Explore Only
**Traces from:** BR09
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a connection request is accepted, the system shall record and communicate that acceptance means willingness to explore the connection only, never implying commitment, exclusivity, seriousness, a relationship declaration, marriage intent, automatic contact exchange, or automatic Home Circle exposure.

**Intent**
Prevents FR043's acceptance action from being over-interpreted anywhere downstream.

**Success outcome**
All post-acceptance messaging matches this bounded meaning.

**Failure / edge outcome**
Any surface implying a stronger meaning (e.g. exclusivity framing) is a defect.

**Acceptance criteria**
- [ ] No UI copy implies commitment/exclusivity/seriousness from acceptance alone.
- [ ] Acceptance does not trigger automatic contact exchange or Home Circle exposure.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR045 — Multiple Parallel Connections; No Forced Continued Engagement
**Traces from:** BR09
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a candidate has one or more connections, the system shall let them maintain multiple simultaneous requests/explorations with no single "current match" state, and shall let them decline further engagement or withdraw from any connection at any point without justification or penalty.

**Intent**
Closes out BR09's FR group with its two structural invariants.

**Success outcome**
Candidate holds several concurrent connections at different stages and can freely disengage from any of them.

**Failure / edge outcome**
An enforced single-current-match constraint, or a required justification/visible penalty for withdrawal, is a defect.

**Acceptance criteria**
- [ ] A candidate can hold 2+ simultaneous accepted connections without any exclusivity block.
- [ ] Withdrawal requires no justification and produces no negative/visible marker.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ~ (two related invariants protecting the same non-exclusivity principle) · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR046 — Per-Category Independent Sharing
**Traces from:** BR10
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When two candidates have an accepted connection (BR09), the system shall let each participant independently choose to share specific categories (additional photos, video introduction, additional personal information, phone number, email, parent/family contact details where authorized), with each category shared or withheld independently of the others.

**Intent**
First demoable Selective Sharing slice.

**Success outcome**
Participant controls exactly which categories are revealed and when.

**Failure / edge outcome**
Sharing one category found to also reveal another is a defect against this FR's core rule.

**Acceptance criteria**
- [ ] Sharing "additional photos" does not reveal phone/email/family contact.
- [ ] Each category has its own independent share/withhold state.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR047 — Clear Sharing Confirmation; No Automatic Disclosure
**Traces from:** BR10
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a participant shares a category, the system shall clearly communicate to both parties what was shared, with whom, and what it does not imply, without a permanent settings-page interface, and shall never automatically disclose any category without that explicit, individually-attributable sharing action.

**Intent**
Ensures FR046's per-category control is transparent and never bypassed by acceptance or connection progress alone.

**Success outcome**
Both parties understand exactly what was just shared; every visible shared category traces to a deliberate action.

**Failure / edge outcome**
An ambiguous sharing confirmation, or a category visible with no corresponding sharing action, is a defect.

**Acceptance criteria**
- [ ] A share action produces an explicit confirmation naming the category and recipient.
- [ ] Every visible shared category has a corresponding, timestamped sharing action by its owner.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ~ (confirmation + no-auto-disclosure both protect the same "deliberate action only" principle) · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR048 — Family-Contact Category Requires Separate Authorization
**Traces from:** BR10, BR04
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a participant attempts to share "parent/family contact details," the system shall require that category to be independently authorized (per BR04) by the relevant family member before it can be shared, distinct from the candidate's own personal-information sharing authority.

**Intent**
Closes this BR's FR group by tying its most sensitive category to BR04's authorization model.

**Success outcome**
Family contact sharing only proceeds when the relevant family member's own authorization permits it.

**Failure / edge outcome**
A candidate attempting to share family contact details without that family member's authorization is blocked.

**Acceptance criteria**
- [ ] Family-contact sharing checks the family member's own BR04 authorization, not just the candidate's.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR049 — Enable Private In-Platform Communication
**Traces from:** BR11
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When two candidates have an accepted connection (BR09), the system shall let them communicate privately in-platform, without requiring a phone number or other external contact exchange (BR12) first.

**Intent**
First demoable Communication slice — a real, working private chat.

**Success outcome**
Candidates converse without pre-exchanging contact details.

**Failure / edge outcome**
Communication blocked pending contact exchange is a defect.

**Acceptance criteria**
- [ ] Messaging is available immediately upon connection acceptance, before any BR12 exchange.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR050 — No Permanent Chat History; Minimal-Necessary Retention
**Traces from:** BR11
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** Medium — exact session lifecycle/retention duration is explicitly open pending technical and legal design (BR11 Confidence note); this FR fixes the required business behavior, not a specific retention window.

**Requirement (ISO 29148 form)**
When a message or conversation event occurs, the system shall process it and retain only the minimal events necessary for consent, authorization, security, abuse prevention, safety, and accountability, and shall not retain the conversation as a conventional, permanently-accessible chat history.

**Intent**
The data-lifecycle/deletion and transient-processing core of BR11, layered onto FR049's working chat.

**Success outcome**
Ordinary conversation content is not permanently browsable; retained data maps to one of the six named purposes.

**Failure / edge outcome**
Conversation content found permanently retained and browsable beyond the minimal-necessity window, or retained data exceeding the six named purposes, is a defect once the window is set at implementation stage.

**Acceptance criteria**
- [ ] Conversation content is not retrievable as a permanent, full-history log outside the minimal-retention/evidence-exception paths (FR053).
- [ ] A data-retention audit maps every retained field to one of the six named purposes.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (retention window/classification deferred) · Singular ~ (lifecycle + minimal-retention are one coherent data commitment) · Feasible ✓ · Verifiable ~ (same reason) · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR11 DEC-001/DEC-002.
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

## FR051 — Access Control: No Routine Human Reading
**Traces from:** BR11
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When any Mangaly operator or system process accesses retained communication data, the system shall restrict that access to the tightly controlled safety pathway (BR14/BR16), with no routine human reading of private communication as a monitoring strategy.

**Intent**
The access-control family BR11 explicitly requires.

**Success outcome**
Only case-specific, authorized safety access occurs.

**Failure / edge outcome**
Any access to communication content outside a logged, case-linked safety pathway is a defect/incident.

**Acceptance criteria**
- [ ] All access to communication content is individually logged with a case/purpose reference.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR052 — Audit Logging of Communication-Related Events
**Traces from:** BR11, BR15
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a consent, authorization, security, abuse-prevention, safety, or accountability-relevant event occurs within a conversation, the system shall record that event to the Accountability/Audit trail (BR15), distinct from and without requiring retention of full message content.

**Intent**
The audit family BR11 explicitly requires, feeding BR15.

**Success outcome**
Relevant events are reconstructable via audit without a full chat log.

**Failure / edge outcome**
An accountability-relevant event (e.g. a reported message) not reconstructable from the audit trail is a gap requiring remediation.

**Acceptance criteria**
- [ ] Each of the six named event categories has a corresponding audit entry type.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR053 — Evidence-Retention Exception and Incident Workflow Trigger
**Traces from:** BR11, BR14, BR16
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** Low — exact scope, duration, and access controls require formal DPDP-compliant legal sign-off before production (BR11 Verifiable: Needs Refinement); this FR intentionally does not fix a specific retention duration or access-control matrix.

**Requirement (ISO 29148 form)**
When Safety Intelligence (BR14) identifies a severe incident (e.g. blackmail, coercion, sexual abuse, financial scam), the system shall allow a tightly controlled, audited, purpose-bound retention of the relevant communication evidence for that specific case, and shall route the case into BR16's controlled human-investigation workflow with only that minimal necessary evidence.

**Intent**
The evidence-retention-exception and incident-workflow families BR11 explicitly requires, kept together since one triggers the other.

**Success outcome**
Severe incident evidence is preserved narrowly, auditable, and reaches a human investigator.

**Failure / edge outcome**
An exception invoked without a documented, audited case-specific justification is itself a defect/incident; a flagged incident that cannot be routed due to over-aggressive deletion triggers an operational alert rather than silently dropping the case.

**Acceptance criteria**
- [ ] Every exception invocation is individually logged with case reference, scope, and time bound.
- [ ] No exception grants access to unrelated conversations.
- [ ] Every flagged incident produces a case record with linked, bounded evidence.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (scope/duration pending legal sign-off) · Singular ~ (exception + its triggered workflow are one coherent severe-incident path) · Feasible ~ (pending legal sign-off) · Verifiable ~ (same reason) · Correct ✓ · Conforming ✓

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

## FR054 — Legal-Hold Handling and Lifecycle-Job Failure Behavior
**Traces from:** BR11
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** Low — exact legal-hold mechanics and retry/alerting mechanics are undefined pending legal and technical design; this FR fixes only the required safe-failure behaviors.

**Requirement (ISO 29148 form)**
When retained communication data becomes subject to a legal or regulatory hold, the system shall suspend normal deletion for that data under FR051-equivalent access controls; and when a scheduled deletion or retention-lifecycle process fails to complete, the system shall alert operations and retry rather than silently defaulting to indefinite retention or premature deletion of held/excepted data.

**Intent**
The legal-hold and failure-behavior families BR11 explicitly requires, kept together as both are "what happens when the normal lifecycle can't proceed as planned."

**Success outcome**
Data under an active hold is preserved and access-controlled; a failed lifecycle job is visible to operations and corrected.

**Failure / edge outcome**
Data under an active legal hold found deleted by the normal lifecycle process, or a failed job found undetected, is a serious defect/incident.

**Acceptance criteria**
- [ ] Data marked under legal hold is excluded from routine deletion jobs.
- [ ] Every lifecycle-job failure produces an operational alert.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (mechanics undefined) · Singular ~ (both are "safe failure of the normal lifecycle") · Feasible ~ (pending design) · Verifiable ~ (same reason) · Correct ✓ · Conforming ✓

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

## FR055 — Multiple Concurrent Conversations, No Seriousness Score
**Traces from:** BR11
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a candidate holds multiple active conversations, the system shall let all of them coexist without computing or displaying a seriousness score, exclusivity requirement, or single current-match state.

**Intent**
Same non-exclusivity invariant as FR045, applied to Communication.

**Success outcome**
Candidate manages several conversations without an imposed exclusivity/seriousness framing.

**Failure / edge outcome**
Any seriousness/exclusivity indicator found is a defect against the module's product invariant.

**Acceptance criteria**
- [ ] A candidate can hold 2+ active conversations with no exclusivity block or seriousness score displayed.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR056 — Capture-Risk-Reduction Measures with Honest Disclosure
**Traces from:** BR11
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** Medium — specific technical mechanisms are an implementation-stage decision (BR11 DEC-003); this FR fixes the business commitment and disclosure requirement only.

**Requirement (ISO 29148 form)**
When a candidate views a protected communication screen, the system shall apply reasonable, platform-appropriate technical measures to reduce the risk of unauthorized capture, while disclosing to users that this is risk reduction, not a guarantee.

**Intent**
Closes out BR11's FR group with its capture-risk-reduction commitment.

**Success outcome**
Reasonable risk-reduction measures are applied and users are honestly informed of their limits.

**Failure / edge outcome**
Product messaging implying an absolute capture guarantee is a defect.

**Acceptance criteria**
- [ ] User-facing copy about communication privacy includes an explicit "risk-reduction, not guarantee" disclosure.
- [ ] No copy claims screenshots/recording/photography are prevented.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR11 DEC-003.
**Assumptions** — specific technical mechanisms (e.g. OS-level capture APIs) are an implementation-stage decision, per BR11.

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

## FR057 — Request Contact Information
**Traces from:** BR12
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a candidate, parent, or appropriately authorized participant wishes to exchange contact information within a connection whose context permits it, the system shall let them submit a contact-information request, recording who requested it and when for Accountability (BR15).

**Intent**
First demoable Contact Exchange slice.

**Success outcome**
Request is created and delivered to the recipient.

**Failure / edge outcome**
A requester lacking BR04 authorization to request on the candidate's behalf is blocked.

**Acceptance criteria**
- [ ] Request records requester identity and timestamp.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR058 — Recipient-Controlled Decision, Internally Attributable
**Traces from:** BR12
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a contact-information request is received, the system shall let only the recipient (or their own authorized decider, per BR04) decide whether to share and what method to share, keeping request authority and receipt/decision authority as distinct roles, and shall record who requested, who decided, what was shared, and when.

**Intent**
Completes FR057's request into a controlled, auditable decision loop.

**Success outcome**
The requester cannot force or auto-approve their own request; the full exchange chain is reconstructable after the fact.

**Failure / edge outcome**
A requester found able to also approve their own request, or a completed exchange missing any element of the chain, is a defect.

**Acceptance criteria**
- [ ] The requesting role and the deciding role are enforced as distinct even within one Home Circle.
- [ ] Every completed exchange has a complete requester/decider/timestamp/content record in Audit.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ~ (decision-control + attributability are one coherent accountability rule) · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR059 — No Automatic Exchange; No Unrequested Channel Disclosure
**Traces from:** BR12
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When any elapsed time, message count, or other behavioral proxy signal occurs, the system shall never automatically trigger a contact exchange as a result, and when one contact channel is shared, the system shall not automatically reveal any other contact channel that was not explicitly requested and approved.

**Intent**
Closes this BR's FR group with its two "no automatic disclosure" invariants.

**Success outcome**
No proxy signal alone ever reveals contact information; only the specific requested-and-approved channel becomes visible.

**Failure / edge outcome**
Any automated trigger revealing contact information, or sharing one channel found to expose another, is a defect.

**Acceptance criteria**
- [ ] No scheduled/automated job or elapsed-time/message-count rule can result in contact-detail disclosure.
- [ ] Sharing phone number does not also reveal email or any other unrequested channel.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ~ (both are "no disclosure beyond the explicit request") · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR060 — Candidate Chooses Timing of Home Circle Involvement
**Traces from:** BR13
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a candidate is exploring a specific connection (BR09), the system shall let the candidate decide when, and whether, to involve their Home Circle in that specific connection, with no automatic or time-based trigger.

**Intent**
First demoable Family Involvement slice.

**Success outcome**
Candidate controls exactly when family becomes part of a specific connection.

**Failure / edge outcome**
Family involvement triggered automatically (e.g. after N messages) is a defect.

**Acceptance criteria**
- [ ] Family involvement in a specific connection requires an explicit candidate action.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR061 — Discovery-Level Involvement ≠ Connection-Level Involvement; Private Comm Stays Private
**Traces from:** BR13
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a parent is already independently involved in discovery (BR03) for a candidate, the system shall not treat that parent as automatically part of any specific connection the candidate is exploring, and shall keep private communication (BR11) within that connection invisible to the Home Circle unless the candidate deliberately shares specific content.

**Intent**
Prevents FR060's deliberate-timing rule from being bypassed by pre-existing discovery-level involvement.

**Success outcome**
General discovery involvement and specific-connection involvement remain distinct states; no Home Circle member sees private conversation content by default.

**Failure / edge outcome**
A parent found automatically visible into a specific connection, or a connection found retroactively exposing prior private messages once family is involved, is a defect.

**Acceptance criteria**
- [ ] A parent's discovery-level involvement grants zero automatic visibility into any specific BR09 connection.
- [ ] Involving family in a connection does not retroactively expose prior private message content.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ~ (both protect the same "involvement is deliberate and scoped" principle) · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR062 — Family-to-Family Introduction as a Distinct Step; No Cross-Side Exposure
**Traces from:** BR13
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When both candidates' families become involved in a connection, the system shall treat family-to-family introduction as a distinct step requiring its own deliberate action, and shall never grant one side's family automatic access to the other candidate's Home Circle as a result of that introduction.

**Intent**
Closes this BR's FR group with its most sensitive transition point.

**Success outcome**
Family introduction is a clearly separate, trackable event; each side's Home Circle exposure remains independently controlled.

**Failure / edge outcome**
Family-to-family introduction occurring without an explicit trigger, or one side's involvement exposing the other's Home Circle, is a defect.

**Acceptance criteria**
- [ ] Family-to-family introduction has its own explicit trigger action and record.
- [ ] Family A's involvement produces zero visibility change to Family B's Home Circle, and vice versa.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ~ (both protect the same cross-side boundary) · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR063 — User-Initiated Reporting, Always Available, Never Downgraded
**Traces from:** BR14
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When any candidate or authorized Home Circle member wants to report a person, profile, message, or interaction as unsafe or abusive, the system shall let them submit that report at any time, and shall process it through the full graduated-response pipeline (FR065) regardless of whether automated pattern detection has flagged anything.

**Intent**
First demoable Safety slice — the co-equal, independent entry point BR14 explicitly requires, never secondary to automated detection.

**Success outcome**
Report is captured and enters the response pipeline on its own merits.

**Failure / edge outcome**
Reporting unavailable or gated behind another condition, or a report auto-closed/deprioritized purely because automated detection found nothing, is a defect against BR14's explicit Constraint.

**Acceptance criteria**
- [ ] Reporting is accessible from any profile, message, or interaction surface at any time.
- [ ] Report triage logic does not reference automated-detection absence as a dismissal criterion.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ~ (availability + non-downgrading are one coherent guarantee) · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR14 DEC-002.
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

## FR064 — Bounded Pattern Detection with AI Inference Labeling
**Traces from:** BR14
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** Medium — exact detection-scope boundaries are implementation-stage; any category not named here requires its own explicit business justification per BR14 Constraints.

**Requirement (ISO 29148 form)**
When the Safety Intelligence layer analyzes activity for named risk categories (fake profiles, deception, grooming, blackmail, harassment, vulgarity, threats, sexual abuse, financial manipulation, romance scams, coercion, suspicious escalation, malicious links, off-platform pressure, repeated unwanted contact), the system shall use only the minimum information necessary to identify a meaningful risk pattern in one of these named categories, and shall present any AI-based flag as an inference requiring human review, never as a definitive determination.

**Intent**
The second, automated entry point — co-equal with, never a substitute for, FR063.

**Success outcome**
Detection activity is demonstrably scoped to the named categories and minimal data; flags are clearly framed as inference pending review.

**Failure / edge outcome**
Detection operating on an unnamed category or excess data, or a flag acted upon as definitively true without human review, is a defect requiring scope correction.

**Acceptance criteria**
- [ ] A documented data-minimization justification exists per named risk category.
- [ ] Every automated flag is labeled as requiring human review before any restrictive action is finalized.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (scope boundaries implementation-stage) · Singular ~ (bounded-scope + inference-labeling both govern the same detection output) · Feasible ✓ · Verifiable ~ (same reason) · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR14 DEC-002.
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

## FR065 — Graduated Response Pipeline
**Traces from:** BR14
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** Low — exact severity taxonomy and stage-escalation thresholds are explicitly open (see FR068); this FR fixes the required stage sequence, not the thresholds.

**Requirement (ISO 29148 form)**
When a safety concern is raised via either FR063 or FR064, the system shall route it through a graduated response: privacy-preserving triage → warning/nudge → restriction/block → controlled human investigation → legal/emergency escalation for severe cases.

**Intent**
The shared pipeline both entry points feed into.

**Success outcome**
A concern moves through appropriately escalating stages based on severity.

**Failure / edge outcome**
A severe case failing to reach human/legal escalation due to an unset threshold is flagged to Impact Analysis/Security & Performance for resolution before production (see FR068).

**Acceptance criteria**
- [ ] Each of the five named stages exists as a distinct, sequenced system state.
- [ ] Escalation to human investigation is possible from any stage when warranted, not solely at pipeline end.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (thresholds open) · Singular ✓ · Feasible ✓ · Verifiable ~ (thresholds open) · Correct ✓ · Conforming ✓

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

## FR066 — Safety and Trust Remain Operationally Distinct
**Traces from:** BR14, BR08
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a candidate is both verified (BR08) and subject to a safety concern (BR14), the system shall evaluate and act on the safety concern independently of that candidate's verification status.

**Intent**
Enforces BR14's named Core Product Principle that safety and trust are separate systems.

**Success outcome**
Safety actions and verification status are demonstrably independent.

**Failure / edge outcome**
A safety case found deprioritized due to the subject's verified status is a defect.

**Acceptance criteria**
- [ ] Safety-case triage logic does not reference verification status as an input.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR067 — Tightly Controlled Safety Access, No Routine Monitoring
**Traces from:** BR14
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When any Mangaly system or operator accesses data for safety purposes, the system shall restrict that access to the minimum necessary for the specific case, with routine human reading of private communication as a general monitoring strategy explicitly out of scope.

**Intent**
The safety-side counterpart to FR051's communication-side access control.

**Success outcome**
Safety access is demonstrably case-scoped, not general surveillance.

**Failure / edge outcome**
Safety access found used for general monitoring beyond specific cases is a defect/incident.

**Acceptance criteria**
- [ ] Every safety-purpose data access is logged with a specific case reference.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR068 — Severity Taxonomy and Escalation Thresholds (Open Design Item)
**Traces from:** BR14
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** Low — genuinely open design item (BR14 Confidence note; BRD BR-SAFE-007 "OPEN") requiring dedicated design work (abuse taxonomy, severity matrix, staffing, legal review) at Impact Analysis/Security & Performance stage.

**Requirement (ISO 29148 form)**
When defining the threshold of severity that moves a case from automated triage to human/legal escalation (FR065), the system shall use a documented severity taxonomy once defined; this FR does not resolve that taxonomy or its exact thresholds.

**Intent**
Names the open gap explicitly rather than letting FR065 silently assume it is solved.

**Success outcome**
The taxonomy work is completed and traceable before production launch.

**Failure / edge outcome**
Production launching without a defined severity taxonomy means FR065's escalation stage cannot be considered verifiable, and this is flagged as a release blocker at the Security & Performance gate.

**Acceptance criteria**
- [ ] A named owner and milestone exist (at Impact Analysis/Security & Performance stage) for severity-taxonomy design.
- [ ] Production launch is gated on this taxonomy's existence.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (taxonomy undefined) · Singular ✓ · Feasible ~ (pending design) · Verifiable ~ (pending design) · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR14 Constraints; this is a design/policy gap, not a fact-finding question the `researcher` subagent could resolve, so it is carried forward as an explicitly flagged open item rather than invented.
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

## FR069 — Record Actor, Capacity, and Authorization for Consequential Actions
**Traces from:** BR15
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When any consequential action occurs anywhere in this module, the system shall record who acted, in what capacity, on whose behalf (where relevant), what action occurred, what person/object was affected, what authorization applied, what consent was present or required, and when it happened.

**Intent**
First demoable Accountability slice — the record every other BR's FRs already write into.

**Success outcome**
Any consequential action is fully reconstructable from the audit trail.

**Failure / edge outcome**
A consequential action found with no corresponding audit record is a defect.

**Acceptance criteria**
- [ ] Every action listed as "consequential" in BR02–BR14, BR16, BR18–BR20 has a corresponding audit-record schema.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR15.
**Assumptions** — storage substrate may be shared platform infrastructure (BR15 Assumptions); this FR governs what must be logged, not where.

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

## FR070 — Record Revocation, Change, and Dispute
**Traces from:** BR15
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a previously recorded accountable action is later revoked, changed, or disputed, the system shall record that subsequent event linked to the original record, preserving the original record rather than overwriting it.

**Intent**
Extends FR069 to cover the full lifecycle of an accountable event, not just its creation.

**Success outcome**
Full history including revocations/disputes is reconstructable.

**Failure / edge outcome**
A revocation found to overwrite/delete the original audit record is a defect.

**Acceptance criteria**
- [ ] Revocation/dispute events are additive, never destructive, to the original audit record.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR071 — Audit Trail Not Exposed as Surveillance; Least-Privilege Admin Query
**Traces from:** BR15
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When an ordinary Home Circle member or candidate attempts to view another member's audit trail, the system shall deny that access; and when Mangaly admin/operations (BR16) needs to investigate a case, the system shall let them query only the audit records relevant to that specific assigned case, itself logged.

**Intent**
Closes this BR's FR group with its two access-boundary rules.

**Success outcome**
No user gains visibility into another's full audit trail; admin access to audit data is case-scoped and itself auditable.

**Failure / edge outcome**
A Home Circle member found able to view another member's trail, or an admin found browsing unrelated records, is a defect against BR15's explicit anti-surveillance constraint.

**Acceptance criteria**
- [ ] No end-user role can query another user's full audit trail.
- [ ] Admin audit-trail queries are scoped to an assigned case ID and are themselves logged.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ~ (both are the same "audit access is need-to-know" principle applied to two roles) · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

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

## FR072 — Verification-Related Admin Workflow
**Traces from:** BR16, BR08
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** Medium — exact workflow steps/staffing are open per BR16 Confidence note.

**Requirement (ISO 29148 form)**
When an identity/profile verification request or a Verification Circle review requires operator action, the system shall provide an operator workflow to review submitted evidence and record a verification decision, feeding the outcome back into BR08's evidence display.

**Intent**
First demoable Admin/Operations slice.

**Success outcome**
Operator completes a verification review and the outcome reaches BR08.

**Failure / edge outcome**
Insufficient evidence lets the operator mark the request incomplete and request more, rather than being forced to approve/deny prematurely.

**Acceptance criteria**
- [ ] Operator workflow exists for both identity/profile verification and Verification Circle review cases.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (exact workflow steps deferred) · Singular ✓ · Feasible ✓ · Verifiable ~ (same reason) · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR16.
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

## FR073 — False-Relationship Investigation Workflow
**Traces from:** BR16, BR02
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** Medium — same workflow-detail caveat as FR072.

**Requirement (ISO 29148 form)**
When a Home Circle relationship claim is reported as false (FR011), the system shall provide an operator workflow to investigate and record a determination, withholding Home Circle access for the disputed relationship pending that determination.

**Intent**
Fulfills FR011's promise of an actual investigation path.

**Success outcome**
Reported relationship claims are investigated and resolved.

**Failure / edge outcome**
If a determination cannot yet be reached, the operator marks the case open/pending rather than forcing a premature outcome.

**Acceptance criteria**
- [ ] Operator workflow produces a recorded determination (confirmed/false/pending) per reported case.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (workflow detail deferred) · Singular ✓ · Feasible ✓ · Verifiable ~ (same reason) · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR16.
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

## FR074 — Abuse/Fraud Investigation with Restriction, Block, and Escalation
**Traces from:** BR16, BR14
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** Medium — same workflow-detail caveat.

**Requirement (ISO 29148 form)**
When an abuse report or fraud indicator (BR14) requires investigation, the system shall provide an operator workflow to review evidence and determine an outcome, and shall let an authorized operator apply a restriction, block, or legal/emergency escalation where warranted, logged to Audit (BR15) and never disclosed publicly.

**Intent**
Connects BR14's pipeline to an actual human decision and consequence.

**Success outcome**
Reports are investigated and actioned appropriately, with every action linked to a case reference.

**Failure / edge outcome**
Insufficient evidence lets the operator record the case as inconclusive rather than forcing a block or dismissal.

**Acceptance criteria**
- [ ] Operator workflow supports evidence review and a recorded outcome per case.
- [ ] Every restriction/block/escalation action has a linked case reference in Audit.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (workflow detail deferred) · Singular ~ (investigation + its resulting action are one coherent case-handling flow) · Feasible ✓ · Verifiable ~ (workflow detail deferred) · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR16.
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

## FR075 — Appeals Workflow
**Traces from:** BR16
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a candidate wishes to appeal a restriction, block, or investigation outcome, the system shall provide a workflow for them to submit an appeal and have it reviewed, recording the appeal outcome to Audit.

**Intent**
Balances FR074's enforcement power with a defined recourse path.

**Success outcome**
Candidate has a defined path to contest an outcome.

**Failure / edge outcome**
An action type found with no available appeal path is a gap against this FR's completeness.

**Acceptance criteria**
- [ ] Every restriction/block outcome type has an available appeal path.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR16.
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

## FR076 — Admin Actions Audited, Least-Privilege, No Public Disclosure
**Traces from:** BR16, BR15
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When an operator performs any consequential admin action, the system shall record it to Audit (BR15) with the same detail as any other actor's actions, shall scope that operator's access to only the case(s)/function(s) assigned to them, and shall keep every investigation outcome visible only to involved parties and authorized operators, never published as a public accusation or reputation signal.

**Intent**
Closes out BR16's FR group with its three cross-cutting operational guardrails.

**Success outcome**
Admin actions are fully auditable, access is demonstrably scoped, and outcomes stay private.

**Failure / edge outcome**
An admin action without an audit record, an operator with access beyond their assigned scope, or an outcome exposed publicly, is each a defect requiring immediate correction.

**Acceptance criteria**
- [ ] 100% of admin actions in FR072–FR075's workflows produce an audit record.
- [ ] Operator role definitions map explicitly to case/function scope, with no "all access" admin role for case data.
- [ ] No investigation outcome is visible to any user outside the case's involved parties and assigned operators.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ~ (three guardrails bundled as they govern the same "admin power is accountable and bounded" principle) · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR16.
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

## FR077 — Scoped, Revocable, Attributable Agent Access
**Traces from:** BR17
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Could
**Status:** Draft
**Confidence:** Low — explicitly a deferred, future capability across every source document (BR17).

**Requirement (ISO 29148 form)**
When a future verified community marriage professional (Agent) is granted access to support a family/candidate, the system shall scope that access explicitly to the specific families/candidates and functions authorized, never defaulting to broad profile-browsing or administrative rights, shall make it revocable at any time by the authorizing party, and shall attribute every Agent action to that Agent in Audit (BR15).

**Intent**
The scoping/attribution foundation this deferred capability would need before it could exist at all.

**Success outcome**
Agent access is demonstrably narrow, revocable, and every action is traceable to that Agent.

**Failure / edge outcome**
An Agent found with default broad access, or an unattributed Agent action, is a defect against this FR.

**Acceptance criteria**
- [ ] Agent access is granted per-family/per-candidate, never platform-wide.
- [ ] Access is revocable by the authorizing party at any time.
- [ ] Every Agent action has a corresponding audit record naming that Agent.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ~ (scoping + revocability + attribution together define one coherent access model) · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR17.
**Assumptions** — this FR describes required behavior for if/when this deferred capability is built; it is not scheduled for the current build cycle (BR17 DEC-001).

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

## FR078 — Agents Cannot Gatekeep Exposure; Deferred Until Core Product Proven
**Traces from:** BR17
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Could
**Status:** Draft
**Confidence:** Low — same deferred-capability caveat as FR077.

**Requirement (ISO 29148 form)**
When an Agent operates within the platform, the system shall ensure the Agent cannot control which candidates receive Discovery exposure or ranking advantage, and the organization shall not enable any Agent-layer functionality until the core candidate/family product (BR01–BR16) is live and proven.

**Intent**
Closes out this deferred BR's FR group with its two hardest non-negotiables: no pay-to-win gatekeeping, and no early activation.

**Success outcome**
Discovery/ranking outcomes are unaffected by Agent involvement or lack thereof; no Agent-layer feature ships ahead of the sequencing gate.

**Failure / edge outcome**
An Agent-represented candidate found with a ranking advantage attributable to Agent involvement, or Agent-layer functionality found active before the gate is met, is a defect against this FR and BR17's explicit Constraint.

**Acceptance criteria**
- [ ] Discovery ranking logic contains no input tied to Agent representation status.
- [ ] A documented go/no-go gate references core-product maturity before any Agent-layer release.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ~ (both are non-negotiable conditions for this deferred capability ever activating) · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR17 DEC-001.
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

## FR079 — Mark Matrimonial Search Concluded
**Traces from:** BR18
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a candidate (or an authorized Home Circle member acting for them per BR04) decides their search has concluded (engaged, married, or otherwise no longer searching), the system shall let them mark that outcome as a deliberate action, never inferred from behavioral/activity signals.

**Intent**
First demoable Lifecycle slice.

**Success outcome**
Candidate's lifecycle state is recorded as concluded.

**Failure / edge outcome**
The system inferring a concluded state from reduced activity is a defect against the module's explicit product invariant.

**Acceptance criteria**
- [ ] Concluding a search requires an explicit user action, never an automated inference.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR18.
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

## FR080 — Concluded Profile Excluded from Discovery/Compatibility Without Data Loss
**Traces from:** BR18
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a profile is marked concluded (FR079), the system shall exclude it from Discovery (BR06) results and from being offered as a Compatibility match (BR07) to others, without deleting historical data or invalidating past connection/accountability records (BR15).

**Intent**
The actual inventory-quality effect FR079's action exists to produce.

**Success outcome**
Concluded profile stops appearing to others; its history remains intact.

**Failure / edge outcome**
Concluding a profile found to delete or invalidate historical records is a defect.

**Acceptance criteria**
- [ ] A concluded profile no longer appears in Discovery/Compatibility results for other users.
- [ ] All historical connection/accountability records for that profile remain queryable by authorized parties.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR18.
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

## FR081 — Reactivate Concluded Profile; Lifecycle State Audited
**Traces from:** BR18, BR15
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When the owner of a concluded profile wants to resume their search, the system shall let them reactivate it, restoring full Discovery/Compatibility participation without requiring re-verification of already-verified facts that have not changed (subject to BR08's normal freshness rules), and shall record every concluded/reactivated transition to Audit (BR15).

**Intent**
Closes this BR's FR group with the reverse action and its accountability record.

**Success outcome**
Owner regains full participation without redundant re-verification; lifecycle state history is fully reconstructable.

**Failure / edge outcome**
Reactivation blocked pending unnecessary re-verification, or a lifecycle change found without a corresponding audit record, is a defect.

**Acceptance criteria**
- [ ] Reactivation restores Discovery/Compatibility eligibility without re-running verification for facts within their freshness window.
- [ ] Every concluded/reactivated transition produces an audit record with actor and timestamp.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ~ (reactivation + its audit record are one coherent lifecycle-transition rule) · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR18.
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

## FR082 — Invite/Capture Success Story Only With Full Consent
**Traces from:** BR19
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Could
**Status:** Draft
**Confidence:** Medium — the business need is real but not core-product-critical, and has no source-document citation (BR19).

**Requirement (ISO 29148 form)**
When a match has concluded per BR18, the system shall let Mangaly invite the involved candidates to share a success story, and shall capture the story only if every involved candidate gives explicit, specific consent, never assumed from the BR18 conclusion action itself.

**Intent**
First demoable Success Story slice for this Could-priority capability.

**Success outcome**
A story is only captured when every party has explicitly agreed.

**Failure / edge outcome**
Any involved party not consenting blocks capture/publication entirely, regardless of the other party's consent.

**Acceptance criteria**
- [ ] Story capture requires a distinct, separate consent action from each involved party.
- [ ] A single non-consenting party blocks capture/publication entirely.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR19 DEC-001.
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

## FR083 — Declining Has Zero Effect on Account Status; Consent Audited and Revocable
**Traces from:** BR19, BR15
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Could
**Status:** Draft
**Confidence:** Medium — same BR19 caveat as FR082.

**Requirement (ISO 29148 form)**
When a candidate declines a success-story invitation or has never been invited, the system shall leave their account status, lifecycle state, and product access completely unaffected; and when a candidate grants, modifies, or revokes story consent, the system shall record that event to Audit (BR15) and halt/remove use of the story upon revocation where technically feasible.

**Intent**
Keeps this Could-priority capability fully independent of BR18's Must-priority lifecycle mechanics, and makes consent state changes enforceable, not just recorded.

**Success outcome**
Declining a story has no downstream consequence anywhere in the product; consent state changes are fully traceable and enforced.

**Failure / edge outcome**
Declining found to affect any other capability, or a revoked story found still in active publication, is a defect requiring immediate remediation.

**Acceptance criteria**
- [ ] A candidate who declines shows no difference in any other capability compared to one who was never invited.
- [ ] Revocation triggers a takedown action for any active publication.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ~ (independence + revocation-enforcement are the same underlying consent guarantee) · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR19 DEC-001.
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

## FR084 — Published Story Excludes Undisclosed Sensitive Content
**Traces from:** BR19
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Could
**Status:** Draft
**Confidence:** Medium — same BR19 caveat.

**Requirement (ISO 29148 form)**
When a consented success story is prepared for publication, the system shall exclude Home Circle membership details, private communication content (BR11), and any contact details beyond exactly what each consenting party explicitly approved for that specific story.

**Intent**
Closes this BR's FR group by bounding what a "yes" in FR082 actually authorizes.

**Success outcome**
Published content matches only what was explicitly approved.

**Failure / edge outcome**
A published story found containing unapproved sensitive content is a defect requiring immediate takedown.

**Acceptance criteria**
- [ ] A pre-publication review checklist confirms only explicitly-approved content is included.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR19.
**Assumptions** — publication channel (in-app, website, social) is a later marketing/distribution decision outside this FR (BR19 Assumptions).

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

## FR085 — Optional Safety Guidance Before In-Person Introduction
**Traces from:** BR20
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** Medium — exact guidance content requires product/legal input per BR20 Assumptions/DEC-003; this FR fixes that guidance must be offered, not its final wording.

**Requirement (ISO 29148 form)**
When a candidate (and, where involved, family) is approaching an in-person introduction, the system shall present optional, clear safety guidance (e.g. meet in a public place, tell someone the plan, verify identity before meeting where not already done), informational and never a mandatory precondition to using the platform.

**Intent**
First demoable slice for this Must-priority safety capability.

**Success outcome**
Candidate sees relevant safety guidance before a real-world meeting.

**Failure / edge outcome**
Guidance presented as a mandatory gate (blocking further use until acknowledged) is a defect against BR20's explicit "optional" constraint.

**Acceptance criteria**
- [ ] Safety guidance is surfaced at a contextually relevant point (e.g. after contact exchange or family involvement) without blocking further use.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ~ (exact guidance content pending product/legal input) · Singular ✓ · Feasible ✓ · Verifiable ~ (same reason) · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR20 DEC-001/DEC-003.
**Assumptions** — guidance is informational content (text/checklist), not a platform-mediated live-safety feature (BR20 Assumptions).

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

## FR086 — Opt-In "Meeting Occurred" Note
**Traces from:** BR20
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a candidate wants to note that an introduction/meeting occurred, the system shall let them record that note, distinct from any other event in the connection's history, opt-in only and never inferred or auto-detected from other signals.

**Intent**
The specific, bounded record BR20 authorizes — nothing more.

**Success outcome**
A meeting-occurred note exists only when a party deliberately records it.

**Failure / edge outcome**
The system inferring a meeting occurred from behavioral signals (e.g. contact exchange followed by reduced messaging) is a defect against the module's product invariant.

**Acceptance criteria**
- [ ] "Meeting occurred" is a distinct, manually-triggered note, never auto-populated.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR20.
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

## FR087 — Report a Concern From a Real-World Meeting
**Traces from:** BR20, BR14
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a candidate or family wants to report a concern arising from a real-world meeting, including a post-meeting incident, the system shall let them submit that report through the same reporting path as any other safety concern (FR063), with no separate or diminished path for post-meeting incidents.

**Intent**
Gives Safety Intelligence (BR14) signal on the highest-physical-risk moment in the journey, per BR20's Worth check.

**Success outcome**
Post-meeting concerns are reported and triaged identically to any other safety concern.

**Failure / edge outcome**
Post-meeting reports found routed through a different, weaker path is a defect.

**Acceptance criteria**
- [ ] A post-meeting incident report uses the identical BR14 reporting mechanism and pipeline as any other report.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR20.
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

## FR088 — No Relationship-Progress Tracking; Platform Role Ends at Introduction
**Traces from:** BR20
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a "meeting occurred" note exists for a connection, the system shall not track, monitor, prompt for, or display any ongoing relationship-progress, status, or planning information beyond that single note and BR18's separate lifecycle-conclusion action, and shall limit its role to safety guidance (FR085), the opt-in note (FR086), and the reporting path (FR087) — never organizing, scheduling, chaperoning, or coordinating location for the meeting itself.

**Intent**
Closes out this BR's FR group with the explicit scope boundary that prevents Mangaly from drifting into relationship-management territory — stated here as a boundary-defining FR since it is essential to hold at the UX/UI/implementation stages, per BR20's explicit non-goal.

**Success outcome**
No feature exists anywhere that tracks post-meeting relationship status/progress, schedules meetings, or chaperones them.

**Failure / edge outcome**
Any relationship-status field, wedding-planning prompt, or scheduling/chaperone-coordination feature found anywhere is a defect directly against BR20's explicit non-goal and DEC-001's narrow scoping decision.

**Acceptance criteria**
- [ ] No data model field or UI surface represents relationship status/progress beyond the BR18 lifecycle state and the FR086 note.
- [ ] No platform feature schedules, coordinates location for, or chaperones a real-world meeting.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ~ (both are the same "platform role ends at introduction" boundary) · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR20 DEC-001.
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

## FR089 — Person-Level Language Preference on Profile
**Traces from:** BR01
**Traced to:** [populated later by UX/Test Scenarios agents]
**Priority:** Must
**Status:** Draft
**Confidence:** High

**Requirement (ISO 29148 form)**
When a candidate creates or edits their profile, the system shall let them set a language preference (English, Hindi, or Telugu at V1, per `ARCHITECTURE.md` ADR-010's day-one language set) attached to that person's own record, not to the app session or device alone, and shall use it as the input every other rendering surface (Discovery, Compatibility, Trust/Verification) reads when presenting that person's content through the platform's shared translated-content model.

**Intent**
Covers BR01's language-preference Constraint (added in this file's 2026-09-10 correction pass) — a genuine Mangaly-owned profile field, distinct from the underlying translation/i18n infrastructure, which stays Common Platform.

**Success outcome**
A candidate's chosen language preference persists on their profile and is available for every downstream rendering surface to read.

**Failure / edge outcome**
A candidate who has not yet set a preference is not blocked from saving a profile (existence tier, FR001) — the field defaults to a platform-level fallback rather than forcing a choice before any other profile action.

**Acceptance criteria**
- [ ] Language preference is stored on the person's own record, not only on a device/session.
- [ ] Changing the preference does not require re-entering or re-saving any other profile field.
- [ ] An unset preference does not block profile creation (FR001) or any other capability.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** — none beyond BR01 DEC-004.
**Assumptions** — the rendering/translation mechanics that consume this preference are Common Platform infrastructure (`ARCHITECTURE.md` ADR-010); this FR only fixes that the preference exists as person-level profile data (BR01 DEC-004).

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
