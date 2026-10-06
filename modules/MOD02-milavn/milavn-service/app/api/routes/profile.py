"""Profile endpoints — FR001, FR002, FR003, FR085.

Thin HTTP layer over `components/profile/interface.py`.
"""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app import media_files
from app.api.deps import CurrentMember, DbSession, Locale
from app.components.places import interface as places
from app.components.profile import interface as profile
from app.config.interests import taxonomy_payload
from app.i18n import translate

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileResponse(BaseModel):
    member_id: str
    locality_city: str
    locality_zone: str | None
    locality_locality: str | None
    locality_state: str | None = None
    locality_lat: float | None = None
    locality_lng: float | None = None
    language_preference: str
    interests: list[str]
    interest_labels: list[str]
    bio: str | None
    photo_url: str | None


class OnboardingRequest(BaseModel):
    locality_city: str | None = None
    locality_zone: str | None = None
    locality_locality: str | None = None
    locality_state: str | None = None
    locality_lat: float | None = None
    locality_lng: float | None = None
    interests: list[str] = Field(default_factory=list)
    language_preference: str | None = None


class PlaceRequest(BaseModel):
    locality_city: str
    locality_zone: str | None = None
    locality_locality: str | None = None
    locality_state: str | None = None
    locality_lat: float | None = None
    locality_lng: float | None = None


class LanguageRequest(BaseModel):
    language_preference: str


def _to_response(p: profile.ProfileSummary) -> ProfileResponse:
    return ProfileResponse(
        member_id=str(p.member_id),
        locality_city=p.locality_city,
        locality_zone=p.locality_zone,
        locality_locality=p.locality_locality,
        locality_state=p.locality_state,
        locality_lat=p.locality_lat,
        locality_lng=p.locality_lng,
        language_preference=p.language_preference,
        interests=p.interests,
        interest_labels=p.interest_labels,
        bio=p.bio,
        photo_url=p.photo_url,
    )


@router.get("/me", response_model=ProfileResponse | None)
async def get_me(session: DbSession, member: CurrentMember) -> ProfileResponse | None:
    result = await profile.get_own_profile(session, member_id=member.member_id)
    return _to_response(result) if result else None


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def save_onboarding(body: OnboardingRequest, session: DbSession, member: CurrentMember, lang: Locale) -> ProfileResponse:
    """[FR001] Persist a usable profile once locality + >=1 interest exist; name any missing field."""
    try:
        result = await profile.save_onboarding(
            session,
            member_id=member.member_id,
            locality_city=body.locality_city,
            locality_zone=body.locality_zone,
            locality_locality=body.locality_locality,
            locality_state=body.locality_state,
            locality_lat=body.locality_lat,
            locality_lng=body.locality_lng,
            interests=body.interests,
            language_preference=body.language_preference,
        )
    except profile.MissingRequiredFields as exc:
        names = ", ".join(translate(f"profile.missing.{f}", lang) for f in exc.fields)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"fields": exc.fields, "message": translate("profile.missingFields", lang, fields=names)},
        ) from exc
    return _to_response(result)


@router.patch("/place", response_model=ProfileResponse)
async def set_place(body: PlaceRequest, session: DbSession, member: CurrentMember, lang: Locale) -> ProfileResponse:
    """[FR001/FR038] Change my approximate home place (picked from the live place search)."""
    try:
        result = await profile.save_place(session, member_id=member.member_id, **body.model_dump())
    except profile.MissingRequiredFields as exc:
        raise HTTPException(status_code=422, detail={"fields": exc.fields, "message": translate("profile.missingFields", lang, fields=", ".join(exc.fields))}) from exc
    if result is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "profile_required", "message": translate("profile.notFound", lang)})
    return _to_response(result)


@router.patch("/language", response_model=ProfileResponse)
async def set_language(body: LanguageRequest, session: DbSession, member: CurrentMember, lang: Locale) -> ProfileResponse:
    """[FR002] Person-level language preference."""
    try:
        result = await profile.set_language(session, member_id=member.member_id, language=body.language_preference)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="unsupported language") from exc
    except profile.ProfileNotFound as exc:
        raise HTTPException(status_code=404, detail=translate("profile.notFound", lang)) from exc
    return _to_response(result)


@router.patch("/enrichment", response_model=ProfileResponse)
async def update_enrichment(
    session: DbSession,
    member: CurrentMember,
    lang: Locale,
    bio: str | None = Form(default=None),  # noqa: B008
    extra_interests: str | None = Form(default=None),  # noqa: B008 — comma separated
    photo: UploadFile | None = File(default=None),  # noqa: B008
) -> ProfileResponse:
    """[FR003] Optional enrichment; never a precondition for anything."""
    try:
        result = await profile.update_enrichment(
            session,
            member_id=member.member_id,
            bio=bio,
            photo=photo,
            extra_interests=[t for t in (extra_interests or "").split(",") if t.strip()],
        )
    except profile.ProfileNotFound as exc:
        raise HTTPException(status_code=404, detail=translate("profile.notFound", lang)) from exc
    except profile.UnsupportedMedia as exc:
        raise HTTPException(status_code=415, detail=translate("moments.unsupported", lang)) from exc
    except media_files.TooLarge as exc:
        raise HTTPException(status_code=413, detail=translate("media.tooLarge", lang, mb=exc.limit_mb)) from exc
    return _to_response(result)


@router.get("/interests/taxonomy")
async def interests_taxonomy() -> list[dict]:
    return taxonomy_payload()


@router.get("/places")
async def search_places(member: CurrentMember, lang: Locale, q: str = "") -> list[dict]:
    """[FR038/TR29] Live India place search (state, district, city, area) for the place picker."""
    try:
        return await places.search(q, lang)
    except (places.PlacesNotConfigured, places.PlacesUnavailable) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"code": "places_unavailable", "message": translate("place.unavailable", lang)}) from exc


@router.get("/places/nearest")
async def nearest_place(member: CurrentMember, lang: Locale, lat: float, lng: float) -> dict:
    """[FR081] Resolve a device position to an approximate place (area centre, never the position itself)."""
    try:
        found = await places.nearest(lat, lng, lang)
    except (places.PlacesNotConfigured, places.PlacesUnavailable) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"code": "places_unavailable", "message": translate("place.unavailable", lang)}) from exc
    if found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "place_not_found", "message": translate("place.notFound", lang)})
    return found
