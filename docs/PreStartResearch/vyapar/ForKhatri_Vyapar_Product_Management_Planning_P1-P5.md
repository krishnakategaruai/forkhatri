# ForKhatri — Product Management Planning Framework
## Module-Level Product Source of Truth — Vyapar

**Document purpose:** Define the product-management decisions that must be settled before Vyapar enters the downstream requirements, UX, UI, QA, architecture, and implementation pipeline.

**Current target module:** Vyapar  
**Parent product:** ForKhatri  
**Product role:** Product Manager / Product Director  
**Document status:** Draft — Product Manager review required

---

# 1. Operating Model

ForKhatri is the parent umbrella. Each module is developed independently as a product capability and later becomes part of the larger ForKhatri ecosystem.

For the current work:

> **We are not planning “ForKhatri” as one large product. We are planning and building the Vyapar module as an independent product capability that must eventually fit cleanly under ForKhatri.**

Therefore every product decision in this document must answer two questions:

1. **What is correct for Vyapar itself?**
2. **Will this decision allow Vyapar to become a clean part of ForKhatri later?**

The second question is a compatibility constraint, not a reason to design every ForKhatri module now.

## 1.1 Product-management ownership

The Product Manager owns:

- the problem being solved
- target users and their needs
- product purpose
- product principles
- product behavior and rules
- scope and boundaries
- value proposition
- prioritization
- product economics and revenue logic
- domain concepts and their meaning
- user journeys at the product level
- business policies
- trust principles
- success metrics
- assumptions and decisions
- what the product must and must not do

The Product Manager does **not** own:

- detailed technical architecture
- database/ER design
- implementation technology
- security architecture
- detailed visual design
- component libraries
- pixel-level UI
- automated test implementation
- deployment engineering

Those are intentionally handed to the downstream specialist agents.

---

# 2. The Product Planning Chain

Vyapar follows this product-management sequence before implementation:

```text
P1 — Problem Discovery & Research
        ↓
P2 — Product Strategy
        ↓
P3 — Product Definition
        ↓
P4 — Domain / Capability Definition
        ↓
P5 — Product Journey & Behavioral Definition
        ↓
Step 1 — Business Requirements
        ↓
Step 2 — Functional Requirements
        ↓
Step 3 — UX
        ↓
Step 4 — UI
        ↓
Step 5 — Test Scenarios
        ↓
Step 6+ — Architecture / Technical / Security / Implementation / QA / Ops
```

P1–P5 are the **Product Management layer**.

The downstream agents are responsible for translating these decisions into progressively more detailed artifacts.

This prevents a common failure mode:

> Requirements are written before the product itself has been sufficiently decided, causing later agents to fill product gaps with their own assumptions.

---

# P1 — Problem Discovery & Research

## Objective

Establish what Vyapar should solve, for whom, why the problem matters, and what evidence supports the product direction.

P1 is not a feature brainstorming phase.

The central question is:

> **What problem deserves to exist as Vyapar?**

## P1.1 Product problem

Vyapar exists to solve the problem of **opportunity visibility and discovery within the community**.

A person may have:

- skills
- experience
- knowledge
- a profession or trade
- services
- resources
- availability

while simultaneously:

- looking for work
- looking for projects
- looking for customers
- looking for business opportunities
- looking for learning
- looking for collaboration
- looking for additional income
- being open to opportunities without actively searching

The problem is that opportunities and capable people are fragmented across:

- personal networks
- WhatsApp groups
- community conversations
- local networks
- public sources
- employer sources
- government sources
- professional platforms
- informal referrals

As a result, relevant opportunities can remain invisible to people who could benefit from them.

## P1.2 Core problem statement

> **People should not lose relevant opportunities simply because those opportunities were outside their immediate network or because they did not know where to look.**

Vyapar therefore focuses on improving the connection between:

```text
PERSON
  ↓
Capability + Intent + Constraints + Trust
  ↓
OPPORTUNITY
  ↓
Relevant Discovery
  ↓
Action
  ↓
Successful Connection
```

## P1.3 What “opportunity” means

The canonical product concept is:

> **Opportunity**

A job is only one type of opportunity.

Vyapar may eventually support:

- employment
- freelance work
- projects
- contracts
- apprenticeships
- internships
- local work
- professional assignments
- business opportunities
- training and learning
- government opportunities
- community opportunities
- collaboration and partnership
- customer/client acquisition
- service opportunities
- other future opportunity types

The product must therefore not be architected or described as a conventional “job board”.

## P1.4 Target users

Vyapar serves multiple sides of an opportunity network.

### Opportunity seeker / participant

A person who wants to:

- discover opportunities
- find work
- find projects
- find customers
- learn
- collaborate
- grow income
- explore possibilities

### Opportunity provider

A person, business, organization, or community participant who:

- creates an opportunity
- shares an opportunity
- forwards an opportunity
- needs someone with a capability
- wants to reach relevant people

### Community connector

A person who may not create an opportunity themselves but helps distribute useful opportunities through the community.

### Business / organization

A provider that wants to use Vyapar as a reliable community opportunity channel.

## P1.5 Key research conclusions

Product research should establish evidence around:

1. opportunity marketplaces
2. marketplace liquidity
3. matching and recommendation
4. local/community network effects
5. onboarding and preference elicitation
6. trust and reputation
7. privacy
8. opportunity freshness
9. monetization of distribution rather than discovery
10. community-generated supply

The product should learn from comparable products, but must not copy their mental model blindly.

Comparable categories include:

- job marketplaces
- freelance marketplaces
- local service marketplaces
- professional networks
- community platforms
- matrimonial/network products where trust and discovery are important

## P1.6 Research principles

Research must distinguish:

- observed fact
- external market precedent
- user evidence
- product inference
- product hypothesis
- unresolved question

No hypothesis should silently become a requirement.

## P1.7 Research questions

The Product Manager should continuously reduce uncertainty around:

### User
- Who has the strongest pain?
- Who contributes opportunities?
- Who benefits most from better distribution?
- What causes people to ignore or miss opportunities?

### Behavior
- Where do people currently discover opportunities?
- How do they share them?
- What makes them trust an opportunity?
- What makes them act?

### Matching
- Which attributes actually determine relevance?
- How important are locality, capability, intent, timing and compensation?
- Which constraints are hard eligibility rules?
- Which are soft preferences?

### Trust
- What signals create confidence?
- What should be verified?
- What must remain private?
- How should new users participate without being disadvantaged?

### Economics
- Who receives economic value?
- Who is willing to pay?
- What value can be monetized without damaging liquidity?

## P1.8 P1 output

P1 should result in:

- validated problem statement
- target user groups
- user/problem evidence
- competitive/market research
- opportunity landscape
- major pain points
- major constraints
- initial hypotheses
- unresolved questions
- research-backed product principles
- decision log

P1 does **not** produce detailed BRs, FRs, UX, UI, ER models or technical architecture.

---

# P2 — Product Strategy

## Objective

Turn the validated problem into a deliberate product direction.

The central question is:

> **What should Vyapar become, and what will we deliberately not build?**

## P2.1 Product mission

> **Help every community member discover opportunities relevant to their capabilities, needs, location and circumstances — and help useful opportunities reach the people who can act on them.**

## P2.2 Product vision

Vyapar should become the community's **opportunity network**, not merely a place where people search listings.

Long-term:

```text
Opportunity discovery
        +
Capability discovery
        +
Community distribution
        +
Trust
        +
Intelligent matching
```

## P2.3 Strategic product principles

### Principle 1 — Opportunity, not jobs

The product must treat jobs as one opportunity type rather than defining the entire system around employment.

### Principle 2 — Discovery before monetization

Relevant opportunity discovery should remain accessible.

Monetization should primarily accelerate or enhance economic value rather than hide relevant opportunities from users.

### Principle 3 — Community supply is strategic

Community-generated and community-shared opportunities are a core differentiator.

### Principle 4 — Relevance over volume

The product should optimize for:

> “This is useful to me.”

not:

> “There are many listings.”

### Principle 5 — Eligibility before ranking

Hard eligibility conditions must be separated from softer relevance ranking.

A paid opportunity must not become eligible merely because it is paid.

### Principle 6 — Explainability

Users should understand why an opportunity is being shown.

Avoid false precision such as:

> “93% AI Match”

Prefer:

> “Why you're seeing this”
> - Matches your accounting experience
> - Within your preferred locality
> - Part-time
> - Recently posted

### Principle 7 — Trust is infrastructure

Trust must influence participation and safety without becoming a popularity contest.

Payment must never purchase reputation.

### Principle 8 — Privacy by default

Capability visibility and “looking for opportunity” status should be separable.

A person can publicly state:

> “I am an accountant.”

without publicly exposing:

> “I am currently looking for work.”

### Principle 9 — Progressive complexity

The user should receive value before being asked for extensive profile information.

### Principle 10 — Community density creates value

The strategic flywheel is:

```text
More members
    ↓
More known capabilities
    ↓
More opportunities
    ↓
Better coverage
    ↓
Better matches
    ↓
More successful connections
    ↓
More trust
    ↓
More participation
    ↓
More opportunities
```

## P2.4 Product differentiation

Vyapar should differentiate through the combination of:

- community context
- opportunity breadth
- capability-aware discovery
- local relevance
- community-generated opportunities
- transparent matching
- trust
- distribution
- eventual network intelligence

The goal is not to compete feature-for-feature with large global marketplaces.

## P2.5 Product lifecycle strategy

Vyapar should mature through:

```text
Structured
   ↓
Relevant
   ↓
Adaptive
   ↓
Intelligent
   ↓
Networked
```

### V1 — Structured

- structured opportunities
- capability profile
- intent
- constraints
- search
- deterministic matching
- community distribution
- trust foundation

### V1.5 — Adaptive

- screenshot/URL/text ingestion
- better preference learning
- freshness
- better distribution
- behavioral feedback

### V2 — Intelligent

- semantic retrieval
- capability graph
- richer recommendation
- network signals

### V3 — Networked

- reverse discovery
- predictive opportunity discovery
- richer network intelligence
- advanced matching

Do not build V3 mechanisms into V1 merely because they are strategically attractive.

## P2.6 Strategic non-goals for V1

Vyapar V1 should not become:

- a generic social network
- a conventional job board
- a full freelancer escrow marketplace
- a full recruitment ATS
- a financial marketplace
- a reputation-only network
- a heavy AI chatbot product
- a scraping-dependent aggregation product

AI may assist the product, but the product value must remain available through normal UI and deterministic domain behavior.

## P2.7 Revenue strategy

Core principle:

> **Keep opportunity discovery free. Monetize additional economic value created around the opportunity network.**

Current monetization scope:

### A — Core monetization
- free community access
- opportunity boost / paid distribution
- business membership
- community/opportunity campaigns
- qualified response / qualified introduction
- business passport

### B — Advertising and sponsorship
- relevant advertising
- sponsored opportunities
- sponsored digests
- sponsored categories
- sponsored opportunity pools
- community brand sponsorship

### C — Intelligence
- opportunity intelligence
- aggregated skill/opportunity demand intelligence
- business analytics
- market/community insights

### D — Membership
- ForKhatri Plus
- business membership
- family/household membership

Pricing values remain hypotheses until validated through experiments.

## P2.8 Monetization guardrail

Payment should change **distribution or commercial capability**, not fundamental relevance eligibility.

For example:

```text
Organic opportunity
        ↓
Relevant users
        ↓
Optional paid acceleration
```

not:

```text
Pay more
  ↓
Show irrelevant opportunity
  ↓
Override eligibility
```

## P2.9 P2 output

P2 should produce:

- product mission
- vision
- product principles
- differentiation
- strategic scope
- strategic non-goals
- product lifecycle
- monetization strategy
- trust/privacy principles
- success model
- major product decisions
- strategic assumptions

---

# P3 — Product Definition

## Objective

Define exactly how Vyapar behaves as a product before detailed requirements are written.

The central question is:

> **What are the core product concepts, rules, behaviors and boundaries that downstream agents must preserve?**

---

## P3.1 Core product mental model

```text
PERSON
 ├── CAN DO / CAN OFFER
 │    ├── skills
 │    ├── knowledge
 │    ├── experience
 │    ├── profession/trade
 │    ├── services/resources
 │    └── availability
 │
 ├── WANTS / NEEDS
 │    ├── work
 │    ├── projects
 │    ├── business
 │    ├── customers
 │    ├── learning
 │    ├── collaboration
 │    └── additional income
 │
 ├── CONDITIONS
 │    ├── location
 │    ├── work mode
 │    ├── timing
 │    ├── compensation/value
 │    ├── eligibility
 │    └── constraints
 │
 └── TRUST / PRIVACY

             ↓

     VYAPAR OPPORTUNITY ENGINE

             ↑

        OPPORTUNITY
```

## P3.2 Canonical domain object

The canonical object is:

> **Opportunity**

Opportunity types are extensible.

The product must not create independent product logic for every opportunity type when a universal behavior can be shared.

Universal opportunity lifecycle:

```text
DISCOVERED
    ↓
NORMALIZED
    ↓
VALIDATING
    ↓
ACTIVE
    ↓
STALE
    ↓
EXPIRED / CLOSED
```

## P3.3 Opportunity structure

An opportunity may contain:

- title
- type
- description
- provider
- capability requirements
- eligibility
- location
- work mode
- timing
- compensation/value
- application/response method
- source
- source URL
- provenance
- published date
- freshness
- expiration/deadline
- trust signals
- status

The exact technical representation belongs downstream.

## P3.4 Person model

A Vyapar profile is not primarily a resume.

It is a **living opportunity model**.

### Capability

“What can I do or offer?”

Includes:

- skills
- knowledge
- profession/trade
- experience
- services
- resources
- education
- certifications
- languages
- portfolio
- things the person can teach or help with

### Intent

“What do I want or need?”

Possible states:

- Looking for
- Open to
- Curious about
- Not interested in

### Constraints

Examples:

- locality/radius
- remote/on-site/hybrid
- availability
- timing
- compensation
- relocation
- night work
- unpaid work
- commission-only work
- exclusions

## P3.5 Privacy behavior

Separate:

### Capability visibility

Example:

> “Accountant”

### Opportunity-seeking state

Example:

> “Looking for work”

The second may be private by default.

Sensitive personal information should not become a ranking signal merely because it exists in a profile.

## P3.6 Matching behavior

The product's matching sequence is:

```text
Opportunity
    ↓
Structure
    ↓
Retrieve candidates
    ↓
Hard eligibility
    ↓
Soft relevance scoring
    ↓
Rank
    ↓
Diversify
    ↓
Distribute
```

### Hard constraints

Examples:

- required certification
- legal eligibility
- required locality
- mandatory work mode
- deadline
- explicit provider restriction

Failure of a hard constraint should normally remove the opportunity from that candidate's eligible set.

### Soft signals

Examples:

- skill similarity
- intent fit
- location convenience
- availability fit
- compensation preference
- experience fit
- freshness
- trust
- personal preferences

V1 should use explainable, configuration-driven rules rather than opaque machine-learning ranking.

## P3.7 “Why am I seeing this?”

Every meaningful recommendation should be explainable in human terms.

Possible explanation categories:

- capability match
- intent match
- location match
- timing match
- work-mode match
- experience/eligibility match
- freshness
- community relevance

## P3.8 Discovery behavior

The discovery experience should conceptually support:

- For You
- Explore Possibilities
- Near You
- Community
- Public/Government
- Search

The product should not assume that every user knows exactly what they want.

A user should be able to say:

> “I don't know what I'm looking for; I just want to find opportunities.”

This is strategically important because discovery itself is part of the product value.

## P3.9 Opportunity creation behavior

A single creation model should support:

```text
Create
Share
Upload
```

A user may provide:

- structured information
- pasted text
- URL
- screenshot/image

The product may structure the input, but must not invent uncertain facts.

Important fields should be confirmed before publication.

## P3.10 Opportunity response behavior

The product should use a universal conceptual action:

> **Opportunity Response**

Depending on opportunity type, this may manifest as:

- Apply
- Respond
- Express interest
- Contact
- Submit proposal
- Register
- Apply externally

The underlying product concept remains consistent.

## P3.11 Feedback behavior

Users should be able to:

- save
- hide
- mark not interested
- share
- report
- respond
- record outcome where appropriate

Feedback should improve relevance without silently changing important user preferences.

For example:

> “Not interested because it requires night work.”

may become a suggestion to update a preference, rather than silently rewriting the profile.

## P3.12 Trust behavior

Trust signals may include:

- verified identity
- completed work
- successful outcomes
- feedback
- reports
- disputes
- cancellations
- account age
- policy violations
- source quality
- freshness

Rules:

- no reputation should not equal bad reputation
- new users must still receive opportunities
- feedback should relate to actual interactions
- reports and ratings are separate
- payment must not purchase reputation
- anti-gaming protection is required
- retaliation must be considered

## P3.13 Distribution behavior

Distribution is a first-class product capability.

Relevant opportunities may reach users through:

- in-product discovery
- notifications
- digests
- community distribution
- sharing
- targeted business campaigns

The product should optimize for:

> relevant reach

rather than:

> maximum reach.

## P3.14 Freshness

Opportunity relevance declines when information becomes stale.

Therefore freshness is part of product behavior, not merely an engineering concern.

Users should be able to understand whether an opportunity is:

- recent
- verified recently
- approaching deadline
- stale
- expired

## P3.15 Zero-result behavior

A zero result should not simply say:

> “No opportunities found.”

The product should help users widen discovery, for example:

- wider locality
- remote
- adjacent capability
- community opportunities
- public/government opportunities
- broader opportunity type

The user remains in control.

## P3.16 Product success model

Primary product metrics:

### Opportunity Coverage

Percentage of active members for whom Vyapar can identify at least one relevant opportunity.

### Relevant Discovery Rate

Percentage of surfaced opportunities judged relevant by the user or subsequent behavior.

### Opportunity Action Rate

Percentage of relevant discoveries producing a meaningful action.

### Successful Connection Rate

Percentage of actions resulting in a meaningful connection.

### Completion Rate

Percentage of connections that reach a meaningful outcome where measurable.

### Community Opportunity Reach

Percentage of relevant community opportunities reaching eligible members.

### Time to First Relevant Opportunity

Time from onboarding/activation to the first meaningful opportunity discovery.

### Profile-to-value time

Time between starting Vyapar and receiving meaningful value.

Secondary metrics:

- false-positive relevance
- user correction rate
- opportunity freshness
- notification fatigue
- report/dispute rates
- provider ROI
- business activation
- business conversion
- retention
- boost repeat
- campaign repeat
- MRR/ARR
- contribution margin
- CAC/LTV

---

# P4 — Domain & Capability Definition

## Objective

Define the stable product concepts that downstream Business Requirements and Functional Requirements must use consistently.

This is **business/domain definition**, not database design.

## P4.1 Core capability areas

Vyapar should be understood through these business capabilities:

1. **Member Opportunity Profile**
2. **Capability Management**
3. **Intent & Preference Management**
4. **Opportunity Creation**
5. **Opportunity Intake / Sharing**
6. **Opportunity Structuring**
7. **Opportunity Discovery**
8. **Eligibility**
9. **Matching**
10. **Ranking**
11. **Distribution**
12. **Opportunity Response**
13. **Opportunity Activity**
14. **Trust & Reputation**
15. **Reporting & Safety**
16. **Opportunity Freshness**
17. **Business Participation**
18. **Commercial Distribution**
19. **Opportunity Intelligence**

These are conceptual capabilities. They are not automatically technical services.

## P4.2 Stable terminology

Downstream documents should preserve these terms:

| Term | Product meaning |
|---|---|
| Person / Member | A community participant using Vyapar |
| Capability | Something a person can do, provide or offer |
| Intent | What a person wants, needs, or is open to |
| Constraint | A condition affecting opportunity suitability |
| Opportunity | The universal unit of economic/professional/community possibility |
| Provider | Person/business/organization offering an opportunity |
| Eligibility | Hard conditions that determine whether an opportunity can be considered |
| Relevance | Degree to which an opportunity fits a person |
| Match | Result of relating a person and opportunity |
| Distribution | Delivering an opportunity to relevant people |
| Response | A person's action toward an opportunity |
| Outcome | Result after response/connection |
| Trust signal | Evidence supporting confidence in a person/opportunity |
| Freshness | Confidence that opportunity information remains current |

## P4.3 Ownership principle

One product concept must have one clear business owner.

For example:

- Opportunity is owned by Vyapar.
- A downstream module may consume opportunity information, but should not independently redefine what an Opportunity means.

This principle protects ForKhatri from cross-module semantic drift.

## P4.4 ForKhatri integration principle

Vyapar should be independently understandable and usable.

Future ForKhatri modules may consume or contribute information through agreed boundaries.

Examples:

```text
ForKhatri Dashboard
        ↓
Vyapar
```

or:

```text
Vyapar
  ↓
ForKhatri member profile / ecosystem
```

But the detailed integration contract is intentionally deferred to architecture.

---

# P5 — Product Journeys & Behavioral Definition

## Objective

Define the major user journeys and product behavior at a level sufficient for Step 1 Business Requirements.

This is not visual UX design.

It defines:

- why the journey exists
- what the product does
- what decisions it makes
- what the user can accomplish
- what happens when things go wrong
- what should never happen

## P5.1 Primary journey — Discover an opportunity

```text
Join Vyapar
    ↓
Tell Vyapar what help is wanted
    ↓
Tell Vyapar what the person can do/offer
    ↓
Tell Vyapar what they are looking for/open to
    ↓
Set relevant location/constraints
    ↓
Receive opportunities
    ↓
Understand why they are relevant
    ↓
Open opportunity
    ↓
Respond / save / share / hide
    ↓
Track activity
```

The critical product principle:

> **Value must appear before profile completion becomes a burden.**

## P5.2 Secondary journey — Create an opportunity

```text
Create / Share / Upload
        ↓
Provide source information
        ↓
Vyapar structures opportunity
        ↓
User confirms important information
        ↓
Opportunity becomes active
        ↓
Eligibility/relevance is determined
        ↓
Opportunity is distributed
        ↓
Responses arrive
        ↓
Provider manages outcome
```

## P5.3 Journey — Discover without knowing exactly what you want

```text
User says:
“I don't know what I'm looking for.”
        ↓
Vyapar asks lightweight preference questions
        ↓
Uses capability + broad intent + context
        ↓
Shows varied relevant opportunities
        ↓
User saves/hides/responds
        ↓
Product learns explicit preferences
```

The product must not require the user to perfectly define their future before providing value.

## P5.4 Journey — Share an external opportunity

```text
Paste URL / text / screenshot
        ↓
Vyapar identifies opportunity information
        ↓
Structures known fields
        ↓
Marks uncertainty where necessary
        ↓
User reviews
        ↓
Publish/share
```

The product must preserve provenance.

It must not present an inferred field as confirmed fact.

## P5.5 Journey — Opportunity matching

```text
Opportunity enters system
        ↓
Normalize
        ↓
Check eligibility
        ↓
Retrieve potentially relevant people
        ↓
Score relevance
        ↓
Rank
        ↓
Diversify
        ↓
Distribute
```

The matching engine should not be treated as a black box.

## P5.6 Journey — User gives negative feedback

```text
Opportunity shown
        ↓
User selects “Not interested”
        ↓
Optional reason
        ↓
Immediate recommendation adjustment
        ↓
If preference appears durable:
ask whether to update preference
```

The user remains the authority over important personal preferences.

## P5.7 Journey — Report trust/safety problem

```text
User reports opportunity/person
        ↓
Capture reason/evidence
        ↓
Restrict harmful behavior where necessary
        ↓
Trust & Safety review
        ↓
Decision/action
        ↓
Audit record
```

The report flow should feel safe, calm and non-retaliatory.

## P5.8 Journey — Business uses Vyapar commercially

```text
Business identity
        ↓
Create opportunity
        ↓
Select relevant audience
        ↓
Organic distribution
        ↓
Optional paid acceleration
        ↓
Qualified responses
        ↓
Analytics / outcome
```

Commercial features must never override fundamental relevance and eligibility rules.

---

# 3. Product Decision Rules

These rules are binding unless explicitly superseded by a later Product Decision Record.

## Rule 1
Vyapar is an **opportunity platform**, not a job board.

## Rule 2
The canonical object is **Opportunity**.

## Rule 3
Opportunity discovery should remain fundamentally accessible to the community.

## Rule 4
Paid distribution may improve reach, but must not buy eligibility or relevance.

## Rule 5
A profile is a living opportunity model, not merely a CV.

## Rule 6
Capability, intent and constraints are distinct concepts.

## Rule 7
Hard eligibility must be separated from soft relevance.

## Rule 8
Matching must be explainable.

## Rule 9
The product should provide value before demanding extensive profile completion.

## Rule 10
Privacy-sensitive information must not automatically become public or a ranking signal.

## Rule 11
Trust is evidence, not popularity.

## Rule 12
New members must not be treated as untrustworthy merely because they lack history.

## Rule 13
Opportunity freshness is part of product quality.

## Rule 14
Community-generated opportunity supply is strategically important.

## Rule 15
AI can assist product operation, but core product behavior must remain understandable and usable without conversational AI.

## Rule 16
Technical architecture must support the product; product decisions must not be distorted merely to fit a preferred technical pattern.

---

# 4. Product Decision Record

Every material product decision should be recorded using:

```text
Decision ID:
Date:
Context:
Problem:
Decision:
Alternatives considered:
Why this was chosen:
Evidence:
Assumptions:
Trade-offs:
Confidence:
Revisit trigger:
Owner:
```

Example:

```text
Decision ID: VY-DEC-001
Context: Opportunity discovery
Problem: Early monetization can reduce marketplace liquidity
Decision: Keep relevant opportunity discovery free
Alternatives: Paid access / subscription-only discovery
Why: Liquidity and network density are more strategically valuable early
Evidence: Marketplace economics and product research
Assumption: Providers will pay for better distribution after useful density exists
Trade-off: Consumer revenue is delayed
Confidence: Medium
Revisit trigger: User willingness-to-pay evidence contradicts the assumption
```

---

# 5. Assumptions vs Decisions

These must never be mixed.

## Decision

A deliberate product choice that downstream agents should follow.

## Assumption

Something believed to be true but not yet sufficiently validated.

Example:

> “Businesses will pay for targeted distribution.”

This is an assumption until tested.

It should not silently become:

> “Businesses shall pay ₹99 for targeted distribution.”

That is a later product/pricing decision based on evidence.

---

# 6. Handoff to Step 1

Once P1–P5 are approved, the Business Requirements agent should use this document as product context.

Step 1 should translate product decisions into **business requirements**.

Step 2 then decomposes approved BRs into functional behavior.

Step 3 owns detailed UX.

Step 4 owns visual/UI design.

Step 5 owns test scenarios.

Step 6+ own architecture, technical design, security, implementation and operations.

## Handoff rule

Downstream agents may:

- clarify
- decompose
- make implementation-specific decisions within their authority
- raise genuine blockers
- identify contradictions

Downstream agents must **not silently change product behavior**.

If a downstream decision changes:

- product scope
- product purpose
- user behavior
- business rules
- monetization
- trust policy
- privacy principle
- core domain meaning

it must be raised back to Product Management.

---

# 7. Product Drift Guard

At every downstream stage, ask:

### Product identity
Are we still solving the same problem?

### User
Are we still serving the same user need?

### Core object
Is Opportunity still the canonical object?

### Value
Are we still optimizing for relevant opportunity discovery and successful connections?

### Behavior
Has any agent introduced behavior that was never a Product decision?

### Scope
Has the module silently become a job board, social network, ATS, marketplace, or another product?

### Economics
Has monetization started damaging liquidity or relevance?

### Trust
Has a convenience feature weakened privacy or trust?

### AI
Has AI become the product instead of supporting the product?

If any answer is “no” or “unclear”, raise a Product Decision / blocker rather than silently proceeding.

---

# 8. Definition of Done — Product Management Layer

The Product Management layer is ready for downstream requirements when:

- [ ] The problem is clearly defined.
- [ ] Target users are defined.
- [ ] Evidence and assumptions are separated.
- [ ] Product mission is approved.
- [ ] Product vision is approved.
- [ ] Product principles are approved.
- [ ] Product scope and non-goals are explicit.
- [ ] Monetization principles are explicit.
- [ ] Trust/privacy principles are explicit.
- [ ] Core domain concepts are defined.
- [ ] Canonical terminology is established.
- [ ] Core product behaviors are defined.
- [ ] Major user journeys are defined.
- [ ] Product success metrics are defined.
- [ ] Material product decisions have Decision Records.
- [ ] Open product uncertainties are explicitly listed.
- [ ] No downstream technical or UI assumptions have been disguised as product decisions.
- [ ] Product Manager has approved the document.

---

# 9. Final Product Boundary

The most important boundary for this pipeline is:

```text
PRODUCT MANAGEMENT
        ↓
What problem?
Who?
Why?
What value?
What product?
What behavior?
What rules?
What scope?
What economics?
What trust?
What success?

        ↓

SPECIALIST PIPELINE
        ↓
Business Requirements
Functional Requirements
UX
UI
Testing
Architecture
Technical Requirements
Security
Implementation
QA
Operations
```

The Product Manager defines **what the product is and how it should behave**.

The specialist agents decide **how to express, design, engineer, test and operate it**.

ForKhatri remains the parent umbrella.

Vyapar is the current independently planned module.

The same product-management framework can later be reused for Mangaly, Milavn, Samachar, Pay Bills, Loans & Finance, and other modules — but each module must receive its own P1–P5 product decisions rather than inheriting assumptions from Vyapar.
