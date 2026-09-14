"""Home Circle endpoints — FR007/FR008/FR009/FR010/FR014/FR016.

Thin HTTP layer over `components/home_circle/interface.py`, matching this
project's standing convention (`api/routes/auth.py`'s own header comment).

Every "own circle" route (`/home-circle/*` without a candidate id in the
path) treats `AuthenticatedAccount` as the candidate — this pass's frontend
is scoped to a candidate managing their own circle (see `interface.py`'s
module docstring for the recorded scope cut on the family-member-acting-on-
someone-else's-circle side of FR014/FR016, which the backend still supports
via `membership_id`-addressed routes below).
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import AuthenticatedAccount, DbSession, Locale
from app.components.home_circle import interface as home_circle
from app.components.home_circle.models import RelationshipType
from app.i18n import translate

router = APIRouter(prefix="/home-circle", tags=["home_circle"])


def _not_found(lang: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=translate("home_circle.error.notFound", lang),
    )


class InviteRequest(BaseModel):
    invitee_identifier: str
    relationship_type: Literal["parent", "sibling", "relative"]


class InviteResponse(BaseModel):
    invitation_id: str


@router.post("/invite", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
async def invite(
    body: InviteRequest, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> InviteResponse:
    """[FR007/TR007] Invite someone into the caller's own Home Circle."""
    try:
        invitation_id = await home_circle.invite(
            session,
            inviter_account_id=account_id,
            candidate_account_id=account_id,
            invitee_identifier=body.invitee_identifier,
            relationship_type=RelationshipType(body.relationship_type),
        )
    except home_circle.InviteSelf as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("home_circle.error.inviteSelf", lang),
        ) from exc
    except home_circle.AlreadyMember as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=translate("home_circle.error.alreadyInvited", lang),
        ) from exc
    except home_circle.RateLimited as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=translate("home_circle.error.rateLimited", lang),
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    return InviteResponse(invitation_id=str(invitation_id))


class PendingInvitationResponse(BaseModel):
    id: str
    candidate_account_id: str
    inviter_account_id: str
    relationship_type: str
    created_at: str
    expires_at: str | None


@router.get("/invitations/pending", response_model=list[PendingInvitationResponse])
async def list_pending_invitations(
    session: DbSession, account_id: AuthenticatedAccount
) -> list[PendingInvitationResponse]:
    """[FR008] Invitations addressed to the caller's own phone/email."""
    rows = await home_circle.list_pending_invitations(session, account_id=account_id)
    return [
        PendingInvitationResponse(
            id=str(r.id),
            candidate_account_id=str(r.candidate_account_id),
            inviter_account_id=str(r.inviter_account_id),
            relationship_type=r.relationship_type.value,
            created_at=r.created_at.isoformat(),
            expires_at=r.expires_at.isoformat() if r.expires_at else None,
        )
        for r in rows
    ]


@router.post("/invitations/{invitation_id}/accept", status_code=status.HTTP_201_CREATED)
async def accept_invitation(
    invitation_id: UUID, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> dict[str, str]:
    """[FR008/TR008] Accept — creates the membership, grants `family_info`."""
    try:
        membership_id = await home_circle.accept_invitation(
            session, invitation_id=invitation_id, account_id=account_id
        )
    except home_circle.InvitationNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=translate("home_circle.error.invitationNotFound", lang),
        ) from exc
    return {"membership_id": str(membership_id)}


@router.post("/invitations/{invitation_id}/decline", status_code=status.HTTP_204_NO_CONTENT)
async def decline_invitation(
    invitation_id: UUID, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> None:
    """[FR009] Decline."""
    try:
        await home_circle.decline_invitation(
            session, invitation_id=invitation_id, account_id=account_id
        )
    except home_circle.InvitationNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=translate("home_circle.error.invitationNotFound", lang),
        ) from exc


class MemberResponse(BaseModel):
    membership_id: str
    member_account_id: str
    relationship_type: str
    status: str
    joined_at: str


@router.get("/members", response_model=list[MemberResponse])
async def list_members(
    session: DbSession, account_id: AuthenticatedAccount
) -> list[MemberResponse]:
    """[FR012-adjacent read] The caller's own active Home Circle members."""
    rows = await home_circle.list_home_circle(session, candidate_account_id=account_id)
    return [
        MemberResponse(
            membership_id=str(m.membership_id),
            member_account_id=str(m.member_account_id),
            relationship_type=m.relationship_type.value,
            status=m.status.value,
            joined_at=m.joined_at.isoformat(),
        )
        for m in rows
    ]


@router.delete("/members/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    membership_id: UUID, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> None:
    """[FR010/TR010] The candidate removes a member. RLS (`hc_membership_participants`)
    is what actually restricts this to the real candidate — see `interface.py`'s
    `remove_member()` docstring."""
    try:
        await home_circle.remove_member(session, membership_id=membership_id)
    except home_circle.NotFound as exc:
        raise _not_found(lang) from exc


@router.post("/members/{membership_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave(
    membership_id: UUID, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> None:
    """[FR010/M01-C §9] A member leaves voluntarily — no approval required."""
    try:
        await home_circle.leave(session, membership_id=membership_id)
    except home_circle.NotFound as exc:
        raise _not_found(lang) from exc


class SuggestRequest(BaseModel):
    membership_id: str
    suggested_profile_id: str
    note: str | None = None


@router.post("/suggest", status_code=status.HTTP_201_CREATED)
async def suggest(
    body: SuggestRequest, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> dict[str, str]:
    """[FR014/TR014] A Home Circle member suggests a profile to the candidate
    whose circle `membership_id` belongs to — never a decision, never a
    connection request (see `interface.py`'s module docstring)."""
    membership_id = UUID(body.membership_id)
    candidate_account_id = await home_circle.get_membership_candidate(
        session, membership_id=membership_id
    )
    if candidate_account_id is None:
        raise _not_found(lang)
    suggestion_id = await home_circle.suggest(
        session,
        member_account_id=account_id,
        membership_id=membership_id,
        candidate_account_id=candidate_account_id,
        suggested_profile_id=UUID(body.suggested_profile_id),
        note=body.note,
    )
    return {"suggestion_id": str(suggestion_id)}


class SuggestionResponse(BaseModel):
    id: str
    suggested_profile_id: str
    suggested_by_relationship_type: str
    note: str | None
    created_at: str


@router.get("/suggestions", response_model=list[SuggestionResponse])
async def list_suggestions(
    session: DbSession,
    account_id: AuthenticatedAccount,
    candidate_account_id: UUID | None = None,
) -> list[SuggestionResponse]:
    """[FR014] Suggestions for one circle — the caller's own by default, or
    (via `candidate_account_id`) a circle the caller is a family member of.
    `suggested_profile_id` is deliberately just an id here: the frontend
    resolves it through `GET /discovery/snippet/{id}`, the same
    pre-connection-safe demographic snippet used everywhere else — never a
    name or photo (see `interface.py`'s `list_suggestions()` docstring)."""
    rows = await home_circle.list_suggestions(
        session,
        caller_account_id=account_id,
        candidate_account_id=candidate_account_id or account_id,
    )
    return [
        SuggestionResponse(
            id=str(s.id),
            suggested_profile_id=str(s.suggested_profile_id),
            suggested_by_relationship_type=s.suggested_by_relationship_type.value,
            note=s.note,
            created_at=s.created_at.isoformat(),
        )
        for s in rows
    ]


class NoteRequest(BaseModel):
    membership_id: str
    content: str


@router.post("/notes", status_code=status.HTTP_201_CREATED)
async def write_note(
    body: NoteRequest, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> dict[str, str]:
    """[FR016] A family-only private note — visible to its author (and other
    family members with `family_info` scope) until the candidate approves
    forwarding it."""
    membership_id = UUID(body.membership_id)
    candidate_account_id = await home_circle.get_membership_candidate(
        session, membership_id=membership_id
    )
    if candidate_account_id is None:
        raise _not_found(lang)
    note_id = await home_circle.write_note(
        session,
        member_account_id=account_id,
        membership_id=membership_id,
        candidate_account_id=candidate_account_id,
        content=body.content,
    )
    return {"note_id": str(note_id)}


class NoteResponse(BaseModel):
    id: str
    content: str
    forwarded_at: str | None
    created_at: str


@router.get("/notes", response_model=list[NoteResponse])
async def list_notes(
    session: DbSession,
    account_id: AuthenticatedAccount,
    candidate_account_id: UUID | None = None,
) -> list[NoteResponse]:
    """Notes for one circle — the caller's own by default, or (via the
    `candidate_account_id` query param) a circle the caller is a family
    member of. Family members see everything in that circle; the candidate
    sees only notes already forwarded to them (RLS draws that line, not this
    route)."""
    rows = await home_circle.list_notes(
        session,
        caller_account_id=account_id,
        candidate_account_id=candidate_account_id or account_id,
    )
    return [
        NoteResponse(
            id=str(n.id),
            content=n.content,
            forwarded_at=n.forwarded_at.isoformat() if n.forwarded_at else None,
            created_at=n.created_at.isoformat(),
        )
        for n in rows
    ]


class PendingNoteResponse(BaseModel):
    id: str
    created_at: str


@router.get("/notes/pending", response_model=list[PendingNoteResponse])
async def list_pending_notes(
    session: DbSession, account_id: AuthenticatedAccount
) -> list[PendingNoteResponse]:
    """[FR016] The candidate's own not-yet-approved notes — id and timestamp
    only, never content (see `interface.py`'s `list_pending_notes()`)."""
    rows = await home_circle.list_pending_notes(session)
    return [PendingNoteResponse(id=str(r.id), created_at=r.created_at.isoformat()) for r in rows]


@router.post("/notes/{note_id}/forward", status_code=status.HTTP_204_NO_CONTENT)
async def forward_note(
    note_id: UUID, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> None:
    """[FR016] The candidate approves forwarding one specific note to
    themselves — see `interface.py`'s `forward_note()` for why this is
    candidate-only despite the RLS policy's own broader `USING` clause."""
    try:
        await home_circle.forward_note(session, note_id=note_id)
    except home_circle.NotFound as exc:
        raise _not_found(lang) from exc
