---
project: ForKhatri
artifact: Parent Application Functional Requirements
step: 2
status: Ready for Review
updated: 2026-09-14
---

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
