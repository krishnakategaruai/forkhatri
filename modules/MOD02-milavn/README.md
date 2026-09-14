# Milavn (MOD02) — run it

Milavn is ForKhatri's real-world participation network: *what's happening around you*, one-tap RSVP, circles that form from people who keep showing up together, trust you can see, privacy by default.

## Start (two terminals)

```powershell
# API — FastAPI on http://127.0.0.1:8001  (no --reload on Windows, see below)
cd modules\MOD02-milavn\milavn-service
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8001

# Web — Next.js on http://localhost:3001
cd modules\MOD02-milavn\milavn-web
npm run dev
```

Prerequisites already in place on this machine: Postgres on `localhost:5433`, database `forkhatridb`, roles `milavn_owner` / `milavn_app` (dev passwords in `07a-db-implementation/.env`), migrations `001–015` applied, `seeds.sql` + `seeds-dev.sql` loaded. To rebuild from scratch: `cd 07a-db-implementation && ./init.sh` then apply `migrations/002..015` and `seeds-dev.sql` as `milavn_owner`.

Why no `--reload` on Windows: uvicorn's reloader binds the socket and spawns the real server as a `multiprocessing` child that inherits it. If the reloader is killed, that child survives as an orphan (`python -c "from multiprocessing.spawn import spawn_main; spawn_main(parent_pid=…)"`) and keeps serving stale code on the port — `netstat` then shows a LISTENING socket owned by a dead PID. That is what had made 8001 unusable earlier. To clear it: find `python.exe` processes whose command line contains `spawn_main` and whose `parent_pid` is gone, and stop them. Restart the API by hand after code changes instead.

## Click through

Works as a phone app (≤ 899px: floating tab bar) and as a desktop app (≥ 900px: left rail, card grid, two-column detail). Open it in a normal browser window and resize. Light, warm paper is the default; Dark is a choice under Profile → Appearance. The visual system is described in `AgentOutputs/DESIGN-DIRECTION-2030.md`.

1. Open **http://localhost:3001** → *Continue as* (sign-in belongs to the ForKhatri platform; this picks a development identity).
   - **Asha Reddy** — organizer with a circle and a series; **Priya Sharma / Neha Verma** — fresh onboarding; **Milavn Moderator** — the moderation queue.
2. Onboarding: locality (use my location / pick), interests, language (English / हिंदी / తెలుగు).
3. **Ask Milavn** at the top of Home in your own words ("badminton this weekend near me", Hindi/Telugu too): what it understood shows as chips, and an empty result widens itself and says so. **Around you**: Today · Tomorrow · This weekend · Coming up, each card with what / when / where / who / how many / *why this* (an empty one says *Be the first*). Switch **Feed / Calendar / Map / Search**. The **Make something happen** button folds to **+** as you scroll.
4. Tap a card → detail → *Why this*, *From your circles* (named circle-mates going), **Where** mini-map (tap for directions), **Add to calendar** (.ics), **Interested / Going** (springy), share (WhatsApp, SMS, email, copy, on-device QR), report, block. Once you're going: **Plan together** (a thread for the people going + organizer) and **Moments** (photos by people who were there). Tap any name → their person page.
5. **Make something happen**: **Smart fill** turns one line ("badminton tomorrow 7pm at Madhapur for 8") into the form; four fields with one-tap *When* chips (Tonight 7 pm, Tomorrow 7 am …), "More options" for capacity, circle, repeats, cover, safety.
6. Header, on every main screen: People · **Alerts bell** (unread count) · **your avatar, always last**. There is no Alerts tab. Profile is about the person; language, appearance, location precision, help, sign-out and delete sit behind the gear icon. **Circles**: **Near me / All** discovery (circles have a home locality; yours comes first), join, a members-only **Board**, community memory, "you keep showing up together" suggestions. **Calendar**: mine / community / circle. **Alerts**: four classes, Important can't be muted. **Profile**: language, appearance, location precision, help.
7. Organizer tools (from an activity you host): attendee list, announcements (timed, the same text twice in an hour is refused), QR / manual check-in, no-show (never punitive), co-organizers.
8. Moderator (`/admin/moderation`): the shared Admin & Governance Console contract, rendered.

Real time, on the device: a **Live** pulse on posters while an activity is on, "in 40 min" when it is close, a **Happening now** rail on Home, and **Use where I am** (a one-shot device position that changes what you see, never your stored profile). Threads refresh every 15 s.

**Chats** (tab before Profile): 1:1 and group messaging with people you share an activity or a circle with (a stranger gets a 403), live over WebSocket (`/ws/chat`), emoji reactions instead of likes, photos, typing, "active now" presence, and **expressions**: turn on the camera icon in a chat and your mood (😊 😂 😮 😉 🤔 😍) is detected on the device and shown next to your messages; the manual mood row works without a camera. From a person page, **Message** opens the chat.

Public page without login: `http://localhost:3001/a/<slug>` (server-rendered, SEO metadata).

## Where things are

- `AgentOutputs/` — the pipeline artifacts (01 → 09a). `09-implementation.md` is the implementation record.
- `milavn-service/app/components/<component>/interface.py` — one package per `architecture.md` component.
- `milavn-web/app/*` — one folder per route; `app/globals.css` is the design system; `locales/` holds every string.
- `milavn-web/scripts/` — the CDP browser-test harness and scenarios (`node scripts/cdp.mjs scripts/scenarios/golden-path.mjs`), screenshots land in `milavn-web/.logs/`.
