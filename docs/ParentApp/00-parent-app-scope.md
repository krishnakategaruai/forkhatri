---
project: ForKhatri
artifact: Parent Application Scope
step: 0
status: Ready for Review
updated: 2026-09-14
---

# Parent Application Scope

## Revision history

| Date | Change | Reason |
|---|---|---|
| 2026-09-13 | Initial scope for a static parent landing/dashboard slice with local demo state. | First reviewable parent slice. |
| 2026-09-14 | Scope restated against the real design: a Next.js ForKhatri web entrance (`platform/forkhatri-web`) and a platform Identity & Trust Service (`platform/identity-service`). Demo session removed from scope. `web/parent-app/` recorded as the superseded prototype, kept. | Product-owner instruction, 2026-09-14: one ForKhatri sign-in and identity, then the member chooses a module. Decisions: `00c-identity-and-entrance-decisions.md`. |

## Decision

ForKhatri is one user-facing application. The seven business capabilities are
modules inside it. The member signs in once to ForKhatri, receives one canonical
member identity, and then chooses which module to enter. This parent slice owns
that entrance, the module hub and the platform identity; it does not replace the
modules' domain requirements.

## Components in scope

| Component | Path | Dev port | Role |
|---|---|---|---|
| Identity & Trust Service | `platform/identity-service/` | 8100 | Canonical member, credentials, one-time codes, sessions, module registry, member→module entry index. Database `forkhatri_identity`. |
| ForKhatri web entrance | `platform/forkhatri-web/` | 3100 | Conversational sign-in and sign-up, module hub, account sheet, `return_to` routing. Next.js, same stack as the modules. |
| Parent prototype (superseded) | `web/parent-app/` | — | Static HTML/CSS/JS shell with a demo session. Kept for reference; not the product and not deleted. |

## Parent responsibilities

- Shared ForKhatri brand and the single application entrance.
- One sign-up and sign-in (code first, password as a secondary path), one session, one account context.
- The module hub, rendered from the module registry, and entry into modules.
- Safe return to the module a member was trying to reach (`return_to`).
- Account sheet: display name, preferred language, sign-out. Profile details live in each module (basic identity only on the platform).
- Header entry points: notifications bell immediately left of the member avatar; avatar right-most.
- Platform Level 1/2 trust only (verified phone or email).
- The integration contract every module follows (`07-tech-reqs.md` TR10–TR24).
- Mobile-first, accessible, English/Hindi/Telugu.

## Module relationship

Mangaly, Milavn, Vyapar, Counsel, Payment Services and Loans & Finance remain
separately owned domain capabilities with their own services, databases,
requirements and release lifecycles. Each keeps its own member-link record keyed
by the canonical `member_id`, and owns its tiers, roles and Level-3 trust. None
of those boundaries create a second user-facing application or a second login.
Dashboard is the hub itself, not a separate tile.

## Explicit non-goals

- Rebuilding module business workflows in the entrance.
- Inventing cross-module workflows or surfacing sensitive module data on the hub.
- Creating module-specific credentials, or module tiers/roles in the platform.
- An API gateway (deferred to deployment, `00c` PA-DEC-06).
- Implementing payment, matrimonial, event, business, finance or consultation transactions.
- Deciding final module launch order.
- A demo or simulated session.

## Current slice

1. Identity & Trust Service with the public and internal APIs in TR13/TR14.
2. ForKhatri web entrance: sign-in (identifier → code → name for new members → hub), password path, module hub, account sheet, `return_to`.
3. Import of existing Mangaly active accounts and Milavn development identities with preserved ids (TR23).
4. Module integration (Identity Bridges, entrance redirects) is carried out by module teams in parallel and recorded in their own implementation records.
