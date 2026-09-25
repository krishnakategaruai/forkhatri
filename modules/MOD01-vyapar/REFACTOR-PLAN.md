# Vyapar decoupling and agent-ready API refactor

**Owner's direction (2026-09-21):** "Since most of implementation is now complete, I want you to do refactoring, like components, compositions etc. where it is easy for me to integrate with other platforms. I don't want Vyapar tightly coupled with anything, and I need more API-like connections, as many as possible, so we can have agents working on top of Vyapar easily."

**Target:** Vyapar is a self-contained product with a public, documented, versioned API. ForKhatri becomes one *host* among several possible hosts. It plugs in through adapters, not through code in the core. Every capability a person has in the web app is also available to an external system or AI agent through a stable API.

## Guiding rules

1. **The core never imports a host.** No ForKhatri names, URLs, cookies or headers appear outside an adapter. The core depends on small interfaces; adapters implement them, and configuration chooses the adapter.
2. **One operation, many front doors.** Business logic lives in a service layer. REST routes, the agent (MCP) server, webhooks and background jobs all call the same service functions. None of them re-implements a rule.
3. **The API is the product surface.** Every route has:
   - an `operation_id`, tag and summary;
   - typed request and response models;
   - documented errors.

   That lets the OpenAPI document generate SDKs and agent tools directly.
4. **Behaviour does not change.** The refactor keeps every screen, rule, RLS boundary and translated string exactly as it is. Adding API surface for agents is new behaviour, and it goes through the same services and permission checks as the web app.
5. **Security is unchanged or stronger.**
   - Agents act *on behalf of* a member with a scoped, revocable credential.
   - Every agent action is audited with the credential that performed it.
   - The database still enforces RLS through `vyapar.authz_context`.

## Workstreams (file ownership is exclusive to avoid collisions)

### A. Backend core: service layer and API contract
**Owns:** `vyapar-service/app/routers/*` and new `vyapar-service/app/services/*`. Does not touch `identity.py`, `main.py` middleware, `integrations/` or `vyapar-mcp/`.

- Extract SQL and business rules from routers into `app/services/<domain>.py` (opportunities, listings, feed, enquiries, reviews, partnerships, trust_safety, verification, commercial, workspace, privacy, activity). Services take `(conn, ctx, typed input)` and return typed output. Routers only parse, call and return.
- Add a unique, stable `operation_id` to every route (`listOpportunities`, `getOpportunity`, `createEnquiry`…), plus a tag and a one-line summary. Every route gets a `response_model`.
- Use one consistent error envelope: `{"error": {"code": "opportunity_not_found", "message": "<localized>", "details": {}}}`. The machine-readable `code` is stable; `message` stays translated. Keep `detail` as well for the existing web app until workstream C switches over.
- Paginate list endpoints with a cursor (`?limit=&cursor=`, response `{items, next_cursor}`), additively and with backward compatibility.
- Responses carry raw slugs next to localized labels (for example `required_capabilities` plus `capability_labels`) so an agent can reason on stable identifiers.

### B. Integration edges: identity, events, agent access
**Owns:** `vyapar-service/app/identity.py`, new `vyapar-service/app/integrations/*`, new `vyapar-service/app/routers/integrations.py`, middleware in `main.py`, new migration(s) `015+`, and new package `vyapar-mcp/`.

- **Identity adapters** behind one `IdentityProvider` interface:
  - `DevHeaderProvider`, the current dev stub;
  - `ForKhatriSessionProvider`, the current real path, moved out of the core;
  - `BearerTokenProvider`, for agent and API credentials.

  Configuration selects the providers (`IDENTITY_PROVIDERS=bearer,forkhatri` or `bearer,dev`). `resolve_authz_context` stays the single choke point and returns an `AuthzContext` that also records *how* the caller was authenticated (member session, or agent credential with scopes).
- **Agent credentials:** a member creates, lists and revokes personal access tokens with scopes (`read`, `opportunities:write`, `enquiries:write`, `listings:write`…). Tokens are stored hashed, carry an expiry and record their last use. Every write made with a token is audited with the token id.
- **Outbound webhooks:** external systems subscribe to domain events (`opportunity.published`, `enquiry.received`, `enquiry.replied`, `review.published`…) that the existing outbox already records. Deliveries are HMAC-signed and retried with backoff. There are endpoints to create, list, delete and test a subscription.
- **Idempotency:** an `Idempotency-Key` header on POST endpoints; a repeated key returns the first response.
- **Adapters for the other host touchpoints:** notifications (in-app, web push, webhook), object storage and payments already have seams. Put them under `app/integrations/` behind their interfaces and document how a new host supplies its own.
- **`vyapar-mcp/`:** a standalone Model Context Protocol server. It talks to Vyapar **only through the public REST API** with a personal access token, so it never shares code or the database with the core. It exposes tools for the member-facing operations:
  - search the feed;
  - get an opportunity;
  - similar opportunities and matching profiles;
  - save;
  - apply or enquire;
  - post an opportunity;
  - list and reply to enquiries;
  - activity;
  - businesses and professionals search and profile;
  - notifications.

  It has its own README with setup instructions for Claude Desktop and Claude Code.

### C. Frontend: SDK, host adapter, composition
**Owns:** `vyapar-web/**` only.

- **`vyapar-web/lib/sdk/`:** a typed client covering every endpoint, grouped by domain (`sdk.opportunities.get(id)`). It uses a pluggable auth strategy (dev header, cookie session or bearer token) and a configurable base URL. `lib/api.ts` becomes a thin shim over it, and the pages move to the SDK.
- **Host adapter:** everything specific to ForKhatri in the shell (the dev member switcher, "Back to ForKhatri", the platform URL, the notification bell source) moves behind a `HostProvider` context with a `forkhatri` implementation and a `standalone` implementation. A configuration value selects between them.
- **Composition:** split the large pages into presentational components (props in, events out, no fetching) plus data hooks (`useOpportunity`, `useFeed`, `useListing`…). Start with Opportunity Detail, Listing Detail, Discover, Businesses, Enquiries and Activity.
- **Embeddable surfaces:** export a small set of self-contained components (an opportunity card, profile recommendations, an opportunity detail panel) that another app could mount with only an SDK instance and a host.

## Shared constraints for every workstream
- Never touch files outside `modules/MOD01-vyapar/`, and never delete files.
- Never disturb other modules' ports or processes. The live Vyapar API stays on 8011 and the web app on 3011, and they are for the owner. Test backend changes on a private uvicorn instance on a free port (check the port first), and kill only processes you started, by their exact PID.
- Keep the web app working at every step. Run `npx tsc --noEmit` (web) and import the backend (`python -c "import app.main"`) before finishing.
- All user-visible text stays translated (en/hi/te). No hardcoded English.
- Record your work as an IMP entry in `09-implementation.md`.
