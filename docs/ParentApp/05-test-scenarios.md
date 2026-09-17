---
project: ForKhatri
artifact: Parent Application Test Scenarios
step: 5
status: Ready for Review
updated: 2026-09-14
---

# Parent Application Test Scenarios

## Revision history

| Date | Change | Reason |
|---|---|---|
| 2026-09-13 | Initial TS01–TS15 for the static shell. | First reviewable parent slice. |
| 2026-09-14 | TS01–TS04, TS07, TS12 and TS13 restated against the real entrance; TS16–TS34 added for code sign-in, new-member name step, password path, anti-enumeration, resend and rate limits, attempts exhaustion, foreign-origin rejection, return-to allow-list, module enter/unavailable, sign-out propagation and identity-service-down resilience. Layer: API = identity-service contract test; E2E = browser; MOD = module bridge test. | Product-owner instruction, 2026-09-14; contract `07-tech-reqs.md`. |

## Entrance and hub

| ID | Scenario | Expected result | Layer |
|---|---|---|---|
| TS01 | Open the entrance with no session cookie | `GET /v1/session` → `401`; conversational sign-in renders. | E2E |
| TS02 | Open with a valid session | Hub renders directly; no module login anywhere. | E2E |
| TS03 | Load the hub | One portal per `GET /v1/modules` row (six; no Dashboard tile) with correct availability labels. | E2E |
| TS04 | Enter an available module | `POST /v1/modules/{key}/enter` → `200 {entry_url}`; browser navigates there; module shows the member signed in. | E2E |
| TS05 | Select a planned or in-development module | Informational state; no navigation; shell remains usable. | E2E |
| TS06 | Switch between two modules via the hub | Same member in both; no sign-in prompt. | E2E |
| TS07 | Open notifications | Bell opens the notification surface; bell is left of avatar; avatar right-most. | E2E |
| TS08 | Open the account sheet | Name, language, locality and sign-out available; `PATCH /v1/me` persists changes. | E2E |
| TS09 | Keyboard only | All controls reachable with visible focus, including the code input and orb. | E2E |
| TS10 | 320 px viewport | No horizontal overflow; navigation usable. | E2E |
| TS11 | Reduced motion enabled | Non-essential motion and view transitions removed. | E2E |
| TS12 | `GET /v1/modules` fails after a previous visit | Cached portals shown dimmed with an offline state; no blank page. | E2E |
| TS13 | Inspect entrance and module entry markup and storage | No module credential form; no token in `localStorage`, `sessionStorage` or URLs. | E2E |
| TS14 | Semantic structure | One main heading, landmarks, accessible names, logical order. | E2E |
| TS15 | Status contrast | Availability labels meet the contrast baseline and are not colour-only. | E2E |

## Sign-in

| ID | Scenario | Expected result | Layer |
|---|---|---|---|
| TS16 | Code sign-in, existing member, 10-digit mobile | `POST /v1/auth/code` → `202` with `+91` normalised hint; correct code → `200 signed_in`; `fk_session` set `HttpOnly`, `SameSite=Lax`, `Path=/`. | API, E2E |
| TS17 | Code sign-in, new identifier | Verify → `200 {outcome: name_required}` with no cookie; `POST /v1/auth/welcome` with name and language → `201 signed_in`, member created with `identity_level` 1. | API, E2E |
| TS18 | Welcome after the 10-minute window, or with a different code | Rejected (`code_expired` / `code_invalid`); no member created. | API |
| TS19 | Password sign-in, correct password (seeded or imported Mangaly member) | `200 signed_in` + cookie; session `auth_method = password`. | API, E2E |
| TS20 | Password sign-in, wrong password vs. unknown identifier | Both `401 invalid_credentials` with the same body; response times not distinguishable beyond noise (dummy verification). | API |
| TS21 | Anti-enumeration on code request | Existing and unknown identifiers both return `202` with the same fields. | API |
| TS22 | Invalid identifier (`12345`, malformed email, non-E.164 `+` number) | `invalid_identifier`. | API |
| TS23 | Resend before `resend_in` elapses | Entrance keeps resend disabled until the countdown ends. | E2E |
| TS24 | Sixth code request for one identifier within 15 minutes | `429 rate_limited` with `Retry-After`. | API |
| TS25 | Wrong code five times | Next attempt → `code_attempts_exhausted`, even with the correct code; entrance offers a new code. | API, E2E |
| TS26 | Code after 5 minutes | `code_expired`. | API |
| TS27 | State-changing request with `Origin: https://evil.example` | `403 origin_not_allowed`. | API |

## Return-to

| ID | Scenario | Expected result | Layer |
|---|---|---|---|
| TS28 | `?return_to=<Milavn entry URL>/events`, signed out | Card names Milavn; after sign-in browser lands on that URL; parameter removed from the address bar. | E2E |
| TS29 | `?return_to=https://evil.example/`, `javascript:` or malformed value | Ignored; member lands on the hub. | E2E |
| TS30 | Signed-in member sent back to the same `return_to` within the loop window | Stays on the hub instead of bouncing. | E2E |

## Modules and resilience

| ID | Scenario | Expected result | Layer |
|---|---|---|---|
| TS31 | `POST /v1/modules/counsel/enter`; unknown key | `409 module_unavailable`; unknown key → `module_unknown`. | API |
| TS32 | Sign out at the entrance, then call Mangaly and Milavn APIs with the old cookie | Rejected within 30 seconds of sign-out; module web clients redirect to the entrance with `return_to`. `everywhere: true` revokes all the member's sessions. | API, MOD |
| TS33 | Identity service stopped | Module authenticated requests → `503` (never a default member); entrance shows cached registry and reconnecting state; recovers without reload after restart. | MOD, E2E |
| TS34 | Module legacy identity paths with default settings (`X-Milavn-Member-Id` header, `mangaly_session` cookie, Mangaly credential routes) | Not honoured; Mangaly login/sign-up/OTP/reset routes redirect to the entrance. | MOD |
| TS35 | Internal resolve without or with a wrong service key | `401`; with a valid key, only services listed in `SERVICES_RECEIVING_IDENTIFIERS` receive `phone_e164`/`email`. | API |
| TS36 | First entry of a new member into a module | Module creates its member-link row just-in-time; no platform write to module tables. | MOD |
