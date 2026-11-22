---
project: ForKhatri
artifact: Parent Application Security and Performance
step: 8
status: As built (2026-11-22); 2026-09-14 history retained
updated: 2026-11-22
---

# Parent Application Security and Performance

> **Document status 2026-11-22, as built.** Original 2026-09-14 content is kept as history; the "As-built update" section at the end is current and wins where they differ. See API-REFERENCE.md, 07a-er-model.md and 07-tech-reqs.md.


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

---

# As-built update (2026-11-22)

Revision row: 2026-11-22, "Security and performance restated as built: session and cookie model, roles and permissions matrix, STRIDE per area, DPDP mapping, rate limits, secrets by name, open findings from the October 2026 critiques", reason: owner request that documents match the application as built. The 2026-09-14 threat table above remains valid; this section adds what was built since (governance console, handoff, provisioning, insights) and records the open findings honestly. Sources: code under `platform/identity-service/app`, [API-REFERENCE.md](API-REFERENCE.md), [07a-er-model.md](07a-er-model.md), `docs/Critique/CRITIQUE-platform.md`, `CRITIQUE-lens-privacy-law-safety.md`, `CRITIQUE-lens-architecture-security-delivery.md`, `RESEARCH-platform-auth-dpdp-2026-10.md`, and owner decisions in memory (`auth-single-source-forkhatri`, `platform-basic-identity-module-profiles`).

## C1. Owner decisions that shape security

| Date | Decision | Effect |
|---|---|---|
| 2026-09-14 | The platform member holds basic identity only; profile data lives in modules | `identity.member` has no profile fields; privacy of sensitive data is a module problem under module RLS |
| 2026 (auth-single-source) | Login and authentication are owned only by the platform; no module builds its own | One cookie, one resolve contract; module sign-in routes redirect to the entrance |
| 2026-09-21 | A member provisioned for someone who never used it is removed after six months | Internal `retire-provisioned` (currently blocked by missing DELETE grant) |
| 2026-09-27 | The members dashboard is open to every signed-in member | `GET /v1/insights` has no role check; small-cell risk accepted for totals, open for small cells |
| 2026-09-30 | Telugu and Hindi strings must be accurate and respectful | Error codes localised by the web; admin console Hindi needs review |
| 2026-10-02 | Samaj heads run ForKhatri; Welfare Trust inside Finance | Admin console roles are samaj office bearers with terms |

## C2. Session and cookie model

1. Sign-in produces a 256-bit CSPRNG token (`secrets.token_urlsafe(32)`). Only its SHA-256 digest is stored (`identity.session.token_hash`); the token travels only in the cookie.
2. Cookie: name `SESSION_COOKIE_NAME` (`fk_session` development, `__Host-fk_session` production), `HttpOnly`, `Path=/`, `Secure` when configured (required in production), `SameSite` default Lax (`none` refused in production), no `Domain` unless explicitly set (refused in production), `Max-Age` 30 days.
3. A session is valid only if not revoked, not expired and the member status is `active`. Suspension, ban and sign-out everywhere revoke sessions; the member status check alone also stops every module at the next resolve.
4. Modules resolve via the internal API with a per-token cache of at most 30 s (negative 5 s). Residual revocation window is therefore about 30 s.
5. No idle timeout and no step-up authentication; `last_seen_at` is updated at most every 5 minutes. No device list, no new-sign-in alert (CRITIQUE-platform C8, architecture M4).
6. Hand-off for hosts that cannot share the cookie: single-use 60 s code held in process memory; the session token never appears in a URL.
7. Dev sessions (`auth_method='dev'`) exist only while the dev router is mounted.

## C3. Roles and permissions matrix

Roles are code (`app/components/governance/roles.py`), assigned in `governance.role_assignment` over a scope and a term. Nobody has administrative power by default. Sensitive roles need a second person to grant unless an owner grants them. Permissions: `members.view`, `members.contact`, `members.suspend`, `members.ban` (propose), `roles.view`, `roles.manage`, `approvals.decide`, `org.view`, `org.manage`, `chapter.manage`, `audit.view`, `modules.manage`. Module actions: `moderate`, `verify`, `commercial` (module's own chokepoint still decides).

| Role (scope) | Sensitive | Platform permissions | Module actions |
|---|---|---|---|
| owner (platform) | yes | all 12 | moderate, verify, commercial |
| president (platform) | yes | members.view, members.suspend, members.ban, roles.view, roles.manage, approvals.decide, org.view, org.manage, audit.view | moderate |
| secretary (platform) | yes | same as president | moderate |
| treasurer (platform) | yes | members.view, org.view, audit.view | commercial |
| grievance_officer (platform) | yes | members.view, members.contact, members.suspend, members.ban, approvals.decide, org.view, audit.view | moderate |
| data_protection_officer (platform) | yes | members.view, members.contact, audit.view | none |
| auditor (platform) | no | members.view, roles.view, org.view, audit.view | none |
| chapter_head (chapter) | no | org.view, roles.view, chapter.manage | none |
| chapter_secretary (chapter) | no | org.view, roles.view | none |
| moderator (module) | no | members.view | moderate |
| verifier (module) | no | none | verify |

Rules enforced in code: nobody acts on themselves (`admin_self_action`); an owner can only be changed by first removing the owner role; staff accounts need someone who manages roles (`admin_target_staff`); only an owner appoints or removes an owner; the last owner cannot be removed (`last_owner`); a ban needs a second person (`approval_four_eyes`); contact reveal needs a reason and is audited with IP. Reason codes: harassment, fraud_scam, fake_profile, impersonation, inappropriate_content, underage, spam, safety_threat, legal_order, member_request, other. Suspension lengths: 1, 3, 7, 30 days or open. Ordinary members: own session, own profile (`PATCH /v1/me`), module list and entry, insights totals.

Endpoint-by-endpoint permission: API-REFERENCE section 4.

## C4. Threat model (STRIDE) by area, as built

| Area | S spoofing | T tampering | R repudiation | I information disclosure | D denial of service | E elevation |
|---|---|---|---|---|---|---|
| Sign-in (code, password) | Code HMAC with pepper, 5 attempts, 5 min; Argon2id with dummy verify | Origin guard plus SameSite | Sessions record method and user-agent | Same 202 for known and unknown identifiers; masked hints | DB rate limits per IP and identifier; resend interval | Pre-hijack of provisioned numbers (open: C4 critique) |
| Session and cookie | Opaque token, digest at rest, `__Host-` | HttpOnly, Secure | `last_seen_at`; no device list (open) | Token never in body or URL | Resolve is one indexed read | Shared phones keep sessions (open) |
| Hand-off | 32-byte single-use code, 60 s | n/a | none logged (open) | Token not in URL | in-memory dict, no limit (low) | Process-memory only |
| Internal API | Service key, constant-time compare, edge block, `X-Forwarded-For` 404 | n/a | Calling service not logged (open) | Identifiers only to listed services | No rate limit (private network) | A leaked key can provision and read claims |
| Admin console | Same weak factors as members (open H6) | Two-person rule, constraints | Append-only audit with trigger | Contact masked; reveal audited | None (no limits on admin) | Roles in code; four-eyes; owner can act alone |
| Registry and hub | n/a | Only `availability` updatable by `identity_app`, audited | Audit `module.availability_changed` | Registry is public data | n/a | `modules.manage` only |
| Insights | n/a | n/a | n/a | Aggregates open to all members; small cells identify (open C9) | Calls modules with 5 s timeouts | n/a |
| Dev tools | Refused in production; token for test mode; owner persona refused in test mode | n/a | `auth_method='dev'` | Personas list is unauthenticated in development (open C1) | n/a | Passwordless impersonation if mounted on a reachable host |
| Federation gateway | Forwards the admin's own session token | Path parameters validated | Audit `queue.action` | Only views the admin is scoped to | 8 s timeout, 502 on failure | Module decides again |

## C5. Input validation and uploads

Pydantic validates every body (lengths, patterns, `extra="forbid"` on member and admin bodies); `422 validation_failed` lists field names. Identifier normalisation: 10-digit Indian mobile to `+91`, `+`E.164 regex `^\+[1-9][0-9]{7,14}$`, email trimmed and lower-cased with `email-validator`; international numbers are accepted. SQL uses bound parameters; the one dynamic column name in `provision` and `welcome` comes from code, and the language column from a fixed whitelist. The identity service has no file uploads.

## C6. Rate limits

See API-REFERENCE section 8. Gaps: no limits on handoff redeem, admin and internal endpoints; per-IP bucket can lock out shared carrier addresses (CRITIQUE-platform C15); whether the real client IP reaches the service depends on `FORWARDED_ALLOW_IPS`.

## C7. Secrets (names only)

Held outside source in `.env` and `deploy/secrets/.env.production` (git-ignored, mode 600), generated by `deploy/scripts/generate-secrets.sh`: OTP_PEPPER, SERVICE_KEYS (per service: MANGALY_SERVICE_KEY, MILAVN_SERVICE_KEY in deployment), DB_APP_PASSWORD, POSTGRES_PASSWORD, IDENTITY_OWNER_PASSWORD, IDENTITY_APP_PASSWORD, module database passwords, RESEND_API_KEY, DEV_TOOLS_TOKEN, CLOUDFLARE_TUNNEL_TOKEN, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY. Development placeholders exist in `settings.py` (names contain `CHANGE_ME`) and in `db/000-bootstrap.sql`; the production guard rejects placeholders for the pepper and service keys but does not inspect database passwords (verify the deploy sets real ones; the generator does).

## C8. Privacy and DPDP mapping

Fiduciary: not named anywhere in the documents (owner and a lawyer must decide: Samaj body, company or founder). DPDP Act 2023 and Rules 2025: Board rules live; Consent Manager Rule 4 about 13 Nov 2026; notice, security, breach, erasure, rights and children's rules about 13 May 2027 (a shortening to 12 months was floated; treat as pending). Needs lawyer.

| Data | Where | Why | Retention today | Deletion or export | DPDP note |
|---|---|---|---|---|---|
| Display name, language, level, status | `identity.member` | Identify the member | Forever | Not built | Rights of access, correction, erasure |
| Phone, email (PII) | `identity.member` | Sign-in channel | Forever | Not built | Shared in full only with identifier-trusted services and audited admin reveal |
| Password hash | `password_credential` | Optional sign-in | Forever | Not built | No set or reset API |
| Code HMAC, identifier | `otp_challenge` | Sign-in | No purge | n/a | Identifier stored in clear; add purge |
| Session digest, user-agent | `session` | Sign-in state | No purge | Revoked on sign-out | Device data |
| Rate-limit buckets (contain identifier or IP) | `rate_limit_counter` | Abuse control | 1 day opportunistic | n/a | IP and identifier in the key |
| Module entries | `member_module_entry` | Hub ordering | Forever | Cascades only if a member row is deleted | Reveals which modules a person visits (C5 critique) |
| Governance and audit, including IP | `governance.*` | Accountability | Never deleted; no period set | Not erasable by design | Rule 8 needs logs for at least one year; set a period with a lawyer |
| Pre-provisioned third-party number | `identity.member` level 0 | A parent created a child's profile | Six-month rule not working (finding) | Retire endpoint blocked | s.6 consent angle: data supplied by a third party (research) |

Not built (open, ranked in CRITIQUE-platform): consent notice and age question at sign-up, terms and privacy links, grievance and appeal screen, account deletion with module fan-out, data export, identifier change, breach procedure (Rule 7: notify without delay, report within 72 hours), processor agreements for Resend, Cloudflare and hosting, pairwise per-module identifiers, and the Consent Manager-ready consent record.

## C9. Audit logging

Every console mutation and contact reveal writes `governance.audit_event` (actor, target, action, module, subject, reason code, note, details, IP, time) in the same transaction. Append-only by trigger and grants. Not audited: sign-ins, failed logins, internal calls, member self-edits, insights reads. Filters: actor, target, action prefix, module, cursor.

## C10. Performance thresholds and known issues

Targets: availability 99.9% monthly, RPO <= 5 min, RTO <= 1 h. Reality per critique: one VM, nightly dump, optional off-server copy, no standby, Cloudflare Tunnel without SLA; so the targets are not yet met (architecture C3, CRITIQUE-platform C11). Authentication performance: Argon2id verification cost is deliberate (about tens of ms); unknown identifiers pay the same cost. Resolve is one join on an indexed unique digest plus an optional `last_seen_at` update every 5 minutes. Insights fans out to modules in parallel with 5 s timeouts; admin gateway 8 s. Known: Mangalya Home made six identical session checks on load in the dev build (M5); no real-device or load testing; `next dev` measurements only.

## C11. Open findings register (honest, 2026-11-22)

Status key: open = no fix found in code at this date; verified = read in code; unverified = not executed.

| ID | Finding | Source | Status |
|---|---|---|---|
| SEC-01 | Dev tools, `DEV_EXPOSE_OTP=true` and placeholder keys default on; fail-open unless `ENVIRONMENT=production` is set; personas list reachable unauthenticated and was reachable through the tunnel proxy | architecture C1 | open (guard exists in code, defaults not inverted; verified in settings) |
| SEC-02 | Phone members cannot sign in in production (SMS disabled) and no password set or reset API exists | platform C1 | open (verified) |
| SEC-03 | No change of number or email, no second identifier, two members from one person possible, no recovery | platform C2 | open (verified) |
| SEC-04 | No account deletion, export or consent; fiduciary not named | platform C3, privacy C1 | open (verified) |
| SEC-05 | Provisioned level-0 members never reach level 1; pre-hijack and consent risk | platform C4 | open (verified) |
| SEC-06 | `retire-provisioned` needs DELETE on `identity.member` which `identity_app` lacks | this review | open (grant verified live; call not executed) |
| SEC-07 | One id and real name across modules; `members/lookup` names for 200 ids; hub shows visited modules | platform C5 | open |
| SEC-08 | Suspension is platform-wide with no appeal screen; single person can impose up to 30 days | platform C6 | open |
| SEC-09 | Sessions: 30-day absolute, no idle timeout, no device list, no step-up for admin, contact reveal or payments | platform C8, architecture M4, H6 | open |
| SEC-10 | Admin accounts have the same factors as members; owner can act alone; audit trigger removable by owner role | platform C12, architecture H6 | open |
| SEC-11 | Insights small cells re-identify; matrimonial fields shown outside Mangalya | platform C9 | open |
| SEC-12 | No CSP, frame-ancestors or clickjacking headers | architecture M1 | open |
| SEC-13 | Handoff codes in process memory, no rate limit | this review | open (verified) |
| SEC-14 | No retention or purge for otp_challenge, session, audit | this review | open (verified) |
| SEC-15 | Only identity, Mangalya and Milavn check Origin; Vyapar and Counsel rely on SameSite | architecture M4 | open |
| SEC-16 | Per-IP rate limit and shared carrier addresses; IP trust depends on `FORWARDED_ALLOW_IPS` | platform C15 | open, unverified |
| SEC-17 | Deploy kit holds 2 of the modules; backups and recovery objectives not met | architecture C2, C3 | open |
| SEC-18 | Critical Next.js advisory, no dependency watch, few automated tests | architecture H1, H2 | open (re-check versions) |
| SEC-19 | Hindi in admin console mixed scripts; "Owner" Hindi term reads religious | platform C13 | open |

## C12. Privacy and architecture lens summary

Privacy lens (CRITIQUE-lens-privacy-law-safety): minimise by keeping the platform thin (done), hold sensitive data in modules under RLS (done in modules), add consent, notice, rights and breach handling (not done). Architecture lens: the platform design (isolated database, non-owning role, digests, strong production guard, four-eyes) is sound and should not change; the risks are defaults that fail open, no automated RLS proof, one-VM operations, and copied cross-cutting code. Keep list from the critique ("Do not change"): opaque HttpOnly cookie with digest storage, anti-enumeration, database rate limits, Origin and `return_to` allow-lists, basic identity only, admin console design, honest empty states, dev tools refused in production.


## C13. Account deletion: privacy and security (added 2026-11-22)

DPDP erasure mapping: the right to erasure is met by kind A (everything, everywhere) and kind B (one module), immediately, with the member told what stays and why. This supersedes the "erasure not built" findings in C8 and C11.

- Retained, no name, contact or free text: payment and tax records where money moved; safety and moderation records (tombstone only); security log and audit rows (tombstone only); the deletion receipt. Every legal basis is marked "needs lawyer" (see `docs/DATA-RIGHTS.md`). Retention period for the audit log is still not decided.
- Tombstones: HMAC-SHA256 with `DELETION_TOMBSTONE_PEPPER`; the pepper must be a long secret kept stable, otherwise a returning member's tombstone cannot be matched.
- Rate limit: 3 attempts per hour per member, every attempt counts. Re-authentication by password or fresh code to the member's own identifier; typed DELETE.
- Auth between services: service key plus service name; internal endpoints refuse requests that came through the edge.
- Receipt endpoint is public by job id (unguessable id as the capability); it holds no name or contact.

Risks and open findings:
- SEC-20: a banned member is only flagged in the receipt; sign-up is not blocked (owner decision).
- SEC-21: Counsel unpaid earnings are lost on deletion; payout-retention path untested.
- SEC-22: Vyapar erase returned 500 once for a member it had never seen (to be fixed or confirmed).
- SEC-23: one identity governance test fails; not confirmed unrelated.
- SEC-24: no browser check of any deletion screen; Vyapar `check_taste.py` 27 of 35 (not compared to before).
- SEC-25: grievance officer, consent notice and age gate are not built.
