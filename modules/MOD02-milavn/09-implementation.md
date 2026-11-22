---
step: 09-implementation
module: MOD02
status: As built (record)
updated: 2026-11-22
---

# 09 - Implementation record - MOD02 Milavn

## Document status
2026-11-22, as built. The long working log of September 2026 stays in `AgentOutputs/09-implementation.md` (IMP1 to IMP37, entries to 2026-09-15, 107 KB; its header still says migrations 001-034). This file is the current summary: structure, key files, how to run, conventions, dated changes through October 2026, and what is not built. Git history for this folder is coarse (commits such as "final push", "new", "messages"; `git log --since=2026-09-01 -- modules/MOD02-milavn` shows 14 commits, last a8f7747 on 2026-10-24), so the change log below is rebuilt from migration headers, QA runs and owner decisions, not from commit messages.

## 1. Folder structure
```
modules/MOD02-milavn/
  01..07a, 08, 09 *.md        documents (this set)
  architecture.md, API-REFERENCE.md, GLOSSARY.md, RUNBOOK.md, TRACEABILITY.md, COVERAGE-REPORT.md
  PLAN-places-events-groups.md, ONBOARDING-REDESIGN-2026-10.md, QA-USERS.md, README.md
  AgentOutputs/               pipeline outputs, REVIEW-*, QA-RUN-*, EVENT-PAGE-LEARNING, research, onboarding-mockups/
  07a-db-implementation/      migrations/001-055, schema.sql (lags), seeds.sql, seeds-dev.sql, init.sh, README
  milavn-service/             FastAPI: app/{api,components,config,db,events,i18n,idempotency,rate_limiting}, tests/
  milavn-web/                 Next.js: app/ (routes), components/, lib/, locales/, public/, scripts/
  scripts/                    seed_qa_members.py, seed_fresh_members.py
```

## 2. Key files per feature
| Feature | Backend | Web | DB |
|---|---|---|---|
| Identity, session | `api/deps.py`, `components/identity_bridge` | `lib/identity.tsx`, `proxy.ts` | none |
| Profile, places, first run | `api/routes/profile.py`, `components/places`, `components/profile` | `app/onboarding`, `components/PlacePicker.tsx`, `lib/first-run.ts` | 050-live-places |
| Discovery, ask, smart fill | `routes/discovery.py`, `components/discovery/{interface,nl}.py` | `app/page.tsx`, `app/discover`, `AskBar.tsx` | 020 |
| Events | `routes/occurrences.py`, `components/activity/interface.py` | `components/DetailClient.tsx`, `app/create`, `app/organizer/[id]` | 001, 051, 054 |
| Program, teams, online | `routes/events.py`, `components/activity/events.py` | `EventProgram.tsx`, `lib/event-formats.ts` | 054 |
| Tickets, codes, QR | `routes/tickets.py`, `routes/payments.py`, `components/ticketing`, `components/payments` | `TicketPanel.tsx`, `TicketsManager.tsx`, `QrCode.tsx`, `app/pay/sandbox` | 017, 052, 055 |
| Circles | `routes/circles.py`, `components/circle/{interface,people,social}.py` | `app/circles`, `app/circles/[id]` | 012, 024-044, 050 |
| Circle social | `routes/circle_social.py`, `routes/conversation.py`, `components/circle/social.py`, `routes/media.py`, `media_files.py` | `CircleAlbums.tsx`, `CohostPanel.tsx`, `CircleCover.tsx` | 045, 049, 053 |
| Chat | `routes/chat.py`, `components/connect/{interface,chat}.py` | `app/chats`, `MoodAvatar.tsx`, `lib/expressions.ts` | 015, 016, 049 |
| Notifications | `routes/notifications.py`, `components/notification/interface.py` | `app/notifications` | 011, 048, 053 |
| Safety, moderation | `routes/safety.py`, `routes/admin.py`, `components/safety` | `app/admin/moderation` | 047 |
| Trust, reputation | `components/trust` | `app/p/[id]` | 006 |
| Public page, calendar feed | `routes/public.py`, `routes/calendar.py` | `app/a/[slug]`, `app/calendar`, `lib/ics.ts` | 014 |
| Insights for dashboard | `routes/insights.py` | none | 039 |

## 3. How to run, test, migrate
- Run: see `RUNBOOK.md` and `README.md`. API without `--reload` on Windows (an orphaned reloader child keeps serving stale code).
- Tests: `cd milavn-service; .venv/Scripts/python -m pytest tests` (needs the dev database). Web checks: `npx tsc --noEmit`, `npm run lint`, browser scenarios `node scripts/cdp.mjs scripts/scenarios/golden-path.mjs`. Not run during this documentation pass.
- Migrate: apply `07a-db-implementation/migrations/NNN-*.sql` in file-name order as role `milavn_owner` (`psql`). `init.sh` builds from scratch. There is no migration ledger table. Never apply as `milavn_app`.
- Seed: `seeds.sql`, `seeds-dev.sql` (12 events, 4 circles); QA members: `platform/identity-service/.venv/Scripts/python modules/MOD02-milavn/scripts/seed_qa_members.py` (add `--remove` to delete exactly those 20 and their Milavn data). Sign in with `QA-USERS.md` (phones +9198000200NN, password in CLAUDE.md), or `dev_session.py <uuid>`.

## 4. Conventions
One component per package, `interface.py` as its only public face; one request equals one transaction equals one member context; writes to other people's rows through SECURITY DEFINER functions with outcome codes; every user-visible string is a key in all five catalogs (en, hi, te, mr, kn) and server reasons are (key, params); no environment values in code (settings only); comment block stating FR and reasoning on each requirement's code (`# [FR..]`); CSS tokens in `globals.css`; Hindi and Telugu must be accurate and respectful; use one term per concept (glossary).

## 5. Dated change log (September to November 2026)
| Date | What was built | Why / source |
|---|---|---|
| 2026-09-06 to 09-15 | Foundations and FR001-FR124 (see AgentOutputs log): discovery, occurrences, RSVP, circles, trust, notifications, safety, chat, paid spots, belonging, regulars | pipeline Step 9 |
| 2026-09-18 | Date-bound temple and travel circles (035); Samaj updates to chapters (036, 037); open circles visible fix (038) | owner request |
| 2026-09-27 | Platform member insights endpoint (039) | owner: total users and location hotspots |
| 2026-09-28 | Circles are communities not chats, pair suggestions removed (040); organizer deletes circle (041); circle covers (042); integrity fixes (043) | owner circle review |
| 2026-09-29 | Invites, links, recommendations (044); private media (045); invites honour ask-first (046); one open report (047); reminders expire (048); activity chat and post social layer (049) | owner and critique |
| 2026-10-05 | Plan approved (PLAN-places-events-groups.md). Migration 050 (flexible groups, women-only, trip plan) and 050 (live places), 051 (venue), 052 (ticket types, codes, contact, professional category), 053 (circle media, albums, notify, co-host), 054 (event formats, agenda, speakers, stalls, teams, online join, follow-up) | owner approval |
| 2026-10-06 | QA runs with 20 QA members (community, fun, professional, safety); fixes in code listed in the QA-RUN files and 05; migration 055 written (waitlist offer fix applied, GRANT not applied); onboarding study and event page study written; first-run redesign (place only) and event page (deciding, going, hosting, recap) implemented in `onboarding/page.tsx` and `DetailClient.tsx`; Marathi and Kannada catalogs added by another session | owner: "too senseless", first-run findings |
| 2026-10-24 | Repository push a8f7747 (last change touching this folder) | owner |
| 2026-11-22 | Documentation brought to as-built state (this set) | owner request |
| 2026-11-22 | Account deletion: migration 056, `components/erasure/interface.py`, `routes/erasure.py` (registered in `main.py`), `rate_limiting/__init__.py` scope ACCOUNT_DATA_DELETE, `identity_bridge` "Deleted member", web `app/me/page.tsx` and five `locales/*/common.json`. Migration 055 recorded as applied the same day | owner: "A user should be deleted if he needs to delete his account, immediately" |

## 6. What is NOT built
Real payment vendor, host payouts, platform fee; verified women-only (steward approval); per-day check-in; automatic recurring dates; guests on paid events; request-based first contact; host verification and large-event checklist; data export and retention schedule (DPDP); malware scan and image re-encode; load and security tests; monitoring and alerting; external scheduler and multi-instance safety; cost split on trips; album tied to an event; in-app video (excluded by decision); migration ledger table; applied GRANT of migration 055; a clean demo tenant.


**Not built (account deletion, 2026-11-22):** browser check of the Me control; erase-specific tests; data export before deletion; email or SMS confirmation; retention-expiry job; payout rule for refund-pending paid tickets; orphan-file sweeper; separate re-authentication for kind B.
