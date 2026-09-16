---
step: 05-test-scenarios
module: MOD01
status: Sealed
approver: Product Manager
updated: 2026-09-14
items: "214 | approved: 214 | blockers: 0"
---

# 05 — Test Scenarios — MOD01 Vyapar

## Revision history

| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-14 | Initial full pass. Read `01-business-requirements.md` (Sealed, 18 BRs), `02-functional-requirements.md` (Sealed, 55 FRs), `03-ux.md` (Sealed, 23 UX items) and `04-ui.md` (Sealed, 23 UI items) in full, plus `docs/PreStartResearch/IMPLEMENTATION-TEST-STANDARDS.md` for the Given/When/Then-mappable Arrange/Act/Assert convention and per-layer mocking rules. Looped FR01→FR55 in numeric order, writing scenarios covering each FR's success outcome, failure/edge outcome, and named UX/UI state, tagging every scenario Unit/Integration/E2E per the test-pyramid discipline. Added 15 explicit INVARIANT-tagged guard scenarios for the 15 standing product invariants named in the brief (three-axes separation, four-document/no-Aadhaar menu, two-state seeking visibility, post-acceptance-only contact, zero-Opportunity Businesses surface, Refer-to-Counsel scope, mandatory source segment, freshness/expiry timers, notification fatigue caps, tokenized payment/idempotency, data-rights SLA + anonymized deletion, minimum-field one-way adjacent contracts, ranking allow-list, FR50 identity consumption, no star ratings). Produced 214 scenarios (TS001–TS214). Authentication (login/signup/OTP-login/session/logout) is out of MOD01 scope per FR50/DEC-001 — no scenario tests a Vyapar-owned login flow; FR07's OTP is tested only as listing-contact verification, and FR50 scenarios test Vyapar's *consumption* of the platform identity contract, never a local auth fallback. Ran the Definition of Done checklist (coverage, distribution ratio, no open blockers) and sealed under the module's standing autonomous-execution mode (2026-09-14). | Principal QA — autonomous execution, 2026-09-14. |

## Coverage check

| Parent FR | Scenarios produced | Layer mix (U/I/E) | Covered |
|---|---|---|---|
| FR01 | TS001–TS004 | 2/2/0 | Yes |
| FR02 | TS005–TS007 | 2/1/0 | Yes |
| FR03 | TS008–TS011 | 1/3/0 | Yes |
| FR04 | TS012–TS015 | 3/0/1 | Yes |
| FR05 | TS016–TS018 | 1/2/0 | Yes |
| FR06 | TS019–TS021 | 1/2/0 | Yes |
| FR07 | TS022–TS025 | 3/1/0 | Yes |
| FR08 | TS026–TS029 | 3/0/1 | Yes |
| FR09 | TS030–TS031 | 1/1/0 | Yes |
| FR10 | TS032–TS035 | 2/2/0 | Yes |
| FR11 | TS036–TS039 | 3/1/0 | Yes |
| FR12 | TS040–TS043 | 3/1/0 | Yes |
| FR13 | TS044–TS047 | 1/3/0 | Yes |
| FR14 | TS048–TS050 | 2/1/0 | Yes |
| FR15 | TS051–TS054 | 2/2/0 | Yes |
| FR16 | TS055–TS057 | 3/0/0 | Yes |
| FR17 | TS058–TS059 | 2/0/0 | Yes |
| FR18 | TS060–TS062 | 2/1/0 | Yes |
| FR19 | TS063–TS067 | 5/0/0 | Yes |
| FR20 | TS068–TS071 | 4/0/0 | Yes |
| FR21 | TS072–TS075 | 2/2/0 | Yes |
| FR22 | TS076–TS079 | 4/0/0 | Yes |
| FR23 | TS080–TS083 | 2/2/0 | Yes |
| FR24 | TS084–TS087 | 2/1/1 | Yes |
| FR25 | TS088–TS091 | 4/0/0 | Yes |
| FR26 | TS092–TS095 | 3/0/1 | Yes |
| FR27 | TS096–TS099 | 2/2/0 | Yes |
| FR28 | TS100–TS103 | 3/1/0 | Yes |
| FR29 | TS104–TS107 | 3/1/0 | Yes |
| FR30 | TS108–TS111 | 2/1/1 | Yes |
| FR31 | TS112–TS114 | 1/2/0 | Yes |
| FR32 | TS115–TS118 | 4/0/0 | Yes |
| FR33 | TS119–TS122 | 2/1/1 | Yes |
| FR34 | TS123–TS126 | 3/1/0 | Yes |
| FR35 | TS127–TS129 | 2/1/0 | Yes |
| FR36 | TS130–TS132 | 1/2/0 | Yes |
| FR37 | TS133–TS136 | 2/2/0 | Yes |
| FR38 | TS137–TS139 | 3/0/0 | Yes |
| FR39 | TS140–TS143 | 3/1/0 | Yes |
| FR40 | TS144–TS147 | 3/0/1 | Yes |
| FR41 | TS148–TS151 | 3/0/1 | Yes |
| FR42 | TS152–TS154 | 3/0/0 | Yes |
| FR43 | TS155–TS157 | 2/0/1 | Yes |
| FR44 | TS158–TS161 | 3/0/1 | Yes |
| FR45 | TS162–TS164 | 2/1/0 | Yes |
| FR46 | TS165–TS166 | 1/1/0 | Yes |
| FR47 | TS167–TS169 | 2/0/1 | Yes |
| FR48 | TS170–TS172 | 2/1/0 | Yes |
| FR49 | TS173–TS175 | 2/1/0 | Yes |
| FR50 | TS176–TS179 | 2/2/0 | Yes |
| FR51 | TS180–TS183 | 2/2/0 | Yes |
| FR52 | TS184–TS187 | 3/1/0 | Yes |
| FR53 | TS188–TS191 | 3/1/0 | Yes |
| FR54 | TS192–TS194 | 2/0/1 | Yes |
| FR55 | TS195–TS199 | 3/0/2 | Yes |
| Standing invariants (INV01–INV15; each also traces to its owning FR above) | TS200–TS214 | 8/7/0 | Yes |

## Set-level quality gate

| Check | Result |
|---|---|
| Every FR success + failure path covered | Pass — all 55 FRs (FR01–FR55) have at least one Success-path and, where the FR defines one, one Failure/edge-path scenario; verified per-row in the Coverage check above. |
| Every UX/UI state covered | Pass — each scenario's Covers line names the specific UXnn/UInn item and, where the FR's own states table names a distinct state, the scenario references it (e.g. TS032/TS035 — all eight FR10 verification states incl. Disputed viewer-facing; TS056/TS057 — FR16 stale-link/enquiries-disabled; TS061/TS062 — FR18 sparse-profile/empty-section states; TS145/TS146 — FR40 auto-limit/escalation). The out-of-scope authentication screens (Launch/Welcome/Sign-in/Sign-up/OTP-login/Forgot-password/Log-out) are verified as a structural absence rather than skipped (TS025, TS161, TS178, INV14/TS213). |
| **Test distribution ratio reasonable — flag if E2E dominates.** | Pass — see Test distribution summary below. The set is Unit-heavy (65.4%), Integration second (28.0%), E2E smallest (6.5%) — the classic unit-heavy testing pyramid, not the "testing trophy" and clearly not the E2E-heavy "ice cream cone" anti-pattern. This shape is a deliberate, examined choice: MOD01's behaviour surface is dominated by pure business-rule logic that is naturally Unit-testable in isolation — the FR19 ranking allow-list/diversification/determinism (TS063–TS067), the three-axis separation and no-star-rating invariants (FR28, INV01, INV15), the FR22 typed-action mapping, and the FR50/FR52 contract-shape guards (INV12, INV14) — none of which need a running multi-service stack or a rendered UI to verify. E2E is deliberately reserved for the ~14 scenarios where the FR's own meaning is inescapably cross-actor/cross-screen (e.g. TS084 provider-accepts→enquirer-sees-contact, TS108 boost-purchase-to-Sponsored-label, TS028 operator-decision-to-listing-display, TS158 the full first-run journey, TS195/TS197 Opportunity detail→Activity). Given MOD01's own architecture (deterministic configuration-driven ranking, a single module-owned database, minimum-field adjacent contracts) and its FR-level density of absolute business invariants, a unit-heavy pyramid is the examined, correct shape here, not an unexamined default. |

## Test distribution summary

| Layer | Count | % of total |
|---|---|---|
| Unit | 140 | 65.4% |
| Integration | 60 | 28.0% |
| E2E | 14 | 6.5% |
| **Total** | **214** | **100%** |

## Open blockers

| ID | Item | What's needed | From |
|---|---|---|---|
| (none) | — | — | — |

No open blockers. Three FR-level open/medium-confidence items are carried forward honestly rather than silently resolved, consistent with `01-business-requirements.md`'s and `02-functional-requirements.md`'s own convention: FR06/FR19/FR33's Medium-confidence dependency on external contracts (Identity & Trust read contract, ranking weight tuning, workspace willingness-to-pay) is reflected in those scenarios' own Confidence field (TS019–TS021, TS063–TS067, TS119–TS122) without inventing certainty the FR itself does not have; none of these blocks sealing this file. Authentication (login/signup/OTP-login/session/logout) is confirmed out of MOD01 scope per FR50 DEC-001 — this file contains zero scenarios exercising a Vyapar-owned login flow, and explicitly tests the *absence* of one (TS025, TS161, TS178, TS213/INV14) as a positive requirement in its own right.

---

## FR01 — Create and edit a BusinessProfile

### TS001 — Draft BusinessProfile created within 2 seconds with mandatory fields
**Traces from:** FR01 (BR01) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an authenticated member starts business setup with name, one category, locality and a contact channel, when they save, then a Draft BusinessProfile is created and persisted within 2 seconds, visible only to its owner.
**Covers:** Success path · UX04/UI04 — Draft created
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS002 — Missing mandatory field blocks submission inline
**Traces from:** FR01 (BR01) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member omits name, category, or locality, when they attempt to save, then submission is blocked with an inline field-level message naming the missing field, and no Draft partial-save loses their other entered values.
**Covers:** Failure/edge path · UX04/UI04 — inline validation state
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS003 — Duplicate name+locality for same owner rejected with edit-existing offer
**Traces from:** FR01 (BR01) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member already owns a BusinessProfile with a given name+locality pair, when they try to create another with the identical pair, then the save is rejected and the system offers to edit the existing profile instead of creating a duplicate.
**Covers:** Failure/edge path · UX04/UI04 — duplicate-owner state
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS004 — Unverified member-provided fields labelled on later display
**Traces from:** FR01 (BR01) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a BusinessProfile has fields the member entered but that carry no verification evidence, when the profile is displayed to any viewer, then each such field carries the `member-provided` inline tag rather than being presented as an established fact.
**Covers:** Success path · UX04/UI04, UX07/UI07 — `member-provided` tag
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR02 — Business contact and visibility controls

### TS005 — Per-channel disclosure setting applies to all surfaces within 5 seconds
**Traces from:** FR02 (BR01) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an owner sets a contact channel to "After accepted enquiry", when they save, then search results, listing detail, the MOD05 summary, and enquiry threads all honor the setting within 5 seconds of the change.
**Covers:** Success path · UX04/UI04 — visibility controls
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS006 — All channels hidden and enquiries disabled requires explicit confirmation
**Traces from:** FR02 (BR01) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an owner sets every contact channel to Hidden and disables enquiries, when they try to save, then the system warns that customers cannot reach the business and requires explicit confirmation before saving.
**Covers:** Failure/edge path · UX04/UI04 — all-hidden warning state
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS007 — Stale cached surface never shows a channel after it was hidden
**Traces from:** FR02 (BR01) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a channel was Public and is then set to Hidden, when any cached surface (search result card, MOD05 summary) is rendered more than 5 seconds later, then that channel is absent from the render.
**Covers:** Failure/edge path · UX07/UI07 — contact disclosure
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR03 — Listing lifecycle (submit, activate, suspend, archive)

### TS008 — Submit with verified contact and clean safety check moves to Active-Unverified immediately
**Traces from:** FR03 (BR01, BR02) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Draft Listing's primary mobile number is OTP-verified and it passes the mandatory-field and automated safety checks, when the owner submits it, then it moves to Active-Unverified immediately and shows the `Unverified · details are member-provided` label.
**Covers:** Success path · UX04/UI04 — lifecycle submit
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS009 — Safety-check failure routes to Submitted with a reason category, not the wordlist
**Traces from:** FR03 (BR01, BR02) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Draft Listing fails the prohibited-content wordlist or spam-pattern check, when the owner submits it, then it moves to Submitted for operator review and the owner sees only the reason category (never the wordlist itself), routed into the FR40 queue.
**Covers:** Failure/edge path · UX04/UI04 — safety-hold state
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS010 — Suspend/archive stops distribution within 5 seconds and retains audit history
**Traces from:** FR03 (BR01, BR02) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an Active-Verified Listing, when an operator suspends it or the owner archives it, then its distribution (FR15/FR18) stops within 5 seconds while its record and audit history are retained, and any open enquiries are closed with a notice to enquirers on archive.
**Covers:** Success path · UX04/UI04, UX19/UI19 — suspend/archive
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS011 — Illegal state transition rejected server-side
**Traces from:** FR03 (BR01, BR02) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Listing in Archived state, when any client attempts to transition it directly to Active-Verified (skipping the defined lifecycle), then the server rejects the transition regardless of client-side state.
**Covers:** Failure/edge path · UX04/UI04 — lifecycle guard
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR04 — Create and edit a ProfessionalListingProfile with progressive setup

### TS012 — Member reaches Discover within three required steps
**Traces from:** FR04 (BR02) · **Layer:** E2E · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member starts professional setup, when they complete only the three required steps (what they offer, where/how they work, contact preference), then they reach Discover without being forced through any optional field.
**Covers:** Success path · UX05/UI05, UX02/UI02 — 3-step setup
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS013 — Unmapped free-text capability stored as searchable label queued for taxonomy review
**Traces from:** FR04 (BR02) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member types a capability that maps to no taxonomy concept, when they save it, then it is stored as an unmapped label, remains searchable by text, and is queued for taxonomy review (FR48).
**Covers:** Failure/edge path · UX05/UI05 — unmapped-capability state
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS014 — Abandoned setup keeps a Draft and prompts once on next open
**Traces from:** FR04 (BR02) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member abandons setup after step one, when they next open Vyapar, then a Draft is preserved and they are prompted exactly once to continue setup.
**Covers:** Failure/edge path · UX02/UI02 — "Continue setup" banner
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS015 — "Opportunity Readiness" list shown instead of a completion percentage
**Traces from:** FR04 (BR02) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a ProfessionalListingProfile with several optional fields unset, when the owner views their profile, then an "Opportunity Readiness" list of high-value missing fields is shown, and no completion percentage appears anywhere on the screen.
**Covers:** Success path · UX05/UI05 — Opportunity Readiness
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR05 — Capability visibility separate from opportunity-seeking visibility

### TS016 — Intent state stored private by default
**Traces from:** FR05 (BR02, BR12) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member sets an intent state (Looking for / Open to / Curious about / Not interested), when it is saved without further action, then it is stored as private and is never displayed on the listing, in search, or in the MOD05 summary.
**Covers:** Success path · UX02/UI02, UX13/UI13 — intent capture
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS017 — Making seeking status visible shows a one-time explanation
**Traces from:** FR05 (BR02, BR12) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member changes seeking visibility from private to `Everyone on Vyapar`, when they confirm the change, then a one-time explanation of who can see it is shown before the change takes effect.
**Covers:** Success path · UX13/UI13 — visibility opt-in explanation
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS018 — Withdrawing seeking visibility propagates within 5 seconds on all surfaces
**Traces from:** FR05 (BR02, BR12) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member's seeking status is currently visible, when they withdraw visibility, then it disappears from every surface (listing, search, MOD05 summary) within 5 seconds, while capability visibility remains unaffected.
**Covers:** Failure/edge path · UX13/UI13 — withdrawal propagation
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR06 — Shared VerifiedCredential reference, distinct from Counsel ExpertProfile

### TS019 — Credential reference displays live claim, issuer, and verification date
**Traces from:** FR06 (BR02, BR03, BR17) · **Layer:** Integration · **Priority:** Should · **Status:** Approved · **Confidence:** Medium
**Scenario:** Given a member's Identity & Trust record holds a VerifiedCredential and they attach a read-only reference to it, when their ProfessionalListingProfile is viewed, then it shows `Credential verified by ForKhatri: <claim>` sourced live, with no evidence copied into MOD01 and no Counsel ExpertProfile data read or shown.
**Covers:** Success path · UX05/UI05, UX07/UI07 — credential reference
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS020 — Identity & Trust unavailable shows last cached status with no error
**Traces from:** FR06 (BR02, BR03, BR17) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** Medium
**Scenario:** Given Identity & Trust is unreachable, when the listing renders its credential reference, then it shows the last cached status with a "last checked" time and no error surfaced to the viewer.
**Covers:** Failure/edge path · UX07/UI07 — degraded credential display
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS021 — Revocation upstream removes the display within one sync cycle
**Traces from:** FR06 (BR02, BR03, BR17) · **Layer:** Integration · **Priority:** Should · **Status:** Approved · **Confidence:** Medium
**Scenario:** Given a credential referenced by a listing is revoked upstream in Identity & Trust, when the next sync cycle runs (≤ 1 hour), then the credential reference disappears from the listing.
**Covers:** Failure/edge path · UX07/UI07 — revocation
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR07 — Phone/OTP contact baseline on every Listing

### TS022 — No Listing leaves Draft without a verified mobile number
**Traces from:** FR07 (BR03) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Draft Listing's primary mobile number has not completed the 6-digit OTP check, when the owner attempts to submit it, then submission is blocked until the number is OTP-verified, reusing the parent platform's OTP-sending capability.
**Covers:** Success path · UX04/UI04, UX05/UI05 — submit-time OTP
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS023 — Five failed OTP attempts locks the number for 15 minutes
**Traces from:** FR07 (BR03) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member has entered an incorrect OTP 5 times for a listing's number, when they attempt a 6th, then the number is locked for 15 minutes with a clear message, and resend is unavailable until the lock clears.
**Covers:** Failure/edge path · UX04/UI04 — OTP lockout
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS024 — Changing the verified number clears the "Contact verified" flag
**Traces from:** FR07 (BR03) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Listing shows `Contact verified` for its current number, when the owner changes the primary mobile number, then the flag is cleared until the new number is re-verified.
**Covers:** Failure/edge path · UX04/UI04, UX14/UI14 — re-verify
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS025 — Listing-contact OTP creates no session, credential, or login state
**Traces from:** FR07 (BR03) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member successfully completes the listing-contact OTP check, when the flow finishes, then no session token, credential, or login state is created anywhere in MOD01 — the member's authentication state is unaffected and remains solely owned by the parent ForKhatri platform (FR50).
**Covers:** Success path · UX01/UI01 (scope boundary), UX04/UI04, UX05/UI05
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR08 — Business-existence document submission and operator review

### TS026 — Exactly four document types offered; Aadhaar never appears
**Traces from:** FR08 (BR03) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Listing owner opens the verification document menu, when the menu renders, then exactly {GST Certificate/GSTIN, Udyam Registration, Business or Personal PAN, Shops & Establishment License} are selectable, one at a time, and no field, label, or upload option anywhere in the flow offers Aadhaar (FR08 DEC-002).
**Covers:** Success path · UX14/UI14 — four-document menu
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS027 — Invalid identifier format rejected inline before submission
**Traces from:** FR08 (BR03) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member enters a GSTIN that is not 15 characters or a PAN that is not 10 characters, when they attempt to submit, then the entry is rejected inline before the BusinessVerificationRecord is created.
**Covers:** Failure/edge path · UX14/UI14 — format validation
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS028 — Operator decision transitions the Listing to Active-Verified or back to Active-Unverified with reason
**Traces from:** FR08 (BR03) · **Layer:** E2E · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a BusinessVerificationRecord in Pending Review, when an operator marks it Verified, then the Listing becomes Active-Verified showing `Business existence verified (GST)` (or the matching document type) plus the verification date; when an operator instead Rejects it with a reason code, then the Listing returns to Active-Unverified with a re-submit option shown to the owner.
**Covers:** Success path · Failure/edge path · UX14/UI14, UX19/UI19, UX07/UI07 — operator decision, owner-facing outcome
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS029 — PAN upload stored encrypted, masked to last 4 digits, deleted 30 days after decision
**Traces from:** FR08 (BR03) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member uploads a PAN document for verification, when the operator decision is recorded, then the stored PAN is encrypted, displayed masked (last 4 characters only), never shown publicly, and scheduled for deletion 30 days after the decision.
**Covers:** Failure/edge path · UX14/UI14, UX19/UI19 — masked storage
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR09 — Professional-credential document review

### TS030 — Operator decision shows the specific credential reviewed and date
**Traces from:** FR09 (BR03) · **Layer:** Integration · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a ProfessionalListingProfile owner submits a credential document with claimed credential name and issuer, when an operator marks it reviewed, then the listing shows `Credential reviewed: <credential name> · <date>` and never the phrase "verified professional".
**Covers:** Success path · UX14/UI14, UX07/UI07 — credential reviewed label
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS031 — Unreadable document routes to "Needs clearer copy" without penalty
**Traces from:** FR09 (BR03) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given an uploaded credential document is illegible, when an operator reviews it, then the record moves to "Needs clearer copy" and the owner may re-upload without any penalty to their listing state.
**Covers:** Failure/edge path · UX14/UI14 — re-upload state
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR10 — Verification state display, expiry, and revert

### TS032 — All eight verification states render with claim scope and date
**Traces from:** FR10 (BR03) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Listing in each of Not Started / Pending Review / Verified / Expiring / Expired / Rejected / Revoked / Disputed, when it is displayed anywhere, then the bounded plain-language label renders with claim scope and date, and no two states are ever visually conflated.
**Covers:** Success path · UX07/UI07, UX14/UI14 — trust-label vocabulary
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS033 — 11-month reconfirmation reminder and 12-month expiry without reconfirmation
**Traces from:** FR10 (BR03) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Verified decision was made 11 months ago, when the reminder job runs, then the owner is prompted to reconfirm; given 12 months pass with no reconfirmation, when the expiry job runs, then the displayed claim reverts to unverified.
**Covers:** Success path · UX14/UI14 — reconfirmation reminder
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS034 — Report, dispute, or operator revocation reverts the label within 5 seconds
**Traces from:** FR10 (BR03) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Verified Listing receives a report that becomes a dispute, or an operator revokes its verification, when the state change is recorded, then the displayed claim reverts to unverified everywhere within 5 seconds.
**Covers:** Failure/edge path · UX07/UI07, UX19/UI19 — revert on dispute/revocation
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS035 — Disputed state shows "Under review" to viewers, never the dispute content
**Traces from:** FR10 (BR03) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Listing's verification is Disputed, when a viewer (not the owner or an operator) views it, then they see only "Under review" with no dispute content exposed.
**Covers:** Failure/edge path · UX07/UI07 — Disputed viewer-facing state
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR11 — Opportunity Composer: create, share, or upload with source segment

### TS036 — Three entry modes offered; segment tag and submitter mandatory
**Traces from:** FR11 (BR04) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member opens Post, when they choose Create, Share (pasted URL/text), or Upload (screenshot), then a Draft Opportunity is created that stores the submitting member as attribution, the raw input, and a mandatory Community or Public/External segment tag.
**Covers:** Success path · UX10/UI10 — Composer
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS037 — Public/External without any source name or URL is blocked
**Traces from:** FR11 (BR04) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member tags an Opportunity Public/External, when they attempt to save without a source name or URL, then the save is blocked with "tell us where you found it".
**Covers:** Failure/edge path · UX10/UI10 — source-required validation
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS038 — Unreachable source URL still accepted as Draft, flagged for review
**Traces from:** FR11 (BR04) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member shares a URL that returns an error when fetched, when the Draft is saved, then it is still accepted as a Draft carrying a "source unreachable" flag for operator review (FR48).
**Covers:** Failure/edge path · UX10/UI10 — source-unreachable flag
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS039 — Unsupported file type or oversize upload rejected inline
**Traces from:** FR11 (BR04) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member uploads a screenshot exceeding 5 MB or in an unsupported format, when they attempt to submit it, then an inline error is shown and no Draft is created from that upload.
**Covers:** Failure/edge path · UX10/UI10 — upload validation
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR12 — Structured fields, uncertainty marking, and contributor confirmation

### TS040 — Fields inferred from Share/Upload input marked "unconfirmed"
**Traces from:** FR12 (BR04) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Draft Opportunity was created from a Shared/Uploaded input, when the contributor reviews it before publish, then every field inferred from that input is visibly marked "unconfirmed".
**Covers:** Success path · UX10/UI10 — unconfirmed-field marking
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS041 — Publish blocked until title, type, location, and response method are confirmed
**Traces from:** FR12 (BR04) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Draft Opportunity has unconfirmed material fields, when the contributor attempts to publish, then publishing is blocked until title, type, location, and response method are explicitly confirmed.
**Covers:** Failure/edge path · UX10/UI10 — publish gate
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS042 — Day-5 reminder and day-7 auto-archive for an unconfirmed Draft
**Traces from:** FR12 (BR04) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Draft Opportunity remains unconfirmed, when 5 days elapse, then one reminder is sent to the contributor; when 7 days elapse with still no confirmation, then it is auto-archived.
**Covers:** Failure/edge path · UX10/UI10, UX11/UI11 — draft reminder/archive timers
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS043 — Illegible screenshot with no usable inference asks for the four material fields manually
**Traces from:** FR12 (BR04) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an uploaded screenshot yields no usable inferred fields, when the contributor opens the Draft, then they are asked to enter title, type, location, and response method manually rather than being shown a fabricated inference.
**Covers:** Failure/edge path · UX10/UI10 — manual-entry fallback
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR13 — Opportunity lifecycle, freshness, and expiry

### TS044 — Day-14 reminder and day-21 Stale after last owner confirmation
**Traces from:** FR13 (BR04, BR06) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an Active Opportunity was last confirmed 14 days ago, when the freshness job runs, then a reminder is sent; given 21 days pass with no reconfirmation, when the job runs again, then it is marked Stale.
**Covers:** Success path · UX08/UI08, UX09/UI09 — freshness stamp/reminder
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS045 — Deadline or 45 days without a deadline marks the Opportunity Expired
**Traces from:** FR13 (BR04, BR06) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an Active Opportunity has no stated deadline, when 45 days elapse since publish, then it is marked Expired; given one has a stated deadline, when that deadline passes, then it is marked Expired regardless of elapsed time.
**Covers:** Success path · UX09/UI09 — Expired state
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS046 — Non-Active states excluded from FR18 distribution within 5 seconds
**Traces from:** FR13 (BR04, BR06) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an Opportunity transitions to Stale, Expired, Closed, Removed, or Pending Review, when the state change is recorded, then it is excluded from the Discover feed (FR18) within 5 seconds while retaining provenance and audit history.
**Covers:** Failure/edge path · UX08/UI08 — distribution exclusion
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS047 — Renew resets freshness; renewing an Expired record older than 90 days requires re-confirmation
**Traces from:** FR13 (BR04, BR06) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an owner taps Renew on a Stale/Expired Opportunity, when the renewal completes, then its freshness stamp resets; given the record has been Expired for more than 90 days, when renewal is attempted, then material fields (FR12) must be re-confirmed first.
**Covers:** Success path · UX10/UI10 — Manage Opportunity, Renew
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR14 — Opportunity types with V1 launch focus

### TS048 — Three promoted types appear first in the picker; others under "Other"
**Traces from:** FR14 (BR04) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member selects an Opportunity type, when the type picker renders, then Employment, Freelance/Project, and Local Business/Professional Service appear first, and Business Partnership, Training, and Community/Government appear grouped under "Other".
**Covers:** Success path · UX10/UI10 — type picker
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS049 — Type change after publish re-validates type-specific mandatory fields
**Traces from:** FR14 (BR04) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a published Opportunity's type is changed from Local Service to Employment, when the owner attempts to save, then the type-specific mandatory fields for Employment (e.g., compensation) are re-validated before the save is accepted.
**Covers:** Failure/edge path · UX09/UI09 — type-specific section validation
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS050 — "Other" types excluded from proactive notifications in V1
**Traces from:** FR14 (BR04) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an Opportunity is tagged a Training or Community/Government type, when it scores above the FR21 strong-match threshold for a member, then no proactive notification is sent for it; it remains distributed only by search and the Community/Public feed sections.
**Covers:** Failure/edge path · UX18/UI18 — notification exclusion
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR15 — Standalone Listing search and browse

### TS051 — Search/browse/filter returns first 20 results within 2 seconds
**Traces from:** FR15 (BR05) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given Active Listings exist matching a keyword and locality/radius filter, when a member searches on the Businesses & Professionals surface, then the first 20 ranked results (organic relevance: text match, category match, distance, verification, freshness) return within 2 seconds.
**Covers:** Success path · UX06/UI06 — search/browse/filter
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS052 — Businesses & Professionals surface works with zero Opportunities in the system
**Traces from:** FR15 (BR05) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given the database contains Active Listings but zero Opportunity records of any state, when a member opens Businesses & Professionals and searches, then results return normally with no error or empty state caused by the absence of Opportunities.
**Covers:** Success path · UX06/UI06 — standalone discovery
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS053 — Private contact fields and private seeking state never appear in results
**Traces from:** FR15 (BR05) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Listing has Hidden contact channels and a private seeking status, when it appears in search results, then neither the hidden channels nor the private seeking status are present in the result payload or card.
**Covers:** Failure/edge path · UX06/UI06 — privacy exclusion
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS054 — Search service unavailable falls back to cached category browse with a notice
**Traces from:** FR15 (BR05) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given the search service is unavailable, when a member opens Businesses & Professionals, then a cached category browse is shown with a "search temporarily unavailable" notice instead of a hard error.
**Covers:** Failure/edge path · UX06/UI06 — degraded search state
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR16 — Listing detail view with trust context and action

### TS055 — All required elements present and visually distinct on the detail view
**Traces from:** FR16 (BR05, BR07) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an Active-Verified Listing with a Sponsored boost active, when a member opens its detail view, then description, capabilities, locality/mode, verification state with claim scope, reputation signals, `member-provided` labels, the `Sponsored` label, contact per FR02, and the primary `Enquire Now` action plus Save/Share/Report all render as visually distinct elements.
**Covers:** Success path · UX07/UI07 — Listing Detail
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS056 — Stale link to a Suspended/Archived listing shows "no longer available" with no data
**Traces from:** FR16 (BR05, BR07) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a shared link points to a Listing that is now Suspended or Archived, when it is opened, then the screen shows "no longer available" and none of the listing's data is rendered.
**Covers:** Failure/edge path · UX07/UI07 — stale-link state
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS057 — Enquiries disabled shows the reason and hides the primary action
**Traces from:** FR16 (BR05, BR07) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Listing's owner has disabled enquiries, when a member opens its detail view, then the reason is shown and the `Enquire Now` action is hidden rather than shown disabled with no explanation.
**Covers:** Failure/edge path · UX07/UI07 — enquiries-disabled state
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR17 — Zero-result broadening

### TS058 — Broadening options are explicit and labelled; no silent relaxation
**Traces from:** FR17 (BR05, BR06) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Listing search returns zero results, when the zero-result state renders, then user-selectable broadening options (widen radius 5→10→25 km, include adjacent categories, remove one filter, include unverified) are offered, and no hard filter the user set is silently relaxed.
**Covers:** Success path · UX06/UI06, UX08/UI08 — zero-result broadening
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS059 — Second zero result offers "Post what you need" and "Notify me"
**Traces from:** FR17 (BR05, BR06) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member applies a broadening option and still gets zero results, when the second zero-result state renders, then "Post what you need" (FR11) and "Notify me when something matches" (FR21) are offered.
**Covers:** Failure/edge path · UX06/UI06, UX08/UI08 — second zero-result fallback
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR18 — Opportunity Discover feed sections

### TS060 — Five sections render with required card fields, first section within 2 seconds
**Traces from:** FR18 (BR06) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given eligible Active Opportunities exist across categories, when a member opens Discover, then For You, Explore, Near You, Community, and Public sections render with type/title/location/value/freshness/segment+submitter/relevance-reason on every card, and the first section loads within 2 seconds.
**Covers:** Success path · UX08/UI08 — Discover feed sections
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS061 — New member with sparse profile sees a fallback instead of an empty For You
**Traces from:** FR18 (BR06) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a new member has a sparse profile with no strong matches, when they open Discover, then they see Near You + Community + Public sections plus one enrichment prompt (FR04), never an empty For You section.
**Covers:** Failure/edge path · UX08/UI08 — sparse-profile fallback
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS062 — A section with no eligible records is hidden, not shown empty
**Traces from:** FR18 (BR06) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given the Explore section has zero eligible records for a member, when Discover renders, then the Explore section is omitted entirely rather than rendered as an empty section.
**Covers:** Failure/edge path · UX08/UI08 — empty-section suppression
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR19 — Eligibility-before-ranking with configuration-driven deterministic scoring

### TS063 — Hard constraints exclude records before any scoring occurs
**Traces from:** FR19 (BR06) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an Opportunity is on-site and outside a member's radius, when any list is built for that member, then the record is excluded by the hard-constraint pass and never reaches the scoring step, regardless of how well it would otherwise score.
**Covers:** Success path · UX08/UI08 — eligibility-before-ranking
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS064 — Identical inputs produce identical rankings
**Traces from:** FR19 (BR06) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given the same member profile, configuration, and candidate set are supplied twice, when the ranking function runs both times, then the output order is byte-identical both times.
**Covers:** Success path · UX08/UI08 — deterministic scoring
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS065 — Signal allow-list excludes community status, account age, paid status, popularity, and report signals
**Traces from:** FR19 (BR06) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given two otherwise-identical Opportunities differing only in the provider's community status, account age, paid status, raw popularity, or report count, when both are scored, then their scores are identical, proving none of those signals were read.
**Covers:** Success path · UX08/UI08 — signal allow-list
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS066 — Diversification prevents more than 3 consecutive results from one provider or type
**Traces from:** FR19 (BR06) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a candidate set where one provider has 6 top-scoring Opportunities, when the ranked list is produced, then no more than 3 consecutive positions in the list share that provider or type.
**Covers:** Success path · UX08/UI08 — diversification
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS067 — Missing configuration falls back to logged safe defaults
**Traces from:** FR19 (BR06) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a ranking weight is missing from configuration, when the scorer runs, then it falls back to a safe default value and logs a warning rather than failing the request.
**Covers:** Failure/edge path · UX08/UI08 — configuration fallback
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR20 — "Why this opportunity" explanation

### TS068 — Top 3 contributing signals shown in plain language with an adjust-preference link
**Traces from:** FR20 (BR06) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a ranked Opportunity card, when the member opens "Why this?", then the top three contributing signals render in plain language (e.g., "matches your capability: accounting") with a direct link to adjust the related preference.
**Covers:** Success path · UX09/UI09 — Why this?
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS069 — Sponsored cards additionally disclose paid reach
**Traces from:** FR20 (BR06) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a ranked card is Sponsored, when its "Why this?" view opens, then it additionally states "shown to more people because the provider paid for reach".
**Covers:** Success path · UX09/UI09 — sponsored disclosure line
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS070 — No percentage match score ever appears
**Traces from:** FR20 (BR06) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given any "Why this?" view, when it renders for any Opportunity, then no percentage or numeric match score appears anywhere in it.
**Covers:** Failure/edge path · UX09/UI09 — no percentage score
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS071 — Fewer than three signals shows only those available; a search-only result shows "matched your search"
**Traces from:** FR20 (BR06) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an Opportunity reached via search with no ranking signals applied, when "Why this?" opens, then it shows "matched your search"; given exactly two signals apply, when it opens, then only those two are shown.
**Covers:** Failure/edge path · UX09/UI09 — degraded explanation
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR21 — Proactive notification and digest with fatigue limits

### TS072 — Strong-match Opportunity triggers one notification via the Notification service
**Traces from:** FR21 (BR06, BR12) · **Layer:** Integration · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a newly Active Opportunity scores above the configured strong-match threshold for a member with notifications enabled, when the scoring job runs, then exactly one push/in-app notification is requested via the Notification service.
**Covers:** Success path · UX18/UI18 — strong-match notification
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS073 — Daily cap of 3 opportunity notifications enforced
**Traces from:** FR21 (BR06, BR12) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member has already received 3 opportunity notifications today, when a 4th strong-match Opportunity qualifies, then no notification is sent and it is instead queued for the daily digest.
**Covers:** Failure/edge path · UX18/UI18 — fatigue cap
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS074 — Notification service failure retried up to 3 times, never duplicated
**Traces from:** FR21 (BR06, BR12) · **Layer:** Integration · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given the Notification service fails to deliver a request, when the system retries, then it retries up to 3 times and then drops the request, and at no point are two notifications sent for the same event.
**Covers:** Failure/edge path · UX18/UI18 — retry/no-duplicate
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS075 — Member mute of a type receives none of that type; "Other" excluded in V1
**Traces from:** FR21 (BR06, BR12) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member mutes the Employment notification type, when a strong-match Employment Opportunity is published, then they receive no notification for it; given any "Other" type (FR14) Opportunity is published, when it qualifies for a strong match, then it is excluded from proactive notification in V1 regardless of mute settings.
**Covers:** Failure/edge path · UX18/UI18 — per-type mute
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR22 — Submit an Enquiry or Opportunity Response

### TS076 — Stored type equals the user-facing label per target type
**Traces from:** FR22 (BR07) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member taps the primary action on an Employment Opportunity, a Freelance/Project Opportunity, and a Local-service Listing in turn, when each Enquiry record is created, then the stored type equals its label exactly ("Apply", "Submit a Proposal", "Enquire Now" respectively).
**Covers:** Success path · UX12/UI12 — typed action mapping
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS077 — Daily cap of 20 and 1-open-enquiry-per-target enforced with existing-thread link
**Traces from:** FR22 (BR07) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member has already sent 20 enquiries today, or already has an open enquiry on the same target, when they attempt to submit another, then the attempt is blocked with a clear message and, for the duplicate-target case, a link to the existing thread.
**Covers:** Failure/edge path · UX12/UI12 — cap/duplicate handling
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS078 — Enquiry to a blocked-by-provider target is silently not delivered but shown as Submitted
**Traces from:** FR22 (BR07) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a provider has blocked a member, when that member submits an Enquiry to the provider's Listing, then it is not delivered to the provider, and the sender sees status "Submitted" with no indication that a block occurred.
**Covers:** Failure/edge path · UX12/UI12 — blocked-sender handling
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS079 — Target no longer Active disables the action with a reason
**Traces from:** FR22 (BR07) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an Opportunity has moved to Expired, when a member views it, then the primary enquire/apply action is disabled and shows the reason rather than allowing submission.
**Covers:** Failure/edge path · UX09/UI09, UX12/UI12 — inactive-target state
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR23 — Provider manages the Enquiry lifecycle

### TS080 — Enquiry transitions Open → Awaiting Response → In Progress → Resolved → Closed are enforced
**Traces from:** FR23 (BR07) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an Open Enquiry, when the provider replies and progresses it through the defined states in order, then each transition is accepted and both parties see the current state and last activity time consistently.
**Covers:** Success path · UX12/UI12, UX11/UI11 — lifecycle states
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS081 — 7-day no-reply marks "No response yet" and counts toward provider responsiveness
**Traces from:** FR23 (BR07) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an Open Enquiry has had no provider reply for 7 days, when the timer job runs, then the enquirer sees "No response yet" and the event is counted in the provider's FR28 responsiveness signal.
**Covers:** Failure/edge path · UX12/UI12 — no-response marker
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS082 — Restricted thread rejects further state changes
**Traces from:** FR23 (BR07) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a thread has been Restricted by either party, when either party attempts a further state change or message, then the attempt is rejected.
**Covers:** Failure/edge path · UX12/UI12 — Restricted-thread guard
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS083 — "Refer to Counsel" sends only the explicit consented referral and changes nothing else in the thread
**Traces from:** FR23 (BR07), FR52(f) (BR17) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an open Enquiry thread, when a party taps "Refer to Counsel" and confirms consent, then exactly one referral (member id, problem summary, consent flag) is sent to MOD04 and the thread's state, messages, and every other field remain unchanged.
**Covers:** Success path · UX12/UI12 — Refer to Counsel
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR24 — Consent-based contact disclosure, blocking, and safety guidance

### TS084 — Contact revealed only for channels set "After accepted enquiry", only upon acceptance
**Traces from:** FR24 (BR07, BR12, BR13) · **Layer:** E2E · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a provider accepts an Enquiry (moves it to In Progress) and has set exactly one contact channel to "After accepted enquiry", when the enquirer opens the thread, then only that channel is revealed, alongside the one-line safety notice ("never pay in advance; report suspicious requests") shown before any external contact.
**Covers:** Success path · UX12/UI12 — consented contact disclosure
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS085 — Safety notice shown exactly once per thread before external contact
**Traces from:** FR24 (BR07, BR12, BR13) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given contact has just been disclosed in a thread, when the enquirer reopens that same thread later, then the safety notice is not shown again — it was shown exactly once.
**Covers:** Success path · UX12/UI12 — one-time safety notice
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS086 — Block ends the thread, prevents future enquiries both ways, hides future content
**Traces from:** FR24 (BR07, BR12, BR13) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given one party blocks the other, when the block is recorded, then the thread ends, neither party can create a new Enquiry with the other, and the blocked party's future content is hidden from the blocker.
**Covers:** Failure/edge path · UX15/UI15 — block
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS087 — Withdrawn/Closed threads no longer show contact; no bulk export of enquirer contacts
**Traces from:** FR24 (BR07, BR12, BR13) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an Enquiry thread is Withdrawn or Closed, when either party reopens it, then previously disclosed contact is no longer shown; given any role attempts a bulk or export view of enquirer contact details, when the attempt is made, then no such capability exists for any role.
**Covers:** Failure/edge path · UX12/UI12 — post-closure contact withdrawal
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR25 — Create a Partnership Request

### TS088 — Fields and character limits enforced; request sent to recipient
**Traces from:** FR25 (BR08) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member with an Active Listing selects "Propose partnership" on another Active Listing and fills need/offer/expectations/category/locality/timing/next-step within 10–500 characters each, when they submit, then a PartnershipRequest is created and sent, and the sender sees Pending.
**Covers:** Success path · UX17/UI17 — create Partnership Request
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS089 — Requester without an Active Listing is prompted to create one first
**Traces from:** FR25 (BR08) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member with no Active Listing attempts "Propose partnership", when they tap the action, then they are prompted to create an Active Listing before a request can be sent.
**Covers:** Failure/edge path · UX17/UI17 — no-active-listing gate
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS090 — 10-pending-cap reached shows a message listing pending requests
**Traces from:** FR25 (BR08) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member already has 10 pending PartnershipRequests, when they attempt an 11th, then the attempt is blocked with a message listing their current pending requests.
**Covers:** Failure/edge path · UX17/UI17 — pending cap
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS091 — Recipient who disabled partnership requests hides the action
**Traces from:** FR25 (BR08) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Listing owner has disabled partnership requests, when another member views that listing, then "Propose partnership" is hidden rather than shown and rejected.
**Covers:** Failure/edge path · UX17/UI17 — recipient opt-out
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR26 — Respond to and manage a Partnership Request

### TS092 — Accept/Decline/Restrict/Withdraw/Close states are enforced across both parties
**Traces from:** FR26 (BR08) · **Layer:** E2E · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Pending PartnershipRequest, when the recipient Accepts it and either party later Closes it, then both parties consistently see the state progression Pending → Accepted → Closed, and the Accepted request appears in each party's Activity and qualifies for FR27.
**Covers:** Success path · UX17/UI17, UX11/UI11 — Partnership Request lifecycle
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS093 — Contact disclosed only after Accept, per the FR02 "after accepted enquiry" level
**Traces from:** FR26 (BR08) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a PartnershipRequest is Pending, when either party views it, then no contact channel is disclosed; when the recipient Accepts it, then contact channels set to "After accepted enquiry" become visible.
**Covers:** Success path · UX17/UI17 — post-accept disclosure
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS094 — Pending requests never auto-expire
**Traces from:** FR26 (BR08) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a PartnershipRequest has been Pending for an extended period, when any background job runs, then it remains Pending — no automatic expiry occurs.
**Covers:** Failure/edge path · UX17/UI17 — no auto-expiry
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS095 — Declined request cannot be re-sent to the same recipient for 30 days
**Traces from:** FR26 (BR08) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a recipient Declined a PartnershipRequest from a sender, when that sender attempts to send another request to the same recipient within 30 days, then the attempt is blocked.
**Covers:** Failure/edge path · UX17/UI17 — decline cooldown
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR27 — Submit a Review tied to a qualifying interaction

### TS096 — Review invite sent once on a qualifying Resolved/Closed thread within 30 days
**Traces from:** FR27 (BR09) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an Enquiry reaches Resolved/Closed with at least one reply from each side, when the qualifying-interaction check runs, then each party is invited exactly once to submit a Review within 30 days, and the linked interaction id is stored on submission.
**Covers:** Success path · UX16/UI16 — review invite
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS097 — Review without a qualifying interaction is rejected
**Traces from:** FR27 (BR09) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given no qualifying interaction exists between two members, when a Review submission referencing them is attempted, then it is rejected.
**Covers:** Failure/edge path · UX16/UI16 — qualifying-interaction gate
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS098 — Second submission for the same interaction rejected
**Traces from:** FR27 (BR09) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a party already submitted a Review for a given interaction, when they attempt a second Review for the same interaction, then the second attempt is rejected.
**Covers:** Failure/edge path · UX16/UI16 — one-review-per-party-per-interaction
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS099 — Review on a thread later found fraudulent is auto-hidden when the thread is removed
**Traces from:** FR27 (BR09) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Review is linked to an Enquiry thread that is subsequently Removed by moderation (FR40), when the thread's removal is processed, then the linked Review is automatically Hidden.
**Covers:** Failure/edge path · UX16/UI16 — auto-hide on thread removal
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR28 — Contextual reputation display with no new-member penalty

### TS100 — Contextual counts render; never a single aggregate score
**Traces from:** FR28 (BR09) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Listing has 12 verified interactions and 9 of 12 recommend, when it is displayed, then it shows `N verified interactions · N of M recommend`, top tags, and `Responds in ~X`, and no single aggregate score (star or numeric) renders anywhere.
**Covers:** Success path · UX07/UI07 — reputation display
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS101 — "New on Vyapar" shown below 3 interactions with no negative treatment
**Traces from:** FR28 (BR09) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Listing has 2 verified interactions, when it is displayed, then it shows `New on Vyapar` with no negative styling, warning icon, or ranking penalty applied because of it.
**Covers:** Success path · UX07/UI07 — New-on-Vyapar treatment
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS102 — Hidden/Removed reviews excluded from counts within 5 seconds
**Traces from:** FR28 (BR09) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a published Review is subsequently Hidden or Removed, when the state change is recorded, then it is excluded from the listing's reputation counts within 5 seconds.
**Covers:** Failure/edge path · UX07/UI07 — count exclusion
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS103 — Disputed review shows "1 review under review" without content
**Traces from:** FR28 (BR09) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Review on a Listing is Disputed, when the listing's reputation section is displayed to a viewer, then it shows "1 review under review" with no dispute content exposed.
**Covers:** Failure/edge path · UX07/UI07 — disputed-review display
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR29 — Review dispute, hide, and removal

### TS104 — Dispute moves a Review to Disputed, kept Published-but-flagged until operator decision
**Traces from:** FR29 (BR09, BR13) · **Layer:** Integration · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given the subject of a Review disputes it with reason "retaliation", when the dispute is submitted, then the Review moves to Disputed, remains Published-but-flagged, and enters the FR40 queue.
**Covers:** Success path · UX16/UI16 — dispute flow
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS105 — Operator outcome (Published/Hidden/Removed) retains original text and full audit history
**Traces from:** FR29 (BR09, BR13) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Disputed Review, when an operator decides Hidden, then the original text is retained in the audit history (visible to author only going forward) and both parties are notified with the reason code.
**Covers:** Success path · UX19/UI19 — operator decision
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS106 — A subject may dispute a given Review only once
**Traces from:** FR29 (BR09, BR13) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a subject already disputed a Review, when they attempt to dispute the same Review again, then the second dispute attempt is rejected.
**Covers:** Failure/edge path · UX16/UI16 — one-dispute-per-review
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS107 — No provider-side path exists to edit or hide a Review directly
**Traces from:** FR29 (BR09, BR13) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a provider is the subject of a published Review, when they attempt any action other than filing a dispute, then no edit or hide capability is available to them through any path.
**Covers:** Failure/edge path · UX16/UI16 — anti-gaming guard
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR30 — Purchase an Opportunity or Listing Boost

### TS108 — Boost purchase creates a Promotion that activates on payment, labelled Sponsored everywhere
**Traces from:** FR30 (BR10) · **Layer:** E2E · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given the owner of an Active-Verified Listing selects Boost, chooses a duration/audience product, and sees price-with-tax and the plain-language does/doesn't-change text, when they confirm and payment is confirmed (FR51), then the Promotion activates and every surface labels the record `Sponsored`.
**Covers:** Success path · UX20/UI20 — boost purchase
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS109 — Unverified Listing cannot Boost; shown "verify first"
**Traces from:** FR30 (BR10) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an Active-Unverified Listing owner opens Boost, when the eligibility check runs, then Boost is unavailable and "verify first" is shown.
**Covers:** Failure/edge path · UX20/UI20 — eligibility gate
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS110 — Payment failure keeps the Promotion Awaiting Payment for 24 hours then Cancels it
**Traces from:** FR30 (BR10) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Boost payment fails, when 24 hours pass without a successful retry, then the Promotion is automatically Cancelled.
**Covers:** Failure/edge path · UX20/UI20 — payment-failure timeout
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS111 — Organic rank of all records is unchanged by an active boost
**Traces from:** FR30 (BR10) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Listing purchases a Boost, when the organic ranking function is computed with and without the active Promotion, then the organic rank of every record (including the boosted one) is identical in both runs.
**Covers:** Success path · UX20/UI20, UX08/UI08 — pay-to-win guard
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR31 — Promotion lifecycle, price versioning, cancellation, and credit

### TS112 — Product/price version stored at purchase; receipt with tax line and history shown
**Traces from:** FR31 (BR10, BR11) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member purchases a Boost, when the order completes, then the exact product and price version in force at purchase is stored on the order, and the owner can view a receipt reference, tax line, and state history at any time.
**Covers:** Success path · UX20/UI20 — receipt/history
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS113 — Pre-activation cancel gives a full refund; active cancel gives a pro-rata credit
**Traces from:** FR31 (BR10, BR11) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Promotion is Awaiting Payment/Scheduled (not yet Active), when the owner cancels, then a full refund is issued; given the same Promotion is already Active and the owner cancels partway through, then a pro-rata credit is issued instead.
**Covers:** Success path · UX20/UI20 — cancel/refund/credit
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS114 — Operator safety rejection triggers an automatic full refund with reason
**Traces from:** FR31 (BR10, BR11) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an operator Rejects a Promotion for a safety reason, when the rejection is recorded, then an automatic full refund request is issued via FR51 and the owner is shown the reason.
**Covers:** Failure/edge path · UX19/UI19, UX20/UI20 — operator reject → refund
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR32 — Provider performance reporting without unsupported claims

### TS115 — Five separate counts shown with boosted-vs-organic split
**Traces from:** FR32 (BR10, BR15) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Listing ran a Boost during the selected period, when the provider opens the performance report, then impressions, detail views, saves, enquiries/responses, and confirmed outcomes are shown as five separate counts, split boosted vs. organic.
**Covers:** Success path · UX20/UI20 — performance report
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS116 — Fewer than 10 impressions shows "too little data to compare"
**Traces from:** FR32 (BR10, BR15) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a period has fewer than 10 impressions, when the report renders that period, then the counts are shown alongside "too little data to compare" rather than a misleading comparison.
**Covers:** Failure/edge path · UX20/UI20 — low-data disclosure
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS117 — No projections, ROI guarantees, or causal statements are ever rendered
**Traces from:** FR32 (BR10, BR15) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given any performance report state, when it is rendered for any provider, then no projection, ROI guarantee, or causal claim ("this boost caused N sales") appears anywhere in it.
**Covers:** Failure/edge path · UX20/UI20 — no unsupported claims
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS118 — No individual member identity is ever shown in reports
**Traces from:** FR32 (BR10, BR15) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a performance report aggregates enquiries from several distinct members, when it renders, then no individual member's identity appears anywhere in the report, only aggregate counts.
**Covers:** Failure/edge path · UX20/UI20 — no member-level data
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR33 — Purchase and manage a Business Workspace entitlement

### TS119 — Entitlement created on payment confirmation; capabilities unlock immediately
**Traces from:** FR33 (BR11) · **Layer:** E2E · **Priority:** Should · **Status:** Approved · **Confidence:** Medium
**Scenario:** Given a BusinessProfile owner selects a Business Workspace plan and sees price/renewal/cancellation terms, when payment is confirmed, then an Entitlement is created and its included capabilities (multi-user admin, campaign management, response tracking, analytics) unlock immediately.
**Covers:** Success path · UX21/UI21 — workspace purchase
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS120 — Workspace plan never grants verification, reputation, ranking, eligibility, or private data
**Traces from:** FR33 (BR11) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** Medium
**Scenario:** Given a BusinessProfile purchases a Workspace entitlement, when its verification state, reputation counts, organic ranking, and eligibility are checked before and after purchase, then none of them changes as a result of the purchase.
**Covers:** Success path · UX21/UI21 — commercial-non-leverage guard
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS121 — Renewal payment failure triggers a 7-day grace period, then Paused with data retained
**Traces from:** FR33 (BR11) · **Layer:** Integration · **Priority:** Should · **Status:** Approved · **Confidence:** Medium
**Scenario:** Given a Workspace renewal payment fails, when 7 days pass with notices sent but no successful retry, then the Entitlement moves to Paused (capabilities locked) with all data retained.
**Covers:** Failure/edge path · UX21/UI21 — grace/pause
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS122 — Cancellation stops renewal at period end with no hidden auto-renewal
**Traces from:** FR33 (BR11) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** Medium
**Scenario:** Given an owner cancels their Workspace plan mid-period, when the current period ends, then the plan does not renew, and at no point was an auto-renewal charged without prior explicit disclosure.
**Covers:** Failure/edge path · UX21/UI21 — cancellation
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR34 — Multi-user business administration roles

### TS123 — Invite by phone number, role assigned after accept
**Traces from:** FR34 (BR11) · **Layer:** Integration · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Workspace owner invites another member by phone number as Admin or Operator, when the invitee accepts, then the role is assigned and every subsequent action by that individual is attributed to them by name.
**Covers:** Success path · UX21/UI21 — team roles
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS124 — Owner revocation has immediate effect on Vyapar surfaces; platform session untouched
**Traces from:** FR34 (BR11) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given an Operator's role is revoked by the owner, when the revocation is recorded, then the Vyapar role is removed with immediate effect on every open Vyapar surface for that invitee, while their ForKhatri platform session itself is left untouched (Vyapar owns no sessions).
**Covers:** Failure/edge path · UX21/UI21 — role revocation
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS125 — Invitee not yet a ForKhatri member stays pending with a 30-day expiry
**Traces from:** FR34 (BR11) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given an invited phone number belongs to someone who is not yet a ForKhatri member, when 30 days pass without them joining, then the invitation expires.
**Covers:** Failure/edge path · UX21/UI21 — invitation expiry
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS126 — Revoked operator's in-progress drafts remain with the business
**Traces from:** FR34 (BR11) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a revoked Operator had an in-progress Opportunity Draft, when their role is revoked, then the Draft remains owned by the business, not deleted or transferred to the individual.
**Covers:** Failure/edge path · UX21/UI21 — draft continuity on revocation
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR35 — Community/Opportunity Campaign creation

### TS127 — Up to 10 Active items grouped under one Campaign with boost rules applied per item
**Traces from:** FR35 (BR11, BR10) · **Layer:** Integration · **Priority:** Should · **Status:** Approved · **Confidence:** Medium
**Scenario:** Given an entitled business groups 10 Active Opportunities/Listings under one Campaign name, budget, and date range, when the Campaign activates, then FR30 boost rules apply to each item individually and a campaign-level report is produced per FR32.
**Covers:** Success path · UX21/UI21 — Campaign creation
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS128 — Item leaving Active mid-campaign is Paused with credit
**Traces from:** FR35 (BR11, BR10) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** Medium
**Scenario:** Given a Campaign item moves out of Active state (e.g., Expired) mid-campaign, when the state change is recorded, then that item's boost is Paused and its remaining time is credited per FR31.
**Covers:** Failure/edge path · UX21/UI21 — item drop-out
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS129 — Budget exhausted completes the campaign early with notice
**Traces from:** FR35 (BR11, BR10) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** Medium
**Scenario:** Given a Campaign's fixed budget is exhausted before its date range ends, when the exhaustion is detected, then the Campaign is marked Completed early and the owner is notified.
**Covers:** Failure/edge path · UX21/UI21 — budget exhaustion
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR36 — Contextual privacy controls

### TS130 — Six controls prompted contextually with defaults applied
**Traces from:** FR36 (BR12) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member first sets seeking-status visibility, when the contextual prompt appears, then it shows a one-sentence explanation and, if left unset, applies the privacy-by-default value (seeking private); the same pattern applies to capability visibility, contact disclosure, discoverability, notifications, and commercial communications.
**Covers:** Success path · UX02/UI02, UX22/UI22 — contextual prompts
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS131 — Declining a contextual prompt keeps the default, revisitable later
**Traces from:** FR36 (BR12) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member declines a contextual privacy prompt, when they proceed, then the privacy-by-default value stays in effect and remains changeable later from the Privacy screen.
**Covers:** Failure/edge path · UX22/UI22 — decline-keeps-default
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS132 — All six controls exposed together in one Privacy screen; changes propagate within 5 seconds
**Traces from:** FR36 (BR12) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member opens the Privacy screen, when it renders, then all six controls (capability visibility, seeking visibility, contact disclosure, discoverability, notifications, commercial communications) appear together; when the member changes one, then the change propagates to every surface within 5 seconds.
**Covers:** Success path · UX22/UI22 — single Privacy screen
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR37 — Data access, correction, deletion, and consent withdrawal

### TS133 — Data export delivered within 72 hours
**Traces from:** FR37 (BR12, BR18) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member requests a downloadable copy of their MOD01 data from the Privacy screen, when the export job runs, then a downloadable copy (profiles, opportunities, enquiries, reviews they wrote, consents) is available within 72 hours.
**Covers:** Success path · UX22/UI22 — data export
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS134 — Correction of a self-entered field and consent withdrawal both apply immediately
**Traces from:** FR37 (BR12, BR18) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member corrects a self-entered field or withdraws an optional consent, when they confirm, then the change is applied immediately with no processing delay.
**Covers:** Success path · UX22/UI22 — correction/withdrawal
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS135 — Deletion within 30 days anonymizes counterpart records rather than deleting them
**Traces from:** FR37 (BR12, BR18) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member requests deletion, when the 30-day deletion job completes, then the member's own MOD01 data is deleted except records required for open disputes/active orders/audit obligations (listed to the member), and their counterpart's enquiry/review records are anonymized rather than deleted.
**Covers:** Success path · UX22/UI22 — deletion with anonymization
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS136 — Deletion during an active paid Promotion informs the member it completes after the order closes
**Traces from:** FR37 (BR12, BR18) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member with an active paid Promotion requests deletion, when the request is submitted, then they are informed deletion completes after the order closes or is cancelled, rather than being silently blocked or silently completed early.
**Covers:** Failure/edge path · UX22/UI22 — deletion-with-active-order
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR38 — Inspect and confirm derived preferences

### TS137 — Repeated pattern proposes an explicit preference change with evidence, applied only on confirmation
**Traces from:** FR38 (BR12, BR06) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member has given "Too far" feedback three times, when the pattern-detection job runs, then an explicit preference-change proposal with the evidence is shown, and the ranking system does not apply it until the member confirms.
**Covers:** Success path · UX22/UI22 — derived-preference proposal
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS138 — Reports are never used as preference input
**Traces from:** FR38 (BR12, BR06) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member has filed several Reports against a category of Opportunity, when the preference-detection job runs, then those Reports are excluded from consideration as a signal for any preference proposal.
**Covers:** Failure/edge path · UX22/UI22 — reports-excluded guard
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS139 — Declined proposal is not re-proposed for 30 days
**Traces from:** FR38 (BR12, BR06) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member declines a preference-change proposal, when the same pattern recurs within 30 days, then no new proposal for that preference is shown until the 30 days elapse.
**Covers:** Failure/edge path · UX22/UI22 — re-proposal cooldown
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR39 — Report and block

### TS140 — Report with reason and evidence creates a Report in the FR40 queue within 5 seconds
**Traces from:** FR39 (BR13) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member selects Report on a Listing with reason "scam/advance payment" and up to 3 evidence images, when they submit, then a Report is created in the FR40 queue within 5 seconds and the reporter sees a receipt confirmation, with Block offered in the same flow.
**Covers:** Success path · UX15/UI15 — report submission
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS141 — Reporter identity is hidden from the reported party
**Traces from:** FR39 (BR13) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Report is filed against a Listing, when the reported owner or any operator-facing surface visible to that owner is rendered, then the reporter's identity is never shown to them.
**Covers:** Success path · UX15/UI15 — reporter anonymity
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS142 — Member exceeding 10 reports/day is rate-limited
**Traces from:** FR39 (BR13) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member has already filed 10 Reports today, when they attempt an 11th, then the attempt is blocked with a rate-limit message.
**Covers:** Failure/edge path · UX15/UI15 — report rate limit
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS143 — Duplicate reports on the same object merge into one case with a reporter count
**Traces from:** FR39 (BR13) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given three different members Report the same Listing, when the third Report is filed, then it merges into the existing case rather than creating a new one, and the case shows a reporter count of 3.
**Covers:** Failure/edge path · UX15/UI15, UX19/UI19 — duplicate-report merge
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR40 — Moderation queue and graduated actions

### TS144 — Operator applies a graduated action with a mandatory reason code
**Traces from:** FR40 (BR13, BR16) · **Layer:** E2E · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Report enters the moderation queue showing object, evidence, severity, and history, when an operator selects Limit distribution, Remove/Hide, Restore, Request verification, Suspend account, or Dismiss with a mandatory reason code, then the action is applied, attributed, audited, and the affected party is notified with the outcome and appeal path.
**Covers:** Success path · UX19/UI19 — moderation action
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS145 — High/Critical items are auto-limited from distribution pending review
**Traces from:** FR40 (BR13, BR16) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Report is auto-classified High or Critical severity, when it enters the queue, then the object is automatically limited from distribution pending an operator's review.
**Covers:** Failure/edge path · UX19/UI19 — auto-limit
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS146 — Automated flag with no decision within target time escalates without an automatic permanent ban
**Traces from:** FR40 (BR13, BR16) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an automated safety flag has no operator decision within its configured target response time, when the target is missed, then the item escalates in the queue, and no automatic permanent ban is applied.
**Covers:** Failure/edge path · UX19/UI19 — escalation
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS147 — Restore fully reverses a prior action; operators cannot edit evidence
**Traces from:** FR40 (BR13, BR16) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a previously Removed Listing, when an operator applies Restore, then the prior action is fully reversed; given any operator attempts to edit submitted evidence in the queue, when the attempt is made, then no edit capability exists.
**Covers:** Success path · UX19/UI19 — Restore / evidence immutability
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR41 — Appeals and outcome communication

### TS148 — One Appeal submitted within 15 days routed to a different operator where possible
**Traces from:** FR41 (BR13, BR18) · **Layer:** E2E · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member received a moderation outcome (e.g., removal), when they submit one Appeal within 15 days, then it is routed to a different operator than the original decision-maker where staffing allows, and the decision with reason code is communicated within the default 7-day target.
**Covers:** Success path · UX15/UI15 — appeal submission and decision
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS149 — Second appeal on the same decision is rejected
**Traces from:** FR41 (BR13, BR18) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member already appealed a decision, when they attempt to appeal the same decision again, then the second appeal attempt is rejected.
**Covers:** Failure/edge path · UX15/UI15 — one-appeal-per-decision
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS150 — Overturned appeal restores the object/account fully
**Traces from:** FR41 (BR13, BR18) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given an Appeal is decided Overturned, when the decision is applied, then the affected object or account is fully restored to its pre-action state.
**Covers:** Success path · UX15/UI15 — Overturned restoration
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS151 — Appeal target missed escalates the case and informs the member of the delay
**Traces from:** FR41 (BR13, BR18) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given an Appeal's 7-day target is missed, when the target elapses, then the case escalates to the queue owner and the member is informed of the delay.
**Covers:** Failure/edge path · UX15/UI15 — missed-target escalation
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR42 — Language selection and rendering (English, Hindi, Telugu)

### TS152 — Selecting a language renders all MOD01 strings via the platform i18n layer
**Traces from:** FR42 (BR14) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member selects Hindi, when any MOD01 screen renders, then all interface text, system messages, labels, notifications, and taxonomy display names render in Hindi via the shared platform i18n layer.
**Covers:** Success path · UX01/UI01, UX13/UI13 — language rendering
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS153 — Member-authored content stays in its original language with a language tag, unchanged
**Traces from:** FR42 (BR14) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member writes a Hindi-language Opportunity description, when a Telugu-preference member views it, then the description is shown unchanged in Hindi with its language tag, never machine-translated.
**Covers:** Success path · UX09/UI09 — untouched member content
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS154 — Language preference is never used as a ranking input
**Traces from:** FR42 (BR14) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given two otherwise-identical Opportunities differ only in their member's language preference, when both are scored by FR19, then their scores are identical, proving language was not read as a signal.
**Covers:** Failure/edge path · UX08/UI08 — language-neutral ranking
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR43 — Accessibility baseline

### TS155 — Core journeys pass a manual screen-reader test before release
**Traces from:** FR43 (BR14) · **Layer:** E2E · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given the core journeys (setup, search, enquiry, post), when a manual screen-reader pass is conducted, then every core action is completable by keyboard and screen reader alone, and the evidence is recorded before release.
**Covers:** Success path · UX03/UI03 — accessibility baseline
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS156 — No information conveyed by colour alone; text resizes to 200% without loss
**Traces from:** FR43 (BR14) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given any state indicator (e.g., verification label) is rendered, when colour is removed, then the same information remains available via text or icon; given the browser text size is increased to 200%, when any MOD01 screen renders, then no content is lost or overlapped.
**Covers:** Success path · UX03/UI03 — colour/resize compliance
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS157 — A screen failing an automated accessibility check blocks its release
**Traces from:** FR43 (BR14) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a screen fails an automated WCAG 2.2 AA check in CI, when the release pipeline runs, then that screen's release is blocked until the failure is resolved.
**Covers:** Failure/edge path · UX03/UI03 — release gate
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR44 — Progressive first-run to discovery

### TS158 — Member reaches Discover within 5 screens and under 3 minutes, only location mandatory
**Traces from:** FR44 (BR14, BR02) · **Layer:** E2E · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member already signed in through the parent ForKhatri platform opens Vyapar for the first time, when they proceed through first-run skipping every optional step, then they land on Discover within 5 screens and under 3 minutes, having been required to provide only their location.
**Covers:** Success path · UX02/UI02 — first-run journey
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS159 — Location permission denied falls back to manual locality entry
**Traces from:** FR44 (BR14, BR02) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member denies the browser location permission during first-run, when the denial is recorded, then they are shown a manual locality entry field instead of being blocked.
**Covers:** Failure/edge path · UX02/UI02 — location-denied fallback
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS160 — "I'm not sure yet" routes to Explore and Near You with a capability-first prompt
**Traces from:** FR44 (BR14, BR02) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member selects "I'm not sure yet" on the first first-run screen, when they finish first-run, then they land on Discover with Explore and Near You sections shown first, alongside a capability-first enrichment prompt.
**Covers:** Failure/edge path · UX02/UI02 — "not sure yet" path
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS161 — None of the 5 first-run screens is a sign-up, login, or OTP sign-in screen
**Traces from:** FR44 (BR14, BR02) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given the 5 first-run screens are enumerated, when each is inspected, then none of them is a sign-up, login, or OTP sign-in screen — those belong solely to the parent ForKhatri platform (FR50) and are never rendered by Vyapar.
**Covers:** Success path · UX01/UI01 (scope boundary), UX02/UI02
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR45 — Event instrumentation with outcome levels

### TS162 — Structured analytics event emitted with pseudonymous id and level tag, received within 60 seconds
**Traces from:** FR45 (BR15) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member views a Listing detail, when the view is recorded, then a structured analytics event with pseudonymous member id, object id, surface, timestamp, and the "view" level tag is emitted and received by the platform analytics pipeline within 60 seconds.
**Covers:** Success path · Cross-flow conventions §Instrumentation
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS163 — Pipeline unavailable buffers locally up to 24 hours then drops with a count metric
**Traces from:** FR45 (BR15) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given the analytics pipeline is unavailable, when events accumulate locally for 24 hours with no successful delivery, then they are dropped and a count metric records how many were dropped.
**Covers:** Failure/edge path · Cross-flow conventions §Instrumentation
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS164 — Withdrawn behavioural-analytics consent emits only the operational minimum
**Traces from:** FR45 (BR15) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member has withdrawn behavioural-analytics consent (FR37), when they interact with any MOD01 surface, then only operational state-change events are emitted, with no behavioral (impression/view/save/share) events.
**Covers:** Failure/edge path · UX22/UI22 — consent-scoped instrumentation
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR46 — Marketplace health metrics view

### TS165 — Metrics view computes from FR45 events with a minimum group size of 10
**Traces from:** FR46 (BR15, BR16) · **Layer:** Integration · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given an operator with the analytics permission selects a period, when the metrics view renders, then Relevant Opportunity Connections, Opportunity Coverage, Relevant Discovery Rate, and the other named metrics are computed from FR45 events alone, each aggregated with a minimum group size of 10.
**Covers:** Success path · UX23/UI23 — marketplace health metrics
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS166 — Groups under 10 suppressed; profile-completion percentage never offered as a metric
**Traces from:** FR46 (BR15, BR16) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a metric segment has fewer than 10 underlying records, when the metrics view renders, then that segment is suppressed rather than shown with a misleadingly small sample; given the metric list is inspected, when it renders, then "profile completion %" never appears among the offered metrics.
**Covers:** Failure/edge path · UX23/UI23 — suppression / excluded metric
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR47 — Verification queue in the Admin Console

### TS167 — Queue lists Pending Review oldest-first with age against the 3-day target; decision applies within 5 seconds
**Traces from:** FR47 (BR16, BR03) · **Layer:** E2E · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given several BusinessVerificationRecords are Pending Review, when an operator opens the queue, then they are listed oldest-first with age shown against the 3-business-day target, and when the operator decides Verify/Reject, the decision applies to the Listing (FR08/FR10) within 5 seconds.
**Covers:** Success path · UX19/UI19 — verification queue
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS168 — Operators without the verification permission cannot open evidence
**Traces from:** FR47 (BR16, BR03) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an operator lacks the verification permission, when they attempt to open a queue record's evidence, then access is denied.
**Covers:** Failure/edge path · UX19/UI19 — permission-gated evidence
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS169 — Records past the 3-day target are highlighted; identity images auto-delete per FR08
**Traces from:** FR47 (BR16, BR03) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a queue record has been Pending Review for more than 3 business days, when the queue renders, then it is visually highlighted as overdue; given a decision's 30-day retention window (FR08) elapses, when the deletion job runs, then the identity image is auto-deleted.
**Covers:** Failure/edge path · UX19/UI19 — overdue highlight / auto-delete
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR48 — Opportunity review, stale queue, and taxonomy management

### TS170 — Three operation areas (review queue, stale queue, taxonomy) offer their defined actions
**Traces from:** FR48 (BR16, BR04) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an operator with the content permission opens operations, when they view the Opportunity review queue, the Stale/Expired queue, and taxonomy management in turn, then Approve/Return/Remove, bulk Remind/Expire, and add/merge/rename/map actions respectively are all available and effective.
**Covers:** Success path · UX23/UI23 — operations areas
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS171 — Merging taxonomy terms preserves both labels as aliases
**Traces from:** FR48 (BR16, BR04) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an operator merges taxonomy term "CA" into "Chartered Accountant", when the merge completes, then both labels remain searchable as aliases of the same concept.
**Covers:** Success path · UX23/UI23 — taxonomy merge
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS172 — Bulk actions require confirmation with counts; taxonomy edits never alter member-entered text
**Traces from:** FR48 (BR16, BR04) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an operator selects a bulk Expire action on 40 stale records, when they trigger it, then a confirmation showing the exact count (40) is required before it applies; given a taxonomy rename is applied, when it completes, then no member-entered free text is altered.
**Covers:** Failure/edge path · UX23/UI23 — bulk confirmation / text preservation
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR49 — Commercial administration and audit review

### TS173 — Product/price version management never edits a version with existing orders; audit log searchable
**Traces from:** FR49 (BR16, BR10, BR11) · **Layer:** Integration · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a price version already has orders against it, when an operator attempts to edit it, then the edit is rejected and a new version must be created instead; given the audit log is searched by actor, object, action, and date, when the search runs, then matching entries are returned.
**Covers:** Success path · UX23/UI23 — versioning / audit search
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS174 — Refund exceeding the order value is rejected
**Traces from:** FR49 (BR16, BR10, BR11) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given an operator attempts to process a refund larger than the original order value, when they submit it, then the request is rejected.
**Covers:** Failure/edge path · UX23/UI23 — refund bound
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS175 — Commercial administration cannot change verification state, organic relevance, or safety decisions
**Traces from:** FR49 (BR16, BR10, BR11) · **Layer:** Unit · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given an operator is in commercial administration, when they inspect the available actions, then no action exists there that changes a Listing's verification state, organic relevance/ranking, or a Trust & Safety decision — diagnostics show the reason for exclusion, not an override control.
**Covers:** Failure/edge path · UX23/UI23 — no cross-domain override
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR50 — Identity & Trust integration

### TS176 — MOD01 reads canonical identity via the versioned read contract and stores only the member id as a foreign key
**Traces from:** FR50 (BR17) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member enters MOD01, when the Identity Bridge resolves their session, then MOD01 reads the canonical member id, display name, platform trust level, and VerifiedCredential references through the versioned read contract, and stores only the member id as a foreign key on MOD01 records.
**Covers:** Success path · UX01/UI01 — identity consumption
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS177 — Identity & Trust unavailable degrades valid sessions to read-only for up to 15 minutes with a banner
**Traces from:** FR50 (BR17) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given Identity & Trust becomes unreachable while a member holds a valid platform session, when they continue using Vyapar, then they continue read-only for up to 15 minutes with a visible banner, and no Vyapar-owned local authentication fallback is offered.
**Covers:** Failure/edge path · UX01/UI01, UX03/UI03 — read-only degradation
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS178 — Unauthenticated visitor is sent to the platform sign-in and returned to FR44/Discover, with no Vyapar login rendered
**Traces from:** FR50 (BR17) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a visitor with no valid platform session opens Vyapar, when the entry point resolves, then they are redirected to the parent platform's sign-in with a `return_to` target, and upon successful platform sign-in they land on Vyapar's first-run (FR44) or Discover — at no point does Vyapar render its own login/signup/OTP-sign-in screen.
**Covers:** Success path · UX01/UI01 — no local login
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS179 — MOD01 never creates, duplicates, or modifies platform identity data
**Traces from:** FR50 (BR17) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given MOD01 processes a member's identity read, when the read completes, then no write, duplicate, or modification is made to any platform Identity & Trust record from MOD01 — the identity bridge is read-only.
**Covers:** Success path · UX01/UI01 — read-only identity bridge
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR51 — Direct payment-gateway integration (self-contained V1)

### TS180 — Payment order created with hosted/tokenized checkout and an idempotency key per order
**Traces from:** FR51 (BR17, BR10, BR11) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Promotion enters Awaiting Payment, when the order is created, then it uses the licensed gateway's hosted/tokenized checkout and carries a unique idempotency key.
**Covers:** Success path · UX20/UI20 — payment order creation
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS181 — Unverified webhook signature is rejected and logged
**Traces from:** FR51 (BR17, BR10, BR11) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a payment webhook arrives with an invalid or missing signature, when it is processed, then it is rejected and the rejection is logged, and no order state changes as a result.
**Covers:** Failure/edge path · UX20/UI20 — webhook signature guard
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS182 — Duplicate webhook for the same order is ignored via the idempotency key
**Traces from:** FR51 (BR17, BR10, BR11) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a payment webhook is delivered twice for the same order with the same idempotency key, when both are processed, then exactly one state update is applied and no duplicate charge/credit results.
**Covers:** Failure/edge path · UX20/UI20 — idempotent webhook handling
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS183 — Raw card/bank credentials never reach MOD01; only reference/amount/state are stored
**Traces from:** FR51 (BR17, BR10, BR11) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a payment completes through the gateway's hosted checkout, when the resulting order record is inspected, then it contains only the gateway order/payment reference, amount, tax, currency, and state — no raw card or bank credential field exists anywhere in MOD01's schema.
**Covers:** Success path · UX20/UI20 — no raw credential storage
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR52 — Loosely coupled platform and adjacent-module contracts

### TS184 — Active Listing/Opportunity index published to Search and removed on state change within 5 seconds
**Traces from:** FR52 (BR17, BR12) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Listing becomes Active, when it is indexed, then a document is published to Search; given it later becomes Suspended, when the state change is recorded, then the index document is removed within 5 seconds.
**Covers:** Success path · Cross-flow conventions — Search contract
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS185 — MOD05 read-summary requests are rejected if they ask for a private field
**Traces from:** FR52 (BR17, BR12) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given MOD05 requests a field outside the approved public-fields contract (e.g., a private contact channel), when the request is evaluated, then it is rejected by contract rather than served.
**Covers:** Failure/edge path · Cross-flow conventions — MOD05 read-only contract
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS186 — MOD04 referral is sent only on explicit "Refer to Counsel" with consent, carrying no appointment or payment state
**Traces from:** FR52 (BR17, BR12) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member taps "Refer to Counsel" and confirms consent, when the referral is sent to MOD04, then its payload contains only member id, problem summary, and consent flag — no appointment or payment state field is present.
**Covers:** Success path · UX12/UI12 — MOD04 referral contract
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS187 — Retry exhaustion parks an item in the dead-letter list without corrupting MOD01 state
**Traces from:** FR52 (BR17, BR12) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an outbound call to an adjacent service exhausts its retries, when the final retry fails, then the item is parked in the dead-letter list visible in FR49, and MOD01's own domain state remains internally consistent (no partial write).
**Covers:** Failure/edge path · UX23/UI23 — dead-letter visibility
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR53 — Privacy notice, terms, and grievance contact

### TS188 — Versioned notice and terms presented and acceptance recorded before first publish/enquiry
**Traces from:** FR53 (BR18, BR12, BR13) · **Layer:** Integration · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member has never accepted the current privacy notice/terms version, when they attempt to publish a Listing/Opportunity or submit an Enquiry, then the versioned notice and terms are presented in their language, and acceptance with version and timestamp is recorded before the action proceeds.
**Covers:** Success path · UX03/UI03 — terms gate
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS189 — Declining terms keeps the member in read-only discovery
**Traces from:** FR53 (BR18, BR12, BR13) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member declines the terms gate, when they continue using Vyapar, then they remain in read-only discovery — browsing works, but publishing and enquiring stay blocked.
**Covers:** Failure/edge path · UX03/UI03 — decline-to-read-only
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS190 — Grievance/takedown-appeal process is visible from every Report and moderation-outcome screen
**Traces from:** FR53 (BR18, BR12, BR13) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member opens the Report flow or a moderation-outcome screen, when either renders, then the grievance/contact channel and the takedown/appeal process description are visible on it.
**Covers:** Success path · UX15/UI15 — grievance visibility
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS191 — New notice version triggers re-prompt without deleting acceptance history
**Traces from:** FR53 (BR18, BR12, BR13) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a new privacy notice version is published, when a previously-accepted member next attempts a gated action, then they are re-prompted to accept the new version, and their prior acceptance record is retained, not deleted.
**Covers:** Failure/edge path · UX03/UI03 — version re-prompt
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR54 — Commercial disclosure and renewal transparency

### TS192 — "Sponsored" label shown in the member's language wherever paid placement is displayed
**Traces from:** FR54 (BR18, BR10, BR11) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Boosted Listing card appears on any surface (search, Discover, detail), when it renders for a Hindi-preference member, then it carries the `Sponsored` label rendered in Hindi.
**Covers:** Success path · UX06/UI06, UX07/UI07, UX08/UI08 — Sponsored labelling
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS193 — Purchase or renewal requires a one-screen disclosure with explicit confirmation before any charge
**Traces from:** FR54 (BR18, BR10, BR11) · **Layer:** E2E · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member initiates a Boost purchase, when the disclosure screen (full price with tax, duration, what changes/doesn't, renewal terms, cancellation/refund rules) is shown, then no order is created and no gateway charge is attempted until the member explicitly confirms that exact screen.
**Covers:** Success path · UX20/UI20 — disclosure-before-charge
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS194 — No pre-selected renewal for one-time products; 3-day reminder gates automatic renewal
**Traces from:** FR54 (BR18, BR10, BR11) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member purchases a one-time Boost, when the purchase screen renders, then no auto-renewal option is pre-selected; given an auto-renewing product's reminder fails to send 3 days before renewal, when the renewal date arrives, then renewal is paused with a notice rather than silently proceeding.
**Covers:** Failure/edge path · UX20/UI20 — renewal gating
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## FR55 — Opportunity detail, member actions, and Activity

### TS195 — Detail shows all required elements; primary action adapted to type per FR22 mapping
**Traces from:** FR55 (BR06, BR04, BR07) · **Layer:** E2E · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member opens an Employment Opportunity and, separately, a Public/External Opportunity, when each detail view renders, then the first shows the full field set with primary action "Apply" (routed through FR22), and the second shows "Apply on source website" with a leave-app notice instead.
**Covers:** Success path · UX09/UI09 — Opportunity Detail
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS196 — "Not interested" captures one structured reason and hides the item immediately
**Traces from:** FR55 (BR06, BR04, BR07) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member taps "Not interested" on an Opportunity and selects reason "Too far", when they confirm, then the item is hidden from their feed immediately and the reason is recorded for FR38.
**Covers:** Success path · UX09/UI09 — Not interested
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS197 — Activity screen lists Saved, Responded, Shared, Posted, Recently viewed, and Completed grouped by state
**Traces from:** FR55 (BR06, BR04, BR07) · **Layer:** E2E · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member has Saved one Opportunity, Responded to another, Shared a third, Posted a fourth, viewed a fifth, and completed a sixth, when they open Activity, then all six groups render, each showing exactly the item that belongs to it.
**Covers:** Success path · UX11/UI11 — Activity groups
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS198 — Opportunity no longer Active shows its state and disables the primary action on detail
**Traces from:** FR55 (BR06, BR04, BR07) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an Opportunity has moved to Closed, when a member opens its detail view, then the detail shows the Closed state and the primary action is disabled rather than actionable.
**Covers:** Failure/edge path · UX09/UI09 — inactive-detail state
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS199 — External link opens with a leave-app notice and is recorded; Share of a Removed item is blocked
**Traces from:** FR55 (BR06, BR04, BR07) · **Layer:** Unit · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member taps "Apply on source website" on a Public/External Opportunity, when they confirm, then a leave-app notice is shown, the source opens, and the action is recorded; given a member attempts to Share an Opportunity that is Removed, when they attempt it, then the Share action is blocked.
**Covers:** Failure/edge path · UX09/UI09 — external link / blocked share
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## Standing invariant guard scenarios (INV01–INV15)

These 15 scenarios exist specifically to guard the standing product invariants named in the brief. Each is additionally tagged `INVARIANT` alongside its test-pyramid layer, and traces to the FR that owns the underlying rule (already counted in that FR's Coverage-check row above).

### TS200 — INVARIANT: the three trust axes never collapse into one signal
**Traces from:** FR10, FR28, FR54, FR19 (INV01) · **Layer:** Unit · **Tag:** INVARIANT · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a Listing that is simultaneously Verified, Sponsored, and carries 12 recommends, when its trust display renders, then the verification badge, the `Sponsored` label, and the reputation counts render as three independent elements with no combined badge or score, and given the Sponsored boost later ends, when the display re-renders, then the verification state and reputation counts are unchanged.
**Covers:** Success path · UX07/UI07 — three-axis independence
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS201 — INVARIANT: exactly four verification documents; Aadhaar never appears
**Traces from:** FR08 DEC-002 (INV02) · **Layer:** Unit · **Tag:** INVARIANT · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given the verification document menu is enumerated across every entry point (FR08, FR47 operator view, UX14), when each is inspected, then exactly {GST/GSTIN, Udyam, PAN, Shops & Establishment} are offered and Aadhaar appears in no field, label, dropdown, or upload option anywhere.
**Covers:** Success path · UX14/UI14, UX19/UI19 — document-menu invariant
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS202 — INVARIANT: seeking visibility has exactly two states, never a third
**Traces from:** FR05 (INV03) · **Layer:** Unit · **Tag:** INVARIANT · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given the seeking-visibility data model and every UI control that sets it (UX02, UX13) are enumerated, when their possible values are inspected, then exactly two values exist — private (default) and visible to everyone on Vyapar — and no intermediate value (e.g. "businesses only") exists anywhere.
**Covers:** Success path · UX13/UI13 — two-state invariant
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS203 — INVARIANT: contact is disclosed only after enquiry acceptance, never before
**Traces from:** FR24 (INV04) · **Layer:** Integration · **Tag:** INVARIANT · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an Enquiry in any state other than In Progress/Resolved/Closed-following-acceptance, when the enquirer views the thread at each such state in turn, then no contact channel is disclosed in any of them, regardless of the provider's per-channel setting.
**Covers:** Success path · UX12/UI12 — pre-acceptance non-disclosure
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS204 — INVARIANT: Businesses & Professionals returns results with zero Opportunities in the system
**Traces from:** FR15 (INV05) · **Layer:** Integration · **Tag:** INVARIANT · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given the database holds Active Listings and exactly zero Opportunity records of any state, when a member searches Businesses & Professionals, then results are returned exactly as if Opportunities existed, with no dependency, join, or feature-flag check against Opportunity data anywhere in the query path.
**Covers:** Success path · UX06/UI06 — standalone-surface invariant
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS205 — INVARIANT: "Refer to Counsel" sends only the explicit consented referral
**Traces from:** FR52(f), FR23 (INV06) · **Layer:** Integration · **Tag:** INVARIANT · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an open Enquiry thread with N prior messages and state In Progress, when a party taps "Refer to Counsel" and confirms consent, then exactly one referral payload (member id, problem summary, consent flag) is sent to MOD04, and the thread's message count, state, and every other field are identical before and after the tap.
**Covers:** Success path · UX12/UI12 — referral-scope invariant
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS206 — INVARIANT: every Opportunity carries a mandatory source segment
**Traces from:** FR11 (INV07) · **Layer:** Unit · **Tag:** INVARIANT · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a save attempt for an Opportunity record with no Community/Public-External segment tag, when the save is attempted, then it is rejected; given a save attempt tagged Public/External with no source name or URL, when the save is attempted, then it is also rejected.
**Covers:** Failure/edge path · UX10/UI10 — mandatory-segment invariant
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS207 — INVARIANT: freshness/staleness/expiry timers fire at documented day counts and vanish within 5 seconds
**Traces from:** FR13 (INV08) · **Layer:** Integration · **Tag:** INVARIANT · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given an Opportunity was last confirmed exactly 21 days ago, when the freshness job runs, then it is marked Stale, and when the FR18 feed is queried within 5 seconds of that state change, then the record is absent from every section.
**Covers:** Success path · UX08/UI08 — timer/exclusion invariant
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS208 — INVARIANT: notification fatigue caps hold even under a strong match
**Traces from:** FR21 (INV09) · **Layer:** Unit · **Tag:** INVARIANT · **Priority:** Should · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member has already received exactly 3 opportunity notifications today, when a new Opportunity scores well above the strong-match threshold for them, then no notification is sent — the match is queued for the daily digest regardless of how strong the match is.
**Covers:** Failure/edge path · UX18/UI18 — fatigue-cap invariant
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS209 — INVARIANT: no raw card data reaches MOD01; idempotency key prevents duplicate charges
**Traces from:** FR51 (INV10) · **Layer:** Integration · **Tag:** INVARIANT · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a payment webhook for one order is redelivered twice with the same idempotency key, when both deliveries are processed, then exactly one charge/state-update is applied, and given the resulting order record's schema is inspected, then no field capable of holding a card number, CVV, or bank account number exists.
**Covers:** Success path · Failure/edge path · UX20/UI20 — payment-integrity invariant
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS210 — INVARIANT: data-rights requests complete within SLA and deletion anonymizes counterpart records
**Traces from:** FR37 (INV11) · **Layer:** Integration · **Tag:** INVARIANT · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given a member requests export, correction, consent withdrawal, and deletion in turn, when each completes, then export finishes within 72 hours, correction/withdrawal are immediate, and deletion completes within 30 days while anonymizing (not deleting) the member's counterpart's enquiry/review records.
**Covers:** Success path · UX22/UI22 — data-rights SLA invariant
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS211 — INVARIANT: adjacent-module contracts stay minimum-field and one-way
**Traces from:** FR52 (INV12) · **Layer:** Unit · **Tag:** INVARIANT · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given the MOD05 read-summary payload schema and the MOD04 referral payload schema are each inspected, when they are compared against the approved field lists, then the MOD05 payload contains no private field (contact, private intent) and the MOD04 payload contains no appointment or payment state field.
**Covers:** Success path · Cross-flow conventions — contract-shape invariant
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS212 — INVARIANT: ranking hard constraints precede scoring and the signal allow-list is never violated
**Traces from:** FR19 (INV13) · **Layer:** Unit · **Tag:** INVARIANT · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given two Opportunities identical in every scored field but differing in the provider's community status, account age, and report count, when both are scored, then their scores are byte-identical, proving those three prohibited signals were never read by the scorer at any stage.
**Covers:** Success path · UX08/UI08 — allow-list invariant
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS213 — INVARIANT: FR50 identity consumption never forks or duplicates authentication
**Traces from:** FR50 (INV14) · **Layer:** Integration · **Tag:** INVARIANT · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given Identity & Trust is unreachable for a visitor with no cached session, when they open Vyapar, then no Vyapar-rendered login/signup screen appears — only a redirect to the platform sign-in — and given the service recovers minutes later, when MOD01's identity records are inspected, then no duplicate or locally-created identity record exists for that visitor.
**Covers:** Success path · UX01/UI01 — no-local-auth invariant
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

### TS214 — INVARIANT: no star ratings or numeric aggregate score ever renders anywhere reputation appears
**Traces from:** FR28 (INV15) · **Layer:** Unit · **Tag:** INVARIANT · **Priority:** Must · **Status:** Approved · **Confidence:** High
**Scenario:** Given every surface where reputation is displayed (listing card, detail, search result card, "Why this?" panel, moderation/report screens) is enumerated, when each is rendered, then none contains a star icon, a 1–5 average, or any single numeric aggregate score — only the contextual counts and tags defined in the trust-label vocabulary.
**Covers:** Success path · UX06/UI06, UX07/UI07, UX09/UI09 — no-aggregate-score invariant
**Approval:** Product Manager — [x] Approved — autonomous execution, 2026-09-14

---

## Closing note for Step 6

This file is Sealed with all 214 scenarios (TS001–TS214) approved under the module's standing autonomous-execution mode (product owner direction, 2026-09-14: "never wait for me ... complete this application developing as continuous chain"). Every FR01–FR55 has scenario coverage tied to its Requirement/Success/Failure/Acceptance-criteria text and its matching UX/UI screen; the 15 standing product invariants named in the brief each have a dedicated INVARIANT-tagged scenario (TS200–TS214) in addition to being exercised implicitly by their owning FR's own scenarios. The test-pyramid distribution (65.4% Unit / 28.0% Integration / 6.5% E2E) is Unit-heavy and examined, not E2E-dominated, per the Set-level quality gate above. No scenario in this file exercises a Vyapar-owned login/signup/OTP-login/session/logout flow — FR50 is tested only as identity *consumption*, and FR07's OTP is tested only as listing-contact verification — consistent with the FR/UX/UI files' own scope correction. Step 6 (Impact Analysis) may now loop over every FR and assess dependencies/risk against this scenario set.
