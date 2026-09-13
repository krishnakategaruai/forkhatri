---
project: ForKhatri
artifact: Parent Application Architecture
step: 0b
status: Ready for Review
---

# Parent Application Architecture

## User-facing boundary

The user sees one ForKhatri Web Client. The client owns the application shell and routes into module surfaces. A module surface may later be served by the Core Platform or by an isolated service, but that deployment choice is invisible to the member.

```text
ForKhatri Web Client
├── Shared session and member context
├── Shared app shell and navigation
├── Dashboard / home
├── Module registry and module entry routes
├── Shared notifications and account surfaces
└── Module surfaces
    ├── Vyapar
    ├── Milavn
    ├── Mangaly
    ├── Counsel
    ├── Payment Services
    └── Loans & Finance
```

## Integration boundary

The parent shell consumes a stable module descriptor rather than importing module internals. A descriptor contains a module id, label, description, icon, route, availability, and permitted entry action. Real module data will be integrated later through the contracts already defined by the platform architecture.

## Identity rule

The parent Identity & Trust capability is the sole authority for authentication and the canonical member identity. The parent webpage may render a demo member context now, but the integration seam is `member_id` plus a shared authenticated session.

## Deployment rule

The parent webpage is a frontend surface, not a new business module. It may be deployed with the Core Platform web client. The backend service and database boundaries in `ARCHITECTURE.md` remain valid and are not collapsed by this page.

## Current implementation choice

The first reviewable artifact is dependency-free HTML, CSS, and JavaScript. This keeps the parent experience inspectable before adopting the repository's eventual React/TypeScript build tooling.

