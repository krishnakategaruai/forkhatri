---
project: ForKhatri
artifact: Parent Application Impact Analysis
step: 6
status: Ready for Review
---

# Parent Application Impact Analysis

## Identity and session

The parent shell depends on the platform Identity & Trust contract. The current static slice uses demo state only and must not be mistaken for production authentication. The eventual integration replaces the demo session adapter without changing the shell's user-facing behavior.

## Module integration

The shell introduces a stable module registry and entry contract. Each module can later provide its real route, availability, badge, and summary data. No module domain table is created by the parent shell.

## Notifications and activity

The shell introduces read-only summary surfaces. Delivery, retention, and module-specific activity ownership remain platform/module responsibilities.

## Privacy

The parent home must only show data explicitly allowed for parent-level surfacing. Sensitive Mangaly information must not appear in generic cards or summaries merely because Mangaly is installed.

## Accessibility and localization

The shell becomes a shared dependency for all module entry flows. Its navigation labels, status copy, dates, and member-facing text must use the shared localization and accessibility conventions.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Parent shell becomes a second dashboard for every module | Keep it limited to navigation, summary, and parent-owned context. |
| Module cards imply separate products | Use consistent ForKhatri branding and shared session language. |
| Sensitive module data leaks into home | Allow-list summary fields and require module contracts. |
| Placeholder UI becomes a production assumption | Mark demo state and integration seams explicitly. |

