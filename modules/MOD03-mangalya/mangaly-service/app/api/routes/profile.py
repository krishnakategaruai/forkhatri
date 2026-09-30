"""Profile endpoints — FR001.

Thin HTTP layer over `components/profile/interface.py`, matching this
project's standing convention (`api/routes/auth.py`'s own header comment).
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal, cast
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel

from app.api.deps import AuthenticatedAccount, DbSession, Locale
from app.components.profile import horoscope_fields
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


def _first_details(
    education_level: str | None,
    occupation: str | None,
    marital_status: str | None,
    relocation_willingness: str | None,
) -> dict[tuple[str, str], str]:
    given = {
        ("education", "highest_education_level"): education_level,
        ("profession", "occupation"): (occupation or "").strip() or None,
        ("marital_history", "marital_status"): marital_status,
        ("relocation", "relocation_willingness"): relocation_willingness,
    }
    return {k: v for k, v in given.items() if v}


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
    name: str = Form(..., min_length=1, max_length=200),  # noqa: B008 — FastAPI's own DI idiom
    date_of_birth: date = Form(...),  # noqa: B008
    gender: str = Form(..., min_length=1, max_length=50),  # noqa: B008
    looking_for: str = Form(..., pattern="^(bride|groom)$"),  # noqa: B008
    city_locality: str = Form(..., min_length=1, max_length=200),  # noqa: B008
    photo: UploadFile = File(...),  # noqa: B008
    education_level: str | None = Form(None, pattern="^(high_school|bachelors|masters|doctorate|other)$"),  # noqa: B008
    occupation: str | None = Form(None, max_length=120),  # noqa: B008
    marital_status: str | None = Form(None, pattern="^(never_married|divorced|widowed|awaiting_divorce)$"),  # noqa: B008
    relocation_willingness: str | None = Form(None, pattern="^(yes|no|open_to_discussion|open_to_relocate)$"),  # noqa: B008
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
            looking_for=looking_for,
            first_details=_first_details(
                education_level, occupation, marital_status, relocation_willingness
            ),
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

    # [DEC-V1-028 minor safety] The wizard refused anyone under the marriage
    # age above; this is the independent under-18 flag (Tier 4) for anything
    # that ever gets past it. Reads the row just written, under this context.
    from app.components.safety import interface as safety

    await safety.check_profile_age(session, account_id=account_id)
    return _to_response(result)


@router.post("/managed", status_code=status.HTTP_201_CREATED)
async def create_profile_for_child(
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
    child_phone: str = Form(..., min_length=6, max_length=32),  # noqa: B008
    relation: str = Form(...),  # noqa: B008
    name: str = Form(..., min_length=1, max_length=200),  # noqa: B008
    date_of_birth: date = Form(...),  # noqa: B008
    gender: str = Form(..., min_length=1, max_length=50),  # noqa: B008
    looking_for: str = Form(..., pattern="^(bride|groom)$"),  # noqa: B008
    city_locality: str = Form(..., min_length=1, max_length=200),  # noqa: B008
    photo: UploadFile = File(...),  # noqa: B008
    education_level: str | None = Form(None, pattern="^(high_school|bachelors|masters|doctorate|other)$"),  # noqa: B008
    occupation: str | None = Form(None, max_length=120),  # noqa: B008
    marital_status: str | None = Form(None, pattern="^(never_married|divorced|widowed|awaiting_divorce)$"),  # noqa: B008
    relocation_willingness: str | None = Form(None, pattern="^(yes|no|open_to_discussion|open_to_relocate)$"),  # noqa: B008
) -> dict[str, str]:
    """[DEC-V1-019] A parent (or other relation) creates a candidate profile for
    their son or daughter — the Shaadi.com "profile for: son / daughter" model.

    1. ForKhatri provisions a member for the child's mobile number (refused if
       that number already belongs to someone: then the parent asks to join
       the child's circle instead — it is their account).
    2. Mangalya makes the child's account on that same id, and builds the
       profile with the child's account bound — so every write is the child's.
    3. The creator becomes the circle's first member, as their exact relation.
    When the child signs in with an OTP to that number, the profile is theirs."""
    from sqlalchemy import text

    from app.components.home_circle import interface as home_circle
    from app.components.home_circle.models import RELATION_ROLE
    from app.components.identity_bridge import platform
    from app.components.trust import interface as trust
    from app.db.session import set_account_context, set_authz_context

    if relation not in RELATION_ROLE:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="unknown relation")
    # [DEC-V1-025] The owner's rule (2026-09-21): "a person who could create an
    # account [for someone] should always be an email, phone, photo verified
    # person only." Phone is proven by the ForKhatri sign-in OTP; photo means a
    # current live face match (DEC-V1-016). Email verification does not exist
    # in the platform identity service yet — a platform blocker, not checked
    # here. Checked before anything is provisioned, so a refused maker leaves
    # no half-made member behind.
    if not await trust.is_face_verified(session, account_id=account_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "verification_required",
                "message": translate("verification.error.required", lang),
            },
        )
    try:
        child_id, digits = await platform.provision_member(
            phone=child_phone, display_name=name, preferred_language=lang
        )
    except platform.MemberExists as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=translate("profile.error.childAlreadyJoined", lang),
        ) from exc
    except platform.InvalidPhone as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("profile.error.childPhone", lang),
        ) from exc
    except platform.PlatformIdentityUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="identity unavailable") from exc

    await session.execute(
        text("SELECT mangaly_identity.create_account_for_child(:id, :phone, :name)"),
        {"id": child_id, "phone": digits, "name": name},
    )

    # Everything below is the child's: their profile, their circle.
    await set_account_context(session, child_id)
    await set_authz_context(session, child_id)
    try:
        await profile.create_profile(
            session,
            account_id=child_id,
            name=name,
            date_of_birth=date_of_birth,
            gender=gender,
            city_locality=city_locality,
            photo=photo,
            looking_for=looking_for,
            first_details=_first_details(
                education_level, occupation, marital_status, relocation_willingness
            ),
        )
    except profile.TooYoung as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("profile.error.tooYoung", lang, years=exc.required_years),
        ) from exc
    except UnsupportedMedia as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("profile.error.unsupportedPhoto", lang),
        ) from exc
    await session.execute(
        text(
            "UPDATE mangaly_profile.profile SET created_by_account_id = :creator, updated_at = now() "
            "WHERE account_id = :child"
        ),
        {"creator": account_id, "child": child_id},
    )
    await home_circle.add_founding_member(
        session, candidate_account_id=child_id, member_account_id=account_id, relation=relation
    )
    await set_account_context(session, account_id)
    await set_authz_context(session, account_id)
    return {"account_id": str(child_id)}


class ManagedProfileResponse(BaseModel):
    account_id: str
    name: str
    photo_url: str | None
    phone_masked: str | None


@router.get("/managed", response_model=list[ManagedProfileResponse])
async def list_managed(session: DbSession, account_id: AuthenticatedAccount) -> list[ManagedProfileResponse]:
    """[DEC-V1-019] Profiles the caller created that their son or daughter has
    not taken over yet — the ones the caller may still fill in."""
    from sqlalchemy import text

    rows = await session.execute(
        text("SELECT * FROM mangaly_profile.managed_profiles_of(:me)"), {"me": account_id}
    )
    return [
        ManagedProfileResponse(
            account_id=str(r["account_id"]),
            name=r["name"],
            photo_url=profile.resolve_photo_url(r["primary_photo_ref"]) if r["primary_photo_ref"] else None,
            phone_masked=r["phone_masked"],
        )
        for r in rows.mappings()
    ]


@router.post("/disown", status_code=status.HTTP_204_NO_CONTENT)
async def disown(session: DbSession, account_id: AuthenticatedAccount) -> None:
    """[DEC-V1-019] "This isn't me": the owner of a mobile number finds a
    profile someone else made with it and removes it. Only while it is still
    unclaimed; the person keeps their own ForKhatri account. The one who made
    it is told."""
    from sqlalchemy import text

    from app.components.notification_bridge import interface as notifications

    creator = (
        await session.execute(
            text(
                "SELECT created_by_account_id FROM mangaly_profile.profile "
                "WHERE account_id = :me AND claimed_at IS NULL"
            ),
            {"me": account_id},
        )
    ).scalar_one_or_none()
    if creator is None:
        return
    removed = (
        await session.execute(
            text("SELECT mangaly_profile.disown_profile_made_for_me(:me)"), {"me": account_id}
        )
    ).scalar_one()
    if removed:
        await notifications.notify(
            session,
            recipients=[creator],
            subject_account_id=None,
            kind="profile_disowned",
            payload={},
            link="/circle",
        )


@router.post("/claim", status_code=status.HTTP_204_NO_CONTENT)
async def claim(session: DbSession, account_id: AuthenticatedAccount) -> None:
    """[DEC-V1-019] The candidate takes over a profile made for them. From now
    on only they may edit it; the creator stays in the circle."""
    from sqlalchemy import text

    await session.execute(
        text(
            "UPDATE mangaly_profile.profile SET claimed_at = now(), updated_at = now() "
            "WHERE account_id = :me AND created_by_account_id IS NOT NULL AND claimed_at IS NULL"
        ),
        {"me": account_id},
    )


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


class PhotoOrderRequest(BaseModel):
    ids: list[UUID]


# PATCH, not PUT: the service's CORS policy (main.py) deliberately allows only
# GET/POST/PATCH/DELETE, and a reorder is a partial update of existing rows.
@router.patch("/photos/order", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_photos(
    body: PhotoOrderRequest, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> None:
    """Save the grid order chosen by long-press drag; the first photo is main."""
    try:
        await profile.reorder_photos(session, account_id=account_id, ordered_ids=body.ids)
    except profile.ProfileNotFound as exc:
        raise _profile_not_found(lang) from exc
    except profile.PhotoOrderMismatch as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=translate("profile.error.photoOrder", lang),
        ) from exc


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


class PublicProfileResponse(BaseModel):
    """[DEC-V1-020] A searchable candidate as anyone signed in may see them:
    the matrimonial facts and the main photo, never the name or contact."""

    account_id: str
    age: int | None
    locality: str | None
    photo_url: str | None
    education_level: str | None
    profession: str | None
    attributes: dict[str, dict[str, dict | list | str | int | float | bool | None]]
    # [Migration 043] What this person chose to show openly.
    open_name: str | None = None
    open_photo_urls: list[str] = []
    # [Owner, 2026-09-25] The full name, for a parent or guardian whose
    # candidate has an ACCEPTED connection with this person. Contact details
    # still follow the candidate's own sharing (FR046/FR048).
    name: str | None = None


async def _connected_name_for_parent(
    session: DbSession, viewer_account_id: UUID, target_account_id: UUID
) -> str | None:
    from app.components.authorization import interface as authz_engine
    from app.components.authorization.context import Action
    from app.components.connection import interface as connection
    from app.components.connection.models import ConnectionStatus
    from app.components.home_circle import interface as home_circle

    # The circle and connection reads are RLS-scoped to the viewer.
    await authz_engine.resolve_self(session, account_id=viewer_account_id, action=Action.READ)
    for ctx in await home_circle.list_member_contexts(session, account_id=viewer_account_id):
        if ctx.relationship_type.value not in ("parent", "guardian"):
            continue
        between = await connection.connection_between(
            session, account_id=ctx.candidate_account_id, other_account_id=target_account_id
        )
        if between is None or between.status is not ConnectionStatus.ACCEPTED:
            continue
        info = await connection.sender_info(session, connection_id=between.id)
        if info is None:
            continue
        return info.target_name if info.subject_account_id == ctx.candidate_account_id else info.subject_name
    return None


@router.get("/view/{target_account_id}/public", response_model=PublicProfileResponse | None)
async def get_public_profile(
    target_account_id: UUID, session: DbSession, account_id: AuthenticatedAccount
) -> PublicProfileResponse | None:
    """[FR021/DEC-V1-020] What a family member evaluating a match — or a
    candidate who has not connected yet — may read: biodata, main photo, age
    and locality. `null` when the subject is not searchable."""
    from app.components.discovery import interface as discovery

    snippet = await discovery.get_snippet(session, account_id=target_account_id)
    if snippet is None:
        return None
    cards = await discovery.cards_for(session, account_ids=[target_account_id])
    card = cards.get(target_account_id)
    biodata = await profile.public_biodata(session, account_id=target_account_id)
    opened = (await discovery.open_cards_for(session, account_ids=[target_account_id])).get(
        target_account_id
    )
    return PublicProfileResponse(
        name=await _connected_name_for_parent(session, account_id, target_account_id),
        open_name=opened.first_name if opened else None,
        open_photo_urls=opened.photo_urls if opened else [],
        account_id=str(target_account_id),
        age=card.age if card else None,
        locality=snippet.locality,
        photo_url=card.photo_url if card else None,
        education_level=snippet.education_level,
        profession=snippet.profession,
        attributes=biodata,
    )


class ProfileViewResponse(BaseModel):
    profile: ProfileResponse
    photos: list[PhotoResponse]
    attributes: dict[str, dict[str, dict | list | str | int | float | bool | None]]
    voice_intro_url: str | None = None


class VoiceIntroResponse(BaseModel):
    voice_intro_url: str | None


@router.post("/voice-intro", response_model=VoiceIntroResponse, status_code=status.HTTP_201_CREATED)
async def record_voice_intro(
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
    clip: Annotated[UploadFile, File()],
) -> VoiceIntroResponse:
    """[Product owner 2026-09-17] Record or replace the spoken introduction on
    the caller's own profile. Heard only by an accepted connection."""
    try:
        url = await profile.save_voice_intro(session, account_id=account_id, clip=clip)
    except profile.ProfileNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=translate("profile.error.notFound", lang),
        ) from exc
    except UnsupportedMedia as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("profile.error.unsupportedRecording", lang),
        ) from exc
    return VoiceIntroResponse(voice_intro_url=url)


@router.get("/voice-intro", response_model=VoiceIntroResponse)
async def get_voice_intro(
    session: DbSession, account_id: AuthenticatedAccount
) -> VoiceIntroResponse:
    """[Product owner 2026-09-17] The caller's own spoken introduction, if any."""
    own = await profile.get_own_profile(session, account_id=account_id)
    if own is None:
        return VoiceIntroResponse(voice_intro_url=None)
    return VoiceIntroResponse(
        voice_intro_url=await profile.voice_intro_url(session, profile_id=own.id)
    )


@router.delete("/voice-intro", status_code=status.HTTP_204_NO_CONTENT)
async def remove_voice_intro(
    session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> None:
    """[Product owner 2026-09-17] Remove the spoken introduction."""
    try:
        await profile.delete_voice_intro(session, account_id=account_id)
    except profile.ProfileNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=translate("profile.error.notFound", lang),
        ) from exc


@router.get("/view/{target_account_id}/full", response_model=ProfileViewResponse | None)
async def get_profile_full(
    target_account_id: UUID, session: DbSession, account_id: AuthenticatedAccount
) -> ProfileViewResponse | None:
    """[FR020/FR021] The full permitted profile in one response; `null` when
    the caller is not authorized, indistinguishable from no such profile."""
    result = await profile.view_profile_full(
        session, viewer_account_id=account_id, target_account_id=target_account_id
    )
    if result is None:
        return None
    return ProfileViewResponse(
        profile=_to_response(result.profile),
        photos=[_photo_response(p) for p in result.photos],
        attributes=result.attributes,  # type: ignore[arg-type]
        # Heard only by an accepted connection — RLS decides, not this route.
        voice_intro_url=await profile.voice_intro_url(session, profile_id=result.profile.id),
    )


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
    request: Request,
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
) -> None:
    # [DEC-V1-019] Only the candidate speaks in their own words: a parent
    # filling in a profile they created may not write the prompts or the ten
    # choices, even before the candidate takes the profile over.
    if category in ("in_my_words", "outlook", "openly", "self_scales") and getattr(
        request.state, "managing_for", None
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="candidate only")
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
        if category == "horoscope":
            # Recalculate the kundli from the new details. A calculation
            # failure never loses the save: the chart is made on next view.
            from app.components.horoscope import interface as horoscope

            try:
                await horoscope.refresh_chart(session, account_id=account_id)
            except horoscope.HoroscopeUnavailable:
                pass
    except profile.ProfileNotFound as exc:
        raise _profile_not_found(lang) from exc
    except profile.UnknownAttributes as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "unknown_attributes", "category": exc.category, "keys": exc.keys},
        ) from exc
    except horoscope_fields.InvalidAttributeValue as exc:
        # Names the field and the rule, never the submitted value.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "invalid_value", "category": exc.category, "key": exc.key, "reason": exc.reason},
        ) from exc


class PlaceResponse(BaseModel):
    id: str
    label: str
    name: str
    region: str
    country: str
    timezone: str


@router.get("/places/search", response_model=list[PlaceResponse])
async def search_places(q: str, account_id: AuthenticatedAccount, limit: int = 8) -> list[PlaceResponse]:
    """Place-of-birth search for the horoscope editor: type a few letters,
    pick one. The chosen id is what the editor saves; coordinates and time
    zone are resolved on the server (components/places)."""
    from app.components.places import interface as places

    return [
        PlaceResponse(id=p.id, label=p.label, name=p.name, region=p.region, country=p.country, timezone=p.timezone)
        for p in places.search(q[:80], limit=min(max(limit, 1), 12))
    ]



# ---------------------------------------------------------------------------
# [Migration 047 / DEC-V1-027] "My profile" for a parent, sibling or relative
# ---------------------------------------------------------------------------


class MemberProfileResponse(BaseModel):
    photo_url: str | None = None
    about: str | None = None
    city: str | None = None
    occupation: str | None = None


class MemberProfileRequest(BaseModel):
    about: str | None = None
    city: str | None = None
    occupation: str | None = None


def _member_response(m: profile.MemberProfile | None) -> MemberProfileResponse:
    if m is None:
        return MemberProfileResponse()
    return MemberProfileResponse(
        photo_url=m.photo_url, about=m.about, city=m.city, occupation=m.occupation
    )


@router.get("/member/me", response_model=MemberProfileResponse)  # "/member" alone is taken by GET /{category}
async def get_member(session: DbSession, account_id: AuthenticatedAccount) -> MemberProfileResponse:
    return _member_response(await profile.get_member_profile(session, account_id=account_id))


@router.patch("/member/me", response_model=MemberProfileResponse)
async def put_member(
    body: MemberProfileRequest, session: DbSession, account_id: AuthenticatedAccount
) -> MemberProfileResponse:
    return _member_response(
        await profile.save_member_profile(
            session,
            account_id=account_id,
            about=body.about,
            city=body.city,
            occupation=body.occupation,
        )
    )


@router.post("/member/photo", response_model=MemberProfileResponse)
async def put_member_photo(
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
    photo: UploadFile = File(...),  # noqa: B008
) -> MemberProfileResponse:
    try:
        m = await profile.set_member_photo(session, account_id=account_id, photo=photo)
    except UnsupportedMedia as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("profile.error.unsupportedPhoto", lang),
        ) from exc
    return _member_response(m)


# ---------------------------------------------------------------------------
# [DEC-V1-031] The AI matchmaker: the family's own words, what was understood,
# and the 1–10 scales. Under /profile so a parent editing a profile they made
# (X-Mangalya-Manage, DEC-V1-019) can describe the partner they want for their
# child; the candidate's ratings of themselves stay candidate-only.
# Two path segments each, so nothing collides with GET/PATCH /{category}.
# ---------------------------------------------------------------------------


class UnderstandRequest(BaseModel):
    text: str


class ScaleWish(BaseModel):
    want: int
    importance: int


class UnderstandResponse(BaseModel):
    items: list[dict[str, object]]
    scales: dict[str, ScaleWish]
    # "ai" when Claude read the words; "basic" for the built-in keyword reader.
    source: Literal["ai", "basic"]


class MatchmakerBrief(BaseModel):
    text: str = ""
    items: list[dict[str, object]] = []
    partner_scales: dict[str, ScaleWish] = {}
    # Omitted (None) leaves the saved ratings as they are.
    self_scales: dict[str, int] | None = None
    # [Owner, 2026-09-28] How much each theme matters, 1–10
    # (config/matching_engine.PRIORITY_THEMES). Omitted keeps what was saved.
    priorities: dict[str, int] | None = None


class MatchmakerBriefResponse(MatchmakerBrief):
    # False for a parent managing a profile: only the candidate rates themselves.
    can_rate_self: bool = True
    ai_available: bool = False
    # [Owner, 2026-09-28] Nothing said yet: starting points read from the
    # profile itself (an age range around the candidate's own age, their
    # city), for the family to keep, change or remove — never re-asked.
    suggested: list[dict[str, object]] = []
    # The candidate's own values each theme would compare with, so the page
    # can say "Same roots — Telugu, Khatri" instead of asking for them.
    theme_facts: dict[str, list[str]] = {}


def _clean_priorities(raw: dict[str, object] | None) -> dict[str, int]:
    from app.config.matching_engine import PRIORITY_THEMES

    out: dict[str, int] = {}
    for theme, value in (raw or {}).items():
        try:
            n = int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        if theme in PRIORITY_THEMES and 1 <= n <= 10:
            out[theme] = n
    return out


def _ai_available() -> bool:
    from app.config.settings import get_settings

    key = get_settings().anthropic_api_key
    return bool(key) and not key.startswith("CHANGE_ME")


@router.post("/matchmaker/understand", response_model=UnderstandResponse)
async def matchmaker_understand(
    body: UnderstandRequest, account_id: AuthenticatedAccount, lang: Locale
) -> UnderstandResponse:
    """Read the family's words into items and scale wishes. Saves nothing —
    the "What we understood" card shows them for the family to adjust first."""
    from app.components.compatibility import interface as compatibility
    from app.config.settings import get_settings
    from app.rate_limiting import limiter

    try:
        await limiter.enforce_durable(
            scope=limiter.RateLimitScope.MATCHMAKER_UNDERSTAND,
            subject=str(account_id),
            limit_max=get_settings().rate_limit_matchmaker_max_per_day,
            window_seconds=86400,
        )
    except limiter.RateLimitExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "rate_limited", "retry_after_seconds": exc.result.retry_after_seconds},
        ) from exc
    result = await compatibility.understand(body.text)
    return UnderstandResponse(
        items=result.items,
        scales={k: ScaleWish(**v) for k, v in result.scales.items()},
        source="ai" if result.source == "ai" else "basic",
    )


@router.get("/matchmaker/brief", response_model=MatchmakerBriefResponse)
async def matchmaker_get(
    request: Request, session: DbSession, account_id: AuthenticatedAccount, lang: Locale
) -> MatchmakerBriefResponse:
    wanted = await profile.get_category(session, account_id=account_id, category="partner_preference")
    if wanted is None:
        raise _profile_not_found(lang)
    own = await profile.get_category(session, account_id=account_id, category="self_scales") or {}
    managing = bool(getattr(request.state, "managing_for", None))

    def value(key: str) -> object:
        entry = wanted.get(key)
        return entry[1] if entry and entry[0] is FieldState.VALUE else None

    brief = value("brief") if isinstance(value("brief"), dict) else {}
    scales = value("scales") if isinstance(value("scales"), dict) else {}
    saved_priorities = value("priorities") if isinstance(value("priorities"), dict) else {}
    from app.components.compatibility import interface as compatibility
    from app.components.discovery import interface as discovery
    from app.config.matching_engine import PRIORITY_THEMES

    items = compatibility.clean_items(brief.get("items"))
    snapshot = await discovery.get_snapshot(session, account_id=account_id) or {}

    suggested: list[dict[str, object]] = []
    if not items and not str(brief.get("text") or "").strip():
        age = None
        dob = snapshot.get("date_of_birth")
        if dob:
            from datetime import date

            born = date.fromisoformat(str(dob)[:10])
            today = date.today()
            age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        # What they already said in the older preference fields comes first.
        said_age = snapshot.get("partner_age_range")
        if isinstance(said_age, dict) and (said_age.get("min") or said_age.get("max")):
            suggested.append(
                {"field": "age", "importance": 6, "min": said_age.get("min"), "max": said_age.get("max"), "values": []}
            )
        elif age is not None:
            # The customary gap: a groom a few years older than the bride.
            low, high = (max(18, age - 5), age + 1) if snapshot.get("gender") == "male" else (max(21, age - 1), age + 5)
            suggested.append({"field": "age", "importance": 6, "min": low, "max": high, "values": []})
        said_places = [p.strip() for p in str(snapshot.get("partner_locality") or "").replace(" or ", ",").split(",") if p.strip()]
        city = str(snapshot.get("locality") or "").split(",")[0].strip()
        if said_places or city:
            suggested.append({"field": "locality", "importance": 5, "values": said_places or [city]})

    def shown(field: str) -> str | None:
        raw = {
            "mother_tongue": snapshot.get("mother_tongue"),
            "sub_community": snapshot.get("sub_community"),
            "locality": str(snapshot.get("locality") or "").split(",")[0].strip() or None,
            "diet": snapshot.get("lifestyle_diet"),
            "family_values": snapshot.get("family_values"),
            "family_type": snapshot.get("family_type"),
            "education": snapshot.get("education_level"),
        }.get(field)
        return str(raw) if raw else None

    theme_facts = {
        theme: [v for f in fields if (v := shown(f))] for theme, fields in PRIORITY_THEMES.items() if fields
    }

    return MatchmakerBriefResponse(
        text=str(brief.get("text") or ""),
        items=items,
        suggested=suggested,
        theme_facts=theme_facts,
        priorities=_clean_priorities(saved_priorities),
        partner_scales={k: ScaleWish(**v) for k, v in compatibility.clean_scales(scales).items()},
        # A parent managing the profile never reads the candidate's own ratings.
        self_scales=None
        if managing
        else {k: int(v) for k, (st, v) in own.items() if st is FieldState.VALUE and v is not None},
        can_rate_self=not managing,
        ai_available=_ai_available(),
    )


@router.patch("/matchmaker/brief", status_code=status.HTTP_204_NO_CONTENT)
async def matchmaker_save(
    body: MatchmakerBrief,
    request: Request,
    session: DbSession,
    account_id: AuthenticatedAccount,
    lang: Locale,
) -> None:
    """Save what the family confirmed. The items are re-validated here (the
    client never decides what the engine may read) and places get their
    coordinates on the server. The older partner-preference fields are kept
    in step, so the biodata, the discoverability gate and the reasons that
    read them agree with what was just said."""
    from datetime import date

    from app.components.compatibility import interface as compatibility
    from app.components.compatibility.understand import resolve_places
    from app.config.matching_engine import ENGINE_VERSION, MAX_BRIEF_CHARS, SCALES

    managing = bool(getattr(request.state, "managing_for", None))
    if body.self_scales is not None and managing:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="candidate only")

    items = resolve_places(compatibility.clean_items(body.items))
    scales = compatibility.clean_scales({k: v.model_dump() for k, v in body.partner_scales.items()})
    by_field = {i["field"]: i for i in items}
    attributes: dict[str, tuple[FieldState, object]] = {
        "brief": (
            FieldState.VALUE,
            {
                "text": body.text.strip()[:MAX_BRIEF_CHARS],
                "items": items,
                "engine": ENGINE_VERSION,
                "saved_on": date.today().isoformat(),
            },
        ),
        "scales": (FieldState.VALUE, scales),
    }
    if body.priorities is not None:
        attributes["priorities"] = (FieldState.VALUE, _clean_priorities(body.priorities))
    if (age := by_field.get("age")) is not None:
        attributes["age_range"] = (FieldState.VALUE, {"min": age.get("min"), "max": age.get("max")})
    if (height := by_field.get("height_cm")) is not None:
        attributes["height_range"] = (FieldState.VALUE, {"min": height.get("min"), "max": height.get("max")})
    if (place := by_field.get("locality")) is not None:
        attributes["locality"] = (FieldState.VALUE, " or ".join(place["values"]))
    for name in ("education", "diet"):
        if (item := by_field.get(name)) is not None:
            attributes[name] = (FieldState.VALUE, item["values"])
    try:
        await profile.update_category(
            session, account_id=account_id, category="partner_preference", attributes=attributes
        )
        if body.self_scales is not None:
            own = {
                k: (FieldState.VALUE, max(1, min(10, int(v))))
                for k, v in body.self_scales.items()
                if k in SCALES
            }
            if own:
                await profile.update_category(
                    session, account_id=account_id, category="self_scales", attributes=own
                )
    except profile.ProfileNotFound as exc:
        raise _profile_not_found(lang) from exc
