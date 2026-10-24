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
| 2026-09-21 | Added **DEC-V1-017**: the §12 assessment is Mangaly's own ten drawn, South-Indian-specific choices with "It depends" on every question (Olson/PREPARE-ENRICH/Gottman-mapped, no score, unanswered renders nothing), closing the "Personality-assessment instrument selection" open item (IA033); recorded the owner's standing rule that all Mangaly art must be Mangaly-specific and mostly South Indian; recorded that the candidate profile page now carries the connection action and a "sealed" card. | Owner review session — krishna kategaru (autonomous), 2026-09-21. |
| 2026-09-21 | **Owner scenario recorded (DEC-V1-018, below DEC-V1-017).** The profile builder is now two parts — "Details" (the standard biodata a family reads; what a match's parents see, only as shared) and "In my words" (prompts, voice, ten choices; seen only by connected candidates unless published) — with Preview as the third tab. The connected candidate lens shows all formal details *and* the prompts, per the owner: "once both sides accept, the child can see all the formal information and also the prompts / psychological test." Still to build from the same scenario: an incognito, non-persisted candidate↔candidate chat; a persistent, circle-visible parent chat; Discover as a photo wall. | Owner review session — krishna kategaru (autonomous), 2026-09-21. |

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
| Verification Circle (community confirmation) | BR08, FR037 | Still specified in M01-F §5 and not built. Not vendor-gated — it is community members answering Yes / No / Don't know / Cannot confirm, with the §5 safeguards against gossip, retaliation and fabricated witnesses. | Engineering time. It is the next verification layer after the face match, and needs no external party. |
| Future Mangaly Agent layer | BR17, FR077/FR078 | Not a gap — a deliberate, explicit sequencing rule ("must not be implemented before the core product is proven"). Resolving it now would violate the BR itself. | Time and adoption data, per BR17's own condition — not an engineering blocker. |
| AI-based ranking/safety-signal specifics | BR06/BR14 conditional AI language (FR028, FR064) | Gated on the AI Service existing at all (ADR-009), which is correctly deferred platform-wide. | A module actually committing to an AI surface, triggering ADR-009's own resolution process. |

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

### DEC-V1-016 — Verification is a live face match against the member's own photos. Document/ID verification is dropped, not deferred

**Date:** 2026-09-21 · **Decided by:** Product owner (direct instruction) · **Status:** Accepted
**Supersedes:** the "Verification vendor/process selection" open item carried since 2026-09-12

**In the context of** BR08/FR035/FR037 verification, where selecting a KYC
vendor had been open since 2026-09-12 and was blocking every form of identity
evidence, including forms that need no vendor at all,

**facing** the product owner's decision that Mangaly will not do document or
ID-scanner verification — *"forget doc verification ID scanner, let's keep face
scanner only"* — and that a live face check is the verification mechanism,

**we decided to** make the **live face match against the member's own uploaded
photos** Mangaly's verification mechanism, and to **drop** government-document
verification, ID scanning and DigiLocker integration from the product rather
than carry them as a backlog item that implies eventual delivery.

**to achieve** verification that ships with no vendor, no procurement cycle and
no custody of government identity documents — which also removes an entire
category of DPDP liability, since the most sensitive data Mangaly would ever
have held is the data it now never collects.

**accepting that** this is a real and deliberate reduction in evidence
strength, recorded here so it reads as a decision rather than a gap:

- **Age is self-declared and never verified.** A face match establishes that
  the photos and the account holder are the same person. It establishes
  nothing about age. DEC-V1-005's marriageable-age threshold therefore rests
  on the date of birth a member types in, and §22's minor-safety and POCSO
  obligations are served by Safety Intelligence and reporting rather than by
  any check at the door. Flagged to the product owner on 2026-09-21; decision
  reaffirmed.
- **Name and legal identity are never verified.** No layer asserts that a
  member is who they say they are in the civil sense.
- Consequently the `identity_age` and `operational_verification` layers of
  M01-F §4 are **not populated in this product**. The enum retains them
  because the conceptual model is sealed and a future owner may revisit this;
  nothing writes them.

#### What the face match actually is

A live capture, compared against the photos the member has already uploaded,
confirming the claim *"the person in these photos is the person using this
account."* It records as the **`profile_facts`** layer with
`source_category = 'face_match'` — the correct layer under M01-F §4.3, because
the verification attaches to a **claim about the photos**, not to the person's
identity or character.

Verified as buildable by live research (2026-09-21), in a mobile-first web app
with no native shell:

| Capability | Available in the browser | Note |
|---|---|---|
| Camera capture | Yes — `getUserMedia` | Already available to the PWA |
| Face detection + landmarks | Yes — MediaPipe FaceMesh, 468 landmarks, on-device | No server round-trip to detect |
| **Active** liveness (head turn, blink, mouth-open) | Yes | Defeatable by a good video replay — a known, accepted limit |
| **Passive** liveness (anti-spoof, no challenge) | No — would need a vendor | Out of scope with this decision |
| Embedding + comparison | Yes — 128-float descriptor, Euclidean/cosine distance | The descriptor travels, not the image |

#### The similarity score is an internal threshold, never a displayed number

A face match *is* a similarity computation: each face becomes a 128-float
descriptor, the two are compared by distance, and a threshold decides
same-person or not. face-api.js's own guidance is a 0.6 Euclidean threshold for
150x150 faces, on a ResNet-34-style model reporting 99.38% on LFW. This is
**1:1 verification** ("is this the same person as the photo?"), a far easier
and more accurate problem than 1:N identification against a population.

Two decisions follow, and they matter more than the model choice.

**1. The score never reaches a member.** Surfacing "87% face match" would be
precisely the number this product refuses to produce — §3 forbids a trust
score, §4.8 makes trust evidence rather than a score, and §11.3 already
rejects the identical pattern on the compatibility side ("no universal '87%
compatible'"). The distance is an internal threshold input, like a spam
filter's. A member sees a fact with provenance: *Photos confirmed as you ·
Sep 2026*. Pass or fail, with a date and a method, and nothing else.

**2. The threshold is set strict, biased toward false rejection.** Threshold
choice is a direct FAR/FRR trade: loosening it admits more distant faces as
the same person (FAR up, FRR down); tightening does the reverse. For a
matrimonial product these errors are not symmetric. A false *accept* means
someone verified an account using another person's photographs — the exact
deception §22 exists to prevent, now shipping with a confirming badge
attached. A false *reject* means an honest member retries in better light.
The first is a safety failure, the second an inconvenience. Mangaly therefore
tightens below the library default and offers easy retry plus a route to human
review, rather than loosening to reduce support contacts. This bias matters
more than it normally would, because with documents dropped the face match is
the only identity-adjacent evidence the product has.

#### The constraint that shapes the design

A face embedding is **biometric data** under the DPDP Act 2023 and the DPDP
Rules notified 14 November 2025, which carry the highest compliance
obligations in that framework. These are design constraints, not paperwork:

- Consent must be **specific and unbundled** — a face check cannot ride on the
  general terms accepted at sign-up. It needs its own consent, with a stated
  purpose and duration, and must be withdrawable.
- Consent must be **logged, timestamped and auditable**. M01-F §8 already
  requires exactly this record shape ("what consent was required and whether
  it was present"), so this reuses the accountability model rather than
  adding a parallel one.
- **Retention schedules are mandatory for raw frames, embeddings and logs,
  with automated purging.** DEC-V1-010 already sets Mangaly's retention
  method; these artefacts extend it.
- Therefore: **discard the captured frames once the comparison completes and
  keep only the outcome**, plus the verification row. Retaining face images to
  re-check later converts a one-off check into a standing biometric database —
  a materially different product and a materially different liability.

#### What remains of the layered model

| Layer | Populated? | By what |
|---|---|---|
| `account_authenticity` | Yes | Phone/OTP at ForKhatri sign-in |
| `profile_facts` | Yes | The live face match (`source_category = 'face_match'`) |
| `community_verification` | Future | Verification Circle (M01-F §5) — still specified, not built |
| `home_circle_relationship` | Future | Implied by an accepted Home Circle invitation |
| `identity_age` | **No — dropped** | Would have required documents |
| `operational_verification` | **No — dropped** | Would have required an admin document queue |


### DEC-V1-017 — The §12 assessment is Mangaly's own ten drawn choices, not a licensed instrument; every drawing is South Indian and specific

**Date:** 2026-09-21 · **Decided by:** Product owner (direct instruction) with autonomous implementation · **Status:** Accepted
**Supersedes:** the "Personality-assessment instrument selection" open item carried since 2026-09-12 (IA033)

**In the context of** BR07/FR033 (baseline §12: a game-like assessment of five minutes or less, no score), **facing** the open question of which psychometric instrument to license, **we decided** not to license one. The activity is ten forced choices with a third "It depends" answer on every question, each dimension mapped to an axis of an instrument that actually predicts marital outcomes (Olson's Circumplex cohesion/flexibility as used by PREPARE/ENRICH; PREPARE/ENRICH's SCOPE scales; Gottman's conflict-start and repair-attempt findings) — the mapping is recorded in `mangaly-web/lib/outlook.ts`. Nothing is summed: the result is ten answers, shown on a connected candidate's profile beside the reader's own answer to the same question ("Same as you" / "You said …"), never a total, never a grade, and a skipped question renders nothing (§3, §4.8; the owner's rule that the product must never assert something a person did not say).

**Presentation.** Each choice is a line drawing, not a text button (`mangaly-web/components/OutlookScene.tsx`). The owner's standing rule for all Mangaly art, given the same day: it must be based on Mangaly and "mostly South Indian culture", never vague or generic. The scenes are therefore the filter-coffee tumbler and dabara, the pillared verandah, the oonjal in the hall, a banana-leaf meal, the temple-pond steps, a brass kalasam, the terrace at night, the ammikallu, a scooter for two. Both sides of every pair get the same warmth and detail on purpose (the Circumplex model treats both extremes as the unhealthy ones, so a prettier picture would bias the answer). The drawings are one ink, one accent, no gradients, and are `currentColor`-based so they hold in dark mode and beside Devanagari/Telugu labels. They are a first version; any scene can be replaced by an exported SVG from a designer without touching the activity.

**Also decided in the same pass (profile page).** Before a connection, a candidate's profile page now carries the connection action itself (send / request sent / accept–decline when they asked first; "send for {candidate}" in Home-Circle context) and a "sealed" card naming exactly what opens on connection. The page previously said answers were "shared once you connect" and offered no way to connect.

**Consequences.** IA033 closes. FR033's skip/non-blocking mechanics are unchanged. No third-party data-sharing or licence obligations arise. If a licensed instrument is ever adopted, it must still satisfy §3 (no score displayed) — which is most of why none was chosen.


### DEC-V1-018 — The owner's reference scenario: who connects, what each role sees after acceptance, two kinds of chat, Discover as a photo wall

**Date:** 2026-09-21 · **Decided by:** Product owner (dictated scenario) · **Status:** Accepted

**Scenario.** A parent P has a candidate child C searching for a groom G. C may connect with G directly; P may search and suggest G to C; or P may send the request to G on C's behalf. What P and C see on G's page before acceptance is G's own choice (his publish/sharing settings). After acceptance on both sides, P sees all of G's formal information; C sees the formal information and everything in the Hinge/Bumble-style part (prompts, voice, ten choices). Candidate↔candidate chat is incognito: opened together, ended together, and gone once the session closes. Parent chat is always available, persistent, and completely monitored (retained and visible to the family side). Circles exist so that, once a relation is made, every role is explicit. Discover reads as a photo wall: scroll all the pictures, pick one, open the profile — for parents and candidates alike.

**Implemented in this pass.** The profile builder in two parts (Details / In my words / Preview); the connected candidate lens carrying formal details plus prompts.

**Open from this decision (next).** Incognito candidate chat (session-scoped, nothing stored — a change to the communication component and the shared chat utility); persistent circle-visible parent chat; Discover photo wall. The chat retention rule interacts with DEC-V1-010 (retention windows) — an incognito session stores nothing, so nothing falls under those windows; safety reporting must therefore capture evidence at report time, inside the session.


### DEC-V1-019 — Home Circle relations have two levels: the role, and the exact relation inside it

**Date:** 2026-09-21 · **Decided by:** Product owner · **Status:** Accepted

**Owner's words:** "I am looking for profile relation (mother, father, etc.), while relative is a role and inside we have exact relations." The existing `relationship_type` (parent / guardian / sibling / relative) stays the ROLE: it groups the circle into **Home** (parents, guardian, siblings) and **Relatives**, and is all any permission reads — unchanged, per the standing rule that only profile-viewing style and messaging vary by role. Migration 040 adds `relation`: the member's exact relation to the candidate — mother, father, brother, sister, guardian, grandmother, grandfather, father's-side uncle (chacha/tau; babai/pedananna), mother's-side uncle (mama; mavayya), father's-side aunt (bua; atta), mother's-side aunt (mausi; pinni/peddamma), cousin, brother-in-law, sister-in-law, family friend. The service derives the role from the relation, so the two cannot disagree. Rows from before 040 keep only their role and are never assigned a guessed relation; the candidate, or the member themselves, states it in place on the Members list, choosing only among the relations inside that row's role (a Parent row offers Mother / Father). The invite card asks "How are they related to you?" with the relations as chips in the two groups, nothing pre-selected.

**Also decided (2026-09-21), and built:** a parent (or any relation) may create a candidate profile for their son or daughter — the Shaadi.com "profile for: son / daughter" model — and the child takes it over on first sign-in.

- *Identity stays the platform's.* Mangaly asks the ForKhatri Identity & Trust Service to provision a member for the child's mobile number (`POST /internal/v1/members/provision`, identity level 0, no credential). A number that already belongs to someone who has ever signed in or has a password is refused ("ask to join their circle instead"); an untouched member provisioned earlier is handed back, so a failed attempt can be retried. The child's Mangaly account is created on that same id (migration 041), so when the child signs in with an OTP to the number the profile is simply theirs — nothing is re-keyed.
- *The creator is the circle's first member,* as their exact relation (DEC-V1-019 above), with the same `family_info` grant an accepted invitation gives.
- *Editing before takeover:* profile and photo requests carrying `X-Mangaly-Manage` run as the child only after `can_manage()` confirms the caller created that profile and the child has not taken it over. Every other path ignores the header. The candidate's own words (prompts, ten choices) return 403 to the creator even then.
- *Formal details are fully fillable by the parent,* as on a Shaadi.com parent-made profile, including a new formal **About** paragraph (`basics.about`) that families write on a biodata. The Details tab names the child ("What Rohit studied", "About Rohit", "Yes, living with them") instead of "you".
- *Takeover:* the child sees "Sunil Kapoor (Father) created this profile for you — Make it mine". After that only the child may edit; the creator stays in the circle.
- *Open:* incoming connection requests to a not-yet-claimed profile have no one who can accept them (the parent may send on the child's behalf, not accept). A "this isn't me" path for someone whose number was used without their knowledge.


### DEC-V1-020 — Requests: the candidate, mother, father or guardian may answer; everyone who may answer gets a popup; unused made-for profiles are removed after six months

**Date:** 2026-09-21 · **Decided by:** Product owner · **Status:** Accepted

**Answering requests.** Owner: "For profile requests there will always be a popup for the parent and the candidate — mother, father, candidate — and any one can accept." A request to a candidate appears as a popup, on every screen, to the candidate and to each member of their circle whose role is parent or guardian (a guardian stands in for a parent, DEC-V1-022). Whoever answers first answers for the family: the request stops being pending and leaves everyone else's popup. Siblings and relatives still see requests on the Circle screen but may not accept or decline (the API returns 403). The popup shows what that reader may see before a connection — the pre-connection-safe card (photo, age, city, education, work) and who sent it — and "View profile" opens the reader's own lens (biodata for a parent, candidate view for the candidate). The person who pressed the button is recorded (`decided_by_account_id`).

**"This isn't me".** The owner of a number that someone used to make a profile can remove it from the takeover banner, confirmed in place. The profile, its discovery entry, trust rows and circle are erased (migration 042); grants are revoked and requests withdrawn; the person keeps their own ForKhatri account; the maker is notified.

**Six months.** Owner: "we should delete unused accounts for almost 6 months." Applied to profiles made for someone who never signs in to take them over: the maker is told on day 173 ("removed in 7 days unless they sign in"), and on day 180 — never less than 48 hours after that notice, per DPDP Rules 2025 Third Schedule — the profile is erased and the platform member provisioned for the child is retired if nobody ever used it. Job: `mangaly-service/scripts/retire_unused_made_for_profiles.py` (dry run unless `--apply`). This narrows DEC-V1-010 for this one case only; accounts people actually use keep DEC-V1-010's windows.

**Open (needs the owner):** "A person who could create an account should always be an email, phone and photo verified person only." Phone is proven by OTP today; email is not separately verified on the platform; and photo verification (DEC-V1-016's live face match) has no capture flow yet and compares against profile photos — which a parent without a profile does not have. Decision needed on scope and on what a parent's photo check compares against.


### DEC-V1-021 — Discover is a photo wall; each candidate chooses what is shown openly

**Date:** 2026-09-22 · **Decided by:** Product owner · **Status:** Accepted

**Owner's words:** "Now focus on discovery! Few people like to share few things openly — let them have that. The Discover tab should be matured and well crafted, well-established UI/UX, so smooth." Earlier (DEC-V1-018): "I want to just scroll and see all the pictures… then select one."

**Discover.** A photo wall — two columns on a phone, up to five on a wide screen; the main photo and three short lines per tile; the profile opens on a tap. Tabs follow what established matrimony apps use, filtered through the baseline: Shaadi.com's Matches has Today's / My / New Matches, Near Me, Recently Viewed and Recent Visitors; Jeevansathi has Daily Recommendations and Just Joined. Mangaly keeps **For you · New · Near you · Saved** and deliberately has no visitor or view lists (the baseline rules out view counts and being watched). Search as you type; every filter the search supports, in one sheet grouped as a biodata is read, with a live count on the apply button ("Show 24 matches"); active filters as removable chips; skeleton tiles while loading; more people load before the end; returning from a profile restores the same tab, results and scroll position; a save (bookmark) on each tile; "Request sent" / "Connected" on the tile when true. "Suggest to {candidate}" moved from the Discover card to the profile page, where a parent has actually read the profile.

**Shown openly (migration 043).** Before any connection, every tile shows the main photo, age, city, education and work (unchanged, DEC-V1-016/020). A candidate may additionally open, each separately and closed by default: their **first name** (never the surname; contact is never openable), **all their photos**, and — already possible since 039 — individual **prompt answers**. Discover then shows "Divya, 29", a photo count and the first published answer as a quote; the pre-connection profile shows the first name and a strip of the opened photos. Only the candidate may change these (a parent filling a profile they created cannot); only searchable profiles show anything openly; photo access is enforced in the database (`is_openly_shared_photo`), not by the screen.


### DEC-V1-022 — "For you" is a set of titled rows, each face with one honest reason

**Date:** 2026-09-22 · **Decided by:** Product owner ("think smartly how we can use this discovery page — recommended to you, based on location, based on same tastes… research… you are free to innovate") · **Status:** Accepted

**Research.** Netflix's home is titled rows whose title is the explanation ("Because you watched…"), a disclosure that builds trust without exposing the algorithm. Bumble's Discover shows people with similar interests, goals and communities in common, refreshed daily. Tinder's Explore groups people by interests and intentions. Hinge's Most Compatible leads with mutual preferences; its Standouts ranks by attention — the one pattern not taken, since popularity weight is 0 by construction (DEC-V1-002).

**Design.** Discover has three tabs: **For you** (rows), **All matches** (the full searchable wall with every filter), **Saved**. The rows, each shown only when it has people and does not repeat a row above it:
Picked for you · Suggested by your family (the Home Circle's own picks — no dating app has this) · Close to home · Would move for the right person (other cities, open to relocating) · Same roots (mother tongue, community, native place) · Shares your way of life (interests or food) · Sees family life the way you do (same family-involvement answer) · In their own words (published answers) · New this month.
Every photo in a row carries one reason, a fact both people can check ("Also speaks Telugu", "You both enjoy trekking", "Suggested by your mother") — never a score. Rows compare only biodata a searchable profile already shows before a connection; prompts and the ten choices are never used (migration 039). A parent searching for a candidate reads every row and reason from their own seat: "Best matches for Varun", "Your family's picks for Varun", "In Hyderabad, like Varun", "You suggested this". "See all" on a row opens All matches with that row's filter applied. Endpoint: `GET /discovery/shelves`.


## Known technical debt (tracked, not blocking V1)

Per `06-impact-analysis.md` IA092: Mangaly is building its own interim account/credential system (FR092-FR095) because no Common Platform Identity & Trust Service exists yet, ahead of Mangaly in build order (ADR-016/017) — a fact FR092 itself already discloses honestly rather than silently. This is the correct and only viable choice given Mangaly's build-order position, not a mistake, but it creates a real, high-likelihood future obligation: whenever a platform-wide Identity module is eventually built, Mangaly's live candidate credentials and sessions will need migrating into it, and live credential/session migration is a genuinely high-risk operation class. Recording this now, explicitly, as a planned future migration rather than a surprise discovered later, is the entire value of naming it here — no action is required of V1 itself beyond building FR092-FR095 exactly as specified. **Credential hashing (2026-09-13, Step 8 note):** the interim `mangaly_identity.account.credential_hash` column names no algorithm in `schema.sql` — Step 9 must implement this using **Argon2id** (current OWASP-recommended default) or bcrypt with a work factor tuned to ~250–500ms verification cost, never an unsalted or fast general-purpose hash; this is a plain implementation instruction, not an open design question.

**Paid down 2026-09-14 (DEC-V1-015).** The platform Identity & Trust Service now owns credentials and sessions. Active Mangaly accounts were imported with their ids and Argon2id hashes (ForKhatri TR23), and Mangaly resolves the ForKhatri session instead of its own. The interim tables remain as dormant history (see DEC-V1-015's accepted trade-off); the interim routes answer `410`.

## Updates this file makes to already-Sealed files

Per this pipeline's append-only convention, `01-business-requirements.md`
and `02-functional-requirements.md` are not rewritten — each affected BR/FR's
own Confidence line gets one small addition pointing here, and nothing else
in either file changes. See the Revision history entries added to both files
for exactly what was touched.

### DEC-V1-023 — The Mangalyam palette: the page carries the colour

Owner, 2026-09-22: "I don't think we are actually representing Mangaly with [the colours]" and "background color is black and white … this looks like a 2017 year app, not a 2040 year app." Mangaly is named for the mangalyam, the thali tied on a turmeric-dyed thread (manjal kayiru). The palette is taken from a South Indian wedding and from ForKhatri's Brand Foundation (navy foundation, warm off-white, saffron accent, controlled green):

- **Paper:** turmeric-warmed ivory (#F8F0DF) in light, midnight navy (#121D3A) in dark. No page, bar or sidebar is white, grey or black.
- **Surfaces are tonal:** each is the paper with a little more of the one brand hue, so cards read as layers of one warm material.
- **Ink:** midnight navy. **Accent:** manjal turmeric (#E0A21B) as a fill with navy words on it, deep turmeric (#875500) when it is text.
- **Kumkum** red appears only as the small dot on the brand mark. **Pachai** green means verified or connected. **Peacock blue** marks family context.
- A single-hue lamp-light wash falls from the top of the page. No multi-hue gradients and no glass.

The same pass fixed what the screens showed a user: Home counted only circles the member helps in, so a candidate with three family members read "No one is helping yet"; the Messages list showed a nameless thread with the raw key "system.connected"; For you rows grew a gap under short tiles; Home's account controls sat on the left; the jaali behind the Home greeting read as grey boxes; the Next.js dev badge covered the Home tab.

### DEC-V1-025 — Face match verification and the maker gate

**Date:** 2026-09-22 · **Decided by:** Product owner (DEC-V1-016; the maker rule of 2026-09-21) with autonomous implementation · **Status:** Accepted
**Resolves in part:** the "Open (needs the owner)" note under DEC-V1-020

**Owner's rule:** "A person who could create an account [for someone] should always be an email, phone, photo verified person only."

**Built.**
- *Screen* `/me/verify` (`mangaly-web/app/me/verify/`): one explanation, one unbundled consent checkbox (purpose; the camera picture is discarded; withdrawable), then the camera (`getUserMedia`), an active liveness challenge (look straight, turn left and right in a random order, look straight), and a comparison of the live face with the member's own photos, all in the browser with `@vladmandic/face-api` (Tiny Face Detector for the challenge, SSD MobileNet v1 + 68 landmarks + the recognition model for descriptors; weights in `public/models/face-api/`). Each photo counts its closest face (group photos are fine); the result is the farthest of those, and the main photo must show a face. Only one number (that distance), the liveness flag and the number of photos compared are sent. The member sees "Photos confirmed as you · Sep 2026" or a kind retry message — never a number. Handled: no camera, permission denied, no face / more than one face, a main photo with no face, no photos, too many attempts. A quiet row on the Me screen links to it, or shows the fact with its month; it is not shown while a parent is filling in someone else's profile.
- *API*: `GET /verification/me`, `POST /verification/face-match` (body `consent: true`, `distance`, `liveness_passed`, `photos_compared`), `POST /verification/withdraw` (`app/api/routes/verification.py`, `components/trust/interface.py`). Always the signed-in person; `X-Mangaly-Manage` never applies.
- *Database* (migration 045): `record_face_match()`, `face_match_status()` and `withdraw_face_match()`, all SECURITY DEFINER and self-only (`is_self`); the new `mangaly_trust.biometric_consent` table (purpose, wording version, granted, withdrawn), read-only to the app role.

**Threshold.** The server decides: pass only when the liveness challenge passed, at least one photo was compared, and the distance is **below 0.45** — tighter than face-api's own 0.6 (Euclidean, 128-d). DEC-V1-016 sets the bias: a false accept puts a confirming badge on someone else's photos; a false reject costs a retry in better light. Attempts: **10 per account per day** (shared durable limiter, `face_match_attempt`).

**Retention.** Nothing biometric is stored anywhere — no frame, no descriptor, no distance. Kept: the `profile_facts` row (`source_category = 'face_match'`, `verified_at`, expiry) and the consent record. The confirmation **expires after two years** (faces and photos change; repeating a biometric check every season is its own privacy cost). **Adding a new photo removes it** (a trigger on `profile_media`): the claim is about the photos that were compared, and a picture added afterwards never was. A failed attempt writes nothing and does not remove a current confirmation.

**Consent.** Its own checkbox, never ticked in advance and never part of the sign-up terms. It is recorded on the first attempt, with the wording version (`2026-09-22`). Withdrawing stamps `withdrawn_at` — the record has to show that consent was given and when it ended, and it holds no biometric data — and deletes the confirmation.

**The gate.** `POST /profile/managed` answers 403 `{code: "verification_required"}` with a translated message unless the maker has a current face match, and it checks before anything is provisioned. Phone is proven by the ForKhatri sign-in OTP. `/profile/create?for=child` checks first and, when needed, offers "Confirm my photos", which returns to the create flow via `?next=`.

**Accepted limits (honest).** The comparison runs in the browser, so someone who edits the page's code or replays the request can claim a pass. The v1 answer is the strict server-side threshold, the rate limit, a revocable confirmation, and human review. Human review has a table (`admin_verification_request`) but no Operations screen yet, so today a member who cannot pass is told to write to support. An active head-turn challenge can be beaten by a good video replay (DEC-V1-016).

**Open.**
- *Email verification (platform blocker).* The ForKhatri Identity & Trust Service has no email verification. Mangaly does not build email sending; the "email" part of the owner's rule waits for the platform.
- *Parents without a profile of their own (needs the owner).* The face match compares against the maker's own profile photos. A parent with no candidate profile has none, so they cannot pass the gate and today cannot create a profile for their child. The screen says so plainly rather than sending them to make a candidate profile of themselves. The decision needed is what such a parent's check compares against, for example a verification-only photo of themselves.

### DEC-V1-024 — The families' group chat is an optional extra, opened by a candidate or a parent

**Date:** 2026-09-22 · **Status:** Accepted · **Migration:** 044

The families' conversation (both candidates plus everyone active in both Home Circles) is kept, not deleted, and every message names its writer and their relation ("Harish · father of Divya"). A candidate, a parent or a guardian may open it; siblings and relatives join once it is open. A parent reaches it through the conversation roster, because RLS keeps the connection row from them; the roster check itself requires the connection to still be accepted, so ending a connection closes the thread for everyone. A report made from any thread stores the thread as it stood at that moment, because the candidates' incognito session is deleted when it ends. The owner confirmed on 2026-09-22 that this group is an addition, not the parent chat (see DEC-V1-026).

### DEC-V1-026 — Three kinds of chat: incognito for the two candidates, ordinary one-to-one for everyone else, the families' group as an extra

**Date:** 2026-09-22 · **Decided by:** Product owner · **Status:** Accepted · **Migration:** 046

Owner: "we only offer incognito mode chat to candidate, and general chat for individual account like how chat present in Instagram / FB; now that we have option of family chat keep that as additional." This followed the owner asking "why do 8 people will be in chat?" when the families' group was presented as the parent chat.

- **Candidate with candidate:** the incognito session only. It is deleted when either person leaves it, or after 30 minutes with nothing written. The screen takes a night mood with a lock so nobody forgets which chat they are in.
- **Every other pair of people:** an ordinary, kept one-to-one chat (`kind = 'direct'`, no connection, one thread per pair). Mangaly is not an open network, so a direct chat needs a real link: the same family (a candidate and their circle, or two members of one circle), or the two families of an accepted connection. Never the two connected candidates, never anyone blocked. Sending re-checks the link, so a block or leaving a family stops new messages while the history stays readable.
- **The families' group:** unchanged, optional (DEC-V1-024).

The Messages screen became one inbox for all three, two panes on a desktop and full-screen threads on a phone, with "New message" listing the people you may write to by family.

**Still open:** the face-match gate for making a profile for someone else cannot be passed by a parent who has no profile of their own, because the check compares against the maker's own photos (DEC-V1-025). The owner decides what such a parent's check compares against.

### DEC-V1-027 — Every account has its own Mangaly "My profile"; a parent's face check compares against it

**Date:** 2026-09-22 · **Decided by:** Product owner · **Status:** Accepted · **Migration:** 047

Owner: "they need to sign up properly in ForKhatri and log into Mangaly, then only they can start a profile building for their child" and "basic authentication of login happens in ForKhatri and each module has its own way of my profile."

- Sign-up, login and the phone check stay in ForKhatri. Signed-out people are sent to the ForKhatri sign-in, and the Mangaly API refuses to make a profile without a ForKhatri session.
- An account without a candidate profile (a parent, sibling or relative) now has a Mangaly "My profile" of its own: one photo of themselves, a line about them, city and work, the families they belong to with their exact relation, and the profiles they made for a child. It is never searchable and has no biodata.
- Their photo is shown to the people Mangaly lets them message (their own family, and the families of accepted connections), on chats, the "New message" list, circle members and the account button.
- The face check for such a member compares the live capture against this photo, and a new photo removes an earlier confirmation. This lifts the block recorded in DEC-V1-025 and DEC-V1-026: a parent adds their photo, passes the check, then makes their child's profile.

### DEC-V1-031 — The AI matching engine: the family's own words, 1–10 scales, and a score that is never shown

**Date:** 2026-09-27 · **Decided by:** Product owner · **Status:** Accepted · **Migration:** none (profile attributes and the Discovery snapshot)

**What the owner asked for.** The owner found preference forms, filters and even Hinge-style "must have / nice to have" switches "old school". They asked for both of these together: AI matching from the family's own words, and 1–10 scales that the member gives, "on bride or groom preference and also about themselves", to help the matching engine. They also showed Shaadi.com's "What she is looking for" panel ("You match 7/10 of her preferences") and asked that Mangaly do better.

**Research.** In 2026, newer apps replace preference screens with an AI matchmaker the person talks to (Ditto, Known, Palaura, and Joey, which works by phone call); Hinge reports 15% more matches from its AI recommendations. Hinge's dealbreaker hides everyone who left the field blank, and that is the known flaw of hard filters. OkCupid's "answer, acceptable answers, importance" is the proven pattern for two-sided importance. A displayed match number steers people whether it is right or not: OkCupid's 2014 experiment told poor matches they were a 90% match, and they messaged more anyway.

**Design.**
- **Own words.** The family types or speaks what they want in English, Hindi or Telugu (`/me/matchmaker`). If an API key is configured, Claude reads the words (`components/compatibility/understand.py`). It receives only the typed text, never a name or profile, and its structured answer is validated against the engine's closed vocabulary (`config/matching_engine.py`). Without a key, a built-in keyword reader does the same job. Each point shows the words it came from and an importance from 1 to 10 that the family can slide. 10 means the point must be met. Nothing is saved until the family presses Save.
- **The 1–10 scales.** There are six: faith and rituals, outlook, family life, career, social life and active life. Each member rates themselves (candidate only, per DEC-V1-019), and rates what they want in a partner along with how much it matters. These deliberately do not repeat the ten outlook choices of DEC-V1-017. They are private: only the engine reads them, and no endpoint returns them to anyone but their owner.
- **The engine** (`components/compatibility/engine.py`) replaces DEC-V1-002's fixed formula.
  - For each direction it takes an importance-weighted average of: how well the other person meets each wish (diet compatibility table; education and income as floors; smoking and drinking as ceilings; age and height with a gentle fall-off; place by distance from coordinates, with a floor for anyone willing to relocate); how close their self-ratings are to the wanted values; and two implicit terms, a shared kitchen and distance.
  - The two directions are combined by harmonic mean (DEC-V1-030), and profile evidence breaks near-ties. The result is a 1–10 score.
  - A must-have removes someone only when their stated fact clearly misses it, and it applies both ways. A blank never removes anyone.
  - Popularity weight stays 0.
  - People who have not used the matchmaker yet are scored on their older partner-preference fields, read at default importance.
- **The score is never shown** (baseline §3/§4.8, PRODUCT-GUARDRAILS). It orders Discover. Members see only a word, "Strong match" (8 and above) or "Good match" (7.5 and above; both set from the real spread of development pairs so the word stays selective); below that no word is shown, never "weak". The number no longer leaves the server: the member-facing search and shelf responses dropped their `score` field.
- **"How you fit each other"** on every profile, for the candidate and for their family from the candidate's seat. It lists each of the reader's own wishes as met, close, different or not shared, with must-haves marked. For the other person's wishes it shows only the topics the reader meets. Their values, their misses and how many wishes they have stay private (FR020). There is no fraction and no percentage, unlike Shaadi's "7/10".
- **Also:** smoking and drinking became biodata fields in Lifestyle, and a "nearby" reason ("In Secunderabad · about 10 km away") replaces treating a neighbouring city as a miss.

**Not taken (with reasons given to the owner):** learning from swipes or clicks (no data yet, and it would break DEC-V1-002), chat-speed matching (it would break the incognito chat promise), Spotify and Instagram links (the data is no longer available to new apps), college tiers, and "neighbouring community" lists.

### DEC-V1-035 — Onboarding redesign: the parent is never blocked, the child's number is optional, the face check is an optional trust step

**Date:** 2026-10-06 · **Decided by:** Product owner (Q1, Q2) and autonomous decisions D1–D17 (`ONBOARDING-REDESIGN-2026-10.md` §6/§8) · **Status:** Accepted
**Changes:** DEC-V1-019 (the child's number), DEC-V1-025 (the maker gate). DEC-V1-001 (one photo to save a profile; the tiers) is unchanged. Numbers 032–034 are used by code comments for assisted matching and agents and are not re-used here.

**Owner's words.** On the shared-phone daughter (Q1): "yes, right — the parent is doing it, then he should be able to." On a Samaj-office or video-call fallback for parents whose camera will not start (Q2): "why would that much, is this an app or what?" On the biodata reader (Q3): one clear consent line before reading; the file is deleted after reading unless the family attaches it. On checking: "check only in one language for now."

**Decided.**
- *A parent may publish a son's or daughter's profile without the child's own mobile number.* The profile is kept under the parent's account and shown as managed by the parent ("managed by her mother") until the child joins. The number is optional, asked as "add your son's/daughter's number so they can take over later". When the child later signs in with that number they are asked "is this you?"; on yes the profile becomes theirs and their consent is recorded (`account_alias.consented_at`). A number that already belongs to a ForKhatri member is no longer a dead end: the profile is managed and that member is asked the same question. Migration 065 holds the data model: `account.managed_by_account_id`, `profile.pending_phone`, `account_alias`, and the SECURITY DEFINER functions `create_managed_account`, `set_pending_phone`, `made_for_my_number`, `take_over_profile`, `not_my_profile`, `alias_of`. The 041 path (a free number → the platform provisions the member) keeps working unchanged for existing data.
- *The live face check is an optional trust step,* never a gate before creating or publishing a child's profile. It earns the "photos confirmed" mark on My profile (its own optional card, D15). No Samaj-office or video-call fallback is built. If the camera cannot start the screen says so plainly, the draft stays on the device, and "Try again later" is offered; nothing is lost.
- *D1–D17 as written in the redesign document,* in short: "Just look around first" (Discover with bride/groom chosen, no requests until a profile exists); a three-card story; "My sister or brother"; the who-for → About (name, three date-of-birth dropdowns with the age rule checked there, gender) → Where (place search) → Photos (several at once, or "add later" as a device draft) → Work and studies (skippable; Diploma and Professional added, "Other" opens a text box; relocation is Yes / No / Can discuss) → Check and publish (for someone else). Every step is saved on the device (IndexedDB, photos included) and resumed; nothing about a child reaches the server before publish. "Start from a biodata" reads a PDF or image into the closed field list after consent (Claude when a key is configured; otherwise attach and type), the family checks each line, and the file is kept only if attached (`profile_document`, owner-only). The setup matchmaker is one short card; "Read my words" adds and never removes; the horoscope theme is hidden until a chart exists. "Next up" is the easiest missing answer. Rashi is a dropdown; unknown-time matches are labelled provisional. Removed photos' files are deleted.

**Built on 2026-10-06/07.** All of the above on the web side and the API additions (`/profile/biodata/reader`, `/profile/biodata/read`, `/profile/documents`, education `diploma`/`professional`/`education_other`), plus migration 065 applied to the development database.

**Still to apply (needs the owner's hand).** The two-line change to `POST /profile/managed` itself — making `child_phone` optional (managed account via `create_managed_account` when absent or already taken; `set_pending_phone` after the circle is made) and dropping the `is_face_verified` refusal — was refused by the build session's permission system as a security weakening, twice. Until it is applied the wizard asks the child's number and the maker's check on the "Check and publish" step (D4/D5 as first written), after all the work is done, so the parent is no longer stopped at the first tap; the owner's Q1/Q2 answers take effect the moment that endpoint change lands. The rollback of the unused 065 objects was likewise refused, so they stay in place, unused and harmless.

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
