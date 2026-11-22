# ForKhatri whole-product glossary (2026-11-22)

Document status: AS BUILT on 2026-11-22. One place for the words of the whole product.
Owner rule (2026-09-29): "Terminology is really important!" Every concept has one canonical term, written the way
people speak in English, Hindi and Telugu (Marathi and Kannada since 2026-10-06); storage words (enum names, table
names) never reach a screen. Before adding a user-visible string, reuse the term below or in the module glossary.

Module glossaries: Vyapar has the full word-level glossary with five languages (`modules/MOD01-vyapar/GLOSSARY.md`,
the model other modules should follow). Milavn, Mangalya and Counsel had no `GLOSSARY.md` on 2026-11-22; their terms
below are gathered from their documents and READMEs and marked "module doc" (gap: each should get its own file).
Telugu and Hindi quality rule: accurate and respectful, as people speak (owner rule 2026-09-30).

## Contents

1. [Product and platform](#1-product-and-platform)
2. [Identity, sign-in and sessions](#2-identity-sign-in-and-sessions)
3. [Governance and the admin console](#3-governance-and-the-admin-console)
4. [Vyapar (MOD01)](#4-vyapar-mod01)
5. [Milavn (MOD02)](#5-milavn-mod02)
6. [Mangalya (MOD03)](#6-mangalya-mod03)
7. [Counsel (MOD04)](#7-counsel-mod04)
8. [Planned modules](#8-planned-modules)
9. [Engineering terms](#9-engineering-terms)
10. [Words not to use](#10-words-not-to-use)

## 1. Product and platform

| Term | Meaning | Where |
|---|---|---|
| ForKhatri | The community app: one entrance, one sign-in, several modules. Written the same in every language | hub |
| Member | Anyone signed in. Use "member", never "user" on screen (Vyapar glossary) | all |
| Khatri community | The community the product serves | all |
| Samaj | The community body whose office bearers run ForKhatri (owner direction 2026-10-02); chapters are local branches | governance |
| Hub | The signed-in home that lists modules ("Open now", "Coming to ForKhatri"), has the intent bar, bell, avatar | `platform/forkhatri-web` |
| Entrance | The sign-in arrival screen; the first owner-approved design | `Arrival.tsx` |
| Module | An independently built capability inside ForKhatri (MOD01 to MOD07). Registry key is its stable name | registry |
| Registry | The platform table of modules (key, name, taglines en/hi/te, availability, accent, order) | `registry.module` |
| Availability | `available`, `in_development`, `planned`; shown as open or "coming" tile | registry |
| Intent bar / command orb | The hub's text and mic box that understands what a member wants in en/hi/te (keyword table, about 60 terms) | `CommandOrb.tsx`, `intent.ts` |
| ForKhatri in numbers | The members dashboard: aggregate counts, open to every signed-in member (owner decision 2026-09-27) | `/insights` |
| Account sheet | Name, masked phone and email, language, theme, sign out | `AccountSheet.tsx` |
| Bell | Alerts icon left of the avatar; empty state today (no platform inbox yet) | hub |
| Act as (development) | Development member switcher; never in production | `/dev/v1` |
| Persona | A named development member: asha, new-member, mangalya-family, mangalya-parent, milavn-moderator, krishna (owner; people only, never automated tests) | `dev_tools/personas.py` |
| Shared integrations | One Python library for payments, messaging, delivery, places that every module adapts to; vendors chosen later | `shared/forkhatri-integrations` |
| Sandbox | A fake payment provider for local development; no money moves | payments adapter |
| Tunnel (quick tunnel) | A temporary public `*.trycloudflare.com` link to a local service, for showing the app on phones | `scripts/tunnel.mjs` |
| Zone | A separately built web app served under one path (Multi-Zones): `/mangaly`, `/milavn`, default `/` | production |
| Core Platform database | `forkhatridb`, the shared database holding Milavn's schemas | ADR-001, ADR-002 |

## 2. Identity, sign-in and sessions

| Term | Meaning |
|---|---|
| Identity & Trust Service | The platform service that owns members, codes, passwords, sessions, registry and governance. Port 8100 |
| Basic identity | The only platform data: name, verified phone or email, language, level, status. Profiles live in modules (owner rule 2026-09-14) |
| Verification level | 0 provisioned (profile created by someone else, not yet signed in), 1 verified phone or email, 2 ID document (no code path yet) |
| Code (OTP) | Six-digit sign-in code, valid 5 minutes, 5 attempts, resend after 30 seconds |
| Pepper | A server secret mixed into code hashes (`OTP_PEPPER`) |
| Challenge | One issued code awaiting verification (`otp_challenge`) |
| Session | A signed-in period: opaque token, 30 days; stored only as a SHA-256 digest |
| `fk_session` / `__Host-fk_session` | The session cookie name in development / production |
| Handoff | A 60-second single-use code that moves a session to a module on a different hostname (`fk_handoff` parameter) |
| `return_to` | Allow-listed address the member returns to after sign-in |
| Service key | Secret a module service presents to the internal API (`X-ForKhatri-Service-Key`) |
| Provisioned member | A not-yet-joined member a parent created for a child's number; removed after six months if never used (owner rule 2026-09-21) |
| Rate limit | Caps on code and password attempts per identifier and per IP in a 15-minute window |
| `delivery_unavailable` | Answer when no SMS provider exists; the member is told to use password or email |

## 3. Governance and the admin console

| Term | Meaning |
|---|---|
| Admin & Governance Console | One shell for all of ForKhatri at `/admin` (ADR-012) |
| Role assignment | A role held over an area for a term (role, scope kind and key, start and end); office bearers change yearly |
| Chapter | A local Samaj branch that scopes roles; can be closed |
| Scope | The area of authority: platform, chapter or module |
| Admin scope | A module permission such as `milavn.moderate`, carried in the session claims |
| Suspension | Temporary block of sign-in everywhere (up to 30 days by one person) with a reason |
| Ban | Permanent block; needs two-person approval |
| Two-person approval | `approval_request` kinds `ban` and `grant_role`: a second office bearer decides |
| Contact reveal | Showing a member's phone or email to an admin; needs a reason and is audited |
| Audit event | Append-only record of an administrative action |
| Queue | A module-owned list of items for moderators shown in the console (for example Milavn moderation) |

## 4. Vyapar (MOD01)

Canonical source: `modules/MOD01-vyapar/GLOSSARY.md` (en, hi, te, mr, kn). Summary of the English terms:

| Term | Meaning | Do not say |
|---|---|---|
| post | Anything published in the feed (storage name `opportunity`) | opportunity |
| Job | Salaried or daily-wage work | Employment |
| Project | Paid piece of freelance work | |
| Local service | A repair, cleaning, catering or similar need at a place | |
| Business partnership | A business tie-up | |
| Training | Course or scheme | |
| Community & government | Samaj or government item | |
| Business profile / Work profile / profile | A business's page / a person's own page / either (storage `listing`) | listing |
| skills | What a person can do (businesses: services and skills) | capabilities |
| member | A signed-in person | user |
| applicant, client, professional | Who applies to a job, who pays, who does the work | buyer, hirer, provider |
| request | A conversation thread (storage `enquiry`); kinds: Question, Application, Proposal, Message, Interested | enquiry |
| Apply, Send proposal, Send a quote, Ask for a price, I'm interested, Discuss partnership, Shortlist, Hire, Decline | The action buttons by post kind | Enquire Now, Submit a Proposal |
| stage / paid in advance | Replace milestone and escrow for non-professionals | milestone, escrow |
| From your community / Shared from elsewhere | Where a post came from | |
| Looking for work, Open to work, Just looking, Not interested right now | A person's intent | |
| Pay wording | "₹15,000 a month", "₹800 a day"; professionals "₹9 lakh a year" with monthly figure | LPA |
| Counsel boundary | Vyapar never uses mentor, mentoring, counselling or guidance; those belong to Counsel; only the "Refer to Counsel" handoff names it | |
| Pre-call | Per-post choice whether people may call before applying (owner decision 2026-09-28; storage name differs: verify in `vyapar-service`) | |
| Reputation, boost, sponsored | Vyapar ranking and paid-visibility words (see its glossary) | |

## 5. Milavn (MOD02)

Source: `modules/MOD02-milavn/README.md`, `PLAN-places-events-groups.md`, `07-tech-reqs.md` (module doc; no `GLOSSARY.md`).

| Term | Meaning |
|---|---|
| Activity / event | Something happening at a time and place that members can join; public page `/a/<slug>` |
| Around you | Home lists by time: Today, Tomorrow, This weekend, Coming up |
| Interested / Going | One-tap RSVP states |
| Circle | A group formed from people who keep showing up together; discovery "Near me / All" |
| Series | A repeating activity |
| Ask Milavn | The natural-language search box; shows what it understood as chips and widens an empty result |
| Why this | Explanation of why an activity was suggested |
| Plan together | A thread for people who are going |
| Smart fill | Turns one line ("badminton tomorrow 7pm at Madhapur for 8") into the create form |
| Organizer, co-organizer | Who hosts; tools: attendee list, announcements, QR or manual check-in, no-show (never punitive) |
| Check-in / no-show | Attendance marking |
| Trust you can see | Visible reliability signals (module doc; verify exact levels in `07-tech-reqs.md`) |
| Expressions | Camera-based reactions in a chat |
| Alerts bell | Header bell with unread count; there is no Alerts tab (owner standard 2026-09-28) |
| Moderator / moderation queue | Role and queue at `/admin/moderation`, via the console |
| Live pulse / Happening now | Real-time indicators while an activity is on |
| Use where I am | One-shot device position that changes what you see, never the stored profile |
| Locality precision | Setting for how exact a member's location is |

## 6. Mangalya (MOD03)

Source: `modules/MOD03-mangalya/` (`v1-decisions.md`, `01-business-requirements.md`, `reference.md`); module doc; no `GLOSSARY.md`.
The product name is Mangalya (renamed from Mangaly on 2026-09-29); folders, service name and registry key still use `mangaly`.

| Term | Meaning |
|---|---|
| Candidate | The person looking for a match |
| Home Circle | The family circle around a candidate: parents and guardians who act for them (owner rule: parents act for the candidate) |
| Looking for | Bride or groom; always applied to discovery (owner rule) |
| Discover | The module's browse screen (one large picture per row on phones) |
| Home | Mangalya's landing (memory: owner rules 2026-09-28 on Home versus Discover; exact wording unverified, check `v1-decisions.md`) |
| Connection | A mutual link between candidates that opens chat |
| Guna Milan | Traditional horoscope compatibility score |
| Mangal Dosha | Horoscope condition checked by the horoscope service |
| Horoscope filter | Birth details public to filter horoscope matches (owner decision 2026-09-27) |
| Match | A suggested compatible profile; AI-first matching (owner direction 2026-09-27) |
| Marriage broker agent | Traditional broker empowered inside the product (owner direction 2026-09-29) |
| Wedding arrangements, Guides | Stage-based wedding services after a match, and a Guides tab (owner direction 2026-10-01) |
| Provisioned profile | A profile a parent creates for a child's number |
| Verification / trust | Evidence-based levels; "mutual story verification" (owner decisions) |
| No screenshots | Screenshots must not be possible anywhere in Mangalya (owner rule 2026-09-29) |
| Calm, not highlighted | Design rule: kumkum and turmeric palette, serif type, red reduced not removed, no grey |

## 7. Counsel (MOD04)

Source: `modules/MOD04-counsel/BACKLOG.md`, owner rule 2026-09-30 (module doc; no `GLOSSARY.md`).

| Term | Meaning |
|---|---|
| Counsel | Paid one-to-one guidance from verified professionals; registry tagline "Guidance from verified professionals when you need it" |
| Expert | A verified professional offering guidance (shared verified-credential idea, ADR-013) |
| Session | A paid one-to-one conversation; Counsel is one-to-one only, groups live in Milavn (owner rule 2026-09-30) |
| Boundary with Vyapar | Peer help and listings stay in Vyapar; paid advice stays in Counsel |
| No platform video call | ForKhatri has no shared video-call service (owner decision 2026-09-30) |

## 8. Planned modules

| Module | Meaning |
|---|---|
| MOD05 Dashboard | The personalised entry and local information; today partly the hub and the insights page |
| MOD06 Payment Services | Everyday payments and member benefits; target of the `payment_services` payments adapter |
| MOD07 Loans & Finance | Financial options and partner pathways; houses the Welfare Trust that routes earnings to welfare (owner direction 2026-10-02); regulatory posture unresolved (BLOCKER-002 in `modules/modules.md`) |

## 9. Engineering terms

| Term | Meaning |
|---|---|
| ADR | Architecture Decision Record, in `ARCHITECTURE.md` |
| BR, FR, SCR, API, TBL, TC | Business requirement, functional requirement, screen, endpoint, table, test case identifiers |
| RLS | Row level security: the database limits rows by policy; works only because app roles do not own tables |
| Owner role / app role | Database role that owns tables / the non-owning role the service uses |
| Migration | An ordered SQL file; forward-only |
| Seed | Reference or development data; development seeds never load in production |
| Basepath | Path prefix a Next.js app is served under (`/mangaly`) |
| Multi-Zones | Several Next.js apps served as one site |
| `root_path` | FastAPI prefix awareness behind the proxy (`/api/identity`) |
| Fail closed | Refuse (503) rather than allow when identity is unreachable |
| Quick tunnel / named tunnel | Temporary random public link / permanent one on a domain |
| Heartbeat | 5-minute cron that checks the site and restarts the stack after 3 failures |
| R2 | Cloudflare object storage used for off-server backups |
| DLT | Indian SMS sender registration (needed before real SMS; unverified details) |
| DPDP | India's Digital Personal Data Protection Act, 2023 (needs lawyer review) |

## 10. Words not to use

Storage and internal words must not reach a screen: opportunity, listing, capabilities, enquiry, segment, stale, enum names.
Use "member" not "user". Never "LPA" for job seekers. Do not call Vyapar features mentoring or counselling.
Hindi and Telugu use common spoken loanwords (job, salary, online), not stiff Sanskritised forms.


## 11. Account deletion words (added 2026-11-22)

- **Kind A deletion**: "Delete my ForKhatri account" in the hub. Removes the identity and the member's data in every module.
- **Kind B deletion**: "Delete my data in <module>" in one module's settings. Removes only that module's data; the ForKhatri identity stays and the member can come back as a new member.
- **Erase**: the module routine that removes one member's data (internal endpoint `POST /internal/v1/members/{id}/erase`). Safe to run twice.
- **Tombstone**: a one-way hash (HMAC-SHA256) that replaces a deleted member's id in records that must stay. It cannot be turned back into the member.
- **Deletion receipt**: the one-line record of a finished deletion (tombstone, date, modules, counts, what was retained and why).
- **Deleted member**: the label other people see where the deleted member's name used to be.
- **Retained**: data that must stay for law or safety, stripped of name, contact and free text.
- **Stuck deletion**: a deletion where a module could not finish; the admin console lists it and can retry.
