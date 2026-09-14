---
module: MOD02
step: module-coding-guide
status: Ready for Review
approver: Engineering Manager / Tech Lead
updated: 2026-09-13
---

# Coding Guide — MOD02 Milavn

Milavn's supplement to `/docs/PreStartResearch/IMPLEMENTATION-TEST-STANDARDS.md` and to MOD03 Mangaly's `CODING-GUIDE.md`, which it deliberately mirrors so an engineer moving between the two modules meets one engineering model. Where this file is silent, those govern.

## 1. Stack and shape

- **API:** Python 3.13 / FastAPI 0.141 / SQLAlchemy 2 async + asyncpg, one process, one package per `architecture.md` component under `milavn-service/app/components/<name>/interface.py`. Only `interface.py` is importable across components.
- **Web:** Next.js 16 (App Router) / React 19 / TypeScript, `milavn-web/`. One route folder per screen; `app/globals.css` is the single realisation of `04-ui.md`'s Design System Foundation; every user-visible string comes from `locales/<lang>/common.json`.
- **DB:** shared `forkhatridb` on `localhost:5433`, schemas `milavn_*`; the runtime role is `milavn_app` (non-owning; boot refuses to start otherwise). Migrations are hand-written SQL in `07a-db-implementation/migrations/`, immutable once applied — fix forward.
- **Ports:** web 3001, API 8001 (8000/3000 are Mangaly's). Run the API without `--reload` on Windows — see README for the orphaned-reloader-child trap and how to clear it.

## 2. Data access — raw SQL on purpose

Queries are explicit `text()` SQL with bound parameters, not ORM models, because every statement must be legible about *which RLS context it runs in*. Rules that follow from the Sealed RLS design:

- One request = one transaction = one member context. `api/deps.py` binds `milavn.member_id` (and `milavn.permission_scope` for moderators) with `set_config(..., true)` — transaction-local, never plain `SET`. Anonymous requests bind the nil UUID so policies evaluate to "public rows only" instead of a cast error.
- Bind-parameter casts are written `CAST(:p AS type)`. `:p::type` silently breaks SQLAlchemy's parameter parsing.
- When a legitimate read or write crosses another member's private rows (aggregate counts, organizer-side status changes, dispatcher fan-out, batch jobs), it goes through a `SECURITY DEFINER` function owned by `milavn_owner` that returns only counts/labels/ids — never by widening a policy. Migrations 002–014 are the catalogue.
- A participant cannot `SELECT … FOR UPDATE` a row they may not update; serialise per-occurrence critical sections with `pg_advisory_xact_lock(hashtext(id))`.

## 3. Cross-cutting rules (MODULE-ARCHITECTURE-STANDARD §4b–§6)

- Every client-queueable mutation wraps in `idempotency.idempotent(...)`; the web client sends `Idempotency-Key` via `api(path, { idempotent: true })`.
- Abuse-prone endpoints call `rate_limiting.enforce(...)`; never a private counter.
- Side effects publish with `events.bus.publish(...)` inside the request transaction; subscribers run after commit through `dispatch_pending` in their own transaction. Payloads carry identifiers only.
- Reads/writes of consequential data take an already-resolved role from `components/authorization/interface.py`; nothing outside the Circle package reads `circle_membership` (FR023).

## 4. Product invariants that are code, not copy

- No popularity input exists in `RankingEngine`; every card has a factor-grounded `why_reason` or is excluded (TR04).
- No endpoint returns a reputation number; `reputation_labels()` is the only reader (FR035/FR037).
- Attendance is private by default; only definer-owned counts leave the participant table (FR040).
- No `Match`/`Like` model anywhere; People suggestions are `(person, reason)` tuples (FR043/FR044).
- Important-class notifications cannot be muted (DB CHECK + API).
- Authentication is the parent platform's; `identity_bridge` is the only place a member id is resolved and it holds no credentials.

## 5. Language

The API resolves the request language once (`X-Milavn-Language`, then `Accept-Language`) into a `ContextVar`; anything that produces prose for a person — reasons, labels, errors — calls `app.i18n.translate(key, lang, **params)`. The web resolves the same language with i18next and formats dates with `Intl` per language. English catalogs are complete; Hindi/Telugu fall back per key.

## 6. Testing while implementing

- `milavn-web/scripts/cdp.mjs` drives a private headless Chrome over CDP (mobile viewport); scenarios live in `scripts/scenarios/` and screenshot to `.logs/`. Run one: `node scripts/cdp.mjs scripts/scenarios/core-loop.mjs`.
- Lint/type gates: `ruff check app` (API), `npx tsc --noEmit` and `npm run lint` (web). React-Compiler heuristics (`set-state-in-effect`, `immutability`) are warnings, not errors.
- Visual system = `AgentOutputs/DESIGN-DIRECTION-2030.md` (poster cards, category colour via `data-cat`, navy primary / saffron accent, Fraunces display type, glass controls, designed pickers `PlacePicker` / `WhenPicker` — never the browser's native select/datetime in product screens).
- Layout is responsive from one stylesheet: phones get the floating tab bar, ≥ 900px gets the rail (`SideNav`), card grids and the two-column detail; sheets become centred dialogs. Never add a second, desktop-only page.
- Natural-language features (`discovery/nl.py`) are deterministic parsers over the module's own vocabulary; anything they understand is echoed back to the person as chips. Do not call an external model from the request path.
- Do not hand-write `-webkit-` prefixed duplicates in `globals.css` (`-webkit-backdrop-filter` next to `backdrop-filter` made Turbopack's Lightning CSS drop the property entirely). Write the standard property once; the bundler prefixes from its targets.
- Step 10 maps `05-test-scenarios.md`'s Given/When/Then onto `Given_…_When_…_Then_…` tests; unit tests that assert an *absence* (no popularity column, no Match table, no raw score) are real tests.

## 7. Revision history
| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-13 | Initial version, written after the first full implementation pass so it records what was actually built and the traps found live (RLS + definer functions, `CAST()` binds, advisory lock, ghost port). | Step 9 — krishna kategaru (autonomous). |

## Approval
Engineering Manager / Tech Lead — [ ] Approved — name, date
