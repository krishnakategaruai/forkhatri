# Vyapar

## 1. What is Vyapar?

**Vyapar is the opportunity discovery and connection platform within ForKhatri, built for the Khatri/Patjari community.**

Its purpose is simple:

> **Every person should have a fair chance to discover opportunities that are relevant to what they can do, what they want, where they are, and what they are willing to consider.**

Vyapar exists because opportunities are often **fragmented, scattered, poorly communicated, or simply invisible to the people who could benefit from them.**

A useful opportunity may exist in:

- a community WhatsApp group
- a friend's message
- a local business
- a government notification
- a community member's post
- a project
- a freelance requirement
- a service request
- a collaboration request
- a training opportunity
- a business opportunity
- a local assignment
- or somewhere else entirely

The problem is often not that the opportunity does not exist.

The problem is:

> **The right person never discovers it.**

Vyapar is designed to solve that problem.

---

# 2. Vyapar is NOT a job portal

This is one of the most important product principles.

**Opportunity is the root concept.**

A job is only one kind of opportunity.

Vyapar should therefore never be designed around the assumption that every user is a job seeker.

A person may be:

- looking for employment
- looking for freelance work
- looking for a project
- offering a service
- looking for customers
- looking for a business partner
- looking for a collaborator
- looking for training
- looking for an apprenticeship
- looking for local work
- looking for a mentor
- looking for someone to help with a project
- sharing an opportunity for someone else
- creating an opportunity
- or simply exploring what possibilities exist

The same person may perform several of these roles simultaneously.

Therefore Vyapar does not permanently classify a person as:

> Job seeker / Employer

Instead, it understands:

> **What can this person do or offer?**

and

> **What opportunities does this person want, need, or remain open to?**

---

# 3. The fundamental problem

Today, opportunity information is fragmented.

A person may be capable of doing something but never know that someone nearby needs exactly that capability.

Another person may have an opportunity but not know anyone suitable.

A third person may know both people but the connection never happens.

A fourth person may not even know what kind of opportunity they should search for.

Vyapar connects these situations.

The fundamental problem is therefore:

> **There is a gap between people, capabilities, needs, and opportunities.**

Vyapar tries to reduce that gap.

---

# 4. Vyapar's core promise

The core promise is:

> **Don't make people search everywhere for opportunities. Help relevant opportunities find the right people.**

This creates two complementary experiences.

### Discovery

The user can actively:

- browse
- search
- filter
- explore
- save
- share
- respond

### Proactive discovery

Vyapar can proactively surface opportunities that appear relevant to the user.

The goal is not to notify everyone about everything.

The goal is:

> **Deliver the right opportunity to the right person at the right time without creating noise.**

---

# 5. The core product model

Vyapar revolves around two major objects:

## Person

A person's:

- capabilities
- interests
- needs
- preferences
- constraints
- availability
- location
- trust signals
- privacy choices
- behaviour

## Opportunity

An opportunity's:

- type
- description
- required capabilities
- location
- timing
- compensation/value
- eligibility
- constraints
- source
- freshness
- trust/provenance
- status

The Opportunity Engine connects them.

```text
PERSON
   │
   ├── What I can do / offer
   ├── What I want / need
   ├── What I might consider
   ├── What I don't want
   ├── Where I can participate
   ├── When I am available
   └── Privacy / trust
             │
             ↓
      OPPORTUNITY ENGINE
             ↑
             │
   ┌─────────┴─────────┐
   │                   │
OPPORTUNITY       COMMUNITY
   │                   │
   ├── Type             ├── People
   ├── Capability       ├── Referrals
   ├── Location         ├── Sources
   ├── Timing           └── Connections
   ├── Value
   ├── Eligibility
   ├── Source
   └── Freshness
```

---

# 6. The Person Model

Vyapar should not treat a profile as a traditional resume.

A resume describes a person's history.

Vyapar needs to understand a person's **opportunity potential**.

Therefore the profile has several dimensions.

## 6.1 Capability

> **What can I do or offer?**

This includes:

- skills
- knowledge
- profession
- trade
- experience
- services
- resources
- certifications
- education
- languages
- portfolio
- things the person can teach
- things the person can help others with

For example:

A person may say:

> Excel, Tally, accounting, GST, customer communication.

Another may say:

> Electrical repair, home wiring, appliance troubleshooting.

Another:

> Photography, editing, wedding shoots.

Another:

> I can introduce businesses to local suppliers.

All of these are capabilities.

---

# 7. Need and Intent

The second major dimension is:

> **What do I want or need?**

A person may want:

- employment
- freelance work
- projects
- customers
- business opportunities
- collaboration
- learning
- mentorship
- local opportunities
- part-time work
- weekend opportunities
- additional income
- a business partner
- people with complementary skills

A person can select multiple intentions.

There is no permanent "user role".

---

# 8. “Open to” is different from “Looking for”

This is important.

Someone might actively want:

> Accounting projects

but also be open to:

> Teaching Excel.

Those are different levels of intent.

Vyapar should eventually distinguish:

### Looking for

Something I actively want.

### Open to

Something I would consider.

### Curious about

Something I may want to explore.

### Not interested in

Something I don't want.

This makes the user model much richer without requiring a complicated form.

---

# 9. Constraints

Matching isn't only about what a person wants.

It is also about what they cannot or will not accept.

Examples:

- location
- commute distance
- work mode
- availability
- working hours
- compensation
- minimum acceptable value
- relocation
- night work
- unpaid work
- commission-only work
- specific opportunity types

Negative preferences are important because a technically relevant opportunity can still be practically useless.

---

# 10. Location

Location should be represented at several levels.

For example:

> Hyderabad → locality → preferred radius

Users should not need to expose their exact home address.

Location is primarily used to improve opportunity relevance.

The system can understand:

> "Within 10 km"

without revealing:

> "This person's house is at this exact address."

---

# 11. Availability

Availability should be simple initially.

Examples:

- full-time
- part-time
- weekends
- evenings
- flexible
- specific dates
- temporary
- project-based

Detailed scheduling can be added later.

---

# 12. Privacy

Privacy is especially important because Vyapar operates inside a close-knit community.

There is a major difference between:

> "I am an accountant."

and:

> "I am currently looking for work."

A person may be comfortable sharing the first publicly while keeping the second private.

Therefore capability and intent should have independent visibility controls.

Possible visibility:

- Private
- Community
- Selected people
- Public

Sensitive information such as:

- exact address
- phone number
- date of birth
- compensation expectations
- personal documents

should not be publicly exposed by default.

---

# 13. Profile is a living model

The profile should not be a form completed once during registration.

It should evolve.

Information can come from:

### Explicit input

The user tells Vyapar.

### Behaviour

The user:

- searches
- saves
- hides
- responds
- shares
- rejects
- changes filters

### Outcomes

The user:

- successfully connects
- completes work
- receives feedback
- provides feedback

The system can then ask useful questions.

For example:

> You have viewed several weekend projects. Should we prioritize weekend opportunities?

The user remains in control.

Vyapar should not silently make major assumptions about a person's preferences.

---

# 14. Profile completion

Vyapar should never optimize for:

> **Profile 72% complete**

That is a vanity metric.

Instead, use:

# Opportunity Readiness

The system should communicate:

> Adding your availability could help us find more relevant opportunities.

The purpose of additional profile information is:

> **Better opportunity discovery.**

Not:

> **Complete our database.**

---

# 15. Progressive profile enrichment

Initial onboarding should collect only information with high matching value.

The first experience should roughly establish:

1. What can you do or offer?
2. What opportunities are you interested in?
3. Where are you?
4. How/when are you available?
5. Important constraints
6. Privacy preferences

Then:

> **Show me opportunities**

Detailed information can be requested later.

For example:

> Add your experience to improve matches.

or:

> Adding your portfolio could help people decide to contact you.

Every additional question should have a reason.

---

# 16. Users who don't know what they want

This is a critical Vyapar use case.

A person may say:

> "I don't know what opportunity I'm looking for."

Vyapar should not punish this user with an empty search page.

Instead it can ask:

> What can you do or offer?

Then use structured relationships to show possibilities.

For example:

```text
You know Excel.

You might consider:

• Reporting projects
• Small-business accounting support
• MIS work
• Excel tutoring
• Data preparation
• Business administration projects
```

The system is helping the user discover opportunities they did not know how to search for.

This is fundamentally different from a conventional job search.

---

# 17. Opportunity

Opportunity is the root object in Vyapar.

Possible opportunity types include:

- Employment
- Freelance
- Project
- Contract
- Apprenticeship
- Internship
- Local work
- Service opportunity
- Business opportunity
- Customer opportunity
- Collaboration
- Partnership
- Training
- Learning
- Mentoring
- Government opportunity
- Community opportunity
- Other future categories

The taxonomy should remain extensible.

---

# 18. Opportunity information

An Opportunity can contain:

### Basic

- title
- description
- type
- status

### Requirements

- capabilities
- experience
- eligibility
- qualifications

### Conditions

- location
- radius
- work mode
- timing
- duration

### Value

Depending on type:

- salary
- project fee
- hourly rate
- commission
- business value
- learning value
- volunteer/non-monetary value

### Trust

- source
- poster
- verification
- freshness
- reports
- reputation

### Action

- respond
- apply
- contact
- register
- visit external source
- share

Not every opportunity needs every field.

---

# 19. Universal opportunity model

The screen should adapt to opportunity type.

A government opportunity may emphasize:

> Eligibility → deadline → official notification.

A freelance project:

> Scope → deliverables → budget → timeline.

A business collaboration:

> What is needed → what is offered → expectations.

A service request:

> Requirement → location → timing → value.

Therefore:

> **One Opportunity model, multiple presentation patterns.**

This prevents the system from becoming a collection of separate mini-products.

---

# 20. Opportunity sources

Vyapar should prioritize sources that are practical, legal, affordable, and useful to the community.

## Primary

### Community opportunities

People can:

- create opportunities
- share opportunities
- forward text
- paste URLs
- upload screenshots

This is the heart of Vyapar.

## Secondary

### Government/public sources

Examples include:

- official government notifications
- public datasets
- government feeds
- public APIs
- official portals

## Future

Licensed/partner sources where appropriate.

Official employer sourcing can remain a later phase rather than being required for launch.

Vyapar should not build its foundation around scraping websites whose terms prohibit it.

---

# 21. Opportunity ingestion

A major Vyapar capability will be turning messy information into structured opportunities.

A community member might submit:

> “Need someone good at Excel for a 3-day project in Secunderabad. Interested people contact…”

Vyapar can structure:

```text
Type: Project
Capability: Excel
Duration: 3 days
Location: Secunderabad
Status: Active
```

But uncertain information must remain uncertain.

The system should ask the contributor to confirm important extracted fields.

---

# 22. Provenance

Every external opportunity should retain:

- original source
- original URL
- source identifier where available
- first seen
- last checked
- published date
- expiration
- application link
- verification status

This enables trust and freshness.

Vyapar should never pretend to be the original authority.

For government information especially:

> **Verify details from the official source.**

---

# 23. Opportunity lifecycle

An opportunity can move through:

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

This is essential because an old opportunity is potentially worse than no opportunity.

---

# 24. The Opportunity Engine

The Opportunity Engine is the core intelligence layer of Vyapar.

Its responsibility is:

> **Determine which opportunities are worth showing to which people, when, and why.**

It should initially be deterministic and explainable.

The engine should not depend on expensive LLM/ML/DL inference for every recommendation.

---

# 25. Engine pipeline

The fundamental pipeline is:

```text
OPPORTUNITY
     ↓
STRUCTURE
     ↓
RETRIEVE
     ↓
ELIGIBILITY
     ↓
SCORE
     ↓
RANK
     ↓
DIVERSIFY
     ↓
DISTRIBUTE
```

For a user searching:

```text
QUERY
  ↓
RETRIEVAL
  ↓
CANDIDATES
  ↓
HARD FILTERS
  ↓
RANKING
  ↓
RESULTS
```

The system should not scan every opportunity in the database for every request.

---

# 26. Retrieval

Retrieval finds a manageable candidate set.

V1 can use:

- PostgreSQL full-text search
- indexes
- structured filters
- taxonomy relationships
- PostGIS for geographic queries

BM25/full-text search can later be complemented by OpenSearch/Elasticsearch if scale and query complexity justify it.

The important architectural principle is:

> **Retrieve first, then spend computation on ranking.**

---

# 27. Eligibility

Hard constraints should be applied before ranking.

Examples:

If the user says:

> No relocation

then relocation opportunities should be removed.

If an opportunity requires:

> specific mandatory eligibility

and the user does not satisfy it, it should not be ranked as a normal match.

Hard constraints are different from preferences.

---

# 28. Ranking

After eligibility, opportunities can receive a deterministic relevance score.

Conceptually:

```text
Relevance =
    capability fit
  + intent fit
  + location fit
  + availability fit
  + value/compensation fit
  + experience fit
  + freshness
  + trust
  + preference fit
```

The exact weights should be experimentally validated.

The engine should also consider:

> **diversity**

so that users aren't shown ten almost-identical opportunities.

---

# 29. Match explanations

Instead of:

> 93% AI Match

show:

> **Why you're seeing this**

For example:

- ✓ Matches your accounting capability
- ✓ Within your preferred area
- ✓ Weekend availability fits
- ✓ Project opportunity is one of your interests

This creates trust.

---

# 30. Uncertainty

The engine should distinguish:

### Strong fit

Good evidence.

### Possible fit

Some information is missing.

### Adjacent possibility

Not a direct match, but potentially useful.

This is much better than pretending the system knows everything.

---

# 31. Opportunity Neighborhood

This is one of the most promising innovation areas.

Instead of only finding identical matches, Vyapar can understand relationships between opportunities and capabilities.

For example:

```text
ACCOUNTING
   ├── Bookkeeping
   ├── GST
   ├── Billing
   ├── MIS
   ├── Financial reporting
   └── Accounting training
```

A person interested in one capability can discover opportunities in neighbouring areas.

This allows:

> **Discovery beyond vocabulary.**

A person does not need to know the exact name of the opportunity.

---

# 32. Capability relationships

The taxonomy should support relationships such as:

- exact
- alias
- related
- transferable
- adjacent
- unrelated

For example:

> Python → Python = exact

> Excel → MS Excel = alias

> Django → Python = related

> Java → programming = adjacent

This can initially be deterministic.

AI can later assist taxonomy maintenance and semantic expansion without becoming the hot-path matching engine.

---

# 33. Behavioural learning

Every user action is valuable information.

Examples:

- search
- view
- save
- hide
- share
- respond
- ignore
- report
- contact
- complete
- feedback

The system can learn from this.

But learning should be transparent.

If a user repeatedly hides night opportunities:

> **We noticed you usually skip night opportunities. Make that a preference?**

This is better than silently changing the user's model.

---

# 34. Feedback vocabulary

Useful feedback includes:

- Too far
- Wrong type
- Not my capability
- Compensation too low
- Wrong timing
- Already found something
- Not interested
- Expired
- Incorrect information

These signals improve the engine.

---

# 35. Distribution Engine

Finding an opportunity isn't enough.

Vyapar must determine:

> **Who should actually receive it?**

The distribution pipeline is:

```text
Opportunity
    ↓
Eligible people
    ↓
Relevant people
    ↓
Interested people
    ↓
Priority people
    ↓
Delivery
```

Strong opportunities can be surfaced immediately.

Good but less urgent opportunities can appear in a digest.

Broad/weak opportunities can remain in discovery.

---

# 36. Avoid notification fatigue

Vyapar should not become:

> “You have 47 new opportunities!”

Instead:

> **3 opportunities worth seeing today**

Notifications should be based on value, not inventory.

---

# 37. Discovery experience

The main screen should be **Discover**.

It should combine:

### For You

Strong personalized opportunities.

### Explore

Possibilities beyond the user's direct search.

### Near You

Location-based opportunities.

### Community

Community-generated opportunities.

### Public/Government

Useful official/public opportunities.

### Search

For intentional discovery.

These should feel like different lenses over the same opportunity universe rather than five disconnected products.

---

# 38. Search

Search should eventually support natural intent.

Examples:

> accounting work near me

> weekend Excel opportunities

> something I can do from home

> business partnership in Hyderabad

V1 can convert these into structured retrieval and filters.

More sophisticated semantic interpretation can be added later.

---

# 39. Filters

Initial filters should focus on:

- opportunity type
- location
- distance
- work mode
- availability
- compensation/value
- date
- source

Advanced filters should remain behind:

> **More filters**

Don't expose a wall of controls.

---

# 40. Opportunity detail

The opportunity detail screen should answer:

1. What is this?
2. Why might it be relevant?
3. What is expected?
4. What is offered?
5. Where/when?
6. Who is behind it?
7. Can I trust it?
8. What should I do next?

Primary action should depend on opportunity type.

Not everything should say:

> Apply.

---

# 41. Response model

The universal action should be:

# Opportunity Response

It may manifest as:

- Apply
- Respond
- Express interest
- Contact
- Submit proposal
- Register
- Apply externally

The system records the underlying response consistently.

---

# 42. Activity

Activity is where the user manages their opportunity journey.

It can contain:

- Saved
- Responded
- Shared
- Viewed
- Posted
- Completed
- Hidden
- Closed

The terminology should remain opportunity-centric.

---

# 43. Posting

Posting is a first-class Vyapar capability.

A user should be able to:

### Create

Describe the opportunity.

### Share

Paste text or a URL.

### Upload

Upload an image/screenshot.

This is particularly useful for community information arriving through WhatsApp.

---

# 44. Opportunity Composer

Instead of a traditional job-posting form:

> **Create an Opportunity**

The user gives simple information.

Vyapar structures it.

For example:

> “Looking for someone who can handle GST and accounting for our small business twice a week.”

The system may identify:

- accounting
- GST
- part-time
- local/business context

Then asks the user to confirm or correct.

---

# 45. Trust in posting

Before publication:

> **Here's what we understood**

Then show:

- type
- requirement
- location
- timing
- value
- contact method

Missing critical information can be highlighted.

The user remains the final authority.

---

# 46. Community sharing

An important growth mechanism is:

> **Useful opportunity → useful share**

A user should be able to send an opportunity to another person.

The shared object should communicate value before asking someone to install the app.

For example:

> **Excel project opportunity in Hyderabad**
>
> Found on Vyapar.
>
> [View opportunity]

This can turn community utility into organic acquisition.

---

# 47. Product-led growth

Vyapar's growth should ideally come from its utility.

The flywheel:

```text
More people
     ↓
More capabilities represented
     ↓
More opportunities can be matched
     ↓
Better discovery
     ↓
More successful connections
     ↓
More trust
     ↓
More community participation
     ↓
More opportunities
     ↓
More people
```

The product becomes its own distribution mechanism.

---

# 48. Trust

Trust is not a decoration.

It is infrastructure.

Vyapar should know:

- who created an opportunity
- where it came from
- whether it is verified
- whether it is fresh
- whether it has been reported
- whether interactions have actually happened

---

# 49. Reputation

Eventually both sides can build reputation.

An opportunity provider can be evaluated on:

- reliability
- clarity
- communication
- professionalism
- payment reliability

A participant can be evaluated on:

- quality
- reliability
- communication
- professionalism
- punctuality

Ratings should be tied to real interactions rather than arbitrary public voting.

---

# 50. New users

A new user should not be treated as untrustworthy simply because they have no history.

Therefore:

> **No reputation ≠ bad reputation.**

New users should still receive opportunities.

Trust should be based on multiple signals rather than popularity.

---

# 51. Safety and moderation

Users must be able to report:

- scam
- fake opportunity
- inappropriate behaviour
- incorrect information
- expired opportunity
- harassment
- privacy violation

Reports should create a moderation workflow.

Comments and feedback can eventually be automatically screened for:

- abuse
- harassment
- vulgarity
- threats
- personal information

Human review remains necessary for serious cases.

---

# 52. Fairness

Vyapar must not silently infer or use sensitive characteristics to determine someone's opportunity access.

The system should avoid:

- protected-trait ranking
- popularity-only ranking
- community-status bias
- appearance bias
- hidden discrimination
- rewarding old accounts simply because they have more history

The engine should prioritize:

> **Relevant capability + intent + constraints + opportunity requirements.**

---

# 53. Community graph

The community relationship itself can eventually become useful.

For example:

> A trusted community member shared this opportunity.

But social connections should be used carefully.

The system should not turn Vyapar into a popularity contest.

A person should receive an opportunity because it is relevant—not because they have the most connections.

---

# 54. Screens

The recommended core navigation is:

### Discover
Opportunity discovery, search and exploration.

### Activity
Saved, responses, history, shared and posted opportunities.

### Post
Create/share/upload opportunities.

### Profile
Capabilities, intent, preferences, trust and privacy.

Notifications sit outside bottom navigation.

---

# 55. Core V1 screens

### Entry

1. Welcome
2. Authentication

### Initial setup

3. How can Vyapar help?
4. What can you do or offer?
5. What opportunities are you interested in?
6. Location/basic constraints
7. Privacy

### Discovery

8. Discover
9. Search/filter
10. Opportunity detail
11. Why this opportunity
12. Save/hide/feedback

### Action

13. Opportunity response
14. Activity

### Creation

15. Create opportunity
16. Review opportunity
17. Manage opportunity

### Profile

18. Profile
19. Edit capabilities/preferences
20. Privacy/settings

### Trust

21. Source/trust information
22. Report opportunity/user

This is enough for V1.

---

# 56. What should NOT be in V1

Do not overbuild.

Avoid initially:

- complex AI chatbot
- ML recommendation system
- deep-learning matching
- embeddings everywhere
- elaborate social feed
- followers
- public popularity ranking
- complicated reputation score
- full chat platform
- map-first discovery
- dozens of filters
- huge onboarding questionnaire
- full resume builder
- sophisticated gamification

Build the foundation first.

---

# 57. Innovation opportunities

The highest-potential innovations are:

## 1. Opportunity Neighborhood

Help users discover adjacent possibilities they didn't search for.

**Impact: Very high**

**Complexity: Medium**

---

## 2. Living Opportunity Profile

The profile improves through explicit information and controlled behavioural feedback.

**Impact: Very high**

**Complexity: Medium**

---

## 3. Opportunity Readiness

Profile improvement is measured by improved opportunity coverage rather than completion percentage.

**Impact: High**

**Complexity: Low**

---

## 4. Explainable Opportunity Engine

Every recommendation can answer:

> Why did Vyapar show me this?

**Impact: Very high**

**Complexity: Low/Medium**

---

## 5. Opportunity Composer

Turn messy text/screenshots/forwarded information into structured opportunities.

**Impact: Very high**

**Complexity: Medium**

---

## 6. Reverse Discovery

Instead of only:

> Person → Opportunity

eventually support:

> Opportunity → suitable people

This is particularly powerful for community opportunities.

**Impact: Very high**

**Complexity: High**

---

## 7. User-controlled preference learning

Let the user explicitly accept or reject what Vyapar learns.

**Impact: High**

**Complexity: Medium**

---

# 58. The long-term Vyapar vision

Eventually Vyapar could become a:

# **Community Opportunity Network**

rather than a job portal.

Imagine a person entering:

> “I know accounting, but I'm not sure what I can do with it.”

Vyapar understands their capabilities.

It knows their location and availability.

It knows what kinds of opportunities they are open to.

It knows the opportunity universe.

It can say:

> **Here are five opportunities you can act on today.**

And:

> **Here are three possibilities you may not have thought about.**

At the same time, a business owner can say:

> “I need someone who can help me with this.”

Vyapar can find relevant people.

A community member can forward an opportunity.

Vyapar can structure it.

A person can respond.

Both sides can establish trust.

The outcome feeds back into the system.

The system gets better.

---

# 59. The core loop

The entire product can ultimately be expressed as:

```text
        PERSON
           ↓
   CAPABILITY + INTENT
           ↓
   OPPORTUNITY ENGINE
           ↑
      OPPORTUNITY
           ↓
       DISCOVERY
           ↓
         ACTION
           ↓
        OUTCOME
           ↓
        FEEDBACK
           ↓
    BETTER USER MODEL
           ↓
   BETTER OPPORTUNITIES
```

And alongside it:

```text
COMMUNITY
    ↓
OPPORTUNITY SHARING
    ↓
MORE OPPORTUNITIES
    ↓
MORE USEFUL CONNECTIONS
    ↓
MORE TRUST
    ↓
MORE COMMUNITY PARTICIPATION
```

These two loops reinforce each other.

---

# 60. The ultimate definition

If someone asks:

> **What is Vyapar?**

The clearest answer is:

> **Vyapar is ForKhatri's community opportunity network. It helps people discover opportunities that match what they can do, what they want, where they are, and what they are open to—and helps opportunities reach the people who can genuinely benefit from them.**
>
> **Jobs are only one type of opportunity. Vyapar also supports projects, freelance work, services, business opportunities, collaborations, learning, government opportunities, local opportunities, and other forms of meaningful opportunity.**
>
> **Its core engine connects people and opportunities using structured capabilities, intent, constraints, location, availability, trust, and behaviour. It combines active discovery with proactive distribution so that people do not have to know exactly where or how to search for every opportunity.**
>
> **The long-term goal is to make opportunity discovery more fair, more local, more trustworthy, and more accessible within the community—so that a useful opportunity is less likely to remain invisible simply because the right person never heard about it.**

# Vyapar's north-star idea

> ## **Don't let a good opportunity remain invisible to the person who could benefit from it.**

That, rather than “job matching,” should remain the conceptual center of Vyapar.