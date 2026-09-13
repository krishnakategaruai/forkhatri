---
step: 01-business-requirements
module: MOD01
status: Sealed
approver: Product Manager
updated: 2026-09-12
items: "18 | approved: 18 | blockers: 0"
---

# 01 - Business Requirements - MOD01 Vyapar

## Revision history

| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-12 | Re-created the missing MOD01 Step 1 artifact from the approved MOD01 boundary, the supplied Vyapar corpus, sealed architecture controls, and current external compliance research. | The repository process log records an earlier MOD01 Step 1/Step 2 seal, but the current `modules/MOD01-vyapar` directory contains only `.gitkeep`; no prior artifact was available to inspect or safely amend. |
| 2026-09-12 | Added explicit boundary, payment-contract, V1-wedge, verification, monetization, and legal/compliance blockers instead of silently absorbing broader source-document proposals. | Reconciliation of `modules/modules.md`, `ARCHITECTURE.md`, and the Vyapar source corpus. |
| 2026-09-12 | Recorded the Product Manager's V1 product-thesis decision: Vyapar is primarily an **opportunity distribution** product, not a professional/business discovery product. General "find a professional/business to consult or hire for advice" discovery is out of scope for Vyapar because MOD04 Counsel already owns consultant/expert reach and appointment-based discovery. Business/professional presence in Vyapar exists to support opportunity supply, enquiries, and networking, not to duplicate Counsel's discovery surface. This partially resolves `BLOCKER-003`; the exact launch opportunity types and geography remain open. | Product Manager decision during Step 1 review, in response to the reviewer's Option A/B/C product-framing question. |
| 2026-09-12 | **Correction pass, superseding the immediately preceding entry.** The Product Manager rejected the "opportunity distribution, not discovery" reframing as a genuine misinterpretation: in the Product Manager's own words, the only thing that belongs to MOD04 Counsel is "if people are finding something to learn or someone to give direction, which comes under counselling" — a member seeking structured counselling/mentorship/guidance/advisory delivery. Ordinary business/professional discovery ("like any other business app, where they can discover also") is explicitly co-equal MOD01 scope, per the Product Manager's own prior agreement recorded across the Vyapar `.docx`/`.md` corpus and `modules/modules.md`'s own scope line. Every place this file had subordinated discovery to opportunity distribution (the scope narrative, the out-of-scope bullet, the actor rows for Professional/freelancer and Customer/client, cross-cutting rule 1, and the BR02/BR05 constraints) is corrected below. Separately, per explicit Product Manager direction to stop manufacturing avoidable complexity: BLOCKER-001 (public/community opportunity source boundary) is resolved with a simple Community/Public-External source-segment tag plus submitter attribution; BLOCKER-002 (MOD01→MOD06 payment contract) is resolved by making V1 payment collection self-contained within Vyapar, with an explicit loose-coupling architecture principle carried into BR17; BLOCKER-003 (V1 opportunity wedge) is substantially resolved using the source corpus's own stated wedge recommendation (critqureport §24), with launch geography recorded as a non-blocking working assumption; BLOCKER-004 (Level-3 verification policy) is resolved with a concrete, deliberately lightweight V1 policy (a small number of checkable claims, not a broad multi-registry system); BLOCKER-005 (legal sign-off) is resolved by rewriting BR18 as a proportionate compliance-awareness constraint appropriate to an early-stage, founder-built product rather than a hard pre-launch legal gate; BLOCKER-006 (monetization phase) is resolved directly from the pricing/revenue-model docx's own V1 roadmap. Zero blockers remain open. | Product Manager correction, in response to explicit feedback that the previous pass misread the Vyapar corpus's Counsel boundary and manufactured avoidable blockers instead of resolving them from the source material already supplied. |
| 2026-09-12 | **Reviewer verification pass, correcting a citation error in the immediately preceding entry (kept above for the audit trail).** A full read of the entire Vyapar source corpus (PM Planning P1-P5, the Complete Product Definition, Vyapar_01/02/03, and critqureport — every `.docx` extracted and read in full, not summarized) found that this deeper research corpus is built almost entirely around a Person+Opportunity model with no standalone business-directory concept, and that critqureport explicitly warns against a profile/directory-style "LinkedIn-lite" product (§12). The claim above that co-equal business/professional discovery was "recorded across the Vyapar `.docx`/`.md` corpus" is therefore not accurate — only `modules/modules.md`'s sealed Step 0 boundary (business + professional discovery/search; `BusinessProfile`/`ProfessionalListingProfile` as owned data) actually supports it. That is still the higher-priority source per this file's own stated hierarchy, and the Product Manager has separately and explicitly confirmed the standalone discovery intent directly (not by way of the research corpus), so the co-equal-scope decision itself stands unchanged. What changed in this pass: the Scope-of-this-step narrative, BR05's Worth check, and BR05's Traced-to line were corrected to stop attributing this decision to the research corpus, name `modules/modules.md` as its actual basis, and record the tension with the corpus honestly; unverified named-app comparisons (Sulekha, UrbanCompany, LinkedIn-as-precedent) were removed since they were never actually checked, keeping only Justdial, WorkIndia, and Apna, which were. | Product Manager instruction to verify the file "as reviewer and with complete docsx knowledge" rather than spot-check it. |
| 2026-09-12 | Sealed. All 18 BRs approved and the file marked Sealed on Product Manager direction ("complete if not complete, and let's move to next") following the reviewer verification pass above, with zero open blockers. | Product Manager approval and directive to proceed to Step 2 (Functional Requirements). |

## Scope of this step

This file defines the business needs for the approved MOD01 - Vyapar boundary in
`modules/modules.md`: a trusted **business and professional discovery ecosystem**
that is equally, and just as fundamentally, a **member-originated opportunity
distribution network**. These are co-equal, first-class capabilities of the same
module — neither is primary infrastructure for the other, and neither may be
silently narrowed in favor of the other.

This dual framing is a deliberate Product Manager decision, and it is worth
recording honestly rather than papering over: `modules/modules.md`'s sealed
Step 0 boundary explicitly names "business + professional discovery/search" as
MOD01 scope and owns `BusinessProfile`/`ProfessionalListingProfile` as
first-class data — that is the higher-priority source per this file's own
stated hierarchy, and it is what BR01/BR02/BR05 below rest on. The deeper
Vyapar product-research corpus (the PM Planning P1-P5 document, the Complete
Product Definition, Vyapar_01/02/03, and critqureport), by contrast, is built
almost entirely around a Person+Opportunity model with no standalone
business-directory concept, and critqureport explicitly warns against building
a profile/follower/directory-style "LinkedIn-lite" product (critqureport §12).
Read literally, that corpus does not itself ask for an independent "browse
businesses" experience the way `modules/modules.md` does. The Product Manager
has confirmed, directly and specifically, that Vyapar should nonetheless work
like an ordinary business/professional discovery app in addition to
distributing opportunities — a member can look someone up without any
opportunity being involved — and that decision is what this file follows,
consistent with the Step 0 boundary. One concrete consequence: `Vyapar_02`'s
screen architecture was designed around an opportunity-only Discover tab (For
You / Explore / Near You / Community / Public) with no dedicated
business/professional browsing surface, so Step 3 (UX) must design that
standalone discovery surface itself rather than assume the research corpus
already specifies it.

It covers business profiles and professional/freelancer listing profiles;
business, professional, and customer discovery/search — an ordinary "find a
business or professional" experience; business enquiries; business networking
and partnership requests; employment and business opportunity listings
originated or shared by ForKhatri business members; business-specific Level-3
verification; reviews and in-module reputation signals; and verified-listing
promotion that is visibly distinct from organic discovery.

Business and professional profiles serve two equally valid purposes: they are
supply-side and trust infrastructure for the opportunity loop, **and** they are
a standalone discovery surface in their own right. A member can use Vyapar
exactly as they would use a trusted community business directory — to find a
plumber, an accountant, a caterer, a supplier, or a fellow professional for an
ordinary business reason — without any opportunity record ever being involved.
The only discovery need MOD01 does not serve is a member specifically seeking
**structured counselling, mentorship, guidance, or paid appointment-based
advisory delivery** from an expert; that narrow use case, and only that use
case, belongs to MOD04 Counsel's ExpertProfile and appointment workflow. An
ordinary business/service enquiry, hiring need, partnership request, or project
need stays squarely in MOD01 scope even when the counterpart happens to be a
professional who also holds a Counsel ExpertProfile, and even when the surface
feeling of "getting help from someone" is superficially similar.

The approved boundary takes precedence over proposals in the supplied source
documents. Those documents are evidence for product intent and hypotheses; they
do not override the Step 1 workflow, the sealed Step 0 boundary, or a human
decision. The source corpus's own broader opportunity-network vision — which
includes members sharing public/government items they found elsewhere — is
reconciled with Step 0's member-originated boundary through a simple rule
adopted in BR04: every opportunity carries a visible source-segment tag
(Community or Public/External) plus its submitter's identity, so provenance
stays honest without requiring either an elaborate ingestion pipeline or a
blanket exclusion of member-shared external content.

This step does not fan out into Functional Requirements, UX, UI, data models, or
implementation tasks. It states business outcomes, actors, invariants,
lifecycle expectations, dependencies, compliance prerequisites, and measurable
success conditions so that a later Step 2 agent can decompose only approved BRs.

### Explicit global boundary

In scope:

- Member-facing business and professional listings and their discovery, usable
  on their own as an ordinary business/professional directory experience,
  independent of any opportunity ever being involved.
- Customer discovery, enquiries, business networking, and partnership requests.
- Member-originated and member-shared job, service, project, hiring, and
  business-opportunity records, each tagged with a Community or Public/External
  source segment and its submitter (see BR04).
- Level-3 verification evidence and status specific to a business or
  professional listing.
- Reviews, interaction-based reputation signals, promotion, and commercial
  distribution controls owned by Vyapar.

Out of scope for MOD01:

- The specific use case of a member seeking structured counselling, mentorship,
  guidance, or paid appointment-based advisory delivery from an expert — owned
  by MOD04 Counsel's ExpertProfile and appointment workflow. Ordinary business/
  professional discovery, enquiries, hiring, and networking remain MOD01 scope
  even when the counterpart also happens to hold a Counsel ExpertProfile.
- Community meetups and events (MOD02 Milavn).
- Capturing, settling, or storing payment instruments. V1 Vyapar collects its
  own payment directly through a payment-gateway integration and never stores
  raw payment credentials (see BR17); routing that collection through a shared
  MOD06 Payment Services contract instead is a future consolidation option, not
  a launch dependency.
- Autonomous scraping, crawling, or ingestion of external/government/public/NGO
  sources that no member has actively chosen to share — that non-member-
  originated pipeline remains MOD05 Dashboard's Local Information Intelligence.
  A member-submitted Public/External item (see BR04) is in scope; an
  independently harvested one is not.
- Matrimonial-context data or discovery (MOD03 Mangaly).
- A generic social network: followers, likes, popularity leaderboards,
  open-ended social feeds, or a general-purpose chat product.
- A full ATS, escrow/freelance marketplace, financial marketplace, or
  transaction marketplace.

## Actors and personas

| Actor | Need / authority | Boundary |
|---|---|---|
| Community member / opportunity seeker | Find relevant businesses, professionals, jobs, projects, services, and member-originated opportunities; send enquiries or responses. | May control their own Vyapar attributes and privacy; must not see private profile/contact fields without permission. |
| Business owner / employer / service provider | Create and maintain a business listing, publish member-originated or member-shared opportunities, receive enquiries, and optionally buy eligible distribution. | May act only for a business they are authorized to represent; payment does not imply verification or reputation. |
| Professional / freelancer | Present capabilities, experience, services, availability, and contact preferences; receive relevant enquiries/opportunities; be found through ordinary discovery. | Vyapar listing is distinct from MOD04 Counsel's ExpertProfile and appointment workflow, but it supports ordinary discovery, enquiries, and opportunity response alike — a customer may find and contact this professional for any normal business reason without that being consultation-seeking. Only a structured, paid, appointment-based advisory engagement belongs to Counsel. |
| Customer / client | Discover a business or professional for any ordinary reason — hiring, buying a service, a project, a partnership, or a general enquiry — as well as in service of a specific opportunity or need, and make a legitimate enquiry or service request. | Does not receive hidden personal data or a directory of private opportunity-seeking status; a customer specifically wanting MOD04 Counsel's structured, paid, appointment-based advisory/counselling is directed there for that narrow use case only — ordinary business/service discovery stays in Vyapar. |
| Partner / community connector | Refer or share a member-originated or member-shared opportunity, or initiate a partnership request. | Sharing is not endorsement; source/provenance and consent remain visible. |
| Verification operator | Review Level-3 evidence, approve, reject, expire, suspend, or revoke a verification state. | Least privilege; cannot rewrite source evidence or grant reputation through a manual shortcut. |
| Trust & Safety / moderator | Review reports, fraud signals, disputes, harmful content, spam, and appeals. | Actions require reason codes and audit records; serious matters may require legal/law-enforcement escalation. |
| Commercial / revenue operator | Configure products, promotions, campaigns, refunds/credits, and provider reporting. | Cannot change hard eligibility, organic relevance, verification truth, or trust signals. |
| Platform services | Identity & Trust, Search, Notification, Audit, Object Storage, and i18n services provide shared contracts. | MOD01 is the business-data owner for the entities listed in Step 0; it does not fork platform identity or shared infrastructure. |
| MOD05 Dashboard | Read-only consumer of approved Vyapar listing/opportunity summaries for cross-module surfacing. | No write access to Vyapar data; no access to private fields by default. |
| MOD04 Counsel | Optional recipient of a referral only when a member specifically wants structured counselling/advisory delivery. | Referral is not consultation delivery, appointment scheduling, or payment. |
| MOD06 Payment Services | Optional future integration point. | V1 Vyapar collects payment directly through its own payment-gateway integration and does not depend on a MOD06 contract at launch; MOD01 never captures/settles money or stores raw payment credentials regardless of whether collection is direct or (later) via MOD06. |

## Set-level quality gate

| Check | Result |
|---|---|
| Comprehensive - covers full approved module scope | Pass; the approved Step 0 scope is now correctly read as covering business/professional discovery and opportunity distribution as co-equal capabilities, with the narrow Counsel exclusion applied only to structured advisory/counselling delivery. |
| Consistent - no contradicting BRs | Pass; BR04's Community/Public-External source-segment tagging reconciles the source corpus's broader opportunity vision with the Step 0 member-originated/MOD05 boundary without a residual contradiction. |
| Prioritized - every BR ranked | Pass; every BR below is Must or Should and the rationale is stated. |
| No duplicates/overlaps | Pass; profile, verification, discovery, opportunity, enquiry, networking, reputation, monetization, privacy, safety, operations, integration, and compliance are separate business capabilities. |
| Human approval present | Pass; the Product Manager approved all 18 BRs and directed the file to Sealed on 2026-09-12 after the reviewer verification pass. |

## Open blockers

No blockers are currently open. The six items previously tracked here are
resolved below; see the resolution log for where each is recorded.

### Resolved blockers log (this pass)

| ID | Original item | Resolution | Recorded in |
|---|---|---|---|
| BLOCKER-001 | Public/government/NGO opportunity source boundary | Every opportunity is tagged with a source segment — **Community** (the member's own opportunity) or **Public/External** (an opportunity a member found elsewhere and chose to share) — plus submitter attribution. No elaborate provenance/ownership adjudication is built; MOD01 never autonomously ingests a source no member has shared, preserving MOD05's ownership of that pipeline. | BR04 |
| BLOCKER-002 | MOD01 -> MOD06 paid-product contract | V1 Vyapar collects payment for its own products directly through a payment-gateway integration; the MOD06 contract is a future consolidation option, not a launch dependency. A general loose-coupling principle is recorded for every adjacent-module contract. | BR17 |
| BLOCKER-003 | V1 opportunity wedge | Launch opportunity types (employment, freelance/project work, local business/professional service opportunities) are taken directly from the source corpus's own stated V1-wedge recommendation. Launch geography (Hyderabad/Secunderabad, Telangana) is recorded as a non-blocking working assumption inferred from the corpus's own repeated illustrative examples, to be confirmed by the Product Manager before go-to-market. | BR04, BR06 |
| BLOCKER-004 | Level-3 verification policy | A concrete, deliberately lightweight V1 policy, checked directly against real comparable apps (Justdial, WorkIndia, Apna): a phone/OTP baseline for every listing, plus a flexible member-chosen business-existence document (GST/Udyam/PAN/Aadhaar/Shops & Establishment License) to reach Active-Verified — not a mandatory GSTIN requirement. Verified contact, self-declared authority, and single-document professional-credential review round out V1; broader registry coverage/automation is explicit future scope. | BR03 |
| BLOCKER-005 | Legal classification and launch sign-off | Rewritten from a hard pre-launch legal-sign-off gate to a proportionate, documented compliance-awareness posture (DPDP-aligned privacy practice, clear terms, non-misleading commercial claims) appropriate to an early-stage, founder-built product; a formal counsel engagement is recorded as a future scaling milestone, not a Step 1 precondition. | BR18 |
| BLOCKER-006 | Monetization phase and commercial claims | V1 vs V1.5 vs V2 commercial layers are decided directly from the pricing/revenue-model docx's own V1 roadmap (§17-18): V1 = Free core + Opportunity Boost + Business Membership/Workspace + Community/Opportunity Campaigns; qualified-response billing, Business Passport, advertising, and intelligence products are V1.5+. | BR10, BR11 |

## Cross-cutting business rules and invariants

These rules apply across every BR and must not be weakened downstream without a
new Product Manager decision:

1. Vyapar is both a trusted **business/professional discovery ecosystem** and a
   member-originated **opportunity distribution network**; these are co-equal,
   first-class capabilities, not a primary/subordinate pair, and neither may be
   silently narrowed in favor of the other. Vyapar is not a conventional job
   board or a social network. The only discovery use case excluded from Vyapar
   is a member specifically seeking structured counselling, mentorship,
   guidance, or paid appointment-based advisory delivery — that narrow need
   belongs to MOD04 Counsel. Employment is one opportunity type, not the whole
   mental model, and "discovery" is not limited to opportunity-seeking: an
   ordinary business/professional directory lookup is a complete, valid use of
   Vyapar entirely on its own.
2. Hard eligibility and safety exclusions are applied before soft relevance
   ranking. Paid distribution cannot make an ineligible, unsafe, stale, or
   irrelevant record eligible.
3. Verification status, paid status, and reputation are separate axes. Payment
   cannot buy verification, reputation, or an organic ranking position.
4. Community membership is context, not proof that a person or business is
   safe, competent, licensed, or reliable.
5. No reputation history is not a negative reputation signal. New members must
   be able to participate subject to ordinary abuse and eligibility controls.
6. Capability visibility is separate from opportunity-seeking visibility. A
   member may publish "accountant" without exposing "looking for work."
7. Sensitive or inferred attributes must not be used as ranking signals merely
   because they exist. Important inferred preferences require user visibility,
   correction, and confirmation before becoming durable profile state.
8. Normalization, extraction, or AI assistance may propose structure, but must
   preserve uncertainty and require contributor confirmation of material fields.
9. Every opportunity/listing needs provenance, freshness, status, a clear
   source or poster, and a visible Community/Public-External source-segment tag
   (see BR04). Vyapar must not imply that it is the original authority for an
   external source, and must not autonomously ingest a public/government source
   that no member has actively chosen to share.
10. Reports are safety signals, not preference signals. Reviews must be tied to
    a real interaction and must support anti-gaming and non-retaliation controls.
11. MOD01 owns its domain records; common identity, Level-1/2 trust, shared
    credential evidence, search infrastructure, notifications, audit delivery,
    object storage, and payment rails remain platform/adjacent contracts. Every
    such contract should favor the smallest practical, loosely-coupled
    integration shape (a single well-defined API call or event with minimum
    fields) over shared databases or synchronous multi-hop dependencies (see
    BR17).
12. MOD05 receives only an approved read-side summary; it cannot write Vyapar
    domain data or receive private profile/contact fields by default.
13. Vyapar does not store raw card/payment credentials or settle funds itself.
    It integrates with a licensed/compliant payment gateway — directly in V1,
    optionally via a future MOD06 contract — using tokenized references only,
    and does not provide paid appointments or silently create a
    Counsel/Mangaly/Milavn workflow.
14. Every consequential verification, moderation, promotion, privacy, payment
    state, and administrative action is attributable and auditable.

## Lifecycle and status model

The following business states are required; exact transition permissions and
timers belong in Step 2, except where noted.

| Object | States | Business meaning / invariant |
|---|---|---|
| Business or professional listing | Draft -> Submitted -> Active-Unverified or Active-Verified -> Suspended -> Archived | A listing may be visible only under the approved visibility policy; unverified and verified states are never visually conflated. Suspension stops relevant distribution without destroying audit history. |
| Verification record/evidence | Not Started, Pending Review, Verified, Expiring, Expired, Rejected, Revoked, Disputed | Verification is evidence about a defined claim at a time, not a permanent character guarantee. Expiry/revocation must affect the displayed claim and applicable eligibility. |
| Member-originated opportunity | Draft, Submitted, Pending Review, Active, Paused, Stale, Expired, Closed, Removed | Uncertain or unsafe records cannot enter normal distribution as confirmed fact. Stale/expired records are not normally ranked. Removed records retain a reason and audit trail. |
| Enquiry | Submitted, Open, Awaiting Response, In Progress, Resolved, Closed, Withdrawn, Restricted | Enquiry status must not imply a paid consultation, service completion, or payment. Contact disclosure follows consent and privacy settings. |
| Partnership request | Draft, Pending, Accepted, Declined, Withdrawn, Restricted, Closed | Pending requests do not auto-expire until the business policy is approved; a request is not a follower relationship or general chat channel. |
| Review/reputation signal | Draft, Submitted, Published, Disputed, Hidden, Removed | A review requires a qualifying interaction; dispute/removal does not silently erase the audit history or create a new rating. |
| Promotion/campaign | Draft, Awaiting Payment, Scheduled, Active, Paused, Completed, Cancelled, Rejected, Refunded/Credited | Paid distribution is bounded by time/budget/entitlement and never overrides eligibility, relevance, safety, or verification. |

---

## BR01 - Business Profile and Business Presence

**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**

Business owners and customers lack a trusted, reusable business presence that
explains what a business does, where it operates, who may contact it, and what
opportunities or services it offers. A one-off listing or forwarded message
loses context, makes repeat discovery difficult, and prevents a business from
building an evidence-based history.

**Proposed outcome**

A business member can create and maintain one Vyapar-owned BusinessProfile with
business name, description, categories/services, operating locality or service
area, service mode, contact and enquiry preferences, opportunity participation,
provenance, verification state, and visibility controls. Customers can inspect
the business's current state, relevant services, and trust/source information
before making an enquiry — including customers who arrive with no opportunity
in mind and are simply looking for a business, exactly as they would in any
trusted local directory. Profile fields that are not verified are labelled as
member-provided or unverified rather than presented as facts established by
ForKhatri.

**Affected users and systems**

Business owners, authorized business representatives, customers, Search, Trust
& Safety, Identity & Trust, Object Storage, MOD05 read-only surfacing, and the
Admin Console.

**Constraints**

- BusinessProfile is owned by MOD01; base Member identity is owned by Identity
  & Trust.
- Business verification, paid status, and reputation must remain independent.
- A business may have multiple services/opportunities, but each record must
  retain its own status, source, and freshness.
- Contact details and enquiry channels are shown only according to the owner's
  visibility and consent settings.

**Out of scope (for this BR specifically)**

Payment settlement, product checkout, appointment booking, event management,
financial-product offers, generic social posting/following, and Counsel's
ExpertProfile.

**Worth check**

Without a persistent business presence, discovery is reduced to disconnected
posts and customers cannot evaluate the provider across enquiries and outcomes.
That is a real deficiency in a trusted business discovery ecosystem, not a
cosmetic profile enhancement.

**Quality gate (ISO 29148, adapted for business-level requirements)**

Necessary Pass · Unambiguous Pass · Complete Pass · Singular Pass · Feasible
Pass · Verifiable Pass · Correct Pass · Conforming Pass

**Decisions**

- DEC-001 · In the context of customers repeatedly evaluating the same business
  across opportunities, facing one-off posts versus a durable business
  presence, we chose a MOD01-owned BusinessProfile over post-only identity, to
  achieve reusable discovery and accountable interactions, accepting that
  profile lifecycle and evidence maintenance must be operated.

**Assumptions**

- The business representative has authority to act for the named business;
  the evidence source and approval method are decided concretely in BR03.

**Traced to (Step 2 FRs):** FR01, FR02, FR03

**Traced to:** `modules/modules.md` MOD01 Scope/Data owned; PM P3.4/P4.1;
Complete Product Definition §§5, 6, 12-15; Vyapar_03 §§1-4; Pricing Model
§§5.3, 5.6.

**Review history**

- 2026-09-12 - Drafted for Product Manager review; no approval yet.

**Approval:** Product Manager - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR02 - Professional and Freelancer Listing Presence

**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**

Professionals, freelancers, and service providers cannot reliably present
capabilities, experience, services, availability, and work preferences in a
business-discovery context without being forced into either a generic resume or
MOD04's structured advisory model. Customers and businesses therefore miss
people who could serve a need.

**Proposed outcome**

A member can create and maintain a ProfessionalListingProfile that represents
what they can do or offer, relevant experience/evidence, service areas, work
mode, availability, languages, enquiry preferences, and independent privacy
controls. The listing can be discovered by customers and businesses using
Vyapar search and can receive enquiries or opportunity responses. A member may
hold both a Vyapar ProfessionalListingProfile and a MOD04 ExpertProfile; each
has separate purpose, ownership, visibility, and lifecycle.

**Affected users and systems**

Professionals, freelancers, service providers, customers, businesses,
Identity & Trust, shared `VerifiedCredential`, Search, Trust & Safety, and
MOD04 referral boundaries.

**Constraints**

- Vyapar may reference a shared verified-credential fact from Identity & Trust
  but must not merge its listing with Counsel's ExpertProfile.
- The ProfessionalListingProfile supports both ordinary business/professional
  discovery (a customer or business finding this person for any legitimate
  reason) and opportunity response, enquiries, and business networking. It is
  not, however, a route into MOD04 Counsel's structured, paid, appointment-based
  advisory workflow — that narrow consultation-delivery need is served by
  Counsel's ExpertProfile, not Vyapar.
- A capability claim may be visible without exposing that the member is seeking
  work; seeking status is private by default unless the member chooses otherwise.
- Profile enrichment must be progressive and must show value before demanding a
  complete resume.
- Experience and capability claims not backed by evidence remain member-provided
  claims, not ForKhatri certification.

**Out of scope (for this BR specifically)**

Appointment scheduling, paid advisory delivery, escrow, full portfolio hosting,
recruitment ATS, or public popularity/endorsement mechanics.

**Worth check**

Professional/freelancer discovery is explicitly in the approved MOD01 scope and
is a distinct affected-user need from business-directory search. Omitting it
would leave the module unable to serve the professionals and service providers
named in its primary users.

**Quality gate (ISO 29148, adapted for business-level requirements)**

Necessary Pass · Unambiguous Pass · Complete Pass · Singular Pass · Feasible
Pass · Verifiable Pass · Correct Pass · Conforming Pass

**Decisions**

- DEC-001 · In the context of the same person possibly offering a service in
  Vyapar and formal advice in Counsel, we chose separate ProfessionalListingProfile
  and ExpertProfile entities with only a shared verified-credential reference,
  over a merged "professional" profile, to preserve business ownership,
  liability, and monetization boundaries, accepting cross-module identity-link
  coordination.

**Assumptions**

- Language, experience, portfolio, and availability are member-controlled
  attributes; verification claims specific to this listing are decided
  concretely in BR03.

**Traced to (Step 2 FRs):** FR03, FR04, FR05, FR06

**Traced to:** `modules/modules.md` MOD01 Scope/Data owned and MOD04 boundary;
Architecture ADR-013; PM P3.4/P4.1/P4.2; Complete Product Definition §§6-15;
Vyapar_01 §§3-7; Vyapar_03 §§1-8.

**Review history**

- 2026-09-12 - Drafted; no approval yet.
- 2026-09-12 - Product Manager correction pass: removed language that treated
  ordinary discovery of this listing as subordinate to opportunity response;
  discovery and opportunity response are equally valid uses of this listing.

**Approval:** Product Manager - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR03 - Level-3 Business and Professional Verification

**Priority:** Must
**Status:** Ready for Review
**Confidence:** High - the need, verification dimensions, and the V1
evidence/registry policy are now all decided directly below as a deliberately
lightweight first version, with explicit room to expand categories and
registries in later phases.

**Problem**

Customers, partners, and members cannot distinguish a self-asserted business or
professional claim from evidence that a business exists, an owner is authorized,
a license/credential is current, or a contact/service channel is legitimate.
That creates foreseeable risks of fake businesses, fake jobs, impersonation,
misleading credentials, advance-payment scams, and reputational harm.

**Proposed outcome**

Vyapar maintains a Level-3 BusinessVerificationRecord that records the claim
being checked, evidence source, verification method, verifier, decision,
verification date, expiry/review date, limitations, and current state. Users
see a bounded, plain-language status and evidence scope; they do not receive a
blanket "safe" or "good business" guarantee.

Real comparable apps were checked directly rather than assumed. Justdial does
not require a GSTIN to list a business at all — name, contact, address, and
category are sufficient, with ID/business proof requested only case-by-case.
WorkIndia verifies employers primarily through OTP plus a company-profile
review (approved in hours), and only asks for GST/MSME evidence in specific
edge cases (a multi-location mismatch, or a staffing/recruitment-agency
business type). Apna treats a GST Certificate as only one of several accepted
company-verification documents — alongside Company PAN, CIN, an FSSAI
Certificate, or a Shops & Establishment License — with a personal PAN Card or
Aadhaar as its actual fastest verification path. No comparable app makes
GSTIN a mandatory universal requirement, and doing so here would also wrongly
exclude the many small or informal Vyapar businesses and professionals who are
not GST-registered. V1 verification follows this precedent: a universal
phone/OTP baseline plus one flexible, member-chosen proof of business
existence, not a single mandatory registry check:

- **Contact/identity baseline** (every listing, no exceptions): a
  platform-verified mobile number for the business/professional, matching the
  OTP-first pattern all three comparable apps above use.
- **Business-existence claim** (needed to reach Active-Verified, not to exist
  as a listing): the member picks ONE document from a short menu of easily
  checkable proofs — a GST Certificate/GSTIN, Udyam Registration, a business
  or personal PAN Card, Aadhaar, or a Shops & Establishment License —
  format-validated at entry and spot-checked by a verification operator
  against the matching public lookup where one exists (GST/Udyam). A listing
  without any of these can still exist and be discoverable as
  Active-Unverified; it simply does not carry the verified label. A manual
  lookup is sufficient for V1; an automated read-only registry API integration
  is a later-phase improvement, not a launch requirement.
- **Ownership/authority claim**: self-declaration of authority to represent the
  business, checked by an operator only on report or dispute rather than
  pre-screened for every listing.
- **Professional-credential claim** (professional/freelancer listings only):
  one uploaded evidence document (for example, a license or certificate
  identifier) reviewed visually by a verification operator; no live external
  registry integration in V1.
- **Re-verification cadence**: an annual self-reconfirmation prompt for the
  business-existence claim; immediate re-review triggered by a report or
  dispute.
- **Manual-review SLA**: a working operator target of 3 business days for V1,
  stated as an internal operating target rather than a contractual SLA.
- **Failed/disputed/expired outcome**: the listing reverts to
  Active-Unverified with a visible "unverified" label rather than being removed
  outright; repeated or serious failure routes to BR13 Trust & Safety review.

Additional claim categories, registries, and automated integrations are
explicit future scope (V1.5+), not a V1 launch precondition.

**Affected users and systems**

Businesses, professionals, customers, partners, verification operators,
Identity & Trust, external KYC/registry providers (GST/Udyam public lookup for
the V1 document menu), shared VerifiedCredential, Audit, Object Storage, and
Search/ranking.

**Constraints**

- Level-3 is domain-specific and layered on platform identity/trust; it does
  not replace base authentication or imply moral/financial reliability.
- Payment and subscription status cannot create or improve verification.
- Evidence access follows least privilege, retention, consent, and applicable
  registry terms; raw identity documents are not exposed in public listings.
- Expired, revoked, disputed, or failed evidence must change the displayed claim
  and any eligibility that depends on it.
- The V1 claim/evidence policy above is the launch scope; expanding it (new
  claim categories, automated registry APIs, additional jurisdictions) is a
  deliberate future-phase decision, not something Step 2 should silently grow.

**Out of scope (for this BR specifically)**

Universal KYC for every member, a government endorsement, criminal/background
clearance unless separately authorized and legally reviewed, payment collection,
or an overall reputation score based only on verification.

**Worth check**

Trust is the central reason to choose a community business/professional
ecosystem over informal forwarding and generic directories. Without evidence-
based verification, the module would expose users to material fraud and
misrepresentation risk and could not honestly distinguish a verified listing
from an advertisement.

**Quality gate (ISO 29148, adapted for business-level requirements)**

Necessary Pass · Unambiguous Pass - the V1 claim/evidence policy is decided
above · Complete Pass for the V1 scope decided here; broader category/registry
expansion is explicit future scope · Singular Pass · Feasible Pass - the V1
policy uses only a manual public-portal lookup and a single-document review ·
Verifiable Pass - decisions are auditable and the policy above is directly
testable · Correct Pass · Conforming Pass

**Decisions**

- DEC-001 · In the context of trust claims being material to discovery and
  safety, we chose scoped evidence-and-status records over a binary "verified
  user" badge, to avoid overclaiming what a check proves, accepting more
  operational and explanatory work.
- DEC-002 · In the context of Vyapar and Counsel both needing credential facts,
  we chose the architecture's shared VerifiedCredential record with separate
  module-owned profile meaning, over duplicated verification records, to prevent
  conflicting credential truth, accepting cross-module contract coordination.
- DEC-003 · In the context of the Product Manager's explicit direction to keep
  verification simple and to ground it in what real comparable apps actually
  do rather than assumption, we chose a phone/OTP baseline plus a flexible,
  member-chosen business-existence document (GST/Udyam/PAN/Aadhaar/Shops &
  Establishment License) over a mandatory GSTIN requirement, after directly
  checking Justdial (no GSTIN requirement at all), WorkIndia (OTP/profile-first,
  GST/MSME only in edge cases), and Apna (GST is only one of several accepted
  company-verification documents, with personal PAN/Aadhaar as the fastest
  path) — to achieve a shippable trust baseline that does not exclude
  unregistered/informal businesses, accepting that category coverage and
  registry automation expand in later phases.
- DEC-004 · (Step 2 approver check, 2026-09-12) In the context of the V1
  document menu above listing Aadhaar, facing UIDAI's Aadhaar (Authentication
  and Offline Verification) Regulations 2021 - which direct verification
  entities not to collect or store Aadhaar numbers, with any retained copy
  masked and irretrievable - and UIDAI's move to require private entities to
  register and use approved offline QR/XML or API methods rather than collect
  copies, we chose to drop Aadhaar from the V1 menu (FR08 DEC-002) over storing
  masked Aadhaar images, to stay simple and compliant, accepting four options
  (GST/GSTIN, Udyam, PAN, Shops & Establishment License) for V1. Aadhaar
  offline QR verification through a UIDAI-registered path is future scope.

**Assumptions**

- The public GST and Udyam lookup portals can lawfully be used for a manual
  spot-check in V1 for those two document types. PAN and Aadhaar have no
  equivalent open public-lookup portal for third-party verification; for V1,
  a self-declared PAN/Aadhaar document is accepted as visual evidence only
  (an uploaded copy reviewed by an operator, not machine-verified against a
  government database) — a future automated PAN/Aadhaar verification
  integration would require an authorized KYC provider and its own
  vendor/legal review, consistent with UIDAI/Income Tax API access rules.

**Traced to (Step 2 FRs):** FR06, FR07, FR08, FR09, FR10

**Traced to:** `modules/modules.md` MOD01 Level-3 scope/data; Architecture
ADR-004, ADR-005, ADR-013; PM P2 Rules 7/11/12, P3.12, P5.7; Complete Product
Definition §§48-52; critqureport §§9-11, 18; Vyapar_01 §§3-7;
Vyapar_03 §§1, 3, 8; external research R8 (Justdial, WorkIndia, and Apna
verification-requirement precedent, below).

**Review history**

- 2026-09-12 - Drafted; legal/evidence-policy blocker remains open.
- 2026-09-12 - Product Manager correction pass: resolved the verification-
  policy blocker with a concrete, deliberately lightweight V1 policy; broader
  registry coverage remains explicit future scope, not a launch blocker.

**Approval:** Product Manager - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR04 - Member-Originated Opportunity Creation and Lifecycle

**Priority:** Must
**Status:** Ready for Review
**Confidence:** High - the Community/Public-External source-segment rule below
resolves the prior source-boundary ambiguity directly, and the V1 launch
opportunity-type set uses the source corpus's own stated wedge recommendation.

**Problem**

Businesses and members share jobs, projects, service needs, hiring needs, and
business opportunities through fragmented messages and one-off posts. The
information is often incomplete, uncertain, stale, or impossible to attribute,
so relevant people cannot act and moderators cannot assess safety.

**Proposed outcome**

A member or authorized business representative can create, share, or upload an
opportunity. Every opportunity is tagged with one of two source segments —
**Community** (the member's own job/project/service/hiring/partnership need) or
**Public/External** (an opportunity the member found elsewhere, such as a
government scheme or public posting, that they believe is relevant and choose
to share) — together with the submitting member's identity, so every user can
see where an opportunity came from without a separate ownership-adjudication
process. Vyapar structures the known title, type, requirements, value/
compensation, location, work mode, timing, eligibility, response method,
source/provenance, freshness, expiry/deadline, and trust signals; it marks
uncertain fields and asks the contributor to confirm material ones. The
opportunity moves through the lifecycle in this file and is only normally
distributed when active, sufficiently structured, attributable, and not blocked
by moderation or safety rules.

**Affected users and systems**

Opportunity providers, seekers, connectors, business/professional listings,
Search, ranking/distribution, Object Storage, Trust & Safety, Audit,
Notification, and MOD05 if an approved summary is later surfaced.

**Constraints**

- Vyapar accepts member-originated (Community) and member-shared
  (Public/External) opportunities alike, provided every record carries a
  visible source-segment tag and submitter attribution. Vyapar does not
  autonomously scrape, crawl, or ingest public/government/NGO inventory on its
  own initiative — that non-member-originated pipeline remains MOD05
  Dashboard's Local Information Intelligence.
- V1 launch opportunity types are employment, freelance/project work, and
  local business/professional service opportunities (hiring, service requests,
  and business-to-business needs), per the source corpus's own explicit
  V1-wedge recommendation (critqureport §24). Business partnership, training,
  and community/government opportunity types remain supported by the same data
  model but are not the initial promotional focus. V1 launch geography is a
  non-blocking working assumption of Hyderabad/Secunderabad (Telangana),
  inferred from the corpus's own repeated illustrative examples; the Product
  Manager should confirm or override this before go-to-market, but it does not
  gate this BR's approval.
- A pasted URL, text, or screenshot may be a contribution input, but the
  contribution must remain attributed and must not convert inferred data into a
  confirmed fact.
- Opportunity is the canonical concept; job, project, hiring, service, and
  business collaboration are types/patterns, not separate products.
- Closed, expired, removed, or stale records retain provenance and audit history
  but must not continue normal distribution.

**Out of scope (for this BR specifically)**

Autonomous scraping/crawling of any external source; a Public/External item
that no member has actively chosen to share; employment contracts; escrow,
payments, or transaction settlement; Milavn events; Counsel appointments; and a
public social feed.

**Worth check**

Member-originated and member-shared opportunities are explicit MOD01-owned
data in Step 0 and are the supply side required for discovery, enquiries, and
monetization. Without a structured lifecycle, the core ecosystem would be an
unaccountable message board whose stale or fraudulent inventory directly harms
trust. The Community/Public-External segment split lets Vyapar honor the source
corpus's broader opportunity vision without silently absorbing an autonomous-
ingestion pipeline that Step 0 placed in MOD05.

**Quality gate (ISO 29148, adapted for business-level requirements)**

Necessary Pass · Unambiguous Pass - the source-segment/attribution rule
directly resolves the prior ambiguity · Complete Pass · Singular Pass ·
Feasible Pass · Verifiable Pass · Correct Pass - the source-segment rule
reconciles the corpus's broader vision with the sealed member-originated/MOD05
boundary · Conforming Pass

**Decisions**

- DEC-001 · In the context of the source corpus wanting broad opportunity
  supply (including public/government items) while Step 0 places autonomous
  public-source ingestion in MOD05, we chose a simple Community/Public-External
  source-segment tag plus submitter attribution over either an elaborate
  provenance-adjudication system or a blanket exclusion of member-shared
  external content, to preserve both real product value and the module
  boundary, accepting that Vyapar never ingests a source a member hasn't
  actively chosen to share.
- DEC-002 · In the context of extracted fields sometimes being incomplete or
  uncertain, we chose explicit uncertainty plus contributor confirmation over
  fabricated completeness, to protect trust, accepting additional authoring
  friction.
- DEC-003 · In the context of a very broad opportunity taxonomy versus a
  solo-founder V1, we chose to launch with employment, freelance/project, and
  local business/professional service opportunities — the wedge the source
  corpus's own critique explicitly recommends — over attempting full-taxonomy
  breadth at launch, to achieve a shippable, measurable V1, accepting that
  other opportunity types remain modeled but not promoted until demand is
  observed.

**Assumptions**

- The V1 launch-geography assumption (Hyderabad/Secunderabad) is inferred from
  the corpus's own repeated illustrative examples, not an explicit Product
  Manager geography decision; it should be confirmed before go-to-market but
  does not block this BR.

**Traced to (Step 2 FRs):** FR11, FR12, FR13, FR14

**Traced to:** `modules/modules.md` MOD01 scope/out-of-scope/data; PM P3.2,
P3.3, P3.9, P5.2, P5.4; Complete Product Definition §§17-24, 41-47;
Vyapar_02 §§8, 12; Vyapar_03 §§3, 9-10; Vyapar_01 §§1-3; critqureport §24.

**Review history**

- 2026-09-12 - Drafted; source-boundary and V1-wedge blockers remain open.
- 2026-09-12 - Product Manager correction pass: resolved the source-boundary
  question with the Community/Public-External segment rule, and the V1 wedge
  using the source corpus's own stated recommendation.

**Approval:** Product Manager - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR05 - Business, Professional, and Customer Discovery

**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**

Members and customers cannot reliably find relevant businesses, professionals,
freelancers, or services beyond their immediate contacts. A directory without
meaningful filters and trust context produces low-quality results, while a
popularity-only feed disadvantages new or less-connected providers.

**Proposed outcome**

A member can intentionally search and browse business and professional
listings using the information needed to evaluate a potential provider, such as
capability/service, locality or service area, work mode, availability, category,
verification state, and freshness. Search results provide meaningful organic
sorting and filters, show why a result is relevant where applicable, and make
verification, paid placement, provenance, and user-provided claims visually
distinct. Zero-result states offer user-controlled broadening rather than
silently relaxing hard constraints.

**Affected users and systems**

Customers, businesses, professionals, Search, taxonomy, Identity & Trust,
Trust & Safety, and MOD05 read-only cross-module surfacing.

**Constraints**

- This discovery capability serves two equally valid uses: an ordinary
  "find a business or professional" lookup with no opportunity involved at
  all — comparable to how a member would use any trusted local business
  directory — and discovery in service of the opportunity-distribution loop
  and attributable enquiries/networking. The only discovery need Vyapar does
  not serve is a member specifically wanting MOD04 Counsel's structured, paid,
  appointment-based advisory search.
- This is Vyapar's in-module discovery/ranking; MOD05 owns cross-module Fair
  Exposure, not Vyapar's internal search.
- Search must not expose private contact details, private opportunity-seeking
  state, or sensitive attributes without consent.
- New or low-history listings remain discoverable under ordinary safety and
  eligibility checks.
- Promoted results must be clearly labelled and cannot be presented as organic
  relevance.

**Out of scope (for this BR specifically)**

Dashboard cross-module ranking, Counsel appointment search, event discovery,
matrimonial discovery, and a popularity or follower graph.

**Worth check**

Business/professional/customer discovery is named directly in the approved
Step 0 scope, as its own capability, not as a byproduct of opportunity
distribution. Without it, profiles and verification have no customer value and
the module cannot solve the stated fragmentation problem — and members lose
the ordinary "just find me a business" experience `modules/modules.md` scopes
in and the Product Manager has explicitly confirmed Vyapar should provide.
(The deeper Vyapar product-research corpus does not itself describe this
standalone directory experience — it is built around opportunity discovery —
but Step 0's sealed boundary is the higher-priority source, and the Product
Manager's direction is explicit; see the Scope-of-this-step note above.)

**Quality gate (ISO 29148, adapted for business-level requirements)**

Necessary Pass · Unambiguous Pass · Complete Pass · Singular Pass · Feasible
Pass · Verifiable Pass · Correct Pass · Conforming Pass

**Decisions**

- DEC-001 · In the context of internal versus cross-module discovery, we chose
  MOD01-owned organic search and ranking for Vyapar records, over delegating all
  ranking to Dashboard, to preserve the module boundary and provider intent,
  accepting that Dashboard will need a separate read-side exposure policy.

**Assumptions**

- Taxonomy and search implementation may begin with indexed structured/text
  retrieval and evolve later; no particular search vendor is a BR decision.

**Traced to (Step 2 FRs):** FR15, FR16, FR17

**Traced to:** `modules/modules.md` MOD01 scope/out-of-scope (the source of the
standalone discovery requirement); PM P2 Rules 1, 4-8, P3.6-P3.8, P5.1/P5.3;
Complete Product Definition §§37-40, 54-56; Vyapar_02 §§4-6, 12; Vyapar_03
§§4-7 (these apply to in-module ranking/discovery mechanics generally; note
that the underlying research corpus designs these mechanics for opportunity
discovery specifically, not a standalone business directory — see this BR's
Worth check); external research R8 (Justdial precedent for a low-friction
local-business discovery experience, below).

**Review history**

- 2026-09-12 - Drafted for Product Manager review; no approval yet.
- 2026-09-12 - Product Manager correction pass: removed language that
  subordinated ordinary business/professional discovery to the
  opportunity-distribution loop; both are equally valid, first-class uses of
  this capability.

**Approval:** Product Manager - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR06 - Opportunity Relevance, Ranking, and Distribution

**Priority:** Must
**Status:** Ready for Review
**Confidence:** High - principles are high-confidence, and BR04's V1 wedge now
sets the initial ranking-signal scope; exact weights remain an experimentally
tuned Step 2 detail.

**Problem**

Relevant member-originated opportunities remain invisible when people do not
know the right vocabulary or do not repeatedly search. Conversely, volume,
popularity, or payment can overwhelm members with irrelevant, stale, unsafe, or
duplicative results and destroy trust.

**Proposed outcome**

For eligible opportunities (Community and Public/External alike, per BR04),
Vyapar supports search, "For You," exploration, nearby discovery, community
views, and appropriate proactive distribution. The business behavior is:
structure -> retrieve -> apply hard eligibility -> score soft relevance -> rank
-> diversify -> distribute. V1 uses deterministic, configuration-driven signals
such as capability/service fit, intent, location, timing, work mode, value/
compensation, experience/eligibility, freshness, and trust. Every meaningful
recommendation can explain its main reasons and important gaps. Distribution
optimizes relevant reach, not maximum reach, and respects notification fatigue.

**Affected users and systems**

Seekers, providers, Search, taxonomy, opportunity lifecycle, notification,
trust/reputation, promotion, analytics, and MOD05's read-only consumer path.

**Constraints**

- Hard constraints are not soft score penalties.
- Sensitive characteristics, community status, account age, paid status, or
  raw popularity cannot silently determine opportunity access.
- Reports and safety incidents never become positive/negative preference signals.
- Paid distribution can increase reach only inside the eligible/relevant safe
  audience and must not override organic relevance.
- "Why this opportunity" must be derived from the same approved signals used for
  ranking; opaque percentage match claims are not acceptable in V1.
- Embeddings, learning-to-rank, bandits, or AI hot-path dependency are future
  options, not prerequisites for the deterministic baseline.

**Out of scope (for this BR specifically)**

Dashboard Fair Exposure, predictive hiring, automated decisions about a
person's suitability, and opaque AI matchmaking.

**Worth check**

Discovery without relevant distribution is a genuine failure of the product
promise; a static directory cannot address opportunity invisibility. Ranking and
distribution are necessary to turn trusted records into useful connections,
while the constraints protect users from monetization and popularity bias.

**Quality gate (ISO 29148, adapted for business-level requirements)**

Necessary Pass · Unambiguous Pass · Complete Pass - BR04 sets the launch
opportunity-type scope; exact weights are a Step 2 tuning exercise · Singular
Pass · Feasible Pass · Verifiable Conditional Pass - explanations and
guardrails are verifiable; numerical relevance thresholds belong in Step 2 ·
Correct Pass · Conforming Pass

**Decisions**

- DEC-001 · In the context of sparse early data and high harm from opaque
  decisions, we chose deterministic, explainable eligibility/ranking/diversity
  rules over ML-first ranking, to achieve measurable relevance and user trust,
  accepting a less adaptive initial model.
- DEC-002 · In the context of paid distribution, we chose relevant reach within
  the eligible audience over pay-to-win ranking, to protect free discovery and
  trust, accepting that commercial inventory cannot always receive the largest
  audience.

**Assumptions**

- The first score weights and notification thresholds are product configuration
  subject to experiment governance, not fixed prices or hidden personalization.

**Traced to (Step 2 FRs):** FR13, FR17, FR18, FR19, FR20, FR21, FR55

**Traced to:** PM P2 Rules 2, 4-8, P3.6-P3.8, P3.13-P3.15, P5.5; Complete
Product Definition §§23-36, 52-53, 57; Pricing Model §§2, 5.2, 6, 14, 16;
Vyapar_01 §§4-7; Vyapar_03 §§5-8; critqureport §24.

**Review history**

- 2026-09-12 - Drafted; launch wedge remains open in BLOCKER-003.
- 2026-09-12 - Product Manager correction pass: launch wedge resolved via
  BR04; this BR's scope note updated accordingly.

**Approval:** Product Manager - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR07 - Business Enquiries and Opportunity Responses

**Priority:** Must
**Status:** Ready for Review
**Confidence:** Medium - the core need is clear; response/contact disclosure
and qualified-response billing follow the monetization phasing decided in
BR10/BR11.

**Problem**

Discovery has no value if an interested customer, seeker, or provider cannot
make a safe, attributable next move. Current informal contact paths expose
personal details too early, lose the context of the enquiry, and make it
impossible to distinguish a genuine lead from spam or a paid consultation.

**Proposed outcome**

A member can submit an enquiry or opportunity response appropriate to the record
(for example, ask a business a question, express interest, apply, contact, or
submit a proposal). The provider can view, acknowledge, progress, resolve, or
close the enquiry with a record of the related listing/opportunity and consented
contact channel. Qualified response/introduction billing (see BR10/BR11's
monetization-phase table) is a V1.5 experiment, not enabled at launch; it must
never sell raw contact lists when it is enabled.

**Affected users and systems**

Customers, seekers, businesses, professionals, opportunity providers,
Notification, Identity & Trust, Trust & Safety, Audit, MOD04 referral, and
MOD06 if a qualified-response product is enabled later.

**Constraints**

- Contact disclosure is purpose-limited, consent-based, and revocable where
  practical; the platform is not a generic chat service.
- A response does not mean that a hire, sale, service, or payment occurred.
- Vyapar may refer a business problem to Counsel, but it does not create or
  manage the Counsel appointment.
- Spam/rate limits, reporting, blocking, and provider safety controls are
  required; a provider cannot retaliate against a report by changing trust data.

**Out of scope (for this BR specifically)**

Appointment-based advisory delivery, escrow, transaction settlement, raw lead
lists, persistent social messaging, and any guarantee that an enquiry produces
a commercial outcome.

**Worth check**

Customer discovery without an attributable enquiry/response path is a genuine
dead end, and unstructured contact sharing creates safety and privacy risk. This
capability is necessary for the module's core discovery-to-connection loop.

**Quality gate (ISO 29148, adapted for business-level requirements)**

Necessary Pass · Unambiguous Pass - "qualified" is intentionally disabled at
launch per BR10/BR11's monetization phasing · Complete Pass · Singular Pass ·
Feasible Pass · Verifiable Pass · Correct Pass · Conforming Pass

**Decisions**

- DEC-001 · In the context of different opportunity types needing different
  actions, we chose one underlying Opportunity Response concept with typed
  presentations over separate mini-products, to preserve consistent tracking,
  safety, and analytics, accepting that each type needs a clear action label.
- DEC-002 · In the context of business value in qualified introductions versus
  privacy risk, we chose qualified consented interaction over selling contact
  data, accepting that monetizable volume will be lower.

**Assumptions**

- The first response channel may be asynchronous and platform-mediated; real-
  time chat is not assumed.

**Traced to (Step 2 FRs):** FR16, FR22, FR23, FR24

**Traced to:** `modules/modules.md` Enquiry/Data owned and MOD04 boundary; PM
P3.10-P3.12, P5.1/P5.2/P5.8; Complete Product Definition §§40-46;
Pricing Model §§5.5, 14.1, 15; Vyapar_02 §§6, 9-11.

**Review history**

- 2026-09-12 - Drafted; qualified-response and payment contract questions remain open.
- 2026-09-12 - Product Manager correction pass: qualified-response phasing
  clarified via BR10/BR11's resolved monetization roadmap; payment collection
  is self-contained per BR17.

**Approval:** Product Manager - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR08 - Business Networking and Partnership Requests

**Priority:** Should
**Status:** Ready for Review
**Confidence:** High

**Problem**

Businesses and professionals cannot express a structured interest in
collaboration, referral, supplier, hiring, or partnership opportunities without
falling back to informal messages or a social-network connection model.

**Proposed outcome**

A member can create or respond to a partnership request containing the need,
offer, expectations, category, locality, timing, and intended next step. The
recipient can accept, decline, withdraw, restrict, or close the request, and
both parties can see the request's provenance, consent, and current state. The
workflow supports meaningful business networking without requiring followers,
public likes, or an always-on chat relationship.

**Affected users and systems**

Business owners, professionals, service providers, partners, connectors,
Notification, Identity & Trust, Trust & Safety, and Audit.

**Constraints**

- A partnership request must be distinct from an enquiry, job application,
  Counsel appointment, or Milavn event registration.
- The request must not disclose private profile/contact fields before the
  recipient's permitted action.
- No auto-expiry rule is assumed until Product Manager approval; a pending
  request remains auditable and can be restricted.
- Verification may inform trust context but cannot be purchased through a paid
  placement.

**Out of scope (for this BR specifically)**

Follower graphs, general social feed mechanics, public endorsements, transaction
execution, contract management, and event-based networking.

**Worth check**

The capability is explicitly in the approved MOD01 scope and is a meaningful
business use case, but core discovery and enquiries can operate without a full
partnership workflow. It therefore passes the worth check as a Should: valuable
and necessary for the complete module vision, not a reason to delay the first
liquidity experiment if capacity is constrained.

**Quality gate (ISO 29148, adapted for business-level requirements)**

Necessary Pass · Unambiguous Pass · Complete Conditional Pass - pending-state
expiry policy is intentionally open · Singular Pass · Feasible Pass ·
Verifiable Pass · Correct Pass · Conforming Pass

**Decisions**

- DEC-001 · In the context of networking being a named capability but social
  graphs being an explicit non-goal, we chose request-based, purpose-limited
  partnership workflow over follows/connections, to support business outcomes
  without turning Vyapar into LinkedIn-lite, accepting less passive discovery.

**Assumptions**

- The partnership request itself is a MOD01-owned record and can later be
  linked to a qualifying interaction for reputation, subject to consent.

**Traced to (Step 2 FRs):** FR25, FR26

**Traced to:** `modules/modules.md` PartnershipRequest and MOD01 rationale; PM
P1.3-P1.4, P3.10-P3.12, P5.8; Complete Product Definition §§31, 41-46;
critqureport §§12, 17-18; Pricing Model §5.4.

**Review history**

- 2026-09-12 - Drafted; no approval yet.

**Approval:** Product Manager - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR09 - Interaction-Based Reviews and Reputation Signals

**Priority:** Must
**Status:** Ready for Review
**Confidence:** Medium - the need is clear; review eligibility, bilateral
feedback, aggregation, and dispute/redress rules need policy confirmation.

**Problem**

Members cannot learn from prior business/professional interactions, while
providers have no accountable feedback loop. Unbounded public ratings would,
however, invite popularity bias, retaliation, review manipulation, and the
false assurance that community identity or payment equals trust.

**Proposed outcome**

Vyapar records reviews and reputation signals only from defined, attributable
interactions such as an enquiry, response, partnership, or declared outcome.
Members can distinguish verification evidence, provider/listing quality,
interaction feedback, reports, disputes, and outcomes. New members are not
penalized for lacking history. Users can report retaliation/manipulation, and
moderators can dispute, hide, or remove a signal with an auditable reason while
preserving the underlying accountability record.

**Affected users and systems**

Providers, customers, partners, reviewers, Trust & Safety, shared Reputation
Engine in Identity & Trust, Audit, Search/ranking, and Admin Console.

**Constraints**

- Review evidence and reputation are separate from reports and verification.
- Payment, subscription, promotion, community membership, and account age
  cannot directly purchase or determine reputation.
- Reputation is contextual to the interaction and should not be shown as a
  universal character guarantee.
- The common platform engine may aggregate signals, but MOD01 remains the sole
  writer of Vyapar's domain-specific Review/ReputationSignal records.

**Out of scope (for this BR specifically)**

Public ratings of every member without an interaction, popularity leaderboards,
automatic "good person" scores, and cross-module reputation leakage without an
approved context/consent contract.

**Worth check**

The approved scope expressly requires reviews and in-module reputation. Without
an interaction-based signal, trust cannot improve through real outcomes and
users have little protection against repeated low-quality providers; without the
guardrails, the reputation feature itself creates a new safety problem.

**Quality gate (ISO 29148, adapted for business-level requirements)**

Necessary Pass · Unambiguous Conditional Pass - qualifying interaction and
aggregation policy remain to be finalized · Complete Conditional Pass - dispute
and anti-gaming categories need operational policy · Singular Pass · Feasible
Pass · Verifiable Pass · Correct Pass · Conforming Pass

**Decisions**

- DEC-001 · In the context of reputation being useful but easy to game, we
  chose evidence from real interactions over arbitrary public voting, to achieve
  accountability without popularity bias, accepting lower review volume.
- DEC-002 · In the context of new users having no history, we chose "no history
  is not bad history" over a cold-start penalty, to avoid exclusion by incumbency,
  accepting less predictive ranking information initially.

**Assumptions**

- The platform reputation engine will expose context-aware read signals but will
  not write or rewrite MOD01's underlying evidence.

**Traced to (Step 2 FRs):** FR27, FR28, FR29

**Traced to:** `modules/modules.md` Review/ReputationSignal; Architecture
ADR-005; PM P3.12, P5.7; Complete Product Definition §§48-50, 52;
critqureport §§9-11, 16, 22-23; Pricing Model §§2, 5.6, 16.

**Review history**

- 2026-09-12 - Drafted; policy details remain review items, not silently assumed.

**Approval:** Product Manager - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR10 - Verified-Listing Promotion and Paid Distribution

**Priority:** Must
**Status:** Ready for Review
**Confidence:** High - the guardrails are high-confidence; the V1 product
catalog is decided directly below from the pricing source's own V1 roadmap, and
payment collection is self-contained per BR17.

**Problem**

Providers need a sustainable way to reach relevant customers and eligible
participants, but a conventional "boost" can make members distrust discovery if
money buys visibility over a better organic match or makes an unverified claim
look endorsed.

**Proposed outcome**

An eligible, trusted business/provider can purchase a bounded promotion such as
a boost or business-workspace-linked campaign. The product shows what the
purchase changes (audience/reach, duration, targeting, reporting) and what it
cannot change (hard eligibility, safety, verification truth, organic relevance).
Paid surfaces are clearly labelled in every relevant discovery context; organic
"why this" explanations remain independent of sponsorship. Provider reporting
uses defensible reach/action measures and avoids unsupported causal or precise
reach claims.

The V1-vs-later commercial catalog, taken directly from the pricing source's
own V1 roadmap (§17-18), is:

| Commercial layer | V1 status | Source |
|---|---|---|
| Free community access (discovery, search, respond, basic posting) | V1 - always free | Pricing §5.1, §18 |
| Opportunity Boost / paid distribution | V1 | Pricing §5.2, §17 |
| Business Membership / Workspace | V1 | Pricing §5.3, §17 (see BR11) |
| Community / Opportunity Campaigns | V1 | Pricing §5.4, §17 |
| Qualified Response / Introduction | V1.5 experiment - not enabled at launch | Pricing §5.5, §17 |
| Business Passport | V1.5 | Pricing §5.6, §17 |
| Advertising & Sponsorship (all formats) | V1.5+ | Pricing §6, §17 |
| Intelligence products (Opportunity/Business/Aggregated) | V1.5-V2 | Pricing §7, §17 |
| ForKhatri Plus / Family membership | Future V2, cross-module | Pricing §8, §17 |

**Affected users and systems**

Providers, free members, Search/ranking/distribution, PromotionPlacement,
Verification, a payment gateway (directly integrated for V1, see BR17),
Commercial Admin, Analytics, and Audit.

**Constraints**

- Discovery, search, save, and legitimate response remain accessible to eligible
  free members; a paid product cannot become a paywall for relevant opportunity
  or for ordinary business/professional discovery.
- Verification status must be visibly separate from paid status and reputation.
- Pricing, duration, tax/fee display, renewal, cancellation, refunds/credits,
  and historical versions must be transparent and auditable.
- Advertising and sponsored opportunities remain secondary to utility and comply
  with applicable consumer/advertising disclosure rules (see BR18).
- V1 promotion catalog is limited to Opportunity Boost and Business Membership/
  Workspace-linked campaign products, per the table above; qualified-response
  billing, Business Passport, and advertising/sponsorship are V1.5+ and are not
  enabled at launch.
- Vyapar collects payment directly through its own payment-gateway integration
  in V1 (tokenized/reference state only; no raw card data stored). Routing this
  collection through a shared MOD06 contract instead is a future consolidation
  option, not a launch dependency (see BR17).

**Out of scope (for this BR specifically)**

Pay-to-win ranking, sale of raw member contact lists, paid verification or
reputation, opaque ad targeting based on sensitive attributes, payment capture or
settlement beyond Vyapar's own direct gateway integration, and cross-module Plus
membership entitlements owned by MOD06.

**Worth check**

Promotion is explicitly part of MOD01's approved scope and its stated revenue
model. Without a safe promotion capability, the module lacks its intended
provider-side monetization; without the guardrails, monetization would damage
the liquidity and trust that make the module valuable.

**Quality gate (ISO 29148, adapted for business-level requirements)**

Necessary Pass · Unambiguous Pass - the V1 product catalog is decided above ·
Complete Pass for V1 scope; V1.5+ layers are explicitly deferred, not silently
included · Singular Pass · Feasible Pass - V1 payment collection is
self-contained per BR17 · Verifiable Pass · Correct Pass · Conforming Pass -
proportionate commercial-disclosure practice per BR18

**Decisions**

- DEC-001 · In the context of provider monetization threatening relevance, we
  chose paid relevant distribution over paid organic ranking, to preserve free
  discovery and network liquidity, accepting lower short-term revenue potential.
- DEC-002 · In the context of indicative prices being hypotheses, we chose
  configurable, versioned products and experiments over hard-coded price points,
  to learn from provider ROI and community health, accepting pricing-operational
  complexity.
- DEC-003 · In the context of the pricing source's own explicit V1 roadmap
  (Free core + Boost + Business Workspace + Campaign foundation), we chose to
  launch with exactly that set and defer qualified-response billing, Business
  Passport, advertising, and intelligence products to V1.5+, over enabling the
  full monetization catalog at once, to keep V1 shippable and validate provider
  ROI before adding commercial complexity.

**Assumptions**

- Indicative rupee price points named in the pricing source remain hypotheses to
  be tested through experiments, not fixed launch prices.

**Traced to (Step 2 FRs):** FR30, FR31, FR32, FR35, FR54

**Traced to:** `modules/modules.md` PromotionPlacement, revenue rationale, and
MOD06 boundary; Pricing Model §§1-6, 9, 14-18; PM P2.7-P2.8 and Rule 4;
critqureport §§15-18; Architecture ADR-008.

**Review history**

- 2026-09-12 - Drafted; commercial phase and payment contract unresolved.
- 2026-09-12 - Product Manager correction pass: V1 commercial catalog and
  payment self-containment resolved directly from the pricing source and BR17.

**Approval:** Product Manager - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR11 - Business Subscription and Commercial Workspace

**Priority:** Should
**Status:** Ready for Review
**Confidence:** Medium-High - the pricing source explicitly places Business
Membership/Workspace in the V1 roadmap (see BR10's monetization-phase table);
the exact entitlement-metering scope is a Step 2 design detail.

**Problem**

Businesses with recurring opportunity or customer-discovery needs cannot manage
multiple listings, campaigns, response activity, and performance information as
one accountable business presence. A subscription that merely unlocks more
posts, or a cross-module membership owned by another module, would either fail
to create business value or blur ownership.

**Proposed outcome**

A business can purchase a configurable workspace entitlement (a V1 capability
per BR10's monetization-phase table) for outcome-oriented capabilities such as
multi-user business administration, opportunity/campaign management, eligible
targeting, response tracking, and provider analytics. Entitlements have explicit
scope, duration/usage, owner, lifecycle, receipt/reference, cancellation,
refund/credit, and audit state. The business can understand performance without
being promised unsupported reach, causality, or guaranteed hires/customers.

**Affected users and systems**

Business owners/admins, provider operators, PromotionPlacement, BusinessProfile,
Analytics, the payment gateway (per BR17), Commercial Admin, and Audit.

**Constraints**

- This BR does not create ForKhatri Plus, family membership, or a consumer
  paywall; those are cross-module/MOD06 decisions and are Future/V2 per BR10's
  monetization-phase table.
- A subscription cannot buy verification, reputation, relevance, eligibility,
  or access to private member data.
- Role delegation and business authority must be auditable; a former operator's
  access must be revocable.
- Historical product/price versions and orders remain reconstructible.

**Out of scope (for this BR specifically)**

Enterprise ATS, payroll, CRM replacement, transaction escrow, cross-module
membership, intelligence products using individual-level data, and guaranteed
outcomes.

**Worth check**

Recurring business participation is named in the pricing model and supports the
approved provider-side revenue model. It is a real need for repeat providers,
but core community discovery can exist without it, so Should is more honest than
Must until liquidity and willingness-to-pay evidence exist.

**Quality gate (ISO 29148, adapted for business-level requirements)**

Necessary Pass - the pricing source's own V1 roadmap places this in V1 ·
Unambiguous Pass · Complete Pass for V1 scope · Singular Pass · Feasible Pass -
V1 payment collection is self-contained per BR17 · Verifiable Pass · Correct
Pass · Conforming Pass - proportionate commercial-disclosure practice per BR18

**Decisions**

- DEC-001 · In the context of business revenue being needed without restricting
  community utility, we chose outcome/workspace entitlements over artificial
  posting-limit plans, to align price with business value, accepting more complex
  metering and reporting.

**Assumptions**

- Business subscriptions are optional and may be phased after the first organic
  discovery evidence; this does not authorize a V1 paywall on discovery or
  opportunity access.

**Traced to (Step 2 FRs):** FR31, FR33, FR34, FR35

**Traced to:** Pricing Model §§4-5, 8-9, 15-18; PM P2.7-P2.8 and Product
Decision Record; `modules/modules.md` MOD01 revenue rationale; Architecture
ADR-008.

**Review history**

- 2026-09-12 - Drafted; scope and phase require Product Manager decision.
- 2026-09-12 - Product Manager correction pass: V1 phase and payment
  self-containment confirmed via BR10/BR17.

**Approval:** Product Manager - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR12 - Privacy, Consent, and Purpose-Limited Data Handling

**Priority:** Must
**Status:** Ready for Review
**Confidence:** Medium-High - product privacy invariants are clear; exact
retention schedules and legal-entity classification are operational
refinements to complete as the product scales (see BR18), not a Step 1 sealing
blocker.

**Problem**

Vyapar processes identity-linked capabilities, professional/business claims,
location, availability, contact preferences, opportunity-seeking state,
interaction history, verification evidence, and potentially uploaded documents or
screenshots. If these are public by default, reused for hidden ranking, sold as
leads, or cross-linked across modules without a clear purpose, members may face
professional, financial, safety, or reputational harm and will not trust the
service.

**Proposed outcome**

Each data use has a stated purpose, lawful basis/consent path where required,
visibility rule, recipient, retention/deletion rule, and user-control path.
Members can separately control capability visibility, opportunity-seeking state,
contact/enquiry disclosure, profile discovery, notifications, and commercial
communications. They can inspect/correct important derived preferences, withdraw
optional consent, request applicable rights, and obtain an understandable reason
for relevant recommendation use. Commercial analytics use aggregated/privacy-
safe data and does not expose identifiable members or sensitive individual-level
inferences.

**Affected users and systems**

All members, businesses, professionals, customers, Identity & Trust, Search,
Recommendation/Distribution, Notification, Object Storage, Audit, MOD05,
MOD04, MOD06, external KYC/analytics providers, and legal/compliance operations.

**Constraints**

- Privacy by default; data minimization and purpose limitation are mandatory
  business constraints, not future UX improvements.
- No cross-module inference such as treating activity in another module as
  employment, relationship, financial need, or consent to contact.
- Uploaded evidence and raw documents are restricted, encrypted/retained only
  as legally and operationally necessary, and never made public by default.
- Erasure, correction, consent withdrawal, access, grievance, breach response,
  processor controls, and retention exceptions are designed against the plain
  language of the applicable DPDP Act/Rules and other law, applied reasonably
  and in good faith for an early-stage product; a full pre-launch legal sign-off
  is not required to seal this BR (see BR18).
- Member data is not a revenue product. Qualified interaction is not a license
  to sell raw contact data.

**Out of scope (for this BR specifically)**

Legal advice, a final privacy notice, appointing a statutory Data Protection
Officer/DPO without a legal trigger, and any claim that this BR alone establishes
compliance.

**Worth check**

Privacy is necessary for adoption and lawful operation because the product's
value depends on sensitive opportunity and contact context. Without this BR,
the core discovery and monetization loops create predictable harm and cannot
credibly operate in a close-knit community.

**Quality gate (ISO 29148, adapted for business-level requirements)**

Necessary Pass · Unambiguous Pass - legal role/classification is addressed
proportionately in BR18 · Complete Conditional Pass - retention schedules and
processor inventory are an operational refinement, not a blocker · Singular
Pass · Feasible Pass · Verifiable Conditional Pass - rights and consent flows
are measurable once implemented · Correct Pass · Conforming Pass - proportionate
compliance approach per BR18

**Decisions**

- DEC-001 · In the context of capability and opportunity-seeking information
  carrying different professional risks, we chose independent visibility and
  consent controls over one public/private profile switch, to minimize unwanted
  disclosure, accepting more settings complexity.
- DEC-002 · In the context of source documents proposing intelligence products,
  we chose aggregated/privacy-safe analysis over individual-level monetization,
  to preserve member trust and legal defensibility, accepting lower data-product
  granularity.

**Assumptions**

- The product will be designed to meet the notified DPDP framework and any
  applicable transition dates even if a particular provision is not yet in force
  on the implementation date.

**Traced to (Step 2 FRs):** FR05, FR21, FR24, FR36, FR37, FR38, FR52

**Traced to:** PM P2 Rules 8/10, P3.5, P3.12, P5.7; Complete Product
Definition §§12, 49, 52; critqureport §§11, 21; Pricing Model §§7-8, 16;
Architecture ADR-004, ADR-010, ADR-011; external research R1-R2 below.

**Review history**

- 2026-09-12 - Drafted; privacy/legal classification remains open.
- 2026-09-12 - Product Manager correction pass: legal-classification approach
  softened to the proportionate posture defined in BR18; no hard blocker
  remains.

**Approval:** Product Manager - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR13 - Trust and Safety, Moderation, Fraud, and Dispute Operations

**Priority:** Must
**Status:** Ready for Review
**Confidence:** Medium-High - the risk classes and control outcomes are clear;
exact legal timelines are tracked as configurable operating policy rather than
a pre-launch legal-sign-off blocker (see BR18).

**Problem**

User-originated listings and professional/business claims can carry scams, fake
jobs, MLM/recruitment fraud, phishing, advance-payment requests, harassment,
discrimination, impersonation, privacy violations, spam, stale information, and
retaliatory reviews. Close-knit community trust may also suppress reporting
against respected members. A report button without triage, action, evidence, and
appeal does not protect users.

**Proposed outcome**

Members can report an opportunity, listing, provider, enquiry, partnership, or
review with a reason and optional evidence; they can block/restrict unsafe
contact. Trust & Safety can triage, temporarily limit distribution/contact,
remove or restore content, suspend accounts, request verification, preserve
evidence, communicate an outcome, and accept an appeal. Moderation queues cover
ingestion uncertainty, stale/expired inventory, fraud, serious harm, and review
disputes. Every action has a reason, actor, timestamp, severity, and audit link;
reports are handled without retaliation and with clear escalation to legal or
law enforcement where required.

**Affected users and systems**

All members and providers, Trust & Safety, Verification, Admin Console, Audit,
Notification, Search/Distribution, Object Storage, and external authorities or
service providers where law requires cooperation.

**Constraints**

- Harmful or uncertain content must not be normally distributed while under
  review; emergency restrictions may precede final adjudication.
- Moderation does not silently change a user's preference model.
- Evidence preservation and access must respect privacy, due process, and legal
  requests.
- The workflow supports current applicable IT-intermediary/grievance guidance
  through policy configuration and staffed operations, applying a reasonable,
  good-faith reading appropriate to an early-stage product and updating
  configuration as guidance evolves, rather than gating launch on a formal legal
  opinion (see BR18).
- Automated flags can prioritize review but cannot be treated as final truth for
  a serious adverse action without an accountable review path.

**Out of scope (for this BR specifically)**

General policing, guaranteed fraud prevention, offline dispute adjudication,
criminal investigation, or an AI-only moderation system.

**Worth check**

Trust and safety are necessary to operate a user-generated business/opportunity
network responsibly. Removing this BR would leave known high-severity harms with
no controlled response and would make promotion and discovery unsafe.

**Quality gate (ISO 29148, adapted for business-level requirements)**

Necessary Pass · Unambiguous Conditional Pass - severity taxonomy is a Step 2
detail · Complete Conditional Pass - staffing/escalation coverage needs an
operating decision · Singular Pass · Feasible Pass · Verifiable Pass · Correct
Pass · Conforming Pass - proportionate compliance approach per BR18

**Decisions**

- DEC-001 · In the context of respected community members potentially creating
  reporting pressure, we chose independent, traceable moderation over informal
  community arbitration, to protect complainants and preserve accountability,
  accepting the need for trained operators.
- DEC-002 · In the context of false positives and serious harms coexisting, we
  chose graduated restriction plus human review over automatic permanent bans,
  except where law or immediate safety requires stronger action, accepting
  response-time and appeal complexity.

**Assumptions**

- A staffed Trust & Safety owner and published grievance contact exist before
  user-generated opportunity publishing is enabled, even if that owner is the
  founder in the earliest phase.

**Traced to (Step 2 FRs):** FR24, FR29, FR39, FR40, FR41

**Traced to:** PM P3.12, P5.7, Rules 10-12, P5.6; Complete Product Definition
§§45, 48-52; Vyapar_02 §§11-12; Vyapar_03 §11; critqureport §§9-11, 14, 16;
external research R3-R4 below.

**Review history**

- 2026-09-12 - Drafted; legal applicability and operating coverage remain open.
- 2026-09-12 - Product Manager correction pass: legal-timeline applicability
  softened to a good-faith, configurable operating policy per BR18; no hard
  blocker remains.

**Approval:** Product Manager - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR14 - Accessibility, Localization, and Progressive Participation

**Priority:** Must
**Status:** Ready for Review
**Confidence:** High for the outcome; the exact conformance target and supported
content translation workflow need Product/UX/Legal confirmation.

**Problem**

Members have different languages, literacy, devices, connectivity, abilities,
and confidence in describing what they can offer or want. Long onboarding,
English-only content, inaccessible controls, or a requirement to complete a
resume before seeing value excludes precisely the members who could add density
to the opportunity network.

**Proposed outcome**

Vyapar provides a mobile-first, responsive, accessible experience with English,
Hindi, and Telugu support at launch consistent with the platform architecture.
Members can reach discovery after a short, progressive setup and can use
structured choices plus a free-text/assisted path for capabilities, intents,
constraints, and opportunities. Important listing/opportunity content and
explanations are rendered in the selected language where a translation exists;
language preference is a member attribute where appropriate, not a hidden
ranking signal. The experience supports keyboard/screen-reader use, readable
text, error recovery, accessible authentication, and non-drag/non-visual paths
for core actions.

**Affected users and systems**

All members, Web Client, i18n library/content model, Search, Notification,
Opportunity Composer, support/operations, and accessibility QA.

**Constraints**

- English/Hindi/Telugu launch support is a platform baseline, not a reason to
  defer MOD01 content or error messages.
- User-authored content may remain in the author's language with clear language
  identification; machine translation must not change privacy, eligibility,
  trust, or safety meaning without review.
- Core tasks cannot require voice, drag-and-drop, colour alone, or a particular
  device capability.
- The business target should be a testable WCAG 2.2 AA conformance baseline
  unless Product/Legal approves a different target; conformance is not claimed
  without testing.

**Out of scope (for this BR specifically)**

Native-app-only features, a full voice assistant, perfect translation of every
user-authored message, and a requirement that every source opportunity be
available in every language.

**Worth check**

The platform explicitly requires multilingual, mobile-first access and the
product thesis depends on community density. Excluding members through language,
ability, or onboarding burden would directly reduce supply, demand, and safety;
this is a necessary product outcome, not a cosmetic localization task.

**Quality gate (ISO 29148, adapted for business-level requirements)**

Necessary Pass · Unambiguous Conditional Pass - final content translation and
WCAG target need confirmation · Complete Pass · Singular Pass · Feasible Pass ·
Verifiable Conditional Pass - requires accessibility testing · Correct Pass ·
Conforming Pass

**Decisions**

- DEC-001 · In the context of multilingual and accessibility requirements being
  platform-wide, we chose English/Hindi/Telugu and accessible responsive web
  participation from the first MOD01 release over an English-only desktop-first
  launch, to protect reach and inclusion, accepting translation/content
  operations cost.

**Assumptions**

- Vyapar uses the shared platform i18n and Web Client rather than creating a
  module-specific localization stack.

**Traced to (Step 2 FRs):** FR42, FR43, FR44

**Traced to:** Architecture ADR-010; PM P1.5/P2 Rules 8-9, P3.4, P5.1/P5.3;
Complete Product Definition §§6, 12, 15, 54-56; Vyapar_02 §§3-4, 12; external
research R5.

**Review history**

- 2026-09-12 - Drafted; no approval yet.

**Approval:** Product Manager - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR15 - Product Analytics, Marketplace Health, and Experimentation

**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**

Registrations, profile completion, post volume, and gross revenue can all grow
while relevant opportunity discovery, successful connections, safety, and
liquidity deteriorate. Without event lineage and guardrail metrics, Vyapar
cannot learn whether members found something they would otherwise have missed or
whether paid distribution harms organic utility.

**Proposed outcome**

Vyapar measures a north-star outcome such as Relevant Opportunity Connections:
meaningful member-opportunity interactions that meet an approved relevance
threshold and produce a response or useful outcome where measurable. Because
discovery is a co-equal capability, Vyapar also measures ordinary
business/professional discovery health directly (e.g., discovery-to-enquiry
rate for listings with no opportunity involved), not only opportunity outcomes.
Supporting metrics include Opportunity Coverage, Relevant Discovery Rate,
Opportunity Action Rate, Successful Connection Rate, Completion Rate, Community
Opportunity Reach, time to first relevant opportunity, freshness,
false-positive/correction rate, reports/disputes, notification fatigue,
provider ROI, business activation and retention, promotion repeat, revenue/
refunds/payment costs, contribution margin, and cohort-level pricing experiment
results.

Every metric distinguishes impressions, views, actions, attributed outcomes,
and confirmed outcomes; it must not claim causality that evidence cannot support.

**Affected users and systems**

All member/provider journeys, Search/Ranking/Distribution, Notifications,
Promotion, Reviews/Outcomes, Trust & Safety, Commercial Admin, privacy/audit,
and the platform analytics pipeline.

**Constraints**

- Analytics must respect consent, purpose, access control, retention, and
  aggregation thresholds; it must not expose individual member data to
  commercial customers.
- Pricing tests compare like-for-like value propositions, preserve historical
  price versions, and monitor liquidity, relevance, safety, and retention with
  revenue.
- A profile-completion percentage is not the primary value metric.
- "Would have missed this," user correction, and explicit relevance feedback are
  valid learning signals but not proof of a successful economic outcome.

**Out of scope (for this BR specifically)**

Individual surveillance, cross-module profiling without explicit governance,
opaque automated performance decisions, and a fixed forecast presented as a
guaranteed business plan.

**Worth check**

The product's core thesis is empirical: useful opportunities and useful
businesses/professionals should reach people who would otherwise miss them.
Without outcome and guardrail measurement, the team cannot distinguish a
healthy marketplace from a noisy feed or monetization that damages trust, so
analytics is necessary for responsible operation.

**Quality gate (ISO 29148, adapted for business-level requirements)**

Necessary Pass · Unambiguous Pass · Complete Pass · Singular Pass · Feasible
Pass · Verifiable Pass · Correct Pass · Conforming Pass - proportionate
compliance approach per BR18

**Decisions**

- DEC-001 · In the context of the source corpus emphasizing successful
  connections over registrations, we chose a connection/outcome north star with
  liquidity and safety guardrails over a growth-only KPI, to optimize real
  member value, accepting slower apparent growth.

**Assumptions**

- Outcome confirmation may be self-reported, bilateral, or operator-verified;
  the confidence level of each outcome remains visible in analytics.

**Traced to (Step 2 FRs):** FR32, FR45, FR46

**Traced to:** PM P1.5/P2.5/P3.16; Complete Product Definition §§13-16, 23,
33-36, 49; Pricing Model §§3, 9-13, 15-18; Vyapar_02 §14; Vyapar_03 §12;
critqureport §§23-26.

**Review history**

- 2026-09-12 - Drafted for Product Manager review; no approval yet.
- 2026-09-12 - Product Manager correction pass: added ordinary discovery health
  measurement alongside opportunity-outcome measurement, reflecting the
  corrected co-equal scope.

**Approval:** Product Manager - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR16 - Verification, Ingestion, Moderation, and Commercial Administration

**Priority:** Must
**Status:** Ready for Review
**Confidence:** Medium-High - the required operational surfaces are explicit;
verification, privacy, and monetization policy are decided concretely in BR03,
BR12/BR18, and BR10/BR11 respectively; staffing and SLA specifics remain an
operational rollout decision for the founder/small team, not a Step 1 blocker.

**Problem**

Trustworthy discovery cannot be operated from user-facing screens alone.
Verification queues, uncertain opportunity intake, source/freshness issues,
reports, taxonomy corrections, ranking diagnostics, promotion approvals,
refunds, and appeals otherwise become invisible manual work with no accountable
owner.

**Proposed outcome**

Authorized operators have a unified Admin Console contribution for: verification
review; opportunity ingestion and normalization; uncertainty review; source
registry; stale/expired queue; reports/moderation; taxonomy management; search/
matching/distribution diagnostics; promotion/product/entitlement administration;
refund/credit workflows; dispute/appeal handling; analytics; and audit review.
Operators can see why a record or promotion is in a queue, what action is
allowed, its SLA/severity, who acted, and the resulting user communication.

**Affected users and systems**

Verification, Trust & Safety, Commercial Operations, Product Operations,
Support, Admin Console, Identity & Trust, Audit, Search, Notification, the
payment gateway (per BR17), and Object Storage.

**Constraints**

- Role-based, least-privilege access; no operator receives broad raw evidence or
  contact data by default.
- Administrative decisions are attributable, reason-coded, reversible where
  appropriate, and auditable.
- One unified Admin Console is the platform architecture decision; MOD01
  contributes domain views rather than creating a separate console.
- Operators must not use a hidden manual override to bypass eligibility,
  verification, promotion disclosure, privacy, or safety invariants.
- Queue and SLA policy must be resourced before enabling public opportunity
  creation or paid promotion, even at small-team scale.

**Out of scope (for this BR specifically)**

Platform-wide identity administration, payment-rail operations owned by the
payment gateway/Payments Infrastructure, legal adjudication, and automated
operation without accountable human escalation.

**Worth check**

The source architecture and implementation plan identify these queues as
required founder/operator surfaces. Without them, verification, freshness,
moderation, and monetization promises cannot be delivered consistently, so this
is an operational prerequisite rather than an internal convenience.

**Quality gate (ISO 29148, adapted for business-level requirements)**

Necessary Pass · Unambiguous Pass · Complete Conditional Pass - staffing and
SLA policy remain a rollout decision · Singular Pass · Feasible Pass ·
Verifiable Pass · Correct Pass · Conforming Conditional Pass - depends on
Admin Console contract.

**Decisions**

- DEC-001 · In the context of cross-cutting governance and module-owned queues,
  we chose one Admin Console with MOD01 domain views over a separate Vyapar
  console, to preserve consistent authorization and audit, accepting plugin/view
  contract coordination.

**Assumptions**

- The first operational owner may be a small team or the founder, but coverage
  and escalation are explicitly staffed before public launch; "founder-operated"
  is not an excuse for an undefined safety SLA.

**Traced to (Step 2 FRs):** FR40, FR46, FR47, FR48, FR49

**Traced to:** Architecture ADR-011/ADR-012; PM P4.1/P5.6-P5.8; Complete
Product Definition §§21-24, 45, 51; Vyapar_02 §§11-12; Vyapar_03 §11;
`modules/modules.md` shared concerns.

**Review history**

- 2026-09-12 - Drafted; operational staffing and console contract remain open.
- 2026-09-12 - Product Manager correction pass: removed stale blocker
  references now resolved in BR03/BR12/BR18/BR10/BR11.

**Approval:** Product Manager - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR17 - Platform and Adjacent-Module Contracts

**Priority:** Must
**Status:** Ready for Review
**Confidence:** High - ownership is approved in Step 0 and architecture; V1
payment collection is self-contained within Vyapar, removing the prior MOD06
contract dependency from the launch path.

**Problem**

Vyapar cannot operate as an isolated module if identity, verification,
credentials, search, notifications, audit, storage, payments, Dashboard
surfacing, and Counsel referral are left as informal assumptions. Informal
coupling would create duplicate member identity, cross-module privacy leaks,
shared-model ownership conflicts, payment-scope violations, and untestable
handoffs.

**Proposed outcome**

MOD01 operates through explicit, versioned business contracts, deliberately
kept as loosely coupled as practical:

- Identity & Trust supplies the canonical member identity, authentication, and
  platform Level-1/2 trust; MOD01 owns Level-3 business/professional records.
- Identity & Trust exposes the shared VerifiedCredential fact without merging
  ProfessionalListingProfile with Counsel ExpertProfile.
- Search indexes approved MOD01 records through the shared search contract;
  MOD01 owns its search meaning and organic ranking.
- Notification receives approved event requests; MOD01 does not own SMS/email/
  push delivery.
- Audit receives consequential events with actor, object, decision, and reason.
- Object Storage holds approved media/evidence under MOD01 access policy.
- MOD05 reads an approved privacy-filtered summary and never writes MOD01 data.
- MOD04 receives an explicit referral only; no appointment/payment state crosses
  implicitly.
- **V1 payment collection is self-contained within Vyapar**: Vyapar integrates
  directly with a licensed/compliant payment gateway to collect boost/campaign/
  workspace payments, using tokenized references only, and never stores raw
  card/payment credentials. Routing this collection through a shared MOD06
  Payment Services contract instead is a future consolidation option if
  ForKhatri later centralizes payments across modules; it is not a MOD01 launch
  dependency, and any future migration must preserve the same minimum-field,
  tokenized-reference contract shape.
- **Loose coupling is an explicit architectural preference for MOD01**: every
  adjacent-module and platform integration should use the smallest practical
  contract (a single well-defined API call or event with minimum fields) rather
  than shared databases, synchronous multi-hop chains, or bidirectional
  dependencies, so Vyapar and its counterparts can be built, deployed, and
  evolve independently. Step 2 and Step 7 should treat this as a standing
  non-functional constraint, not merely a Step 1 suggestion.

**Affected users and systems**

Every actor and every platform/adjacent system named above, especially Identity
& Trust, Search, Notification, Audit, Admin Console, MOD04, MOD05, and the
payment gateway.

**Constraints**

- One data owner per business entity; no cross-module shared database or silent
  direct table access.
- Contracts must define authorization, purpose, minimum fields, error/failure
  behavior, idempotency where actions may be retried, versioning, and audit.
- No cross-module inference or raw sensitive data sharing by default.
- Dashboard aggregation cannot alter Vyapar ranking or write Vyapar state.
- Direct payment collection is Vyapar's own responsibility for V1 and does not
  wait on a cross-module contract; the gateway itself must be a licensed/
  RBI-compliant Payment Aggregator or authorized bank/gateway, with MOD01 acting
  only as its merchant client, never as a payment aggregator itself.

**Out of scope (for this BR specifically)**

Defining technical protocols, database schemas, deployment topology, or the
internal implementation of any adjacent module/service.

**Worth check**

These contracts are necessary to preserve the approved module boundaries and
prevent high-impact identity, privacy, payment, and ownership failures. Without
them, the business capability cannot be safely delivered even if its screens
exist.

**Quality gate (ISO 29148, adapted for business-level requirements)**

Necessary Pass · Unambiguous Pass - V1 payment collection is direct; no missing
contract blocks the launch path · Complete Conditional Pass - failure/
idempotency details belong in Step 2/architecture · Singular Pass · Feasible
Pass · Verifiable Pass · Correct Pass · Conforming Pass

**Decisions**

- DEC-001 · In the context of the architecture's one-owner and isolated-data
  rules, we chose explicit minimum-field contracts over shared models or direct
  database reads, to preserve privacy and replaceability, accepting integration
  coordination.
- DEC-002 · In the context of the architecture recording only a Vyapar
  benefit-trigger event while Step 0 anticipated paid promotion/subscription
  collection through MOD06, we chose direct, self-contained payment collection
  within Vyapar for V1 over waiting for a cross-module payment contract, to
  avoid gating launch on another module's roadmap, accepting that a later
  migration to a shared MOD06 contract remains possible and should preserve the
  same tokenized-reference shape.
- DEC-003 · In the context of the Product Manager's explicit preference for very
  loosely coupled modules, we chose minimum-field, single-purpose API/event
  contracts for every adjacent integration over shared models or synchronous
  dependency chains, to preserve independent evolution and failure isolation,
  accepting that some cross-module conveniences (e.g., richer aggregated views)
  take more integration work to achieve.

**Assumptions**

- Architecture ADR-004 through ADR-013 remains the governing platform baseline
  unless the Solution Architect records a superseding decision, including
  recording MOD01's direct payment-gateway integration as a sanctioned pattern.

**Traced to (Step 2 FRs):** FR06, FR50, FR51, FR52

**Traced to:** `modules/modules.md` MOD01 Depends on/Depended on/Data owned and
shared concerns; Architecture dependency table, ADR-004 through ADR-013;
PM P4.3-P4.4 and P5.8; Pricing Model §12.2 (payment processing as a cost
driver, supporting a direct-gateway model).

**Review history**

- 2026-09-12 - Drafted; payment contract mismatch remains open.
- 2026-09-12 - Product Manager correction pass: resolved the payment-contract
  mismatch with self-contained V1 payment collection; added the loose-coupling
  architectural principle per explicit Product Manager direction.

**Approval:** Product Manager - [x] Approved - Krishna Kategaru, 2026-09-12

---

## BR18 - Proportionate Legal and Compliance Awareness for an Early-Stage Launch

**Priority:** Must
**Status:** Ready for Review
**Confidence:** Medium - proportionate compliance awareness is achievable now
using existing public regulatory guidance; a full external counsel engagement
is recorded as a future scaling milestone, not a Step 1 precondition.

**Problem**

Vyapar combines user-generated content, business/professional claims,
recommendation/distribution, paid promotion, member contact, verification
evidence, and payment initiation. An early-stage, founder-built product cannot
obtain a full formal legal-counsel sign-off before every launch increment, but
it also cannot treat privacy, safety, and honest commercial communication as
someone else's problem. The right proportionate response is a documented,
reasonable compliance posture the team can actually execute now — not a
blocking legal gate the founder has no current path to satisfy.

**Proposed outcome**

Before each capability that touches member data, claims, or payment goes live,
ForKhatri applies and documents a reasonable, good-faith compliance posture
appropriate to an early-stage product:

- **Privacy**: DPDP-aligned practice — purpose limitation, a clear privacy
  notice, consent for optional processing, a working way for a member to
  access/correct/delete their personal data, and reasonable security measures
  (see BR12).
- **Transparency**: clear, findable terms of use; a grievance/contact channel
  for user-generated content and reports; a documented (even if lightweight)
  takedown/appeal process (see BR13).
- **Commercial honesty**: non-misleading, clearly labeled commercial/sponsored
  claims — no fabricated reach numbers, no deceptive urgency, no hidden
  auto-renewal (see BR10/BR11).

This posture is owned by the Product Manager/founder, is reviewed and
tightened as the product scales, as revenue grows, or as a materially
higher-risk capability is added (for example, a larger-scale government-scheme
data feature, or an expanded payment product), and does not require a formal
external counsel opinion to begin operating responsibly at V1 scale.

**Affected users and systems**

ForKhatri legal/compliance (as it exists — the founder in the earliest phase),
Product Manager, Identity & Trust, MOD01, the payment gateway, Trust & Safety,
Admin Console, Audit, verification vendors, business providers, members, and
authorities.

**Constraints**

- This artifact records a reasonable, good-faith compliance posture appropriate
  to an early-stage, founder-built product; it is not legal advice and does not
  certify regulatory compliance. Engaging qualified counsel remains valuable and
  should happen as the product scales, revenue grows, or a specific high-risk
  capability is added — it is not a precondition for sealing this BR or for an
  early, small-scale launch.
- DPDP-aligned design follows the plain language of the 2023 Act and the
  notified 2025 Rules as public guidance, applied reasonably; the team tracks
  phased-commencement dates as they are published rather than waiting for a
  full legal interpretation before building basic privacy controls (consent,
  access, correction, deletion).
- User-generated content requires a working grievance/contact channel and a
  documented takedown/appeal process; timelines follow current public
  intermediary guidance as a good-faith operating target, revisited as guidance
  changes.
- Paid surfaces, sponsored opportunities, and commercial claims must be clear,
  non-misleading, and understandable in the language of the communication —
  this is a product-quality and trust requirement independent of any specific
  regulatory citation.
- Payment/settlement and any regulated financial activity remain outside MOD01
  ownership regardless of whether collection is direct (BR17) or via a future
  MOD06 contract; MOD01 uses a licensed/compliant payment gateway rather than
  acting as a payment aggregator itself.

**Out of scope (for this BR specifically)**

Providing legal opinions, guaranteeing regulatory compliance, replacing a future
formal counsel engagement once the business scales, or implementing Step 8
security controls in this Step 1 artifact.

**Worth check**

Reasonable privacy, transparency, and honest commercial communication are
necessary business behaviors for any product handling contact and claims
data — removing them would create real, foreseeable harm to members. But
gating this BR's approval on a formal legal sign-off the founder has no current
path to obtain would block the entire module without making anyone safer in
practice; a proportionate, documented posture the team can actually execute is
the necessary and sufficient bar for Step 1.

**Quality gate (ISO 29148, adapted for business-level requirements)**

Necessary Pass · Unambiguous Pass · Complete Pass for a proportionate
early-stage posture · Singular Pass · Feasible Pass · Verifiable Pass - the
documented posture and its review cadence are checkable · Correct Pass ·
Conforming Pass

**Decisions**

- DEC-001 · In the context of an early-stage, founder-built product needing
  real privacy/transparency practice but having no path to a formal pre-launch
  legal sign-off, we chose a documented, reasonable, good-faith compliance
  posture that the team can execute now over a hard legal-sign-off gate, to keep
  the module shippable while still protecting members, accepting that the
  posture will be tightened as legal capacity and scale increase.
- DEC-002 · In the context of DPDP Rules 2025 having phased commencement, we
  chose to design basic privacy controls (consent, access, correction, deletion)
  now using the plain language of published guidance, tracking each effective
  date as it is published, over waiting for a full legal interpretation before
  building anything, to avoid delaying the whole module over a compliance
  question that has a workable interim answer.

**Assumptions**

- ForKhatri will identify the operating legal entity and revisit this posture
  with qualified counsel once the product has real users, revenue, or a
  materially higher-risk capability; that engagement is a scaling milestone, not
  a Step 1 precondition.

**Traced to (Step 2 FRs):** FR37, FR41, FR53, FR54

**Traced to:** `modules/modules.md` out-of-scope payment boundary/shared
concerns; Architecture ADR-008/ADR-011/ADR-012; Pricing Model §§14-18;
external research R1-R7 below.

**Review history**

- 2026-09-12 - Drafted; legal/compliance blocker remains open.
- 2026-09-12 - Product Manager correction pass: rewritten from a hard
  pre-launch legal-sign-off gate to a proportionate, achievable
  compliance-awareness posture; BLOCKER-005 removed accordingly.

**Approval:** Product Manager - [x] Approved - Krishna Kategaru, 2026-09-12

---

## Non-functional business constraints

These are business-level constraints carried into later steps; they are not
implementation prescriptions beyond the sealed architecture baseline.

| Area | Constraint / outcome |
|---|---|
| Availability | MOD01 runs in the Core Platform V1 baseline of 99.5% monthly availability, subject to planned maintenance. |
| Scale | The platform baseline is design for 50,000 registered members and approximately 5,000 concurrent sessions without architectural redesign; re-baseline with measured V2 traffic. |
| Recovery | Core Platform/Search/Notification baseline: RPO <= 1 hour, RTO <= 4 hours. Identity & Trust, Payments, and other elevated services keep their own stricter baselines; MOD01 must tolerate dependency failure without corrupting domain state. |
| Security/privacy | Least privilege, server-side authorization, encryption appropriate to evidence/contact sensitivity, append-only audit events, secure upload handling, abuse/rate controls, and no raw payment credentials in MOD01. Exact controls belong to Step 8. |
| Performance | Search/discovery, profile, enquiry, and moderation paths must be usable on mobile/low-bandwidth conditions; exact thresholds belong to Step 2/Step 8 using the V1 wedge decided in BR04. |
| Accessibility/localization | English/Hindi/Telugu, responsive/mobile-first, accessibility target and test evidence per BR14. |
| Explainability | Material recommendation, promotion, verification, moderation, and privacy decisions must expose a user/operator reason and preserve the input evidence. |
| Freshness | Active inventory needs a revalidation/expiry policy; stale/expired information must not remain indistinguishable from current information. |
| Auditability | Actor, timestamp, object, policy/decision, source, and outcome are retained for consequential actions subject to applicable retention/deletion rules. |
| Resilience | Retries must not duplicate enquiries, promotion orders, entitlements, or moderation actions; adjacent contract idempotency is required. |
| Coupling | Every adjacent-module and platform integration favors the smallest practical, loosely-coupled contract shape (BR17), so a dependency's failure or change does not cascade into MOD01's domain state. |

## Completeness and quality checklist

| Check | Result / evidence |
|---|---|
| Problem and outcomes | Pass - BR01-BR06 define the core discovery/supply loop, correctly presenting business/professional discovery and opportunity distribution as co-equal; BR07-BR11 define connection and commercial outcomes. |
| Actors/personas | Pass - actor table covers seekers, providers, customers, partners, operators, platform, and adjacent modules, with the Counsel boundary correctly narrowed to structured advisory-seeking only. |
| Approved scope and boundaries | Pass - approved Step 0 scope is explicit and is now correctly read as covering business/professional discovery and opportunity distribution as co-equal capabilities; source-corpus proposals are reconciled via BR04's source-segment rule rather than either being silently absorbed or wrongly excluded. |
| Business rules/invariants | Pass - fourteen cross-cutting invariants are stated, with rule 1 corrected to the co-equal discovery/opportunity framing. |
| Lifecycle/statuses | Pass - listing, verification, opportunity, enquiry, partnership, review, and promotion states are stated. |
| Discovery/search/ranking | Pass - BR05-BR06 treat in-module discovery as a first-class capability, separate in-module search from cross-module Dashboard exposure, and enforce eligibility-before-ranking. |
| Verification/trust/reputation | Pass - BR03 decides a concrete, lightweight V1 verification policy; BR09 separates reports, reviews, and reputation. |
| Enquiries/networking/partnerships | Pass - BR07 and BR08 cover bounded interaction flows without a generic chat/social graph. |
| Member-originated opportunities | Pass - BR04's Community/Public-External source-segment rule resolves the external-source interpretation directly. |
| Promotion/monetization | Pass - BR10-BR11 decide the V1 commercial catalog directly from the pricing source; no pay-to-win or raw lead sale. |
| Privacy/consent/data handling | Pass - BR12 defines product privacy invariants; a proportionate compliance posture is recorded in BR18 rather than gated on formal legal sign-off. |
| Moderation/safety/fraud | Pass - BR13 defines moderation/safety operations; legal-timeline applicability follows BR18's proportionate posture. |
| Accessibility/localization | Conditional Pass - BR14; exact target/testing plan follows UX/QA. |
| Analytics/KPIs | Pass - BR15 names north-star, guardrails, commercial, safety, and discovery-health measures. |
| Admin/operations | Conditional Pass - BR16; staffing/SLA specifics and the Admin Console plugin contract are Step 2/architecture-level refinements, not open Step 1 blockers. |
| Platform/adjacent contracts | Pass - BR17; V1 payment collection is self-contained, and a loose-coupling principle governs every adjacent contract. |
| Legal/compliance prerequisites | Pass - BR18 records a proportionate, achievable compliance posture and current external evidence without claiming legal advice or gating launch on formal sign-off. |
| Singular, necessary, unambiguous, complete, feasible, verifiable, correct, conforming | Pass overall - the 18 BRs are singular and business-level; all six prior blockers are resolved with concrete Step 1 decisions above, and what remains before Sealing is Product Manager per-BR approval, not open blockers. |

## Source traceability and evidence register

### Repository sources read

| Source | Use in this artifact |
|---|---|
| `modules/modules.md` - MOD01 and shared concerns | Approved scope, out-of-scope boundary, primary users, dependencies, owned entities, and cross-module ownership. |
| `docs/PreStartResearch/PROCESS-README.md` | Process status and handoff controls. The recorded prior MOD01 seal conflicts with the current missing artifact; this file does not treat that log as evidence that this artifact is present or approved. |
| `/ARCHITECTURE.md` (project root) | Container/ownership/dependency baseline: Identity & Trust, Search, Notification, Audit, Object Storage, Admin Console, MOD06/Payments Infrastructure, shared credential, and NFR baselines. |
| `docs/PreStartResearch/vyapar/critqureport.md` | Risks and hypotheses: cold start, trust/fraud, privacy, WhatsApp/input behavior, pay-to-win, qualified introductions, Business Passport, north-star metrics, and the explicit V1-wedge recommendation (§24) used to resolve BLOCKER-003. |
| `docs/PreStartResearch/vyapar/ForKhatri_Vyapar_Final_Pricing_and_Revenue_Model_v1.docx` | Free-core philosophy, Boost/business workspace/campaign layers, future qualified responses/intelligence/membership, the explicit V1 Monetization Roadmap (§17) and Final Decisions (§18) used to resolve BLOCKER-006, pricing experiments, and disclosure/refund/analytics guardrails. |
| `docs/PreStartResearch/vyapar/ForKhatri_Vyapar_Product_Management_Planning_P1-P5.md` | Problem/actors, product principles, canonical Opportunity/Person concepts, lifecycle, matching/distribution rules, journeys, terminology, decision rules, and handoff boundary. |
| `docs/PreStartResearch/vyapar/Vyapar — Complete Product Definition.md` | Full product definition: profile, privacy, opportunity model, provenance, lifecycle, engine, discovery, composer, trust, moderation, screens, and V1 non-goals. |
| `docs/PreStartResearch/vyapar/Vyapar_01_Final_Research_and_Product_Decisions.docx` | Consolidated product decisions, evidence-backed implications, and opportunity-network thesis. |
| `docs/PreStartResearch/vyapar/Vyapar_02_Final_Screen_Architecture.docx` | Screen/journey inventory, empty/error states, trust and safety surfaces, and analytics events. |
| `docs/PreStartResearch/vyapar/Vyapar_03_Profile_Engine_and_Implementation_Plan.docx` | Canonical domain concepts, deterministic engine, controlled preference learning, roadmap, and operational screens. |

### External research (accessed 2026-09-12)

| ID | Source / URL | Requirement implication |
|---|---|---|
| R1 | [Digital Personal Data Protection Act, 2023 - MeitY/Gazette](https://www.meity.gov.in/static/uploads/2024/02/Digital-Personal-Data-Protection-Act-2023.pdf) | Purpose/lawful processing, notice, consent, rights, security, erasure, and fiduciary accountability inform BR12/BR18's proportionate posture. |
| R2 | [Digital Personal Data Protection Rules, 2025 - notified Gazette](https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf) and [MeitY Rules page](https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa?pageTitle=Digital-Personal-Data-Protection-Rules-2025) | Notified Rules require clear standalone notices, itemized data/purpose, comparable consent withdrawal, security safeguards, rights mechanisms, and phased commencement; BR18 tracks launch dates as public guidance rather than waiting for a full legal opinion. |
| R3 | [MeitY IT Intermediary Rules page](https://www.meity.gov.in/data-governance/information-technology-intermediary-guidelines-and-digital-media-ethics-code-rules-2021) and [current MeitY FAQ on 2026 amendments](https://www.meity.gov.in/static/uploads/2025/10/065b6deb585441b5ccdf8be42502a49c.pdf) | User-generated content and reports inform BR13's grievance/takedown/appeal operation, applied as good-faith operating policy per BR18 rather than a hard legal gate. |
| R4 | [CERT-In Directions under Section 70B](https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf) and [CERT-In Directions landing page](https://cert-in.org.in/Directions70B.jsp) | Incident reporting, point-of-contact, and secure ICT-log retention obligations inform BR13, BR16, BR17, and BR18 as good-faith operating guidance. |
| R5 | [W3C Web Content Accessibility Guidelines 2.2](https://www.w3.org/TR/WCAG22/) | WCAG 2.2 is a testable web accessibility standard covering mobile/web content; it supports BR14's proposed AA baseline. |
| R6 | [Department of Consumer Affairs - misleading advertisements and endorsements](https://consumeraffairs.nic.in/latestnews/guidelines-prevention-misleading-advertisements-and-endorsements-misleading) and [Consumer Protection resource page](https://consumeraffairs.nic.in/acts-and-rules/consumer-protection/consumer-protection) | Paid/sponsored placements and provider claims need non-misleading, clearly disclosed commercial treatment, per BR10/BR11/BR18. |
| R7 | [RBI reference to Payment Aggregator/Payment Gateway directions](https://www.rbi.org.in/scripts/NotificationUser.aspx?Id=11996) and [RBI discussion/reference material](https://www.rbi.org.in/Scripts/PublicationReportDetails.aspx?ID=943&UrlPage=) | Money movement, merchant onboarding, settlement, security, dispute handling, and raw card-data boundaries inform BR17's direct-gateway integration: Vyapar is a merchant client of a licensed/compliant gateway, not a payment aggregator itself. |
| R8 | [How to Register Your Business on Just Dial (GetSwipe)](https://getswipe.in/blog/article/register-your-business-on-just-dial); [WorkIndia KYC Process](https://www.workindia.in/kyc-process/) and [WorkIndia Employer Login guide](https://resumeera.xyz/JobPost/blog/workindia-employer-login-complete-guide-access-portal-2026); [Apna — Which documents are required, and why](https://apna.co/employer-help-center/2/which-documents-are-required-and-why) and [Apna — How can I get my account verified](https://employer-help-centre.apna.co/support/solutions/articles/1060000139180-how-can-i-get-my-account-verified-) | Directly checked (not assumed) what comparable real apps require: Justdial lists a business on name/contact/address/category alone with no GSTIN requirement; WorkIndia verifies employers via OTP plus company-profile review and requires GST/MSME evidence only in specific edge cases; Apna accepts a GST Certificate as only one of several company-verification options (Company PAN, CIN, FSSAI, Shops & Establishment License), with personal PAN/Aadhaar as its actual fastest path. This directly grounds BR03's phone/OTP-baseline-plus-flexible-document V1 policy (no mandatory GSTIN); it also illustrates one real precedent for a low-friction local-business discovery experience, though BR05's standalone-discovery scope itself is grounded in `modules/modules.md`'s Step 0 boundary, not in this research finding. |

## Open items for downstream awareness (non-blocking)

These are residual, Step-2-or-later-level details, not Step 1 blockers:

1. Exact operator tooling/workflow for the V1 flexible business-existence
   document spot-check (GST/Udyam/PAN/Aadhaar/Shops & Establishment License)
   (BR03, Admin Console detail).
2. Confirm or override the non-blocking working V1 launch-geography assumption
   (Hyderabad/Secunderabad) before go-to-market (BR04).
3. Trust & Safety staffing plan and severity/response-time targets appropriate
   to actual launch scale, once real usage exists (BR13/BR16).
4. Timing and design of a possible future MOD06 payment-consolidation
   migration, if/when ForKhatri centralizes payments across modules (BR17).
5. Final accessibility conformance testing plan and untranslated
   user-authored-content handling (BR14, Step 3/UX/QA detail).
6. Module name collision (found 2026-09-13 during Step 4 research): "Vyapar"
   is also the name of a widely used, unrelated Indian GST billing and
   accounting app (vyaparapp.in, Simply Vyapar Apps Pvt Ltd; Play Store
   `in.android.vyapar`). Inside ForKhatri the module can keep its working
   name, but the Product Manager should decide the public-facing label
   (e.g. "ForKhatri Vyapar" always with the umbrella brand) and have a
   trademark check done before launch marketing. Not a pipeline blocker.
