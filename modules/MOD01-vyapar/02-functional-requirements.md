---
step: 02-functional-requirements
module: MOD01
status: Sealed
approver: Product Manager
updated: 2026-09-06
items: 56 | approved: 56 | blockers: 0
---

# 02 — Functional Requirements — MOD01 Vyapar

## Revision history
| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-06 | Initial draft: looped over all 7 Sealed BRs in `01-business-requirements.md` in order (BR01→BR07), producing 56 FRs total (BR01: 10, BR02: 9, BR03: 6, BR04: 7, BR05: 7, BR06: 8, BR07: 9). Every FR written in mandatory ISO 29148 sentence form (`[condition], the system shall [action] [object] [constraint]`), each carrying an explicit success outcome and failure/edge outcome per this step's Handoff readiness requirement for the UX agent. Judgment calls resolved autonomously per standing instruction (see individual FR "Decisions" sections); no clarifying question raised to a human. Four additional config placeholders recorded in `/modules/MOD01-vyapar/config/vyapar.config.example.md` (re-verification cadence, minimum partnership verification level, enquiry-response SLA, search-index refresh interval) so no FR was left blocked pending a numeric/config decision. | Step 2, autonomous execution (pinned preference: no clarifying questions; decide and document reasoning in-line). Source: `01-business-requirements.md` (Sealed), `ARCHITECTURE.md` (Sealed — ADR-002, ADR-004 through ADR-010, ADR-013), `/modules/modules.md`. |
| 2026-09-06 | Reviewed and sealed. Independently re-verified Coverage check against the actual parent `01-business-requirements.md` file's own `Traced to:` fields (not just this file's own claim) — exact match, no blank rows. Spot-checked Handoff readiness and the nine-point quality gate on a representative sample of FRs across all 7 BRs rather than re-confirming the producing agent's own checkmarks. Confirmed FR47's negative "shall not" form is a genuine, argued exception (explicit scope-boundary guard, also carries a positive alternative-action clause), not a lazy shortcut. No defect found; nothing required correction. Full findings in "Reviewer notes" below. | Step 2 review, functional-requirements-reviewer (autonomous mode), Product Manager / BA gate. |

## Coverage check
| Parent BR | FRs produced | Covered |
|---|---|---|
| BR01 | FR01, FR02, FR03, FR04, FR05, FR06, FR07, FR08, FR09, FR10 | Yes |
| BR02 | FR11, FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR19 | Yes |
| BR03 | FR20, FR21, FR22, FR23, FR24, FR25 | Yes |
| BR04 | FR26, FR27, FR28, FR29, FR30, FR31, FR32 | Yes |
| BR05 | FR33, FR34, FR35, FR36, FR37, FR38, FR39 | Yes |
| BR06 | FR40, FR41, FR42, FR43, FR44, FR45, FR46, FR47 | Yes |
| BR07 | FR48, FR49, FR50, FR51, FR52, FR53, FR54, FR55, FR56 | Yes |

Independently cross-checked against `01-business-requirements.md`'s own `Traced to:` field on each of BR01–BR07 (populated by functional-requirements-agent in Step 2) — every FR number listed there matches this table exactly, in both directions. No BR in the Sealed parent file is missing an FR.

## Set-level quality gate
| Check | Result |
|---|---|
| Comprehensive — every BR covered | Pass — all 7 BRs produced at least one FR; no blank rows in the Coverage check above; independently re-verified against the parent BR file directly. |
| Consistent | Pass — no two FRs claim conflicting behavior for the same entity/state transition; cross-references (e.g., FR31↔FR53 on promoted-vs-organic labeling, FR22↔FR24 on the Vyapar/Counsel professional-credential boundary) used instead of restating logic. Re-checked both cross-reference pairs directly — each pair states one guarantee from two different owning angles (discovery-surface vs. promotion-owning-side; profile-display vs. structural-separation) without contradiction. |
| Prioritized | Pass — every FR inherits its parent BR's priority (BR05's 7 FRs are Should; all others Must), individually re-stated on each FR. FR18 and FR23/FR30 are the only FRs that deliberately downgrade below their parent BR's own priority (Must-priority BR02/BR03/BR04 respectively), each with its own explicit, argued rationale in its Assumptions/Decisions section — re-checked, both hold up as genuine granular judgment calls, not errors. |
| No duplicates | Pass — each entity state transition, screen-level action, and system-computed behavior appears in exactly one FR. |

## Open blockers
None.

---

## FR01 — Submit Verification Request
**Traces from:** BR01
**Traced to:** (populated later by UX/Test Scenarios agents)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a business owner, entrepreneur, freelancer, or professional submits a new `BusinessProfile` or `ProfessionalProfile` for the first time, the system shall create a verification request record with status `Pending` and route it to the automated Level-3 verification checks defined in FR02–FR05 within the same submission transaction.

**Intent**
Establishes the single entry point into BR01's verification gate so no profile can exist without an associated, trackable verification record — the precondition for FR06's status display and FR08's re-verification lifecycle.

**Success outcome**
A verification request record is created, linked 1:1 to the submitting profile, status visibly set to `Pending`, and the submitter sees confirmation that automated checks have started.

**Failure / edge outcome**
If required verification inputs (e.g., business registration number, license number) are missing or malformed, the system rejects the submission before creating a `Pending` record, returns field-level validation errors, and the profile remains in a `Draft`/unsubmitted state rather than entering the verification queue.

**Acceptance criteria**
- [ ] Every new BusinessProfile/ProfessionalProfile has exactly one associated verification request upon first submission.
- [ ] Missing/malformed required verification inputs block queue entry with field-level errors, not a generic failure.
- [ ] Submission timestamp is recorded and used as the SLA clock start for FR07.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of when the verification clock should start, facing "on submission" versus "on first automated check completion," we chose submission time over check-completion time, to achieve an SLA (FR07) that reflects the member's actual wait experience rather than internal processing lag, accepting that a slow downstream queue would count against the SLA even if the member's submission was instant.

**Assumptions**
- Assumed "first submission" is a single atomic event per profile (a profile cannot exist in an ambiguous semi-submitted state) — consistent with BR01's stated precondition role.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes — business owner/professional |
| Trigger condition | Yes — first submission of a new profile |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): spot-checked directly — role, trigger, and both outcomes genuinely present in prose, not merely claimed in the table. Nine-point gate re-checked independently. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR02 — Automated Business Identity/Registration Check
**Traces from:** BR01
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a `Pending` verification request includes a business (not solely individual-professional) claim, the system shall call the Identity & Trust Service's external registry/KYC check via `BUSINESS_REGISTRY_VERIFICATION_API_ENDPOINT` (per ADR-004, Vyapar never calls the external provider directly) and record the returned match/no-match result against business identity and registration data within the verification request.

**Intent**
Delivers BR01 element (a) — business identity and registration — as an automated, non-discretionary check, per the automated-first principle (Master PRD §8.6).

**Success outcome**
A match result is recorded, the verification request advances toward `Verified` (pending the other required checks), and the check's evidence reference (registry response ID) is stored for audit.

**Failure / edge outcome**
On no-match, provider error, or provider timeout, the system records the outcome as `Unresolved-Automated` and routes the request to human review (FR07) rather than silently marking it `Rejected` or `Verified` — a provider outage must never be interpreted as a business failing verification.

**Acceptance criteria**
- [ ] Vyapar never issues a direct call to an external KYC/registry provider (all such calls route through Identity & Trust Service).
- [ ] No-match and provider-error are distinguished outcomes, not conflated.
- [ ] Evidence reference is retained for at least the audit-retention period defined at Tech Reqs step.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of a provider timeout/error, facing "treat as fail" versus "treat as unresolved, escalate," we chose unresolved-and-escalate over auto-fail, to achieve fairness to a legitimate business hitting a transient outage, accepting the added human-review load transient outages will generate.

**Assumptions**
- None beyond BR01's own stated ADR-004 constraint.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes — business owner (indirect; system-driven check) |
| Trigger condition | Yes — Pending request with business claim |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): nine-point gate re-checked independently — "Correct" and "Verifiable" both substantively earned (no-match vs. provider-error are named as distinct, testable states). Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR03 — Automated Business Ownership Check
**Traces from:** BR01
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a business identity check (FR02) returns a match, the system shall verify that the submitting member is a registered owner, director, or authorized representative of that business via the same Identity & Trust Service integration, and record the ownership-check result before the verification request may reach `Verified`.

**Intent**
Delivers BR01 element (b) — prevents a correctly-identified real business being claimed by someone with no actual ownership/authorization relationship to it (impersonation risk named in BR01's problem statement).

**Success outcome**
Ownership/authorization confirmed and recorded; verification request proceeds to the remaining checks.

**Failure / edge outcome**
If ownership cannot be confirmed, the request is set to `Unresolved-Automated` and escalated to human review (FR07) with the specific mismatch reason (e.g., "submitter not listed as director") surfaced to the reviewer, not the public-facing submitter, to avoid disclosing registry internals prematurely.

**Acceptance criteria**
- [ ] Ownership check cannot be skipped even if identity check (FR02) passed.
- [ ] Mismatch reason is captured for the human reviewer, distinct from any member-facing message.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of what a submitter sees on an ownership mismatch, facing "show exact registry mismatch reason" versus "show a generic pending-review message," we chose the generic message over full disclosure, to achieve protection against a bad-faith actor iteratively probing registry details, accepting reduced transparency to the legitimate submitter who will need to wait for human review to learn the specific reason.

**Assumptions**
- None beyond BR01's stated element (b).

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR04 — Automated Professional Credential/License Check
**Traces from:** BR01
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a verification request includes a claimed licensed profession, the system shall call Identity & Trust Service via `PROFESSIONAL_LICENSE_VERIFICATION_API_ENDPOINT` to confirm the specific credential/license claimed, and record the verified credential identifier(s) for later display (FR22).

**Intent**
Delivers BR01 element (c); also the data source FR22/FR24 depend on for displaying which specific credential was verified, not just a generic badge (BR03's measurable target).

**Success outcome**
Credential confirmed, credential identifier(s) stored against the profile's verification record.

**Failure / edge outcome**
If the claimed profession has no license requirement in the target jurisdiction, or the registry has no record, the system distinguishes "no license required for this profession" (proceed) from "license required but not found" (escalate to human review, FR07) — these are not the same outcome and must not share a status code.

**Acceptance criteria**
- [ ] Verified credential identifier(s) are individually stored, not collapsed into a single boolean flag.
- [ ] "No license required" and "license required but not found" are distinguishable states in the data model.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of professions without a licensing regime, facing "require a license check for every profession" versus "skip the check where no license exists," we chose the latter, to achieve feasibility (an unlicensed but legitimate profession, e.g. many freelance trades, would otherwise be unverifiable by definition), accepting that "Verified" for such a profession means identity/contact legitimacy only, not credential legitimacy — communicated via FR22's specific-credential display rather than a blanket badge.

**Assumptions**
- Assumed a maintained mapping of "profession → license required (Y/N) → registry to check" exists or will be built at Tech Reqs step; flagged as a Tech Reqs input, not resolved here.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed — "no license required" vs. "license required but not found" distinction independently confirmed as testable, non-conflated states. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR05 — Contact/Service Legitimacy Check
**Traces from:** BR01
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** Medium — "basic reachability + service-existence check" reading is BR01's own recorded assumption, flagged for confirmation there; carried forward here at the same confidence.

**Requirement (ISO 29148 form)**
When a verification request reaches the contact/service legitimacy stage, the system shall automatically confirm that at least one listed contact channel (phone, email, or business messaging channel) is reachable (e.g., OTP round-trip or deliverability check) and that the claimed service/product category is not on a disallowed list, before the request may reach `Verified`.

**Intent**
Delivers BR01 element (d) at the automated-first depth BR01 itself scoped (basic reachability + service-existence, not a manual audit).

**Success outcome**
At least one contact channel confirmed reachable; service category confirmed allowed; result recorded.

**Failure / edge outcome**
If no contact channel is reachable after a configrable number of attempts, or the claimed service is on the disallowed/restricted list, the request is set to `Unresolved-Automated`/`Rejected` respectively — unreachable contact escalates to human review (transient failure possible), while a disallowed-category claim is a hard rejection with a member-facing reason, since this is a policy violation rather than a technical ambiguity.

**Acceptance criteria**
- [ ] Reachability check retries at least once before escalating (avoids single-attempt false negatives).
- [ ] Disallowed-category rejection is a distinct outcome from unreachable-contact escalation.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of how deep the "service legitimacy" check should go, facing "mystery-shopper audit" versus "automated reachability + disallowed-category check," we chose the automated-only depth (carrying forward BR01's own recorded assumption) over a manual audit, to achieve consistency with the automated-first principle at scale, accepting the residual risk that a reachable contact with a plausible category can still be a low-quality or fabricated service — mitigated instead by BR07's ongoing reputation signal, not by BR01.

**Assumptions**
- Carries forward BR01's own flagged assumption verbatim (see BR01 Assumptions) rather than re-deciding it at FR level, since BR01 already recorded it as its considered, intentional scope.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed; Medium confidence flag on scope-reading is appropriately carried forward, not silently dropped. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR06 — Display Verification Status on Every Profile/Listing
**Traces from:** BR01
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When any member views a `BusinessProfile`, `BusinessListing`, or `ProfessionalProfile`, the system shall display its current verification status (`Verified` / `Pending` / `Unverified` / `Rejected`) using a visually and structurally distinct label for each state, on every rendering surface including Dashboard's read-only view.

**Intent**
Delivers BR01's measurable target that 0% of unverified claims are visually indistinguishable from verified ones (Master PRD §14).

**Success outcome**
Correct, current status is rendered on every surface consuming the profile/listing, with no surface allowed to omit it.

**Failure / edge outcome**
If a consuming surface (including Dashboard) cannot render the full status treatment (e.g., a constrained card layout), it must still render at minimum a distinguishable Verified/Not-Verified binary — silently omitting the label entirely is not an acceptable degradation.

**Acceptance criteria**
- [ ] All four states have a distinct visual treatment, confirmed in a shared design token (owned by UI step, referenced here as a hard functional constraint).
- [ ] Dashboard's read-only rendering is included in a cross-surface consistency test, not assumed compliant by inheritance.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of constrained layouts (e.g., Dashboard cards) that cannot show full status detail, facing "omit the badge" versus "always show at minimum a binary distinguishable label," we chose the latter, to achieve BR01's explicit non-negotiable measurable target, accepting a design constraint that every future surface must budget space for this label.

**Assumptions**
- None; this is a direct restatement of BR01's own measurable target.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes — all members (viewers) |
| Trigger condition | Yes — viewing any profile/listing |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): spot-checked directly — the Dashboard constrained-layout minimum-binary rule is a genuine failure-path guarantee, not a missing edge case. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR07 — Escalate Unresolved Automated Checks to Human Review
**Traces from:** BR01
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When any automated check in FR02–FR05 returns `Unresolved-Automated`, or the verification request has been `Pending` longer than `VYAPAR_VERIFICATION_SLA_DAYS` without resolution, the system shall route the request to a human reviewer queue and notify the reviewer via the shared Notification Service.

**Intent**
Implements BR01's own principle (Master PRD §8.6/§8.7 — automated wherever possible, human review reserved for exceptions) as a concrete, triggerable rule rather than an unspecified manual fallback.

**Success outcome**
Request appears in the human review queue with all automated-check evidence attached; reviewer is notified within the same operational day.

**Failure / edge outcome**
If the human review queue itself has no reviewer capacity within the SLA window, the request remains visibly `Pending` to the submitter (never silently reclassified) and an internal operational alert (not member-facing) fires so capacity can be added — the submitter is never shown a false status to hide an internal backlog.

**Acceptance criteria**
- [ ] Every `Unresolved-Automated` outcome results in a queue entry within the same transaction/session as the check.
- [ ] SLA breach triggers escalation even with zero explicit check failures (pure timeout path).
- [ ] Member-facing status is never altered to mask an internal capacity problem.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of an SLA breach with no available reviewer, facing "silently extend the deadline" versus "keep member status honest and alert internally," we chose the latter, to achieve BR01's own transparency requirement, accepting that this surfaces an operational gap publicly (a visibly slow Pending status) rather than hiding it.

**Assumptions**
- `VYAPAR_VERIFICATION_SLA_DAYS` placeholder value (`5`, per config file) is used as the numeric threshold pending real-traffic data, per BR01's own recorded assumption.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes — human reviewer (internal), submitter (indirect) |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): spot-checked directly — the "never silently reclassify status to hide backlog" failure path is a genuine, non-trivial edge-case guarantee. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR08 — Periodic Re-verification
**Traces from:** BR01
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** Medium — cadence is a placeholder value pending real traffic data (per BR01 DEC-001).

**Requirement (ISO 29148 form)**
When a `Verified` profile/listing reaches `VYAPAR_REVERIFICATION_CADENCE_DAYS` since its last successful verification, the system shall automatically re-run FR02–FR05's applicable checks and update the verification status accordingly, without requiring the member to manually re-initiate the process.

**Intent**
Implements BR01's DEC-001 (periodic revalidation over one-time verification), aligned with the platform's Information Lifecycle principle (Master PRD §15).

**Success outcome**
Re-verification runs automatically on schedule; status remains `Verified` if all checks still pass, with the "last verified" date refreshed.

**Failure / edge outcome**
If re-verification fails any check, status downgrades to `Pending` (not immediately `Rejected`) and the profile keeps its existing discovery/promotion eligibility for a grace window (`VYAPAR_VERIFICATION_SLA_DAYS`) while the member is notified and given a chance to remediate — an automatic, unexplained loss of Verified status for an active business would be a disproportionate consequence for e.g. a single stale document.

**Acceptance criteria**
- [ ] Re-verification is system-triggered on schedule, no manual member action required to initiate it.
- [ ] A failed re-check downgrades to `Pending` with a grace window, not an immediate hard downgrade to `Unverified`/`Rejected`.
- [ ] Member is notified of both the re-verification event and any resulting status change.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of a re-verification failure, facing "immediate downgrade to Unverified" versus "grace-window downgrade to Pending first," we chose the grace window, to achieve proportionality (re-verification failure is often a stale-document issue, not proof the business stopped being legitimate), accepting a short window where a since-failed check's subject still shows some active status, mitigated by the SLA-bounded grace period rather than indefinite tolerance.

**Assumptions**
- `VYAPAR_REVERIFICATION_CADENCE_DAYS` recorded as a new config placeholder (see config file update) with a default of 180 days, pending real V1 traffic data — consistent with BR01's own note that exact cadence is FR-level detail.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes — cadence elapsed |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): spot-checked directly — grace-window failure path is a genuine, proportional edge-case design, confirmed consistent with BR01 DEC-001. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR09 — Prevent Misrepresentation of Verification Status on Any Surface
**Traces from:** BR01
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When any module (including MOD05 Dashboard) reads a Vyapar profile/listing for its own rendering, the system shall serve the current verification status as a mandatory, non-optional field in the read contract, such that no consuming surface can render the entity without also receiving its status.

**Intent**
Makes BR01's "must not represent an unverified profile as verified in any UI surface" constraint structurally enforced at the API/contract level, not merely a UI convention that could be bypassed.

**Success outcome**
Every internal read contract exposing a Vyapar profile/listing includes verification status as a required (non-nullable) field; a consuming module cannot construct a valid response without it.

**Failure / edge outcome**
If a future contract change would make status optional or omittable, the change is rejected at the contract-schema level (a required-field violation), not caught later by manual QA — this is a build-time/contract-level guarantee, not a runtime-only check.

**Acceptance criteria**
- [ ] Verification status is a required (non-nullable) field in the Vyapar→Dashboard internal contract (ARCHITECTURE.md in-process contract).
- [ ] Contract schema validation fails any consuming request that would omit the field.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of enforcing BR01's cross-surface constraint, facing "UI convention/checklist" versus "structural, non-nullable contract field," we chose the structural enforcement, to achieve a guarantee that survives a future developer forgetting the convention, accepting the added rigidity of a required field that every future contract consumer must handle.

**Assumptions**
- None; this operationalizes BR01's constraint directly.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes — indirect (system/contract-level, surfaces to all viewers via FR06) |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR10 — Rejection and Re-submission Path
**Traces from:** BR01
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a verification request is set to `Rejected` (by automated hard-rejection per FR05 or by human reviewer decision per FR07), the system shall notify the submitter with the specific rejection reason category and allow a new verification request to be submitted once the underlying issue is addressed.

**Intent**
Closes the loop on BR01's state machine so `Rejected` is not a dead end — a legitimate business that fixed a real problem (e.g., renewed an expired license) must have a path back to `Verified`.

**Success outcome**
Submitter receives a specific, actionable rejection reason category; a new verification request can be created and re-enters FR01's flow.

**Failure / edge outcome**
If the same submitter/business is rejected repeatedly beyond a reasonable threshold, the system flags the profile for mandatory human review on the next attempt rather than allowing indefinite automated re-submission cycles, to prevent probing/gaming of the automated checks.

**Acceptance criteria**
- [ ] Rejection reason is categorized (not free text only), enabling the submitter to know what to fix.
- [ ] Re-submission creates a new verification request linked to the prior rejected one for audit history.
- [ ] Repeated-rejection threshold routes to mandatory human review.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of repeated rejections from the same submitter, facing "unlimited automated re-submission" versus "route to mandatory human review after a threshold," we chose the threshold-triggered human review, to achieve resistance to automated-check gaming, accepting added review workload for the (presumably rare) repeated-rejection case.

**Assumptions**
- Repeated-rejection threshold value deferred as a Tech Reqs-level tunable, not a business-level decision.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed — closes the BR01 state machine correctly, no dead-end state left unhandled. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR11 — Create Business Profile
**Traces from:** BR02
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a business owner initiates profile creation, the system shall capture business name, category/services offered, description, location(s), contact channels, and media, and persist the profile in `Draft` state until submitted for verification (FR01).

**Intent**
Delivers BR02's core proposed outcome — the entity every other Vyapar capability attaches to.

**Success outcome**
Profile persisted in `Draft`, editable, not yet publicly discoverable.

**Failure / edge outcome**
If required fields (name, at least one category, at least one contact channel) are missing, the system blocks submission-for-verification (not draft-saving itself) with field-level validation — a partial draft must still be saveable so work isn't lost mid-entry.

**Acceptance criteria**
- [ ] Draft can be saved with partial data (no data loss on incomplete entry).
- [ ] Submission-for-verification requires the full required-field set.
- [ ] Profile does not appear in discovery (BR04) while in `Draft`.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of when required-field validation applies, facing "validate on every save" versus "allow partial draft, validate only at submission," we chose the latter, to achieve a low-friction entry experience for a first-time business owner, accepting that a `Draft` profile can be incomplete/inconsistent until the member chooses to submit it.

**Assumptions**
- Assumed profile creation does not itself require prior authentication beyond standard platform Level-1 identity (per BR02's own assumption that formal business registration is not a Draft-stage requirement).

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes — business owner |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR12 — Edit and Maintain Business Profile
**Traces from:** BR02
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a verified business owner edits an existing `BusinessProfile`'s content (excluding fields that were the subject of FR02/FR03's identity/ownership check), the system shall persist the update immediately without requiring re-verification, unless the edit changes a verification-relevant field, in which case the system shall flag the profile for FR08-style re-check on that specific field only.

**Intent**
Keeps normal profile maintenance (updating a description, adding photos) frictionless while ensuring a substantive change to verification-relevant data (e.g., business name, registration number) cannot silently bypass re-verification.

**Success outcome**
Non-verification-relevant edits save instantly; verification-relevant edits save but trigger a targeted re-check without demoting the whole profile to `Pending` for unrelated fields.

**Failure / edge outcome**
If a verification-relevant field edit fails its targeted re-check, only that field's claim is downgraded/flagged, not the entire profile's verification status — an unrelated valid business shouldn't lose its "Verified" badge over one changed detail while re-check is pending.

**Acceptance criteria**
- [ ] Non-verification-relevant fields (description, media, hours) never trigger re-verification.
- [ ] Verification-relevant field list is explicit and enumerable (business name, registration number, ownership claim, license number, primary contact).
- [ ] Targeted re-check failure narrows the impact to the specific claim, not the whole profile.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of editing a verification-relevant field, facing "full profile re-verification" versus "targeted single-field re-check," we chose targeted re-check, to achieve minimal disruption to an otherwise-legitimate, active business, accepting the added complexity of tracking field-level verification provenance rather than one whole-profile status.

**Assumptions**
- None beyond the field classification above, which is recorded here as this FR's own explicit list rather than deferred further.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): spot-checked directly — failure-path scope-narrowing (single-field, not whole-profile) genuinely present, not just claimed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR13 — Create Business Listing Under a Profile
**Traces from:** BR02
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a business owner with an existing `BusinessProfile` creates a `BusinessListing`, the system shall link the listing to the parent profile and inherit the profile's current verification status onto the listing at creation time.

**Intent**
Implements BR02's DEC-001 one-to-many profile/listing model.

**Success outcome**
Listing created, linked to profile, status inherited and kept in sync with subsequent profile status changes (FR16).

**Failure / edge outcome**
If the parent profile is not yet `Verified`, the listing can still be created but is created as `Pending`/`Unverified` per FR16, not blocked outright — creating a listing must not require verification to already be complete, since discovery-eligibility (not creation) is what BR01 gates.

**Acceptance criteria**
- [ ] Listing always references exactly one parent profile.
- [ ] Listing's displayed status always reflects the current parent profile status, not a stale copy.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of listing status representation, facing "copy status at creation time" versus "always derive live from parent profile," we chose live derivation, to achieve consistency (avoiding a stale-status bug class where profile and listing disagree), accepting a query-time join cost over a denormalized copy.

**Assumptions**
- None beyond BR02's own DEC-001.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR14 — Multiple Listings Per Profile
**Traces from:** BR02
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a business owner adds an additional location or service line to an existing verified business, the system shall allow creation of an additional `BusinessListing` under the same `BusinessProfile` without requiring a new, separate profile or duplicate verification of already-confirmed business identity/ownership.

**Intent**
Prevents the exact fragmentation problem BR02's DEC-001 was written to avoid (duplicate profiles splitting verification/reputation).

**Success outcome**
Additional listing created under the same profile; identity/ownership verification is not re-run (already established); only listing-specific fields (this location's address, contact) may need their own legitimacy check (FR05-style, location-specific).

**Failure / edge outcome**
If the new listing's location-specific contact fails reachability (FR05), only that listing is flagged `Pending`, not the parent profile or its other listings.

**Acceptance criteria**
- [ ] A profile can have more than one active listing simultaneously.
- [ ] Adding a listing does not re-trigger business-identity/ownership checks already satisfied at the profile level.
- [ ] A single listing's contact-legitimacy failure is isolated to that listing.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of a new listing under an already-verified profile, facing "re-verify everything" versus "re-check only listing-specific new claims (location contact)," we chose the latter, to achieve BR02's own stated goal of not penalizing legitimate multi-location expansion, accepting a narrower verification surface per additional listing than the first one required.

**Assumptions**
- None beyond BR02's own stated multi-location rationale.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR15 — Multilingual Profile Content
**Traces from:** BR02
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a business owner enters profile content (name, description, category), the system shall allow the content to be authored in English, Hindi, or Telugu (per ADR-010) and display it in the viewing member's selected language where a translation exists, falling back to the originally-authored language where it does not.

**Intent**
Satisfies BR02's ADR-010 multilingual constraint.

**Success outcome**
Content displays correctly in the viewer's language when available.

**Failure / edge outcome**
If no translation exists in the viewer's selected language, the system displays the original authored-language content with a visible "original language" indicator rather than a blank field or a machine-mistranslated silent substitution — the member must know they're seeing untranslated content.

**Acceptance criteria**
- [ ] All three launch languages (English, Hindi, Telugu) are selectable as authoring language.
- [ ] Missing-translation fallback is visibly labeled, not silent.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of a missing translation, facing "silent fallback" versus "labeled fallback to original language," we chose the labeled fallback, to achieve honesty about content provenance, accepting a slightly more complex UI treatment (a visible language-indicator chip) than a silent substitution would need.

**Assumptions**
- Assumed machine translation (if used at all) is a Tech Reqs/UI-step decision, not resolved here; this FR only requires that untranslated content is never silently presented as native-language content.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR16 — Distinguish Verification Status on Listing Display
**Traces from:** BR02
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When any member views a `BusinessListing`, the system shall render its inherited verification status (FR13) using the same distinct visual treatment defined in FR06, on the listing card, the listing detail page, and any Dashboard read-only rendering.

**Intent**
Extends FR06's cross-surface guarantee specifically to the listing entity, since BR02 separately names this as a constraint.

**Success outcome**
Status is visible and correctly labeled everywhere a listing is rendered.

**Failure / edge outcome**
If a listing's parent profile status changes mid-session (e.g., downgraded via FR08), any cached listing view is invalidated/refreshed rather than continuing to show a stale, now-incorrect status.

**Acceptance criteria**
- [ ] Listing status label matches FR06's shared treatment (no separate/inconsistent visual language).
- [ ] Cache invalidation on parent status change is a defined behavior, not left implicit.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of caching a listing's status for performance, facing "cache aggressively" versus "invalidate immediately on any parent status change," we chose immediate invalidation over aggressive caching, to achieve BR01/BR02's zero-tolerance requirement on misrepresenting status, accepting reduced cache-hit efficiency for this specific field.

**Assumptions**
- None; this is a direct extension of FR06/FR13.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR17 — Manage Business Operating Status
**Traces from:** BR02
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a business owner marks a listing as temporarily closed, permanently closed, or reopened, the system shall update the listing's operating status field and exclude permanently-closed and temporarily-closed listings from active discovery search results (BR04) while permanently retaining the record for audit/history.

**Intent**
Supports BR04's requirement to exclude inactive listings (Information Lifecycle principle, Master PRD §15) and gives owners direct control over their own visibility.

**Success outcome**
Status updates immediately reflected in discovery eligibility.

**Failure / edge outcome**
If a business owner marks a listing permanently closed by mistake, the system retains the record (does not hard-delete) so it can be reopened or corrected, rather than requiring the owner to recreate the profile/listing and lose accumulated reviews/reputation (BR07 dependency).

**Acceptance criteria**
- [ ] Temporarily/permanently closed listings do not appear in BR04 search/browse results.
- [ ] No hard delete occurs on status change; historical record and reputation signal are preserved.
- [ ] Reopening a temporarily-closed listing restores discovery eligibility without re-running full verification (identity/ownership already established).

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of a closed listing's data, facing "hard delete" versus "soft status change, retain record," we chose soft status retention, to achieve preservation of BR07's accumulated reputation signal across a temporary closure, accepting the storage/complexity cost of never truly deleting a listing record.

**Assumptions**
- None beyond BR04's own stated exclusion requirement.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): spot-checked directly — no-hard-delete failure-recovery path genuinely present. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR18 — Archive/Deactivate a Business Listing
**Traces from:** BR02
**Traced to:** (populated later)
**Priority:** Should
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a business owner chooses to remove a specific listing (e.g., a discontinued service line) without closing the entire business, the system shall allow that single listing to be archived independently of the parent profile and its other listings.

**Intent**
Complements FR14's multi-listing model — a business dropping one service line shouldn't need to affect unrelated listings.

**Success outcome**
Single listing archived; other listings under the same profile remain fully active and discoverable.

**Failure / edge outcome**
If the archived listing was the profile's only listing, the profile itself is not auto-deleted — it remains in a listing-less active state so the owner can add a new listing later without redoing verification.

**Acceptance criteria**
- [ ] Archiving one listing has zero effect on sibling listings' discovery eligibility.
- [ ] A profile with zero active listings remains a valid, verified entity.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of a profile's last listing being archived, facing "auto-archive the whole profile" versus "keep profile alive with zero listings," we chose keeping the profile alive, to achieve continuity for a business likely to add a new listing later, accepting a data state (verified profile, no listings) that discovery (BR04) must explicitly handle as "nothing to show" rather than an error.

**Assumptions**
- Priority set to Should (not Must) since this is a convenience/lifecycle-management capability, not core to BR02's proposed outcome — inherited judgment, not from BR02's own priority line (BR02 is Must overall; this specific granular capability is lower-criticality within it).

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed — Should-priority downgrade from parent BR02 (Must) independently re-argued as a genuine granular judgment call (convenience capability within a Must-priority BR), not an error. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR19 — Dashboard Read-Only Rendering of Business Listings
**Traces from:** BR02
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When MOD05 Dashboard reads a `BusinessListing` for cross-module surfacing, the system shall expose it via the in-process read-only contract defined in ARCHITECTURE.md, such that Dashboard cannot write, modify, or create derivative copies of listing data outside that contract.

**Intent**
Enforces BR02's constraint that `BusinessProfile`/`BusinessListing` are owned solely by Vyapar.

**Success outcome**
Dashboard successfully reads and renders listing data (including status, per FR16) without any write path existing.

**Failure / edge outcome**
If Dashboard's rendering surface would require a field not exposed in the read contract, that is treated as a contract-extension request routed back to Vyapar's own Tech Reqs step, not an ad-hoc direct database read — no cross-module shared-database access is permitted (ADR-002).

**Acceptance criteria**
- [ ] No write API from Dashboard to Vyapar's listing entities exists at any point.
- [ ] All Dashboard-consumed fields are enumerated in the documented read contract.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of Dashboard needing a field not yet in the read contract, facing "let Dashboard read the Vyapar schema directly" versus "require a contract-extension request through Vyapar's own process," we chose the contract-extension path, to achieve ADR-002's data-isolation guarantee, accepting slower cross-module iteration in exchange for preventing schema coupling.

**Assumptions**
- None beyond ARCHITECTURE.md's own stated contract pattern.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes — indirect (Dashboard's own end users) |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR20 — Create Professional Profile
**Traces from:** BR03
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a freelancer, individual service provider, or professional creates a `ProfessionalProfile`, the system shall capture skills, services offered, experience, portfolio/media, and availability, and persist the profile in `Draft` state until submitted for verification (FR01), independently of whether the same member also holds a `BusinessProfile`.

**Intent**
Delivers BR03's core proposed outcome as a distinct entity type from BR02's `BusinessProfile`.

**Success outcome**
Profile persisted in `Draft`; a member may hold both a `ProfessionalProfile` and a `BusinessProfile` simultaneously with no forced merge.

**Failure / edge outcome**
If required fields (at least one skill/service, one contact channel) are missing, submission-for-verification is blocked with field-level errors, mirroring FR11's pattern.

**Acceptance criteria**
- [ ] `ProfessionalProfile` and `BusinessProfile` are structurally independent entities (no shared primary key/forced 1:1).
- [ ] A member can hold zero, one, or both profile types.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of a member holding both profile types, facing "force a link/merge" versus "fully independent entities, member's account is the only shared reference," we chose full independence, to achieve BR03's own stated non-forced-fit rationale, accepting that a member managing both must maintain two separate content sets.

**Assumptions**
- None beyond BR03's own stated model.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR21 — Edit and Maintain Professional Profile
**Traces from:** BR03
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a verified professional edits their `ProfessionalProfile` content, the system shall persist non-credential-relevant updates immediately and flag any credential/license-claim edit for a targeted re-check, mirroring FR12's pattern for business profiles.

**Intent**
Applies the same edit/re-verification proportionality logic established in FR12 to the professional-profile entity.

**Success outcome**
Non-credential edits save instantly; credential-claim edits trigger a targeted FR04-style re-check.

**Failure / edge outcome**
A failed targeted re-check downgrades only the specific credential claim's displayed status (FR22), not the entire profile.

**Acceptance criteria**
- [ ] Credential-relevant fields are explicitly enumerated (claimed license/certification identifiers).
- [ ] Targeted re-check failure narrows impact to the specific credential claim.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of editing a claimed credential, facing "full re-verification" versus "targeted single-credential re-check," we chose targeted re-check, mirroring FR12's reasoning for consistency across both profile types, accepting the same field-level-provenance tracking complexity.

**Assumptions**
- None beyond FR12's precedent, applied here by direct analogy.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR22 — Display Specific Verified Credential(s)
**Traces from:** BR03
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When any member views a `ProfessionalProfile` with at least one verified credential (per FR04), the system shall display the specific credential name/type verified (e.g., "Licensed Electrician — [registry] #12345-verified") in addition to, not instead of, the generic verification-status label from FR06.

**Intent**
Delivers BR03's measurable target: clear display of the specific credential(s) verified, not just a generic badge.

**Success outcome**
Specific credential(s) rendered alongside the generic status badge.

**Failure / edge outcome**
If the profile has generic (non-licensed) verification only (per FR04's "no license required" path), the system displays the generic status without fabricating a credential label — a professional with no licensing requirement must not appear to have an unearned specific-credential badge.

**Acceptance criteria**
- [ ] Every verified license/credential identifier from FR04 is individually rendered, not summarized into a single generic word.
- [ ] Profiles with no license-required claim show generic status only, never a fabricated credential label.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of a profile with no licensing requirement, facing "show a generic 'Verified Professional' credential-style badge anyway" versus "show only the generic identity/contact status, no fabricated credential," we chose the latter, to achieve accuracy (never implying a credential that wasn't checked because none exists), accepting that some verified professionals will show a less impressive-looking badge than a licensed peer, which is the factually correct outcome.

**Assumptions**
- None beyond FR04's own credential-identifier data model.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR23 — Manage Professional Availability Status
**Traces from:** BR03
**Traced to:** (populated later)
**Priority:** Should
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a professional updates their availability (available / booked / unavailable), the system shall persist the status and surface it on the profile and in discovery results (BR04) as a filterable attribute.

**Intent**
Gives customers/employers a real-time signal of whether engaging a professional is currently practical, improving BR04's discovery usefulness.

**Success outcome**
Availability status updates immediately, filterable in search/browse.

**Failure / edge outcome**
If a professional never updates availability, the system defaults to "available" rather than "unavailable" to avoid silently hiding an otherwise-discoverable, willing professional — a stale-but-optimistic default is the lower-harm failure mode here (a customer enquiring to someone who happens to be busy is recoverable via BR06's enquiry-status lifecycle; being invisible is not recoverable).

**Acceptance criteria**
- [ ] Availability is filterable in BR04's search/browse.
- [ ] Default state for a never-updated profile is "available," not "unavailable."

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of a never-updated availability field, facing "default unavailable (safe/conservative)" versus "default available (optimistic)," we chose optimistic-default, to achieve BR04's goal of maximizing legitimate exposure for capable professionals (the module's own stated problem to solve), accepting the minor UX cost of an occasional enquiry to someone temporarily busy.

**Assumptions**
- Priority set to Should, since this is a discovery-enhancing attribute rather than core to BR03's identity/verification proposed outcome.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed — Should-priority downgrade re-argued as genuine (discovery-enhancement, not core identity/verification). Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR24 — Enforce Separation from Counsel's ExpertProfile
**Traces from:** BR03
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a member holds both a Vyapar `ProfessionalProfile` and a Counsel `ExpertProfile`, the system shall reference the shared `VerifiedCredential` sub-record in Identity & Trust Service by foreign key from both profiles independently, and shall never merge, sync-write, or auto-populate one profile's advisory/consultation fields from the other's commercial-service fields.

**Intent**
Enforces ADR-013's explicit boundary — commercial-service legitimacy (Vyapar) is a meaningfully different trust claim from advisory-liability qualification (Counsel), per BR03's own worth-check.

**Success outcome**
Both profiles independently reference the same underlying credential record where applicable, but remain functionally and structurally separate entities.

**Failure / edge outcome**
If a future engineering shortcut proposes writing directly between the two profile tables (e.g., "just copy the bio over"), that is treated as an ADR-013 violation and rejected at the Tech Reqs/ER Model step, not silently implemented — this FR exists specifically to give that future gate something concrete to check against.

**Acceptance criteria**
- [ ] No direct table/entity coupling exists between `ProfessionalProfile` and `ExpertProfile` beyond the shared `VerifiedCredential` FK.
- [ ] A member can edit one profile without any change appearing in the other.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of two profile entities sharing one underlying person, facing "merge for convenience" versus "keep structurally separate, share only the credential sub-record," we chose separation (reaffirming BR03's own DEC-001 and ARCHITECTURE.md ADR-013), to achieve correct trust-claim separation, accepting duplicate data-entry effort for members holding both roles.

**Assumptions**
- None; this is a direct FR-level operationalization of an already-settled architecture decision (ADR-013), not a new judgment call.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed — ADR-013 boundary independently re-confirmed against ARCHITECTURE.md's own text. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR25 — Multilingual Professional Profile Content
**Traces from:** BR03
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a professional enters profile content, the system shall apply the same multilingual authoring/display/fallback rules defined in FR15 (English/Hindi/Telugu, labeled fallback).

**Intent**
Applies ADR-010's multilingual requirement to the professional-profile entity, consistent with FR15's business-profile treatment.

**Success outcome**
Same as FR15, applied to `ProfessionalProfile`.

**Failure / edge outcome**
Same fallback behavior as FR15 — labeled, never silent.

**Acceptance criteria**
- [ ] Identical acceptance criteria to FR15, scoped to `ProfessionalProfile` fields.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · Reuses FR15's DEC-001 reasoning directly; no new judgment call introduced by applying it to a second entity type.

**Assumptions**
- None beyond FR15's precedent.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR26 — Search and Browse by Category, Service, Location, Keyword
**Traces from:** BR04
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a member enters a search query or applies browse filters (category, service type, location, keyword), the system shall return matching `BusinessListing`s and `ProfessionalProfile`s using the shared Search Service integration (ADR-007) within 2 seconds under normal load.

**Intent**
Delivers BR04's core proposed outcome as the primary discovery mechanism.

**Success outcome**
Relevant results returned within the performance target, correctly scoped to the filters applied.

**Failure / edge outcome**
If the query returns zero results, the system shows a clear "no matches" state with suggested filter relaxation (e.g., "try removing the location filter") rather than a blank page with no guidance — this is the discovery-side equivalent of a dead end and must have a recovery path.

**Acceptance criteria**
- [ ] Search/browse responds within 2 seconds under normal load (measurable target carried from BR04).
- [ ] Zero-result state offers at least one actionable next step, not a blank page.
- [ ] Uses the shared Search Service pattern (ADR-007), not a bespoke stack.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of zero search results, facing "blank no-results page" versus "no-results page with actionable filter-relaxation suggestions," we chose the actionable version, to achieve genuine discovery usefulness rather than a technically-correct but unhelpful dead end, accepting the added UI/logic complexity of generating relevant relaxation suggestions.

**Assumptions**
- "Normal load" performance baseline is a Tech Reqs/Security & Performance step concern for exact thresholds under stress; the 2-second figure here is BR04's own stated measurable target carried forward as-is.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): spot-checked directly — the zero-result recovery-path guarantee is a genuine, non-trivial failure-mode design, not a token line. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR27 — Browse and Filter Combinations
**Traces from:** BR04
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a member applies more than one filter simultaneously (e.g., category + location + verification status), the system shall combine filters with AND logic across filter types and OR logic within a multi-select filter (e.g., multiple categories selected).

**Intent**
Defines the specific, testable combination semantics BR04's browse capability needs — without this, "browse by category, service, location" is ambiguous about how filters interact.

**Success outcome**
Combined filters return the correctly-intersected result set.

**Failure / edge outcome**
If a filter combination legitimately has zero matches, this is a valid (not erroneous) empty state, handled per FR26's zero-result guidance.

**Acceptance criteria**
- [ ] Cross-filter-type combination is AND; within-filter-type multi-select is OR.
- [ ] Filter state persists across pagination within the same search session.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of undefined multi-filter combination logic, facing several plausible semantics (all-OR, all-AND, mixed), we chose the standard AND-across-types/OR-within-type convention, to achieve predictable, industry-standard filter behavior members already expect from other search UIs, accepting no real downside since this is the de facto standard pattern.

**Assumptions**
- None; this fills an ambiguity gap BR04 itself left open at the coarse BR level, appropriately resolved at FR granularity.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR28 — Relevance Ranking Excluding Payment-Only Signals
**Traces from:** BR04
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When the system ranks organic (non-promoted) search/browse results, the system shall compute rank using relevance-to-query, verification status, quality signals (reputation, per BR07), and capability-match signals, and shall never use payment/promotion status as a ranking input for organic result order.

**Intent**
Delivers BR04's Fair Opportunity constraint (Master PRD §8.3/§24) as a concrete, testable ranking-input rule.

**Success outcome**
Organic ranking demonstrably excludes payment as an input (verifiable via ranking-function audit).

**Failure / edge outcome**
If a promoted listing also happens to be highly relevant, it may appear high in organic rank on its own merits, but the system must not artificially boost it beyond what its organic signals justify — promotion's actual visibility mechanism is a separate, clearly labeled placement (BR07/FR53), not a hidden organic-rank boost.

**Acceptance criteria**
- [ ] Ranking function's input parameters are documented and auditable; "payment/promotion status" is absent from the organic-rank formula.
- [ ] A promoted listing's organic rank position, if measured independently of its promoted placement, matches what its non-payment signals alone would produce.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of a promoted listing's organic rank, facing "let promotion slightly boost organic rank too" versus "keep organic rank entirely independent of promotion," we chose full independence, to achieve an auditable, unambiguous Fair Opportunity guarantee (Master PRD §8.3/§59) rather than a blended system that's hard to verify from outside, accepting that a promoted business gets no organic-ranking benefit from its purchase — only the separate, clearly-labeled promoted placement (BR07).

**Assumptions**
- None beyond BR04's own explicit constraint.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed — auditability claim independently confirmed as testable (documented ranking-input parameter list). Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR29 — Exclude Expired/Inactive Listings from Results
**Traces from:** BR04
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When the search index is queried, the system shall exclude any listing/profile whose operating status (FR17) is closed, whose verification status is `Rejected`, or whose promotion/active window (if applicable) has lapsed without renewal, per `VYAPAR_SEARCH_INDEX_REFRESH_INTERVAL_SECONDS`.

**Intent**
Delivers BR04's Information Lifecycle constraint (Master PRD §15) as a concrete index-freshness rule.

**Success outcome**
Index never returns a stale/inactive listing beyond the defined refresh interval.

**Failure / edge outcome**
If the search index lags behind a real-time status change (e.g., a business closes mid-session), the system bounds the maximum staleness window to the configured refresh interval rather than leaving it indefinite — an SLA-bounded staleness window is an acceptable, disclosed trade-off; unbounded staleness is not.

**Acceptance criteria**
- [ ] Closed/rejected/lapsed listings are excluded from index results within the configured refresh interval.
- [ ] Refresh interval value is a named, documented config item, not an undocumented implementation detail.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of index freshness, facing "real-time synchronous re-index on every status change" versus "periodic refresh on a bounded interval," we chose a bounded periodic refresh, to achieve a workable performance trade-off consistent with the shared Search Service pattern (ADR-007), accepting a small, disclosed staleness window rather than paying the cost of fully synchronous re-indexing on every write.

**Assumptions**
- `VYAPAR_SEARCH_INDEX_REFRESH_INTERVAL_SECONDS` recorded as a new config placeholder (default 60s) pending Tech Reqs-step performance tuning.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed; config placeholder confirmed present in `config/vyapar.config.example.md`. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR30 — Multilingual Search Query Support
**Traces from:** BR04
**Traced to:** (populated later)
**Priority:** Should
**Status:** Ready for Review
**Confidence:** Medium — cross-language semantic search depth deferred to Tech Reqs; this FR guarantees same-language matching only, flagged explicitly.

**Requirement (ISO 29148 form)**
When a member submits a search query in English, Hindi, or Telugu, the system shall match against listing/profile content authored in that same language, per ADR-010's multilingual requirement.

**Intent**
Ensures BR04's discovery capability actually works for non-English-first members, consistent with the platform's multilingual requirement.

**Success outcome**
A Telugu-language query matches Telugu-authored content correctly.

**Failure / edge outcome**
Cross-language matching (a Hindi query matching English-only-authored content) is explicitly out of scope for this FR — flagged as a Should-priority enhancement, not a Must, since it requires semantic/translation-layer search infrastructure beyond this pipeline stage's scope; same-language matching is the Must-level guarantee.

**Acceptance criteria**
- [ ] Query language is correctly detected or explicitly selected by the member.
- [ ] Same-language query-to-content matching works for all three launch languages.
- [ ] Cross-language matching is documented as an explicit non-goal for this FR, not silently absent.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of scoping multilingual search, facing "full cross-language semantic search at launch" versus "same-language matching only, defer cross-language," we chose the narrower same-language scope for V1, to achieve a feasible V1 build within the shared Search Service's stated capability (ADR-007, Postgres full-text search), accepting that a Hindi-speaking member searching in Hindi will not find English-only-authored listings until a later semantic-search capability ships.

**Assumptions**
- Assumed the shared Search Service's V1 capability (Postgres full-text search per ADR-007) does not include cross-language semantic matching; if Tech Reqs step finds otherwise, this FR's scope can be widened then.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed — Should-priority scope-limitation (same-language only) explicitly documented as a non-goal, not a silent gap. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR31 — Visually Distinguish Promoted from Organic Results
**Traces from:** BR04
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When search/browse results include one or more promoted listings (BR07), the system shall render each promoted listing with a persistent, unambiguous "Promoted"/"Sponsored" label distinct from organic result styling, at every position it appears.

**Intent**
Cross-references BR07's promotion capability into BR04's discovery surface, since BR04 itself names this as an explicit constraint (promotion never blended silently into organic ranking).

**Success outcome**
Every promoted result is labeled, at every occurrence, including repeated appearances across paginated result sets.

**Failure / edge outcome**
If a technical error would cause a promoted listing to render without its label (e.g., a caching bug), the system treats this as a hard rendering defect blocking release, not a cosmetic issue — see also FR53's related acceptance criterion for the promotion-owning side of this same guarantee.

**Acceptance criteria**
- [ ] 100% of promoted listings show the label at every appearance (measurable target carried from BR07).
- [ ] Label persists across pagination/infinite-scroll, not just the first page.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of where this labeling requirement is owned, facing "duplicate the full promotion logic in BR04 versus reference BR07's requirement directly," we chose cross-reference over duplication, to achieve BR04's own quality-gate rule against duplicate/overlapping FRs, accepting that BR04's FR31 and BR07's FR53 must be read together to see the complete guarantee.

**Assumptions**
- None beyond BR04's and BR07's own explicit constraints.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): FR31↔FR53 cross-reference independently re-checked — each states one half of a single guarantee from a different owning angle, not a duplicate. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR32 — Dashboard Read Subset for Cross-Module Surfacing
**Traces from:** BR04
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When MOD05 Dashboard surfaces Vyapar content in its own cross-module view, the system shall provide a read-only subset of discovery results via the in-process contract, without exposing Vyapar's internal ranking-function weights or implementation details, and without Dashboard implementing its own competing version of Vyapar's in-module ranking logic.

**Intent**
Enforces BR04's explicit boundary that Dashboard's fair-exposure engine is a separate concern from Vyapar's own in-module ranking.

**Success outcome**
Dashboard renders a correct, current subset of Vyapar results without duplicating or reverse-engineering Vyapar's ranking algorithm.

**Failure / edge outcome**
If Dashboard's own fair-exposure engine needs a ranking-relevant signal (e.g., verification status, reputation score) that isn't in the current contract, that is a contract-extension request (per FR19's precedent), not a justification for Dashboard to compute its own parallel ranking of Vyapar content.

**Acceptance criteria**
- [ ] Dashboard's rendering never re-derives or replicates Vyapar's own relevance-ranking formula.
- [ ] Contract exposes only the fields Dashboard actually needs, not the full internal ranking implementation.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of Dashboard needing a ranking-relevant signal not yet exposed, facing "expose full ranking internals" versus "expose only specific named fields via contract-extension requests as needed," we chose the narrower, request-driven exposure, to achieve ARCHITECTURE.md's own explicit warning against conflating Vyapar's and Dashboard's two distinct ranking concerns, accepting slower iteration when Dashboard's needs evolve.

**Assumptions**
- None beyond BR04's and ARCHITECTURE.md's own explicit boundary statement.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes — indirect (Dashboard's own end users) |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR33 — Initiate a Partnership Request
**Traces from:** BR05
**Traced to:** (populated later)
**Priority:** Should
**Status:** Ready for Review
**Confidence:** Medium — inherited from BR05's own Medium confidence on partnership-record mechanics.

**Requirement (ISO 29148 form)**
When a business/professional discovers another verified business/professional through Vyapar (BR04) and both parties meet the minimum verification level (`VYAPAR_MIN_PARTNERSHIP_VERIFICATION_LEVEL`), the system shall allow the initiating party to create a `Partnership` request specifying its type (supplier, referral, joint service) and a message to the recipient.

**Intent**
Delivers BR05's core proposed outcome — structured B2B relationship formation distinct from informal networking.

**Success outcome**
Request created in `Requested` status, recipient notified (FR37).

**Failure / edge outcome**
If either party falls below the minimum verification level, the system blocks request creation with a clear reason ("both parties must be at least Level-2 verified to form a partnership") rather than allowing the request and failing silently later.

**Acceptance criteria**
- [ ] Partnership type is a required, enumerated field (not free text only).
- [ ] Verification-level check happens before request creation, not after.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of what verification level is required to form a partnership, facing "Level-3 (full Vyapar verification)" versus "Level-2 (identity, not full business/credential verification)," we chose Level-2 as the minimum, to achieve BR05's own stated affected-systems note ("both parties must be at least Level-2 verified"), accepting that a partnership could theoretically form between two identity-verified-but-not-yet-fully-business-verified parties — an acceptable risk since BR05 explicitly excludes financial/contractual enforcement from its own scope.

**Assumptions**
- `VYAPAR_MIN_PARTNERSHIP_VERIFICATION_LEVEL` recorded as a new config placeholder set to `Level-2`, directly reflecting BR05's own stated affected-systems constraint.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): spot-checked directly — verification-level failure path genuinely blocks request creation before it exists, not a post-hoc rejection. Config placeholder confirmed present. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR34 — Accept or Decline a Partnership Request
**Traces from:** BR05
**Traced to:** (populated later)
**Priority:** Should
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a recipient views a `Requested` partnership, the system shall allow them to accept or decline it, transitioning status to `Active` (on accept) or `Declined` (on decline), and notify the initiator of the outcome via the shared Notification Service.

**Intent**
Implements BR05's measurable target of a clear request→response lifecycle.

**Success outcome**
Status transitions correctly; both parties see the current state.

**Failure / edge outcome**
If the recipient never responds, the request remains `Requested` indefinitely rather than auto-expiring silently — the initiator can see it's still pending and choose to withdraw it (FR39-adjacent), but the system does not invent a fake "expired" status without an explicit business rule for it (none was specified in BR05).

**Acceptance criteria**
- [ ] Accept/decline are the only two direct member-initiated transitions from `Requested`.
- [ ] Both parties are notified of the response.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of an unanswered request, facing "auto-expire after N days" versus "remain open indefinitely until explicitly withdrawn," we chose remaining open, to achieve conservatism (BR05 didn't specify an expiry rule, and inventing one risks contradicting a future, more-informed decision), accepting that a stale unanswered request could sit indefinitely — mitigated by giving the initiator an explicit withdraw action (FR39) rather than relying on auto-expiry.

**Assumptions**
- None beyond BR05's own stated lifecycle (requested → accepted/declined → active/ended).

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed — no-invented-expiry-rule judgment call independently re-confirmed as conservative and appropriate, not an oversight. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR35 — Partnership Status Lifecycle Visibility
**Traces from:** BR05
**Traced to:** (populated later)
**Priority:** Should
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When either party to a `Partnership` views their profile or the partnership record, the system shall display its current lifecycle status (requested / accepted / declined / active / ended) identically to both parties at all times.

**Intent**
Delivers BR05's measurable target that both parties can see current partnership status — a shared, not per-party-divergent, view of truth.

**Success outcome**
Both parties always see the same status value.

**Failure / edge outcome**
If a status-changing action is in flight (e.g., one party just clicked "end partnership"), the system uses a single authoritative status field with no read-replica lag exposed to either party — no scenario should exist where party A sees "Active" and party B simultaneously sees "Ended" for the same record.

**Acceptance criteria**
- [ ] Single source of truth for partnership status, read identically by both parties.
- [ ] No party-specific status override exists.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of potential read-lag between two parties' views, facing "accept eventual-consistency lag" versus "guarantee identical reads," we chose to require identical reads (single authoritative field, no per-party cache divergence tolerated for this specific field), to achieve BR05's own explicit "both parties able to see current status" requirement, accepting a small added consistency-engineering requirement at Tech Reqs step.

**Assumptions**
- None beyond BR05's own stated measurable target.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR36 — Enforce Minimum Verification Level for Both Parties
**Traces from:** BR05
**Traced to:** (populated later)
**Priority:** Should
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When either party's verification level drops below `VYAPAR_MIN_PARTNERSHIP_VERIFICATION_LEVEL` after a partnership is already `Active` (e.g., due to a failed re-verification, FR08), the system shall flag the existing partnership as `At Risk` and notify both parties, without unilaterally terminating it.

**Intent**
Extends FR33's entry-gate check to the ongoing lifecycle — a partnership shouldn't silently continue to display full trust signals if one party's underlying verification later lapses.

**Success outcome**
Both parties are informed of the changed status; partnership continues to exist (they may choose to end it themselves, FR39) but with an honest risk flag.

**Failure / edge outcome**
The system does not auto-terminate the partnership on its own initiative, since BR05 explicitly scopes out contractual enforcement — that decision belongs to the parties themselves, not the platform.

**Acceptance criteria**
- [ ] `At Risk` flag appears on the partnership record for both parties within the same operational day as the triggering verification change.
- [ ] System never auto-terminates a partnership without an explicit party action.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of a mid-partnership verification-level drop, facing "auto-terminate the partnership" versus "flag At Risk, let parties decide," we chose flagging over auto-termination, to achieve consistency with BR05's own explicit scoping-out of contractual enforcement (the platform records status, it doesn't adjudicate the relationship), accepting that an at-risk partnership could remain nominally active until a party acts.

**Assumptions**
- None beyond BR01's re-verification mechanism (FR08) as the triggering event.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR37 — Notify Parties of Partnership Request/Response
**Traces from:** BR05
**Traced to:** (populated later)
**Priority:** Should
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a partnership request is created, accepted, declined, or ended, the system shall send a notification to the affected party via the shared Notification & Communication Service (ADR-006), without Vyapar building or maintaining its own notification channel.

**Intent**
Enforces BR05's ADR-006 constraint and gives FR33/FR34/FR39 their actual delivery mechanism.

**Success outcome**
Notification delivered through the shared broker for every lifecycle transition.

**Failure / edge outcome**
If the shared Notification Service is unavailable, the lifecycle transition itself still completes and is recorded (the partnership record is the source of truth) — a downstream notification outage must never block or roll back the underlying state change.

**Acceptance criteria**
- [ ] All four lifecycle transition types (request, accept, decline, end) trigger a notification event.
- [ ] Notification delivery failure does not roll back the state transition.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of a notification-service outage during a lifecycle transition, facing "roll back the transition until notification succeeds" versus "complete the transition regardless, notification is best-effort," we chose completing the transition regardless, to achieve correctness of the actual business state (the partnership existing is the important fact, notification is a courtesy layer on top), accepting that a party might learn of a change later than the event itself occurred.

**Assumptions**
- None beyond BR05's own stated ADR-006 constraint.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR38 — Display Active Partnerships on Both Profiles
**Traces from:** BR05
**Traced to:** (populated later)
**Priority:** Should
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a `Partnership` reaches `Active` status, the system shall display it (partner name, type, since-date) on both parties' profile pages, visible to any member viewing either profile.

**Intent**
Delivers BR05's proposed outcome of visible, mutually-acknowledged partnerships as a trust signal.

**Success outcome**
Partnership appears symmetrically on both profiles.

**Failure / edge outcome**
If one party later chooses to end the partnership (FR39), it is removed from active display on both profiles simultaneously — an ended partnership cannot appear active on only one side.

**Acceptance criteria**
- [ ] Active partnerships render identically (symmetric) on both parties' profiles.
- [ ] Ending a partnership removes it from active display on both sides atomically.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of display symmetry, facing "let each party control their own display of the partnership" versus "single shared, symmetric display," we chose the shared symmetric display, to achieve BR05's own stated "visible on both parties' profiles once accepted," which implies a single fact rather than two independently-controlled claims, accepting that neither party can unilaterally hide an active partnership without ending it outright.

**Assumptions**
- None beyond BR05's own stated proposed outcome.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR39 — End or Withdraw a Partnership
**Traces from:** BR05
**Traced to:** (populated later)
**Priority:** Should
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When either party to a `Requested` or `Active` partnership chooses to withdraw or end it, the system shall transition the record to `Ended` (from Active) or effectively withdraw the request (from Requested), record the acting party and timestamp, and remove it from both parties' active display (FR38).

**Intent**
Completes BR05's full lifecycle (requested → accepted/declined → active/ended) with the one remaining transition not yet covered by FR33/FR34.

**Success outcome**
Partnership correctly transitions to its terminal state; both parties see the updated status.

**Failure / edge outcome**
Either party — not just the original initiator — can end an `Active` partnership, since a one-sided-only exit right would misrepresent a mutual business relationship as controlled by whoever initiated it.

**Acceptance criteria**
- [ ] Either party can trigger the end/withdraw transition, not just the initiator.
- [ ] Acting party and timestamp are recorded for audit/history.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of who may end an active partnership, facing "only the original initiator" versus "either party," we chose either party, to achieve fairness in what is by definition a two-sided relationship (an accepted partnership has no single "owner"), accepting no meaningful downside since this is the intuitively correct behavior for a bilateral record.

**Assumptions**
- None beyond BR05's own stated lifecycle completeness requirement.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed — completes BR05's lifecycle with no gap. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR40 — Post a Job or Business Opportunity
**Traces from:** BR06
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a verified business/employer creates a `JobOpportunity` or `BusinessOpportunity`, the system shall capture role/opportunity type, requirements, location, and compensation/terms where applicable, and require the posting business/professional to be at least `Verified` (not merely `Pending`) before publication.

**Intent**
Delivers BR06's core proposed outcome while enforcing that opportunities — unlike draft profiles — cannot appear publicly without passing BR01's gate, since an opportunity is an active solicitation, not a passive presence.

**Success outcome**
Opportunity created and published, visible in discovery/browse.

**Failure / edge outcome**
If the posting party is not yet `Verified`, the opportunity can be drafted but not published, with a clear message directing the member to complete verification (FR01) first.

**Acceptance criteria**
- [ ] Only `Verified` posters can publish an opportunity (draft-only for unverified/pending posters).
- [ ] Required fields (type, requirements, location) are enforced at publish time.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of who may publish an opportunity, facing "allow Pending posters to publish" versus "require full Verified status," we chose requiring Verified, to achieve a stricter bar than mere profile existence (BR02 allows Pending profiles to exist; an active opportunity solicitation is a higher-stakes public action than a passive listing), accepting that a newly-onboarding business must wait through verification before it can post opportunities, consistent with BR01 being a precondition for "promotion eligibility" (BR07) — opportunity publication is treated with the same seriousness.

**Assumptions**
- None beyond BR06's own stated model.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR41 — Edit and Close an Opportunity
**Traces from:** BR06
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a poster edits or closes their own `JobOpportunity`/`BusinessOpportunity`, the system shall apply the update immediately and, on close, exclude it from discovery/browse (BR04) while retaining historical enquiries against it.

**Intent**
Gives posters lifecycle control and keeps discovery results current (Information Lifecycle principle, shared with FR17/FR29).

**Success outcome**
Edited opportunity reflects updates immediately; closed opportunity disappears from active discovery but its enquiry history remains accessible to the poster.

**Failure / edge outcome**
If a poster attempts to close an opportunity with unresolved open enquiries, the system allows the close but flags the unresolved enquiries so they aren't silently lost/forgotten — closing the opportunity must not implicitly close its enquiries without the poster's awareness.

**Acceptance criteria**
- [ ] Closed opportunities are excluded from BR04 discovery.
- [ ] Unresolved enquiries against a newly-closed opportunity are explicitly flagged to the poster, not silently orphaned.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of closing an opportunity with open enquiries, facing "auto-close all enquiries too" versus "close the opportunity, flag orphaned open enquiries," we chose flagging over auto-closing, to achieve BR06's own stated enquiry status lifecycle (submitted/responded/closed) being an explicit poster decision, not an implicit side effect, accepting the added UI complexity of a "you have N unresolved enquiries" flag at close time.

**Assumptions**
- None beyond BR06's own stated lifecycle model.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): spot-checked directly — the unresolved-enquiry flagging failure path genuinely present, not just claimed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR42 — Submit a Business Enquiry
**Traces from:** BR06
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When any member submits a `BusinessEnquiry` against a `BusinessListing`, `ProfessionalProfile`, or `JobOpportunity`/`BusinessOpportunity`, the system shall capture the enquiry content, the specific target entity referenced, and the submitting member's identity, and set its status to `Submitted`.

**Intent**
Delivers BR06's structured lead/application mechanism as the platform's action pathway on top of discovery (BR04).

**Success outcome**
Enquiry recorded, linked to its target, status `Submitted`, poster notified (FR44).

**Failure / edge outcome**
If the target entity is closed/inactive at the moment of submission (a race condition between browsing and submitting), the system rejects the submission with a clear "this opportunity/listing is no longer accepting enquiries" message rather than silently accepting an enquiry against a dead target.

**Acceptance criteria**
- [ ] Every enquiry references exactly one target entity.
- [ ] Submission against a closed/inactive target is rejected with a clear reason at submission time.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of "job application" versus "general commercial lead" under one `BusinessEnquiry` shape, facing "one unified enquiry entity" versus "two separate entity types," we chose one unified entity (per BR06's own recorded assumption and modules.md's singular `BusinessEnquiry` data-ownership line), to achieve consistency with the already-settled data model, accepting that some fields (e.g., "expected start date" for a job vs. "quantity needed" for a commercial lead) may need to be optional/conditional rather than universally required — a schema detail for Tech Reqs step, not a scope change here.

**Assumptions**
- Carries forward BR06's own recorded assumption verbatim rather than re-deciding it.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): spot-checked directly — the race-condition failure path (closed target at submission time) is a genuine, non-trivial edge case correctly handled. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR43 — Enquiry Status Lifecycle
**Traces from:** BR06
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When the poster (recipient) of a `BusinessEnquiry` takes action on it, the system shall transition its status from `Submitted` to `Responded` (poster has replied) to `Closed` (poster or submitter marks it resolved/no longer active), visible to both the submitter and the poster at every stage.

**Intent**
Delivers BR06's measurable target of a clear enquiry status.

**Success outcome**
Status transitions correctly and is visible to both parties.

**Failure / edge outcome**
If the poster never responds within `VYAPAR_ENQUIRY_RESPONSE_SLA_DAYS`, the enquiry remains visibly `Submitted` (not auto-escalated to a false status) but the submitter is shown how long it's been outstanding, so they can judge for themselves whether to follow up elsewhere — consistent with FR34's precedent of not inventing an unspecified auto-expiry rule.

**Acceptance criteria**
- [ ] Three-state lifecycle (Submitted/Responded/Closed) implemented exactly as specified, no additional undocumented states.
- [ ] Elapsed time since submission is visible to the submitter for outstanding enquiries.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of a poster who never responds, facing "auto-close after SLA" versus "remain Submitted, show elapsed time," we chose remaining Submitted with elapsed-time transparency, mirroring FR34's reasoning, to achieve honesty about actual poster responsiveness rather than a fabricated status, accepting that a genuinely abandoned enquiry could sit in `Submitted` indefinitely without an automatic cleanup.

**Assumptions**
- `VYAPAR_ENQUIRY_RESPONSE_SLA_DAYS` recorded as a new config placeholder (default 3 days) purely as an elapsed-time transparency threshold, not an auto-transition trigger.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed; config placeholder confirmed present. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR44 — Notify Poster of New Enquiry
**Traces from:** BR06
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a new `BusinessEnquiry` is submitted, the system shall notify the poster via the shared Notification & Communication Service within the same operational transaction as the enquiry's creation.

**Intent**
Delivers BR06's measurable target that the poster is notified of new enquiries.

**Success outcome**
Notification dispatched to the shared broker immediately on enquiry creation.

**Failure / edge outcome**
Mirrors FR37's reasoning — a notification-dispatch failure never rolls back the enquiry's own creation; the enquiry record remains the source of truth and is independently visible to the poster on next login regardless of notification delivery success.

**Acceptance criteria**
- [ ] Notification dispatch is attempted for 100% of new enquiries.
- [ ] Notification failure does not roll back or hide the enquiry record itself.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · Reuses FR37's reasoning directly (notification is best-effort, underlying state is authoritative) applied to the enquiry entity — no new judgment call introduced.

**Assumptions**
- None beyond BR06's own stated measurable target.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR45 — Opportunity Open/Closed Status Display
**Traces from:** BR06
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When any member views a `JobOpportunity`/`BusinessOpportunity`, the system shall display its current status (`Open`/`Closed`) prominently, and disable the enquiry-submission action (FR42) on any listing/opportunity page rendering a `Closed` status.

**Intent**
Prevents the exact race condition FR42 already guards against at the submission layer, by also preventing the action from being offered at all once closed — a defense-in-depth pairing (UI-level prevention + submission-layer rejection).

**Success outcome**
Closed opportunities visibly show `Closed` and offer no enquiry action.

**Failure / edge outcome**
If a member has an already-open enquiry-submission form loaded when the opportunity closes, submission is still rejected server-side (FR42), even though the UI-level prevention (this FR) didn't catch it in time — the two layers are complementary, neither is a substitute for the other.

**Acceptance criteria**
- [ ] Closed opportunities render with no visible/enabled enquiry-submission control.
- [ ] Server-side rejection (FR42) remains the authoritative guarantee regardless of UI state.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of preventing enquiries against closed opportunities, facing "rely on server-side rejection alone (FR42)" versus "also prevent it at the UI layer," we chose defense-in-depth (both), to achieve a better member experience (no wasted effort filling a form that will be rejected) on top of the already-guaranteed server-side correctness, accepting the minor added UI-state-management complexity.

**Assumptions**
- None beyond BR06's own stated status field.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR46 — Dashboard Read-Only Surfacing of Opportunities
**Traces from:** BR06
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When MOD05 Dashboard surfaces Vyapar opportunities cross-module, the system shall provide read-only access via the in-process contract (per ARCHITECTURE.md), consistent with FR19's pattern for listings, with no write path from Dashboard to `JobOpportunity`/`BusinessOpportunity`.

**Intent**
Extends FR19's Dashboard read-only guarantee to the opportunity entity, since BR06 separately names Dashboard as an affected system.

**Success outcome**
Dashboard renders opportunities correctly without any write capability.

**Failure / edge outcome**
Mirrors FR19 — a missing field is a contract-extension request, not a direct schema read.

**Acceptance criteria**
- [ ] Identical acceptance criteria to FR19, scoped to the opportunity entities.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · Reuses FR19's DEC-001 reasoning directly, applied to a second entity type — no new judgment call introduced.

**Assumptions**
- None beyond FR19's precedent.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes — indirect (Dashboard's own end users) |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR47 — Block In-App Payment Collection for Enquiry-Resulting Transactions
**Traces from:** BR06
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When any enquiry, opportunity, or listing interaction would otherwise lead to a commercial transaction, the system shall not offer or process any in-app payment-collection mechanism for that transaction in V1, and shall instead direct both parties to complete payment off-platform.

**Intent**
Operationalizes BR06's explicit V1 constraint (no in-app payment; deferred to MOD06 Payment Services integration) as a hard, testable negative requirement — the kind of requirement most likely to be silently violated by well-intentioned scope creep during implementation if not stated explicitly.

**Success outcome**
No payment UI/API surface exists anywhere in Vyapar's V1 enquiry/opportunity flow.

**Failure / edge outcome**
If a future implementation PR attempts to add any payment-collection UI element to this flow before MOD06 integration ships, that is treated as an out-of-scope addition to be rejected at Implementation-review step (Step 9), not silently merged — this FR exists specifically to give that later gate an explicit rule to check against.

**Acceptance criteria**
- [ ] No payment-collection UI/API exists in the V1 Vyapar enquiry/opportunity/listing flow.
- [ ] Any future payment-related PR against this flow references MOD06 integration readiness explicitly before being accepted.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of representing a scope-boundary as a testable requirement, facing "leave it as a documented constraint only" versus "write it as an explicit negative FR with its own acceptance criteria," we chose the explicit negative FR, to achieve a durable, checkable guard against scope creep at later pipeline steps (Implementation, Test Automation), accepting the slightly unusual form of a requirement whose main content is "shall not," which is a deliberate, justified deviation from the standard positive ISO sentence form for exactly this reason.

**Assumptions**
- None beyond BR06's own explicit constraint and modules.md's own out-of-scope line.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): the deliberate ISO-form deviation independently re-examined — this FR is not purely negative (it also carries a positive alternative-action clause, "shall instead direct both parties to complete payment off-platform"), and its justification (durable scope-creep guard, checked at a later implementation-review gate) is genuinely argued rather than a shortcut around the mandatory sentence form. Accepted as a valid, justified exception. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR48 — Submit a Business Review Tied to a Verified Interaction
**Traces from:** BR07
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a member who has an existing `BusinessEnquiry` (or equivalent recorded engagement) against a business/professional wishes to leave feedback, the system shall allow submission of a `BusinessReview` (structured rating plus comment) referencing that specific interaction.

**Intent**
Delivers BR07's interaction-tied review model (DEC-001), the platform's "Evidence Over Rumours" principle (Master PRD §8.4).

**Success outcome**
Review recorded, linked to the specific enquiry/interaction, visible on the business/professional's profile.

**Failure / edge outcome**
If the member has no qualifying recorded interaction with the target, submission is blocked with a clear explanation ("you can review a business after submitting an enquiry to them") rather than a generic permission error.

**Acceptance criteria**
- [ ] Every review references exactly one qualifying interaction record.
- [ ] A member cannot submit more than one review per distinct interaction (prevents duplicate-review inflation).

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of how many reviews one interaction may generate, facing "allow multiple reviews per interaction" versus "one review per interaction," we chose one-per-interaction, to achieve resistance to review-count inflation/manipulation, consistent with BR07's own interaction-tied design intent, accepting that a member with an evolving experience must edit their existing review rather than add a new one for the same interaction.

**Assumptions**
- Carries forward BR07's own recorded DEC-001 directly.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): spot-checked directly — the no-qualifying-interaction failure message is genuinely specific and actionable, not a generic error. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR49 — Prevent Non-Participant Review Submission
**Traces from:** BR07
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a member without any recorded interaction against a given business/professional attempts to submit a `BusinessReview`, the system shall reject the submission at the API layer, independent of any client-side UI restriction.

**Intent**
Makes BR07's anti-manipulation constraint a server-enforced guarantee, not merely a UI convention that a modified client could bypass — the security-relevant counterpart to FR48.

**Success outcome**
Non-participant submission attempts are rejected 100% of the time, regardless of client.

**Failure / edge outcome**
If a legitimate off-platform interaction exists but has no on-platform record, the member genuinely cannot review yet (per BR07's own recorded, accepted trade-off) — this is a known, deliberate limitation, not a bug to work around client-side.

**Acceptance criteria**
- [ ] Server-side validation rejects any review lacking a valid interaction reference, tested independent of client UI.
- [ ] No client-only enforcement path exists as the sole guard.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of where to enforce the interaction-tied requirement, facing "client-side only" versus "server-side, independent of client," we chose server-side enforcement, to achieve a real security/integrity guarantee rather than a bypassable UI convention, accepting the standard engineering cost of server-side validation logic.

**Assumptions**
- None beyond BR07's own stated interaction-tied design.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR50 — Compute and Display Business-Domain Reputation Signal
**Traces from:** BR07
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a business/professional has at least one `BusinessReview`, the system shall compute an aggregate business-domain reputation signal (e.g., average rating, review count) from its own `BusinessReview` records and display it on the profile, updating it as new reviews are submitted.

**Intent**
Delivers BR07's ongoing-reputation proposed outcome, distinct from BR01's point-in-time verification.

**Success outcome**
Aggregate signal displayed and kept current with each new review.

**Failure / edge outcome**
If a business has zero reviews, the system displays a neutral "No reviews yet" state rather than a fabricated zero/default score that could be misread as a poor rating.

**Acceptance criteria**
- [ ] Aggregate updates on every new review submission (no manual recompute needed).
- [ ] Zero-review state is visually distinct from a low-rating state.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of a business with zero reviews, facing "show a default/zero score" versus "show an explicit 'No reviews yet' neutral state," we chose the neutral state, to achieve fairness to newly-onboarded legitimate businesses (a zero/blank numeric score reads as a bad rating, not an absence of data), accepting a slightly more complex display-state model than a single numeric field.

**Assumptions**
- Assumed this FR computes Vyapar's own raw aggregate only, per BR07's own assumption that the shared reputation-aggregation engine's cross-module scoring logic (ADR-005) is a separate, later concern (FR51) — this FR is the source-signal computation, not the platform-wide score.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): spot-checked directly — the "Correct" gate item independently confirmed, since the no-fabricated-score rule is genuinely testable and fair to new entrants. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR51 — Expose BusinessReview Read-Only to the Shared Reputation Engine
**Traces from:** BR07
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When the shared reputation-aggregation engine inside Identity & Trust Service requests business-domain review data, the system shall provide read-only access to `BusinessReview` records via the ADR-005 contract, with Vyapar remaining the sole writer of that entity at all times.

**Intent**
Enforces BR07's ADR-005 constraint (shared engine reads, never writes, `BusinessReview`).

**Success outcome**
Shared engine successfully reads current review data for its own cross-module scoring.

**Failure / edge outcome**
If the shared engine's read request would require a write-back to `BusinessReview` (e.g., a computed engine-side flag), that is rejected at the contract level — no write path from the shared engine into Vyapar's own entity exists under any circumstance.

**Acceptance criteria**
- [ ] No write API from the shared reputation engine to `BusinessReview` exists.
- [ ] Read contract is versioned/documented consistent with ARCHITECTURE.md's ADR-005 resolution.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of the shared engine potentially wanting to write derived data back onto the review record, facing "allow engine write-back for its own computed fields" versus "read-only, no exceptions," we chose strict read-only, to achieve ADR-005's own unambiguous ownership rule, accepting that any engine-side computed value must live in the engine's own storage, not annotate Vyapar's entity.

**Assumptions**
- None beyond ARCHITECTURE.md's own already-settled ADR-005.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes — indirect (platform-wide reputation consumers) |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR52 — Purchase a Promotion
**Traces from:** BR07
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a `Verified` business/professional selects a promotion tier from `VYAPAR_PROMOTION_TIER_CONFIG` and completes purchase (routed through MOD06 Payment Services once integrated), the system shall create a `Promotion` record with its active window (start/end date) and associate it with the purchasing listing/profile.

**Intent**
Delivers BR07's revenue-bearing capability (Master PRD §46) while enforcing that only already-`Verified` entities may purchase (BR01's precondition explicitly named in BR01's proposed outcome).

**Success outcome**
Promotion record created with a defined active window; listing begins appearing in promoted placements (FR31/FR53) from purchase confirmation.

**Failure / edge outcome**
If the purchasing entity is not `Verified` (only `Pending`/`Unverified`), the system blocks the purchase flow entirely with a message directing the member to complete verification first — this is BR01's explicit precondition, not merely a suggestion.

**Acceptance criteria**
- [ ] Only `Verified` listings/profiles can complete a promotion purchase.
- [ ] Promotion record always has a defined, bounded active window (no indefinite/undated promotions).

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of actual payment processing for a promotion purchase, facing "build a V1 stand-in payment path" versus "record the purchase intent and route actual processing through MOD06 once it ships," we chose the latter, to achieve consistency with BR07's own explicit out-of-scope line (payment processing deferred to MOD06 integration), accepting that until MOD06 ships, promotion purchase is either unavailable or uses an interim manual/off-platform payment process — a Tech Reqs-step decision on interim mechanics, not resolved here.

**Assumptions**
- `VYAPAR_PROMOTION_TIER_CONFIG` (already recorded as a placeholder in the config file) is populated with real tier definitions at Tech Reqs step; this FR only requires that tiers exist as a structured, referenceable config, not that specific tiers/pricing are decided here.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): confirmed `VYAPAR_PROMOTION_TIER_CONFIG` exists in `config/vyapar.config.example.md` (recorded at Step 1, correctly referenced here rather than re-created). Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR53 — Enforce 100% Visual Labeling of Promoted Listings
**Traces from:** BR07
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a listing/profile has an active `Promotion`, the system shall render a persistent "Promoted"/"Sponsored" label on that listing/profile in every surface it appears, including Dashboard's read-only rendering, with no configuration path able to disable or hide the label while the promotion is active.

**Intent**
Delivers BR07's explicit 100%-labeling measurable target — the owning-side counterpart to FR31's discovery-surface guarantee.

**Success outcome**
Label appears on 100% of surfaces rendering a promoted entity, verifiable via a cross-surface audit.

**Failure / edge outcome**
If Dashboard's rendering constraints would otherwise omit the label (mirroring FR06's constrained-layout case), the system requires at minimum a distinguishable icon/marker — never full omission, since BR07's measurable target is explicitly "100% ... in every surface, including Dashboard's read-only rendering."

**Acceptance criteria**
- [ ] Cross-surface audit (web, Dashboard) confirms 100% labeling of all active promotions.
- [ ] No admin/config toggle exists to disable the label while a promotion is active.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of whether an admin/config override to hide the promoted label should ever exist (e.g., for a special campaign), facing "allow an override" versus "no override path, ever," we chose no override, to achieve an unconditional guarantee matching BR07's own unconditional measurable target and the platform's Fair Opportunity principle (Master PRD §24/§59), accepting that this removes a degree of commercial flexibility a sales/marketing team might otherwise want.

**Assumptions**
- None beyond BR07's own explicit, unconditional measurable target.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): FR31↔FR53 pairing re-confirmed as complementary, not duplicated. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR54 — Promotion Never Implies or Substitutes for Verification
**Traces from:** BR07
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a `Promotion` is active on any listing/profile, the system shall render its verification-status label (FR06/FR16) independently of and never overridden by the promotion label, such that an `Unverified`/`Pending` entity cannot display any visual signal implying full verification merely by virtue of having purchased a promotion.

**Intent**
Enforces BR07's explicit constraint that promotion must never substitute for or override verification status — the direct guard against a "pay to look verified" failure mode.

**Success outcome**
Verification and promotion labels render as two independent, simultaneously-visible signals; no combination of the two ever implies a verification level higher than the entity's actual status.

**Failure / edge outcome**
Since FR52 already blocks non-Verified entities from purchasing a promotion in the first place, this scenario (a Pending/Unverified entity with an active promotion) should not occur in normal operation — this FR exists as the explicit last-line rendering guarantee in case that upstream gate is ever bypassed (e.g., a data migration, an admin override, a future bug), so the display layer itself never compounds an upstream gap into a user-facing misrepresentation.

**Acceptance criteria**
- [ ] Verification and promotion labels are rendered from independent data fields, never a single combined "trust" field.
- [ ] Even in a hypothetical data-integrity edge case (unverified + promoted), the verification label still renders its true, current status.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of a hypothetical unverified-but-promoted state (should be prevented upstream by FR52, but not provably impossible under all future conditions), facing "trust the upstream gate, no display-layer safeguard" versus "add an independent display-layer guarantee regardless," we chose the independent display-layer guarantee, to achieve defense-in-depth consistent with BR07's own zero-tolerance framing ("must never be allowed"), accepting the modest added rendering-logic complexity of never merging the two signals into one.

**Assumptions**
- None beyond BR07's own explicit constraint.

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed — defense-in-depth rationale independently re-confirmed as sound (guards against upstream FR52 bypass via migration/admin-override/bug). Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR55 — Track Promotion Active Window and Expiry
**Traces from:** BR07
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When a `Promotion`'s active window end-date is reached, the system shall automatically remove the promoted placement and label (FR53) from the listing/profile without requiring manual admin intervention, and shall notify the purchasing party of the expiry with an option to renew.

**Intent**
Delivers BR07's "records that a promotion was purchased and its active window" scope, and the Information Lifecycle principle applied to a commercial artifact.

**Success outcome**
Promotion expires automatically and cleanly; renewal is offered, not forced.

**Failure / edge outcome**
If a renewal payment fails or is not completed before expiry, the listing reverts to organic-only display (FR28) — a lapsed promotion never continues to display promoted placement/labeling past its paid window, regardless of renewal-in-progress state.

**Acceptance criteria**
- [ ] Expiry is system-triggered, no manual step required.
- [ ] Promoted display never persists past the recorded active-window end-date.
- [ ] Renewal is offered as a distinct action, not an automatic re-charge without consent.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of a promotion nearing expiry, facing "auto-renew and re-charge automatically" versus "expire and offer renewal as a separate consented action," we chose the latter, to achieve transparent, consent-based commercial behavior (no surprise charges), accepting that a business that forgets to renew loses promoted placement until they actively renew, a foreseeable and acceptable trade-off against silent auto-billing.

**Assumptions**
- None beyond BR07's own stated scope for this capability (recording purchase/window, not processing payment itself).

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## FR56 — Dashboard Read-Only Rendering of Reputation and Promotion Status
**Traces from:** BR07
**Traced to:** (populated later)
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Requirement (ISO 29148 form)**
When MOD05 Dashboard reads a Vyapar listing/profile's reputation signal (FR50) or promotion status (FR52), the system shall provide both via the in-process read-only contract, preserving the organic-vs-promoted visual distinction (FR53) that Dashboard itself did not create and must not alter.

**Intent**
Extends FR19/FR46's Dashboard read-only pattern specifically to reputation and promotion data, since BR07 separately names Dashboard as an affected system with an explicit obligation to preserve, not weaken, the promoted/organic distinction.

**Success outcome**
Dashboard renders both signals correctly and preserves the visual distinction rule.

**Failure / edge outcome**
If Dashboard's own layout constraints would make preserving the full distinction difficult, that is a Dashboard-side UI-step problem to solve within its own constraints — it is never resolved by relaxing Vyapar's contract to omit the promotion flag, since that would recreate exactly the "pay to look verified/organic" risk FR54 exists to prevent.

**Acceptance criteria**
- [ ] Dashboard's contract read always includes both the reputation signal and promotion-active flag as non-omittable fields.
- [ ] Dashboard's own rendering choices cannot be used to justify weakening Vyapar's contract guarantee.

**Quality gate (ISO 29148)**
Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ ·
Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of Dashboard's own layout constraints potentially conflicting with the full labeling requirement, facing "relax Vyapar's contract to accommodate Dashboard's layout" versus "keep the contract fixed, push the layout problem to Dashboard's own UI step," we chose keeping the contract fixed, to achieve the same non-negotiable guarantee FR06/FR53 already established, accepting that Dashboard's own UI-step work may need extra design effort to fit the requirement rather than getting an easier contract.

**Assumptions**
- None beyond BR07's own explicit statement that Dashboard "must preserve the organic-vs-promoted visual distinction it did not create."

**Handoff readiness**
| UX needs | Present |
|---|---|
| User/role | Yes — indirect (Dashboard's own end users) |
| Trigger condition | Yes |
| Success + failure outcomes | Yes |

**Review history**
- 2026-09-06 · functional-requirements-reviewer (autonomous mode): reviewed — final FR in the set; confirms full 56/56 coverage. Approved.

**Approval:** Product Manager / BA — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## Definition of Done check

- Every BR in Step 1 has produced at least one FR — Pass (see Coverage
  check table; 56 FRs total across all 7 BRs, no blank rows; independently
  cross-checked against `01-business-requirements.md`'s own `Traced to:`
  fields, not just this file's own claim).
- Every FR passes the nine-point gate and uses the ISO sentence form — Pass
  for all 56, independently re-checked on a representative sample across
  all 7 BRs (not merely re-confirmed from the producing agent's own
  checkmarks), with one deliberate, explicitly-flagged deviation (FR47's
  negative "shall not" form, re-examined and confirmed as a genuine,
  argued exception — a scope-boundary guard with its own positive
  alternative-action clause — not a forced-fit rewrite or a lazy
  shortcut).
- Every FR's Handoff readiness table is fully "Yes" — Pass (all 56 confirm
  user/role, trigger condition, and success+failure outcomes; spot-checked
  a representative sample directly in prose, not just the table's own
  claim, per this gate's elevated-risk instruction that a missing failure
  path is the most common silent gap at this step).
- No open blockers — Pass.
- Product Manager / BA approval — Pass. All 56 FRs marked Approved by
  reviewer-agent (autonomous mode) per this project's autonomous-mode
  pipeline. Status changed **Ready for Review** → **Sealed**.

## Config additions made during this step

Four new placeholder entries added to
`/modules/MOD01-vyapar/config/vyapar.config.example.md` (not left as open
questions, per standing autonomous-execution instruction):
- `VYAPAR_REVERIFICATION_CADENCE_DAYS` (default 180) — FR08's periodic
  re-verification trigger.
- `VYAPAR_MIN_PARTNERSHIP_VERIFICATION_LEVEL` (default `Level-2`) — FR33/
  FR36's partnership eligibility gate.
- `VYAPAR_ENQUIRY_RESPONSE_SLA_DAYS` (default 3) — FR43's elapsed-time
  transparency threshold (not an auto-transition trigger).
- `VYAPAR_SEARCH_INDEX_REFRESH_INTERVAL_SECONDS` (default 60) — FR29's
  index-staleness bound.

All four independently confirmed present in the config file during this
review, correctly cross-referenced from their originating FRs.

## Reviewer notes

Independent review performed as the sole reviewer (autonomous mode, no
human check). Verified the following against the actual artifacts, not
merely against this file's own self-reported claims:

1. **Coverage.** Read `01-business-requirements.md` directly and confirmed
   each of BR01–BR07's own `Traced to:` field lists exactly the FR numbers
   this file's Coverage check table claims, in both directions. No BR is
   missing an FR; no FR traces to a nonexistent BR.

2. **ISO 29148 sentence form.** All 56 FRs open with a conditional clause
   ("When ..."/"When ... reaches ...") followed by "the system shall
   [action] [object] [constraint]." FR47 is the one deliberate deviation
   (negative "shall not" form) — re-examined specifically because a
   negative-form exception is exactly the kind of thing that could be a
   lazy shortcut rather than a genuine argued case. It holds up: FR47 also
   carries a positive alternative-action clause ("shall instead direct
   both parties to complete payment off-platform"), and its Decisions
   section argues a specific, non-generic rationale (a durable, checkable
   guard against scope creep at a later, named pipeline gate — Step 9
   Implementation review), not merely "this was hard to phrase
   positively."

3. **Handoff readiness.** Spot-checked FR01, FR02, FR06, FR07, FR08, FR12,
   FR17, FR23, FR26, FR29, FR33, FR41, FR42, FR48, FR50, FR52, FR54 (a
   sample spanning all 7 BRs, weighted toward FRs with the most
   nontrivial failure paths) by reading the actual Success outcome and
   Failure/edge outcome prose directly, not the Handoff readiness table's
   own "Yes" claims. Every sampled FR's failure/edge path is a genuine,
   specific, testable statement (e.g., FR07's "member-facing status is
   never altered to mask an internal capacity problem," FR42's
   race-condition rejection message, FR54's defense-in-depth guard against
   an upstream-gate bypass) — none is a placeholder or a restatement of
   the success case. No missing failure path found in the sample, which
   is this gate's single most common silent-gap risk.

4. **Nine-point quality gate.** Re-checked FR02, FR04, FR09, FR17, FR27,
   FR28, FR29, FR39, FR48, FR50 independently against their own stated
   Intent/Acceptance-criteria text rather than re-confirming the producing
   agent's checkmarks. All hold up — e.g., FR28's "Verifiable" claim is
   backed by a concrete, auditable acceptance criterion (documented
   ranking-input parameters with payment/promotion status absent), not an
   unfalsifiable assertion.

5. **Set-level gate.** Comprehensive/Consistent/Prioritized/No-duplicates
   all independently re-derived, not just re-read. The two named
   cross-reference pairs (FR31↔FR53, FR22↔FR24) were each read in full to
   confirm they describe one guarantee from two legitimately different
   owning angles, not a hidden duplicate. Priority inheritance was
   checked for every FR that departs from its parent BR's own priority
   (FR18, FR23, FR30 — Should within an otherwise-Must BR) and each has
   its own explicit, argued rationale in its Assumptions/Decisions
   section, not an unexplained downgrade.

6. **Config placeholders.** All four new placeholders this step recorded
   (`VYAPAR_REVERIFICATION_CADENCE_DAYS`,
   `VYAPAR_MIN_PARTNERSHIP_VERIFICATION_LEVEL`,
   `VYAPAR_ENQUIRY_RESPONSE_SLA_DAYS`,
   `VYAPAR_SEARCH_INDEX_REFRESH_INTERVAL_SECONDS`) confirmed present in
   `/modules/MOD01-vyapar/config/vyapar.config.example.md`, along with the
   pre-existing `VYAPAR_PROMOTION_TIER_CONFIG` that FR52 correctly
   references rather than re-creating.

No genuine defect was found rising to a Blocked item — every FR examined,
whether by full read or targeted spot-check, held up under independent
scrutiny. No correction was required in this file (unlike Step 1's BR
review, which found and fixed two citation defects — this step's FRs
carry forward those already-corrected BR citations by reference rather
than re-citing source documents directly, so there was nothing equivalent
to re-verify at this layer). Status changed **Ready for Review** →
**Sealed**; frontmatter `approved: 56`; every FR's Approval line filled in
as `reviewer-agent (autonomous mode)`, 2026-09-06.
