---
project: ForKhatri
status: Sealed
approver: Chief Architect
updated: 2026-09-12
---

# Module Internal Architecture Standard — ForKhatri

## Purpose

`/ARCHITECTURE.md` decides *cross-module* questions: what container each of
the seven modules is, what database backs it, and how it talks to its
siblings and the platform's shared services. It deliberately stops at the
C4 Container boundary and leaves what happens *inside* each container to
that module's own `architecture.md` (`modules/MODxx-<slug>/architecture.md`
— superseding the earlier `07b-component-diagram.md` naming used before
this file existed) — correctly, since a system-wide architecture document
shouldn't grow seven different internal designs inside it.

But "each module invents its own internal shape independently" has a real
cost: seven modules that each solve the same internal problems (how do
components inside one container talk to each other, how is the one shared
database divided up, where does authorization actually get enforced) in
seven different ways makes every later cross-module integration, every new
engineer's second module, and every shared code-review checklist harder
than it needs to be. This file exists so that doesn't happen — it is the
one place the *pattern* for a module's internal architecture is decided,
so building the next module means applying a known shape, not rediscovering
one. It was written while building MOD03-Mangaly (`modules/MOD03-mangaly/
architecture.md` is its concrete application) but every principle below is
written generically, for whichever module reads it next.

**This file decides the pattern. It does not decide any module's actual
component list** — that is genuinely module-specific and belongs in
`modules/MODxx-<slug>/architecture.md`, built by applying the principles
here.

## 1. Where a module's internal architecture document lives, and what it contains

Every module gets its own `modules/MODxx-<slug>/architecture.md` once its
own BR/FR/UX/UI are Sealed and it's about to enter Impact Analysis/Tech
Reqs (or sooner, if — as with Mangaly — it's the module actually being
built while the wider platform's other modules aren't yet). That file
should contain, and only contain, what's genuinely specific to that module:

1. A recap (not a re-decision) of the module's placement in `/ARCHITECTURE.md`
   — its container, its database, its actual integration edges.
2. Its own component diagram (§2 below) and component→BR/FR traceability.
3. Any decision that is genuinely specific to that module's own domain
   (Mangaly's example: whether its wave-timing changes what a shared
   service needs, which is a Mangaly-build-order fact, not a generic
   pattern).

It should **not** re-derive or re-argue the generic patterns in §§2-5 below
— it applies them, and cites this file for why, the same way every module's
BR file cites `/ARCHITECTURE.md` rather than re-litigating container choice.

## 2. Component decomposition: use the module's own source language first

**Principle:** before inventing a component boundary scheme, check whether
the module's own source requirements documents already state one. Several
of this project's modules' source material (Mangaly's Master Requirements
Input is the clearest example, describing itself as "thin, replaceable
layers: identity, profile, Home Circle, authorization, discovery,
compatibility, trust, connection, sharing, communication, safety,
notifications, operations") already commits to an internal architecture
philosophy. Building the component diagram directly from that list, rather
than re-deriving a competing decomposition from the BR set independently,
avoids two decompositions of the same module quietly disagreeing with each
other. Only where the source is silent should the component boundaries be
invented fresh — and when they are, prefer the fewest components that
capture genuinely distinct technical responsibilities, not one component
per BR (a BR is a business-capability grouping, not necessarily a technical
boundary — several BRs commonly belong in one component, and one BR
occasionally spans two).

**Every fold-in or deviation from the source's own list must be recorded
as an explicit decision** in the module's own `architecture.md`, with the
reasoning — never a silent, undocumented departure from what the module's
own domain experts already said the shape should be.

## 3. Internal deployment shape: one process per container, modular internally

**Principle:** the module-internal deployment shape should mirror
`/ARCHITECTURE.md` ADR-001's own platform-level pattern one level down —
components inside one container are Python (or equivalent) packages under
strict import-boundary discipline, not separate internal services
communicating over a network, unless and until one component's load
profile genuinely diverges enough to justify a future, deliberate
extraction (its own ADR, not a default).

**Why:** this project's own ADR-001 already made this trade-off once, for
the platform as a whole (modular monolith over microservices, given team
size and operational capacity) — the same reasoning holds at one level
down inside any single container. A module that instead builds N internal
microservices for its own dozen-ish components has reintroduced the exact
operational overhead ADR-001 avoided at the platform level, just one layer
lower.

**Enforcement:** the import-boundary rule must be a lint rule the build
fails on, not a convention documented in a README. Each component exposes
exactly one public interface module other components import; nothing else
in that component's package is reachable from outside it.

## 4. Data ownership inside one shared database: schema-per-component

**Principle:** `/ARCHITECTURE.md` ADR-002 already rejects one flat database
shared by every container with no ownership discipline, at the platform
level. Apply the identical discipline **inside** each container's own
single database: one Postgres schema per business-logic component, each
with exactly one owning component as the only writer, and no
cross-schema join written by any component other than the schema's own
owner. A component that needs another component's data goes through that
component's own public interface (§3), never a direct query into its
schema.

**Add Postgres Row-Level Security as a second, database-enforced layer**
for any module whose data carries meaningful sensitivity — current (2026)
practice specifically recommends RLS for exactly this situation: an
application-level authorization bug does not become a data leak, because
the database itself refuses the query. Concretely: an authorization
component (§5) sets a session-scoped context variable once it resolves who
may see what; every schema's RLS policies key off that variable. This is
additive to, never a replacement for, application-level authorization
enforcement — RLS is what happens *if* a bug reaches the database, not the
primary design.

**Two specific, real (not hypothetical) failure modes any module adopting
this pattern must design against**, confirmed by live research when this
pattern was first exercised: (a) RLS is silently bypassed entirely if the
application connects to Postgres as a role that *owns* the table — RLS
policies do not apply to a table's owner by default, so the application's
runtime database role must be a non-owning role with policies explicitly
applied to it, never the migration/owner role; (b) under connection
pooling in transaction mode (e.g. PgBouncer), setting the session context
variable with plain `SET` lets it leak across pooled connections and
transactions, so one request's authorization context can silently apply to
a different request — the context variable must be set with **`SET
LOCAL`** (scoped to the current transaction only) or the pooling mode must
guarantee session affinity, never assumed safe by default. Any module
adopting RLS must confirm both of these explicitly in its own Tech Reqs
(Step 7) — "we added RLS" is not a complete answer without also stating
which role the application connects as and which of `SET`/`SET LOCAL` its
context-setting code uses.

## 4b. Idempotent mutation endpoints for offline-capable clients

**Principle:** any module whose client is expected to work offline or
under unreliable connectivity — a stated design goal for this platform's
own mobile-first, tier-2/3-connectivity user base, not an edge case —
must treat every mutation endpoint a client can plausibly queue and retry
(a message send, a profile save, a request accept/decline, a sharing
grant) as requiring an explicit idempotency mechanism. Without one, a
retried request after a connectivity drop can silently create a
**duplicate** record rather than safely no-op — a distinct and easy-to-miss
failure mode from "the write was lost," which is usually the only failure
mode offline-resilience requirements are written to describe.

**What this looks like concretely:** the client generates and persists an
idempotency key alongside each locally-queued mutation; the API layer
accepts that key on the relevant endpoints and returns the original
result on a repeated key rather than re-executing the mutation. This is a
cross-cutting API-contract requirement owned at the API layer (§3's
component boundary), not something each business-logic component
re-implements independently — a module that names "offline resilience" as
a requirement without also naming idempotency as its own explicit
mechanism has left a real gap, not a minor detail.

## 4c. One shared rate-limiting utility, not one per abuse-prone endpoint

**Principle:** almost every module ends up with several endpoints that
need rate-limiting for the same underlying reason — repeated login
failures, repeated invite/verification-request sends, repeated
OTP-resend taps — each of which is a distinct business capability
(possibly owned by different components) but an *identical* technical
problem: count attempts against a key within a rolling window, backed by
a store that survives a process restart and works across instances (a
DB-backed counter, not an in-memory one). Treat this the same way as
idempotency (§4b): **one shared rate-limiting utility, parameterized by
key/window/limit, that every rate-limited endpoint calls** — never
several components each building "a DB-backed counter, following the
same pattern as" another component's already-built one. The phrase "same
pattern as" is itself a warning sign worth watching for during review: it
usually means the *design* was shared but the *implementation* wasn't,
which is exactly the divergence risk this file's own §2 already warns
about for component boundaries, just recurring here for a cross-cutting
utility instead.

**Why this matters even though each individual counter is simple:** three
independently-built rate limiters "following the same pattern" can still
drift — one implementer picks a sliding window, another a fixed window;
one correctly uses `SET LOCAL`-equivalent transaction scoping, another
doesn't; a bug fix applied to one doesn't reach the other two. A shared
utility makes this class of endpoint uniformly correct by construction,
the same reason §3's import-boundary rule and §5's authorization
chokepoint both exist.

## 5. Authorization as a structural chokepoint, not a shared-library convention

**Principle:** any module whose BRs describe a real authorization
model — who may see or do what, under what relationship/consent/context —
should implement that as a single internal component every other
component's data-access path is *required* to route through, not a shared
library every component is merely *expected* to call. The difference
matters: a convention can be silently skipped by a rushed change; a
structural chokepoint (no component's schema is reachable without first
resolving through the authorization component) cannot be, by construction.

**What this looks like concretely:** a component method that needs to read
or write consequential data takes an already-resolved authorization
context as a parameter — it never accepts a raw actor identifier and
decides for itself whether that actor may proceed. If a method is found
taking a bare user ID and querying data with it, that is a defect against
this pattern, not a stylistic preference.

## 5b. Identity Bridge: how every module accepts the ForKhatri session

*(Added 2026-09-14; post-seal correction awaiting the owner's review. Binding
contract: `docs/ParentApp/07-tech-reqs.md` TR11, TR15, TR16; decisions:
`docs/ParentApp/00c-identity-and-entrance-decisions.md`.)*

**Principle:** a module never authenticates a person. The ForKhatri Identity &
Trust Service (`platform/identity-service`) and web entrance
(`platform/forkhatri-web`) own sign-in, sign-up, one-time codes, passwords and
sessions. Each module has exactly one internal component, its Identity Bridge,
that turns the platform session into the module's own authorization context;
no other component reads the cookie or calls the identity service.

**What the bridge does, in order:**

1. **No credentials in the module.** The module stores no passwords, OTPs,
   reset tokens or sessions for platform members and exposes no sign-in
   endpoint.
2. **Cookie.** Read the `fk_session` cookie (name from configuration). Absent
   means anonymous; the module decides between `401` and a public view.
3. **Internal resolve.** Call `POST /internal/v1/sessions/resolve` with the
   module's service name and key. Cache the result per token in process for
   at most 30 seconds (negative results 5 seconds), so sign-out reaches the
   module within 30 seconds.
4. **Fail closed.** If the identity service is unreachable, return `503`.
   Never fall back to a default or development member.
5. **Member-link row.** Ensure the module's own member-link row exists for
   `member_id`, creating it just-in-time on first entry. Tiers, roles,
   onboarding state and Level-3 trust live in that module's tables, never in
   the session.
6. **Module RLS context.** Bind the resolved `member_id` into the module's
   own authorization context and RLS variable with `SET LOCAL` (§4, §5), as
   before.
7. **Legacy development identity paths off by default.** Any interim path
   (for example a development member header or a module-local session
   cookie) is disabled by default and may be enabled only by an explicit
   development setting for automated tests.

**Module web clients:** send `credentials: "include"` on every API call; on
signed-out or `401`, navigate the full page to
`${FORKHATRI_ENTRANCE_URL}/?return_to=${encodeURIComponent(location.href)}`
(the entrance honours only allow-listed origins, TR17); sign-out calls the
identity service then returns to the entrance; module login/sign-up/OTP/reset
routes redirect to the entrance (files retained); every module surface shows a
persistent way back to the ForKhatri hub.

**Why:** one identity with no second account anywhere (ADR-004, ADR-021), no
credential readable by page JavaScript (ADR-019), and module data ownership
unchanged. The bridge is the same seam a future API gateway would take over.

## 6. Cross-component side effects: an in-process domain event bus, not direct call-chaining

**Principle:** when one action needs several independent components to
react (an audit log write, a notification, an operational case entry, all
triggered by the same underlying event), the triggering component
publishes a domain event to an **in-process** publish/subscribe bus that
reacting components subscribe to — it does not import and call each
reacting component directly. This is a different thing from
`/ARCHITECTURE.md`'s external Message Broker (which crosses container
boundaries); this bus lives entirely inside one container's process.

**Reliability requirement:** publish the event in the same database
transaction as the state change that caused it (a transactional outbox),
so a process crash between "the state changed" and "the event was
published" cannot happen — an audit trail with a silent gap is a
compliance failure, not an acceptable edge case.

**Why this over direct calls:** a new cross-cutting reaction (a future
compliance requirement, a new notification type) becomes a new subscriber
with zero change to the component that publishes the event it reacts to.
Direct call-chaining instead accumulates import dependencies between
components that have no real reason to know about each other.

## 7. Non-functional note: architectural coupling and business-operational priority are different lenses

**Principle:** `/ARCHITECTURE.md`'s non-functional baselines are set from
architectural coupling (is this container on another container's critical
path). When a module is, in practice, the platform's only live surface —
as Mangaly currently is — its actual operational priority is higher than
its architectural coupling alone implies, even though the coupling-based
number is still technically correct. Any module in this situation should
record that distinction explicitly in its own `architecture.md`, rather
than silently inheriting a baseline that undercounts real business risk.
This is a recording obligation, not a license to change the technical
number without an actual re-analysis.

## 8. What is *not* generic, and should never be pulled into this file

Tech stack (Python/FastAPI, React/TypeScript, Postgres) is fixed once, in
`/IMPLEMENTATION-TEST-STANDARDS.md`, for the whole platform — this file
does not repeat or re-litigate it. A module's actual component list, its
own domain-specific ADRs, and its own non-functional risk framing are
module-specific by definition and belong in that module's own
`architecture.md`, never generalized into this file just because two
modules happen to share a similar shape — generalize only a pattern
confirmed to recur, not a coincidence.

## Revision history

| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-12 | Initial version. Extracted from `modules/MOD03-mangaly/architecture.md`'s own MOD03-ADR-001 through MOD03-ADR-004, which on review were not actually Mangaly-specific — they were general patterns that happened to be written while building Mangaly. Moved here so every future module applies the same pattern instead of each independently rediscovering (or worse, diverging from) it, which is what actually makes later cross-module integration and shared engineering practice easy. Mangaly's own `architecture.md` was trimmed to reference this file and keep only what's genuinely Mangaly-specific. | Chief Architect — krishna kategaru (autonomous), 2026-09-12. |
| 2026-09-12 | Impact Analysis follow-up (Mangaly, the first module to exercise this pattern, surfaced two real gaps in it — genuinely generic ones, so fixed here rather than only in Mangaly's own file). §4 strengthened with the two specific RLS failure modes any adopting module must design against (non-owning application DB role; `SET LOCAL`, not `SET`, for the session context variable under transaction-mode connection pooling) — found via live research when this pattern was first exercised for real. Added §4b: idempotent mutation endpoints as a required pattern for any module with an offline-capable client, since "offline resilience" as a stated requirement silently implies this and a module could otherwise miss it entirely, as Mangaly's own Impact Analysis pass (IA102) found. | Chief Architect — krishna kategaru (autonomous), 2026-09-12. |
| 2026-09-13 | Tech Reqs review follow-up. A critique-mindset review of Mangaly's `07-tech-reqs.md` (checking specifically for common-utility duplication, per explicit instruction) found rate-limiting described three times as "the same pattern as" an earlier item, across two different components (Identity Bridge, Trust & Verification), rather than genuinely one shared implementation — the same divergence risk class §4b's idempotency pattern was already written to prevent, just recurring for a different cross-cutting concern. Added §4c: one shared, parameterized rate-limiting utility required for any module with multiple abuse-prone endpoints, rather than one independently-built counter per endpoint. | Chief Architect — krishna kategaru (autonomous), 2026-09-13. |
| 2026-09-14 | Post-seal correction: ForKhatri platform identity. Added §5b (Identity Bridge: how every module accepts the ForKhatri session), summarising `docs/ParentApp/07-tech-reqs.md` TR11, TR15 and TR16. No other section changed. Not re-sealed; awaits the owner's review. | Product-owner instruction, 2026-09-14: one ForKhatri sign-in and member identity for every module. |

## Approval

Chief Architect — [x] Approved — krishna kategaru (autonomous), 2026-09-12
