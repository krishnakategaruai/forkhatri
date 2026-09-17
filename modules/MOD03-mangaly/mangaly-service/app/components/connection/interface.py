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
    "RateLimited",
    "ShareState",
    "ShareUnavailable",
    "SharingOverview",
    "OnBehalfNotAllowed",
    "accept",
    "decline",
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


class OnBehalfNotAllowed(Exception):
    """[FR042, DEC-V1-019] A request named an `on_behalf_of_profile_id`. Family
    members suggest a profile to the candidate (FR014); only the candidate
    sends a connection request, because a request is the candidate's own
    decision (M01-I §6–7: suggestion is not consent, initiation authority is
    not decision authority)."""


class AlreadyPending(Exception):
    """[FR045] Not a "no repeat connections" rule (FR045 explicitly allows
    many) — just a spam guard: an already-pending request to the SAME target
    should not be duplicated by a second tap of the same button."""


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

    existing = (
        await session.execute(
            select(ConnectionRequest.id).where(
                ConnectionRequest.subject_account_id == subject_account_id,
                ConnectionRequest.target_profile_id == target_account_id,
                ConnectionRequest.status == ConnectionStatus.PENDING,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise AlreadyPending

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


async def accept(session: AsyncSession, *, connection_id: UUID, account_id: UUID) -> None:
    """[FR043/FR044/TR043/TR044] Accept: flips status and grants each party
    `candidate_info` visibility into the other's real profile — the two
    grants ARE the meaning of "accepted", not a downstream side effect
    FR044's "triggers nothing else" forbids (that clause is about NOT
    auto-exchanging contact info, NOT auto-exposing Home Circle, and NOT
    creating unrelated event subscribers — see this module's own docstring).
    Creating the conversation row is deliberately NOT done here: it happens
    lazily on the first message send (`communication.interface.send_message`),
    which is what actually keeps this endpoint's side effects to exactly the
    entitlement change acceptance itself represents.

    The two grants are created through `mangaly_authz
    .grant_connection_candidate_info()`, a SECURITY DEFINER function, NOT
    through `authorization.interface.grant()` — see
    `migrations/010-authz-grant-connection-candidate-info-function.sql` for
    why: one of the two grants (subject = the OTHER party, target = this
    party's own real `profile.id`) cannot be inserted by EITHER party's own
    session under `mangaly_authz.grant`'s own RLS at all, a genuine
    structural id-space mismatch in the sealed schema, not a permissions gap
    this module can close by calling the sanctioned function correctly.
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
            "SET status = 'accepted', decided_at = :now, decided_by_account_id = :account_id, "
            "updated_at = :now WHERE id = :id"
        ),
        {"now": now, "account_id": account_id, "id": connection_id},
    )

    await session.execute(
        text("SELECT mangaly_authz.grant_connection_candidate_info(:connection_id, :account_id)"),
        {"connection_id": connection_id, "account_id": account_id},
    )

    # [FR049, migration 026] Acceptance opens the private conversation with one
    # system line, so both people — the candidate above all — learn the request
    # succeeded where they will actually talk, not by re-reading a status word
    # on another screen.
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
        },
    )


async def decline(session: AsyncSession, *, connection_id: UUID, account_id: UUID) -> None:
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
            "SET status = 'declined', decided_at = :now, decided_by_account_id = :account_id, "
            "updated_at = :now WHERE id = :id"
        ),
        {"now": datetime.now(UTC), "account_id": account_id, "id": connection_id},
    )


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
    if row is None or account_id not in (row.acting_account_id, row.target_profile_id):
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
    other = row.target_profile_id if row.acting_account_id == account_id else row.acting_account_id
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
                        ConnectionRequest.acting_account_id == owner_account_id,
                        ConnectionRequest.target_profile_id == viewer_account_id,
                    ),
                    and_(
                        ConnectionRequest.acting_account_id == viewer_account_id,
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
    other = row.target_profile_id if row.acting_account_id == account_id else row.acting_account_id
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
        if connection_row.acting_account_id == account_id
        else connection_row.acting_account_id
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
