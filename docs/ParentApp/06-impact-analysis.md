---
project: ForKhatri
artifact: Parent Application Impact Analysis
step: 6
status: Ready for Review
updated: 2026-09-14
---

# Parent Application Impact Analysis

## Revision history

| Date | Change | Reason |
|---|---|---|
| 2026-09-13 | Initial impact analysis for the static shell with a demo session. | First reviewable parent slice. |
| 2026-09-14 | Restated for the real Identity & Trust Service and entrance: module impacts (Mangaly, Milavn, Vyapar), availability coupling, migration, zones; risks updated. | Product-owner instruction, 2026-09-14. |

## Identity and session

The Identity & Trust Service becomes a dependency of every authenticated module
path. The demo session is gone; the browser's only credential is the `fk_session`
cookie, and each module resolves it through the internal API (TR14/TR15). If the
identity service is down, module authenticated requests fail closed with `503`
and the entrance shows an unavailable state.

## Module impacts

| Module | Before | Impact |
|---|---|---|
| Mangaly | Interim credential system in database `mangaly` (`mangaly_identity.account`, `otp_challenge`, `password_reset_token`, `session`; cookie `mangaly_session`) and its own sign-up/login/OTP/reset screens. | `mangaly_identity.account` becomes the member-link table. Active accounts are imported with ids and Argon2id hashes; pending accounts are not. Interim credential routes are switched off by a setting (kept for tests); login screens redirect to the entrance. Home Circle invitations still match on identifiers, so Mangaly receives `phone_e164`/`email` in session claims. |
| Milavn | Development stand-in: `X-Milavn-Member-Id` from `dev_identities.json`, member chosen on `/welcome`. | Development identities imported with their ids; header path disabled by default; `milavn_profile.member_profile` is the member-link table; web client redirects to the entrance. |
| Vyapar | Schema only (`vyapar.members` mirror). | `vyapar.members` is the member-link table; no identity work beyond the bridge when its service is built. |
| All module web apps | Standalone on dev ports. | Must adopt `basePath`/`assetPrefix` and audit raw `/assets/...` paths before production (scheduled module work). |

## Module registry and entry

The entrance introduces `registry.module` and `registry.member_module_entry` in
`forkhatri_identity`. No module domain table is created by the platform, and the
entry index is not an access list.

## Notifications and activity

Delivery, retention and module-specific activity ownership remain platform/module
responsibilities. The header bell is an entry point; no cross-module notification
contract is defined in this slice.

## Privacy

The hub shows only registry data and the member's own entry index. Sensitive
Mangaly information must never appear on the hub. Full phone/email leave the
identity service only to services listed in `SERVICES_RECEIVING_IDENTIFIERS`.

## Accessibility and localization

The entrance is the first surface every member sees. Its text, errors (by stable
code) and taglines must be available in English, Hindi and Telugu.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Identity service outage blocks every module | 99.9% target (ADR-004); fail closed with a clear unavailable state; cached registry on the hub. |
| Sign-out does not reach modules immediately | Resolve cache capped at 30 s (TR15); documented and tested. |
| Open redirect through `return_to` | Origin allow-list of entrance plus registry entry URLs (TR17). |
| Account enumeration through sign-in | Identical `202` for code requests; dummy password verification (TR13/TR19). |
| Migrated members lose access | Ids and password hashes preserved; idempotent import with reconciliation summary (TR23). |
| Legacy module identity paths left on | Disabled by default; enabled only by an explicit development setting (TR15). |
| Parent shell becomes a second dashboard for every module | Keep the hub to registry, entry and parent-owned context. |
| Sensitive module data leaks into the hub | Require explicit contracts; no module data in the session. |
