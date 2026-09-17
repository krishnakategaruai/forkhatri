"""Discovery endpoints — FR021/FR026/FR027, and FR030's compatibility panel.

Thin HTTP layer over `components/discovery/interface.py` and
`components/compatibility/interface.py`.
"""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import AuthenticatedAccount, DbSession
from app.components.authorization.context import AuthorizationDenied
from app.components.compatibility import interface as compatibility
from app.components.discovery import interface as discovery

router = APIRouter(prefix="/discovery", tags=["discovery"])


class SearchResultResponse(BaseModel):
    candidate_account_id: str
    score: float
    locality: str | None
    education_level: str | None
    profession: str | None
    photo_url: str | None = None
    age: int | None = None


@router.get("/search", response_model=list[SearchResultResponse])
async def search(
    session: DbSession,
    account_id: AuthenticatedAccount,
    page: int = 1,
    for_candidate: UUID | None = None,
    nearby: Literal["city", "state"] | None = None,
    age_min: Annotated[int | None, Query(ge=18, le=99)] = None,
    age_max: Annotated[int | None, Query(ge=18, le=99)] = None,
    marital_status: Annotated[list[str] | None, Query()] = None,
    education: Annotated[list[str] | None, Query()] = None,
    diet: Annotated[list[str] | None, Query()] = None,
    open_to_relocate: bool = False,
) -> list[SearchResultResponse]:
    """[FR021/FR026] Ranked by DEC-V1-002's fixed weights, never popularity.
    Results carry demographic snippet fields only — see `SearchResult`'s own
    docstring for why name/photo are deliberately absent here."""
    try:
        results = await discovery.search(
            session,
            viewer_account_id=account_id,
            for_candidate_account_id=for_candidate,
            filters=discovery.DiscoverFilters(
                nearby=nearby,
                age_min=age_min,
                age_max=age_max,
                marital_status=tuple(marital_status or ()),
                education=tuple(education or ()),
                diet=tuple(diet or ()),
                open_to_relocate=open_to_relocate,
            ),
            page=page,
        )
    except AuthorizationDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from exc
    except discovery.LookingForMissing as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail={"code": "looking_for_missing"}
        ) from exc
    cards = await discovery.cards_for(
        session, account_ids=[r.candidate_account_id for r in results]
    )
    return [
        SearchResultResponse(
            candidate_account_id=str(r.candidate_account_id),
            score=r.score,
            locality=r.locality,
            education_level=r.education_level,
            profession=r.profession,
            photo_url=card.photo_url if (card := cards.get(r.candidate_account_id)) else None,
            age=card.age if card else None,
        )
        for r in results
    ]


class SnippetResponse(BaseModel):
    locality: str | None
    education_level: str | None
    profession: str | None
    photo_url: str | None = None
    age: int | None = None


@router.get("/snippet/{candidate_account_id}", response_model=SnippetResponse | None)
async def get_snippet(
    candidate_account_id: UUID, session: DbSession, account_id: AuthenticatedAccount
) -> SnippetResponse | None:
    """[FR021] One candidate's demographic snippet — used to identify a
    not-yet-connected candidate (e.g. a pending connection request's
    sender) somewhere more meaningful than a raw account id, without
    unlocking anything `profile_owner_or_granted` doesn't already allow."""
    snippet = await discovery.get_snippet(session, account_id=candidate_account_id)
    if snippet is None:
        return None
    card = (await discovery.cards_for(session, account_ids=[candidate_account_id])).get(
        candidate_account_id
    )
    return SnippetResponse(
        locality=snippet.locality,
        education_level=snippet.education_level,
        profession=snippet.profession,
        photo_url=card.photo_url if card else None,
        age=card.age if card else None,
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
    for_candidate: UUID | None = None,
) -> list[CompatibilityReasonResponse]:
    """[FR030/FR031] 2-4 templated reasons, or an empty list — never a
    numeric score."""
    try:
        reasons = await compatibility.explain(
            session,
            viewer_account_id=account_id,
            candidate_account_id=candidate_account_id,
            for_candidate_account_id=for_candidate,
        )
    except AuthorizationDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from exc
    return [CompatibilityReasonResponse(text=r.text, source=r.source) for r in reasons]
