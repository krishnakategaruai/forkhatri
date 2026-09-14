"""Discovery endpoints — FR021/FR026/FR027, and FR030's compatibility panel.

Thin HTTP layer over `components/discovery/interface.py` and
`components/compatibility/interface.py`.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import AuthenticatedAccount, DbSession
from app.components.compatibility import interface as compatibility
from app.components.discovery import interface as discovery

router = APIRouter(prefix="/discovery", tags=["discovery"])


class SearchResultResponse(BaseModel):
    candidate_account_id: str
    score: float
    locality: str | None
    education_level: str | None
    profession: str | None


@router.get("/search", response_model=list[SearchResultResponse])
async def search(
    session: DbSession,
    account_id: AuthenticatedAccount,
    locality: str | None = None,
    page: int = 1,
) -> list[SearchResultResponse]:
    """[FR021/FR026] Ranked by DEC-V1-002's fixed weights, never popularity.
    Results carry demographic snippet fields only — see `SearchResult`'s own
    docstring for why name/photo are deliberately absent here."""
    results = await discovery.search(
        session, viewer_account_id=account_id, locality=locality, page=page
    )
    return [
        SearchResultResponse(
            candidate_account_id=str(r.candidate_account_id),
            score=r.score,
            locality=r.locality,
            education_level=r.education_level,
            profession=r.profession,
        )
        for r in results
    ]


class SnippetResponse(BaseModel):
    locality: str | None
    education_level: str | None
    profession: str | None


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
    return SnippetResponse(
        locality=snippet.locality,
        education_level=snippet.education_level,
        profession=snippet.profession,
    )


class CompatibilityReasonResponse(BaseModel):
    text: str
    source: str


@router.get(
    "/compatibility/{candidate_account_id}", response_model=list[CompatibilityReasonResponse]
)
async def why_this_match(
    candidate_account_id: UUID, session: DbSession, account_id: AuthenticatedAccount
) -> list[CompatibilityReasonResponse]:
    """[FR030/FR031] 2-4 templated reasons, or an empty list — never a
    numeric score."""
    reasons = await compatibility.explain(
        session, viewer_account_id=account_id, candidate_account_id=candidate_account_id
    )
    return [CompatibilityReasonResponse(text=r.text, source=r.source) for r in reasons]
