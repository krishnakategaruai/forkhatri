# IMP — Backend workstream D: contracts and milestone payments (2026-09-28)

## What was built

A client (the side that pays) and a provider (the side that does the work) can now turn an accepted enquiry into a contract.

- **Fixed-price contracts** are paid milestone by milestone. The client funds a milestone through the existing Payment Bridge, the provider submits the work, and the client approves it (releasing the money) or sends it back with a note. A submitted milestone releases itself after 14 days of client silence.
- **Hourly contracts** are paid from weekly timesheets, one per Monday-to-Sunday week. A weekly hours cap applies and no screenshots are taken. When the client approves a week, it becomes one milestone that is released the moment it is paid.
- **Disputes** give either party a simple in-product mediation stage. A moderation operator records the outcome; there is no arbitration.
- **Completion:** when the contract completes, the source enquiry becomes `resolved` and both parties receive review invites through the existing reviews service.

**Who is the client (who pays).** One function, `contract_parties()` in `services/contracts.py`, decides it, and the web app and the MCP server read the answer from `getContractRoles`, never working it out themselves.
- **A response to a post** (a proposal, quote, application or registration: the enquiry has an `opportunity_id`): **the poster pays.** For these enquiries `enquiries.provider_id` is the poster, set when the enquiry was created.
- **A request to a profile** (a listing enquiry, a price request or a package request: no `opportunity_id`): **the sender pays.**
- The enquiry must be `in_progress`, meaning its receiving side accepted it.

*Re-applied 2026-09-30.* At 2026-09-29 17:46, a file restore outside this workstream reset every workstream D file to its state before the fix (commit `0f1825d`), and 8011 was then restarted on that code. Lost with it: the payer rule, `getContractRoles`, the MCP tool and these doc lines. The payment notice and the commit-before-response change survived. The fix itself had never been committed.
- **What that cost:** two contracts were created on the live API with the payer backwards: Suresh's price request on Meena's evening-delivery post (post 110, enquiry `ad08774f…`).
  - `4ffd3bbe…` is already cancelled.
  - **`e0aaaf62…` is still `proposed` with Suresh as the client.**
- **Current state:** the code is fixed and 8011 has been restarted, so `getContractRoles` now names Meena as the client. It reports `duplicate_contract` until that wrong contract is cancelled; Suresh or Meena can cancel it with `cancelContract`, after which Meena can create the correct one. It was left as it is because it is another agent's live test data.
- **To stop this happening again:** commit these files so another restore cannot reset them.

*Fixed 2026-09-29 (CRITIQUE-2026-09-28, N1, blocker):* the first rule only treated `apply` as poster-pays, so after Shreya accepted Priya's proposal, Priya (the freelancer) was offered "Start a contract" as the payer and Shreya got nothing. On 2026-09-29 no contract had been saved with the payer backwards (but see the 2026-09-30 note above). The web app's own copy of the rule (`ContractEntry.tsx`, `isClientOf`) belongs to the frontend workstream and should switch to `getContractRoles`.

**Money is a ledger, not escrow (BLOCKER-01, `09-implementation.md`).** Funding creates a `payment_orders` row of the new kind `contract_milestone` through `services/payments.create_payment_order()`, which is the same path boosts use (dev sandbox today). On payment success, `contract_ledger` records `held`. On approval it records `released`, and a provider notification goes out. A cancellation or a dispute resolved for the client records `refunded` and calls the gateway refund.
- No money reaches a provider from this code. Without a merchant account there is no payout rail.
- When the account exists, a payout adapter (Razorpay Route or a nodal account) plugs in behind the `released` ledger entry. No table changes.

**Platform fee.** `CONTRACT_PLATFORM_FEE_BPS` defaults to `0`, because Vyapar takes no cut from workers. The rate is copied onto each contract when it is created, and a `fee` ledger entry is written only when it is above 0. A rate change never alters a contract that already exists.

### Files (all new, except where noted)

| File | What |
|---|---|
| `07a-db-implementation/migrations/021-contracts-milestones.sql` | See the migration breakdown below. |
| `07a-db-implementation/schema.sql` (edited) | Section 13, `vyapar_contracts`, appended; `payment_orders.kind` check updated. |
| `vyapar-service/app/services/contracts.py` | All rules, typed models, the auto-release pass. Own `ContractSettings` (no edit to `config.py`). |
| `vyapar-service/app/routers/contracts.py` | Thin router, 21 operations. |
| `vyapar-service/app/main.py` (edited) | One import and `include_router` line, at the end. |
| `vyapar-service/app/i18n/locales/{en,hi,te}/contracts.json` | Errors and labels. |
| `vyapar-service/app/i18n/locales/{en,hi,te}/notifications.json` (edited) | 13 new templates added; existing keys untouched. |
| `vyapar-service/scripts/check_contracts.py` | End-to-end check with full cleanup. |

What migration 021 adds:
- **New schema `vyapar_contracts`** with six tables: `contracts`, `contract_milestones`, `contract_ledger`, `contract_events` (the audit timeline), `contract_disputes` and `timesheets`.
- **RLS on every table:**
  - who can read: the two parties, `is_operator('moderation')`, and `service_role = 'dispatcher'`;
  - child tables go through `is_party()`.
- **`payment_orders.kind` gains `contract_milestone`.**
- **Payment trigger:** `payment_orders_contract_milestone` handles success (`funded`, `held` in the ledger, the `milestone.funded` event, the provider notification), failure and refund in the same transaction as the Payment Bridge's own update. Webhook, status poll and sandbox all need no change.
- **`notify_party()`** works like migration 005's `notify_interaction_party`, scoped to contracts.
- **`vyapar_reviews.issue_invites()` is extended** so that a completed contract qualifies its enquiry. Invites are still issued once per party.

**Domain events** go to `vyapar_enquiries.outbox_event`, which the webhook fan-out already reads. A contract is the continuation of an enquiry between the same two members. The events are:
- `contract.proposed`, `contract.accepted`, `milestone.funded`, `milestone.submitted`, `milestone.approved` and `contract.completed`;
- plus `contract.cancelled` and `contract.disputed`.

Payloads carry ids, states and amounts only, plus `audience = [client, provider]`.

### Verification
- `python -c "import app.main"` passes. All 21 operations are in `openapi.json` with operation ids.
- **Test run:** migration 021 applied with `psql -f` as `vyapar_owner`, per the README. The check ran on a private uvicorn on port 8017, which was checked free first and killed afterwards by its own PID.
- **Command:** `.venv/Scripts/python scripts/check_contracts.py --api http://127.0.0.1:8017`. Result: **92/92 checks pass** (two consecutive runs, 2026-09-30), with no tracebacks in the server log.
- **Who pays (added for N1):**
  - Shreya publishes a freelance project through the API (draft, confirm, budget, publish), and Kavita proposes on it. Priya was used until her privacy and terms acceptances disappeared from the development database, which happened outside this workstream.
  - Before acceptance, `getContractRoles` says Shreya is the client (`poster_pays`) and blocks creation with `enquiry_not_accepted`.
  - After Shreya accepts: Shreya gets `my_role: client` and `can_create: true`; the freelancer gets `my_role: provider` and `blocked_reason: not_client`; a third member gets 404.
  - The freelancer creating the contract gets **403 `not_client`**. Shreya creates it and is the client; the roles then point at the live contract (`duplicate_contract`).
  - Price request on a local-service post (the live 2026-09-30 case): Meena publishes an evening-delivery post, and Suresh sends a price request (`request_quote`), which she accepts. The roles say Meena is the client (`poster_pays`); Suresh creating the contract gets 403 `not_client`; Meena creates it and pays.
  - Package request: Rahul publishes a package on his profile, and Vikram requests it. Vikram is the client (`requester_pays`); Rahul creating the contract gets 403 `not_client`.
  - Cleanup also removes the package, the post (with its saves, views and outbox rows) and both senders' rate-limit hits.
- **Commit before response:** all contract routes now use `Depends(get_conn, scope="function")`, the convention every other router already follows. The request transaction commits before the response is sent, so a client that reads right after a write sees it. Before this, the review-invite check could read 0 on the slowest call (dispute resolve).
- **Fixed-price run** (m_vikram is the client, m_rahul's tutoring listing is the provider). It checks:
  - milestones that don't add up to the total are refused (422);
  - the provider cannot create the contract (403);
  - a duplicate live contract is refused (409);
  - draft add and edit work, and milestones are frozen after proposal;
  - RLS: the outsider m_priya gets 404 with a Hindi message, and the provider and a moderation operator can read;
  - `sandbox` is true for both client and provider, and the provider receives `payment_notice` too, localized (Telugu when asked);
  - accept; submitting before funding is refused;
  - funding returns a sandbox checkout, and funding again reuses it;
  - the milestone stays `pending` until the sandbox payment, then becomes `funded` with ₹3,000 held;
  - submit, reject, resubmit and approve end in `released`;
  - the second milestone is auto-released by the pass, and the contract completes;
  - two review invites; the enquiry is `resolved`;
  - all six required events are in the outbox, and seven notification templates were sent;
  - listing works as client and as provider; the outsider's list does not include the contract.
- **Hourly run:**
  - hours over the cap are refused, and so is a week that doesn't start on a Monday;
  - timesheet: 6 h × ₹500 = ₹3,000;
  - dispute opened; the operator list shows it; members get 403 on the list; a party cannot resolve;
  - the operator closes it and the contract is active again;
  - `approveTimesheet` returns a checkout; after the sandbox payment the timesheet is `paid` and the milestone `released`;
  - `completeContract` works, and review invites are issued.
- **Dispute resolved for the provider:**
  - the milestone is released and the contract completes, with invites issued;
  - this caught and fixed a bug: operator-triggered completion now runs its party-only steps as the client.
- **Cleanup:** the script deletes every row it created:
  - orders, contracts (cascading to their child tables), invites, notifications, outbox rows, audit rows, enquiries and anonymous impressions;
  - it also restores `m_vikram`'s enquiry rate-limit counter;
  - it then sweeps **every `vyapar_*` table** for any row mentioning a test id. Result: clean.
- **The one non-API step:** the test moves one milestone's `auto_release_at` into the past to simulate 14 days going by. Nothing else is written directly.

### Left for others, and known limits
1. **Scheduler wiring (owner of `main.py` middleware and loops):** add `await run_contract_auto_release_pass(get_pool())` to `verification_cleanup_loop()` in `main.py`. It is importable from `app.routers.contracts` or `app.services.contracts`. Until then, auto-release runs only through `POST /v1/contracts/jobs/auto-release`, which is dev-only (404 unless `DEV_MODE`).
2. **Agent tokens (workstream B, `integrations/identity/scopes.py`):**
   - `/v1/contracts` has no write-scope mapping, so personal access tokens can *read* contracts (`read`) but every write is denied (fail-closed).
   - Adding `("/v1/contracts", ("contracts:write",))` enables agent writes.
   - `fundMilestone` returns a checkout URL that a person must open, like boosts do.
3. **Real payouts and refunds:** BLOCKER-01 (above). A refund the gateway cannot perform (the order is unreadable, or the gateway is down) stays as a `succeeded` order for the existing refund queue, while the ledger already says `refunded`.
4. **Web UI:** not built. This is backend only; `vyapar-web` is not touched.
5. **Live API on 8011** was restarted on 2026-09-29, with the coordinator's permission, after `import app.main` passed. It serves every route above, including `getContractRoles`.
6. **Data oddity seen while testing (not workstream D's to fix):** seeded freelance posts 103 and 111 are still `active` although their last dates (24 and 28 September) have passed, so they refuse proposals with `opportunity_expired` while still showing as active. The expiry pass should move them to `expired`.
6. **Configuration (optional, all have defaults):** `CONTRACT_PLATFORM_FEE_BPS=0`, `CONTRACT_AUTO_RELEASE_DAYS=14`, `CONTRACT_CHECKOUT_REUSE_HOURS=24`. They can be added to `vyapar-service/.env` when needed.

---

## API contract

Base path `/v1/contracts`, tag `contracts`. The auth, `X-Vyapar-Language` and error envelope are the same as every other Vyapar route:

```json
{"detail": "<localized>", "error": {"code": "milestones_must_sum_to_total", "message": "<localized>", "details": {"i18n_key": "contracts.error.milestonesMustSumToTotal", "total": "₹8,000", "milestones_paise": 700000, "total_paise": 800000}}}
```

Amounts are integer paise, in INR only. Dates are ISO 8601.

### State machines

```
contract:   draft --propose(client)--> proposed --accept(provider)--> active --(all milestones released: fixed, auto)--> completed
            active --complete(client; nothing held, >=1 released)--> completed        (how hourly contracts end)
            draft|proposed|active --cancel--> cancelled   (draft: client only; proposed: either = withdraw/decline;
                                                           active: either if nothing held, client only if money held -> refunded;
                                                           never while a milestone is submitted)
            active --openDispute(either)--> disputed --resolve(operator)--> active | cancelled (resolved_client) | completed

milestone:  pending --fund+payment success--> funded --submit(provider)--> submitted --approve(client) / 14-day pass--> released
                                                                                     --reject(client, note)--> rejected --submit--> submitted
            funded|rejected|submitted --cancel / resolved_client--> refunded
            (approved is reserved in the model; release is immediate on approval, so rows go submitted -> released)

timesheet:  submitted --approve(client: opens checkout)--> approved --payment success--> paid
            submitted --reject(client, note)--> rejected
```

### Operations

| Method and path | operationId | Who | Body | Returns |
|---|---|---|---|---|
| `GET /v1/contracts/roles?enquiry_id=` | `getContractRoles` | either side of the enquiry | none | `ContractRolesOut` |
| `POST /v1/contracts` | `createContract` | client (see `getContractRoles`) | `ContractCreateIn` | 201 `ContractOut` |
| `GET /v1/contracts?role=client\|provider\|all&state=&limit=&cursor=` | `listMyContracts` | member | none | `Page[ContractSummaryOut]` (keyset on created_at, id) |
| `GET /v1/contracts/{id}` | `getContract` | parties, moderation operator | none | `ContractOut` |
| `POST /v1/contracts/{id}/propose` | `proposeContract` | client | none | `ContractOut` |
| `POST /v1/contracts/{id}/accept` | `acceptContract` | provider | none | `ContractOut` |
| `POST /v1/contracts/{id}/cancel` | `cancelContract` | party (rules above) | `{"reason"?}` (optional body) | `ContractOut` |
| `POST /v1/contracts/{id}/complete` | `completeContract` | client | none | `ContractOut` |
| `POST /v1/contracts/{id}/milestones` | `addMilestone` | client, draft fixed | `MilestoneIn` | 201 `ContractOut` |
| `PATCH /v1/contracts/{id}/milestones/{mid}` | `updateMilestone` | client, draft | `MilestoneUpdateIn` (any subset) | `ContractOut` |
| `DELETE /v1/contracts/{id}/milestones/{mid}` | `deleteMilestone` | client, draft | none | `ContractOut` |
| `POST /v1/contracts/{id}/milestones/{mid}/fund` | `fundMilestone` | client, active | none | `FundingOut` |
| `POST /v1/contracts/{id}/milestones/{mid}/submit` | `submitMilestone` | provider | `{"note"?}` (optional body) | `ContractOut` |
| `POST /v1/contracts/{id}/milestones/{mid}/approve` | `approveMilestone` | client | none | `ContractOut` |
| `POST /v1/contracts/{id}/milestones/{mid}/reject` | `rejectMilestone` | client | `{"note"}` | `ContractOut` |
| `POST /v1/contracts/{id}/disputes` | `openDispute` | party, active | `{"reason", "milestone_id"?}` | 201 `ContractOut` |
| `POST /v1/contracts/{id}/disputes/{did}/resolve` | `resolveContractDispute` | moderation operator | `{"outcome": "resolved_client"\|"resolved_provider"\|"closed", "notes"?}` | `ContractOut` |
| `GET /v1/contracts/disputes?state=&limit=` | `listContractDisputes` | moderation operator | none | `AdminDisputeOut[]` |
| `POST /v1/contracts/{id}/timesheets` | `submitTimesheet` | provider, hourly | `TimesheetIn` | 201 `ContractOut` |
| `POST /v1/contracts/{id}/timesheets/{tid}/approve` | `approveTimesheet` | client | none | `FundingOut` |
| `POST /v1/contracts/{id}/timesheets/{tid}/reject` | `rejectTimesheet` | client | `{"note"}` | `ContractOut` |
| `POST /v1/contracts/jobs/auto-release` | `runContractAutoRelease` | dev only | none | `{"released": n, "completed": n}` |

**Paying for a milestone.** To pay, open `checkout_url`. The milestone becomes `funded` only when the gateway confirms the payment, through the webhook, a status poll or `POST /v1/payments/orders/{payment_order_id}/simulate` in the dev sandbox. The web app then re-reads the contract with `getContract`. Calling `fundMilestone` again while the order is pending and less than 24 h old returns the same checkout. A `notice` of `"gatewayUnavailable"` means no checkout could be created; the milestone stays `pending` and the call can be retried.

### Examples

**getContractRoles** asks who pays and who works, and whether the caller can start the contract now. Call it before showing "Start a contract", and show the action only when `can_create` is true.
```json
GET /v1/contracts/roles?enquiry_id=5c1e…          (as m_shreya, the poster)
{"enquiry_id": "5c1e…", "client_member_id": "m_shreya", "provider_member_id": "m_priya",
 "basis": "poster_pays", "my_role": "client", "can_create": true, "blocked_reason": null, "live_contract_id": null}

GET /v1/contracts/roles?enquiry_id=5c1e…          (as m_priya, the freelancer)
{"enquiry_id": "5c1e…", "client_member_id": "m_shreya", "provider_member_id": "m_priya",
 "basis": "poster_pays", "my_role": "provider", "can_create": false, "blocked_reason": "not_client", "live_contract_id": null}
```
- `basis`: `poster_pays` (a response to a post) or `requester_pays` (a request to a profile).
- `blocked_reason` uses the same codes `createContract` would return:
  - `enquiry_not_accepted`: checked first;
  - `not_client`;
  - `duplicate_contract`: `live_contract_id` then names the contract to open.
- A member who is not on the enquiry gets 404 `enquiry_not_found`.

**MCP:** `get_contract_roles(enquiry_id)` is a new read tool. The `create_contract` description now states the rule and tells agents to call `get_contract_roles` first, and to proceed only when `can_create` is true.

**createContract**, fixed price:
```json
POST /v1/contracts
{
  "enquiry_id": "3f0c9d1e-7a3b-4f39-9a51-2d7f1e0c4b11",
  "title": "Maths coaching for accounts team",
  "description": "Two evening sessions a week at the Karol Bagh office.",
  "kind": "fixed",
  "total_paise": 800000,
  "milestones": [
    {"title": "Month 1: arithmetic and percentages", "amount_paise": 300000, "due_date": "2026-10-28"},
    {"title": "Months 2-3: ratios, interest and GST", "amount_paise": 500000}
  ],
  "propose": true
}
```
**createContract**, hourly (no milestones; each approved timesheet becomes one):
```json
{"enquiry_id": "…", "title": "GST practice sessions (hourly)", "kind": "hourly",
 "total_paise": 1000000, "hourly_rate_paise": 50000, "weekly_hours_cap": 10, "propose": true}
```

**ContractOut** (from `getContract` and every action):
```json
{
  "id": "b7d4…", "enquiry_id": "3f0c…", "opportunity_id": null,
  "client_member_id": "m_vikram", "provider_member_id": "m_rahul",
  "provider_listing_id": "00000000-0000-4000-8000-000000000006",
  "title": "Maths coaching for accounts team", "kind": "fixed", "currency": "INR",
  "total_paise": 800000, "state": "active", "my_role": "client", "counterpart_name": "Rahul Chadha",
  "created_at": "2026-09-28T13:05:11Z", "updated_at": "2026-09-28T13:06:40Z",
  "description": "Two evening sessions a week at the Karol Bagh office.",
  "hourly_rate_paise": null, "weekly_hours_cap": null, "platform_fee_bps": 0,
  "sandbox": true,
  "payment_notice": "Test mode: payments on this contract go through a sandbox and no real money moves.",
  "proposed_at": "2026-09-28T13:05:30Z", "accepted_at": "2026-09-28T13:05:52Z",
  "completed_at": null, "cancelled_at": null, "cancelled_by": null, "cancel_reason": null,
  "client_name": "Vikram Sethi", "provider_name": "Rahul Chadha",
  "milestones": [
    {"id": "a1…", "title": "Month 1: arithmetic and percentages", "description": null, "amount_paise": 300000,
     "due_date": "2026-10-28", "sort": 0, "state": "submitted", "funded_order_id": "60340bd4-…", "checkout_url": null,
     "funded_at": "2026-09-28T13:06:02Z", "submitted_at": "2026-09-28T13:06:40Z",
     "submission_note": "Eight sessions held; worksheets shared.", "approved_at": null, "released_at": null,
     "rejected_at": null, "reject_note": null, "auto_release_at": "2026-10-12T13:06:40Z", "auto_approve": false},
    {"id": "a2…", "title": "Months 2-3: ratios, interest and GST", "amount_paise": 500000, "state": "pending", "…": "…"}
  ],
  "ledger": {"held_paise": 300000, "released_paise": 0, "refunded_paise": 0, "fee_paise": 0},
  "ledger_entries": [
    {"id": 1, "milestone_id": "a1…", "entry": "held", "amount_paise": 300000,
     "payment_order_id": "60340bd4-…", "note": "payment_succeeded", "created_at": "2026-09-28T13:06:02Z"}
  ],
  "timesheets": [],
  "disputes": [],
  "events": [
    {"id": 5, "milestone_id": "a1…", "actor_member_id": "m_rahul", "type": "milestone.submitted",
     "data": {"note": "Eight sessions held; worksheets shared.", "auto_release_days": 14}, "created_at": "…"},
    {"id": 4, "milestone_id": "a1…", "actor_member_id": null, "type": "milestone.funded",
     "data": {"payment_order_id": "60340bd4-…", "amount_paise": 300000}, "created_at": "…"}
  ]
}
```
`events` is the newest-first audit timeline, capped at 100. Its types are:
- `contract.created`, `contract.proposed`, `contract.accepted`, `contract.cancelled`, `contract.completed`, `contract.disputed`;
- `milestone.funding_started`, `milestone.funded`, `milestone.payment_failed`, `milestone.submitted`, `milestone.rejected`, `milestone.released`, `milestone.refunded`;
- `timesheet.submitted`, `timesheet.approved`, `timesheet.rejected`;
- `dispute.resolved`.

`actor_member_id: null` means the system acted: the payment trigger or the auto-release pass.

`ledger.held_paise` is computed as held − released − fee − refunded.

**`sandbox` and `payment_notice` (added 2026-09-29).** Both come from the configured gateway (`PAYMENT_GATEWAY`), not from any payment order, so client, provider and operator all see the same values. The provider cannot read the client's `payment_orders` rows (RLS), which is why order-level `sandbox` was never available to them.
- `sandbox: true` when `PAYMENT_GATEWAY=dev_sandbox`.
- `payment_notice` is a translated sentence, in the caller's language, explaining how money on the contract is handled. Its key is `contracts.label.paymentNotice.sandbox` or `.live`, in en/hi/te.
  - Sandbox (en): "Test mode: payments on this contract go through a sandbox and no real money moves."
  - Live (en): "The client pays each milestone in advance and Vyapar records it as held. It is released to the provider when the client approves the work, or automatically 14 days after submission."
- The web app shows `payment_notice` as-is to either party; it is not role-specific.

**fundMilestone / approveTimesheet → FundingOut:**
```json
{"milestone_id": "a1…", "state": "pending", "amount_paise": 300000,
 "payment_order_id": "60340bd4-…", "checkout_url": "http://localhost:3011/payments/checkout/60340bd4-…",
 "sandbox": true, "notice": null}
```

**submitTimesheet:**
```json
POST /v1/contracts/{id}/timesheets
{"week_start": "2026-09-21", "hours": 6, "note": "Three 2-hour sessions"}
```
The response is a `ContractOut` whose `timesheets` array includes this entry:
```json
{"id": "…", "week_start": "2026-09-21", "hours": 6.0, "note": "Three 2-hour sessions", "state": "submitted", "reject_note": null,
 "amount_paise": 300000, "milestone_id": null, "submitted_at": "…", "approved_at": null, "paid_at": null}
```

**listMyContracts → Page:**
```json
{"items": [{"id": "b7d4…", "enquiry_id": "…", "opportunity_id": null, "client_member_id": "m_vikram",
            "provider_member_id": "m_rahul", "provider_listing_id": "…", "title": "Maths coaching for accounts team",
            "kind": "fixed", "currency": "INR", "total_paise": 800000, "state": "completed", "my_role": "client",
            "counterpart_name": "Rahul Chadha", "created_at": "…", "updated_at": "…"}],
 "next_cursor": "eyJ0IjoiMjAyNi0wOS0yOFQxMzowNToxMS…"}
```

**openDispute / resolve:**
```json
POST /v1/contracts/{id}/disputes            {"reason": "The fourth session was held on Saturday; attendance sheet shared.", "milestone_id": "a1…"}
POST /v1/contracts/{id}/disputes/{did}/resolve   {"outcome": "resolved_provider", "notes": "Attendance sheet confirms four sessions."}
```
Outcomes:
- `resolved_client`: held milestones are refunded, and the contract is cancelled.
- `resolved_provider`: held milestones are released, and the contract completes if nothing is left open.
- `closed`: the contract becomes active again, unchanged.

Every outcome is written to `audit_events`.

### Error codes (stable)

| HTTP | code | When |
|---|---|---|
| 404 | `contract_not_found` | Unknown id, or the caller is not a party or moderation operator (RLS). |
| 404 | `enquiry_not_found`, `milestone_not_found`, `timesheet_not_found`, `dispute_not_found` | The item does not exist. |
| 400 | `enquiry_not_accepted` | The enquiry is not `in_progress`. |
| 403 | `not_client`, `not_provider`, `not_party`, `moderation_permission_required` | Wrong side. |
| 409 | `duplicate_contract` | The enquiry already has a live (draft, proposed, active or disputed) contract. |
| 400 | `contracts_invalid_transition` | The contract is in the wrong state for this action. |
| 400 | `draft_only`, `hourly_no_manual_milestones` | Milestone edits outside a draft, or on an hourly contract. |
| 422 | `hourly_rate_required`, `milestones_required`, `milestones_must_sum_to_total` | Creation or proposal validation. |
| 400 | `milestone_not_fundable`, `milestone_not_funded`, `milestone_not_submitted` | Wrong milestone state. |
| 400 | `held_funds_client_only`, `submitted_blocks_cancel`, `not_completable` | Cancel or complete rules. |
| 400 | `hourly_only`, `timesheet_not_submitted` | Timesheet rules. |
| 422 | `week_start_not_monday`, `week_in_future`, `weekly_cap_exceeded`, `budget_exceeded` | Timesheet validation. |
| 409 | `timesheet_duplicate_week`, `dispute_already_open` | Uniqueness. |
| 404 | `dev_only` | Auto-release endpoint called outside `DEV_MODE`. |
| 422 | `validation_error` | Schema validation (lengths, amounts > 0, and so on). |

Messages are translated in en, hi and te (`contracts.error.*`). The notification templates are `contractProposed`, `contractAccepted`, `contractCancelled`, `contractCompleted`, `contractDisputed`, `disputeResolved`, `milestoneFunded`, `milestoneSubmitted`, `milestoneReleased`, `milestoneRejected`, `timesheetSubmitted`, `timesheetPaid` and `timesheetRejected`, each in all three languages. The recipient's own language is chosen at send time; a block by the recipient silences the notification.
