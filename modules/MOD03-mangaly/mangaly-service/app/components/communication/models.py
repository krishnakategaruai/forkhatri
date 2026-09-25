"""SQLAlchemy models for the `mangaly_communication` schema.

# [TR049] One model module per component package. Columns mirror
# `schema.sql` exactly. Only `conversation`/`message`/`conversation_participant`
# are modeled — `contact_exchange_request`, `retention_policy_exception`,
# `legal_hold`, and `retention_job_run` are BR12/FR050/FR053/FR054 scaffolding,
# out of scope, and are left unmapped rather than guessed at.
# Traces to: TR049, SP049, SP051, DEC-V1-024 (migration 035).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

_SCHEMA = "mangaly_communication"


class Conversation(Base):
    """[TR049, migrations 026/035] One row per (connection, kind). `candidate`
    is opened when the connection is accepted; `family` when either candidate
    involves their family."""

    __tablename__ = "conversation"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    connection_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    kind: Mapped[str] = mapped_column(default="candidate")
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))


class ConversationParticipant(Base):
    """[Migration 035] The roster, with per-person `last_read_at`."""

    __tablename__ = "conversation_participant"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey(f"{_SCHEMA}.conversation.id", ondelete="CASCADE")
    )
    account_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    joined_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    last_read_at: Mapped[datetime | None] = mapped_column(default=None)


class Message(Base):
    """[TR049/SP051] `content` is read, per live RLS, only by a participant of
    the conversation or an operator in an active safety-case investigation —
    `interface.py` never adds a second application-level path to it."""

    __tablename__ = "message"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    # [Migration 026] NULL for a system line: the platform is speaking, not a person.
    sender_account_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), default=None)
    content: Mapped[str]
    kind: Mapped[str] = mapped_column(default="member")
    sent_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
