"""SQLAlchemy models for the `mangaly_profile` schema.

# [TR001/TR002] One model module per component package, per the project's
# established ORM convention. Columns mirror `schema.sql` exactly — this file
# describes the already-applied schema, it does not define it (migrations stay
# authoritative). No cross-schema ForeignKey; `account_id` is a plain UUID
# column into `mangaly_identity.account`, resolved only through Identity
# Bridge's own interface, never joined directly (07a-er-model.md Assumptions #3).
# Traces to: TR001, TR002, TR006, SP001, SP002, SP006.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, ForeignKey, text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import OutboxEventMixin, TimestampMixin

_SCHEMA = "mangaly_profile"


class ProfileStatus(StrEnum):
    """Mirrors `mangaly_profile.profile_status`.

    [Found live, 2026-09-13] The live enum has exactly `active`/`paused` — no
    `concluded` member exists yet at the database level, despite TR079-TR081
    describing a conclude/reactivate lifecycle. That is TR079's own future
    migration to add, not something to guess a value for here.
    """

    ACTIVE = "active"
    PAUSED = "paused"


class MediaType(StrEnum):
    """Mirrors `mangaly_profile.media_type`."""

    PHOTO = "photo"
    VIDEO = "video"
    # [Migration 029] A spoken introduction the candidate records themselves.
    AUDIO = "audio"


class MediaUploadStatus(StrEnum):
    """Mirrors `mangaly_profile.media_upload_status`.

    [Found live, 2026-09-13] The live enum member is `complete`, not
    `uploaded` — caught only by an actual INSERT against the real database
    (`InvalidTextRepresentationError`), not by review of this file in isolation.
    """

    PENDING = "pending"
    COMPLETE = "complete"
    FAILED = "failed"


class Profile(Base, TimestampMixin):
    """[TR001] The existence-tier row — DEC-V1-001's four required columns.

    `account_id` is UNIQUE: one profile per account, matching FR001's model
    (a candidate has exactly one profile, family members act on it via grants,
    never own a second profile of their own for the same candidate).
    """

    __tablename__ = "profile"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), unique=True)
    name: Mapped[str]
    date_of_birth: Mapped[date] = mapped_column(Date)
    gender: Mapped[str]
    city_locality: Mapped[str]
    language_preference: Mapped[str] = mapped_column(default="en")
    status: Mapped[ProfileStatus] = mapped_column(
        SqlEnum(
            ProfileStatus,
            name="profile_status",
            schema=_SCHEMA,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=ProfileStatus.ACTIVE,
    )


class ProfileMedia(Base):
    """[TR001/TR006] One row per photo/video. `storage_ref` is an opaque
    pointer into whichever storage backend `app.components.profile.storage`
    is currently configured with — never a raw, permanently-public URL (TR006's
    short-TTL signed URL requirement lives at the read path, not stored here).
    """

    __tablename__ = "profile_media"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey(f"{_SCHEMA}.profile.id", ondelete="CASCADE")
    )
    media_type: Mapped[MediaType] = mapped_column(
        SqlEnum(
            MediaType,
            name="media_type",
            schema=_SCHEMA,
            values_callable=lambda e: [m.value for m in e],
        )
    )
    storage_ref: Mapped[str | None] = mapped_column(default=None)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    # [migration 013] Person-chosen grid order; position 0 is always the
    # primary photo (the application keeps the two in step).
    sort_order: Mapped[int] = mapped_column(default=0)
    upload_status: Mapped[MediaUploadStatus] = mapped_column(
        SqlEnum(
            MediaUploadStatus,
            name="media_upload_status",
            schema=_SCHEMA,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=MediaUploadStatus.PENDING,
    )
    uploaded_at: Mapped[datetime | None] = mapped_column(default=None)


class FieldState(StrEnum):
    """Mirrors `mangaly_profile.field_state`.

    [TR002] A column-level tri-state, never collapsed to null: `declined` is
    a first-class, distinct fact from `unset` — a candidate who declined a
    field made an active choice, which is not the same as never having been
    asked. DEC-V1-001's tier gates read this state, not just presence.
    """

    UNSET = "unset"
    DECLINED = "declined"
    VALUE = "value"


class ProfileAttribute(Base):
    """[TR002] One row per (category, attribute_key) — every non-existence-
    tier field a candidate can fill, decline, or leave unset. Deliberately a
    generic (category, key, state, value) shape rather than one column per
    field: DEC-V1-001 fixes which fields belong to which TIER, not a frozen
    DDL shape, and FR002's own Assumptions state the exact per-category field
    schema is still implementation-stage. `config/profile_tiers.py` is the
    one place that maps (category, key) pairs to tier membership.
    """

    __tablename__ = "profile_attribute"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey(f"{_SCHEMA}.profile.id", ondelete="CASCADE")
    )
    category: Mapped[str]
    attribute_key: Mapped[str]
    state: Mapped[FieldState] = mapped_column(
        SqlEnum(
            FieldState,
            name="field_state",
            schema=_SCHEMA,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=FieldState.UNSET,
    )
    value: Mapped[dict | None] = mapped_column(JSONB, default=None)
    updated_at: Mapped[datetime] = mapped_column(server_default=text("now()"))


class ProfileOutboxEvent(Base, OutboxEventMixin):
    __table_args__ = {"schema": _SCHEMA}
