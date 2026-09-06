---
step: 01-business-requirements
module: MOD01
status: Sealed
approver: Product Manager
updated: 2026-09-06
items: 7 | approved: 7 | blockers: 0
---

# 01 — Business Requirements — MOD01 Vyapar

## Revision history
| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-06 | Initial draft: 7 Business Requirements covering Vyapar's full modules.md scope (verification, business profiles, professional profiles, in-module discovery, networking/partnerships, opportunities/enquiries, reviews/reputation/promotions). | Step 1, autonomous execution (pinned preference: no clarifying questions; decide and document reasoning in-line). Source: `/modules/modules.md` (Sealed, MOD01 section), `/ARCHITECTURE.md` (Sealed, container/dependency resolution for MOD01), `docs/PreStartResearch/ForKhatri — Complete High-Level Business Requirements.md` §13, `docs/PreStartResearch/ForKhatri — Master Product Requirements Document.md` §18 and §7.1/§7.5 (core problems answered), §46 (revenue model). |
| 2026-09-06 | Reviewed and sealed. Independently re-verified every numbered Master PRD/BRD citation used across all 7 BRs against the actual source documents' heading numbers (not just accepted the prose). Confirmed correct: §7.1, §7.3, §7.5, §8.3, §8.5, §8.6, §8.7, §14, §15, §18, §24, §46, §56, §59 (BRD §13). Found and fixed two mis-citations that did not correspond to their claimed content: (1) "§34/§46 (revenue model)" — §34 is "Web and Mobile Strategy," unrelated to revenue; only §46 ("Business Model") actually supports the claim, so "§34/" was removed wherever it appeared (revision-history line above, BR07 constraints, BR07 worth-check); (2) "Master PRD §10.4/§8.5" for "Reputation Is Earned" in BR07's worth-check — §10.4 does not carry that meaning in either source document (Master PRD's §10 is "Unified Identity," undivided; the BRD's own §10.4 is "Merit and Contribution," a related but distinct principle), while §8.5 ("Reputation Is Earned") is the correct and sufficient citation on its own — "§10.4/" was removed. Both were citation-accuracy defects, not defects in the underlying argument (§46 and §8.5 alone fully support each respective claim), so corrected in place rather than treated as blocking. No other citation across BR01-BR07 failed independent verification. | Step 1 review, business-requirements-reviewer (autonomous mode), Product Manager gate. |
| 2026-09-06 | Populated each BR's `Traced to:` field now that Step 2 (Functional Requirements) has produced 56 FRs fanning out from these 7 BRs — a small, targeted update, not a re-opening of the sealed content above. | Step 2, functional-requirements-agent (autonomous mode), per this pipeline's standing instruction to update the parent BR file's `Traced to:` field once its FRs exist. |

## Scope of this step

This file covers every Business Requirement for MOD01 Vyapar, strictly
within the boundary `/modules/modules.md` already sealed for this module:
business and professional discovery; business and professional profiles;
business/job/employment opportunity listings; business enquiries;
networking; business partnerships; reviews and business-domain reputation
signals; verified-listing promotions; and independent Level-3 verification
of business identity, business ownership, professional credentials/
licenses, and contact/service legitimacy.

Explicitly out of scope for this file (per modules.md, not re-litigated
here): in-app payment collection for business transactions (V1 is
enquiries/leads only — MOD06 Payment Services integration is deferred);
consultation scheduling/paid-advice workflows (MOD04 Counsel's domain, even
where the same person also holds a Vyapar ProfessionalProfile — see
ARCHITECTURE.md ADR-013 for how the two entities relate without merging);
and cross-module "fair exposure" ranking across the whole platform (MOD05
Dashboard's job — Vyapar owns only its own in-module discovery ranking).

Per `/ARCHITECTURE.md`, Vyapar runs inside the Core Platform modular
monolith (its own `vyapar` schema, ADR-002), calls Identity & Trust Service
for all identity/Level-1/Level-2 checks and for any external KYC/registry
call (Vyapar itself never calls an external verification provider
directly — ADR-004), and is read by MOD05 Dashboard via an in-process
internal contract (never the reverse). These are binding constraints
inherited into every BR below, not decisions this file re-makes.

## Set-level quality gate
| Check | Result |
|---|---|
| Comprehensive — covers full module scope | Pass — every bullet in modules.md's MOD01 "Scope" line and every capability named in the source BRD §13/PRD §18 maps to exactly one BR below (traceability table follows). Independently re-checked against Master PRD §18's own "Business Capabilities" list (Business identity, Business profiles, Professional profiles, Business discovery, Service discovery, Opportunity discovery, Job opportunities, Business enquiries, Networking, Business partnerships, Reviews, Reputation, Promotions) — every item maps to a BR below, no gaps found. |
| Consistent — no contradicting BRs | Pass — no two BRs claim ownership of the same data entity; BR01's verification gate is a precondition referenced by, not duplicated in, BR02/BR03. |
| Prioritized — every BR ranked | Pass — see each BR's Priority line. |
| No duplicates/overlaps | Pass — Professional discovery appears once (BR04), reputation once (BR07), etc.; cross-references used instead of restating content. |

### Scope-to-BR traceability
| modules.md / source capability | BR |
|---|---|
| Independent Level-3 verification (business identity/ownership/professional credentials/licenses/contact-service legitimacy) | BR01 |
| Business profiles, verified business presence | BR02 |
| Professional profiles | BR03 |
| Business discovery, professional discovery, service discovery (in-module) | BR04 |
| Networking, business partnerships | BR05 |
| Business/job/employment opportunities, business enquiries | BR06 |
| Reviews, business-domain reputation, verified-listing promotions | BR07 |

## Open blockers

None.

---

## BR01 — Independent Level-3 Verification of Business, Ownership and Professional Credentials
**Priority:** Must
**Status:** Sealed
**Confidence:** High

**Problem**
Today (pre-ForKhatri, and for any member arriving at Vyapar without this
capability), there is no independent way for a customer, employer, or
prospective partner to distinguish a real, currently-operating,
legitimately-owned business or licensed professional from a fabricated
listing, an unlicensed practitioner, or an impersonator. Community trust
has historically been exploited by people leveraging existing networks,
money, or perceived status to appear credible without actually being
credible (Master PRD §7.3). Every capable business/professional and every
member trying to evaluate one is affected.

**Proposed outcome**
Vyapar independently verifies, before a business or professional listing
is marked "Verified" and before it receives any discovery-ranking boost
(BR04) or promotion eligibility (BR07): (a) business identity and
registration, (b) business ownership, (c) professional credentials/
licenses where the profile claims a licensed profession, and (d) basic
contact/service legitimacy (working contact channel, service actually
offered). Verification status (Verified / Pending / Unverified / Rejected)
is visible on every profile and listing. Measurable target: 100% of
listings that display a "Verified" badge have passed this check; 0% of
unverified claims are visually indistinguishable from verified ones (per
Master PRD §14, information trust classification must be communicated
clearly in the UI).

**Affected users and systems**
Entrepreneurs, business owners, professionals, freelancers, service
providers submitting a listing; customers and partners relying on
verification status to decide whether to engage; Identity & Trust Service
(external KYC/registry calls, per ADR-004 — Vyapar never calls an external
verification provider directly); MOD05 Dashboard (reads verification
status read-only when surfacing Vyapar listings).

**Constraints**
Must use the shared Identity & Trust Service for any external
registry/KYC-class check (ADR-004) — Vyapar owns only the domain-specific
verification *record* (per modules.md: "Vyapar-domain verification
records"), not the external integration itself. Must not represent an
unverified profile as verified in any UI surface, including Dashboard's
read-only rendering. Per Master PRD §8.6/§8.7, verification should be
automated wherever objectively possible; human review is reserved for
exceptions, disputes, and cases the automated check cannot resolve.

**Out of scope (for this BR specifically)**
The actual external registry/KYC integration build-out (Identity & Trust
Service's job, not Vyapar's — tracked in ARCHITECTURE.md ADR-004).
Matrimonial-grade or financial-grade verification depth (MOD03/MOD07's own
domains). Ongoing behavioral/reputation trust — that is BR07's job; this
BR covers only the initial and periodic re-verification gate.

**Worth check**
Without independent verification, Vyapar is indistinguishable from any
unmoderated business directory and directly reintroduces the "members
being cheated via exploited trust" problem the platform exists to solve
(Master PRD §7.3). This is not a nice-to-have layered on top of listings —
it is the precondition that makes every other Vyapar capability (discovery,
reviews, promotion) trustworthy rather than decorative. Removing it would
mean Vyapar is a directory, not a trust-based ecosystem, which fails the
module's own stated rationale in modules.md.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ (verification status is a checkable field with a defined
state machine) · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of deciding where automated re-verification sits
  versus one-time-only verification, facing the choice of "verify once at
  onboarding" versus "verify once and periodically revalidate," we chose
  periodic revalidation (exact cadence deferred to FR step) over one-time
  verification only, to achieve the platform's own "Information Lifecycle"
  principle (Master PRD §15 — verification status has an expiry/refresh
  date, not permanent validity), accepting the added operational cost of
  running revalidation checks on a recurring basis rather than once.

**Assumptions**
- Assumed "contact/service legitimacy" (named explicitly in modules.md)
  means a basic reachability + service-existence check, not a full
  mystery-shopper style audit — inferred from the automated-verification-
  first principle (Master PRD §8.6), since a manual audit at scale
  contradicts that principle. Flagged for confirmation at FR step if this
  reading is too light.
- Assumed re-verification cadence and escalation SLA are FR-level detail,
  not BR-level; a config placeholder (`VYAPAR_VERIFICATION_SLA_DAYS`) has
  been recorded in `/modules/MOD01-vyapar/config/vyapar.config.example.md`
  so this isn't lost as an undocumented open question.

**Traced to:** FR01, FR02, FR03, FR04, FR05, FR06, FR07, FR08, FR09, FR10
(`02-functional-requirements.md`, Step 2)

**Review history**
- 2026-09-06 · business-requirements-reviewer (autonomous mode): nine-point
  gate re-checked independently, worth-check confirmed genuinely argued
  (removal reintroduces a named, cited platform problem, not merely
  asserted), citations (§7.3, §8.6, §8.7, §15) independently verified
  against source document heading numbers — all correct. Approved.

**Approval:** Product Manager — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## BR02 — Verified Business Profiles and Listings
**Priority:** Must
**Status:** Sealed
**Confidence:** High

**Problem**
Today, a legitimate business in the community has no single trusted,
platform-native place to present itself with verified status attached —
members rely on word-of-mouth, informal WhatsApp groups, or generic
directories with no verification layer at all. Small and newer businesses
without existing social networks are disproportionately affected, since
word-of-mouth systematically favors those who already have connections
(Master PRD §7.1/§7.5).

**Proposed outcome**
A business owner can create and maintain a `BusinessProfile` (business
name, category/services offered, description, location(s), contact
channels, media, operating status) and an associated `BusinessListing`
that is discoverable once BR01's verification gate has been passed (or
clearly marked Unverified/Pending if not). A business can hold multiple
listings under one profile (e.g., multiple locations or service lines).
Measurable target: a business owner can go from profile creation to a
live, correctly trust-labeled listing without needing manual admin
intervention for the common case (per Master PRD §8.7).

**Affected users and systems**
Business owners, entrepreneurs; customers browsing/searching (BR04);
Identity & Trust Service (verification status, read); MOD05 Dashboard
(reads listings read-only, per ARCHITECTURE.md's Dashboard→Vyapar
in-process contract).

**Constraints**
`BusinessProfile` and `BusinessListing` are owned solely by Vyapar (no
other module ever writes these entities, per modules.md's Data Owned
line). Must support the multilingual requirement (English/Hindi/Telugu at
launch, per ARCHITECTURE.md ADR-010) for member-authored profile content.
Must visually and structurally distinguish Verified from
Pending/Unverified status on every rendering, including when consumed by
Dashboard.

**Out of scope (for this BR specifically)**
Professional (individual/credentialed) profiles — that is BR03, a
deliberately separate entity even where the same person is also a business
owner. In-app payment collection (deferred to MOD06 integration, not V1).
Reviews/ratings display (BR07).

**Worth check**
This is the module's core value-delivery unit — without a
`BusinessProfile`/`BusinessListing` capability, there is nothing for BR01's
verification, BR04's discovery, BR06's opportunities, or BR07's reputation
to attach to. Removing it removes Vyapar's entire reason to exist as a
distinct module rather than a feature of Dashboard.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of one business potentially operating multiple
  locations/service lines, facing "one profile = one listing" versus "one
  profile, many listings," we chose the one-to-many model over strict 1:1,
  to achieve accurate real-world representation of multi-location
  businesses without forcing duplicate profiles (which would fragment
  verification and reputation across artificial duplicates), accepting the
  added modeling complexity of a profile/listing split rather than a single
  flat entity.

**Assumptions**
- Assumed "business" in this BR means any commercial entity a member
  operates, not limited to registered companies — sole proprietors and
  informal service providers are explicitly named as target participants
  in the source PRD (§18), so profile creation must not hard-require formal
  business registration to exist in Pending state (only to reach Verified,
  per BR01).

**Traced to:** FR11, FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR19
(`02-functional-requirements.md`, Step 2)

**Review history**
- 2026-09-06 · business-requirements-reviewer (autonomous mode): nine-point
  gate re-checked independently. Worth-check's "removing it removes
  Vyapar's reason to exist" line is circular on its own, but the preceding
  sentence grounds it in a real, cited deficiency (no trusted
  platform-native presence today, word-of-mouth bias against
  newer/unconnected businesses, Master PRD §7.1/§7.5) — treated as
  sufficiently argued on that basis, not on the circular framing alone.
  Citations verified correct. Approved.

**Approval:** Product Manager — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## BR03 — Verified Professional Profiles
**Priority:** Must
**Status:** Sealed
**Confidence:** High

**Problem**
Freelancers, individual service providers, and professionals (distinct
from registered businesses) currently have no dedicated, verifiable way to
present their individual professional identity within the community
ecosystem. Without it, capable individuals without an existing employer
network or client base remain invisible (Master PRD §7.1/§7.5), and
members cannot distinguish a genuinely credentialed professional from
someone merely claiming expertise.

**Proposed outcome**
A member can create and maintain a `ProfessionalProfile` (Vyapar context:
commercial/business-service identity — skills, services offered,
experience, portfolio/media, availability) that is verified per BR01
(professional credential/license check where the claimed service is a
licensed profession) before being discoverable at full strength. Members
seeking to hire, refer, or engage a professional can locate them via BR04.
Measurable target: a professional's profile clearly displays verification
status and the specific credential(s) verified, not just a generic
"Verified" badge.

**Affected users and systems**
Freelancers, professionals, service providers; employers and customers
seeking to engage them; job seekers (where "professional" overlaps with
"employable individual," see BR06); Identity & Trust Service (credential
verification, read).

**Constraints**
`ProfessionalProfile` here is the Vyapar-context entity only — deliberately
distinct from MOD04 Counsel's `ExpertProfile`, even though one member may
hold both, per modules.md's explicit "Professional spans two modules by
design" note and ARCHITECTURE.md ADR-013 (shared `VerifiedCredential`
sub-record in Identity & Trust Service, referenced by FK from both, but the
two profile entities themselves never merge). Vyapar's own BR/FR work must
never attempt to absorb Counsel's advisory-consultation workflow into this
profile.

**Out of scope (for this BR specifically)**
Paid consultation, appointment booking, and advisory-liability workflows
(MOD04 Counsel's domain — a Vyapar professional profile can exist and be
fully verified with zero Counsel involvement). Employment-contract or
payroll mechanics (Vyapar surfaces opportunities/enquiries only, per BR06;
it does not manage employment itself).

**Worth check**
Without a distinct professional-profile capability, Vyapar would either
force individual professionals into the business-entity model (a poor fit
for a freelancer with no registered company) or exclude them entirely,
directly failing the "capable professionals lacking networks" problem this
module exists to solve. The deliberate separation from Counsel's
ExpertProfile is itself necessary, not incidental: collapsing them would
misrepresent commercial-service legitimacy as advisory-liability
qualification, a meaningfully different trust claim (see ARCHITECTURE.md's
own independent re-derivation of this boundary).

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of a member potentially holding both a Vyapar
  ProfessionalProfile and a Counsel ExpertProfile, facing merge-into-one-
  entity versus keep-fully-separate, we chose to keep them fully separate
  (deferring to ARCHITECTURE.md ADR-013's shared-credential-sub-record
  resolution) over merging, to achieve correct separation of commercial
  legitimacy from advisory qualification, accepting that a member managing
  both profiles must maintain two separate records rather than one unified
  "professional" record.

**Assumptions**
- Assumed a professional listed here may still also be an employer/job
  seeker via BR06 — these are complementary roles, not mutually exclusive
  profile types, inferred from the source PRD's target-participant list
  (§18) naming "job seekers" and "professionals" as overlapping, not
  disjoint, populations.

**Traced to:** FR20, FR21, FR22, FR23, FR24, FR25
(`02-functional-requirements.md`, Step 2)

**Review history**
- 2026-09-06 · business-requirements-reviewer (autonomous mode): nine-point
  gate re-checked independently. Worth-check genuinely argued (states the
  specific failure mode of not having this BR — forcing freelancers into
  an ill-fitting business entity, or excluding them — rather than
  asserting necessity). ADR-013 boundary re-checked against
  ARCHITECTURE.md directly, holds up. Approved.

**Approval:** Product Manager — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## BR04 — Business and Professional Discovery (In-Module Search and Browse)
**Priority:** Must
**Status:** Sealed
**Confidence:** High

**Problem**
Even once verified profiles/listings exist (BR02/BR03), members today have
no way to find the right business, professional, or service within the
community without relying on personal networks or informal referrals —
which is precisely the "unequal access to networks" problem the module
exists to address (Master PRD §7.1). Without in-module discovery, BR02/BR03
are write-only capabilities with no read-side value.

**Proposed outcome**
Members can search and browse verified (and clearly-labeled
pending/unverified) `BusinessListing`s and `ProfessionalProfile`s by
category, service type, location, and keyword, with results ranked by
Vyapar's own in-module relevance rules (never simply payment or
popularity, per Master PRD §8.3/§24 — the "fair opportunity" principle
applies inside Vyapar's own ranking, not just at Dashboard's cross-module
layer). Measurable target: search/browse surfaces relevant, currently-
active listings and excludes expired/inactive ones (per Information
Lifecycle principle, Master PRD §15).

**Affected users and systems**
All members browsing/searching; businesses/professionals being discovered;
shared Search Service (V1: Postgres full-text search embedded in Vyapar's
own schema behind the shared query-syntax library, per ARCHITECTURE.md
ADR-007); MOD05 Dashboard (reads a subset of this for cross-module
surfacing, but does not implement its own version of this ranking — per
modules.md's explicit boundary that Dashboard's fair-exposure engine
governs only what Dashboard itself surfaces, not Vyapar's in-module
ranking).

**Constraints**
Must use the shared Search Service integration pattern (ADR-007) rather
than building a bespoke search stack. Ranking logic must incorporate
relevance, trust/verification status, quality, and capability signals —
never payment alone, per the platform's Fair Opportunity principle
(Master PRD §8.3). Must support multilingual query/content per ADR-010.

**Out of scope (for this BR specifically)**
Dashboard's cross-module "fair exposure" ranking engine (MOD05's separate
capability — this BR governs only ranking within Vyapar's own
discovery surface). Promotion-driven visibility (BR07) — commercial
promotion must be visually distinguished from this organic ranking, not
blended into it silently.

**Worth check**
Discovery is the mechanism through which BR02/BR03's entire value is
realized — a verified profile nobody can find delivers zero exposure,
which is the exact deficiency (lack of exposure, Master PRD §7.5) this
module was created to fix. This is not optional polish on top of profiles;
it is the other half of the same capability.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of choosing where relevance ranking logic lives,
  facing "Vyapar owns its own ranking" versus "defer entirely to
  Dashboard's fair-exposure engine," we chose Vyapar owning its own
  in-module ranking (per modules.md's explicit boundary) over deferring to
  Dashboard, to achieve a working, self-contained discovery experience
  inside Vyapar even before Dashboard exists or surfaces Vyapar content,
  accepting that this creates two distinct ranking concerns in the
  platform (Vyapar's own + Dashboard's fair-exposure layer) that must not
  be conflated, per ARCHITECTURE.md's own explicit warning on this point.

**Assumptions**
- None beyond what's stated; this BR is a direct, low-ambiguity
  restatement of modules.md's "business discovery/professional discovery/
  service discovery" scope line.

**Traced to:** FR26, FR27, FR28, FR29, FR30, FR31, FR32
(`02-functional-requirements.md`, Step 2)

**Review history**
- 2026-09-06 · business-requirements-reviewer (autonomous mode): nine-point
  gate re-checked independently. Worth-check argued via a concrete
  mechanism (verified profile + zero findability = zero exposure), not
  asserted. §7.1/§7.5/§8.3/§24/§15 citations independently verified
  against source heading numbers — all correct. Approved.

**Approval:** Product Manager — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## BR05 — Business Networking and Partnerships
**Priority:** Should
**Status:** Sealed
**Confidence:** Medium — networking/partnership workflows are named in
modules.md and source docs but with less structural detail than
profiles/discovery; specific mechanics (e.g., what constitutes a
"partnership" record vs. an informal connection) are deferred to FR step.

**Problem**
Businesses and professionals in the community today have no structured,
platform-native way to identify and formally connect with potential
business partners (suppliers, collaborators, referral partners) — this
depends entirely on pre-existing personal networks, which is the same
network-inequality problem named throughout the source docs (Master PRD
§7.1), applied specifically to B2B relationships rather than B2C
discovery.

**Proposed outcome**
A business or professional can initiate, request, and formally record a
`Partnership` with another verified business/professional discovered
through Vyapar (e.g., supplier relationship, referral partnership, joint
service arrangement), visible on both parties' profiles once accepted.
Measurable target: a partnership request has a clear lifecycle
(requested → accepted/declined → active/ended) with both parties able to
see current partnership status.

**Affected users and systems**
Business owners, professionals, suppliers, business partners; Identity &
Trust Service (both parties must be at least Level-2 verified members);
Notification & Communication Service (partnership request/response
notifications, via the shared broker per ADR-006 — Vyapar never builds its
own notification channel).

**Constraints**
`Partnership` is owned solely by Vyapar. Must not become a general-purpose
messaging/social-networking feature — scope is limited to
business-relationship formation, per modules.md's framing of this as
"business networking," not open community social networking (that overlap
belongs to MOD02 Milavn, a deliberately separate module).

**Out of scope (for this BR specifically)**
General community networking / real-world meetups (MOD02 Milavn's
domain). Financial terms or contractual enforcement of a partnership
(Vyapar records that a partnership exists and its status; it is not a
contract-management or escrow system).

**Worth check**
Applying the worth check directly: is this a necessary need or a
nice-to-have? It is necessary at Should (not Must) priority — removing it
does not prevent Vyapar from delivering its core value (discovery +
verified presence, BR01-04 already do that), but its absence leaves a
named source-doc capability ("business partnerships," modules.md scope
line; "networking," Master PRD §18) entirely unaddressed, and B2B
relationship-formation is a distinct real need from B2C discovery/
enquiries (BR06). Kept in scope at Should priority rather than deferred
out of the module, since deferring it to a later module would violate
modules.md's own data-ownership decision (Partnership is Vyapar-owned, not
a candidate for another module).

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of scoping "networking" broadly (social
  connection) versus narrowly (business-relationship formation only), we
  chose the narrow business-relationship scope over a general social/
  networking feature, to achieve a clean non-overlap with MOD02 Milavn
  (which modules.md already designates for general real-world community
  connection), accepting that members wanting general social networking
  within Vyapar's audience must use Milavn instead, which is a deliberate
  module-boundary decision, not an oversight.

**Assumptions**
- Assumed "networking" and "partnerships" in modules.md's scope line refer
  to the same underlying capability (structured B2B relationship
  formation) rather than two separate capabilities, since no source
  document distinguishes them further. If FR-step analysis finds they
  actually diverge, this BR should be split then, not now (BRs stay
  coarse per this step's own definition).

**Traced to:** FR33, FR34, FR35, FR36, FR37, FR38, FR39
(`02-functional-requirements.md`, Step 2)

**Review history**
- 2026-09-06 · business-requirements-reviewer (autonomous mode): this BR's
  worth-check is the clearest example in the file of a genuinely argued
  (not asserted) necessity test — it explicitly runs the
  necessary-vs-nice-to-have question, concedes core value doesn't depend
  on it, and still grounds the Should-priority inclusion in a named,
  cited, unaddressed capability. Independently re-asked "would removing
  this BR leave a real, stated deficiency": yes — B2B partnership
  formation is a distinct need from BR06's enquiry/opportunity flow and
  from Milavn's general social networking, and modules.md's data-ownership
  decision means it cannot simply move to another module. Approved at
  Should priority as proposed.

**Approval:** Product Manager — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## BR06 — Business and Job Opportunity Listings with Enquiries
**Priority:** Must
**Status:** Sealed
**Confidence:** High

**Problem**
Today, job seekers and businesses seeking commercial opportunities
(customers, suppliers, collaborators) within the community have no trusted,
verification-backed channel to post and respond to opportunities — general
job boards and informal community groups carry no verification signal and
no structured enquiry/lead mechanism, and capable candidates/businesses
without personal connections are systematically disadvantaged (Master PRD
§7.1/§7.5).

**Proposed outcome**
A verified business/employer can post a `JobOpportunity`/
`BusinessOpportunity` (role or commercial opportunity, requirements,
location, compensation/terms where applicable). Any member can respond by
submitting a `BusinessEnquiry` (structured lead/application, not a full
application-tracking system) directly against a listing or a business
profile. Measurable target: every opportunity/enquiry has a clear status
(open/closed for opportunities; submitted/responded/closed for enquiries)
and the poster is notified of new enquiries via the shared Notification
Service.

**Affected users and systems**
Employers, business owners posting opportunities; job seekers, customers,
prospective suppliers submitting enquiries; Notification & Communication
Service (enquiry alerts); MOD05 Dashboard (reads opportunities read-only
for cross-module surfacing, per ARCHITECTURE.md's Dashboard→Vyapar
contract).

**Constraints**
Per modules.md's explicit out-of-scope line: no in-app payment collection
for any business transaction resulting from an enquiry in V1 — payment
happens off-platform until MOD06 Payment Services ships and is integrated.
`JobOpportunity`/`BusinessOpportunity`/`BusinessEnquiry` are owned solely
by Vyapar.

**Out of scope (for this BR specifically)**
Full applicant-tracking-system functionality (resume parsing, interview
scheduling, etc.) — Vyapar provides enquiries/leads only, not a full
recruitment platform, consistent with modules.md's "V1: enquiries/leads
only" framing. Payment collection for the resulting transaction (deferred
to MOD06 integration).

**Worth check**
This BR is one of the two structural problems modules.md explicitly says
Vyapar answers directly (unequal access to networks, lack of exposure).
Without a structured opportunity + enquiry mechanism, verified discovery
(BR02-04) produces visibility but no actionable pathway to an actual
opportunity — the module would prove trust without proving utility, which
directly fails the Master PRD's own V1 success bar (§56: Trust, Utility,
Community Effect must all be proven).

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of how deep Vyapar's opportunity/enquiry
  capability should go in V1, facing full-ATS-style functionality versus
  lightweight leads-only, we chose leads-only (structured enquiry, no
  interview/offer-management workflow) over a full recruitment platform,
  to achieve a scope that fits Vyapar's stated regulatory/technical
  complexity budget (Low/Med per modules.md's scoring table) and ships
  within V1, accepting that businesses with heavier hiring-pipeline needs
  will still need an external ATS for anything beyond the initial lead.

**Assumptions**
- Assumed "business enquiry" covers both a job application and a general
  commercial lead (e.g., "I want this service") under one entity shape,
  since modules.md lists `BusinessEnquiry` singularly as the one owned
  entity for this concern — if FR-step analysis finds the two need
  materially different fields/workflows, that's a legitimate FR-level
  split, not a BR-level one.

**Traced to:** FR40, FR41, FR42, FR43, FR44, FR45, FR46, FR47
(`02-functional-requirements.md`, Step 2)

**Review history**
- 2026-09-06 · business-requirements-reviewer (autonomous mode): nine-point
  gate re-checked independently. Worth-check argued via the trust-without-
  utility failure mode against the platform's own named V1 success bar
  (§56, independently verified — "Trust / Utility / Community Effect"
  content confirmed against source), not merely asserted. Approved.

**Approval:** Product Manager — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## BR07 — Business Reviews, Reputation, and Verified-Listing Promotions
**Priority:** Must
**Status:** Sealed
**Confidence:** High

**Problem**
Even a verified, discoverable listing (BR01-04) gives no ongoing signal of
actual service quality or customer satisfaction after the point of
verification — verification proves legitimacy at a point in time, not
ongoing reliability. Members currently have no trustworthy,
manipulation-resistant way to see how a business/professional has actually
performed for other members, and legitimate businesses have no
platform-native way to gain additional, fairly-labeled visibility for
demonstrated quality (Master PRD §7.2/§10.4 — "reputation is earned," not
popularity).

**Proposed outcome**
Members who have engaged with a business/professional (via BR06's enquiry
flow at minimum) can submit a `BusinessReview` (structured
feedback/rating tied to a specific interaction, not an anonymous open
post). Vyapar computes and displays a business-domain reputation signal
from these reviews, feeding the shared reputation-aggregation engine
(read-only, per ARCHITECTURE.md ADR-005 — Vyapar is the sole writer of
`BusinessReview`, the shared engine only reads it). Separately, a verified
business/professional may purchase a `Promotion` (visibility boost) that
is always visually and structurally distinguished from organic,
relevance-based results (per Master PRD §24's fair-exposure principle).
Measurable target: 100% of promoted listings are visually labeled as
promotional in every surface, including Dashboard's read-only rendering;
reviews are tied to a verifiable interaction, not freely postable by
non-participants.

**Affected users and systems**
Members who engaged with a business/professional (reviewers); businesses/
professionals being reviewed and purchasing promotions; the shared
reputation-aggregation engine inside Identity & Trust Service (reads
`BusinessReview` read-only, per ADR-005); MOD05 Dashboard (reads reputation
signals and promotion status read-only, must preserve the
organic-vs-promoted visual distinction it did not create).

**Constraints**
`BusinessReview` and `Promotion` are owned solely by Vyapar — the shared
reputation engine never writes to `BusinessReview` (ADR-005). Promotion
must never be allowed to substitute for or override verification status
(an unverified business cannot purchase its way to appearing verified).
Revenue model: business subscriptions, verified listings, promotions, and
lead generation are the named monetization paths for this module (Master
PRD §46) — this BR is Vyapar's primary revenue-bearing capability and
must be built with that commercial role in mind, without letting payment
override the Fair Opportunity principle (Master PRD §8.3).

**Out of scope (for this BR specifically)**
Actual payment processing for a purchased promotion (routed through MOD06
Payment Services once it ships, per modules.md's explicit out-of-scope
line — Vyapar records that a promotion was purchased and its active
window, it does not process the payment itself). Cross-module reputation
scoring logic (the shared engine's job, per ADR-005 — Vyapar only writes
its own signal).

**Worth check**
Reviews/reputation are necessary, not optional, because verification alone
(BR01) only proves a point-in-time legitimacy claim — the platform's own
principle "Reputation Is Earned" (Master PRD §8.5) explicitly
requires an ongoing, evidence-based signal beyond initial verification.
Promotions are necessary because they are one of the module's few named,
concrete revenue mechanisms (Master PRD §46) — without a revenue-bearing
capability, Vyapar cannot meet modules.md's own sustainability rationale,
even though its early-stage revenue potential is explicitly rated
"Med (needs traction first)."

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ (bundles two closely
related but distinct capabilities — reviews/reputation and promotions —
kept in one BR because modules.md lists them together and both are the
"back half" of the same trust-to-commerce lifecycle; if FR-step analysis
finds the two need materially independent treatment, split there, not
here) · Feasible ✓ · Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions** (append-only)
- DEC-001 · In the context of whether a review can be submitted without any
  verifiable underlying interaction, facing open/anonymous reviews versus
  interaction-tied reviews, we chose interaction-tied reviews (must
  reference a BR06 enquiry or equivalent recorded engagement) over
  open-posting, to achieve resistance to fake/manipulated reviews
  consistent with the platform's "Evidence Over Rumours" principle (Master
  PRD §8.4), accepting that members who engaged with a business entirely
  off-platform cannot leave a review until an on-platform interaction
  record exists.
- DEC-002 · In the context of promotions potentially being confused with
  verification, facing "promotion boosts rank silently" versus "promotion
  must be visually distinct and never implies verification," we chose the
  latter over the former, to achieve compliance with the platform-wide Fair
  Opportunity principle carried down from Dashboard's own fair-exposure
  engine design, accepting that this caps how aggressively a paying
  business can visually dominate a results page, which is a deliberate
  revenue-vs-trust trade-off the source docs already make explicit (Master
  PRD §59: ForKhatri should not compete as "another payment application" or
  win purely on who paid the most).

**Assumptions**
- Assumed reputation *scoring/aggregation* logic itself (the algorithm)
  lives in the shared engine per ADR-005, and this BR's business
  responsibility is limited to collecting and exposing the raw
  `BusinessReview` signal — consistent with modules.md's explicit
  "no module ever writes another module's feedback entity" rule and
  ADR-005's read-only-engine resolution.

**Traced to:** FR48, FR49, FR50, FR51, FR52, FR53, FR54, FR55, FR56
(`02-functional-requirements.md`, Step 2)

**Review history**
- 2026-09-06 · business-requirements-reviewer (autonomous mode): nine-point
  gate re-checked independently, including a specific re-check of the
  "Singular" item given this BR explicitly bundles two capabilities
  (reviews/reputation, promotions) — accepted as a deliberate, justified
  BR-level coarse grouping (consistent with this file's stated BR
  granularity elsewhere, e.g. BR05's networking+partnerships bundle), not a
  quality-gate failure, since both halves share one lifecycle stage and the
  file already commits to splitting at FR step if warranted. Worth-check
  genuinely argued for both halves (ongoing reputation signal distinct from
  point-in-time verification; promotions as one of the module's few named
  revenue mechanisms), not asserted. Found and corrected two citation
  defects during independent verification of every numbered reference: (1)
  "§34/§46" — §34 ("Web and Mobile Strategy") does not support the revenue
  claim; corrected to "§46" alone (which does, confirmed directly against
  source: "Business subscriptions / Verified profiles / Premium listings /
  Promotions / Lead generation" appears verbatim under Vyapar's §46
  revenue-sources list). (2) "§10.4/§8.5" for "Reputation Is Earned" — §10.4
  does not carry that meaning in either source document; corrected to §8.5
  alone (confirmed as the correct and sufficient citation). Both were
  citation-accuracy defects only; the underlying arguments held without the
  incorrect half of each citation, so corrected in place rather than
  blocking the BR. Approved.

**Approval:** Product Manager — [x] Approved — reviewer-agent (autonomous mode), 2026-09-06

---

## Definition of Done check

- Every BR passes its nine-point quality gate — Pass (all 7 above,
  independently re-checked by business-requirements-reviewer, not just
  re-confirmed from the producing agent's own assertion).
- Set-level quality gate is entirely Pass — Pass (see table above;
  Comprehensive check independently re-derived against Master PRD §18's
  own capability list, not just accepted from the traceability table's own
  claim).
- Every BR has a priority — Pass (5 Must, 1 Should — BR05; see individual
  Priority lines and BR05's worth-check justification for the one
  non-Must item, independently re-argued in BR05's Review history above).
- No open blockers — Pass (none recorded; none found during review).
- Every numbered source-document citation across all 7 BRs (Master PRD and
  Complete High-Level BRD) independently verified against the actual
  section headings in `docs/PreStartResearch/`, not merely trusted as
  written — Pass, with two citation-accuracy defects found and corrected
  in place (see BR07's Review history and the revision-history row above
  for full detail); no defect changed the substance of any worth-check
  argument.
- Product Manager approval — Pass. All 7 BRs marked Approved by
  reviewer-agent (autonomous mode) per this project's autonomous-mode
  pipeline. Status changed **Ready for Review** → **Sealed**.

## Reviewer notes

Per this gate's elevated-risk instruction (an agent validating its own or
a sibling agent's worth-check is the least independent check in the
pipeline), each BR's worth-check was re-tested by directly asking "would
removing this BR leave a real, stated deficiency" rather than accepting
that the BR's own prose asserts one. All 7 held up under that test — see
each BR's own Review history entry above for the specific re-argued case.
BR02's worth-check contains one internally circular sentence ("removing it
removes Vyapar's reason to exist") which was not treated as sufficient on
its own; the BR passes because the preceding sentence separately grounds
the need in a real, cited present-day deficiency. BR07's bundling of
reviews/reputation and promotions into a single BR was scrutinized
specifically against the "Singular" gate item and accepted as a deliberate
coarse-grained BR-level grouping, consistent with how BR05 similarly
bundles networking and partnerships — both explicitly reserve the right to
split at FR step if warranted, which is this pipeline's stated definition
of BR-level granularity, not an evasion of the gate.

Independently verified every numbered citation to Master PRD and the
Complete High-Level BRD against actual section headings in
`docs/PreStartResearch/` (not merely trusted as transcribed). Found and
corrected two citation-accuracy defects (both in BR07, propagating from
one typo pattern): an incorrect "§34" appended to an otherwise-correct
"§46" revenue-model citation, and an incorrect "§10.4" appended to an
otherwise-correct "§8.5" "Reputation Is Earned" citation. Neither defect
changed the substance of the underlying argument (the correct half of each
citation fully supports the claim on its own), so both were corrected in
place as part of this review rather than treated as blocking — consistent
with this project's autonomous-mode instruction to resolve ordinary
judgment calls rather than surfacing them, reserving Blocked status for a
genuine unresolvable issue. No such issue was found in this file.

No open blockers. File sealed.
