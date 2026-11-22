---
project: ForKhatri
artifact: Platform Functional Requirements, part a: entrance, sign-in, session, identity
step: 2
status: Document status 2026-11-22, as built
updated: 2026-11-22
---

# FR part a: entrance, sign-in, session, identity

Index: `02-functional-requirements.md`. Endpoint ids follow `API-<METHOD>-<path-slug>` (see `API-REFERENCE.md`); table ids `TBL-<schema>.<table>`. FR01-FR18 keep their original numbers (FR01 = FR-001). Status: built / partial / planned. Tests: automated tests are under `platform/identity-service/tests` (governance DB tests need `IDENTITY_DB_TESTS=1`); web checks are manual unless stated; test-scenario ids are in `05-test-scenarios.md`.

Screens named here: SCR-ENTRANCE (signed-out entry, `Entrance.tsx`), SCR-HUB (`Hub.tsx`), SCR-ACCOUNT (`AccountSheet.tsx`, route `/account`), SCR-SPLASH (`Splash.tsx`, `Arrival.tsx`), SCR-OFFLINE (`Offline.tsx`), SCR-ORB (`CommandOrb.tsx`).

## Shared rules for this part
- Session cookie `fk_session`, opaque, HttpOnly, 30-day absolute life (`SESSION_TTL_DAYS`); only a digest of the token is stored (`TBL-identity.session`).
- Errors come as stable codes (examples: `not_signed_in`, `invalid_credentials`, `delivery_unavailable`, `handoff_invalid`, `module_unavailable`, `rate_limited`); the UI maps codes to localised text.
- Rate limits are stored in `TBL-platform.rate_limit_counter` per window `RATE_LIMIT_WINDOW_SECONDS` (900 s): 5 code requests per identifier, 30 per IP; 10 verify tries per challenge; 10 password tries per identifier, 30 per IP.
- Code life 300 s (`OTP_TTL_SECONDS`), 5 attempts, resend after 30 s, verified-grace 600 s for the name step.

---
## FR01 Initialise the session (BR-01, BR-02) - built
Actors: any visitor. Flow: page load calls `GET /v1/session` with credentials; `401 not_signed_in` shows SCR-ENTRANCE, `200` shows SCR-HUB. Alternate: network error shows SCR-OFFLINE. Rules: no demo or locally stored session. Data: `TBL-identity.session`, `TBL-identity.member`. Endpoint: API-GET-v1-session. Accept: signed-out reload shows sign-in; signed-in reload shows hub without flicker (splash covers load). Tests: manual; TC in 05.

## FR02 Shared navigation (BR-04) - built
Header: wordmark, bell immediately left of the avatar, avatar right-most, floating command orb (SCR-ORB); no tab bar (owner rule). Accept: header present at 390 px and 1280 px, no horizontal overflow.

## FR03 Module registry on the hub (BR-03) - built
Hub renders `GET /v1/modules`: name, tagline in member language (`tagline_en/hi/te/mr/kn`), state `available | in_development | planned`, accent; recently entered first by `last_entered_at`; Dashboard is the hub itself. Endpoint: API-GET-v1-modules. Tables: `TBL-registry.module`, `TBL-registry.member_module_entry`. Accept: Payments and Loans & Finance show Planned; Mangalya display name is "Mangalya" (registry key remains `mangaly`, migration 006).

## FR04 Enter a module without a second login (BR-01, BR-02) - built
Tap an available module: `POST /v1/modules/{key}/enter` records the entry (upsert) and returns `entry_url` (from `MODULE_ENTRY_URLS`); the browser navigates. `409 module_unavailable` shows a calm unavailable state. Endpoint: API-POST-v1-modules-key-enter. Table: `TBL-registry.member_module_entry`. Accept: no module credential is ever requested.

## FR05 Notifications entry point (BR-04, BR-21) - partial
The bell opens "You're all caught up". No notification service exists (critique C7); modules keep their own notifications. Planned: shared inbox (FR-045).

## FR06 Account sheet (BR-04) - built
SCR-ACCOUNT shows display name and language (editable via `PATCH /v1/me`), masked phone and email (read-only), theme Light/Dark/System, development "Act as" (dev only), sign-out, sign-out everywhere. Validations: name length and language in `en|hi|te|mr|kn` (`TBL-identity.member` CHECK, migration 007). Endpoint: API-PATCH-v1-me. Gap: no password row, no Privacy/Terms/Help/Grievance entry, no identifier change (BR-17, BR-18).

## FR07 Responsive and accessible behaviour (BR-06) - partial
Keyboard navigation, visible focus, semantic headings, reduced-motion honoured by transitions and splash scripts (`lib/view-transition.ts`, `lib/theme-script.ts`). Not audited with a screen reader (unverified). Critique C16: wide-screen greeting wraps awkwardly.

## FR08 Offline and unreachable service (BR-05) - built
If identity or modules endpoint is unreachable, SCR-OFFLINE shows the last cached public registry (dimmed) from local storage (`lib/storage.ts`); never a token or per-member entry times.

## FR09 Data-driven module seams (BR-03) - built
Entry URLs come from `MODULE_ENTRY_URLS`; availability from the registry table, changeable by an owner in the console (FR-031).

## FR10 Never create module credentials (BR-02) - built (rule)
No module password, OTP or account is created or requested by the entrance.

## FR11 Sign in with a one-time code (BR-09, BR-10) - built; phone delivery blocked in production
Flow: enter phone or email, `POST /v1/auth/code` returns `202` with masked destination and resend seconds (same reply whether or not a member exists); enter the 6 digits, `POST /v1/auth/code/verify`: `outcome: signed_in` for a known member, `name_required` for a new one. Delivery: `SMS_PROVIDER` / `EMAIL_PROVIDER` = console (dev), disabled, resend (email), shared. In production `console` is refused at start-up (`Settings._production_guard`); with `SMS_PROVIDER=disabled` a phone request returns `delivery_unavailable` (critique C1). Dev only: `DEV_EXPOSE_OTP` returns the code in the response. Tables: `TBL-identity.otp_challenge` (digest with `OTP_PEPPER`), `TBL-platform.rate_limit_counter`. Endpoints: API-POST-v1-auth-code, API-POST-v1-auth-code-verify. Accept: wrong code 5 times locks the challenge; resend before 30 s is refused.

## FR12 New-member name step (BR-09) - built
After `name_required`, SCR-ENTRANCE asks display name and language; `POST /v1/auth/welcome` within the grace window (600 s) creates the member (`identity_level` 1 is NOT set: see FR-021) and signs in; `201`. Endpoint: API-POST-v1-auth-welcome. Table: `TBL-identity.member`.

## FR13 Password sign-in (BR-09, BR-10) - built (secondary)
"Use a password instead": `POST /v1/auth/password`; any failure returns one `invalid_credentials`; a dummy hash check hides unknown identifiers. Endpoint: API-POST-v1-auth-password. Table: `TBL-identity.password_credential`. Gap: no endpoint to set, change or reset a password (critique C1), so only imported or seeded members have one.

## FR14 Return to the intended module (BR-01) - built
`return_to` is followed after sign-in only when its origin is the entrance or a registry `entry_url` origin (`lib/return-to.ts`); parameter removed from the address; repeat bounce within 20 s keeps the member on the hub.

## FR15 Sign out (BR-02) - built
`POST /v1/auth/sign-out` (optional `everywhere: true`) returns `204`, clears the cookie; modules stop accepting within 30 s (resolve cache). Endpoint: API-POST-v1-auth-sign-out. Table: `TBL-identity.session`. Rule: automated tests must never use "everywhere" on shared personas.

## FR16 Localised interface (BR-11) - built
English, Hindi, Telugu, Marathi, Kannada across entrance (`lib/i18n.ts`), console (`lib/admin-i18n.ts`), insights (`lib/insights-i18n.ts`), registry taglines. Language chosen while signed out is remembered locally and becomes `preferred_language` for a new member. Gap: human review of Indic text (critique C13).

## FR17 Modules accept the ForKhatri session (BR-02, BR-04) - built (module side)
Modules resolve `fk_session` via `POST /internal/v1/sessions/resolve` (service key; 30-second cache) and redirect signed-out members to the entrance. Endpoint: API-POST-internal-v1-sessions-resolve.

## FR18 Existing identities imported (BR-07) - built
Mangaly accounts and Milavn dev identities imported with ids preserved; Mangaly passwords kept (password hashes in `TBL-identity.password_credential`).

---
## New requirements (built since 2026-09-14)

## FR-019 Cross-origin session handoff (BR-01) - built
Purpose: let a module on another origin (local dev ports, or a preview host) receive the session. Flow: a signed-in entrance calls `POST /v1/auth/handoff` and gets a one-time `code` valid 60 s; the target calls `POST /v1/auth/handoff/redeem` and receives its own `fk_session` cookie. Errors: `handoff_invalid` (401) when expired, reused or the session ended. Business rule: stored in service memory (`_handoffs`), so it does not survive a restart and does not work across more than one identity process (unverified for scale). Endpoints: API-POST-v1-auth-handoff, API-POST-v1-auth-handoff-redeem. Accept: second redeem of the same code fails.

## FR-020 Internal service API (BR-02, BR-19) - built
Called by module services with `X-Service-Key`-style authentication (`SERVICE_KEYS`), refused when reached through the public edge (`not_through_the_edge` returns 404):
- API-POST-internal-v1-sessions-resolve: member id, language, level, `admin_scopes` (for example `milavn.moderate`).
- API-POST-internal-v1-members-provision: create a member for another person (level 0). Only services in `SERVICES_RECEIVING_IDENTIFIERS` (default mangaly) receive phone or email.
- API-POST-internal-v1-members-member_id-retire-provisioned: remove an unclaimed provisioned member.
- API-POST-internal-v1-members-lookup: names for up to 200 ids.
Risks: critique C4, C5.

## FR-021 Identity level rises on first verified sign-in (BR-19) - **planned (known bug)**
Today `identity_level` is never raised from 0 to 1 after a verified code, so provisioned members stay "waiting to sign in" (critique C4). Acceptance: after first verified code level becomes 1 and audit records it.

## FR-022 Claim a provisioned profile - **planned**
First sign-in of a provisioned member shows "A profile was created for you by X: keep, edit or delete"; unclaimed profiles expire.

## FR-023 Development persona switching (BR-23) - built (dev only)
`GET /dev/v1/personas`, `POST /dev/v1/sessions` (header token `DEV_TOOLS_TOKEN` for automation) open a session with `auth_method='dev'` (migration 004). Router is mounted only when `DEV_TOOLS_ENABLED` and refused in production. UI: `components/dev/DevActAs.tsx` ("Act as (development)"; signed out: "Development: act as…"). Script: `platform/identity-service/scripts/dev_session.py`. Personas defined in `app/dev_tools/personas.py`; `krishna` never for automation. Endpoints: API-GET-dev-v1-personas, API-POST-dev-v1-sessions.

## FR-024 Health check (BR-22) - built
`GET /health` on the identity service (no auth) for monitoring and compose. Endpoint: API-GET-health.

## FR-025 Splash and arrival experience (BR-04) - built
`Splash.tsx` and `Arrival.tsx` (with `splash.css`, `arrival.css`, `lib/splash-script.ts`) show the first-load brand sequence and hero art (`lib/hero-art.ts`, `DevotionalPortrait.tsx`); skipped for reduced-motion. Owner theme and devotional imagery: see `platform/forkhatri-web/DESIGN-NOTES.md`.

## FR-026 Theme (BR-06) - built
Light, Dark, System in the account sheet; `lib/theme.ts`, `theme-script.ts` apply before paint to avoid flash.

## FR-027 Intent bar and voice orb (BR-03) - built (limited)
`CommandOrb.tsx` and `lib/intent.ts` map typed or dictated phrases (about 60 keyword terms, en/hi/te) to modules. Voice uses the browser SpeechRecognition with the chosen language; accuracy and privacy of audio depend on the browser (critique C14); intents may point to planned modules. Not the guided voice conversation the owner wants in modules.

## FR-028 Rate limiting (BR-10) - built
See shared rules; per-IP caps may hit shared mobile addresses (critique C15). Table `TBL-platform.rate_limit_counter`.

## FR-029 Cross-origin and cookie policy (BR-02) - built
CORS allow-list `CORS_ALLOWED_ORIGINS`; cookie attributes via `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_DOMAIN`, `SESSION_COOKIE_SAMESITE` (default lax); `LOCAL_HTTP_TEST` relaxes for local compose test.

## FR-030 Sessions are not listed or limited (BR-24) - planned gaps
No device list, no idle timeout, no new-sign-in alert, no step-up (critique C8).

## FR-040 to FR-046 Planned platform features (not built)
FR-040 password set and reset; FR-041 identifier change and second identifier; FR-042 data export; FR-043 account deletion with module fan-out; FR-044 consent and privacy notice in five languages; FR-045 notification inbox and channel preferences; FR-046 support, grievance and appeal screen. Each traces to BR-17, BR-18, BR-21 and the matching critique item.

## Acceptance traceability
BR-01: FR01-FR04, FR14, FR-019. BR-02: FR01, FR10, FR15, FR17, FR-020. BR-09/10: FR11-FR13, FR-028. BR-11: FR16. BR-19: FR-020 to FR-022. BR-23: FR-023.
