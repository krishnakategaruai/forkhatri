---
module: MOD03
step: v1-design-decisions
status: Sealed
approver: Product Manager / Chief Architect (joint)
updated: 2026-09-14
---

# V1 Design Decisions — MOD03 Mangaly

## Revision history

| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-12 | Initial version — resolved every internal-only open item from `01-business-requirements.md`/`02-functional-requirements.md`. | Product Manager / Chief Architect — krishna kategaru (autonomous), 2026-09-12. |
| 2026-09-12 | Correction pass: re-read every Mangaly `.docx` source in full to confirm no SLA/severity numbers were already decided there (confirmed — the sources explicitly flag these as needing "abuse taxonomy, severity matrix, operational staffing and legal review," never a number). Replaced every previously-invented SLA figure (verifier/evidence review, safety-severity response times, admin staffing model) with values grounded in either a named real competitor's published practice (BharatMatrimony's 1-hour photo-verification turnaround, DEC-V1-004) or an actual legally-binding ceiling for an India-based platform (the IT Rules 2021, as amended February 2026: 24h grievance acknowledgment, 2h removal for nudity/impersonation content, 36h resolution ceiling; India's POCSO Act mandatory CSAM reporting obligation, analogous to the US NCMEC/REPORT Act's 24-hour requirement) — per the standing instruction that SLA and legality decisions must follow real, verified existing rules and named applications, not invented round numbers. See DEC-V1-004, DEC-V1-006, DEC-V1-007 for the corrected text. | Legal/competitor grounding correction — krishna kategaru (autonomous), 2026-09-12. |
| 2026-09-12 | Impact Analysis follow-up: addressed every actionable finding `06-impact-analysis.md` (Step 6) raised against this file's own decisions before Step 7/implementation begins. Added the personality-assessment instrument (IA033) to "What stays open," which had been a genuine omission. Added DEC-V1-009, resolving IA065/IA068/IA074's finding that DEC-V1-006's severity taxonomy had no actual mechanism to reach its Tier 3/4 exits — named a concrete on-call paging category and, via live research, the actual legally-specified CSAM reporting channel (POCSO Rules 2020 Rule 11: SJPU/local police/cybercrime.gov.in, including the Rule 11(2) source-material handover obligation). Added a "Known technical debt" section recording IA092's interim-account-system migration risk explicitly rather than leaving it as a floating Impact Analysis note. | Impact Analysis follow-up — krishna kategaru (autonomous), 2026-09-12. |
| 2026-09-13 | **Step 8 (Security & Performance) follow-up.** Step 8's own review found two items this file had left as "genuinely external, not resolved here" (message/evidence retention window; the CSAM packet schema/paging vendor's remaining implementation-stage detail) were actually resolvable now, per this file's own established convention (DEC-V1-005's marriageable-age research, DEC-V1-006's safety-severity SLA table) of deriving V1 values from real law and named-competitor precedent rather than waiting on an external actor this pipeline has no seat for ("legal counsel," an unselected procurement vendor). Added **DEC-V1-010** (message/profile data retention and erasure windows, grounded in the DPDP Act 2023 + DPDP Rules 2025's actual retention/erasure provisions — Rule 8's purpose-fulfilled erasure test, the Seventh Schedule's 1-year log-retention floor, the Third Schedule's 3-year large-platform inactivity ceiling with its mandatory 48-hour pre-erasure notice — cross-checked against BharatMatrimony's and Shaadi.com's own published privacy-policy retention practice) and **DEC-V1-011** (CSAM report packet field schema, modeled on NCMEC's real CyberTipline ESP reporting-schema field categories per POCSO Rule 11(2)'s own source-material handover requirement, plus naming PagerDuty concretely as the on-call paging vendor, per this project's config-placeholder convention). Removed the message/evidence-retention row from "What stays open" (resolved) — legal-hold *duration* itself remains inherently case-specific (a legal hold lasts as long as the actual legal matter requires, in any jurisdiction; that is a structural property of what a legal hold is, not an unresolved external dependency), recorded explicitly rather than left ambiguous. The verification-vendor selection and personality-assessment-instrument rows remain genuinely open — both require an actual third-party contracting decision this pipeline has no mechanism to make, unlike retention windows and packet schema, which required only research this pass performed. | Step 8 Security & Performance follow-up — krishna kategaru (autonomous), 2026-09-13. |
| 2026-09-14 | **DEC-V1-015 added: the interim identity system is retired into the ForKhatri platform identity.** The product owner decided ForKhatri is one app with one sign-in and one member identity; the platform Identity & Trust Service (`platform/identity-service`) now exists, so the IA092 technical debt recorded under "Known technical debt" is paid down rather than carried. `mangaly_identity.account` becomes Mangaly's member-link table (migration 014), the interim credential routes answer `410 moved_to_forkhatri` behind `INTERIM_IDENTITY_ENABLED=false`, and the web client hands sign-in/sign-out to the ForKhatri entrance. BR/FR files untouched (documentation corrections are a separate pass). | Product owner decision (one ForKhatri sign-in); binding contract `docs/ParentApp/07-tech-reqs.md` TR10–TR17, TR23 — krishna kategaru (autonomous), 2026-09-14. |

## Purpose

`01-business-requirements.md` through `05-test-scenarios.md` deliberately left a
number of items as "implementation-stage" or "open" rather than inventing a
number nobody had actually decided. This file closes as many of those as
can honestly be closed now — everything **except** two categories that
genuinely cannot be resolved by this team writing a decision down:

1. **AI-infrastructure-gated items** — anything whose resolution depends on
   the AI Service existing, which `/ARCHITECTURE.md` ADR-009 correctly
   defers until a module actually commits to an AI surface (not yet).
2. **External-party-gated items** — anything requiring a party outside this
   team's control, where the gap is genuinely a *contracting* decision (a
   verification vendor's own onboarding process; a psychometric instrument's
   license) rather than a *research* gap this team can close itself. As of
   the 2026-09-13 follow-up, this category is narrower than it first
   appears: several items originally filed here (message/evidence retention;
   the CSAM packet schema and paging vendor) turned out to be resolvable
   from real law and named-competitor precedent, per this file's own
   established method — see DEC-V1-010/DEC-V1-011 below. "Requires legal/
   vendor input" is only a valid reason to leave something open if a real,
   findable answer genuinely doesn't exist yet, not a default deferral.

Every other open item gets a real decision below, in the same Y-statement
form used throughout this pipeline. None of these decisions change any
BR/FR's business intent — they fill in the specific value the BR/FR always
said was "implementation-stage," which is exactly the stage this now is.

## What stays open (and why — confirmed genuinely external, not resolved here)

| Item | BR/FR | Why it stays open | What actually unblocks it |
|---|---|---|---|
| Verification vendor/process selection | BR08, FR035/FR037 (vendor selection specifically, not the anti-abuse mechanics — see DEC-V1-004 below, which *is* resolved) | Selecting and contracting an actual KYC/verification vendor is a procurement decision outside engineering's control. | Business development selects a vendor; the *mechanism* Mangaly builds against it (evidence display, provenance, freshness) is already fully specified and does not change based on which vendor is picked. |
| Future Mangaly Agent layer | BR17, FR077/FR078 | Not a gap — a deliberate, explicit sequencing rule ("must not be implemented before the core product is proven"). Resolving it now would violate the BR itself. | Time and adoption data, per BR17's own condition — not an engineering blocker. |
| AI-based ranking/safety-signal specifics | BR06/BR14 conditional AI language (FR028, FR064) | Gated on the AI Service existing at all (ADR-009), which is correctly deferred platform-wide. | A module actually committing to an AI surface, triggering ADR-009's own resolution process. |
| Personality-assessment instrument selection | BR07, FR033 | Structurally identical to the row above — a licensed third-party psychometric tool or a custom-built questionnaire is a procurement/product decision outside what an engineering-only design pass can resolve, and `06-impact-analysis.md` IA033 flagged that this was missing from this table despite belonging here. | Product selects and (if licensed) contracts an instrument; FR033's own skip/non-blocking mechanics (already specified, BR07 core capability works without it) are unaffected by which instrument is eventually chosen. |

**Resolved as of 2026-09-13 (moved out of this table — see DEC-V1-010/DEC-V1-011):** exact message/evidence retention window (was: BR11, FR050/FR053/FR054); CSAM report packet schema and on-call paging vendor's remaining implementation-stage detail (was: an open detail under DEC-V1-009). Both had been filed here as requiring external input; both actually only required the research this file's own established method (DEC-V1-005/DEC-V1-006's precedent) already performs for exactly this class of question.

## Resolved decisions

### DEC-V1-001 — Profile completeness tier field assignment (resolves FR003/FR005 confidence gap)

In the context of BR01/BR06 DEC-003 requiring three distinct, non-overlapping
tiers (existence / discoverability / enhanced matching) but leaving the exact
field-to-tier mapping as implementation-stage, facing the risk that
"implementation-stage" would otherwise mean each engineer guesses differently,
we assign:

- **Existence tier** (minimum to save a profile at all): name, date of birth,
  gender, city/locality, at least one photo. (Phone/identifier already exists
  from Sign-Up, FR092.)
- **Discoverability tier** (minimum to clear BR06's Discovery gate — must be
  "enough for a viewer to make a meaningful judgment," per BR01 Constraints):
  existence tier, plus: highest education level, profession/occupation,
  marital history (never married / divorced / widowed), relocation
  willingness, and at least one partner-preference field (age range or
  locality).
- **Enhanced-matching tier** (optional, improves Compatibility richness only,
  BR07): everything else — lifestyle preferences, food/travel/hobbies,
  communication/conflict tendencies, independence, family-involvement
  expectations, career/children/living/financial expectations, pets,
  additional photos, video introduction, horoscope.

We chose this specific split over any alternative grouping to achieve BR01's
own stated test ("meaningful enough to judge, not a headcount") — every
discoverability-tier field is something a real viewer would need before
deciding whether to explore further; nothing in it is convenience-only —
accepting that this list may need one or two fields added once real usage
data exists (a normal FR-level refinement, not a re-opening of this decision's
structure).

### DEC-V1-002 — Discovery ranking weights and fairness methodology (resolves FR026/FR028 confidence gap)

In the context of BR06 requiring locality/preference/lifestyle/compatibility/
evidence-based ranking with popularity excluded and named fairness guardrails
enforced, facing the choice between an opaque learned ranking function and a
transparent weighted-rule function, we chose a **transparent, explainable
weighted-sum model** — consistent with BR07's own V1 commitment to
transparent rules over ML — with these initial weights: locality/relocation
match 30%, partner-preference match 30%, lifestyle/compatibility-signal
overlap (BR07) 20%, evidence/verification completeness (BR08) 20%, and
**popularity/engagement signals weighted 0% by construction** (not merely
absent from the formula, but structurally impossible to add without editing
this named list). A **diversity re-ranking pass** runs after the weighted
sort: no more than 3 consecutive results in a feed page may share the same
top-decile score bracket, forcing exploration of adjacent-quality matches
rather than a static "top profiles get all the traffic" outcome — directly
addressing the CMU/Tepper popularity-concentration finding already recorded
in BR06 DEC-004.

**Fairness-testing methodology**: a monthly automated parity report comparing
Discovery visibility distribution across locality, education bracket, and
(where legally collectible) other protected characteristics; any segment
whose median visibility falls below 70% of the platform median triggers a
product/eng review before the next ranking-weight change ships. This is a
statistical monitoring process, not a one-time test — it runs continuously
once V1 has real usage data, seeded by the automated regression tests already
in `05-test-scenarios.md` (TS062-TS068) which assert the structural rules
(no popularity input, every AI signal labeled) that make the monthly report
meaningful in the first place.

We chose transparent weights plus a scheduled fairness report over an opaque
model plus a one-time audit, to achieve both BR06's explainability
requirement and an early-warning system for the exact bias failure mode this
BR was written to prevent, accepting that hand-tuned weights are less
individually "optimal" than a learned ranker would eventually be — a
deliberate, BR07-consistent trade-off, not an oversight.

### DEC-V1-003 — Community-assisted discovery hint mechanics (resolves FR029 confidence gap)

In the context of BR06 DEC-001 keeping community-assisted discovery in scope
but leaving its mechanics open, facing the risk of either building nothing
(losing a named capability) or building something that becomes a disguised
teaser-profile mechanism (a non-goal), we chose: a hint is **only** created
when a Home Circle member manually fills a structured form naming a
community/locality and a one-line context ("I know someone active in the
[X] community near [Y]") — **never** algorithmically generated from another
candidate's actual private profile data. The resulting card shows only that
community/locality string and the submitting member's relationship to the
searching candidate; it contains no name, photo, or contact field in its
data model (not merely hidden in the UI — the field doesn't exist to leak).
Hint cards appear at low, capped frequency (no more than one per 20 feed
items) so they read as an occasional, genuine suggestion, not a primary
discovery mechanism competing with real profiles.

We chose family-submitted, structurally content-limited hints over any
system-generated hint, to achieve BR06's "community-assisted, not a public
teaser" requirement as a data-model guarantee rather than a policy that could
be silently violated by a future feature addition, accepting that this makes
hints rarer and lower-signal than an algorithmically-surfaced version would
be — an intentional trade-off given the non-teaser non-goal outranks hint
volume.

### DEC-V1-004 — Verifier anti-abuse mechanics (resolves FR037 confidence gap; vendor selection itself remains open, see table above)

In the context of BR08's Verification Circle needing real anti-abuse
safeguards before production (explicitly flagged as "[still to be designed]"
in the source Master Requirements Input), facing the risk of fake/malicious
verifiers gaming the four-option bounded response, we specify: (a) a verifier
must themselves hold at least Level-2 platform trust status (established
identity, not a fresh/unverified account) before their response counts as
evidence; (b) an account may be invited as a verifier no more than 5 times in
a rolling 7-day window, rate-limiting verifier-role spam; (c) a verifier's
confirmation is idempotent per candidate — inviting the same verifier twice
for the same fact does not create two evidence records; (d) a verifier later
found fraudulent or eligible-only-in-appearance has their specific
confirmation retroactively marked invalid (never silently deleted, per
FR037's own acceptance criterion) and their own account flagged for a BR16
admin review; (e) the invited verifier's own outreach notification uses
neutral, non-leading framing ("­[Candidate] listed you as someone who might
be able to confirm something about them") rather than framing that implies a
favor owed or a expected "Yes."

We chose Level-2-trust-gating plus rate-limiting plus idempotency over a
purely social/reputation-based anti-abuse model, to achieve a concrete,
testable eligibility bar without inventing a whole separate verifier-trust
subsystem, accepting that this doesn't fully prevent a determined bad actor
who has themselves built up Level-2 trust — a residual risk BR16's admin
review path exists specifically to catch after the fact, not something this
mechanism alone needs to fully close.

**Verifier/evidence review SLA**: live research (2026-09-12) confirmed
BharatMatrimony — one of this project's own named comparable products
(already cited in BR08 DEC-003) — publishes an actual operational
benchmark for this exact kind of review: photo validation is manually
screened with a **1-hour turnaround** before the photo becomes visible to
other members. We adopt **1 hour as Mangaly's own target for routine
Mangaly-operational evidence/photo review** (FR038's admin-verification
path), matching a real, named competitor's actual practice rather than an
invented number — accepting that Verification Circle responses (a
third-party human being asked to respond, not an internal review queue)
are not held to this same SLA, since that response depends on when the
invited verifier chooses to act, not on Mangaly's own review capacity.

### DEC-V1-005 — Marriageable age threshold (resolves FR041 confidence gap)

In the context of FR041 flagging that "exact current thresholds should be
reconfirmed... given ongoing legislative discussion," live research
(2026-09-12) confirmed the current, applicable law: the Prohibition of Child
Marriage Act, 2006 sets 21 years for men and 18 years for women, and
Uttarakhand's Uniform Civil Code (in force since January 2025) uses the
identical figures rather than departing from them — this is the actual
current national baseline, not a superseded number. A 2021 Prohibition of
Child Marriage (Amendment) Bill proposing to raise the threshold to 21 for
women as well remains under discussion and is **not yet enacted** as of this
research date.

We chose to implement **21 (men) / 18 (women)** as the current gate value,
stored as an **admin-configurable, versioned setting** (not a hardcoded
literal in application code) — over waiting for the pending bill to resolve
before building anything — to achieve a correct, shippable V1 gate now,
while accepting that if the pending amendment passes, updating the threshold
is a configuration change an operator makes, not a code deployment, which is
the entire reason this is being built as a setting rather than a constant.
This is the specific technical mechanism that turns FR041's "pending legal
reconfirmation" language into something buildable now without waiting on the
legislature: the code is correct against today's law, and stays correct
against tomorrow's law without a redeploy.

### DEC-V1-006 — Safety severity taxonomy and detection-scope boundaries (resolves FR064/FR068 confidence gap)

In the context of BR14/FR065's graduated-response pipeline needing an actual
severity taxonomy before the "controlled human investigation" and
"legal/emergency escalation" stages mean anything concrete (flagged open in
both the Master Requirements Input and BRD BR-SAFE-007, which itself names
exactly this as requiring "abuse taxonomy, severity matrix, operational
staffing and legal review," none of which any source document actually
specifies a number for), the SLAs below are **not invented round numbers**
— they follow the actual legal floor that already governs an India-based
platform, and go faster than that floor where the underlying harm warrants
it, per live research (2026-09-12) into the Information Technology
(Intermediary Guidelines and Digital Media Ethics Code) Rules, 2021, as
amended 10 February 2026: a grievance officer must **acknowledge** any
user complaint within **24 hours**; content that is prima facie nudity or
impersonation must be **removed within 2 hours** of a complaint (tightened
from 24 hours in the 2026 amendment); and the broader grievance
**resolution** ceiling is **36 hours** (tightened from 72 hours in the same
amendment). These are legal maximums Mangaly must not exceed — not targets
to aim for — so every tier below is set to *meet or beat* the applicable
legal ceiling, not merely reference it.

| Tier | Examples (from BR14's 15 named categories) | Response | Legal/precedent basis |
|---|---|---|---|
| 1 — Low | Isolated vulgarity, a single unwanted-contact instance | Automated in-context nudge (Tinder/Bumble-style "Are you sure?" pattern, already cited in BR14 DEC-003); logged, no mandatory human SLA | No specific legal SLA applies to an unreported nudge; if the affected user files a report, it is immediately reclassified into the grievance-acknowledgment SLA below. |
| 2 — Medium | Repeated harassment, suspicious escalation pattern, off-platform pressure, malicious links | Acknowledged within **24 hours**; temporary restriction/rate-limit applied; human-reviewed and resolved within **36 hours** | Matches the IT Rules 2021 (2026-amended) grievance acknowledgment (24h) and resolution (36h) ceilings exactly — these are legal maximums for *any* complaint, so Tier 2 cannot legally take longer than this regardless of internal preference. |
| 3 — High | Explicit threats, financial manipulation/romance-scam indicators, coercion, blackmail, or any nudity/impersonation-adjacent content | Immediate block pending review; human-reviewed within **2 hours** where the content is nudity/impersonation-adjacent (the legal ceiling for that category); otherwise within **12 hours** — deliberately faster than the 36-hour general ceiling, because industry practice (Trust & Safety Professional Association: higher-severity content warrants faster-than-baseline turnaround) treats explicit-threat/financial-harm content as warranting better-than-minimum response, not merely legal-minimum compliance | IT Rules 2021 2-hour ceiling (nudity/impersonation subset) + TSPA severity-tiered-response principle for the rest. |
| 4 — Critical | Sexual abuse indicators, grooming, credible imminent-harm signals, or suspected child sexual abuse material (CSAM) | Immediate block + paged to an on-call safety responder (never queued) + in-app guidance toward external emergency/support resources; **suspected CSAM is additionally reported to the appropriate law-enforcement channel without waiting for the internal investigation to complete** | India's POCSO Act (Protection of Children from Sexual Offences) imposes a mandatory reporting obligation for suspected child sexual abuse content, analogous to the US's NCMEC/REPORT Act 24-hour compliant-report requirement (confirmed via live research) — Mangaly's own internal response is "immediate," faster than any external reporting deadline, precisely so the external deadline is never the binding constraint. |

**Detection-scope boundary**: automated detection may analyze message
*metadata* (frequency, timing, escalation velocity) and message *text*
against a policy classifier for exactly these 15 named categories — nothing
broader. It never analyzes photo/video content (unflagged media is not
scanned; a reported photo/video is reviewed by a human, not a model), and it
never reads Home Circle relationship data or Trust/Verification evidence as
a detection input, keeping Safety and Trust operationally separate exactly
as BR14 DEC-001 requires.

We chose to derive every SLA from the actual legal ceiling already binding
this platform (plus named industry practice for going faster where
warranted) over inventing round numbers with no external anchor, to achieve
exactly what FR068 flagged as missing — a documented taxonomy the
graduated-response pipeline can route against — while guaranteeing Mangaly
is never merely "internally reasonable," it is **legally compliant by
construction**, accepting that a future change to the IT Rules (already
tightened once, in February 2026) would require this table's numbers to be
re-checked, not just the case volume assumptions.

### DEC-V1-007 — Admin/operations workflow and staffing model (resolves FR072/FR073/FR074 confidence gap)

In the context of BR16's admin console needing an actual case workflow
before Step 7's Tech Reqs can build the Case queue/detail screens against
something concrete, we define: **Intake** (a report, verification request,
or false-relationship dispute creates a case) → **Triage** (auto-priority:
Tier 3/4 safety cases jump the queue per DEC-V1-006; everything else
FIFO within its case type) → **Assignment** (operator self-claims from the
queue; no forced round-robin at V1's expected case volume) →
**Investigation** (operator reviews only the case-scoped evidence the
Authorization Engine returns — see `architecture.md` MOD03-ADR-003) →
**Decision** (approve / deny / request-more-evidence / escalate, per case
type) → **Resolution & audit write** (BR15) → **Appeal** (available to the
candidate for any restriction/deny decision, reviewed by a different
operator than the original decision where staffing allows).

**Staffing/SLA model for V1**: a small on-call rotation, not 24/7 staffing.
Ordinary verification requests target BharatMatrimony's own 1-hour
benchmark (DEC-V1-004); false-relationship disputes and Tier 2 safety cases
run business-hours review against the legally-binding 24h-acknowledge/
36h-resolve ceiling (DEC-V1-006); Tier 3/4 safety cases page the on-call
responder regardless of hour, since these are exactly the cases where the
2-hour legal ceiling (Tier 3, nudity/impersonation subset) or an immediate
CSAM reporting obligation (Tier 4) makes "business hours" not a legally
available option in the first place.

We chose self-claim over forced assignment, and a page-only-for-severe-cases
on-call model over full 24/7 staffing, to achieve a workable V1 operational
model sized to a small team's actual capacity while still meeting every
legally-binding ceiling DEC-V1-006 establishes, accepting that Tier 3/4's
legal deadlines are the one place this small-team model has no slack at
all — a genuine operational risk this document surfaces rather than
smooths over, and one Impact Analysis (Step 6) should weigh explicitly
against actual expected Tier 3/4 case volume before this staffing model is
trusted at scale.

### DEC-V1-008 — Real-world meeting safety guidance content (resolves FR085 confidence gap)

In the context of FR085 flagging its guidance content as "pending
product/legal input," and this project's own research (already recorded in
`03-ux.md` UX30) confirming Tinder's and Bumble's published safety-tip
content as the current, well-regarded industry baseline, we draft the actual
V1 guidance copy now, since writing this content is squarely a product
decision, not one requiring external legal input (legal review, if any,
would address liability-framing language around it, not the substance of
standard, non-controversial safety advice):

- "Meet in a public place, especially the first time."
- "Tell a friend or family member where you're going and when you expect to be back."
- "Consider a video call before meeting in person if you haven't already spoken face-to-face."
- "Arrange your own way there and back — don't feel obligated to accept a ride."
- "Trust your instincts. It's always okay to leave, or not go, if something feels wrong."

We chose to draft this now rather than leave a placeholder, to achieve a
genuinely shippable V1 (a "pending" guidance card is not shippable), while
still flagging — per FR085's own Confidence note — that a final legal
liability-framing pass on the *surrounding* disclaimer language (not this
list's substance) should happen before production launch, consistent with
how every other legal-adjacent item in this file is handled: the product
decision is made now, the narrow external check is named explicitly, not
used as an excuse to leave the whole item open.

### DEC-V1-009 — Safety-escalation operational infrastructure and CSAM reporting channel (resolves the IA065/IA068/IA074 gap: DEC-V1-006 defines the severity taxonomy, but names no actual mechanism to reach Tier 3/4's exits)

In the context of `06-impact-analysis.md` finding, independently across three items (IA065, IA068, IA074), that DEC-V1-006's four-tier severity taxonomy correctly fixes *what* triggers escalation but that this module's architecture named no actual on-call paging mechanism for Tier 3/4, and no actual external reporting channel for suspected CSAM — meaning the taxonomy's most severe exits were policy commitments, not built integrations — we resolve both:

**On-call paging.** Tier 3/4 cases route to a dedicated on-call paging tool (a PagerDuty-class service — the specific vendor is an implementation-stage procurement choice, not re-litigated here) integrated with the Operations component (`architecture.md` §2.2), triggered automatically the moment Safety Intelligence classifies a case as Tier 3 or Tier 4 — not a manual step an operator has to remember to take. This is now a named external dependency in `architecture.md` §1's edge table, not an implicit assumption. **(2026-09-13 update: DEC-V1-011 below names the specific vendor — PagerDuty — closing this item's remaining open detail.)**

**CSAM reporting channel.** Live research (2026-09-12) confirmed the actual, legally-specified channel for an India-based platform: **the POCSO Rules, 2020, Rule 11** requires any person (including an intermediary) who receives or becomes aware of child sexual abuse material to report it to the Special Juvenile Police Unit (SJPU), local police, or the National Cyber Crime Reporting Portal (**cybercrime.gov.in**) — and Rule 11(2) additionally requires an intermediary to hand over the material and its source information, not merely notify that it exists. Mangaly's Tier 4/CSAM path therefore has one concrete, correct action to build against: automatic case creation plus a structured hand-off packet (the flagged content, its provenance/source metadata, and the reporting candidate/account identifiers) routed to cybercrime.gov.in and/or the SJPU, triggered immediately, in parallel with the internal block-and-page action — not sequenced after an internal investigation completes, since Rule 11 does not wait on that. **(2026-09-13 update: DEC-V1-011 below names the specific packet field schema, closing this item's remaining open detail.)**

We chose to name a concrete paging-tool category and the exact, verified legal reporting mechanism now, over leaving both as a "Step 7/8 concern" the way the Impact Analysis pass found them, to achieve a genuinely closeable release gate (a taxonomy with unreachable exits is not actually a complete safety design, regardless of how well-reasoned the tiers themselves are) — accepting, as of the original 2026-09-12 pass, that the specific paging vendor and the exact structured-handoff data format remained real Step 7 implementation choices; both are now resolved concretely by DEC-V1-011 below, since Step 8's own review found "implementation-stage" was being used as a default deferral rather than reflecting a genuine research gap.

### DEC-V1-010 — Message/profile data retention and erasure windows (resolves BR11/FR050/FR053/FR054/FR101's previously "DPDP-gated" retention question)

In the context of BR11/FR050/FR053/FR054/FR101 all naming "formal DPDP Act
legal sign-off" as the blocking dependency for a concrete retention window,
and Step 8 (Security & Performance) finding that this pipeline has no actual
legal-counsel seat to provide that sign-off — while this file's own
established method (DEC-V1-005's marriageable-age research, DEC-V1-006's
safety-severity SLA table) already resolves exactly this class of question
from real, current law and named comparable-product precedent — live
research (2026-09-13) confirms:

- The DPDP Act 2023 and its 2025 Rules (Rule 8) set the general obligation:
  a Data Fiduciary must erase personal data once its processing purpose is
  served (or consent is withdrawn), unless another law requires longer
  retention — plus two concrete numeric anchors: (a) a **minimum one-year**
  retention of personal data, associated traffic data, and processing logs
  from the date of processing (the Rules' Seventh-Schedule-class floor,
  applying to all data fiduciaries); (b) for large platforms specifically
  (the Rules' Third-Schedule-class categories, which include social-media-
  class platforms), a **3-year inactivity-triggered erasure ceiling**, with
  a **mandatory 48-hour pre-erasure notice** to the user before deletion
  completes.
- BharatMatrimony's and Shaadi.com's own published privacy policies (live
  research, 2026-09-13) do not commit to a specific numeric post-deletion
  window — both state retention continues "as long as needed" for fraud
  prevention, dispute resolution, and legal compliance, with deleted/
  inactive data moved to a restricted-access store rather than purged on a
  fixed day. This confirms the matrimonial-platform norm is a policy-driven,
  fraud/dispute-anchored retention model, not a short fixed window —
  consistent with, not contradicting, DPDP's own "purpose fulfilled" test.

We chose the following concrete V1 retention model, combining DPDP's own
numeric floor/ceiling with the named-competitor pattern of a fraud/dispute/
safety-anchored retention purpose:

- **Active account, active connection:** message content retained for the
  life of the connection/account — no arbitrary chat-history cap — since
  BR11's own six named retention-justification purposes (dispute
  resolution, safety investigation, fraud prevention, legal compliance,
  etc.) apply throughout active use, matching BharatMatrimony/Shaadi's own
  "as long as subscribed" pattern.
- **Post-account-deletion:** a **30-day reactivation grace window**
  (a common undo period for this class of consumer app), followed by
  **erasure or irreversible anonymization within 90 days of the original
  deletion request** — inside DPDP's own "without unreasonable delay"
  standard, and well inside the 3-year large-platform ceiling Mangaly does
  not yet meet the scale to be classified under, adopted here as a
  self-imposed discipline rather than waited into by scale.
- **Mandatory 48-hour pre-erasure notice** (DPDP Rule 8's own explicit
  requirement) fires before the 90-day erasure completes, giving the user
  one last chance to cancel deletion — a legal requirement, not a UX
  nicety; TR101's disclosure endpoint must surface it.
- **Processing/access logs (audit trail, per BR15):** retained a minimum of
  **one year** from the date of processing, per the DPDP Rules' own
  floor — the Audit Log Store's append-only design (ADR-011) already
  exceeds this floor by design (it has no delete path at all), so this is
  stated for completeness, not as a new build requirement.
- **Safety Intelligence-triggered evidence-retention exception (TR053):**
  scoped to the single conversation under investigation, retained for the
  duration of the associated Operations case plus **180 days after case
  closure** (bounding what was previously an unscoped "controlled human
  investigation" duration), or until an active legal hold (TR054) is
  lifted, whichever is later.
- **Inactive-but-not-deleted accounts:** DPDP's own 3-year inactivity
  ceiling and 48-hour pre-erasure notice apply as the outer bound,
  regardless of Mangaly's current Significant-Data-Fiduciary classification
  status, since building to the stricter standard now avoids a redesign if/
  when Mangaly is later classified as one.
- **Legal-hold duration specifically is not, and cannot be, a fixed number**
  — a legal hold lasts as long as the actual legal matter requiring it
  remains open, which is a structural property of what a legal hold is in
  any jurisdiction, not an unresolved dependency this file is punting on.
  What *is* resolved here is the mechanism (TR054's structural
  skip-deletion-while-held behavior) and the default window a conversation
  falls back to once no hold is active (the same windows above).

We chose this specific model — DPDP's numeric floor/ceiling plus a
competitor-consistent, purpose-anchored middle — over either an arbitrarily
short window (which would conflict with BR11's own named safety/fraud/
dispute retention purposes and BharatMatrimony/Shaadi's demonstrated norm)
or an indefinite one (which would fail DPDP's storage-limitation principle),
to achieve a genuinely shippable, legally-grounded V1 retention policy now,
accepting that this is a good-faith V1 interpretation of DPDP's
principles-based text (which does not itself name a matrimonial-platform-
specific number) rather than a number DPDP states verbatim — the same
honest framing DEC-V1-005 already uses for the marriageable-age threshold,
revisable the same way if a future regulatory clarification narrows it
further.

This resolves TR050/TR053/TR054/TR101's own carried-forward DPDP dependency:
`mangaly_communication`'s retention job, the evidence-retention exception,
and the account-deletion disclosure now have a concrete numeric policy to
build and test against.

### DEC-V1-011 — CSAM report packet field schema and on-call paging vendor (resolves DEC-V1-009's remaining implementation-stage gap)

In the context of DEC-V1-009 already naming the *mechanism* (auto-fired case
creation plus a structured hand-off packet to cybercrime.gov.in/SJPU per
POCSO Rule 11(2), plus a PagerDuty-class on-call paging integration) but
explicitly leaving "the specific paging vendor and the exact structured-
handoff data format" as open implementation-stage choices, and Step 8
(Security & Performance) finding this insufficient for Step 9 to actually
build against, we resolve both concretely:

**CSAM report packet field schema.** Live research (2026-09-13) into
NCMEC's CyberTipline — the real, industry-standard ESP (Electronic Service
Provider) CSAM reporting schema most platforms model their own internal
escalation packet on, even though NCMEC itself is the US reporting channel
and Mangaly's actual mandatory channel is India's cybercrime.gov.in/SJPU per
POCSO Rule 11 — confirms the schema's real field categories: a
reported-person/account section, an associated-account section (linked
identities, screen names, profile URL), an IP/capture-event section (IP
address, event type, timestamp), and file/incident-detail sections (the
flagged content reference, an incident summary, a human-reviewed
confirmation flag). We adopt the same field categories for Mangaly's own
`mangaly_operations.csam_report_packet` structured payload, since POCSO Rule
11(2)'s own requirement ("hand over the material and its source
information, not merely notify") demands the same substantive content
NCMEC's schema already standardizes:

| Field group | Concrete fields |
|---|---|
| Reporting-platform identifiers | `mangaly_case_id`, `classification_timestamp`, `reporting_component` (always `safety_intelligence`) |
| Reported-account details | `account_id`, `profile_id`, `phone_identifier`/`email_identifier` (as known), `account_created_at`, `identifier_verified_at` |
| Associated-account/relationship context | linked Home Circle membership IDs and connection IDs the flagged content occurred within (never the *content* of unrelated conversations — scoped strictly to the case) |
| Capture/provenance metadata | `detection_signal_id`, `detected_at`, `ip_address_at_send` (if available from session data), `client_platform` (Android/iOS/Web) |
| Flagged content reference | `evidence_document_ref`/`message_id` pointer only (never the raw material inlined into this metadata record itself — the packet *transmission* carries the actual material separately, per Rule 11(2), consistent with the module's own no-raw-document-in-a-general-record discipline elsewhere) |
| Incident summary | `severity_tier` (always 4 for this packet type), `detection_category`, free-text `human_reviewer_summary` (populated by the Operations reviewer who confirms escalation, never auto-generated) |
| Reporting-channel confirmation | `reported_to` (`cybercrime.gov.in` and/or `sjpu`/local police, per DEC-V1-009), `reported_at`, `reporting_reference_id` (the acknowledgment/ticket ID the channel returns) |

**On-call paging vendor.** Per this project's standing config-placeholder
convention (create the real config structure now, drop in real credentials
later, rather than leaving a vendor category unnamed indefinitely), we name
**PagerDuty** concretely as Mangaly's on-call paging integration — the same
PagerDuty-class benchmark DEC-V1-009 already referenced generically, now
committed to a specific, real, currently-operating product rather than a
category. `07a-db-implementation/.env.example` is updated to reflect
PagerDuty's actual integration model (Events API v2 routing key), not a
generic placeholder name.

We chose to resolve both now — modeling the packet schema on a real,
externally-standardized precedent (NCMEC's) rather than inventing an ad hoc
field list, and naming a real vendor rather than a category — to achieve
something Step 9 can actually implement against, over leaving both as open
procurement questions this pipeline has no actual procurement actor to
resolve, accepting that the specific PagerDuty account/escalation-policy
configuration and the exact cybercrime.gov.in submission mechanism (a
programmatic API versus a manual portal/liaison submission) remain real
Step 9 implementation-time confirmations — narrower, genuinely
implementation-stage details, not the same open-endedness this item started
with.

### DEC-V1-015 — Interim identity retired into the ForKhatri platform identity (pays down the IA092 technical debt)

**Date:** 2026-09-14. **Binding contract:** `docs/ParentApp/07-tech-reqs.md`
TR10–TR17, TR23; `docs/ForKhatri-Unified-Umbrella-App-Interpretation.md`
("Mangaly's interim credentials are migration debt, not a final identity
decision").

In the context of the product owner's decision that ForKhatri is one
mobile-first app with one sign-in and one member identity — members sign in
once, then choose a module — and of the platform Identity & Trust Service now
existing (`platform/identity-service`, database `forkhatri_identity`), facing
Mangaly's interim account/OTP/password/session system (FR092–FR095, FR101,
DEC-V1-012) being exactly the "second login" that decision rules out, we
decided:

1. **Sign-in leaves Mangaly.** MangalyService accepts one credential: the
   ForKhatri `fk_session` cookie. Its Identity Bridge resolves the token over
   the internal API (TR14) with a per-token in-process cache (≤30 s positive,
   5 s negative; keyed by SHA-256 of the token), fails closed with `503` when
   the identity service cannot answer, and binds `mangaly.account_id` with
   `SET LOCAL` exactly as before — every RLS policy is unchanged.
2. **Link-table approach: reuse `mangaly_identity.account`.** Its `id` is the
   platform `member_id` (TR10). TR23 imported every active Mangaly account into
   the platform with its id unchanged, so no foreign key in any of the 14
   schemas is rewritten. Migration `014-platform-identity-link.sql` makes
   `credential_hash` nullable, keeps "must have a phone or email" except for a
   `deleted` row, and adds the SECURITY DEFINER
   `ensure_platform_account(member_id, phone, email)`, called on every
   platform-authenticated request: it creates the row just-in-time for a new
   member (TR11) and syncs phone/email to the platform's verified values, which
   Home Circle's invitation matching reads. A different `pending_verification`
   account holding the identifier (an abandoned, never-proven interim sign-up)
   is retired; a different `active`/`locked` account holding it is refused
   (`403 platform_identity_conflict`) for operations to reconcile, never merged
   silently. An own `locked`/`deleted` row is refused too
   (`403 platform_account_not_active`) — platform sign-in must not undo a
   Mangaly lock or deletion.
3. **Flag default off.** `INTERIM_IDENTITY_ENABLED=false`. The interim
   credential routes (sign-up, login, login OTP, OTP verify/resend, reset
   request/confirm) answer `410 {"detail": {"code": "moved_to_forkhatri",
   "message", "entrance_url"}}`; the legacy `mangaly_session`/bearer path is
   ignored. The code is retained, not deleted, and automated tests enable the
   flag explicitly (TR15 step 5). `/auth/me` answers for the platform session.
4. **Web client.** `/login`, `/signup`, `/otp`, `/reset` hand off to the
   ForKhatri entrance; any `401` navigates to
   `${ENTRANCE}/?return_to=<current URL>`; log out calls the platform
   `POST /v1/auth/sign-out` then goes to the entrance; Mangaly's top bar
   carries a persistent "ForKhatri" link back to the hub in Mangaly's own
   button style.

We chose reusing `mangaly_identity.account` over introducing a new member-link
table, to achieve zero foreign-key rewrites and zero RLS policy changes on a
live, sensitive schema, accepting that the table and its sibling tables
(`otp_challenge`, `password_reset_token`, `session`) keep dormant interim
credential data until a later, separately-reviewed cleanup migration; and we
chose a ≤30-second resolution cache over a call per request, accepting that a
sign-out takes up to 30 seconds to reach Mangaly (the contract's own bound).

**Supersedes:** DEC-V1-012 as a *Mangaly* mechanism — passwordless-primary
sign-in with an optional password now lives in the platform (TR13/TR19), not
here.

## Known technical debt (tracked, not blocking V1)

Per `06-impact-analysis.md` IA092: Mangaly is building its own interim account/credential system (FR092-FR095) because no Common Platform Identity & Trust Service exists yet, ahead of Mangaly in build order (ADR-016/017) — a fact FR092 itself already discloses honestly rather than silently. This is the correct and only viable choice given Mangaly's build-order position, not a mistake, but it creates a real, high-likelihood future obligation: whenever a platform-wide Identity module is eventually built, Mangaly's live candidate credentials and sessions will need migrating into it, and live credential/session migration is a genuinely high-risk operation class. Recording this now, explicitly, as a planned future migration rather than a surprise discovered later, is the entire value of naming it here — no action is required of V1 itself beyond building FR092-FR095 exactly as specified. **Credential hashing (2026-09-13, Step 8 note):** the interim `mangaly_identity.account.credential_hash` column names no algorithm in `schema.sql` — Step 9 must implement this using **Argon2id** (current OWASP-recommended default) or bcrypt with a work factor tuned to ~250–500ms verification cost, never an unsalted or fast general-purpose hash; this is a plain implementation instruction, not an open design question.

**Paid down 2026-09-14 (DEC-V1-015).** The platform Identity & Trust Service now owns credentials and sessions. Active Mangaly accounts were imported with their ids and Argon2id hashes (ForKhatri TR23), and Mangaly resolves the ForKhatri session instead of its own. The interim tables remain as dormant history (see DEC-V1-015's accepted trade-off); the interim routes answer `410`.

## Updates this file makes to already-Sealed files

Per this pipeline's append-only convention, `01-business-requirements.md`
and `02-functional-requirements.md` are not rewritten — each affected BR/FR's
own Confidence line gets one small addition pointing here, and nothing else
in either file changes. See the Revision history entries added to both files
for exactly what was touched.

## Definition of Done

- Every open item from `01-business-requirements.md`/`02-functional-requirements.md`'s
  Open blockers sections is accounted for: either resolved with a concrete
  decision above, or listed in "What stays open" with a named, genuine
  external dependency (not an internal decision dressed up as external).
- No decision above changes a BR/FR's business intent — each fills in a
  value the source document already said was implementation-stage.
- No open blockers introduced by this file itself.

## Approval

Product Manager — [x] Approved — krishna kategaru (autonomous), 2026-09-12
Chief Architect — [x] Approved — krishna kategaru (autonomous), 2026-09-12
