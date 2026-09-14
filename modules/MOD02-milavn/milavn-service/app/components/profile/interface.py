"""Member Profile — public interface (architecture.md §2.1, `milavn_profile`).

# [FR001, FR002, FR003, TR01] A usable profile exists once locality + at
# least one interest are saved; language is a person-level field; optional
# enrichment (photo/bio) never gates anything.
# Approach: `save_onboarding()` validates the two required inputs and names
# each missing one (FR001's failure outcome), upserting `member_profile` and
# replacing `member_interest` rows in the caller's transaction. Language and
# enrichment are separate writes so an unset language or a failed photo upload
# can never block the profile itself (TR01's two-transaction rule: the media
# reference is nullable and written after the profile row).
# `member_id` is a reference into the platform identity, never a local
# identity table (ADR-004).
# Traces to: FR001, FR002, FR003, FR085, TR01.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import localities
from app.config.interests import TAG_LABELS
from app.config.settings import get_settings

__all__ = [
    "MissingRequiredFields",
    "ProfileNotFound",
    "ProfileSummary",
    "get_own_profile",
    "get_public_profile",
    "save_onboarding",
    "set_language",
    "update_enrichment",
]

SUPPORTED_LANGUAGES = ("en", "hi", "te")
_ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


class MissingRequiredFields(Exception):
    def __init__(self, fields: list[str]) -> None:
        super().__init__(f"missing: {fields}")
        self.fields = fields


class ProfileNotFound(Exception):
    pass


class UnsupportedMedia(Exception):
    pass


@dataclass(frozen=True, slots=True)
class ProfileSummary:
    member_id: UUID
    locality_city: str
    locality_zone: str | None
    locality_locality: str | None
    language_preference: str
    interests: list[str]
    interest_labels: list[str]
    bio: str | None
    photo_url: str | None


_SELECT_PROFILE = text(
    """
    SELECT p.member_id, p.locality_city, p.locality_zone, p.locality_locality,
           p.language_preference, p.bio, m.storage_ref
    FROM milavn_profile.member_profile p
    LEFT JOIN milavn_profile.member_profile_media m
      ON m.id = p.photo_media_id AND m.upload_status = 'completed'
    WHERE p.member_id = :member_id
    """
)
_SELECT_INTERESTS = text("SELECT interest_tag FROM milavn_profile.member_interest WHERE member_id = :member_id ORDER BY created_at")


async def get_own_profile(session: AsyncSession, *, member_id: UUID) -> ProfileSummary | None:
    row = (await session.execute(_SELECT_PROFILE, {"member_id": str(member_id)})).first()
    if row is None:
        return None
    tags = [r[0] for r in (await session.execute(_SELECT_INTERESTS, {"member_id": str(member_id)})).all()]
    return ProfileSummary(
        member_id=row.member_id,
        locality_city=row.locality_city,
        locality_zone=row.locality_zone,
        locality_locality=row.locality_locality,
        language_preference=row.language_preference,
        interests=tags,
        interest_labels=[TAG_LABELS.get(t, t) for t in tags],
        bio=row.bio,
        photo_url=f"/media/{row.storage_ref}" if row.storage_ref else None,
    )


async def get_public_profile(session: AsyncSession, *, member_id: UUID) -> dict | None:
    """[TR01] The non-sensitive projection other components read (view)."""
    row = (
        await session.execute(
            text(
                "SELECT member_id, locality_city, locality_zone, locality_locality, language_preference "
                "FROM milavn_profile.member_public_profile WHERE member_id = :member_id"
            ),
            {"member_id": str(member_id)},
        )
    ).first()
    return dict(row._mapping) if row else None


async def save_onboarding(
    session: AsyncSession,
    *,
    member_id: UUID,
    locality_city: str | None,
    locality_zone: str | None,
    locality_locality: str | None,
    interests: list[str],
    language_preference: str | None,
) -> ProfileSummary:
    missing: list[str] = []
    city = (locality_city or "").strip()
    if not city:
        missing.append("locality_city")
    tags = sorted({t.strip().lower() for t in interests if t and t.strip()})
    if not tags:
        missing.append("interests")
    if missing:
        raise MissingRequiredFields(missing)

    loc = localities.find(city, locality_locality)
    zone = loc.zone if loc else (locality_zone or None)
    lang = language_preference if language_preference in SUPPORTED_LANGUAGES else None

    await session.execute(
        text(
            """
            INSERT INTO milavn_profile.member_profile
                (member_id, locality_city, locality_zone, locality_locality, language_preference)
            VALUES (:member_id, :city, :zone, :locality, COALESCE(:lang, 'en'))
            ON CONFLICT (member_id) DO UPDATE
              SET locality_city = EXCLUDED.locality_city,
                  locality_zone = EXCLUDED.locality_zone,
                  locality_locality = EXCLUDED.locality_locality,
                  language_preference = COALESCE(:lang, milavn_profile.member_profile.language_preference),
                  updated_at = now()
            """
        ),
        {
            "member_id": str(member_id),
            "city": city,
            "zone": zone,
            "locality": (locality_locality or None),
            "lang": lang,
        },
    )
    await session.execute(
        text("DELETE FROM milavn_profile.member_interest WHERE member_id = :member_id"),
        {"member_id": str(member_id)},
    )
    for tag in tags:
        await session.execute(
            text("INSERT INTO milavn_profile.member_interest (member_id, interest_tag) VALUES (:member_id, :tag) ON CONFLICT DO NOTHING"),
            {"member_id": str(member_id), "tag": tag},
        )
    # [FR041] Default precision setting is created alongside the profile so the
    # shared helper (Location & Privacy) always has a row to read.
    await session.execute(
        text("INSERT INTO milavn_locationprivacy.location_precision_setting (member_id) VALUES (:member_id) ON CONFLICT (member_id) DO NOTHING"),
        {"member_id": str(member_id)},
    )
    summary = await get_own_profile(session, member_id=member_id)
    assert summary is not None
    return summary


async def set_language(session: AsyncSession, *, member_id: UUID, language: str) -> ProfileSummary:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(language)
    result = await session.execute(
        text("UPDATE milavn_profile.member_profile SET language_preference = :lang, updated_at = now() WHERE member_id = :member_id"),
        {"lang": language, "member_id": str(member_id)},
    )
    if result.rowcount == 0:
        raise ProfileNotFound
    summary = await get_own_profile(session, member_id=member_id)
    assert summary is not None
    return summary


async def update_enrichment(
    session: AsyncSession,
    *,
    member_id: UUID,
    bio: str | None,
    photo: UploadFile | None,
    extra_interests: list[str] | None,
) -> ProfileSummary:
    existing = await get_own_profile(session, member_id=member_id)
    if existing is None:
        raise ProfileNotFound

    if bio is not None:
        await session.execute(
            text("UPDATE milavn_profile.member_profile SET bio = NULLIF(:bio, ''), updated_at = now() WHERE member_id = :member_id"),
            {"bio": bio.strip(), "member_id": str(member_id)},
        )
    if extra_interests:
        for tag in {t.strip().lower() for t in extra_interests if t.strip()}:
            await session.execute(
                text("INSERT INTO milavn_profile.member_interest (member_id, interest_tag) VALUES (:member_id, :tag) ON CONFLICT DO NOTHING"),
                {"member_id": str(member_id), "tag": tag},
            )
    if photo is not None and photo.filename:
        storage_ref = await _store_photo(member_id, photo)
        media_id = uuid4()
        await session.execute(
            text("INSERT INTO milavn_profile.member_profile_media (id, member_id, storage_ref, upload_status) VALUES (:id, :member_id, :ref, 'completed')"),
            {"id": str(media_id), "member_id": str(member_id), "ref": storage_ref},
        )
        await session.execute(
            text("UPDATE milavn_profile.member_profile SET photo_media_id = :mid, updated_at = now() WHERE member_id = :member_id"),
            {"mid": str(media_id), "member_id": str(member_id)},
        )
    summary = await get_own_profile(session, member_id=member_id)
    assert summary is not None
    return summary


async def _store_photo(member_id: UUID, photo: UploadFile) -> str:
    """Local-disk stand-in for Object Storage (TR01 pre-signed upload)."""
    ext = _ALLOWED_IMAGE_TYPES.get(photo.content_type or "")
    if ext is None:
        raise UnsupportedMedia(photo.content_type or "unknown")
    root: Path = get_settings().media_root / "profiles"
    root.mkdir(parents=True, exist_ok=True)
    name = f"{member_id}-{uuid4().hex[:8]}{ext}"
    with (root / name).open("wb") as fh:
        shutil.copyfileobj(photo.file, fh)
    return f"profiles/{name}"
