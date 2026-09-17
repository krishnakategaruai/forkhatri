---
project: ForKhatri
artifact: Parent Application Security and Performance
step: 8
status: Ready for Review
updated: 2026-09-14
---

# Parent Application Security and Performance

## Revision history

| Date | Change | Reason |
|---|---|---|
| 2026-09-13 | Initial security, performance and accessibility baseline for the static shell. | First reviewable parent slice. |
| 2026-09-14 | Restated for the real identity service and entrance: session cookie (TR12), credentials and codes (TR19), abuse and forgery protection (TR20), internal API, return-to, data minimisation, no-RLS rationale, availability and caching. | Product-owner instruction, 2026-09-14. |

## Threats and controls

| Threat (STRIDE) | Control | Ref |
|---|---|---|
| Token theft by injected script (I) | One opaque token in an `HttpOnly` cookie (`fk_session`; production `__Host-fk_session`), `Secure` when deployed, no `Domain`; never in `localStorage`, `sessionStorage`, URLs or response bodies. | TR12, RFC 10017 |
| Stolen database contents used as credentials (S) | Session tokens stored only as SHA-256 digests; OTPs as HMAC-SHA256 keyed by `OTP_PEPPER` over `challenge_id:code`; passwords as Argon2id. | TR12, TR19 |
| Guessing or brute-forcing codes (S) | 6 digits, 5-minute expiry, 5 attempts per challenge, 30-second resend interval, 10 verifications per challenge. | TR19, TR20 |
| Account enumeration (I) | Identical `202` for code requests; identical `invalid_credentials`; dummy Argon2id verification for unknown identifiers. | TR13, TR19 |
| Credential stuffing and SMS pumping (D) | Shared database-backed fixed-window limiter: codes 5/identifier and 30/IP per 15 min; passwords 10/identifier and 30/IP per 15 min. Deployed defaults; only local development may raise them. | TR20 |
| Cross-site request forgery (T) | `SameSite=Lax` plus rejection of state-changing requests whose `Origin` is outside `CORS_ALLOWED_ORIGINS` (`403 origin_not_allowed`); CORS only for entrance and module origins, with credentials. `Lax` is chosen over `Strict` so SMS/notification deep links open signed in. | TR12, TR20 |
| Open redirect via `return_to` (S) | Follow only the entrance origin or registry `entry_url` origins; `http`/`https` only; otherwise hub. | TR17 |
| Internal API abuse (E) | Server-to-server only; `X-ForKhatri-Service` and `X-ForKhatri-Service-Key` compared in constant time against `SERVICE_KEYS`; never callable from browsers. | TR14 |
| Over-sharing identifiers with modules (I) | Session claims carry `phone_e164`/`email` only for services in `SERVICES_RECEIVING_IDENTIFIERS` (development: `mangaly`). Public responses show masked hints only. | TR13, TR14 |
| Module trusting a missing identity service (E) | Module bridges fail closed with `503`; never a default member. Legacy development identity paths disabled by default. | TR15 |
| Revoked session still accepted (E) | Resolve cache ≤30 s (negative 5 s); `everywhere` sign-out revokes all sessions. Residual window accepted in ADR-019. | TR15 |
| Sensitive module data on the hub (I) | No module tiers, roles, trust or Mangaly data in the session or hub; explicit contracts required. | TR11 |
| Secrets in source (I) | All secrets in `.env`; `.env.example` holds `CHANGE_ME` placeholders; no hardcoded identity URL, key, entrance URL or cookie name. | TR24 |
| XSS in the entrance (T) | React text rendering; no raw HTML from API data; CSP and dependency scanning before deployment. | — |

## Database protection and the no-RLS decision

`forkhatri_identity` does not use row-level security, unlike module schemas.
Sign-in, code verification and internal session resolution must look up rows by
identifier or token digest before any member context exists, so RLS would force
a `SECURITY DEFINER` bypass on exactly those queries, recreating the privilege RLS
removes. Protection is instead: an isolated database only this service connects
to (ADR-002); a non-owning runtime role `identity_app` with no `DELETE` on members
and no DDL; `SELECT` only on the registry; and digests rather than secrets at
rest. Module databases keep RLS bound from the resolved `member_id` with
`SET LOCAL` (MODULE-ARCHITECTURE-STANDARD §4, §5b).

## Performance and availability

- Identity & Trust Service availability target 99.9% monthly (ARCHITECTURE.md); RPO ≤5 min, RTO ≤1 h.
- Module bridges cache resolution per token for up to 30 s, so a member costs at most one internal call per module per 30 s.
- The entrance renders its signed-out card without waiting for module data; the hub renders from one registry call and falls back to the cached public registry.
- Moving between hub and module is a full navigation (Multi-Zones); inside a module navigation stays client-side.
- A slow or unavailable module never blocks the hub.

## Accessibility baseline

- Keyboard access for all actions, including the command orb and sheets.
- Visible focus; semantic landmarks and heading order.
- Contrast for text and status labels; no information by colour alone.
- `prefers-reduced-motion` honoured.
- Code input supports platform one-time-code autofill.
