---
project: ForKhatri
artifact: Parent Application Architecture
step: 0b
status: Ready for Review
updated: 2026-09-14
---

# Parent Application Architecture

## Revision history

| Date | Change | Reason |
|---|---|---|
| 2026-09-13 | Initial boundary: one Web Client, module descriptors, demo member context, dependency-free static page. | First reviewable parent slice. |
| 2026-09-14 | Replaced with the real architecture: Next.js entrance as Multi-Zones host, Identity & Trust Service, opaque session cookie resolved by module Identity Bridges, registry and entry index, `return_to` rules. Static page recorded as the superseded prototype. | Product-owner instruction, 2026-09-14. See `00c` PA-DEC-04…07, `ARCHITECTURE.md` ADR-019/020/021. |

## User-facing boundary

The member sees one ForKhatri application. The entrance is the default zone at
`/`; each module web app is its own zone. In production all zones share one
origin; in development they run on separate ports and the entrance navigates
to them.

```text
ForKhatri (one origin in production)
├── /            ForKhatri web entrance (platform/forkhatri-web, dev :3100)
│                sign-in, module hub, account sheet
├── /mangaly     Mangaly web zone   (dev :3000, API :8000)
├── /milavn      Milavn web zone    (dev :3001, API :8001)
└── /vyapar      Vyapar web zone    (in development)

Identity & Trust Service (platform/identity-service, dev :8100)
└── database forkhatri_identity (schemas identity, registry, platform)
```

Composition uses Next.js Multi-Zones (PA-DEC-04). Module Federation is not used:
its Next.js plugin never supported the App Router. Moving between the hub and a
module is a full page load; inside a module navigation stays client-side. Each
module adopts `basePath`/`assetPrefix` before production as scheduled module
work.

## Session flow

```text
Browser ──sign-in──▶ Identity service  (POST /v1/auth/code, /code/verify, /welcome, /password)
        ◀── Set-Cookie fk_session (opaque, HttpOnly, SameSite=Lax)
Browser ──request + cookie──▶ Module API
Module Identity Bridge ──POST /internal/v1/sessions/resolve (service key)──▶ Identity service
        ◀── SessionClaims (member_id, display_name, language, identity_level, status)
        cache ≤30 s · unreachable → 503 · ensure member-link row · SET LOCAL RLS context
```

The browser never holds a readable token (PA-DEC-05). There is no API gateway
yet; the resolve call is the seam a gateway would later take over (PA-DEC-06).

## Module registry and entry index

- `registry.module` lists modules with name, taglines (en/hi/te), availability
  (`available`, `in_development`, `planned`), accent and order. Entry URLs come
  from environment configuration, not rows.
- `GET /v1/modules` renders the hub; `POST /v1/modules/{key}/enter` records the
  entry and returns the `entry_url`, or `409 module_unavailable`.
- `registry.member_module_entry` is an entry index (first/last entry, count) used
  for ordering and "continue" affordances. It is not an access list: every member
  may enter every available module, and tiers/roles stay in modules.

## Return-to rules

A module sends a signed-out member to
`<entrance>/?return_to=<encoded module URL>`. The entrance follows `return_to`
only if its origin is the entrance origin or the origin of a registry
`entry_url`; otherwise it is ignored and the member lands on the hub. The
parameter is removed from the address bar once handled, and a short loop guard
keeps a member on the hub if a module immediately bounces them back.

## Identity rule

The Identity & Trust Service is the sole authority for authentication and the
canonical `member_id`. It holds only Level 1/2 trust. Module member-link tables
(`mangaly_identity.account`, `milavn_profile.member_profile`, `vyapar.members`)
stay in module databases and are created just-in-time on first entry. The
platform never reads or writes module tables.

## Deployment rule

The entrance is a frontend surface, not a business module. The service and
database boundaries in `ARCHITECTURE.md` remain valid; the identity service has
its own database (ADR-002). Production routing of zones (entrance rewrites or
edge proxy) is decided at deployment.

## Prototype

`web/parent-app/` (dependency-free HTML/CSS/JS with a demo session) is the
superseded prototype. It is kept for reference and is not extended.
