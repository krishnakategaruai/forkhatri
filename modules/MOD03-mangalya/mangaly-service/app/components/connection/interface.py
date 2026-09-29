"""Connection — public interface.

`/MODULE-ARCHITECTURE-STANDARD.md` §3: this is the only way other components
reach Connection state.

Implements:
  * FR042 / TR042 — send a connection request (self or on-behalf-of).
  * FR043 / TR043 — recipient review and accept/decline.
  * FR044 / TR044 — acceptance triggers nothing beyond the connection-state
    write itself and the `candidate_info` grants that write IS (see
    `respond()`'s docstring — this is a considered reading of FR044's "no
    downstream side effects" wording, not an oversight).
  * FR045 — no single-active-connection constraint; a candidate can hold any
    number of concurrent connections (the schema has no unique constraint
    here, matching this deliberately — never add one "to be safe").

Security findings this module implements as code:
  * [Confirmed live, 2026-09-13] `target_profile_id`/`acting_account_id` are
    account ids (`connection_participants` calls `is_self()`). The
    `candidate_info` grants `respond()` creates on acceptance are a THIRD id
    convention: `mangaly_profile.profile`'s own RLS reads `has_scope(id, ...)`
    against the real `profile.id`, so those two grants (one per direction)
    must target `profile.id`, not the account id `connection_request` itself
    uses — see `models.py`'s module docstring for the full reasoning.
  * SP042 — no rate limit is named in TR042's own text; Step 8 flagged
    connection-request spam as a real harassment vector, so one is applied
    here anyway rather than left for a later pass to notice missing.
  * [Real gap found live, 2026-09-14] FR042's own acceptance criterion —
    "Unauthorized on-behalf-of requests are blocked" — was unimplemented:
    `send_request()` accepted a caller-supplied `on_behalf_of_profile_id`
    with no check that the caller is actually an authorized Home Circle
    member of that candidate at all, meaning ANY account could send a
    request "on behalf of" any candidate profile.id it could discover,
    misattributing the request's origin (BR15's accountability guarantee)
    with no gate at all. Fixed by resolving the candidate's owning account
    (`profile.lookup_account_by_profile_id()`, a new SECURITY DEFINER
    function — the reverse of the one `connection.accept()` already uses,
    same RLS bind in reverse) and requiring `GrantScope.FAMILY_INFO` on that
    account through the standard `authorization.interface.resolve()`
    chokepoint before the request is allowed to name anyone but the caller
    themselves.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.connection.models import ConnectionRequest, ConnectionStatus, SharingGrant
from app.config.settings import get_settings
from app.events import bus
from app.rate_limiting import limiter

__all__ = [
    "SHARE_CATEGORIES",
    "AlreadyPending",
    "ConnectionNotFound",
    "ConnectionSummary",
    "InvalidTarget",
    "NotLookingFor",
    "OnBehalfRoleNotAllowed",
    "RequestCooldown",
    "declined_ids",
    "RateLimited",
    "ShareState",
    "ShareUnavailable",
    "SharingOverview",
    "OnBehalfNotAllowed",
    "Blocked",
    "SentBy",
    "accept",
    "connected_ids",
    "connection_between",
    "decline",
    "sender_info",
    "withdraw",
    "get_request",
    "has_active_share",
    "list_incoming",
    "list_sent",
    "send_request",
    "set_share",
    "sharing_overview",
    "FamilyContactRequest",
    "FamilyContactRequestNotFound",
    "NotAHomeCircleMember",
    "decide_family_contact_request",
    "family_contact_overview",
    "list_family_contact_requests",
    "request_family_contact",
    "withdraw_family_contact",
]

_SOURCE = "connection"


class InvalidTarget(Exception):
    """[FR042 failure outcome] Cannot connect to yourself, or the target has
    no profile at all."""


class NotLookingFor(Exception):
    """The two are not what each other is looking for (bride / groom): a
    request may only reach someone search would show."""


class RequestCooldown(Exception):
    """[Owner, 2026-09-25] This side was declined (or withdrew) recently and
    may not ask the same person again until `until`."""

    def __init__(self, until: datetime, reason: str) -> None:
        super().__init__(f"{reason} until {until.isoformat()}")
        self.until = until
        self.reason = reason  # "declined" | "withdrawn"


class OnBehalfRoleNotAllowed(Exception):
    """[Owner, 2026-09-25] Only a parent or guardian may send a request on a
    candidate's behalf; siblings and relatives suggest instead."""


class OnBehalfNotAllowed(Exception):
    """[FR042, DEC-V1-019] A request named an `on_behalf_of_profile_id`. Family
    members suggest a profile to the candidate (FR014); only the candidate
    sends a connection request, because a request is the candidate's own
    decision (M01-I §6–7: suggestion is not consent, initiation authority is
    not decision authority)."""


class Blocked(Exception):
    """[Contract §3] One of the two people has blocked the other; nothing
    may be sent between them, in either direction, by anyone."""


class AlreadyPending(Exception):
    """[FR045] Not a "no repeat connections" rule (FR045 explicitly allows
    many) — just a spam guard: an already-pending request to the SAME target
    should not be duplicated by a second tap of the same button."""


class AlreadyConnected(Exception):
    """The two are already connected, so there is nothing to request.

    [2026-09-21] The pending-only guard above let a SECOND request through
    once the first had been accepted, and acceptance opens a conversation per
    connection — so two people could accumulate several live connections and
    several parallel threads with each other. A connection is a state between
    two people, not a log of attempts: at most one may be live at a time, in
    either direction."""


class ConnectionNotFound(Exception):
    """The connection does not exist, is not visible to this caller under
    RLS, or is no longer `pending` (for a response action)."""


class RateLimited(Exception):
    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__(f"retry after {retry_after_seconds}s")
        self.retry_after_seconds = retry_after_seconds


@dataclass(frozen=True, slots=True)
class ConnectionSummary:
    id: UUID
    acting_account_id: UUID
    subject_account_id: UUID
    on_behalf_of_profile_id: UUID | None
    target_account_id: UUID
    status: ConnectionStatus
    requested_at: datetime
    decided_at: datetime | None


def _to_summary(row: ConnectionRequest) -> ConnectionSummary:
    return ConnectionSummary(
        id=row.id,
        acting_account_id=row.acting_account_id,
        subject_account_id=row.subject_account_id,
        on_behalf_of_profile_id=row.on_behalf_of_profile_id,
        target_account_id=row.target_profile_id,
        status=row.status,
        requested_at=row.requested_at,
        decided_at=row.decided_at,
    )


async def send_request(
    session: AsyncSession,
    *,
    acting_account_id: UUID,
    target_account_id: UUID,
    on_behalf_of_account_id: UUID | None = None,
) -> UUID:
    """[FR042/TR042] Send a connection request — for yourself, or for a candidate
    whose Home Circle you belong to.

    [2026-09-17, owner decision, replacing DEC-V1-019] A parent who runs the
    profile may send the request themselves, as families do on Shaadi.com and the
    other Indian matrimony services; FR042's own sealed wording always said "a
    candidate or authorized family participant ... self or on-behalf-of". What
    DEC-V1-019 was actually protecting against — the candidate ending up connected
    to someone they never chose, and acceptance granting profile visibility to the
    parent instead of the candidate — is fixed in migration 023 rather than by
    removing the capability: `acting_account_id` records WHO pressed send (BR15
    accountability), `subject_account_id` records WHOSE request it is, and every
    downstream rule (visibility, sharing, conversation, acceptance grants) keys on
    the subject.

    `acting_account_id` is always the authenticated caller (SP001-class: never
    client-supplied). Sending for someone else requires `family_info` on that
    candidate; without it the request is refused, never quietly downgraded to a
    request from the caller themselves."""
    subject_account_id = acting_account_id
    on_behalf_of_profile_id: UUID | None = None
    if on_behalf_of_account_id is not None and on_behalf_of_account_id != acting_account_id:
        from app.components.authorization import interface as authorization
        from app.components.authorization.context import (
            Action,
            AuthorizationDenied,
            Capacity,
            GrantScope,
        )
        from app.components.profile import interface as profile_module

        context = await authorization.resolve(
            session,
            subject_id=acting_account_id,
            account_id=acting_account_id,
            target_profile_id=on_behalf_of_account_id,
            action=Action.WRITE,
            capacity=Capacity.FAMILY,
        )
        try:
            context.require_scope(GrantScope.FAMILY_INFO)
        except AuthorizationDenied as exc:
            raise OnBehalfNotAllowed from exc
        # [Owner, 2026-09-25] Sending is a decision: the candidate, a parent
        # or a guardian. Siblings and relatives suggest (FR014) instead.
        from app.components.home_circle import interface as home_circle

        contexts = await home_circle.list_member_contexts(session, account_id=acting_account_id)
        mine = next(
            (c for c in contexts if c.candidate_account_id == on_behalf_of_account_id), None
        )
        if mine is None or mine.relationship_type.value not in ("parent", "guardian"):
            raise OnBehalfRoleNotAllowed
        subject_account_id = on_behalf_of_account_id
        # Stored as the candidate's real `profile.id`: that is the id space the row's
        # own RLS policy reads (`has_scope(on_behalf_of_profile_id, 'candidate_info')`).
        on_behalf_of_profile_id = await profile_module.lookup_profile_id_by_account(
            session, account_id=on_behalf_of_account_id
        )
        if on_behalf_of_profile_id is None:
            raise InvalidTarget

    if subject_account_id == target_account_id or acting_account_id == target_account_id:
        raise InvalidTarget

    from app.components.discovery import interface as discovery

    if not await discovery.looking_for_allows(
        session, seeker_account_id=subject_account_id, target_account_id=target_account_id
    ):
        raise NotLookingFor

    from app.components.safety import interface as safety

    if await safety.is_blocked_between(session, subject_account_id, target_account_id) or (
        acting_account_id != subject_account_id
        and await safety.is_blocked_between(session, acting_account_id, target_account_id)
    ):
        raise Blocked

    settings = get_settings()
    try:
        await limiter.enforce_durable(
            scope=limiter.RateLimitScope.CONNECTION_REQUEST,
            subject=str(subject_account_id),
            limit_max=settings.rate_limit_connection_request_max_per_day,
            window_seconds=86400,
        )
    except limiter.RateLimitExceeded as exc:
        raise RateLimited(exc.result.retry_after_seconds) from exc

    # One live connection per pair, whichever side opened it. Declined and
    # withdrawn rows are not live, so FR045's "ask again later" still works.
    pair = or_(
        and_(
            ConnectionRequest.subject_account_id == subject_account_id,
            ConnectionRequest.target_profile_id == target_account_id,
        ),
        and_(
            ConnectionRequest.subject_account_id == target_account_id,
            ConnectionRequest.target_profile_id == subject_account_id,
        ),
    )
    live = (
        await session.execute(
            select(ConnectionRequest.status).where(
                pair,
                ConnectionRequest.status.in_(
                    (ConnectionStatus.PENDING, ConnectionStatus.ACCEPTED)
                ),
            )
        )
    ).scalars().first()
    if live is ConnectionStatus.ACCEPTED:
        raise AlreadyConnected
    if live is ConnectionStatus.PENDING:
        raise AlreadyPending

    # [Owner, 2026-09-25] Cool-downs apply to the side that asked: after a
    # decline (90 days) or its own withdrawal (21 days). The person who
    # declined may still ask the other way at any time.
    until = await _cooldown_until(
        session, subject_account_id=subject_account_id, target_account_id=target_account_id
    )
    if until is not None:
        raise RequestCooldown(*until)

    connection_id = uuid4()
    await session.execute(
        text(
            """
            INSERT INTO mangaly_connection.connection_request
                (id, acting_account_id, subject_account_id, on_behalf_of_profile_id,
                 target_profile_id, status)
            VALUES (:id, :acting, :subject, :on_behalf_of, :target, 'pending')
            """
        ),
        {
            "id": connection_id,
            "acting": acting_account_id,
            "subject": subject_account_id,
            "on_behalf_of": on_behalf_of_profile_id,
            "target": target_account_id,
        },
    )
    on_behalf_str = str(on_behalf_of_profile_id) if on_behalf_of_profile_id else None
    await bus.publish(
        session,
        schema="mangaly_connection",
        aggregate_id=connection_id,
        event_type="ConnectionRequested",
        payload={
            "connection_id": str(connection_id),
            "acting_account_id": str(acting_account_id),
            "subject_account_id": str(subject_account_id),
            "target_account_id": str(target_account_id),
            "on_behalf_of_profile_id": on_behalf_str,
        },
    )

    # [Contract §3] The recipient — and their circle — learn an interest
    # arrived. Only the demographic snippet travels (never a name).
    from app.components.discovery import interface as discovery
    from app.components.notification_bridge import interface as notifications

    snippet = await discovery.get_snippet(session, account_id=subject_account_id)
    card = (await discovery.cards_for(session, account_ids=[subject_account_id])).get(
        subject_account_id
    )
    sent_by = await sender_info(session, connection_id=connection_id)
    await notifications.notify_circle(
        session,
        candidate_account_id=target_account_id,
        kind="request_received",
        payload={
            "connection_id": connection_id,
            "subject_account_id": subject_account_id,
            "sent_by_relationship": sent_by.relationship if sent_by else "self",
            "locality": snippet.locality if snippet else None,
            "profession": snippet.profession if snippet else None,
            "age": card.age if card else None,
        },
        link=f"/requests/{connection_id}",
    )
    return connection_id


async def list_incoming(session: AsyncSession, *, account_id: UUID) -> list[ConnectionSummary]:
    """[FR043] Requests where the caller is the target, pending review."""
    rows = (
        await session.execute(
            select(ConnectionRequest)
            .where(
                ConnectionRequest.target_profile_id == account_id,
                ConnectionRequest.status == ConnectionStatus.PENDING,
            )
            .order_by(ConnectionRequest.requested_at.desc())
        )
    ).scalars()
    return [_to_summary(r) for r in rows]


async def list_sent(session: AsyncSession, *, account_id: UUID) -> list[ConnectionSummary]:
    """[FR045] Every connection the caller has sent, any status — a candidate can
    hold several at once by design. Includes requests a Home Circle member sent in
    the caller's name (the caller is the subject) as well as requests the caller
    sent for a candidate they help (the caller is the sender)."""
    rows = (
        await session.execute(
            select(ConnectionRequest)
            .where(
                or_(
                    ConnectionRequest.acting_account_id == account_id,
                    ConnectionRequest.subject_account_id == account_id,
                )
            )
            .order_by(ConnectionRequest.requested_at.desc())
        )
    ).scalars()
    return [_to_summary(r) for r in rows]


async def _cooldown_until(
    session: AsyncSession, *, subject_account_id: UUID, target_account_id: UUID
) -> tuple[datetime, str] | None:
    """When this candidate may next ask this person, if a cool-down applies."""
    from datetime import timedelta

    settings = get_settings()
    rows = (
        await session.execute(
            select(ConnectionRequest.status, ConnectionRequest.decided_at).where(
                ConnectionRequest.subject_account_id == subject_account_id,
                ConnectionRequest.target_profile_id == target_account_id,
                ConnectionRequest.status.in_((ConnectionStatus.DECLINED, ConnectionStatus.WITHDRAWN)),
                ConnectionRequest.decided_at.is_not(None),
            )
        )
    ).all()
    now = datetime.now(UTC)
    best: tuple[datetime, str] | None = None
    for status_, decided_at in rows:
        days = (
            settings.request_cooldown_after_decline_days
            if status_ is ConnectionStatus.DECLINED
            else settings.request_cooldown_after_withdraw_days
        )
        until = decided_at + timedelta(days=days)
        if until > now and (best is None or until > best[0]):
            best = (until, status_.value)
    return best


async def declined_ids(session: AsyncSession, *, account_id: UUID) -> set[UUID]:
    """People who declined this candidate within the decline cool-down: they
    stay out of this candidate's Discover and New matches until it ends."""
    from datetime import timedelta

    cutoff = datetime.now(UTC) - timedelta(days=get_settings().request_cooldown_after_decline_days)
    rows = (
        await session.execute(
            select(ConnectionRequest.target_profile_id).where(
                ConnectionRequest.subject_account_id == account_id,
                ConnectionRequest.status == ConnectionStatus.DECLINED,
                ConnectionRequest.decided_at > cutoff,
            )
        )
    ).scalars()
    return set(rows)


async def connected_ids(session: AsyncSession, *, account_id: UUID) -> set[UUID]:
    """Everyone this candidate has an ACCEPTED connection with, in either
    direction. Discovery leaves them out: the relationship already lives in
    Messages and on their profile, so they are no longer "new matches"
    (pending requests stay, with their state on the card)."""
    rows = (
        await session.execute(
            select(ConnectionRequest.subject_account_id, ConnectionRequest.target_profile_id).where(
                ConnectionRequest.status == ConnectionStatus.ACCEPTED,
                or_(
                    ConnectionRequest.subject_account_id == account_id,
                    ConnectionRequest.target_profile_id == account_id,
                ),
            )
        )
    ).all()
    return {target if subject == account_id else subject for subject, target in rows}


async def get_request(session: AsyncSession, *, connection_id: UUID) -> ConnectionSummary | None:
    """[FR043] One request's full detail, for the review screen. RLS alone
    decides visibility — a caller who is neither party sees nothing, the
    same zero-row-under-RLS pattern this codebase uses everywhere else
    rather than an application-level ownership check that could drift."""
    row = (
        await session.execute(
            select(ConnectionRequest).where(ConnectionRequest.id == connection_id)
        )
    ).scalar_one_or_none()
    return _to_summary(row) if row else None


async def accept(
    session: AsyncSession,
    *,
    connection_id: UUID,
    account_id: UUID,
    acting_account_id: UUID | None = None,
) -> None:
    """[FR043/FR044/TR043/TR044] Accept: flips status and grants each party
    `candidate_info` visibility into the other's real profile — the two
    grants ARE the meaning of "accepted". `account_id` is the recipient
    CANDIDATE; `acting_account_id` is whoever pressed the button (the
    candidate, or a circle member acting for them under `family_info`,
    contract §6), recorded as `decided_by_account_id`.

    The two grants are created through `mangaly_authz
    .grant_connection_candidate_info()`, a SECURITY DEFINER function — see
    `migrations/010` for why one of them cannot be inserted by either party's
    own session under RLS.
    """
    row = (
        await session.execute(
            select(ConnectionRequest).where(
                ConnectionRequest.id == connection_id,
                ConnectionRequest.target_profile_id == account_id,
                ConnectionRequest.status == ConnectionStatus.PENDING,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise ConnectionNotFound

    now = datetime.now(UTC)
    await session.execute(
        text(
            "UPDATE mangaly_connection.connection_request "
            "SET status = 'accepted', decided_at = :now, decided_by_account_id = :decided_by, "
            "updated_at = :now WHERE id = :id"
        ),
        {"now": now, "decided_by": acting_account_id or account_id, "id": connection_id},
    )

    await session.execute(
        text("SELECT mangaly_authz.grant_connection_candidate_info(:connection_id, :account_id)"),
        {"connection_id": connection_id, "account_id": account_id},
    )

    # [FR049, migration 026] Acceptance opens the private conversation with one
    # system line, so both people learn the request succeeded where they will
    # actually talk.
    from app.components.communication import interface as communication

    await communication.open_conversation_on_accept(
        session, connection_id=connection_id, account_id=account_id
    )

    await bus.publish(
        session,
        schema="mangaly_connection",
        aggregate_id=connection_id,
        event_type="ConnectionAccepted",
        payload={
            "connection_id": str(connection_id),
            "acting_account_id": str(row.acting_account_id),
            "target_account_id": str(account_id),
            "decided_by_account_id": str(acting_account_id or account_id),
        },
    )

    # [Contract §3] The sending candidate and their circle learn it succeeded.
    from app.components.notification_bridge import interface as notifications
    from app.components.profile import interface as profile_module

    me = await profile_module.get_own_profile(session, account_id=account_id)
    await notifications.notify_circle(
        session,
        candidate_account_id=row.subject_account_id,
        kind="request_accepted",
        payload={
            "connection_id": connection_id,
            "other_account_id": account_id,
            "other_name": me.name if me else None,
        },
        link=f"/messages/{connection_id}",
    )


async def decline(
    session: AsyncSession,
    *,
    connection_id: UUID,
    account_id: UUID,
    acting_account_id: UUID | None = None,
) -> None:
    """[FR043] Decline: an explicit status, never a silent non-response —
    there is no auto-expiry transition on this endpoint or any other
    (FR043's own explicit failure-outcome requirement)."""
    row = (
        await session.execute(
            select(ConnectionRequest.id).where(
                ConnectionRequest.id == connection_id,
                ConnectionRequest.target_profile_id == account_id,
                ConnectionRequest.status == ConnectionStatus.PENDING,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise ConnectionNotFound

    await session.execute(
        text(
            "UPDATE mangaly_connection.connection_request "
            "SET status = 'declined', decided_at = :now, decided_by_account_id = :decided_by, "
            "updated_at = :now WHERE id = :id"
        ),
        {"now": datetime.now(UTC), "decided_by": acting_account_id or account_id, "id": connection_id},
    )


async def withdraw(
    session: AsyncSession,
    *,
    connection_id: UUID,
    account_id: UUID,
    acting_account_id: UUID | None = None,
) -> None:
    """[Contract §3] Take back a pending request. `account_id` is the SUBJECT
    candidate (self, or the candidate a circle member acts for). The
    recipient's incoming list no longer shows it; nothing else changes."""
    row = (
        await session.execute(
            select(ConnectionRequest.id).where(
                ConnectionRequest.id == connection_id,
                ConnectionRequest.subject_account_id == account_id,
                ConnectionRequest.status == ConnectionStatus.PENDING,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise ConnectionNotFound
    now = datetime.now(UTC)
    await session.execute(
        text(
            "UPDATE mangaly_connection.connection_request "
            "SET status = 'withdrawn', decided_at = :now, decided_by_account_id = :decided_by, "
            "updated_at = :now WHERE id = :id"
        ),
        {"now": now, "decided_by": acting_account_id or account_id, "id": connection_id},
    )
    await bus.publish(
        session,
        schema="mangaly_connection",
        aggregate_id=connection_id,
        event_type="ConnectionWithdrawn",
        payload={
            "connection_id": str(connection_id),
            "subject_account_id": str(account_id),
            "withdrawn_by_account_id": str(acting_account_id or account_id),
        },
    )


@dataclass(frozen=True, slots=True)
class SentBy:
    """[Contract §2] Who pressed send, in relation to the candidate it is for.
    `relationship` is `self` when the candidate sent it themselves, else the
    member's relation (`parent|guardian|sibling|relative`). `subject_name` /
    `target_name` are present only where identity is already disclosed
    (the sending side, or an accepted connection)."""

    acting_account_id: UUID
    subject_account_id: UUID
    relationship: str
    acting_name: str | None
    subject_name: str | None
    subject_profile_id: UUID | None
    target_name: str | None


async def sender_info(session: AsyncSession, *, connection_id: UUID) -> SentBy | None:
    row = (
        await session.execute(
            text("SELECT * FROM mangaly_connection.request_sender_info(:id)"), {"id": connection_id}
        )
    ).mappings().first()
    if row is None:
        return None
    return SentBy(
        acting_account_id=row["acting_account_id"],
        subject_account_id=row["subject_account_id"],
        relationship=row["relationship_type"],
        acting_name=row["acting_name"],
        subject_name=row["subject_name"],
        subject_profile_id=row["subject_profile_id"],
        target_name=row["target_name"],
    )


async def connection_between(
    session: AsyncSession, *, account_id: UUID, other_account_id: UUID
) -> ConnectionSummary | None:
    """The request that describes where two candidates stand, in either
    direction: a live one (accepted, then pending) before any ended one, then
    the most recent — what a profile screen needs to offer the right next
    action. (A newer withdrawn or declined row must never hide a live one.)"""
    row = (
        await session.execute(
            select(ConnectionRequest)
            .where(
                or_(
                    and_(
                        ConnectionRequest.subject_account_id == account_id,
                        ConnectionRequest.target_profile_id == other_account_id,
                    ),
                    and_(
                        ConnectionRequest.subject_account_id == other_account_id,
                        ConnectionRequest.target_profile_id == account_id,
                    ),
                )
            )
            .order_by(
                (ConnectionRequest.status == ConnectionStatus.ACCEPTED).desc(),
                (ConnectionRequest.status == ConnectionStatus.PENDING).desc(),
                ConnectionRequest.requested_at.desc(),
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    return _to_summary(row) if row else None


# [FR046] Categories a participant can share today. A video introduction and
# "additional personal information" have no content to share yet, and family
# contact details (FR048) go through `family_contact_share`.
SHARE_CATEGORIES = ("additional_photos", "phone", "email")


class ShareUnavailable(Exception):
    """Nothing to share in this category yet (no phone, email or extra photos)."""


@dataclass(frozen=True, slots=True)
class ShareState:
    category: str
    shared_at: datetime | None
    value: str | None
    available: bool
    pending: str | None = None


@dataclass(frozen=True, slots=True)
class SharingOverview:
    connection_id: UUID
    other_account_id: UUID
    mine: list[ShareState]
    theirs: list[ShareState]


async def _accepted_connection(
    session: AsyncSession, *, connection_id: UUID, account_id: UUID
) -> ConnectionRequest:
    row = (
        await session.execute(
            select(ConnectionRequest).where(
                ConnectionRequest.id == connection_id,
                ConnectionRequest.status == ConnectionStatus.ACCEPTED,
            )
        )
    ).scalar_one_or_none()
    if row is None or account_id not in (row.subject_account_id, row.target_profile_id):
        raise ConnectionNotFound
    return row


async def _own_share_values(session: AsyncSession, *, account_id: UUID) -> dict[str, str | None]:
    from app.components.identity_bridge import interface as identity_bridge
    from app.components.profile import interface as profile

    phone, email = await identity_bridge.get_own_identifiers(session, account_id=account_id)
    photos = await profile.list_own_photos(session, account_id=account_id) or []
    extra = len(photos) - 1
    return {
        "additional_photos": str(extra) if extra > 0 else None,
        "phone": phone,
        "email": email,
    }


async def sharing_overview(
    session: AsyncSession, *, connection_id: UUID, account_id: UUID
) -> SharingOverview:
    """[FR046/FR047] What the caller has shared with this connection, and what
    the other participant has shared back. Every visible item traces to a
    timestamped grant written by its owner."""
    row = await _accepted_connection(session, connection_id=connection_id, account_id=account_id)
    other = row.target_profile_id if row.subject_account_id == account_id else row.subject_account_id
    grants = (
        (
            await session.execute(
                select(SharingGrant).where(
                    SharingGrant.connection_id == connection_id,
                    SharingGrant.revoked_at.is_(None),
                )
            )
        )
        .scalars()
        .all()
    )
    mine = {g.category: g for g in grants if g.granted_by_account_id == account_id}
    theirs = {g.category: g for g in grants if g.granted_by_account_id == other}
    own = await _own_share_values(session, account_id=account_id)
    return SharingOverview(
        connection_id=connection_id,
        other_account_id=other,
        mine=[
            ShareState(
                category=c,
                shared_at=mine[c].granted_at if c in mine else None,
                value=own[c],
                available=own[c] is not None,
            )
            for c in SHARE_CATEGORIES
        ],
        theirs=[
            ShareState(
                category=c,
                shared_at=theirs[c].granted_at,
                value=theirs[c].shared_value,
                available=True,
            )
            for c in SHARE_CATEGORIES
            if c in theirs
        ],
    )


async def set_share(
    session: AsyncSession, *, connection_id: UUID, account_id: UUID, category: str, shared: bool
) -> ShareState:
    """[FR046/FR047/TR046/TR047] Share, or stop sharing, ONE category with ONE
    connection. This explicit call is the only writer of a sharing grant: no
    job, milestone or other category ever triggers it."""
    if category not in SHARE_CATEGORIES:
        raise ShareUnavailable

    from app.components.authorization import interface as authz
    from app.components.authorization.context import Action

    await authz.resolve(
        session,
        subject_id=account_id,
        account_id=account_id,
        target_profile_id=None,
        action=Action.WRITE,
    )
    await _accepted_connection(session, connection_id=connection_id, account_id=account_id)

    own = await _own_share_values(session, account_id=account_id)
    existing = (
        await session.execute(
            select(SharingGrant).where(
                SharingGrant.connection_id == connection_id,
                SharingGrant.category == category,
                SharingGrant.granted_by_account_id == account_id,
            )
        )
    ).scalar_one_or_none()
    now = datetime.now(UTC)

    if shared:
        if own[category] is None:
            raise ShareUnavailable
        value = None if category == "additional_photos" else own[category]
        if existing is None:
            existing = SharingGrant(
                connection_id=connection_id,
                category=category,
                granted_by_account_id=account_id,
                granted_at=now,
                shared_value=value,
            )
            session.add(existing)
        elif existing.revoked_at is not None or existing.shared_value != value:
            existing.granted_at = now
            existing.revoked_at = None
            existing.shared_value = value
        event_type = "CategoryShared"
    else:
        if existing is not None and existing.revoked_at is None:
            existing.revoked_at = now
            existing.shared_value = None
        event_type = "CategoryShareWithdrawn"

    await session.flush()
    await bus.publish(
        session,
        schema="mangaly_connection",
        aggregate_id=connection_id,
        event_type=event_type,
        payload={
            "connection_id": str(connection_id),
            "category": category,
            "actor_account_id": str(account_id),
        },
    )
    active = existing is not None and existing.revoked_at is None
    return ShareState(
        category=category,
        shared_at=existing.granted_at if active and existing is not None else None,
        value=own[category],
        available=own[category] is not None,
    )


async def has_active_share(
    session: AsyncSession, *, owner_account_id: UUID, viewer_account_id: UUID, category: str
) -> bool:
    """Whether `owner` currently shares `category` with `viewer` through an
    accepted connection between the two of them."""
    found = (
        await session.execute(
            select(SharingGrant.id)
            .join(ConnectionRequest, ConnectionRequest.id == SharingGrant.connection_id)
            .where(
                SharingGrant.category == category,
                SharingGrant.granted_by_account_id == owner_account_id,
                SharingGrant.revoked_at.is_(None),
                ConnectionRequest.status == ConnectionStatus.ACCEPTED,
                or_(
                    and_(
                        ConnectionRequest.subject_account_id == owner_account_id,
                        ConnectionRequest.target_profile_id == viewer_account_id,
                    ),
                    and_(
                        ConnectionRequest.subject_account_id == viewer_account_id,
                        ConnectionRequest.target_profile_id == owner_account_id,
                    ),
                ),
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    return found is not None


# --- FR048: family contact details, decided by the family member ----------


class NotAHomeCircleMember(Exception):
    """The chosen person is not an active member of the caller's Home Circle."""


class FamilyContactRequestNotFound(Exception):
    """No request is waiting for this family member's decision."""


@dataclass(frozen=True, slots=True)
class FamilyContactRequest:
    share_id: UUID
    candidate_account_id: UUID
    candidate_name: str | None
    relationship_type: str | None
    requested_at: datetime


async def family_contact_overview(
    session: AsyncSession, *, connection_id: UUID, account_id: UUID
) -> tuple[ShareState, ShareState | None]:
    """[FR048] The caller's own family-contact row (shared, waiting on a member,
    or not shared) and the family contact the other participant has shared."""
    from app.components.home_circle import interface as home_circle

    row = await _accepted_connection(session, connection_id=connection_id, account_id=account_id)
    other = row.target_profile_id if row.subject_account_id == account_id else row.subject_account_id
    members = await home_circle.list_home_circle(session, candidate_account_id=account_id)
    relationship_by_member = {m.member_account_id: m.relationship_type.value for m in members}

    grants = (
        (
            await session.execute(
                select(SharingGrant).where(
                    SharingGrant.connection_id == connection_id,
                    SharingGrant.category == "family_contact",
                    SharingGrant.revoked_at.is_(None),
                )
            )
        )
        .scalars()
        .all()
    )
    mine_grant = next((g for g in grants if g.granted_by_account_id == account_id), None)
    theirs_grant = next((g for g in grants if g.granted_by_account_id == other), None)

    pending = None
    if mine_grant is None:
        waiting = await session.execute(
            text(
                "SELECT family_member_account_id FROM mangaly_connection.family_contact_share "
                "WHERE connection_id = :connection_id AND candidate_account_id = :account_id "
                "AND family_authz_resolved_at IS NULL AND declined_at IS NULL "
                "ORDER BY candidate_authz_resolved_at DESC"
            ),
            {"connection_id": connection_id, "account_id": account_id},
        )
        for (member_account_id,) in waiting:
            if member_account_id in relationship_by_member:
                pending = relationship_by_member[member_account_id]
                break

    mine = ShareState(
        category="family_contact",
        shared_at=mine_grant.granted_at if mine_grant else None,
        value=None,
        available=bool(members),
        pending=pending,
    )
    theirs = (
        ShareState(
            category="family_contact",
            shared_at=theirs_grant.granted_at,
            value=theirs_grant.shared_value,
            available=True,
        )
        if theirs_grant
        else None
    )
    return mine, theirs


async def request_family_contact(
    session: AsyncSession, *, connection_id: UUID, account_id: UUID, membership_id: UUID
) -> ShareState:
    """[FR048/TR048, first of two authorization contexts] The candidate asks one
    Home Circle member to let their phone be shared with this connection.
    Nothing is shared until that member approves in their own session."""
    from app.components.authorization import interface as authz
    from app.components.authorization.context import Action, Capacity
    from app.components.home_circle import interface as home_circle

    await authz.resolve(
        session,
        subject_id=account_id,
        account_id=account_id,
        target_profile_id=None,
        action=Action.WRITE,
        capacity=Capacity.CANDIDATE,
    )
    current, _ = await family_contact_overview(
        session, connection_id=connection_id, account_id=account_id
    )
    if current.shared_at is not None:
        return current

    members = await home_circle.list_home_circle(session, candidate_account_id=account_id)
    member = next((m for m in members if m.membership_id == membership_id), None)
    connection_row = await _accepted_connection(
        session, connection_id=connection_id, account_id=account_id
    )
    match_account_id = (
        connection_row.target_profile_id
        if connection_row.subject_account_id == account_id
        else connection_row.subject_account_id
    )
    if member is None or member.member_account_id == match_account_id:
        raise NotAHomeCircleMember

    await session.execute(
        text(
            "INSERT INTO mangaly_connection.family_contact_share "
            "(connection_id, candidate_account_id, family_member_account_id, "
            "candidate_authz_resolved_at) "
            "VALUES (:connection_id, :account_id, :member_account_id, :now) "
            "ON CONFLICT (connection_id, candidate_account_id, family_member_account_id) "
            "DO UPDATE SET "
            "candidate_authz_resolved_at = EXCLUDED.candidate_authz_resolved_at, "
            "family_authz_resolved_at = NULL, granted_at = NULL, declined_at = NULL, "
            "family_member_phone = NULL"
        ),
        {
            "connection_id": connection_id,
            "account_id": account_id,
            "member_account_id": member.member_account_id,
            "now": datetime.now(UTC),
        },
    )
    await bus.publish(
        session,
        schema="mangaly_connection",
        aggregate_id=connection_id,
        event_type="FamilyContactShareRequested",
        payload={
            "connection_id": str(connection_id),
            "candidate_account_id": str(account_id),
            "family_member_account_id": str(member.member_account_id),
        },
    )
    return ShareState(
        category="family_contact",
        shared_at=None,
        value=None,
        available=True,
        pending=member.relationship_type.value,
    )


async def withdraw_family_contact(
    session: AsyncSession, *, connection_id: UUID, account_id: UUID
) -> ShareState:
    """The candidate stops sharing a family contact with this connection."""
    from app.components.authorization import interface as authz
    from app.components.authorization.context import Action

    await authz.resolve(
        session,
        subject_id=account_id,
        account_id=account_id,
        target_profile_id=None,
        action=Action.WRITE,
    )
    await _accepted_connection(session, connection_id=connection_id, account_id=account_id)
    grant = (
        await session.execute(
            select(SharingGrant).where(
                SharingGrant.connection_id == connection_id,
                SharingGrant.category == "family_contact",
                SharingGrant.granted_by_account_id == account_id,
                SharingGrant.revoked_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    # The request rows go with the grant, so a later request starts fresh and
    # no member's phone stays recorded against a connection it no longer
    # reaches.
    await session.execute(
        text(
            "DELETE FROM mangaly_connection.family_contact_share "
            "WHERE connection_id = :connection_id AND candidate_account_id = :account_id"
        ),
        {"connection_id": connection_id, "account_id": account_id},
    )
    if grant is not None:
        grant.revoked_at = datetime.now(UTC)
        grant.shared_value = None
        await session.flush()
        await bus.publish(
            session,
            schema="mangaly_connection",
            aggregate_id=connection_id,
            event_type="CategoryShareWithdrawn",
            payload={
                "connection_id": str(connection_id),
                "category": "family_contact",
                "actor_account_id": str(account_id),
            },
        )
    mine, _ = await family_contact_overview(
        session, connection_id=connection_id, account_id=account_id
    )
    return mine


async def list_family_contact_requests(
    session: AsyncSession, *, account_id: UUID
) -> list[FamilyContactRequest]:
    """[FR048] Requests waiting for the caller to decide about their own contact details."""
    rows = await session.execute(
        text("SELECT * FROM mangaly_connection.list_family_contact_requests(:account_id)"),
        {"account_id": account_id},
    )
    return [
        FamilyContactRequest(
            share_id=r["share_id"],
            candidate_account_id=r["candidate_account_id"],
            candidate_name=r["candidate_name"],
            relationship_type=r["relationship_type"],
            requested_at=r["requested_at"],
        )
        for r in rows.mappings()
    ]


async def decide_family_contact_request(
    session: AsyncSession, *, share_id: UUID, account_id: UUID, approve: bool
) -> None:
    """[FR048/TR048, second authorization context] The family member decides,
    in their own session and capacity, whether their phone may be shared."""
    from app.components.authorization import interface as authz
    from app.components.authorization.context import Action, Capacity

    await authz.resolve(
        session,
        subject_id=account_id,
        account_id=account_id,
        target_profile_id=None,
        action=Action.WRITE,
        capacity=Capacity.FAMILY,
    )
    decided = (
        await session.execute(
            text(
                "SELECT mangaly_connection.decide_family_contact_share("
                ":share_id, :account_id, :approve)"
            ),
            {"share_id": share_id, "account_id": account_id, "approve": approve},
        )
    ).scalar_one()
    if not decided:
        raise FamilyContactRequestNotFound
    await bus.publish(
        session,
        schema="mangaly_connection",
        aggregate_id=share_id,
        event_type="FamilyContactShareApproved" if approve else "FamilyContactShareDeclined",
        payload={"share_id": str(share_id), "family_member_account_id": str(account_id)},
    )
