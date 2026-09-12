# Mangaly — Master Requirements Input
Version: 1.0
Status: Approved Product Baseline
Product: ForKhatri — Mangaly
Audience: SDLC Agent Pipeline

## 1. Purpose

Mangaly is the matrimonial capability of ForKhatri, a platform for the Khatri/patjari community.

Mangaly modernises the process of finding a marriage partner without turning marriage into dating, swiping, popularity competition, or an AI-managed relationship.

Core philosophy:

> Marriage is the destination. Trust is the journey.

Mangaly should function like a trusted modern marriage-search handbook/tool: it gives candidates and participating families broad opportunity to discover eligible people, understand compatibility, evaluate evidence, communicate safely, involve family naturally, and make their own decision.

Mangaly facilitates introductions. It does not decide whom a person should marry and does not manage the resulting relationship.

---

# 2. Product Goals

Mangaly shall aim to:

1. Give eligible community members broad and meaningful opportunity to discover matrimonial partners.
2. Support both candidate-led and family-assisted discovery.
3. Treat parents as legitimate matrimonial participants, not secondary observers.
4. Let siblings and relatives contribute useful suggestions.
5. Make meaningful information available before a recipient must accept an introduction.
6. Build trust through evidence, verification, provenance, and accountability rather than reputation scores.
7. Allow progressive and voluntary sharing of additional personal information.
8. Support communication without requiring immediate personal contact exchange.
9. Reduce fraud, deception, grooming, harassment, blackmail, coercion, sexual abuse, and financial scams.
10. Keep user experience simple even when the underlying authorization/safety system is sophisticated.
11. Preserve individual agency while enabling family collaboration.
12. Use AI as assistance, not as the final matrimonial decision-maker.
13. Build V1 as thin, modular, replaceable layers so later requirements can be added, removed, or replaced safely.

---

# 3. Non-Goals

Mangaly is not:

- A dating app.
- A Tinder/swipe clone.
- A social popularity platform.
- A public biodata directory.
- An AI romantic companion.
- An AI that chooses a spouse.
- A Trust Score or Family Reputation Score.
- A public rating/review system for matrimonial participants.
- A system that forces phone-number exchange.
- A system that forces family involvement.
- A system that forces exclusivity.
- A system with a single "current match" or "seriousness" state.
- A family surveillance system.
- A product that intentionally withholds meaningful profile information to force acceptance or payment.
- A product that guarantees screenshots or external capture are impossible.
- A product that permanently stores conventional chat history as a core feature.

---

# 4. Core Product Principles

## 4.1 Human Decision

Mangaly helps people discover and understand; people decide.

## 4.2 Real-Life Matrimonial Model

The product should resemble how real matrimonial introductions work:

Discover → understand → express interest → introduce → know each other → involve family → exchange appropriate contact → meet → decide.

This is a conceptual journey, not a mandatory user-facing state machine.

## 4.3 Shared Journey + Individual Agency

Candidate and family can participate in the same matrimonial journey while retaining their own authority and privacy.

## 4.4 Relationship ≠ Permission

A family relationship does not automatically grant access to every piece of information or every action.

## 4.5 Suggestion ≠ Consent

A parent/sibling/relative can suggest a person without deciding on behalf of the candidate.

## 4.6 Initiation Authority ≠ Decision Authority

The person who discovers or initiates an introduction does not automatically control the final matrimonial decision.

## 4.7 Observed Behaviour ≠ Intention

Viewing a profile does not prove interest.
Interest does not prove commitment.
A suggestion does not prove consent.
A request does not prove seriousness.
A relationship does not prove permission.

## 4.8 Trust Is Evidence, Not a Score

Trust is represented by understandable evidence, verification, provenance, context, and accountable behaviour.

## 4.9 Privacy Is a System Property

Privacy should be built into the system rather than delegated to users through dozens of difficult settings.

## 4.10 Safety Is Separate From Verification

Verification establishes facts/evidence.
Safety Intelligence detects harmful or suspicious behaviour.
A verified person can still behave badly.

---

# 5. Actors

Mangaly shall support these conceptual actors:

- Candidate
- Parent
- Sibling
- Relative / trusted family member
- Guardian where legitimately applicable
- Community verifier
- Mangaly/admin verifier
- Mangaly administrator/operations
- Future Mangaly Agent / professional community marriage worker

Parent is a unified functional category. Mother and father are relationships within that category rather than separate product roles.

---

# 6. Home Circle

Home Circle is the digital representation of people who participate in helping a candidate find a matrimonial partner.

It is:

- A collaboration mechanism.
- An identity/relationship context.
- An authorization input.

It is not:

- A public family tree.
- A reputation system.
- A complete family directory.
- Automatic permission to inspect private activity.

## 6.1 Membership

A user shall be able to:

- Search another Mangaly user by username.
- Send an invitation/add request.
- Accept an invitation.
- Ignore an invitation.
- Report a false/inappropriate relationship claim.
- Remove/revoke an existing relationship where appropriate.
- Leave a Home Circle.
- Establish/use another Home Circle where appropriate.

Valid invitation paths include:

- Candidate → Parent
- Parent → Candidate
- Candidate → Sibling/family member
- Existing Home Circle participant → another participating family member/relative

## 6.2 Home Circle Behaviour

Parents may:

- Search broadly.
- Inspect profiles.
- Compare potential matches.
- Suggest people.
- Continue searching in parallel.
- Participate in family-side communication where authorized.

Candidates may:

- Search independently.
- Explore multiple people.
- Accept/decline introductions.
- Communicate privately.
- Decide when to involve family.

Siblings/relatives may:

- Search where appropriate.
- Identify potential people.
- Suggest potential matches to the family.

Family members may disagree. Mangaly shall not force resolution.

A candidate cannot be forced to remain in a Home Circle.

---

# 7. Authorization

Authorization shall be contextual and least-privilege.

The system shall distinguish:

Person → Relationship → Responsibility → Authorization/Scope → Consent → Collaboration → Audit

Important rules:

- Home Circle membership does not automatically grant all access.
- Parents do not automatically receive private candidate-to-candidate conversations.
- Siblings/relatives do not automatically gain decision authority.
- A prospective match/family does not automatically see the candidate's Home Circle.
- Candidate information and family information are separate concepts.
- Authorization is evaluated before consequential access or disclosure.

---

# 8. Privacy & Visibility

## 8.1 Core Rules

Mangaly shall:

- Provide meaningful information to help users make matrimonial decisions.
- Avoid deliberate teaser-profile UX.
- Separate candidate personal information from family information.
- Protect the social fact/pattern of marriage searching where unnecessary exposure could cause gossip or stigma.
- Avoid public profile-view counts.
- Avoid rejection counts.
- Avoid popularity/demand indicators.
- Separate visibility from searchability.
- Keep private candidate-to-candidate communication private by default.
- Support contextual sharing controls.
- Support pause/disengagement without unnecessary social signalling.
- Permit controlled safety exceptions when severe harm requires intervention.

## 8.2 Important Family Boundary

If a parent is searching for a groom/bride for their child, the prospective candidate should receive the relevant candidate profile information, not the candidate's entire family status/Home Circle.

The prospective family can receive appropriate family information only through deliberate, authorized sharing.

---

# 9. Profile

The profile is the main discovery/evidence surface.

The product should support, as appropriate:

- Identity/basic information.
- Photos.
- Optional video introduction.
- Education.
- Profession/career.
- Location/locality.
- Relocation expectations.
- Lifestyle.
- Food preferences.
- Travel.
- Movies/music.
- Hobbies.
- Sports/social preferences.
- Communication tendencies.
- Conflict tendencies.
- Independence.
- Family involvement expectations.
- Career/work-after-marriage expectations.
- Children/family-planning expectations.
- Living arrangement.
- Financial philosophy / practical life-stage compatibility.
- Pets.
- Other meaningful lifestyle factors.
- Partner preferences.
- Optional horoscope information.

Exact field schema and required/optional classification are implementation-stage decisions.

---

# 10. Discovery

Discovery is available to candidates and authorized family participants.

Discovery should support:

- Broad profile discovery.
- Locality.
- Community context.
- Practical geography.
- Partner preferences.
- Lifestyle relevance.
- Compatibility relevance.
- Verification/evidence context.
- Community-assisted discovery.

Mangaly shall not make popularity the primary ranking mechanism.

## 10.1 Community-Assisted Discovery

If a family knows a potentially suitable person but cannot directly access their profile, Mangaly may provide limited contextual hints sufficient to help identify the appropriate community/locality/intermediary route.

This is not a public teaser-profile model.

---

# 11. Matching & Compatibility

Mangaly separates:

1. Discovery — Who should I see?
2. Compatibility — Why might these people work well together?
3. Evidence — What do we actually know?
4. Human exploration — Do we want to know this person better?

## 11.1 Matching Inputs

Potential inputs include:

- Explicit partner preferences.
- Locality.
- Relocation.
- Lifestyle.
- Food.
- Hobbies.
- Travel.
- Media preferences.
- Sports/social preferences.
- Communication.
- Conflict tendencies.
- Independence.
- Family involvement.
- Career orientation.
- Work-after-marriage expectations.
- Children.
- Living arrangement.
- Financial philosophy.
- Life-stage compatibility.
- Personality signals.
- Verification/trust evidence.
- Optional horoscope.

## 11.2 Preference Philosophy

V1 shall:

- Respect stated preferences.
- Treat preferences as meaningful inputs.
- Allow intelligently selected exceptions when there is a meaningful compatibility reason.
- Explain why an exception was surfaced.
- Avoid assuming every preference has identical importance.

The exact hard/strong/weak preference taxonomy may evolve after product learning.

## 11.3 Compatibility Philosophy

Mangaly shall not assume that similarity equals compatibility.

Personality is a soft signal.

Compatibility should consider both alignment and meaningful differences.

No universal "87% compatible" or similar score shall be presented as objective truth.

## 11.4 Why This Match?

Recommendations should provide concrete explanations such as:

- Shared living arrangement expectations.
- Similar work-after-marriage expectations.
- Compatible family involvement expectations.
- Similar relocation direction.
- Compatible communication preferences.
- Meaningful lifestyle overlap.
- Important differences worth discussing.

The system shall distinguish verified facts from algorithmic inference.

## 11.5 Horoscope

Horoscope may be supported as an optional user-selected input.

It must:

- Remain optional.
- Not silently influence users who have not chosen it.
- Be clearly separated from evidence-based compatibility.
- Not be presented as scientific proof.

---

# 12. Personality Assessment

Mangaly may use a short, game-like assessment, targeted at approximately five minutes or less.

Potential dimensions:

- Communication.
- Conflict.
- Independence.
- Family involvement.
- Career orientation.
- Decision-making.
- Money attitudes.
- Social preferences.
- Marriage expectations.

It is not a clinical diagnosis.

The assessment supports understanding and compatibility; it does not label people as good/bad spouses.

---

# 13. Trust & Verification

## 13.1 Trust Model

Mangaly shall not create:

- Trust Score.
- Family Reputation Score.
- Public reputation ranking.
- Public participant ratings.

Instead, trust is represented through evidence.

## 13.2 Verification Layers

Conceptual layers:

1. Account authenticity.
2. Identity/age.
3. Selected profile facts.
4. Home Circle relationship.
5. Community/factual verification.
6. Mangaly operational verification where appropriate.

## 13.3 Verification Circle

Verification Circle is factual confirmation, not reputation.

Allowed responses:

- Yes
- No
- Don't know
- Cannot confirm

Safeguards are required against:

- Gossip.
- Malicious confirmation.
- Retaliation.
- Fake witnesses.
- False claims.

If suitable community verification is unavailable, Mangaly/admin verification may be requested.

## 13.4 Verification Provenance

A verification record should conceptually support:

- What was verified.
- Method/source category.
- Time.
- Appropriate provenance.
- Evidence control.
- Freshness.
- Expiry/reverification where the fact can change.

Verification does not certify:

- Character.
- Safety.
- Honesty.
- Marital suitability.

---

# 14. Accountability

For consequential actions, Mangaly should be able to determine:

- Who acted.
- In what capacity.
- On whose behalf, where relevant.
- What action occurred.
- What person/object was affected.
- What authorization applied.
- What consent was present/required.
- When it happened.
- Whether it was revoked/changed/disputed.

Accountability is internal system integrity.

It is not permission for family surveillance.

---

# 15. Connection Request

Core flow:

Discover → Request → Review → Accept/Decline → Selective Sharing → Continue Knowing Each Other → Optional Contact Exchange → Family Involvement

## 15.1 Incoming Request

When a request arrives:

- Recipient receives the request.
- Recipient can inspect meaningful profile information.
- Recipient can inspect relevant compatibility context.
- Recipient can inspect available trust/evidence signals.
- Recipient can accept or decline.
- Acceptance is not required to reveal meaningful basic profile information.

## 15.2 Acceptance

Acceptance means:

> I am willing to explore this connection.

Acceptance does not mean:

- Commitment.
- Exclusivity.
- Seriousness.
- Relationship declaration.
- Marriage intent.
- Automatic contact exchange.
- Automatic Home Circle exposure.

---

# 16. Selective Sharing

After acceptance, each participant controls additional disclosure.

Possible shareable categories:

- Additional photos.
- Video introduction.
- Additional personal information.
- Phone number.
- Email.
- Parent/family contact details where authorized.
- Other deliberate shareable information.

Rules:

- Sharing is contextual.
- Sharing one category does not authorize all categories.
- The user should understand what will be shared, with whom, and what it does not imply.
- Avoid a large permanent privacy-settings burden.

Core principle:

> Acceptance opens the door; it does not open everything inside the house.

---

# 17. Communication

People should be able to get to know one another before exchanging personal phone numbers.

Requirements:

- Private in-platform communication can precede contact exchange.
- Phone numbers remain hidden until voluntarily shared.
- Contact exchange is recipient-controlled.
- Multiple conversations may coexist.
- Mangaly does not manage the resulting relationship.
- No seriousness score.
- No exclusivity requirement.
- No single current-match state.

---

# 18. Ephemeral Communication

Mangaly does not intend conventional persistent chat history as a core product feature.

The system may retain minimal events necessary for:

- Consent.
- Authorization.
- Security.
- Abuse prevention.
- Safety.
- Accountability.

Severe safety incidents may require tightly controlled evidence retention.

Mangaly cannot guarantee that users cannot capture content through screenshots, screen recording, another device, photography, or other external means.

---

# 19. Contact Exchange

Contact exchange is deliberate.

A candidate, parent, or appropriately authorized participant may request contact information where context permits.

The recipient:

- Decides whether to share.
- Decides what contact method to share.

Exchange:

- Is internally attributable.
- Does not imply commitment.
- Does not imply exclusivity.
- Does not automatically reveal other contact details.

---

# 20. Family Involvement in a Connection

Family involvement is deliberate.

Requirements:

- Candidate can choose when to involve Home Circle in a connection.
- Parents may already be involved in discovery.
- Private candidate-to-candidate communication remains private unless deliberately shared.
- Family-to-family introduction is a separate step.
- Prospective families do not automatically receive another family's Home Circle.

---

# 21. Parallel Exploration

Mangaly intentionally supports multiple legitimate matrimonial explorations.

A user may:

- Like multiple profiles.
- Express interest in multiple people.
- Communicate with multiple people.
- Request multiple contacts.
- Continue discovery while another connection exists.

Parents may evaluate multiple possibilities.

There is no:

- Current match.
- Seriousness state.
- Exclusivity state.
- Popularity state.

Mutual Interest means both sides have expressed willingness to explore.

It does not mean commitment, exclusivity, relationship, seriousness, or marriage.

---

# 22. Safety Intelligence

Safety is a separate layer operating alongside trust and communication.

It should identify patterns associated with:

- Fake profiles.
- Deception.
- Grooming.
- Blackmail.
- Harassment.
- Vulgarity.
- Threats.
- Sexual abuse.
- Financial manipulation.
- Romance scams.
- Coercion.
- Suspicious escalation.
- Malicious links.
- Off-platform pressure.
- Repeated unwanted contact.

Graduated response:

1. Invisible monitoring where appropriate.
2. Warning/nudge.
3. Restriction/block.
4. Controlled human investigation.
5. Legal/emergency escalation for severe cases.

Routine human reading of private communication is not the objective.

Safety access must be tightly controlled.

---

# 23. Screen / Capture Protection

Mangaly should use defense-in-depth where technically possible:

- iOS screen-capture state detection/response where applicable.
- Android FLAG_SECURE where appropriate.
- Other platform controls as available.

These are risk-reduction measures, not guarantees.

Physical second-device capture cannot be reliably prevented.

Dynamic visual/RGB/temporal techniques may be researched as an additional defensive measure, but must never be represented as guaranteed protection.

---

# 24. AI Requirements

AI may assist with:

- Discovery.
- Recommendation.
- Compatibility explanation.
- Profile understanding.
- Safety intelligence.
- Routing/community assistance.

AI shall not:

- Decide whom a person should marry.
- Claim certainty about character.
- Claim certainty about honesty.
- Claim to predict marriage success.
- Act as a romantic partner.
- Act as a definitive truth detector from language.
- Present inference as verified fact.
- Create opaque human-worth rankings.

AI components must be independently replaceable.

---

# 25. Fairness & Exposure

Mangaly must guard against:

- Popularity bias.
- Wealth/status bias.
- Education/profession ranking as human worth.
- Locality bias becoming unfair exclusion.
- Community preference becoming hidden hierarchy.
- Recommendation bubbles.
- Historical user bias being silently amplified.
- Sparse profiles being permanently disadvantaged.
- Unnecessary sensitive-attribute inference.

Legitimate user preferences may influence discovery, but recommendation logic must not silently turn those preferences into human-worth rankings.

---

# 26. Notifications

The system should support useful notifications for:

- Requests.
- Acceptances/declines where appropriate.
- Suggestions.
- Sharing events.
- Contact requests.
- Family collaboration events.
- Important safety actions.

Notifications must not expose private activity to unintended people.

Safety notifications should reflect urgency without unnecessary social signalling.

---

# 27. Admin & Operations

Mangaly operations shall support controlled:

- Identity/profile verification.
- Verification Circle review.
- False relationship investigation.
- Abuse reports.
- Fraud investigation.
- Restrictions/blocks.
- Safety investigation.
- Appeals where applicable.
- Legal/emergency escalation.
- Audit of consequential administrative actions.

Operator access shall follow need-to-know and least privilege.

Operators should not gain unrelated private communication access merely because they are administrators.

---

# 28. Agent Layer — Future

Mangaly Agents are intended to support existing Samaj/community marriage professionals.

They are not intended to eliminate their livelihood.

Agent requirements:

- Stronger professional identity verification.
- Scoped access.
- Attributable actions.
- Revocable permissions.
- Auditability.
- Need-to-know access.
- No pay-to-win trust manipulation.
- Commercial model may evolve independently.

---

# 29. Multilingual / Community Context

Mangaly is intended for an Indian community context.

The product should be designed for future multilingual support and culturally appropriate communication.

Language/localisation must not change authorization, privacy, trust, or safety principles.

---

# 30. V1 Thin-Layer Architecture Principle

The product shall be designed as replaceable layers.

Conceptual layers include:

- Identity.
- Profile.
- Home Circle.
- Authorization.
- Privacy.
- Discovery.
- Compatibility.
- Trust/Verification.
- Connection.
- Selective Sharing.
- Communication.
- Safety.
- Notifications.
- Operations.
- Future Agent capabilities.

A future implementation may combine or split technical components differently, but the product boundaries should remain understandable.

A replacement of one implementation should not require rewriting unrelated stable foundations.

---

# 31. V1 Philosophy

Build the smallest version that supports the real matrimonial journey safely.

Preferred V1 approach:

- Simple identity.
- Meaningful profile.
- Home Circle.
- Basic discovery.
- Transparent matching rules/signals.
- Trust/verification foundation.
- Request/accept flow.
- Selective sharing.
- Private communication.
- Optional contact exchange.
- Family involvement.
- Reporting/safety.
- Internal accountability.

Do not prematurely build sophisticated ML, elaborate relationship states, or excessive configuration.

Observe real usage before increasing complexity.

---

# 32. Core User Journey

The complete conceptual journey:

Join
→ Establish identity
→ Build Home Circle if desired
→ Build meaningful profile
→ Discover
→ Understand
→ Request
→ Review
→ Accept/Decline
→ Selectively Share
→ Communicate
→ Optionally Exchange Contact
→ Involve Family
→ Meet in real life
→ Decide

The journey may be repeated, paused, or exited.

It is not a mandatory state machine.

---

# 33. Product Invariants

The following are high-priority product invariants:

- Marriage is the purpose; engagement is not the objective.
- Human judgment remains final.
- Relationship ≠ permission.
- Suggestion ≠ consent.
- Initiation authority ≠ decision authority.
- Observed behaviour ≠ intention.
- Request ≠ acceptance.
- Acceptance ≠ contact exchange.
- Contact exchange ≠ commitment.
- Verification ≠ character certification.
- Mutual Interest ≠ seriousness/exclusivity.
- Home Circle ≠ family directory.
- Accountability ≠ surveillance.
- Visibility ≠ searchability.
- AI assistance ≠ autonomous matrimonial decision-making.
- Trust ≠ score.
- Privacy ≠ a settings burden.
- Safety ≠ verification.
- Multiple matrimonial explorations are legitimate.
- Candidate agency must remain intact.
- Parents are legitimate matrimonial participants.

---

# 34. Requirements Classification

When converting this input into the SDLC pipeline:

### Product Invariants
Treat the Core Product Principles and Product Invariants as constraints that downstream agents must preserve unless a formal Change Request supersedes them.

### Functional Requirements Candidates
Convert user-visible/system behaviors into Business Requirements and then Functional Requirements through the pipeline. Do not copy this document mechanically into FRs.

### Architecture Constraints
Thin-layer modularity, contextual authorization, least privilege, privacy-by-design, evidence provenance, auditability, and replaceability are architectural constraints to be refined by the architecture agents.

### Research Areas
The following should be researched when they become relevant:
- Personality assessment methodology.
- Recommendation fairness.
- Safety/grooming/scam detection.
- Ephemeral communication implementation.
- Screen/capture mitigation.
- Verification providers.
- Indian privacy/data-protection implementation.
- Multilingual UX.
- Community-assisted discovery.
- Agent operations/economics.

### Deferred Decisions
Exact schemas, field-level permissions, UI layouts, ranking weights, model selection, retention periods, provider selection, notification catalogue, and monetization are intentionally not frozen here.

---

# 35. Definition of a Correct Downstream Interpretation

Downstream agents must not reinterpret Mangaly as:

- Dating.
- Swipe matching.
- A reputation marketplace.
- A popularity contest.
- Parent-only matrimonial software.
- Candidate-only matrimonial software.
- AI spouse selection.
- A family surveillance system.

If an implementation decision appears to conflict with a product invariant, the agent must flag it rather than silently changing the invariant.

---

# 36. Change Management

This document is the current product baseline.

Future changes shall:

1. Identify the affected requirement.
2. State why the change is needed.
3. Analyse downstream impact.
4. Preserve traceability.
5. Record rejected alternatives where appropriate.
6. Avoid silently overwriting prior decisions.
7. Use the project's Change Request process for changes to sealed requirements.

The architecture should make changes cheap where possible.

---

# 37. V1 Success

Mangaly V1 is successful if a real candidate/family can:

- Establish a usable identity.
- Build a Home Circle.
- Create a meaningful profile.
- Discover relevant people.
- Understand basic compatibility.
- See useful trust evidence.
- Send/receive matrimonial requests.
- Accept/decline.
- Selectively share additional information.
- Communicate privately.
- Optionally exchange contact details.
- Involve family deliberately.
- Report unsafe/fraudulent/abusive behaviour.
- Continue multiple legitimate explorations.
- Reach real-world introductions without Mangaly pretending to make the marriage decision.

End of Master Requirements Input.
