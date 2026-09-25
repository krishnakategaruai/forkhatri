"""Notification endpoints (rework contract §3):
`GET /notifications?for_candidate=` and `POST /notifications/read`.

Titles and bodies are rendered here, in the reader's language, from the
row's `kind` and non-identifying `payload` (SP098) — nothing prose is stored.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import AuthenticatedAccount, DbSession, Locale
from app.components.authorization import interface as authz
from app.components.authorization.context import AuthorizationDenied
from app.components.notification_bridge import interface as notifications
from app.i18n import translate

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    id: str
    kind: str
    title: str
    body: str
    link: str | None
    created_at: str
    read_at: str | None
    payload: dict


def _render(
    n: notifications.Notification, lang: str, open_names: dict[str, str] | None = None
) -> tuple[str, str]:
    p = dict(n.payload)
    relationship = str(p.get("sent_by_relationship") or p.get("relationship") or "")
    if relationship and relationship != "self":
        p["relationship_text"] = translate(f"home_circle.relationship.{relationship}", lang)
    else:
        p["relationship_text"] = ""
    if n.kind == "request_received":
        # "Siddharth (32, Hyderabad)" when they opened their first name,
        # "A new match (32, Hyderabad)" when not — never a bare list of facts.
        name = (open_names or {}).get(str(p.get("subject_account_id") or ""))
        facts = ", ".join(
            str(v)
            for v in (p.get("age"), str(p.get("locality") or "").split(",")[0].strip())
            if v
        )
        lead = name or translate("notifications.someone", lang)
        p["who"] = f"{lead} ({facts})" if facts else lead
        body_key = (
            "notifications.request_received.bodyFamily"
            if relationship and relationship != "self"
            else "notifications.request_received.body"
        )
        return translate("notifications.request_received.title", lang), translate(body_key, lang, **p)
    if n.kind == "request_accepted":
        p["other_name"] = p.get("other_name") or translate("notifications.someone", lang)
    if n.kind == "invitation_received":
        body_key = (
            "notifications.invitation_received.bodyToCandidate"
            if p.get("direction") == "to_candidate"
            else "notifications.invitation_received.body"
        )
        return translate("notifications.invitation_received.title", lang), translate(body_key, lang, **p)
    title_key, body_key = f"notifications.{n.kind}.title", f"notifications.{n.kind}.body"
    title, body = translate(title_key, lang), translate(body_key, lang, **p)
    # A kind with no catalog entry (older rows, a new event not yet worded)
    # must never show its raw key: a plain generic line instead.
    if title == title_key:
        title = translate("notifications.generic.title", lang)
    if body == body_key:
        body = str(p.get("message") or "") or translate("notifications.generic.body", lang)
    return title, body


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
    for_candidate: UUID | None = None,
) -> list[NotificationResponse]:
    """[Contract §3] The caller's own notifications in one context: their
    personal ones by default, or those about a candidate their circle helps."""
    try:
        ctx = await authz.resolve_context_account(
            session, acting_account_id=account_id, for_candidate=for_candidate
        )
    except AuthorizationDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from exc
    rows = await notifications.list_for(session, account_id=account_id, subject_account_id=ctx)
    from app.components.discovery import interface as discovery

    senders = {
        UUID(str(n.payload["subject_account_id"]))
        for n in rows
        if n.kind == "request_received" and n.payload.get("subject_account_id")
    }
    opened = await discovery.open_cards_for(session, account_ids=list(senders)) if senders else {}
    open_names = {str(k): v.first_name for k, v in opened.items() if v.first_name}
    out = []
    for n in rows:
        title, body = _render(n, lang, open_names)
        out.append(
            NotificationResponse(
                id=str(n.id),
                kind=n.kind,
                title=title,
                body=body,
                link=n.link,
                created_at=n.created_at.isoformat(),
                read_at=n.read_at.isoformat() if n.read_at else None,
                payload={k: (str(v) if not isinstance(v, (int, float, bool)) and v is not None else v) for k, v in n.payload.items()},
            )
        )
    return out


class ReadRequest(BaseModel):
    ids: list[str] | None = None
    for_candidate: str | None = None


class ReadResponse(BaseModel):
    marked: int


@router.post("/read", response_model=ReadResponse)
async def mark_read(
    body: ReadRequest, session: DbSession, account_id: AuthenticatedAccount
) -> ReadResponse:
    """Mark the given ids read; with no ids, everything unread in the context
    (every context when no `for_candidate` is given either)."""
    ctx = None
    if body.for_candidate:
        try:
            ctx = await authz.resolve_context_account(
                session, acting_account_id=account_id, for_candidate=UUID(body.for_candidate)
            )
        except AuthorizationDenied as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from exc
    marked = await notifications.mark_read(
        session,
        account_id=account_id,
        ids=[UUID(i) for i in body.ids] if body.ids else None,
        subject_account_id=ctx,
    )
    return ReadResponse(marked=marked)
