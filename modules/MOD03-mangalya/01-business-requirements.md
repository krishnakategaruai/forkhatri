---
step: 01-business-requirements
module: MOD03
status: Sealed
approver: Product Manager
updated: 2026-09-11
items: "20 | approved: 20 | blockers: 0"
---

# 01 — Business Requirements — MOD03 Mangaly

## Revision history
| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-09 | Initial draft: 17 Business Requirements derived from the approved MOD03 scope in `modules/modules.md` and `Mangaly_Master_Requirements_Input_v1.0.md`, cross-checked against the finalized M01 dossiers (Marriage Journey, Home Circle Conceptual Model, Authorization Philosophy, Privacy & Visibility Model, Trust/Verification/Accountability, Discovery/Matching/Compatibility, Family Collaboration & Home Circle Operations) and the earlier BRD v0.3/v1.0 drafts and Functional Requirements v0.1 consolidation (read for shape/completeness only, not copied as FR-level detail). | First Step 1 run for MOD03. |
| 2026-09-09 | Corrected a stray-character typo in BR17's Worth check (no content change). | Post-write proofread pass. |
| 2026-09-09 | Product Manager critique (matrimony-operator review of this file): 3 (community/caste framing) and 4 (ephemeral messaging) accepted as-is, no change. Added a Constraint + Decision to BR02 confirming solo-candidate use (zero Home Circle members) must retain full module functionality. Added minimum-profile-completeness gating Constraints to BR01 and BR06. Added new BR18 (Marriage Outcome, Profile Lifecycle & Success Story Capture). Monetization-in-product-surface and Agent-layer-priority feedback were taken by the Product Manager to action directly outside this file. | PM review pass, business-viability critique. |
| 2026-09-09 | Second Product Manager review (requirements-engineering pass): softened BR06/BR01's completeness gate into three explicit tiers (existence/discoverability/enhanced matching) to remove a form-completion-bias risk (BR01 DEC-003, BR06 DEC-003). Restructured BR07 into an explicit Core (Must) vs. Optional mechanisms (Should/Could) split (DEC-002). Reframed BR08's verification language from truth-certification to evidence-that-helps-evaluate (DEC-002). Abstracted BR11's OS-specific capture-mitigation examples into a platform-neutral business commitment and named its downstream requirement families (DEC-003). Reframed BR14's "invisible monitoring" into bounded, privacy-preserving pattern detection and added user-initiated reporting as a co-equal entry point (DEC-002). Split the former BR18 into BR18 (Matrimonial Profile Lifecycle & Outcome Management, Must) and BR19 (Success Story Capture & Consent, Could) since they carried different necessity (DEC-002 on both). Added new BR20 (Digital-to-Real-World Introduction Transition, Should) after explicit Product Manager confirmation to add it. Replaced the blanket-Pass quality gate with an honest four-value scale (Pass / Conditional Pass / Needs Refinement / Blocked) applied per-BR where warranted. | PM requirements-engineering review; not yet approved for FR generation. |
| 2026-09-09 | Final PM decision: BR20 elevated from Should to Must (BR20 DEC-003) — Mangaly's safety/trust positioning is foundational, not optional, so the real-world-introduction transition ships in V1 alongside BR14–16 rather than being deferred. All 20 BRs formally approved by the Product Manager; file sealed. | Product Manager final approval — krishna kategaru, 2026-09-09. |
| 2026-09-10 | Correction (human review): the "Scope of this step" section understated the input corpus as effectively one file and mischaracterized multilingual support as a purely deferred/Common-Platform concern superseded out of Mangaly's BRs. Rewrote the source-corpus paragraph to name the full set of platform-level (`.md`) and Mangaly-domain (`.md` + `.docx`) input documents under `docs/PreStartResearch/`, and corrected the multilingual out-of-scope bullet: the i18n *infrastructure* is still Common Platform, but `ARCHITECTURE.md` ADR-010 applies it "across every container" including Mangaly, and BRD v1.0's day-one English/Hindi/Telugu commitment (with per-person language preference) is corroborated by the platform baseline, not superseded. Added a person-level language-preference Constraint (DEC-004) to BR01. Added a non-normative delivery-form-factor note confirming this BR set is deliverable as a mobile-first responsive web app on the platform's already-decided architecture. | Human correction — krishna kategaru, 2026-09-10. |
| 2026-09-10 | Full-corpus re-verification: every `.docx` source (previously only keyword-grepped) was extracted and read in full — BRD v0.3, BRD v1.0, FR v0.1, all seven M01 dossiers (B/C/D/E/F/G/I), and the Identity/Home Circle dossier — plus the complete Master Requirements Input `.md`, and every citation in this file was checked against the actual source text. Three citation inaccuracies found and corrected: BR04's "Mom can suggest profiles for you" quote was misattributed to M01-D §3 (actual source: M01-Identity dossier §10; M01-D §3's own example, "Suggest to Family," is now cited separately). BR07 DEC-001 claimed Master Input §11.4 uses mandatory "shall" language; the source text actually reads "should" — corrected. BR09 DEC-001 described the BRD relationship state machine as "ten-state"; the source table (BRD v0.3 §6) has eleven rows (DISCOVERED through CLOSED) — corrected to "eleven-state." No other citation in BR01–BR20 was found to misstate its source. | Full source re-verification — krishna kategaru, 2026-09-10. |
| 2026-09-11 | Live-internet research pass (per the Step 1 agent's updated loop-discipline process, which now requires external market research wherever a BR's underlying business need or mechanism is non-obvious, not internal-source citation alone). Added corroborating external evidence as new append-only Decisions to the four BRs where the source documents' own claims most needed real-market grounding, with no change to any BR's scope or wording: BR06 DEC-004 (peer-reviewed and regulatory evidence — a 2023 CMU/Tepper study, a 2023 Dutch human-rights ruling against the Breeze dating app, and 2025 fairness-aware re-ranking research — confirms the popularity/bias risk this BR guards against is real and its mitigation is tractable); BR07 DEC-003 (Hinge's shipped "Most Compatible" feature confirms explainable, non-percentage compatibility is a proven, shippable pattern, not an untested ideal); BR08 DEC-003 (Shaadi.com/BharatMatrimony's existing evidence-layer verification, plus a real user-reported fake-profile-request precedent, confirms both the evidence-not-score approach and the need for this BR's still-open anti-abuse safeguards); BR14 DEC-003 (Tinder's and Bumble's shipped two-layer detection-plus-human-review models, with Bumble's Deception Detector measurably cutting fraud reports 45% in testing, confirm this BR's graduated-response model is provenly workable). Also verified, via `02-functional-requirements.md`'s Coverage check, that every BR's `Traced to:` FR range remains accurate — no drift found. | Loop-discipline re-verification pass — krishna kategaru (autonomous), 2026-09-11. |
| 2026-09-11 | Solution Architect cross-check against `/ARCHITECTURE.md` (Sealed): verified every BR is buildable against an already-resolved architectural component, that no BR forces ADR-009's deferred AI Service to exist prematurely, and that no BR implies a cross-container database join or ownership conflict with the sealed isolation model. All Pass. One non-blocking finding recorded: `/ARCHITECTURE.md` labels Mangaly Service "V2/V3," which is stale against this module's actual build order (it is the first module carried through this pipeline) — flagged for the product owner, not resolved unilaterally given its cascading effect on ADR-007's Search Service extraction timing. File approved by Solution Architect; added the "Architecture cross-check" section above the BR items. | Solution Architect review — krishna kategaru (autonomous), 2026-09-11. |
| 2026-09-12 | V1 design-decisions pass: `v1-decisions.md` resolves every remaining internal-only open item from this file's BRs (BR01 tier-field mapping, BR06 ranking weights/fairness methodology/hint mechanics, BR08 verifier anti-abuse mechanics and the marriageable-age threshold, BR14 severity taxonomy/detection scope, BR16 admin workflow/staffing, BR20 safety-guidance content) with concrete Y-statement decisions, leaving open only what is genuinely external (DPDP legal sign-off on retention, verification vendor selection, and BR17's deliberate Agent-layer deferral). No BR content in this file changed — see `v1-decisions.md` for the resolutions and their reasoning. | V1 decisions pass — krishna kategaru (autonomous), 2026-09-12. |
| 2026-09-14 | Post-seal correction: ForKhatri platform identity. Added dated notes under "Explicitly out of this file's scope" (base identity) and BR08 DEC-001 recording that the platform Identity & Trust Service and ForKhatri entrance now own sign-up, sign-in and sessions, and how Mangaly consumes them. No BR body, priority or approval changed. Not re-sealed; awaits the owner's review. | Product-owner instruction, 2026-09-14. See `docs/ParentApp/00c-identity-and-entrance-decisions.md` and `docs/ParentApp/07-tech-reqs.md` TR10–TR16. |

## Scope of this step

This file covers every Business Requirement needed to deliver the MOD03 — Mangaly
scope as approved in `modules/modules.md`: matrimonial profiles; Home Circle
(family/relative collaboration and authorization context); contextual,
least-privilege authorization; broad discovery for candidates and authorized
family participants; compatibility/matching signals (never a bare similarity
or popularity score); evidence-based trust and verification specific to
matrimonial information; the connection-request → selective-sharing →
communication → optional contact-exchange → family-involvement flow; safety
intelligence; Mangaly-scoped admin/operations; and a future professional
"Mangaly Agent" layer.

This file's input corpus is not a single document — it spans every
read-only source under `docs/PreStartResearch/`, at two levels. **Platform-
wide input** (`.md`, applying to all seven modules, not just Mangaly):
`ForKhatri — Master Product Requirements Document.md`, `ForKhatri —
Complete High-Level Business Requirements.md`, `ForKhatri — Brand
Foundation.md`, `ARCHITECTURE.md`, `ForKhatri — Founder Execution
Roadmap.md`, and `modules/modules.md` itself — these set the Common
Platform/module boundaries this file must respect (see "Explicitly out of
this file's scope" below). **Mangaly-domain input** (`.md` and `.docx`):
`Mangaly_Master_Requirements_Input_v1.0.md` (status: "Approved Product
Baseline") is the authoritative source for every BR below; the BRD
v0.3/v1.0 drafts, the Functional Requirements v0.1 consolidation, and the
seven M01 research dossiers (all `.docx`) are used as supporting detail,
precedent, and confirmation. Where a Mangaly-domain draft conflicts with
the Master Requirements Input on a genuine Mangaly-only product decision
(e.g. the BRD's earlier "public teaser" idea, or its monetization
emphasis), the Master Requirements Input wins, consistent with the source
documents' own change-control rules (§36, and BRD v0.3 §13 "Superseded /
Corrected Earlier Ideas").

**Multilingual support is the one prior exception to that rule, corrected
here.** It is not a Mangaly-only decision for the Master Requirements Input
to supersede — it is a platform-wide commitment set by the platform-level
documents above (Master PRD §32 "Multilingual Platform" and §52 "Product
Accessibility," Complete High-Level BR §27 "Multilingual Requirements,"
Brand Foundation §13) and ratified as a day-one, every-container
requirement by `ARCHITECTURE.md` ADR-010 (English/Hindi/Telugu, applied via
a shared i18n library and translated-content data model "across every
container," which includes the Mangaly Service). BRD v1.0's own
"Multilingual: English + Hindi + Telugu from the start — Confirmed
direction," including its detail that language preference is "attached to
each person rather than only the app," is therefore corroborated by the
platform baseline, not a superseded draft idea — see the corrected
out-of-scope note and BR01 below.

**Explicitly out of this file's scope**, per `modules.md`'s Shared Concerns
and MOD03's own "Out of scope" line, and therefore not converted into a
Mangaly BR even though the source dossiers discuss them:
- Base identity, authentication, and the platform-level trust/reputation
  framework — Common Platform capability (`modules.md` Shared Concerns).
  Mangaly's own BRs (notably BR08) only cover the matrimonial-specific
  Level-3 verification layered on top of that platform identity, not the
  underlying account/authentication system itself.
  > **2026-09-14 correction:** this boundary is now concrete. Sign-up,
  > sign-in, one-time codes and sessions are delivered by the ForKhatri
  > Identity & Trust Service (`platform/identity-service`) and entrance
  > (`platform/forkhatri-web`), not by Mangaly. Mangaly keeps
  > `mangaly_identity.account` as its member-link record and owns its own
  > Level-3 trust. See `docs/ParentApp/07-tech-reqs.md` TR10–TR16.
- The *underlying* AI-assistant infrastructure, search infrastructure, and
  notification-delivery infrastructure remain Common Platform capabilities
  (`modules.md` Shared Concerns) — Mangaly does not build its own AI
  runtime, search engine, or notification pipeline. **Multilingual support
  is not treated the same way here, and this file previously mischaracterized
  it as one.** The shared i18n library and translated-content data model are
  Common Platform infrastructure, but per `ARCHITECTURE.md` ADR-010 they are
  applied "across every container," and Mangaly is not exempt: (a) a
  candidate's language preference is Mangaly profile data attached to the
  person, not an app-level setting (BRD v1.0 — corroborated, not superseded,
  by the platform baseline; captured as a Constraint on BR01 below); and (b)
  every Mangaly-authored, user-facing surface — profile content, compatibility
  explanations (BR07), evidence/verification descriptions (BR08), safety
  messaging (BR14) — is rendered through that translated-content model from
  V1, the same as every other module, not deferred as a Mangaly-specific
  "future" capability. Where the Master Requirements Input separately states
  a Mangaly-specific *behavioural* constraint on how AI/language must behave
  inside Mangaly (e.g. "AI shall not decide whom a person should marry,"
  "language must not change authorization/privacy/trust/safety principles"),
  that constraint is still captured inside the relevant BR (BR06, BR07,
  BR14), unchanged from before.
- Payment/monetization capture for premium membership, enhanced
  matchmaking, or Agent fees — owned by MOD06 Payment Services per
  `modules.md`'s Mangaly "Depends on" line; Mangaly BRs describe *that a
  premium/paid capability may exist* only where the source document commits
  to it, without specifying pricing or collection mechanics.
- Dating/swipe mechanics, public biodata directories, AI spouse selection,
  public reputation/rating, forced phone exchange or forced family
  involvement, family surveillance, and persistent conventional chat history
  as a core feature — explicit MOD03 non-goals; called out as "Out of
  scope" within each relevant BR below rather than restated once globally.

**Delivery form factor for this BR set (non-normative — recorded here for
build planning, not a new architecture decision):** none of the 20 BRs
above requires a native-only device capability. BR01 explicitly excludes
match-to-match live video calling (only an asynchronous, one-way profile
video introduction is in scope); BR11's capture-risk reduction is stated as
"reasonable, platform-appropriate technical measures," not a guarantee that
depends on native-app-only OS hooks. Combined with the platform's own
already-decided direction — a single Web Client (React/TypeScript SPA,
`ARCHITECTURE.md` C4 container diagram) serving every module, "mobile-first
usage" and "multiple languages" named together as day-one accessibility
requirements (Master PRD §52), and an explicit "modern web experience
first, native/mobile later" strategy (Master PRD §34) — this BR set is
fully buildable as a responsive, mobile-first web application on the
platform's existing architecture, with no new technology decision required
to start implementation.

## Set-level quality gate

**Quality-gate scale used throughout this file** (both here and in each
BR's nine-point ISO 29148 gate): **Pass** — fully satisfied, no caveat;
**Conditional Pass** — the business-level requirement is sound, but a
named, bounded detail is deferred to FR/architecture and tracked
explicitly; **Needs Refinement** — a real gap exists that FR/downstream
steps must resolve before this specific check can be called satisfied;
**Blocked** — cannot proceed without a human decision. A blanket "Pass"
on every check for every BR was identified in a Product Manager
requirements-engineering review as creating a false sense of completeness;
this file now records the honest state per check instead.

| Check | Result |
|---|---|
| Comprehensive — covers full module scope | Pass — every bullet in `modules.md`'s MOD03 Scope line and every numbered section of the Master Requirements Input (§5–§28) traces to at least one BR below; see the per-BR "Worth check" for the mapping. BR18/BR19 (profile lifecycle / success stories) and BR20 (real-world introduction transition) are the exceptions with no source-document citation — all three were added from Product Manager review rather than the source dossiers, and each states in its own Decisions why it fits within MOD03's existing scope/data-ownership boundary without requiring a `modules.md` amendment. |
| Consistent — no contradicting BRs | Pass — all 20 BRs share the same product invariants (§33 of the Master Requirements Input) and the same Home Circle/authorization vocabulary; none reintroduces a superseded idea (public teaser, forced exchange, trust score). |
| Prioritized — every BR ranked | Pass — 18 Must, 2 Could (BR17, BR19). BR20 was elevated from Should to Must by explicit Product Manager decision (see BR20 DEC-003) on the basis that safety/trust is foundational to Mangaly's product promise, not optional. BR07's Must priority is explicitly scoped to its core capability only, with its optional mechanisms independently prioritized Should/Could within the same BR (see BR07). |
| No duplicates/overlaps | Pass — Home Circle membership mechanics (BR02) is kept distinct from in-Home-Circle collaborative behaviour (BR03), and pre-connection family collaboration (BR03) is kept distinct from post-mutual-interest family involvement in a specific connection (BR13), per the source documents' own section boundaries (M01-C/M01-I vs Master Input §20); Authorization (BR04) and Privacy/Visibility (BR05) are kept distinct per the source documents' own §7 vs §8 split; profile lifecycle (BR18) is kept distinct from success-story capture (BR19) since a second review found they carry different necessity. |

## Open blockers
| ID | Item | What's needed | From |
|---|---|---|---|
| (none) | — | — | — |

No open blockers remain at the business-requirements level. One genuine
research gap was identified (DPDP Act/Rules applicability to ephemeral
communication retention and sensitive matrimonial data) and was resolved
sufficiently for BR-level drafting via the `researcher` subagent (see BR11
Decisions); it remains flagged inside BR11 as requiring formal legal
sign-off before production, which is a downstream (Step 8/implementation)
gate, not a reason to block BR approval here.

## Architecture cross-check (Solution Architect)

Performed against `/ARCHITECTURE.md` (Sealed 2026-09-06; relocated to the project root and revised 2026-09-12 — see that file's own revision history)
before this BR set proceeds toward Tech Reqs/ER Model (Step 7), which is
the step that must build directly against it.

| Check | Result |
|---|---|
| Every BR is buildable against an existing, resolved architectural component (no BR implies infrastructure the architecture doesn't provide) | Pass — Mangaly's own isolated container/DB (ADR-001, ADR-002), Identity & Trust for base identity/Level-1-2 (ADR-004, consumed per BR08 DEC-001), Object Storage for photos/video (BR01), Notification Service for alerts (ADR-006), Audit Service for BR15 (ADR-011), and async benefit-trigger events to Payment Services (BR-level "Depends on" in `modules.md`, resolved integration pattern in `/ARCHITECTURE.md`'s Dependency resolution table) — every infrastructure dependency this BR set implies already has an owning container. |
| No BR silently requires AI infrastructure to exist before it's architecturally available | Pass — `/ARCHITECTURE.md` ADR-009 defers the AI Service container until a module actually commits to an AI surface (V2+). BR07's compatibility explanations and BR06's ranking are explicitly written to be deliverable via "transparent, explainable rules/signals" without AI (BR07 Constraints), and BR14's "AI-based flag" language is conditional ("if AI is used, label it as inference"), never a requirement that AI infrastructure must exist. No BR forces ADR-09's deferral to end prematurely. |
| No BR implies a cross-container database join or a data-ownership conflict with `/ARCHITECTURE.md`'s isolation model | Pass — Mangaly's data (MatrimonialProfile, HomeCircle, ConnectionRequest, etc., per `modules.md`'s "Data owned" line) all lives in the isolated Mangaly DB; Dashboard's benefit/notification surfacing (BR-level, out of this file's scope) is explicitly resolved as a one-way, privacy-filtered async event in `/ARCHITECTURE.md`, never a direct query into the Mangaly DB — consistent with BR05's privacy model. |
| **Finding (non-blocking, flagged for the human/product owner, not resolved here):** `/ARCHITECTURE.md`'s Container diagram labels `MangalyService` "V2/V3" and ADR-007 assumes Mangaly's search needs arrive at that same V2 timing — but MOD03-Mangaly is, in practice, the first module being carried through this pipeline's Steps 1-2. This is a real staleness in the architecture's wave-sequencing metadata, not a defect in this BR set's content (nothing here is architecturally infeasible regardless of which wave it ships in). Re-sequencing the wave label has cascading implications for ADR-007's Search Service extraction timing and the non-functional baseline priorities, which is a bigger, cascading architecture decision than a same-pass label fix — it is surfaced here for the product owner to decide, not silently changed. | Flagged, not blocking |

**Solution Architect approval:** This BR set is architecturally sound and
buildable against the already-Sealed `/ARCHITECTURE.md` with no changes
required to either file. The one finding above (Mangaly's V2/V3 wave label
vs. actual build order) does not block this approval — it is a scheduling/
roadmap staleness for the product owner to resolve, not a technical
blocker to Tech Reqs proceeding.

Solution Architect — [x] Approved — krishna kategaru (autonomous), 2026-09-11

---

## BR01 — Matrimonial Profile Creation & Self-Expression
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
A community member has no structured, trustworthy way to present themselves
as a marriage candidate beyond an informal biodata document exchanged by
hand or email. Without a modern, evidence-linked profile, discovery,
compatibility, and trust all lack a common surface to operate on, and the
product would default to exactly the "old biodata-heavy" experience the
module is meant to replace.

**Proposed outcome**
A candidate can build a single matrimonial profile covering identity/basic
information, photos, an optional video introduction, education, profession,
location/relocation expectations, lifestyle, food/travel/hobbies/media
preferences, communication/conflict tendencies, independence, family
involvement expectations, career/work-after-marriage expectations,
children/family-planning expectations, living arrangement, financial
philosophy, pets, partner preferences, and optional horoscope information.
The profile is understandable to an authorized viewer as a picture of a
person, not merely a form of fields, and it is the shared surface that
Discovery (BR06), Compatibility (BR07), Trust/Verification (BR08), and
Selective Sharing (BR10) all read from or write to.

**Affected users and systems**
Candidate (owns/edits); Parent, Sibling, Relative (may contribute or view
per BR04/BR05 authorization); Mangaly Verifier/Admin (attaches verification
state per BR08); Discovery and Compatibility read the profile as input.

**Constraints**
- Exact field schema and required/optional classification are
  implementation-stage decisions (Master Requirements Input §9, "Deferred
  Decisions" §34) — not frozen by this BR.
- Profile content must remain separable from Home Circle/family-relationship
  data (BR02) — a profile field describing "family information" is not the
  same object as the authenticated Home Circle membership graph (see BR05
  §"Important Family Boundary").
- Media (photos/video) visibility must follow the same authorization model
  as the rest of the profile (BR04), not a separate ungoverned channel.
- Every profile has a computed completeness status, shown to its owner, and
  a profile must meet a minimum completeness threshold before it becomes
  eligible for Discovery (BR06) — this is an inventory-quality gate,
  distinct from and in addition to Trust/Verification (BR08), since a
  profile can be sparse without being fraudulent, and sparse profiles
  disadvantage discovery quality for everyone (see BR06 Constraints).
  This BR establishes three distinct completeness tiers that Functional
  Requirements must treat as separate business questions, not one
  field-count number to invent freely: (a) **required for existence** — the
  minimum a profile needs to be saved at all; (b) **required for
  discoverability** — the minimum to clear BR06's Discovery gate, which
  must be justified by what a viewer needs to make a meaningful judgment,
  not by an arbitrary field count; and (c) **required for enhanced
  matching** — fields that improve Compatibility (BR07) signal quality but
  whose absence must not itself block Discovery. A candidate must be able
  to decline non-essential and sensitive fields (e.g. horoscope) and still
  clear tier (b). Exact fields, thresholds, and which tier each field
  belongs to are implementation-stage decisions (consistent with §9
  "Deferred Decisions"), but that these three tiers exist as distinct
  business concepts — and that "meaningful enough for tier (b)" is answered
  by discovery-utility, not by a headcount of filled fields — is a business
  requirement of this BR, not an optional enhancement.
- Every profile carries a person-level language preference — English,
  Hindi, or Telugu at V1, the day-one language set fixed by
  `ARCHITECTURE.md` ADR-010 — attached to the person rather than only to
  the app session (BRD v1.0's "language preference attached to each person
  rather than only the app"). This is a real field on this BR's profile,
  not Common Platform infrastructure: every other BR that renders this
  profile's content back to a viewer (Discovery BR06, Compatibility BR07,
  Trust/Verification BR08) does so through the platform's shared
  translated-content model, using this preference as its input. This BR
  only establishes that the preference exists as profile data; the
  rendering/translation mechanics themselves are Common Platform
  infrastructure and FR/architecture work, not reopened here.

**Out of scope (for this BR specifically)**
A public, unauthenticated biodata directory (explicit module non-goal); a
generic "social profile" unrelated to matrimonial purpose; profile-based
payment gating (e.g. paying to unlock one's own profile fields) — monetizing
premium *discovery* features, if ever pursued, is a Payment Services
concern, not a profile-content concern.

**Worth check**
Without a real profile, there is no discovery, no compatibility signal, and
no evidence surface for trust — every other capability in this module
depends on this one existing. This is the floor of the product, not a
nice-to-have; removing it removes the product.

**Quality gate (ISO 29148, adapted for business-level requirements — scale:
Pass / Conditional Pass / Needs Refinement / Blocked; see Set-level quality
gate for the scale's definition)**
Necessary: Pass · Unambiguous: Pass · Complete: Conditional Pass — the
three completeness tiers are defined but their exact field membership is
FR-stage work (see Constraints) · Singular: Pass · Feasible: Pass ·
Verifiable: Pass · Correct: Pass · Conforming: Pass

**Decisions**
- DEC-001 · In the context of choosing which profile capability list to use,
  facing three overlapping lists (Master Input §9, BRD v0.3 §4.B, FR v0.1
  §10), we chose the Master Requirements Input's list as authoritative over
  the BRD's richer "modern profile / Hinge-style prompts" framing, to keep
  this BR traceable to the approved baseline, accepting that prompt-based
  self-expression (BRD M02-REQ-003) is deferred to the Functional
  Requirements step as an optional enhancement rather than asserted here as
  a business need.
- DEC-002 · In the context of a business-viability critique flagging that,
  without a minimum-completeness gate, Discovery inventory fills with
  half-filled profiles that depress response rates for everyone, we added
  a minimum-completeness requirement (see Constraints above) rather than
  leaving completeness as a purely informational signal. We chose an
  actual gate over a display-only completeness indicator, per explicit
  Product Manager direction, to protect Discovery inventory quality,
  accepting that the exact threshold and which fields count toward it are
  deferred to Functional Requirements/FR-stage design, same as the rest of
  this BR's field schema.
- DEC-003 · In the context of a second Product Manager review flagging that
  a single "completeness threshold" was too absolute — risking an
  unintended form-completion bias where a legitimate, verified, sparsely-
  filled candidate disappears from Discovery entirely while a fully-filled
  but poorly-compatible candidate does not — we introduced the three-tier
  distinction above (existence / discoverability / enhanced matching) as a
  business-level refinement of DEC-002's gate, over leaving the single
  threshold as originally written. This achieves the original goal
  (protecting Discovery inventory quality) while bounding it to what a
  viewer actually needs to judge a profile, accepting that Functional
  Requirements now inherits a three-way classification exercise instead of
  a single number, which is more work but prevents FR from silently
  equating "complete" with "worth discovering."
- DEC-004 · In the context of a human correction flagging that this file's
  "Explicitly out of this file's scope" section wrongly lumped multilingual
  support in with genuinely Common-Platform-only infrastructure (AI, search,
  notification delivery) and treated BRD v1.0's day-one "English + Hindi +
  Telugu, language preference attached to each person" direction as
  superseded draft material, we added the person-level language-preference
  Constraint above. We chose to add it here, to this BR, over inventing a
  separate Mangaly-owned localization BR, because `ARCHITECTURE.md` ADR-010
  already fixes the day-one language set and rendering mechanism
  platform-wide — this BR only needs to own the one genuinely
  Mangaly-specific fact, that the preference is per-person profile data —
  accepting that the translated-content rendering itself stays Common
  Platform infrastructure, unchanged by this correction.

**Assumptions**
- Video introduction is a profile feature only (asynchronous, one-way); the
  Master Requirements Input and both BRD drafts are explicit that
  match-to-match live video calling is out of scope for this product
  (BRD D-007) — inferred as an assumption of this BR since it is not
  restated in modules.md's out-of-scope line verbatim.

**Traced to:** FR001–FR006, FR089 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-09

---

## BR02 — Home Circle Membership Management
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
Real matrimonial search in this community is a family effort, but today
there is no digital way to establish *who* is authenticated, related, and
participating in a given candidate's marriage search — without either
building an intrusive family directory or leaving family participation
entirely informal and unaccountable.

**Proposed outcome**
A candidate or an existing participant can search another Mangaly user by
username, send an invitation to join a Home Circle, and have that invitation
accepted, ignored, or reported as a false/inappropriate relationship claim.
Any of the valid invitation paths (Candidate→Parent, Parent→Candidate,
Candidate→Sibling/family member, existing member→another family
member/relative) is supported. A member can be removed, can leave
voluntarily, and a candidate can establish or use another Home Circle after
leaving one. No one can be trapped in a Home Circle.

**Affected users and systems**
Candidate, Parent, Sibling, Relative/trusted family member, Guardian (where
legitimate); Mangaly-scoped admin/operations (BR16, for false-relationship
investigation); Authorization (BR04) consumes Home Circle membership as an
input.

**Constraints**
- Home Circle membership must never, by itself, grant access to any
  specific piece of information or action — that determination belongs to
  BR04 (Authorization), not to this BR.
- Exact relationship taxonomy (mother/father/guardian/sibling/cousin/etc.)
  is a later design detail and must not be artificially expanded without a
  real use case (M01-C §4).
- A candidate who never invites or accepts any Home Circle member must
  retain full, undiminished access to every other Candidate-level
  capability in this module (Profile, Discovery, Compatibility, Trust,
  Connection Request, Selective Sharing, Communication, Contact Exchange,
  Safety, Accountability). A zero-member Home Circle must not degrade,
  block, gate, or limit any of those capabilities. Home Circle membership
  is strictly additive accountability/collaboration infrastructure — the
  module's core purpose (making participation accountable, whether or not
  family is involved) must hold for a solo candidate exactly as it does for
  a candidate with an active Home Circle.

**Out of scope (for this BR specifically)**
Automatic exposure of a Home Circle to a prospective match or prospective
family (explicit non-goal, Master Input §6, §8.2); a public family tree or
complete family directory (explicit non-goal, Master Input §6); resolving
family disagreement — Mangaly does not force resolution (Master Input §6.2)
and that is a collaboration-behaviour concern of BR03, not a membership
concern of this BR.

**Worth check**
Without an authenticated, verifiable Home Circle membership mechanism,
"family collaboration" and "family-assisted discovery" — both explicitly
in the module's approved scope — have no factual foundation to build
authorization or trust on top of; family participation would remain an
unverifiable, unaccountable claim.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of scoping Home Circle into one or two BRs,
  facing the source documents' own split between "how you join/leave" (M01-C,
  M01-I §2–§4, §9) and "what you do once inside" (M01-B, M01-I §5–§12), we
  chose to split them into BR02 (this one) and BR03, over merging into a
  single oversized Home Circle BR, to keep each BR singular and verifiable,
  accepting a longer BR list for this module (consistent with the module's
  own flagged 10–15+ sizing exception in `modules.md`).

- DEC-002 · In the context of a business-viability critique raising concern
  that the multi-actor Home Circle mechanics (this BR, BR03, BR13) might be
  over-engineered relative to actual family usage patterns — since many
  families will not create separate logins and a candidate may run their
  Home Circle alone or informally over the phone — we clarified, rather
  than removed or shrank, this capability: the module's stated purpose is
  to make matrimonial participation accountable whether or not family is
  formally onboarded, so the requirement (see Constraints above) is that
  the product works completely for a solo candidate with zero Home Circle
  members, and Home Circle involvement is additive value on top of that,
  never a precondition for it. We chose this over reducing Home Circle's
  scope pre-emptively, to achieve both correctness (accountability holds
  regardless of family participation level) and adoption safety (the
  product is not broken for users whose families don't engage with it),
  accepting that actual family-account adoption rates remain an open
  question for Impact Analysis (Step 6) to validate empirically once usage
  data exists.

**Assumptions**
- "Search another Mangaly user by username" (Master Input §6.1) assumes a
  platform-level username/identity lookup capability already exists
  (platform concern, not built by this BR) that Mangaly can query.

**Traced to:** FR007–FR012 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-09

---

## BR03 — Family Collaboration Within Home Circle
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
Once a Home Circle exists (BR02), there is still no defined way for parents,
siblings, and relatives to actually do useful matrimonial work together —
discover profiles in parallel, suggest candidates to each other, and keep
private working notes — without either being reduced to passive observers
or being handed unlimited authority over the candidate's decisions.

**Proposed outcome**
Parents can search broadly, inspect profiles, compare potential matches,
suggest people, and continue searching in parallel with the candidate.
Candidates can search independently and decide when to involve family.
Siblings/relatives can search where appropriate and suggest potential
matches. A suggestion is treated as family collaboration, never as consent
or a decision on the suggested person's behalf. Family members may disagree,
and Mangaly does not force resolution. Parents may keep private working
notes not automatically visible to the candidate, with the option to
forward a selected note with the candidate's approval.

**Affected users and systems**
Candidate, Parent, Sibling, Relative/trusted family member; Discovery (BR06,
which this BR's suggestions route through); Authorization (BR04, which
governs what a suggestion actually unlocks for the recipient).

**Constraints**
- "Initiation authority ≠ decision authority" must hold: the person who
  discovers/suggests never automatically becomes the person who decides
  (Master Input §4.6, M01-I §7).
- Private candidate-to-candidate communication remains outside this BR's
  reach by default (governed by BR11), even for parents inside the same
  Home Circle.

**Out of scope (for this BR specifically)**
Forcing family involvement on a candidate (explicit module non-goal); family
surveillance of private candidate activity (explicit module non-goal);
inferring "seriousness" from suggestion/interaction volume (explicit product
invariant, Master Input §21, §33).

**Worth check**
This is the actual value proposition that distinguishes Mangaly from a
candidate-only dating product: "parents are legitimate matrimonial
participants, not secondary observers" is a named product invariant (Master
Input §33). Without this BR, Home Circle membership (BR02) would be an inert
social graph with no real family collaboration behaviour on top of it.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of the "mother finds a groom for daughter" and
  "cousin suggests a profile" scenarios described in the M01 dossier, facing
  a choice between modeling suggestions as a notification-only feature
  versus a full family-collaboration capability with private notes and
  parallel search, we chose the fuller collaboration capability described
  in M01-B/M01-I, over the thinner BRD v0.3 BR-DI-002 framing, because the
  Master Requirements Input's own Product Goals (§2.2–§2.4) require treating
  parents/siblings as full participants, accepting the larger BR scope this
  implies.

**Assumptions**
- "Private family notes" (M01-B §12, M01-I §9) are assumed to be a Mangaly
  business capability rather than a generic productivity/notes feature —
  scoped strictly to matrimonial evaluation content, not general purpose.

**Traced to:** FR013–FR016 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-09

---

## BR04 — Contextual, Least-Privilege Authorization
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
Relationship alone (being a parent, sibling, or Home Circle member) does not
tell the system what a person is actually allowed to see or do. Without an
explicit authorization model, the product would default to a crude
all-or-nothing "family access" toggle that either over-exposes private
candidate activity or under-serves legitimate family collaboration — both
of which the module's approved scope explicitly forbids.

**Proposed outcome**
Every consequential access or disclosure is evaluated against
Person → Relationship → Responsibility → Authorization/Scope → Consent →
Collaboration → Audit before it is granted. Home Circle membership never
automatically grants all access. Parents do not automatically receive
private candidate-to-candidate conversations. Siblings/relatives do not
automatically gain decision authority. A prospective match/family does not
automatically see the candidate's Home Circle. Candidate information and
family information remain separate concepts for authorization purposes.

**Affected users and systems**
All actors (Candidate, Parent, Sibling, Relative, Guardian, Verifier, Mangaly
admin, future Agent); every other BR in this module consumes this
authorization model as its access-control layer.

**Constraints**
- Must be presented to end users as plain-language capability statements
  ("Mom can suggest profiles for you" — M01-Identity dossier §10), not as a
  technical permission/RBAC screen (M01-D §3's "Suggest to Family" example,
  §11–§12) — this is a UX constraint on downstream FR/UX work, not a
  technical architecture decision made here.
- Exact permission matrix/taxonomy is explicitly deferred (Master Input §9
  "exact field schema," §34 "Deferred Decisions"; BRD OPEN-01) — this BR
  establishes the *model*, not the final matrix.

**Out of scope (for this BR specifically)**
A user-facing RBAC/permissions-management screen (explicit anti-pattern per
M01-D §12); authorization for the other six ForKhatri modules (platform/
Common Platform concern per `modules.md` Shared Concerns) — this BR governs
only Mangaly-internal contextual authorization.

**Worth check**
This is the single mechanism that makes "family collaboration with
individual agency" simultaneously true — without it, at least one of family
participation or candidate privacy has to be sacrificed. The module's stated
non-goals (no forced family involvement, no family surveillance) are
unenforceable without this BR existing.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of naming this BR, facing the source documents'
  use of both "Authorization" (Master Input §7) and "Authorization &
  Collaboration Philosophy" (M01-D), we chose to keep this BR focused on the
  authorization mechanism itself and route the "collaboration" behaviours
  into BR03/BR13, over folding collaboration philosophy into this BR, to
  keep this BR singular per the quality gate.

**Assumptions**
- None beyond what is stated in the Constraints — the direction here is
  unusually well-corroborated across all seven M01 dossiers plus the Master
  Requirements Input, which is why Confidence is High despite the
  permission matrix itself being unresolved.

**Traced to:** FR017–FR019 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-09

---

## BR05 — Privacy & Visibility Boundaries for Matrimonial Information
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
Matrimonial searching is itself socially sensitive in this community —
exposure of the mere fact or pattern of searching (not just profile content)
can cause gossip or stigma. Left unaddressed, the product would either
under-share (a frustrating "teaser" experience that withholds information
to force engagement) or over-share (exposing search activity, popularity
signals, or family status to people who have no legitimate purpose to see
them).

**Proposed outcome**
Authorized viewers receive meaningful, sufficiently complete information for
their legitimate matrimonial purpose — Mangaly does not deliberately
withhold information via an artificial teaser UX. Candidate personal
information and family information are treated as separate categories.
Visibility and searchability are separate concepts. Public profile-view
counts, rejection counts, and popularity/demand indicators are not exposed.
If a parent is searching for a match for their child, the prospective
candidate receives the relevant *candidate* profile information, not the
candidate's entire family status/Home Circle — family information reaches
the prospective family only through deliberate, authorized sharing. Users
can pause/disengage without unnecessary social signalling. Controlled safety
exceptions are permitted when severe harm requires intervention.

**Affected users and systems**
Candidate, Parent, Sibling, Relative, prospective match/family; Discovery
(BR06) and Connection Request (BR09), which must respect this visibility
model when surfacing or exchanging information; Safety Intelligence (BR14),
which is the source of the controlled exceptions.

**Constraints**
- Privacy is a system property, not a large collection of user-managed
  settings (Master Input §4.9, "Deferred Decisions" — exact field-level
  visibility rules are implementation-stage).
- The "Important Family Boundary" (Master Input §8.2) is a hard rule, not a
  configurable default: a prospective candidate's information ≠ the
  candidate's family/Home Circle information.

**Out of scope (for this BR specifically)**
Any public, unauthenticated teaser profile (explicitly superseded per BRD
v0.3 §13 — this BR intentionally does not resurrect that idea); a
field-by-field user-configurable privacy settings screen as the *primary*
mechanism (contrary to the "privacy is a system property" principle) —
simple contextual controls are in scope, an exhaustive settings matrix is
not.

**Worth check**
Removing this BR would either force Mangaly into a frustrating
teaser-profile model (an explicit product anti-pattern) or expose sensitive
social facts about who is searching for marriage and to whom — both are
named, serious deficiencies the source documents treat as core to the
product's trust proposition, not cosmetic.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of the BRD v0.3 draft's earlier "public teaser /
  limited-profile tiers" proposal versus its own later explicit reversal
  ("this version explicitly supersedes that direction," BRD v0.3 §7.2), we
  chose to follow the reversal and the Master Requirements Input's
  "meaningful information... avoid deliberate teaser-profile UX" (§8.1)
  over the earlier draft, to stay aligned with the current approved
  baseline, accepting that this forecloses a monetization lever (paying to
  unlock a teaser) some earlier research considered.

**Assumptions**
- None beyond the Constraints above.

**Traced to:** FR020–FR024 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-09

---

## BR06 — Broad Discovery for Candidates and Authorized Family Participants
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
Candidates and parents currently have no shared, meaningful way to discover
eligible people within the community beyond informal networks — and a
naive discovery design (youth-only, or popularity-ranked) would both
contradict how this community actually searches for marriage partners and
would reintroduce a dating-app-style popularity contest the product
explicitly rejects.

**Proposed outcome**
Discovery is available to candidates and to authorized family participants
(parents can discover broadly and in parallel, not only after a candidate
acts first). Discovery supports locality, community context, practical
geography, partner preferences, lifestyle relevance, compatibility
relevance, and verification/evidence context, and is not primarily ranked by
popularity. Where a family knows of a potentially suitable person but cannot
directly access their profile, Mangaly may provide limited contextual hints
sufficient to identify an appropriate community/locality/intermediary route
— this is community-assisted discovery, not a public teaser-profile
mechanism.

**Affected users and systems**
Candidate, Parent, Sibling, Relative; reads Profile (BR01) and Trust/
Verification (BR08) as ranking/relevance inputs; feeds Connection Request
(BR09).

**Constraints**
- Must not make popularity the primary ranking mechanism (Master Input
  §10, explicit).
- Must guard against the fairness failure modes named in the source
  document — popularity bias, wealth/status bias, education/profession
  ranking as human worth, locality bias becoming unfair exclusion,
  recommendation bubbles, sparse profiles being permanently disadvantaged,
  unnecessary sensitive-attribute inference (Master Input §25) — as
  acceptance-level constraints on this BR, not as a separate BR.
- Any AI used for discovery ranking must not present inference as verified
  fact and must remain independently replaceable (Master Input §24) — a
  constraint on this BR's implementation, since AI infrastructure itself is
  a Common Platform concern per `modules.md`.
- A profile that has not cleared BR01's "required for discoverability"
  tier is excluded from Discovery entirely — this is an inventory-quality
  gate (protecting response-rate quality for all participants), not a
  ranking penalty, and is distinct from the popularity-bias/fairness
  constraints above, which govern ranking among profiles that already
  clear the gate. It is deliberately *not* tied to BR01's "required for
  enhanced matching" tier — a verified, legitimate candidate who declines
  optional compatibility-enrichment fields must still be discoverable;
  only genuine sparseness below the discoverability bar is excluded, never
  incomplete Compatibility (BR07) enrichment data.

**Out of scope (for this BR specifically)**
Swipe/dating-style browsing as the core interaction model (explicit
non-goal); a public biodata directory (explicit non-goal); verified
community "Agent" intermediaries actively brokering discovery — that is
BR17's future, deferred capability, not this BR's V1 scope.

**Worth check**
"Give eligible community members broad and meaningful opportunity to
discover matrimonial partners" is Product Goal #1 in the Master
Requirements Input (§2). Without discovery, no other downstream capability
(compatibility, connection, sharing) has anything to operate on.

**Quality gate (ISO 29148, adapted for business-level requirements — see
Set-level quality gate for the four-value scale)**
Necessary: Pass · Unambiguous: Conditional Pass — "excluded from Discovery"
now correctly scoped to BR01's discoverability tier only, resolved by
DEC-003 below; still depends on FR fixing exactly what that tier requires
· Complete: Pass · Singular: Pass · Feasible: Pass · Verifiable: Pass ·
Correct: Pass · Conforming: Pass

**Decisions**
- DEC-001 · In the context of community-assisted discovery being marked
  "LATER / P2" in the BRD v0.3 draft (§4.H) but described directly inside
  the core Discovery section of the authoritative Master Requirements Input
  (§10.1, no deferral language), we chose to keep it inside this BR's scope
  as a lighter, later-implementable sub-capability rather than excluding it
  or promoting it to its own BR, to follow the authoritative source over
  the earlier draft's phasing note, accepting that its exact mechanics
  remain an open, implementation-stage design question.
- DEC-002 · In the context of a business-viability critique noting that
  Discovery without a completeness floor accumulates sparse, low-response
  profiles that degrade the experience for every participant, we added the
  minimum-completeness exclusion above (paired with BR01's completeness
  requirement) as an inventory-quality gate distinct from ranking. We chose
  a hard exclusion over a soft ranking penalty, per explicit Product
  Manager direction, to protect Discovery inventory quality outright rather
  than merely deprioritizing sparse profiles, accepting that a profile
  below threshold is simply not discoverable until completed — a stronger
  intervention than this module's earlier drafts assumed.
- DEC-003 · In the context of a second Product Manager review identifying a
  form-completion bias risk — a legitimate, verified candidate who skips
  optional compatibility-enrichment fields could disappear from Discovery
  entirely while a fully-filled but poorly-compatible candidate remains
  visible — we narrowed the exclusion to BR01's discoverability tier only,
  over the original single-threshold wording, to keep the inventory-quality
  goal from DEC-002 while removing the unintended penalty on candidates who
  are legitimately sparse only on enrichment data, accepting that this
  requires FR to actually maintain the tier distinction rather than
  collapsing it back into one number for implementation convenience.
- DEC-004 · In the context of grounding this BR's anti-popularity-bias
  constraint against real-world evidence rather than only this project's own
  stated principle, live research (2026-09-11) found peer-reviewed and
  industry confirmation that the risk is real and specific, not
  hypothetical: a 2023 Carnegie Mellon/Tepper study found current dating-
  platform recommender algorithms weight popularity above compatibility,
  and unbiased recommendations reduce platform revenue/engagement — i.e.
  the failure mode this BR guards against is one platforms are
  commercially incentivized to drift toward, not an unlikely edge case;
  separately, the Netherlands Institute for Human Rights' 2023 ruling
  against the Dutch dating app Breeze (ethnicity-based match filtering)
  shows this failure mode has already produced a real regulatory finding of
  discrimination, not merely a reputational risk; and a 2025 multi-objective
  framework (FAIR-MATCH, arXiv:2507.01063) confirms fairness-aware
  re-ranking that preserves match quality while reducing popularity/
  demographic bias is an active, tractable research area, not something
  this BR's Constraints ask FR/implementation to solve from a blank page.
  We chose to record this as corroborating evidence for the existing
  Constraints (popularity-bias, wealth/status bias, locality-bias
  guardrails) rather than adding a new Constraint, since the business
  requirement itself was already correctly stated — this closes the gap
  where the file's fairness requirement was asserted on Master Input
  authority alone with no external validation that the risk or its
  mitigation approach are real, accepting that FR/architecture still owns
  selecting the specific fairness technique.

**Assumptions**
- "Locality and practical geography" (Master Input §10) is assumed to rely
  on a general geolocation/mapping capability that may be platform-level
  infrastructure rather than Mangaly-built from scratch; this BR only
  requires that Mangaly *use* locality as a discovery input, not that it
  builds geolocation infrastructure.

**Traced to:** FR025–FR029 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-09

---

## BR07 — Compatibility & Match Intelligence, Explainable and Non-Score
**Priority:** Must (core capability only — see "Core vs. optional
mechanisms" below; the personality assessment and horoscope input are
independently prioritized as Should/Could, not Must)
**Status:** Ready for Review
**Confidence:** Medium — the underlying algorithm/weighting methodology and
hard/strong/weak preference taxonomy for the core (Must) capability are
open/deferred (Master Input §11.2, §34), so while the *business need* for
explainable compatibility is firmly established, the eventual mechanism is
genuinely unresolved at this stage. The personality-assessment instrument
carries its own, separately lower, confidence — see that sub-section.

**Problem**
A bare discovery list of eligible profiles (BR06) does not tell a candidate
or family *why* a given person might be worth exploring, and a naive
solution (a single similarity/compatibility percentage) would be both
scientifically unsupported and would reduce human beings to a misleading
score — something the module's approved scope explicitly forbids
("compatibility/matching signals — never a bare similarity or popularity
score").

**Proposed outcome**

*Core capability (Must) — this is the business requirement:*
Mangaly separates discovery, compatibility, evidence, and human exploration
as distinct concepts. Recommendations provide concrete, explainable reasons
(e.g. shared living-arrangement expectations, similar relocation direction,
compatible family-involvement expectations) rather than an opaque score.
The system distinguishes verified facts from algorithmic inference.
Compatibility considers both alignment and meaningful differences, not
similarity alone.

*Optional mechanisms that may feed the core capability — these are
distinct, separately-prioritized product decisions, not part of the Must
commitment above:*
- **Personality assessment (Should/Could, not Must):** an optional short
  (~5 minute), non-clinical personality assessment may contribute
  additional signals into the core capability. Whether and when this ships
  is a separate decision from whether explainable compatibility itself
  ships — the core capability must be fully deliverable with zero
  personality-assessment data for any candidate who declines it.
- **Horoscope-assisted input (Could):** horoscope may be offered as a
  clearly separated, optional, non-scientific input that never silently
  influences users who have not opted in. Like the assessment, this is
  additive to the core capability, never a prerequisite for it.

A candidate who declines both optional mechanisms must still receive full,
genuinely explainable compatibility signal from profile/evidence data
alone — the optional mechanisms improve signal richness, they do not
constitute the requirement.

**Affected users and systems**
Candidate, Parent, Sibling/Relative (as consumers of "why this match"
explanations); reads Profile (BR01) and Trust/Verification (BR08) as
inputs; surfaces into Discovery (BR06) and Connection Request (BR09).

**Constraints**
- No universal "87% compatible" or similar objective-sounding score may be
  presented (Master Input §11.3, explicit).
- Horoscope must remain optional, clearly separated from evidence-based
  compatibility, and must not be presented as scientific proof (Master
  Input §11.5).
- AI-generated compatibility explanations must not claim certainty about
  character, honesty, or predict marriage success (Master Input §24).
- V1 is expected to use transparent, explainable rules/signals rather than
  an opaque ML system (Master Input §31; M01-G §21) — a build-order
  constraint for downstream FR/implementation, not a limitation on this
  BR's business need.

**Out of scope (for this BR specifically)**
Any single objective compatibility percentage/score (explicit non-goal); AI
autonomously deciding whom a person should marry (explicit non-goal); using
personality results as clinical diagnosis or as a "good/bad spouse" label
(explicit non-goal, Master Input §12).

**Worth check**
Without explainable compatibility, Mangaly degrades into exactly the
"generic biodata database with filters" the source documents explicitly
reject; the module's own scope statement singles this capability out by
name as a required, non-negotiable feature of Mangaly's discovery
experience, distinct from bare discovery.

**Quality gate (ISO 29148, adapted for business-level requirements — see
Set-level quality gate for the four-value scale)**
Necessary: Pass · Unambiguous: Pass · Complete: Pass · Singular: Conditional
Pass — one BR number covers one core capability plus two clearly
subordinated optional mechanisms (see Proposed outcome), a deliberate
structural choice (DEC-002) rather than a single undifferentiated
capability · Feasible: Pass · Verifiable: Conditional Pass — the core
capability's exact algorithm is FR-stage work; the optional mechanisms are
independently unresolved · Correct: Pass · Conforming: Pass

**Decisions**
- DEC-001 · In the context of the personality assessment being described as
  optional ("Mangaly *may* use," Master Input §12) while explainable
  "why this match" reasoning is described in stronger, directive ("should")
  language (Master Input §11.4), we chose to keep both inside one BR rather than
  splitting the assessment into its own BR, to avoid over-fragmenting a
  single coherent compatibility capability, accepting that this BR's
  priority (Must) technically overstated the assessment sub-feature, which
  is independently lower-confidence/optional — flagged explicitly here
  rather than silently smoothed over.
- DEC-002 · In the context of a Product Manager review finding that DEC-001's
  fix (a flagged caveat) was insufficient — an FR agent reading "Priority:
  Must" at the top of this BR could still reasonably conclude the
  personality assessment and horoscope input must be built — we restructured
  the Proposed Outcome into an explicit "Core capability (Must)" versus
  "Optional mechanisms (Should/Could)" split, over merely re-wording the
  caveat, so the priority distinction is structural rather than a note that
  is easy to skip past, accepting the added length in exchange for removing
  a real risk of scope inflation into the FR stage.
- DEC-003 · In the context of confirming that "explainable, non-score
  compatibility" is achievable in a real shipped product rather than an
  aspirational constraint with no working precedent, live research
  (2026-09-11) found that Hinge's "Most Compatible" feature already ships
  this exact pattern at scale: it surfaces a reasoned recommendation
  ("we think you'll connect because...") built from profile answers and
  behavioral signals, explicitly *not* a percentage-based compatibility
  score. This directly corroborates this BR's Core capability requirement
  (concrete, explainable reasons rather than an opaque score) as a proven,
  shippable product pattern, not a theoretical ideal the Master Requirements
  Input asserts without market precedent. We chose to record this as
  supporting evidence for the existing Core capability wording rather than
  changing it, over leaving the "never a bare similarity or popularity
  score" requirement unsupported by any real comparable product, accepting
  that Hinge's specific ML/behavioral-signal mechanism does not itself
  transfer here (Constraints already commit V1 to transparent, explainable
  rules/signals, not opaque ML) — only the explainable-recommendation
  *pattern*, not the underlying algorithm, is the precedent being cited.

**Assumptions**
- The exact hard/strong/weak preference taxonomy (Master Input §11.2) is
  assumed to be resolvable at the Functional Requirements stage without
  changing this BR's business intent.

**Traced to:** FR030–FR034 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-09

---

## BR08 — Evidence-Based Trust & Matrimonial Verification
**Priority:** Must
**Status:** Ready for Review
**Confidence:** Medium — the direction (evidence over scores) is firmly
locked across every source document, but verifier anti-abuse safeguards,
verification vendor/process selection, and exact eligibility thresholds are
explicitly open (BRD OPEN-03/OPEN-04, Master Input §13.3 "Safeguards are
required against... [still to be designed]").

**Problem**
A prospective match or family currently has no evidence-based way to
evaluate whether profile claims (identity, age, relationship, factual
claims) are well-supported, and the two failure modes the module must
avoid are: (a) no verification at all, which invites fraud, fake profiles,
and false relationship claims; and (b) a single "trust score," which the
source documents identify as creating stigma, gaming, and false precision.

**Proposed outcome**
Trust is represented through evidence rather than a score. Mangaly does not
certify that a claim is true — even a government document, community
confirmation, or human verification can be outdated, incomplete,
misinterpreted, or fraudulent — it provides recipients with evidence and
its provenance so *they* can evaluate a claim, which is a materially
different and more honest commitment than "verified = true." Account
authenticity, identity/age, selected profile facts, Home Circle
relationship, community/factual verification, and Mangaly operational
verification are distinct, explainable layers, each with provenance (what
was verified, method/source category, time, freshness/expiry where the fact
can change, and the inherent limits of that method). A Verification Circle
lets a sufficiently verified third party factually confirm or deny
knowledge of a candidate/family (Yes/No/Don't know/Cannot confirm only —
never a rating), with safeguards against gossip, malicious confirmation,
retaliation, and fake witnesses. If no suitable community verifier exists,
a user may request Mangaly/admin verification. Verification explicitly does
not certify character, safety, honesty, marital suitability, or the
underlying truth of a claim — only that specific evidence of a specific
type, from a specific source, at a specific time, exists and can be shown.

**Affected users and systems**
Candidate, Parent/Family (subject of verification), Verifier (provides
factual confirmation), Mangaly admin/verifier (BR16, operational path);
consumed by Discovery (BR06), Compatibility (BR07), and Connection Request
(BR09) as evidence signals.

**Constraints**
- No Trust Score, Family Reputation Score, public reputation ranking, or
  public participant ratings may be created (Master Input §13.1, explicit,
  repeated as a Product Invariant §33).
- A person cannot become a verifier merely because someone invited them —
  the verifier's own identity/eligibility must be checked first (BRD-ID-006).
- Sensitive source verification documents must not become public profile
  content (M01-F §4.2).
- Age/eligibility verification must respect applicable Indian legal
  marriageable-age requirements; exact current thresholds should be
  reconfirmed at Functional Requirements/legal-review time given ongoing
  legislative discussion in this area — flagged as an open detail, not a
  blocker to this BR's approval.

**Out of scope (for this BR specifically)**
Any generic single trust/reputation score (explicit non-goal); verification
that implies or certifies character/safety/marital suitability (explicit
non-goal, Master Input §13.4); base platform identity/authentication itself
(Common Platform concern per `modules.md` Shared Concerns) — this BR covers
only the matrimonial-specific Level-3 verification layered on top of that.

**Worth check**
"Build trust through evidence, verification, provenance, and accountability
rather than reputation scores" is Product Goal #6 (Master Input §2) and is
explicitly named in the module's approved scope as
"evidence-based trust and verification specific to matrimonial
information." Removing this BR removes the entire basis on which a
prospective match can evaluate whether a profile's claims are
well-supported — a fraud and safety deficiency, not a convenience gap.

**Quality gate (ISO 29148, adapted for business-level requirements — see
Set-level quality gate for the four-value scale)**
Necessary: Pass · Unambiguous: Pass · Complete: Pass · Singular: Pass ·
Feasible: Pass · Verifiable: Pass · Correct: Pass · Conforming: Pass

**Decisions**
- DEC-001 · In the context of `modules.md`'s Shared Concerns explicitly
  assigning base identity/authentication to the Common Platform, facing a
  choice between writing a standalone "Identity & Account Foundation" BR
  (as several BRD drafts do, e.g. BR-ID-001–BR-ID-007) or folding the
  Mangaly-specific verification layers into this Trust & Verification BR,
  we chose to fold them in and explicitly exclude base identity/auth from
  this BR's scope, to respect the module boundary set in `modules.md`
  rather than silently re-absorbing a platform concern into Mangaly,
  accepting the risk that this needs re-checking once Solution Architecture
  (Step 0b) defines exactly how Mangaly consumes platform identity.
  > **2026-09-14 correction:** the re-check this decision called for is now
  > defined: Mangaly's Identity Bridge resolves the ForKhatri session
  > server-side and binds `member_id` into Mangaly's RLS context
  > (`docs/ParentApp/07-tech-reqs.md` TR14–TR15, `/ARCHITECTURE.md`
  > ADR-019/ADR-021). The platform supplies only Level 1/2 trust
  > (`identity_level`); BR08's matrimonial Level-3 layers remain Mangaly's.
- DEC-002 · In the context of a Product Manager review noting that framing
  verification as knowing claims "are real" implicitly promises truth
  certification, which even government documents or human verifiers cannot
  actually guarantee, we reframed the Problem and Proposed outcome around
  evidence-that-helps-evaluate rather than truth-certification, over
  leaving the original wording, to keep this BR philosophically consistent
  with its own explicit "does not certify... marital suitability" clause
  and with BR14's Trust-vs-Safety distinction (a verified person can still
  behave badly), accepting no change to the underlying business capability
  — this was a framing correction, not a scope change.
- DEC-003 · In the context of checking whether real matrimony platforms
  already validate evidence-based (non-score) verification as a workable
  market approach, live research (2026-09-11) on India's largest incumbents
  (Shaadi.com, BharatMatrimony) found they already ship exactly the kind of
  evidence-layer verification this BR describes — phone/email verification,
  profile review, "blue-tick" identity verification, and BharatMatrimony's
  SecureConnect® (lets a recipient receive a call without exposing their own
  number) — none of which reduces to a single trust score, corroborating
  that this BR's evidence-not-score approach is proven in this exact market,
  not an unprecedented invention. The same research also surfaced a
  concrete cautionary precedent for the anti-abuse safeguards this BR
  already requires but leaves undesigned (Constraints, Assumptions): user
  reports describe an existing incumbent app sending fake profile/contact
  requests, i.e. exactly the kind of verifier/evidence abuse this BR's
  "safeguards against... [still to be designed]" gap must close before
  implementation, not a hypothetical risk. We chose to record both findings
  as corroborating evidence and a concrete negative precedent respectively,
  rather than changing this BR's scope, since the business requirement was
  already correctly stated — this is added grounding for FR/Security &
  Performance to design against, not a new business commitment.

**Assumptions**
- Verifier eligibility/anti-abuse mechanics are assumed resolvable at FR
  stage; this BR only commits to the requirement that such safeguards must
  exist, not their design.

**Traced to:** FR035–FR041 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-09

---

## BR09 — Connection Request Lifecycle
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
Once a candidate or family finds someone of interest (BR06/BR07), there is
no structured way to express that interest and have the other side review
and respond to it without either forcing premature, unwanted contact or
requiring full commitment before either side knows anything meaningful
about the other.

**Proposed outcome**
The core flow is Discover → Request → Review → Accept/Decline. When a
request arrives, the recipient can inspect meaningful profile information,
relevant compatibility context, and available trust/evidence signals before
deciding — acceptance is not required to reveal meaningful basic profile
information (i.e. no forced teaser-then-pay pattern). Acceptance means
"I am willing to explore this connection" — nothing more. It does not mean
commitment, exclusivity, seriousness, a relationship declaration, marriage
intent, automatic contact exchange, or automatic Home Circle exposure.

**Affected users and systems**
Candidate, Parent/authorized family participant (as initiator or recipient
per BR04); reads Profile (BR01), Compatibility (BR07), Trust (BR08); leads
into Selective Sharing (BR10) and Communication (BR11) on mutual interest.

**Constraints**
- Multiple parallel requests/explorations must be supported — there is no
  single "current match" state (Master Input §21, explicit product
  invariant).
- "Mutual Interest" must be represented as reciprocal willingness to
  explore only, never as a proxy for seriousness or exclusivity (Master
  Input §21, §33).

**Out of scope (for this BR specifically)**
Any forced acceptance or forced continued engagement; any user-facing
"seriousness," exclusivity, or single-current-match status; automatic
contact-detail or Home Circle disclosure upon acceptance (covered
separately, and explicitly deliberate, in BR10/BR12/BR13).

**Worth check**
This is the connective tissue between discovery/compatibility (finding
someone) and selective sharing/communication (getting to know them) —
without an explicit request → review → accept/decline flow, there is no
mutual, consent-based way to move from "discovered" to "exploring," and the
product would either force disclosure or leave interest entirely informal
and unaccountable.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of the BRD v0.3/v1.0 drafts describing an
  eleven-state relationship state machine (DISCOVERED → ... → PROCEEDING/
  CLOSED, BRD v0.3 §6) versus the Master Requirements Input's explicit
  instruction that the journey is "a conceptual journey, not a mandatory
  user-facing state machine" (§4.2, §32), we chose to write this BR (and
  BR10/BR12/BR13) around the *conceptual* flow and natural user actions
  (request/accept/decline/share/communicate/exchange contact/involve
  family) rather than a literal state-machine BR, over adopting the BRD's
  more mechanical state-machine framing, to follow the authoritative
  Master Requirements Input, accepting that an internal state
  representation may still exist as an implementation detail (M01-B §4)
  without being a business requirement in its own right.

**Assumptions**
- None beyond the Constraints above.

**Traced to:** FR042–FR045 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-09

---

## BR10 — Selective Sharing After Acceptance
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
After two people agree to explore a connection (BR09), there is no
graduated way to reveal additional personal information — without either
dumping everything at once (privacy risk) or requiring a rigid, one-size,
multi-stage disclosure ceremony that frustrates users and doesn't match how
people actually build trust with each other.

**Proposed outcome**
After acceptance, each participant independently controls further
disclosure of categories such as additional photos, a video introduction,
additional personal information, phone number, email, and parent/family
contact details where authorized. Sharing is contextual: agreeing to reveal
one category (e.g. additional photos) does not authorize any other category
(e.g. phone number). The user understands what will be shared, with whom,
and what it does not imply, without being burdened by a large, permanent
privacy-settings apparatus. "Acceptance opens the door; it does not open
everything inside the house."

**Affected users and systems**
Candidate (primary actor); Parent/authorized family member where a shared
category is "parent/family contact details" specifically; builds on
Connection Request (BR09); feeds Communication (BR11) and Contact Exchange
(BR12).

**Constraints**
- Sharing one category must not implicitly authorize any other category
  (Master Input §16, explicit rule).
- Must avoid creating "a large permanent privacy-settings burden" (Master
  Input §16) — the mechanism should be a simple, contextual, per-category
  disclosure action, not a settings page.

**Out of scope (for this BR specifically)**
Forced or automatic disclosure of any category upon acceptance (explicit
non-goal, covered by BR09); phone-number exchange itself, which has its own
dedicated deliberateness requirements — see BR12.

**Worth check**
Without a selective, per-category sharing mechanism, Mangaly would have to
choose between over-exposing personal information immediately after
acceptance or under-serving genuine, growing interest — both contradict
"progressive and voluntary sharing of additional personal information,"
which is Product Goal #7 (Master Input §2).

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of choosing whether phone-number sharing belongs
  inside this general Selective Sharing BR or in its own BR, facing the
  Master Requirements Input's decision to give Contact Exchange its own
  dedicated section (§19) with additional deliberateness/attribution rules
  beyond ordinary selective sharing, we chose to give Contact Exchange its
  own BR (BR12), over folding it fully into this one, to preserve the
  extra rigor the source document places specifically on phone/contact
  disclosure, accepting minor conceptual overlap between the two BRs that
  is intentional and traceable rather than accidental duplication.

**Assumptions**
- None beyond the Constraints above.

**Traced to:** FR046–FR048 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-09

---

## BR11 — Private Communication, Ephemerality & Capture-Risk Reduction
**Priority:** Must
**Status:** Ready for Review
**Confidence:** Medium — direction is locked, but exact session
lifecycle/retention mechanics and the severe-incident evidence-retention
exception are explicitly open pending technical and legal design (Master
Input §18; BRD OPEN-05/OPEN-06/OPEN-07), and formal legal sign-off on the
DPDP-compliant retention design is still required before production (see
Decisions below).

**Problem**
Two people who have accepted a connection (BR09) need a way to communicate
and get to know each other before exchanging personal contact details
(BR12), but a conventional, permanently-stored chat history would both
create a lasting, potentially embarrassing or misusable record of a
matrimonial search (contrary to this community's social-privacy needs) and
would contradict the module's explicit non-goal of persistent chat history
as a core feature.

**Proposed outcome**
This is a system-level data-lifecycle business requirement, not a chat-UI
preference — it must generate, at minimum, distinct downstream requirement
families for data lifecycle/deletion semantics, transient processing,
the evidence-retention exception, access control, audit, incident
workflow, legal-hold handling, and failure behaviour (what happens if
deletion or retention fails). Candidates can communicate privately
in-platform before any phone number is exchanged. The system does not
retain a conventional, permanent chat history as a core feature; it may
retain only the minimal events necessary for consent, authorization,
security, abuse prevention, safety, and accountability. Severe safety
incidents (e.g. blackmail, coercion, sexual abuse, financial scams) may
require a tightly controlled, audited, purpose-bound evidence-retention
exception. Multiple conversations may coexist; there is no seriousness
score, exclusivity requirement, or single current-match state. Mangaly
commits to applying reasonable, platform-appropriate technical measures to
reduce the risk of unauthorized capture of protected screens as
risk-reduction, explicitly not as a guarantee — the exact mechanisms are an
implementation-stage decision for architecture/security, not a business
requirement fixed here — and Mangaly cannot promise that screenshots,
screen recording, another device, or photography are prevented.

**Affected users and systems**
Candidate (primary participant); Safety Intelligence (BR14, consumer of the
minimal retained signals and the incident-retention exception); Mangaly
admin/operations (BR16, operates the controlled evidence-exception path);
Accountability/Audit (BR15, records the consent/authorization events this
BR generates).

**Constraints**
- Must not promise that physical/external capture (screenshot, screen
  recording, second device, photography) is impossible — messaging and
  design must reflect "risk-reduction, not guarantee" honestly (Master
  Input §23, explicit).
- The retention design (ephemeral-by-default with a narrow, audited,
  purpose-bound safety exception) is directionally supported by India's
  DPDP Act 2023 storage-limitation/purpose-limitation principles and its
  Section 17 exemption for prevention/investigation of offences, per
  research conducted for this BR (see Decisions) — but the *exact* scope,
  duration, and access controls of the safety exception require formal
  legal sign-off before production, and DPDP Rules 2025's phased
  commencement should be reconfirmed against Mangaly's user-base size at
  launch time.
- No routine human reading of private communication (Master Input §22,
  explicit) — safety access to any retained signal must be tightly
  controlled (BR14).

**Out of scope (for this BR specifically)**
Persistent, conventional chat history as a core product feature (explicit
module non-goal); match-to-match live video/voice calling (explicit
non-goal per all source drafts; profile video introduction is a BR01
concern, not this BR); an absolute, guaranteed anti-capture claim (explicitly
disclaimed, not offered).

**Worth check**
"Support communication without requiring immediate personal contact
exchange" is Product Goal #8 (Master Input §2), and "keep user experience
simple even when the underlying... safety system is sophisticated" (Goal
#10) depends directly on this BR's ephemerality-plus-exception design. Its
absence would force a choice between an intrusive permanent record (privacy
harm) or no communication channel at all (defeats the product's purpose).

**Quality gate (ISO 29148, adapted for business-level requirements — see
Set-level quality gate for the four-value scale)**
Necessary: Pass · Unambiguous: Pass · Complete: Pass · Singular: Conditional
Pass — communication, ephemerality, and capture-risk-reduction are kept as
one BR deliberately (DEC-002), a single coherent privacy promise rather
than an undifferentiated grab-bag · Feasible: Conditional Pass — feasible
in direction, but exact retention/capture mechanics are unresolved ·
Verifiable: Needs Refinement — formal legal sign-off on the DPDP-compliant
retention design is still outstanding (see Constraints); this BR cannot be
fully verified until that lands · Correct: Pass · Conforming: Pass

**Decisions**
- DEC-001 · In the context of an identified legal-research gap (whether
  India's DPDP Act 2023/Rules 2025 make an "ephemeral-by-default,
  narrow-audited-safety-exception" retention design plausible or clearly
  non-compliant), facing genuine ambiguity that could have blocked this BR,
  we invoked the `researcher` subagent (one self-loop; resolved on first
  attempt) rather than guessing or leaving the BR fully blocked. The
  finding: DPDP's storage-limitation/purpose-limitation principles and
  Section 17 offence-prevention/investigation exemption directionally
  support this design, and no DPDP-specific "sensitive personal data"
  category exists for caste/religion-adjacent matrimonial attributes (that
  category was removed relative to earlier 2019/2021 drafts) — so ordinary
  minimization/consent duties apply uniformly. We chose to treat this as a
  resolvable BR-level design constraint (stated above) rather than an open
  blocker requiring PM/legal escalation before BR approval, over leaving
  BR11 in Blocked status, to achieve forward progress on an otherwise
  well-supported BR, accepting that formal legal sign-off on the *exact*
  implementation is still required before production (captured explicitly
  in the Constraints above so it is not lost).
- DEC-002 · In the context of the source documents' own screenshot/capture
  research being separately sectioned (Master Input §23; BRD v0.3 §4.F) from
  ephemeral communication (Master Input §18; BRD v0.3 §4.E), facing a
  choice of one merged BR versus two, we chose to merge them into this one
  BR, over a separate "Capture Protection" BR, because capture mitigation
  is a risk-reduction technique in service of the communication-privacy
  promise rather than an independent business capability, accepting a
  slightly broader single BR in exchange for avoiding a BR that would only
  restate "apply platform capture APIs" as its entire content.
- DEC-003 · In the context of a Product Manager review flagging that naming
  specific mechanisms (iOS screen-capture state response, Android
  FLAG_SECURE) inside a business requirement blurs the BR/FR/technical-design
  boundary and risks a future reviewer mistaking this BR for having already
  chosen an implementation, we replaced the named mechanisms with a
  platform-neutral business commitment ("reasonable, platform-appropriate
  technical measures... an implementation-stage decision for architecture/
  security") and added an explicit list of the downstream requirement
  families this BR must generate. We chose this over leaving the specific
  mechanisms in place, to keep this BR at business-requirement altitude
  consistently with the rest of this document, accepting no change to the
  underlying business commitment — Mangaly still commits to applying
  capture-risk-reduction measures where technically available, exactly as
  before.

**Assumptions**
- None beyond the Constraints/Decisions above.

**Traced to:** FR049–FR056 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-09

---

## BR12 — Deliberate Contact Exchange
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
At some point in a connection, a candidate or authorized family participant
may want to exchange a phone number — but doing this automatically (e.g.
upon acceptance or after some elapsed time) exposes personal contact
details before either side is ready, which is both a safety risk and an
explicit module non-goal ("forced phone exchange").

**Proposed outcome**
A candidate, parent, or appropriately authorized participant may request
contact information where the journey's context permits. The recipient
decides whether to share and what contact method to share — request
authority and receipt/decision authority are separate. The exchange is
internally attributable (who requested, who decided, when), does not imply
commitment or exclusivity, and does not automatically reveal any other
contact detail beyond what was explicitly shared.

**Affected users and systems**
Candidate, Parent/authorized family participant (as requester or decider per
BR04); builds on Selective Sharing (BR10); feeds Accountability/Audit
(BR15).

**Constraints**
- Contact exchange must never be automatic or forced by elapsed time,
  message count, or any other proxy signal (Master Input §19, §33 —
  "Acceptance ≠ contact exchange").
- Request authority and receipt authority are explicitly separate
  concepts (M01 dossier §5, §7).

**Out of scope (for this BR specifically)**
Automatic phone-number reveal upon acceptance or connection progress
(explicit non-goal); exposing any other contact channel not explicitly
requested/shared.

**Worth check**
"Support communication without requiring immediate personal contact
exchange" (Product Goal #8) only has teeth if contact exchange itself is
governed by an explicit, deliberate, recipient-controlled mechanism — this
BR is the enforcement point for that goal and for the module's explicit
"no forced phone exchange" non-goal.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · See BR10 DEC-001 (same decision, recorded once): Contact
  Exchange is deliberately kept as its own BR distinct from general
  Selective Sharing because the source document gives it dedicated,
  stricter rules (request/receipt authority separation, internal
  attributability) beyond ordinary category-based sharing.

**Assumptions**
- None beyond the Constraints above.

**Traced to:** FR057–FR059 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-09

---

## BR13 — Family Involvement in an Established Connection
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
Once two candidates are exploring a connection privately (BR09/BR11), there
is no defined, deliberate way to bring family into *that specific
connection* at the right time — without either exposing the private
conversation to family by default (a privacy violation) or leaving family
introduction entirely undefined and ad hoc.

**Proposed outcome**
A candidate can choose when to involve their Home Circle in a specific
connection. Parents may already be independently involved in discovery
(BR03) without this implying they are automatically part of *this*
connection. Private candidate-to-candidate communication remains private
unless deliberately shared. Family-to-family introduction is a distinct,
separate step from the candidate-level connection, and a prospective
family does not automatically receive the other candidate's Home Circle
just because family involvement has begun.

**Affected users and systems**
Candidate (controls timing); Parent/Home Circle member (participant once
involved); depends on Home Circle (BR02/BR03) and Connection Request (BR09)
already being established; interacts with Contact Exchange (BR12) at the
family stage.

**Constraints**
- Family involvement is deliberate, never automatic or inferred (Master
  Input §20, explicit).
- Bringing in one's own family does not grant that family automatic access
  to the other side's Home Circle (Master Input §20, §6).

**Out of scope (for this BR specifically)**
Automatic family exposure to private candidate-to-candidate communication
merely because a Home Circle exists (explicit non-goal, covered by BR04);
forcing family involvement on a candidate who does not want it (explicit
module non-goal).

**Worth check**
This BR is what makes "preserve individual agency while enabling family
collaboration" (Product Goal #11) operational at the most sensitive moment
— the transition from a private, individual exploration to a family-visible
one. Without it, the product cannot honor both candidate privacy and
family's legitimate eventual role at once.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · See BR02 DEC-001: this BR is deliberately kept distinct from
  BR03 (pre-connection family collaboration/discovery) because the Master
  Requirements Input treats "Family Involvement in a Connection" as its own
  numbered section (§20) with rules specific to an *already-established*
  connection, not to general Home Circle collaboration.

**Assumptions**
- None beyond the Constraints above.

**Traced to:** FR060–FR062 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-09

---

## BR14 — Safety Intelligence & Abuse Prevention
**Priority:** Must
**Status:** Ready for Review
**Confidence:** Medium — the intervention model (graduated response) and
detection categories are locked, but the exact severity taxonomy and the
precise threshold at which an automated safety event escalates to human/
legal review are explicitly open (Master Input §22 implies but does not
define thresholds; BRD BR-SAFE-007 "OPEN").

**Problem**
A matrimonial platform that enables private, ephemeral communication
(BR11) and family collaboration (BR03) creates real exposure to fraud,
deception, grooming, harassment, blackmail, coercion, sexual abuse, and
financial scams — and doing nothing about it, or routinely reading all
private communication to catch it, are both unacceptable: the former is a
serious harm the module exists partly to reduce, and the latter directly
contradicts the module's privacy commitments.

**Proposed outcome**
Safety detection in this module has two distinct entry points, and neither
may substitute for the other: (1) **user-initiated reporting** — any
candidate or authorized Home Circle member can directly report a person,
profile, message, or interaction as unsafe or abusive at any time, and this
must not be assumed to be handled automatically just because pattern
detection also exists; and (2) a dedicated Safety Intelligence layer,
operating alongside but distinct from Trust/Verification (BR08), which
identifies patterns associated with fake profiles, deception, grooming,
blackmail, harassment, vulgarity, threats, sexual abuse, financial
manipulation, romance scams, coercion, suspicious escalation, malicious
links, off-platform pressure, and repeated unwanted contact — using the
minimum information necessary to identify a meaningful risk pattern, not
open-ended behavioural surveillance. Both entry points feed the same
graduated response: privacy-preserving detection/triage where appropriate →
warning/nudge → restriction/block → controlled human investigation →
legal/emergency escalation for severe cases. Routine human reading of
private communication is not the objective, and safety access is tightly
controlled.

**Affected users and systems**
All actors (as potential targets or subjects of a safety event); Mangaly
admin/operations (BR16, executes human investigation/escalation);
Accountability/Audit (BR15, records safety actions); consumes the minimal
signals retained per BR11.

**Constraints**
- A verified person can still behave badly, and an unverified claim does
  not automatically mean malicious behaviour — Safety and Trust must remain
  operationally distinct systems (Master Input §4.10, M01-F §11).
- Any AI used for detection must not act as a "definitive truth detector
  from language" and must not present inference as verified fact (Master
  Input §24).
- Exact severity taxonomy and escalation thresholds are open and require
  further design (abuse taxonomy, severity matrix, staffing, legal review)
  before this BR's graduated-response model can be fully operationalized —
  flagged for the Impact Analysis/Security & Performance steps, not a
  blocker to BR approval since the business requirement itself (a graduated,
  privacy-respecting safety system must exist) is unambiguous.
- Pattern-detection scope is bounded to the minimum information necessary
  to identify a meaningful, named risk category (see Proposed outcome's
  list) — this BR authorizes targeted, privacy-preserving risk detection,
  not open-ended behavioural monitoring or profiling; anything broader is
  out of scope for this BR and would require its own explicit business
  justification.
- User-initiated reporting (see Proposed outcome) must remain available and
  effective independent of whether automated pattern detection has flagged
  anything — a user's report is never downgraded or ignored merely because
  the automated layer saw no pattern.

**Out of scope (for this BR specifically)**
Routine human reading of private communication as a monitoring strategy
(explicitly rejected); a public reporting/rating system for participants
(explicit non-goal, distinct from the internal report/block mechanism this
BR does include).

**Worth check**
"Reduce fraud, deception, grooming, harassment, blackmail, coercion, sexual
abuse, and financial scams" is Product Goal #9 (Master Input §2) — named
explicitly, not implied. Given the private-communication and family-
collaboration capabilities this module also requires, omitting a safety
layer would leave known, named harm categories unaddressed by design, not
merely under-resourced.

**Quality gate (ISO 29148, adapted for business-level requirements — see
Set-level quality gate for the four-value scale)**
Necessary: Pass · Unambiguous: Pass · Complete: Pass · Singular: Pass ·
Feasible: Pass · Verifiable: Needs Refinement — severity taxonomy and
escalation thresholds remain open (see Constraints); this BR cannot be
fully verified until Impact Analysis/Security & Performance resolve them ·
Correct: Pass · Conforming: Pass

**Decisions**
- DEC-001 · In the context of Safety Intelligence and Trust/Verification
  both appearing under a broadly similar "trust" umbrella in early BRD
  drafts (BRD v0.3 groups Verification §4.A and Safety §4.G separately, but
  earlier v0.1/v0.2 concept notes blur them), we chose to keep them as two
  separate BRs (this one and BR08), over merging them, because the Master
  Requirements Input explicitly states "Safety Is Separate From
  Verification" as a named Core Product Principle (§4.10), making the
  distinction a locked product decision rather than an editorial choice.
- DEC-002 · In the context of a Product Manager review flagging two risks —
  (a) "invisible monitoring" is phrasing broad enough that an implementation
  agent could read it as authorizing a general-purpose behavioural
  surveillance engine, and (b) the original text implied all safety
  detection was automated, with no explicit user-initiated reporting path —
  we reframed automated detection as bounded, privacy-preserving pattern
  detection using minimum necessary information (added as an explicit
  Constraint), and added user-initiated reporting as a co-equal, independent
  entry point in the Proposed outcome. We chose this over leaving the
  original single-path, broadly-worded description, to prevent scope
  inflation into surveillance and to close a real functional gap (a user
  must always be able to say "something is wrong" without depending on
  automated detection), accepting no change to this BR's core commitment —
  a graduated, privacy-respecting safety system must exist — only to how
  it is entered and how tightly its automated component is bounded.
- DEC-003 · In the context of checking whether this BR's graduated,
  privacy-preserving detection model is achievable in practice rather than
  aspirational, live research (2026-09-11) found that Tinder and Bumble
  already operate the same two-layer model this BR requires, at meaningful
  effectiveness: Tinder's context-aware "Are You Sure?"/"Does This Bother
  You?" nudges intervene on harmful messages before escalation (not a
  block-only response), and its Face Check facial-verification layer is
  paired with continued human review, not deployed as a sole automated
  gate; Bumble's Deception Detector — AI pattern detection backed by a
  dedicated human moderation team, matching this BR's "privacy-preserving
  detection/triage → controlled human investigation" chain — blocked 95% of
  spam/scam accounts identified in testing and cut fake-profile user
  reports by 45% in two months, evidence that automated pattern detection
  paired with human review measurably reduces the harm categories this BR
  names, not merely a plausible theory. We chose to record this as
  corroborating evidence for the existing graduated-response Proposed
  outcome rather than changing it, accepting that these platforms' specific
  detection techniques (facial biometrics, LLM-based message scoring) are
  FR/Security & Performance's decision to adopt, adapt, or reject — this BR
  only needed confirmation that its overall model is provenly workable, not
  a specific technique.

**Assumptions**
- None beyond the Constraints above.

**Traced to:** FR063–FR068 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-09

---

## BR15 — Internal Accountability & Audit Trail
**Priority:** Must
**Status:** Ready for Review
**Confidence:** High

**Problem**
Every other capability in this module — Home Circle membership, family
collaboration, authorization decisions, connection requests, selective
sharing, contact exchange, family involvement, and safety interventions —
produces consequential actions whose actor, authority, and consent context
must be reconstructable after the fact (for disputes, false-relationship
investigations, and safety escalation). Without an explicit accountability
requirement, none of these capabilities can be investigated or trusted when
something goes wrong.

**Proposed outcome**
For every consequential action, Mangaly can determine, as appropriate: who
acted; in what capacity; on whose behalf, where relevant; what action
occurred; what person/object was affected; what authorization applied; what
consent was present or required; when it happened; and whether it was later
revoked, changed, or disputed. This accountability is internal system
integrity — it is not permission for family surveillance of another
member's private activity, and it does not expose a full audit log to other
users.

**Affected users and systems**
All actors, as subjects of accountable events; Mangaly admin/operations
(BR16, primary consumer, for investigation and dispute resolution); every
other BR in this module is a source of accountable events for this
capability.

**Constraints**
- Accountability is internal integrity, explicitly not surveillance —
  ordinary Home Circle members must never gain access to another member's
  audit trail merely because accountability data exists (Master Input §14,
  explicit).
- Final event-storage architecture/retention/aggregation rules are
  explicitly deferred to the ER-model and technical-design stage (M01
  dossier §13–§14) — this BR establishes the business requirement that
  accountability exist, not its schema.

**Out of scope (for this BR specifically)**
Exposing a full audit trail to ordinary users or family members (explicit
non-goal, would constitute surveillance); granular session/behavioural
telemetry retained without a defined safety, security, reliability, or
product purpose (explicitly cautioned against, M01 dossier §14).

**Worth check**
Accountability is listed as its own numbered section in the Master
Requirements Input (§14) and is one of the seven links in the module's own
authorization chain (Person → Relationship → Responsibility →
Authorization/Scope → Consent → Collaboration → Audit, §7). Every dispute-
handling, false-relationship-investigation, and safety-escalation capability
in this module (BR02, BR08, BR14, BR16) is unimplementable without it —
removing this BR would leave every other accountability-dependent BR
unverifiable in practice.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of `modules.md`'s Shared Concerns listing
  "audit/accountability logging" as a platform-level cross-cutting
  requirement "that every module's consequential actions must feed, but
  which no single business module owns," facing a choice between omitting
  this BR entirely (treating it as pure platform infrastructure) or keeping
  it as a Mangaly BR, we chose to keep it as a Mangaly-scoped BR describing
  *what Mangaly-specific events must be accountable and why* (per Master
  Input §14, a Mangaly product commitment, not just infrastructure), over
  omitting it, to preserve the module's own explicit business requirement
  language, accepting that the underlying storage/logging *mechanism* may
  ultimately be shared platform infrastructure that this BR's eventual FRs
  will need to consume rather than build from scratch.

**Assumptions**
- The underlying audit-log storage mechanism may be platform-level
  infrastructure (per `modules.md` Shared Concerns); this BR assumes
  Mangaly-specific business logic determines *what* must be logged and
  *who* may query it, while the storage substrate itself may be shared.

**Traced to:** FR069–FR071 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-09

---

## BR16 — Mangaly-Scoped Admin & Operations
**Priority:** Must
**Status:** Ready for Review
**Confidence:** Medium — the requirement that these operational capabilities
exist is clear, but exact operational workflows, staffing model, and
severity-based routing rules are explicitly open (Master Input §27 states
*what* must be supported, not *how*; BRD BR-SAFE-007 links this to the
undefined severity taxonomy).

**Problem**
Verification exceptions (BR08), false-relationship claims (BR02),
safety escalations (BR14), and general abuse/fraud reports need a human
operational path to be investigated and acted upon — without one, every
upstream "controlled exception" or "human escalation" promise made by this
module's other BRs would be an empty commitment.

**Proposed outcome**
Mangaly operations support controlled workflows for: identity/profile
verification, Verification Circle review, false-relationship investigation,
abuse reports, fraud investigation, restrictions/blocks, safety
investigation, appeals where applicable, and legal/emergency escalation.
Every consequential administrative action is audited (via BR15). Operator
access follows need-to-know and least privilege; operators do not gain
unrelated private-communication access merely by virtue of being
administrators.

**Affected users and systems**
Mangaly admin/verifier, Mangaly administrator/operations (primary actors);
Candidate, Parent, Sibling, Relative, Verifier (as subjects of
investigation/appeal); consumes Accountability/Audit (BR15); acts on
outcomes from BR08 (verification exceptions), BR02 (false-relationship
reports), and BR14 (safety escalations).

**Constraints**
- Operators must not gain unrelated private-communication access merely
  because they are administrators (Master Input §27, explicit).
- Access must follow need-to-know and least privilege (Master Input §27).
- Investigation outcomes must not become public accusations or reputation
  scores (M01-F §10, consistent with the "no public rating" invariant).

**Out of scope (for this BR specifically)**
Unrestricted administrative access to private candidate-to-candidate
communication (explicit non-goal); public disclosure of investigation
outcomes (explicit non-goal); the general business/professional, event, or
financial admin/operations capabilities of the other six ForKhatri modules
(explicitly out of MOD03's scope per `modules.md`).

**Worth check**
Every other BR in this module that promises a "controlled exception,"
"investigation," or "escalation" path (BR02, BR08, BR11, BR14) depends on
this BR existing to actually fulfil that promise — without it, those
promises are unenforceable, which the source document treats as a named,
required capability (Master Input §27), not an optional nicety.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of `modules.md`'s explicit inclusion of
  "Mangaly-scoped admin/operations" as its own named item in MOD03's
  approved Scope line, facing a choice between folding admin/operations
  into BR15 (Accountability) or BR14 (Safety) versus giving it its own BR,
  we chose a standalone BR, over folding it in, because the source
  document explicitly names it as a distinct capability and because it
  spans multiple upstream BRs (verification, false-relationship,
  safety) rather than belonging to only one.

**Assumptions**
- None beyond the Constraints above.

**Traced to:** FR072–FR076 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-09

---

## BR17 — Future Mangaly Agent Layer
**Priority:** Could
**Status:** Ready for Review
**Confidence:** Low — explicitly a deferred, future capability across every
source document, with commercial model, exact scope of authority, and
governance model all intentionally unspecified pending the core product
proving itself first.

**Problem**
Existing Samaj/community marriage professionals currently operate entirely
outside any digital trust/accountability system, and if Mangaly grows
without ever providing them a legitimate path into the platform, it risks
either competing destructively with an existing community livelihood or
permanently excluding a discovery channel (community-assisted introductions)
that some families will continue to rely on regardless.

**Proposed outcome**
A future professional "Mangaly Agent" layer allows verified community
marriage professionals to support families and candidates with stronger
professional identity verification, explicitly scoped and revocable access,
fully attributable actions, and full auditability. Agents cannot become
gatekeepers who control who receives exposure, and agent economics must not
create a pay-to-win trust manipulation dynamic. This layer is explicitly
sequenced last, after the core candidate/family product (BR01–BR16) works
well.

**Affected users and systems**
Future Mangaly Agent (community marriage professional); Candidate, Parent,
Family (as beneficiaries of agent-assisted introductions); consumes
Authorization (BR04), Accountability (BR15), and Admin/Operations (BR16) as
its scoping/audit/revocation foundation.

**Constraints**
- Must not be implemented before the core candidate/family product is
  proven — explicit sequencing instruction (Master Requirements Input §28;
  BRD v0.3 §11 "implement community-agent/intermediary functionality last").
- Agent access must never default to broad profile browsing/administration
  rights; scope must be explicit and revocable (Master Input §28).
- Commercial/monetization model for Agents is explicitly out of scope for
  this BR and is owned by MOD06 Payment Services once designed (`modules.md`
  Mangaly "Depends on" line).

**Out of scope (for this BR specifically)**
Any Agent capability being built or activated in the current release
cycle (explicitly deferred/"LATER" across all source drafts); Agent
commercial/pricing model (deferred to Payment Services and to a future
BR when the Agent layer itself is prioritized); Agents gaining
unrestricted access to any private profile or Home Circle outside their
authorized scope (explicit non-goal).

**Worth check**
This BR passes the worth check narrowly and differently than the others:
it is not needed for V1, but its *absence from this document entirely*
would silently drop a capability `modules.md` explicitly lists as in-scope
for MOD03 ("a future professional 'Mangaly Agent' layer"). Recording it now
as a low-priority, explicitly deferred BR preserves traceability to the
approved module scope without pretending it is a near-term build
commitment — omitting it would understate the module's actual approved
scope and could mislead a later reviewer into thinking Agent was never
considered.

**Quality gate (ISO 29148, adapted for business-level requirements)**
Necessary ✓ · Unambiguous ✓ · Complete ✓ · Singular ✓ · Feasible ✓ ·
Verifiable ✓ · Correct ✓ · Conforming ✓

**Decisions**
- DEC-001 · In the context of every source document consistently marking
  the Agent layer as "LATER"/"Future"/"deferred until core trust graph is
  proven," facing a choice between omitting it from this BR set entirely
  (since it will not be built soon) or recording it as a low-priority,
  explicitly deferred BR, we chose to record it, over omitting it, to keep
  this file traceable to the full approved MOD03 scope in `modules.md` and
  to avoid a future reviewer mistaking its absence for an oversight,
  accepting that this BR will remain essentially un-actionable until the
  core product (BR01–BR16) is live and proven.

**Assumptions**
- Assumed that "future" means "not in the current SDLC cycle for this
  module," not "never" — consistent with `modules.md` listing it as
  in-scope rather than out-of-scope for MOD03.

**Traced to:** FR077–FR078 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-09

---

## BR18 — Matrimonial Profile Lifecycle & Outcome Management
**Priority:** Must
**Status:** Ready for Review
**Confidence:** Medium — the business need is clear and was raised directly
by the Product Manager, but the source documents (Master Requirements
Input, BRD drafts, M01 dossiers) do not address this capability at all, so
there is no existing baseline language to trace to; this BR is written from
first principles against the module's own stated purpose rather than a
cited source section.

**Problem**
Once a candidate's matrimonial search ends in an engagement or marriage —
or the candidate simply stops searching — there is no defined way for that
outcome to be recorded. Discovery (BR06) and Compatibility (BR07) keep
surfacing and matching against profiles that are no longer active
participants, silently degrading inventory quality and response rates for
every remaining active candidate. This is a compounding quality problem
BR06's completeness gate alone does not solve, since a concluded profile
can be fully complete and verified and still be stale inventory.

**Proposed outcome**
A candidate (or an authorized Home Circle member acting for them, per BR04)
can mark their own matrimonial search as concluded — engaged, married, or
otherwise no longer searching — at which point their profile stops
appearing in Discovery (BR06) and stops being offered as a Compatibility
match (BR07) to others, without deleting their historical data or
retroactively invalidating past connections/accountability records (BR15).
A concluded profile can be reactivated by its owner if the outcome does not
proceed (e.g. an engagement that ends), restoring full Discovery/
Compatibility participation.

**Affected users and systems**
Candidate (primary actor, controls their own lifecycle state); Parent/
authorized Home Circle member (may act on the candidate's behalf per BR04
where authorized); Discovery (BR06) and Compatibility (BR07), which must
exclude concluded profiles; Accountability/Audit (BR15), which records the
lifecycle-state change.

**Constraints**
- Marking a profile concluded must never delete or invalidate historical
  Home Circle, connection, sharing, or accountability records — this is a
  visibility/eligibility state change, not a data-deletion action.
- Reactivation must be available to the profile owner without requiring
  re-verification of already-verified facts that have not changed (though
  BR08's normal freshness/expiry rules still apply to any evidence that has
  gone stale).

**Out of scope (for this BR specifically)**
Automatically inferring that a candidate has married or stopped searching
from behavioural signals (e.g. reduced activity) — the state change is a
deliberate candidate action, not an algorithmic guess, consistent with this
module's product invariant against inferring seriousness from activity
volume (§21, §33); success-story capture and consent (a distinct, lower-
priority capability — see BR19); any public-facing success-story gallery or
marketing site.

**Worth check**
Without this BR, the module has no way to keep Discovery/Compatibility
inventory representative of people actually searching. This is a genuine
deficiency, not a nice-to-have: every other BR in this module optimizes the
search-and-connect journey, and none of them close the loop on what happens
when that journey succeeds or ends.

**Quality gate (ISO 29148, adapted for business-level requirements — see
Set-level quality gate for the four-value scale)**
Necessary: Pass · Unambiguous: Pass · Complete: Pass · Singular: Pass ·
Feasible: Pass · Verifiable: Pass · Correct: Pass · Conforming: Pass

**Decisions**
- DEC-001 · In the context of this gap being identified in a Product
  Manager business-viability critique rather than in any source document,
  facing a choice between treating it as out of MOD03's scope (since
  `modules.md` does not name it explicitly) or writing it as a Mangaly BR,
  we chose to write it as a Mangaly BR, over deferring it to a future
  module-scope change, because profile lifecycle state is intrinsically
  Mangaly-owned data (it directly gates BR06/BR07, both Mangaly
  capabilities) and does not create or require access to any other
  module's data, so it fits within MOD03's existing "Data owned" boundary
  in `modules.md` without requiring a scope amendment there.
- DEC-002 · In the context of a second Product Manager review judging that
  this BR, as originally written, bundled two capabilities of materially
  different necessity — lifecycle management (needed for the core product
  to function correctly) and success-story capture (valuable, but not
  required for the core product to operate) — under one "Must" priority, we
  split them into this BR (lifecycle, Must) and BR19 (success stories,
  Could), over keeping them merged. This achieves genuine requirement
  singularity and an honest priority per capability, over a merged BR whose
  single "Must" label overstated the success-story sub-feature, accepting
  the larger BR list this implies (consistent with this module's own
  flagged sizing exception).

**Assumptions**
- None beyond the Constraints above.

**Traced to:** FR079–FR081 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-09

---

## BR19 — Success Story Capture & Consent
**Priority:** Could
**Status:** Ready for Review
**Confidence:** Medium — the business need is real but not core-product-
critical, and, like BR18, has no source-document citation; written from
first principles and explicitly lower-priority than BR18 by Product
Manager direction.

**Problem**
The product has no mechanism to capture the very outcomes — successful
matches — that constitute both validation that the product works and one
of the platform's most credible, lowest-cost sources of future trust and
word-of-mouth. This is a marketing/trust-building opportunity, not a
functional gap in the core search-and-connect journey (which BR18 already
closes on its own).

**Proposed outcome**
Only with the explicit, specific, revocable consent of every candidate
involved, Mangaly may invite a concluded match (per BR18) to share a
success story for use in trust-building and marketing. Consent to share is
never required, never assumed from marking a profile concluded, and is
fully separable from BR18's lifecycle-state change — a candidate can mark
their search concluded via BR18 and decline to share any story, and that
must have zero effect on their account status.

**Affected users and systems**
Candidate (primary actor, grants/withholds/revokes consent); builds on
BR18's concluded-profile state; Accountability/Audit (BR15), which records
consent given/withdrawn for story sharing; Mangaly admin/operations (BR16),
which may operate the (opt-in, consented) success-story publication path.

**Constraints**
- Success-story consent must be per-story, specific, and revocable, and
  must never be a precondition of, or bundled with, BR18's lifecycle-state
  change — the two remain independent actions on independent axes even
  though they are now independent BRs.
- A published success story must not disclose Home Circle membership,
  private communication content (BR11), or contact details beyond what
  every consenting party explicitly approved for that specific story.

**Out of scope (for this BR specifically)**
A public-facing success-story gallery or marketing site (a distribution/
marketing-channel decision outside this BR's scope, which covers only the
consent-and-capture mechanism); forced or default-opt-in story sharing
(explicit non-goal, per the Constraints above); any change to BR18's
lifecycle mechanics.

**Worth check**
This capability is valuable — a matrimonial product that can show "this
worked" gains a credible, low-cost trust and acquisition asset — but,
unlike BR18, the core product (Discovery, Compatibility, Connection,
Sharing, Communication, Contact Exchange, Family Involvement, Safety,
Accountability, Admin) is fully functional without it. It passes the worth
check as a Could: worth building, not worth blocking V1 on, and its absence
from this document would understate the module's opportunity without
breaking anything if it never ships.

**Quality gate (ISO 29148, adapted for business-level requirements — see
Set-level quality gate for the four-value scale)**
Necessary: Pass · Unambiguous: Pass · Complete: Pass · Singular: Pass ·
Feasible: Pass · Verifiable: Pass · Correct: Pass · Conforming: Pass

**Decisions**
- DEC-001 · In the context of success stories being a high-value trust/
  marketing asset but also involving what is, by definition, the most
  sensitive possible disclosure (that two named people married through this
  platform), we chose to require explicit, specific, per-story, revocable
  consent from every party rather than any default-share or opt-out model,
  over a lighter-weight consent mechanism, to remain consistent with this
  module's own privacy invariants (BR05) and to avoid the module's named
  non-goal of exposing participants' search activity without authorization,
  accepting that this will yield fewer publishable stories than an opt-out
  model would, in exchange for not compromising the trust proposition the
  rest of this module is built on.
- DEC-002 · See BR18 DEC-002 (same decision, recorded once): this BR was
  split out of the original merged BR18 specifically because success-story
  capture does not carry the same necessity as lifecycle management and
  should not inherit a "Must" priority by association.

**Assumptions**
- The publication *channel* for a consented success story (in-app, website,
  social media, etc.) is assumed to be a marketing/distribution decision
  made later, outside this BR, which covers only that consent can be
  captured and a story can exist as data.

**Traced to:** FR082–FR084 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-09

---

## BR20 — Digital-to-Real-World Introduction Transition
**Priority:** Must (elevated from Should — see DEC-003)
**Status:** Ready for Review
**Confidence:** Medium — the business need was identified directly by the
Product Manager during BR review (not sourced from the Master Requirements
Input or BRD drafts, which describe the journey only as far as "Meet →
Decide" without detailing what "Meet" requires of the product), and its
exact scope was deliberately kept narrow pending further design.

**Problem**
Once family involvement (BR13) and/or contact exchange (BR12) have
happened, candidates and families eventually move from digital interaction
toward a real-world introduction or meeting — but the module currently has
no defined business capability for that transition. Left entirely
undefined, two risks follow: candidates and families get no safety guidance
at the single highest-risk moment in the entire journey (meeting a stranger
in person), and there is no way to report what happened afterward, leaving
Safety Intelligence (BR14) blind to exactly the events it most needs
signal on.

**Proposed outcome**
Mangaly explicitly does not organize, chaperone, or manage real-world
meetings — that remains between the people and families involved. What
this BR does require: candidates (and, where involved, family) receive
optional, clear safety guidance before an in-person introduction (e.g.
meet in a public place, tell someone the plan, verify identity before
meeting where not already done); either party can, with consent, note that
an introduction/meeting occurred, distinct from any other event in the
connection's history; and either party can report a concern arising from a
real-world meeting through the same reporting path as any other safety
concern (BR14), explicitly including post-meeting incidents. The platform's
role ends at the introduction — Mangaly does not track, monitor, or manage
the relationship after a real-world meeting occurs, consistent with this
module's stated purpose (a matrimonial search product, not a relationship-
management product).

**Affected users and systems**
Candidate, Parent/authorized family participant (as introduced parties or
supporting family); builds on Contact Exchange (BR12) and Family
Involvement (BR13); feeds Safety Intelligence (BR14, as an additional
report entry point) and Accountability/Audit (BR15, for the optional
meeting-occurred note).

**Constraints**
- Safety guidance is informational and optional to act on — Mangaly cannot
  and must not require a meeting to occur in any particular way as a
  precondition of using the platform.
- Noting that a meeting occurred is opt-in and must not be inferable or
  auto-detected from other signals (e.g. contact exchange followed by
  reduced messaging) — consistent with this module's product invariant
  against inferring seriousness/status from activity signals (§21, §33).
- This BR must not expand into relationship-progress tracking, engagement/
  wedding planning features, or any ongoing relationship-management
  capability — those are explicit non-goals of a matrimonial *search*
  product.

**Out of scope (for this BR specifically)**
Mangaly organizing, chaperoning, or being present at any real-world
meeting (explicit non-goal); tracking relationship status or progress after
an introduction (explicit non-goal — see BR18 for the separate, deliberate
act of marking a search concluded); any platform-managed post-meeting
relationship feature.

**Worth check**
Every other BR in this module optimizes discovery, evaluation, and
digital-to-family stages of the journey, but the Master Requirements
Input's own "Meet → Decide" framing names real-world meeting as part of the
journey without this module offering any safety guidance or reporting path
specific to it — the single highest-physical-risk moment in the entire
product experience currently has zero explicit business requirement
attached to it. That is a genuine safety gap, not a nice-to-have; removing
this BR would leave Safety Intelligence (BR14) unable to receive signal
about exactly the incidents most likely to cause serious real-world harm.
Consistent with this module treating safety and trust as foundational
rather than optional (the same standard applied to BR14/BR15/BR16), this
capability is judged Must for responsible operation of the product even
though the purely digital product would still run without it.

**Quality gate (ISO 29148, adapted for business-level requirements — see
Set-level quality gate for the four-value scale)**
Necessary: Pass · Unambiguous: Conditional Pass — the boundary between
"safety guidance/reporting" (in scope) and "relationship management" (out
of scope) is stated but not yet tested against concrete FR scenarios ·
Complete: Pass · Singular: Pass · Feasible: Pass · Verifiable: Conditional
Pass — depends on FR defining what "safety guidance" concretely consists
of · Correct: Pass · Conforming: Pass

**Decisions**
- DEC-001 · In the context of this gap being raised in a Product Manager
  review with an explicit instruction to discuss before adding rather than
  add unilaterally, and the Product Manager then directing it be added, we
  wrote this BR narrowly — safety guidance, an opt-in meeting-occurred note,
  and a reporting entry point — over a broader "meeting coordination"
  capability (e.g. scheduling, location-sharing, chaperone arrangement),
  to close the identified safety-guidance/reporting gap without creating a
  new relationship-management surface the source documents never
  contemplated, accepting that if a broader capability is wanted later, it
  should be raised as its own explicit decision rather than assumed here.
- DEC-002 · In the context of this BR having no source-document citation
  and touching the single highest physical-risk moment in the product,
  facing a choice between Must and Should, we chose Should — over Must —
  because the core digital product (BR01–BR18) is fully functional without
  it and the exact safety-guidance content needs product/legal input this
  BR does not resolve, accepting that Impact Analysis (Step 6) or the
  Product Manager may later elevate this to Must once that content exists.
- DEC-003 · In the context of the Product Manager's final BR-approval review
  explicitly reopening DEC-002 — noting that "Must" has two different
  readings here, "Must for the core digital product to function" versus
  "Must for Mangaly to operate responsibly," and that Mangaly positions
  safety and trust as foundational to the product promise rather than
  optional decoration — the Product Manager decided this BR is Must, over
  leaving it Should. We chose this over DEC-002's original reasoning to
  align this BR's priority with the same foundational-safety standard
  already applied to BR14/BR15/BR16, accepting that the underlying
  uncertainty DEC-002 named (exact safety-guidance content still needs
  product/legal input) is unchanged by this priority elevation — Must here
  means this capability ships in V1 in some form, not that its content is
  now fully resolved.

**Assumptions**
- "Safety guidance" is assumed to be informational content (text/checklist)
  at this stage, not a platform-mediated live-safety feature (e.g. live
  location sharing); that would be a materially larger capability requiring
  its own explicit decision.

**Traced to:** FR085–FR088 (Step 2 Functional Requirements)

**Review history**
- (none yet)

**Approval:** Product Manager — [x] Approved — krishna kategaru, 2026-09-09
