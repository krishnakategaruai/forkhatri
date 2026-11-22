# MOD04 Counsel — 06 Impact analysis

**Document status:** 2026-11-22, "as built". Read this before changing a feature: what depends on it and what breaks.

## Contents
1 External dependencies · 2 Internal dependency map · 3 Change-risk table · 4 Cross-module notes

## 1. External dependencies
| Dependency | Used for | If it changes or is down |
|---|---|---|
| Identity service :8100 | every authenticated call, names | 503 `identity_unavailable` for members; public pages still work except names are cache-only; cached sessions live up to 30 s |
| Hub :3100 | sign-in redirect, account link, "act as" | users cannot sign in; Counsel unaffected otherwise |
| shared/forkhatri-integrations | payments, messaging, delivery | non-mock payment path fails; any change to `ChargeRequest`, `RefundRequest`, `PayoutRequest`, `get_gateway`, `Dispatcher`, `get_sender` breaks `money.py` and `outbound.py` |
| Postgres + btree_gist | all data, no double booking | outage = full outage; removing the extension breaks migration 001 |
| Disk `STORAGE_ROOT` | photos, proofs, files | lost disk = lost proofs and recordings (no backup defined) |
| Anthropic API | optional match and recap | falls back to rules, silently |
| ClamAV | optional scan | if enabled and down, all uploads refused |
| Browser WebRTC/MediaRecorder/getDisplayMedia | room | unsupported browser = no call; chat/notes still work |

## 2. Internal dependency map
- Booking depends on: service, availability engine, quote (settings), blocks, payment adapter, notifications, audit. Changing slot rules affects booking creation, time-request accept, package session booking, `is_free`, next-slot on cards, "soonest" sort and profile strength `slot_soon`.
- Money fields (`gross`, `platform_fee`, `provider_payable`, `refund`) are read by: earnings, dashboard, admin overview/transactions, payout, dispute decision, privacy export, booking detail, ledger. **Changing the fee model (G-01) touches `money.quote`, `bookings.create`, `purchases._create/session_share`, `confirm_payment` ledger rows, `refund` semantics, payout sums, every fee string in 5 locale files (`book.fee_note`, `services.fee_note`, `home.provide_body`, `me`/`admin` labels), admin overview economics and `booking.platform_fee` displays.** Existing bookings keep their snapshot, so old and new bookings will coexist with different meaning of `gross`.
- Cancellation policy is snapshotted per booking: changing the setting affects new bookings only; the UI reads the snapshot.
- Badges depend on completed bookings, reviews, verification, provider.created_at; they feed cards, profile, dashboard, notifications. `standing` currently feeds nothing else.
- Search ranking depends on verification count, years, completed, reviews, cancellations; changes alter provider rank and "How you are found" rank text.
- Compliance rules gate service publishing; changing rules does not unpublish existing active services.
- Room depends on booking status and times (`OPEN_BEFORE`, +2 h), ticket store, recording consent, area rule `recording_allowed`.
- Privacy erase depends on every table that holds member ids; **adding a table that stores member data requires updating `privacy.export/erase`**.
- Notification kinds map to client strings `notif.<kind>`; a new kind needs keys in all 5 locales or the raw key shows.
- Housekeeping loop is the single driver for expiry, reminders, auto-complete, retention, badges, delivery; if it dies silently, payments are stuck pending and reminders stop (errors are only logged).

## 3. Change-risk table
| Change | Risk | Check |
|---|---|---|
| Add a booking status | breaks CHECK, `LIVE` tuple, EXCLUDE predicate, bookings list `where`, web `isLive`, StatusTag, timeline, privacy blockers | grep status strings in service and web |
| Change price/fee rounding | ledger vs booking drift | compare `gross - fee` with payable |
| Switch payment provider | adapter keys non-idempotent (G-04), payout recorded paid at once | do C5 fixes first |
| Add TURN | only `ICE_SERVERS` env; credentials in JSON are sent to browsers | use short-lived credentials |
| Move to several API instances | in-memory hub, tickets, caches and duplicated housekeeping break | add Redis/pub-sub and a job lock |
| Rename a locale key | missing text in 5 languages | run `scripts/check_locale_parity.py` and key diff |
| Add admin action | must write audit; check reports/area upserts which currently do not | |
| Change `platform_setting` keys | whitelist in `admin.settings_put`, readers use defaults | |
| Expand file types | update `ALLOWED_MIME`, scanner, retention | |
| Change member id format | no FKs on seeker ids; identity contract | |

## 4. Cross-module
Vyapar: "refer to Counsel" and free professional listings overlap (critique C14); one policy for regulated professions is needed. Milavn: groups and online events are Milavn's; Counsel must not add them. MOD06 Payment Services: planned destination of payments (`payment_services` provider, port 8016 default); not started by owner decision until vendors exist. MOD07: Welfare Trust routing of earnings not connected. Platform: account deletion should call Counsel's internal erase (T1); notification service may take over delivery (B2).

## 5. Account deletion impact (added 2026-11-22)
- Cross-module: identity calls `POST /internal/v1/members/{id}/erase` (service key and `X-ForKhatri-Service: identity`) and retries; Counsel calls no other service. `identity.py forget()` drops the cached session and name.
- Other members touched: consumer or expert on future bookings (cancelled, refunded, notified `booking.cancelled_deleted`); holders of open packages and questions (`purchase.closed_deleted`); counterparties of time requests; counterparties of completed consultations (see "Deleted member"); reviewers and reviewees; reporters and reported (tombstoned).
- Money: refund rows and ledger entries on cancellation use the booking's snapshotted money, so a later G-01 change does not alter them; payments and payouts stay where money moved; unpaid eligible earnings are lost (owner decision).
- Files on disk (`STORAGE_ROOT`): `private/evidence/<member>/`, `public/photos/<member>/` (whole folder), `file.storage_key` files; removed after commit. A crash between commit and removal could leave orphans (unverified).
- Caches: 30 s session and name cache, call tickets (signed, in memory).
- Risk: one long transaction for members with a lot of data (not measured); no CI tests, manual script only.
