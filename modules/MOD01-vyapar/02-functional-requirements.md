---
step: 02-functional-requirements
module: MOD01
status: Sealed
approver: Product Manager
updated: 2026-09-12
items: "55 | approved: 55 | blockers: 0"
---

# 02 - Functional Requirements - MOD01 Vyapar

## Revision history

| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-12 | Initial full decomposition of the 18 Sealed BRs into 54 lean, incrementally buildable FRs. Written tersely by Product Manager direction ("complete it fast"): near-identical CRUD/lifecycle variants are consolidated into single FRs with parameterized acceptance criteria rather than split into near-duplicates. | `01-business-requirements.md` Sealed 2026-09-12; PM speed/leanness directive. |
| 2026-09-12 | Approver check (Product Manager role) on the full file. Corrections: FR03 now requires the FR07 OTP check before a Listing leaves Draft (was inconsistent); FR08 drops Aadhaar from the V1 document menu after checking UIDAI's offline-verification rules (storing Aadhaar images/numbers is not a compliant path for a private entity) - four options remain; FR23 gains the "Refer to Counsel" action so FR52(f) has a user-facing trigger; FR35 priority raised Could -> Should to match BR11 and the pricing model's V1 "Campaign foundation"; FR44 clarified as 5 screens after authentication; FR45 consent reference corrected to FR37. Gap found and filled: no FR specified the Opportunity detail screen, its actions/feedback, or the Activity screen - added FR55 under BR06 (55 FRs total); BR06's Traced-to updated in the Step 1 file and BR03 gains DEC-004 for the Aadhaar refinement. | "act as approver and do check" - Product Manager. |
| 2026-09-13 | Post-seal vocabulary refinement on Product Manager direction ("look over existing applications and inspire the words"): FR22's typed actions renamed so stored type = label (Enquire / Apply / Propose / Contact / Register) using words verified on Sulekha, Naukri, Apna, Upwork and IndiaMART (FR22 DEC-002); FR16 primary is "Enquire Now"; FR55 primary labels aligned; FR28 responsiveness cue worded "Responds in ~X". No behaviour changed. Resolves the Step 4 Fidelity flag on FR22. | Product Manager, during Step 4 review. |

## Scope of this step

Decomposes every approved BR in `01-business-requirements.md` into testable,
singular functional requirements in ISO 29148 sentence form. Carries forward
the three Step 1 review decisions verbatim: (1) standalone business/professional
discovery is first-class scope (grounded in `modules/modules.md`), not
supply-side infrastructure for opportunities; (2) the MOD04 Counsel exclusion is
only structured counselling/mentorship/paid-appointment advisory; (3) V1
verification is a phone/OTP baseline plus one member-chosen document from a
short menu, never a mandatory GSTIN. FRs are ordered so Step 9 can build in
visible slices: profiles -> discovery -> opportunities -> enquiries -> trust ->
commercial -> operations.

## Coverage check

| Parent BR | FRs produced | Covered |
|---|---|---|
| BR01 Business Profile | FR01, FR02, FR03 | Yes |
| BR02 Professional Listing | FR04, FR05, FR06 | Yes |
| BR03 Level-3 Verification | FR07, FR08, FR09, FR10 | Yes |
| BR04 Opportunity Creation & Lifecycle | FR11, FR12, FR13, FR14 | Yes |
| BR05 Discovery | FR15, FR16, FR17 | Yes |
| BR06 Ranking & Distribution | FR18, FR19, FR20, FR21, FR55 | Yes |
| BR07 Enquiries & Responses | FR22, FR23, FR24 | Yes |
| BR08 Partnership Requests | FR25, FR26 | Yes |
| BR09 Reviews & Reputation | FR27, FR28, FR29 | Yes |
| BR10 Promotion | FR30, FR31, FR32 | Yes |
| BR11 Business Workspace | FR33, FR34, FR35 | Yes |
| BR12 Privacy & Consent | FR36, FR37, FR38 | Yes |
| BR13 Trust & Safety | FR39, FR40, FR41 | Yes |
| BR14 Accessibility & Localization | FR42, FR43, FR44 | Yes |
| BR15 Analytics | FR45, FR46 | Yes |
| BR16 Administration | FR47, FR48, FR49 | Yes |
| BR17 Platform Contracts | FR50, FR51, FR52 | Yes |
| BR18 Compliance Awareness | FR53, FR54 | Yes |

## Set-level quality gate

| Check | Result |
|---|---|
| Comprehensive - every BR covered | Pass - no blank Coverage rows. |
| Consistent | Pass - one vocabulary (Listing, Opportunity, Enquiry, Partnership Request, Review, Promotion, Entitlement) used throughout; no FR narrows discovery below BR05's standalone scope. |
| Prioritized | Pass - every FR inherits or refines its BR priority. |
| No duplicates | Pass - lifecycle/CRUD variants are consolidated, not repeated. |
| Human approval present | Pass - Product Manager explicitly approved all 55 FRs (including FR55) on 2026-09-12 after the approver check; file Sealed. |

## Open blockers

None.

## Shared definitions (used by every FR below)

- **Listing** = a BusinessProfile or ProfessionalListingProfile.
- **Member** = an authenticated ForKhatri identity supplied by Identity & Trust.
- **Operator** = a staff role in the unified Admin Console with a named permission.
- **Audit event** = actor, timestamp, object id, action, reason code, outcome, written append-only to the platform Audit service.
- Every FR that changes state records an Audit event; this is not repeated per FR.
- Every FR that writes data enforces server-side authorization; this is not repeated per FR.

---

## BR01 - Business Profile and Business Presence

### FR01 - Create and edit a BusinessProfile
**Traces from:** BR01 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When an authenticated member starts business setup, the system shall create one BusinessProfile owned by that member with business name, description, categories/services (from the platform taxonomy plus free text), operating locality or service area, service mode (on-site / remote / both), contact channels, enquiry preference, and opportunity-participation flag, saving it in Draft within 2 seconds of each save.

**Intent:** Durable, reusable business presence instead of one-off posts.

**Success outcome:** Draft BusinessProfile exists, editable, visible only to its owner until submitted (FR03).

**Failure / edge outcome:** Missing mandatory field (name, at least one category, locality) blocks submission with an inline field-level message; save failure preserves entered values client-side and shows retry; a member may own multiple BusinessProfiles only if each has a distinct name + locality pair, otherwise the system offers to edit the existing one.

**Acceptance criteria**
- [ ] Draft created with the fields above; mandatory-field validation shown inline.
- [ ] Unverified member-provided fields are labelled "member-provided" on later display.
- [ ] Duplicate name + locality for the same owner is rejected with an edit-existing option.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions:** DEC-001 · Facing a rich profile vs. a fast first save, we chose a three-question minimum (what, where, how to contact) with everything else optional, to reach discovery quickly, accepting thinner initial listings.

**Assumptions:** Taxonomy is a platform-shared reference list editable via FR48.

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR02 - Business contact and visibility controls
**Traces from:** BR01 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When the owner opens BusinessProfile settings, the system shall let them set, per contact channel, whether it is shown publicly, shown only after an enquiry is accepted, or hidden, and whether the listing is discoverable in search, applying the change to all surfaces within 5 seconds.

**Intent:** Owner controls disclosure; no contact leakage.

**Success outcome:** Search results, listing detail, MOD05 summaries, and enquiry threads all honor the setting.

**Failure / edge outcome:** If every channel is hidden and enquiries are disabled, the system warns that customers cannot reach the business and requires explicit confirmation; a stale cached surface must never show a channel newer than 5 seconds after it was hidden.

**Acceptance criteria**
- [ ] Per-channel disclosure levels: Public / After accepted enquiry / Hidden.
- [ ] "Discoverable in search" toggle removes the listing from FR15 results when off.
- [ ] Hidden channels never appear in the MOD05 read-side summary (FR52).

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Assumptions:** Default for a new listing is Public discovery, contact After accepted enquiry.

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR03 - Listing lifecycle (submit, activate, suspend, archive)
**Traces from:** BR01, BR02 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When the owner submits a Draft Listing, the system shall move it to Active-Unverified immediately if its primary mobile number is OTP-verified (FR07) and it passes mandatory-field and automated safety checks (prohibited-content wordlist, spam pattern), otherwise to Submitted for operator review; when an operator suspends or the owner archives a Listing, the system shall stop its distribution within 5 seconds while retaining its record and audit history.

**Intent:** Members get value immediately; unsafe content is held; nothing is destroyed.

**Success outcome:** Lifecycle Draft -> Submitted/Active-Unverified -> Active-Verified (FR08/FR09) -> Suspended -> Archived is enforced; state and "Unverified"/"Verified" label are always shown together, never conflated.

**Failure / edge outcome:** Safety-check failure shows the reason category (not the wordlist) and routes to FR40; a Suspended listing's owner sees the reason code and appeal path (FR41); archiving a listing with open enquiries closes them with a notice to the enquirers.

**Acceptance criteria**
- [ ] All state transitions above are enforced server-side; illegal transitions rejected.
- [ ] Suspended/Archived listings disappear from FR15/FR18 within 5 seconds.
- [ ] Verified and unverified listings are visually distinct on every surface.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Assumptions:** The same lifecycle applies to ProfessionalListingProfile (BR02) - this FR is shared.

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR02 - Professional and Freelancer Listing Presence

### FR04 - Create and edit a ProfessionalListingProfile with progressive setup
**Traces from:** BR02 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When an authenticated member starts professional setup, the system shall create a ProfessionalListingProfile after a maximum of three required steps (what I can do/offer, where/how I work, contact preference) and shall let the member reach Discover before completing optional fields (experience, services, languages, availability, evidence links, rates).

**Intent:** Show value before demanding a full resume.

**Success outcome:** Member reaches Discover within the three steps; profile shows an "Opportunity Readiness" list of high-value missing fields, never a completion percentage.

**Failure / edge outcome:** Free-text capability that maps to no taxonomy concept is stored as an unmapped label, still searchable by text, and queued for taxonomy review (FR48); a member who abandons after step one keeps a Draft and is prompted once on next open.

**Acceptance criteria**
- [ ] Three required steps only; every other field optional.
- [ ] Structured choice plus free-text escape hatch for capabilities.
- [ ] "Opportunity Readiness" shown instead of a completion %.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Assumptions:** A member may hold both a BusinessProfile and a ProfessionalListingProfile.

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR05 - Capability visibility separate from opportunity-seeking visibility
**Traces from:** BR02, BR12 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a member sets an intent state (Looking for / Open to / Curious about / Not interested) on their ProfessionalListingProfile, the system shall store it as private by default and shall never display it on the listing, in search, or in the MOD05 summary unless the member explicitly sets it to visible, while capability and service fields remain independently controllable.

**Intent:** "I'm an accountant" must be publishable without exposing "I'm looking for work".

**Success outcome:** A customer sees capabilities; only opportunity matching (FR19) uses private intent.

**Failure / edge outcome:** If a member makes seeking status visible, the system shows a one-time explanation of who can see it; withdrawing visibility takes effect on all surfaces within 5 seconds.

**Acceptance criteria**
- [ ] Intent states default to private; visible only on explicit opt-in.
- [ ] Search/detail/MOD05 never render private intent.
- [ ] Capability visibility and seeking visibility are two independent settings.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR06 - Shared VerifiedCredential reference, distinct from Counsel ExpertProfile
**Traces from:** BR02, BR03, BR17 · **Priority:** Should · **Status:** Ready for Review · **Confidence:** Medium - depends on the Identity & Trust read contract.

**Requirement:** When a member's Identity & Trust record holds a VerifiedCredential, the system shall let the member attach a read-only reference to it on their ProfessionalListingProfile and display the credential's claim, issuer, and verification date, without copying the evidence and without linking, merging, or exposing any MOD04 Counsel ExpertProfile.

**Intent:** One credential truth across modules; no profile merge.

**Success outcome:** Listing shows "Credential verified by ForKhatri: <claim>" sourced live from Identity & Trust.

**Failure / edge outcome:** If Identity & Trust is unavailable, the listing shows the last cached status with a "last checked" time and no error to the viewer; if the credential is revoked upstream, the reference disappears within one sync cycle (<= 1 hour).

**Acceptance criteria**
- [ ] Reference is by id only; no evidence stored in MOD01.
- [ ] Revocation upstream removes the display within 1 hour.
- [ ] No Counsel data is read or shown.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR03 - Level-3 Business and Professional Verification

### FR07 - Phone/OTP contact baseline on every Listing
**Traces from:** BR03 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a Listing is submitted, the system shall require that its declared primary mobile number is verified via a 6-digit OTP (valid 10 minutes, maximum 5 attempts, resend after 30 seconds) before the Listing can leave Draft, reusing the Identity & Trust OTP service.

**Intent:** Universal, low-friction legitimacy baseline matching real comparable apps.

**Success outcome:** "Contact verified" flag set on the Listing; shown as a trust cue.

**Failure / edge outcome:** After 5 failed attempts the number is locked for 15 minutes with a clear message; changing the number later clears the flag until re-verified.

**Acceptance criteria**
- [ ] No Listing leaves Draft without a verified mobile number.
- [ ] OTP limits above enforced; lockout message shown.
- [ ] Number change resets the flag.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR08 - Business-existence document submission and operator review
**Traces from:** BR03 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a Listing owner requests verification, the system shall let them choose exactly one document type from {GST Certificate/GSTIN, Udyam Registration, Business or Personal PAN, Shops & Establishment License}, capture the identifier and/or an image upload (JPG/PNG/PDF <= 5 MB), format-validate the identifier where a format exists (GSTIN 15 chars, PAN 10 chars, Udyam pattern), create a BusinessVerificationRecord in Pending Review, and present it in the operator queue (FR47) with a 3-business-day internal target.

**Intent:** Lightweight, flexible, real-world-aligned verification; no mandatory GSTIN.

**Success outcome:** Operator marks Verified -> Listing becomes Active-Verified showing "Business existence verified (<document type>)" and the verification date; the record stores claim, method, verifier, decision, date, expiry.

**Failure / edge outcome:** Invalid format is rejected inline before submission; operator Rejected returns the Listing to Active-Unverified with a reason code and a re-submit option; PAN uploads are stored encrypted, masked on display (last 4), never shown publicly, and deleted 30 days after decision; Aadhaar is not accepted in any form (no number, no image, no photocopy) in V1 - see DEC-002.

**Acceptance criteria**
- [ ] Exactly one document type per request; all four options selectable; Aadhaar is not offered anywhere in the flow.
- [ ] Format validation for GSTIN/PAN/Udyam; image upload limits enforced.
- [ ] Operator Verify/Reject with reason; masked storage and 30-day deletion for identity documents.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions:** DEC-001 · Facing registry APIs vs. manual spot-check, we chose manual operator lookup against public GST/Udyam portals for V1, over paid KYC APIs, to ship without vendor dependency, accepting operator effort.
- DEC-002 · Facing Aadhaar as a V1 document option (listed in BR03), we chose to drop Aadhaar from the V1 menu entirely, over storing masked Aadhaar images, because UIDAI's Aadhaar (Authentication and Offline Verification) Regulations 2021 direct verification entities not to collect or store Aadhaar numbers after offline verification (any retained copy must be masked and irretrievable), and UIDAI has since moved to require private entities to register with it and use approved methods (offline QR/XML or API) instead of collecting copies - so a simple image upload is not a compliant path. Checked 2026-09-12: [UIDAI Offline Verification Regulations 2021](https://uidai.gov.in/images/The_Aadhaar_Authentication_and_Offline_Verifications_Regulations_2021.pdf), [PIB: UIDAI urges verification entities to adhere to Aadhaar usage hygiene](https://www.pib.gov.in/PressReleasePage.aspx?PRID=1889996&reg=48&lang=2), [Biometric Update, Dec 2025: UIDAI moves to regulate private-sector verification](https://www.biometricupdate.com/202512/india-to-ban-aadhaar-photocopying-as-uidai-moves-to-regulate-private-sector-verification). Aadhaar offline QR verification via a UIDAI-registered path is explicit future scope if ever needed; the remaining four options already cover registered and unregistered businesses (PAN is available to any individual).

**Assumptions:** PAN is visually reviewed only (no government-database check) in V1, per BR03; Aadhaar is deferred per DEC-002 (BR03 DEC-004 records the refinement).

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR09 - Professional-credential document review
**Traces from:** BR03 · **Priority:** Should · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a ProfessionalListingProfile owner requests credential verification, the system shall accept one credential document (license/certificate image or identifier, <= 5 MB), record the claimed credential name and issuer, create a BusinessVerificationRecord in Pending Review, and on operator decision display "Credential reviewed: <credential name>" or return it to Active-Unverified with a reason.

**Intent:** Scoped, plain-language credential claim; not a blanket "verified professional".

**Success outcome:** Listing shows the specific credential reviewed and date.

**Failure / edge outcome:** Unreadable document -> operator "Needs clearer copy" state prompts re-upload without penalty; expired credential (date on document) -> Rejected with reason.

**Acceptance criteria**
- [ ] One document per request; claim + issuer captured.
- [ ] Display names the specific credential, never "verified professional".
- [ ] "Needs clearer copy" re-upload path exists.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR10 - Verification state display, expiry, and revert
**Traces from:** BR03 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a Listing is displayed anywhere, the system shall show its verification state (Not Started / Pending Review / Verified / Expiring / Expired / Rejected / Revoked / Disputed) as a bounded plain-language label with the claim scope and date; 11 months after a Verified decision the system shall prompt the owner to reconfirm; at 12 months without reconfirmation, or on a report/dispute (FR39) or operator revocation, the system shall revert the displayed claim to unverified within 5 seconds.

**Intent:** Verification is evidence at a time, not a permanent guarantee.

**Success outcome:** Labels never conflate paid, verified, and reputation; expiry and revocation change the label everywhere.

**Failure / edge outcome:** Reconfirmation notification failure does not extend expiry; a Disputed state shows "Under review" to viewers (not the dispute content).

**Acceptance criteria**
- [ ] All eight states render with scope + date.
- [ ] 11-month reminder, 12-month expiry enforced.
- [ ] Report/dispute/revocation reverts label within 5 seconds.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR04 - Member-Originated Opportunity Creation and Lifecycle

### FR11 - Opportunity Composer: create, share, or upload with source segment
**Traces from:** BR04 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When an authenticated member opens Post, the system shall offer three entry modes (Create from a form; Share a pasted URL or text; Upload a screenshot image <= 5 MB) and shall require the member to tag the Opportunity's source segment as Community (my own opportunity) or Public/External (found elsewhere, with the source URL or name), storing the submitting member as attribution on every record.

**Intent:** Simple provenance; WhatsApp forwards become structured inputs.

**Success outcome:** A Draft Opportunity exists with segment + submitter + raw input preserved.

**Failure / edge outcome:** Unsupported file type or size -> inline error; Public/External without any source name/URL -> blocked with "tell us where you found it"; a URL that returns an error is still accepted as a Draft with a "source unreachable" flag for review.

**Acceptance criteria**
- [ ] Three modes available; segment tag mandatory.
- [ ] Submitter and raw input stored on every Opportunity.
- [ ] Public/External requires source name or URL.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions:** DEC-001 · Facing an elaborate provenance system vs. a segment tag, we chose a two-value segment tag plus submitter attribution, per BR04, to keep authoring simple, accepting that source authority is asserted by the member, not by Vyapar.

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR12 - Structured fields, uncertainty marking, and contributor confirmation
**Traces from:** BR04 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a Draft Opportunity is reviewed before publish, the system shall present the structured fields (title, type, description, requirements, value/compensation, location, work mode, timing, eligibility, response method, deadline/expiry) with any field that was inferred from Share/Upload input marked "unconfirmed", and shall not publish until the contributor confirms title, type, location, and response method.

**Intent:** Preserve uncertainty; never present an inferred value as fact.

**Success outcome:** Published Opportunity has confirmed material fields; unconfirmed optional fields display as "not specified".

**Failure / edge outcome:** If inference produced no usable fields (e.g., illegible screenshot), the member is asked to enter the four material fields manually; a Draft older than 7 days without confirmation is auto-archived with one reminder at day 5.

**Acceptance criteria**
- [ ] Inferred fields visibly marked unconfirmed.
- [ ] Publish blocked until title/type/location/response method confirmed.
- [ ] Day-5 reminder, day-7 archive for unconfirmed drafts.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Assumptions:** Inference may be rule-based extraction in V1; AI extraction is optional and never a hot-path dependency.

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR13 - Opportunity lifecycle, freshness, and expiry
**Traces from:** BR04, BR06 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When an Opportunity is published, the system shall manage its state through Active -> Paused / Stale / Expired / Closed / Removed, marking it Stale 21 days after last owner confirmation (with a reminder at day 14), Expired at its stated deadline or 45 days after publish if none, and shall exclude Stale, Expired, Closed, Removed, and Pending Review records from normal distribution (FR18) within 5 seconds of the state change while retaining provenance and audit history.

**Intent:** Stale inventory must never look current.

**Success outcome:** Owner can Pause/Resume/Close/Renew (renew resets freshness); viewers see a freshness stamp on every card.

**Failure / edge outcome:** Renewal of an Expired record older than 90 days requires re-confirmation of material fields (FR12); Removed records show only "removed" plus reason category to the owner.

**Acceptance criteria**
- [ ] Day-14 reminder, day-21 Stale, deadline/day-45 Expired enforced.
- [ ] Non-Active states excluded from FR18 within 5 seconds.
- [ ] Freshness stamp on every card and detail.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR14 - Opportunity types with V1 launch focus
**Traces from:** BR04 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a member selects an Opportunity type, the system shall offer Employment, Freelance/Project, and Local Business/Professional Service as the promoted V1 types, with Business Partnership, Training, and Community/Government available under "Other", and shall render type-specific sections (e.g., compensation for Employment, scope and budget for Freelance/Project, service window for Local Service) on the detail view.

**Intent:** One canonical Opportunity concept; types are patterns, not products.

**Success outcome:** All types share the core schema; V1 types are first in the picker and eligible for FR18 sections.

**Failure / edge outcome:** A type change after publish re-validates type-specific mandatory fields before saving; "Other" types are distributed by search and Community/Public sections but not by proactive notification (FR21) in V1.

**Acceptance criteria**
- [ ] Three promoted types first; others under "Other".
- [ ] Type-specific sections render on detail.
- [ ] "Other" types excluded from proactive notifications in V1.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Assumptions:** Launch geography (Hyderabad/Secunderabad) is configuration, not code.

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR05 - Business, Professional, and Customer Discovery

### FR15 - Standalone Listing search and browse
**Traces from:** BR05 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a member opens the Businesses & Professionals surface (a top-level entry distinct from the Opportunity Discover feed), the system shall let them search by keyword and browse by category, and filter by locality/radius, service mode, availability, verification state, and freshness, returning Active Listings ranked by organic relevance (text match, category match, distance, verification, freshness - configuration-weighted) within 2 seconds for the first 20 results, with no Opportunity required.

**Intent:** Ordinary "find me a plumber / accountant / supplier" discovery, first-class per `modules/modules.md`.

**Success outcome:** Result cards show name, category, locality, verification label, freshness, and a short relevance reason; promoted cards carry a "Sponsored" label (FR30) and never displace organic order.

**Failure / edge outcome:** Search service unavailable -> cached category browse with a "search temporarily unavailable" notice; private contact fields and private seeking state are never in results (FR02, FR05).

**Acceptance criteria**
- [ ] Separate surface from the Opportunity feed; works with zero Opportunities in the system.
- [ ] Filters above; first 20 results within 2 seconds.
- [ ] Sponsored label present; organic order unaffected by payment.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions:** DEC-001 · Facing `Vyapar_02`'s opportunity-only Discover tab vs. the Step 0 boundary, we chose a distinct Businesses & Professionals surface, over folding listings into the opportunity feed, to honor standalone discovery scope, accepting one extra top-level surface for UX to design.

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR16 - Listing detail view with trust context and action
**Traces from:** BR05, BR07 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a member opens a Listing, the system shall display description, services/capabilities, locality/service area, service mode, verification state with claim scope (FR10), reputation signals (FR28), "member-provided" labels on unverified fields, any Sponsored label, contact channels per FR02 disclosure rules, and a primary "Enquire Now" action (FR22), plus Save, Share, and Report (FR39).

**Intent:** Everything needed to evaluate and safely contact a provider on one screen.

**Success outcome:** Viewer can distinguish verified, paid, reputation, and member-provided information at a glance.

**Failure / edge outcome:** Suspended/Archived listing opened from a stale link shows "no longer available" (no data); a listing with enquiries disabled shows the reason and hides the action.

**Acceptance criteria**
- [ ] All elements above present and visually distinct.
- [ ] Contact respects FR02 levels.
- [ ] Stale-link handling.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR17 - Zero-result broadening
**Traces from:** BR05, BR06 · **Priority:** Should · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a Listing search or Opportunity search returns zero results, the system shall state that no exact match exists and offer user-selectable broadening options (widen radius to the next step 5 -> 10 -> 25 km, include adjacent categories, remove one filter, include unverified) and shall not silently relax any user-set hard filter.

**Intent:** Helpful empty states without hidden constraint changes.

**Success outcome:** One tap applies the chosen broadening and re-runs the search, showing which filter changed.

**Failure / edge outcome:** If broadening also yields zero, the system offers "Post what you need" (FR11) and "Notify me when something matches" (FR21).

**Acceptance criteria**
- [ ] No silent relaxation; each broadening is explicit and labelled.
- [ ] Post/notify fallbacks offered after second zero result.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR06 - Opportunity Relevance, Ranking, and Distribution

### FR18 - Opportunity Discover feed sections
**Traces from:** BR06 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a member opens Discover, the system shall present Active Opportunities in five sections - For You (top eligible matches), Explore (adjacent capability/category), Near You (within the member's radius), Community (Community-segment records), Public (Public/External-segment records) - each card showing type, title, location, value/timing, freshness, source segment + submitter, and a one-line relevance reason, loading the first section within 2 seconds.

**Intent:** Relevant opportunities find people who would otherwise miss them.

**Success outcome:** Every card is eligible (FR19) and labelled by segment; Sponsored cards labelled and confined to the eligible audience.

**Failure / edge outcome:** New member with a sparse profile sees Near You + Community + Public plus one enrichment prompt (FR04) instead of an empty For You; a section with no records is hidden, not shown empty.

**Acceptance criteria**
- [ ] Five sections; card fields above; segment visible.
- [ ] Sparse-profile fallback; empty sections hidden.
- [ ] First section within 2 seconds.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR19 - Eligibility-before-ranking with configuration-driven deterministic scoring
**Traces from:** BR06 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When the system builds any Opportunity list for a member, it shall first exclude records failing hard constraints (non-Active state, member exclusions, location outside radius when the opportunity is on-site, eligibility fields the member does not meet, safety restrictions), then score the remainder with a weighted sum of capability fit, intent fit, location fit, timing/availability fit, value fit, experience/eligibility fit, freshness, and trust, with weights read from configuration, then apply diversification so no more than 3 consecutive results share the same provider or type.

**Intent:** Hard constraints are never soft penalties; ranking is explainable and tunable.

**Success outcome:** Identical inputs produce identical rankings; weight changes require no code change.

**Failure / edge outcome:** Missing configuration -> safe defaults logged as a warning; sensitive attributes, community status, account age, paid status, raw popularity, and report signals are never inputs to the score (enforced by the signal allow-list).

**Acceptance criteria**
- [ ] Hard filter precedes scoring; excluded records never appear.
- [ ] Weights in configuration; deterministic output.
- [ ] Signal allow-list excludes the prohibited inputs above; diversification rule enforced.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions:** DEC-001 · Facing ML ranking vs. deterministic scoring, we chose deterministic configuration-weighted scoring, per BR06, to ship explainable relevance on sparse data, accepting less adaptivity.

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR20 - "Why this opportunity" explanation
**Traces from:** BR06 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a member opens an Opportunity's "Why this?" view, the system shall list the top three contributing signals from FR19 in plain language (e.g., "matches your capability: accounting", "within 8 km", "posted 2 days ago") and any important gap (e.g., "requires 3 years experience - you listed 1"), and shall offer a direct link to adjust the related preference, never showing a percentage match score.

**Intent:** Explanations derive from the same signals that rank.

**Success outcome:** Every ranked card can explain itself; sponsored cards additionally state "shown to more people because the provider paid for reach".

**Failure / edge outcome:** If fewer than three signals apply, show those available; if none (search-only result), show "matched your search".

**Acceptance criteria**
- [ ] Top-3 signals + gaps; no percentage score.
- [ ] Adjust-preference link present.
- [ ] Sponsored disclosure line on paid cards.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR21 - Proactive notification and digest with fatigue limits
**Traces from:** BR06, BR12 · **Priority:** Should · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a newly Active Opportunity scores above the configured "strong match" threshold for a member who has notifications enabled, the system shall request one push/in-app notification via the Notification service, limited to 3 opportunity notifications per member per day, and shall batch all other matches into one optional daily digest at the member's chosen hour; Sponsored reach may raise a record's inclusion within the eligible audience but never exceeds these limits.

**Intent:** Relevant reach, not maximum reach.

**Success outcome:** Members receive few, strong notifications; digest opt-out and per-type mute available.

**Failure / edge outcome:** Notification service failure is retried up to 3 times then dropped (never duplicated); a member who mutes a type receives none of that type; "Other" types (FR14) excluded in V1.

**Acceptance criteria**
- [ ] Threshold and daily cap in configuration; cap enforced.
- [ ] Digest hour selectable; opt-out and per-type mute.
- [ ] No duplicate sends on retry.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR55 - Opportunity detail, member actions, and Activity
**Traces from:** BR06, BR04, BR07 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a member opens an Opportunity, the system shall display title, type and status, description, requirements, value/compensation, location/mode/timing, source segment + submitter + freshness, poster trust context (FR10, FR28), the "Why this?" entry (FR20), a primary action adapted to the type (Enquire Now / Apply / Submit a Proposal / Contact / Register per FR22 DEC-002, all routed through FR22; or "Apply on source website" / "Open official website" for a Public/External item), and secondary actions Save, Share, Not interested (with one structured reason: Too far, Wrong type, Not my capability, Value too low, Wrong timing, Already found something, Not interested), and Report (FR39); and the Activity screen shall list the member's Saved, Responded, Shared, Posted, Recently viewed, and Completed items grouped by state.

**Intent:** Understand and act on one screen; preference learning only through explicit signals.

**Success outcome:** Saved items persist; Not interested hides the item immediately and records the reason for FR38; Shared items carry the sharer's attribution; External link opens the source with a leave-app notice and records the action.

**Failure / edge outcome:** Opportunity no longer Active -> detail shows its state and disables the primary action; External link unreachable -> item flagged "source unreachable" for FR48; Share of a Removed item is blocked.

**Acceptance criteria**
- [ ] All elements above; primary action adapted to type; External link only for Public/External items.
- [ ] Not interested reason captured; hide takes effect immediately.
- [ ] Activity shows the six groups by state.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Assumptions:** Detail structure follows `Vyapar_02` §6 and §9 (Opportunity detail, Activity) and the feedback vocabulary in §10.

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Added during the Product Manager approval check: the feed (FR18) and "Why this?" (FR20) existed but no FR specified the Opportunity detail screen, its actions, or the Activity screen - a gap UX would have hit immediately.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR07 - Business Enquiries and Opportunity Responses

### FR22 - Submit an Enquiry or Opportunity Response
**Traces from:** BR07 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When an authenticated member taps the primary action on a Listing or Opportunity, the system shall create one Enquiry record linked to that Listing/Opportunity with a typed action whose stored type equals its user-facing label — Enquire ("Enquire Now": Listings and Local-service opportunities), Apply (Employment), Propose ("Submit a Proposal": Freelance/Project), Contact (Business partnership), Register (Training, Community/Government) — determined by the target type, a message of 20-1000 characters, and optional attachment (<= 5 MB), and shall deliver it to the provider within 10 seconds, limiting a member to 20 new enquiries per day and 1 open enquiry per target.

**Intent:** One attributable next move; no raw contact exchange.

**Success outcome:** Provider notified; enquirer sees status Submitted; the thread shows the related Listing/Opportunity.

**Failure / edge outcome:** Daily cap or duplicate open enquiry -> clear message with the existing thread link; provider has blocked the member -> silently not delivered and shown as Submitted to the sender (no block disclosure); target no longer Active -> action disabled with reason.

**Acceptance criteria**
- [ ] Typed action by target; message limits; attachment limit.
- [ ] 20/day and 1-open-per-target limits.
- [ ] Blocked-sender handling without disclosure.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions:** DEC-001 · Facing real-time chat vs. asynchronous threads, we chose asynchronous platform-mediated threads for V1, per BR07, to avoid building a chat product, accepting slower exchanges.
- DEC-002 · (Product Manager direction 2026-09-13: "look over existing applications and inspire the words".) Facing a UX/FR vocabulary mismatch, we chose action words verified on real Indian/global apps and made the stored type equal the label: "Enquire Now" (Sulekha provider cards, opened: https://www.sulekha.com/plumbers/hyderabad ), "Apply" (Naukri FAQ https://www.naukri.com/faq/job-seeker-apply ; Apna jobs https://apna.co/jobs ), "Submit a Proposal" (Upwork support https://support.upwork.com/hc/en-us/articles/211062998-How-to-submit-a-proposal-on-Upwork ), "Contact" (IndiaMART "Contact Supplier", help centre https://help.indiamart.com/knowledge-base/contact-a-seller-from-search/ ), "Register" (public-portal convention), and for Public/External items "Apply on source website" (Naukri's "Apply on Company Website" pattern). Justdial's "Send Enquiry"/"Show Number" were seen only in search snippets (site returned 403) and are not relied on. Accepting that "Ask a question" / "Request a quote" become sub-choices inside the Enquire compose step rather than separate stored types.

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR23 - Provider manages the Enquiry lifecycle
**Traces from:** BR07 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a provider opens an Enquiry, the system shall let them reply (same limits as FR22), and move it through Open -> Awaiting Response -> In Progress -> Resolved -> Closed, let the enquirer Withdraw at any time, and let either party Restrict the thread (no further messages), showing each party the current state and last activity time, with the Activity screen listing all threads by state; either party may tap "Refer to Counsel" on the thread, which sends only the explicit, consented referral defined in FR52(f) and changes nothing else in the thread.

**Intent:** Enquiries are tracked outcomes, not lost messages.

**Success outcome:** Both parties see a consistent state; Resolved/Closed threads feed FR27 eligibility.

**Failure / edge outcome:** An Open enquiry with no provider reply for 7 days is marked "No response yet" to the enquirer and counted in provider responsiveness (FR28); state changes on a Restricted thread are rejected.

**Acceptance criteria**
- [ ] All states and transitions above; Withdraw and Restrict available.
- [ ] 7-day no-response marker.
- [ ] Activity list grouped by state.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR24 - Consent-based contact disclosure, blocking, and safety guidance
**Traces from:** BR07, BR12, BR13 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a provider accepts an Enquiry (moves it to In Progress), the system shall reveal to the enquirer only the contact channels the provider set to "After accepted enquiry" (FR02) and shall show a one-line safety notice before any external contact ("never pay in advance; report suspicious requests"); when either party blocks the other, the system shall end the thread, prevent new enquiries between them, and hide the blocked party's future content from the blocker.

**Intent:** Purpose-limited, revocable disclosure; no lead lists.

**Success outcome:** Contact appears only after acceptance and disappears if the provider later hides the channel.

**Failure / edge outcome:** Withdrawn/Closed threads no longer show contact; export or bulk view of enquirer contact details is not available to any role.

**Acceptance criteria**
- [ ] Disclosure only after acceptance and per channel setting.
- [ ] Safety notice shown once per thread before contact.
- [ ] Block ends thread and prevents future enquiries both ways.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR08 - Business Networking and Partnership Requests

### FR25 - Create a Partnership Request
**Traces from:** BR08 · **Priority:** Should · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a member with an Active Listing selects "Propose partnership" on another Active Listing, the system shall create a PartnershipRequest with need, offer, expectations, category, locality, timing, and intended next step (each 10-500 characters), send it to the recipient, and limit a member to 10 pending requests at a time.

**Intent:** Structured business networking without a social graph.

**Success outcome:** Recipient sees the request with sender's Listing trust context; sender sees Pending.

**Failure / edge outcome:** Requester without an Active Listing is prompted to create one first; pending-cap reached -> message listing pending requests; recipient has disabled partnership requests -> action hidden.

**Acceptance criteria**
- [ ] Fields and limits above; requires Active Listing on both sides.
- [ ] 10-pending cap enforced.
- [ ] Recipient opt-out respected.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR26 - Respond to and manage a Partnership Request
**Traces from:** BR08 · **Priority:** Should · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a recipient opens a PartnershipRequest, the system shall let them Accept, Decline, or Restrict it, let the sender Withdraw it while Pending, let either party Close an Accepted request, and shall disclose contact channels (per FR02 "After accepted enquiry" level) only after Accept; Pending requests shall not auto-expire.

**Intent:** Purpose-limited workflow; no contact before consent.

**Success outcome:** State (Draft/Pending/Accepted/Declined/Withdrawn/Restricted/Closed) shown to both; Accepted requests appear in Activity and qualify for FR27.

**Failure / edge outcome:** Declined requests cannot be re-sent to the same recipient for 30 days; Restricted blocks further requests between the parties.

**Acceptance criteria**
- [ ] All actions and states above; no auto-expiry of Pending.
- [ ] Contact only after Accept.
- [ ] 30-day re-send cooldown after Decline.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR09 - Interaction-Based Reviews and Reputation Signals

### FR27 - Submit a Review tied to a qualifying interaction
**Traces from:** BR09 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When an Enquiry reaches Resolved/Closed with at least one reply from each side, or a PartnershipRequest reaches Accepted then Closed, the system shall invite each party once to submit a Review (recommend yes/no, up to three structured tags, optional 20-500 character comment) within 30 days, storing the linked interaction id, and shall reject any Review without a qualifying interaction.

**Intent:** Reputation from real interactions only; no arbitrary public rating.

**Success outcome:** Review Published (after FR40 automated safety check) and linked to the interaction; reviewer identity shown as first name + "verified interaction".

**Failure / edge outcome:** Second submission for the same interaction rejected; a Review submitted on a thread later found fraudulent is Hidden automatically when the thread is removed (FR40).

**Acceptance criteria**
- [ ] Qualifying-interaction rule enforced; one review per party per interaction.
- [ ] 30-day window; structured fields above.
- [ ] Reviews tied to removed threads auto-hidden.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions:** DEC-001 · Facing star ratings vs. recommend + tags, we chose recommend/tags, per the Step 1 review guidance, to avoid authoritative-looking averages on tiny samples, accepting less granular scores.

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR28 - Contextual reputation display with no new-member penalty
**Traces from:** BR09 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a Listing is displayed, the system shall show reputation as contextual counts - "N verified interactions", "N of M recommend", top tags, and "Responds in ~X" (from FR23; wording mirrors Sulekha's verified "Responds In 15 Mins" cue) - and shall display "New on Vyapar" with no negative treatment when fewer than 3 interactions exist, never rendering a single aggregate score.

**Intent:** Evidence, not a leaderboard; no history is not bad history.

**Success outcome:** Counts shown separately from verification and paid labels; FR19 trust signal uses counts only above the 3-interaction threshold.

**Failure / edge outcome:** Hidden/Removed reviews are excluded from counts within 5 seconds; disputes show "1 review under review" without content.

**Acceptance criteria**
- [ ] Counts and tags only; no aggregate score.
- [ ] "New on Vyapar" below 3 interactions; no ranking penalty.
- [ ] Hidden/Removed excluded promptly.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR29 - Review dispute, hide, and removal
**Traces from:** BR09, BR13 · **Priority:** Should · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When the subject of a Review disputes it (reason: retaliation, manipulation, not the interaction, abusive), the system shall move it to Disputed, keep it Published but flagged until an operator decides within the FR40 queue, and on decision set it to Published, Hidden (visible to author only), or Removed, retaining the original text and full audit history in all cases.

**Intent:** Anti-gaming and non-retaliation with due process.

**Success outcome:** Author and subject both notified of the outcome with reason code; counts (FR28) updated.

**Failure / edge outcome:** A subject may dispute a given Review once; a provider cannot alter or hide a Review through any other path (verified by absence of such an action for the provider role).

**Acceptance criteria**
- [ ] Dispute reasons above; one dispute per review.
- [ ] Operator outcomes Published/Hidden/Removed with audit.
- [ ] No provider-side edit/hide capability.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR10 - Verified-Listing Promotion and Paid Distribution

### FR30 - Purchase an Opportunity or Listing Boost
**Traces from:** BR10 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When the owner of an Active-Verified Listing or an Active Opportunity selects Boost, the system shall present configurable products (duration 3/7/14 days; audience: same eligible/relevant audience as organic, optionally narrowed by locality/category), show the price including tax and what the boost does and does not change, create a Promotion in Awaiting Payment, and on payment confirmation (FR51) activate it, labelling every boosted card "Sponsored" in every surface.

**Intent:** Paid reach inside the eligible audience, never pay-to-win.

**Success outcome:** Boosted record receives additional impressions within the eligible audience; organic rank of all records is unchanged; label visible.

**Failure / edge outcome:** Unverified Listing -> Boost unavailable with "verify first"; payment failure -> Promotion stays Awaiting Payment for 24 hours then Cancelled; record suspended/expired mid-boost -> Promotion Paused and remaining time credited (FR31).

**Acceptance criteria**
- [ ] Eligibility (verified/Active) enforced; products from configuration.
- [ ] Price with tax and plain-language does/doesn't-change text shown before purchase.
- [ ] Sponsored label on every surface; organic ranking unchanged.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Assumptions:** Prices are configuration hypotheses per the pricing model, versioned per FR31.

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR31 - Promotion lifecycle, price versioning, cancellation, and credit
**Traces from:** BR10, BR11 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a Promotion or Entitlement changes state, the system shall enforce Draft -> Awaiting Payment -> Scheduled/Active -> Paused -> Completed / Cancelled / Rejected / Refunded-Credited, store the product and price version in force at purchase, let the owner cancel before activation for a full refund and during activity for a pro-rata credit, and show a receipt reference, tax line, and history to the owner.

**Intent:** Transparent, auditable, reconstructible commercial records.

**Success outcome:** Every order is reconstructible with product version, price, tax, state history, and payment reference.

**Failure / edge outcome:** Operator Rejects a Promotion (safety) -> automatic full refund request via FR51 and reason to owner; refund request failure -> retried and surfaced in the FR49 queue.

**Acceptance criteria**
- [ ] All states above enforced; product/price version stored per order.
- [ ] Pre-activation full refund; active pro-rata credit.
- [ ] Receipt with tax line and payment reference visible to owner.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR32 - Provider performance reporting without unsupported claims
**Traces from:** BR10, BR15 · **Priority:** Should · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a provider opens a Promotion or Listing report, the system shall show impressions, detail views, saves, enquiries/responses, and outcomes confirmed (FR23/FR27) as separate counts for the period, comparing boosted vs. organic where a boost ran, and shall not display projections, ROI guarantees, or causal statements.

**Intent:** Defensible measures only.

**Success outcome:** Provider sees what changed during the boost as counts with dates.

**Failure / edge outcome:** Fewer than 10 impressions -> counts shown with "too little data to compare"; no individual member identity is ever shown in reports.

**Acceptance criteria**
- [ ] Five separate counts; boosted vs. organic split.
- [ ] No projections/guarantees/causal language.
- [ ] No member-level data.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR11 - Business Subscription and Commercial Workspace

### FR33 - Purchase and manage a Business Workspace entitlement
**Traces from:** BR11 · **Priority:** Should · **Status:** Ready for Review · **Confidence:** Medium - product scope is configuration; willingness to pay is unproven.

**Requirement:** When a BusinessProfile owner selects Business Workspace, the system shall present the configurable plan (monthly or annual; included capabilities: multi-user administration FR34, campaign management FR35, response tracking, provider analytics FR32), show price with tax, renewal date, and cancellation terms before purchase, create an Entitlement (scope, duration, owner, state per FR31) on payment confirmation, and shall never grant verification, reputation, ranking, eligibility, or private member data through the plan.

**Intent:** Outcome/workspace value, not a posting paywall.

**Success outcome:** Entitled capabilities unlock immediately; core discovery, posting, and enquiries remain free for all members.

**Failure / edge outcome:** Renewal payment failure -> 7-day grace with notices, then Entitlement Paused (capabilities locked, data retained); cancellation stops renewal at period end with no hidden auto-renewal.

**Acceptance criteria**
- [ ] Plan from configuration; terms shown pre-purchase; Entitlement created on payment.
- [ ] No effect on verification/reputation/ranking/eligibility.
- [ ] 7-day grace then Paused; explicit renewal disclosure.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR34 - Multi-user business administration roles
**Traces from:** BR11 · **Priority:** Should · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a Workspace owner invites another member by phone number, the system shall assign a role of Admin (all actions except delete/transfer) or Operator (opportunities, enquiries, reports; no billing), require the invitee to accept, and let the owner revoke a role at any time with immediate effect on all sessions.

**Intent:** Auditable delegated authority.

**Success outcome:** Role holders act on behalf of the business; every action is attributed to the individual member.

**Failure / edge outcome:** Invitee not a ForKhatri member -> invitation pending until they join (30-day expiry); revoked operator's in-progress drafts remain with the business.

**Acceptance criteria**
- [ ] Two roles with the permission split above; accept flow.
- [ ] Immediate revocation; actions attributed to individuals.
- [ ] 30-day invitation expiry.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR35 - Community/Opportunity Campaign creation
**Traces from:** BR11, BR10 · **Priority:** Should · **Status:** Ready for Review · **Confidence:** Medium - the pricing model places "Campaign foundation" in V1 and BR11 is Should, so this inherits Should; scope is kept to boost mechanics only.

**Requirement:** When an entitled business creates a Campaign, the system shall let them group up to 10 of their Active Opportunities/Listings under one name, budget (fixed packages from configuration), date range, and eligible-audience narrowing, apply FR30 boost rules to each item, and report per FR32 at campaign level.

**Intent:** Packaged distribution for repeat providers; nothing beyond boost mechanics.

**Success outcome:** Campaign runs as a set of boosts with one payment and one report.

**Failure / edge outcome:** An item leaving Active mid-campaign is Paused with credit per FR31; budget exhausted -> campaign Completed early with notice.

**Acceptance criteria**
- [ ] Up to 10 items; package budgets from configuration.
- [ ] Boost rules and labels apply per item.
- [ ] Campaign-level report.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR12 - Privacy, Consent, and Purpose-Limited Data Handling

### FR36 - Contextual privacy controls
**Traces from:** BR12 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a member first sets any of capability visibility, seeking-status visibility, contact disclosure, listing discoverability, notifications, or commercial communications, the system shall ask at the moment of the related action with a one-sentence explanation of who will see what, apply privacy-by-default values (contact after acceptance; seeking private; commercial communications off), and expose all six controls together in one Privacy screen for later change.

**Intent:** Privacy complexity in the platform, not in the member's head.

**Success outcome:** No member reaches a public surface with an unset control; all changes propagate within 5 seconds.

**Failure / edge outcome:** Declining a contextual prompt keeps the default and can be revisited from the Privacy screen; no cross-module inference is used to preset any control.

**Acceptance criteria**
- [ ] Six controls; contextual first-set prompts; defaults above.
- [ ] Single Privacy screen; 5-second propagation.
- [ ] No cross-module data used for defaults.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR37 - Data access, correction, deletion, and consent withdrawal
**Traces from:** BR12, BR18 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a member requests it from the Privacy screen, the system shall (a) provide a downloadable copy of their MOD01 data (profiles, opportunities, enquiries, reviews they wrote, consents) within 72 hours, (b) allow correction of any self-entered field immediately, (c) withdraw any optional consent immediately, and (d) delete their MOD01 data within 30 days, retaining only records required for open disputes, active paid orders, or audit obligations, with the retained categories listed to the member.

**Intent:** Working rights mechanisms proportionate to DPDP-aligned practice.

**Success outcome:** Requests tracked with status; deletion anonymizes the member's reviews and enquiries rather than deleting the counterpart's record.

**Failure / edge outcome:** Deletion while a paid Promotion is active -> user informed it completes after the order closes or is cancelled; export generation failure -> retried and status shown.

**Acceptance criteria**
- [ ] Export within 72 hours; correction and consent withdrawal immediate.
- [ ] Deletion within 30 days with listed retention exceptions.
- [ ] Counterparty records preserved via anonymization.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR38 - Inspect and confirm derived preferences
**Traces from:** BR12, BR06 · **Priority:** Should · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When the system detects a repeated behavioral pattern (e.g., three "Too far" feedbacks), it shall propose an explicit preference change to the member with the evidence, apply it only on confirmation, and shall list every active derived preference with its source in the Profile so the member can edit or remove it; reports shall never be used as preference input.

**Intent:** Explainable, user-controlled learning; nothing silent.

**Success outcome:** Ranking (FR19) uses only confirmed preferences plus explicit profile facts.

**Failure / edge outcome:** Declined proposal is not re-proposed for 30 days; removing a preference takes effect on the next feed load.

**Acceptance criteria**
- [ ] Proposal with evidence; confirmation required.
- [ ] Preference list with source; edit/remove.
- [ ] Reports excluded as inputs; 30-day re-proposal cooldown.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR13 - Trust and Safety, Moderation, Fraud, and Dispute Operations

### FR39 - Report and block
**Traces from:** BR13 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a member selects Report on a Listing, Opportunity, Enquiry, PartnershipRequest, or Review, the system shall capture a reason (scam/advance payment, fake, impersonation, harassment/abuse, discrimination, spam, stale/wrong information, privacy violation, other), optional evidence (text up to 1000 characters, up to 3 images), create a Report in the FR40 queue within 5 seconds, confirm receipt to the reporter, and offer Block (FR24) in the same flow.

**Intent:** Reports are safety signals with a real path to action.

**Success outcome:** Report visible to operators with severity auto-suggested from reason; reporter identity hidden from the reported party.

**Failure / edge outcome:** A member exceeding 10 reports/day is rate-limited with a message; duplicate reports on the same object merge into one case with a reporter count; a report never changes the reporter's or the reported party's ranking preferences.

**Acceptance criteria**
- [ ] Reason list and evidence limits; receipt confirmation.
- [ ] Reporter anonymity; duplicate merge; 10/day limit.
- [ ] No effect on preference/ranking inputs.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR40 - Moderation queue and graduated actions
**Traces from:** BR13, BR16 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a Report, automated safety flag (FR03 wordlist/spam, or an opportunity mentioning advance payment/registration fees), or Review dispute enters the moderation queue, the system shall show operators the object, evidence, severity (Low/Medium/High/Critical with configurable target response times), and history, and shall let them apply Limit distribution, Remove/Hide, Restore, Request verification, Suspend account (with duration), or Dismiss, each with a mandatory reason code, notifying the affected party of the outcome and appeal path; High/Critical items shall be auto-limited from distribution pending review.

**Intent:** Graduated, accountable response; automated flags prioritize but never finalize.

**Success outcome:** Every action attributable, reason-coded, audited; distribution changes take effect within 5 seconds.

**Failure / edge outcome:** An automated flag with no operator decision within its target time escalates in the queue (no automatic permanent ban); Restore reverses a prior action fully; operators cannot edit evidence.

**Acceptance criteria**
- [ ] Queue with severity, targets, evidence, history; six actions with reason codes.
- [ ] High/Critical auto-limited pending review; escalation on missed target.
- [ ] Party notification with appeal path; evidence immutable.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR41 - Appeals and outcome communication
**Traces from:** BR13, BR18 · **Priority:** Should · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a member receives a moderation outcome (removal, suspension, verification revocation, review removal), the system shall let them submit one Appeal (up to 1000 characters, optional evidence) within 15 days, route it to a different operator than the original decision-maker where staffing allows, and communicate the appeal decision with reason code within a configurable target (default 7 days).

**Intent:** Due process without a heavy legal apparatus.

**Success outcome:** Appeal state (Open/Upheld/Overturned) visible to the member; Overturned restores the object/account.

**Failure / edge outcome:** Second appeal on the same decision rejected; appeal target missed -> case escalated to the queue owner and member informed of delay.

**Acceptance criteria**
- [ ] One appeal per decision within 15 days.
- [ ] Different reviewer where possible; default 7-day target.
- [ ] Overturn restores fully; delay notice on missed target.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR14 - Accessibility, Localization, and Progressive Participation

### FR42 - Language selection and rendering (English, Hindi, Telugu)
**Traces from:** BR14 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a member selects English, Hindi, or Telugu (defaulting to the device locale when supported, else English), the system shall render all MOD01 interface text, system messages, labels, notifications, and taxonomy display names in that language via the shared platform i18n layer, keep member-authored content in its original language with a language tag, and shall not use language preference as a ranking input.

**Intent:** Inclusion without hidden ranking effects.

**Success outcome:** 100% of MOD01 system strings available in all three languages before release; missing strings fall back to English and are logged.

**Failure / edge outcome:** Untranslated taxonomy term -> English shown with the member's language tag preserved; a member-authored Hindi listing appears in a Telugu member's results by text/category match, unchanged.

**Acceptance criteria**
- [ ] Three languages; device-locale default; switch takes effect without re-login.
- [ ] Member content untouched with language tag.
- [ ] Language not in the FR19 signal allow-list.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR43 - Accessibility baseline
**Traces from:** BR14 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** For every MOD01 screen, the system shall meet WCAG 2.2 Level AA: all core actions operable by keyboard and screen reader, no information conveyed by colour alone, no drag-and-drop-only or voice-only path, text resizable to 200% without loss, minimum 4.5:1 contrast for text, visible focus, and error messages that identify the field and the fix.

**Intent:** Members with different abilities and devices can complete core tasks.

**Success outcome:** Automated accessibility checks pass in CI and a manual screen-reader pass of the core journeys (setup, search, enquiry, post) is recorded before release.

**Failure / edge outcome:** A screen failing an automated check blocks release of that screen; conformance is claimed only after the recorded test evidence exists.

**Acceptance criteria**
- [ ] Criteria above verifiable by automated tooling plus manual pass.
- [ ] No colour-only, drag-only, or voice-only core paths.
- [ ] Release gate on failures.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR44 - Progressive first-run to discovery
**Traces from:** BR14, BR02 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a new member opens Vyapar for the first time, the system shall present a Welcome, ask what they want help with (multi-select, including "I'm not sure yet"), capture capabilities via structured choices plus free text, capture location/radius and work mode, set privacy defaults (FR36), and land them on Discover within 5 screens after authentication (FR50) and under 3 minutes, with every step skippable except location.

**Intent:** Value before a resume.

**Success outcome:** Member sees Discover or the Businesses & Professionals surface with content; setup abandonment point is recorded (FR45).

**Failure / edge outcome:** Location permission denied -> manual locality entry; "I'm not sure yet" routes to Explore and Near You sections with a capability-first prompt.

**Acceptance criteria**
- [ ] <= 5 screens; only location mandatory; skip everywhere else.
- [ ] "Not sure yet" path exists.
- [ ] Abandonment step logged.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR15 - Product Analytics, Marketplace Health, and Experimentation

### FR45 - Event instrumentation with outcome levels
**Traces from:** BR15 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When any of the following occurs, the system shall emit a structured analytics event with member pseudonymous id, object id, surface, and timestamp: listing/opportunity impression, detail view, save, hide with reason, share, search (with zero-result flag), enquiry/response submitted, enquiry state change, review submitted, report submitted, notification sent/opened/muted, setup step completed/abandoned, promotion purchased/active/completed, and outcome confirmed - each tagged with its level (impression / view / action / attributed outcome / confirmed outcome).

**Intent:** Lineage from discovery to outcome without inferring causality.

**Success outcome:** The platform analytics pipeline receives >= 99% of events within 60 seconds; levels never collapsed.

**Failure / edge outcome:** Pipeline unavailable -> events buffered locally up to 24 hours then dropped with a count metric; members who withdraw behavioral-analytics consent (FR37) emit only the operational minimum (state changes) with no behavioral events.

**Acceptance criteria**
- [ ] Event list and fields above; level tag on every event.
- [ ] Buffering and consent behavior.
- [ ] Pseudonymous ids only.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR46 - Marketplace health metrics view
**Traces from:** BR15, BR16 · **Priority:** Should · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When an operator with the analytics permission opens the metrics view, the system shall show, for a selectable period, Relevant Opportunity Connections (responses on records above the configured relevance threshold), Opportunity Coverage, Relevant Discovery Rate, Opportunity Action Rate, Successful Connection Rate, discovery-to-enquiry rate for Listings, time to first relevant opportunity, freshness, zero-result rate, reports per 1,000 interactions, notification opt-out rate, promotion repeat rate, and revenue/refunds, each aggregated with a minimum group size of 10 and labelled by outcome level.

**Intent:** Distinguish a healthy marketplace from a noisy feed.

**Success outcome:** Metrics computable from FR45 events alone; no individual member visible.

**Failure / edge outcome:** Groups under 10 are suppressed; profile-completion percentage is not offered as a metric.

**Acceptance criteria**
- [ ] Metric list above with period selection.
- [ ] Minimum group size 10; outcome-level labels.
- [ ] No profile-completion metric.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR16 - Verification, Ingestion, Moderation, and Commercial Administration

### FR47 - Verification queue in the Admin Console
**Traces from:** BR16, BR03 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When an operator with the verification permission opens the verification queue, the system shall list Pending Review BusinessVerificationRecords oldest first with age against the 3-business-day target, show the claim, document type, masked identifier, uploaded image, and listing, provide a link to the public GST/Udyam lookup where applicable, and offer Verify / Reject (reason) / Needs clearer copy, recording the verifier and decision time.

**Intent:** Verification promises are operable, not implicit.

**Success outcome:** Decision applies to the Listing (FR08/FR09/FR10) within 5 seconds.

**Failure / edge outcome:** Records past target are highlighted; operators without the permission cannot open evidence; identity images auto-delete per FR08.

**Acceptance criteria**
- [ ] Queue fields and three decisions; verifier recorded.
- [ ] Lookup link where applicable; overdue highlighting.
- [ ] Permission-gated evidence access.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR48 - Opportunity review, stale queue, and taxonomy management
**Traces from:** BR16, BR04 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When an operator with the content permission opens the operations area, the system shall provide (a) an Opportunity review queue for records in Submitted/Pending Review or flagged "source unreachable"/"unconfirmed", with Approve / Return to contributor / Remove; (b) a Stale/Expired queue with bulk Remind / Expire; and (c) taxonomy management to add, merge, rename, or map unmapped capability/category labels, with changes versioned and applied to search within 5 minutes.

**Intent:** Founder/operator surfaces the source plan requires, grown alongside the product.

**Success outcome:** Queues show reason, age, allowed actions; taxonomy edits do not alter member-entered text.

**Failure / edge outcome:** Merging taxonomy terms preserves both labels as aliases; bulk actions require confirmation with counts.

**Acceptance criteria**
- [ ] Three areas with actions above.
- [ ] Taxonomy versioning; 5-minute search refresh; aliases on merge.
- [ ] Bulk confirmation.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR49 - Commercial administration and audit review
**Traces from:** BR16, BR10, BR11 · **Priority:** Should · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When an operator with the commercial permission opens commercial administration, the system shall let them manage product/price versions (create new version; never edit a version with orders), view Promotions/Entitlements by state, process refund/credit requests with reason, view ranking/distribution diagnostics for a given record (eligibility result and score breakdown), and search the audit log by actor, object, action, and date, with no ability to change verification state, organic relevance, or safety decisions from this area.

**Intent:** Commercial operations without hidden overrides.

**Success outcome:** Every commercial action is attributable; historical orders reconstructible.

**Failure / edge outcome:** Refund exceeding order value rejected; diagnostics show why a record is excluded (which hard constraint) rather than allowing an override.

**Acceptance criteria**
- [ ] Versioned products; refund/credit workflow; diagnostics; audit search.
- [ ] No verification/relevance/safety overrides in this area.
- [ ] Refund bounds enforced.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR17 - Platform and Adjacent-Module Contracts

### FR50 - Identity & Trust integration
**Traces from:** BR17 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a member accesses MOD01, the system shall authenticate them solely through the Identity & Trust service (phone/OTP session), read the canonical member id, display name, platform trust level, and VerifiedCredential references through its versioned read contract, store only the member id as a foreign key in MOD01 records, and never create, duplicate, or modify platform identity data.

**Intent:** One identity; no fork.

**Success outcome:** MOD01 works against the contract version it declares; identity changes upstream appear within one sync (<= 1 hour).

**Failure / edge outcome:** Identity & Trust unavailable -> existing sessions continue read-only for up to 15 minutes with a banner; new logins blocked with a retry message; no local credential fallback exists.

**Acceptance criteria**
- [ ] Auth only via Identity & Trust; member id as sole stored identity key.
- [ ] Contract version declared; upstream changes synced within 1 hour.
- [ ] Read-only degradation on outage; no local auth.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR51 - Direct payment-gateway integration (self-contained V1)
**Traces from:** BR17, BR10, BR11 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** When a Promotion or Entitlement enters Awaiting Payment, the system shall create a payment order with a licensed payment gateway using a gateway-hosted or tokenized checkout, pass an idempotency key per order, receive the payment result via signed webhook (verified before processing) and a status poll fallback, store only the gateway order/payment reference, amount, tax, currency, and state, and issue refund/credit requests through the same gateway with the original reference; raw card or bank credentials shall never reach MOD01.

**Intent:** Vyapar's pricing is self-contained in V1; loosely coupled so a future MOD06 consolidation is a swap, not a rewrite.

**Success outcome:** Payment states (Pending/Succeeded/Failed/Refunded) update the order within 30 seconds of the gateway event; duplicate webhooks are ignored via the idempotency key.

**Failure / edge outcome:** Unverified webhook signature -> rejected and logged; gateway outage -> order remains Awaiting Payment with a retry option (24-hour window per FR30); refund failure -> surfaced in FR49.

**Acceptance criteria**
- [ ] Hosted/tokenized checkout; idempotency key per order; signed webhooks verified.
- [ ] Only references/amount/state stored; no raw credentials.
- [ ] Gateway adapter isolated behind one internal payment interface (config-driven provider keys in `.env`/config with placeholders).

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions:** DEC-001 · Facing a cross-module MOD06 contract vs. a direct gateway, we chose a direct gateway behind an internal payment interface, per BR17/PM direction, to ship without a cross-module dependency, accepting a later adapter swap if payments centralize.

**Assumptions:** Gateway provider is configuration; sample placeholder keys are created at implementation time.

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR52 - Loosely coupled platform and adjacent-module contracts
**Traces from:** BR17, BR12 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** Medium - adjacent owners must accept the minimum-field contracts.

**Requirement:** When MOD01 interacts with Search, Notification, Audit, Object Storage, MOD05, or MOD04, the system shall use only versioned, minimum-field contracts: (a) publish Active Listing/Opportunity index documents to Search and remove them on state change within 5 seconds; (b) send notification requests with template id, member id, and parameters only; (c) send audit events per the shared definition; (d) store media/evidence in Object Storage under MOD01 access policy; (e) expose to MOD05 a read-only, privacy-filtered summary (public fields only, no contact, no private intent) with no write path; (f) send to MOD04 an explicit referral (member id, problem summary, consent flag) only when the member taps "Refer to Counsel", with no appointment or payment state exchanged; every call shall carry an idempotency key where retried and shall fail without corrupting MOD01 state.

**Intent:** One owner per entity; failures do not cascade; everything replaceable.

**Success outcome:** Any adjacent service outage degrades only its own feature (search fallback, queued notifications, buffered audit) and MOD01 domain state stays consistent.

**Failure / edge outcome:** Retry exhaustion -> item parked in a dead-letter list visible in FR49; MOD05 requesting a private field -> rejected by contract; no direct database access from any other module.

**Acceptance criteria**
- [ ] Six contracts above with declared versions and minimum fields.
- [ ] Idempotent retries; dead-letter visibility.
- [ ] MOD05 read-only public-only summary; MOD04 referral explicit and consented.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR18 - Proportionate Legal and Compliance Awareness

### FR53 - Privacy notice, terms, and grievance contact
**Traces from:** BR18, BR12, BR13 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** Before a member can publish a Listing or Opportunity or submit an Enquiry, the system shall have presented a versioned privacy notice (what data, purpose, who sees it, retention, rights path) and terms of use in the member's language and recorded acceptance with version and timestamp; the system shall display a grievance/contact channel and the takedown/appeal process description from every Report and moderation-outcome screen, and shall re-prompt acceptance when a new notice version is published.

**Intent:** Proportionate DPDP-aligned transparency without a legal gate.

**Success outcome:** Acceptance records exist for every publishing member; documents editable by the Product Manager with version history.

**Failure / edge outcome:** Declining terms keeps the member in read-only discovery; notice version rollback restores the prior text without deleting acceptance history.

**Acceptance criteria**
- [ ] Versioned notice/terms in three languages; acceptance recorded before first publish/enquiry.
- [ ] Grievance channel and process visible from Report and outcome screens.
- [ ] Re-prompt on new version; decline -> read-only.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

### FR54 - Commercial disclosure and renewal transparency
**Traces from:** BR18, BR10, BR11 · **Priority:** Must · **Status:** Ready for Review · **Confidence:** High

**Requirement:** Wherever a paid placement, boosted record, or campaign item is displayed, the system shall label it "Sponsored" in the member's language, and before any purchase or renewal the system shall display the full price with tax, duration, what the purchase changes and does not change, renewal terms, and cancellation/refund rules on one screen requiring explicit confirmation, with no pre-selected renewal for one-time products and a renewal reminder 3 days before any automatic renewal.

**Intent:** Non-misleading commercial communication as a product rule.

**Success outcome:** No paid surface is unlabelled; no charge occurs without a confirmed disclosure screen.

**Failure / edge outcome:** Disclosure screen not confirmed -> no order created; reminder delivery failure does not permit silent renewal (renewal proceeds only if the reminder was sent successfully, else it is paused with a notice).

**Acceptance criteria**
- [ ] Sponsored label everywhere paid items appear.
- [ ] One-screen disclosure with explicit confirmation before purchase/renewal.
- [ ] 3-day renewal reminder gating automatic renewal.

**Quality gate:** Necessary ✓ · Appropriate ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Handoff readiness:** User/role Yes · Trigger Yes · Success + failure Yes

**Review history:** 2026-09-12 - Drafted.

**Approval:** Product Manager / BA - [x] Approved - Krishna Kategaru, 2026-09-12

---

## Build-order note for Step 3 onward

Suggested incremental slices so each step yields visible app progress:
1. FR50, FR44, FR01-FR05, FR07 - identity, first-run, profiles, OTP baseline.
2. FR15-FR17, FR16 - standalone Businesses & Professionals discovery.
3. FR11-FR14, FR18-FR20, FR55 - opportunities, the Discover feed, and Opportunity detail/Activity.
4. FR22-FR24 - enquiries and consented contact.
5. FR08-FR10, FR47 - verification and its queue.
6. FR39-FR41, FR40 - reporting and moderation.
7. FR27-FR29, FR25-FR26 - reviews and partnerships.
8. FR30-FR32, FR51, FR54 - boost, payments, disclosure.
9. FR33-FR35, FR49 - workspace and commercial admin.
10. FR36-FR38, FR42-FR43, FR45-FR46, FR48, FR52, FR53 - privacy, localization, analytics, remaining operations.
