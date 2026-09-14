"""Profile endpoints — FR001.

Thin HTTP layer over `components/profile/interface.py`, matching this
project's standing convention (`api/routes/auth.py`'s own header comment).
"""

from __future__ import annotations

from datetime import date
from typing import Literal, cast
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.api.deps import AuthenticatedAccount, DbSession, Locale
from app.components.profile import interface as profile
from app.components.profile.models import FieldState
from app.components.profile.storage import UnsupportedMedia
from app.i18n import translate

router = APIRouter(prefix="/profile", tags=["profile"])


def _profile_not_found(lang: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=translate("profile.error.notFound", lang),
    )


class ProfileResponse(BaseModel):
    id: str
    name: str
    date_of_birth: date
    gender: str
    city_locality: str
    photo_url: str | None


def _to_response(p: profile.ProfileSummary) -> ProfileResponse:
    return ProfileResponse(
        id=str(p.id),
        name=p.name,
        date_of_birth=p.date_of_birth,
        gender=p.gender,
        city_locality=p.city_locality,
        photo_url=p.photo_url,
    )


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
    name: str = Form(..., min_length=1, max_length=200),  # noqa: B008 — FastAPI's own DI idiom
    date_of_birth: date = Form(...),  # noqa: B008
    gender: str = Form(..., min_length=1, max_length=50),  # noqa: B008
    city_locality: str = Form(..., min_length=1, max_length=200),  # noqa: B008
    photo: UploadFile = File(...),  # noqa: B008
) -> ProfileResponse:
    """[FR001/TR001] Create the existence-tier profile. `multipart/form-data`
    because a photo is required, not optional — DEC-V1-001's own existence
    tier includes "at least one photo"."""
    try:
        result = await profile.create_profile(
            session,
            account_id=account_id,
            name=name,
            date_of_birth=date_of_birth,
            gender=gender,
            city_locality=city_locality,
            photo=photo,
        )
    except profile.MissingRequiredFields as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "fields": exc.fields,
                "message": translate("profile.error.missingFields", lang),
            },
        ) from exc
    except profile.TooYoung as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("profile.error.tooYoung", lang, years=exc.required_years),
        ) from exc
    except profile.AlreadyExists as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=translate("profile.error.alreadyExists", lang),
        ) from exc
    except UnsupportedMedia as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("profile.error.unsupportedPhoto", lang),
        ) from exc

    return _to_response(result)


@router.get("/me", response_model=ProfileResponse | None)
async def get_own_profile(
    session: DbSession, account_id: AuthenticatedAccount
) -> ProfileResponse | None:
    """Whether the caller has a saved profile yet, and what it contains."""
    result = await profile.get_own_profile(session, account_id=account_id)
    return _to_response(result) if result else None


class PhotoResponse(BaseModel):
    id: str
    url: str
    is_primary: bool


def _photo_response(p: profile.PhotoSummary) -> PhotoResponse:
    return PhotoResponse(id=str(p.id), url=p.url, is_primary=p.is_primary)


# Registered ahead of `GET /{category}` below — a single-segment static GET
# declared after it would be swallowed as `category="photos"`.
@router.get("/photos", response_model=list[PhotoResponse])
async def list_photos(
    session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> list[PhotoResponse]:
    """The caller's own photos, main photo first."""
    result = await profile.list_own_photos(session, account_id=account_id)
    if result is None:
        raise _profile_not_found(lang)
    return [_photo_response(p) for p in result]


@router.post("/photos", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED)
async def add_photo(
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
    photo: UploadFile = File(...),  # noqa: B008
) -> PhotoResponse:
    """Add one photo (up to `profile.MAX_PHOTOS`)."""
    try:
        result = await profile.add_photo(session, account_id=account_id, photo=photo)
    except profile.ProfileNotFound as exc:
        raise _profile_not_found(lang) from exc
    except profile.PhotoLimitReached as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=translate("profile.error.photoLimit", lang, max=profile.MAX_PHOTOS),
        ) from exc
    except UnsupportedMedia as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("profile.error.unsupportedPhoto", lang),
        ) from exc
    return _photo_response(result)


@router.delete("/photos/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
    media_id: UUID, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> None:
    """Remove a photo. The last remaining photo cannot be removed — the
    existence tier (DEC-V1-001) requires at least one."""
    try:
        await profile.delete_photo(session, account_id=account_id, media_id=media_id)
    except (profile.ProfileNotFound, profile.PhotoNotFound) as exc:
        raise _profile_not_found(lang) from exc
    except profile.LastPhotoRequired as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=translate("profile.error.lastPhoto", lang),
        ) from exc


@router.post("/photos/{media_id}/primary", status_code=status.HTTP_204_NO_CONTENT)
async def set_primary_photo(
    media_id: UUID, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> None:
    """Make this photo the main one."""
    try:
        await profile.set_primary_photo(session, account_id=account_id, media_id=media_id)
    except (profile.ProfileNotFound, profile.PhotoNotFound) as exc:
        raise _profile_not_found(lang) from exc


class AttributeInput(BaseModel):
    """One `profile_attribute` row's desired new state. `value` is ignored
    (and stored as null) when `state` is `declined` — FieldState's tri-state
    contract holds a declined field can never carry a stale value."""

    state: Literal["value", "declined"]
    value: dict | list | str | int | float | bool | None = None


class CompletenessResponse(BaseModel):
    existence_complete: bool
    discoverability_complete: bool
    discoverability_missing: list[str]
    enhanced_filled_categories: int
    enhanced_total_categories: int


@router.get("/view/{target_account_id}", response_model=ProfileResponse | None)
async def get_profile(
    target_account_id: UUID, session: DbSession, account_id: AuthenticatedAccount
) -> ProfileResponse | None:
    """[FR021] Any account id, not just the caller's own — RLS
    (`profile_owner_or_granted`) is the only gate: self, or a candidate the
    caller holds a `candidate_info` grant for (post-accepted-connection),
    return the real row; anyone else gets `null`, indistinguishable from
    "no such profile" (the same anti-enumeration shape this app uses
    everywhere else — Discovery already told the caller this id exists and
    is searchable, so there is nothing left to protect by distinguishing
    the two here). Deliberately `/view/{id}`, not a bare `/{id}` — this
    router already has `GET /profile/{category}` for the category editor,
    and a bare `/{id}` here would collide with it (same single-segment GET
    shape, ambiguous to FastAPI's router, no way to "reorder" out of it —
    unlike the earlier static-vs-dynamic bug this module already fixed
    once, dynamic-vs-dynamic has no ordering fix, only a distinct path)."""
    result = await profile.view_profile(
        session, viewer_account_id=account_id, target_account_id=target_account_id
    )
    return _to_response(result) if result else None


@router.get("/completeness", response_model=CompletenessResponse)
async def get_completeness(
    session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> CompletenessResponse:
    """[FR005/TR005] The three-tier completeness read UX11/UI11 render as
    three physically separate bars.

    Registered ahead of the `/{category}` routes below: Starlette matches
    routes in registration order, and `"completeness"` would otherwise be
    swallowed by `/{category}` as a literal category name."""
    result = await profile.completeness(session, account_id=account_id)
    if result is None:
        raise _profile_not_found(lang)
    return CompletenessResponse(
        existence_complete=result.existence_complete,
        discoverability_complete=result.discoverability_complete,
        discoverability_missing=result.discoverability_missing,
        enhanced_filled_categories=result.enhanced_filled_categories,
        enhanced_total_categories=result.enhanced_total_categories,
    )


@router.get("/attributes", response_model=dict[str, dict[str, str]])
async def get_all_attributes(
    session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> dict[str, dict[str, str]]:
    """[FR002] Every saved attribute's state, grouped by category — the
    Profile edit hub's category cards read this once rather than issuing one
    request per category. Registered ahead of `/{category}` for the same
    static-before-dynamic reason as `/completeness` above."""
    result = await profile.get_all_attributes(session, account_id=account_id)
    if result is None:
        raise _profile_not_found(lang)
    return {
        category: {key: state.value for key, state in attrs.items()}
        for category, attrs in result.items()
    }


@router.get("/attributes/full", response_model=dict[str, dict[str, AttributeInput]])
async def get_all_attribute_values(
    session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> dict[str, dict[str, AttributeInput]]:
    """[FR002] The caller's own attributes WITH values, for the Profile hub's
    value badges and its Edit/Preview toggle. Two path segments, so it cannot
    collide with the single-segment `/{category}` route below."""
    result = await profile.get_all_attribute_values(session, account_id=account_id)
    if result is None:
        raise _profile_not_found(lang)
    return {
        category: {
            key: AttributeInput(state=cast(Literal["value", "declined"], state.value), value=value)
            for key, (state, value) in attrs.items()
        }
        for category, attrs in result.items()
    }


@router.get("/{category}", response_model=dict[str, AttributeInput])
async def get_category(
    category: str,
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
) -> dict[str, AttributeInput]:
    """[FR002] Pre-fills the category editor with whatever was already saved."""
    result = await profile.get_category(session, account_id=account_id, category=category)
    if result is None:
        raise _profile_not_found(lang)
    # `result` only ever contains rows this same route's PATCH wrote, which
    # never persists FieldState.UNSET (absence of a row IS unset) — so the
    # literal narrowing here always holds, cast makes that explicit to mypy.
    return {
        key: AttributeInput(state=cast(Literal["value", "declined"], state.value), value=value)
        for key, (state, value) in result.items()
    }


@router.patch("/{category}", status_code=status.HTTP_204_NO_CONTENT)
async def update_category(
    category: str,
    attributes: dict[str, AttributeInput],
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
) -> None:
    """[FR002/TR002] Set or decline any number of attributes within one
    category in a single request — one PATCH per category (matching UX02's
    per-category editing screens), not one PATCH per field."""
    try:
        await profile.update_category(
            session,
            account_id=account_id,
            category=category,
            attributes={
                key: (FieldState(item.state), item.value) for key, item in attributes.items()
            },
        )
    except profile.ProfileNotFound as exc:
        raise _profile_not_found(lang) from exc
