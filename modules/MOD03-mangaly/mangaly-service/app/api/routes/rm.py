"""Assisted matching endpoints (DEC-V1-032) — thin HTTP layer over
`components/assisted_matching/interface.py`.

Member seat (ordinary account, or a circle member with `?for_candidate=`):
    GET  /rm/me                        my relationship manager, suggestions, calls
    GET  /rm/me/role                   is this account an RM (for the console link)
    POST /rm/suggestions/{id}/decision liked | passed

RM seat (`RmAccount`: an active RM, bound as one for this request):
    GET  /rm/assignments
    GET  /rm/assignments/{id}          member summary (never contact details)
    GET  /rm/assignments/{id}/search   Discover, run AS the member
    POST /rm/assignments/{id}/suggestions
    POST /rm/assignments/{id}/interactions
    POST /rm/assignments/{id}/end
    POST /rm/assign                    v1: self-assign a member
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import AuthenticatedAccount, DbSession, Locale
from app.api.rm_deps import RmAccount
from app.components.assisted_matching import interface as assisted
from app.components.authorization import interface as authz
from app.components.authorization.context import AuthorizationDenied
from app.components.discovery import interface as discovery
from app.i18n import translate

router = APIRouter(prefix="/rm", tags=["assisted-matching"])


# ---------------------------------------------------------------------------
# Shapes
# ---------------------------------------------------------------------------


class RmResponse(BaseModel):
    account_id: str
    display_name: str
    languages: list[str]
    region: str | None
    photo_url: str | None


class SuggestedPersonResponse(BaseModel):
    """The same pre-connection card Discover shows: photo, age, city,
    education, work, and only what the person chose to show openly."""

    candidate_account_id: str
    photo_url: str | None = None
    age: int | None = None
    locality: str | None = None
    education_level: str | None = None
    profession: str | None = None
    open_name: str | None = None
    open_photo_urls: list[str] = []


class SuggestionResponse(BaseModel):
    id: str
    assignment_id: str
    suggested_account_id: str
    note: str | None
    created_at: str
    member_decision: str | None
    decided_at: str | None
    person: SuggestedPersonResponse | None = None


class InteractionResponse(BaseModel):
    id: str
    kind: str
    scheduled_at: str | None
    summary: str | None
    created_at: str


class AssignmentResponse(BaseModel):
    id: str
    rm_account_id: str
    member_account_id: str
    member_name: str | None
    member_photo_url: str | None
    status: str
    assigned_at: str
    ended_at: str | None
    note: str | None


class MyRmResponse(BaseModel):
    assignment: AssignmentResponse
    rm: RmResponse
    suggestions: list[SuggestionResponse]
    interactions: list[InteractionResponse]


class RoleResponse(BaseModel):
    is_rm: bool


class DecisionRequest(BaseModel):
    decision: Literal["liked", "passed"]
    for_candidate: str | None = None


class FamilyMemberResponse(BaseModel):
    account_id: str
    display_name: str | None
    relationship_type: str
    relation: str | None


class MemberSummaryResponse(BaseModel):
    name: str
    age: int | None
    city: str | None
    gender: str | None
    looking_for: str | None
    mother_tongue: str | None
    education_level: str | None
    profession: str | None
    partner_preference: dict
    family_involvement: dict
    language_preference: str
    family: list[FamilyMemberResponse]


class AssignmentDetailResponse(BaseModel):
    assignment: AssignmentResponse
    member: MemberSummaryResponse | None
    suggestions: list[SuggestionResponse]
    interactions: list[InteractionResponse]


class RmSearchResultResponse(SuggestedPersonResponse):
    score: float
    height_cm: int | None = None
    marital_status: str | None = None
    mother_tongue: str | None = None
    already_suggested: bool = False


class RmSearchPageResponse(BaseModel):
    results: list[RmSearchResultResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class SuggestRequest(BaseModel):
    suggested_account_id: str
    note: str | None = Field(default=None, max_length=assisted.NOTE_MAX_LENGTH)


class InteractionRequest(BaseModel):
    kind: Literal["call", "meeting", "note"]
    scheduled_at: datetime | None = None
    summary: str | None = Field(default=None, max_length=assisted.NOTE_MAX_LENGTH)


class AssignRequest(BaseModel):
    member_account_id: str
    note: str | None = Field(default=None, max_length=assisted.NOTE_MAX_LENGTH)


# ---------------------------------------------------------------------------
# Mapping
# ---------------------------------------------------------------------------


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _rm(r: assisted.RmSummary) -> RmResponse:
    return RmResponse(
        account_id=str(r.account_id),
        display_name=r.display_name,
        languages=r.languages,
        region=r.region,
        photo_url=r.photo_url,
    )


def _assignment(a: assisted.Assignment) -> AssignmentResponse:
    return AssignmentResponse(
        id=str(a.id),
        rm_account_id=str(a.rm_account_id),
        member_account_id=str(a.member_account_id),
        member_name=a.member_name,
        member_photo_url=a.member_photo_url,
        status=a.status,
        assigned_at=a.assigned_at.isoformat(),
        ended_at=_iso(a.ended_at),
        note=a.note,
    )


def _interaction(i: assisted.Interaction) -> InteractionResponse:
    return InteractionResponse(
        id=str(i.id),
        kind=i.kind,
        scheduled_at=_iso(i.scheduled_at),
        summary=i.summary,
        created_at=i.created_at.isoformat(),
    )


async def _people(session: DbSession, ids: list[UUID]) -> dict[UUID, SuggestedPersonResponse]:
    """The Discover card for each suggested person, from the caller's seat."""
    if not ids:
        return {}
    cards = await discovery.cards_for(session, account_ids=ids)
    opened = await discovery.open_cards_for(session, account_ids=ids)
    out: dict[UUID, SuggestedPersonResponse] = {}
    for account_id in ids:
        snippet = await discovery.get_snippet(session, account_id=account_id)
        card = cards.get(account_id)
        o = opened.get(account_id)
        out[account_id] = SuggestedPersonResponse(
            candidate_account_id=str(account_id),
            photo_url=card.photo_url if card else None,
            age=card.age if card else None,
            locality=snippet.locality if snippet else None,
            education_level=snippet.education_level if snippet else None,
            profession=snippet.profession if snippet else None,
            open_name=o.first_name if o else None,
            open_photo_urls=o.photo_urls if o else [],
        )
    return out


async def _suggestions(session: DbSession, assignment_id: UUID) -> list[SuggestionResponse]:
    rows = await assisted.list_suggestions(session, assignment_id=assignment_id)
    people = await _people(session, [s.suggested_account_id for s in rows])
    return [
        SuggestionResponse(
            id=str(s.id),
            assignment_id=str(s.assignment_id),
            suggested_account_id=str(s.suggested_account_id),
            note=s.note,
            created_at=s.created_at.isoformat(),
            member_decision=s.member_decision,
            decided_at=_iso(s.decided_at),
            person=people.get(s.suggested_account_id),
        )
        for s in rows
    ]


def _not_found(lang: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "not_found", "message": translate("rm.error.notFound", lang)},
    )


# ---------------------------------------------------------------------------
# Member seat
# ---------------------------------------------------------------------------


@router.get("/me", response_model=MyRmResponse | None)
async def my_rm(
    session: DbSession,
    account_id: AuthenticatedAccount,
    for_candidate: UUID | None = None,
) -> MyRmResponse | None:
    """My relationship manager (or the RM of the candidate my circle helps),
    with every suggestion and every logged call — the family's own copy of
    what the RM is doing. `null` when nobody is assigned."""
    try:
        member = await authz.resolve_context_account(
            session, acting_account_id=account_id, for_candidate=for_candidate
        )
    except AuthorizationDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from exc
    assignment = await assisted.active_assignment_for_member(session, member_account_id=member)
    if assignment is None:
        return None
    rm = await assisted.rm_summary(session, rm_account_id=assignment.rm_account_id)
    if rm is None:
        return None
    return MyRmResponse(
        assignment=_assignment(assignment),
        rm=_rm(rm),
        suggestions=await _suggestions(session, assignment.id),
        interactions=[
            _interaction(i)
            for i in await assisted.list_interactions(session, assignment_id=assignment.id)
        ],
    )


@router.get("/me/role", response_model=RoleResponse)
async def my_role(session: DbSession, account_id: AuthenticatedAccount) -> RoleResponse:
    """Whether this account is a relationship manager (shows the console link)."""
    return RoleResponse(is_rm=await assisted.is_rm(session, account_id=account_id))


@router.post("/suggestions/{suggestion_id}/decision", response_model=SuggestionResponse)
async def decide(
    suggestion_id: UUID,
    body: DecisionRequest,
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
) -> SuggestionResponse:
    """Liked or passed. Nothing is sent to the suggested person; the RM is told."""
    member = account_id
    if body.for_candidate:
        try:
            member = await authz.resolve_context_account(
                session, acting_account_id=account_id, for_candidate=UUID(body.for_candidate)
            )
        except AuthorizationDenied as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from exc
    try:
        s = await assisted.decide_suggestion(
            session, suggestion_id=suggestion_id, decision=body.decision, member_account_id=member
        )
    except assisted.NotFound:
        raise _not_found(lang) from None
    people = await _people(session, [s.suggested_account_id])
    return SuggestionResponse(
        id=str(s.id),
        assignment_id=str(s.assignment_id),
        suggested_account_id=str(s.suggested_account_id),
        note=s.note,
        created_at=s.created_at.isoformat(),
        member_decision=s.member_decision,
        decided_at=_iso(s.decided_at),
        person=people.get(s.suggested_account_id),
    )


# ---------------------------------------------------------------------------
# RM seat
# ---------------------------------------------------------------------------


@router.get("/assignments", response_model=list[AssignmentResponse])
async def assignments(session: DbSession, rm_account_id: RmAccount) -> list[AssignmentResponse]:
    return [_assignment(a) for a in await assisted.list_assignments(session, rm_account_id=rm_account_id)]


async def _own_assignment(
    session: DbSession, rm_account_id: UUID, assignment_id: UUID, lang: str
) -> assisted.Assignment:
    a = await assisted.get_assignment(session, rm_account_id=rm_account_id, assignment_id=assignment_id)
    if a is None:
        raise _not_found(lang)
    return a


@router.get("/assignments/{assignment_id}", response_model=AssignmentDetailResponse)
async def assignment_detail(
    assignment_id: UUID, session: DbSession, rm_account_id: RmAccount, lang: Locale
) -> AssignmentDetailResponse:
    a = await _own_assignment(session, rm_account_id, assignment_id, lang)
    summary = (
        await assisted.member_summary(session, member_account_id=a.member_account_id)
        if a.status == "active"
        else None
    )
    return AssignmentDetailResponse(
        assignment=_assignment(a),
        member=(
            MemberSummaryResponse(
                name=summary.name,
                age=summary.age,
                city=summary.city,
                gender=summary.gender,
                looking_for=summary.looking_for,
                mother_tongue=summary.mother_tongue,
                education_level=summary.education_level,
                profession=summary.profession,
                partner_preference=summary.partner_preference,
                family_involvement=summary.family_involvement,
                language_preference=summary.language_preference,
                family=[
                    FamilyMemberResponse(
                        account_id=str(f.account_id),
                        display_name=f.display_name,
                        relationship_type=f.relationship_type,
                        relation=f.relation,
                    )
                    for f in summary.family
                ],
            )
            if summary
            else None
        ),
        suggestions=await _suggestions(session, a.id),
        interactions=[_interaction(i) for i in await assisted.list_interactions(session, assignment_id=a.id)],
    )


@router.get("/assignments/{assignment_id}/search", response_model=RmSearchPageResponse)
async def search_for_member(
    assignment_id: UUID,
    session: DbSession,
    rm_account_id: RmAccount,
    lang: Locale,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
    sort: Literal["relevance", "newest", "recently_active"] = "relevance",
    q: str | None = None,
    nearby: Literal["city", "state"] | None = None,
    city: Annotated[list[str] | None, Query()] = None,
    age_min: Annotated[int | None, Query(ge=18, le=99)] = None,
    age_max: Annotated[int | None, Query(ge=18, le=99)] = None,
    height_min: Annotated[int | None, Query(ge=100, le=250)] = None,
    height_max: Annotated[int | None, Query(ge=100, le=250)] = None,
    marital_status: Annotated[list[str] | None, Query()] = None,
    education: Annotated[list[str] | None, Query()] = None,
    diet: Annotated[list[str] | None, Query()] = None,
    gotra: Annotated[list[str] | None, Query()] = None,
    sub_community: Annotated[list[str] | None, Query()] = None,
    profession: Annotated[list[str] | None, Query()] = None,
    income_band: Annotated[list[str] | None, Query()] = None,
    mother_tongue: Annotated[list[str] | None, Query()] = None,
    manglik: str | None = None,
    open_to_relocate: bool = False,
) -> RmSearchPageResponse:
    """Discover, run AS the member: ranked the member's own way, under the
    member's "looking for" rule and blocks. The RM changes nothing about the
    ranking — they only search with the family's wishes in mind."""
    a = await _own_assignment(session, rm_account_id, assignment_id, lang)
    if a.status != "active":
        raise _not_found(lang)
    filters = discovery.DiscoverFilters(
        nearby=nearby,
        age_min=age_min,
        age_max=age_max,
        marital_status=tuple(marital_status or ()),
        education=tuple(education or ()),
        diet=tuple(diet or ()),
        open_to_relocate=open_to_relocate,
        height_min=height_min,
        height_max=height_max,
        gotra=tuple(gotra or ()),
        sub_community=tuple(sub_community or ()),
        profession=tuple(profession or ()),
        income_band=tuple(income_band or ()),
        mother_tongue=tuple(mother_tongue or ()),
        manglik=manglik,
        q=q,
        city=tuple(city or ()),
    )
    try:
        page_result, cards, opened = await assisted.search_for_member(
            session,
            rm_account_id=rm_account_id,
            member_account_id=a.member_account_id,
            filters=filters,
            page=page,
            page_size=page_size,
            sort=sort,
        )
    except discovery.LookingForMissing as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "looking_for_missing",
                "message": translate("rm.error.memberLookingForMissing", lang),
            },
        ) from exc
    already = {s.suggested_account_id for s in await assisted.list_suggestions(session, assignment_id=a.id)}
    return RmSearchPageResponse(
        results=[
            RmSearchResultResponse(
                candidate_account_id=str(r.candidate_account_id),
                score=r.score,
                locality=r.locality,
                education_level=r.education_level,
                profession=r.profession,
                photo_url=card.photo_url if (card := cards.get(r.candidate_account_id)) else None,
                age=card.age if card else None,
                height_cm=r.height_cm,
                marital_status=r.marital_status,
                mother_tongue=r.mother_tongue,
                open_name=(o := opened.get(r.candidate_account_id)) and o.first_name,
                open_photo_urls=o.photo_urls if o else [],
                already_suggested=r.candidate_account_id in already,
            )
            for r in page_result.results
        ],
        total=page_result.total,
        page=page_result.page,
        page_size=page_result.page_size,
        has_more=page_result.has_more,
    )


@router.post(
    "/assignments/{assignment_id}/suggestions",
    response_model=SuggestionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def suggest(
    assignment_id: UUID,
    body: SuggestRequest,
    session: DbSession,
    rm_account_id: RmAccount,
    lang: Locale,
) -> SuggestionResponse:
    a = await _own_assignment(session, rm_account_id, assignment_id, lang)
    if a.status != "active":
        raise _not_found(lang)
    try:
        s = await assisted.suggest(
            session,
            rm_account_id=rm_account_id,
            assignment=a,
            suggested_account_id=UUID(body.suggested_account_id),
            note=body.note.strip() if body.note else None,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "invalid_target", "message": translate("rm.error.invalidTarget", lang)},
        ) from None
    people = await _people(session, [s.suggested_account_id])
    return SuggestionResponse(
        id=str(s.id),
        assignment_id=str(s.assignment_id),
        suggested_account_id=str(s.suggested_account_id),
        note=s.note,
        created_at=s.created_at.isoformat(),
        member_decision=s.member_decision,
        decided_at=_iso(s.decided_at),
        person=people.get(s.suggested_account_id),
    )


@router.post(
    "/assignments/{assignment_id}/interactions",
    response_model=InteractionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_interaction(
    assignment_id: UUID,
    body: InteractionRequest,
    session: DbSession,
    rm_account_id: RmAccount,
    lang: Locale,
) -> InteractionResponse:
    a = await _own_assignment(session, rm_account_id, assignment_id, lang)
    if a.status != "active":
        raise _not_found(lang)
    i = await assisted.add_interaction(
        session,
        rm_account_id=rm_account_id,
        assignment=a,
        kind=body.kind,
        scheduled_at=body.scheduled_at,
        summary=body.summary.strip() if body.summary else None,
    )
    return _interaction(i)


@router.post("/assignments/{assignment_id}/end", response_model=AssignmentResponse)
async def end_assignment(
    assignment_id: UUID, session: DbSession, rm_account_id: RmAccount, lang: Locale
) -> AssignmentResponse:
    try:
        await assisted.end_assignment(session, rm_account_id=rm_account_id, assignment_id=assignment_id)
    except assisted.NotFound:
        raise _not_found(lang) from None
    a = await _own_assignment(session, rm_account_id, assignment_id, lang)
    return _assignment(a)


@router.post("/assign", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign(
    body: AssignRequest, session: DbSession, rm_account_id: RmAccount, lang: Locale
) -> AssignmentResponse:
    """v1: the RM takes on a member themselves. Allocation is backlog."""
    try:
        a = await assisted.assign(
            session,
            rm_account_id=rm_account_id,
            member_account_id=UUID(body.member_account_id),
            note=body.note.strip() if body.note else None,
        )
    except assisted.NotEntitled:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"code": "not_entitled", "message": translate("rm.error.notEntitled", lang)},
        ) from None
    except assisted.AlreadyAssigned:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "already_assigned", "message": translate("rm.error.alreadyAssigned", lang)},
        ) from None
    return _assignment(a)
