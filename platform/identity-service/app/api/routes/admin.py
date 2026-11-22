"""Admin & Governance Console API (ARCHITECTURE.md ADR-012; module views per TR-PLAT-01).

    GET  /v1/admin/me                         am I an admin, with which roles and permissions
    GET  /v1/admin/overview                   Today: what needs attention
    GET  /v1/admin/members                    search people (contact details masked)
    GET  /v1/admin/members/{id}               one person, across the platform
    GET  /v1/admin/members/{id}/modules       each module's own view of them (its tier, flags)
    POST /v1/admin/members/{id}/contact       reveal full phone and email (audited, reason required)
    POST /v1/admin/members/{id}/suspend       time-boxed or open suspension; ends every session
    POST /v1/admin/members/{id}/lift          end a suspension (or, with approvals.decide, a ban)
    POST /v1/admin/members/{id}/sign-out      end every session
    POST /v1/admin/members/{id}/ban           propose a permanent ban (a second person decides)
    GET  /v1/admin/approvals                  two-person requests
    POST /v1/admin/approvals/{id}/decide      approve, decline or withdraw
    GET  /v1/admin/roles                      who holds which role, where, until when
    POST /v1/admin/roles                      appoint
    POST /v1/admin/roles/{id}/revoke          end an appointment
    GET  /v1/admin/org                        national office bearers and chapters
    POST /v1/admin/org/chapters               add a state or city chapter
    POST /v1/admin/org/chapters/{key}/close   close an empty chapter
    GET  /v1/admin/audit                      the append-only audit log
    GET  /v1/admin/modules                    module registry
    PATCH /v1/admin/modules/{key}             open or close a module
    GET  /v1/admin/queues                     every module queue this admin is appointed to
    GET  /v1/admin/queues/{m}/{view}/{item}   one queue item
    POST /v1/admin/queues/{m}/{view}/{item}/actions/{action}

Everything except /me answers 403 to a member without an administrative role.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import AppSettings, DbSession, RequiredSession, client_ip
from app.components.deletion import interface as deletion
from app.components.governance import gateway
from app.components.governance import interface as gov
from app.components.governance import roles as R
from app.config.settings import LANGUAGES
from app.errors import DomainError

router = APIRouter(prefix="/v1/admin", tags=["admin"])


async def _admin(session: RequiredSession, db: DbSession) -> gov.Admin:
    admin = await gov.load_admin(db, session.member.member_id, session.member.display_name)
    if not admin.is_admin:
        raise DomainError("admin_forbidden", "The admin console is for people the samaj has appointed.", 403)
    return admin


CurrentAdmin = Annotated[gov.Admin, Depends(_admin)]


def _lang(request: Request, session: RequiredSession) -> str:
    code = request.headers.get("accept-language", "")[:2].lower()
    return code if code in LANGUAGES else session.member.preferred_language


class Note(BaseModel):
    model_config = ConfigDict(extra="forbid")
    note: str | None = Field(default=None, max_length=1000)


class SuspendBody(Note):
    reason_code: str = Field(max_length=40)
    days: int | None = None


class BanBody(Note):
    reason_code: str = Field(max_length=40)


class DecideBody(Note):
    decision: Literal["approved", "declined", "withdrawn"]


class GrantBody(Note):
    member_id: UUID
    role: str = Field(max_length=40)
    scope_key: str | None = Field(default=None, max_length=60)
    title: str | None = Field(default=None, max_length=60)
    ends_at: datetime | None = None


class ChapterBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(max_length=80)
    kind: Literal["state", "city"]
    parent_key: str | None = Field(default=None, max_length=60)


class ModulePatch(Note):
    availability: Literal["available", "in_development", "planned"]


class QueueAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notes: str | None = Field(default=None, max_length=1000)
    reason_code: str | None = Field(default=None, max_length=40)


# --------------------------------------------------------------------------- me / today


@router.get("/me")
async def me(session: RequiredSession, db: DbSession) -> dict[str, Any]:
    """Answers every signed-in member (the hub asks it to decide whether to show the console link)."""
    admin = await gov.load_admin(db, session.member.member_id, session.member.display_name)
    return {
        "is_admin": admin.is_admin,
        "member": {"member_id": str(admin.member_id), "display_name": admin.display_name},
        "roles": list(admin.roles),
        "permissions": sorted(admin.permissions),
        "module_scopes": sorted(admin.module_scopes),
        "managed_chapters": sorted(admin.managed_chapters),
        "catalogue": {
            "roles": [
                {"key": r.key, "scope_kind": r.scope_kind, "sensitive": r.sensitive, "permissions": list(r.permissions), "module_actions": list(r.module_actions)}
                for r in R.ROLES.values()
            ],
            "reason_codes": list(R.REASON_CODES),
            "suspension_days": list(R.SUSPENSION_DAYS),
        }
        if admin.is_admin
        else None,
    }


@router.get("/overview")
async def overview(admin: CurrentAdmin, db: DbSession) -> dict[str, Any]:
    return await gov.overview(db, admin)


# --------------------------------------------------------------------------- members


@router.get("/members")
async def members(
    admin: CurrentAdmin,
    db: DbSession,
    q: str | None = Query(default=None, max_length=80),
    status: str | None = Query(default=None, max_length=20),
    limit: int = 30,
    offset: int = 0,
) -> dict[str, Any]:
    # Chapter heads search only to pick whom to appoint; results carry masked contact details.
    if not (admin.can(R.MEMBERS_VIEW) or admin.managed_chapters):
        raise DomainError("admin_forbidden", "Your role does not allow this.", 403)
    return await gov.search_members(db, q=q, status=status, limit=limit, offset=offset)


@router.get("/members/{member_id}")
async def member(member_id: UUID, admin: CurrentAdmin, db: DbSession) -> dict[str, Any]:
    admin.require(R.MEMBERS_VIEW)
    return await gov.member_detail(db, member_id)


@router.get("/members/{member_id}/modules")
async def member_modules(
    member_id: UUID, request: Request, session: RequiredSession, admin: CurrentAdmin, settings: AppSettings
) -> list[dict[str, Any]]:
    """Each module's own view of this person (its pricing tier, reports, flags), side by side."""
    admin.require(R.MEMBERS_VIEW)
    return await gateway.member_summaries(
        settings, member_id=str(member_id), token=session.token, lang=_lang(request, session), scopes=admin.module_scopes
    )


@router.post("/members/{member_id}/contact")
async def reveal_contact(member_id: UUID, body: Note, request: Request, admin: CurrentAdmin, db: DbSession) -> dict[str, Any]:
    return await gov.reveal_contact(db, admin, member_id, note=body.note, ip=client_ip(request))


@router.post("/members/{member_id}/suspend")
async def suspend(member_id: UUID, body: SuspendBody, request: Request, admin: CurrentAdmin, db: DbSession) -> dict[str, Any]:
    return await gov.suspend(db, admin, member_id, reason_code=body.reason_code, note=body.note, days=body.days, ip=client_ip(request))


@router.post("/members/{member_id}/lift")
async def lift(member_id: UUID, body: Note, request: Request, admin: CurrentAdmin, db: DbSession) -> dict[str, Any]:
    return await gov.lift(db, admin, member_id, note=body.note, ip=client_ip(request))


@router.post("/members/{member_id}/sign-out")
async def sign_out(member_id: UUID, body: Note, request: Request, admin: CurrentAdmin, db: DbSession) -> dict[str, Any]:
    return await gov.sign_out_everywhere(db, admin, member_id, note=body.note, ip=client_ip(request))


@router.post("/members/{member_id}/ban")
async def ban(member_id: UUID, body: BanBody, request: Request, admin: CurrentAdmin, db: DbSession) -> dict[str, Any]:
    return await gov.propose_ban(db, admin, member_id, reason_code=body.reason_code, note=body.note, ip=client_ip(request))


# --------------------------------------------------------------------------- approvals


@router.get("/approvals")
async def approvals(admin: CurrentAdmin, db: DbSession, status: str | None = "pending") -> list[dict[str, Any]]:
    if not (admin.can(R.APPROVALS_DECIDE) or admin.can(R.MEMBERS_BAN) or admin.can(R.ROLES_MANAGE)):
        raise DomainError("admin_forbidden", "Your role does not allow this.", 403)
    rows = await gov.list_approvals(db, status=status if status in ("pending", "approved", "declined", "withdrawn") else None)
    return [
        {**a, "can_decide": admin.can(R.APPROVALS_DECIDE) and a["requested_by"]["member_id"] != str(admin.member_id) and a["target"]["member_id"] != str(admin.member_id)}
        for a in rows
    ]


@router.post("/approvals/{approval_id}/decide")
async def decide(approval_id: UUID, body: DecideBody, request: Request, admin: CurrentAdmin, db: DbSession) -> dict[str, Any]:
    return await gov.decide_approval(db, admin, approval_id, decision=body.decision, note=body.note, ip=client_ip(request))


# --------------------------------------------------------------------------- roles and organisation


@router.get("/roles")
async def roles(admin: CurrentAdmin, db: DbSession, include_ended: bool = False) -> list[dict[str, Any]]:
    if not (admin.can(R.ROLES_VIEW) or admin.managed_chapters):
        raise DomainError("admin_forbidden", "Your role does not allow this.", 403)
    return await gov.list_assignments(db, include_ended=include_ended)


@router.post("/roles")
async def grant(body: GrantBody, request: Request, admin: CurrentAdmin, db: DbSession) -> dict[str, Any]:
    return await gov.grant_role(
        db,
        admin,
        member_id=body.member_id,
        role=body.role,
        scope_key=body.scope_key,
        title=body.title,
        ends_at=body.ends_at,
        note=body.note,
        ip=client_ip(request),
    )


@router.post("/roles/{assignment_id}/revoke")
async def revoke(assignment_id: UUID, body: Note, request: Request, admin: CurrentAdmin, db: DbSession) -> dict[str, Any]:
    return await gov.revoke_role(db, admin, assignment_id, note=body.note, ip=client_ip(request))


@router.get("/org")
async def org(admin: CurrentAdmin, db: DbSession) -> dict[str, Any]:
    admin.require(R.ORG_VIEW)
    return await gov.organisation(db)


@router.post("/org/chapters")
async def add_chapter(body: ChapterBody, request: Request, admin: CurrentAdmin, db: DbSession) -> dict[str, Any]:
    return await gov.create_chapter(db, admin, name=body.name, kind=body.kind, parent_key=body.parent_key, ip=client_ip(request))


@router.post("/org/chapters/{key}/close")
async def close_chapter(key: str, body: Note, request: Request, admin: CurrentAdmin, db: DbSession) -> dict[str, Any]:
    return await gov.archive_chapter(db, admin, key, note=body.note, ip=client_ip(request))


# --------------------------------------------------------------------------- audit and modules


@router.get("/audit")
async def audit(
    admin: CurrentAdmin,
    db: DbSession,
    actor: UUID | None = None,
    target: UUID | None = None,
    action: str | None = Query(default=None, max_length=60),
    module: str | None = Query(default=None, max_length=30),
    before: int | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    admin.require(R.AUDIT_VIEW)
    return await gov.audit_log(db, actor=actor, target=target, action_prefix=action, module_key=module, before_id=before, limit=limit)


@router.get("/modules")
async def modules(admin: CurrentAdmin, db: DbSession) -> list[dict[str, Any]]:
    return await gov.list_modules(db)


@router.patch("/modules/{key}")
async def set_module(key: str, body: ModulePatch, request: Request, admin: CurrentAdmin, db: DbSession) -> list[dict[str, Any]]:
    return await gov.set_module_availability(db, admin, key, availability=body.availability, note=body.note, ip=client_ip(request))


# --------------------------------------------------------------------------- federated module queues


@router.get("/queues")
async def queues(request: Request, session: RequiredSession, admin: CurrentAdmin, settings: AppSettings) -> list[dict[str, Any]]:
    return await gateway.queues(settings, token=session.token, lang=_lang(request, session), scopes=admin.module_scopes)


@router.get("/queues/{module}/{view_id}/{item_id}")
async def queue_item(
    module: str, view_id: str, item_id: str, request: Request, session: RequiredSession, admin: CurrentAdmin, settings: AppSettings
) -> Any:
    return await gateway.detail(
        settings, module=module, view_id=view_id, item_id=item_id, token=session.token, lang=_lang(request, session), scopes=admin.module_scopes
    )


@router.post("/queues/{module}/{view_id}/{item_id}/actions/{action_id}")
async def queue_action(
    module: str,
    view_id: str,
    item_id: str,
    action_id: str,
    body: QueueAction,
    request: Request,
    session: RequiredSession,
    admin: CurrentAdmin,
    settings: AppSettings,
    db: DbSession,
) -> Any:
    result = await gateway.act(
        settings,
        module=module,
        view_id=view_id,
        item_id=item_id,
        action_id=action_id,
        body=body.model_dump(exclude_none=True),
        token=session.token,
        lang=_lang(request, session),
        scopes=admin.module_scopes,
    )
    await gov.audit(
        db,
        actor=admin.member_id,
        action="queue.action",
        module_key=module,
        subject=f"{view_id}/{item_id}",
        reason_code=body.reason_code,
        note=body.notes,
        details={"action": action_id, "view_id": view_id, "item_id": item_id},
        ip=client_ip(request),
    )
    return result


# --------------------------------------------------------------------------- stuck account deletions


@router.get("/deletions/stuck")
async def stuck_deletions(admin: CurrentAdmin, db: DbSession) -> dict[str, Any]:
    """Account deletions that a module keeps refusing (read-only list; no member details)."""
    admin.require(R.MEMBERS_VIEW)
    return {"deletions": await deletion.stuck_list(db)}


@router.post("/deletions/{job_id}/retry")
async def retry_deletion(job_id: UUID, request: Request, admin: CurrentAdmin, db: DbSession, settings: AppSettings) -> dict[str, Any]:
    admin.require(R.MEMBERS_SUSPEND)
    await deletion.admin_retry(db, settings, job_id)
    await gov.audit(db, actor=admin.member_id, action="account.deletion_retried", subject=str(job_id)[:8], ip=client_ip(request))
    await db.commit()
    from app.components.deletion.interface import launch
    from app.api.deps import get_session_factory

    launch(get_session_factory(request), settings, job_id)
    return {"retrying": True}
