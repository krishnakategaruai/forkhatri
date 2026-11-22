---
project: ForKhatri
artifact: Platform Functional Requirements, part b: admin and governance console
step: 2
status: Document status 2026-11-22, as built
updated: 2026-11-22
---

# FR part b: admin and governance console

Index: `02-functional-requirements.md`. Narrative and module contract: `admin-console.md`. Screens (route `/admin/...` on the entrance, port 3100): SCR-ADM-TODAY (`/admin`, `Today.tsx`), SCR-ADM-MEMBERS (`/admin/members`), SCR-ADM-MEMBER (`/admin/members/[id]`, `MemberDetail.tsx`), SCR-ADM-APPROVALS, SCR-ADM-TEAM (`/admin/team`), SCR-ADM-ORG (`/admin/org`), SCR-ADM-QUEUES, SCR-ADM-MODULES, SCR-ADM-AUDIT; shell `AdminShell.tsx`, shared widgets `kit.tsx`, strings `lib/admin-i18n.ts`, client `lib/admin-api.ts`. The hub shows the "Admin console" row only to appointed people.

Tables: `TBL-governance.chapter`, `TBL-governance.role_assignment`, `TBL-governance.suspension`, `TBL-governance.approval_request`, `TBL-governance.audit_event` (migration 005); plus `TBL-identity.member`, `TBL-identity.session`, `TBL-registry.module`. Rules code: `app/components/governance/roles.py`, `interface.py`, `gateway.py`. Automated tests: `platform/identity-service/tests/integration/test_governance_db.py` (transaction rolled back; `IDENTITY_DB_TESTS=1`).

## Permissions (from `roles.py`)
`members.view`, `members.contact`, `members.suspend`, `members.ban`, `roles.view`, `roles.manage`, `approvals.decide`, `org.view`, `org.manage`, `chapter.manage`, `audit.view`, `modules.manage`; module actions `<module>.moderate|verify|commercial`. Roles are code: national (president, secretary, treasurer), platform staff (owner, grievance officer, data protection officer, auditor), chapter (chapter head, chapter secretary), module (moderator, verifier). Exact permission lists per role: read `roles.py` (unverified here beyond the names).

## Global guards (BR-12)
Nobody has admin rights by default; nobody can act on their own account; only an owner can act on an owner; staff accounts can only be changed by someone with `roles.manage`; the requester of an approval can never decide it; chapter heads appoint only inside their own chapter.

## FR-031 Admin identity and landing (BR-12, BR-15) - built
`GET /v1/admin/me` returns the person's roles, permissions, scopes and the role catalogue; `GET /v1/admin/overview` feeds SCR-ADM-TODAY (counts of waiting approvals, open queue items, recent activity). Non-appointed members get 403 and never see the hub row. Endpoints: API-GET-v1-admin-me, API-GET-v1-admin-overview.

## FR-032 Member directory (BR-12) - built
Search and list members (`members.view`), open one member, see their module memberships and per-module summary. Endpoints: API-GET-v1-admin-members, API-GET-v1-admin-members-member_id, API-GET-v1-admin-members-member_id-modules. Known gap: "last seen" is visible to every viewer (critique C12).

## FR-033 Contact reveal with reason (BR-14) - built
`POST /v1/admin/members/{id}/contact` (`members.contact`) returns full phone and email only with a reason code; every view is written to the audit log in the same transaction. Endpoint: API-POST-v1-admin-members-member_id-contact. Table: `TBL-governance.audit_event`.

## FR-034 Suspend, lift, sign-out-everywhere (BR-13) - built
`POST .../suspend` (reason code; 1, 3, 7, 30 days or until lifted), `.../lift`, `.../sign-out` (`members.suspend`). A suspension ends all the member's sessions; a sweep every minute ends timed suspensions. Modules fail closed because a suspended session no longer resolves. Sign-in returns a message "Contact ForKhatri support" but no support screen exists (critique C6). Endpoints: API-POST-v1-admin-members-member_id-suspend, ...-lift, ...-sign-out. Tables: `TBL-governance.suspension`, `TBL-identity.session`.

## FR-035 Ban needs two people (BR-12) - built
`POST .../ban` (`members.ban`) creates an approval request; a different person with `approvals.decide` approves or declines. Endpoint: API-POST-v1-admin-members-member_id-ban. Table: `TBL-governance.approval_request`.

## FR-036 Approvals inbox (BR-12) - built
`GET /v1/admin/approvals` lists requests; `POST /v1/admin/approvals/{id}/decide` approves or declines with notes; requester cannot decide their own. Endpoints: API-GET-v1-admin-approvals, API-POST-v1-admin-approvals-approval_id-decide.

## FR-037 Team and roles (BR-12) - built
`GET /v1/admin/roles`, `POST /v1/admin/roles` (appoint over a scope with a term and optional end date), `POST /v1/admin/roles/{id}/revoke`. Sensitive roles need a second person unless an owner grants them. Endpoints: API-GET-v1-admin-roles, API-POST-v1-admin-roles, API-POST-v1-admin-roles-assignment_id-revoke. Table: `TBL-governance.role_assignment`. Gap: first owner is a direct database insert (see `seed_dev_governance.py`).

## FR-038 Organisation (BR-12) - built
State chapters with city chapters under them: `GET /v1/admin/org`, `POST /v1/admin/org/chapters`, `POST /v1/admin/org/chapters/{key}/close` (`org.manage`). Table: `TBL-governance.chapter`.

## FR-039 Audit log (BR-14) - built
`GET /v1/admin/audit` (`audit.view`) with filters; append-only (a database trigger refuses UPDATE and DELETE; runtime role `identity_app` has INSERT and SELECT only). Known gap: the owner role can drop the trigger; no external hash anchor (critique C12). Table: `TBL-governance.audit_event`.

## FR-031a Module open or closed (BR-03, BR-15) - built
`GET /v1/admin/modules` and `PATCH /v1/admin/modules/{key}` (`modules.manage`, owners only) change a module's availability in the registry. Table: `TBL-registry.module`. (Number kept as FR-031a to avoid renumbering; planned renumber in index.)

## FR-047 Module work queues (BR-15) - built (module-dependent)
`GET /v1/admin/queues` merges queue views from each module's `GET /{module}/admin/manifest` and lists; `GET /v1/admin/queues/{module}/{view_id}/{item_id}` returns detail with available actions; `POST .../actions/{action_id}` forwards the action with the admin's own `fk_session` and `Accept-Language` so the module still authorises; the platform records a `queue.action` audit event. Endpoints: API-GET-v1-admin-queues, API-GET-v1-admin-queues-module-view_id-item_id, API-POST-v1-admin-queues-module-view_id-item_id-actions-action_id. Config: `ADMIN_MODULE_API_URLS`, `MODULE_API_URLS`, `ADMIN_GATEWAY_TIMEOUT_SECONDS`. Status on 2026-09-29: Mangalya and Milavn live; Vyapar views being built; Counsel unverified.

## FR-048 Admin console language (BR-11) - built
Console is in all five languages through `lib/admin-i18n.ts`; mixed-script Hindi and the "Swami" label for Owner flagged in critique C13.

## Error and notification behaviour
Console actions show success or a localised error code; there are no outbound notifications to the affected member (no channel), so a suspended member learns only when sign-in or a module refuses (gap).

## Acceptance traceability
BR-12: FR-031, FR-035 to FR-038. BR-13: FR-034. BR-14: FR-033, FR-039. BR-15: FR-031a, FR-047.


## Account deletion (added 2026-11-22)

FR-065: the Modules page lists stuck deletions with a Retry button (`GET /v1/admin/deletions/stuck`, `POST /v1/admin/deletions/{job_id}/retry`). Deletion is refused while a member holds a live admin role (409 `admin_role_held`): remove the role first. Full list: `02-functional-requirements.md`, FR-061 to FR-070.
