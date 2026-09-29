"""Governance component — public interface (MODULE-ARCHITECTURE-STANDARD §3).

The Admin & Governance Console's platform half (ARCHITECTURE.md ADR-012): who holds
which administrative role over which area, the samaj chapters, platform suspensions
and bans, two-person approvals, and the append-only audit log. Routers call only
these functions; nothing else reads or writes the `governance` schema.

Rules enforced here, not in the screens:
  * nobody acts on themselves, and nobody but an owner touches an owner;
  * every suspension, ban and role change carries a reason, and every one is audited
    in the same transaction as the change it records;
  * a ban always needs a second person; a sensitive role needs one unless an owner grants it;
  * suspensions with an end date end on their own (expire_due_suspensions).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.governance import roles as R
from app.components.identity.identifiers import mask_email, mask_phone
from app.errors import DomainError

_LIVE = "a.revoked_at IS NULL AND a.starts_at <= now() AND (a.ends_at IS NULL OR a.ends_at > now())"


# --------------------------------------------------------------------------- who is acting


@dataclass(frozen=True, slots=True)
class Admin:
    member_id: UUID
    display_name: str
    roles: tuple[dict[str, Any], ...]
    permissions: frozenset[str]
    module_scopes: frozenset[str]
    # Chapters (and everything under them) this person may appoint office bearers in.
    managed_chapters: frozenset[str] = field(default_factory=frozenset)

    @property
    def is_admin(self) -> bool:
        return bool(self.roles)

    @property
    def is_owner(self) -> bool:
        return any(r["role"] == "owner" for r in self.roles)

    def can(self, permission: str) -> bool:
        return permission in self.permissions

    def require(self, permission: str) -> None:
        if permission not in self.permissions:
            raise DomainError("admin_forbidden", "Your role does not allow this.", 403)


async def _module_keys(db: AsyncSession) -> list[str]:
    """Modules that exist as software (a planned module has nothing to moderate yet)."""
    return [
        r.key
        for r in await db.execute(text("SELECT key FROM registry.module WHERE availability <> 'planned' ORDER BY sort_order"))
    ]


async def _chapter_subtree(db: AsyncSession, roots: list[str]) -> set[str]:
    if not roots:
        return set()
    rows = await db.execute(
        text(
            "WITH RECURSIVE t AS (SELECT key FROM governance.chapter WHERE key = ANY(:roots) "
            "UNION SELECT c.key FROM governance.chapter c JOIN t ON c.parent_key = t.key) SELECT key FROM t"
        ),
        {"roots": roots},
    )
    return {r.key for r in rows}


def _scopes_for(role_rows: list[Any], module_keys: list[str]) -> tuple[set[str], set[str]]:
    permissions: set[str] = set()
    scopes: set[str] = set()
    for row in role_rows:
        role = R.ROLES.get(row.role)
        if role is None:
            continue
        permissions.update(role.permissions)
        targets = [row.scope_key] if row.scope_kind == "module" else module_keys if row.scope_kind == "platform" else []
        scopes.update(f"{m}.{action}" for m in targets for action in role.module_actions)
    return permissions, scopes


async def load_admin(db: AsyncSession, member_id: UUID, display_name: str) -> Admin:
    rows = list(
        await db.execute(
            text(
                "SELECT a.id, a.role, a.scope_kind, a.scope_key, a.title, a.ends_at "
                f"FROM governance.role_assignment a WHERE a.member_id = :m AND {_LIVE} ORDER BY a.created_at"
            ),
            {"m": member_id},
        )
    )
    permissions, scopes = _scopes_for(rows, await _module_keys(db))
    managed = await _chapter_subtree(
        db, [r.scope_key for r in rows if r.scope_kind == "chapter" and R.CHAPTER_MANAGE in R.ROLES[r.role].permissions]
    )
    return Admin(
        member_id=member_id,
        display_name=display_name,
        roles=tuple(
            {
                "assignment_id": str(r.id),
                "role": r.role,
                "scope_kind": r.scope_kind,
                "scope_key": r.scope_key,
                "title": r.title,
                "ends_at": _iso(r.ends_at),
            }
            for r in rows
        ),
        permissions=frozenset(permissions),
        module_scopes=frozenset(scopes),
        managed_chapters=frozenset(managed),
    )


async def module_scopes_for(db: AsyncSession, member_id: UUID) -> list[str]:
    """Module permissions the samaj has appointed this member to (identity resolve → `admin_scopes`)."""
    rows = list(
        await db.execute(
            text(f"SELECT a.role, a.scope_kind, a.scope_key FROM governance.role_assignment a WHERE a.member_id = :m AND {_LIVE}"),
            {"m": member_id},
        )
    )
    if not rows:
        return []
    return sorted(_scopes_for(rows, await _module_keys(db))[1])


# --------------------------------------------------------------------------- audit


async def audit(
    db: AsyncSession,
    *,
    actor: UUID | None,
    action: str,
    target: UUID | None = None,
    module_key: str | None = None,
    subject: str | None = None,
    reason_code: str | None = None,
    note: str | None = None,
    details: dict[str, Any] | None = None,
    ip: str | None = None,
) -> None:
    import json

    await db.execute(
        text(
            "INSERT INTO governance.audit_event (actor_member_id, action, target_member_id, module_key, subject, "
            "reason_code, note, details, ip) VALUES (:actor, :action, :target, :module, :subject, :reason, :note, "
            "CAST(:details AS jsonb), :ip)"
        ),
        {
            "actor": actor,
            "action": action,
            "target": target,
            "module": module_key,
            "subject": subject,
            "reason": reason_code,
            "note": note,
            "details": json.dumps(details or {}, default=str),
            "ip": ip,
        },
    )


async def audit_log(
    db: AsyncSession,
    *,
    actor: UUID | None = None,
    target: UUID | None = None,
    action_prefix: str | None = None,
    module_key: str | None = None,
    before_id: int | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    where = ["TRUE"]
    params: dict[str, Any] = {"limit": min(max(limit, 1), 200)}
    if actor:
        where.append("e.actor_member_id = :actor")
        params["actor"] = actor
    if target:
        where.append("e.target_member_id = :target")
        params["target"] = target
    if action_prefix:
        where.append("e.action LIKE :action")
        params["action"] = action_prefix.rstrip("%") + "%"
    if module_key:
        where.append("e.module_key = :module")
        params["module"] = module_key
    if before_id:
        where.append("e.id < :before")
        params["before"] = before_id
    rows = list(
        await db.execute(
            text(
                "SELECT e.*, am.display_name AS actor_name, tm.display_name AS target_name "
                "FROM governance.audit_event e "
                "LEFT JOIN identity.member am ON am.id = e.actor_member_id "
                "LEFT JOIN identity.member tm ON tm.id = e.target_member_id "
                f"WHERE {' AND '.join(where)} ORDER BY e.id DESC LIMIT :limit"
            ),
            params,
        )
    )
    events = [
        {
            "id": r.id,
            "at": _iso(r.at),
            "action": r.action,
            "actor": _person(r.actor_member_id, r.actor_name),
            "target": _person(r.target_member_id, r.target_name),
            "module_key": r.module_key,
            "subject": r.subject,
            "reason_code": r.reason_code,
            "note": r.note,
            "details": r.details,
        }
        for r in rows
    ]
    return {"events": events, "next_before": events[-1]["id"] if len(events) == params["limit"] else None}


# --------------------------------------------------------------------------- helpers


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _person(member_id: UUID | None, name: str | None) -> dict[str, Any] | None:
    return {"member_id": str(member_id), "display_name": name} if member_id else None


def _clean(note: str | None, *, required: bool = True) -> str | None:
    value = (note or "").strip()
    if required and len(value) < 3:
        raise DomainError("note_required", "Write a short reason (at least a few words).", 422)
    return value[:1000] or None


def _reason(code: str) -> str:
    if code not in R.REASON_CODES:
        raise DomainError("reason_unknown", "Choose a reason from the list.", 422)
    return code


async def _member_row(db: AsyncSession, member_id: UUID) -> Any:
    row = (
        await db.execute(
            text(
                "SELECT id, display_name, phone_e164, email, preferred_language, identity_level, status::text AS status, "
                "created_at FROM identity.member WHERE id = :id"
            ),
            {"id": member_id},
        )
    ).first()
    if row is None:
        raise DomainError("member_unknown", "No member has that id.", 404)
    return row


async def _live_roles_of(db: AsyncSession, member_id: UUID) -> list[str]:
    return [
        r.role
        for r in await db.execute(
            text(f"SELECT a.role FROM governance.role_assignment a WHERE a.member_id = :m AND {_LIVE}"), {"m": member_id}
        )
    ]


async def _guard_target(db: AsyncSession, admin: Admin, target_id: UUID) -> Any:
    """Common protection for every action on a person."""
    if target_id == admin.member_id:
        raise DomainError("admin_self_action", "You cannot take this action on your own account.", 403)
    target = await _member_row(db, target_id)
    target_roles = await _live_roles_of(db, target_id)
    if "owner" in target_roles:
        raise DomainError("admin_target_owner", "An owner's account can only be changed by removing the owner role first.", 403)
    if target_roles and not admin.can(R.ROLES_MANAGE):
        raise DomainError("admin_target_staff", "This person holds an administrative role; ask someone who manages roles.", 403)
    return target


async def _revoke_sessions(db: AsyncSession, member_id: UUID) -> int:
    result = await db.execute(
        text("UPDATE identity.session SET revoked_at = now() WHERE member_id = :m AND revoked_at IS NULL"),
        {"m": member_id},
    )
    return result.rowcount or 0


# --------------------------------------------------------------------------- members


async def search_members(
    db: AsyncSession, *, q: str | None, status: str | None, limit: int = 30, offset: int = 0
) -> dict[str, Any]:
    where = ["TRUE"]
    params: dict[str, Any] = {"limit": min(max(limit, 1), 100), "offset": max(offset, 0)}
    query = (q or "").strip()
    if query:
        digits = "".join(ch for ch in query if ch.isdigit())
        if len(digits) >= 5:
            where.append("m.phone_e164 LIKE :digits")
            params["digits"] = f"%{digits}%"
        else:
            where.append("(m.display_name ILIKE :like OR m.email ILIKE :prefix)")
            params["like"] = f"%{query}%"
            params["prefix"] = f"{query.lower()}%"
    if status in ("active", "suspended", "deleted"):
        where.append("m.status = CAST(:status AS identity.member_status)")
        params["status"] = status
    elif status == "not_joined":
        where.append("m.identity_level = 0")
    sql_where = " AND ".join(where)
    total = await db.scalar(text(f"SELECT count(*) FROM identity.member m WHERE {sql_where}"), params)
    rows = await db.execute(
        text(
            "SELECT m.id, m.display_name, m.phone_e164, m.email, m.identity_level, m.status::text AS status, m.created_at, "
            "(SELECT max(s.last_seen_at) FROM identity.session s WHERE s.member_id = m.id) AS last_seen_at, "
            f"(SELECT count(*) FROM governance.role_assignment a WHERE a.member_id = m.id AND {_LIVE}) AS role_count "
            f"FROM identity.member m WHERE {sql_where} ORDER BY m.created_at DESC LIMIT :limit OFFSET :offset"
        ),
        params,
    )
    return {
        "total": total,
        "members": [
            {
                "member_id": str(r.id),
                "display_name": r.display_name,
                "phone_hint": mask_phone(r.phone_e164) if r.phone_e164 else None,
                "email_hint": mask_email(r.email) if r.email else None,
                "status": r.status,
                "joined": r.identity_level >= 1,
                "created_at": _iso(r.created_at),
                "last_seen_at": _iso(r.last_seen_at),
                "is_staff": r.role_count > 0,
            }
            for r in rows
        ],
    }


async def member_detail(db: AsyncSession, member_id: UUID) -> dict[str, Any]:
    m = await _member_row(db, member_id)
    sessions = (
        await db.execute(
            text(
                "SELECT count(*) FILTER (WHERE revoked_at IS NULL AND expires_at > now()) AS active, "
                "max(last_seen_at) AS last_seen, min(created_at) AS first_sign_in FROM identity.session WHERE member_id = :m"
            ),
            {"m": member_id},
        )
    ).first()
    modules = await db.execute(
        text(
            "SELECT e.module_key, r.name, e.first_entered_at, e.last_entered_at, e.entry_count "
            "FROM registry.member_module_entry e JOIN registry.module r ON r.key = e.module_key "
            "WHERE e.member_id = :m ORDER BY e.last_entered_at DESC"
        ),
        {"m": member_id},
    )
    roles = await list_assignments(db, member_id=member_id)
    suspensions = await db.execute(
        text(
            "SELECT s.*, cm.display_name AS by_name, lm.display_name AS lifted_by_name FROM governance.suspension s "
            "LEFT JOIN identity.member cm ON cm.id = s.created_by LEFT JOIN identity.member lm ON lm.id = s.lifted_by "
            "WHERE s.member_id = :m ORDER BY s.starts_at DESC"
        ),
        {"m": member_id},
    )
    history = await audit_log(db, target=member_id, limit=30)
    pending = await list_approvals(db, status="pending", target=member_id)
    return {
        "member": {
            "member_id": str(m.id),
            "display_name": m.display_name,
            "phone_hint": mask_phone(m.phone_e164) if m.phone_e164 else None,
            "email_hint": mask_email(m.email) if m.email else None,
            "preferred_language": m.preferred_language,
            "identity_level": m.identity_level,
            "joined": m.identity_level >= 1,
            "status": m.status,
            "created_at": _iso(m.created_at),
        },
        "sessions": {
            "active": sessions.active,
            "last_seen_at": _iso(sessions.last_seen),
            "first_sign_in_at": _iso(sessions.first_sign_in),
        },
        "modules": [
            {
                "key": r.module_key,
                "name": r.name,
                "first_entered_at": _iso(r.first_entered_at),
                "last_entered_at": _iso(r.last_entered_at),
                "visits": r.entry_count,
            }
            for r in modules
        ],
        "roles": roles,
        "suspensions": [
            {
                "id": str(s.id),
                "kind": s.kind,
                "reason_code": s.reason_code,
                "note": s.note,
                "starts_at": _iso(s.starts_at),
                "ends_at": _iso(s.ends_at),
                "by": _person(s.created_by, s.by_name),
                "lifted_at": _iso(s.lifted_at),
                "lifted_by": _person(s.lifted_by, s.lifted_by_name),
                "lift_note": s.lift_note,
            }
            for s in suspensions
        ],
        "pending_approvals": pending,
        "history": history["events"],
    }


async def reveal_contact(db: AsyncSession, admin: Admin, member_id: UUID, *, note: str | None, ip: str) -> dict[str, Any]:
    admin.require(R.MEMBERS_CONTACT)
    m = await _member_row(db, member_id)
    await audit(db, actor=admin.member_id, action="member.contact_viewed", target=member_id, note=_clean(note), ip=ip)
    return {"phone_e164": m.phone_e164, "email": m.email}


async def _open_suspension(db: AsyncSession, member_id: UUID) -> Any:
    return (
        await db.execute(
            text("SELECT * FROM governance.suspension WHERE member_id = :m AND lifted_at IS NULL"), {"m": member_id}
        )
    ).first()


async def suspend(
    db: AsyncSession,
    admin: Admin,
    member_id: UUID,
    *,
    reason_code: str,
    note: str | None,
    days: int | None,
    ip: str,
) -> dict[str, Any]:
    admin.require(R.MEMBERS_SUSPEND)
    target = await _guard_target(db, admin, member_id)
    if target.status == "deleted":
        raise DomainError("member_deleted", "This account no longer exists.", 409)
    if days is not None and days not in R.SUSPENSION_DAYS:
        raise DomainError("validation_failed", "Choose one of the offered lengths.", 422)
    note = _clean(note)
    previous = await _open_suspension(db, member_id)
    if previous is not None:
        if previous.kind == "ban":
            raise DomainError("member_banned", "This member is banned; lift the ban before changing it.", 409)
        await db.execute(
            text(
                "UPDATE governance.suspension SET lifted_at = now(), lifted_by = :by, lift_note = 'Replaced by a new suspension.' "
                "WHERE id = :id"
            ),
            {"by": admin.member_id, "id": previous.id},
        )
    ends_at = datetime.now(UTC) + timedelta(days=days) if days else None
    await db.execute(
        text(
            "INSERT INTO governance.suspension (member_id, kind, reason_code, note, ends_at, created_by) "
            "VALUES (:m, 'suspension', :reason, :note, :ends, :by)"
        ),
        {"m": member_id, "reason": _reason(reason_code), "note": note, "ends": ends_at, "by": admin.member_id},
    )
    await db.execute(
        text("UPDATE identity.member SET status = 'suspended', updated_at = now() WHERE id = :m"), {"m": member_id}
    )
    signed_out = await _revoke_sessions(db, member_id)
    await audit(
        db,
        actor=admin.member_id,
        action="member.suspended",
        target=member_id,
        reason_code=reason_code,
        note=note,
        details={"days": days, "ends_at": ends_at, "sessions_ended": signed_out, "replaced": bool(previous)},
        ip=ip,
    )
    return await member_detail(db, member_id)


async def lift(db: AsyncSession, admin: Admin, member_id: UUID, *, note: str | None, ip: str) -> dict[str, Any]:
    admin.require(R.MEMBERS_SUSPEND)
    await _guard_target(db, admin, member_id)
    open_row = await _open_suspension(db, member_id)
    if open_row is None:
        raise DomainError("not_suspended", "This member is not suspended.", 409)
    if open_row.kind == "ban":
        # Undoing a ban is as serious as imposing one: only those who may decide bans.
        admin.require(R.APPROVALS_DECIDE)
    note = _clean(note)
    await db.execute(
        text("UPDATE governance.suspension SET lifted_at = now(), lifted_by = :by, lift_note = :note WHERE id = :id"),
        {"by": admin.member_id, "note": note, "id": open_row.id},
    )
    await db.execute(
        text("UPDATE identity.member SET status = 'active', updated_at = now() WHERE id = :m AND status = 'suspended'"),
        {"m": member_id},
    )
    await audit(
        db,
        actor=admin.member_id,
        action="member.ban_lifted" if open_row.kind == "ban" else "member.suspension_lifted",
        target=member_id,
        note=note,
        details={"suspension_id": open_row.id},
        ip=ip,
    )
    return await member_detail(db, member_id)


async def sign_out_everywhere(db: AsyncSession, admin: Admin, member_id: UUID, *, note: str | None, ip: str) -> dict[str, Any]:
    admin.require(R.MEMBERS_SUSPEND)
    await _guard_target(db, admin, member_id)
    note = _clean(note)
    count = await _revoke_sessions(db, member_id)
    await audit(
        db, actor=admin.member_id, action="member.signed_out", target=member_id, note=note, details={"sessions_ended": count}, ip=ip
    )
    return await member_detail(db, member_id)


async def expire_due_suspensions(db: AsyncSession) -> int:
    """Suspensions with an end date end on their own; the member can sign in again."""
    rows = list(
        await db.execute(
            text(
                "UPDATE governance.suspension SET lifted_at = ends_at, lift_note = 'Ended automatically.' "
                "WHERE lifted_at IS NULL AND kind = 'suspension' AND ends_at IS NOT NULL AND ends_at <= now() "
                "RETURNING id, member_id"
            )
        )
    )
    for row in rows:
        await db.execute(
            text("UPDATE identity.member SET status = 'active', updated_at = now() WHERE id = :m AND status = 'suspended'"),
            {"m": row.member_id},
        )
        await audit(db, actor=None, action="member.suspension_ended", target=row.member_id, details={"suspension_id": row.id})
    return len(rows)


# --------------------------------------------------------------------------- approvals (two-person rule)


async def _request_approval(
    db: AsyncSession, admin: Admin, *, kind: str, target: UUID, payload: dict[str, Any], reason_code: str, note: str, ip: str
) -> dict[str, Any]:
    import json

    existing = await db.scalar(
        text(
            "SELECT id FROM governance.approval_request WHERE status = 'pending' AND kind = :kind "
            "AND target_member_id = :t AND payload = CAST(:p AS jsonb)"
        ),
        {"kind": kind, "t": target, "p": json.dumps(payload, default=str)},
    )
    if existing:
        raise DomainError("approval_exists", "The same request is already waiting for a second person.", 409)
    row = (
        await db.execute(
            text(
                "INSERT INTO governance.approval_request (kind, target_member_id, payload, reason_code, note, requested_by) "
                "VALUES (:kind, :t, CAST(:p AS jsonb), :reason, :note, :by) RETURNING id"
            ),
            {
                "kind": kind,
                "t": target,
                "p": json.dumps(payload, default=str),
                "reason": reason_code,
                "note": note,
                "by": admin.member_id,
            },
        )
    ).first()
    await audit(
        db,
        actor=admin.member_id,
        action=f"approval.requested.{kind}",
        target=target,
        reason_code=reason_code,
        note=note,
        details={"approval_id": row.id, **payload},
        ip=ip,
    )
    return {"status": "approval_required", "approval_id": str(row.id)}


async def propose_ban(
    db: AsyncSession, admin: Admin, member_id: UUID, *, reason_code: str, note: str | None, ip: str
) -> dict[str, Any]:
    admin.require(R.MEMBERS_BAN)
    target = await _guard_target(db, admin, member_id)
    if target.status == "deleted":
        raise DomainError("member_deleted", "This account no longer exists.", 409)
    current = await _open_suspension(db, member_id)
    if current is not None and current.kind == "ban":
        raise DomainError("member_banned", "This member is already banned.", 409)
    return await _request_approval(
        db, admin, kind="ban", target=member_id, payload={}, reason_code=_reason(reason_code), note=_clean(note) or "", ip=ip
    )


async def list_approvals(db: AsyncSession, *, status: str | None = "pending", target: UUID | None = None) -> list[dict[str, Any]]:
    where = ["TRUE"]
    params: dict[str, Any] = {}
    if status:
        where.append("r.status = :status")
        params["status"] = status
    if target:
        where.append("r.target_member_id = :t")
        params["t"] = target
    rows = await db.execute(
        text(
            "SELECT r.*, tm.display_name AS target_name, rm.display_name AS requested_by_name, dm.display_name AS decided_by_name "
            "FROM governance.approval_request r JOIN identity.member tm ON tm.id = r.target_member_id "
            "JOIN identity.member rm ON rm.id = r.requested_by LEFT JOIN identity.member dm ON dm.id = r.decided_by "
            f"WHERE {' AND '.join(where)} ORDER BY r.requested_at DESC LIMIT 100"
        ),
        params,
    )
    return [
        {
            "id": str(r.id),
            "kind": r.kind,
            "target": _person(r.target_member_id, r.target_name),
            "payload": r.payload,
            "reason_code": r.reason_code,
            "note": r.note,
            "requested_by": _person(r.requested_by, r.requested_by_name),
            "requested_at": _iso(r.requested_at),
            "status": r.status,
            "decided_by": _person(r.decided_by, r.decided_by_name),
            "decided_at": _iso(r.decided_at),
            "decision_note": r.decision_note,
        }
        for r in rows
    ]


async def decide_approval(
    db: AsyncSession, admin: Admin, approval_id: UUID, *, decision: str, note: str | None, ip: str
) -> dict[str, Any]:
    row = (
        await db.execute(
            text("SELECT * FROM governance.approval_request WHERE id = :id FOR UPDATE"), {"id": approval_id}
        )
    ).first()
    if row is None:
        raise DomainError("approval_unknown", "No such request.", 404)
    if row.status != "pending":
        raise DomainError("approval_closed", "This request has already been decided.", 409)
    if decision == "withdrawn":
        if row.requested_by != admin.member_id:
            raise DomainError("admin_forbidden", "Only the person who asked can withdraw a request.", 403)
    else:
        admin.require(R.APPROVALS_DECIDE)
        if decision not in ("approved", "declined"):
            raise DomainError("validation_failed", "Approve or decline.", 422)
        if row.requested_by == admin.member_id:
            raise DomainError("approval_four_eyes", "A second person must decide a request you made.", 403)
        if row.target_member_id == admin.member_id:
            raise DomainError("admin_self_action", "You cannot decide a request about yourself.", 403)
    note = _clean(note, required=decision == "declined")
    if decision == "approved":
        if row.kind == "ban":
            await _apply_ban(db, row, decided_by=admin.member_id, ip=ip)
        elif row.kind == "grant_role":
            p = row.payload
            await _insert_assignment(
                db,
                member_id=row.target_member_id,
                role=p["role"],
                scope_kind=p["scope_kind"],
                scope_key=p.get("scope_key"),
                title=p.get("title"),
                ends_at=datetime.fromisoformat(p["ends_at"]) if p.get("ends_at") else None,
                granted_by=row.requested_by,
                note=row.note,
                approval_id=row.id,
            )
            await audit(
                db,
                actor=admin.member_id,
                action="role.granted",
                target=row.target_member_id,
                note=row.note,
                details={**p, "approval_id": row.id, "requested_by": row.requested_by},
                ip=ip,
            )
    await db.execute(
        text(
            "UPDATE governance.approval_request SET status = :s, decided_by = :by, decided_at = now(), decision_note = :note "
            "WHERE id = :id"
        ),
        {"s": decision, "by": admin.member_id, "note": note, "id": approval_id},
    )
    await audit(
        db,
        actor=admin.member_id,
        action=f"approval.{decision}.{row.kind}",
        target=row.target_member_id,
        note=note,
        details={"approval_id": row.id},
        ip=ip,
    )
    return (await list_approvals(db, status=None, target=row.target_member_id))[0]


async def _apply_ban(db: AsyncSession, row: Any, *, decided_by: UUID, ip: str) -> None:
    member_id = row.target_member_id
    if "owner" in await _live_roles_of(db, member_id):
        raise DomainError("admin_target_owner", "An owner cannot be banned.", 403)
    current = await _open_suspension(db, member_id)
    if current is not None:
        await db.execute(
            text("UPDATE governance.suspension SET lifted_at = now(), lifted_by = :by, lift_note = 'Replaced by a ban.' WHERE id = :id"),
            {"by": decided_by, "id": current.id},
        )
    await db.execute(
        text(
            "INSERT INTO governance.suspension (member_id, kind, reason_code, note, created_by, approval_id) "
            "VALUES (:m, 'ban', :reason, :note, :by, :approval)"
        ),
        {"m": member_id, "reason": row.reason_code, "note": row.note, "by": row.requested_by, "approval": row.id},
    )
    await db.execute(text("UPDATE identity.member SET status = 'suspended', updated_at = now() WHERE id = :m"), {"m": member_id})
    signed_out = await _revoke_sessions(db, member_id)
    revoked = await db.execute(
        text(
            "UPDATE governance.role_assignment SET revoked_at = now(), revoked_by = :by, revoke_note = 'Member banned.' "
            "WHERE member_id = :m AND revoked_at IS NULL RETURNING role"
        ),
        {"by": decided_by, "m": member_id},
    )
    await audit(
        db,
        actor=decided_by,
        action="member.banned",
        target=member_id,
        reason_code=row.reason_code,
        note=row.note,
        details={"approval_id": row.id, "requested_by": row.requested_by, "sessions_ended": signed_out, "roles_removed": [r.role for r in revoked]},
        ip=ip,
    )


# --------------------------------------------------------------------------- roles


async def list_assignments(db: AsyncSession, *, member_id: UUID | None = None, include_ended: bool = False) -> list[dict[str, Any]]:
    where = ["TRUE"] if include_ended else [_LIVE.replace("a.starts_at <= now() AND ", "")]
    params: dict[str, Any] = {}
    if member_id:
        where.append("a.member_id = :m")
        params["m"] = member_id
    rows = await db.execute(
        text(
            "SELECT a.*, m.display_name, m.status::text AS member_status, g.display_name AS granted_by_name, "
            "coalesce(c.name, r.name) AS scope_name "
            "FROM governance.role_assignment a JOIN identity.member m ON m.id = a.member_id "
            "LEFT JOIN identity.member g ON g.id = a.granted_by "
            "LEFT JOIN governance.chapter c ON a.scope_kind = 'chapter' AND c.key = a.scope_key "
            "LEFT JOIN registry.module r ON a.scope_kind = 'module' AND r.key = a.scope_key "
            f"WHERE {' AND '.join(where)} ORDER BY a.created_at"
        ),
        params,
    )
    order = {k: i for i, k in enumerate(R.ROLE_ORDER)}
    result = [
        {
            "id": str(r.id),
            "member": {"member_id": str(r.member_id), "display_name": r.display_name, "status": r.member_status},
            "role": r.role,
            "scope_kind": r.scope_kind,
            "scope_key": r.scope_key,
            "scope_name": r.scope_name,
            "title": r.title,
            "starts_at": _iso(r.starts_at),
            "ends_at": _iso(r.ends_at),
            "granted_by": _person(r.granted_by, r.granted_by_name),
            "grant_note": r.grant_note,
            "revoked_at": _iso(r.revoked_at),
        }
        for r in rows
    ]
    return sorted(result, key=lambda a: (order.get(a["role"], 99), a["scope_name"] or "", a["member"]["display_name"]))


async def _insert_assignment(
    db: AsyncSession,
    *,
    member_id: UUID,
    role: str,
    scope_kind: str,
    scope_key: str | None,
    title: str | None,
    ends_at: datetime | None,
    granted_by: UUID,
    note: str,
    approval_id: UUID | None = None,
) -> UUID:
    exists = await db.scalar(
        text(
            "SELECT 1 FROM governance.role_assignment WHERE member_id = :m AND role = :role AND scope_kind = :sk "
            "AND coalesce(scope_key, '') = coalesce(:key, '') AND revoked_at IS NULL"
        ),
        {"m": member_id, "role": role, "sk": scope_kind, "key": scope_key},
    )
    if exists:
        raise DomainError("role_exists", "This person already holds that role there.", 409)
    return await db.scalar(
        text(
            "INSERT INTO governance.role_assignment (member_id, role, scope_kind, scope_key, title, ends_at, granted_by, "
            "grant_note, approval_id) VALUES (:m, :role, :sk, :key, :title, :ends, :by, :note, :approval) RETURNING id"
        ),
        {
            "m": member_id,
            "role": role,
            "sk": scope_kind,
            "key": scope_key,
            "title": title,
            "ends": ends_at,
            "by": granted_by,
            "note": note,
            "approval": approval_id,
        },
    )


async def grant_role(
    db: AsyncSession,
    admin: Admin,
    *,
    member_id: UUID,
    role: str,
    scope_key: str | None,
    title: str | None,
    ends_at: datetime | None,
    note: str | None,
    ip: str,
) -> dict[str, Any]:
    definition = R.ROLES.get(role)
    if definition is None:
        raise DomainError("role_unknown", "No such role.", 422)
    scope_kind = definition.scope_kind
    if scope_kind == "platform":
        scope_key = None
    elif not scope_key:
        raise DomainError("validation_failed", "Choose where this role applies.", 422)
    elif scope_kind == "module":
        if scope_key not in await _module_keys(db):
            raise DomainError("scope_unknown", "No such module.", 422)
    elif not await db.scalar(
        text("SELECT 1 FROM governance.chapter WHERE key = :k AND archived_at IS NULL"), {"k": scope_key}
    ):
        raise DomainError("scope_unknown", "No such chapter.", 422)

    # Who may appoint whom.
    if role == "owner":
        if not admin.is_owner:
            raise DomainError("admin_forbidden", "Only an owner can appoint another owner.", 403)
    elif not admin.can(R.ROLES_MANAGE) and not (scope_kind == "chapter" and scope_key in admin.managed_chapters):
        raise DomainError("admin_forbidden", "Your role does not allow appointing this role.", 403)
    if member_id == admin.member_id:
        raise DomainError("admin_self_action", "You cannot appoint yourself.", 403)
    target = await _member_row(db, member_id)
    if target.status != "active":
        raise DomainError("member_inactive", "Only an active member can be appointed.", 409)
    if ends_at is not None and ends_at <= datetime.now(UTC):
        raise DomainError("validation_failed", "The term must end in the future.", 422)
    note = _clean(note) or ""
    title = (title or "").strip()[:60] or None

    if definition.sensitive and not admin.is_owner:
        return await _request_approval(
            db,
            admin,
            kind="grant_role",
            target=member_id,
            payload={"role": role, "scope_kind": scope_kind, "scope_key": scope_key, "title": title, "ends_at": _iso(ends_at)},
            reason_code="other",
            note=note,
            ip=ip,
        )
    assignment_id = await _insert_assignment(
        db,
        member_id=member_id,
        role=role,
        scope_kind=scope_kind,
        scope_key=scope_key,
        title=title,
        ends_at=ends_at,
        granted_by=admin.member_id,
        note=note,
    )
    await audit(
        db,
        actor=admin.member_id,
        action="role.granted",
        target=member_id,
        module_key=scope_key if scope_kind == "module" else None,
        note=note,
        details={"assignment_id": assignment_id, "role": role, "scope_kind": scope_kind, "scope_key": scope_key, "title": title, "ends_at": ends_at},
        ip=ip,
    )
    return {"status": "granted", "assignment_id": str(assignment_id)}


async def revoke_role(db: AsyncSession, admin: Admin, assignment_id: UUID, *, note: str | None, ip: str) -> dict[str, Any]:
    row = (
        await db.execute(
            text("SELECT * FROM governance.role_assignment WHERE id = :id AND revoked_at IS NULL FOR UPDATE"), {"id": assignment_id}
        )
    ).first()
    if row is None:
        raise DomainError("role_unknown", "This appointment has already ended.", 404)
    stepping_down = row.member_id == admin.member_id
    if row.role == "owner":
        if not admin.is_owner:
            raise DomainError("admin_forbidden", "Only an owner can remove an owner.", 403)
        owners = await db.scalar(
            text(f"SELECT count(*) FROM governance.role_assignment a WHERE a.role = 'owner' AND {_LIVE}")
        )
        if owners <= 1:
            raise DomainError("last_owner", "ForKhatri must always have at least one owner.", 409)
    elif not stepping_down and not admin.can(R.ROLES_MANAGE) and not (
        row.scope_kind == "chapter" and row.scope_key in admin.managed_chapters
    ):
        raise DomainError("admin_forbidden", "Your role does not allow removing this appointment.", 403)
    note = _clean(note)
    await db.execute(
        text("UPDATE governance.role_assignment SET revoked_at = now(), revoked_by = :by, revoke_note = :note WHERE id = :id"),
        {"by": admin.member_id, "note": note, "id": assignment_id},
    )
    await audit(
        db,
        actor=admin.member_id,
        action="role.revoked",
        target=row.member_id,
        module_key=row.scope_key if row.scope_kind == "module" else None,
        note=note,
        details={"assignment_id": row.id, "role": row.role, "scope_kind": row.scope_kind, "scope_key": row.scope_key},
        ip=ip,
    )
    return {"status": "revoked"}


# --------------------------------------------------------------------------- organisation


_OFFICE_ROLES = ("president", "secretary", "treasurer")


async def organisation(db: AsyncSession) -> dict[str, Any]:
    chapters = await db.execute(
        text("SELECT key, name, kind, parent_key, created_at FROM governance.chapter WHERE archived_at IS NULL ORDER BY name")
    )
    assignments = await list_assignments(db)
    return {
        # Elected samaj office bearers, apart from the people who run the platform itself.
        "national": [a for a in assignments if a["scope_kind"] == "platform" and a["role"] in _OFFICE_ROLES],
        "staff": [a for a in assignments if a["scope_kind"] == "platform" and a["role"] not in _OFFICE_ROLES],
        "chapters": [
            {
                "key": c.key,
                "name": c.name,
                "kind": c.kind,
                "parent_key": c.parent_key,
                "office_bearers": [a for a in assignments if a["scope_kind"] == "chapter" and a["scope_key"] == c.key],
            }
            for c in chapters
        ],
        "modules": [a for a in assignments if a["scope_kind"] == "module"],
    }


def _slug(name: str) -> str:
    import re
    import unicodedata

    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")[:50]


async def create_chapter(
    db: AsyncSession, admin: Admin, *, name: str, kind: str, parent_key: str | None, ip: str
) -> dict[str, Any]:
    name = (name or "").strip()
    if not 2 <= len(name) <= 80:
        raise DomainError("validation_failed", "Give the chapter a name.", 422)
    if kind not in ("state", "city"):
        raise DomainError("validation_failed", "A chapter is a state or a city.", 422)
    if kind == "state":
        admin.require(R.ORG_MANAGE)
        parent_key = None
    else:
        if not parent_key:
            raise DomainError("validation_failed", "Choose the state this city belongs to.", 422)
        parent = (await db.execute(text("SELECT kind FROM governance.chapter WHERE key = :k AND archived_at IS NULL"), {"k": parent_key})).first()
        if parent is None or parent.kind != "state":
            raise DomainError("scope_unknown", "Choose the state this city belongs to.", 422)
        if not admin.can(R.ORG_MANAGE) and parent_key not in admin.managed_chapters:
            raise DomainError("admin_forbidden", "Your role does not allow adding chapters here.", 403)
    base = _slug(name) or "chapter"
    key = base if kind == "state" else f"{parent_key}-{base}"[:60]
    if await db.scalar(text("SELECT 1 FROM governance.chapter WHERE key = :k"), {"k": key}):
        raise DomainError("chapter_exists", "A chapter with this name already exists.", 409)
    await db.execute(
        text("INSERT INTO governance.chapter (key, name, kind, parent_key, created_by) VALUES (:k, :n, :kind, :p, :by)"),
        {"k": key, "n": name, "kind": kind, "p": parent_key, "by": admin.member_id},
    )
    await audit(db, actor=admin.member_id, action="org.chapter_created", subject=key, details={"name": name, "kind": kind, "parent_key": parent_key}, ip=ip)
    return {"key": key}


async def archive_chapter(db: AsyncSession, admin: Admin, key: str, *, note: str | None, ip: str) -> dict[str, Any]:
    admin.require(R.ORG_MANAGE)
    if await db.scalar(text("SELECT 1 FROM governance.chapter WHERE parent_key = :k AND archived_at IS NULL"), {"k": key}):
        raise DomainError("chapter_has_children", "Close the city chapters under this state first.", 409)
    if await db.scalar(
        text("SELECT 1 FROM governance.role_assignment WHERE scope_kind = 'chapter' AND scope_key = :k AND revoked_at IS NULL"),
        {"k": key},
    ):
        raise DomainError("chapter_has_bearers", "End the office bearers' terms in this chapter first.", 409)
    note = _clean(note)
    result = await db.execute(
        text("UPDATE governance.chapter SET archived_at = now() WHERE key = :k AND archived_at IS NULL"), {"k": key}
    )
    if not result.rowcount:
        raise DomainError("scope_unknown", "No such chapter.", 404)
    await audit(db, actor=admin.member_id, action="org.chapter_closed", subject=key, note=note, ip=ip)
    return {"status": "closed"}


# --------------------------------------------------------------------------- modules


async def list_modules(db: AsyncSession) -> list[dict[str, Any]]:
    rows = await db.execute(
        text(
            "SELECT r.key, r.name, r.availability, r.sort_order, r.updated_at, "
            "(SELECT count(*) FROM registry.member_module_entry e WHERE e.module_key = r.key) AS members "
            "FROM registry.module r ORDER BY r.sort_order"
        )
    )
    return [
        {"key": r.key, "name": r.name, "availability": r.availability, "members": r.members, "updated_at": _iso(r.updated_at)}
        for r in rows
    ]


async def set_module_availability(
    db: AsyncSession, admin: Admin, key: str, *, availability: str, note: str | None, ip: str
) -> list[dict[str, Any]]:
    admin.require(R.MODULES_MANAGE)
    if availability not in ("available", "in_development", "planned"):
        raise DomainError("validation_failed", "Unknown availability.", 422)
    note = _clean(note)
    before = await db.scalar(text("SELECT availability FROM registry.module WHERE key = :k"), {"k": key})
    if before is None:
        raise DomainError("scope_unknown", "No such module.", 404)
    await db.execute(
        text("UPDATE registry.module SET availability = :a, updated_at = now() WHERE key = :k"), {"a": availability, "k": key}
    )
    await audit(
        db, actor=admin.member_id, action="module.availability_changed", module_key=key, note=note,
        details={"from": before, "to": availability}, ip=ip,
    )
    return await list_modules(db)


# --------------------------------------------------------------------------- today


async def overview(db: AsyncSession, admin: Admin) -> dict[str, Any]:
    await expire_due_suspensions(db)
    counts = (
        await db.execute(
            text(
                "SELECT count(*) AS total, count(*) FILTER (WHERE status = 'suspended') AS suspended, "
                "count(*) FILTER (WHERE identity_level = 0) AS not_joined, "
                "count(*) FILTER (WHERE created_at > now() - interval '7 days') AS new_7d FROM identity.member WHERE status <> 'deleted'"
            )
        )
    ).first()
    active_7d = await db.scalar(
        text("SELECT count(DISTINCT member_id) FROM identity.session WHERE last_seen_at > now() - interval '7 days'")
    )
    pending = await list_approvals(db, status="pending") if (admin.can(R.APPROVALS_DECIDE) or admin.can(R.MEMBERS_BAN) or admin.can(R.ROLES_MANAGE)) else []
    ending_suspensions = await db.execute(
        text(
            "SELECT s.member_id, m.display_name, s.ends_at, s.reason_code FROM governance.suspension s "
            "JOIN identity.member m ON m.id = s.member_id WHERE s.lifted_at IS NULL AND s.ends_at IS NOT NULL "
            "AND s.ends_at < now() + interval '7 days' ORDER BY s.ends_at LIMIT 20"
        )
    )
    terms = await db.execute(
        text(
            "SELECT a.id, a.role, a.scope_kind, a.scope_key, a.ends_at, m.id AS member_id, m.display_name "
            "FROM governance.role_assignment a JOIN identity.member m ON m.id = a.member_id "
            "WHERE a.revoked_at IS NULL AND a.ends_at IS NOT NULL AND a.ends_at > now() "
            "AND a.ends_at < now() + interval '30 days' ORDER BY a.ends_at LIMIT 20"
        )
    )
    recent = await audit_log(db, limit=8) if admin.can(R.AUDIT_VIEW) else {"events": []}
    return {
        "members": {
            "total": counts.total,
            "suspended": counts.suspended,
            "not_joined": counts.not_joined,
            "new_7d": counts.new_7d,
            "active_7d": active_7d,
        },
        "approvals": [
            {**a, "can_decide": admin.can(R.APPROVALS_DECIDE) and a["requested_by"]["member_id"] != str(admin.member_id)}
            for a in pending
        ],
        "suspensions_ending": [
            {"member": _person(r.member_id, r.display_name), "ends_at": _iso(r.ends_at), "reason_code": r.reason_code}
            for r in ending_suspensions
        ],
        "terms_ending": [
            {
                "assignment_id": str(r.id),
                "member": _person(r.member_id, r.display_name),
                "role": r.role,
                "scope_kind": r.scope_kind,
                "scope_key": r.scope_key,
                "ends_at": _iso(r.ends_at),
            }
            for r in terms
        ],
        "recent": recent["events"],
    }
