---
project: ForKhatri
artifact: Parent Application Technical Requirements
step: 7
status: Ready for Review
---

# Parent Application Technical Requirements

## TR01 — Static parent shell

Implement the first reviewable slice as dependency-free HTML, CSS, and JavaScript with no embedded secrets or external runtime dependency.

## TR02 — Data-driven module registry

Keep module descriptors in one JavaScript data structure with id, label, description, icon, status, route, and action metadata.

## TR03 — Shared session adapter

Expose a small client-side session adapter. The demo adapter may return a local member, while the production adapter will consume the parent Identity & Trust session.

## TR04 — Parent routing seam

Use stable parent routes or route placeholders for Home, Modules, Activity, and Account. Module entry actions must be replaceable with real module routes.

## TR05 — Resilient rendering

Render the shell from safe defaults when module data or notifications are unavailable. Do not fail the entire page because one module is unavailable.

## TR06 — Accessible interaction

Use semantic HTML, button elements for actions, keyboard-visible focus, labels, live-region messaging where needed, and reduced-motion media queries.

## TR07 — Responsive layout

Use CSS grid/flex layouts and responsive breakpoints without fixed desktop-only dimensions.

## TR08 — No module authentication

The parent shell shall not contain module credential fields, module password storage, or module-specific sign-in fallback logic.

## TR09 — Integration boundary

Later React/TypeScript integration may replace the static implementation, but it must preserve the module descriptor, session, route, and accessibility contracts defined here.

