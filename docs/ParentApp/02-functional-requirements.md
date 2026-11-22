---
project: ForKhatri
artifact: Parent Application (Platform) Functional Requirements, index
step: 2
status: Document status 2026-11-22, as built
updated: 2026-11-22
---

# Platform Functional Requirements: index

**Document status 2026-11-22, as built.** Split by feature area. Original FR01-FR18 keep their numbers (detailed in 02a); new ones are FR-019 onward. Original 2026-09 text is preserved in Appendix A.

| File | Covers | FR ids |
|---|---|---|
| `02a-functional-requirements-entrance-identity.md` | Entrance, hub, sign-in, session, handoff, internal API, dev tools, theme, intent bar | FR01-FR18, FR-019 to FR-030, planned FR-040 to FR-046 |
| `02b-functional-requirements-admin-console.md` | Governance console, roles, suspensions, approvals, audit, queues | FR-031 to FR-039, FR-031a, FR-047, FR-048 |
| `02c-functional-requirements-insights-integrations-ops.md` | Members dashboard, shared integrations, deployment | FR-050 to FR-060 |

Numbering note: FR-031 to FR-039 are console items; FR-031a is "module open or closed" (inserted late, not renumbered). Ids FR-040 to FR-046 are reserved for planned features not built.

## BR to FR map
BR-01 FR01-04, 14, 019 | BR-02 FR01, 10, 15, 17, 020 | BR-03 FR03, 09, 027 | BR-04 FR02, 05, 06, 025 | BR-05 FR08 | BR-06 FR07, 026 | BR-07 FR18 | BR-08 FR03 | BR-09 FR11-13 | BR-10 FR11, 13, 028 | BR-11 FR16, 048 | BR-12 FR-031, 035-038 | BR-13 FR-034 | BR-14 FR-033, 039 | BR-15 FR-031a, 047 | BR-16 FR-050, 051 | BR-17 FR-042 to 044 (planned) | BR-18 FR-041 (planned) | BR-19 FR-020 to 022 | BR-20 FR-052 to 055 | BR-21 FR-045 (planned) | BR-22 FR-056 to 060 | BR-23 FR-023 | BR-24 FR-030 (planned).

## Appendix A: original functional requirements (history, unchanged)

# Parent Application Functional Requirements

## Revision history

| Date | Change | Reason |
|---|---|---|
| 2026-09-13 | Initial FR01–FR10 for the static shell. | First reviewable parent slice. |
| 2026-09-14 | FR01–FR04, FR06 and FR08 revised for the real entrance and identity service (no demo session, no tab bar, registry API). FR11–FR18 added: code sign-in, new-member name step, password path, return-to, sign-out, account sheet, languages, module session acceptance. Contract: `07-tech-reqs.md`. | Product-owner instruction, 2026-09-14. |

## FR01 — Initialize the parent session (revised 2026-09-14)

When the entrance loads it shall call `GET /v1/session` with credentials included and render the signed-out entry (`401 not_signed_in`) or the member hub (`200`). There is no demo or locally stored session.

## FR02 — Render shared navigation (revised 2026-09-14)

The signed-in entrance shall provide a header with the ForKhatri wordmark, the notifications bell immediately left of the member avatar, and the avatar as the right-most item, plus a floating command orb for navigation. There is no tab bar. Navigation shall remain available on supported viewport sizes.

## FR03 — Render the module registry (revised 2026-09-14)

The hub shall render every module returned by `GET /v1/modules` with its name, tagline in the member's language, availability state (`available`, `in_development`, `planned`) and accent. Recently entered modules are ordered first using `last_entered_at`. Dashboard is the hub itself and has no tile.

## FR04 — Enter a module without a second login (revised 2026-09-14)

Selecting an available module shall call `POST /v1/modules/{key}/enter` and navigate to the returned `entry_url` without requesting any module credential. A `409 module_unavailable` or a non-available module shall show a clear, non-destructive unavailable state.

## FR05 — Render shared activity and notifications

The entrance shall show a concise notification entry point using parent-level records or integration placeholders. Module-specific details shall be opened in the relevant module surface.

## FR06 — Render member context (revised 2026-09-14)

The member avatar shall open an account sheet with display name and preferred language (`PATCH /v1/me`), masked phone/email, and sign-out. The platform holds basic identity only; every other profile detail is edited inside the module that owns it. These are platform controls, not module-owned account controls.

## FR07 — Preserve responsive and accessible behavior

The entrance shall support keyboard navigation, visible focus, semantic headings, accessible names, reduced-motion preferences, and responsive layouts without horizontal overflow.

## FR08 — Handle unavailable integrations (revised 2026-09-14)

If the identity service or `GET /v1/modules` is unreachable, the entrance shall show the last cached public registry dimmed with a clear offline state rather than a blank page. Cached data never includes a token or per-member entry times.

## FR09 — Preserve module integration seams

The module registry shall remain data-driven; entry URLs come from environment configuration (`MODULE_ENTRY_URLS`), not code.

## FR10 — Never create module credentials

The entrance and its module-entry behavior shall not create, store, or request module-specific passwords, OTPs, or accounts.

## FR11 — Sign in with a one-time code

A signed-out member enters a phone number or email. The entrance calls `POST /v1/auth/code`, shows the masked destination and a resend countdown, then submits the 6-digit code to `POST /v1/auth/code/verify`. An existing member is signed in (`outcome: signed_in`). The response to a code request is identical whether or not a member exists.

## FR12 — New-member name step

When verification returns `outcome: name_required`, the entrance asks for a display name and preferred language and calls `POST /v1/auth/welcome` within the 10-minute window, which creates the member and signs them in.

## FR13 — Password sign-in (secondary)

"Use a password instead" lets a member with a password sign in through `POST /v1/auth/password`. Failures show one generic `invalid_credentials` message.

## FR14 — Return to the intended module

When the entrance is opened with `return_to`, it follows the target after sign-in (or immediately if already signed in) only if the target origin is the entrance origin or a registry `entry_url` origin; otherwise it shows the hub. The parameter is removed from the address bar once handled, and a repeat bounce within a short window keeps the member on the hub.

## FR15 — Sign out

Sign-out calls `POST /v1/auth/sign-out` (optionally `everywhere: true`), clears the cookie and returns to the signed-out entry. Modules stop accepting the session within 30 seconds.

## FR16 — Localized interface

All entrance text, errors (mapped from stable error codes) and module taglines are available in English, Hindi and Telugu. A language chosen while signed out is remembered locally and applied to a new member's `preferred_language`.

## FR17 — Modules accept the ForKhatri session

Every module service resolves `fk_session` through its Identity Bridge (TR15) and every module web client redirects signed-out members to the entrance with `return_to` and shows a way back to the hub (TR16). Delivered by module teams; listed here so the parent acceptance tests can cover it.

## FR18 — Existing identities imported

Active Mangaly accounts and Milavn development identities are imported into the platform with their ids preserved (TR23), so returning members sign in with their existing identifier and, for Mangaly, their existing password.


## Account deletion (added 2026-11-22)

Numbering continues the platform set (FR-061 and up). Contract and as-built detail: `ACCOUNT-DELETION.md`. Traces to BR-25 to BR-30.

| ID | Requirement | Rules | Endpoints and tables | Screens | Status |
|---|---|---|---|---|---|
| FR-061 | Preview: show what will be deleted and what will be kept. | Signed-in member only. | `GET /v1/account/delete/preview` | Delete sheet | Built |
| FR-062 | Re-authentication step-up. | Password, or a fresh one-time code sent only to the member's own phone or email. | `POST /v1/account/delete/code` | Delete sheet | Built |
| FR-063 | Start a kind A deletion. | Body: confirm "DELETE" plus either password or challenge_id and code. Wrong confirm word refused; wrong password 401; 3 attempts per hour per member, every attempt counts; 409 `admin_role_held` while the member holds a live admin role; closes the member and revokes all sessions at once; clears the cookie; idempotent. | `POST /v1/account/delete`; tables `identity.deletion_job`, `deletion_job_module` | Delete sheet | Built |
| FR-064 | Orchestrate every module. | Call `POST /internal/v1/members/{id}/erase` on all modules in parallel with the service key; a module with no URL is `failed: not_configured`, never skipped; identity rows removed only when all modules are `done` or `nothing_to_delete`. | function `identity.finalize_member_deletion` | none | Built |
| FR-065 | Retry and escalate. | Backoff 30 s doubling to 6 h, loop every 30 s, up to 7 days; after 3 failed attempts or 7 days the job is stuck; admin can retry. | `GET /v1/admin/deletions/stuck`, `POST /v1/admin/deletions/{job_id}/retry` | Admin Modules page | Built |
| FR-066 | Progress and receipt. | Public by job id (the job id is the capability because the member is signed out); receipt keeps tombstone, per-module counts, retained list with reasons; member id nulled. | `GET /v1/account/deletion/{job_id}` | Progress and receipt page | Built |
| FR-067 | Audit tombstone. | Member id in audit rows replaced by an HMAC-SHA256 tombstone; notes, subject, details and ip about the member cleared. | `governance.audit_event` | none | Built |
| FR-068 | Module erase contract (kind A, internal). | Service-key authenticated, idempotent; answers `done`, `nothing_to_delete` or `partial`; counts, retained list, files removed. | `POST /internal/v1/members/{id}/erase` in each module | none | Built in all four modules |
| FR-069 | Module-level deletion (kind B). | Session-authenticated, body confirm "DELETE", 3 per hour, then sign the member out of that module. | `POST /privacy/delete-account-data` (Vyapar `/v1/privacy/delete-account-data`; Counsel `/me/delete-account-data`) | Each module's own settings | Built; browser not checked |
| FR-070 | Notify other parties. | People affected (for example Counsel bookings, Milavn event attendees) are told; the deleted member shows as "Deleted member". | per module | per module | Built (see module docs) |

Acceptance: wrong confirm word refused; wrong password 401; old session 401 afterwards; second erase answers `nothing_to_delete`; zero identity rows left; a failing module is retried and the job reaches done. Evidence in `05-test-scenarios.md`.
