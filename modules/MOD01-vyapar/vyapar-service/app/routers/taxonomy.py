# [Backend A, 2026-09-28] Taxonomy tree — HTTP front door only. The tree is
# built in app/services/taxonomy.py from the shared in-process cache.
# Traces to: FR01, FR04, FR44, FR48
from __future__ import annotations

from fastapi import APIRouter

from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.services import taxonomy as svc
from app.services.taxonomy import TaxonomyCategoryOut, TaxonomyTermOut, TaxonomyTreeOut  # noqa: F401  schemas re-exported

router = APIRouter(prefix="/v1/taxonomy", tags=["taxonomy"], responses=ERROR_RESPONSES)


@router.get("/tree", response_model=TaxonomyTreeOut, operation_id="getTaxonomyTree", summary="Categories with their skills and roles, localized")
async def get_taxonomy_tree(lang: Locale) -> TaxonomyTreeOut:
    return svc.get_taxonomy_tree(lang)
