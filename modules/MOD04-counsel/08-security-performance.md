# MOD04 Counsel — 08 Security and performance

**Document status:** 2026-11-22, "as built". Evidence: code, schema, `docs/Critique/CRITIQUE-mod04-counsel.md`, `MASTER-CRITIQUE-2026-10.md`. No penetration test was run.

## Contents
1 Auth and session · 2 Roles and permissions · 3 Authorisation design (no RLS) · 4 Threat model (STRIDE) · 5 Input validation and uploads · 6 Rate limits · 7 Secrets · 8 Privacy and DPDP mapping · 9 Audit logging · 10 Performance · 11 Open findings

## 1. Auth and session
Counsel stores no credentials. The browser holds the platform's HttpOnly `fk_session` cookie; the API resolves it by `POST {identity}/internal/v1/sessions/resolve` with service headers `X-ForKhatri-Service` and `X-ForKhatri-Service-Key`; result cached by SHA-256 of the token (30 s positive, 5 s negative). Identity down -> 503 `identity_unavailable`. WebSocket: single-use 60 s ticket (from `POST /me/ws-ticket`) or the cookie. CORS allows credentials only for `CORS_ALLOWED_ORIGINS`. Internal routes accept only service name `identity` plus constant-time key comparison.

## 2. Roles and permissions
| Capability | Visitor | Member | Seeker on a booking | Consultant on a booking | Admin |
|---|---|---|---|---|---|
| Browse, search, profile, slots, service | yes | yes | | | yes |
| `/understand`, `/home` | yes | yes | | | yes |
| Book, ask question, buy follow-up | | yes (not own service, not blocked) | | | |
| Pay, cancel, message, room, notes, files | | | yes | yes | no (admin has no special booking access) |
| Review | | | seeker of a completed booking | | |
| Complete, dispute | | | yes | yes | |
| No-show claim | | | yes | yes | |
| Consultant profile, services, availability, earnings | | yes (own) | | | |
| Approve providers, verify, decide disputes/reports, settings, audit | | | | | yes |
| View private proof documents | | owner | | | yes (audited) |
Admin = platform scope `counsel.admin` or member id in `ADMIN_MEMBER_IDS` (dev list includes the Milavn moderator account; T7: replace by governance grant).

## 3. Authorisation design
Handler-level checks (`participant()`, owner filters `provider_id = actor`, `_own_request`). The DB role is non-owning (cannot alter schema) but has full DML. **No row-level security** on any of the 40 tables, so a coding mistake in a handler is not backstopped (G-11). Download endpoints re-check participation (the UI is never the control).

## 4. Threat model (STRIDE, condensed)
| Area | S | T | R | I | D | E |
|---|---|---|---|---|---|---|
| Auth/session | token theft: HttpOnly cookie, identity-owned | n/a | audit of key actions | cache 30 s means revoked session may live 30 s | identity outage = 503 | admin via env id list in dev |
| Booking/money | impersonation prevented by participant checks | price snapshot prevents tampering; client sends only service, time, brief | `audit_log`, ledger | amounts visible to participants only | slot hoarding limited by 15-min pending expiry; **no rate limit on creating bookings** | consultant cancel/no-show claims; **G-03** payout without attendance |
| Payments | mock refused off-loopback; event signature verified | **G-04** non-idempotent refund/payout keys | payment, ledger | n/a | gateway call inside DB transaction | n/a |
| Files | type allow-list + magic bytes + scan hook | AES-GCM integrity tag | audit uploads/downloads/proof views | encrypted at rest; per-participant access | size caps 25 MB (500 MB recordings); **no per-user quota** | path traversal guarded |
| Room/WebSocket | ticket single-use, participant-only | relay limited to fixed message types to the other party only | session events | media peer to peer; signalling content is not stored | in-memory hub, no limits on message rate | n/a |
| Discovery/AI | n/a | prompt injection into `/understand` only changes filters | n/a | text sent to Anthropic when enabled (private notes only for recap summary, **consent not asked**, C10) | **`/understand` unauthenticated, unlimited** (G-13) | n/a |
| Admin | admin gating on router | settings whitelist of 6 keys | audit on decisions; **report decisions and area upserts are not audited** | admin sees all names | n/a | n/a |

## 5. Input validation and uploads
pydantic limits (lengths, ranges listed in API-REFERENCE and 02). Photo: jpeg/png/webp, 5 MB, magic bytes. Evidence proof: image/pdf, 10 MB, magic bytes. Consultation files: MIME regexp allow-list (images, pdf, text, csv, office, zip, json), size by `MAX_UPLOAD_MB`; **MIME is the client-declared header, no magic check on these** (verified in `room.py`). Recording: webm/mp4 only, 500 MB. Malware scan off by default (T2). Filenames sanitised to basename. `target_id` in reports is free text.

## 6. Rate limits
None in the service (no middleware). Business limits exist: 3 pending time requests per consultant, 2 open questions per consultant, one open dispute per booking, 6 call-issue chips.

## 7. Secrets handling
`.env` files hold DB, service key, webhook, encryption keys and AI key (CHANGE_ME placeholders in the example); service refuses to start off-loopback with placeholder encryption keys; development derives keys from the service key (never for production). Payout secrets Fernet-encrypted, shown only as last 4. The repository `.gitignore` excludes keys (commit d8371f8) — `.env` files exist in the working tree and must not be committed (unverified they are untracked).

## 8. Privacy and DPDP mapping
| Data | Why | Retention | Export | Delete |
|---|---|---|---|---|
| Name cache (`member`) | display | until erased (becomes "Deleted member") | no (platform) | yes |
| Provider profile, evidence, proofs | marketplace and trust | until erasure | yes (proof files not exported, only metadata) | yes |
| Bookings, briefs, messages, notes | service delivery | bookings kept for tax; brief and messages blanked on erasure | yes | partial by design |
| Files, recordings | delivery | 365 d / 90 d | listed not included (file names only in messages) | yes |
| Payout method | payouts | until erasure | masked | yes |
| Ledger, payments, audit | tax/dispute law | kept (no name) | partial | no |
| Search/profile counters | analytics | indefinite | no | yes (provider) |
Status (updated 2026-11-22: identity now calls Counsel erase; the Delete column above is superseded by section 12): Counsel export and delete work; consent notice is absent (T1, master critique 2). Notices of consent for AI summarisation of notes: not built. DPDP phase dates: *unverified*. Needs lawyer.

## 9. Audit logging
`audit_log` records: provider created/submitted/decisions, verification granted/revoked, evidence decisions and document uploaded/viewed, service created and price changes, booking created/cancelled/completed/no-show, payment succeeded, dispute opened/decided, payout paid, payout method changed, recording consented/saved, file uploaded/accessed, time request accepted, question answered, package refunded, settings changed, privacy exported/erased, retention removal, expertise request decided. Not audited: report decisions, area upserts, notes, messages, refund inside cancel is within the cancel record.

## 10. Performance
No thresholds defined. Known: N+1 card building in search; dashboard rank runs a 500-result search; housekeeping loops over all approved providers every 10 min; room hub in memory; all fine at pilot scale (tens of consultants). Poll interval 8 s for booking chat. No caching of search. To verify: run `EXPLAIN` on search under 1,000 providers.

## 11. Open findings (from critiques and this audit)
C1-C3 regulated-profession exposure; C4 pay without attendance; C5 payments idempotency, async payouts, outbox, reconciliation; C6 fee below cost; C7 no TURN; C9 reminders; C10 reviewer names and AI consent; C11 badge wording; C13 tax and RBI; no RLS; no rate limits; `/understand` open; Next.js 16.3.5 advisory (published 2026-09-22, likely unaffected, master critique 11); no frame-blocking or CSP headers.

## 12. Account deletion: privacy and security (added 2026-11-22)
**DPDP mapping.** Right to erasure met by immediate erase (no waiting period). Retained and why: consultations (other person's record; stand-in id, brief blanked); payments, ledger, payouts where money moved (tax and dispute law); star ratings without text; reports, disputes, audit trail (safety and security; names replaced by the stand-in id, detail cleared); one receipt. Each retained item is shown to the member in plain words. Lawyer confirmation needed; DPDP dates unverified.
**Controls.** Internal erase needs the service key and `X-ForKhatri-Service: identity`; member route needs the session (kind A re-authentication is done by the hub; kind B relies on session plus typed DELETE); 3 attempts per hour per member (the first rate limit in Counsel); idempotent; one transaction, no privilege widened.
**Tombstone.** One-way sha256 of member id plus service key. Anyone holding the service key could test a known member id against stored stand-ins.
**Risks and open findings.**
1. Unpaid eligible earnings are lost on deletion: OWNER DECISION NEEDED (see 01 section 13); payout-retention path untested.
2. Fee model G-01 unresolved; refunds on deletion follow the snapshot.
3. Erase for a never-seen member: unverified in Counsel.
4. Orphan files if the process dies between commit and file removal: unverified.
5. No automated tests (G-10): manual script only; browser UI not checked.
6. Kind B has no step-up re-authentication inside the module (the contract allows it; owner may want more).
