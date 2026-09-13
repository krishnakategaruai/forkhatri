---
project: ForKhatri
artifact: Parent Application Scope
step: 0
status: Ready for Review
---

# Parent Application Scope

## Decision

ForKhatri is one user-facing application. The existing seven business capabilities are modules inside the application. This parent slice owns the shared entry experience and app shell; it does not replace the modules' domain requirements.

## Parent responsibilities

- Shared ForKhatri brand and application entry.
- One sign-up, sign-in, session, and account context.
- Shared navigation between modules.
- Dashboard/home surface.
- Module discovery and module entry points.
- Shared notifications, profile/account access, help, and settings entry points.
- Responsive web experience that can later become the basis for a mobile application.
- Stable module contracts so modules can be integrated progressively.

## Module relationship

Vyapar, Milavn, Mangaly, Counsel, Payment Services, and Loans & Finance remain separately owned domain capabilities. A module may have a separate backend service, database, requirements set, verification model, revenue model, and release lifecycle. None of those boundaries create a second user-facing application or a second ForKhatri login.

## Explicit non-goals

- Rebuilding module-specific business workflows in the parent shell.
- Inventing cross-module workflows.
- Creating module-specific credentials.
- Implementing payment, matrimonial, event, business, finance, or consultation transactions in the parent shell.
- Deciding final module launch order.

## Initial webpage slice

The first implementation is a responsive parent landing/dashboard webpage with:

1. ForKhatri branding.
2. Shared navigation shell.
3. Module cards and status.
4. Quick actions.
5. Activity and notification previews.
6. Member profile/context controls.
7. Responsive and accessible interaction states.

This slice uses local demo state so the parent experience can be reviewed before backend integration.

