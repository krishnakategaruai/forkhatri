# MOD04 Counsel — 09 Implementation record

**Document status:** 2026-11-22, "as built".

## Contents
1 Structure · 2 Key files per feature · 3 Run, test, migrate · 4 Dev tooling · 5 Conventions · 6 Change log · 7 What is NOT built

## 1. Structure
```
modules/MOD04-counsel/
  BACKLOG.md                      open items (last updated 1 Oct 2026)
  counsel-service/
    app/main.py settings.py db.py errors.py i18n.py identity.py
    app/api/routes/ me discovery provide bookings requests offers payments room admin internal
    app/components/ ai audit availability badges bookings insights money notifications outbound places privacy providers purchases storage workspace
    db/init.sh  db/migrations/001..011  db/seeds.sql
    requirements.txt  .env.example  (.env local, api.log local)
  counsel-web/
    app/ (24 pages)  components/ (Shell, ProviderCard, BookingCard, BookingsBoard, Offers, TimeRequests, Badges, ui)
    lib/ (api, booking, format, identity, places, platform, i18n/)  locales/{en,hi,te,mr,kn}/common.json
    proxy.ts next.config.ts package.json
```

## 2. Key files per feature
| Feature | Files |
|---|---|
| Onboarding, evidence | `routes/provide.py`, `storage.py`, `routes/admin.py`, web `provide/profile`, `admin/providers/[id]` |
| Search and ranking | `components/providers.py`, `routes/discovery.py`, `places.py`, web `discover`, `lib/places.ts` |
| AI understanding, recap summary | `components/ai.py` |
| Slots | `components/availability.py` |
| Booking lifecycle, refunds, payout | `components/bookings.py`, `money.py`, `routes/bookings.py` |
| Custom times | `routes/requests.py`, web `TimeRequests.tsx` |
| Follow-ups, questions | `components/purchases.py`, `routes/offers.py`, web `Offers.tsx` |
| Room | `routes/room.py`, `workspace.py`, web `room/[id]/page.tsx` (708 lines) |
| Badges, insights | `badges.py`, `insights.py` |
| Notifications and delivery | `notifications.py`, `outbound.py` |
| Privacy | `privacy.py`, `routes/me.py`, `routes/internal.py` |
| Identity | `identity.py`, web `lib/identity.tsx`, `lib/platform.ts`, `proxy.ts` |

## 3. Run, test, migrate
See RUNBOOK.md. Migrate: `bash counsel-service/db/init.sh` (needs `.env` with DB_ADMIN/OWNER/APP credentials; creates DB, roles, extension, runs every migration in order, optional seeds). Tests: none exist (G-10).

## 4. Dev tooling
QA/dev members: `modules/MOD02-milavn/QA-USERS.md` (password sign-in `+9198000200NN`). Dev sessions: `platform/identity-service/scripts/dev_session.py`. Hub "Act as (development)". Seed consultants: Meera Iyer (business), Ravi Kumar (CA), Priya Sharma (design), Arjun Nair (legal), Neha Verma (career), Kiran Das (agriculture), Vikram Rao (pending review for admin demo). Admin in dev: members in `ADMIN_MEMBER_IDS`.

## 5. Conventions
One error shape; codes translated by client; no user-visible strings in the server; money in minor units; settings as data; every state change that moves money or trust writes `audit_log`; each component module has a docstring stating the rule it owns; handler-level authorisation; migrations are idempotent.

## 6. Change log (git history is thin: 4 commits touch this module — `24fef0f` 2026-09-06 initial, `692b61f` 2026-10-01 messages, `a8f7747` 2026-10-24 final push, `d8371f8` 2026-11-16 gitignore; dates below come from BACKLOG, migration headers and the critique)
| Date | What | Why |
|---|---|---|
| 2026-09-06 | Module scaffold, schema 001, taxonomy 002 | initial commit |
| 2026-09-30 | Custom time proposals (003), recordings/reminders/photos (004), badges (005), business offers (006: packages, questions, instant, recap), competitor-review features, call polish | owner requests and competitor review |
| 2026-09-30 | Packages reshaped into 1-3 follow-ups (008); group formats declined; no platform video | owner: "not tuitions", "no platform video call" |
| 2026-10-01 | Privacy export/delete and payout methods (007), file encryption and scan hook, discovery insights and near-me (009), delivery dispatcher and shared integrations (010), BACKLOG update | privacy and discovery research |
| 2026-10-06 | Marathi and Kannada (011); critique written | owner language request |
| 2026-11-22 | This documentation set (no code changes) | owner request for complete docs |

## 7. What is NOT built
Real payments, refunds, payouts, reconciliation (B1) and idempotency/outbox (C5); real delivery to WhatsApp/SMS/email/push (B2); professional register checks (B3); TURN server (B4); two-way calendar (B5); transcripts/captions (B6); AI key (B7); platform-wide account deletion calling Counsel (T1); ClamAV installed (T2); GST/TDS (T3); free pre-booking message (T4); other time zones and currencies (T5); admin role from platform governance (T7); real-device call checks (T8); recruitment of real consultants (T11); review highlights (T12); in-person consults (T13); search keyword insights (T14); reply time from chat (T15); more cities (T16); standing/reply time influence on ranking (D6); additional platform fee model per owner definition (G-01); attendance-based completion (G-03); rate limiting; RLS; automated tests; block UI; admin ability to hide reviews; operations desk/grievance officer; Welfare Trust routing; deploy kit; metrics dashboards; consent for AI summaries; reviewer anonymity option.
