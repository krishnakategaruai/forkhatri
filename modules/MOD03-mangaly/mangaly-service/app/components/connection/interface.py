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

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.connection.models import ConnectionRequest, ConnectionStatus
from app.config.settings import get_settings
from app.events import bus
from app.rate_limiting import limiter

__all__ = [
    "AlreadyPending",
    "ConnectionNotFound",
    "ConnectionSummary",
    "InvalidTarget",
    "RateLimited",
    "UnauthorizedOnBehalfOf",
    "accept",
    "decline",
    "get_request",
    "list_incoming",
    "list_sent",
    "send_request",
]

_SOURCE = "connection"


class InvalidTarget(Exception):
    """[FR042 failure outcome] Cannot connect to yourself, or the target has
    no profile at all."""


class UnauthorizedOnBehalfOf(Exception):
    """[FR042 acceptance criterion] The caller named an `on_behalf_of_profile_id`
    they hold no `family_info` grant for — not a genuine Home Circle member
    of that candidate, so the request is refused rather than silently sent
    as if it came from the candidate themselves."""


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
    on_behalf_of_profile_id: UUID | None
    target_account_id: UUID
    status: ConnectionStatus
    requested_at: datetime
    decided_at: datetime | None


def _to_summary(row: ConnectionRequest) -> ConnectionSummary:
    return ConnectionSummary(
        id=row.id,
        acting_account_id=row.acting_account_id,
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
    on_behalf_of_profile_id: UUID | None = None,
) -> UUID:
    """[FR042/TR042] Send a connection request. `acting_account_id` is
    always the authenticated caller (SP001-class: never client-supplied);
    `on_behalf_of_profile_id` marks a family member acting for their own
    candidate, carried for BR15 accountability, never used to widen who the
    request is *from* in the recipient's eyes (`target_account_id` is the
    only thing that changes)."""
    if acting_account_id == target_account_id:
        raise InvalidTarget

    if on_behalf_of_profile_id is not None:
        from app.components.authorization import interface as authz
        from app.components.authorization.context import AuthorizationDenied

        try:
            await authz.resolve_effective_account(
                session,
                acting_account_id=acting_account_id,
                on_behalf_of_profile_id=on_behalf_of_profile_id,
            )
        except AuthorizationDenied as exc:
            raise UnauthorizedOnBehalfOf from exc

    settings = get_settings()
    try:
        await limiter.enforce_durable(
            scope=limiter.RateLimitScope.CONNECTION_REQUEST,
            subject=str(acting_account_id),
            limit_max=settings.rate_limit_connection_request_max_per_day,
            window_seconds=86400,
        )
    except limiter.RateLimitExceeded as exc:
        raise RateLimited(exc.result.retry_after_seconds) from exc

    existing = (
        await session.execute(
            select(ConnectionRequest.id).where(
                ConnectionRequest.acting_account_id == acting_account_id,
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
                (id, acting_account_id, on_behalf_of_profile_id, target_profile_id, status)
            VALUES (:id, :acting, :on_behalf_of, :target, 'pending')
            """
        ),
        {
            "id": connection_id,
            "acting": acting_account_id,
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
    """[FR045] Every connection the caller has sent, any status — a
    candidate can hold several at once by design."""
    rows = (
        await session.execute(
            select(ConnectionRequest)
            .where(ConnectionRequest.acting_account_id == account_id)
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
