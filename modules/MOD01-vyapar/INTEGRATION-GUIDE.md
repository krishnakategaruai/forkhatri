# Vyapar integration guide

Vyapar is a self-contained product with a public, versioned REST API (`/v1/...`, described in `vyapar-service/openapi.json`). ForKhatri is one **host**, and other hosts can plug in the same way. Every host-specific touchpoint sits behind a small adapter in `vyapar-service/app/integrations/`, and configuration chooses the adapter. The core never imports a host.

The guide has two parts:
- **Part 1** is for teams embedding Vyapar in their own platform.
- **Part 2** is for anyone building an agent, script or system on top of Vyapar's API.

---

## Part 1: plugging Vyapar into a host platform

| Seam | Where | Interface | Shipped adapters |
|---|---|---|---|
| Identity: who is calling | `app/integrations/identity/` | `IdentityProvider.resolve(request)` | `bearer` (personal access tokens), `forkhatri` (fk_session cookie), `dev` (development header) |
| Notifications | `app/integrations/notifications/channels.py` | `NotificationChannel.deliver(...)` | in-app inbox (always on), web push (stub), plus outbound webhooks for machines |
| Payments | `app/integrations/payments/gateway.py` | `PaymentGateway` (checkout, webhook verify/parse, refund, status poll) | `razorpay`, `dev_sandbox` |
| Object storage | `app/integrations/storage/` | `ObjectStorage.put(name, data, content_type)` | local filesystem (`/uploads`) |
| URLs and origins | `app/config.py` / `.env` | settings | `WEB_ORIGIN`, `FORKHATRI_ENTRANCE_URL`, `API_PORT` |

The old import paths still work through shims:
- `app/payment_gateway.py` re-exports the payments adapters;
- `app/notifications.py` re-exports the channel classes.

### Identity

`resolve_authz_context()` in `app/identity.py` is the single choke point every route depends on.
- It runs the providers listed in `IDENTITY_PROVIDERS`, in order.
- The first provider that recognises a credential decides who the caller is.
- It then produces an `AuthzContext(member_id, is_operator, auth_method, scopes, credential_id)`.
- Every database transaction runs with `vyapar.authz_context = member_id`, so Postgres row-level security enforces visibility whichever provider identified the caller.

```env
IDENTITY_PROVIDERS=bearer,forkhatri   # production with ForKhatri as host
IDENTITY_PROVIDERS=bearer,dev         # local development
IDENTITY_PROVIDERS=bearer,myhost      # your own host
```

If `IDENTITY_PROVIDERS` is empty, Vyapar keeps its original behaviour: `bearer,dev` when `DEV_MODE=true`, otherwise `bearer,forkhatri`.

Every provider must follow this contract:
- **Return `None`** when there is no credential of its kind, so the next provider gets a turn.
- **Raise** (401, or 503 when the identity service is down) when a credential of its kind is present but invalid. It must never fall through to a weaker provider. This is what keeps a revoked token from silently turning into some default member.
- **Fail closed.** A provider must never fall back to a default member when its upstream is unreachable.
- **Create the member-link row** on first sight, by calling `ensure_member_row(member_id, display_name, phone, language)`.

To add a host, write a provider and register it at startup:

```python
# myhost_identity.py
from fastapi import Request
from app.integrations.identity import register_provider
from app.integrations.identity.base import AUTH_MEMBER_SESSION, ResolvedIdentity, ensure_member_row
from app.integrations.errors import fail, request_language

class MyHostProvider:
    name = "myhost"

    async def resolve(self, request: Request) -> ResolvedIdentity | None:
        session = request.cookies.get("myhost_session")
        if not session:
            return None                                   # not our credential
        member = await verify_with_my_identity_service(session)   # your call
        if member is None:
            raise fail(401, "session_invalid", request_language(request))
        await ensure_member_row(member.id, member.name, member.phone, member.language)
        return ResolvedIdentity(member_id=member.id, auth_method=AUTH_MEMBER_SESSION)

register_provider("myhost", MyHostProvider)
```

The ForKhatri adapter (`forkhatri_session.py`) is the reference implementation. It resolves the cookie against `IDENTITY_SERVICE_INTERNAL_URL/internal/v1/sessions/resolve` using `X-ForKhatri-Service: IDENTITY_SERVICE_NAME` and `X-ForKhatri-Service-Key: IDENTITY_SERVICE_KEY` with the body `{"session_token": ...}`, and a 2-second timeout. The response's `admin_scopes` are mapped onto operator permissions (see `references/imp-admin-console.md`). A successful resolve is cached for 30 seconds and a failed one for 5 seconds. Any failure gives a 503.

### Notifications

Every notification goes through `app/notifications.py`:
- `send_notification()` for one member;
- `notify_member()` for one member, rendered in their own language;
- `notify_interaction_party()` for the other party of an enquiry, review or partnership.

The in-app inbox row is always written, and it is idempotent by `idempotency_key`.

To push notifications through your own service (SMS, WhatsApp, email, a platform push service), implement `NotificationChannel.deliver(conn, member_id, title, body, link)` and add it next to `InAppChannel`.

For machine consumers, use outbound webhooks instead (Part 2).

### Payments

`get_gateway()` returns the adapter named by `PAYMENT_GATEWAY`. To use a different payment provider, implement the `PaymentGateway` protocol:
- `create_checkout`: a hosted page, so card data never touches Vyapar;
- `verify_webhook`;
- `parse_webhook`, returning a `GatewayEvent`;
- `refund`;
- `fetch_outcome`.

Then return your adapter from `get_gateway()` for your `PAYMENT_GATEWAY` value. The Commercial logic never calls a gateway directly.

### Object storage

`app/integrations/storage` defines `ObjectStorage.put(name, data, content_type) -> url`. The shipped `LocalFilesystemStorage` matches today's upload behaviour exactly.

A host with S3, GCS or its own media service calls `set_storage(MyStorage())` at startup.

One step is still to do. The upload route (`app/routers/uploads.py`) belongs to the service-layer workstream and still writes files directly. Switching its one write to `get_storage().put(...)` is the remaining change.

### URLs

| Setting | Meaning |
|---|---|
| `WEB_ORIGIN` | The only origin CORS allows, with credentials |
| `FORKHATRI_ENTRANCE_URL` | Where the web app sends a signed-out person (host-specific) |
| `API_PORT` | Vyapar's API port (8011 in development) |

The web app's host adapter (`vyapar-web`, `HostProvider`) holds its own host URLs.

---

## Part 2: building on Vyapar (agents, scripts, other systems)

### Authentication: personal access tokens

An agent acts **on behalf of one member** with a scoped, revocable credential that the member created.

| Call (member session only) | Purpose |
|---|---|
| `GET /v1/integrations/scopes` | Scopes, with localized descriptions |
| `POST /v1/integrations/tokens` `{name, scopes, expires_in_days}` | Create a token. The `vyp_...` value is returned **once**. |
| `GET /v1/integrations/tokens` | List tokens: prefix, scopes, status, created, expires, last used. The value is never shown again. |
| `DELETE /v1/integrations/tokens/{id}` | Revoke. The next request with the token gets a 401. |

Tokens expire after 90 days by default, and after at most 365 days. A member can hold at most 20 active tokens.

Use a token like this:

```bash
curl http://localhost:8011/v1/opportunities/feed -H "Authorization: Bearer vyp_..."
curl http://localhost:8011/v1/integrations/me    -H "Authorization: Bearer vyp_..."   # who am I, which scopes
```

| Scope | Grants |
|---|---|
| `read` | Every `GET` a member can make: feed, opportunities, profiles, search, enquiries, activity, notifications |
| `opportunities:write` | Writes under `/v1/opportunities`: post, edit, publish, pause, save, hide |
| `listings:write` | Writes under `/v1/listings`: profiles and saving profiles. Verification documents and phone OTP are excluded. |
| `enquiries:write` | Writes under `/v1/enquiries`: apply, enquire, reply, accept, close |
| `reviews:write` | `POST /v1/reviews` |
| `partnerships:write` | Writes under `/v1/partnership-requests` |
| `notifications:write` | Mark notifications as read |

Uploads (`POST /v1/uploads`) accept any of `opportunities:write`, `listings:write` or `enquiries:write`.

Some actions are never available to a token, whatever its scopes. The policy is default-deny, in `app/integrations/identity/scopes.py`. A token can never do these:
- operator tools (`/v1/admin`, `/internal`) and development tools (`/v1/dev`);
- payments, promotions, campaigns, plans and workspace management;
- privacy settings, data export and account deletion, and legal acceptance;
- verification documents and contact OTP;
- reports and appeals;
- managing tokens or webhooks.

A token never carries operator powers, even when an operator created it. A write to an area without a scope rule is refused.

Security properties:
- Tokens are stored as SHA-256 hashes, never in plaintext. The table is `vyapar_integration.access_tokens`, and its row-level security lets a member see only their own tokens.
- Authentication looks up the hash through the SECURITY DEFINER function `resolve_access_token()`, which returns only unrevoked, unexpired tokens of live members.
- Requests made with a token still run under the member's row-level-security context. A token can never see more than the member can.
- **Every write made with a token is audited** in `vyapar_integration.audit_events`, including refused writes. The action is `api_token.<method>`, and the details record `access_token_id`, the route, the status and the scopes. Creating and revoking a token is audited too.

Errors use one envelope, and the code is also sent in the `X-Vyapar-Error-Code` header:

```json
{"detail": "<localized message>",
 "error": {"code": "scope_required", "message": "<localized>", "details": {"scope": "opportunities:write"}}}
```

| Code | Status | Meaning |
|---|---|---|
| `token_invalid` | 401 | Unknown, revoked or expired token. The response also carries `WWW-Authenticate: Bearer`. |
| `scope_required` | 403 | The token lacks the scope this request needs |
| `not_available_to_tokens` | 403 | This area is member-only |
| `member_session_required` | 403 | Token and webhook management needs the member's own session |

Send `X-Vyapar-Language: hi` or `X-Vyapar-Language: te` to get localized messages and labels.

### Idempotency

Send `Idempotency-Key: <unique string, 1 to 200 characters>` on any `POST`:

| Situation | Result |
|---|---|
| First request | Runs normally. A **2xx** response is stored for 24 hours (`IDEMPOTENCY_TTL_HOURS`). |
| Same key, same method, path and body | The stored response is replayed byte for byte, with the header `Idempotent-Replayed: true`. Nothing runs twice. |
| Same key, different body | `422 idempotency_key_reused` |
| Same key while the first request is still running | `409 idempotency_in_progress`, with `Retry-After: 2` |
| First response was 4xx or 5xx | The key is released, so the caller can fix the request and retry with the same key |

Keys are scoped per caller: the member plus the credential (each token, or the member's session). One caller's key can never replay another caller's response.

The store is `vyapar_platform.idempotency_key`, which has member-scoped row-level security. Expired rows are purged hourly.

### Webhooks

Subscribe a URL to domain events.

| Call (member session only) | Purpose |
|---|---|
| `GET /v1/integrations/webhooks/events` | Event catalogue, with localized descriptions |
| `POST /v1/integrations/webhooks` `{url, event_types, description?, all_events?}` | Create a subscription. The signing secret `whsec_...` is returned **once**. `event_types` can be `["*"]`. |
| `GET /v1/integrations/webhooks` | List subscriptions |
| `DELETE /v1/integrations/webhooks/{id}` | Delete. The delivery log is kept. |
| `POST /v1/integrations/webhooks/{id}/test` | Send a signed `ping` now and return the outcome |
| `GET /v1/integrations/webhooks/{id}/deliveries` | Delivery log: status, attempts, last HTTP code or error |

A member's subscription receives only **events about that member**:
- their own opportunities and profiles;
- enquiries they received;
- replies to them;
- partnership requests and reviews that involve them.

An operator can set `all_events: true` to receive every event, including the operator events `opportunity.queue_decided` and `taxonomy.changed`.

**Events:**

| Type | When it is sent |
|---|---|
| `opportunity.published` | An opportunity goes live |
| `opportunity.reactivated` | A paused or stale opportunity is live again |
| `opportunity.paused`, `.stale`, `.expired`, `.closed`, `.removed` | An opportunity leaves the live state |
| `opportunity.queue_decided` | Operator only |
| `listing.published` | A profile goes live |
| `listing.suspended`, `listing.archived` | A profile is suspended or archived |
| `listing.verification_verified`, `_revoked`, `_expired` | A profile's verification changes |
| `taxonomy.changed` | Operator only |
| `enquiry.received` | Sent to the provider |
| `enquiry.replied` | The provider answered. Sent to the asker. |
| `enquiry.message_received` | The asker followed up. Sent to the provider. |
| `enquiry.state_changed` | An enquiry changes status |
| `partnership.requested`, `.accepted`, `.declined`, `.withdrawn`, `.restricted`, `.closed` | A partnership request changes |
| `review.published`, `.disputed`, `.hidden`, `.removed` | A review changes |

How events are produced:
- Events come from the transactional outbox: `vyapar_listings`, `vyapar_opportunities`, `vyapar_commercial`, `vyapar_enquiries` and `vyapar_reviews` each have an `outbox_event` table.
- Migration 016 adds triggers on the owning tables, so an event commits in the same transaction as the change it describes. That holds whether the change came from the web app, an agent, an operator or a background job.
- Payloads contain **identifiers and states only**, never message text or contact details. To get details, call the API with your own token.

**Delivery:**

```http
POST <your url>
Content-Type: application/json
User-Agent: Vyapar-Webhooks/1.0
X-Vyapar-Event: enquiry.received
X-Vyapar-Event-Id: evt_enquiry_42
X-Vyapar-Delivery: 1234
X-Vyapar-Signature: t=1790000000,v1=5f2c...e9

{"id":"evt_enquiry_42","type":"enquiry.received","created_at":"2026-09-21T16:19:06Z",
 "data":{"id":"<enquiry uuid>","sender_id":"m_...","provider_id":"m_...","listing_id":null,
         "opportunity_id":"<uuid>","action_type":"apply","state":"open"}}
```

How delivery behaves:
- Any 2xx response counts as delivered.
- Anything else is retried after 30 seconds, 2 minutes, 10 minutes, 1 hour and 6 hours, up to 6 attempts. After that the delivery is marked `failed`.
- After 25 failures in a row, the subscription is switched off.
- Deliveries never follow redirects. Outside development, set `WEBHOOK_ALLOW_PRIVATE_TARGETS=false`: targets must then be `https` and must not resolve to private, loopback or link-local addresses. This is checked when the subscription is created and again at every delivery.
- Deduplicate on `X-Vyapar-Event-Id`, because a retry after a timeout can arrive twice.

**Verify the signature.** Compute HMAC-SHA256 with your secret over `"<t>." + raw body`, compare in constant time, and reject old timestamps:

```python
import hashlib, hmac, time

def verify(secret: str, raw_body: bytes, header: str, tolerance: int = 300) -> bool:
    parts = dict(p.split("=", 1) for p in header.split(","))
    t = int(parts["t"])
    if abs(time.time() - t) > tolerance:
        return False
    expected = hmac.new(secret.encode(), f"{t}.".encode() + raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, parts["v1"])
```

```js
import crypto from "node:crypto";
export function verify(secret, rawBody /* Buffer */, header, tolerance = 300) {
  const parts = Object.fromEntries(header.split(",").map((p) => p.split("=")));
  if (Math.abs(Date.now() / 1000 - Number(parts.t)) > tolerance) return false;
  const expected = crypto.createHmac("sha256", secret).update(`${parts.t}.`).update(rawBody).digest("hex");
  return crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(parts.v1 ?? ""));
}
```

Always verify over the **raw** bytes, before any JSON parsing.

Signing secrets are stored with AES-256-GCM encryption under `INTEGRATION_SECRET_KEY`. That key is a deployment secret and is never stored in the database.

Dispatch runs inside the API process, every `WEBHOOK_DISPATCH_INTERVAL_SECONDS` (10 seconds by default). Several API processes can run it safely at the same time, because fan-out locks its cursors and deliveries are claimed with `SKIP LOCKED`.

### The MCP server (AI agents)

`vyapar-mcp/` is a standalone Model Context Protocol server. It exposes the member-facing operations as typed tools for Claude Desktop, Claude Code or any MCP client:
- the feed, opportunity detail and why an opportunity was recommended;
- similar opportunities and matching profiles;
- save and hide;
- apply or enquire, and post an opportunity;
- enquiries and replies;
- activity;
- business and professional search, profiles and similar profiles;
- reviews;
- notifications.

It talks to Vyapar only through this REST API, with a personal access token (`VYAPAR_API_URL`, `VYAPAR_TOKEN`). It shares no code and no database with the core.

Setup and configuration snippets are in `vyapar-mcp/README.md`.

### Configuration reference (new in IMP37)

| Setting | Default | Meaning |
|---|---|---|
| `IDENTITY_PROVIDERS` | *(derived from `DEV_MODE`)* | Ordered provider list |
| `ACCESS_TOKEN_DEFAULT_DAYS` / `ACCESS_TOKEN_MAX_DAYS` | 90 / 365 | Token lifetime |
| `ACCESS_TOKEN_MAX_ACTIVE_PER_MEMBER` | 20 | Active token limit per member |
| `INTEGRATION_SECRET_KEY` | `CHANGE_ME_...` | Encrypts webhook signing secrets. **Set it in production.** |
| `WEBHOOK_ALLOW_PRIVATE_TARGETS` | `true` | **Set to `false` in any shared deployment.** |
| `WEBHOOK_DISPATCH_INTERVAL_SECONDS` | 10 | Dispatch loop interval |
| `WEBHOOK_TIMEOUT_SECONDS` | 5 | Timeout for each delivery attempt |
| `WEBHOOK_MAX_ATTEMPTS` | 6 | Attempts before a delivery is marked failed |
| `WEBHOOK_DISABLE_AFTER_FAILURES` | 25 | Consecutive failures before a subscription is switched off |
| `WEBHOOK_MAX_PER_MEMBER` | 10 | Subscription limit per member |
| `IDEMPOTENCY_TTL_HOURS` | 24 | How long a response is kept for replay |

### Database (migrations 015 and 016)

- **015:** adds `vyapar_integration.access_tokens` with self-only row-level security and no DELETE grant (revoking is an update). It also adds `resolve_access_token()` and `vyapar_platform.purge_expired_idempotency_keys()`.
- **016:** adds `vyapar_enquiries.outbox_event`, `vyapar_reviews.outbox_event`, the domain-event triggers, and the tables `vyapar_integration.webhook_subscriptions`, `webhook_deliveries` and `webhook_cursors`. Subscriptions and deliveries are visible to their owner or to the dispatcher role; cursors only to the dispatcher role.
