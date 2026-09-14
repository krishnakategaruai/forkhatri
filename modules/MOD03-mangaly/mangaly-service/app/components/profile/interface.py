"""Profile & Completeness — public interface.

`/MODULE-ARCHITECTURE-STANDARD.md` §3: this is the only way other components
reach profile state.

Implements:
  * FR001 / TR001 — existence-tier profile creation.

Security findings this module implements as code:
  * SP001 — `account_id` is resolved server-side from the caller's already-
    authenticated session (`api/deps.py`'s `AuthenticatedAccount`), never
    accepted as a client-supplied field.
  * TR041/DEC-V1-005 — marriageable-age gate, read from
    `config/thresholds.py`'s versioned setting, never a literal here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import delete, func, insert, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.profile import storage
from app.components.profile.models import (
    FieldState,
    MediaType,
    MediaUploadStatus,
    Profile,
    ProfileAttribute,
    ProfileMedia,
)
from app.config.profile_tiers import (
    DISCOVERABILITY_TIER_ATTRIBUTES,
    DISCOVERABILITY_TIER_PARTNER_PREFERENCE_ANY_OF,
    ENHANCED_MATCHING_CATEGORIES,
)
from app.config.thresholds import MARRIAGEABLE_AGE_DEFAULT_YEARS, MARRIAGEABLE_AGE_YEARS
from app.events import bus

__all__ = [
    "AlreadyExists",
    "CompletenessReport",
    "MissingRequiredFields",
    "ProfileNotFound",
    "TooYoung",
    "completeness",
    "create_profile",
    "get_all_attributes",
    "get_category",
    "get_own_profile",
    "is_discoverable",
    "lookup_account_by_profile_id",
    "lookup_profile_id_by_account",
    "update_category",
    "view_profile",
]


class MissingRequiredFields(Exception):
    """[FR001 failure outcome] Raised with the exact missing fields, never a
    generic failure — TR001/SP001 both require field-level errors."""

    def __init__(self, fields: list[str]) -> None:
        super().__init__(f"missing required fields: {fields}")
        self.fields = fields


class TooYoung(Exception):
    """[TR041/DEC-V1-005] The candidate is below the gender-specific
    marriageable-age threshold. Carries the threshold actually applied, so the
    caller can render FR041's "plain language, not a raw date-range error"
    requirement without re-deriving the number."""

    def __init__(self, required_years: int) -> None:
        super().__init__(f"below the {required_years}-year marriageable-age threshold")
        self.required_years = required_years


class AlreadyExists(Exception):
    """One profile per account (the DB's own UNIQUE constraint) — surfaced as
    a named exception rather than a raw integrity error reaching the caller."""


class ProfileNotFound(Exception):
    """[FR002/FR005] Raised by every non-creation profile operation when the
    caller has no saved profile yet — FR001 must run first."""


@dataclass(frozen=True, slots=True)
class ProfileSummary:
    id: UUID
    name: str
    date_of_birth: date
    gender: str
    city_locality: str
    photo_url: str | None


def _age_years(dob: date, today: date) -> int:
    years = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        years -= 1
    return years


def _required_age(gender: str) -> int:
    return MARRIAGEABLE_AGE_YEARS.get(gender, MARRIAGEABLE_AGE_DEFAULT_YEARS)


async def create_profile(
    session: AsyncSession,
    *,
    account_id: UUID,
    name: str,
    date_of_birth: date,
    gender: str,
    city_locality: str,
    photo: UploadFile,
) -> ProfileSummary:
    """[FR001/TR001] Create the existence-tier profile row plus its one
    required photo, in one transaction, publishing `ProfileCreated`.

    Raises `MissingRequiredFields`, `TooYoung`, or `AlreadyExists` — never a
    generic failure (SP001's own validation-failure-rate threshold).
    """
    missing = [
        field_name
        for field_name, value in (
            ("name", name),
            ("date_of_birth", date_of_birth),
            ("gender", gender),
            ("city_locality", city_locality),
        )
        if not value
    ]
    if missing:
        raise MissingRequiredFields(missing)

    required_years = _required_age(gender)
    if _age_years(date_of_birth, date.today()) < required_years:
        raise TooYoung(required_years)

    existing = (
        await session.execute(select(Profile.id).where(Profile.account_id == account_id))
    ).scalar_one_or_none()
    if existing is not None:
        raise AlreadyExists

    profile_id = uuid4()
    try:
        # No RETURNING — same RLS-under-INSERT reasoning as Identity Bridge's
        # account creation (`MODULE-ARCHITECTURE-STANDARD.md` §4's third RLS
        # failure mode): `profile_owner_or_granted`'s SELECT half depends on
        # `mangaly.authz_context`, which for a brand-new row resolves through
        # `is_self(account_id)` — already bindable here since the caller is
        # authenticated, but there is no reason to depend on RETURNING's extra
        # round trip when the id is already known application-side.
        await session.execute(
            insert(Profile).values(
                id=profile_id,
                account_id=account_id,
                name=name,
                date_of_birth=date_of_birth,
                gender=gender,
                city_locality=city_locality,
            )
        )
    except IntegrityError as exc:
        raise AlreadyExists from exc

    storage_ref = await storage.save_photo(profile_id, photo)
    await session.execute(
        insert(ProfileMedia).values(
            id=uuid4(),
            profile_id=profile_id,
            media_type=MediaType.PHOTO,
            storage_ref=storage_ref,
            is_primary=True,
            upload_status=MediaUploadStatus.COMPLETE,
        )
    )

    # [TR001] "publishes a ProfileCreated domain event ... consumed by the
    # Audit Bridge for BR15" — same transaction as the insert (TR069's outbox rule).
    await bus.publish(
        session,
        schema="mangaly_profile",
        aggregate_id=profile_id,
        event_type="ProfileCreated",
        payload={"account_id": str(account_id), "profile_id": str(profile_id)},
    )

    # [FR021/FR026/FR027] Interim synchronous call — see
    # `discovery.interface.refresh_index()`'s own docstring for why this is
    # not an event-consumer yet (TR069's dispatcher does not exist).
    await _refresh_discovery_index(session, account_id=account_id)

    return ProfileSummary(
        id=profile_id,
        name=name,
        date_of_birth=date_of_birth,
        gender=gender,
        city_locality=city_locality,
        photo_url=storage.resolve_url(storage_ref),
    )


async def _refresh_discovery_index(session: AsyncSession, *, account_id: UUID) -> None:
    """Deferred import, not module-scope: `discovery.interface` itself calls
    back into this module's own public functions to build its snapshot, so a
    top-level `from app.components.discovery import interface` here would be
    a real circular import, not just a style preference."""
    from app.components.discovery import interface as discovery_module

    await discovery_module.refresh_index(session, account_id=account_id)


async def get_own_profile(session: AsyncSession, *, account_id: UUID) -> ProfileSummary | None:
    """The caller's own profile, or None if they have not created one yet."""
    row = (
        await session.execute(select(Profile).where(Profile.account_id == account_id))
    ).scalar_one_or_none()
    if row is None:
        return None

    media = (
        await session.execute(
            select(ProfileMedia.storage_ref)
            .where(ProfileMedia.profile_id == row.id, ProfileMedia.is_primary.is_(True))
            .limit(1)
        )
    ).scalar_one_or_none()

    return ProfileSummary(
        id=row.id,
        name=row.name,
        date_of_birth=row.date_of_birth,
        gender=row.gender,
        city_locality=row.city_locality,
        photo_url=storage.resolve_url(media) if media else None,
    )


MAX_PHOTOS = 6


class PhotoLimitReached(Exception):
    """Already at `MAX_PHOTOS` — the same six-photo cap Hinge and Bumble use."""


class LastPhotoRequired(Exception):
    """DEC-V1-001's existence tier requires at least one photo, so the last
    remaining photo can be replaced but never removed outright."""


class PhotoNotFound(Exception):
    """No such photo on the caller's own profile."""


@dataclass(frozen=True, slots=True)
class PhotoSummary:
    id: UUID
    url: str
    is_primary: bool


async def _own_photo_rows(session: AsyncSession, profile_id: UUID) -> list:
    return list(
        (
            await session.execute(
                select(ProfileMedia.id, ProfileMedia.storage_ref, ProfileMedia.is_primary)
                .where(
                    ProfileMedia.profile_id == profile_id,
                    ProfileMedia.media_type == MediaType.PHOTO,
                    ProfileMedia.upload_status == MediaUploadStatus.COMPLETE,
                )
                .order_by(ProfileMedia.is_primary.desc(), text("created_at"))
            )
        ).all()
    )


async def list_own_photos(session: AsyncSession, *, account_id: UUID) -> list[PhotoSummary] | None:
    """The caller's own photos, main photo first, then oldest first. Self-only
    (`_own_profile_id`); other viewers keep reading only the primary photo
    through `get_own_profile()`/`view_profile()` under the same RLS."""
    profile_id = await _own_profile_id(session, account_id=account_id)
    if profile_id is None:
        return None
    return [
        PhotoSummary(id=row.id, url=storage.resolve_url(row.storage_ref), is_primary=row.is_primary)
        for row in await _own_photo_rows(session, profile_id)
        if row.storage_ref
    ]


async def add_photo(session: AsyncSession, *, account_id: UUID, photo: UploadFile) -> PhotoSummary:
    """Add one photo. The first photo on a profile becomes the main one."""
    profile_id = await _own_profile_id(session, account_id=account_id)
    if profile_id is None:
        raise ProfileNotFound
    count = (
        await session.execute(
            select(func.count())
            .select_from(ProfileMedia)
            .where(ProfileMedia.profile_id == profile_id, ProfileMedia.media_type == MediaType.PHOTO)
        )
    ).scalar_one()
    if count >= MAX_PHOTOS:
        raise PhotoLimitReached

    storage_ref = await storage.save_photo(profile_id, photo)
    media_id = uuid4()
    is_primary = count == 0
    await session.execute(
        insert(ProfileMedia).values(
            id=media_id,
            profile_id=profile_id,
            media_type=MediaType.PHOTO,
            storage_ref=storage_ref,
            is_primary=is_primary,
            upload_status=MediaUploadStatus.COMPLETE,
        )
    )
    await bus.publish(
        session,
        schema="mangaly_profile",
        aggregate_id=profile_id,
        event_type="ProfilePhotoAdded",
        payload={"profile_id": str(profile_id), "media_id": str(media_id)},
    )
    return PhotoSummary(id=media_id, url=storage.resolve_url(storage_ref), is_primary=is_primary)


async def delete_photo(session: AsyncSession, *, account_id: UUID, media_id: UUID) -> None:
    """Remove a photo; if it was the main one, the oldest remaining photo is
    promoted. The file itself is left on the local-disk stand-in — deleting
    stored bytes belongs to TR006's real Object Storage lifecycle, not here."""
    profile_id = await _own_profile_id(session, account_id=account_id)
    if profile_id is None:
        raise ProfileNotFound
    rows = await _own_photo_rows(session, profile_id)
    target = next((r for r in rows if r.id == media_id), None)
    if target is None:
        raise PhotoNotFound
    if len(rows) <= 1:
        raise LastPhotoRequired

    await session.execute(
        delete(ProfileMedia).where(ProfileMedia.id == media_id, ProfileMedia.profile_id == profile_id)
    )
    if target.is_primary:
        successor = next(r for r in rows if r.id != media_id)
        await session.execute(
            update(ProfileMedia).where(ProfileMedia.id == successor.id).values(is_primary=True)
        )
    await bus.publish(
        session,
        schema="mangaly_profile",
        aggregate_id=profile_id,
        event_type="ProfilePhotoRemoved",
        payload={"profile_id": str(profile_id), "media_id": str(media_id)},
    )


async def set_primary_photo(session: AsyncSession, *, account_id: UUID, media_id: UUID) -> None:
    """Make one photo the main one — exactly one primary per profile."""
    profile_id = await _own_profile_id(session, account_id=account_id)
    if profile_id is None:
        raise ProfileNotFound
    rows = await _own_photo_rows(session, profile_id)
    if not any(r.id == media_id for r in rows):
        raise PhotoNotFound

    await session.execute(
        update(ProfileMedia)
        .where(ProfileMedia.profile_id == profile_id, ProfileMedia.id != media_id)
        .values(is_primary=False)
    )
    await session.execute(
        update(ProfileMedia).where(ProfileMedia.id == media_id).values(is_primary=True)
    )


async def view_profile(
    session: AsyncSession, *, viewer_account_id: UUID, target_account_id: UUID
) -> ProfileSummary | None:
    """[FR021] View any account's profile — `viewer_account_id` may differ
    from `target_account_id`, unlike `get_own_profile()`. RLS
    (`profile_owner_or_granted`) is the only real gate, but its
    `has_scope()` half reads `mangaly.authz_context`, a variable only
    `authorization.interface.resolve()` ever sets — found live, 2026-09-14,
    the exact same missing-chokepoint-call bug already found and fixed in
    Home Circle's `suggest()`/`write_note()`. Binding it here, once, keeps
    `get_own_profile()` itself a plain self-scoped read with no audit
    side effect for its many existing self-only call sites, while this
    function is the one used wherever the viewer and target can genuinely
    differ.
    """
    from app.components.authorization import interface as authz
    from app.components.authorization.context import Action

    await authz.resolve(
        session,
        subject_id=viewer_account_id,
        account_id=viewer_account_id,
        target_profile_id=None,
        action=Action.READ,
    )
    return await get_own_profile(session, account_id=target_account_id)


async def lookup_profile_id_by_account(session: AsyncSession, *, account_id: UUID) -> UUID | None:
    """[Fourth instance of the third RLS failure mode, found live 2026-09-14]
    Resolve ANY account's real `profile.id` — used by `connection.interface
    .accept()` to grant `candidate_info` scope for the OTHER party in a
    connection, whose profile row the caller cannot yet read via
    `get_own_profile()` under `profile_owner_or_granted` (that grant is
    exactly what accepting is about to create). Goes through
    `mangaly_profile.lookup_profile_id_by_account()`, a SECURITY DEFINER
    function held to the same four constraints as every other instance of
    this pattern (exact-match only, minimal projection — the id column
    alone, no liveness state to enforce here since a profile has no
    active/inactive distinction at this level, at most one row).
    """
    row = (
        await session.execute(
            text("SELECT mangaly_profile.lookup_profile_id_by_account(:account_id)"),
            {"account_id": account_id},
        )
    ).scalar_one_or_none()
    return row


async def lookup_account_by_profile_id(session: AsyncSession, *, profile_id: UUID) -> UUID | None:
    """[Fifth instance of the third RLS failure mode, found live 2026-09-14]
    The reverse of `lookup_profile_id_by_account()` — used by
    `connection.interface.send_request()` to check whether a caller sending
    an on-behalf-of request is an authorized Home Circle member of the
    candidate BEFORE any `profile_attribute`/`profile` row for that
    candidate is otherwise reachable (FR042's own "unauthorized on-behalf-of
    requests are blocked" acceptance criterion). Goes through
    `mangaly_profile.lookup_account_by_profile_id()`, held to the same
    SECURITY DEFINER constraints as every other instance of this pattern.
    """
    row = (
        await session.execute(
            text("SELECT mangaly_profile.lookup_account_by_profile_id(:profile_id)"),
            {"profile_id": profile_id},
        )
    ).scalar_one_or_none()
    return row


async def _own_profile_id(session: AsyncSession, *, account_id: UUID) -> UUID | None:
    return (
        await session.execute(select(Profile.id).where(Profile.account_id == account_id))
    ).scalar_one_or_none()


async def _attribute_states(
    session: AsyncSession, *, profile_id: UUID
) -> dict[tuple[str, str], FieldState]:
    rows = (
        await session.execute(
            select(
                ProfileAttribute.category, ProfileAttribute.attribute_key, ProfileAttribute.state
            ).where(ProfileAttribute.profile_id == profile_id)
        )
    ).all()
    return {(category, key): state for category, key, state in rows}


async def update_category(
    session: AsyncSession,
    *,
    account_id: UUID,
    category: str,
    attributes: dict[str, tuple[FieldState, dict | list | str | int | float | bool | None]],
) -> None:
    """[FR002/TR002] Set or decline any number of `attribute_key`s within one
    category, in one transaction. `declined` always clears any stored value —
    a candidate who declines a field is not merely leaving old data in place,
    they are actively withdrawing it (the same tri-state reasoning `models.py`
    documents on `FieldState`).

    One `INSERT ... ON CONFLICT DO UPDATE` per key rather than a read-then-
    write: `profile_attribute`'s own UNIQUE(profile_id, category,
    attribute_key) constraint is the concurrency control, not an
    application-level check-then-act.
    """
    profile_id = await _own_profile_id(session, account_id=account_id)
    if profile_id is None:
        raise ProfileNotFound

    for attribute_key, (state, value) in attributes.items():
        stored_value = value if state is FieldState.VALUE else None
        stmt = pg_insert(ProfileAttribute).values(
            id=uuid4(),
            profile_id=profile_id,
            category=category,
            attribute_key=attribute_key,
            state=state,
            value=stored_value,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[
                ProfileAttribute.profile_id,
                ProfileAttribute.category,
                ProfileAttribute.attribute_key,
            ],
            set_={
                "state": stmt.excluded.state,
                "value": stmt.excluded.value,
                "updated_at": text("now()"),
            },
        )
        await session.execute(stmt)

    # [TR069] Same transaction as the upserts above — the outbox rule applies
    # here exactly as it does to `ProfileCreated`.
    await bus.publish(
        session,
        schema="mangaly_profile",
        aggregate_id=profile_id,
        event_type="ProfileAttributesUpdated",
        payload={
            "account_id": str(account_id),
            "profile_id": str(profile_id),
            "category": category,
            "attribute_keys": list(attributes.keys()),
        },
    )

    # [FR021/FR026/FR027] Any category can feed the Discovery snapshot or
    # flip the discoverability gate — refresh unconditionally rather than
    # maintaining a fragile "which categories matter" allow-list that could
    # silently go stale as new categories are added.
    await _refresh_discovery_index(session, account_id=account_id)


async def get_category(
    session: AsyncSession, *, account_id: UUID, category: str
) -> dict[str, tuple[FieldState, dict | list | str | int | float | bool | None]] | None:
    """[FR002] The caller's own saved attribute rows for one category —
    lets the editor pre-fill with what was actually saved rather than
    re-prompting an already-answered question. Returns `None` (not an empty
    dict) when the caller has no profile at all, so callers can tell "no
    profile yet" apart from "profile exists, category untouched"."""
    profile_id = await _own_profile_id(session, account_id=account_id)
    if profile_id is None:
        return None

    rows = (
        await session.execute(
            select(ProfileAttribute.attribute_key, ProfileAttribute.state, ProfileAttribute.value)
            .where(ProfileAttribute.profile_id == profile_id)
            .where(ProfileAttribute.category == category)
        )
    ).all()
    return {key: (state, value) for key, state, value in rows}


async def get_all_attributes(
    session: AsyncSession, *, account_id: UUID
) -> dict[str, dict[str, FieldState]] | None:
    """[FR002] Every saved attribute's state, grouped by category — powers the
    Profile edit hub's per-category filled/declined/empty cards in one query
    rather than one request per category (13 categories × a round trip each
    would be the chatty alternative). Values are deliberately omitted: the hub
    only needs state, not content, and this keeps the payload small."""
    profile_id = await _own_profile_id(session, account_id=account_id)
    if profile_id is None:
        return None

    rows = (
        await session.execute(
            select(
                ProfileAttribute.category, ProfileAttribute.attribute_key, ProfileAttribute.state
            ).where(ProfileAttribute.profile_id == profile_id)
        )
    ).all()
    grouped: dict[str, dict[str, FieldState]] = {}
    for category, key, state in rows:
        grouped.setdefault(category, {})[key] = state
    return grouped


async def get_all_attribute_values(
    session: AsyncSession, *, account_id: UUID
) -> dict[str, dict[str, tuple[FieldState, dict | list | str | int | float | bool | None]]] | None:
    """[FR002] The caller's OWN attributes with values, grouped by category —
    the Profile hub renders actual answers ("Vegetarian", "Master's degree")
    as value badges instead of bare filled/empty ticks. Self-only by
    construction (`_own_profile_id`), so this is never a disclosure path for
    anyone else's data; `get_all_attributes()` stays the lean state-only
    read for callers that only need completeness."""
    profile_id = await _own_profile_id(session, account_id=account_id)
    if profile_id is None:
        return None

    rows = (
        await session.execute(
            select(
                ProfileAttribute.category,
                ProfileAttribute.attribute_key,
                ProfileAttribute.state,
                ProfileAttribute.value,
            ).where(ProfileAttribute.profile_id == profile_id)
        )
    ).all()
    grouped: dict[str, dict[str, tuple[FieldState, object]]] = {}
    for category, key, state, value in rows:
        grouped.setdefault(category, {})[key] = (state, value)
    return grouped  # type: ignore[return-value]


async def is_discoverable(session: AsyncSession, *, profile_id: UUID) -> bool:
    """[FR003/TR003] The single shared discoverability gate — Discovery's own
    future search/matching code must call this rather than re-deriving it, so
    the two can never diverge (TR003/TR027's non-divergence contract)."""
    states = await _attribute_states(session, profile_id=profile_id)
    for category, key in DISCOVERABILITY_TIER_ATTRIBUTES:
        if states.get((category, key)) is not FieldState.VALUE:
            return False
    return any(
        states.get((category, key)) is FieldState.VALUE
        for category, key in DISCOVERABILITY_TIER_PARTNER_PREFERENCE_ANY_OF
    )


@dataclass(frozen=True, slots=True)
class CompletenessReport:
    """[FR005/TR005] Three physically separate tiers — UX11/UI11 both require
    these never be blended into one combined percentage."""

    existence_complete: bool
    discoverability_complete: bool
    discoverability_missing: list[str] = field(default_factory=list)
    enhanced_filled_categories: int = 0
    enhanced_total_categories: int = 0


async def completeness(session: AsyncSession, *, account_id: UUID) -> CompletenessReport | None:
    """[FR005/TR005] A pure read composed from the same `profile_attribute`
    rows `is_discoverable()` reads — no independent business logic and no
    cached/derived column, exactly as TR005 requires, so this can never drift
    out of sync with the gate it is describing."""
    profile_id = await _own_profile_id(session, account_id=account_id)
    if profile_id is None:
        return None

    states = await _attribute_states(session, profile_id=profile_id)

    missing: list[str] = [
        f"{category}.{key}"
        for category, key in DISCOVERABILITY_TIER_ATTRIBUTES
        if states.get((category, key)) is not FieldState.VALUE
    ]
    if not any(
        states.get((category, key)) is FieldState.VALUE
        for category, key in DISCOVERABILITY_TIER_PARTNER_PREFERENCE_ANY_OF
    ):
        missing.append("partner_preference.age_range_or_locality")

    touched_enhanced = {
        category
        for (category, _key), state in states.items()
        if state is FieldState.VALUE and category in ENHANCED_MATCHING_CATEGORIES
    }

    return CompletenessReport(
        # [FR001] Reaching this point at all means the existence tier is
        # already satisfied — FR001's own required-field gate runs at profile
        # creation, so there is no "existing but existence-incomplete" state.
        existence_complete=True,
        discoverability_complete=not missing,
        discoverability_missing=missing,
        enhanced_filled_categories=len(touched_enhanced),
        enhanced_total_categories=len(ENHANCED_MATCHING_CATEGORIES),
    )
