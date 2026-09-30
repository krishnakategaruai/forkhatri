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

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import AuthenticatedAccount, DbSession, Locale
from app.components.connection import interface as connection  # noqa: E402
from app.components.discovery import interface as discovery  # noqa: E402
from app.components.home_circle import interface as home_circle
from app.components.home_circle.models import RELATION_ROLE, RelationshipType
from app.components.profile import interface as profile  # noqa: E402
from app.i18n import translate

router = APIRouter(prefix="/home-circle", tags=["home_circle"])


def _not_found(lang: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=translate("home_circle.error.notFound", lang),
    )


class InviteRequest(BaseModel):
    """[Rework contract §3/§6, DEC-V1-018] Three invite paths, one request:

    * candidate → family: no `for_candidate`, `direction` `to_member`.
    * member → relative: `for_candidate` names a circle the caller is already
      an active member of; the invitee joins THAT circle.
    * family → candidate: `direction` `to_candidate`; the invitee is the
      candidate, and the caller asks to join their circle as
      `relationship_type` — how a parent starts their child's circle.

    The invitee is a person found by `GET /home-circle/people` (account id) or
    a typed phone/email."""

    invitee_identifier: str | None = None
    invitee_account_id: UUID | None = None
    # [Migration 040] The exact relation (mother, paternal_uncle, …) of the
    # MEMBER to the candidate. When given, the role is derived from it and any
    # `relationship_type` sent alongside is ignored, so the two cannot disagree.
    relation: str | None = None
    relationship_type: Literal["parent", "guardian", "sibling", "relative"] | None = None
    for_candidate: UUID | None = None
    direction: Literal["to_member", "to_candidate"] = "to_member"


class InviteResponse(BaseModel):
    invitation_id: str


@router.post("/invite", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
async def invite(
    body: InviteRequest, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> InviteResponse:
    """[FR007/TR007] Invite someone into a Home Circle (see `InviteRequest`)."""
    if body.relation is not None and body.relation not in RELATION_ROLE:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="unknown relation")
    role = RELATION_ROLE[body.relation] if body.relation else (
        RelationshipType(body.relationship_type) if body.relationship_type else None
    )
    if role is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="relation required")
    candidate_account_id = account_id
    if body.direction == "to_member" and body.for_candidate and body.for_candidate != account_id:
        # Member → relative: only someone already in that circle may add to it.
        contexts = await home_circle.list_member_contexts(session, account_id=account_id)
        if not any(c.candidate_account_id == body.for_candidate for c in contexts):
            raise _not_found(lang)
        candidate_account_id = body.for_candidate
    try:
        invitation_id = await home_circle.invite(
            session,
            inviter_account_id=account_id,
            candidate_account_id=candidate_account_id,
            invitee_identifier=body.invitee_identifier,
            invitee_account_id=body.invitee_account_id,
            relationship_type=role,
            direction=body.direction,
            relation=body.relation,
        )
    except home_circle.CandidateNotOnForKhatri as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=translate("home_circle.error.candidateNotFound", lang),
        ) from exc
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
    direction: str = "to_member"
    inviter_name: str | None = None
    candidate_name: str | None = None
    relation: str | None = None


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
            direction=r.direction,
            inviter_name=r.inviter_name,
            candidate_name=r.candidate_name,
            relation=r.relation,
        )
        for r in rows
    ]


class PersonResponse(BaseModel):
    account_id: str
    display_name: str | None
    phone_masked: str | None
    has_profile: bool


@router.get("/people", response_model=list[PersonResponse])
async def search_people(
    q: str, session: DbSession, account_id: AuthenticatedAccount
) -> list[PersonResponse]:
    """[Rework contract §6] ForKhatri members by name or phone, to invite.
    Never the caller; phone masked; at most 20 rows."""
    del account_id  # authentication only
    rows = await home_circle.search_people(session, q=q)
    return [
        PersonResponse(
            account_id=str(r.account_id),
            display_name=r.display_name,
            phone_masked=r.phone_masked,
            has_profile=r.has_profile,
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
    member_name: str | None = None
    relation: str | None = None
    # [Migration 047] The member's own Mangalya photo, when they have added one.
    member_photo_url: str | None = None


@router.get("/members", response_model=list[MemberResponse])
async def list_members(
    session: DbSession,
    account_id: AuthenticatedAccount,
    candidate_account_id: UUID | None = None,
    for_candidate: UUID | None = None,
) -> list[MemberResponse]:
    """[FR012-adjacent read] One circle's active Home Circle members — the
    caller's own by default, or (via `candidate_account_id`) the circle of a
    candidate the caller is a family member of, which is what the parent-role
    Circle screen draws. Same parameter shape as `/suggestions` above."""
    # `for_candidate` is the name the web client sends (lib/homeCircle.ts);
    # it was silently ignored, so a parent always read their own, empty circle.
    circle_of = candidate_account_id or for_candidate or account_id
    members = await home_circle.list_circle_for(
        session, caller_account_id=account_id, candidate_account_id=circle_of
    )
    from app.components.profile import interface as profile_module
    from app.components.profile.storage import resolve_url

    photos = await profile_module.member_photo_refs(
        session, account_ids=[m.member_account_id for m in members]
    )
    return [
        MemberResponse(
            membership_id=str(m.membership_id),
            member_account_id=str(m.member_account_id),
            relationship_type=m.relationship_type.value,
            status="active",
            joined_at=m.joined_at.isoformat(),
            member_name=m.member_name,
            relation=m.relation,
            member_photo_url=(
                resolve_url(photos[m.member_account_id]) if m.member_account_id in photos else None
            ),
        )
        for m in members
    ]


class RelationRequest(BaseModel):
    relation: str


@router.patch("/members/{membership_id}/relation", status_code=status.HTTP_204_NO_CONTENT)
async def set_member_relation(
    membership_id: UUID,
    body: RelationRequest,
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
) -> None:
    """[Migration 040] The candidate, or the member themselves, states the exact
    relation (mother, maternal_uncle, …); the role follows from it."""
    if body.relation not in RELATION_ROLE:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="unknown relation")
    changed = await home_circle.set_relation(
        session, membership_id=membership_id, caller_account_id=account_id, relation=body.relation
    )
    if not changed:
        raise _not_found(lang)


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
    # So each reader gets their own wording: "You suggested this" for the
    # member who made it, "Suggested by your mother" for the candidate.
    suggested_by_is_you: bool = False
    suggested_by_relation: str | None = None


@router.get("/suggestions", response_model=list[SuggestionResponse])
async def list_suggestions(
    session: DbSession,
    account_id: AuthenticatedAccount,
    candidate_account_id: UUID | None = None,
    for_candidate: UUID | None = None,
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
        candidate_account_id=candidate_account_id or for_candidate or account_id,
    )
    return [
        SuggestionResponse(
            id=str(s.id),
            suggested_profile_id=str(s.suggested_profile_id),
            suggested_by_relationship_type=s.suggested_by_relationship_type.value,
            note=s.note,
            created_at=s.created_at.isoformat(),
            suggested_by_is_you=s.suggested_by_account_id == account_id,
            suggested_by_relation=s.suggested_by_relation,
        )
        for s in rows
    ]


NoteText = Annotated[str, Field(min_length=1, max_length=home_circle.NOTE_MAX_LENGTH)]


class NoteCreateRequest(BaseModel):
    membership_id: UUID
    subject_account_id: UUID
    content: NoteText


class NoteEditRequest(BaseModel):
    content: NoteText


class FamilyNoteResponse(BaseModel):
    id: str
    subject_account_id: str
    content: str
    status: Literal["private", "requested", "shared", "declined"]
    created_at: str
    updated_at: str


def _note_response(note: home_circle.FamilyNote) -> FamilyNoteResponse:
    return FamilyNoteResponse(
        id=str(note.id),
        subject_account_id=str(note.subject_account_id),
        content=note.content,
        status=note.status,  # type: ignore[arg-type]
        created_at=note.created_at.isoformat(),
        updated_at=note.updated_at.isoformat(),
    )


def _note_text(content: str, lang: str) -> str:
    cleaned = content.strip()
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("home_circle.error.noteEmpty", lang),
        )
    return cleaned


@router.post("/notes", response_model=FamilyNoteResponse, status_code=status.HTTP_201_CREATED)
async def add_note(
    body: NoteCreateRequest, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> FamilyNoteResponse:
    """[FR016/TR016] A Home Circle member's private note about one match —
    readable only by its author."""
    try:
        note = await home_circle.add_note(
            session,
            member_account_id=account_id,
            membership_id=body.membership_id,
            subject_account_id=body.subject_account_id,
            content=_note_text(body.content, lang),
        )
    except home_circle.NotFound as exc:
        raise _not_found(lang) from exc
    except home_circle.InvalidNoteSubject as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("home_circle.error.noteSubject", lang),
        ) from exc
    return _note_response(note)


@router.get("/notes", response_model=list[FamilyNoteResponse])
async def list_my_notes(
    membership_id: UUID,
    subject_account_id: UUID,
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
) -> list[FamilyNoteResponse]:
    """[FR016] The caller's own notes about one match."""
    try:
        notes = await home_circle.list_my_notes(
            session,
            member_account_id=account_id,
            membership_id=membership_id,
            subject_account_id=subject_account_id,
        )
    except home_circle.NotFound as exc:
        raise _not_found(lang) from exc
    return [_note_response(n) for n in notes]


class NoteForwardRequestResponse(BaseModel):
    id: str
    author_name: str | None
    relationship_type: str
    subject_account_id: str
    requested_at: str


@router.get("/notes/requests", response_model=list[NoteForwardRequestResponse])
async def list_note_requests(
    session: DbSession, account_id: AuthenticatedAccount
) -> list[NoteForwardRequestResponse]:
    """[FR016] Notes family members have asked the candidate to read: who asks
    and which match, never the words until the candidate chooses to read."""
    rows = await home_circle.list_note_requests(session, account_id=account_id)
    return [
        NoteForwardRequestResponse(
            id=str(r.note_id),
            author_name=r.author_name,
            relationship_type=r.relationship_type,
            subject_account_id=str(r.subject_account_id),
            requested_at=r.requested_at.isoformat(),
        )
        for r in rows
    ]


class SharedNoteResponse(BaseModel):
    id: str
    content: str
    author_name: str | None
    relationship_type: str
    subject_account_id: str
    forwarded_at: str


@router.get("/notes/shared", response_model=list[SharedNoteResponse])
async def list_shared_notes(
    session: DbSession, account_id: AuthenticatedAccount
) -> list[SharedNoteResponse]:
    """[FR016] Notes the candidate chose to read."""
    rows = await home_circle.list_shared_notes(session, account_id=account_id)
    return [
        SharedNoteResponse(
            id=str(r.note_id),
            content=r.content,
            author_name=r.author_name,
            relationship_type=r.relationship_type,
            subject_account_id=str(r.subject_account_id),
            forwarded_at=r.forwarded_at.isoformat(),
        )
        for r in rows
    ]


@router.patch("/notes/{note_id}", response_model=FamilyNoteResponse)
async def edit_note(
    note_id: UUID,
    body: NoteEditRequest,
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
) -> FamilyNoteResponse:
    """[FR016] The author rewrites a note that has not been shared."""
    try:
        note = await home_circle.edit_note(
            session, note_id=note_id, content=_note_text(body.content, lang)
        )
    except home_circle.NotFound as exc:
        raise _not_found(lang) from exc
    return _note_response(note)


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: UUID, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> None:
    """[FR016] The author deletes one of their notes."""
    try:
        await home_circle.delete_note(session, note_id=note_id)
    except home_circle.NotFound as exc:
        raise _not_found(lang) from exc


@router.post("/notes/{note_id}/request", response_model=FamilyNoteResponse)
async def request_note_forward(
    note_id: UUID, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> FamilyNoteResponse:
    """[FR016/UX13] The author asks the candidate to read this one note."""
    try:
        note = await home_circle.request_note_forward(session, note_id=note_id)
    except home_circle.NotFound as exc:
        raise _not_found(lang) from exc
    return _note_response(note)


class NoteReadResponse(BaseModel):
    content: str


@router.post("/notes/{note_id}/read", response_model=NoteReadResponse)
async def read_note(
    note_id: UUID, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> NoteReadResponse:
    """[FR016/TS036] The candidate chooses to read one note; only that note is shared."""
    try:
        content = await home_circle.decide_note_request(
            session, account_id=account_id, note_id=note_id, approve=True
        )
    except home_circle.NotFound as exc:
        raise _not_found(lang) from exc
    return NoteReadResponse(content=content or "")


@router.post("/notes/{note_id}/decline", status_code=status.HTTP_204_NO_CONTENT)
async def decline_note(
    note_id: UUID, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> None:
    """[FR016] The candidate says not now; the author learns only that."""
    try:
        await home_circle.decide_note_request(
            session, account_id=account_id, note_id=note_id, approve=False
        )
    except home_circle.NotFound as exc:
        raise _not_found(lang) from exc


class ContactRequestResponse(BaseModel):
    id: str
    candidate_account_id: str
    candidate_name: str | None
    relationship_type: str | None
    requested_at: str


@router.get("/contact-requests", response_model=list[ContactRequestResponse])
async def list_contact_requests(
    session: DbSession, account_id: AuthenticatedAccount
) -> list[ContactRequestResponse]:
    """[FR048] Requests to share the caller's own phone with someone a
    candidate in their Home Circle is connected to."""
    rows = await connection.list_family_contact_requests(session, account_id=account_id)
    return [
        ContactRequestResponse(
            id=str(r.share_id),
            candidate_account_id=str(r.candidate_account_id),
            candidate_name=r.candidate_name,
            relationship_type=r.relationship_type,
            requested_at=r.requested_at.isoformat(),
        )
        for r in rows
    ]


async def _decide_contact_request(
    share_id: UUID, session: DbSession, account_id: UUID, lang: str, approve: bool
) -> None:
    try:
        await connection.decide_family_contact_request(
            session, share_id=share_id, account_id=account_id, approve=approve
        )
    except connection.FamilyContactRequestNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=translate("home_circle.error.contactRequestNotFound", lang),
        ) from exc


@router.post("/contact-requests/{share_id}/approve", status_code=status.HTTP_204_NO_CONTENT)
async def approve_contact_request(
    share_id: UUID, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> None:
    """[FR048/TR048] The family member approves sharing their own phone."""
    await _decide_contact_request(share_id, session, account_id, lang, approve=True)


@router.post("/contact-requests/{share_id}/decline", status_code=status.HTTP_204_NO_CONTENT)
async def decline_contact_request(
    share_id: UUID, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> None:
    """[FR048] The family member declines; nothing is shared."""
    await _decide_contact_request(share_id, session, account_id, lang, approve=False)


class OwnProfileContext(BaseModel):
    account_id: str
    name: str
    looking_for: str | None = None


class CircleContextResponse(BaseModel):
    membership_id: str
    candidate_account_id: str
    candidate_name: str
    relationship_type: str
    relation: str | None = None
    joined_at: str
    # [2026-09-17] Whose side of the match this context searches on. The owner
    # asked for the "looking for" answer to be present always, so every screen
    # that can act in a context can show which one is in force — and a family
    # member acting for a candidate sees the CANDIDATE's answer, never their own,
    # because that is the answer the server ranks and routes requests by.
    looking_for: str | None = None


class ContextsResponse(BaseModel):
    own_profile: OwnProfileContext | None
    circles: list[CircleContextResponse]


@router.get("/contexts", response_model=ContextsResponse)
async def list_contexts(session: DbSession, account_id: AuthenticatedAccount) -> ContextsResponse:
    """[FR097] Every search the caller can act in: their own (if they have a
    candidate profile) and each candidate whose Home Circle they belong to."""
    # [Owner walkthrough, 2026-09-29] This route never called authz.resolve(),
    # so `mangaly.authz_context` was unset for the whole request. That is
    # fine for the caller's own row (`is_self()` also falls back to the
    # always-set `mangaly.account_id`), but `discovery_profile_index`'s
    # family-member policy checks `has_scope()`, which has no such fallback —
    # so a circle member's read of a candidate's `looking_for` silently
    # returned nothing, correct grant and all. TR017's "one request, one
    # authz context" rule means the fix is to bind it explicitly here, the
    # same way `deps.py`'s manage-header path and the other components that
    # read across a grant already do.
    from app.db.session import set_authz_context

    await set_authz_context(session, account_id)
    own = await profile.get_own_profile(session, account_id=account_id)
    circles = await home_circle.list_member_contexts(session, account_id=account_id)

    async def looking_for(of_account_id: UUID) -> str | None:
        """Read it from the very snapshot `discovery.search()` ranks by, rather
        than from the profile row, so what a screen shows and what the engine
        actually applies cannot drift apart. `None` when the candidate has not
        answered yet or has paused their profile — the screens already have a
        "who are you looking for?" state for that (`lookingForMissing`)."""
        snapshot = await discovery.get_snapshot(session, account_id=of_account_id)
        value = (snapshot or {}).get("looking_for")
        return str(value) if value else None

    return ContextsResponse(
        own_profile=(
            OwnProfileContext(
                account_id=str(account_id),
                name=own.name,
                looking_for=await looking_for(account_id),
            )
            if own
            else None
        ),
        circles=[
            CircleContextResponse(
                membership_id=str(c.membership_id),
                candidate_account_id=str(c.candidate_account_id),
                candidate_name=c.candidate_name,
                relationship_type=c.relationship_type.value,
                relation=c.relation,
                joined_at=c.joined_at.isoformat(),
                looking_for=await looking_for(c.candidate_account_id),
            )
            for c in circles
        ],
    )
