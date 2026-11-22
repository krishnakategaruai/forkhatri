# Admin & Governance Console

ARCHITECTURE.md ADR-012 calls for one console for the whole of ForKhatri, with each module
contributing views to it. This document describes the console as built on 2026-09-29 and
the contract a module follows to join it. It implements and extends TR-PLAT-01
(`modules/MOD02-milavn/07-tech-reqs.md`).

## Where it lives

| Part | Location |
|---|---|
| Screens | `platform/forkhatri-web/app/admin/*` at `/admin` on the entrance (port 3100). The hub shows the "Admin console" row only to appointed people. |
| API | `platform/identity-service/app/api/routes/admin.py`, under `/v1/admin/*` |
| Rules | `platform/identity-service/app/components/governance/` (`roles.py`, `interface.py`, `gateway.py`) |
| Data | `forkhatri_identity`, schema `governance`, from migration `db/migrations/005-governance.sql` |
| Tests | `tests/integration/test_governance_db.py`. Each test runs in a transaction that is rolled back, so nothing is left in the database. Run with `IDENTITY_DB_TESTS=1`. |

## What the platform owns

- **Roles.** Each role is held over an area (the platform, one module, or one samaj
  chapter) for a term with an optional end date. Nobody has any admin rights by default.
  - National office bearers: president, secretary, treasurer.
  - Platform staff: owner, grievance officer, data protection officer, auditor.
  - Chapter roles: chapter head (appoints inside their own chapter), chapter secretary.
  - Module roles: moderator, verifier.
  - The roles are defined in `roles.py`, not in the database.
- **Organisation.** State chapters, with city chapters under them.
- **Suspensions.** A suspension has a reason code and a length: 1, 3, 7 or 30 days, or
  until someone lifts it.
  - Suspending a member ends all their sessions. Every module fails closed, because a
    suspended member's session no longer resolves.
  - Timed suspensions end on their own. A sweep runs every minute.
- **Bans and senior appointments need two people.**
  - Bans always need a second person.
  - Sensitive roles need a second person too, unless an owner grants them.
  - The person who asked can never be the person who decides.
- **Audit log.** It is append-only: a database trigger refuses UPDATE and DELETE, and the
  runtime role has only INSERT and SELECT.
  - Every change is logged in the same transaction that makes it.
  - Every time someone views a member's full contact details, that view is logged with a
    reason.
- **Module open or closed.** Only owners can change a module's availability.

Guards on every action:
- Nobody can act on their own account.
- Only an owner can act on an owner.
- Staff accounts can only be changed by someone who can manage roles.

## What each module owns, and how it joins

Reports, cases, verification, pricing tiers and orders stay in each module. **Tiers differ
per module and are never merged into a single platform plan.** The console calls module
endpoints through the identity service. It sends the admin's own `fk_session` cookie and
`Accept-Language`, so the module's own authorisation still makes the decision.

Identity's `POST /internal/v1/sessions/resolve` returns `admin_scopes`, for example
`["milavn.moderate","mangaly.moderate","vyapar.verify"]`. Each scope is
`<module>.<action>`, where the action is moderate, verify or commercial. A module maps
these scopes onto its own moderator or operator check.

A module publishes these endpoints, all paths relative to its API base
(`MODULE_API_URLS` / `ADMIN_MODULE_API_URLS`):

| Endpoint | Returns |
|---|---|
| `GET /{module}/admin/manifest` | `{module_id, views:[{view_id, title, nav_group, required_permission_scope, list_endpoint, detail_endpoint, action_endpoints[]}]}`. A single view object is also accepted. `nav_group` is one of moderation, verification, commercial, disputes, policy. |
| list | `AdminQueueItem[]`: `{item_id, module_id, item_type, submitted_at, priority (urgent/high/normal), status, summary_text (localised, no raw codes), subject_title?, reason?, due_at?}` |
| detail | `{item_id, case_detail:{…, fields?:[{label,value}] (localised), history?:[{action,by,notes,at}]}, available_actions:[…], action_options?:{action:[codes]}}` |
| action (POST) | Body `{notes?, reason_code?}`. Returns the updated item. The platform also records a `queue.action` audit event. |
| `GET /{module}/admin/members/{member_id}/summary` | Optional. `{plan:{tier,name,status,status_label?,renews_at?}\|null, facts:[{label,value}], flags:[…]}`. Return 404 when the person has no account in that module. |

Status on 2026-09-29:
- Mangaly: manifest, queue, fields and member summary are live.
- Milavn: manifest, queue and member summary are live. Localisation and grouping of
  duplicate reports are being built.
- Vyapar: views for moderation, verification, opportunities, appeals, disputes and
  commercial are being built.

## Development

Personas for automated tests:
- `samaj-president` (Ramesh Khatri) and `samaj-secretary` (Meena Khatri). They are the two
  people for two-person approvals.
- `milavn-moderator`.

`krishna` is the owner persona, for people only. It is never used in automated tests.

The seed is `scripts/seed_dev_governance.py`, run by `deploy/migrate/migrate.py --seed-dev`.
In production, appoint the first owner with a direct, audited insert as the owner database
role, the same way the seed does.

## Document status 2026-11-22, as built

Checked against code on 2026-11-22. What is built and where:

| Item | Detail |
|---|---|
| API (all under `/v1/admin`, in `admin.py`) | GET me, overview, members, members/{id}, members/{id}/modules, approvals, roles, org, audit, modules, queues, queues/{module}/{view_id}/{item_id}; POST members/{id}/contact, suspend, lift, sign-out, ban; approvals/{id}/decide; roles; roles/{id}/revoke; org/chapters; org/chapters/{key}/close; queues/.../actions/{action_id}; PATCH modules/{key}. 25 routes. |
| Screens | `/admin` (Today), `/admin/members`, `/admin/members/[id]`, `/admin/approvals`, `/admin/team`, `/admin/org`, `/admin/queues`, `/admin/modules`, `/admin/audit`. |
| Tables | `governance.chapter`, `role_assignment`, `suspension`, `approval_request`, `audit_event` (migration 005). |
| Functional requirements | `02b-functional-requirements-admin-console.md` (FR-031 to FR-039, FR-031a, FR-047, FR-048). |
| Languages | Console strings in English, Hindi, Telugu, Marathi, Kannada (`lib/admin-i18n.ts`). |

Open items (from `docs/Critique/CRITIQUE-platform.md`): "last seen" shown to all viewers (C12); no external anchor for audit integrity (C12); owner role can act alone and first owner is a manual insert (C12); no member-facing explanation or appeal after suspension (C6); mixed-script Hindi labels and the "Swami" owner label (C13). Module status in the table above dated 2026-09-29 may have moved: verify each module's `GET /{module}/admin/manifest`.
