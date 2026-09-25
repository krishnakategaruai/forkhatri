"""Discovery endpoints — FR021/FR026/FR027, FR030's compatibility panel, and
the rework's filters, browse mode and `total` (contract §3/§6).

Thin HTTP layer over `components/discovery/interface.py` and
`components/compatibility/interface.py`.
"""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import AuthenticatedAccount, DbSession, Locale
from app.components.authorization import interface as authz
from app.components.authorization.context import AuthorizationDenied
from app.components.compatibility import interface as compatibility
from app.components.discovery import interface as discovery
from app.components.trust import interface as trust
from app.components.shortlist import interface as shortlist
from app.i18n import translate

router = APIRouter(prefix="/discovery", tags=["discovery"])


class VerifiedLayerResponse(BaseModel):
    """One verified fact. `layer` is a key the client translates; `verified_on`
    and `method` are the provenance §13.4 requires so the reader can weigh how
    fresh the check is and how it was made."""

    layer: str
    verified_on: str | None = None
    method: str | None = None


class SearchResultResponse(BaseModel):
    candidate_account_id: str
    score: float
    locality: str | None
    education_level: str | None
    profession: str | None
    photo_url: str | None = None
    age: int | None = None
    height_cm: int | None = None
    marital_status: str | None = None
    mother_tongue: str | None = None
    gotra: str | None = None
    income_band: str | None = None
    shortlisted: bool = False
    # [§13] Verified facts with their date and method. A list, never a score:
    # the reader judges the evidence, the product does not judge the person.
    verification: list[VerifiedLayerResponse] = []
    # [Migration 043] Only what this person chose to show openly.
    open_name: str | None = None
    open_prompt: dict[str, str] | None = None
    open_photo_urls: list[str] = []


class SearchPageResponse(BaseModel):
    """[Contract §3] The page plus `total`, so a list can say "of 128"."""

    results: list[SearchResultResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
    # Which side is being searched for, so browse mode can show what it applied.
    looking_for: str | None = None


@router.get("/search", response_model=SearchPageResponse)
async def search(
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
    for_candidate: UUID | None = None,
    looking_for: Literal["bride", "groom"] | None = None,
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
) -> SearchPageResponse:
    """[FR021/FR026] Ranked by DEC-V1-002's fixed weights, never popularity.
    `for_candidate` (a profile id or account id) searches for a candidate the
    caller's circle helps; with no own profile and no context the caller must
    pass `looking_for` (browse mode, contract §6). Results carry demographic
    snippet fields only — never a name."""
    try:
        context_account_id = await authz.resolve_context_account(
            session, acting_account_id=account_id, for_candidate=for_candidate
        )
        page_result = await discovery.search(
            session,
            viewer_account_id=account_id,
            for_candidate_account_id=(
                context_account_id if context_account_id != account_id else None
            ),
            filters=discovery.DiscoverFilters(
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
            ),
            page=page,
            page_size=page_size,
            looking_for=looking_for,
            sort=sort,
        )
    except AuthorizationDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from exc
    except discovery.LookingForMissing as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "looking_for_missing",
                "message": translate("discovery.error.lookingForMissing", lang),
            },
        ) from exc
    results = page_result.results
    cards = await discovery.cards_for(session, account_ids=[r.candidate_account_id for r in results])
    opened = await discovery.open_cards_for(
        session, account_ids=[r.candidate_account_id for r in results]
    )
    saved = await shortlist.saved_ids(session, candidate_account_id=context_account_id)
    seeker = await discovery.get_snapshot(session, account_id=context_account_id) or {}
    return SearchPageResponse(
        results=[
            SearchResultResponse(
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
                gotra=r.gotra,
                income_band=r.income_band,
                shortlisted=r.candidate_account_id in saved,
                verification=[VerifiedLayerResponse(**v) for v in r.verification],
                open_name=(o := opened.get(r.candidate_account_id)) and o.first_name,
                open_prompt=r.open_prompt,
                open_photo_urls=o.photo_urls if o else [],
            )
            for r in results
        ],
        total=page_result.total,
        page=page_result.page,
        page_size=page_result.page_size,
        has_more=page_result.has_more,
        looking_for=str(seeker.get("looking_for") or looking_for or "") or None,
    )


class SnippetResponse(BaseModel):
    locality: str | None
    education_level: str | None
    profession: str | None
    photo_url: str | None = None
    age: int | None = None
    # Their first name, only when they chose to show it openly (migration 043).
    name: str | None = None
    # [§13] Evidence follows the person, not the surface. It was only on the
    # Discover card, so a reader who opened the profile — the point at which
    # they are actually deciding — lost sight of it.
    verification: list[VerifiedLayerResponse] = []


@router.get("/snippet/{candidate_account_id}", response_model=SnippetResponse | None)
async def get_snippet(
    candidate_account_id: UUID, session: DbSession, account_id: AuthenticatedAccount
) -> SnippetResponse | None:
    """[FR021] One candidate's demographic snippet — used to identify a
    not-yet-connected candidate somewhere more meaningful than a raw id."""
    snippet = await discovery.get_snippet(session, account_id=candidate_account_id)
    if snippet is None:
        return None
    card = (await discovery.cards_for(session, account_ids=[candidate_account_id])).get(
        candidate_account_id
    )
    layers = (
        await trust.verified_layers_for(session, account_ids=[candidate_account_id])
    ).get(candidate_account_id, [])
    opened = (await discovery.open_cards_for(session, account_ids=[candidate_account_id])).get(
        candidate_account_id
    )
    return SnippetResponse(
        locality=snippet.locality,
        education_level=snippet.education_level,
        profession=snippet.profession,
        photo_url=card.photo_url if card else None,
        age=card.age if card else None,
        name=(opened.first_name or None) if opened else None,
        verification=[VerifiedLayerResponse(**v) for v in trust.snapshot_form(layers)],
    )


class CompatibilityReasonResponse(BaseModel):
    text: str
    source: str


@router.get(
    "/compatibility/{candidate_account_id}", response_model=list[CompatibilityReasonResponse]
)
async def why_this_match(
    candidate_account_id: UUID,
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
    for_candidate: UUID | None = None,
) -> list[CompatibilityReasonResponse]:
    """[FR030/FR031] 2-4 templated reasons, or an empty list — never a
    numeric score."""
    try:
        context_account_id = await authz.resolve_context_account(
            session, acting_account_id=account_id, for_candidate=for_candidate
        )
        reasons = await compatibility.explain(
            session,
            viewer_account_id=account_id,
            candidate_account_id=candidate_account_id,
            for_candidate_account_id=(
                context_account_id if context_account_id != account_id else None
            ),
            lang=lang,
        )
    except AuthorizationDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from exc
    return [CompatibilityReasonResponse(text=r.text, source=r.source) for r in reasons]



class ShelfItemResponse(SearchResultResponse):
    reason: str | None = None


class ShelfResponse(BaseModel):
    key: str
    see_all: dict
    results: list[ShelfItemResponse]


@router.get("/shelves", response_model=list[ShelfResponse])
async def list_shelves(
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
    for_candidate: UUID | None = None,
    looking_for: str | None = None,
) -> list[ShelfResponse]:
    """[DEC-V1-022] The "For you" rows: each a fact both people can check, each
    face with its one reason. Same matching rules as search — this only groups
    the ranked results; it never adds anyone search would not show."""
    try:
        context_account_id = await authz.resolve_context_account(
            session, acting_account_id=account_id, for_candidate=for_candidate
        )
    except AuthorizationDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from exc
    try:
        found = await discovery.shelves(
            session,
            viewer_account_id=account_id,
            for_candidate_account_id=context_account_id if context_account_id != account_id else None,
            looking_for=looking_for,
            lang=lang,
        )
    except discovery.LookingForMissing as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "looking_for_missing", "message": translate("discovery.error.lookingForMissing", lang)},
        ) from exc
    ids = list({i.result.candidate_account_id for sh in found for i in sh.items})
    cards = await discovery.cards_for(session, account_ids=ids)
    opened = await discovery.open_cards_for(session, account_ids=ids)
    saved = await shortlist.saved_ids(session, candidate_account_id=context_account_id)
    out = []
    for sh in found:
        items = []
        for i in sh.items:
            r = i.result
            card = cards.get(r.candidate_account_id)
            o = opened.get(r.candidate_account_id)
            items.append(
                ShelfItemResponse(
                    candidate_account_id=str(r.candidate_account_id),
                    score=r.score,
                    locality=r.locality,
                    education_level=r.education_level,
                    profession=r.profession,
                    photo_url=card.photo_url if card else None,
                    age=card.age if card else None,
                    height_cm=r.height_cm,
                    marital_status=r.marital_status,
                    mother_tongue=r.mother_tongue,
                    gotra=r.gotra,
                    income_band=r.income_band,
                    shortlisted=r.candidate_account_id in saved,
                    verification=[VerifiedLayerResponse(**v) for v in r.verification],
                    open_name=o.first_name if o else None,
                    open_prompt=r.open_prompt,
                    open_photo_urls=o.photo_urls if o else [],
                    reason=i.reason,
                )
            )
        out.append(ShelfResponse(key=sh.key, see_all=sh.see_all, results=items))
    return out
