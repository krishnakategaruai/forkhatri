"""Messaging endpoints + WebSocket (owner decision 2026-09-14).

REST for state, WebSocket for liveness. The socket carries only events
(new message, reaction, typing, presence/expression); the source of truth is
always the database read through RLS.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentMember, DbSession, IdempotencyKeyHeader, Locale, origin_allowed, resolve_member_identity
from app.components.connect import chat
from app.components.identity_bridge import interface as identity
from app.config.settings import get_settings
from app.db.engine import get_process_session_factory
from app.db.session import set_member_context
from app.i18n import translate
from app.idempotency import idempotent
from app.rate_limiting import RateLimitScope, enforce

router = APIRouter(prefix="/chats", tags=["chat"])


class DirectRequest(BaseModel):
    member_id: UUID


class GroupRequest(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    member_ids: list[UUID] = Field(min_length=1, max_length=50)


class SendRequest(BaseModel):
    kind: str = "text"
    body: str | None = Field(default=None, max_length=2000)
    expression: str | None = None


class ReactionRequest(BaseModel):
    emoji: str


class PresenceRequest(BaseModel):
    expression: str | None = None
    at_occurrence_id: UUID | None = None


def _person(p: chat.Person) -> dict:
    return {
        "member_id": str(p.member_id),
        "display_name": p.display_name,
        "avatar": p.avatar,
        "active": p.active,
        "expression": p.expression,
        "last_seen_at": p.last_seen_at.isoformat() if p.last_seen_at else None,
    }


def _context(x: chat.SharedContext | None) -> dict | None:
    if x is None:
        return None
    return {"kind": x.kind, "title": x.title, "ref": x.ref, "starts_at": x.starts_at.isoformat() if x.starts_at else None, "locality": x.locality}


def _conv(c: chat.Conversation, me: UUID) -> dict:
    others = [p for p in c.members if p.member_id != me]
    title = c.title or ", ".join(p.display_name for p in others) or "…"
    return {
        "id": str(c.id),
        "kind": c.kind,
        "title": title,
        "members": [_person(p) for p in c.members],
        "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
        "last_preview": c.last_preview,
        "unread": c.unread,
        "avatar": others[0].avatar if c.kind == "direct" and others else None,
        "active": any(p.active for p in others),
        "expression": others[0].expression if c.kind == "direct" and others else None,
        "context": _context(c.context),
    }


def _msg(m: chat.Message) -> dict:
    return {
        "id": str(m.id),
        "conversation_id": str(m.conversation_id),
        "member_id": str(m.member_id),
        "display_name": m.display_name,
        "avatar": m.avatar,
        "kind": m.kind,
        "body": m.body,
        "media_url": m.media_url,
        "expression": m.expression,
        "created_at": m.created_at.isoformat(),
        "mine": m.mine,
        "reactions": {k: [str(x) for x in v] for k, v in m.reactions.items()},
    }


@router.get("")
async def list_chats(session: DbSession, member: CurrentMember) -> dict:
    convs = await chat.list_conversations(session, me=member.member_id)
    return {"conversations": [_conv(c, member.member_id) for c in convs], "expressions": list(chat.EXPRESSIONS), "reactions": list(chat.REACTIONS)}


@router.get("/unread")
async def unread(session: DbSession, member: CurrentMember) -> dict:
    return {"unread": await chat.total_unread(session, me=member.member_id)}


@router.post("/direct", status_code=201)
async def open_direct(body: DirectRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    try:
        cid = await chat.open_direct(session, me=member.member_id, other=body.member_id)
    except chat.NotAllowed as exc:
        raise HTTPException(status_code=403, detail=translate("chat.notAllowed", lang)) from exc
    return {"id": str(cid)}


@router.post("/group", status_code=201)
async def create_group(body: GroupRequest, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    await enforce(session, scope=RateLimitScope.CIRCLE_CREATE, subject=str(member.member_id), limit_max=20, window_seconds=3600)
    try:
        cid = await chat.create_group(session, me=member.member_id, title=body.title, others=body.member_ids)
    except chat.NotAllowed as exc:
        raise HTTPException(status_code=403, detail=translate("chat.notAllowed", lang)) from exc
    except chat.InvalidInput as exc:
        raise HTTPException(status_code=422, detail={"fields": ["title", "member_ids"]}) from exc
    return {"id": str(cid)}


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: UUID, session: DbSession, member: CurrentMember, lang: Locale, after: datetime | None = None) -> dict:
    try:
        c = await chat.conversation(session, conversation_id=conversation_id, me=member.member_id)
        msgs = await chat.messages(session, conversation_id=conversation_id, me=member.member_id, after=after)
    except (chat.NotFound, chat.NotAllowed) as exc:
        raise HTTPException(status_code=404, detail=translate("common.notFound", lang)) from exc
    conv = _conv(c, member.member_id)
    here = chat.hub.present_in(conversation_id)
    for p in conv["members"]:
        p["here"] = UUID(p["member_id"]) in here  # in this chat now; `active` stays the app-wide heartbeat
    return {"conversation": conv, "messages": [_msg(m) for m in msgs], "reactions": list(chat.REACTIONS), "expressions": list(chat.EXPRESSIONS)}


@router.post("/{conversation_id}/messages", status_code=201)
async def send_message(conversation_id: UUID, body: SendRequest, session: DbSession, member: CurrentMember, lang: Locale, idem: IdempotencyKeyHeader) -> dict:
    await enforce(session, scope=RateLimitScope.MESSAGE_POST, subject=str(member.member_id), limit_max=120, window_seconds=600)
    try:
        async with idempotent(
            session,
            actor_member_id=member.member_id,
            idempotency_key=idem,
            endpoint="POST /chats/messages",
            request_payload={"c": str(conversation_id), "b": body.body, "k": body.kind, "e": body.expression},
        ) as outcome:
            if not outcome.replayed:
                m = await chat.send(session, conversation_id=conversation_id, me=member.member_id, kind=body.kind, body=body.body, expression=body.expression)
                payload = _msg(m)
                outcome.set_result(201, payload)
                chat.hub.publish(conversation_id, {"type": "message", "message": {**payload, "mine": False}})
                chat.hub.publish_to_members(
                    [i for i in await chat.member_ids(session, conversation_id) if i != member.member_id], {"type": "inbox", "conversation_id": str(conversation_id)}
                )
        return outcome.response
    except chat.NotAllowed as exc:
        raise HTTPException(status_code=403, detail=translate("chat.notAllowed", lang)) from exc
    except chat.InvalidInput as exc:
        raise HTTPException(status_code=422, detail={"fields": ["body"]}) from exc


@router.post("/{conversation_id}/photos", status_code=201)
async def send_photo(conversation_id: UUID, session: DbSession, member: CurrentMember, lang: Locale, photo: Annotated[UploadFile, File()]) -> dict:
    await enforce(session, scope=RateLimitScope.PHOTO_UPLOAD, subject=str(member.member_id), limit_max=60, window_seconds=3600)
    try:
        ref = await chat.store_photo(conversation_id, photo)
        m = await chat.send(session, conversation_id=conversation_id, me=member.member_id, kind="photo", body=None, expression=None, media_ref=ref)
    except chat.NotAllowed as exc:
        raise HTTPException(status_code=403, detail=translate("chat.notAllowed", lang)) from exc
    except chat.InvalidInput as exc:
        raise HTTPException(status_code=415, detail=translate("moments.unsupported", lang)) from exc
    payload = _msg(m)
    chat.hub.publish(conversation_id, {"type": "message", "message": {**payload, "mine": False}})
    return payload


@router.delete("/{conversation_id}/messages/{message_id}", status_code=204)
async def retract(conversation_id: UUID, message_id: UUID, session: DbSession, member: CurrentMember) -> None:
    await chat.retract(session, message_id=message_id, me=member.member_id)
    chat.hub.publish(conversation_id, {"type": "retract", "message_id": str(message_id)})


@router.post("/{conversation_id}/messages/{message_id}/reactions")
async def react(conversation_id: UUID, message_id: UUID, body: ReactionRequest, session: DbSession, member: CurrentMember) -> dict:
    try:
        present = await chat.toggle_reaction(session, message_id=message_id, me=member.member_id, emoji=body.emoji)
    except chat.InvalidInput as exc:
        raise HTTPException(status_code=422, detail={"fields": ["emoji"]}) from exc
    chat.hub.publish(conversation_id, {"type": "reaction", "message_id": str(message_id), "member_id": str(member.member_id), "emoji": body.emoji, "present": present})
    return {"present": present}


@router.post("/{conversation_id}/read", status_code=204)
async def read(conversation_id: UUID, session: DbSession, member: CurrentMember) -> None:
    await chat.mark_read(session, conversation_id=conversation_id, me=member.member_id)


presence_router = APIRouter(prefix="/presence", tags=["chat"])


@presence_router.post("", status_code=204)
async def presence(body: PresenceRequest, session: DbSession, member: CurrentMember) -> None:
    """Heartbeat every ~30 s while the app is open; carries the current expression (a word, never an image)."""
    await chat.heartbeat(session, me=member.member_id, expression=body.expression, at_occurrence_id=body.at_occurrence_id)


# --- WebSocket ---------------------------------------------------------------------

ws_router = APIRouter()


@ws_router.websocket("/ws/chat")
async def chat_socket(ws: WebSocket, conversation: str | None = None, member: str | None = None) -> None:
    """Live events for one conversation (or the inbox when no conversation is given).
    Identity [ParentApp TR15]: the browser sends the ForKhatri `fk_session` cookie on the handshake and it is
    resolved exactly like HTTP (`deps.resolve_member_identity`). `member` is honoured only as the legacy
    development stand-in when `dev_identity_enabled` is explicitly on. The Origin must be a Milavn web origin,
    because a cookie-authenticated socket is otherwise open to cross-site hijacking."""
    settings = get_settings()
    if not origin_allowed(ws.headers.get("origin"), settings):
        await ws.close(code=4403)
        return
    try:
        conv_id = UUID(conversation) if conversation else None
    except ValueError:
        await ws.close(code=4400)
        return
    try:
        ident = await resolve_member_identity(ws.cookies, member, settings)
    except identity.IdentityServiceUnavailable:
        await ws.close(code=1013)  # try again later; never a default member
        return
    if ident is None:
        await ws.close(code=4401)
        return
    member_id = ident.member_id
    if conv_id is not None:
        factory = get_process_session_factory()
        async with factory() as s, s.begin():
            await set_member_context(s, member_id, list(ident.scopes))
            if not await chat.is_member(s, conv_id, member_id):
                await ws.close(code=4403)
                return
    await ws.accept()
    q = chat.hub.subscribe(conv_id, member_id)
    if conv_id is not None:
        chat.hub.publish(conv_id, {"type": "presence", "member_id": str(member_id), "active": True})

    async def pump() -> None:
        while True:
            event = await q.get()
            await ws.send_text(json.dumps(event, default=str))

    task = asyncio.create_task(pump())
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            kind = msg.get("type")
            if conv_id is None:
                continue
            if kind == "typing":
                chat.hub.publish(conv_id, {"type": "typing", "member_id": str(member_id)})
            elif kind == "expression" and msg.get("value") in chat.EXPRESSIONS:
                chat.hub.publish(conv_id, {"type": "presence", "member_id": str(member_id), "active": True, "expression": msg["value"]})
                factory = get_process_session_factory()
                async with factory() as s, s.begin():
                    await set_member_context(s, member_id, list(ident.scopes))
                    await chat.heartbeat(s, me=member_id, expression=msg["value"], at_occurrence_id=None)
    except WebSocketDisconnect:
        pass
    finally:
        task.cancel()
        chat.hub.unsubscribe(conv_id, member_id, q)
        # A second tab (or a dev double-mount) still open means the person is still here.
        if conv_id is not None and member_id not in chat.hub.present_in(conv_id):
            chat.hub.publish(conv_id, {"type": "presence", "member_id": str(member_id), "active": False})


__all__ = ["router", "presence_router", "ws_router", "status"]
