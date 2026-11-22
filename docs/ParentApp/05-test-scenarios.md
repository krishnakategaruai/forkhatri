---
project: ForKhatri
artifact: Parent Application Test Scenarios
step: 5
status: Ready for Review
updated: 2026-11-22
---

> **Document status (2026-11-22, as built).** Original 2026-09 text kept; the "As-built addendum" at the end records the shipped platform web app (platform/forkhatri-web) and wins where they differ.

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


---

# As-built addendum (2026-11-22): TC-01 to TC-40 mapped to real tests

AUTO = automated and named; MAN = manual only. The TSxx rows above stay valid. Screens are SCR-xx in `03-ux.md`.

Automated suites in the repo:
- Browser end-to-end: `platform/forkhatri-web/scripts/e2e-smoke.mjs` (Playwright, 717 lines, scenario groups using `check(...)`).
- Identity unit tests: `platform/identity-service/tests/` (`test_delivery.py` 7, `test_dev_tools.py` 10, `test_identifiers.py` 6, `test_origin_guard.py` 2, `test_secrets.py` 4).
- Identity integration: `platform/identity-service/tests/integration/test_contract_live.py` (10) and `test_governance_db.py` (10).
- Shared integrations: `shared/forkhatri-integrations/tests/test_integrations.py` (2), `test_places.py` (3).
- Translation parity: `scripts/check_locale_parity.py`.

| ID | Scenario | Screens | Expected | Automation |
|---|---|---|---|---|
| TC-01 | Arrival asks for mobile or email | SCR-02 | question shown, Send code disabled until valid | AUTO e2e-smoke.mjs |
| TC-02 | Code step: identifier chip, resend countdown, dev code hint | SCR-03 | chip and countdown shown | AUTO e2e-smoke.mjs |
| TC-03 | Wrong code shows friendly error | SCR-03 | "isn't right" | AUTO e2e-smoke.mjs |
| TC-04 | New identifier reaches name step; hub greets by name | SCR-04, 06 | greeting has name | AUTO e2e-smoke.mjs |
| TC-05 | Password sign-in reaches hub | SCR-05 | hub greeting | AUTO e2e-smoke.mjs |
| TC-06 | Hub shows six modules; not-open ones are not buttons | SCR-06 | 4 open plus 2 coming | AUTO e2e-smoke.mjs |
| TC-07 | Bell left of avatar, avatar right-most | SCR-06 | order check | AUTO e2e-smoke.mjs |
| TC-08 | Header opaque over scrolled content | SCR-06 | not transparent | AUTO e2e-smoke.mjs |
| TC-09 | Intent chips (English, Hindi, Mangalya with place) | SCR-07 | chips as in script | AUTO e2e-smoke.mjs |
| TC-10 | Unavailable module said plainly | SCR-07 | "Vyapar isn't open yet" | AUTO e2e-smoke.mjs |
| TC-11 | Enter Milavn: enter call, veil, navigation | SCR-23 | request seen | AUTO e2e-smoke.mjs |
| TC-12 | Hindi interface and taglines follow member language | SCR-08, 09 | Devanagari text | AUTO e2e-smoke.mjs |
| TC-13 | Session survives reload; sign out ends it | SCR-08 | session 401, notice | AUTO e2e-smoke.mjs |
| TC-14 | Sign out on all devices returns to arrival | SCR-08 | arrival | AUTO e2e-smoke.mjs (never on shared personas) |
| TC-15 | Honest empty notifications | SCR-10 | "all caught up" | AUTO e2e-smoke.mjs |
| TC-16 | `/` focuses input; Escape clears; suggestion fills input; no dialog while typing | SCR-07 | per script | AUTO e2e-smoke.mjs |
| TC-17 | Hub fits 360x740; tap targets 48px or more; light and dark; en, hi, te | SCR-06 | docHeight within viewport | AUTO e2e-smoke.mjs |
| TC-18 | Deity emblem role=img, localised, inert, no external photo request | SCR-06 | per script | AUTO e2e-smoke.mjs |
| TC-19 | Intent field above keyboard on phone | SCR-07 | bounds within visual viewport | AUTO e2e-smoke.mjs |
| TC-20 | Theme: System default, choice persists, set before first paint, AA contrast, theme-color | SCR-08 | per script | AUTO e2e-smoke.mjs |
| TC-21 | return_to Milavn: kicker names module; navigation attempted | SCR-02 | per script | AUTO e2e-smoke.mjs |
| TC-22 | return_to evil origin, javascript:, malformed is ignored | SCR-02 | lands on hub | MAN (rule in `lib/return-to.ts`; no script case) |
| TC-23 | Bounce-loop guard (20 s) | SCR-06 | stays on hub | MAN |
| TC-24 | No page errors or view-transition rejections | all | zero | AUTO e2e-smoke.mjs |
| TC-25 | Identifier parsing (10-digit mobile, email, invalid) | SCR-02 | normalised or invalid_identifier | AUTO test_identifiers.py |
| TC-26 | Code delivery adapters | SCR-03 | per tests | AUTO test_delivery.py |
| TC-27 | Foreign Origin on state-changing request rejected | API | 403 origin_not_allowed | AUTO test_origin_guard.py |
| TC-28 | Secrets handling | API | per tests | AUTO test_secrets.py |
| TC-29 | Dev tools (act-as personas, dev session) | SCR-21 | per tests | AUTO test_dev_tools.py |
| TC-30 | Live identity contract (session, code, welcome, modules, enter, sign out) | SCR-02..06 | per tests | AUTO test_contract_live.py (service must run) |
| TC-31 | Governance in database (roles, appointments, approvals, audit) | SCR-12..20 | per tests | AUTO test_governance_db.py |
| TC-32 | Shared integrations and places lookup | SCR-07 | per tests | AUTO test_integrations.py, test_places.py |
| TC-33 | Locale parity en, hi, te, mr, kn | all | exit 0 | AUTO scripts/check_locale_parity.py |
| TC-34 | Admin gates: signed out sees sign-in; non-appointed sees "for people the samaj has appointed" | SCR-24 | gate text | MAN |
| TC-35 | Admin Today as Ramesh: needs-you rows, KPIs, recent activity | SCR-12 | executed once 2026-11-22: 136 members, Milavn moderation 4 open, Vyapar unreachable row | MAN |
| TC-36 | Member detail shows account, modules used, history; actions need reason | SCR-14 | viewed read-only 2026-11-22 | MAN |
| TC-37 | Two-person rule: requester cannot approve own ban or grant; sees Withdraw | SCR-15 | per UI | MAN; server side likely covered by TC-31 (exact test names unverified) |
| TC-38 | Module availability change needs owner and reason | SCR-17 | non-owner refused | MAN |
| TC-39 | Offline: identity service stopped, cached modules dimmed, auto recovery | SCR-22 | reconnecting state | MAN (TS33) |
| TC-40 | Insights loads; empty and failed states; gender and age only from Mangalya candidates | SCR-11 | counts and caveat | MAN |

Run: `node platform/forkhatri-web/scripts/e2e-smoke.mjs`; `platform/identity-service/.venv/Scripts/python -m pytest platform/identity-service/tests`; `python scripts/check_locale_parity.py`. These were not executed in this documentation pass, so pass/fail is unverified.
