---
project: ForKhatri
artifact: Parent Application Impact Analysis
step: 6
status: As built (2026-11-22); 2026-09-14 history retained
updated: 2026-11-22
---

# Parent Application Impact Analysis

> **Document status 2026-11-22, as built.** Original 2026-09-14 content is kept as history; the "As-built update" section at the end is current and wins where they differ. See API-REFERENCE.md, 07a-er-model.md and 07-tech-reqs.md.


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

---

# As-built update (2026-11-22)

Revision row: 2026-11-22, "Impact analysis restated for the platform as built: 43 endpoints, governance, four schemas, five languages, seven modules in the registry; change-risk table per component", reason: owner request that documents match the application as built. The 2026-09-14 text above stays valid as history; where it says three languages, Mangaly-only identifier sharing or "three schemas", read the tables below.

## B1. Dependency map (who depends on what)

| Component | Depends on | Depended on by |
|---|---|---|
| Identity service (`platform/identity-service`, port 8100) | Postgres `forkhatri_identity`; Resend (email); shared messaging library; module APIs (insights, admin federation) | Web entrance; every module's Identity Bridge (internal API); admin console |
| `fk_session` cookie | `identity.session`, `SESSION_COOKIE_*` settings | Every module web app and API; the edge routing (one origin in production) |
| Internal API `/internal/v1/sessions/resolve` | `SERVICE_KEYS`, `identity.session`, `identity.member`, `governance.role_assignment` | Mangalya, Milavn, Vyapar, Counsel bridges (and their moderation chokepoints via `admin_scopes`) |
| Internal `members/provision` and `retire-provisioned` | `SERVICES_RECEIVING_IDENTIFIERS` | Mangalya parent-created profiles |
| Internal `members/lookup` | `identity.member` | Any module showing another member's name |
| `registry.module` + `MODULE_ENTRY_URLS` | admin `PATCH /v1/admin/modules/{key}` | Hub tiles, `enter` endpoint, console module list |
| Governance (roles, suspension, approvals, audit) | `identity.member`, session revocation, module federation | Admin console web; every module (a suspended member fails resolution everywhere) |
| Insights | module APIs (`MODULE_API_URLS`) with service keys | Members dashboard page |
| Web entrance (`platform/forkhatri-web`, 3100) | Identity API; `NEXT_PUBLIC_IDENTITY_API` | Everything a member sees first; hub, account sheet, admin console, insights page |
| Shared integrations library | none (stdlib) | Identity delivery; Counsel, Vyapar, Milavn, Mangalya adapters |

## B2. Change-risk notes (what breaks if X changes)

| Change | Breaks or affects | Risk | Mitigation or check |
|---|---|---|---|
| Rename or change `SESSION_COOKIE_NAME`, or `SESSION_COOKIE_DOMAIN` / `SAMESITE` | Every module's cookie read; cross-origin tunnels; production `__Host-` guard | High | Change in one place; re-run production guard; test hub to module hop |
| Alter `identity.session` columns or digest scheme | Every module bridge (via resolve), sign-out everywhere, suspension | High | Keep resolve contract; migration is additive |
| Change `SessionClaims` shape (`/sessions/resolve`) | All four module bridges and their tests | High | Add fields only; never remove or rename (`admin_scopes` was added this way) |
| Add or remove a role or permission in `roles.py` | Who can act in console; `admin_scopes` strings modules map (`milavn.moderate`) | High | Roles are code: review as a change; update 08 matrix; module chokepoint tests |
| Change `SERVICE_KEYS` or `SERVICES_RECEIVING_IDENTIFIERS` | Module bridges fail with 401 `service_unauthorized`; Mangalya loses phone claims and provisioning | High | Rotate keys on both sides together (module `PLATFORM_SERVICE_KEY`) |
| Change rate-limit values | Sign-in lockouts (shared carrier IPs) or weaker brute-force protection | Medium | Keep deployed defaults; local `.env` may raise |
| Widen `preferred_language` again | DB check constraint, `LANGUAGES` tuple, web catalogue, registry taglines (migration 007 shows the pattern) | Medium | Additive migration; add taglines; all web strings |
| Change `registry.module` keys | Service keys, module data, entry URLs, role scopes, audit module keys (the key `mangaly` is kept although the product is Mangalya) | High | Change display name only (migration 006 pattern) |
| Re-run migration 002 | Resets availability and taglines of live modules, overwriting admin changes | Medium | Do not re-run on a live database |
| Grant DELETE on `identity.member` to fix `retire-provisioned` | Weakens the no-delete safeguard; affects DPDP erasure design | Medium | Decide with account deletion design (owner) |
| Make module `availability` stricter | Hub tiles, `enter` returns 409 | Low | Console warns; reversible |
| Suspend or ban a member | Sessions revoked in every module within about 30 s; member sees `account_unavailable` | Medium | Reason code and note required; second person for bans |
| Turn on `SMS_PROVIDER=shared` | Phone sign-in changes from `delivery_unavailable` to codes; cost and DLT templates | Medium | Vendor adapter in shared library only; no module change |
| Change `CORS_ALLOWED_ORIGINS` | Browser calls and the Origin guard for all writes | High | Single list; add each module web origin |
| Move to multiple identity processes | Handoff codes are in process memory and would fail across processes | Medium | Move to database or cache before scaling out |
| Edit insights output | Dashboard page; privacy of small cells | Medium | Suppress small cells (CRITIQUE C9) |
| Edit audit actions | Console audit filters (`action` prefix) | Low | Keep dotted names |

## B3. Module impacts as of 2026-11-22

| Module | Dependency on platform | Note |
|---|---|---|
| Mangalya | Identity bridge; receives phone and email claims; provisions members; module link `mangaly_identity.account`; admin queues through the gateway | Only service in `SERVICES_RECEIVING_IDENTIFIERS` by default |
| Milavn | Identity bridge; `admin_scopes` for moderation (`milavn.moderate`); module profile table | Legacy `X-Milavn-Member-Id` path off by default |
| Vyapar | Registered `in_development`; one profile per member; entry URL 3011 | Not in the deployed kit |
| Counsel | Entry URL 3014; service key present in dev settings | Not in the deployed kit |
| Payment Services, Loans & Finance | Registry rows only, `planned` | Hub shows them as planned |
| Dashboard / hub | Is the entrance itself | No registry row |

## B4. Cross-cutting concerns not covered by the platform

Notifications (the bell is an empty state; no shared inbox), account deletion and data export (not built), consent record (not built), device list and step-up authentication (not built). Each would touch every module; see 08 for DPDP mapping and CRITIQUE-platform C3, C7, C8.


## Account deletion (added 2026-11-22)

Supersedes B4's "account deletion and data export (not built)": deletion is built, export is not.

- Cross-module calls: identity calls `POST /internal/v1/members/{id}/erase` on Vyapar, Milavn, Mangalya and Counsel in parallel (header `X-ForKhatri-Service: identity` plus the module's service key). A module that is down leaves the job open; the member is already signed out and cannot sign in.
- Identity data touched: member, session, password credential, one-time codes and rate-limit keys, registry entries, role assignments, approvals, suspensions; audit rows are rewritten to a tombstone, not removed.
- Other members: shared records show "Deleted member" (Vyapar, Milavn, Counsel); Mangalya one-to-one chats are removed for both sides; Milavn circles are handed to another organiser; event attendees and Counsel counterparties are notified.
- Files on disk: uploads, photos, voice and document folders are removed by each module (Vyapar 3 files, Milavn 7 folders, Mangalya photos, Counsel files).
- Caches: sessions are revoked at the start. Module caches were not separately verified.
- Risks: partial deletion if a module is down (retry for 7 days, admin list); an admin cannot be deleted while holding a role; unpaid Counsel earnings are lost (open decision); a banned member can sign up again (not enforced).
