"""Who is here, what they can do, and their personal lists."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from pydantic import BaseModel

from app import db
from app.components import privacy, providers
from app.i18n import request_language
from app.identity import Actor, current_actor, mint_ticket
from app.settings import get_settings

router = APIRouter(tags=["me"])


@router.get("/me")
async def me(actor: Actor = Depends(current_actor)):
    p = await db.fetchrow("SELECT status FROM provider WHERE member_id=$1", actor.member_id)
    unread = await db.fetchval("SELECT count(*) FROM notification WHERE member_id=$1 AND read_at IS NULL", actor.member_id)
    upcoming = await db.fetchval(
        "SELECT count(*) FROM booking WHERE (seeker_id=$1 OR provider_id=$1) AND status IN ('confirmed','in_progress') AND ends_at > now()", actor.member_id)
    return {
        "member_id": actor.id, "display_name": actor.display_name, "language": actor.language,
        "is_admin": actor.is_admin, "provider_status": p["status"] if p else None,
        "unread": unread, "upcoming": upcoming,
        "entrance_url": get_settings().forkhatri_entrance_url,
    }


@router.post("/me/ws-ticket")
async def ws_ticket(actor: Actor = Depends(current_actor)):
    return {"ticket": mint_ticket(actor)}


@router.get("/me/export")
async def export_my_data(actor: Actor = Depends(current_actor)):
    async with db.tx() as conn:
        data = await privacy.export(conn, actor.member_id)
    return Response(privacy.dumps(data), media_type="application/json",
                    headers={"Content-Disposition": 'attachment; filename="counsel-my-data.json"'})


@router.get("/me/deletion-check")
async def deletion_check(actor: Actor = Depends(current_actor)):
    async with db.pool().acquire() as conn:
        return {"blockers": await privacy.blockers(conn, actor.member_id)}


class DeleteIn(BaseModel):
    confirm: str


_delete_attempts: dict[str, list[float]] = {}


def _rate_limit_delete(member_id: str) -> None:
    """3 attempts per hour per member (contract: ACCOUNT-DELETION.md)."""
    import time
    from app.errors import DomainError
    now = time.monotonic()
    hits = [h for h in _delete_attempts.get(member_id, []) if h > now - 3600]
    if len(hits) >= 3:
        raise DomainError("rate_limited", "Too many attempts. Try again in an hour.", 429)
    hits.append(now)
    _delete_attempts[member_id] = hits


@router.post("/me/delete-account-data")
@router.post("/me/delete")
async def delete_my_data(body: DeleteIn, actor: Actor = Depends(current_actor)):
    """Kind B deletion: everything Counsel holds about the signed-in member, immediately.
    The ForKhatri account and other modules are untouched. (/me/delete is the older path.)"""
    from app.errors import DomainError
    if body.confirm.strip().upper() != "DELETE":
        raise DomainError("confirm_required", "Type DELETE to confirm.", 422)
    _rate_limit_delete(actor.id)
    result = await privacy.erase_member(actor.member_id, "member_request")
    return {**result, "erased": True, "signed_out": True}


@router.get("/me/saved")
async def saved(request: Request, actor: Actor = Depends(current_actor)):
    lang = request_language(request)
    ids = await db.fetch("SELECT provider_id FROM saved_provider WHERE member_id=$1 ORDER BY created_at DESC", actor.member_id)
    async with db.pool().acquire() as conn:
        return [c for r in ids if (c := await providers.card(conn, r["provider_id"], lang, actor.member_id))]


@router.put("/me/saved/{provider_id}")
async def save(provider_id: UUID, actor: Actor = Depends(current_actor)):
    await db.execute("INSERT INTO saved_provider (member_id, provider_id) VALUES ($1,$2) ON CONFLICT DO NOTHING", actor.member_id, provider_id)
    return {"saved": True}


@router.delete("/me/saved/{provider_id}")
async def unsave(provider_id: UUID, actor: Actor = Depends(current_actor)):
    await db.execute("DELETE FROM saved_provider WHERE member_id=$1 AND provider_id=$2", actor.member_id, provider_id)
    return {"saved": False}


@router.get("/me/notifications")
async def notifications(actor: Actor = Depends(current_actor)):
    rows = await db.fetch("SELECT id, kind, params, booking_id, read_at, created_at FROM notification WHERE member_id=$1 ORDER BY id DESC LIMIT 50", actor.member_id)
    return db.rows(rows)


@router.post("/me/notifications/read")
async def mark_read(actor: Actor = Depends(current_actor)):
    await db.execute("UPDATE notification SET read_at=now() WHERE member_id=$1 AND read_at IS NULL", actor.member_id)
    return {"ok": True}


@router.post("/me/blocks/{member_id}")
async def block(member_id: UUID, actor: Actor = Depends(current_actor)):
    await db.execute("INSERT INTO block (member_id, blocked_id) VALUES ($1,$2) ON CONFLICT DO NOTHING", actor.member_id, member_id)
    return {"blocked": True}


@router.delete("/me/blocks/{member_id}")
async def unblock(member_id: UUID, actor: Actor = Depends(current_actor)):
    await db.execute("DELETE FROM block WHERE member_id=$1 AND blocked_id=$2", actor.member_id, member_id)
    return {"blocked": False}
