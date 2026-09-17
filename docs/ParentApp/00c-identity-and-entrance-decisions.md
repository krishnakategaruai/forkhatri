---
project: ForKhatri
artifact: Identity and Entrance Decisions
step: 0c
status: Ready for Review
updated: 2026-09-14
---

# Identity and Entrance Decisions

Why the ForKhatri entrance is built the way `07-tech-reqs.md` specifies. Each
decision records the question, what was researched, the decision, and what it
costs. This file supersedes the three drafts written earlier the same day
(now in `research/`), which contained recommendations this research overturned.

## Starting point (verified in the repository, 2026-09-14)

| Area | What actually existed |
|---|---|
| Product decision | `docs/ForKhatri-Unified-Umbrella-App-Interpretation.md`: one app, one identity, modules inside. |
| Parent app | `docs/ParentApp/00`–`09` (Ready for Review) and a static demo shell in `web/parent-app/` with no real identity. |
| Mangaly | Real interim credential system in database `mangaly`: `mangaly_identity.account`, `otp_challenge`, `password_reset_token`, `session`; cookie `mangaly_session`; web sign-up/login/OTP/reset screens. Recorded by Mangaly itself as technical debt. 38 accounts (active and pending). |
| Milavn | No login. Development stand-in: header `X-Milavn-Member-Id` resolved from `dev_identities.json`; member chosen on `/welcome` and kept in localStorage. Data in `forkhatridb`. |
| Vyapar | Database schema only (`vyapar.members` mirror keyed by platform member id); no service; default Next.js page. |
| Platform identity | Designed in ARCHITECTURE.md ADR-004, never built. |

## PA-DEC-01 — Unified member plus per-module member records

**Question.** How do real platforms combine one account with module-specific
users, tiers and behaviour?

**Research.** Slack keeps a global user plus a per-workspace membership with its
own role; GitHub keeps a global user plus per-organisation membership; Google
keeps one Google Account while YouTube keeps a separate channel profile. The
common shape is *identity* (who you are, how you sign in) owned once, and a
*product-local record* (profile, role, tier, onboarding state) owned by each
product, keyed by the global id and created the first time the person uses that
product (just-in-time provisioning).

**Product-owner rule (2026-09-14).** "Profile will be present in each module as
per their needs; ForKhatri only has basic user info, while all others are added
in their specific modules."

**Decision.** `identity.member` in the Identity & Trust Service is the only
person record, and it holds basic identity only: name, verified phone and/or
email, language, platform verification level. The first version also stored a
home locality; migration `003-member-basic-identity-only.sql` removed it because
location is module profile data with module-specific privacy rules. Each module keeps its own member-link table keyed by that id:
`mangaly_identity.account` (now credential-less for platform members),
`milavn_profile.member_profile`, `vyapar.members`. Existing ids were preserved
on import, so no module foreign key changed.

**Cost.** Display names live on the platform, so modules fetch them through the
internal lookup API and cache them rather than joining.

## PA-DEC-02 — Trust: shared foundation, separate module trust

**Question (product owner).** "Each trust factor is different."

**Decision.** The platform holds only Level 1/2 trust (a verified phone or
email, later a verified identity document) because it is a fact about the
person. Every module computes its own Level-3 trust from its own evidence: a
trusted professional in Vyapar is not thereby trusted matrimonially in Mangaly
(ARCHITECTURE.md ADR-005). No module's trust, reputation, tier or role is ever
placed in the platform session, and no module reads another module's trust.

## PA-DEC-03 — Tiers belong to modules

**Decision.** Every member may enter every available module. Tiers (free,
premium and so on) and roles (organiser, moderator, Home Circle member) are
module data in module databases. `registry.member_module_entry` is an index of
which modules a member has opened, used for ordering on the hub, not an access
list.

## PA-DEC-04 — Separate module apps under one entrance: Next.js Multi-Zones

**Question.** How are separately built apps wrapped under one platform so the
member signs in once and then chooses a module?

**Research.**
- Next.js Multi-Zones: several Next.js apps serve different paths of one domain,
  each deployed independently; the default app routes paths to other zones with
  rewrites; each zone sets `assetPrefix`; cross-zone links are hard navigations
  ([Next.js docs, v16.3.5](https://nextjs.org/docs/app/guides/multi-zones)).
- Module Federation for Next.js: `@module-federation/nextjs-mf` never supported
  the App Router and its maintainers have placed it in maintenance mode ahead of
  retirement ([module-federation/core #3153](https://github.com/module-federation/core/issues/3153)).
  All three module web apps use the App Router.
- iframes: strongest isolation, but break deep links, back navigation, focus
  management and accessibility on phones.

**Decision.** Multi-Zones. The entrance is the default zone; each module web app
becomes a zone at `/mangaly`, `/milavn`, `/vyapar` in production. In development
the zones run on their own ports and the entrance navigates to them.

**Cost.** Moving between the hub and a module is a full page load (acceptable for
a module switch; within a module navigation stays instant). Each module app must
adopt `basePath`/`assetPrefix` before production, which also means auditing raw
`/assets/...` paths; scheduled as module work, not done in this slice so module
teams working in parallel are not disrupted.

## PA-DEC-05 — Browser session: one HttpOnly cookie, no tokens in JavaScript

**Research.** RFC 10017 (BCP 212, OAuth 2.0 for Browser-Based Applications,
August 2026) strongly recommends a backend-held session for applications
handling personal data, requires `HttpOnly` and `Secure` cookies, and advises
against tokens in `localStorage`, which is readable by any injected script.

**Decision.** The browser holds one opaque, HttpOnly session cookie. The earlier
draft's "access token in localStorage" and "tiers inside the JWT" are rejected:
the first is the exact exposure the BCP warns against, the second would copy
module data into a platform credential and go stale.

**Cost.** `SameSite=Lax` instead of the BCP's `Strict` suggestion, so SMS and
notification links open signed in; compensated by an `Origin` allow-list check on
every state-changing request.

## PA-DEC-06 — API layer: no gateway yet; modules resolve the session server-side

**Question (product owner).** "API layer — not sure, do research."

**Options considered.**
1. A central API gateway in front of every module API.
2. One unified backend that imports every module.
3. Module APIs stay independent; each resolves the platform session by asking
   the identity service (introspection), with a short cache.

**Research.** The phantom-token pattern (Curity) puts introspection in a gateway
so opaque tokens never reach APIs and only the gateway calls the authorisation
server ([Curity](https://curity.io/resources/learn/introspect-with-phantom-token/)).
Option 2 contradicts ADR-001/ADR-002 (Mangaly's isolated service and database are
a privacy requirement).

**Decision.** Option 3 now: each module's Identity Bridge calls
`POST /internal/v1/sessions/resolve` with a service credential and caches the
result for 30 seconds. The seam is deliberately the same one a gateway would
use, so introducing the gateway at deployment (the same edge that routes the
zones) moves the call out of the modules without changing module business
code.

**Cost.** One internal call per member per 30 seconds per module; sign-out takes
up to 30 seconds to reach every module; the identity service is on every
authenticated path, which ADR-004 already accepted with a 99.9% target.

## PA-DEC-07 — ADR-004 token mechanism refined

ADR-004 chose "OAuth2/OIDC with short-lived JWTs". This slice keeps its core
decision (one standalone Identity & Trust Service, sole writer of members and
credentials) and refines the mechanism: opaque session plus introspection
instead of self-contained JWTs, because instant revocation across modules and no
signing-key distribution matter more at this stage than avoiding one cached
internal call. JWTs can still be minted by the future gateway for internal hops
(phantom-token style) without changing the browser contract.

## PA-DEC-08 — Migrating existing identities

- Active Mangaly accounts move with their ids, identifiers and Argon2id hashes, so
  members keep their passwords.
- Pending (never-verified) Mangaly accounts are not imported; if their identifier
  later signs up through ForKhatri, Mangaly retires the stale pending row.
- Milavn development identities move with their ids. Development seed ids that
  exist in both modules (`1111…`, `2222…`) become one member.
- Mangaly's interim credential routes are switched off by a setting (kept in the
  code for tests), and its login screens redirect to the entrance.

## PA-DEC-09 — Entrance experience

The entrance follows the product owner's standing design direction: a new
interaction model rather than a re-skinned dashboard. No tab bar; a floating
command orb; a conversational sign-in (one question at a time); an intent bar
that shows how it understood a request before opening a module; modules as
live portals. Notifications bell sits immediately left of the member avatar;
the avatar is always right-most. The older `web/parent-app/` prototype is kept
for reference, not deleted.

## Corrections to the earlier drafts (`research/`)

| Draft claim | Status |
|---|---|
| Module Federation for the module apps | Rejected: not supported with the App Router; see PA-DEC-04. |
| Access token in `localStorage`, tiers/roles in the JWT | Rejected: see PA-DEC-05 and PA-DEC-03. |
| Milavn and Vyapar have login screens to delete | Incorrect: Milavn had a development stand-in, Vyapar had no service. |
| Mangaly users must be re-created and lose passwords | Incorrect: ids and password hashes are preserved (PA-DEC-08). |
| `user_module_access` table controlling which modules a member can open | Rejected: every member may open every available module (PA-DEC-03). |
| 8–12 week effort estimate | Removed: not grounded in any measurement. |
