---
step: 08-security-performance
module: MOD02
status: As built (written after the fact)
approver: Security lead / Tech Lead (not yet reviewed)
updated: 2026-11-22
---

# 08 - Security and Performance - MOD02 Milavn

## Document status

- Date: 2026-11-22. Scope: **as built**. This file was missing; the pipeline's Step 8 (STRIDE gate) was never run before implementation (see `AgentOutputs/09a-external-dependencies.md`, SEC-BLOCKER-01, and critique C3 in `docs/Critique/CRITIQUE-mod02-milavn.md`). It is therefore written from the code, the live database and the QA runs, **not** from a prior design gate. Nothing here has been penetration tested by an outside party. Statements marked *unverified* say how to check them.
- Companion files: `07-tech-reqs.md` (requirements), `07a-er-model.md` (RLS policy list in appendix A), `API-REFERENCE.md` (auth per endpoint), `RUNBOOK.md` (operations).

## Contents
1. Trust boundaries and the request path
2. Authentication and session model
3. Roles and permissions matrix
4. Row level security (RLS) design
5. Protected information rules (venue, link, contact, ticket, photos)
6. Threat model (STRIDE by area)
7. Input validation, uploads and media
8. Rate limits, idempotency, abuse controls
9. Secrets and configuration
10. Privacy and DPDP mapping
11. Audit and logging
12. Performance thresholds and known issues
13. Open security findings (honest list)

## 1. Trust boundaries and the request path

```
Browser (milavn-web :3001, Next.js 16)
   |  HTTPS in production; cookie fk_session (set by the ForKhatri entrance :3100 / identity service :8100)
   v
milavn-service :8001 (FastAPI)  --server-to-server-->  identity service :8100 (resolve session -> member id, name, scopes)
   |  one request = one transaction; SET LOCAL milavn.member_id / milavn.permission_scope
   v
PostgreSQL :5433, database forkhatridb, schemas milavn_* , connecting as role milavn_app (non-owner, RLS applies)
```

Other outward calls: shared places adapter (OpenStreetMap Nominatim, server side), MOD06 payment service (only if `PAYMENTS_PROVIDER` is not `none`; default is the local **sandbox**), the browser fetches map tiles directly from the tile host (see finding S-09).

## 2. Authentication and session model

- Sign-in is owned only by the ForKhatri platform (owner rule "auth-single-source-forkhatri"). Milavn renders no sign-in screens. The platform sets the `fk_session` cookie; Milavn resolves it per request through the Identity Bridge (`components/identity_bridge`, `deps.resolve_member_identity`). The same function authenticates HTTP and the `/ws/chat` WebSocket.
- If the identity service cannot answer, the API returns **503 and fails closed**; it never falls back to anonymous or to a default member (TR15.3).
- A legacy development stand-in (`X-Milavn-Member-Id` header or `milavn_member` cookie) works **only when `DEV_IDENTITY_ENABLED=true`**; the default is `false`. It must be false in any shared environment (finding S-03).
- Anonymous requests bind the nil member `00000000-...` so RLS predicates evaluate and only public rows match.
- Cross-site request protection: for POST/PUT/PATCH/DELETE with a valid cookie, the `Origin` header must be in `CORS_ALLOWED_ORIGINS` (or absent for server-side calls); otherwise 403 `origin_not_allowed`. CORS allows credentials only for those origins.
- Tunnel hand-off: `milavn-web/proxy.ts` redeems a single-use `fk_handoff` code with the identity service server to server (active only when `FORKHATRI_IDENTITY_INTERNAL_URL` is set, used by `npm run dev:tunnel`).
- Sessions last 30 days (platform setting, not Milavn). Normal sign-out only; "Sign out on all devices" must not be used on shared dev personas.
- Internal route `GET /internal/v1/insights/members` is guarded by the platform service key (`PLATFORM_SERVICE_KEY`) and hidden from OpenAPI. Payment webhooks arrive at `POST /payments/events` and are authenticated with `PAYMENT_SERVICES_WEBHOOK_KEY` (verified in code: key checked in `payments.py`; signature scheme *unverified* until MOD06 exists).

## 3. Roles and permissions matrix

Roles are not stored as a global table; they are derived per object.

| Role | How a person becomes it | Powers |
|---|---|---|
| Anonymous visitor | no session | public event page `/public/occurrences/{slug}`, host calendar feed, circle invite preview (token), public media only |
| Signed-in member | valid `fk_session` | discover, RSVP, join circles, chat with allowed people, report/block, own profile |
| Confirmed attendee | participation status going / checked_in / attended (a paid ticket makes the spot `going`) | sees exact venue, notes, join link (window), organizer contact (if set to "after booking"), Plan together thread, Moments, activity chat |
| Interested / waitlisted | status interested / waitlisted | sees only the area; no venue, link, contact |
| Organizer (of an occurrence) | `created_by` | edit/cancel, ticket types and codes, agenda, speakers, stalls, announcements, attendee list, money view, check-in, co-organizers |
| Co-organizer | `occurrence_co_organizer` row | same as organizer except granting/revoking co-organizers (verify: `occurrences.py grant_co_organizer`) |
| Circle member / assistant / organizer | `circle_membership.role` (member, assistant, organizer) | members read board and media; assistants moderate posts and let people in; organizer edits, deletes (only without upcoming events), sets roles |
| Moderator | identity scope `milavn.moderate` (Milavn-owned role data) | `/milavn/admin/*` queue, actions: dismiss, warn, escalate, restrict |
| Platform service | service key | internal insights, payment events |

Enforcement is two layers: handler dependency (`CurrentMember`, `OptionalMember`, `Moderator`) and RLS in the database. Where they disagree the database wins.

## 4. Row level security (RLS) design

- Every request opens one transaction and sets **transaction-local** variables: `milavn.member_id`, `milavn.permission_scope`, and for background jobs `milavn.internal_service`. Because `SET LOCAL` dies with the transaction, the transaction boundary is the authorization boundary (`db/session.py`, `deps.get_db_session`).
- The application connects as `milavn_app`, which does **not own** tables, so RLS applies. Owner role `milavn_owner` runs migrations only.
- Live database (2026-11-22): 81 tables, **68 with RLS enabled, 13 without** (list below), 104 policies (policy list per table in `07a-er-model.md` appendix A).
- Tables with RLS **off** (reasons): `activity` (grouping, no personal data), `organization_scope`, `ranking_weight_config`, `trust_status` (derived labels), `circle_formation_suggestion` (writes only through definer functions), all four `outbox_event` and `notification_outbox` (internal queue, never exposed by an endpoint), `participation_status_history` (read only by definer functions), `idempotency_key`, `rate_limit_counter` (infrastructure). Risk: if a future endpoint selects from these directly, nothing in the database stops it. *Verify*: `select tablename from pg_tables where schemaname like 'milavn_%' and not rowsecurity`.
- SECURITY DEFINER functions (the live count is 188 functions in `milavn_*`, most are definer) are used where a member may need an effect on rows RLS hides (organizer-only writes, cross-member reads, jobs, ticket quota under a per-event advisory lock). Each checks the acting member itself and returns an outcome code mapped to 403/404/409, never a 500. A definer function with `search_path` unset is a known risk class; the newer migrations (050-055) pin `SET search_path`. *Unverified* for migrations 001-049; verify with `select proname from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname like 'milavn_%' and prosecdef and proconfig is null`.
- Database-enforced business rules (cannot be bypassed from the API): women-only membership trigger `circle_membership_women_only` (error WO001); capacity and ticket-type quota under advisory lock; one team per person; team size not below existing teams; participation leaving a team on cancel; one open report per reporter per subject (unique index, migration 047); circle delete refused with upcoming events.

## 5. Protected information rules

| Information | Who can read | Where enforced |
|---|---|---|
| Exact venue address, arrival notes, map pin (`occurrence_venue`) | organizer, co-organizers, people with a confirmed spot | RLS on `occurrence_venue`, written only by `set_event_venue()` |
| Online join link | confirmed attendees from `ONLINE_JOIN_OPEN_MINUTES` (15) before start until end; organizers always | RLS + API state `later/open/ended`; tapping Join runs `record_online_join()` (marks checked in) |
| Recording / notes links (`occurrence_followup`) | organizer + confirmed attendees | RLS; link scheme restricted (a `javascript:` link was refused in QA) |
| Organizer phone/email (`occurrence_contact`) | per organizer setting: after confirmed booking, or any signed-in member | RLS + definer read |
| Ticket QR code | the ticket owner; organizer check-in function | RLS on `ticket`; `/checkin/ticket` |
| Circle posts, comments, photos, documents, albums, covers | circle members; invite token holders for covers; moderators looking at a reported post | RLS + gated `/media/*` routes via `circle_media_access` |
| Chat messages and photos | conversation members; DM allowed only if the pair share an activity/circle (`can_message`) | RLS + `can_message` |
| Moments photos | people who were at the activity (`was_there()`), blocked pairs filtered | RLS + gated route |
| Member's woman/man answer (`member_gender`) | only the member | RLS own-row; never in public profile or any other endpoint |
| Location | public screens show only the approximate area chosen by the member's precision (city/zone/locality); stored centre is the area centre, not a person's position; "Use where I am" is one-shot and not stored | FR038/FR041, `public_locality()` |

QA evidence: `QA-RUN-safety-2026-10.md` scenario 21 probed about 30 endpoints as an unbooked member, an "interested" member, a cancelled member and a signed-out caller and found **no leak** of address, notes, link, contact, follow-up, program/teams admin, ticket admin, money, attendees or QR.

## 6. Threat model (STRIDE by area)

S spoofing, T tampering, R repudiation, I information disclosure, D denial of service, E elevation of privilege.

| Area | Threat | Existing control | Gap / status |
|---|---|---|---|
| Session / identity | S: forged member header | header honoured only if `DEV_IDENTITY_ENABLED`; cookie resolved by identity service | must stay off outside dev (S-03) |
| Session | E: cross-site writes | Origin check on unsafe methods | cookie `SameSite` attribute is set by the platform: *unverified* |
| RSVP / waitlist | T: oversubscribing the last seat | per-event advisory lock, capacity check in DB | covered by `test_paid_spots.py` |
| Tickets / payments | T: price tamper, code abuse | price and discount computed server side in a definer function; code limits (max uses, expiry, floor Rs 1); idempotency key | real money path unreviewed against RBI aggregator rules (C1); sandbox only |
| Tickets | S: forged webhook | webhook key | signature verification scheme *unverified* until MOD06 |
| Tickets | I: QR leak | ticket RLS | a QR is a bearer code: whoever shows it checks in; no per-day check-in (S-08) |
| Venue / link | I | RLS (see section 5) | tested, no leak |
| Chat | I/E: unsolicited DMs | `can_message` requires a shared activity or circle; blocks respected | "Interested" alone counts as shared activity (critique H1); interested and waitlisted people can read/write the event chat (QA safety note) |
| Chat WebSocket | S/D | same identity resolution; in-process hub | single-process hub; no per-connection rate limit found: *unverified* |
| Circles | E: women-only bypass | DB trigger on membership requiring self-declared "woman"; invite of an ineligible member sends nothing | it is **self-declared** and cannot be verified; QA found a man can set his answer before joining anything (critique C2); invite of a man returns 201 and fails on acceptance |
| Circles | E: plain member walks someone past "Ask first" | migration 046: only organizer/assistant invites are an approval | covered |
| Uploads | T/I: malicious file | magic-byte sniff (`media_files.sniff_image/sniff_document`), size caps, allow-listed types, random names, private folders | no malware scan; no image re-encoding/EXIF strip found: *unverified* |
| Moderation | R/E | one open report per reporter; moderator scope; actions logged in `moderation_action` | one moderator persona; reporter cannot see status (H6) |
| Notifications | I/D | per-member RLS; de-dup 24 h; grouped circle posts; push at most once an hour per circle per person | older notices stored in the language at send time |
| Public event page | I/D | shows area only, no attendee list; server rendered | rate limiting on anonymous endpoints: none found (S-07) |
| Search / place | D | adapter throttles to 1 request/second and caches | public Nominatim policy forbids autocomplete use (H4) |
| Admin console | E | `Moderator` dependency + RLS scope | verified by `test_admin_queue_grouping.py` only for grouping |

## 7. Input validation, uploads and media

- Request bodies use Pydantic models with length and range limits (for example venue address 400 chars, ticket type name 1-60, price Rs 1 to Rs 100,000 per ticket type check, pledge minimum Rs 100). Database CHECK constraints repeat the key limits (see appendix A constraints).
- Raw validation lists leak to users in some places (quota 0, pledge below Rs 100): `QA-RUN-professional`, `QA-RUN-community`. Known cosmetic issue.
- Uploads: photos (jpeg/png/webp by magic bytes), `MAX_PHOTO_BYTES` 10 MB, covers 5 MB, documents 10 MB by constant and `CIRCLE_FILE_MAX_MB` 15 by setting (the two numbers disagree: confirm which wins, finding S-10), post limits 10 photos and 5 files, albums 20 photos per upload, document types pdf/doc/docx/xls/xlsx/ppt/pptx/txt. A fake `.jpg` was refused with 415 in QA.
- Media storage is the local folder `milavn-service/.local-media/`. Private folders (circle-posts, circle-docs, circle-albums, circle-covers, chat, moments) are not served by the static mount; they are answered by routes that ask the database. Direct URL guesses, upper-case and `..` paths returned 404 in QA.
- External links entered by organizers (join link, recording) are validated: scheme must be http(s). Provider is detected and labelled (Meet, Zoom, Teams, YouTube).

## 8. Rate limits, idempotency, abuse controls

Rate limits are database counters (`milavn_platform.rate_limit_counter`) with scopes REPORT_SUBMIT, OCCURRENCE_CREATE, PARTICIPATION_TOGGLE, CIRCLE_CREATE, MESSAGE_POST, PHOTO_UPLOAD. Configured values: reports 10 per 3600 s, event creates 20 per 3600 s, RSVP toggles 60 per 600 s. Message/photo/circle-create limits use defaults in code (values *unverified*, read `rate_limiting/__init__.py`). Exceeding returns 429.
Idempotency: `Idempotency-Key` on mutations, stored 7 days (`IDEMPOTENCY_KEY_TTL_DAYS`); a replay with a different body returns 409.
Other controls: block list (both directions respected in chat, Moments, suggestions); identical organizer update within one hour refused (409); one report per reporter per subject.

## 9. Secrets and configuration

Environment names (values never recorded here) are listed in `07-tech-reqs.md` section "Configuration reference". Secrets: `DB_APP_PASSWORD`, `PLATFORM_SERVICE_KEY`, `PAYMENT_SERVICES_KEY`, `PAYMENT_SERVICES_WEBHOOK_KEY`, `MAP_TILE_API_KEY`, `GEOCODING_API_KEY`. Defaults in `settings.py` are dev placeholders (`CHANGE_ME`, `REPLACE_ME_*`, a dev DB password). The service must refuse to start in production with a placeholder: **not implemented** (S-04). `.env` files are git-ignored (commit d8371f8 added the ignore rules).

## 10. Privacy and DPDP mapping

| Data | Purpose | Stored where | Retention | Deletion / export |
|---|---|---|---|---|
| Profile (name via platform, place area, language, bio, photo, interests) | discovery, trust | `member_profile`, `member_interest`, `member_profile_media` | while account exists | delete-account screen exists (FR088); **purge built 2026-11-22 (migration 056, FR161-FR166; section 14)**; **export: not built** |
| Woman/man answer | women-only circles only | `member_gender` | account life | same as above |
| Participation, check-in, attendance history | RSVP, reputation, reminders | `participation`, `participation_status_history` | unlimited today | no retention rule written |
| Photos of identifiable people (Moments, albums, chat) | memories | files in `.local-media` | unlimited | photo-removal "Remove photo of me" exists for Moments; children/minors rule not built (H5) |
| Chat messages | messaging | `chat_message` | unlimited | no export |
| Reports and moderation actions | safety | `report`, `moderation_action` | unlimited | internal |
| Location | approximate area only | profile/occurrence lat-lng of area centre | account life | precision level chosen by member |
| Payment records | tickets | `ticket`, `payment_event` | unlimited | finance retention rule needs CA advice |

Gaps to close before launch (from critique H5): written retention schedule, data-export, grievance officer contact, breach plan, under-18 handling, consent text review. All marked **needs lawyer**.

## 11. Audit and logging

- Application logs via Python `logging` to stdout (service start, reminders sent, circle suggestions created, payment holds expired, failed scheduled jobs). No structured JSON, no correlation id: *unverified, none found*.
- Database audit: `participation_status_history`, `moderation_action`, `payment_event`, outbox tables, `reputation_signal`. There is no general admin-action audit log for organizer edits.
- No log shipping, alerting or dashboards exist (Step 13 monitoring was never run).

## 12. Performance thresholds and known issues

No load test has been run. Figures below are **design targets taken from `07-tech-reqs.md`** unless marked measured.

| Item | Target | Status |
|---|---|---|
| Around You API p95 | under 500 ms | not measured |
| Event page first contentful paint on 4G | under 2.5 s | not measured |
| DB pool | `DB_POOL_MAX_CONNECTIONS` 20 | configured |
| Place search | 1 request/second to upstream, cached | implemented in the shared adapter |
| Background jobs | reminders every 10 min, circle suggestions hourly, hold expiry every minute, all in-process | single instance only (two instances would run every job twice) |
| WebSocket chat | in-process hub | single instance only |
| Ranking | in-memory score over the viewer's city, next 21 days | fine at seed scale (38 events); *unverified* at thousands |

Known performance risks: Home loads digest + around-you + circles (three calls); the map pulls tiles from a public tile server (no SLA); definer functions that scan `participation` per row (for example per-viewer counts) have no load evidence; the first request after an API restart showed untranslated server strings (QA professional note).

## 13. Open security findings (honest list)

| ID | Severity | Finding | Source | Suggested action | Owner |
|---|---|---|---|---|---|
| S-01 | Critical | Paid events rest on a payment path that may not satisfy RBI 2025 aggregator rules; money, KYC, GST, host payouts undecided; sandbox only | critique C1 | decide legal shape (licensed partner, Samaj entity, or UPI direct) before real money | owner + lawyer/CA |
| S-02 | Critical | Women-only is self-declared and described as "enforced"; man can answer "woman"; invite accepted then fails; misuse report has no status route | critique C2, QA safety 23 | change wording; steward approval; refuse at invite time | product |
| S-03 | High | Dev identity stand-in exists behind a flag | code | assert flag false at startup when env is not dev | engineering |
| S-04 | High | Placeholder secrets accepted at startup | settings.py | fail fast outside dev | engineering |
| S-05 | High | STRIDE gate never run before money, uploads, WebSocket and QR shipped | critique C3 | run this document's threat table through a real review; add tests | security |
| S-06 | High | Anyone who taps "Interested" can message every other attendee and read the event chat | critique H1, QA safety | first contact as a request; Interested does not unlock chat | product + engineering |
| S-07 | Medium | No rate limit on anonymous public endpoints | code review | add per-IP limits at the edge | ops |
| S-08 | Medium | Ticket QR is a bearer code; single check-in per ticket (no per-day count); organizer can scan before the event | QA professional | per-day check-in; time check | engineering |
| S-09 | Medium | Browser fetches map tiles from a public tile host (leaks viewer IP and area); QR image earlier used a third-party site (now on-device) | critique C3 | self-host or commercial tiles | ops |
| S-10 | Low | Upload size constants and settings disagree (doc 10 MB constant vs 15 MB setting) | code | single source | engineering |
| S-11 | High | Public Nominatim use with search-as-you-type breaks the OSM usage policy | critique H4 | self-host Photon/Nominatim or commercial provider | ops |
| S-12 | High (superseded 2026-11-22: 055 recorded as applied; GRANT not re-verified) | Migration 055's `GRANT DELETE` on `notification_inbox_entry` is **not applied** in the dev database (verified 2026-11-22: privileges are INSERT, SELECT, UPDATE); dismissing a notification returns 500 | live DB vs file | owner role runs the GRANT; add a migration-tracking table | DB owner |
| S-13 | Medium | No migration ledger table: applied state of 001-055 can only be inferred | live DB | add `schema_migrations` | engineering |
| S-14 | Medium | Test (QA) rows remain visible in dev data and could be visible to real members on a shared tunnel | critique M7 | clean demo tenant; owner-run cleanup | owner |
| S-15 | Medium | DPDP: no retention schedule, export, under-18 rule, grievance contact | critique H5 | lawyer-led | owner |
| S-16 | Low | Moderator capacity: one persona, no response-time promise | critique H6 | named safety lead | owner |



## 14. Account deletion (added 2026-11-22)
- DPDP mapping: erasure met by immediate deletion (kind A via the hub, kind B in Milavn). Kept only where law or safety requires: payment records (tax), reports, blocks and moderation (safety), deletion receipt. Retained rows hold a one-way tombstone id, no name, contact, photo or free text. Retention periods need a lawyer or CA (open, with S-15).
- Re-authentication: kind A at the hub (password or one-time code, typed DELETE). Kind B: typed DELETE plus the existing ForKhatri session only; a stolen live session could erase a member's Milavn data (new finding S-17, Medium).
- Rate limit: 3 per hour per member (kind B). The internal route needs the service key (401 without; 404 on the public edge; hidden from OpenAPI).
- Safety: the function acts only for the calling member or the internal service; SECURITY DEFINER, no RLS loosened; a refund failure rolls back everything.
- Risks and open findings: a removed person can re-enter as a new member (only the report record remains; the hub does not block sign-up, a ban is only a flag in the receipt); orphan files after a crash between commit and removal; refund-pending paid ticket retained; no audit of who asked beyond the receipt; the hub identity suite had 1 governance test failing (not confirmed unrelated).
