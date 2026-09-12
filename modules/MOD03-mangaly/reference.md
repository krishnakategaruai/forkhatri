---
module: MOD03
artifact: reference
title: External Matrimonial Product Reference and Mangaly MVP Mapping
status: Reference
updated: 2026-09-11
owner: Product / Solution Architecture
---

# MOD03 Reference — Matrimonial Product Patterns and Mangaly MVP Mapping

## Purpose

This document is a reusable reference for later MOD03 product, UX, solution
architecture, implementation, test-scenario, and review steps.

It records publicly observable Shaadi.com product patterns and official
Shaadi.com guidance, then maps those patterns to a deliberately simpler,
mobile-first Mangaly implementation.

This is a reference and benchmarking artifact. It does not replace the
approved requirements in `01-business-requirements.md` or
`02-functional-requirements.md`, and it does not authorize copying Shaadi.com
branding, content, proprietary algorithms, or private implementation details.

## Evidence boundary

The reference uses:

1. Publicly accessible Shaadi.com pages and navigation.
2. Official Shaadi.com support content.
3. Official ShaadiBuzz articles describing common app and website workflows.
4. The approved MOD03 BR and FR files in this directory.

Authenticated screens, private APIs, source code, ranking formulas, fraud
models, moderation operations, and internal data models were not available for
inspection. Any logic described below as “observed” is limited to public UI and
officially documented behaviour. Any Mangaly mapping is a product-design
recommendation, not a claim about Shaadi.com internals.

## Executive conclusion

The core matrimonial product pattern can be transformed into a working,
mobile-first Mangaly web application.

The essential experience is a manageable sequence of journeys:

`Create profile → become discoverable → discover a person → understand compatibility → send connection request → accept/decline → selectively share → communicate → optionally involve family → optionally exchange contact details`

Mangaly should not attempt to reproduce the full scale of Shaadi.com in its
first release. It should implement the core journey with Mangaly’s defining
behaviours: Home Circle collaboration, contextual authorization, explainable
compatibility, selective sharing, privacy, safety, and accountable transitions.

The MOD03 business requirements explicitly confirm that the module requires no
native-only device capability and is suitable for a responsive, mobile-first
web application on the platform architecture. See
`01-business-requirements.md`, “Delivery form factor for this BR set”.

## Public Shaadi.com screen inventory

### 1. Public entry and trust surface

- Landing/home page.
- Registration entry.
- Login entry.
- Product value proposition.
- Verification/trust claims.
- Success stories.
- FAQ.
- Community, country, religion, city, state, and mother-tongue discovery links.
- Premium and personalized matchmaking entry points.
- Privacy policy, terms, safety, support, and report-misuse links.

### 2. Main signed-in navigation exposed publicly

The public search page exposes the following navigation groups:

- Search.
  - Advanced Search.
  - Basic Search.
  - Who is Online.
  - Special Cases.
- Matches.
  - Preferred Matches.
  - Discover.
  - Broader Matches.
  - 2-way Matches.
  - Reverse Matches.
  - Maybe’s and Shortlists.
- Inbox.
  - Inbox.
  - Accepted.
  - Sent.
  - Deleted.
  - Filtered Out.
  - Notifications.
  - Call / SMS Log.
- More.
  - Mobile experience.
  - Shaadi Centres.
  - Select Shaadi.
  - Success Stories.
  - Blog.
  - Membership plans.
  - Customer support.

### 3. Profile and verification screens

Official support topics expose these profile-related surfaces:

- Edit profile details.
- Add photos.
- Change display name.
- Change photo privacy.
- Hide or delete profile.
- Change or hide phone number.
- Change email address.
- Update family details.
- Selfie verification.
- Verification failure/retry support.
- Verification privacy questions.
- Profile created for another person.
- Verification required before viewing contact details.

### 4. Search and discovery screens

The public search surface includes:

- Bride/groom selection.
- Age range.
- Height range.
- Marital status.
- Children preference.
- Religion.
- Mother tongue.
- Community.
- Country.
- State.
- City/district.
- Photo visibility settings.
- Search and reset actions.
- Saved searches.
- Profile ID search.

The official FAQ also describes advanced search, online search, special-case
search, refinement after results, and multiple saved searches.

### 5. Profile detail actions

The publicly documented profile actions include:

- View a candidate profile.
- Inspect profile information and verification indicators.
- Shortlist/save for later.
- Ignore a profile so it does not reappear.
- Express interest/connect.
- Add an optional personal note.
- Request or view contact information when permitted.
- Block or report.

### 6. Connection, communication, and contact screens

The documented flow is:

1. Open a profile.
2. Tap Connect, Send Interest, or Express Interest.
3. Optionally add a short note.
4. Confirm the request.
5. Recipient accepts or declines.
6. If accepted, use in-app communication.
7. If allowed by privacy and membership rules, request or view contact details.

The public product distinguishes connection/interest from communication and
contact exchange. The labels and availability can vary by region and
subscription.

### 7. Privacy, safety, and support screens

Official guidance describes:

- Profile visibility controls.
- Photo privacy or protected photos.
- Last-seen/online visibility.
- Contact-detail visibility.
- Block.
- Report.
- Verification and moderation.
- Help search.
- Support chat.
- Email support.
- Phone support.
- WhatsApp support.
- Ticket submission.

## Observable product logic patterns

### Profile logic

Shaadi.com combines structured fields with free-text self-expression. Profile
data commonly covers identity, lifestyle, education, profession, family,
location, religion/community, preferences, photos, videos, and horoscope or
astrological information.

### Search logic

Search uses explicit filters and saved searches. The public FAQ describes basic
and advanced search, online and special-case search, refinement, Profile ID
search, and result sorting.

### Match logic

The public FAQ distinguishes:

- Preferred Matches: closely match stated preferences.
- Broader Matches: match some preferences while relaxing others.
- Reverse Matches: the other person’s preferences match the current profile.
- 2-way Matches: both sides’ preferences match each other.

Mangaly should use the useful idea of explaining alignment and difference, but
must not expose a popularity score, demand score, or unexplained “best match”
number.

### Connection logic

Connection is an explicit, attributable action. A request can be accepted or
declined. Acceptance means permission to explore the connection; it does not
mean commitment or marriage intent.

### Communication logic

Communication is downstream of connection or explicit eligibility. Contact
details are not automatically exposed. Privacy settings and, in Shaadi.com’s
case, membership rules can affect availability.

### Privacy logic

Visibility is configurable by category or surface. A profile may be visible
while photos or contact details remain protected. Block and report are always
available safety actions.

### Verification and moderation logic

Shaadi.com publicly describes a combination of machine checks, rules, photo or
selfie verification, human review, reporting, and moderation. The exact
implementation is not public and should not be assumed.

## Official external references

### Shaadi.com product and support

- [Shaadi.com public home and product overview](https://www.shaadi.com/)
- [Shaadi.com public search surface](https://www.shaadi.com/search?loc=top-nav)
- [Shaadi.com Help & Support](https://support.shaadi.com/support/home)
- [Profile and Selfie Verification support](https://support.shaadi.com/support/solutions/48000024547)
- [Search and Matches support](https://support.shaadi.com/support/solutions/48000024550)
- [Shaadi.com profile tips](https://www.shaadi.com/info/customer-relations/faq/profiletips)
- [Shaadi.com searching and matching FAQ](https://www.shaadi.com/info/customer-relations/faq/match-making)
- [Shaadi.com privacy policy](https://www.shaadi.com/info/privacy)

### Official ShaadiBuzz articles

- [How to Use Shaadi.com as a Matchmaking Platform](https://blog.shaadi.com/how-to-use-shaadi-app-as-a-matchmaking-platform-step-by-step-guide/)
- [How Shaadi.com Protects Your Data and Keeps Online Matchmaking Safe](https://blog.shaadi.com/how-shaadi-com-protects-your-data-and-keeps-online-matchmaking-safe/)
- [Official ShaadiBuzz blog](https://blog.shaadi.com/)

## Mangaly transformation

### Recommended mobile-first navigation

Use five primary destinations:

1. Home — current tasks, requests, profile completeness, and safety notices.
2. Discover — candidate discovery, filters, and compatibility explanations.
3. Connections — sent, received, accepted, active, and concluded connections.
4. Home Circle — family/relative members, invitations, permissions, and
   suggestions.
5. More — profile editing, privacy, verification, language, help, and account.

Use contextual bottom sheets or full-screen flows for actions such as:

- Send connection request.
- Accept or decline.
- Selectively share a category.
- Invite a Home Circle member.
- Report or block.
- Request contact exchange.

Avoid reproducing Shaadi.com’s dense desktop-style navigation on mobile. Keep
one primary action visible per screen and progressively reveal advanced fields.

### Simple Mangaly screen set

The following screen set is sufficient for a first working product slice:

1. Welcome and sign in.
2. Profile setup wizard.
3. Profile completeness view.
4. Discover list with a small filter set.
5. Candidate profile detail.
6. Compatibility explanation panel.
7. Home Circle invitation and role screen.
8. Connection request and response screen.
9. Selective-sharing screen.
10. Private conversation screen.
11. Contact-exchange request screen.
12. Safety/report/block screen.
13. Privacy and account settings.

### Simple working state flow

```text
Profile draft
  → discoverable profile
  → discovery result
  → profile viewed
  → connection request sent
  → accepted or declined
  → selective sharing
  → private communication
  → optional contact exchange
  → optional family involvement
  → optional meeting-occurred note
  → concluded or reactivated profile
```

### Minimum entities for a working implementation

- Person / account.
- Matrimonial profile.
- Partner preferences.
- Home Circle member and role.
- Authorization grant.
- Visibility rule.
- Verification item and evidence status.
- Compatibility explanation.
- Connection and connection state.
- Selective-sharing grant.
- Conversation and minimal message events.
- Contact-exchange request.
- Safety report and case state.
- Audit event.

### What to simplify in the first release

- Start with a small, curated filter set rather than dozens of search fields.
- Use deterministic compatibility explanations before advanced AI ranking.
- Support photos before profile video.
- Support one private conversation mode before richer communication features.
- Support manual or admin-assisted verification before advanced automated checks.
- Support one Home Circle invitation and a small permission vocabulary first.
- Keep contact exchange explicit and mutual.
- Keep reporting and blocking available from every relevant profile and
  conversation surface.

### What must remain distinct from a generic matrimonial clone

Mangaly’s differentiating product logic is not “more profiles” or “more
filters.” It is:

- The candidate remains the decision owner.
- Family participation is collaborative and bounded, not surveillance.
- Authorization is contextual and least-privilege.
- Compatibility is explainable and not a popularity score.
- Sharing is category-specific and deliberate.
- Communication is private and retention-aware.
- Safety reporting is always available.
- Real-world introduction is supported with optional safety guidance, not
  relationship-progress tracking.

## Implementation conclusion

A simple working Mangaly version is achievable as a mobile-first web app. The
first implementation should prove the golden path rather than attempt the full
89-FR surface at once:

`Profile → Discover → Explain → Connect → Accept → Share → Communicate → Safety`

The approved MOD03 BR and FR documents already provide the business and
functional traceability needed to turn this reference into UX flows, route
definitions, domain models, API contracts, and test scenarios.
