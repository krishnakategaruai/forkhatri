# Vyapar: Admin & Governance Console contract (ADR-012, TR-PLAT-01)

This is Vyapar's (MOD01) side of the shared console. It follows the generic
contract in `modules/MOD02-milavn/07-tech-reqs.md`, TR-PLAT-01. Vyapar ships:

- a manifest;
- six federated views;
- a person summary.

The console shell renders them. It never touches Vyapar data directly.

The wrappers add no tables and no business rules. Two things come from the existing services:

- **Queue membership:** the existing list functions decide which items are in each queue.
- **Actions:** the existing decision functions carry them out, with their notifications, outbox events and audit rows unchanged.

| Piece | Path |
|---|---|
| Routes | `vyapar-service/app/routers/admin_console.py` (one `include_router` line in `app/main.py`) |
| Wrappers, models, member summary | `vyapar-service/app/services/admin_console.py` |
| Host scope mapping | `vyapar-service/app/integrations/identity/admin_scopes.py` |
| ForKhatri resolve adapter (fixed contract) | `vyapar-service/app/integrations/identity/forkhatri_session.py` |
| Dev scope override | `vyapar-service/app/integrations/identity/dev_header.py` |
| Internal bridge authentication | `vyapar-service/app/integrations/internal_auth.py` |
| DB: session permissions | `07a-db-implementation/migrations/024-session-admin-permissions.sql` (also appended to `schema.sql` §17) |
| Strings (en/hi/te) | `vyapar-service/app/i18n/locales/{en,hi,te}/admin_console.json` |
| End-to-end check | `vyapar-service/scripts/check_admin_console.py` |

All paths below are relative to the Vyapar API base URL.

## 1. Access

Two sources grant access, and either one is enough:

1. **The member row.** `vyapar_identity.members.is_operator` and `operator_permissions`, as before.
2. **The platform session.** The identity service's `POST /internal/v1/sessions/resolve` returns `admin_scopes`. The ForKhatri adapter maps them in `admin_scopes.py`:

| Host scope | Vyapar permissions |
|---|---|
| `vyapar.moderate` | `moderation`, `content` |
| `vyapar.verify` | `verification` |
| `vyapar.commercial` | `commercial` |
| `vyapar.analytics` | `analytics` |

Other modules' scopes (for example `milavn.moderate`) and unknown scopes grant nothing.

**How session permissions travel:**

1. `AuthzContext.session_permissions` carries them.
2. `app/db.py get_conn()` writes them next to `vyapar.authz_context` in the same transaction, using `set_config(..., true)`. The value is `vyapar.authz_permissions = {"member_id": "...", "permissions": [...]}`.
3. Migration 024 adds `vyapar_identity.session_permissions()`. It returns the permissions only while `authz_context` is that same member, so a code path that switches context never carries them across.
4. Migration 024 also extends `is_operator(permission)` with the same signature. Every existing RLS policy therefore honours session permissions without change.
5. The route chokepoints union session permissions into the member-row check through `identity.with_session_permissions`. They do this in `trust_safety`, `verification`, `admin_ops`, `admin_commercial` and `commercial`.

**Where scopes can come from:**

- **Production:** only the identity service's resolve response. No header, cookie or body is ever read for them.
- **Development:** the dev provider accepts `X-Dev-Admin-Scopes: vyapar.moderate,vyapar.verify`, but only while `DEV_MODE=true`. The header is ignored on a platform session and on a bearer token.

**Personal access tokens** are refused on every `/vyapar/admin/*` route with `403 not_available_to_tokens`, before any route code runs. `scopes.py` lists the prefix as token-forbidden.

**Without permission:** a caller whose permissions allow no view gets `403` on everything, including the manifest. The error envelope is:

```json
{"detail": "You don't have access to this part of the Admin Console.",
 "error": {"code": "admin_console_permission_required", "message": "You don't have access to this part of the Admin Console.",
           "details": {"i18n_key": "admin_console.error.permissionRequired"}}}
```

**Other error codes:**

| Code | Status | Meaning |
|---|---|---|
| `item_not_found` | 404 | No such item |
| `action_not_available` | 409 | The item's state no longer offers the action |
| `reason_required` | 422 | The action needs a reason code |
| `reason_not_allowed` | 422 | The reason code is not in the action's list |
| `validation_error` | 422 | The request body is malformed |

## 2. Manifest: `GET /vyapar/admin/manifest` (`getVyaparAdminManifest`)

The manifest lists only the views the caller may open. Titles follow `X-Vyapar-Language` or `Accept-Language` (en/hi/te).

```json
{
  "module_id": "vyapar",
  "views": [
    {"view_id": "moderation", "title": "Reported content", "nav_group": "moderation",
     "required_permission_scope": "vyapar.moderate",
     "list_endpoint": "/vyapar/admin/moderation",
     "detail_endpoint": "/vyapar/admin/moderation/{item_id}",
     "action_endpoints": ["/vyapar/admin/moderation/{item_id}/actions/{action_id}"]},
    {"view_id": "verification", "title": "Business verification", "nav_group": "moderation", "required_permission_scope": "vyapar.verify", "...": "..."},
    {"view_id": "opportunities", "title": "Opportunity review", "nav_group": "moderation", "required_permission_scope": "vyapar.moderate", "...": "..."},
    {"view_id": "appeals", "title": "Appeals", "nav_group": "moderation", "required_permission_scope": "vyapar.moderate", "...": "..."},
    {"view_id": "disputes", "title": "Disputes", "nav_group": "disputes", "required_permission_scope": "vyapar.moderate", "...": "..."},
    {"view_id": "commercial", "title": "Orders & refunds", "nav_group": "commercial", "required_permission_scope": "vyapar.commercial", "...": "..."}
  ]
}
```

| view_id | Item types | Queue source | Actions (dispatched to) |
|---|---|---|---|
| `moderation` | `moderation_case` | `trust_safety.list_moderation_queue`, excluding review disputes | `dismiss`, `limit`, `remove`, `request_verification` (listings), `suspend` (`duration_days`, default 30) → `decide_moderation_case` |
| `verification` | `verification_record` | `verification.list_verification_queue` | `verify`, `reject`, `needs_clearer_copy` → `approve_verification` / `reject_verification` / `request_clearer_verification_copy` |
| `opportunities` | `opportunity_review`, `stale_opportunity` | `admin_ops.list_opportunity_review_queue` + `list_stale_queue` | `approve`, `return`, `remove` → `decide_opportunity_review`; `remind`, `expire` → `bulk_stale_action` (one id) |
| `appeals` | `appeal` | `trust_safety.list_appeals` | `upheld`, `overturned` → `decide_appeal` |
| `disputes` | `contract_dispute`, `review_dispute` | `contracts.list_disputes_for_operators(state="open")` + review-dispute cases | contract: `resolved_client`, `resolved_provider`, `closed` → `resolve_dispute` (notes stored on the dispute); review: `keep` / `hide` / `remove` → `decide_moderation_case` (`dismiss` / `limit` / `remove`) |
| `commercial` | `promotion_order`, `plan_order`, `campaign_order` | `admin_commercial.list_commercial_orders` (50 newest per kind) | `reject` (boosts) → `commercial.reject_promotion`; `refund` (optional `amount_paise`, default: everything not yet refunded) → `admin_commercial.process_refund` |

**Priority:**

- **urgent:** critical severity, or a job seeker was asked for money (`asked_for_money`).
- **high:** high severity, escalated or overdue; an appeal that is overdue or delayed; a verification past 3 business days; a contract dispute with money held; an order whose last refund failed.
- **normal:** everything else.

**`due_at`** comes from the existing timers:

- the moderation case's `target_due_at` (4 h / 24 h / 72 h / 7 d by severity);
- the appeal's `due_at` (7 days);
- the verification queue's 3-business-day target (TR047).

Other items have no `due_at`.

## 3. List: `GET /vyapar/admin/{view}` (`listVyaparAdmin<View>Items`)

The list returns `AdminQueueItem[]`:

- **Work queues** are sorted by priority, then `due_at`, then oldest first.
- **Orders** are sorted by priority, then newest first.

`summary_text`, `subject_title`, `reason` and `status_label` are human words in the caller's language, never raw ids. `item_id` is opaque: `<item_type>:<uuid>`.

```json
[
  {"item_id": "moderation_case:6c1d0e0a-8a51-4b8e-9d0f-2f7f0f1c9a11", "module_id": "vyapar",
   "item_type": "moderation_case", "item_type_label": "Reported content",
   "submitted_at": "2026-09-29T09:14:03.201+00:00", "priority": "urgent",
   "status": "open", "status_label": "Open",
   "summary_text": "Opportunity “Counter helper for electrical spares shop” was reported 1 time(s): Asked a job seeker for money.",
   "subject_title": "Counter helper for electrical spares shop",
   "reason": "Asked a job seeker for money",
   "due_at": "2026-09-30T09:14:03.201+00:00", "overdue": false,
   "deep_link": "/opportunities/0b6e…"}
]
```

`deep_link` is the web-app path of the thing under review, or `null`.

## 4. Detail: `GET /vyapar/admin/{view}/{item_id}` (`getVyaparAdmin<View>Item`)

The console treats `case_detail` as opaque, except for `history`, whose entries are `{action, label, by, notes, at}`. `action` is a stable code, `label` is in the caller's language, and `by` is a person's name. A reporter is always shown as "A member (kept private)". `available_actions` is empty once the item has been decided.

```json
{
  "item_id": "moderation_case:6c1d0e0a-…",
  "item": {"…": "the AdminQueueItem"},
  "case_detail": {
    "history": [
      {"action": "case_opened", "label": "Case opened", "by": "Vyapar (automatic)", "notes": null, "at": "2026-09-29T09:14:03+00:00"},
      {"action": "reported", "label": "Reported: Asked a job seeker for money", "by": "A member (kept private)",
       "notes": "When I called, they said I must pay ₹1,500 as a uniform and training deposit before joining.", "at": "2026-09-29T09:14:03+00:00"}
    ],
    "object_kind": "opportunity", "object_kind_label": "Opportunity", "object_title": "Counter helper for electrical spares shop",
    "about_member": "Rahul Chadha", "severity": "high", "source": "report", "reporter_count": 1, "distribution_limited": true,
    "evidence": [{"reason": "asked_for_money", "reason_label": "Asked a job seeker for money", "text": "…", "attachments": [], "at": "…"}],
    "prior_cases": []
  },
  "available_actions": [
    {"action_id": "dismiss", "label": "No violation, close the report", "requires_reason": true,
     "reason_codes": ["no_violation"], "reason_labels": {"no_violation": "No violation found"}},
    {"action_id": "limit", "label": "Limit who sees it", "requires_reason": true,
     "reason_codes": ["scam_confirmed", "asked_for_money", "fake_listing", "…"], "reason_labels": {"asked_for_money": "Asked applicants for money", "…": "…"}},
    {"action_id": "remove", "label": "Remove it", "requires_reason": true, "reason_codes": ["…"], "reason_labels": {"…": "…"}},
    {"action_id": "suspend", "label": "Suspend the member's posts", "requires_reason": true, "reason_codes": ["…"], "reason_labels": {"…": "…"}}
  ]
}
```

What `case_detail` carries in the other views:

- **Verification:** only the masked identifier (never the encrypted one), the document label, the image and the days pending.
- **Commercial:** the charged, refunded and refundable amounts (₹ text and paise) and the order's state changes.
- **Contract disputes:** the parties, the reason, the milestone and the held amount.

## 5. Action: `POST /vyapar/admin/{view}/{item_id}/actions/{action_id}` (`actOnVyaparAdmin<View>Item`)

Request body:

```json
{"notes": "Deposit request confirmed by the caller; limiting while the poster responds.", "reason_code": "asked_for_money"}
```

Optional fields:

- `duration_days` (1–365), for `suspend` only.
- `amount_paise`, for `refund` only.

The response is the updated `AdminQueueItem`:

```json
{"item_id": "moderation_case:6c1d0e0a-…", "module_id": "vyapar", "item_type": "moderation_case", "priority": "urgent",
 "status": "actioned", "status_label": "Action taken", "summary_text": "…", "subject_title": "…", "reason": "…",
 "due_at": "…", "overdue": false, "item_type_label": "Reported content", "submitted_at": "…", "deep_link": "/opportunities/…"}
```

**How actions are audited:**

- The existing service writes its own audit rows unchanged, for example `opportunity_queue_*`, `refund_processed` and `contract_dispute_resolved`.
- The console also writes one `vyapar_integration.audit_events` row per action, as TR-PLAT-01 §4 requires:
  - `action = "admin_action.vyapar.<view_id>"`;
  - `object_kind = item_type`;
  - `reason_code`;
  - `details = {action_id, notes, via: "admin_console", auth_method, permission_source: "member" | "session"}`.
- These rows are read back into `history`. The older endpoints had no field for free-text notes, so this is where the notes live.

## 6. Person summary: `GET /vyapar/admin/members/{member_id}/summary` (`getVyaparAdminMemberSummary`)

- Needs any operator permission; otherwise 403.
- Returns 404 when the person has no Vyapar account.
- Facts follow the caller's permissions: "Open reports" needs `moderation`, and "Paid to Vyapar" needs `commercial`.
- Labels are localized.

```json
{
  "module_id": "vyapar",
  "plan": {"tier": "workspace_monthly", "name": "Business Workspace · monthly", "status": "active", "renews_at": "2026-10-14T00:00:00+00:00"},
  "facts": [
    {"label": "Member since", "value": "14/09/2026"},
    {"label": "Business listings", "value": "1"},
    {"label": "Verification", "value": "1 verified, 0 waiting"},
    {"label": "Open opportunities", "value": "3"},
    {"label": "Running boosts", "value": "0"},
    {"label": "Running campaigns", "value": "0"},
    {"label": "Active contracts", "value": "1"},
    {"label": "Open reports about this member", "value": "0"},
    {"label": "Paid to Vyapar so far", "value": "₹0"}
  ],
  "flags": [{"code": "verification_pending", "label": "Verification waiting for a decision"}],
  "deep_link": null
}
```

- **`plan`:** `null` when there is no active or paused Business Workspace plan. `status` is `active`, `paused` or `cancelling` (ends at the end of the period).
- **Flag codes:** `open_reports`, `content_suspended`, `appeal_open`, `verification_pending`, `verification_rejected`, `plan_paused`, `plan_ending`, `payment_failed`, `contract_disputed`, `operator`.

## 7. Platform integration fixes made with this work

- **Resolve contract corrected** in `forkhatri_session.py`, checked against `platform/identity-service/app/api/routes/internal.py`:
  - Vyapar now sends `X-ForKhatri-Service: $IDENTITY_SERVICE_NAME` and `X-ForKhatri-Service-Key: $IDENTITY_SERVICE_KEY` with the body `{"session_token": …}`. It previously sent `X-Service-Key` and `session_cookie`, which the identity service rejects.
  - It reads `preferred_language` and `phone_e164`.
  - A rejected service credential now answers 503 and is logged. It is no longer treated as a bad session.
  - `IDENTITY_SERVICE_NAME` is new in `.env` and `.env.example`.
  - The local `.env` now points at `http://127.0.0.1:8100` with the platform's development key. Use `127.0.0.1`, not `localhost`: on Windows, `localhost` tries IPv6 first and costs 2 seconds, which trips the 2-second fail-closed timeout.
- **`GET /internal/v1/dashboard-summary/{listing_id}` is authenticated:**
  - It needs `X-ForKhatri-Service-Key`, the same shared key as the Milavn and Mangaly internal routes.
  - A request that came through the public edge (it carries `X-Forwarded-For`) gets 404.
  - It runs on a connection with no member context (`get_internal_conn`). It used to resolve a member session.
- **Operators can approve queued opportunities:** `admin_ops.decide_opportunity_review` could not approve an opportunity for an operator. It called the poster-only `_lifecycle_action`, which answers 404 to anyone else. It now makes the same transition itself.
- **Verification-only operators can decide:** a new RLS policy, `listings_verification_operator_update` (migration 024), lets a `verification`-only operator update the listing's verification label. Before this, verify, reject and clearer-copy failed under RLS for anyone without `content`. Seeded operators hold both permissions, which had hidden the gap.

- **Samaj admin got 403 on first contact (bug report, 2026-09-29).**
  - *Cause:* the live dev API ran with `DEV_MODE=true` and the default provider chain `bearer,dev`. The ForKhatri provider never ran. The dev provider ignored the `fk_session` cookie and turned Ramesh Khatri (`samaj-president`, holding `vyapar.moderate`) into `DEV_DEFAULT_MEMBER_ID` (`m_krishna`), who has no permissions.
  - *Ruled out:* scopes were not dropped, no member row was created without scopes, no timeout fell back to a default, and the permissions setting was not bound to the wrong member.
  - *Fix, provider chain:* the dev `.env` now sets `IDENTITY_PROVIDERS=bearer,dev,forkhatri`.
  - *Fix, dev provider:* `dev_header.py` steps aside when no dev member was chosen (no `X-Dev-Member-Id` header or cookie), the request carries `fk_session`, and `forkhatri` is configured. The platform session is then resolved normally, with `admin_scopes`.
  - *Unchanged:* the web app's dev switcher always sends `X-Dev-Member-Id`, so it still wins.
  - *First contact:* the member row is provisioned through `ensure_member`, with no operator flags stored. Access comes from the session's scopes.

## 8. Test

Run the check against private instances on free ports; the owner's 8011 is never used:

```
IDENTITY_PROVIDERS=bearer,dev .venv/Scripts/python -m uvicorn app.main:app --port 8911   # dev-only instance
.venv/Scripts/python -m uvicorn app.main:app --port 8912   # .env: bearer,dev,forkhatri (like live 8011)
.venv/Scripts/python scripts/check_admin_console.py --api http://127.0.0.1:8911 --forkhatri-api http://127.0.0.1:8912
```

Result on 2026-09-29: **91/91 checks passed**, and the leftover sweep was clean. The check covers:

- a non-operator getting 403;
- the seeded operator (`m_neha_ops`);
- dev scopes, including a session-scoped moderator who both reads and decides through RLS;
- token refusal and internal-bridge authentication;
- one real item walked through list, detail and an action in every view;
- the person summary;
- real platform sessions resolving through the corrected contract: `milavn-moderator` (no Vyapar scope, so 403) and `samaj-president` (console on first contact with only the cookie, and the member row provisioned normally);
- an explicit dev member still winning over the platform cookie.

Everything created is deleted, and the seeded rows the check touched are restored.
