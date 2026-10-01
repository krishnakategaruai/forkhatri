"""The consultation workspace: state, notes, action items, files, recording
consent, and the WebSocket that carries WebRTC signalling + live updates."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app import db, identity
from app.components import audit, bookings, storage, workspace
from app.errors import DomainError, forbidden, not_found
from app.identity import Actor, current_actor, ws_actor
from app.settings import get_settings

router = APIRouter(tags=["room"])

OPEN_BEFORE = timedelta(minutes=15)


async def _booking_for(booking_id: UUID, member_id: UUID) -> tuple[dict, str]:
    b = await db.fetchrow("SELECT * FROM booking WHERE id=$1", booking_id)
    if not b:
        raise not_found("booking")
    b = dict(b)
    role = bookings.participant(b, member_id)
    return b, role


def _room_open(b: dict) -> bool:
    now = datetime.now(timezone.utc)
    return b["status"] in ("confirmed", "in_progress") and now >= b["starts_at"] - OPEN_BEFORE and now <= b["ends_at"] + timedelta(hours=2)


@router.get("/bookings/{booking_id}/room")
async def room_state(booking_id: UUID, actor: Actor = Depends(current_actor)):
    b, role = await _booking_for(booking_id, actor.member_id)
    names = await identity.display_names([b["provider_id"], b["seeker_id"]])
    shared = await db.fetchrow("SELECT body, version, updated_at FROM note WHERE booking_id=$1 AND owner_id IS NULL", booking_id)
    private = await db.fetchrow("SELECT body, version FROM note WHERE booking_id=$1 AND owner_id=$2", booking_id, actor.member_id)
    actions = db.rows(await db.fetch("SELECT id, text, owner_id, done, created_by, created_at FROM action_item WHERE booking_id=$1 ORDER BY created_at", booking_id))
    files = db.rows(await db.fetch("SELECT id, owner_id, name, mime, size_bytes, created_at, is_recording FROM file WHERE booking_id=$1 AND deleted_at IS NULL ORDER BY created_at", booking_id))
    consents = [str(r["member_id"]) for r in await db.fetch("SELECT member_id FROM recording_consent WHERE booking_id=$1", booking_id)]
    r = workspace.room(booking_id)
    return {
        "booking": {k: b[k] for k in ("id", "status", "starts_at", "ends_at", "service_title", "duration_min", "recording_allowed", "formats", "brief", "provider_id", "seeker_id")},
        "role": role, "me": actor.id, "names": names, "open": _room_open(b) or b["status"] == "completed",
        "live": _room_open(b), "ice_servers": get_settings().ice_server_list,
        "shared_note": dict(shared) if shared else {"body": "", "version": 0},
        "private_note": dict(private) if private else {"body": "", "version": 0},
        "actions": actions, "files": files, "consents": consents, "recording": r.recording, "present": r.members(),
    }


class NoteIn(BaseModel):
    body: str = Field(max_length=50000)
    version: int = 0
    private: bool = False


@router.put("/bookings/{booking_id}/note")
async def save_note(booking_id: UUID, body: NoteIn, actor: Actor = Depends(current_actor)):
    b, _ = await _booking_for(booking_id, actor.member_id)
    owner = actor.member_id if body.private else None
    async with db.tx() as conn:
        if owner:
            row = await conn.fetchrow(
                "INSERT INTO note (booking_id, owner_id, body, updated_by, version) VALUES ($1,$2,$3,$2,1) "
                "ON CONFLICT (booking_id, owner_id) WHERE owner_id IS NOT NULL DO UPDATE SET body=$3, updated_at=now(), version=note.version+1 RETURNING version",
                booking_id, owner, body.body)
        else:
            row = await conn.fetchrow(
                "INSERT INTO note (booking_id, owner_id, body, updated_by, version) VALUES ($1,NULL,$2,$3,1) "
                "ON CONFLICT (booking_id) WHERE owner_id IS NULL DO UPDATE SET body=$2, updated_by=$3, updated_at=now(), version=note.version+1 RETURNING version",
                booking_id, body.body, actor.member_id)
    if not owner:
        await workspace.broadcast(booking_id, {"type": "note", "body": body.body, "version": row["version"], "by": actor.id})
    return {"version": row["version"]}


class ActionIn(BaseModel):
    text: str = Field(min_length=1, max_length=300)
    owner_id: UUID | None = None


@router.post("/bookings/{booking_id}/actions", status_code=201)
async def add_action(booking_id: UUID, body: ActionIn, actor: Actor = Depends(current_actor)):
    await _booking_for(booking_id, actor.member_id)
    row = await db.fetchrow("INSERT INTO action_item (booking_id, text, owner_id, created_by) VALUES ($1,$2,$3,$4) RETURNING id, text, owner_id, done, created_by, created_at",
                            booking_id, body.text, body.owner_id, actor.member_id)
    await workspace.broadcast(booking_id, {"type": "action", "action": dict(row)})
    return dict(row)


class ActionPatch(BaseModel):
    done: bool


@router.patch("/bookings/{booking_id}/actions/{action_id}")
async def patch_action(booking_id: UUID, action_id: UUID, body: ActionPatch, actor: Actor = Depends(current_actor)):
    await _booking_for(booking_id, actor.member_id)
    row = await db.fetchrow("UPDATE action_item SET done=$3 WHERE id=$1 AND booking_id=$2 RETURNING id, text, owner_id, done, created_by, created_at", action_id, booking_id, body.done)
    if row:
        await workspace.broadcast(booking_id, {"type": "action", "action": dict(row)})
    return dict(row) if row else {}


@router.delete("/bookings/{booking_id}/actions/{action_id}")
async def delete_action(booking_id: UUID, action_id: UUID, actor: Actor = Depends(current_actor)):
    await _booking_for(booking_id, actor.member_id)
    await db.execute("DELETE FROM action_item WHERE id=$1 AND booking_id=$2", action_id, booking_id)
    await workspace.broadcast(booking_id, {"type": "action_removed", "id": str(action_id)})
    return {"ok": True}


ALLOWED_MIME = re.compile(r"^(image/(png|jpeg|webp|gif)|application/pdf|text/plain|text/csv|application/(vnd\.openxmlformats-officedocument\.[a-z.]+|msword|vnd\.ms-excel|vnd\.ms-powerpoint|zip|json))$")


@router.post("/bookings/{booking_id}/files", status_code=201)
async def upload(booking_id: UUID, file: UploadFile = File(...), actor: Actor = Depends(current_actor)):
    await _booking_for(booking_id, actor.member_id)
    s = get_settings()
    mime = file.content_type or "application/octet-stream"
    if not ALLOWED_MIME.match(mime):
        raise DomainError("file_type", "That file type is not allowed.", 422)
    data = await file.read()
    if len(data) > s.max_upload_mb * 1024 * 1024:
        raise DomainError("file_too_large", f"Files up to {s.max_upload_mb} MB.", 422)
    key, scanned = storage.save_private(str(booking_id), data)
    name = Path(file.filename or "file").name[:120]
    async with db.tx() as conn:
        row = await conn.fetchrow("INSERT INTO file (booking_id, owner_id, name, mime, size_bytes, storage_key, encrypted, scan_status) VALUES ($1,$2,$3,$4,$5,$6,true,$7) "
                                  "RETURNING id, owner_id, name, mime, size_bytes, created_at",
                                  booking_id, actor.member_id, name, mime, len(data), key, scanned)
        await conn.execute("INSERT INTO message (booking_id, sender_id, kind, body, file_id) VALUES ($1,$2,'file',$3,$4)", booking_id, actor.member_id, name, row["id"])
        await audit.record(conn, actor.member_id, "file.uploaded", "booking", booking_id, {"file_id": str(row["id"]), "bytes": len(data)})
    await workspace.broadcast(booking_id, {"type": "file", "file": dict(row)})
    return dict(row)


@router.get("/bookings/{booking_id}/files/{file_id}")
async def download(booking_id: UUID, file_id: UUID, actor: Actor = Depends(current_actor)):
    await _booking_for(booking_id, actor.member_id)   # backend authorization, never only the UI
    f = await db.fetchrow("SELECT * FROM file WHERE id=$1 AND booking_id=$2 AND deleted_at IS NULL", file_id, booking_id)
    if not f:
        raise not_found("file")
    await db.execute("INSERT INTO audit_log (actor_id, action, target_kind, target_id, detail) VALUES ($1,'file.accessed','file',$2,'{}')", actor.member_id, str(file_id))
    return storage.serve(f["storage_key"], f["encrypted"], f["mime"], f["name"])


@router.delete("/bookings/{booking_id}/files/{file_id}")
async def delete_file(booking_id: UUID, file_id: UUID, actor: Actor = Depends(current_actor)):
    await _booking_for(booking_id, actor.member_id)
    n = await db.execute("UPDATE file SET deleted_at=now() WHERE id=$1 AND booking_id=$2 AND owner_id=$3", file_id, booking_id, actor.member_id)
    if n.endswith("0"):
        raise forbidden("Only the uploader can remove a file.")
    await workspace.broadcast(booking_id, {"type": "file_removed", "id": str(file_id)})
    return {"ok": True}


@router.post("/bookings/{booking_id}/recordings", status_code=201)
async def upload_recording(booking_id: UUID, file: UploadFile = File(...), actor: Actor = Depends(current_actor)):
    """A recording made in the room (both consented, indicator shown to both).
    Stored as a private consultation file visible only to the two participants."""
    b, _ = await _booking_for(booking_id, actor.member_id)
    both = {b["seeker_id"], b["provider_id"]}
    consents = {r["member_id"] for r in await db.fetch("SELECT member_id FROM recording_consent WHERE booking_id=$1", booking_id)}
    if not b["recording_allowed"] or not both <= consents:
        raise DomainError("consent_required", "Both people must allow recording first.", 409)
    mime = (file.content_type or "").split(";")[0]
    if mime not in ("video/webm", "audio/webm", "video/mp4"):
        raise DomainError("file_type", "That file type is not allowed.", 422)
    data = await file.read()
    if len(data) > 500 * 1024 * 1024:
        raise DomainError("file_too_large", "Recording is too large.", 422)
    key, scanned = storage.save_private(str(booking_id), data, ".webm")
    title = re.sub(r"[^A-Za-z0-9]+", "-", b["service_title"]).strip("-")[:40] or "consultation"
    name = f"{title}-{b['starts_at'].date().isoformat()}.webm"
    async with db.tx() as conn:
        row = await conn.fetchrow("INSERT INTO file (booking_id, owner_id, name, mime, size_bytes, storage_key, is_recording, encrypted, scan_status) VALUES ($1,$2,$3,$4,$5,$6,true,true,$7) "
                                  "RETURNING id, owner_id, name, mime, size_bytes, created_at, is_recording", booking_id, actor.member_id, name, mime, len(data), key, scanned)
        await audit.record(conn, actor.member_id, "recording.saved", "booking", booking_id, {"file_id": str(row["id"]), "bytes": len(data)})
    await workspace.broadcast(booking_id, {"type": "file", "file": dict(row)})
    return dict(row)


class CallFeedbackIn(BaseModel):
    good: bool
    issues: list[str] = Field(default_factory=list, max_length=6)


CALL_ISSUES = {"audio", "video", "screen", "connection", "echo", "other"}


@router.post("/bookings/{booking_id}/call-feedback")
async def call_feedback(booking_id: UUID, body: CallFeedbackIn, actor: Actor = Depends(current_actor)):
    """Quick thumbs after a call (Teams-style), used to improve the room."""
    await _booking_for(booking_id, actor.member_id)
    issues = [i for i in body.issues if i in CALL_ISSUES]
    await db.execute("INSERT INTO call_feedback (booking_id, member_id, good, issues) VALUES ($1,$2,$3,$4) "
                     "ON CONFLICT (booking_id, member_id) DO UPDATE SET good=$3, issues=$4, created_at=now()",
                     booking_id, actor.member_id, body.good, issues)
    return {"ok": True}


@router.post("/bookings/{booking_id}/recording-consent")
async def consent(booking_id: UUID, actor: Actor = Depends(current_actor)):
    b, _ = await _booking_for(booking_id, actor.member_id)
    if not b["recording_allowed"]:
        raise DomainError("recording_not_allowed", "Recording is not available for this consultation.", 409)
    async with db.tx() as conn:
        await conn.execute("INSERT INTO recording_consent (booking_id, member_id) VALUES ($1,$2) ON CONFLICT DO NOTHING", booking_id, actor.member_id)
        await audit.record(conn, actor.member_id, "recording.consented", "booking", booking_id)
    consents = [str(r["member_id"]) for r in await db.fetch("SELECT member_id FROM recording_consent WHERE booking_id=$1", booking_id)]
    await workspace.broadcast(booking_id, {"type": "consents", "consents": consents})
    return {"consents": consents}


# --- WebSocket ---------------------------------------------------------------------------

@router.websocket("/ws/bookings/{booking_id}")
async def socket(ws: WebSocket, booking_id: UUID):
    actor = await ws_actor(ws)
    if actor is None:
        await ws.close(code=4401)
        return
    b = await db.fetchrow("SELECT * FROM booking WHERE id=$1", booking_id)
    if not b or actor.member_id not in (b["seeker_id"], b["provider_id"]):
        await ws.close(code=4403)
        return
    b = dict(b)
    await ws.accept()
    me = actor.id
    room = await workspace.join(booking_id, me, ws)
    if b["status"] == "confirmed" and _room_open(b):
        async with db.tx() as conn:
            await bookings.start(conn, booking_id)
    await db.execute("INSERT INTO session_event (booking_id, member_id, kind) VALUES ($1,$2,'joined')", booking_id, actor.member_id)
    await workspace.broadcast(booking_id, {"type": "presence", "present": room.members(), "recording": room.recording, "sharing": room.sharing})
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            t = msg.get("type")
            if t in ("offer", "answer", "ice", "ready", "media"):
                # Relay to the other party only. Media never touches the server.
                other = str(b["provider_id"] if actor.member_id == b["seeker_id"] else b["seeker_id"])
                await workspace.send_to(booking_id, other, {**msg, "from": me})
            elif t == "recording":
                consents = {str(r["member_id"]) for r in await db.fetch("SELECT member_id FROM recording_consent WHERE booking_id=$1", booking_id)}
                both = {str(b["seeker_id"]), str(b["provider_id"])}
                if msg.get("on") and not (b["recording_allowed"] and both <= consents):
                    await ws.send_text(json.dumps({"type": "error", "code": "consent_required"}))
                    continue
                room.recording = bool(msg.get("on"))
                await db.execute("INSERT INTO session_event (booking_id, member_id, kind) VALUES ($1,$2,$3)", booking_id, actor.member_id,
                                 "recording_started" if room.recording else "recording_stopped")
                await workspace.broadcast(booking_id, {"type": "recording", "on": room.recording, "by": me})
            elif t == "sharing":
                room.sharing = me if msg.get("on") else None
                await workspace.broadcast(booking_id, {"type": "sharing", "sharing": room.sharing})
            elif t == "typing":
                await workspace.broadcast(booking_id, {"type": "typing", "from": me}, exclude=ws)
            elif t == "ping":
                await ws.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        pass
    finally:
        await workspace.leave(booking_id, me, ws)
        await db.execute("INSERT INTO session_event (booking_id, member_id, kind) VALUES ($1,$2,'left')", booking_id, actor.member_id)
        r = workspace.room(booking_id)
        await workspace.broadcast(booking_id, {"type": "presence", "present": r.members(), "recording": r.recording, "sharing": r.sharing})
